# How many games does the build need? Run the same honest pipeline (screen |z|>=2 with seed gap controlled, same sign both
# halves, one per overlap group, ridge 30) on ROUND 1, but train each held-out year on only k of the other years.
# If Round 1 collapses at ~256 training games, the later-round failures are about game counts, not the rounds.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RNDS"] = "First round"
src = open(os.path.join(HERE, "m247_s16_model.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("# ---- 1.")])
import numpy as np
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
right = lambda pk: int((pk == (ys == 1)).sum())
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
s_up_, sim_up_ = s_up[idx], sim_up[idx]
print(f"Round 1: {nS} games, {int(ys.sum())} upsets | higher seed {right(np.zeros(nS) >= .5)}, original {right(s_up_ >= .5)}, simulator {right(sim_up_ >= .5)}")
rng = np.random.default_rng(7)
print("training years | ~games | ~upsets | inputs picked | held-out AUC | right@40% | right@50% | avg of 3 @45%")
for k, reps in ((4, 3), (8, 3), (11, 2), (15, 1)):
    for r_ in range(reps):
        p = np.zeros(nS); nin = []; ng = []; nu = []
        for s in SEASONS:
            others = [x for x in SEASONS if x != s]; use = list(rng.choice(others, k, replace=False)) if k < 15 else others
            tr, te = np.isin(Ss, use), Ss == s
            sel = [j for j, _ in screen(tr)]; nin.append(len(sel)); ng.append(tr.sum()); nu.append(ys[tr].sum())
            if not sel: p[te] = ys[tr].mean(); continue
            f, _ = fit(PX[tr][:, sel], ys[tr], Ws[tr]); p[te] = f(PX[te][:, sel])
        av = (p + s_up_ + sim_up_) / 3
        print(f"{k:14} | {np.mean(ng):6.0f} | {np.mean(nu):7.0f} | {np.mean(nin):13.1f} | {auc(p, ys):12.3f} | {right(p >= .4):9} | {right(p >= .5):9} | {right(av >= .45)}", flush=True)
