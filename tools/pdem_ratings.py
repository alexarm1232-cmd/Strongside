import os
import re
import csv
import json
import glob

# The two teams' net ratings going into each NCAA tournament game, from the built full-season pages (each schedule
# game carries "nt", the team's net rating from the games before that day, and "no", the opponent's):
#     python tools/pdem_ratings.py
# Matched to reports/tournament_spreads.csv by date and final score, and written beside the spread as
# reports/tournament_games_model.csv: one row per tournament game outside the First Four, from the lower seed's side
# (the bigger seed number; the winner's side when the seeds are equal), with the seed gap, the net-rating gap going in,
# the closing line, the margin at halftime, with 10 and 5 minutes left, the final margin and whether it won.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
PAGES = os.path.join(ROOT, "dashboard")

def page_data(path):
    text = open(path, encoding="utf-8").read()
    at = text.index("const DATA = ") + len("const DATA = ")
    return json.loads(text[at:text.index("\n", at)].rstrip().rstrip(";"))

def ratings_going_in():
    """(date, low score, high score) -> [(team, its net going in, opponent, opponent's net going in, points for, against)]"""
    out = {}
    for path in [os.path.join(PAGES, "dashboard_full.html")] + glob.glob(os.path.join(PAGES, "dashboard_*_full.html")):
        if not os.path.exists(path): continue
        for t in page_data(path)["teams"]:
            for g in t.get("sched", []):
                key = (g["d"].replace("/", "-"), min(g["pf"], g["pa"]), max(g["pf"], g["pa"]))
                out.setdefault(key, []).append((t["name"], g.get("nt"), g["opp"], g.get("no"), g["pf"], g["pa"]))
    return out

def main():
    nets = ratings_going_in()
    pdem = {r["game_id"]: r for r in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8"))}
    rows, unmatched = [], 0
    for s in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8")):
        if s["round"] == "First Four": continue
        wp, lp = (int(x) for x in s["score"].split("-"))
        ws, ls = int(s["winner_seed"]), int(s["loser_seed"])
        lower_won = ws > ls or ws == ls
        lower, higher = (s["winner"], s["loser"]) if lower_won else (s["loser"], s["winner"])
        cands = nets.get((s["date"].replace("/", "-"), lp, wp), [])
        clean = lambda n: re.sub(r"[^a-z0-9]", "", n.lower())
        mine = next((c for c in cands if clean(c[0]) == clean(lower)), None) or next((c for c in cands if clean(c[2]) == clean(higher)), None)
        if mine is None:
            # the entry from the other team's side
            other = next((c for c in cands if clean(c[0]) == clean(higher)), None)
            mine = (lower, other[3], higher, other[1], other[5], other[4]) if other else None
        if mine is None or mine[1] is None or mine[3] is None:
            unmatched += 1
            continue
        p = pdem[s["game_id"]]
        m = [int(p[f"m{i}"]) for i in range(int(p["minutes"]) + 1)]
        sign = 1 if p["lower_seed_won"] in ("yes", "") and lower_won or (p["lower_seed_won"] == "no" and not lower_won) else -1
        # the PMPM file is already from the lower seed's side where the seeds differ, from the winner's where equal
        at = lambda i: m[min(i, len(m) - 1)]
        line = float(s["lower_seed_line"]) if s["lower_seed_line"] != "" else (float(s["spread"]) if s["favorite"] == lower else -float(s["spread"]))
        rows.append({"season": s["season"], "date": s["date"], "round": s["round"], "lower_team": lower, "higher_team": higher,
                     "lower_seed": max(ws, ls), "higher_seed": min(ws, ls), "seed_gap": abs(ws - ls),
                     "net_gap": round(mine[1] - mine[3], 1),                  # lower seed's net minus the higher seed's, going in
                     "line": line, "m20": at(20), "m30": at(30), "m35": at(35),
                     "final": (wp - lp) if lower_won else (lp - wp), "lower_won": 1 if lower_won else 0})
    with open(os.path.join(REPORTS, "tournament_games_model.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} games with ratings going in ({unmatched} without)")

if __name__ == "__main__":
    main()
