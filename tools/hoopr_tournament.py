import os
import sys
import csv
import gzip
import json
from datetime import datetime, timedelta

# The NCAA tournament games of the seasons built from hoopR (tools/build_from_hoopr.py), in the layout of
# reports/tournament_spreads.csv, so dashboard/Tourneystat.py can set them up for the simulator:
#     python tools/hoopr_tournament.py 0809 0708
# Writes reports/tournament_games_hoopr.csv. There are no betting lines for these seasons (BetIQ's start in 2010):
# favorite, spread, total and money line are left blank, and seeds too (the simulator does not use them).
# A game is one ESPN tags as the NCAA tournament (tournament id 22) that is on our full-season game list; ESPN's game
# id is our game id for these seasons. The round comes from the date.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports", "tournament_games_hoopr.csv")
# season code -> (hoopR season, the first day of the round of 64)
SEASONS = {"0506": (2006, "2006/03/16"), "0607": (2007, "2007/03/15"), "0708": (2008, "2008/03/20"), "0809": (2009, "2009/03/19")}
COLUMNS = ["season", "date", "round", "game_id", "winner", "winner_seed", "loser", "loser_seed", "score", "favorite", "spread", "total",
           "money_line", "lower_seed_line"]

def round_of(day, r64):
    d = (datetime.strptime(day, "%Y/%m/%d") - datetime.strptime(r64, "%Y/%m/%d")).days
    return ("Opening round" if d < 0 else "First round" if d <= 1 else "Second round" if d <= 3 else "Sweet 16" if d <= 8
            else "Elite Eight" if d <= 10 else "Final Four" if d <= 17 else "Championship")

def main():
    codes = [a for a in sys.argv[1:] if a in SEASONS]
    if not codes:
        print("Name the seasons, e.g.  python tools/hoopr_tournament.py 0809 0708"); return
    rows = []
    if os.path.exists(OUT):
        rows = [r for r in csv.DictReader(open(OUT, encoding="utf-8")) if r["season"] not in {f"20{c[:2]}-{c[2:]}" for c in codes}]
    for code in codes:
        year, r64 = SEASONS[code]; label = f"20{code[:2]}-{code[2:]}"
        tour = {r["id"] for r in csv.DictReader(gzip.open(os.path.join(ROOT, "data", "hoopr", str(year), "schedule.csv.gz"), "rt", encoding="utf-8"))
                if r["season_type"] == "3" and r["tournament_id"] == "22"}
        games = {}
        base = os.path.join(ROOT, "data", "seasons", code + " full")
        for conf in os.listdir(base):
            for team in os.listdir(os.path.join(base, conf)) if os.path.isdir(os.path.join(base, conf)) else []:
                path = os.path.join(base, conf, team, "game_scores.json")
                if os.path.exists(path):
                    for g in json.load(open(path, encoding="utf-8")):
                        if str(g["game_id"]) in tour: games[str(g["game_id"])] = g
        for gid, g in sorted(games.items(), key=lambda kv: kv[1]["date"]):
            hs, as_ = int(g["home_score"]), int(g["away_score"])
            w, l = (g["home_team"], g["away_team"]) if hs > as_ else (g["away_team"], g["home_team"])
            rows.append({"season": label, "date": g["date"], "round": round_of(g["date"], r64), "game_id": gid, "winner": w, "winner_seed": "",
                         "loser": l, "loser_seed": "", "score": f"{max(hs, as_)}-{min(hs, as_)}", "favorite": "", "spread": "", "total": "",
                         "money_line": "", "lower_seed_line": ""})
        print(f"{label}: {len(games)} tournament games of the {len(tour)} ESPN lists")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
