import os
import re
import sys
import json
import requests
import time
from collections import defaultdict

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2425 full"
SEASON = 2025                   # 2025 = the 2024-25 season
SHOTS_FOLDER = "shots"          # made by 9espnshots.py; each file there carries the game's ESPN id
PLAYS_FOLDER = "cbbd"           # saved inside each team folder, e.g. data/seasons/2526/SEC/Alabama/cbbd/6505422.json
TEAM_IDS_FILE = os.path.join(BASE_DIR, "espn_teams.json")      # our team name -> ESPN's team id (made by 9espnshots.py)
SCHOOLS_FILE = os.path.join(BASE_DIR, "cbbd_schools.json")     # our team name -> their school name, kept so it is only asked for once
TRIED_FILE = os.path.join(BASE_DIR, "cbbd_tried.json")         # teams already asked for; delete it to ask for them again
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cbbd_key.txt")   # your CollegeBasketballData.com API key
API = "https://api.collegebasketballdata.com"
KEEP_CALLS = 25                 # stop before the month's allowance runs out, leaving this many calls
ENOUGH = 0.8                    # a game counts as having shot spots when this share of its shots do (the dashboard's own rule)
SOURCE = "cbbd"
# Every play is kept too (with the running score), so 11cbbdsubs.py can build a play-by-play file from it for a game
# the NCAA has none for, or one whose NCAA play-by-play has no substitutions. A game saved before this was switched on
# is asked for again.
SAVE_PLAYS = True

# CollegeBasketballData.com has three things the other sources do not, and one request gets all of them for every
# game a team played (both teams' plays):
#   - the player on every turnover
#   - the five on the floor for each team on every play (recent seasons only)
#   - where on the floor each shot was taken, for games where ESPN's own play-by-play has no shot spots
# The first two are saved for each game in the team's "cbbd" folder. The shot spots are written into the shot files
# 9espnshots.py saved: only the missing x and y are filled, and a shot that already has a spot keeps it.
#
# A game is covered by asking for either of its two teams, so the teams are asked for in the order that covers the
# most unfinished games first: fewer requests than one per team. It can be stopped and run again.
#     python "collect/2425\10cbbdplays.py"            get what is missing
#     python "collect/2425\10cbbdplays.py" count      only say how many requests it would take
#
# A saved cbbd file looks like:
#   "turnovers": [side, period, seconds left, player]                 side 0 = home_team, 1 = away_team
#   "floor":     [period, seconds left, side, [the five players]]     one entry each time that side's five changes

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data, **how):
    with open(path, "w", encoding="utf-8") as out:
        json.dump(data, out, **how)

# ---------------------------
# OUR GAMES
# ---------------------------
def is_free_throw(shot):
    return "free" in str(shot[4]).lower()

def has_spots(shots):
    tries = [s for s in shots if not is_free_throw(s)]
    return bool(tries) and sum(1 for s in tries if s[7] is not None and s[8] is not None) >= ENOUGH * len(tries)

def load_our_games():
    """ESPN game id -> our game id, teams, date, its shot files, and what it still needs:
    "plays" (no cbbd file yet) and "spots" (its shots have no spots, and they have not been asked for)."""
    games = {}
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            shots_dir = os.path.join(conf_path, team, SHOTS_FOLDER)
            if not os.path.isdir(shots_dir): continue
            for f in os.listdir(shots_dir):
                path = os.path.join(shots_dir, f)
                data = read_json(path)
                if not data or not data.get("espn_id"): continue
                game = games.setdefault(str(data["espn_id"]), {"id": f[:-5], "home": data["home_team"], "away": data["away_team"],
                                                               "date": data.get("date", ""), "files": [], "plays": False, "spots": False})
                game["files"].append(path)
                saved = os.path.join(conf_path, team, PLAYS_FOLDER, f)
                if not os.path.exists(saved) or (SAVE_PLAYS and "plays" not in (read_json(saved) or {})):
                    game["plays"] = True
                if not has_spots(data.get("shots") or []) and not data.get("spots"):
                    game["spots"] = True
    return games

def unfinished(game):
    return game["plays"] or game["spots"]

