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
g = np.arange(.30, .61, .01)
def cut_on(q, m):
    sc = np.array([int(((q[m] >= c) == (y[m] == 1)).sum()) for c in g]); return float(np.median(g[sc == sc.max()]))
def run(ins):
    X = np.column_stack([ALL[c] for c in ins]); p = np.zeros(n); pa = np.zeros(n, bool)
    for s in sorted(set(seas)):
        tr, te = seas != s, seas == s; p[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    a = (p + s_up + sim_up) / 3
    for s in sorted(set(seas)):   # average cutoff from the other years (their held-out chances)
        tr, te = seas != s, seas == s; pa[te] = a[te] >= cut_on(a, tr)
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    af, ab = (f + s_up[~early] + sim_up[~early]) / 3, (b + s_up[early] + sim_up[early]) / 3
    # forward/backward for the average: cutoff picked on the training half using the training half's held-out avg
    fw_a = int(((af >= cut_on(a, early)) == (y[~early] == 1)).sum()); bw_a = int(((ab >= cut_on(a, ~early)) == (y[early] == 1)).sum())
    return dict(u=int(((p >= .4) == (y == 1)).sum()), auc=auc(p, y), uf=int(((f >= .4) == (y[~early] == 1)).sum()), ub=int(((b >= .4) == (y[early] == 1)).sum()),
                a45=int(((a >= .45) == (y == 1)).sum()), ah=int((pa == (y == 1)).sum()), af=fw_a, ab=bw_a, picks=int(pa.sum()), hit=int((pa & (y == 1)).sum()))
print("\n                                          | UPSET MODEL ALONE (40%)                     | AVERAGE OF 3")
print("version                                   | held out | AUC   | fwd  | back | fwd+back | avg 45% | avg honest | fwd | back | fwd+back | picks (hit)")
for lab, ins in (("Upset Model 29 (current)", U29), ("+ steals gap", U29 + [STL]), ("+ supporting-cast BPM gap", U29 + [CAST]), ("+ perimeter cut share allowed", U29 + [PCS]),
                 ("+ steals gap + cast BPM", U29 + [STL, CAST]), ("+ steals gap + perimeter cut share", U29 + [STL, PCS]), ("+ all three", U29 + [STL, CAST, PCS])):
    r = run(ins)
    print(f"{lab:41} | {r['u']:8} | {r['auc']:.3f} | {r['uf']:4} | {r['ub']:4} | {r['uf'] + r['ub']:8} | {r['a45']:7} | {r['ah']:10} | {r['af']:3} | {r['ab']:4} | {r['af'] + r['ab']:8} | {r['picks']} ({r['hit']})")