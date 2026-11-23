# Round 1 upset model (no net rating). Ridge logistic (lam 30, half-life-12 season weights, as the main model), inputs
# standardized, outcome = the LOWER seed won, 511 Round of 64 games, each tournament held out. Two versions: with the
# seed gap as an input, and without. Upset picked when its chance >= a cutoff (50/45/40/35%).
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
n = len(rows); seas = np.array([r["s"] for r in rows]); sgap = np.array([r["sL"] - r["sH"] for r in rows], float)
W = Q.WT[[r["i"] for r in rows]]
def col(name):
    lab, k = name.split(" ", 1)
    return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
INPUTS = ["L pt_d_ppp Rim Attack", "L-H pt_d_ppp Dribble Jumper", "H pt_ppp Big Cut & Roll", "H pt_d_share Dribble Jumper", "H d_blk",
          "L pt_d_share Dribble Jumper", "L-H pt_d_ppp Transition", "H pm_close2h", "L pt_d_ppp Pick & Pop", "L pt_d_share Post-Up",
          "H star_usage_rate", "H 3pt/vol: mar_sd", "H basic: ppg", "L-H returning", "H big_height", "L-H ftr",
          "L-H tourney wins last 3", "L-H pt_ppp Big Cut & Roll", "L-H depth_bpm", "L d_tov",
          "L-H pt_d_ppp Rim Attack", "L-H pt_d_ppp Drive & Kick", "L-H pt_d_ppp Inside Out", "L pt_d_ppp Dribble Jumper",
          "L pt_d_ppp Inside Out", "L pt_d_ppp Perimeter Cut", "L-H pt_d_ppp Pick & Pop", "H pt_d_ppp Transition"]
XM = np.column_stack([col(c) for c in INPUTS])
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1])
    P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(50):
        p = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(H, A.T @ (w * (ytr - p)) - P @ b)
    return lambda X: np.column_stack([(X - mu) / sd, np.ones(len(X))]) @ b
def auc(s, yy):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
res = {}
for name, X in (("with seed gap", np.column_stack([sgap, XM])), ("without seed", XM), ("seed gap only (baseline)", sgap[:, None])):
    out = np.zeros(n); ins_auc = []
    for s in sorted(set(seas)):
        tr, te = seas != s, seas == s; f = ridge(X[tr], y[tr], W[tr]); out[te] = f(X[te]); ins_auc.append(auc(f(X[tr]), y[tr]))
    p = 1 / (1 + np.exp(-out)); res[name] = p
    print(f"\n== {name}: held-out AUC {auc(out, y):.3f} | training AUC (avg of 16 folds) {np.mean(ins_auc):.3f}")
    for cut in (0.50, 0.45, 0.40, 0.35):
        pick = p >= cut; right = int(((pick & (y == 1)) | (~pick & (y == 0))).sum())
        print(f"   upset when chance >= {cut:.0%}: right {right}/511 | upsets picked {int(pick.sum())} ({pick.sum() / 16:.1f} a year), hit {int((pick & (y == 1)).sum())} ({(pick & (y == 1)).sum() / max(pick.sum(), 1):.0%}) | upsets caught {int((pick & (y == 1)).sum())}/{int(y.sum())}")
print("\nreference: always the higher seed 368/511 | current model 386/511 (AUC 0.778)")
p = res["with seed gap"]; q = res["without seed"]
print("\n2025 and 2026 upsets: chance the model gave the winning lower seed (with seed / without seed)")
for j, r in enumerate(rows):
    if r["s"] in ("2024-25", "2025-26") and y[j] == 1: print(f"   {r['s']} ({r['sL']}) {r['L']} over ({r['sH']}) {r['H']}: {p[j]:.0%} / {q[j]:.0%}")
json.dump({"inputs": INPUTS, "p_seed": p.tolist(), "p_noseed": q.tolist()}, open(os.path.join(HERE, "m188_out.json"), "w"))
