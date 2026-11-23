# Four factors in the Round 1 Upset Model: each factor (offense + defense), the 40/25/20/15 composites, net = offense - defense.
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from m210_followups import F, rows, y, n, seas, U, ridge, auc, zc, mw, col
import m99_model_types as Q
W = Q.WT[[r["i"] for r in rows]]; sL = np.array([r["sL"] for r in rows]); big = sL >= 14; early = np.array([int(s[:4]) < 2018 for s in seas])
TM = Q.R.B.TM; rg = np.array([TM[r["s"]][r["L"]]["adj_net"] - TM[r["s"]][r["H"]]["adj_net"] for r in rows])
for side in "HL":
    g = lambda k: F[f"{side} {k}"]
    F[f"{side} 4F offense"] = .40 * g("efg") + .25 * (1 - g("tov")) + .20 * g("orb") + .15 * g("ftr")
    F[f"{side} 4F defense allowed"] = .40 * g("d_efg") + .25 * (1 - g("d_tov")) + .20 * g("d_orb") + .15 * g("d_ftr")
    F[f"{side} 4F net"] = F[f"{side} 4F offense"] - F[f"{side} 4F defense allowed"]
def full(ins):
    X = np.column_stack([col(c) for c in ins]); p = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; p[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    return int(((p >= .4) == (y == 1)).sum()), auc(p, y), int(((f >= .4) == (y[~early] == 1)).sum()), int(((b >= .4) == (y[early] == 1)).sum()), int((p >= .4).sum()), int(((p >= .4) & (y == 1)).sum())
b0 = full(U); print(f"locked 28: held out {b0[0]}/511 | AUC {b0[1]:.3f} | forward {b0[2]}/255 | backward {b0[3]}/288 | fwd+back {b0[2] + b0[3]}/543 | picks {b0[4]} ({b0[5]} hit)")
print("already in the 28 from the four factors: L d_tov (turnovers forced), L-H ftr (free-throw rate gap)\n")
print("measure | z all 511 (seed controlled) | 14-16 z | r net-rating gap | held out | fwd+back | picks (hit)")
names = []
for k in ("efg", "tov", "orb", "ftr", "d_efg", "d_tov", "d_orb", "d_ftr", "4F offense", "4F defense allowed", "4F net"):
    for lab in ("L", "H", "L-H"): names.append(f"{lab} {k}")
for nm in names:
    v = col(nm)
    if nm in U: print(f"{nm}|{zc(v):+.2f}|{mw(v, big):+.2f}|{np.corrcoef(v, rg)[0, 1]:+.2f}|in the 28|"); continue
    r = full(U + [nm]); print(f"{nm}|{zc(v):+.2f}|{mw(v, big):+.2f}|{np.corrcoef(v, rg)[0, 1]:+.2f}|{r[0]} ({r[0] - b0[0]:+d})|{r[2] + r[3]} ({r[2] + r[3] - b0[2] - b0[3]:+d})|{r[4]} ({r[5]})")
for lab, ins in (("all 4 factors gaps (8, adding 7 not in model)", U + [f"L-H {k}" for k in ("efg", "tov", "orb", "d_efg", "d_tov", "d_orb", "d_ftr")]),
                 ("composites: L-H 4F offense + L-H 4F defense allowed", U + ["L-H 4F offense", "L-H 4F defense allowed"]),
                 ("composite: L-H 4F net", U + ["L-H 4F net"])):
    r = full(ins); print(f"\n{lab}: held out {r[0]} ({r[0] - b0[0]:+d}) | AUC {r[1]:.3f} | fwd {r[2]} back {r[3]} = {r[2] + r[3]} ({r[2] + r[3] - b0[2] - b0[3]:+d}) | picks {r[4]} ({r[5]} hit)")