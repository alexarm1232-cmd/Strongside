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
lg = lambda q: np.log(np.clip(q, 1e-4, 1 - 1e-4) / (1 - np.clip(q, 1e-4, 1 - 1e-4)))
early = np.array([int(s[:4]) < 2018 for s in seas])
def fit(X, yy):
    w = np.zeros(X.shape[1])
    for _ in range(60):
        q = 1 / (1 + np.exp(-X @ w)); Hm = X.T @ (X * (q * (1 - q))[:, None]) + 1e-3 * np.eye(X.shape[1]); w += np.linalg.solve(Hm, X.T @ (yy - q) - 1e-3 * w)
    return w
def test(extra, lab):
    X = np.column_stack([lg(avg)] + [(e - e.mean()) / e.std() for e in extra] + [np.ones(n)]); out = np.zeros(n); pk = np.zeros(n, bool)
    for s in sorted(set(seas)):
        tr, te = seas != s, seas == s; w = fit(X[tr], y[tr]); q = 1 / (1 + np.exp(-X @ w))
        g = np.arange(.30, .61, .01); sc = [int(((q[tr] >= c) == (y[tr] == 1)).sum()) for c in g]; c = np.median(g[np.array(sc) == max(sc)])
        out[te] = q[te]; pk[te] = q[te] >= c
    wf = fit(X[early], y[early]); qf = 1 / (1 + np.exp(-X @ wf)); g = np.arange(.30, .61, .01); cf = np.median(g[np.array([int(((qf[early] >= c) == (y[early] == 1)).sum()) for c in g]) == max([int(((qf[early] >= c) == (y[early] == 1)).sum()) for c in g])])
    wb = fit(X[~early], y[~early]); qb = 1 / (1 + np.exp(-X @ wb)); cb = np.median(g[np.array([int(((qb[~early] >= c) == (y[~early] == 1)).sum()) for c in g]) == max([int(((qb[~early] >= c) == (y[~early] == 1)).sum()) for c in g])])
    fw = int(((qf[~early] >= cf) == (y[~early] == 1)).sum()); bw = int(((qb[early] >= cb) == (y[early] == 1)).sum())
    print(f"{lab:46} held out {int((pk == (y == 1)).sum())}/511 | upset picks {int(pk.sum())} ({int((pk & (y == 1)).sum())} hit) | forward {fw}/255 | backward {bw}/288 | fwd+back {fw + bw}/543" + (f" | steals weight {w[1]:+.2f}" if extra else ""))
    return out
print("all with the cutoff chosen on the training years only")
test([], "average of 3 (no steals)")
test([col("L-H stl")], "average + steals gap")
test([col("L stl")], "average + underdog steals")
test([col("L-H basic: spg")], "average + steals per game gap")
test([col("L-H stl"), col("L pt_d_share Perimeter Cut")], "average + steals gap + perimeter cuts allowed")