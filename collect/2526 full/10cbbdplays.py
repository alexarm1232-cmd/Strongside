import os
import sys
import json
import requests
import time

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2526 full"
SEASON = 2026                   # 2026 = the 2025-26 season
SHOTS_FOLDER = "shots"          # made by 9espnshots.py; each file there carries the game's ESPN id
PLAYS_FOLDER = "cbbd"           # saved inside each team folder, e.g. data/seasons/2526/SEC/Alabama/cbbd/6505422.json
TEAM_IDS_FILE = os.path.join(BASE_DIR, "espn_teams.json")      # our team name -> ESPN's team id (made by 9espnshots.py)
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cbbd_key.txt")   # your CollegeBasketballData.com API key
API = "https://api.collegebasketballdata.com"
KEEP_CALLS = 25                 # stop before the month's allowance runs out, leaving this many calls
SOURCE = "cbbd"

# CollegeBasketballData.com has two things the other sources do not: the player on every turnover, and the five
# on the floor for each team on every play. One request returns a whole team's season, so this goes team by team
# and saves, for each of our games, just those two things. Files keep the NCAA game id.
#
# A saved file looks like:
#   "turnovers": [side, period, seconds left, player]                 side 0 = home_team, 1 = away_team
#   "floor":     [period, seconds left, side, [the five players]]     one entry each time that side's five changes

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def load_our_games():
    """ESPN game id -> our game id, the two team names and the team folders that hold the game."""
    games = {}
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            shots_dir = os.path.join(conf_path, team, SHOTS_FOLDER)
            if not os.path.isdir(shots_dir): continue
            for f in os.listdir(shots_dir):
                shots = read_json(os.path.join(shots_dir, f))
                if not shots or not shots.get("espn_id"): continue
                game = games.setdefault(str(shots["espn_id"]), {"id": f[:-5], "home": shots["home_team"], "away": shots["away_team"],
                                                               "date": shots.get("date", ""), "folders": []})
                game["folders"].append(os.path.join(conf_path, team))
    return games

def is_saved(game):
    return all(os.path.exists(os.path.join(folder, PLAYS_FOLDER, game["id"] + ".json")) for folder in game["folders"])

def compact(plays, game, school_side):
    """One game's plays -> the turnovers and the changes of the five on the floor."""
    plays.sort(key=lambda p: (p.get("period") or 0, -(p.get("secondsRemaining") or 0), p.get("id") or 0))
    turnovers, floor = [], []
    current = {0: None, 1: None}
    for p in plays:
        period, left = p.get("period"), p.get("secondsRemaining")
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
    return {"game_id": game["id"], "source": SOURCE, "date": game["date"], "home_team": game["home"], "away_team": game["away"],
            "turnovers": turnovers, "floor": floor}

def main():
    key = (read_json(KEY_FILE) if False else open(KEY_FILE, encoding="utf-8").read().strip()) if os.path.exists(KEY_FILE) else ""
    if not key:
        print(f"Put your CollegeBasketballData.com API key in {KEY_FILE} first.")
        return
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    games = load_our_games()
    team_ids = read_json(TEAM_IDS_FILE, {})
    if not games or not team_ids:
        print("Run 9espnshots.py first: this needs the ESPN game and team ids it saves.")
        return

    # Their school names, matched to ours through the ESPN team id both sides know
    response = requests.get(API + "/teams", params={"season": SEASON}, headers=headers, timeout=60)
    if response.status_code != 200:
        print(f"Could not read the team list ({response.status_code}): {response.text[:200]}")
        return
    ours_by_espn = {str(espn_id): name for name, espn_id in team_ids.items()}
    school_of = {}      # our team name (as the game files spell it) -> their school name
    for t in response.json():
        if str(t.get("sourceId")) in ours_by_espn:
            school_of[ours_by_espn[str(t["sourceId"])].rstrip(". ")] = t["school"]

    # Optional: name some teams to do only those, e.g.  python "collect\10cbbdplays.py" Alabama Duke
    wanted = [w.lower() for w in sys.argv[1:]]
    by_team = {}        # our team name -> its games
    for espn_id, game in games.items():
        for name in (game["home"], game["away"]):
            by_team.setdefault(name.rstrip(". "), {})[espn_id] = game
    teams = sorted(t for t in by_team if t in school_of and (not wanted or t.lower() in wanted))
    print(f"{len(games)} games, {len(teams)} teams. One request per team; teams whose games are all saved are skipped.", flush=True)

    saved = 0
    try:
        for n, team in enumerate(teams, 1):
            todo = {i: g for i, g in by_team[team].items() if not is_saved(g)}
            if not todo:
                continue
            try:
                response = requests.get(API + "/plays/team", params={"season": SEASON, "team": school_of[team]}, headers=headers, timeout=300)
            except Exception as e:
                print(f"[{n}/{len(teams)}] {team}: request failed ({e}) - will retry next run", flush=True)
                time.sleep(10)
                continue
            left = response.headers.get("X-CallLimit-Remaining", "?")
            if response.status_code != 200:
                print(f"[{n}/{len(teams)}] {team}: refused ({response.status_code}) {response.text[:120]}", flush=True)
                if response.status_code in (401, 403, 429): break
                continue
            by_game = {}
            for p in response.json():
                by_game.setdefault(str(p.get("gameSourceId")), []).append(p)
            count = 0
            for espn_id, game in todo.items():
                plays = by_game.get(espn_id)
                if not plays: continue
                school_side = {school_of.get(game["home"].rstrip(". ")): 0, school_of.get(game["away"].rstrip(". ")): 1}
                data = compact(plays, game, school_side)
                for folder in game["folders"]:
                    os.makedirs(os.path.join(folder, PLAYS_FOLDER), exist_ok=True)
                    with open(os.path.join(folder, PLAYS_FOLDER, game["id"] + ".json"), "w", encoding="utf-8") as out:
                        json.dump(data, out, separators=(",", ":"))
                count += 1
            saved += count
            print(f"[{n}/{len(teams)}] {team}: {count} of {len(todo)} games saved ({left} requests left this month)", flush=True)
            if left != "?" and int(left) <= KEEP_CALLS:
                print("Stopping: nearly out of requests for the month.", flush=True)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    missing = [g for g in games.values() if not is_saved(g)]
    print("-" * 30)
    print(f"Games saved this run: {saved}")
    print(f"Games with plays saved: {len(games) - len(missing)} of {len(games)}")
    for g in sorted(missing, key=lambda g: g["date"])[:40]:
        print(f"   {g['date']}  {g['away']} at {g['home']}  (game {g['id']})")
    print("-" * 30)

if __name__ == "__main__":
    main()
