# Training vs testing AUC for the model the usual way: each tournament held out in turn (all rounds trained).
# Testing = held-out predictions. Training = (a) each fold's model scored on its own training games, averaged over the
# 16 folds; (b) one fit on all 1,007 games scored on those same games. Picking the winner (stronger team won).
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from concurrent.futures import ProcessPoolExecutor
k = ~Q.FF; y = Q.yb.astype(int); R1 = Q.RND == "First round"
def auc(s, yy):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
def fold(s):
    fit = Q.t_ridge(); tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
    m_tr, m_te = Q.base(tr, te, fit); test = Q.run(m_tr, tr, m_te, te, Q.EX)
    m_a, m_in = Q.base(tr, tr, fit); train = Q.run(m_a, tr, m_in, tr, Q.EX)
    r1 = R1[tr]
    return s, te, test, auc(train, y[tr]), auc(train[r1], y[tr][r1]), int(((train > 0) == Q.yb[tr]).sum()), len(tr)
if __name__ == "__main__":
    out = np.zeros(Q.N); tr_all, tr_r1 = [], []
    with ProcessPoolExecutor(8) as ex:
        for s, te, test, a, a1, right, n in ex.map(fold, Q.SEASONS): out[te] = test; tr_all.append(a); tr_r1.append(a1)
    fit = Q.t_ridge(); idx = np.where(k)[0]; m_a, m_in = Q.base(idx, idx, fit); ins = Q.run(m_a, idx, m_in, idx, Q.EX)
    m1 = k & R1; ins_full = np.zeros(Q.N); ins_full[idx] = ins
    print(f"ALL ROUNDS | testing (held out) AUC {auc(out[k], y[k]):.3f} right {int(((out[k] > 0) == Q.yb[k]).sum())}/1007 | training: avg over 16 folds {np.mean(tr_all):.3f} (range {min(tr_all):.3f}-{max(tr_all):.3f}) | one fit on all games {auc(ins, y[idx]):.3f} right {int(((ins > 0) == Q.yb[idx]).sum())}/1007")
    print(f"ROUND 1    | testing (held out) AUC {auc(out[m1], y[m1]):.3f} right {int(((out[m1] > 0) == Q.yb[m1]).sum())}/511 | training: avg over 16 folds {np.mean(tr_r1):.3f} | one fit on all games {auc(ins_full[m1], y[m1]):.3f} right {int(((ins_full[m1] > 0) == Q.yb[m1]).sum())}/511")
