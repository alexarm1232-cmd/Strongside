# The four boxes (model right/wrong x simulator right/wrong) as a picture of the teams. Every Round-of-64-to-title game
# (First Four out) puts BOTH teams in its box. Each team point = that team's pre-tournament numbers the model uses (the
# measures behind its 30 inputs: rating, schedule strength, tempo/pace and the 25 team/player measures, as season
# percentiles), labelled with team AND year (so Duke 2015 and Duke 2019 are different points). All boxes pooled, PCA on
# the standardized numbers, first two components for the picture. Tests: do the boxes sit in different places?
# (permutation test on the centroids, all components; and model-wins vs simulator-wins boxes alone)
import os, sys, re, json, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM tpct ppct TEAMK PLAYK
    import m18_rebuild as R
D = np.load("m3_data.npz", allow_pickle=True); NAMES = [str(n) for n in D["names"]]; sS, sW = D["seedS"], D["seedW"]
BG, RND, seas, yb = R.B.G, R.RND, R.seas, R.yb
FF = RND == "First Four"
v = np.load("m56_scores.npz")["fixed 27 (picked from all games)"]; sim = R.B.simS
mr = (v > 0) == yb; sr = (sim > 0.5) == yb                       # model right, simulator right (no pick'ems in these games)
QUAD = np.where(mr & sr, "Both right", np.where(mr & ~sr, "Model right, sim wrong", np.where(~mr & sr, "Sim right, model wrong", "Both wrong")))
KEYS = []
for n in [m for m in NAMES if m not in ("gap", "sos gap", "gap x possessions") and "stocks" not in m]:
    k = n[2:]
    if k not in KEYS: KEYS.append(k)
LABEL = {"adj_net": "Rating (net)", "sos": "Schedule strength", "tempo": "Tempo"}
FEATS = ["adj_net", "sos"] + [k for k in KEYS]
FEATS = list(dict.fromkeys(FEATS + (["tempo"] if "tempo" not in FEATS else [])))
S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
RN = {"First round": "Round of 64", "Second round": "Round of 32", "Sweet 16": "Sweet 16", "Elite Eight": "Elite Eight", "Final Four": "Final Four", "Championship": "Title"}
pts, X = [], []
for i in np.where(~FF)[0]:
    g = BG[i]; gd = {"gid": g["gid"], "season": seas[i]}
    for team, opp, sd, od, won in ((S_name[i], W_name[i], sS[i], sW[i], yb[i]), (W_name[i], S_name[i], sW[i], sS[i], not yb[i])):
        row = []
        for k in FEATS:
            row.append(ppct(gd, team, k) if k in PLAYK else tpct(seas[i], team, k))
        if any(x is None or not np.isfinite(x) for x in row): continue
        X.append(row); pts.append(dict(team=str(team), year=int(seas[i][:4]) + 1, opp=str(opp), seed=int(sd), opp_seed=int(od),
                                       round=RN[RND[i]], quad=str(QUAD[i]), won=bool(won), game=int(i)))
X = np.array(X, float); print("team points:", len(X), "features:", len(FEATS))
Z = (X - X.mean(0)) / (X.std(0) + 1e-9); U, S_, Vt = np.linalg.svd(Z, full_matrices=False); pve = S_ ** 2 / (S_ ** 2).sum()
PC = Z @ Vt.T
for p, (a, b) in zip(pts, PC[:, :2]): p["pc1"], p["pc2"] = round(float(a), 3), round(float(b), 3)
nice = lambda k: LABEL.get(k, k.replace("pt_d_share ", "def. share vs ").replace("pt_d_ppp ", "def. pts/play vs ").replace("pt_share ", "share of ")
                         .replace("pt_ppp ", "pts/play on ").replace("d_", "opp. ").replace("_", " "))
load = {f"PC{c + 1}": sorted([(nice(FEATS[j]), round(float(Vt[c, j]), 3)) for j in range(len(FEATS))], key=lambda t: -abs(t[1]))[:6] for c in range(2)}
print("variance explained:", [round(float(x), 3) for x in pve[:5]]); print(json.dumps(load, indent=1))
quads = ["Both right", "Model right, sim wrong", "Sim right, model wrong", "Both wrong"]
q = np.array([p["quad"] for p in pts])
cent = {k: [round(float(PC[q == k, 0].mean()), 3), round(float(PC[q == k, 1].mean()), 3), int((q == k).sum())] for k in quads}
print("centroids (PC1, PC2, points):", cent)
def perm(mask_a, mask_b, cols=None, reps=2000):
    A = PC if cols is None else PC[:, cols]; idx = np.where(mask_a | mask_b)[0]; la = mask_a[idx]
    stat = lambda l: float(np.linalg.norm(A[idx][l].mean(0) - A[idx][~l].mean(0)))
    obs = stat(la); rng = np.random.default_rng(1); null = [stat(rng.permutation(la)) for _ in range(reps)]
    return obs, float((np.sum(np.array(null) >= obs) + 1) / (reps + 1))
tests = {}
for a, b in [("Model right, sim wrong", "Sim right, model wrong"), ("Both right", "Both wrong"), ("Model right, sim wrong", "Both right")]:
    o, p_ = perm(q == a, q == b); o2, p2 = perm(q == a, q == b, cols=[0, 1]); tests[f"{a} vs {b}"] = dict(all_dist=o, all_p=p_, pc12_dist=o2, pc12_p=p2)
    print(f"{a} vs {b}: all components p={p_:.3f}; PC1-2 p={p2:.3f}")
# how the boxes differ in plain numbers: mean percentile of rating / tempo etc. per box, winners and losers separately
summ = {}
for k in quads:
    m = q == k
    summ[k] = {nice(f): round(float(X[m, j].mean()), 1) for j, f in enumerate(FEATS) if f in ("adj_net", "sos", "tempo")}
    summ[k]["seed"] = round(float(np.mean([p["seed"] for p, mm in zip(pts, m) if mm])), 2)
print(summ)
json.dump(dict(points=pts, pve=[float(x) for x in pve[:10]], loadings=load, centroids=cent, tests=tests, summary=summ,
               features=[nice(f) for f in FEATS]), open(os.path.join(HERE, "m103_out.json"), "w"))

