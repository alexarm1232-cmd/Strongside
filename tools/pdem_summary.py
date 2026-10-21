import os
import csv
import json
import statistics as st

# Summary numbers and chart data for the PDEM upset study, from reports/pdem_all_ncaa_tournament.csv
# (python tools/pdem.py all tournament):   python tools/pdem_summary.py
# The games looked at are the ones between seeds 4 or more lines apart; the margin is always the lower seed's
# (the bigger seed number). An upset is a game the lower seed won. Writes reports/pdem_summary.json.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
GAP = 4

def load():
    games = []
    with open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["seed_gap"] in ("", "0"): continue
            gap = abs(int(r["seed_gap"]))
            if gap < GAP: continue
            m = [int(r[f"m{i}"]) for i in range(int(r["minutes"]) + 1)]
            games.append({"season": r["season"], "date": r["date"], "round": r["round"], "upset": int(r["seed_gap"]) > 0,
                          "lower": int(max(int(r["winner_seed"]), int(r["loser_seed"]))), "higher": int(min(int(r["winner_seed"]), int(r["loser_seed"]))),
                          "winner": r["winner"], "loser": r["loser"], "score": f'{r["winner_pts"]}-{r["loser_pts"]}', "m": m})
    return games

def at(g, minute):
    return g["m"][min(minute, len(g["m"]) - 1)]

def main():
    games = load()
    ups = [g for g in games if g["upset"]]
    holds = [g for g in games if not g["upset"]]
    out = {"games": len(games), "upsets": len(ups), "holds": len(holds)}
    # the average path: minutes 0-40, regulation only
    avg = lambda gs: [round(st.mean(at(g, i) for g in gs), 2) for i in range(41)]
    out["avg_path"] = {"upsets": avg(ups), "holds": avg(holds)}
    # where the lower seed stood at the half, at minute 30 and with 5 minutes left
    def standing(gs, minute):
        v = [at(g, minute) for g in gs]
        return {"ahead": sum(x > 0 for x in v), "level": sum(x == 0 for x in v), "behind": sum(x < 0 for x in v), "n": len(v)}
    out["standing"] = {f"m{k}": {"upsets": standing(ups, k), "holds": standing(holds, k)} for k in (10, 20, 30, 35)}
    # if the lower seed is ahead at minute k, how often does it win? (the base rate the upsets are drawn from)
    def win_rate_when(minute, cond):
        sel = [g for g in games if cond(at(g, minute))]
        return {"n": len(sel), "won": sum(g["upset"] for g in sel)}
    out["win_when"] = {f"m{k}": {"ahead": win_rate_when(k, lambda x: x > 0), "level": win_rate_when(k, lambda x: x == 0),
                                 "behind_1_5": win_rate_when(k, lambda x: -5 <= x < 0), "behind_6_plus": win_rate_when(k, lambda x: x < -5)}
                       for k in (20, 30, 35)}
    # in the upsets: the biggest hole climbed out of, how much of the game was spent ahead, and when the lead was for good
    for g in ups:
        g["low"] = min(g["m"])
        g["share_ahead"] = sum(x > 0 for x in g["m"][1:]) / (len(g["m"]) - 1)
        last_not_ahead = max(i for i, x in enumerate(g["m"]) if x <= 0)
        g["for_good"] = last_not_ahead + 1           # the first minute from which the lower seed stayed ahead
    out["upset_low"] = {"median": st.median(g["low"] for g in ups), "trailed_10_plus": sum(g["low"] <= -10 for g in ups),
                        "never_trailed": sum(g["low"] >= 0 for g in ups)}
    out["upset_for_good"] = {"median": st.median(g["for_good"] for g in ups),
                             "last_5_min_or_ot": sum(g["for_good"] > 35 for g in ups), "first_half": sum(g["for_good"] <= 20 for g in ups)}
    out["upset_share_ahead"] = round(st.mean(g["share_ahead"] for g in ups), 3)
    out["comebacks"] = sorted(({"season": g["season"], "round": g["round"], "game": f'({g["lower"]}) {g["winner"]} over ({g["higher"]}) {g["loser"]}',
                                "score": g["score"], "low": g["low"]} for g in ups), key=lambda x: x["low"])[:6]
    # how big the margin swings: the average absolute change per minute
    swing = lambda gs: round(st.mean(st.mean(abs(g["m"][i + 1] - g["m"][i]) for i in range(40)) for gs_ in [gs] for g in gs_), 2)
    out["swing_per_minute"] = {"upsets": swing(ups), "holds": swing(holds)}
    # by round and by matchup
    by = {}
    for g in games:
        k = g["round"]
        by.setdefault(k, [0, 0])[0 if g["upset"] else 1] += 1
    out["by_round"] = by
    json.dump(out, open(os.path.join(REPORTS, "pdem_summary.json"), "w", encoding="utf-8"), indent=1)
    # the games themselves from the lower seed's side, for the charts: reports/pdem_seed_gap_4plus.csv
    most = max(len(g["m"]) for g in games) - 1
    with open(os.path.join(REPORTS, "pdem_seed_gap_4plus.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game", "season", "date", "round", "lower_seed", "lower_team", "higher_seed", "higher_team", "lower_won",
                    "lower_pts", "higher_pts", "minutes"] + [f"m{i}" for i in range(most + 1)])
        for g in sorted(games, key=lambda g: g["date"]):
            lower_team, higher_team = (g["winner"], g["loser"]) if g["upset"] else (g["loser"], g["winner"])
            wp, lp = (int(x) for x in g["score"].split("-"))
            lower_pts, higher_pts = (wp, lp) if g["upset"] else (lp, wp)
            w.writerow([f'{g["date"]} {lower_team} v {higher_team}', g["season"], g["date"], g["round"], g["lower"], lower_team,
                        g["higher"], higher_team, "yes" if g["upset"] else "no", lower_pts, higher_pts, len(g["m"]) - 1]
                       + g["m"] + [""] * (most + 1 - len(g["m"])))
    print(json.dumps({k: v for k, v in out.items() if k != "avg_path"}, indent=1))
    print("avg path upsets (every 5 min):", out["avg_path"]["upsets"][::5])
    print("avg path holds  (every 5 min):", out["avg_path"]["holds"][::5])

if __name__ == "__main__":
    main()
