import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m168_new_model_rescreen as M
from math import comb
from concurrent.futures import ProcessPoolExecutor
Q = M.Q; k = M.k
def held_out(extra):
    XX = M.XM if extra is None else np.column_stack([M.XM, extra]); fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    return out
import builtins
def _init(e): builtins.EXTRA = e
def perm(seed):
    rng = np.random.default_rng(seed); import builtins; E = builtins.EXTRA.copy()
    for s in Q.SEASONS:                          # shuffle the two stocks columns across games within each season
        idx = np.where(Q.seas == s)[0]; E[idx] = E[rng.permutation(idx)]
    return int(((held_out(E)[k] > 0) == Q.yb[k]).sum())
if __name__ == "__main__":
    with ProcessPoolExecutor(6) as ex: AL = dict(ex.map(M._allowed, sorted({g["season"] for g in M.G})))
    M.AL = AL
    def col(i_side, j):
        out = np.full(Q.N, 0.5)
        for i, g in enumerate(M.G):
            s = g["season"]; t = M.B.Sname[i] if i_side == "S" else M.Wn[i]; d = AL[s]; v = d.get(t) or d.get(t + ".") or d.get(t.rstrip("."))
            if v: out[i] = M.pct_of([x[j] for x in d.values()], v[j])
        return out
    EXTRA = np.column_stack([col("S", 0), col("W", 0)])
    import builtins; builtins.EXTRA = EXTRA
    base, plus = held_out(None), held_out(EXTRA); yk = Q.yb[k]
    a, b = (base[k] > 0) == yk, (plus[k] > 0) == yk; g_, l_ = int((b & ~a).sum()), int((~b & a).sum()); n = g_ + l_
    p = sum(comb(n, i) for i in range(max(g_, l_), n + 1)) / 2 ** n * 2
    print(f"base {int(a.sum())} | + stocks per game {int(b.sum())} | gained {g_} lost {l_} | sign test p = {min(p, 1):.3f}")
    with ProcessPoolExecutor(6, initializer=_init, initargs=(EXTRA,)) as ex:
        sh = list(ex.map(perm, range(30)))
    print("shuffled stocks (30 runs): held", sorted(sh), "| runs >= +7 over base:", sum(x >= int(a.sum()) + 7 for x in sh))


