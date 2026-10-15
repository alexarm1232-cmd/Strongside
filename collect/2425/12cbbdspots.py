import os
import sys
import json
import re
import requests
import time
from collections import defaultdict

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2425"
SEASON = 2025                   # 2025 = the 2024-25 season
SHOTS_FOLDER = "shots"          # made by 9espnshots.py; each file there carries the game's ESPN id
TEAM_IDS_FILE = os.path.join(BASE_DIR, "espn_teams.json")      # our team name -> ESPN's team id (made by 9espnshots.py)
SCHOOLS_FILE = os.path.join(BASE_DIR, "cbbd_schools.json")     # our team name -> their school name, kept so it is only asked for once
TRIED_FILE = os.path.join(BASE_DIR, "cbbd_spots_tried.json")   # teams already asked for; delete it to ask for them again
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cbbd_key.txt")   # your CollegeBasketballData.com API key
API = "https://api.collegebasketballdata.com"
KEEP_CALLS = 25                 # stop before the month's allowance runs out, leaving this many calls
ENOUGH = 0.8                    # a game counts as having shot spots when this share of its shots do (the dashboard's own rule)

# ESPN's play-by-play has no shot spots for 2024-25 games before about February 11, 2025. CollegeBasketballData.com
# has them for the whole season. This fills the missing x and y into the shot files 9espnshots.py saved; nothing else
# in a file is touched, and a shot that already has a spot keeps it.
#
# One request returns every shot in every game a team played, both teams' shots. So a game is covered by asking for
# either of its two teams, and the teams are asked for in the order that covers the most missing games first: far
# fewer requests than one per team. It can be stopped and run again; it picks up where it left off.
#     python "collect/2425\12cbbdspots.py"            fill what is missing
#     python "collect/2425\12cbbdspots.py" count      only say how many requests it would take

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data, **how):
    with open(path, "w", encoding="utf-8") as out:
        json.dump(data, out, **how)

def is_free_throw(shot):
    return "free" in str(shot[4]).lower()

def has_spots(shots):
    tries = [s for s in shots if not is_free_throw(s)]
    return bool(tries) and sum(1 for s in tries if s[7] is not None and s[8] is not None) >= ENOUGH * len(tries)

def load_our_games():
    """ESPN game id -> our game id, teams, date and the shot files that hold it; only games still missing shot spots."""
    games, total = {}, set()
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
                total.add(f)
                if has_spots(data.get("shots") or []): continue
                game = games.setdefault(str(data["espn_id"]), {"id": f[:-5], "home": data["home_team"], "away": data["away_team"],
                                                               "date": data.get("date", ""), "files": []})
                game["files"].append(path)
    return games, len(total)

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

def main():
    count_only = "count" in sys.argv[1:]
    games, total = load_our_games()
    print(f"{total} games have a shot file; {len(games)} of them are missing shot spots.", flush=True)
    if not games:
        return
    team_ids = read_json(TEAM_IDS_FILE, {})
    tried = set(read_json(TRIED_FILE, []))
    by_team = defaultdict(set)      # our team name -> the ESPN ids of its games still missing spots
    for espn_id, game in games.items():
        for name in (game["home"], game["away"]):
            by_team[name.rstrip(". ")].add(espn_id)

    def order(schools):             # the teams to ask for, most missing games covered first
        left, picked = set(games), []
        open_teams = {t for t in by_team if t in schools and t not in tried}
        while left and open_teams:
            best = max(open_teams, key=lambda t: (len(by_team[t] & left), t))
            if not by_team[best] & left: break
            picked.append(best)
            left -= by_team[best]
            open_teams.discard(best)
        return picked, left

    key = open(KEY_FILE, encoding="utf-8").read().strip() if os.path.exists(KEY_FILE) else ""
    if not key and not count_only:
        print(f"Put your CollegeBasketballData.com API key in {KEY_FILE} first.")
        return
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    schools = read_json(SCHOOLS_FILE)
    if not schools:
        if count_only and not key:
            schools = {t: t for t in by_team}
        else:
            response = requests.get(API + "/teams", params={"season": SEASON}, headers=headers, timeout=60)
            if response.status_code != 200:
                print(f"Could not read the team list ({response.status_code}): {response.text[:200]}")
                return
            ours_by_espn = {str(espn_id): name for name, espn_id in team_ids.items()}
            schools = {ours_by_espn[str(t.get("sourceId"))].rstrip(". "): t["school"] for t in response.json() if str(t.get("sourceId")) in ours_by_espn}
            write_json(SCHOOLS_FILE, schools, indent=1, sort_keys=True)

    picked, unreachable = order(schools)
    print(f"{len(picked)} requests would cover {len(games) - len(unreachable)} of the {len(games)} games"
          + (f"; {len(unreachable)} have no team left to ask" if unreachable else "") + ".", flush=True)
    if count_only:
        return

    done = set()
    saved = shots_filled = 0
    try:
        for n, team in enumerate(picked, 1):
            todo = by_team[team] - done
            if not todo: continue
            try:
                response = requests.get(API + "/plays/team", params={"season": SEASON, "team": schools[team], "shootingPlaysOnly": "true"},
                                        headers=headers, timeout=300)
            except Exception as e:
                print(f"[{n}/{len(picked)}] {team}: request failed ({e}) - will retry next run", flush=True)
                time.sleep(10)
                continue
            left = response.headers.get("X-CallLimit-Remaining", "?")
            if response.status_code != 200:
                print(f"[{n}/{len(picked)}] {team}: refused ({response.status_code}) {response.text[:120]}", flush=True)
                if response.status_code in (401, 403, 429): break
                continue
            by_game = defaultdict(list)
            for p in response.json():
                by_game[str(p.get("gameSourceId"))].append(p)
            count = 0
            for espn_id in sorted(todo):
                plays = by_game.get(espn_id)
                if not plays: continue
                good = False
                for path in games[espn_id]["files"]:
                    data = read_json(path)
                    if not data: continue
                    filled = fill(data, plays)
                    if filled:
                        data["spots"] = "cbbd"          # where the spots came from; the rest of the file is still ESPN's
                        write_json(path, data, separators=(",", ":"))
                        shots_filled += filled
                    good = good or has_spots(data["shots"])
                if good:
                    done.add(espn_id)
                    count += 1
            saved += count
            tried.add(team)
            write_json(TRIED_FILE, sorted(tried))
            print(f"[{n}/{len(picked)}] {team}: {count} of {len(todo)} games filled ({left} requests left this month)", flush=True)
            if left != "?" and int(left) <= KEEP_CALLS:
                print("Stopping: nearly out of requests for the month. Run it again when the allowance resets.", flush=True)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    still, total = load_our_games()
    print("-" * 30)
    print(f"Games filled this run: {saved}  ({shots_filled} shots given a spot)")
    print(f"Games with shot spots: {total - len(still)} of {total}")
    print(f"Games still missing them: {len(still)}")
    for g in sorted(still.values(), key=lambda g: g["date"])[:40]:
        print(f"   {g['date']}  {g['away']} at {g['home']}  (game {g['id']})")
    print("-" * 30)

if __name__ == "__main__":
    main()
