import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m132_reddit as R2
import numpy as np
Q = R2.Q; k = R2.k
fit = Q.t_ridge(); out = np.zeros(Q.N)
for s in Q.SEASONS:
    tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
    m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
flag = (R2.overS >= 2) * 1.0
def z_on(base, v):
    Xs = np.column_stack([base[k], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(3)
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[1] / np.sqrt(np.linalg.inv(H)[1, 1])
print(f"z of 'stronger team over-seeded 2+' on top of the full model's held-out output: {z_on(out, flag):+.2f}")
m = k & (flag == 1); p = 1 / (1 + np.exp(-out[m]))
print(f"those {int(m.sum())} games: stronger team won {int(Q.yb[m].sum())}; model expected {p.sum():.1f}; model picked the stronger team in {int((out[m] > 0).sum())} and got {int(((out[m] > 0) == Q.yb[m]).sum())} right")
m2 = k & (flag == 0); p2 = 1 / (1 + np.exp(-out[m2]))
print(f"other {int(m2.sum())} games: stronger team won {int(Q.yb[m2].sum())}; model expected {p2.sum():.1f}")
def held(ex):
    o = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); o[te] = Q.run(m_tr, tr, m_te, te, ex)
    s_ = o[k]; y_ = Q.yb[k].astype(int); oo = np.argsort(s_); rk = np.empty(len(s_)); rk[oo] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    c = (o[k] > 0) == Q.yb[k]; c0 = (out[k] > 0) == Q.yb[k]
    return int(c.sum()), auc, int((c & ~c0).sum()), int((~c & c0).sum())
EX = np.asarray(Q.EX); EX = EX if EX.ndim == 2 else EX[:, None]
for nm, ex in (("flag in the round lines (with coach + star)", np.column_stack([EX, flag])),
               ("flag + weaker team's flag in the round lines", np.column_stack([EX, flag, (R2.overW >= 2) * 1.0]))):
    h, a, g, l = held(ex); print(f"{nm:46} held {h} | AUC {a:.4f} | gained {g} lost {l}")
