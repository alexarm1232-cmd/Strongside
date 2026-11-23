import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
k = ~Q.FF; fit = Q.t_ridge(); out = np.zeros(Q.N)
for s in Q.SEASONS:
    tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
    m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
B = Q.R.B; r64 = k & (Q.RND == "First round"); yb = Q.yb
# higher seed won? (Andrew's framing); seeds of S and W
sS, sW = np.array(B.sS), np.array(B.sW)
def auc(sc, y):
    o = np.argsort(sc); rk = np.empty(len(sc)); rk[o] = np.arange(1, len(sc) + 1); n1 = y.sum(); return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
right = (out > 0) == yb
print("season   model R64   higher seed R64")
for s in Q.SEASONS:
    m = r64 & (Q.seas == s); hs = np.where(sS < sW, yb, np.where(sS > sW, ~yb, True))
    print(f"{s}   {int(right[m].sum())}/{int(m.sum())}      {int(hs[m].sum())}/{int(m.sum())}")
for yrs in (("2015-16", "2025-26"), ("2016-17", "2024-25")):
    m = r64 & np.isin(Q.seas, yrs); print(f"{yrs}: model {int(right[m].sum())}/{int(m.sum())} = {right[m].mean():.1%}, AUC {auc(out[m], yb[m].astype(int)):.3f}")
print(f"all R64: {int(right[r64].sum())}/{int(r64.sum())} = {right[r64].mean():.1%}, AUC {auc(out[r64], yb[r64].astype(int)):.3f}")
