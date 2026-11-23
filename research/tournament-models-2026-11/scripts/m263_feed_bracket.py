# FEEDING test (separate from the Round of 32 Upset Model work). Everything pre-tournament.
#   Team table: every tournament team's season measures, taken from its Round 1 row (so nothing from tournament games).
#   R64 Upset Model: its held-out chance for every Round 1 game (m230_out, upset at 40%).
#   R32 Upset Model: style inputs (core 12 + 2 coach + 4 matchups), trained on real Round of 32 games of the other years,
#                    able to score ANY pair (predicted matchups), so it can fill a bracket.
#   Feeding: (1) R64 -> R32: each team's Round 1 win chance from the R64 Upset Model as R32 inputs;
#            (2) R32 -> R64 (joint pod pick): pick each pod's Sweet 16 team by P(win R1) x P(win R32), and its R1 game for it.
# Scored on the real Round of 32 games and as a bracket (Round 1 = 1 point a game, Round of 32 = 2 points), every year held out.
import os, sys, json, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RNDS"] = "First round"
src = open(os.path.join(HERE, "m256_r32_report.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("NM = list(POOL)")])   # rows, F (incl. volume 3s), G, ...
import numpy as np
kk = lambda s: (s or "").rstrip(". ")
CF = np.load(os.path.join(Q.OLD, "coach_feats.npy")); CC = json.load(open(os.path.join(Q.OLD, "coach_cols.json")))
BASES = sorted({k[2:] for k in F if k[:2] in ("H ", "L ") and ("H " + k[2:]) in F and ("L " + k[2:]) in F})
TEAM = {}
for j, r in enumerate(rows):
    if r["r"] != "First round": continue
    g = G[r["i"]]
    for sd in "HL":
        t = kk(r[sd]); d = {b: float(F[f"{sd} {b}"][j]) for b in BASES}
        cs = "fav" if r[sd] == g["fav"] else "dog"
        for c in CC:
            if c.startswith(cs + " "): d["coach " + c.split(" ", 1)[1]] = float(CF[r["i"], CC.index(c)])
        d["seed"] = r["s" + sd]; TEAM[(r["s"], t)] = d
for j, r in enumerate(rows):   # 2021 Oregon (Round 1 no-contest): season measures from its Round of 32 row
    if r["r"] != "Second round": continue
    g = G[r["i"]]
    for sd in "HL":
        t = kk(r[sd])
        if (r["s"], t) in TEAM: continue
        d = {b: float(F[f"{sd} {b}"][j]) for b in BASES}; cs = "fav" if r[sd] == g["fav"] else "dog"
        for c in CC:
            if c.startswith(cs + " "): d["coach " + c.split(" ", 1)[1]] = float(CF[r["i"], CC.index(c)])
        d["seed"] = r["s" + sd]; TEAM[(r["s"], t)] = d; print("added from Round of 32 row:", r["s"], t)
# R64 Upset Model held-out chance per Round 1 game -> each team's Round 1 win chance
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); R64 = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
P1 = {}
for r, p in zip(D186["rows"], R64): P1[(r["s"], kk(r["L"]))] = float(p); P1[(r["s"], kk(r["H"]))] = 1 - float(p)
t = open(os.path.join(HERE, "m242_bracket_in.js"), encoding="utf-8").read(); BI = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
SEASONS = sorted(BI)
# ---- pair features
CORE12 = ["H pt_d_share Post-Up", "H pt_ppp Big Cut & Roll", "L pt_share Post-Up", "L-H big_height", "H ftr", "H pt_d_ppp High-Low", "L pt_d_ppp Transition",
          "L pt_ppp Inside Out", "L-H pt_d_ppp Rim Attack", "L pt_share Mid-Range", "H exp", "H bench_minutes"]
COACH = ["L coach car_s16", "L-H coach rec5_s16"]
def raw(h, l, c):
    side, b = c.split(" ", 1); A, Bv = TEAM[h], TEAM[l]
    return Bv[b] - A[b] if side == "L-H" else (A[b] if side == "H" else Bv[b])
# real Round of 32 games from the bracket
def r1_winners(s):
    return [g["won"] for g in BI[s]["games"]]
REAL = []
for s in SEASONS:
    W = r1_winners(s); wins = BI[s]["wins"]
    for p in range(16):
        a, b = W[2 * p], W[2 * p + 1]
        if (s, a) not in TEAM or (s, b) not in TEAM: continue
        h, l = (a, b) if TEAM[(s, a)]["seed"] <= TEAM[(s, b)]["seed"] else (b, a)
        if TEAM[(s, h)]["seed"] == TEAM[(s, l)]["seed"]: continue
        REAL.append(dict(s=s, h=(s, h), l=(s, l), up=int(wins.get(l, 0) >= 2)))
yR = np.array([r["up"] for r in REAL]); sR = np.array([r["s"] for r in REAL]); nR = len(REAL)
print(f"real Round of 32 games rebuilt from the bracket: {nR}, {int(yR.sum())} lower-seed wins")
# matchup measures: z-scored products using the real-R32 H / L distributions
PTM = [("lower uses x higher leaks: Pick & Pop", "L pt_share Pick & Pop", "H pt_d_ppp Pick & Pop"), ("lower good at x higher leaks: Perimeter Cut", "L pt_ppp Perimeter Cut", "H pt_d_ppp Perimeter Cut"),
       ("lower uses x higher allows often: Perimeter Cut", "L pt_share Perimeter Cut", "H pt_d_share Perimeter Cut")]
STD = {}
for _, a, b in PTM:
    for c in (a, b): v = np.array([raw(r["h"], r["l"], c) for r in REAL]); STD[c] = (v.mean(), v.std() + 1e-12)
for c in ("L pt_ppp Rim Attack", "H pt_d_ppp Rim Attack", "H pt_ppp Rim Attack", "L pt_d_ppp Rim Attack"):
    v = np.array([raw(r["h"], r["l"], c) for r in REAL]); STD[c] = (v.mean(), v.std() + 1e-12)
zz = lambda h, l, c: (raw(h, l, c) - STD[c][0]) / STD[c][1]
def feats(h, l, feed=False, which="core"):
    v = [raw(h, l, c) for c in CORE12 + COACH]
    v += [zz(h, l, a) * zz(h, l, b) for _, a, b in PTM]
    v += [(zz(h, l, "L pt_ppp Rim Attack") + zz(h, l, "H pt_d_ppp Rim Attack")) - (zz(h, l, "H pt_ppp Rim Attack") + zz(h, l, "L pt_d_ppp Rim Attack"))]
    if feed:
        ph, pl = P1.get(h, .5), P1.get(l, .5)
        v += [ph, pl, pl - ph] if feed == "probs" else [pl - ph]
    return v
def ridge(X, y, w, lam=30.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(len(X))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (y - p)) - P @ b)
    return lambda Xq: 1 / (1 + np.exp(-(np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b)))
