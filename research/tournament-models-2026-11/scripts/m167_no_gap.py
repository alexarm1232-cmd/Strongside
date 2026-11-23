# Drop the rating gap, keep rating gap x pace (and schedule gap). Corrected data. Exact 756 pipeline.
#  1) the original 27 measures + sos gap + gap x pace (29 inputs)
#  2) full rebuild: the selection rule (report measures in z order, drop overlap with the strength inputs at |r| >= 0.3,
#     one per overlap group) rerun with strength = sos gap + gap x pace only
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m99_model_types as Q
OLD = Q.OLD
ns = {"__file__": os.path.join(OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS, STR, REPORT, zrep = ns["X"], ns["KS"], ns["STR"], ns["REPORT"], ns["zrep"]
C = np.corrcoef(X.T)
def select(strength):
    out = []
    for c in sorted(REPORT, key=lambda c: -zrep.get(KS[c], (0, 0))[0]):
        if max(abs(C[c, s]) for s in strength) >= 0.3: continue
        if all(abs(C[c, k_]) < 0.3 for k_ in out): out.append(c)
    return out
iG = next(c for c in STR if KS[c] == "gap"); rest = [c for c in STR if c != iG]
old_names = [str(n) for n in np.load(os.path.join(OLD, "_before_stl_fix", "m3_data.npz"), allow_pickle=True)["names"]]
m27 = old_names[3:]
rebuilt = [KS[c] for c in select(rest)]
V = {"original 30 (gap + gap x pace)": ["gap", "sos gap", "gap x possessions"] + m27,
     "original 27, no rating gap (29)": ["sos gap", "gap x possessions"] + m27,
     f"full rebuild, no rating gap ({2 + len(rebuilt)})": ["sos gap", "gap x possessions"] + rebuilt}
k = ~Q.FF; RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
def job(name):
    XX = np.column_stack([X[:, KS.index(n)] for n in V[name]]); fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    p = np.clip(1 / (1 + np.exp(-out[k])), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(yk, np.log(p), np.log(1 - p))))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in RN]
    return name, held, insr, auc, ll, rr, out
if __name__ == "__main__":
    print("full rebuild picks", len(rebuilt), "measures | same as the original 27:", set(rebuilt) == set(m27))
    print("   added:", [n for n in rebuilt if n not in m27], "| dropped:", [n for n in m27 if n not in rebuilt])
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(3) as ex:
        for name, held, insr, auc, ll, rr, out in ex.map(job, V):
            res[name] = out
            print(f"{name:36} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | LL {ll:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
    yk = Q.yb[k]; a = (res["original 30 (gap + gap x pace)"][k] > 0) == yk
    for n in list(V)[1:]:
        b = (res[n][k] > 0) == yk; print(f"vs original 30: {n:36} gained {int((b & ~a).sum())} lost {int((~b & a).sum())}")
