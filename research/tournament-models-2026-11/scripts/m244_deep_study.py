# Deep-run study + model (Elite 8, Final Four, title game, champion), 2010-2026, First Four out.
# One row per tournament team (1,022: both teams of every Round of 64 game), pre-tournament numbers only.
# Outcomes from real tournament wins: Elite 8 = 3+ wins, Final Four = 4+, title game = 5+, champion = 6.
# Part A: who gets there (seeds, net-rating ranks, offense/defense ranks of champions).
# Part B: what separates deep teams beyond strength (each measure added to net rating + seed + path, Wald z; both eras).
# Part C: models, each year held out; inputs picked inside the training years only; scored as bracket picks
#         (Elite 8: 2 per region, Final Four: 1 per region, finalists: 1 per half, champion) and team-level AUC.
import os, sys, json, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
import numpy as np
src = open(os.path.join(HERE, "m228_three.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()):
    exec(src[:src.index("g = np.arange")])          # rows, ALL (every measure H/L incl. cast BPM), Q, W, kk, ...
TM = Q.R.B.TM; G = Q.R.B.G
t = open(os.path.join(HERE, "m242_bracket_in.js"), encoding="utf-8").read(); BI = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
CF = np.load(os.path.join(Q.OLD, "coach_feats.npy")); CC = json.load(open(os.path.join(Q.OLD, "coach_cols.json")))
bases = sorted({k[2:] for k in ALL if k[:2] in ("H ", "L ")})
bases = [b for b in bases if ("H " + b) in ALL and ("L " + b) in ALL]
# ---- team table
T = []
for j, r in enumerate(rows):
    s = r["s"]; order = BI[s]["games"]
    for side, opp in (("H", "L"), ("L", "H")):
        nm = r[side]; k_ = kk(nm)
        gpos = next(i for i, g in enumerate(order) if k_ in (g["H"], g["L"]))
        wins = BI[s]["wins"].get(k_, 0)
        g = G[r["i"]]; cs = "fav" if kk(g["fav"]) == k_ else "dog"
        row = {"s": s, "team": k_, "seed": r["s" + side], "gpos": gpos, "quad": gpos // 4, "region": gpos // 8, "half": gpos // 16, "wins": wins,
               "net": TM[s][nm]["adj_net"], "o": TM[s][nm]["adj_o"], "d": TM[s][nm]["adj_d"], "w": float(W[j]),
               "coach_ncaa": float(CF[r["i"], CC.index(f"{cs} car_ncaa")]), "coach_s16": float(CF[r["i"], CC.index(f"{cs} rec5_s16")])}
        for b in bases: row["f " + b] = float(ALL[f"{side} {b}"][j])
        T.append(row)
# 2021 VCU-Oregon no-contest: Oregon's walkover counts as a win
for s in BI:
    for g in BI[s]["games"]:
        if g.get("bye"):
            for row in T:
                if row["s"] == s and row["team"] == g["bye"]: row["wins"] += 1
n = len(T); S = np.array([r["s"] for r in T]); SEASONS = sorted(set(S))
wins = np.array([r["wins"] for r in T]); seed = np.array([r["seed"] for r in T], float); net = np.array([r["net"] for r in T])
quad = np.array([r["quad"] for r in T]); region = np.array([r["region"] for r in T]); half = np.array([r["half"] for r in T]); wt = np.array([r["w"] for r in T])
# net-rating ranks among all D-I teams, offense/defense ranks
def rank_of(s, val, key, low_good=False):
    arr = np.array([v[key] for v in TM[s].values()]); return int((arr < val).sum() + 1) if low_good else int((arr > val).sum() + 1)
netrk = np.array([rank_of(r["s"], r["net"], "adj_net") for r in T]); ork = np.array([rank_of(r["s"], r["o"], "adj_o") for r in T]); drk = np.array([rank_of(r["s"], r["d"], "adj_d", True) for r in T])
# path: best other team in your quadrant / region (net rating), and your rank inside the region
qriv = np.zeros(n); rriv = np.zeros(n); rgrk = np.zeros(n)
for i in range(n):
    mq = (S == S[i]) & (quad == quad[i]); mr = (S == S[i]) & (region == region[i]); mq[i] = False; mr[i] = False
    qriv[i] = net[mq].max(); rriv[i] = net[mr].max(); rgrk[i] = 1 + (net[mr] > net[i]).sum()
STAGES = {"Elite 8": 3, "Final Four": 4, "Title game": 5, "Champion": 6}
Y = {k: (wins >= v).astype(int) for k, v in STAGES.items()}
print(f"teams {n} | Elite 8 {Y['Elite 8'].sum()} | Final Four {Y['Final Four'].sum()} | title game {Y['Title game'].sum()} | champions {Y['Champion'].sum()}")

# ================= PART A: who gets there
print("\n=== A. WHO GETS THERE")
print("seed | teams | Elite 8 | Final Four | title game | champion")
for sd in range(1, 17):
    m = seed == sd; print(f"{sd:4} | {int(m.sum()):4} | " + " | ".join(f"{int(Y[k][m].sum()):3} ({Y[k][m].mean():.0%})" for k in STAGES))
print("\nnet-rating rank (all D-I) | teams | Elite 8 | Final Four | title game | champion")
for lo, hi in ((1, 1), (2, 3), (4, 6), (7, 10), (11, 15), (16, 25), (26, 50), (51, 400)):
    m = (netrk >= lo) & (netrk <= hi); print(f"{lo}-{hi} | {int(m.sum())} | " + " | ".join(f"{int(Y[k][m].sum())} ({Y[k][m].mean():.0%})" for k in STAGES))
print("\nrank inside its own region by net rating (1 = best of the 16) | teams | Elite 8 | Final Four | champion")
for rk in range(1, 6):
    m = rgrk == rk; print(f"{rk} | {int(m.sum())} | {int(Y['Elite 8'][m].sum())} ({Y['Elite 8'][m].mean():.0%}) | {int(Y['Final Four'][m].sum())} ({Y['Final Four'][m].mean():.0%}) | {int(Y['Champion'][m].sum())}")
m = rgrk >= 6; print(f"6+ | {int(m.sum())} | {int(Y['Elite 8'][m].sum())} | {int(Y['Final Four'][m].sum())} | {int(Y['Champion'][m].sum())}")
print("\nchampions: seed, net rank, offense rank, defense rank, rank in region")
for i in np.where(Y["Champion"] == 1)[0]: print(f"   {int(S[i][:4]) + 1} {T[i]['team']}: seed {int(seed[i])} | net #{netrk[i]} | offense #{ork[i]} | defense #{drk[i]} | region rank {int(rgrk[i])}")
both = (ork <= 25) & (drk <= 25)
print(f"top-25 offense AND top-25 defense: {int(both.sum())} teams -> champions {int(Y['Champion'][both].sum())}/16, Final Four {int(Y['Final Four'][both].sum())}/64")
both = (ork <= 40) & (drk <= 40)
print(f"top-40 offense AND top-40 defense: {int(both.sum())} teams -> champions {int(Y['Champion'][both].sum())}/16, Final Four {int(Y['Final Four'][both].sum())}/64")

# ================= PART B: beyond strength
def logit_fit(X, y, w, lam=1e-4):
    w_ = np.zeros(X.shape[1])
    for _ in range(80):
        p = 1 / (1 + np.exp(-X @ w_)); Hm = X.T @ (X * (w * p * (1 - p))[:, None]) + lam * np.eye(X.shape[1]); w_ += np.linalg.solve(Hm, X.T @ (w * (y - p)) - lam * w_)
    return w_, Hm
def std(v): return (v - v.mean()) / (v.std() + 1e-12)
BASE = {"net": net, "seed": seed, "quad rival": qriv, "region rival": rriv}
CANDS = {"coach NCAA games": np.array([r["coach_ncaa"] for r in T]), "coach recent S16s": np.array([r["coach_s16"] for r in T]),
         "offense rating": np.array([r["o"] for r in T]), "defense rating": -np.array([r["d"] for r in T]),
         "balance (worse of O/D rank)": -np.maximum(ork, drk).astype(float)}
for b in bases: CANDS[b] = np.array([r["f " + b] for r in T])
CANDS = {k: v for k, v in CANDS.items() if np.std(v) > 0}
def zbeyond(v, y, m):
    X = np.column_stack([std(BASE[k][m]) for k in BASE] + [std(v[m]), np.ones(m.sum())]); w_, Hm = logit_fit(X, y[m], np.ones(m.sum()))
    return w_[-2] / math.sqrt(np.linalg.inv(Hm)[-2, -2])
early = np.array([int(s[:4]) < 2018 for s in S]); allm = np.ones(n, bool)
print("\n=== B. WHAT ADDS BEYOND NET RATING + SEED + PATH (Wald z; + = more likely to get there)")
for k in ("Elite 8", "Final Four", "Champion"):
    y = Y[k]; res = []
    for c, v in CANDS.items():
        try: z = zbeyond(v, y, allm)
        except Exception: continue
        res.append((abs(z), c, z))
    res.sort(reverse=True)
    print(f"\n{k} ({int(y.sum())} teams; {len(res)} tests, ~{int(len(res) * .046)} pass |z|>=2 by chance): top 12, with 2010-17 | 2018-26")
    for _, c, z in res[:12]:
        try: e1, e2 = zbeyond(CANDS[c], y, early), zbeyond(CANDS[c], y, ~early)
        except Exception: e1 = e2 = float("nan")
        print(f"   {c:40} z {z:+.2f} | {e1:+.1f} | {e2:+.1f}{'  (same sign both eras)' if np.sign(e1) == np.sign(e2) else ''}")
    # base variables alone
    X = np.column_stack([std(BASE[b]) for b in BASE] + [np.ones(n)]); w_, Hm = logit_fit(X, y, np.ones(n))
    print("   base variables (z): " + ", ".join(f"{b} {w_[i] / math.sqrt(np.linalg.inv(Hm)[i, i]):+.2f}" for i, b in enumerate(BASE)))
json.dump({"T": [{k: v for k, v in r.items() if not k.startswith("f ")} for r in T]}, open(os.path.join(HERE, "m244_teams.json"), "w"))
np.savez(os.path.join(HERE, "m244_data.npz"), wins=wins, seed=seed, net=net, quad=quad, region=region, half=half, qriv=qriv, rriv=rriv, netrk=netrk, ork=ork, drk=drk, rgrk=rgrk, S=S, wt=wt,
         names=np.array(list(CANDS)), C=np.column_stack(list(CANDS.values())))
