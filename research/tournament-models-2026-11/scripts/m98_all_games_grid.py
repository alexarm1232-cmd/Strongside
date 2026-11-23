# Every method from m97, on EVERY game, with a grid of settings ("weights") per method. NumPy only.
# Inputs: the 30 measures + who plays (6) + coach/star (3) = 39 columns, S (stronger-rated) vs W; y = S won.
# Each tournament held out; training uses every game of the other 15 (First Four included). Scored on all 1,068 games and
# on the Round of 64 to title (1,007). Model-only everywhere (no simulator), so the current model's F4/title use its own line.
# Settings varied:
#   recency   H = sample weight halves every H seasons back (none = equal)
#   penalty   ridge strength (linear models), shrinkage (LDA/QDA), C (SVM), depth/size (trees), size/decay (neural net)
#   strength  the 3 team-strength inputs scaled up x1 or x3 before the ridge penalty (= penalised less, "weighted up")
# For each method: its default, its best setting (optimistic: picked after seeing every result), and an honest score
# (the setting chosen on the other 15 tournaments, then used on the held-out one).
import os, sys, contextlib, io, math, time, itertools
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM, TEAMK
    import m18_rebuild as R
    import m10_model2 as M
T0 = time.time()
seas, RND, y, yb = R.seas, R.RND, R.y.astype(float), R.yb
N = len(y); ALL = np.ones(N, bool); R64T = RND != "First Four"
CS = R.EXTRA["coach+star"]; X39 = np.column_stack([R.X30, M.F, CS]); SEASONS = list(R.SEASONS)
# ---- team styles (ML11B): k-means, 6 styles, on each team-season's play-type mix + tempo + 3-point rate (regular season,
# no game results used), then each game's stronger and weaker team's style as on/off columns (5 + 5, style 0 = baseline)
import re
SK = [k for k in TEAMK if k.startswith("pt_share")] + ["tempo", "r3"]
keys = [(s, t) for s in TM for t in TM[s] if all(TM[s][t].get(k) is not None for k in SK)]
V = np.array([[TM[s][t][k] for k in SK] for s, t in keys], float); Vz = (V - V.mean(0)) / (V.std(0) + 1e-9); best = None
for seed in range(10):
    rng = np.random.default_rng(seed); Cc = Vz[rng.choice(len(Vz), 6, replace=False)]
    for _ in range(100):
        lab = np.argmin(((Vz[:, None, :] - Cc[None]) ** 2).sum(2), 1); Cc = np.array([Vz[lab == c].mean(0) for c in range(6)])
    wss = ((Vz - Cc[lab]) ** 2).sum()
    if best is None or wss < best[0]: best = (wss, lab)
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
STY = {(s, clean(t)): l for (s, t), l in zip(keys, best[1])}
Wn = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(R.B.G, R.B.Sname)])
CLU = np.zeros((N, 10)); miss = 0
for i in range(N):
    a, b = STY.get((seas[i], clean(R.B.Sname[i]))), STY.get((seas[i], clean(Wn[i])))
    if a is None or b is None: miss += 1; continue
    if a > 0: CLU[i, a - 1] = 1
    if b > 0: CLU[i, 5 + b - 1] = 1
print(f"styles: {len(keys)} team-seasons clustered; games without both styles: {miss}")
XX, EXTRA = X39, CS                                            # switched to the with-styles versions on the second pass
WTS = {"none": R.weights(None), "12": R.weights(12), "6": R.weights(6)}
def loso(fp):                                                  # First Four out of training and scoring
    p = np.full(N, 0.5)
    for s in SEASONS:
        tr = np.where((seas != s) & R64T)[0]; te = np.where((seas == s) & R64T)[0]; p[te] = fp(tr, te)
    return np.clip(p, 1e-6, 1 - 1e-6)
RIGHT = lambda p: ((p > 0.5) == yb)
LL = lambda p, m: float(-np.mean(np.where(yb, np.log(p), np.log(1 - p))[m]))
# ---------------- methods: fit_predict(tr, te, **setting)
X30_ORIG = R.X30.copy(); WFIT = R.wfit
def current(tr, te, H="12", lam=30.0):
    R.wfit = lambda idx, wts, lam_=lam: WFIT(idx, wts, lam_)
    w = WTS[H]; m_tr, m_te = R.base_scores(tr, te, w); R.wfit = WFIT
    return 1 / (1 + np.exp(-R.model(m_tr, tr, m_te, te, w, EXTRA)))
