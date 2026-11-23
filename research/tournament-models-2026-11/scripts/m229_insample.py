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
print("\nfit on ALL years (no hold-out)")
print("version | Upset Model AUC | Upset right at 40% | upset picks (hit) | average AUC | average right at 45% | avg upset picks (hit)")
for lab, ins in (("Upset Model 29 (current)", U29), ("+ steals gap", U29 + [STL]), ("+ supporting-cast BPM gap", U29 + [CAST]), ("+ perimeter cut share allowed", U29 + [PCS]),
                 ("+ steals gap + cast BPM", U29 + [STL, CAST]), ("+ steals gap + perimeter cut share", U29 + [STL, PCS]), ("+ cast BPM + perimeter cut share", U29 + [CAST, PCS]), ("+ all three", U29 + [STL, CAST, PCS])):
    X = np.column_stack([ALL[c] for c in ins]); p = 1 / (1 + np.exp(-ridge(X, y, W)(X))); a = (p + s_up + sim_up) / 3
    print(f"{lab}|{auc(p, y):.3f}|{int(((p >= .4) == (y == 1)).sum())}|{int((p >= .4).sum())} ({int(((p >= .4) & (y == 1)).sum())})|{auc(a, y):.3f}|{int(((a >= .45) == (y == 1)).sum())}|{int((a >= .45).sum())} ({int(((a >= .45) & (y == 1)).sum())})")