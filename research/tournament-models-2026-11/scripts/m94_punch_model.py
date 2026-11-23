# Punching up, in the model. For each game, the weaker-rated team's regular-season punch-up: its margin vs that season's
# top 40 beyond what the ratings expect (m93), only when it is outside the top 40 and had 2+ such games (else 0), and
# whether it beat a top-40 team. Added to the round lines beside coach + star (as m84/m88), each tournament held out.
# Scored on the Rounds of 64 to Elite Eight (959 games): games right, log-loss (are the chances better even where the pick
# doesn't flip), and upset picks (the worse seed picked) with how many hit.
import os, sys, re, json, contextlib, io, math
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM
    import m18_rebuild as R
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
G = json.load(open(os.path.join(HERE, "m88_games.json")))
NET = {(s, clean(t)): v["adj_net"] for s in TM for t, v in TM[s].items()}
TOP = {}
for s in TM:
    for k, (t, v) in enumerate(sorted(TM[s].items(), key=lambda kv: -kv[1]["adj_net"])): TOP[(s, clean(t))] = k < 40
rows = [(s, clean(h), clean(a), n, f) for s, h, a, n, f, m in G if (s, clean(h)) in NET and (s, clean(a)) in NET]
gap = np.array([NET[(r[0], r[1])] - NET[(r[0], r[2])] for r in rows]); home = np.array([0.0 if r[3] else 1.0 for r in rows])
fin = np.array([r[4] for r in rows], float); A = np.column_stack([gap, home]); res = fin - A @ np.linalg.lstsq(A, fin, rcond=None)[0]
from collections import defaultdict
PU = defaultdict(list); BW = defaultdict(int)
for k, (s, h, a, n, f) in enumerate(rows):
    for team, opp, sg in ((h, a, 1), (a, h, -1)):
        if TOP[(s, opp)] and not TOP[(s, team)]:
            PU[(s, team)].append(sg * res[k]); BW[(s, team)] += sg * f > 0
BG, RND, seas, yb = R.B.G, R.RND, R.seas, R.yb
D3 = np.load("m3_data.npz", allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
pu = np.zeros(len(BG)); bw = np.zeros(len(BG)); low = np.zeros(len(BG))
for i in range(len(BG)):
    k = (seas[i], clean(W_name[i]))
    if k in NET and not TOP.get(k, True) and len(PU[k]) >= 2: pu[i] = np.mean(PU[k])
    if k in NET and not TOP.get(k, True): bw[i] = float(BW[k] >= 1)
    low[i] = float(sW[i] >= 10)
print(f"games where the weaker-rated team has a punch-up number: {int((pu != 0).sum())} of {len(BG)}")
CS = R.EXTRA["coach+star"]; WT = R.weights(12)
BASE = {s: (tr, te) + R.base_scores(tr, te, WT) for s in R.SEASONS for tr, te in [(np.where(seas != s)[0], np.where(seas == s)[0])]}
def run(extra):
    sc = np.zeros(len(yb))
    for s, (tr, te, m_tr, m_te) in BASE.items(): sc[te] = R.model(m_tr, tr, m_te, te, WT, extra)
    return sc
E4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"]); diff = E4 & (sS != sW)
dogS = sS > sW; up = np.where(dogS, yb, ~yb)
def show(nm, sc, base=None):
    right = int(((sc > 0) == yb)[E4].sum()); p = np.clip(1 / (1 + np.exp(-sc)), 1e-6, 1 - 1e-6)
    ll = float(-np.mean(np.where(yb, np.log(p), np.log(1 - p))[E4]))
    dp = diff & np.where(dogS, sc > 0, sc < 0); lowd = dp & (np.maximum(sS, sW) >= 10)
    extra = ""
    if base is not None:
        b = (base > 0) == yb; r = (sc > 0) == yb; extra = f" | fixed {int((E4 & r & ~b).sum())}, broke {int((E4 & b & ~r).sum())}"
    print(f"   {nm:52} right {right:4d}  log-loss {ll:.4f} | upset picks {int(dp.sum()):3d} hit {int(up[dp].sum()):3d} ({up[dp].mean():.0%}); "
          f"10-16 seeds {int(lowd.sum()):2d} hit {int(up[lowd].sum()):2d}{extra}")
print("\nRound of 64 to Elite Eight, 959 games, each tournament held out")
b0 = run(CS); show("current model", b0)
for nm, ex in [("+ weaker team's punch-up", pu), ("+ weaker team beat a top-40 team", bw), ("+ both", np.column_stack([pu, bw])),
               ("+ punch-up, 10-16 seeds only", pu * low), ("+ beat a top-40 team, 10-16 seeds only", bw * low),
               ("+ both, 10-16 seeds only", np.column_stack([pu * low, bw * low]))]:
    show(nm, run(np.column_stack([CS, ex])), b0)
