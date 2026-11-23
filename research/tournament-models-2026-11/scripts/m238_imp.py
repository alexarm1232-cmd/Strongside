# The games the 45% average (Upset 29 + Strongside + simulator) gets wrong: 111 of 511. What they look like, and what
# separates them, using every measure we have (including ones not in any model).
import os, sys, json, math, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
exec(open(os.path.join(H, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
U29 = json.load(open(os.path.join(H, "m219_out.json")))["inputs"]
ALL = dict(CAND); ALL.update({c: col(c) for c in U29})
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
STL, CAST, PCS = "L-H stl", "L-H cast_bpm_bpm", "L pt_d_share Perimeter Cut"
print("is 'share of perimeter cuts allowed' already in? the model has", [c for c in U29 if "Perimeter Cut" in c])
print(f"   r(L pt_d_share Perimeter Cut, L pt_d_ppp Perimeter Cut) = {np.corrcoef(ALL[PCS], col('L pt_d_ppp Perimeter Cut'))[0, 1]:+.2f}")
print(f"   r with net rating gap: steals gap {np.corrcoef(ALL[STL], rg)[0, 1]:+.2f} | cast BPM gap {np.corrcoef(ALL[CAST], rg)[0, 1]:+.2f} | perimeter cut share {np.corrcoef(ALL[PCS], rg)[0, 1]:+.2f}")
print(f"   r steals gap vs L d_tov (in model) {np.corrcoef(ALL[STL], col('L d_tov'))[0, 1]:+.2f} | cast BPM gap vs L-H depth_bpm (in model) {np.corrcoef(ALL[CAST], col('L-H depth_bpm'))[0, 1]:+.2f}")
# Variable importance for the Upset Model (31): fit on all 511 Round 1 games; permutation importance = how much the AUC
# drops when that one input is shuffled (average of 200 shuffles); direction from the standardized weight.
NEW = json.load(open(os.path.join(H, "m230_out.json")))["inputs"]; X = np.column_stack([ALL[c] for c in NEW]); f = ridge(X, y, W); base = auc(f(X), y)
mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(n)]); b = np.zeros(A.shape[1]); P = 30 * np.eye(A.shape[1]); P[-1, -1] = 0
for _ in range(60):
    pp = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (W * pp * (1 - pp))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (W * (y - pp)) - P @ b)
rng = np.random.default_rng(7); imp = []
for j, c in enumerate(NEW):
    drops = []
    for _ in range(200):
        Xp = X.copy(); Xp[:, j] = rng.permutation(Xp[:, j]); drops.append(base - auc(f(Xp), y))
    imp.append((float(np.mean(drops)), c, float(b[j])))
imp.sort(reverse=True)
print(f"base AUC {base:.3f}")
for v, c, w in imp: print(f"{c}|{v:.4f}|{w:+.3f}")
json.dump({"base": base, "imp": imp}, open(os.path.join(H, "m238_imp.json"), "w"))
# same for the original model's inputs? (report only how the average splits weight)