def std(tr, te, sw=1.0):
    mu, sd = XX[tr].mean(0), XX[tr].std(0) + 1e-9; A, B = (XX[tr] - mu) / sd, (XX[te] - mu) / sd
    A[:, :3] *= sw; B[:, :3] *= sw; return A, B
def ridge(tr, te, H="12", lam=30.0, sw=1.0):
    A, B = std(tr, te, sw); w = WTS[H][tr]; Z = np.column_stack([A, np.ones(len(A))]); b = np.zeros(Z.shape[1])
    P = lam * np.eye(Z.shape[1]); P[-1, -1] = 0
    for _ in range(40):
        q = 1 / (1 + np.exp(-Z @ b)); Hs = Z.T @ (Z * (w * q * (1 - q))[:, None]) + P; b += np.linalg.solve(Hs, Z.T @ (w * (y[tr] - q)) - P @ b)
    return 1 / (1 + np.exp(-(np.column_stack([B, np.ones(len(B))]) @ b)))
def lda(tr, te, shrink=0.2, quad=False, sw=1.0):
    A, B = std(tr, te, sw); yy = y[tr]; mus = [A[yy == c].mean(0) for c in (0, 1)]; pri = [np.mean(yy == c) for c in (0, 1)]
    pooled = np.cov(A.T); covs = [np.cov(A[yy == c].T) for c in (0, 1)] if quad else [pooled, pooled]
    covs = [(1 - shrink) * C + shrink * np.eye(len(C)) * np.trace(C) / len(C) for C in covs]; ll = []
    for c in (0, 1):
        d = B - mus[c]; _, ld = np.linalg.slogdet(covs[c]); ll.append(-0.5 * np.einsum("ij,jk,ik->i", d, np.linalg.inv(covs[c]), d) - 0.5 * ld + math.log(pri[c]))
    return 1 / (1 + np.exp(np.clip(ll[0] - ll[1], -30, 30)))
def svm(tr, te, C=0.01, H="12", sw=1.0, it=600):
    A, B = std(tr, te, sw); s = 2 * y[tr] - 1; w0 = WTS[H][tr] / WTS[H][tr].mean(); w = np.zeros(A.shape[1]); b = 0.0; n = len(A)
    for t in range(1, it + 1):
        act = s * (A @ w + b) < 1; lr = 0.5 / math.sqrt(t)
        w -= lr * (C * w - ((w0 * s)[act, None] * A[act]).sum(0) / n); b -= lr * (-(w0 * s)[act].sum() / n)
    fa, fb = A @ w + b, B @ w + b; a = 1.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-a * fa)); a += np.sum((y[tr] - q) * fa) / (np.sum(q * (1 - q) * fa * fa) + 1e-9)
    return 1 / (1 + np.exp(-a * fb))
QS = np.linspace(0.05, 0.95, 15)
def build(X, g, h, depth, minleaf, fps, rng, lam=1.0):
    nodes = []
    def grow(idx, d):
        G, Hh = g[idx].sum(), h[idx].sum(); leaf = -G / (Hh + lam)
        if d == 0 or len(idx) < 2 * minleaf: nodes.append(("leaf", leaf)); return len(nodes) - 1
        fs = rng.choice(X.shape[1], fps, replace=False) if fps < X.shape[1] else range(X.shape[1]); best = None; base = G * G / (Hh + lam)
        for f in fs:
            col = X[idx, f]
            for thr in np.unique(np.quantile(col, QS)):
                L = col <= thr; nl = L.sum()
                if nl < minleaf or len(idx) - nl < minleaf: continue
                GL, HL = g[idx][L].sum(), h[idx][L].sum(); gain = GL * GL / (HL + lam) + (G - GL) ** 2 / (Hh - HL + lam) - base
                if best is None or gain > best[0]: best = (gain, f, thr)
        if best is None or best[0] <= 0: nodes.append(("leaf", leaf)); return len(nodes) - 1
        _, f, thr = best; me = len(nodes); nodes.append(None)
        nodes[me] = ("split", f, thr, grow(idx[X[idx, f] <= thr], d - 1), grow(idx[X[idx, f] > thr], d - 1)); return me
    grow(np.arange(len(X)), depth)
    def pred(Z):
        out = np.zeros(len(Z))
        for i, z in enumerate(Z):
            k = 0
            while nodes[k][0] == "split": _, f, thr, a, b = nodes[k]; k = a if z[f] <= thr else b
            out[i] = nodes[k][1]
        return out
    return pred
