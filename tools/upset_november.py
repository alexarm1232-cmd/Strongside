import os
import csv
import glob
import pdem_ratings

# November records of the higher seeds in tournament games between seeds 4+ lines apart:   python tools/upset_november.py
# For every such game 2010-2026 (First Four left out), the higher seed's wins and losses in November of that season,
# from its schedule on the season's pre-tournament page, and whether it was upset. Writes reports/upset_november.csv.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
PAGES = os.path.join(ROOT, "dashboard")

def schedules():
    """season -> team -> its games"""
    out = {}
    for path in [os.path.join(PAGES, "dashboard.html")] + glob.glob(os.path.join(PAGES, "dashboard_*.html")):
        if path.endswith(("_full.html", "_template.html", "upsets.html")): continue
        data = pdem_ratings.page_data(path)
        out[data["meta"]["season"]] = {t["name"]: t.get("sched", []) for t in data["teams"]}
    return out

def main():
    sched = schedules()
    rows = []
    for s in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8")):
        if s["round"] == "First Four" or not s["seed_gap"] or abs(int(s["seed_gap"])) < 4: continue     # seed_gap is winner minus loser
        ws, ls = int(s["winner_seed"]), int(s["loser_seed"])
        upset = ws > ls
        high = s["loser"] if upset else s["winner"]
        games = [g for g in sched.get(s["season"], {}).get(high, []) if g["d"][5:7] == "11"]
        w = sum(g["pf"] > g["pa"] for g in games)
        rows.append({"season": s["season"], "date": s["date"], "round": s["round"], "high_seed": min(ws, ls), "high_team": high,
                     "low_seed": max(ws, ls), "low_team": s["winner"] if upset else s["loser"], "upset": "yes" if upset else "no",
                     "nov_wins": w, "nov_losses": len(games) - w})
    with open(os.path.join(REPORTS, "upset_november.csv"), "w", encoding="utf-8", newline="") as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)
    for kind in ("yes", "no"):
        sel = [r for r in rows if r["upset"] == kind]
        w, l = sum(r["nov_wins"] for r in sel), sum(r["nov_losses"] for r in sel)
        print(f"{'upset' if kind == 'yes' else 'held'}: {len(sel)} games, higher seeds {w}-{l} in November ({w / (w + l):.1%}),"
              f" {sum(r['nov_losses'] == 0 for r in sel)} unbeaten in November, no November games: {sum(r['nov_wins'] + r['nov_losses'] == 0 for r in sel)}")

if __name__ == "__main__":
    main()