# ---------------------------
# TURNOVERS AND THE FIVE ON THE FLOOR
# ---------------------------
def compact(plays, game, school_side):
    """One game's plays -> the turnovers and the changes of the five on the floor."""
    plays = sorted(plays, key=lambda p: (p.get("period") or 0, -(p.get("secondsRemaining") or 0), p.get("id") or 0))
    turnovers, floor, kept = [], [], []
    current = {0: None, 1: None}
    # their home team is not always ours (neutral floors), so the running score is turned our way round
    their_home = next((school_side[p.get("team")] if p.get("isHomeTeam") else 1 - school_side[p.get("team")]
                       for p in plays if p.get("isHomeTeam") is not None and school_side.get(p.get("team")) is not None), 0)
    for p in plays:
        period, left = p.get("period"), p.get("secondsRemaining")
        if SAVE_PLAYS:
            scores = (p.get("homeScore"), p.get("awayScore")) if their_home == 0 else (p.get("awayScore"), p.get("homeScore"))
            kept.append([period, left, school_side.get(p.get("team")), scores[0], scores[1], p.get("playText") or ""])
        fives = {0: [], 1: []}
        for player in p.get("onFloor") or []:
            side = school_side.get(player.get("team"))
            if side is not None:
                fives[side].append(player.get("name", ""))
        for side in (0, 1):
            five = sorted(fives[side])
            if len(five) == 5 and five != current[side]:
                current[side] = five
                floor.append([period, left, side, five])
        if "Turnover" in (p.get("playType") or ""):
            side = school_side.get(p.get("team"))
            people = p.get("participants") or []
            if side is not None:
                turnovers.append([side, period, left, people[0].get("name", "") if people else ""])
    data = {"game_id": game["id"], "source": SOURCE, "date": game["date"], "home_team": game["home"], "away_team": game["away"],
            "turnovers": turnovers, "floor": floor}
    if SAVE_PLAYS:
        data["cbbd_id"], data["plays"] = (plays[0].get("gameId") if plays else None), kept
    return data

# ---------------------------
# SHOT SPOTS
# ---------------------------
def our_spot(location):
    """Their spot (tenths of a foot on the whole floor, x along it) -> ours: feet, x across the floor and y out from
    the basket's end, the same way round as ESPN's."""
    x, y = location.get("x"), location.get("y")
    if x is None or y is None: return None
    if x < 470:
        return round(50 - y / 10), round(x / 10 - 5)
    return round(y / 10), round((940 - x) / 10 - 5)

def last_name(name):
    words = re.sub(r"[^a-z ]", "", str(name).lower()).split()
    words = [w for w in words if w not in ("jr", "sr", "ii", "iii", "iv")]
    return words[-1] if words else ""

def fill(data, plays):
    """Puts their spots on our shots. Returns how many shots got one."""
    theirs = defaultdict(list)       # (period, seconds left, made, points) -> their shots at that moment
    for p in plays:
        info = p.get("shotInfo") or {}
        spot = our_spot(info.get("location") or {})
        if spot is None: continue
        key = (p.get("period"), p.get("secondsRemaining"), int(bool(info.get("made"))), p.get("scoreValue") or 0)
        theirs[key].append([last_name((info.get("shooter") or {}).get("name")), spot, False])
    filled = 0
    for shot in data["shots"]:
        if is_free_throw(shot) or (shot[7] is not None and shot[8] is not None): continue
        found = [t for t in theirs.get((shot[2], shot[3], shot[5], shot[6]), []) if not t[2]]
        named = [t for t in found if t[0] == last_name(shot[1])]
        pick = named[0] if named else found[0] if len(found) == 1 else None      # same moment and result; the name settles a tie
        if pick:
            pick[2] = True
            shot[7], shot[8] = pick[1]
            filled += 1
    return filled

