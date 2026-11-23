# Tournament experience weighted by roster continuity: sum over the last 3 tournaments of (wins that year) x continuity^k,
# continuity = share of last season's minutes that returned this season (rosters), k = seasons ago. Replaces the program
# version ("tourney wins last 3") in the Round 1 Upset Model. Tested each year held out and on 2018-26 (fit 2010-17).
import os, sys, json, math
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import numpy as np
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
U = json.load(open(os.path.join(H, "m188_out.json")))["inputs"]; seas = np.array([r["s"] for r in rows]); W = Q.WT[[r["i"] for r in rows]]; n = len(rows)
RET = json.load(open(os.path.join(H, "m135_ret.json")))
G = Q.R.B.G; SEAS = sorted({g["season"] for g in G}); TW = {}
for g in G:
    if g["rnd"] != "First Four": w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
def cont(s, t):
    v = (RET.get(s, {}).get(t) or RET.get(s, {}).get(t + ".") or {}).get("returning"); return 0.6 if v is None else v
def exp_c(s, t):
    i = SEAS.index(s); c = cont(s, t); return sum(TW.get((SEAS[i - k], t), 0) * c ** k for k in (1, 2, 3) if i - k >= 0)
for side in "HL": F[f"{side} tourney exp (roster)"] = np.array([exp_c(r["s"], r[side]) for r in rows])
CF = np.load(os.path.join(Q.OLD, "coach_feats.npy")); CC = json.load(open(os.path.join(Q.OLD, "coach_cols.json")))
def tenure(r, side):
    g = G[r["i"]]; who = "fav" if r[side] == g["fav"] else "dog"; return CF[r["i"], CC.index(who + " tenure")]
def exp_coach(r, side):
    i = SEAS.index(r["s"]); ten = tenure(r, side); return sum(TW.get((SEAS[i - k], r[side]), 0) for k in (1, 2, 3) if i - k >= 0 and ten >= k)
for side in "HL": F[f"{side} tourney exp (same coach)"] = np.array([exp_coach(r, side) for r in rows])
NEW = [c if c != "L-H tourney wins last 3" else "L-H tourney exp (roster)" for c in U]; NEWC = [c if c != "L-H tourney wins last 3" else "L-H tourney exp (same coach)" for c in U]
def col(name):
    lab, k = name.split(" ", 1); return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
def auc(s, yy):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
sg = np.array([r["sL"] - r["sH"] for r in rows], float)
def zc(v):
    Xs = np.column_stack([sg, v, np.ones(n)]); w = np.zeros(3)
    for _ in range(60):
        p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(Hm, Xs.T @ (y - p))
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
TM = Q.R.B.TM; rg = np.array([TM[r["s"]][r["H"]]["adj_net"] - TM[r["s"]][r["L"]]["adj_net"] for r in rows])
for nm in ("L-H tourney wins last 3", "L-H tourney exp (roster)", "L-H tourney exp (same coach)"):
    v = col(nm); print(f"{nm:28} z (seed controlled) {zc(v):+.2f} | r with net rating gap {abs(np.corrcoef(v, rg)[0, 1]):.2f}")
early = np.array([int(s[:4]) < 2017 for s in seas])
res = {}
for name, ins in (("program tourney wins (locked model)", U), ("roster-continuity tourney experience", NEW), ("same-coach tourney experience", NEWC), ("program wins + same-coach version", U + ["L-H tourney exp (same coach)"])):
    X = np.column_stack([col(c) for c in ins]); out = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    pf = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early])))
    res[name] = out
    print(f"\n== {name}\n   each year held out: AUC {auc(out, y):.3f} | right at 50% {int(((out >= .5) == (y == 1)).sum())} · 40% {int(((out >= .4) == (y == 1)).sum())} of 511 | upset picks at 40% {int((out >= .4).sum())} ({int(((out >= .4) & (y == 1)).sum())} hit)")
    print(f"   2018-26 (fit 2010-17): AUC {auc(pf, y[~early]):.3f} | right at 50% {int(((pf >= .5) == (y[~early] == 1)).sum())} · 40% {int(((pf >= .4) == (y[~early] == 1)).sum())} of 255")
j = next(k for k, r in enumerate(rows) if r["s"] == "2023-24" and r["L"] == "Saint Peter's")
spc = cont('2023-24', "Saint Peter's")
print(f"\nSaint Peter's 2024: continuity {spc:.2f} | experience program {col('L-H tourney wins last 3')[j]:+.1f} -> roster {col('L-H tourney exp (roster)')[j]:+.2f} | upset chance {res['program tourney wins (locked model)'][j]:.0%} -> {res['roster-continuity tourney experience'][j]:.0%}")
hp = next(k for k, r in enumerate(rows) if r["s"] == "2025-26" and r["L"] == "High Point")
print(f"same coach: Saint Peter's {res['same-coach tourney experience'][j]:.0%} (tenure {tenure(rows[j], 'L')})")
print(f"High Point 2026 upset chance {res['program tourney wins (locked model)'][hp]:.0%} -> {res['roster-continuity tourney experience'][hp]:.0%}")
json.dump({"inputs": NEW, "p": res["roster-continuity tourney experience"].tolist()}, open(os.path.join(H, "m206_out.json"), "w"))


