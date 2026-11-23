# Part C: deep-run models, each year held out (16 folds). One ridge logistic per stage (Elite 8, Final Four, title game,
# champion) on team rows; inputs standardized; any input screening is redone inside each fold's training years.
# Bracket picks, top-down and consistent: champion = best champion chance; other finalist = best title-game chance in
# the other half; other Final Four teams = best Final Four chance in each remaining region; other Elite 8 teams = best
# Elite 8 chance in each remaining quarter-region. Points as on ESPN for those rounds: 4 per Elite 8 team, 8 per Final
# Four team, 16 per finalist, 32 for the champion (the same 1-2-4-8-16-32 scale as before, rounds 3-6).
import os, json, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
Z = np.load(os.path.join(HERE, "m244_data.npz"), allow_pickle=True)
wins, seed, net, quad, region, half, qriv, rriv, S, wt = (Z[k] for k in ("wins", "seed", "net", "quad", "region", "half", "qriv", "rriv", "S", "wt"))
ork, drk = Z["ork"], Z["drk"]; NAMES = [str(x) for x in Z["names"]]; C = Z["C"]; n = len(wins); SEASONS = sorted(set(S))
TEAMS = [r["team"] for r in json.load(open(os.path.join(HERE, "m244_teams.json")))["T"]]
FJ = json.load(open(os.path.join(HERE, "m186_r64_features.json")))["F"]   # team rows are (H, L) per Round of 64 game, in order
TW3 = np.ravel(np.column_stack([FJ["H tourney wins last 3"], FJ["L tourney wins last 3"]]))
C = np.column_stack([C, TW3]); NAMES = NAMES + ["tourney wins last 3"]
col = lambda nm: C[:, NAMES.index(nm)]
STAGES = {"Elite 8": 3, "Final Four": 4, "Title game": 5, "Champion": 6}; Y = {k: (wins >= v).astype(float) for k, v in STAGES.items()}
BASE = {"net rating": net, "seed": seed, "quarter-region rival": qriv, "region rival": rriv}
HAND = dict(BASE, **{"offense rating": col("offense rating"), "defense rating": col("defense rating"), "balance (worse of O/D rank)": col("balance (worse of O/D rank)"),
                     "coach recent S16s": col("coach recent S16s"), "coach NCAA games": col("coach NCAA games"), "tourney wins last 3": col("tourney wins last 3"),
                     "lost minutes (out of lineup)": col("lost_minutes"), "star BPM": col("star_bpm"), "supporting-cast BPM": col("cast_bpm_bpm") if "cast_bpm_bpm" in NAMES else col("depth_bpm")})
def ridge(X, y, w, lam):
    mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(len(X))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(80):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (y - p)) - P @ b)
    return (lambda Xq: 1 / (1 + np.exp(-(np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b)))), b
def auc(s, y):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = y.sum(); return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
def zbeyond(v, y, m, base):
    X = np.column_stack([(b[m] - b[m].mean()) / b[m].std() for b in base] + [(v[m] - v[m].mean()) / (v[m].std() + 1e-12), np.ones(m.sum())]); w = np.zeros(X.shape[1])
    for _ in range(60):
        p = 1 / (1 + np.exp(-X @ w)); Hm = X.T @ (X * (p * (1 - p))[:, None]) + 1e-4 * np.eye(X.shape[1]); w += np.linalg.solve(Hm, X.T @ (y[m] - p) - 1e-4 * w)
    return w[-2] / math.sqrt(np.linalg.inv(Hm)[-2, -2])
