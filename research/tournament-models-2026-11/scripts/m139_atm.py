# "ATM": ridge logistic refit for each game on only the K most similar training games (similarity = distance on the
# standardized 30 inputs). Same 756 pipeline otherwise.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
k = ~Q.FF
def ridge_w(A, y, w, lam=30.0, it=8):
    A1 = np.column_stack([A, np.ones(len(A))]); b = np.zeros(A1.shape[1]); P = lam * np.eye(A1.shape[1]); P[-1, -1] = 0
    for _ in range(it):
        p = 1 / (1 + np.exp(-A1 @ b)); H = A1.T @ (A1 * (w * p * (1 - p))[:, None]) + P; g = A1.T @ (w * (y - p)) - P @ b
        b += np.linalg.solve(H, g)
    return b
def t_atm(K):
    def fit(idx):
        Z = Q.zstd(Q.X30, idx); A = Z(idx); yy = Q.y_[idx]; w = Q.WT[idx]
        def pred(r):
            R = Z(r); out = np.zeros(len(r))
            for i in range(len(r)):
                d = ((A - R[i]) ** 2).sum(1); d[idx == r[i]] = np.inf; nn = np.argpartition(d, K)[:K]
                b = ridge_w(A[nn], yy[nn], w[nn]); out[i] = R[i] @ b[:-1] + b[-1]
            return out
        return pred
    return fit
V = {"current 756 (all games)": Q.t_ridge(), "ATM: 300 most similar": t_atm(300), "ATM: 500 most similar": t_atm(500), "ATM: 700 most similar": t_atm(700)}
def job(name):
    fit = V[name]; out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]]
    return name, held, auc, rr
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(4) as ex:
        for name, held, auc, rr in ex.map(job, V):
            print(f"{name:26} held {held} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