YEAR = np.array([int(s[:4]) + 1 for s in sR]); wR = 0.5 ** ((2026 - YEAR) / 12)
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
MODELS = {}
for lab, feed in (("R32 Upset Model (separate)", False), ("R32 Upset Model fed R64 chances (gap)", "gap"), ("R32 Upset Model fed R64 chances (both + gap)", "probs")):
    X = np.array([feats(r["h"], r["l"], feed) for r in REAL]); ph = np.zeros(nR); fits = {}
    for s in SEASONS:
        tr, te = sR != s, sR == s; f = ridge(X[tr], yR[tr], wR[tr]); fits[s] = f
        if te.any(): ph[te] = f(X[te])
    MODELS[lab] = (feed, fits, ph)
    print(f"   {lab:48} real R32 games held out: AUC {auc(ph, yR):.3f} | right @40 {int(((ph >= .4) == (yR == 1)).sum())} @50 {int(((ph >= .5) == (yR == 1)).sum())} / {nR}")
print(f"   {'higher seed every time':48} right {int((yR == 0).sum())}")
# ---- brackets
def pr32(model, s, a, b):
    feed, fits, _ = MODELS[model]
    h, l = (a, b) if TEAM[(s, a)]["seed"] <= TEAM[(s, b)]["seed"] else (b, a)
    if TEAM[(s, h)]["seed"] == TEAM[(s, l)]["seed"]: p_up = .5
    else: p_up = float(fits[s](np.array([feats((s, h), (s, l), feed)]))[0])
    return h, l, p_up
