import os
import sys
import json
import requests
import time
from collections import defaultdict

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2324 full"
SEASON = 2024                   # 2024 = the 2023-24 season
PLAYS_FOLDER = "cbbd"           # made by 10cbbdplays.py: each game's plays, with the running score
PBP_FOLDER = "playbyplay"       # what this writes, in the layout 6playbyplay.py uses: what on/off and the lineups are built from
SCHOOLS_FILE = os.path.join(BASE_DIR, "cbbd_schools.json")     # our team name -> their school name (made by 10cbbdplays.py)
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cbbd_key.txt")   # your CollegeBasketballData.com API key
API = "https://api.collegebasketballdata.com"
KEEP_CALLS = 25                 # stop before the month's allowance runs out, leaving this many calls
SOURCE = "cbbd"
BACKUP_FOLDER = "playbyplay_ncaa"   # an NCAA play-by-play file that is replaced is moved here first

# For a season the NCAA's feed has no play-by-play for, this builds each game's play-by-play file from
# CollegeBasketballData.com: the plays 10cbbdplays.py saved, plus every substitution (who came in and went out, and
# when), which is what on/off and the lineups need. One request per team returns that team's substitutions for the
# whole season, so each team's copy of a game carries its own substitutions. Run it after 10cbbdplays.py.
# A game the NCAA does have play-by-play for is left alone unless that file has no substitutions for the team (about
# half of 2024-25's do not): then the lineups cannot be worked out from it, and it is replaced the same way.
# Teams with nothing to do are skipped, so it can be stopped and run again.

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def period_length(period):
    return 1200 if period <= 2 else 300

def clock(left):
    return "%02d:%02d" % divmod(max(0, int(left)), 60)

def build(game, side, stints):
    """One team's play-by-play for one game. game: its cbbd file. side: 0 if the team is home_team, 1 if away_team.
    stints: the team's rows for this game, each one player's spell on the floor."""
    team_name = game["home_team"] if side == 0 else game["away_team"]
    def row(period, left, mine, theirs, text, order):
        home, away = (mine, theirs) if side == 0 else (theirs, mine)
        return (period, -left, order, {"period": period, "period_name": "", "clock": clock(left), "seconds_left": left, "team": team_name,
                                       "is_home": side == 0, "home_score": home, "away_score": away, "text": text})
    rows = []
    starters = defaultdict(list)        # period -> the players on the floor as it began
    for s in stints:
        name, came, went = s.get("athlete") or "", s.get("subIn") or {}, s.get("subOut") or {}
        if not name or came.get("period") is None or went.get("period") is None: continue
        # every period he was on the floor at the start of
        for period in range(came["period"], went["period"] + 1):
            starts_it = came["secondsRemaining"] >= period_length(period) if period == came["period"] else True
            if starts_it:
                # (how sure, name): surest when his spell begins with the period, then the later he came in before it
                sure = 2 if period == came["period"] else 1
                starters[period].append((sure, came["period"], -came["secondsRemaining"], name))
        if came["secondsRemaining"] < period_length(came["period"]):
            rows.append(row(came["period"], came["secondsRemaining"], came.get("teamPoints"), came.get("opponentPoints"), f"Subbing in for {team_name}-{name}", 2))
        if went["secondsRemaining"] > 0:
            rows.append(row(went["period"], went["secondsRemaining"], went.get("teamPoints"), went.get("opponentPoints"), f"Subbing out for {team_name}-{name}", 2))
    for period, names in starters.items():
        # Named in a play as the period opens, which is how the lineup code knows who started it. Substitutions made
        # at half-time are not recorded, so a spell can run on into a half the player did not start: when that leaves
        # more than five names, the five likeliest are kept (a spell that begins with the period, then the players
        # who came in latest before it).
        five = []
        for _, _, _, name in sorted(names, reverse=True):
            if name not in five and len(five) < 5:
                five.append(name)
        rows.append(row(period, period_length(period), None, None, "On the floor: " + ", ".join(sorted(five)), 0))
    for period, left, play_side, home, away, text in game.get("plays", []):
        if period is None or left is None: continue
        name = game["home_team"] if play_side == 0 else game["away_team"] if play_side == 1 else ""
        rows.append((period, -left, 1, {"period": period, "period_name": "", "clock": clock(left), "seconds_left": left, "team": name,
                                        # The play's wording is left out on purpose. The lineup code takes anyone named in a
                                        # play as being on the floor, and these plays' clocks do not always agree with the
                                        # substitutions' to the second; the substitutions and the "On the floor" rows say it all.
                                        "is_home": play_side == 0, "home_score": home, "away_score": away, "text": ""}))
    rows.sort(key=lambda r: r[:3])
    return {"game_id": game["game_id"], "source": SOURCE, "game_info": "", "status": "", "home_team": game["home_team"],
            "away_team": game["away_team"], "plays": [r[3] for r in rows]}

