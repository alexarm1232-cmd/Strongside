# Two model types from the RPubs project not yet tested: k-nearest neighbors and a radial-kernel (RBF) model.
# Same 756 pipeline as m99 (same 30 inputs, half-life 12 weights, base held out inside training, round lines, 85% sim
# in F4/title, First Four out, each tournament held out). RBF via random Fourier features + the same ridge logistic.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
k = ~Q.FF; lg = lambda p: np.log(np.clip(p, 1e-3, 1 - 1e-3) / (1 - np.clip(p, 1e-3, 1 - 1e-3)))
def t_knn(K):
    def fit(idx):
        Z = Q.zstd(Q.X30, idx); A = Z(idx); yy = Q.y_[idx]; w = Q.WT[idx]
        def pred(r):
            D = ((Z(r)[:, None, :] - A[None, :, :]) ** 2).sum(-1); out = np.zeros(len(r))
            for i in range(len(r)):
                nn = np.argsort(D[i])
                nn = nn[(idx[nn] != r[i])][:K]          # never its own game
                out[i] = lg((np.sum(w[nn] * yy[nn]) + 1) / (np.sum(w[nn]) + 2))
            return out
        return pred
    return fit
def t_rbf(D=400, gamma_mult=1.0, lam=30.0):
    rng = np.random.default_rng(7); p = Q.X30.shape[1]; g = gamma_mult / p
    W_ = rng.normal(0, np.sqrt(2 * g), (p, D)); b_ = rng.uniform(0, 2 * np.pi, D)
    def fit(idx):
        Z = Q.zstd(Q.X30, idx); Phi = lambda r: np.sqrt(2 / D) * np.cos(Z(r) @ W_ + b_)
        F = np.zeros((Q.N, D)); F[idx] = Phi(idx); rest = np.setdiff1d(np.arange(Q.N), idx); F[rest] = Phi(rest)
        f = Q.t_ridge(X=F, lam=lam)(idx); return f
    return fit
V = {"current 756 (ridge)": Q.t_ridge(), "KNN k=25": t_knn(25), "KNN k=50": t_knn(50), "KNN k=100": t_knn(100),
     "RBF kernel (gamma 1/p)": t_rbf(), "RBF kernel (gamma 0.3/p)": t_rbf(gamma_mult=0.3)}
def job(name):
    fit = V[name]; out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]]
    return name, held, insr, auc, rr
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(6) as ex:
        for name, held, insr, auc, rr in ex.map(job, V):
            print(f"{name:26} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
