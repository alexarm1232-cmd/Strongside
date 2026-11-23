# The games the 45% average (Upset 29 + Strongside + simulator) gets wrong: 111 of 511. What they look like, and what
# separates them, using every measure we have (including ones not in any model).
import os, sys, json, math, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
exec(open(os.path.join(H, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); sL = np.array([r["sL"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (p + s_up + sim_up) / 3; pk = avg >= .45; wrong = pk != (y == 1)
mu = wrong & (y == 1); wp = wrong & (y == 0)
print(f"45% average: right {int((~wrong).sum())}/511 | wrong {int(wrong.sum())}: missed upsets {int(mu.sum())}, wrong upset picks {int(wp.sum())}")
print("\nby matchup: games | upsets | missed upsets | wrong upset picks | right")
for h in range(1, 9):
    m = sL == 17 - h; print(f"   {h} vs {17 - h}|{int(m.sum())}|{int(y[m].sum())}|{int((mu & m).sum())}|{int((wp & m).sum())}|{int((~wrong & m).sum())}")
print("\nmissed upsets by how close the average was: ", {f"{lo}-{hi}%": int((mu & (avg * 100 >= lo) & (avg * 100 < hi)).sum()) for lo, hi in ((0, 15), (15, 25), (25, 35), (35, 45))})
print("wrong upset picks by average: ", {f"{lo}-{hi}%": int((wp & (avg * 100 >= lo) & (avg * 100 < hi)).sum()) for lo, hi in ((45, 50), (50, 60), (60, 101))})
any1 = (p >= .4) | (s_up >= .5) | (sim_up >= .5)
print(f"\nof the {int(mu.sum())} missed upsets, at least one model leaned upset (Upset >= 40% or other >= 50%): {int((mu & any1).sum())} | Upset Model >= 40%: {int((mu & (p >= .4)).sum())} | Strongside >= 50%: {int((mu & (s_up >= .5)).sum())} | sim >= 50%: {int((mu & (sim_up >= .5)).sum())} | none of them: {int((mu & ~any1).sum())}")
print(f"of the {int(wp.sum())} wrong upset picks: all three leaned upset {int((wp & (p >= .4) & (s_up >= .5) & (sim_up >= .5)).sum())}")
print("\nMISSED UPSETS (avg chance | Upset / Strongside / sim):")
for j in np.where(mu)[0][np.argsort(-avg[mu])]:
    r = rows[j]; print(f"   {int(r['s'][:4]) + 1} ({r['sL']}) {r['L']} over ({r['sH']}) {r['H']}: {avg[j]:.0%} | {p[j]:.0%} / {s_up[j]:.0%} / {sim_up[j]:.0%}")
print("\nWRONG UPSET PICKS:")
for j in np.where(wp)[0][np.argsort(-avg[wp])]:
    r = rows[j]; print(f"   {int(r['s'][:4]) + 1} ({r['sL']}) {r['L']} vs ({r['sH']}) {r['H']}: {avg[j]:.0%} | {p[j]:.0%} / {s_up[j]:.0%} / {sim_up[j]:.0%}")
# what separates them: missed upsets vs correct no-upset calls; wrong upset picks vs correct upset picks
def zc_(v, a, b):
    m = a | b; vv = (v[m] - v[m].mean()) / (v[m].std() + 1e-12); Xs = np.column_stack([sg[m], vv, np.ones(m.sum())]); w = np.zeros(3); yy = a[m].astype(float)
    for _ in range(50):
        q = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (q * (1 - q))[:, None]) + 1e-9 * np.eye(3); w += np.linalg.solve(Hm, Xs.T @ (yy - q))
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
ALL = dict(CAND); ALL.update({c: col(c) for c in U})
for lab, a, b in (("missed upsets vs correct 'no upset' calls", mu, ~pk & (y == 0)), ("wrong upset picks vs correct upset picks", wp, pk & (y == 1))):
    res = sorted(((abs(zc_(v, a, b)), k, zc_(v, a, b), v[a].mean(), v[b].mean()) for k, v in ALL.items() if v[a | b].std() > 0), reverse=True)
    print(f"\n{lab} ({int(a.sum())} vs {int(b.sum())}; {len(res)} tests, ~{int(len(res) * .046)} pass |z|>=2 by chance): top 15")
    for _, k, z, x1, x2 in res[:15]: print(f"   {k:40} {x1:.3f} vs {x2:.3f} | z {z:+.2f} | r net gap {np.corrcoef(ALL[k], rg)[0, 1]:+.2f}{'  [in Upset Model]' if k in U else ''}")