# ---------------------------
# MAIN
# ---------------------------
def main():
    count_only = "count" in sys.argv[1:]
    games = load_our_games()
    todo_games = {i: g for i, g in games.items() if unfinished(g)}
    print(f"{len(games)} games have a shot file; {sum(g['plays'] for g in games.values())} still need their plays, "
          f"{sum(g['spots'] for g in games.values())} are missing shot spots.", flush=True)
    team_ids = read_json(TEAM_IDS_FILE, {})
    if not games or not team_ids:
        print("Run 9espnshots.py first: this needs the ESPN game and team ids it saves.")
        return
    if not todo_games:
        return
    key = open(KEY_FILE, encoding="utf-8").read().strip() if os.path.exists(KEY_FILE) else ""
    if not key:
        print(f"Put your CollegeBasketballData.com API key in {KEY_FILE} first.")
        return
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}

    # Their school names, matched to ours through the ESPN team id both sides know
    schools = read_json(SCHOOLS_FILE)
    # (asked for again when the saved list is short: it was made before 9espnshots.py had learned every team's id)
    if not schools or len(schools) < 0.9 * len(team_ids):
        response = requests.get(API + "/teams", params={"season": SEASON}, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"Could not read the team list ({response.status_code}): {response.text[:200]}")
            return
        ours_by_espn = {str(espn_id): name for name, espn_id in team_ids.items()}
        schools = {ours_by_espn[str(t.get("sourceId"))].rstrip(". "): t["school"] for t in response.json() if str(t.get("sourceId")) in ours_by_espn}
        write_json(SCHOOLS_FILE, schools, indent=1, sort_keys=True)

    tried = set(read_json(TRIED_FILE, []))
    by_team = defaultdict(set)      # our team name -> the ESPN ids of its unfinished games
    for espn_id, game in todo_games.items():
        for name in (game["home"], game["away"]):
            by_team[name.rstrip(". ")].add(espn_id)
    # the teams to ask for, most unfinished games covered first
    left, picked = set(todo_games), []
    open_teams = {t for t in by_team if t in schools and t not in tried}
    # Optional: name some teams to ask for only those, e.g.  python "collect/2425\10cbbdplays.py" Alabama Duke
    wanted = [w.lower() for w in sys.argv[1:] if w != "count"]
    if wanted:
        open_teams = {t for t in open_teams if t.lower() in wanted}
    while left and open_teams:
        best = max(open_teams, key=lambda t: (len(by_team[t] & left), t))
        if not by_team[best] & left: break
        picked.append(best)
        left -= by_team[best]
        open_teams.discard(best)
    print(f"{len(picked)} requests would cover {len(todo_games) - len(left)} of the {len(todo_games)} unfinished games"
          + (f"; {len(left)} have no team left to ask" if left else "") + ".", flush=True)
    if count_only:
        return

    done = set()
    plays_saved = spots_filled = 0
    try:
        for n, team in enumerate(picked, 1):
            todo = by_team[team] - done
            if not todo: continue
            try:
                response = requests.get(API + "/plays/team", params={"season": SEASON, "team": schools[team]}, headers=headers, timeout=300)
            except Exception as e:
                print(f"[{n}/{len(picked)}] {team}: request failed ({e}) - will retry next run", flush=True)
                time.sleep(10)
                continue
            calls_left = response.headers.get("X-CallLimit-Remaining", "?")
            if response.status_code != 200:
                print(f"[{n}/{len(picked)}] {team}: refused ({response.status_code}) {response.text[:120]}", flush=True)
                if response.status_code in (401, 403, 429): break
                continue
            by_game = defaultdict(list)
            for p in response.json():
                by_game[str(p.get("gameSourceId"))].append(p)
            got_plays = got_spots = 0
            for espn_id in sorted(todo):
                plays = by_game.get(espn_id)
                if not plays: continue
                game = games[espn_id]
                school_side = {schools.get(game["home"].rstrip(". ")): 0, schools.get(game["away"].rstrip(". ")): 1}
                summary = compact(plays, game, school_side)
                located = False
                for path in game["files"]:
                    folder = os.path.dirname(os.path.dirname(path))
                    os.makedirs(os.path.join(folder, PLAYS_FOLDER), exist_ok=True)
                    write_json(os.path.join(folder, PLAYS_FOLDER, game["id"] + ".json"), summary, separators=(",", ":"))
                    if game["spots"]:
                        data = read_json(path)
                        if not data: continue
                        filled = fill(data, plays)
                        # "spots" says where the spots came from, or that there were none to be had, so it is not asked for again
                        data["spots"] = "cbbd" if filled else "none"
                        write_json(path, data, separators=(",", ":"))
                        located = located or has_spots(data["shots"])
                done.add(espn_id)
                got_plays += 1 if game["plays"] else 0
                got_spots += 1 if located else 0
            plays_saved += got_plays
            spots_filled += got_spots
            tried.add(team)
            write_json(TRIED_FILE, sorted(tried))
            print(f"[{n}/{len(picked)}] {team}: {len(todo)} games to do - plays saved for {got_plays}, shot spots filled for {got_spots} "
                  f"({calls_left} requests left this month)", flush=True)
            if calls_left != "?" and int(calls_left) <= KEEP_CALLS:
                print("Stopping: nearly out of requests for the month. Run it again when the allowance resets.", flush=True)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    games = load_our_games()
    print("-" * 30)
    print(f"This run: plays saved for {plays_saved} games, shot spots filled for {spots_filled}")
    print(f"Games with plays saved: {sum(not g['plays'] for g in games.values())} of {len(games)}")
    print(f"Games with shot spots: {sum(1 for g in games.values() if all(has_spots((read_json(f) or {}).get('shots') or []) for f in g['files']))} of {len(games)}")
    print("-" * 30)

if __name__ == "__main__":
    main()