def tree(tr, te, depth=4, H="12"):
    A, B = XX[tr], XX[te]; w = WTS[H][tr]; p0 = np.average(y[tr], weights=w); f0 = math.log(p0 / (1 - p0))
    return 1 / (1 + np.exp(-(f0 + build(A, (p0 - y[tr]) * w, p0 * (1 - p0) * w, depth, 25, XX.shape[1], np.random.default_rng(1))(B))))
def forest(tr, te, depth=6, mtry=6, H="12", ntree=100):
    rng = np.random.default_rng(7); A, B = XX[tr], XX[te]; w = WTS[H][tr]; out = np.zeros(len(te))
    for _ in range(ntree):
        bs = rng.choice(len(tr), len(tr), replace=True, p=w / w.sum()); yy = y[tr][bs]; p0 = yy.mean()
        out += np.clip(p0 + build(A[bs], p0 - yy, np.ones(len(bs)), depth, 10, mtry, rng, lam=0.0)(B), 0.001, 0.999)
    return out / ntree
def boost(tr, te, rounds=200, depth=2, H="12", lr=0.05):
    rng = np.random.default_rng(3); A, B = XX[tr], XX[te]; w = WTS[H][tr]; p0 = np.average(y[tr], weights=w)
    fa = np.full(len(tr), math.log(p0 / (1 - p0))); fb = np.full(len(te), fa[0])
    for _ in range(rounds):
        sub = rng.random(len(tr)) < 0.7; q = 1 / (1 + np.exp(-fa)); g = (q - y[tr]) * w; h = q * (1 - q) * w
        pr = build(A[sub], g[sub], h[sub], depth, 20, XX.shape[1], rng, lam=5.0); fa += lr * pr(A); fb += lr * pr(B)
    return 1 / (1 + np.exp(-fb))
def mlp(tr, te, hidden=8, decay=0.03, H="12", epochs=400, seeds=5, sw=1.0):
    A, B = std(tr, te, sw); yy = y[tr]; wv = WTS[H][tr] / WTS[H][tr].mean(); out = np.zeros(len(te))
    for sd in range(seeds):
        rng = np.random.default_rng(sd); P = [rng.normal(0, 0.3, (A.shape[1], hidden)), np.zeros(hidden), rng.normal(0, 0.3, hidden), np.zeros(1)]
        m = [np.zeros_like(x) for x in P]; v = [np.zeros_like(x) for x in P]
        for ep in range(1, epochs + 1):
            Hh = np.tanh(A @ P[0] + P[1]); q = 1 / (1 + np.exp(-(Hh @ P[2] + P[3][0]))); e = wv * (q - yy) / len(A)
            dH = np.outer(e, P[2]) * (1 - Hh ** 2)
            grads = [A.T @ dH + decay * P[0], dH.sum(0), Hh.T @ e + decay * P[2], np.array([e.sum()])]
            for k in range(4):
                m[k] = 0.9 * m[k] + 0.1 * grads[k]; v[k] = 0.999 * v[k] + 0.001 * grads[k] ** 2
                P[k] = P[k] - 0.01 * (m[k] / (1 - 0.9 ** ep)) / (np.sqrt(v[k] / (1 - 0.999 ** ep)) + 1e-8)
        out += 1 / (1 + np.exp(-(np.tanh(B @ P[0] + P[1]) @ P[2] + P[3][0])))
    return out / seeds
BX = R.B.X; Zs = (BX - BX.mean(0)) / (BX.std(0) + 1e-9); Vt = np.linalg.svd(Zs, full_matrices=False)[2]
def pca(tr, te, k=20, H="12", lam=30.0):
    R.X30 = Zs @ Vt[:k].T
    try: return current(tr, te, H, lam)
    finally: R.X30 = X30_ORIG