def bracket(r1pick, r32mode, cut=.4, model="R32 Upset Model (separate)"):
    pts = r1r = r32r = 0; ups = 0
    for s in SEASONS:
        games = BI[s]["games"]; wins = BI[s]["wins"]
        if r32mode == "joint":   # pick each pod's Sweet 16 team by P(win R1) x P(beat the likely R32 opponent)
            for p in range(16):
                g1, g2 = games[2 * p], games[2 * p + 1]
                teams = [(g1["H"], g1), (g1["L"], g1), (g2["H"], g2), (g2["L"], g2)]
                def pw1(tm, g): return 1.0 if g["H"] == g["L"] else P1.get((s, tm), .5)
                best = None
                for tm, g in teams:
                    og = g2 if g is g1 else g1; tot = 0
                    for om in {og["H"], og["L"]}:
                        h, l, pu = pr32(model, s, tm, om); pwin = pu if tm == l else 1 - pu; tot += pw1(om, og) * pwin
                    val = pw1(tm, g) * tot
                    if best is None or val > best[0]: best = (val, tm, g)
                _, champ, gch = best; og = g2 if gch is g1 else g1
                picks1 = {id(gch): champ, id(og): (og["L"] if (og["H"] != og["L"] and P1.get((s, og["L"]), 0) >= cut) else og["H"])}
                for g in (g1, g2):
                    pk = picks1[id(g)]; ok = pk == g["won"]
                    if g["H"] != g["L"]: r1r += ok; pts += ok
                ok2 = wins.get(champ, 0) >= 2; r32r += ok2; pts += 2 * ok2; ups += TEAM[(s, champ)]["seed"] > min(TEAM[(s, x)]["seed"] for x in (g1["H"], g1["L"], g2["H"], g2["L"]) if (s, x) in TEAM)
            continue
        pk1 = []
        for g in games:
            if g["H"] == g["L"]: pk1.append(g["H"]); continue
            pk = r1pick(s, g); pk1.append(pk); ok = pk == g["won"]; r1r += ok; pts += ok
        for p in range(16):
            a, b = pk1[2 * p], pk1[2 * p + 1]
            if r32mode == "chalk": w_ = a if TEAM[(s, a)]["seed"] <= TEAM[(s, b)]["seed"] else b
            else:
                h, l, pu = pr32(r32mode, s, a, b); w_ = l if pu >= cut else h; ups += w_ == l
            ok2 = wins.get(w_, 0) >= 2; r32r += ok2; pts += 2 * ok2
    return pts, r1r, r32r, ups
up40 = lambda s, g: g["L"] if P1.get((s, g["L"]), 0) >= .4 else g["H"]
chalk = lambda s, g: g["H"]
print("\nBRACKETS, every year held out (Round 1: 32 games x 1 pt; Round of 32: 16 picks x 2 pts; 16 years)")
print(f"{'Round 1 picks':28} {'Round of 32 picks':52} {'points':>6} | R1 right /511 | R32 right /256 | R32 upset picks")
for r1lab, r1f in (("higher seed", chalk), ("R64 Upset Model @40", up40)):
    for r32lab, mode, cut in (("higher seed", "chalk", .5), ("R32 Upset Model (separate) @40", "R32 Upset Model (separate)", .4), ("R32 Upset Model (separate) @50", "R32 Upset Model (separate)", .5),
                              ("R32 fed R64 chances (gap) @40", "R32 Upset Model fed R64 chances (gap)", .4), ("R32 fed R64 chances (gap) @50", "R32 Upset Model fed R64 chances (gap)", .5),
                              ("R32 fed R64 chances (both) @40", "R32 Upset Model fed R64 chances (both + gap)", .4), ("R32 fed R64 chances (both) @50", "R32 Upset Model fed R64 chances (both + gap)", .5)):
        pts, a, b, u = bracket(r1f, mode, cut); print(f"{r1lab:28} {r32lab:52} {pts:6} | {a:4} | {b:4} | {u}")
for lab, model in (("separate", "R32 Upset Model (separate)"), ("fed (gap)", "R32 Upset Model fed R64 chances (gap)")):
    pts, a, b, u = bracket(None, "joint", .4, model)
    print(f"{'JOINT pod pick (both ways)':28} {'R64 x R32 ' + lab:52} {pts:6} | {a:4} | {b:4} | {u}")
json.dump({lab: v[2].tolist() for lab, v in MODELS.items()}, open(os.path.join(HERE, "m263_feed.json"), "w"))
