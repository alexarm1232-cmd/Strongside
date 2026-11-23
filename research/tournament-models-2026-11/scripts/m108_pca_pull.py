# What else the PCA can tell us. Rebuilds m103's team points and components (same features, same PCA).
#  1) Component by component (PC1-PC10): which ones separate the boxes? (game-level: average of the two teams, and the
#     winner-minus-loser gap), with the top weights of any that do. Permutation p, 2,000 shuffles.
#  2) Winner vs loser: the winner-minus-loser gap on each component, overall and by box (sign test).
#  3) Can the components predict a SPLIT game (model and simulator disagree)? Logistic regression on the game's
#     team-average and gap components, each tournament held out; AUC.
import os, sys, re, json, contextlib, io, math
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
M103 = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m103_quad_pca.py"
__file__ = M103
with contextlib.redirect_stdout(io.StringIO()):
    src = open(M103, encoding="utf-8").read().split("# how the boxes differ")[0].split("quads = [")[0]
    exec(src)                                                    # X, Z, Vt, PC, pts, FEATS, nice, pve, QUAD...
K = 10
g = np.array([p["game"] for p in pts]); won = np.array([p["won"] for p in pts]); quad = np.array([p["quad"] for p in pts])
games = sorted(set(g)); G = len(games)
avg = np.zeros((G, K)); gap = np.zeros((G, K)); gq = []; gseas = []
for k, gi in enumerate(games):
    i = np.where(g == gi)[0]
    if len(i) != 2: avg[k] = np.nan; continue
    w, l = (i[0], i[1]) if won[i[0]] else (i[1], i[0])
    avg[k] = (PC[w, :K] + PC[l, :K]) / 2; gap[k] = PC[w, :K] - PC[l, :K]; gq.append(quad[w]); gseas.append(seas[gi])
ok = ~np.isnan(avg[:, 0]); avg, gap = avg[ok], gap[ok]; gq = np.array(gq); gseas = np.array(gseas); G = len(gq)
print(f"games with both teams: {G}; variance explained PC1-10: {[round(float(x) * 100, 1) for x in pve[:K]]}")
rng = np.random.default_rng(1)
def perm(x, mask, reps=2000):
    obs = abs(x[mask].mean() - x[~mask].mean()); null = []
    for _ in range(reps):
        m = rng.permutation(mask); null.append(abs(x[m].mean() - x[~m].mean()))
    return obs, (np.sum(np.array(null) >= obs) + 1) / (reps + 1)
def top(c, n=4): return ", ".join(f"{nice(FEATS[j])} {Vt[c, j]:+.2f}" for j in np.argsort(-np.abs(Vt[c]))[:n])
split = np.isin(gq, ["Model right, sim wrong", "Sim right, model wrong"]); agree = ~split
print("\n1) WHICH COMPONENTS SEPARATE THE BOXES?  (p < 0.005 counts with 10 components x 3 comparisons)")
comps = [("split games vs agree games", split, np.ones(G, bool)),
         ("both wrong vs both right", gq == "Both wrong", np.isin(gq, ["Both wrong", "Both right"])),
         ("model-wins vs sim-wins (splits only)", gq == "Model right, sim wrong", split)]
for name, mask, within in comps:
    print(f"  {name}:")
    for c in range(K):
        for lab, arr in (("team average", avg), ("winner-loser gap", gap)):
            o, p = perm(arr[within, c], mask[within])
            if p < 0.05:
                print(f"    PC{c + 1} {lab:16} diff {arr[within & mask, c].mean() - arr[within & ~mask, c].mean():+.2f}  p={p:.4f}   [{top(c)}]")
print("\n2) WINNER MINUS LOSER, by component (mean gap; share of games the winner is higher)")
for c in range(4):
    line = f"  PC{c + 1}: all {gap[:, c].mean():+.2f} ({np.mean(gap[:, c] > 0):.0%})"
    for q in ["Both right", "Model right, sim wrong", "Sim right, model wrong", "Both wrong"]:
        m = gq == q; line += f" | {q}: {gap[m, c].mean():+.2f} ({np.mean(gap[m, c] > 0):.0%})"
    print(line + f"   [{top(c, 3)}]")
print("\n3) PREDICTING A SPLIT GAME from the components (each tournament held out)")
def auc(s, y):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def logit_fit(A, y, lam=1.0):
    mu, sd = A.mean(0), A.std(0) + 1e-9; Zt = np.column_stack([(A - mu) / sd, np.ones(len(A))]); w = np.zeros(Zt.shape[1])
    P = lam * np.eye(Zt.shape[1]); P[-1, -1] = 0
    for _ in range(50):
        q = 1 / (1 + np.exp(-Zt @ w)); H = Zt.T @ (Zt * (q * (1 - q))[:, None]) + P; w += np.linalg.solve(H, Zt.T @ (y - q) - P @ w)
    return lambda B: np.column_stack([(B - mu) / sd, np.ones(len(B))]) @ w
# the gap's sign depends on who won (unknown beforehand), so use its absolute size: how far apart the two teams are
feat = {"team average (PC1-10)": avg, "how far apart (|gap| PC1-10)": np.abs(gap), "both": np.column_stack([avg, np.abs(gap)])}
y = split.astype(float)
for nm, A in feat.items():
    sc = np.zeros(G)
    for s in sorted(set(gseas)):
        tr, te = gseas != s, gseas == s; sc[te] = logit_fit(A[tr], y[tr])(A[te])
    top10 = np.argsort(-sc)[: G // 10]
    print(f"  {nm:30} AUC {auc(sc, y):.3f} | split rate in the 10% of games it flags most: {y[top10].mean():.0%} (overall {y.mean():.0%})")