def needs_one(team_path, team, f):
    """True when the team has no usable play-by-play for the game: no file, or an NCAA file with no substitutions of its own."""
    game = read_json(os.path.join(team_path, PBP_FOLDER, f))
    if not game: return True
    if game.get("source") == SOURCE: return False
    name = team.rstrip(". ")
    return not any(p.get("text", "").startswith("Subbing") and str(p.get("team", "")).rstrip(". ") == name for p in game.get("plays", []))

def main():
    key = open(KEY_FILE, encoding="utf-8").read().strip() if os.path.exists(KEY_FILE) else ""
    schools = read_json(SCHOOLS_FILE)
    if not key or not schools:
        print("Run 10cbbdplays.py first (and put your API key in cbbd_key.txt).")
        return
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    wanted = [w.lower() for w in sys.argv[1:]]
    teams = []
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            plays_dir = os.path.join(conf_path, team, PLAYS_FOLDER)
            if not os.path.isdir(plays_dir) or team.rstrip(". ") not in schools: continue
            if wanted and team.lower() not in wanted: continue
            todo = [f for f in os.listdir(plays_dir) if f.endswith(".json") and needs_one(os.path.join(conf_path, team), team, f)]
            if todo:
                teams.append((team, os.path.join(conf_path, team), todo))
    print(f"{len(teams)} teams have games with no usable play-by-play yet ({sum(len(t[2]) for t in teams)} team-games). One request per team.", flush=True)
    written = 0
    try:
        for n, (team, team_path, todo) in enumerate(teams, 1):
            try:
                response = requests.get(API + "/substitutions/team", params={"season": SEASON, "team": schools[team.rstrip(". ")]}, headers=headers, timeout=300)
            except Exception as e:
                print(f"[{n}/{len(teams)}] {team}: request failed ({e}) - will retry next run", flush=True)
                time.sleep(10)
                continue
            left = response.headers.get("X-CallLimit-Remaining", "?")
            if response.status_code != 200:
                print(f"[{n}/{len(teams)}] {team}: refused ({response.status_code}) {response.text[:120]}", flush=True)
                if response.status_code in (401, 403, 429): break
                continue
            by_game = defaultdict(list)
            for s in response.json():
                by_game[s.get("gameId")].append(s)
            count = 0
            for f in todo:
                game = read_json(os.path.join(team_path, PLAYS_FOLDER, f))
                if not game or not game.get("plays") or game.get("cbbd_id") not in by_game: continue
                side = 0 if game["home_team"].rstrip(". ") == team.rstrip(". ") else 1 if game["away_team"].rstrip(". ") == team.rstrip(". ") else None
                if side is None: continue
                os.makedirs(os.path.join(team_path, PBP_FOLDER), exist_ok=True)
                if os.path.exists(os.path.join(team_path, PBP_FOLDER, f)):      # the NCAA's version is kept, out of the way
                    os.makedirs(os.path.join(team_path, BACKUP_FOLDER), exist_ok=True)
                    if not os.path.exists(os.path.join(team_path, BACKUP_FOLDER, f)):
                        os.replace(os.path.join(team_path, PBP_FOLDER, f), os.path.join(team_path, BACKUP_FOLDER, f))
                with open(os.path.join(team_path, PBP_FOLDER, f), "w", encoding="utf-8") as out:
                    json.dump(build(game, side, by_game[game["cbbd_id"]]), out, separators=(",", ":"))
                count += 1
            written += count
            print(f"[{n}/{len(teams)}] {team}: {count} of {len(todo)} games written ({left} requests left this month)", flush=True)
            if left != "?" and int(left) <= KEEP_CALLS:
                print("Stopping: nearly out of requests for the month. Run it again when the allowance resets.", flush=True)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")
    print("-" * 30)
    print(f"Play-by-play files written this run: {written}")
    print("-" * 30)

if __name__ == "__main__":
    main()
