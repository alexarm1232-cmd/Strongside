# The 2x2 from the sketch: model right/wrong vs simulator right/wrong (and the other pairs), R64-title, First Four cut.
# Pick'ems (simulator or closing line exactly 50%) count half, as m57.
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
__file__ = os.path.join(OLD, "overfit_test.py")                # overfit_test finds its files next to __file__
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("NAMES = {")[0])   # closeright
    import m18_rebuild as R
yb, keep = R.yb, R.RND != "First Four"
PK = np.abs(R.B.simS - 0.5) < 1e-4
sim = np.where(PK, 0.5, (R.B.simS > 0.5) == yb).astype(float)
model = ((np.load("m56_scores.npz")["fixed 27 (picked from all games)"] > 0) == yb).astype(float)
D = np.load("m3_data.npz", allow_pickle=True); sS, sW = D["seedS"], D["seedW"]
seed = np.where(sS == sW, 0.5, np.where(sS < sW, yb, ~yb)).astype(float)
P = {"model": model, "simulator": sim, "closing line": closeright.astype(float), "seeds": seed}
n = int(keep.sum()); print("games", n, {k: round(float(v[keep].sum()), 1) for k, v in P.items()})
def grid(a, b):
    A, B = P[a][keep], P[b][keep]
    both = ((A == 1) & (B == 1)).sum(); none = ((A == 0) & (B == 0)).sum()
    ao = ((A == 1) & (B == 0)).sum(); bo = ((A == 0) & (B == 1)).sum(); half = ((A == 0.5) | (B == 0.5)).sum()
    print(f"\n{a} vs {b}: both right {both}, both wrong {none}  -> agree {both + none} ({(both + none) / n:.1%})")
    print(f"   splits: {a} right {ao}, {b} right {bo}  ({ao + bo} games, {a} wins {ao / max(ao + bo, 1):.1%}); half-games {half}")
for a, b in (("model", "simulator"), ("model", "closing line"), ("simulator", "closing line"), ("closing line", "seeds"), ("model", "seeds")):
    grid(a, b)
