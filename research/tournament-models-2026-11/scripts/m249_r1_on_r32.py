# Every Round 1 Upset Model input tested on the Round of 32: z with the seed gap controlled (Round 1 vs Round of 32),
# then Round of 32 models: R32 leaders (14), the 31 Round 1 inputs refit, R1 inputs that also pass in R32, leaders + those,
# the Round 1 model as is; inputs fixed, fit with each year held out (how the Round 1 model was scored); averages with
# the original model and the simulator.
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("RNDS", "Second round")
src = open(os.path.join(HERE, "m247_s16_model.py"), encoding="utf-8").read()
exec(src[:src.index("allm = np.ones")])
INS = json.load(open(os.path.join(HERE, "m230_out.json")))["inputs"]
fullcol = lambda c: (F["L " + c.split(" ", 1)[1]] - F["H " + c.split(" ", 1)[1]]) if c.startswith("L-H ") else F[c]
R1m = rnd == "First round"; i1 = np.where(R1m)[0]; y1 = y[i1]; sg1 = sgap[i1]; e1m = np.array([int(s[:4]) < 2018 for s in seas[i1]])
def waldv(v, yy, m, c):
    X = np.column_stack([(c[m] - c[m].mean()) / c[m].std(), (v[m] - v[m].mean()) / (v[m].std() + 1e-12), np.ones(m.sum())]); w = np.zeros(3)
    for _ in range(40):
        p = 1 / (1 + np.exp(-X @ w)); Hm = X.T @ (X * (p * (1 - p))[:, None]) + 1e-4 * np.eye(3); w += np.linalg.solve(Hm, X.T @ (yy[m] - p) - 1e-4 * w)
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
a1 = np.ones(len(i1), bool); a2 = np.ones(nS, bool)
print(f"Round of 32: {nS} games, {int(ys.sum())} upsets\n")
print(f"{'Round 1 input':42} {'R1 z':>6} {'R32 z':>6} {'10-17':>6} {'18-26':>6}  same direction as R1?")
rows_ = []
for c in INS:
    v1, v2 = fullcol(c)[i1], fullcol(c)[idx]
    z1, z2 = waldv(v1, y1, a1, sg1), waldv(v2, ys, a2, sg)
    ea, eb = waldv(v2, ys, early, sg), waldv(v2, ys, ~early, sg)
    rows_.append((c, z1, z2, ea, eb))
for c, z1, z2, ea, eb in sorted(rows_, key=lambda r: -abs(r[2])):
    tag = ("yes" if np.sign(z1) == np.sign(z2) else "FLIPS") + ("  <- passes in R32" if abs(z2) >= 2 and np.sign(z1) == np.sign(z2) else "")
    print(f"{c:42} {z1:+6.2f} {z2:+6.2f} {ea:+6.1f} {eb:+6.1f}  {tag}")
same = sum(np.sign(r[1]) == np.sign(r[2]) for r in rows_)
print(f"\n{same}/31 keep the Round 1 direction; {sum(abs(r[2]) >= 2 for r in rows_)} at |z|>=2 in R32; {sum(abs(r[2]) >= 1 and np.sign(r[1]) == np.sign(r[2]) for r in rows_)} at |z|>=1 same direction")
# ---- models
def X_of(names): return np.column_stack([fullcol(c)[idx] for c in names])
LEAD = ["L-H cast_bpm_bpm", "H pm_behind6", "H pm_ahead10", "H pt_d_share Post-Up", "H pt_ppp Big Cut & Roll", "L pt_share Post-Up", "L-H big_height", "H ftr",
        "L-H tourney wins last 3", "H pt_d_ppp High-Low", "L pt_ppp Inside Out", "L-H star_usage_rate", "H pt_share Perimeter Cut", "L-H pt_ppp Pick & Pop"]
PASS = [r[0] for r in rows_ if abs(r[2]) >= 2 and np.sign(r[1]) == np.sign(r[2])]
P1 = [r[0] for r in rows_ if abs(r[2]) >= 1 and np.sign(r[1]) == np.sign(r[2])]
def ho(names, lam=30.0):
    Xg = X_of(names); p = np.zeros(nS)
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; f, _ = fit(Xg[tr], ys[tr], Ws[tr], lam); p[te] = f(Xg[te])
    fa, _ = fit(Xg, ys, Ws, lam); return p, fa(Xg)
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
right = lambda pk, m=a2: int((pk[m] == (ys[m] == 1)).sum())
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
s_up_ = s_up[idx]; sim_up_ = sim_up[idx]
X64 = np.column_stack([fullcol(c) for c in INS]); f64, _ = fit(X64[R1m], y[R1m], W[R1m]); p64 = f64(X64[idx])
print(f"\nRound of 32 models ({nS} games; higher seed 187, simulator 192, original model 203)")
print(f"{'model':52} {'inputs':>6} | fit all yrs: AUC, right@40/50 | held out: AUC, right@40/50 | avg of 3 held out: right@45/50")
def show(lab, p_ho, p_all, k):
    av = (p_ho + s_up_ + sim_up_) / 3
    print(f"{lab:52} {k:6} | {auc(p_all, ys):.3f} {right(p_all >= .4)} {right(p_all >= .5)} | {auc(p_ho, ys):.3f} {right(p_ho >= .4)} {right(p_ho >= .5)} | {right(av >= .45)} {right(av >= .5)}  (AUC {auc(av, ys):.3f})")
show("Round 1 Upset Model as is (not refit)", p64, p64, 31)
for lab, names in (("31 Round 1 inputs, refit on R32", INS), (f"R1 inputs that pass in R32 (|z|>=2)", PASS), (f"R1 inputs same direction, |z|>=1 in R32", P1),
                   ("R32 leaders (14)", LEAD), ("R32 leaders + R1 passes", list(dict.fromkeys(LEAD + PASS))), ("R32 leaders + R1 |z|>=1", list(dict.fromkeys(LEAD + P1)))):
    if not names: print(f"{lab}: none"); continue
    p_ho, p_all = ho(names); show(lab, p_ho, p_all, len(names))
print(f"{'original + simulator average':52} {'':6} | {'':27} | {auc((s_up_ + sim_up_) / 2, ys):.3f} {right((s_up_ + sim_up_) / 2 >= .4)} {right((s_up_ + sim_up_) / 2 >= .5)}")
print("\nR1 passes:", PASS); print("R1 |z|>=1 same direction:", P1)
