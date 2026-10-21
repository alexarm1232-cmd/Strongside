import os
import csv
import glob
import difflib

# Closing spreads for every NCAA tournament game, matched to the PDEM games:   python tools/tournament_spreads.py
# The lines come from BetIQ's custom trend tool (betiq.teamrankings.com, game type "NCAA Tournament"), saved in
# data/betiq/ncaa_tournament_lines_*.tsv, one row per game from the favorite's side:
#     date, team, opponent, site (N/H/A), spread, total, money line, score (team's points first)
# A game is matched to ours by its date and final score (the two scores, either order), which is unique within a day.
# Writes reports/tournament_spreads.csv: each of our tournament games with BetIQ's names, the favorite, the spread,
# total and money line, and the spread from the lower seed's side ("lower_seed_line": +5.5 means the lower seed was
# getting 5.5 points; minus means the lower seed was the favorite).

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")

def lines():
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "betiq", "ncaa_tournament_lines_*.tsv"))):
        for row in csv.reader(open(path, encoding="utf-8"), delimiter="\t"):
            if len(row) < 8: continue
            date, team, opp, site, spread, total, ml, score = row[:8]
            a, b = (int(x) for x in score.split("-"))
            key = (date, tuple(sorted((a, b))))
            out.setdefault(key, []).append({"team": team, "opp": opp, "site": site, "spread": float(spread), "total": total, "ml": ml, "pts": a, "opp_pts": b})
    return out

def name_match(ours, theirs):
    """How alike our name and BetIQ's are (they abbreviate differently: "South Fla." / "S Florida")."""
    clean = lambda s: s.lower().replace(".", "").replace("state", "st").replace("saint", "st").split()
    a, b = clean(ours), clean(theirs)
    return difflib.SequenceMatcher(None, " ".join(a), " ".join(b)).ratio() + (0.5 if a and b and a[0][:3] == b[0][:3] else 0)

def pick(candidates, winner, loser):
    """Where two games on a day ended with the same score, the one whose teams' names fit ours."""
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=lambda c: max(name_match(winner, c["team"]) + name_match(loser, c["opp"]),
                                             name_match(winner, c["opp"]) + name_match(loser, c["team"])))

def main():
    betiq = lines()
    games = list(csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")))
    rows, missing = [], []
    for g in games:
        date = g["date"].replace("/", "-")
        wp, lp = int(g["winner_pts"]), int(g["loser_pts"])
        found = betiq.get((date, tuple(sorted((wp, lp)))))
        b = pick(found, g["winner"], g["loser"]) if found else None
        if found and len(found) > 1:
            print(f"   {g['date']} {g['winner']} {wp}-{lp} {g['loser']}: two games with that score; took {b['team']} v {b['opp']}")
        if not b:
            missing.append(f'{g["date"]} {g["winner"]} {wp}-{lp} {g["loser"]}')
            continue
        # which of our teams BetIQ's favorite is: the one with its points
        fav_won = b["pts"] == wp if wp != lp else None
        favorite = g["winner"] if fav_won else g["loser"]
        underdog = g["loser"] if fav_won else g["winner"]
        gap = g["seed_gap"]
        lower_seed_won = gap not in ("", "0") and int(gap) > 0
        lower_team = g["winner"] if lower_seed_won else (g["loser"] if gap not in ("", "0") else "")
        # the lower seed's line: the favorite gives the spread, so the underdog's line is its negative
        lower_line = "" if not lower_team else (b["spread"] if lower_team == favorite else -b["spread"])
        rows.append({"season": g["season"], "game_id": g["game_id"], "date": g["date"], "round": g["round"],
                     "winner": g["winner"], "winner_seed": g["winner_seed"], "loser": g["loser"], "loser_seed": g["loser_seed"],
                     "seed_gap": gap, "score": f"{wp}-{lp}", "favorite": favorite, "underdog": underdog,
                     "spread": b["spread"], "total": b["total"], "favorite_money_line": b["ml"],
                     "favorite_won": "yes" if fav_won else "no", "lower_seed_line": lower_line,
                     "betiq_favorite": b["team"], "betiq_underdog": b["opp"]})
    with open(os.path.join(REPORTS, "tournament_spreads.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} of {len(games)} tournament games matched to a BetIQ line")
    if missing:
        print(f"   not matched ({len(missing)}): {missing[:10]}")
    print("   reports/tournament_spreads.csv")

if __name__ == "__main__":
    main()
