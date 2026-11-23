# Screen the deep-run / absence measures: add each (gap, model side minus other side) to the current late-round line.
# Real games Sweet 16 -> title (240), each year held out. Also on Round 1 + Round of 32 for reference (absences matter there too).
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m302_full_brackets.py"), encoding="utf-8-sig").read(); src = src[:src.index("CACHE = {}")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
F = json.load(open(os.path.join(HERE, "m337_feats.json")))
KEYS = ["winpct_vs_field", "margin_vs_field", "margin_vs_top30", "late_margin_vs_field", "games_vs_field", "games_vs_top30", "close_winpct", "close_games",
        "star_mpg", "top2_minutes_share", "star_close_minutes_ratio", "absent_minutes_share", "absent_points_share", "top_scorer_absent"]
def other(i): g = G[i]; return g["dog"] if kk(g["fav"]) == kk(B.Sname[i]) else g["fav"]
def gap(i, key):
    s = seas[i]; a = (F.get(s, {}).get(kk(B.Sname[i])) or {}).get(key); b = (F.get(s, {}).get(kk(other(i))) or {}).get(key)
    return np.nan if a is None or b is None else a - b
fit = Q.t_ridge(X=XX); LATE_ = Q.S16 | Q.E8 | Q.F4T; EARLY_ = np.isin(RND, ["First round", "Second round"])
def heldout(mask, extra=None, target=None):
    tgt = np.where((mask if target is None else target) & k)[0]; p = np.zeros(len(tgt))
    for s in SEASONS:
        te = tgt[seas[tgt] == s]
        if len(te) == 0: continue
        tr = np.where((seas != s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); a_ = mask[tr]; pos = np.searchsorted(tgt, te)
        cols_tr = [m_tr[a_], Q.EX[tr][a_]]; cols_te = [m_te, Q.EX[te]]
        if extra is not None:
            mu = np.nanmean(extra[tr][a_]); sd = np.nanstd(extra[tr][a_]) + 1e-9; e = np.nan_to_num((extra - mu) / sd)
            cols_tr.append(e[tr][a_]); cols_te.append(e[te])
        f = R.wlr(np.column_stack(cols_tr), y_[tr][a_], WT[tr][a_]); p[pos] = 1 / (1 + np.exp(-f(np.column_stack(cols_te))))
    return tgt, p
def score(tgt, p):
    yy = y_[tgt]; return int(((p >= .5) == (yy == 1)).sum()), float(-np.mean(yy * np.log(p) + (1 - yy) * np.log(1 - p)))
for lab, mask in (("SWEET 16 ONLY (real games; line still trained on Sweet 16 -> title)", LATE_),):
    tgt, p0 = heldout(mask, target=Q.S16); r0, l0 = score(tgt, p0)
    print(f"\n{lab}: {len(tgt)} games | current model {r0} right, log loss {l0:.4f}")
    print(f"{'measure (gap)':28} | coverage | +games | log loss change (negative = better) | weight z (all years)")
    res = []
    for key in KEYS:
        v = np.array([gap(i, key) for i in range(len(G))], float)
        cov = int(np.isfinite(v[tgt]).sum())
        t2, p = heldout(mask, v, target=Q.S16); r, l = score(t2, p)
        # z of the added weight, fit on all years
        tr = np.where(mask & k)[0]; mu = np.nanmean(v[tr]); sd = np.nanstd(v[tr]) + 1e-9; e = np.nan_to_num((v - mu) / sd)
        m_all, _ = Q.base(tr, tr[:1], fit)
        A = np.column_stack([np.ones(len(tr)), m_all, Q.EX[tr], e[tr]]); yy = y_[tr]; b = np.zeros(A.shape[1])
        for _ in range(30):
            q = 1 / (1 + np.exp(-A @ b)); H_ = A.T @ (A * (q * (1 - q))[:, None]) + 1e-6 * np.eye(A.shape[1]); b += np.linalg.solve(H_, A.T @ (yy - q))
        z = b[-1] / np.sqrt(np.linalg.inv(H_)[-1, -1])
        res.append((key, cov, r - r0, l - l0, z))
    for key, cov, d, dl, z in sorted(res, key=lambda t: t[3]): print(f"{key:28} | {cov:4} | {d:+3d} | {dl:+.4f} | {z:+.2f}")

