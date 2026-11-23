# Majority vote of the three pickers (upset models, regular model patched, simulator), Rounds 1-2.
# (a) Bracket filled out before Round 1: vote on each Round 1 game; then on the vote bracket's own Round of 32 games.
# (b) Real games: vote on every real Round 1 and Round of 32 game.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m282_bracket_r1r2.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D = json.load(open(os.path.join(HERE, "m285_brackets.json"))); VP = json.load(open(os.path.join(HERE, "m289_vote_pairs.json")))
UPX = json.load(open(os.path.join(HERE, "m289_upset_r32.json"))); SR = json.load(open(os.path.join(HERE, "m283_sim_r32.json")))
# regular model chances for the vote pairs (same held-out fit as m282)
NEW = []; RQ = []
for s, prs in VP.items():
    for a, b in prs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); NEW.append(x); RQ.append((s, a, b, S_, W_, ex_of(s, S_, W_)))
Xe = np.vstack([XX, np.array(NEW)]); fit2 = Q.t_ridge(X=Xe); MZ = {}
for s in SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.array([N + j for j, r in enumerate(RQ) if r[0] == s])
    m_tr, m_te = Q.base(tr, te, fit2); a_ = E12[tr]
    f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
    z = f(np.column_stack([m_te, np.array([RQ[j - N][5] for j in te])]))
    for j, zz in zip(te, z): r = RQ[j - N]; MZ[(s, r[1], r[2])] = (r[3], r[4], float(zz))
def model_pick(s, a, b):
    S_, W_, z = MZ[(s, a, b)]
    if abs(z) < 1e-12: return chalk2(s, a, b)
    w = S_ if z > 0 else W_; return a if kk(a) == w else b
def sim_pick(s, a, b):
    p = SR[s].get(f"{a}|{b}"); p = p if p is not None else 1 - SR[s][f"{b}|{a}"]
    return chalk2(s, a, b) if abs(p - .5) < 1e-9 else (a if p > .5 else b)
vote = lambda v: max(set(v), key=v.count)
tot = [0, 0]; YR = []
for d in D:
    s = d["season"]; pk = []; r1 = r2 = 0
    for j, g in enumerate(d["games"]):
        p = vote([d["brackets"][x]["r1"][j]["pick"] for x in ("upset", "model", "sim")]); pk.append(p)
        if not g["bye"]: r1 += p == g["won"]
    for q in range(16):
        a, b = pk[2 * q], pk[2 * q + 1]; assert [a, b] == VP[s][q]
        w = vote([UPX["vote_r32_upset_pick"][s][q], model_pick(s, a, b), sim_pick(s, a, b)]); r2 += w == d["r2won"][q]
    tot[0] += r1; tot[1] += r2; YR.append((d["year"], r1, r2, r1 + 2 * r2))
print("BRACKET, majority vote of the 3:", tot[0], tot[1], tot[0] + 2 * tot[1])
for y, a, b, p in YR: print(f"   {y}: {a} {b} {p}")
# ---- real games
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"]); y1 = np.array(D186["y"])
OUT_G = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))
ok1 = 0; ag = 0
for r, p, yy in zip(D186["rows"], pho, y1):
    i = r["i"]; hS = r["HisS"]
    up = p >= .4; mo = (OUT_I[i] <= 0) if hS else (OUT_I[i] > 0); si = (B.simS[i] < .5) if hS else (B.simS[i] >= .5)
    v = (up + mo + si) >= 2; ok1 += v == (yy == 1); ag += (up == mo == si)
ok2 = 0; n2 = 0
for r in UPX["real"]:
    i = next(j for j, g in enumerate(G) if g["season"] == r["s"] and g["rnd"] == "Second round" and {kk(g["fav"]), kk(g["dog"])} == {kk(r["h"]), kk(r["l"])})
    hS = kk(B.Sname[i]) == kk(r["h"]); up = r["p"] >= .45; mo = (OUT_G[i] <= 0) if hS else (OUT_G[i] > 0); si = (B.simS[i] < .5) if hS else (B.simS[i] >= .5)
    v = (up + mo + si) >= 2; ok2 += v == (r["up"] == 1); n2 += 1
print(f"REAL GAMES, majority vote: Round 1 {ok1}/511 (all three agree in {ag}) | Round of 32 {ok2}/{n2}")
