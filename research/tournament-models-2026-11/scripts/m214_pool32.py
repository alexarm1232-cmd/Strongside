# Upset Model 28 + steals + close-game first-half margin + close games overall (share of games close, record in them).
# Tested each year held out, forward and backward; then compared pick-for-pick with the Strongside Model on all 511 R64 games.
import os, sys, json, numpy as np
from math import comb
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from m210_followups import F, rows, y, n, seas, U, ridge, auc, zc, kk, col
import m99_model_types as Q
W = Q.WT[[r["i"] for r in rows]]
HV = json.load(open(os.path.join(H, "m210_halves.json")))
for kx in ("c10_h1", "c10_share", "c10_win"):
    for side in "HL":
        v = np.array([(HV.get(r["s"], {}).get(kk(r[side])) or {}).get(kx, np.nan) for r in rows], float); v[np.isnan(v)] = np.nanmean(v); F[f"{side} half: {kx}"] = v
ADD = ["L stl", "L-H half: c10_h1", "L-H half: c10_share", "L-H half: c10_win"]
NEW = U + ADD
early = np.array([int(s[:4]) < 2018 for s in seas])
def held(ins):
    X = np.column_stack([col(c) for c in ins]); out = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    return out, int(((f >= .4) == (y[~early] == 1)).sum()), int(((b >= .4) == (y[early] == 1)).sum())
print("added inputs (z on all 511, seed controlled):")
for c in ADD: print(f"   {c:24} z {zc(col(c)):+.2f}")
res = {}
for lab, ins in (("locked 28", U), ("28 + 4 new (32)", NEW), ("28 + 4 new, underdog's own close 1st half", U + ["L stl", "L half: c10_h1", "L-H half: c10_share", "L-H half: c10_win"])):
    p, fw, bw = held(ins); res[lab] = p
    print(f"{lab:44} held out {int(((p >= .4) == (y == 1)).sum())}/511 | AUC {auc(p, y):.3f} | upset picks {int((p >= .4).sum())} ({int(((p >= .4) & (y == 1)).sum())} hit) | forward {fw}/255 | backward {bw}/288 | fwd+back {fw + bw}/543")
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))
sim = Q.B.simS[gi]; sim_up = np.where(hsS, 1 - sim, sim) if sim.max() <= 1 else None
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
print(f"\nStrongside Model on these 511: right {int(((s_up >= .5) == (y == 1)).sum())} | upset picks {int((s_up >= .5).sum())} ({int(((s_up >= .5) & (y == 1)).sum())} hit)")
for lab in ("locked 28", "28 + 4 new (32)"):
    up = res[lab]; print(f"\n== {lab} vs the Strongside Model: chance correlation {np.corrcoef(lg(up), lg(s_up))[0, 1]:.2f} | average gap in upset chance {np.abs(up - s_up).mean():.1%}")
    for cut in (0.5, 0.4):
        a, b = up >= cut, s_up >= .5; same = a == b; ra, rb = a == (y == 1), b == (y == 1); dis = ~same
        x, z = int((ra & dis).sum()), int((rb & dis).sum()); pv = min(1, 2 * sum(comb(x + z, i) for i in range(max(x, z), x + z + 1)) / 2 ** (x + z)) if x + z else 1
        print(f"   upset at {cut:.0%}: same pick {int(same.sum())}/511 ({same.mean():.0%}) | both pick upset {int((a & b).sum())} | only Upset {int((a & ~b).sum())} | only Strongside {int((~a & b).sum())} | disagree {int(dis.sum())}: Upset right {x}, Strongside right {z} (p {pv:.2f})")
a, b = res["locked 28"] >= .4, res["28 + 4 new (32)"] >= .4
print(f"\nnew vs locked Upset Model at 40%: same pick {int((a == b).sum())}/511 | upsets only new picks {int((b & ~a).sum())} ({int((b & ~a & (y == 1)).sum())} hit) | only locked picks {int((a & ~b).sum())} ({int((a & ~b & (y == 1)).sum())} hit)")
json.dump({"inputs": NEW, "p": res["28 + 4 new (32)"].tolist()}, open(os.path.join(H, "m214_out.json"), "w"))