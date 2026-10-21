import os
import csv
import json
import math
import numpy as np

# What predicts tournament results, and how games followed the closing line:   python tools/pdem_models.py
# Reads reports/tournament_games_model.csv (tools/pdem_ratings.py): every tournament game outside the First Four from
# the lower seed's side. Writes reports/pdem_models.json and prints the tables.
#  1. Wins: logistic models of "did the lower seed win" from the seed gap, the net-rating gap going in, the closing
#     line, and the margin at halftime / with 10 minutes left, alone and together. Each is fitted with one tournament
#     held out at a time and scored on that tournament (log loss, Brier score, share called right), so no model is
#     scored on games it learned from.
#  2. Do upsets come from rating gaps the seeds hide? Upset rate by seed gap against by net-rating gap.
#  3. The line as a path: the closing line implies a straight path from 0 to minus the line at minute 40; how the
#     real games compare, and whether being ahead of that path at halftime carries through.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")

def fit(X, y, l2=1e-3, steps=50):
    X = np.column_stack([np.ones(len(X)), X])
    b = np.zeros(X.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-X @ b))
        g = X.T @ (p - y) + l2 * np.r_[0, b[1:]]
        H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.diag(np.r_[0, np.ones(len(b) - 1)])
        b -= np.linalg.solve(H, g)
    return b

def predict(b, X):
    return 1 / (1 + np.exp(-np.column_stack([np.ones(len(X)), X]) @ b))

def held_out(rows, cols):
    seasons = sorted({r["season"] for r in rows})
    p_all, y_all = [], []
    for s in seasons:
        train = [r for r in rows if r["season"] != s]
        test = [r for r in rows if r["season"] == s]
        X = np.array([[r[c] for c in cols] for r in train], float)
        b = fit(X, np.array([r["lower_won"] for r in train], float))
        p_all += list(predict(b, np.array([[r[c] for c in cols] for r in test], float)))
        y_all += [r["lower_won"] for r in test]
    p, y = np.clip(np.array(p_all), 1e-6, 1 - 1e-6), np.array(y_all)
    return {"log_loss": round(float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), 4),
            "brier": round(float(np.mean((p - y) ** 2)), 4), "right": round(float(np.mean((p > 0.5) == (y == 1))), 4)}

def main():
    rows = []
    for r in csv.DictReader(open(os.path.join(REPORTS, "tournament_games_model.csv"), encoding="utf-8")):
        for k in ("seed_gap", "net_gap", "line", "m20", "m30", "m35", "final", "lower_won"):
            r[k] = float(r[k])
        rows.append(r)
    games = [r for r in rows if r["seed_gap"] > 0]          # a lower seed to speak of
    out = {"games": len(games), "upsets_4plus": sum(1 for r in games if r["seed_gap"] >= 4 and r["lower_won"])}

    # 1. what predicts the lower seed winning
    models = [("Seed gap", ["seed_gap"]), ("Net-rating gap going in", ["net_gap"]), ("Closing line", ["line"]),
              ("Seed gap + net-rating gap", ["seed_gap", "net_gap"]), ("Net-rating gap + line", ["net_gap", "line"]),
              ("Halftime margin", ["m20"]), ("Net-rating gap + halftime margin", ["net_gap", "m20"]),
              ("Line + halftime margin", ["line", "m20"]), ("Line + margin, 10 min left", ["line", "m30"])]
    out["models"] = [{"model": name, **held_out(games, cols)} for name, cols in models]
    base = np.mean([r["lower_won"] for r in games])
    out["base_rate"] = round(float(base), 4)
    out["base_log_loss"] = round(float(-(base * math.log(base) + (1 - base) * math.log(1 - base))), 4)

    # 2. upsets by seed gap and by rating gap, among games 4+ seed lines apart
    four = [r for r in games if r["seed_gap"] >= 4]
    def rate(sel): return {"games": len(sel), "won": int(sum(r["lower_won"] for r in sel)),
                           "rate": round(sum(r["lower_won"] for r in sel) / len(sel), 3) if sel else None}
    out["by_net_gap"] = [{"band": band, **rate([r for r in four if test(r["net_gap"])])} for band, test in [
        ("Lower seed rated higher", lambda v: v > 0), ("0 to 5 worse", lambda v: -5 <= v <= 0), ("5 to 10 worse", lambda v: -10 <= v < -5),
        ("10 to 15 worse", lambda v: -15 <= v < -10), ("15 to 20 worse", lambda v: -20 <= v < -15), ("More than 20 worse", lambda v: v < -20)]]
    ups, holds = [r for r in four if r["lower_won"]], [r for r in four if not r["lower_won"]]
    med = lambda v: float(np.median(v))
    out["net_gap_median"] = {"upsets": med([r["net_gap"] for r in ups]), "holds": med([r["net_gap"] for r in holds])}
    out["upsets_rated_higher"] = sum(1 for r in ups if r["net_gap"] > 0)
    out["upsets_line_underdog"] = sum(1 for r in ups if r["line"] > 0)
    out["corr_net_gap_line"] = round(float(np.corrcoef([r["net_gap"] for r in games], [r["line"] for r in games])[0, 1]), 3)

    # 3. the line as a path: expected margin at minute m is -line * m / 40
    def vs_line(sel):
        half = [r["m20"] + r["line"] / 2 for r in sel]            # ahead (+) or behind (-) the line's path at halftime
        end = [r["final"] + r["line"] for r in sel]               # beat (+) or fell short of (-) the line at the end
        return {"games": len(sel), "half_vs_line": round(float(np.mean(half)), 2), "final_vs_line": round(float(np.mean(end)), 2),
                "covered": round(float(np.mean([e > 0 for e in end])), 3), "corr_half_final": round(float(np.corrcoef(half, end)[0, 1]), 3)}
    out["vs_line"] = {"all": vs_line(games), "upsets": vs_line(ups), "seed_4plus": vs_line(four)}
    # when the lower seed is ahead of the line's path at halftime, how often does it beat the line / win?
    ahead = [r for r in games if r["m20"] + r["line"] / 2 > 0]
    behind = [r for r in games if r["m20"] + r["line"] / 2 < 0]
    out["half_ahead_of_line"] = {"ahead": {"games": len(ahead), "covered": round(float(np.mean([r["final"] + r["line"] > 0 for r in ahead])), 3),
                                          "won": round(float(np.mean([r["lower_won"] for r in ahead])), 3)},
                                 "behind": {"games": len(behind), "covered": round(float(np.mean([r["final"] + r["line"] > 0 for r in behind])), 3),
                                            "won": round(float(np.mean([r["lower_won"] for r in behind])), 3)}}
    json.dump(out, open(os.path.join(REPORTS, "pdem_models.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
