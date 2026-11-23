import os, sys, json, shutil, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from m210_followups import F, rows, y, n, seas, U, ridge, auc, zc, col
import m99_model_types as Q
W = Q.WT[[r["i"] for r in rows]]; early = np.array([int(s[:4]) < 2018 for s in seas])
NEW = U + ["H orb"]
def full(ins):
    X = np.column_stack([col(c) for c in ins]); p = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; p[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    return p, int(((f >= .4) == (y[~early] == 1)).sum()), int(((b >= .4) == (y[early] == 1)).sum()), X
p28, f28, b28, _ = full(U); p29, f29, b29, X = full(NEW)
for lab, p, f, b in (("locked 28", p28, f28, b28), ("28 + H orb (29)", p29, f29, b29)):
    print(f"{lab:16} held out {int(((p >= .4) == (y == 1)).sum())}/511 | AUC {auc(p, y):.3f} | forward {f}/255 | backward {b}/288 | fwd+back {f + b}/543 | upset picks {int((p >= .4).sum())} ({int(((p >= .4) & (y == 1)).sum())} hit)")
# weight of H orb in the full fit
mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(n)]); bb = np.zeros(A.shape[1]); P = 30 * np.eye(A.shape[1]); P[-1, -1] = 0
for _ in range(60):
    pp = 1 / (1 + np.exp(-A @ bb)); Hm = A.T @ (A * (W * pp * (1 - pp))[:, None]) + P; bb += np.linalg.solve(Hm, A.T @ (W * (y - pp)) - P @ bb)
rk = np.argsort(-np.abs(bb[:-1])); print(f"H orb weight {bb[len(U)]:+.3f} per SD (rank {int(np.where(rk == len(U))[0][0]) + 1} of 29 by size) | z alone {zc(col('H orb')):+.2f}")
print(f"most correlated inputs with H orb: {sorted([(c, round(float(np.corrcoef(col(c), col('H orb'))[0, 1]), 2)) for c in U], key=lambda t: -abs(t[1]))[:3]}")
a, b = p28 >= .4, p29 >= .4
print(f"picks changed vs the 28: {int((a != b).sum())}")
for j in np.where(a != b)[0]:
    r = rows[j]; print(f"   {int(r['s'][:4]) + 1} ({r['sL']}) {r['L']} vs ({r['sH']}) {r['H']}: 28 {p28[j]:.0%} -> 29 {p29[j]:.0%} | {'upset happened' if y[j] else 'higher seed won'} | now {'RIGHT' if b[j] == (y[j] == 1) else 'wrong'}")
sp = os.path.join(H, "upset_model_r64.json"); shutil.copy(sp, os.path.join(H, "upset_model_r64_28inputs.json"))
d = json.load(open(sp)); d["inputs"] = NEW
d["results_each_year_held_out"] = {"games_right": int(((p29 >= .4) == (y == 1)).sum()), "of": 511, "auc": round(auc(p29, y), 3), "upset_picks": int(b.sum()), "upset_hits": int((b & (y == 1)).sum())}
d["forward_2010_17_to_2018_26"] = f"{f29}/255"; d["backward_2018_26_to_2010_17"] = f"{b29}/288"; d["note"] = "29 inputs: the locked 28 + favorite's offensive rebound rate (H orb), added by the user 2026-11-18"
json.dump(d, open(sp, "w"), indent=1); json.dump({"inputs": NEW, "p": p29.tolist()}, open(os.path.join(H, "m219_out.json"), "w"))