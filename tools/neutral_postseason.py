import os
import sys
import json
from datetime import datetime

# Marks every postseason game (after Selection Sunday: the NCAA tournament, the NIT and the other events) as played on
# a neutral floor, in every season's game lists:
#     python tools/neutral_postseason.py            every season
#     python tools/neutral_postseason.py 1213 1112  only these
# The arena-based guess in ncaa_stats_season.py missed many of them (a team that played two tournament games at one
# site had that arena counted as a home court), so the ratings gave the "home" team an edge it did not have. Rebuild
# the pages afterwards (dashboard/main.py), since the ratings change. ncaa_stats_season.py now does the same itself.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SEASONS_DIR = os.path.join(ROOT, "data", "seasons")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ncaa_stats_season import SEASONS as SELECTION        # code -> (label, Selection Sunday)

def main():
    codes = [a for a in sys.argv[1:] if a.isdigit()] or sorted(c for c in os.listdir(SEASONS_DIR) if c.isdigit() and c in SELECTION)
    for code in codes:
        sunday = SELECTION[code][1].strftime("%Y/%m/%d")
        changed, games = 0, set()
        for folder in (code, code + " full"):
            base = os.path.join(SEASONS_DIR, folder)
            if not os.path.isdir(base): continue
            for conf in os.listdir(base):
                conf_path = os.path.join(base, conf)
                if not os.path.isdir(conf_path): continue
                for team in os.listdir(conf_path):
                    path = os.path.join(conf_path, team, "game_scores.json")
                    if not os.path.exists(path): continue
                    with open(path, encoding="utf-8") as f:
                        rows = json.load(f)
                    fixed = 0
                    for r in rows:
                        if r.get("date", "") > sunday and not r.get("neutral"):
                            r["neutral"] = True
                            fixed += 1
                            games.add(str(r.get("game_id")))
                    if fixed:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(rows, f, indent=4)
                        changed += 1
        print(f"{code}: {len(games)} postseason games now neutral ({changed} team files changed)")

if __name__ == "__main__":
    main()
