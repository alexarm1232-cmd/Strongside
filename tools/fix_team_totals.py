import os
import sys
import json
import time
import requests

# Sports Reference's team totals add up the players' rebounds only: rebounds credited to the team are left out, which
# makes offensive rebounding read low and possessions (and so tempo) read high. Where the NCAA has a box score for the
# game, this puts the NCAA's team totals (which count team rebounds) into the box scores 8srboxscores.py built, and
# keeps the Sports Reference player lines. It also saves the NCAA version in boxscores_ncaa, as the newer seasons have.
#     python tools/fix_team_totals.py 2324            add  test  to try the first few games and change nothing
# It can be stopped and run again: a game that is already done is skipped.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
API_URL = "https://ncaa-api.henrygd.me/game/{}/boxscore"
DELAY_SECONDS = 0.4

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def ncaa_box(raw):
    """The NCAA's box score in our layout (the same as 4boxscorefetch.py writes)."""
    out = {"game_id": raw.get("instanceId"), "game_info": raw.get("description", ""), "teams": []}
    names = {str(t.get("teamId")): t.get("nameShort", "") for t in raw.get("teams", [])}
    for entry in raw.get("teamBoxscore", []):
        line = lambda s: {
            "PTS": int(s.get("points") or 0),
            "FG": f"{s.get('fieldGoalsMade')}-{s.get('fieldGoalsAttempted')}",
            "3PT": f"{s.get('threePointsMade')}-{s.get('threePointsAttempted')}",
            "FT": f"{s.get('freeThrowsMade')}-{s.get('freeThrowsAttempted')}",
            "REB": int(s.get("totalRebounds") or 0), "AST": int(s.get("assists") or 0), "PF": int(s.get("personalFouls") or 0),
            "TO": int(s.get("turnovers") or 0), "OREB": int(s.get("offensiveRebounds") or 0), "DREB": int(s.get("defensiveRebounds") or 0),
            "STL": int(s.get("steals") or 0), "BLK": int(s.get("blockedShots") or 0)}
        team = {"team_name": names.get(str(entry.get("teamId")), ""), "starters_table": [], "bench_table": [], "team_totals": line(entry.get("teamStats") or {})}
        for p in entry.get("playerStats", []):
            row = dict(line(p), Name=f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(), MIN=p.get("minutesPlayed", "0"))
            team["starters_table" if p.get("isStarter") else "bench_table"].append(row)
        out["teams"].append(team)
    return out

def main():
    code = next((a for a in sys.argv[1:] if a not in ("test",)), None)
    test = "test" in sys.argv[1:]
    base = os.path.join(ROOT, "data/seasons/" + (code or ""))
    if not code or not os.path.isdir(base):
        print("Name a season, e.g.  python tools/fix_team_totals.py 2324")
        return
    games = {}      # game id -> the team folders that hold its box score
    for conf in sorted(os.listdir(base)):
        conf_path = os.path.join(base, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            box_dir = os.path.join(conf_path, team, "boxscores")
            if os.path.isdir(box_dir):
                for f in os.listdir(box_dir):
                    if f.endswith(".json"):
                        games.setdefault(f[:-5], []).append(os.path.join(conf_path, team))
    todo = [g for g, folders in games.items() if not all((read_json(os.path.join(f, "boxscores", g + ".json")) or {}).get("totals") for f in folders)]
    print(f"{len(games)} games; {len(todo)} still to do.", flush=True)
    fixed = no_box = mismatch = 0
    try:
        for n, game_id in enumerate(sorted(todo)[:8] if test else sorted(todo), 1):
            try:
                response = requests.get(API_URL.format(game_id), timeout=20)
                raw = response.json() if response.status_code == 200 else None
            except Exception:
                raw = None
            time.sleep(DELAY_SECONDS)
            ncaa = ncaa_box(raw) if raw else None
            if not ncaa or len(ncaa["teams"]) != 2 or not any(t["team_totals"]["REB"] for t in ncaa["teams"]):
                no_box += 1
                continue
            by_name = {t["team_name"].rstrip(". "): t for t in ncaa["teams"]}
            ok = True
            for folder in games[game_id]:
                path = os.path.join(folder, "boxscores", game_id + ".json")
                box = read_json(path)
                if not box: continue
                swaps = []
                for team in box["teams"]:
                    theirs = by_name.get(team["team_name"].rstrip(". "))
                    # only when it is plainly the same game: the same team name and the same points
                    if theirs and theirs["team_totals"]["PTS"] == team["team_totals"]["PTS"]:
                        swaps.append((team, theirs["team_totals"]))
                if len(swaps) != 2:
                    ok = False
                    continue
                if test:
                    for team, totals in swaps:
                        print(f"   {team['team_name']}: rebounds {team['team_totals']['REB']} -> {totals['REB']}, offensive {team['team_totals']['OREB']} -> {totals['OREB']}, "
                              f"shots {team['team_totals']['FG']} -> {totals['FG']}, turnovers {team['team_totals']['TO']} -> {totals['TO']}")
                    continue
                for team, totals in swaps:
                    team["team_totals"] = totals
                box["totals"] = "ncaa"      # where the team totals came from; the player lines are still Sports Reference's
                with open(path, "w", encoding="utf-8") as out:
                    json.dump(box, out, indent=4)
                backup = os.path.join(folder, "boxscores_ncaa")
                os.makedirs(backup, exist_ok=True)
                with open(os.path.join(backup, game_id + ".json"), "w", encoding="utf-8") as out:
                    json.dump(ncaa, out, indent=4)
            if ok: fixed += 1
            else: mismatch += 1
            if n % 250 == 0:
                print(f"[{n}/{len(todo)}] done {fixed}, no NCAA box score {no_box}, names or scores did not match {mismatch}", flush=True)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")
    print("-" * 30)
    print(f"Games given the NCAA's team totals: {fixed}")
    print(f"No NCAA box score: {no_box}   Names or scores did not match: {mismatch}")
    print("-" * 30)

if __name__ == "__main__":
    main()
