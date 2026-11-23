# Overfitting with both rating inputs vs one: in-sample (trained on all 1,007 games, scored on them, as m99) minus held
# out (each tournament held out), same 756 pipeline. Also log-loss held out, and how much the weights move from season
# to season (instability is the usual sign that correlated inputs hurt).
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
ig, ip = names.index("gap"), names.index("gap x possessions")
V = {"current (30, both)": list(range(Q.X30.shape[1])), "29, no rating gap": [c for c in range(Q.X30.shape[1]) if c != ig], "29, no gap x pace": [c for c in range(Q.X30.shape[1]) if c != ip]}
def job(name):
    cols = V[name]; fit = Q.t_ridge(X=Q.X30[:, cols]); keep = ~Q.FF; out = np.zeros(Q.N); wts = []
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & keep)[0]; te = np.where((Q.seas == s) & keep)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
        f = fit(tr); Z = Q.zstd(Q.X30[:, cols], tr); A = np.column_stack([Z(tr), np.ones(len(tr))])
        wts.append(np.linalg.lstsq(A, f(tr), rcond=None)[0][:-1])
    tr = np.where(keep)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    held = int(((out > 0) == Q.yb)[keep].sum()); insr = int(((ins > 0) == Q.yb[tr]).sum())
    p = np.clip(1 / (1 + np.exp(-out[keep])), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(Q.yb[keep], np.log(p), np.log(1 - p))))
    W = np.array(wts); rating = [cols.index(c) for c in (ig, ip) if c in cols]
    s_, y_ = out[keep], Q.yb[keep].astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1; auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    print(f"AUC {name}: {auc:.4f}", flush=True)
    return name, held, insr, ll, [(names[cols[j]], float(W[:, j].mean()), float(W[:, j].std())) for j in rating]
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(3) as ex:
        for name, held, insr, ll, rw in ex.map(job, V):
            print(f"{name:22} held out {held} | in-sample {insr} | overfit {insr - held:+d} | log-loss {ll:.4f} | rating weights (mean ± sd over 16 fits): "
                  + ", ".join(f"{n} {m:+.3f}±{s:.3f}" for n, m, s in rw))

