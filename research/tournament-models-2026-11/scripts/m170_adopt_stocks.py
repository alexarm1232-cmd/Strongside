# Adopt steals + blocks per game (both teams, percentile within season, pre-tournament corrected box scores) as inputs:
# sos gap + gap x pace + 27 measures + S stocks per game + W stocks per game = 31 inputs. Save as m3_data.npz.
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m168_new_model_rescreen as M
from concurrent.futures import ProcessPoolExecutor
Q = M.Q; k = M.k
if __name__ == "__main__":
    with ProcessPoolExecutor(6) as ex: AL = dict(ex.map(M._allowed, sorted({g["season"] for g in M.G})))
    def col(i_side):
        out = np.full(Q.N, 0.5)
        for i, g in enumerate(M.G):
            s = g["season"]; t = M.B.Sname[i] if i_side == "S" else M.Wn[i]; d = AL[s]; v = d.get(t) or d.get(t + ".") or d.get(t.rstrip("."))
            if v: out[i] = M.pct_of([x[0] for x in d.values()], v[0])
        return out
    S_, W_ = col("S"), col("W")
    XX = np.column_stack([M.XM, S_, W_]); names = M.NAMES + ["S stocks per game", "W stocks per game"]
    dst = os.path.join(Q.OLD, "m3_data.npz"); d = dict(np.load(dst, allow_pickle=True))
    import shutil; shutil.copy(dst, os.path.join(Q.OLD, "m3_data_gappace29.npz"))
    d["X"] = XX; d["names"] = np.array(names); np.savez(dst, **d)
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    p = np.clip(1 / (1 + np.exp(-out[k])), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(yk, np.log(p), np.log(1 - p))))
    RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in RN]
    f = fit(np.where(k)[0]); Z = Q.zstd(XX, np.where(k)[0]); A = np.column_stack([Z(np.where(k)[0]), np.ones(k.sum())])
    w = np.linalg.lstsq(A, f(np.where(k)[0]), rcond=None)[0][:-1]
    print(f"saved {len(names)} inputs | held {held} | in-sample {insr} | overfit {insr - held:+d} | AUC {auc:.4f} | LL {ll:.4f} | by round {'/'.join(map(str, rr))}")
    print(f"ridge weights (standardized): gap x pace {w[1]:+.3f} | S stocks {w[-2]:+.3f} | W stocks {w[-1]:+.3f} | largest measure {max(abs(w[2:-2])):.3f}")
    np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m170_model_out.npy"), out)
