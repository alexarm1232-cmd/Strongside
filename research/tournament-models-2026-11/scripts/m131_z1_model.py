# Model with every candidate measure at z >= 1 (and >= 1.4, and the current >= 2-ish report set for reference), on top of
# the 3 strength inputs. Two ways: all of them, and through the same overlap rule as the 27 (|r| < 0.3 with strength
# and with measures already kept, in z order). Exact 756 pipeline, each tournament held out, First Four out.
import os, sys, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
ns = {"__file__": os.path.join(Q.OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(Q.OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS, STR, kept, zrep = ns["X"], ns["KS"], ns["STR"], ns["kept"], ns["zrep"]
C = np.corrcoef(X.T); z = {c: abs(zrep.get(KS[c], (0, 0))[0]) for c in range(len(KS)) if c not in STR}
def dedup(cand):
    out = []
    for c in sorted(cand, key=lambda c: -z[c]):
        if max(abs(C[c, s]) for s in STR) >= 0.3: continue
        if all(abs(C[c, k]) < 0.3 for k in out): out.append(c)
    return out
S3 = Q.X30[:, :3]
V = {"current 756 (30)": Q.X30}
for th in (1.0, 1.4):
    cand = [c for c in z if z[c] >= th]
    V[f"z >= {th}: all {len(cand)} measures"] = np.column_stack([S3, X[:, cand]])
    d = dedup(cand); V[f"z >= {th}: overlap rule, {len(d)} measures"] = np.column_stack([S3, X[:, d]])
def job(name):
    XX = V[name]; fit = Q.t_ridge(X=XX); keep = ~Q.FF; out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & keep)[0]; te = np.where((Q.seas == s) & keep)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(keep)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[keep]; held = int(((out[keep] > 0) == yk).sum()); insr = int(((ins > 0) == Q.yb[tr]).sum())
    s_ = out[keep]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1; auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    rr = [int(((out[keep & (Q.RND == r)] > 0) == Q.yb[keep & (Q.RND == r)]).sum()) for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]]
    return name, held, insr, auc, rr, out
if __name__ == "__main__":
    print("inputs:", {k: v.shape[1] for k, v in V.items()})
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(5) as ex:
        for name, held, insr, auc, rr, out in ex.map(job, V):
            res[name] = out; print(f"{name:40} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
    k = ~Q.FF; yk = Q.yb[k]; c0 = (res["current 756 (30)"][k] > 0) == yk
    for name, out in res.items():
        c1 = (out[k] > 0) == yk; print(f"vs current {name:40} gained {int((c1 & ~c0).sum())} lost {int((~c1 & c0).sum())}")
