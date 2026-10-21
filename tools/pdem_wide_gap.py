import os
import csv
import pdem_ratings

# Tournament games between seeds fewer than 4 lines apart where the teams were still far apart going in: a net-rating
# gap of 10+ or a closing line of 7+ points.   python tools/pdem_wide_gap.py
# Reads reports/tournament_games_model.csv (tools/pdem_ratings.py) and reports/pdem_all_ncaa_tournament.csv (tools/pdem.py)
# and writes reports/pdem_wide_gap.csv: one row per game from the lower seed's side (the winner's when the seeds are
# equal, as in the PDEM files), with both teams' net ratings going in, the closing line, the score, whether it was an
# upset (different seeds and the lower seed won; equal seeds never are) and the margin after each minute, m0-m50.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
NET_WIDE, LINE_WIDE = 10, 7

def main():
    nets = pdem_ratings.ratings_going_in()
    pdem = {}
    for p in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")):
        pdem[(p["date"], frozenset((p["winner"], p["loser"])))] = p
    rows = []
    for g in csv.DictReader(open(os.path.join(REPORTS, "tournament_games_model.csv"), encoding="utf-8")):
        if float(g["seed_gap"]) >= 4 or (abs(float(g["net_gap"])) < NET_WIDE and abs(float(g["line"])) < LINE_WIDE):
            continue
        p = pdem[(g["date"], frozenset((g["lower_team"], g["higher_team"])))]
        lower_won = g["lower_won"] == "1"
        lo_pts, hi_pts = (p["winner_pts"], p["loser_pts"]) if lower_won else (p["loser_pts"], p["winner_pts"])
        side = next(c for c in nets[(g["date"].replace("/", "-"), min(int(lo_pts), int(hi_pts)), max(int(lo_pts), int(hi_pts)))]
                    if c[0] == p["winner"] or c[2] == p["winner"])
        net = {side[0]: side[1], side[2]: side[3]}
        row = {"game": f'{g["date"]} {g["lower_team"]} v {g["higher_team"]}', "season": g["season"], "date": g["date"], "round": g["round"],
               "lower_seed": g["lower_seed"], "lower_team": g["lower_team"], "higher_seed": g["higher_seed"], "higher_team": g["higher_team"],
               "lower_pts": lo_pts, "higher_pts": hi_pts, "minutes": p["minutes"],
               "lower_net": net.get(g["lower_team"]), "higher_net": net.get(g["higher_team"]), "net_gap": g["net_gap"],
               "line": g["line"], "upset": "yes" if lower_won and g["seed_gap"] != "0" else "no"}
        row.update({f"m{i}": p[f"m{i}"] for i in range(51)})
        rows.append(row)
    rows.sort(key=lambda r: r["date"])
    with open(os.path.join(REPORTS, "pdem_wide_gap.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} games, {sum(r['upset'] == 'yes' for r in rows)} upsets")
    # the upset tracker's games: every game between seeds 4+ lines apart (tools/pdem_summary.py) and these, which the
    # tracker counts in its upsets too, marked by "kind"
    four = list(csv.DictReader(open(os.path.join(REPORTS, "pdem_seed_gap_4plus.csv"), encoding="utf-8")))
    cols = list(four[0]) + ["kind"]
    with open(os.path.join(REPORTS, "pdem_upset_games.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({**r, "kind": "Seed gap 4+"} for r in four)
        w.writerows({**{c: r.get(c, "") for c in cols}, "lower_won": "yes" if int(r["lower_pts"]) > int(r["higher_pts"]) else "no",
                     "kind": "Wide gap"} for r in rows)
    print(f"{len(four) + len(rows)} games for the upset tracker")

if __name__ == "__main__":
    main()
