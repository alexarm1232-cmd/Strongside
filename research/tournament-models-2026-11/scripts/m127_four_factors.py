# Four factors in the 756 model: the 16 single factors forced in, Oliver-weighted offense/defense composites per team,
# a net composite per team, the net gap, and offense/defense gaps. Exact 756 pipeline, each tournament held out,
# First Four out. Also correlation with the rating gap (the selection rule drops anything at |r| >= 0.3 with strength).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
BX, KS = Q.R.B.X, Q.R.B.KS
g = lambda k: BX[:, KS.index(k)]
def off(t): return .40 * g(t+" efg") - .25 * g(t+" tov") + .20 * g(t+" orb") + .15 * g(t+" ftr")
def dfn(t): return -.40 * g(t+" d_efg") + .25 * g(t+" d_tov") - .20 * g(t+" d_orb") - .15 * g(t+" d_ftr")
SO, SD, WO, WD = off("S"), dfn("S"), off("W"), dfn("W"); SN, WN = SO + SD, WO + WD
singles = np.column_stack([g(f"{t} {k}") for t in "SW" for k in ["efg","tov","orb","ftr","d_efg","d_tov","d_orb","d_ftr"]])
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
gap = Q.X30[:, names.index("gap")]
V = {"current 756 (30)": None,
     "+16 single four factors": singles,
     "+4 composites (S/W off, S/W def)": np.column_stack([SO, SD, WO, WD]),
     "+2 net composites (S net, W net)": np.column_stack([SN, WN]),
     "+1 net gap (S net - W net)": (SN - WN)[:, None],
     "+2 gaps (off gap, def gap)": np.column_stack([SO - WO, SD - WD]),
     "+2 matchups (S off-W def, W off-S def)": np.column_stack([SO - WD, WO - SD])}
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
    for nm, v in [("S off", SO), ("S def", SD), ("W off", WO), ("W def", WD), ("S net", SN), ("W net", WN), ("net gap", SN - WN), ("off gap", SO - WO), ("def gap", SD - WD)]:
        print(f"corr with rating gap  {nm:8} {np.corrcoef(v[k], gap[k])[0,1]:+.2f}")
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(4) as ex:
        for name, held, insr, ll, auc, rr, out in ex.map(job, V):
            res[name] = out
            print(f"{name:40} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | LL {ll:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
    base = res["current 756 (30)"]; yk = Q.yb[k]; c0 = (base[k] > 0) == yk
    for name, out in res.items():
        c1 = (out[k] > 0) == yk; print(f"vs current {name:40} gained {int((c1 & ~c0).sum())} lost {int((~c1 & c0).sum())}")

