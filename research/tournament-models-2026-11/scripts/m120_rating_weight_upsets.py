# Does leaning on the rating gap cost upset picks? The 756 pipeline (m99) with the rating weight varied:
#   current            both "gap" and "gap x possessions" (the near-copy)
#   one column         gap x possessions dropped
#   one column, x0.75 / x0.5   the remaining rating gap scaled down after standardizing, so ridge shrinks it harder
# For each: games right (of 1,007), upset picks by seed (worse seed picked) and how many hit, picks against the
# stronger-rated team and hits, and the Round of 64 seeds 11-16 picks.
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
D3 = np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
ig, ip = names.index("gap"), names.index("gap x possessions")
def t_ridge_scaled(cols, scale, lam=30.0):
    X = Q.X30[:, cols]; f = np.ones(len(cols)); f[cols.index(ig)] = scale
    def fit(idx):
        mu, sd = X[idx].mean(0), X[idx].std(0) + 1e-9; Zf = lambda r: (X[r] - mu) / sd * f
        A = np.column_stack([Zf(idx), np.ones(len(idx))]); w = Q.WT[idx]; b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
        for _ in range(40):
            q = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (w * q * (1 - q))[:, None]) + P; b += np.linalg.solve(H, A.T @ (w * (Q.y_[idx] - q)) - P @ b)
        return lambda r: np.column_stack([Zf(r), np.ones(len(r))]) @ b
    return fit
V = {"current (both rating columns)": (list(range(30)), 1.0), "one rating column": ([c for c in range(30) if c != ip], 1.0),
     "one column, rating x0.75": ([c for c in range(30) if c != ip], 0.75), "one column, rating x0.5": ([c for c in range(30) if c != ip], 0.5)}
def job(name):
    cols, sc = V[name]; fit = t_ridge_scaled(cols, sc); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & ~Q.FF)[0]; te = np.where((Q.seas == s) & ~Q.FF)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    return name, out
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    keep = ~Q.FF; yb = Q.yb; dogS = sS > sW; diff = keep & (sS != sW); R64 = keep & (Q.RND == "First round")
    print(f"{'version':32} {'right':>5} | {'seed upsets picked':>18} {'hit':>4} {'hit %':>6} | {'vs stronger-rated':>17} {'hit':>4} | {'R64 11-16 seeds':>15} {'hit':>4}")
    with ProcessPoolExecutor(4) as ex:
        for name, sc in ex.map(job, V):
            right = int(((sc > 0) == yb)[keep].sum())
            up = diff & np.where(dogS, sc > 0, sc < 0); uh = int((up & ((sc > 0) == yb)).sum())
            vs = keep & (sc < 0); vh = int((vs & ~yb).sum())
            low = R64 & (np.maximum(sS, sW) >= 11) & np.where(dogS, sc > 0, sc < 0); lh = int((low & ((sc > 0) == yb)).sum())
            print(f"{name:32} {right:5d} | {int(up.sum()):18d} {uh:4d} {uh / max(up.sum(), 1):6.0%} | {int(vs.sum()):17d} {vh:4d} | {int(low.sum()):15d} {lh:4d}")