G = lambda **kw: [dict(zip(kw, v)) for v in itertools.product(*kw.values())]
METHODS = [
    ("Your model (ridge logistic + round lines)", current, dict(H="12", lam=30.0), G(H=["none", "12", "6"], lam=[10.0, 30.0, 100.0])),
    ("Plain ridge logistic", ridge, dict(H="12", lam=30.0, sw=1.0), G(H=["none", "12", "6"], lam=[3.0, 30.0, 300.0], sw=[1.0, 3.0])),
    ("LDA", lda, dict(shrink=0.2), G(shrink=[0.0, 0.2, 0.5, 0.8])),
    ("QDA", lambda tr, te, **k: lda(tr, te, quad=True, **k), dict(shrink=0.3), G(shrink=[0.3, 0.6, 0.9])),
    ("Linear SVM", svm, dict(C=0.01, H="12"), G(C=[0.001, 0.01, 0.1], H=["none", "12"], sw=[1.0, 3.0])),
    ("Decision tree", tree, dict(depth=4, H="12"), G(depth=[2, 3, 6], H=["12"])),
    ("Random forest", forest, dict(depth=6, mtry=6, H="12"), G(depth=[6], mtry=[3, 12], H=["12"])),
    ("Boosting", boost, dict(rounds=200, depth=2, H="12"), G(rounds=[100, 300], depth=[1, 3], H=["12"])),
    ("Neural net", mlp, dict(hidden=8, decay=0.03, H="12"), G(hidden=[4, 16], decay=[0.01, 0.1], H=["12"])),
    ("PCA (all 246 measures)", pca, dict(k=20, H="12", lam=30.0), G(k=[5, 20, 60], H=["none", "12"], lam=[30.0, 100.0])),
]
summary = []
for with_styles in (False, True):
  XX, EXTRA = (np.column_stack([X39, CLU]), np.column_stack([CS, CLU])) if with_styles else (X39, CS)
  print(f"\n===== {'WITH team styles' if with_styles else 'WITHOUT team styles'} =====")
  print(f"{'method':42} | {'default':>22} | {'best setting (optimistic)':>40} | {'honest (chosen on other years)':>22}")
  print(f"{'':42} | {'R64-E8':>7} {'R64-T':>6} {'LL':>6} | {'R64-E8':>6} {'R64-T':>6} {'LL':>6} {'setting':>20} | {'R64-E8':>6} {'R64-T':>6} {'LL':>6}")
  for name, fn, default, grid in METHODS:
    if default not in grid: grid = [default] + grid
    P = {}
    for st in grid: P[tuple(sorted(st.items()))] = loso(lambda tr, te, st=st: fn(tr, te, **st))
    keyd = tuple(sorted(default.items())); pd_ = P[keyd]
    bestk = max(P, key=lambda k: (RIGHT(P[k])[R64T].sum(), -LL(P[k], R64T))); pb = P[bestk]
    ph = np.zeros(N)
    for s in SEASONS:
        oth = (seas != s) & R64T; k = max(P, key=lambda k: (RIGHT(P[k])[oth].sum(), -LL(P[k], oth))); ph[seas == s] = P[k][seas == s]
    E8 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
    f = lambda p: (int(RIGHT(p)[E8].sum()), int(RIGHT(p)[R64T].sum()), LL(p, R64T))
    a, b, c = f(pd_), f(pb), f(ph)
    stxt = ",".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}" for k, v in bestk)
    print(f"{name:42} | {a[0]:7d} {a[1]:6d} {a[2]:6.4f} | {b[0]:6d} {b[1]:6d} {b[2]:6.4f} {stxt:>20} | {c[0]:6d} {c[1]:6d} {c[2]:6.4f}   ({time.time() - T0:.0f}s)", flush=True)
    summary.append((with_styles, name, a, b, c, stxt))
sim = R.B.simS; simr = np.where(np.abs(sim - 0.5) < 1e-4, 0.5, (sim > 0.5) == yb)
E8 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
print(f"\nreference: simulator R64-E8 {simr[E8].sum():.1f}, R64-title {simr[R64T].sum():.1f}; workbook model (F4/title 85% simulator) R64-title 756")
print("\nWITH vs WITHOUT styles, R64-title right (default / honest):")
for name in [m[0] for m in METHODS]:
    w0 = next(s for s in summary if not s[0] and s[1] == name); w1 = next(s for s in summary if s[0] and s[1] == name)
    print(f"   {name:42} default {w0[2][1]} -> {w1[2][1]} ({w1[2][1] - w0[2][1]:+d}) | honest {w0[4][1]} -> {w1[4][1]} ({w1[4][1] - w0[4][1]:+d}) | LL {w0[2][2]:.4f} -> {w1[2][2]:.4f}")
