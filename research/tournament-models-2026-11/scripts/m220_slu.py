import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from m210_followups import F, rows, y, n, seas, U, ridge, auc, col
import m99_model_types as Q
W = Q.WT[[r["i"] for r in rows]]; early = np.array([int(s[:4]) < 2018 for s in seas])
NEW = json.load(open(os.path.join(H, "m219_out.json")))["inputs"]; p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
j = next(k for k, r in enumerate(rows) if r["s"] == "2025-26" and r["L"] == "Saint Louis")
print(f"2026 (9) Saint Louis over (8) Georgia: 29-input chance {p[j]:.2%} (28 had {np.array(json.load(open(os.path.join(H, 'm188_out.json')))['p_noseed'])[j]:.2%})")
X = np.column_stack([col(c) for c in NEW])
f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
print("\ncutoff | held out /511 | upset picks (hit) | forward /255 | backward /288 | fwd+back /543 | Saint Louis picked?")
for c in (.42, .41, .40, .395, .39, .385, .38, .37, .36, .35):
    pk = p >= c; print(f"{c:.1%}|{int((pk == (y == 1)).sum())}|{int(pk.sum())} ({int((pk & (y == 1)).sum())})|{int(((f >= c) == (y[~early] == 1)).sum())}|{int(((b >= c) == (y[early] == 1)).sum())}|{int(((f >= c) == (y[~early] == 1)).sum()) + int(((b >= c) == (y[early] == 1)).sum())}|{'yes' if p[j] >= c else 'no'}")
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
print(f"\nSaint Louis: Strongside {s_up[j]:.0%} | simulator {sim_up[j]:.0%} | Upset (29) {p[j]:.0%}")
for lab, up in (("Upset at 50%", p >= .5), ("Upset at 40%", p >= .4)):
    v = (up.astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2
    print(f"3-way vote ({lab}) with the 29: right {int((v == (y == 1)).sum())}/511 | upset picks {int(v.sum())} ({int((v & (y == 1)).sum())} hit) | Saint Louis picked: {'yes' if v[j] else 'no'}")
avg = (p + s_up + sim_up) / 3; print(f"average of the three (50%): right {int(((avg >= .5) == (y == 1)).sum())}/511 | Saint Louis avg {avg[j]:.0%} -> {'picked' if avg[j] >= .5 else 'not picked'}")
# what moved it: contribution change of H orb
print(f"Georgia's offensive rebound rate (percentile among D-I): {F['H orb'][j]:.2f} | avg favorite {F['H orb'].mean():.2f}")