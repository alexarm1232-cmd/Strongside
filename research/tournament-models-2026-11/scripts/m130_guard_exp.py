# Four factors in the 756 model: the 16 single factors forced in, Oliver-weighted offense/defense composites per team,
# a net composite per team, the net gap, and offense/defense gaps. Exact 756 pipeline, each tournament held out,
# First Four out. Also correlation with the rating gap (the selection rule drops anything at |r| >= 0.3 with strength).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
import json
B = Q.R.B; PG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m129_pg.json")))
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(B.G, B.Sname)]
def pct(key, s, t):
    arr = np.sort([v[key] for v in PG[s].values()]); x = PG[s].get(t, {}).get(key)
    return 0.5 if x is None else float(np.searchsorted(arr, x, side="right") / len(arr))
col = lambda key, side: np.array([pct(key, g["season"], (B.Sname[i] if side == "S" else Wn[i])) for i, g in enumerate(B.G)])
SG, WG, S2, W2 = col("guard_exp", "S"), col("guard_exp", "W"), col("top2_guard_exp", "S"), col("top2_guard_exp", "W")
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
gap = Q.X30[:, names.index("gap")]
V = {"current 756 (30)": None,
     "+ guard experience (S, W)": np.column_stack([SG, WG]),
     "+ guard experience gap (S - W)": (SG - WG)[:, None],
     "+ top-2 guard experience (S, W)": np.column_stack([S2, W2]),
     "+ top-2 guard experience gap": (S2 - W2)[:, None]}
def job(name):
    extra = V[name]; X = Q.X30 if extra is None else np.column_stack([Q.X30, extra])
    fit = Q.t_ridge(X=X); keep = ~Q.FF; out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & keep)[0]; te = np.where((Q.seas == s) & keep)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(keep)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[keep]; held = int(((out[keep] > 0) == yk).sum()); insr = int(((ins > 0) == Q.yb[tr]).sum())
    p = np.clip(1 / (1 + np.exp(-out[keep])), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(yk, np.log(p), np.log(1 - p))))
    s_ = out[keep]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1; auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    rr = [int(((out[keep & (Q.RND == r)] > 0) == Q.yb[keep & (Q.RND == r)]).sum()) for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]]
    up = keep & (out < 0); return name, held, insr, ll, auc, rr, out
if __name__ == "__main__":
    k = ~Q.FF
    for nm, v in [("S guard", SG), ("W guard", WG), ("guard gap", SG - WG), ("top2 gap", S2 - W2)]:
        print(f"corr with rating gap  {nm:8} {np.corrcoef(v[k], gap[k])[0,1]:+.2f}")
    # significance on top of strength, like the selection step: logistic y ~ 3 strength + measure, Wald z
    def zt(v):
        Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
        for _ in range(50):
            p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
        return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
    for nm, v in [("S guard exp", SG), ("W guard exp", WG), ("guard gap", SG - WG), ("S top2", S2), ("W top2", W2), ("top2 gap", S2 - W2)]:
        print(f"z on top of strength  {nm:12} {zt(v):+.2f}")
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(4) as ex:
        for name, held, insr, ll, auc, rr, out in ex.map(job, V):
            res[name] = out
            print(f"{name:40} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | LL {ll:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
    base = res["current 756 (30)"]; yk = Q.yb[k]; c0 = (base[k] > 0) == yk
    for name, out in res.items():
        c1 = (out[k] > 0) == yk; print(f"vs current {name:40} gained {int((c1 & ~c0).sum())} lost {int((~c1 & c0).sum())}")


