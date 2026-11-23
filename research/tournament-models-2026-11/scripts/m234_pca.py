# PCA map for the 45% average of 3 (Upset 31 + Strongside + simulator), Round 1, fit on all years.
# Each point = one team in one Round 1 game (1,022), placed by its pre-tournament numbers: the Strongside Model's 27 measures
# plus the Upset Model's team measures (season percentiles), standardized, PCA. Colored by how the average did on that game.
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
exec(open(os.path.join(H, "m228_three.py"), encoding="utf-8").read().split("STL, CAST, PCS")[0])
O = json.load(open(os.path.join(H, "m230_out.json"))); pin = np.array(O["p_all"]); NEW = O["inputs"]
a = (pin + s_up + sim_up) / 3; pk = a >= .45
names = [str(x) for x in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
keys = sorted({x[2:] for x in names if x[:2] in ("S ", "W ")} | {c.split(" ", 1)[1] for c in NEW} | {"cast_bpm_bpm"})
keys = [k for k in keys if ("H " + k) in ALL and ("L " + k) in ALL]
Xh = np.column_stack([ALL["H " + k] for k in keys]); Xl = np.column_stack([ALL["L " + k] for k in keys])
X = np.vstack([Xh, Xl]); Z = (X - X.mean(0)) / (X.std(0) + 1e-9); Uu, S_, Vt = np.linalg.svd(Z, full_matrices=False); pve = S_ ** 2 / (S_ ** 2).sum(); PC = Z @ Vt[:2].T
cat = np.where(pk & (y == 1), "Upset picked right", np.where(pk & (y == 0), "Upset picked wrong", np.where(~pk & (y == 1), "Upset missed", "Higher seed picked right")))
pts = []
for side, off in (("H", 0), ("L", n)):
    for j, r in enumerate(rows):
        won = bool(y[j] == 1) if side == "L" else bool(y[j] == 0)
        pts.append(dict(x=round(float(PC[off + j, 0]), 3), y=round(float(PC[off + j, 1]), 3), c=str(cat[j]), w=won, t=f"{int(r['s'][:4]) + 1} ({r['s' + side]}) {r[side]}", side=side, a=round(float(a[j]), 3)))
print(f"{len(keys)} measures | PC1 {pve[0]:.1%} PC2 {pve[1]:.1%}")
for i in range(2):
    o = np.argsort(-np.abs(Vt[i])); print(f"PC{i + 1} top loadings:", [(keys[k], round(float(Vt[i, k]), 2)) for k in o[:6]])
cats = ["Higher seed picked right", "Upset picked right", "Upset missed", "Upset picked wrong"]
for c in cats:
    for side in "HL":
        m = np.array([p["c"] == c and p["side"] == side for p in pts]); print(f"   {c:26} {side} teams {int(m.sum()):4} | center PC1 {PC[m, 0].mean():+.2f} PC2 {PC[m, 1].mean():+.2f}")
json.dump({"pve": pve[:2].tolist(), "points": pts, "load": {f"PC{i + 1}": [(keys[k], float(Vt[i, k])) for k in np.argsort(-np.abs(Vt[i]))[:5]] for i in range(2)}}, open(os.path.join(H, "m234_pca.json"), "w"))