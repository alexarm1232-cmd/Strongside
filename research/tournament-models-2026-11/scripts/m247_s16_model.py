# Sweet 16 -> title game model, trained like the Round 1 Upset Model:
#   game rows (H = better seed, L = worse seed; same seed: H = favorite), outcome = L wins ("upset");
#   pool = every H, L and L-H measure; screen = Wald z with the seed gap controlled, |z| >= 2, same sign in 2010-17 and 2018-26;
#   one per overlap group (|r| >= 0.3); ridge logistic, penalty 30, half-life-12 season weights, standardized; no seed/net gap inputs.
# Scored: games right on the 240 real Sweet 16-to-title games (each year held out, inputs re-picked inside each fold),
#         vs higher seed, better net rating, original model, simulator; plus a bracket from the real Sweet 16 field.
import os, sys, json, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "m241_later_rounds.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()):
    exec(src[:src.index("col = lambda c")])
import numpy as np
RNDS = os.environ.get("RNDS", "Sweet 16,Elite Eight,Final Four,Championship").split(",")
M = np.isin(rnd, RNDS); idx = np.where(M)[0]; print("rounds:", RNDS)
ys, Ws, Ss, sg, rg = y[idx], W[idx], seas[idx], sgap[idx], rgap[idx]; nS = len(idx)
early = np.array([int(s[:4]) < 2018 for s in Ss]); SEASONS = sorted(set(Ss))
print(f"Sweet 16 to title: {nS} games, {int(ys.sum())} won by the worse seed ({ys.mean():.0%}); seasons {len(SEASONS)}")
# ---- pool
bases = sorted({k[2:] for k in F if k[:2] in ("H ", "L ")}); bases = [b for b in bases if "H " + b in F and "L " + b in F]
POOL = {}
for b in bases:
    h, l = F["H " + b][idx], F["L " + b][idx]
    for nm, v in ((f"H {b}", h), (f"L {b}", l), (f"L-H {b}", l - h)):
        if np.std(v) > 1e-9: POOL[nm] = v
NM = list(POOL); PX = np.column_stack([POOL[c] for c in NM])
print(f"pool: {len(NM)} measures")
def wald(v, yy, m, ctrl):
    X = np.column_stack([(c[m] - c[m].mean()) / (c[m].std() + 1e-12) for c in ctrl] + [(v[m] - v[m].mean()) / (v[m].std() + 1e-12), np.ones(m.sum())]); w = np.zeros(X.shape[1])
    for _ in range(40):
        p = 1 / (1 + np.exp(-X @ w)); Hm = X.T @ (X * (p * (1 - p))[:, None]) + 1e-4 * np.eye(X.shape[1]); w += np.linalg.solve(Hm, X.T @ (yy[m] - p) - 1e-4 * w)
    return w[-2] / math.sqrt(np.linalg.inv(Hm)[-2, -2])
