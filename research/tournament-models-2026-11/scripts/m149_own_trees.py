# Trees on the user's own data (the 30 inputs), all 1,007 games R64-title, each tournament held out.
# A) depth-limited CART on the 30 inputs (depth 2-6, min leaf 15); depth chosen inside training by grouped CV.
# B) CART on [the model's held-out base score + the 30 inputs] (base from Q.base: training rows held out by tournament).
# C) a readable surrogate tree (depth 3 and 4) fit to the 756 model's held-out picks: how often it agrees, and its own
#    held-out accuracy when refit without each tournament.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m110_cart_rf as T
import m99_model_types as Q
import numpy as np
from concurrent.futures import ProcessPoolExecutor
k = ~Q.FF; IDX = np.where(k)[0]; y = Q.yb.astype(int)
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
def grow(X, yy, idx, maxd, minleaf=15, d=0):
    n = len(idx); kk = yy[idx].sum(); node = {"n": n, "k": int(kk), "p": (kk + 1) / (n + 2)}
    if d >= maxd or n < 2 * minleaf or kk == 0 or kk == n: return node
    best = None; g0 = n * T.gini(kk / n)
    for f in range(X.shape[1]):
        col = X[idx, f]; o = np.argsort(col, kind="mergesort"); cs = col[o]; yc = np.cumsum(yy[idx][o])
        nl = np.arange(1, n); ok = (cs[1:] > cs[:-1]) & (nl >= minleaf) & (n - nl >= minleaf)
        if not ok.any(): continue
        kl = yc[:-1]; sc = nl * T.gini(kl / nl) + (n - nl) * T.gini((kk - kl) / (n - nl)); sc[~ok] = np.inf; j = int(np.argmin(sc))
        if best is None or sc[j] < best[0]: best = (sc[j], f, (cs[j] + cs[j + 1]) / 2)
    if best is None or best[0] >= g0 - 1e-12: return node
    _, f, thr = best; L = idx[X[idx, f] <= thr]; R = idx[X[idx, f] > thr]
    node.update(f=int(f), thr=float(thr), L=grow(X, yy, L, maxd, minleaf, d + 1), R=grow(X, yy, R, maxd, minleaf, d + 1)); return node
pred = lambda node, X, idx: np.array([T.predict(node, X[i]) for i in idx])
def pick_depth(X, yy, tr):
    s_ = Q.seas[tr]; best = None
    for d in range(1, 7):
        right = 0
        for s in sorted(set(s_)):
            a, b = tr[s_ != s], tr[s_ == s]; t = grow(X, yy, a, d); right += int(((pred(t, X, b) > .5) == yy[b]).sum())
        if best is None or right > best[1]: best = (d, right)
    return best[0]
def job_A(s):
    tr = IDX[Q.seas[IDX] != s]; te = IDX[Q.seas[IDX] == s]; d = pick_depth(Q.X30, y, tr); t = grow(Q.X30, y, tr, d)
    return s, te, pred(t, Q.X30, te), d
def job_B(s):
    tr = IDX[Q.seas[IDX] != s]; te = IDX[Q.seas[IDX] == s]; m_tr, m_te = Q.base(tr, te, Q.t_ridge())
    Xb = np.zeros((Q.N, 31)); Xb[:, 1:] = Q.X30; Xb[tr, 0] = m_tr; Xb[te, 0] = m_te
    d = pick_depth(Xb, y, tr); t = grow(Xb, y, tr, d); return s, te, pred(t, Xb, te), d
def show(node, nm, d=0, out=None):
    out = [] if out is None else out; pad = "    " * d
    if "f" not in node: out.append(f"{pad}-> stronger team wins {node['k']}/{node['n']} ({node['k']/node['n']:.0%})"); return out
    out.append(f"{pad}{nm[node['f']]} <= {node['thr']:.3g}"); show(node["L"], nm, d + 1, out)
    out.append(f"{pad}{nm[node['f']]} >  {node['thr']:.3g}"); show(node["R"], nm, d + 1, out); return out
if __name__ == "__main__":
    fit = Q.t_ridge(); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    RN = ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]
    def report(nm, p, extra=""):
        r = (p[IDX] > (0 if nm.startswith("756") else .5)) == Q.yb[IDX]
        rr = "/".join(str(int(((p[k & (Q.RND == x)] > (0 if nm.startswith('756') else .5)) == Q.yb[k & (Q.RND == x)]).sum())) for x in RN)
        print(f"{nm:46} held {int(r.sum())} | AUC {T.auc(p[IDX], y[IDX]):.3f} | by round {rr} {extra}")
    report("756 model (ridge)", out)
    with ProcessPoolExecutor(6) as ex:
        A = list(ex.map(job_A, Q.SEASONS)); Bb = list(ex.map(job_B, Q.SEASONS))
    for nm, R_ in (("A) depth-limited tree, 30 inputs", A), ("B) tree on base score + 30 inputs", Bb)):
        p = np.zeros(Q.N)
        for s, te, pp, d in R_: p[te] = pp
        report(nm, p, f"| depths chosen {sorted({d for *_, d in R_})}")
    # C) surrogate of the 756 model's picks
    pick = (out > 0).astype(int)
    for d in (3, 4):
        t_all = grow(Q.X30, pick, IDX, d, minleaf=10); agree = int(((pred(t_all, Q.X30, IDX) > .5) == pick[IDX]).sum())
        p = np.zeros(Q.N)
        for s in Q.SEASONS:
            tr = IDX[Q.seas[IDX] != s]; te = IDX[Q.seas[IDX] == s]; t = grow(Q.X30, pick, tr, d, minleaf=10); p[te] = pred(t, Q.X30, te)
        report(f"C) surrogate tree depth {d} (copies model picks)", p, f"| agrees with the model on {agree}/1007 (all games)")
        if d == 3: print("\n".join(show(t_all, names))); print()
    # A on all games, for display
    dA = pick_depth(Q.X30, y, IDX); tA = grow(Q.X30, y, IDX, dA); print(f"\nA) tree on all games (depth {dA}):"); print("\n".join(show(tA, names)))
