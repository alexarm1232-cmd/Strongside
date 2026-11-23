# Which part of the fix moved the old 30-input model from 756 to 753? Swap the two changed pieces one at a time:
# the steal/block measures inside the 27 (S nst_to, W d_blk) vs the who-plays inputs (built from player BPM).
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m165_retest as R
Q = R.Q; k = R.k
names = R.old_names
iN, iB, iT = names.index("S nst_to"), names.index("W d_blk"), names.index("W d_tov")
m = k & np.isin(Q.seas, ["2009-10", "2010-11"])
for nm, j in (("S nst_to", iN), ("W d_blk", iB), ("W d_tov", iT)):
    d = np.abs(R.XB[:, j] - R.OLD_X[:, j]); print(f"{nm:9} 2010-11 games: avg change {d[m].mean():.3f} (percentile points), largest {d[m].max():.3f} | other years max {d[k & ~np.isin(Q.seas, ['2009-10', '2010-11'])].max():.3f}")
dF = np.abs(R.NEW_F - R.OLD_F); print("who-plays inputs, 2010-11 games: avg change per column", np.round(dF[m].mean(0), 3), "| other years", np.round(dF[k & ~m].mean(0), 3))
def run(X, F):
    Q.M.F[:] = F; fit = Q.t_ridge(X=X); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    return int(((out[k] > 0) == Q.yb[k]).sum())
for label, X, F in (("old measures + old who-plays (original)", R.OLD_X, R.OLD_F), ("NEW steal/block measures + old who-plays", R.XB, R.OLD_F),
                    ("old measures + NEW who-plays", R.OLD_X, R.NEW_F), ("both new (corrected)", R.XB, R.NEW_F)):
    print(f"{label:42} {run(X, F)}")
