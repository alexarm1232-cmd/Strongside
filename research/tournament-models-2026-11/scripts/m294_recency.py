# Choose the blend (Round 1 weights of upset / regular / simulator + cutoff; Round of 32 weight of upset vs regular + cutoff)
# with recent tournaments counting more. Year weight = 0.5 ** ((2026 - year) / half_life). Bracket points (R1 x1, R32 x2).
# Honest check: for each year 2015-2026, choose the blend from the EARLIER years only (recency-weighted), score that year.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m292_blend_bracket.py"), encoding="utf-8-sig").read(); src = src[:src.index("PICKS = {")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
import subprocess
# all four possible Round of 32 pairs per pod
pairs = {}
for s in SEASONS:
    g = BI[s]["games"]; pairs[s] = []
    for q in range(16):
        A = [g[2 * q]["H"]] if g[2 * q]["H"] == g[2 * q]["L"] else [g[2 * q]["H"], g[2 * q]["L"]]
        Bb = [g[2 * q + 1]["H"]] if g[2 * q + 1]["H"] == g[2 * q + 1]["L"] else [g[2 * q + 1]["H"], g[2 * q + 1]["L"]]
        pairs[s] += [[a, b] for a in A for b in Bb]
json.dump(pairs, open(os.path.join(HERE, "m292_pairs.json"), "w"))
print(subprocess.run([sys.executable, os.path.join(HERE, "m292_upset_pairs.py")], capture_output=True, text=True).stdout.strip())
UPP = json.load(open(os.path.join(HERE, "m292_upset_p.json")))
NEW = []; RQ = []
for s, prs in pairs.items():
    for a, b in prs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); NEW.append(x); RQ.append((s, a, b, S_, W_, ex_of(s, S_, W_)))
Xe = np.vstack([XX, np.array(NEW)]); fit2 = Q.t_ridge(X=Xe); MZ = {}
for s in SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.array([N + j for j, r in enumerate(RQ) if r[0] == s])
    m_tr, m_te = Q.base(tr, te, fit2); a_ = E12[tr]
    f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
    z = f(np.column_stack([m_te, np.array([RQ[j - N][5] for j in te])]))
    for j, zz in zip(te, z): r = RQ[j - N]; MZ[(s, r[1], r[2])] = (r[3], r[4], float(zz))
W1 = [(a / 10, b / 10, round(1 - a / 10 - b / 10, 1)) for a in range(11) for b in range(11 - a)]; C1 = [c / 100 for c in range(35, 56)]
W2 = [a / 10 for a in range(11)]; C2 = [c / 100 for c in range(35, 56)]
O1 = [(w, c) for w in W1 for c in C1]; O2 = [(w, c) for w in W2 for c in C2]
YEARS = [int(s[:4]) + 1 for s in SEASONS]; PTS = {}
for s in SEASONS:
    g = BI[s]["games"]; wins = BI[s]["wins"]
    U = np.array([R1P[str(x["gid"])] if x["H"] != x["L"] else (0, 0, 0) for x in g]); bye = np.array([x["H"] == x["L"] for x in g])
    lowwon = np.array([x["won"] == x["L"] and x["H"] != x["L"] for x in g])
    r1pts = np.zeros(len(O1)); sel = np.zeros((len(O1), 32), bool)    # sel = picked the lower seed
    for oi, (w, c) in enumerate(O1):
        p = U @ np.array(w); pk = (p >= c) & ~bye; sel[oi] = pk; r1pts[oi] = ((pk == lowwon) & ~bye).sum()
    # pair index per pod: 2*(first game picked low) + (second picked low), adjusted for byes
    corr = np.zeros((len(O2), 16, 4))
    for q in range(16):
        A = [g[2 * q]["H"]] if bye[2 * q] else [g[2 * q]["H"], g[2 * q]["L"]]; Bb = [g[2 * q + 1]["H"]] if bye[2 * q + 1] else [g[2 * q + 1]["H"], g[2 * q + 1]["L"]]
        for ia, a in enumerate(A):
            for ib, b in enumerate(Bb):
                h, l, pu = UPP[f"{s}|{a}|{b}"]; S_, W_, z = MZ[(s, a, b)]; pS = 1 / (1 + np.exp(-z)); pm = pS if kk(l) == S_ else 1 - pS
                for oj, (wu, c) in enumerate(O2):
                    pick = l if wu * pu + (1 - wu) * pm >= c else h; corr[oj, q, ia * 2 + ib] = wins.get(pick, 0) >= 2
    idx = sel[:, 0::2].astype(int) * 2 + sel[:, 1::2].astype(int)                  # (O1, 16)
    r32 = np.stack([corr[:, q, :][:, idx[:, q]] for q in range(16)]).sum(0).T     # (O1, O2)
    PTS[s] = r1pts[:, None] + 2 * r32
TOT = sum(PTS.values())
def best(wts, years):
    M = sum(wts[j] * PTS[s] for j, s in enumerate(SEASONS) if s in years); i, j = np.unravel_index(np.argmax(M), M.shape); return i, j
def show(lab, i, j):
    print(f"{lab:38} R1 {O1[i][0]} @ {O1[i][1]:.2f} | R32 upset {O2[j][0]:.1f} / regular {1 - O2[j][0]:.1f} @ {O2[j][1]:.2f} | all 16 years: {int(TOT[i, j])} points")
cur_i = O1.index(((1 / 3 * 0 + .3, .3, .4), .45)) if False else None
print(f"current blend (thirds @45, 50/50 @42): {int(TOT[O1.index((W1[[k_ for k_, w in enumerate(W1) if w == (0.3, 0.3, 0.4)][0]], .45)), O2.index((.5, .42))])} (thirds approximated as 0.3/0.3/0.4 on the 0.1 grid)")
for hl in (None, 12, 8, 6, 4):
    wts = [1.0] * 16 if hl is None else [0.5 ** ((2026 - y) / hl) for y in YEARS]
    i, j = best(wts, set(SEASONS)); show(f"best, {'equal years' if hl is None else f'half-life {hl} years'}", i, j)
    # honest forward: choose from earlier years only, score the next year
    f_pts = 0; base = 0
    for t, s in enumerate(SEASONS):
        if YEARS[t] < 2015: continue
        prev = set(SEASONS[:t]); w_ = [1.0] * 16 if hl is None else [0.5 ** ((YEARS[t] - 1 - y) / hl) for y in YEARS]
        i2, j2 = best(w_, prev); f_pts += PTS[s][i2, j2]
        base += PTS[s][O1.index(((1.0, 0.0, 0.0), .40)), O2.index((1.0, .45))]
    print(f"      forward test 2015-2026 (choose from earlier years only): {int(f_pts)} points | upset models (40/45) same years: {int(base)}")
