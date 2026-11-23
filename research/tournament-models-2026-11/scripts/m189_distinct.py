# Is the Round 1 upset model distinct from the main model ("Model 1", 759) and the simulator, and still significant?
# Everything in "upset" terms on the 511 Round of 64 games (lower seed won), all predictions held out by tournament.
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
import importlib.util
spec = importlib.util.spec_from_file_location("R1", os.path.join(HERE, "m188_r64_upset_model.py"))
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
n = len(rows); seas = np.array([r["s"] for r in rows]); sgap = np.array([r["sL"] - r["sH"] for r in rows], float); W = Q.WT[[r["i"] for r in rows]]
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))      # P(lower seed wins)
simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
def col(name):
    lab, k = name.split(" ", 1); return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
ALL = json.load(open(os.path.join(HERE, "m188_out.json")))["inputs"]
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(50):
        p = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(H, A.T @ (w * (ytr - p)) - P @ b)
    return lambda X: np.column_stack([(X - mu) / sd, np.ones(len(X))]) @ b
def held(X):
    out = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = ridge(X[tr], y[tr], W[tr])(X[te])
    return 1 / (1 + np.exp(-out))
def auc(s, yy):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
def zadd(p):   # z of the model's log-odds on top of Model 1 + simulator log-odds (upset outcome)
    Xs = np.column_stack([lg(m1_up), lg(sim_up), lg(p), np.ones(n)]); w = np.zeros(4)
    for _ in range(60):
        q = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (q * (1 - q))[:, None]); w += np.linalg.solve(Hm, Xs.T @ (y - q))
    return w[2] / math.sqrt(np.linalg.inv(Hm)[2, 2])
def sign_p(a, b):
    from math import comb
    n_ = a + b; k = max(a, b); return min(1, 2 * sum(comb(n_, i) for i in range(k, n_ + 1)) / 2 ** n_) if n_ else 1
def report(name, p, cut):
    pick = p >= cut; right = (pick == (y == 1))
    print(f"\n== {name} (upset at {cut:.0%}+): right {int(right.sum())}/511 | AUC {auc(p, y):.3f} | adds over Model 1 + simulator: z {zadd(p):+.2f}")
    for oname, op, ocut in (("Model 1", m1_up, 0.5), ("simulator", sim_up, 0.5)):
        opick = op >= ocut; oright = (opick == (y == 1)); dis = pick != opick
        a, b = int((right & dis).sum()), int((oright & dis).sum())
        print(f"   vs {oname:9}: same pick {int((~dis).sum())}/511 ({(~dis).mean():.0%}) | win-chance corr {np.corrcoef(lg(p), lg(op))[0,1]:.2f} | disagreements {int(dis.sum())}: this right {a}, {oname} right {b}, sign p {sign_p(a, b):.3f}")
    both = int(((pick != (m1_up >= .5)) & (pick != (sim_up >= .5))).sum()); print(f"   picks a different winner than BOTH: {both} games")
print(f"Model 1: right {int(((m1_up >= .5) == (y == 1)).sum())} | simulator: right {int(((sim_up >= .5) == (y == 1)).sum())} | they agree on {int(((m1_up >= .5) == (sim_up >= .5)).sum())}/511")
p_full = held(np.column_stack([sgap] + [col(c) for c in ALL])); report("Round 1 model, with seed gap (28 + seed)", p_full, 0.45)
# distinct version: no seed gap, and drop any input that overlaps Model 1 or the simulator (|r| >= 0.3 with either's log-odds)
keep = [c for c in ALL if abs(np.corrcoef(col(c), lg(m1_up))[0, 1]) < 0.3 and abs(np.corrcoef(col(c), lg(sim_up))[0, 1]) < 0.3]
drop = [(c, round(abs(np.corrcoef(col(c), lg(m1_up))[0, 1]), 2), round(abs(np.corrcoef(col(c), lg(sim_up))[0, 1]), 2)) for c in ALL if c not in keep]
print(f"\nDISTINCT VERSION: no seed gap; dropped {len(drop)} inputs that overlap Model 1 or the simulator (r with each): {drop}")
p_dist = held(np.column_stack([col(c) for c in keep]))
for cut in (0.5, 0.45, 0.4): report(f"Distinct Round 1 model ({len(keep)} inputs)", p_dist, cut)
json.dump({"keep": keep, "p_dist": p_dist.tolist(), "p_full": p_full.tolist()}, open(os.path.join(HERE, "m189_out.json"), "w"))

