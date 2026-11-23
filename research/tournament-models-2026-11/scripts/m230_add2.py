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
import shutil
NEW = U29 + [CAST, PCS]
sL = np.array([r["sL"] for r in rows])
def evaluate(ins):
    X = np.column_stack([ALL[c] for c in ins])
    pin = 1 / (1 + np.exp(-ridge(X, y, W)(X))); pho = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; pho[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    return pin, pho
R = {lab: evaluate(ins) for lab, ins in (("current 29", U29), ("31 (+ cast BPM + perimeter cut share)", NEW))}
for lab, (pin, pho) in R.items():
    print(f"\n== {lab}")
    for nm, p in (("fit on all years", pin), ("each year held out", pho)):
        a = (p + s_up + sim_up) / 3; v = ((p >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2
        best = max(range(35, 56), key=lambda c: int(((a >= c / 100) == (y == 1)).sum()))
        print(f"   {nm:20} Upset alone: AUC {auc(p, y):.3f}, right at 40% {int(((p >= .4) == (y == 1)).sum())} | AVERAGE: AUC {auc(a, y):.3f}, right at 45% {int(((a >= .45) == (y == 1)).sum())} ({int((a >= .45).sum())} upset picks, {int(((a >= .45) & (y == 1)).sum())} hit), at 50% {int(((a >= .5) == (y == 1)).sum())}, best cutoff {best}% -> {int(((a >= best / 100) == (y == 1)).sum())} | vote {int((v == (y == 1)).sum())}")
pin, pho = R["31 (+ cast BPM + perimeter cut share)"]; a = (pin + s_up + sim_up) / 3; pk = a >= .45
print("\n31-input average at 45% (fit on all years), by matchup: games | upsets | caught | upset picks | right")
for h in range(1, 9):
    m = sL == 17 - h; print(f"   {h} vs {17 - h}|{int(m.sum())}|{int(y[m].sum())}|{int((pk & m & (y == 1)).sum())}|{int((pk & m).sum())}|{int(((pk == (y == 1)) & m).sum())}")
sp = os.path.join(H, "upset_model_r64.json"); shutil.copy(sp, os.path.join(H, "upset_model_r64_29inputs.json"))
dd = json.load(open(sp)); dd["inputs"] = NEW
dd["results_each_year_held_out"] = {"games_right": int(((pho >= .4) == (y == 1)).sum()), "of": 511, "auc": round(auc(pho, y), 3)}
dd["results_fit_on_all_years"] = {"games_right": int(((pin >= .4) == (y == 1)).sum()), "auc": round(auc(pin, y), 3)}
dd["note"] = "31 inputs: 28 + favorite ORB% + supporting-cast BPM gap (10+ mpg minus top 2 by BPM) + share of perimeter cuts the underdog allows; user 2026-11-18"
json.dump(dd, open(sp, "w"), indent=1); json.dump({"inputs": NEW, "p_heldout": pho.tolist(), "p_all": pin.tolist()}, open(os.path.join(H, "m230_out.json"), "w"))