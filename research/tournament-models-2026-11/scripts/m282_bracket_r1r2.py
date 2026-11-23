# Brackets filled out before Round 1, Rounds 1-2 only, scored against what happened (R1 = 1 pt, R32 = 2 pts), 2010-2026.
#   higher seed | regular model (patched: who plays in Round 1 only; Round of 32 = shared line without who plays)
#   | simulator (from m283 results, if present) | upset models (R64 @40 -> R32 standalone @45, from m274)
# Each picker picks its Round 1 winners, then picks the Round of 32 game between ITS OWN winners. Favored team wins;
# a dead pick'em goes to the higher seed. Regular model: each year scored by a model trained on the other 15.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "m281_pair_features.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src.split("# validate on every")[0])
R = Q.R; WT, y_ = Q.WT, Q.y_; E12 = Q.E12
CF = np.load(os.path.join(Q.OLD, "coach_feats.npy")); CC = json.load(open(os.path.join(Q.OLD, "coach_cols.json")))
# ---- coach + star extras for any pair; check against the real Round 1 rows
COACH = {}
for i, g in enumerate(G):
    if g["rnd"] != "First round": continue
    for side in ("fav", "dog"):
        COACH[(g["season"], kk(g[side]))] = [CF[i, CC.index(f"{side} car_ncaa")], CF[i, CC.index(f"{side} rec5_s16")]]
for i, g in enumerate(G):
    if g["rnd"] == "Second round":
        for side in ("fav", "dog"): COACH.setdefault((g["season"], kk(g[side])), [CF[i, CC.index(f"{side} car_ncaa")], CF[i, CC.index(f"{side} rec5_s16")]])
def ex_of(s, S_, W_):
    a, b = COACH[(s, S_)], COACH[(s, W_)]; cg = [a[j] - b[j] for j in range(2)]; cg = [c if np.isfinite(c) else 0.0 for c in cg]
    return np.array(cg + [value(s, S_, "S", "star_usage_rate")[0] - value(s, W_, "W", "star_usage_rate")[0]])
ok = n = 0
for i in range(N):
    if k[i] and RND[i] == "First round":
        n += 1; ok += np.allclose(ex_of(seas[i], Sn[i], Wn[i]), Q.EX[i], atol=1e-6)
print(f"coach + star rebuilt = real Round 1 rows: {ok}/{n}")
# ---- bracket data
t = open(os.path.join(HERE, "m242_bracket_in.js"), encoding="utf-8").read(); BI = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
SEASONS = sorted(BI)
OUT_I = np.load(os.path.join(HERE, "m262_model_pre_I.npy"))     # patched model, Round 1 (who plays) held out
gid2i = {str(g["gid"]): i for i, g in enumerate(G)}
seed_of = lambda s, tm: next((g["sH"] if g["H"] == tm else g["sL"]) for g in BI[s]["games"] if tm in (g["H"], g["L"]))
def r1_model_pick(s, g):
    if g["H"] == g["L"]: return g["H"]
    i = gid2i[str(g["gid"])]; z = OUT_I[i]
    if z == 0: return g["H"]
    return kk(B.Sname[i]) if z > 0 else Wn[i]
# Round of 32 chances for any pair: one held-out fit per season
NEWROWS = []; REQ = []
def need(s, a, b):
    S_, W_, x, _ = features(s, a, b); NEWROWS.append(x); REQ.append((s, a, b, S_, W_, ex_of(s, S_, W_)))
for s in SEASONS:
    W1 = {}
    pk = [r1_model_pick(s, g) for g in BI[s]["games"]]
    for p in range(16): need(s, kk(pk[2 * p]), kk(pk[2 * p + 1]))
Xext = np.vstack([XX, np.array(NEWROWS)]); fit = Q.t_ridge(X=Xext); PZ = {}
for s in SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.array([N + j for j, r in enumerate(REQ) if r[0] == s])
    m_tr, m_te = Q.base(tr, te, fit); a = E12[tr]
    f = R.wlr(np.column_stack([m_tr[a], Q.EX[tr][a]]), y_[tr][a], WT[tr][a])
    z = f(np.column_stack([m_te, np.array([REQ[j - N][5] for j in te])]))
    for j, zz in zip(te, z): r = REQ[j - N]; PZ[(s, r[1], r[2])] = (r[3], r[4], float(zz))
def r32_model_pick(s, a, b):
    S_, W_, z = PZ[(s, kk(a), kk(b))]
    if abs(z) < 1e-12: return a if seed_of(s, a) <= seed_of(s, b) else b
    win = S_ if z > 0 else W_
    return a if kk(a) == win else b
# ---- score
def score(r1pick, r32pick):
    r1 = r32 = 0; rows = []
    for s in SEASONS:
        games = BI[s]["games"]; wins = BI[s]["wins"]; pk = []
        for g in games:
            p = r1pick(s, g); pk.append(p)
            if g["H"] != g["L"]: r1 += p == g["won"]
        for q in range(16):
            a, b = pk[2 * q], pk[2 * q + 1]; w = r32pick(s, a, b); r32 += wins.get(w, 0) >= 2
    return r1, r32, r1 + 2 * r32
chalk1 = lambda s, g: g["H"]
chalk2 = lambda s, a, b: a if seed_of(s, a) <= seed_of(s, b) else b
RES = {"Higher seed": score(chalk1, chalk2), "Regular model (patched)": score(r1_model_pick, r32_model_pick)}
# simulator, if m283 results exist
SIMF = os.path.join(HERE, "m283_sim_r32.json")
if os.path.exists(SIMF):
    SR = json.load(open(SIMF))   # {season: {"a|b": win% for a}}
    def r1_sim_pick(s, g):
        if g["H"] == g["L"]: return g["H"]
        p = g.get("simH")
        i = gid2i[str(g["gid"])]; pS = B.simS[i]; S_ = kk(B.Sname[i]); pH = pS if S_ == g["H"] else 1 - pS
        return g["H"] if pH >= 0.5 else g["L"]
    def r32_sim_pick(s, a, b):
        p = SR[s].get(f"{a}|{b}");
        if p is None: p = 1 - SR[s][f"{b}|{a}"]
        if abs(p - 0.5) < 1e-9: return chalk2(s, a, b)
        return a if p > 0.5 else b
    RES["Simulator"] = score(r1_sim_pick, r32_sim_pick)
else:
    # write the pairs the simulator bracket needs
    need_pairs = {}
    for s in SEASONS:
        pk = []
        for g in BI[s]["games"]:
            if g["H"] == g["L"]: pk.append(g["H"]); continue
            i = gid2i[str(g["gid"])]; pS = B.simS[i]; S_ = kk(B.Sname[i]); pH = pS if S_ == g["H"] else 1 - pS
            pk.append(g["H"] if pH >= 0.5 else g["L"])
        need_pairs[s] = [[pk[2 * q], pk[2 * q + 1]] for q in range(16)]
    json.dump(need_pairs, open(os.path.join(HERE, "m283_sim_pairs.json"), "w"))
    print("simulator Round 1 picks right:", sum(1 for s in SEASONS for g, p in zip(BI[s]["games"], [x for q in need_pairs[s] for x in q]) if g["H"] != g["L"] and p == g["won"]))
print(f"\n{'Bracket (filled out before Round 1)':34} | R1 right /511 | R32 right /256 | points (R1 x1 + R32 x2)")
for lab, (a, b, p) in RES.items(): print(f"{lab:34} | {a:4} | {b:4} | {p}")
print(f"{'Upset models (m274: R64 @40, R32 @45)':34} |  400 |  172 | 744")
