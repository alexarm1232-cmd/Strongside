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
def heldout(mask, extra=None):
    tgt = np.where(mask & k)[0]; p = np.zeros(len(tgt))
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
netv = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
ng = np.array([netv(seas[i], B.Sname[i]) - netv(seas[i], other(i)) for i in range(len(G))], float)
for lab, mask in (("Round 1 + Round of 32", EARLY_), ("Sweet 16 -> title", LATE_)):
    tgt, p0 = heldout(mask); r0, l0 = score(tgt, p0); t2, p1_ = heldout(mask, ng); r1_, l1 = score(t2, p1_)
    zm = np.log(p0 / (1 - p0)); c = np.corrcoef(zm, ng[tgt])[0, 1]
    sim = np.array([B.simS[i] for i in tgt]); cs_ = np.corrcoef(np.log(sim / (1 - sim)), ng[tgt])[0, 1]
    print(f"{lab}: {len(tgt)} games | corr(model, net gap) {c:+.2f} | corr(simulator, net gap) {cs_:+.2f} | model {r0} right -> + net gap {r1_} | log loss {l0:.4f} -> {l1:.4f}")
