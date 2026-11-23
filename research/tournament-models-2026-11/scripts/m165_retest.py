# Retest after the steals/blocks fix. Exact 756 pipeline (ridge lam 30, half-life 12, base held out inside training,
# round lines with who plays + coach/star, 85% simulator in F4/title, First Four out, each tournament held out).
#   A) the original model as it was (backup data)        B) the same 27 measures, corrected data
#   C) the re-selected measures on corrected data (the selection rule rerun on the corrected report)
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m99_model_types as Q
OLD = Q.OLD
ns = {"__file__": os.path.join(OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS, STR = ns["X"], ns["KS"], ns["STR"]
old_names = [str(n) for n in np.load(os.path.join(OLD, "_before_stl_fix", "m3_data.npz"), allow_pickle=True)["names"]]
new_names = [str(n) for n in np.load(os.path.join(OLD, "m3_data.npz"), allow_pickle=True)["names"]]
XB = np.column_stack([X[:, KS.index(n)] for n in old_names]); XC = Q.X30
OLD_F = np.load(os.path.join(OLD, "_before_stl_fix", "m9_whoplays.npy")); NEW_F = Q.M.F.copy()
OLD_X = np.load(os.path.join(OLD, "_before_stl_fix", "m3_data.npz"), allow_pickle=True)["X"]
k = ~Q.FF; RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
def job(name):
    XX, F = {"A) original model (before the fix)": (OLD_X, OLD_F), "B) same 27 measures, corrected data": (XB, NEW_F),
             f"C) re-selected {len(new_names) - 3} measures, corrected data": (XC, NEW_F)}[name]
    Q.M.F[:] = F
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    p = np.clip(1 / (1 + np.exp(-out[k])), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(yk, np.log(p), np.log(1 - p))))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in RN]
    m1011 = k & np.isin(Q.seas, ["2009-10", "2010-11"])
    return name, held, insr, auc, ll, rr, int(((out[m1011] > 0) == Q.yb[m1011]).sum()), int(m1011.sum()), out
if __name__ == "__main__":
    print("selected now:", new_names[3:])
    from concurrent.futures import ProcessPoolExecutor
    names = ["A) original model (before the fix)", "B) same 27 measures, corrected data", f"C) re-selected {len(new_names) - 3} measures, corrected data"]
    res = {}
    with ProcessPoolExecutor(3) as ex:
        for name, held, insr, auc, ll, rr, r1011, n1011, out in ex.map(job, names):
            res[name] = out
            print(f"{name:42} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | LL {ll:.4f} | by round {'/'.join(map(str, rr))} | 2010+2011 {r1011}/{n1011}", flush=True)
    yk = Q.yb[k]; a = (res[names[0]][k] > 0) == yk
    for n in names[1:]:
        b = (res[n][k] > 0) == yk; print(f"vs original: {n:42} gained {int((b & ~a).sum())} lost {int((~b & a).sum())}")
    np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m165_outs.npy"), np.array([res[n] for n in names]))