def screen(m, ctrl=None, zmin=2.0, rmax=0.3):
    ctrl = ctrl if ctrl is not None else [sg]; yrs = sorted(set(Ss[m])); h1 = m & np.isin(Ss, yrs[:len(yrs) // 2]); h2 = m & ~h1
    res = []
    for j, c in enumerate(NM):
        try: z = wald(PX[:, j], ys, m, ctrl)
        except Exception: continue
        if abs(z) >= zmin: res.append((abs(z), j, z))
    res.sort(reverse=True); kept = []
    for _, j, z in res:
        if any(abs(np.corrcoef(PX[m, j], PX[m, k])[0, 1]) >= rmax for k, _ in kept): continue
        try:
            if np.sign(wald(PX[:, j], ys, h1, ctrl)) != np.sign(z) or np.sign(wald(PX[:, j], ys, h2, ctrl)) != np.sign(z): continue
        except Exception: continue
        kept.append((j, z))
    return kept
def fit(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return (lambda Xq: 1 / (1 + np.exp(-(np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b)))), b
allm = np.ones(nS, bool)
# ---- 1. screen on all years (what the model would be built from)
K = screen(allm)
print(f"\n1. Screen on all {nS} games (seed gap controlled, |z|>=2, same sign both halves, one per overlap group): {len(K)} inputs")
for j, z in K: print(f"   {NM[j]:45} z {z:+.2f} | 2010-17 {wald(PX[:, j], ys, early, [sg]):+.1f} | 2018-26 {wald(PX[:, j], ys, ~early, [sg]):+.1f}")
print(f"   (chance: ~{int(len(NM) * .046)} of {len(NM)} pass |z|>=2 before the half-split and overlap filters)")
# ---- 2. held-out scoring
def heldout(lam=30.0, ctrl=None, rmax=0.3, fixed=None):
    p = np.zeros(nS); picks = {}
    for s in SEASONS:
        tr, te = Ss != s, Ss == s
        sel = fixed if fixed is not None else [j for j, _ in screen(tr, ctrl, rmax=rmax)]
        for j in sel: picks[NM[j]] = picks.get(NM[j], 0) + 1
        f, _ = fit(PX[tr][:, sel], ys[tr], Ws[tr], lam); p[te] = f(PX[te][:, sel])
    return p, picks
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
right = lambda pk, m=allm: int((pk[m] == (ys[m] == 1)).sum())
def line(lab, p, cut):
    pk = p >= cut; print(f"   {lab:58} | AUC {auc(p, ys):.3f} | right {right(pk)}/{nS} | 2010-17 {right(pk, early)}/{int(early.sum())} | 2018-26 {right(pk, ~early)}/{int((~early).sum())} | upset picks {int(pk.sum())} (hit {int((pk & (ys == 1)).sum())})")
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
s_up_ = s_up[idx]; sim_up_ = sim_up[idx]; netdog = (rg < 0).astype(float)
print(f"\n2. Games right, Sweet 16 to title ({nS} games, {int(ys.sum())} upsets)")
line("Higher seed every time", np.zeros(nS), .5)
line("Better net rating every time", netdog + 0 * rg, .5)
line("Original model", s_up_, .5); line("Simulator", sim_up_, .5)
selK = [j for j, _ in K]
fA, bA = fit(PX[:, selK], ys, Ws); pA = fA(PX[:, selK])
for cut in (.4, .5): line(f"S16 model, inputs + fit on all years, {cut:.0%} (in sample)", pA, cut)
pF, _ = heldout(fixed=selK)
for cut in (.4, .5): line(f"S16 model, all-years inputs, each year held out, {cut:.0%}", pF, cut)
pH, picks = heldout()
for cut in (.4, .5): line(f"S16 model, inputs re-picked in each fold (honest), {cut:.0%}", pH, cut)
print("      picked most often:", sorted(picks.items(), key=lambda x: -x[1])[:10])
pHn, picksn = heldout(ctrl=[sg, rg])
for cut in (.4, .5): line(f"S16 model, screened beyond seed AND net gap (honest), {cut:.0%}", pHn, cut)
# with the net gap as an input (strength + style)
PX = np.column_stack([PX, rg, sg]); NM = NM + ["net gap", "seed gap"]
pN = np.zeros(nS)
for s in SEASONS:
    tr, te = Ss != s, Ss == s; sel = [j for j, _ in screen(tr)] + [len(NM) - 2]; f, _ = fit(PX[tr][:, sel], ys[tr], Ws[tr]); pN[te] = f(PX[te][:, sel])
for cut in (.4, .5): line(f"S16 model + net gap input (honest), {cut:.0%}", pN, cut)
for lab, p in (("Average: S16 model + original + simulator", (pH + s_up_ + sim_up_) / 3), ("Average: S16 model+net + original + simulator", (pN + s_up_ + sim_up_) / 3)):
    for cut in (.45, .5): line(f"{lab}, {cut:.0%}", p, cut)
print("\n   by round (honest S16 model at 50% | original | simulator | higher seed):")
for rd in RNDS:
    m = rnd[idx] == rd
    print(f"   {rd:13} {int(m.sum()):3} games | {right(pH >= .5, m)} | {right(s_up_ >= .5, m)} | {right(sim_up_ >= .5, m)} | {right(np.zeros(nS) >= .5, m)}")
print("\n3. All-years fit, standardized weights (+ = helps the worse seed):")
for i in np.argsort(-np.abs(bA[:-1])): print(f"   {NM[selK[i]]:45} {bA[i]:+.3f}")
json.dump({"inputs": [NM[j] for j in selK], "p_honest": pH.tolist(), "p_net": pN.tolist(), "idx": idx.tolist()}, open(os.path.join(HERE, f"m247_out_{RNDS[0].replace(' ', '')}_{len(RNDS)}.json"), "w"))
