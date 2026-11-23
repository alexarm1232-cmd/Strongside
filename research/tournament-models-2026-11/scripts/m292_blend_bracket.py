# Brackets filled out before Round 1 with weighted blends (no simulator needed in the Round of 32 blends tested here).
#   Round 1 options: Upset Model @40 | 0.5 upset + 0.25 model + 0.25 sim @45 | thirds @45
#   Round of 32 options: R32 Upset Model @45 | 0.4 R32 upset + 0.6 regular model @42 | 0.5 / 0.5 @42
import os, sys, json, contextlib, io, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m282_bracket_r1r2.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
sig = lambda z: 1 / (1 + np.exp(-z))
R1P = {}   # gid -> (upset, model, sim) chance the LOWER seed wins
for r, p in zip(D186["rows"], pho):
    i = r["i"]; hs = r["HisS"]; R1P[str(G[i]["gid"])] = (float(p), float(sig(-OUT_I[i]) if hs else sig(OUT_I[i])), float(1 - B.simS[i] if hs else B.simS[i]))
R1OPT = {"Upset @40": ((1, 0, 0), .40), "1/2 upset + 1/4 + 1/4 @45": ((.5, .25, .25), .45), "thirds @45": ((1 / 3, 1 / 3, 1 / 3), .45)}
def r1picks(s, w, c):
    out = []
    for g in BI[s]["games"]:
        if g["H"] == g["L"]: out.append(g["H"]); continue
        u, m, si = R1P[str(g["gid"])]; p = w[0] * u + w[1] * m + w[2] * si; out.append(g["L"] if p >= c else g["H"])
    return out
PICKS = {lab: {s: r1picks(s, *v) for s in SEASONS} for lab, v in R1OPT.items()}
pairs = {s: sorted({(pk[s][2 * q], pk[s][2 * q + 1]) for pk in PICKS.values() for q in range(16)}) for s in SEASONS}
json.dump({s: [list(x) for x in v] for s, v in pairs.items()}, open(os.path.join(HERE, "m292_pairs.json"), "w"))
print(subprocess.run([sys.executable, os.path.join(HERE, "m292_upset_pairs.py")], capture_output=True, text=True).stdout.strip())
UPP = json.load(open(os.path.join(HERE, "m292_upset_p.json")))
# regular model chance for every pair (held-out fit per season, Round 1-2 line without who plays)
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
def r32_pick(s, a, b, wu, wm, c):
    h, l, pu = UPP[f"{s}|{a}|{b}"]
    S_, W_, z = MZ[(s, a, b)]; pS = float(sig(z)); pm = pS if kk(l) == S_ else 1 - pS     # model's chance the lower seed (l) wins
    p = wu * pu + wm * pm
    return l if p >= c else h
R32OPT = {"R32 Upset @45": (1, 0, .45), "0.4 upset + 0.6 model @42": (.4, .6, .42), "0.5 upset + 0.5 model @42": (.5, .5, .42)}
print(f"\n{'Round 1':30} {'Round of 32':30} points | R1 | R32")
RES = {}
for l1 in R1OPT:
    for l2, (wu, wm, c) in R32OPT.items():
        r1 = r2 = 0; yr = []
        for s in SEASONS:
            games = BI[s]["games"]; wins = BI[s]["wins"]; pk = PICKS[l1][s]; a1 = sum(p == g["won"] for p, g in zip(pk, games) if g["H"] != g["L"])
            a2 = sum(wins.get(r32_pick(s, pk[2 * q], pk[2 * q + 1], wu, wm, c), 0) >= 2 for q in range(16)); r1 += a1; r2 += a2; yr.append(a1 + 2 * a2)
        RES[(l1, l2)] = yr; print(f"{l1:30} {l2:30} {r1 + 2 * r2:6} | {r1} | {r2}")
json.dump({f"{a} || {b}": v for (a, b), v in RES.items()}, open(os.path.join(HERE, "m292_by_year.json"), "w"))
