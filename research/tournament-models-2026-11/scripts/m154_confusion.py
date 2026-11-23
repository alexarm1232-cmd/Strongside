# Confusion matrices like Andrew's slide 14: random forest (500 trees) trained on all other years, tested on his test
# years (2016 + 2026; and 2017 + 2025; his 2008 / 2009 are outside our data), cutoff 0.5. Pre-tournament stats + site
# pre-tournament ratings; full-season version for comparison; the 756 model on the same test games.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m153_imp_site_ratings as S
import numpy as np
from concurrent.futures import ProcessPoolExecutor
M, A, T, Q = S.M, S.A, S.T, S.A.Q
def build(which):
    RT = {s: S.Look(d) for s, d in S.site_rt(which).items()}
    BX = json.load(open(M.F.CACHE if which == "full" else A.CACHE)); Xr, yr, sr, rows, hi = [], [], [], [], []
    for i, g in enumerate(A.G):
        if g["rnd"] != "First round" or g["fseed"] == g["dseed"]: continue
        a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        H, L, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); hw = g["fav_won"] if H == a else not g["fav_won"]
        vh, vl = M.team_vars_full(g["season"], H, sH, BX, RT), M.team_vars_full(g["season"], L, sL, BX, RT)
        Xr.append(np.array(vh) - np.array(vl)); yr.append(int(hw)); sr.append(g["season"]); rows.append(i); hi.append(H == A.B.Sname[i])
    return np.array(Xr, float), np.array(yr), np.array(sr), np.array(rows), np.array(hi)
def job(args):
    which, test = args; X, y, sr, rows, hi = build(which); te = np.where(np.isin(sr, test))[0]; tr = np.where(~np.isin(sr, test))[0]
    trees, _, _ = A.forest(X, y, tr, ntree=500, seed=7); p = A.rfp(trees, X, te)
    return which, test, te.tolist(), p.tolist(), y[te].tolist(), T.auc(p, y[te])
def cm(pred, yy):
    pred, yy = np.asarray(pred), np.asarray(yy)
    a, b = int(((pred == 0) & (yy == 0)).sum()), int(((pred == 0) & (yy == 1)).sum()); c, d = int(((pred == 1) & (yy == 0)).sum()), int(((pred == 1) & (yy == 1)).sum())
    return a, b, c, d
if __name__ == "__main__":
    X, y, sr, rows, hi = build("pre")
    k = ~Q.FF; fit = Q.t_ridge(); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    mod = np.where(hi, out[rows], -out[rows])
    tests = [["2015-16", "2025-26"], ["2016-17", "2024-25"]]
    with ProcessPoolExecutor(4) as ex: R = list(ex.map(job, [(w, t) for w in ("pre", "full") for t in tests]))
    def show(title, pred, yy, aucv):
        a, b, c, d = cm(pred, yy); n = a + b + c + d
        print(f"{title}\n              actual 0  actual 1\n  predict 0   {a:8d}  {b:8d}\n  predict 1   {c:8d}  {d:8d}")
        print(f"  right {a + d}/{n} | misclassification {(b + c) / n:.4f} | sensitivity (higher seed wins called) {d / (b + d):.4f} | specificity (upsets called) {a / (a + c):.4f} | AUC {aucv:.3f}")
    for which, test, te, p, yy, aucv in R:
        show(f"\n=== Random forest, {'PRE-tournament' if which == 'pre' else 'FULL-season'}, test {test}", (np.array(p) > .5).astype(int), yy, aucv)
        if which == "pre":
            te = np.array(te); show(f"--- 756 model on the same {len(te)} games", (mod[te] > 0).astype(int), y[te], T.auc(mod[te], y[te]))
            print(f"--- higher seed always: {int(y[te].sum())}/{len(te)} right")
