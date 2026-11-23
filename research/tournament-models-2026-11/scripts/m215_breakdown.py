import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
src = open(os.path.join(H, "m214_pool32.py"), encoding="utf-8").read().split("print(\"added inputs")[0]
exec(src)
X = np.column_stack([col(c) for c in NEW]); mu, sd = X.mean(0), X.std(0) + 1e-9
A = np.column_stack([(X - mu) / sd, np.ones(n)]); b = np.zeros(A.shape[1]); P = 30 * np.eye(A.shape[1]); P[-1, -1] = 0
for _ in range(60):
    p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (W * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (W * (y - p)) - P @ b)
base, _, _ = held(NEW); br = int(((base >= .4) == (y == 1)).sum())
out = []
for j, c in enumerate(NEW):
    pj = np.zeros(n); Xj = np.delete(X, j, 1)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; pj[te] = 1 / (1 + np.exp(-ridge(Xj[tr], y[tr], W[tr])(Xj[te])))
    out.append((c, b[j], zc(col(c)), br - int(((pj >= .4) == (y == 1)).sum())))
out.sort(key=lambda r: -abs(r[1]))
print("input | weight (per 1 SD, + = more upsets) | z alone | games lost if removed")
for c, w, z, d in out: print(f"{c}|{w:+.3f}|{z:+.2f}|{d:+d}")
print("\nyear | games | upsets | right (32) | right (locked 28) | Strongside | upset picks (hit)")
p28, _, _ = held(U)
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))
for s in sorted(set(seas)):
    m = seas == s
    print(f"{int(s[:4]) + 1}|{int(m.sum())}|{int(y[m].sum())}|{int(((base[m] >= .4) == (y[m] == 1)).sum())}|{int(((p28[m] >= .4) == (y[m] == 1)).sum())}|{int(((s_up[m] >= .5) == (y[m] == 1)).sum())}|{int((base[m] >= .4).sum())} ({int(((base[m] >= .4) & (y[m] == 1)).sum())})")
print("\nby seed line: games | upsets | 32 right | upset picks (hit)")
sl = np.array([r["sL"] for r in rows])
for h in range(1, 9):
    m = sl == 17 - h; print(f"{h} vs {17 - h}|{int(m.sum())}|{int(y[m].sum())}|{int(((base[m] >= .4) == (y[m] == 1)).sum())}|{int((base[m] >= .4).sum())} ({int(((base[m] >= .4) & (y[m] == 1)).sum())})")