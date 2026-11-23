# Out-of-bag AUC for our model, the way a random forest gets one: 200 bootstrap samples of the 1,007 games (all rounds,
# drawn with replacement); the full model pipeline is fit on each sample and scores the games left out of it; each
# game's out-of-bag predictions are averaged. AUC on picking the winner (stronger team won), Round 1 and all rounds.
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from concurrent.futures import ProcessPoolExecutor
k = ~Q.FF; IDX = np.where(k)[0]
def auc(s, y):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = y.sum(); return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
def one(seed):
    rng = np.random.default_rng(seed); bs = np.sort(rng.choice(IDX, len(IDX), replace=True)); oob = np.setdiff1d(IDX, bs)
    fit = Q.t_ridge(); m_tr, m_te = Q.base(bs, oob, fit); return oob, Q.run(m_tr, bs, m_te, oob, Q.EX)
if __name__ == "__main__":
    S = np.zeros(Q.N); C = np.zeros(Q.N)
    with ProcessPoolExecutor(8) as ex:
        for oob, p in ex.map(one, range(200)): S[oob] += 1 / (1 + np.exp(-p)); C[oob] += 1
    ok = k & (C > 0); prob = S / np.maximum(C, 1)
    r64 = ok & (Q.RND == "First round"); y = Q.yb.astype(int)
    print(f"out-of-bag draws per game: median {int(np.median(C[k]))}, min {int(C[k].min())}")
    print(f"Round 1: OOB AUC {auc(prob[r64], y[r64]):.3f} | right {int(((prob[r64] > .5) == Q.yb[r64]).sum())}/{int(r64.sum())}")
    print(f"All rounds: OOB AUC {auc(prob[ok], y[ok]):.3f} | right {int(((prob[ok] > .5) == Q.yb[ok]).sum())}/{int(ok.sum())}")