SCREEN = [c for c in NAMES if np.std(col(c)) > 0]
def screen(y, m, k):
    """top-k extra measures beyond the base inside the training rows m: |z| >= 2, same sign in both halves of those years, |r| < .6 with net and each other"""
    yrs = sorted(set(S[m])); h1 = m & np.isin(S, yrs[:len(yrs) // 2]); h2 = m & ~h1
    base = list(BASE.values()); res = []
    for c in SCREEN:
        v = col(c)
        try: z = zbeyond(v, y, m, base)
        except Exception: continue
        if abs(z) >= 2: res.append((abs(z), c, z))
    res.sort(reverse=True); kept = []
    for _, c, z in res:
        v = col(c)
        if abs(np.corrcoef(v[m], net[m])[0, 1]) >= .6 or any(abs(np.corrcoef(v[m], col(o)[m])[0, 1]) >= .6 for o in kept): continue
        try:
            if np.sign(zbeyond(v, y, h1, base)) != np.sign(z) or np.sign(zbeyond(v, y, h2, base)) != np.sign(z): continue
        except Exception: continue
        kept.append(c)
        if len(kept) == k: break
    return kept
def heldout(feats_fn, lam):
    P = {k: np.zeros(n) for k in STAGES}; picked = {k: {} for k in STAGES}
    for s in SEASONS:
        tr, te = S != s, S == s
        for k in STAGES:
            fs = feats_fn(k, tr); X = np.column_stack(fs[1]); f, _ = ridge(X[tr], Y[k][tr], wt[tr], lam); P[k][te] = f(X[te])
            for c in fs[0]: picked[k][c] = picked[k].get(c, 0) + 1
    return P, picked
def bracket(P, s):
    m = np.where(S == s)[0]
    ch = m[np.argmax(P["Champion"][m])]
    oh = m[half[m] != half[ch]]; f2 = oh[np.argmax(P["Title game"][oh])]
    f4 = [ch, f2]
    for rg in sorted(set(region[m])):
        if rg in (region[ch], region[f2]): continue
        mr = m[region[m] == rg]; f4.append(mr[np.argmax(P["Final Four"][mr])])
    e8 = list(f4)
    for q in sorted(set(quad[m])):
        if any(quad[i] == q for i in f4): continue
        mq = m[quad[m] == q]; e8.append(mq[np.argmax(P["Elite 8"][mq])])
    return e8, f4, [ch, f2], ch
def score(P, label, show_years=False):
    tot = np.zeros(4, int); pts = 0; champs = []
    for s in SEASONS:
        e8, f4, fin, ch = bracket(P, s)
        r = [sum(wins[i] >= 3 for i in e8), sum(wins[i] >= 4 for i in f4), sum(wins[i] >= 5 for i in fin), int(wins[ch] == 6)]
        tot += r; pts += 4 * r[0] + 8 * r[1] + 16 * r[2] + 32 * r[3]; champs.append(f"{int(s[:4]) + 1} {TEAMS[ch]}{'*' if wins[ch] == 6 else ''}")
    print(f"   {label:52} Elite 8 {tot[0]}/128 | Final Four {tot[1]}/64 | finalists {tot[2]}/32 | champions {tot[3]}/16 | points {pts}")
    if show_years: print("      champion picks:", ", ".join(champs))
    return pts
def teamauc(P): return " | ".join(f"{k} {auc(P[k], Y[k]):.3f}" for k in STAGES)
# One model for every stage: predicted tournament wins (0-6) from all 1,022 teams, so Round 2 and Sweet 16 results
# teach it too. Ridge regression on wins; its score ranks teams for every slot. Also a Sweet-16-or-better stage model
# (wins >= 2, 256 teams) used for every slot. Each year held out.
def ridge_lin(X, y, w, lam):
    mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(len(X))]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    b = np.linalg.solve(A.T @ (A * w[:, None]) + P, A.T @ (w * y)); return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
for label, feats in (("base (4)", list(BASE.values())), ("hand-picked deep set (13)", list(HAND.values()))):
    X = np.column_stack(feats)
    for lam in (3.0, 10.0, 30.0):
        pw = np.zeros(n); p16 = np.zeros(n)
        for s in SEASONS:
            tr, te = S != s, S == s
            pw[te] = ridge_lin(X[tr], wins[tr].astype(float), wt[tr], lam)(X[te])
            f, _ = ridge(X[tr], (wins[tr] >= 2).astype(float), wt[tr], lam); p16[te] = f(X[te])
        print(f"\n== {label}, ridge {lam:.0f}")
        print(f"   predicted-wins model | team AUC: " + " | ".join(f"{k} {auc(pw, Y[k]):.3f}" for k in STAGES)); score({k: pw for k in STAGES}, "bracket picks", lam == 10.0)
        print(f"   Sweet 16 model       | team AUC: " + " | ".join(f"{k} {auc(p16, Y[k]):.3f}" for k in STAGES)); score({k: p16 for k in STAGES}, "bracket picks")