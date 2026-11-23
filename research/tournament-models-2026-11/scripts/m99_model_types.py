# The 756 model with only its MODEL TYPE swapped. Everything else is exactly as m56 ran it: the same 30 inputs (3 strength +
# the 27 picked), recency half-life 12, the base score held out by tournament inside training, the three round lines
# (Rounds 1-2: base + who plays + coach/star; Sweet 16/Elite 8: base + coach/star; Final Four/title: 15% its line + 85%
# simulator), First Four out, each tournament held out. Each model type learns its own weights on the inputs.
# Settings are fixed up front (no tuning on these results), so the only overfitting is in the fit itself, measured as
# in-sample (trained on all the games it is scored on) vs held out, like 775 vs 756.
# Each type is run twice: as is, and with team styles (6 k-means clusters on play-type mix, tempo and 3-point rate; the
# stronger and weaker team's style as on/off columns) added to the round lines beside coach + star.
import os, sys, contextlib, io, math, re
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"; os.environ.setdefault("OMP_NUM_THREADS", "1")
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
_here = __file__
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM, TEAMK
    import m18_rebuild as R
    import m10_model2 as M
__file__ = _here
B = R.B; N, seas, yb, y_, SEASONS, RND = R.N, R.seas, R.yb, R.y.astype(float), R.SEASONS, R.RND
FF = RND == "First Four"; EX = R.EXTRA["coach+star"]; WT = R.weights(12); E12 = B.EARLY
S16, E8 = RND == "Sweet 16", RND == "Elite Eight"; F4T = np.isin(RND, ["Final Four", "Championship"])
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
SIM = lg(B.simS); X30 = R.X30.copy()
# ---- team styles
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
Wn = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(B.G, B.Sname)])
CLU = np.zeros((N, 10))
for i in range(N):
    a, b = STY.get((seas[i], clean(B.Sname[i]))), STY.get((seas[i], clean(Wn[i])))
    if a is not None and a > 0: CLU[i, a - 1] = 1
    if b is not None and b > 0: CLU[i, 5 + b - 1] = 1
EXTRAS = {"as is": EX, "with styles": np.column_stack([EX, CLU])}
# ---- the round lines, exactly as m56 run()
VER = [(E12, "m who ex"), (S16 | E8, "m ex"), (F4T, "blend")]
def run(m_tr, tr, m_te, te, ex):
    cols = lambda spec, m, idx: np.column_stack([{"m": m[:, None], "who": M.F[idx], "ex": ex[idx]}[c] for c in spec.split()])
    out = np.zeros(len(te))
    for grp, spec in VER:
        b = grp[te]; a = grp[tr]
        if not b.any(): continue
        if spec == "blend":
            f = R.wlr(cols("m ex", m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = 0.15 * f(cols("m ex", m_te[b], te[b])) + 0.85 * SIM[te][b]
        else:
            f = R.wlr(cols(spec, m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = f(cols(spec, m_te[b], te[b]))
    return out
# ---- model types: fit(idx) -> function giving log-odds that S wins, for rows
def zstd(X, idx): mu, sd = X[idx].mean(0), X[idx].std(0) + 1e-9; return lambda r: (X[r] - mu) / sd
def t_ridge(X=X30, lam=30.0):
    def fit(idx):
        Z = zstd(X, idx); A = np.column_stack([Z(idx), np.ones(len(idx))]); w = WT[idx]; b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
        for _ in range(40):
            q = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (w * q * (1 - q))[:, None]) + P; b += np.linalg.solve(H, A.T @ (w * (y_[idx] - q)) - P @ b)
        return lambda r: np.column_stack([Z(r), np.ones(len(r))]) @ b
    return fit
def t_lda(quad=False, shrink=0.2):
    def fit(idx):
        Z = zstd(X30, idx); A = Z(idx); yy = y_[idx]; mus = [A[yy == c].mean(0) for c in (0, 1)]; pri = [np.mean(yy == c) for c in (0, 1)]
        pooled = np.cov(A.T); covs = [np.cov(A[yy == c].T) for c in (0, 1)] if quad else [pooled, pooled]
        covs = [(1 - shrink) * C + shrink * np.eye(len(C)) * np.trace(C) / len(C) for C in covs]; inv = [np.linalg.inv(C) for C in covs]
        ld = [np.linalg.slogdet(C)[1] for C in covs]
        def pred(r):
            Bm = Z(r); ll = [-0.5 * np.einsum("ij,jk,ik->i", Bm - mus[c], inv[c], Bm - mus[c]) - 0.5 * ld[c] + math.log(pri[c]) for c in (0, 1)]
            return np.clip(ll[1] - ll[0], -15, 15)
        return pred
    return fit
def t_svm(C=0.01, it=600):
    def fit(idx):
        Z = zstd(X30, idx); A = Z(idx); s = 2 * y_[idx] - 1; w0 = WT[idx] / WT[idx].mean(); w = np.zeros(A.shape[1]); b = 0.0; n = len(A)
        for t in range(1, it + 1):
            act = s * (A @ w + b) < 1; lr = 0.5 / math.sqrt(t)
            w -= lr * (C * w - ((w0 * s)[act, None] * A[act]).sum(0) / n); b -= lr * (-(w0 * s)[act].sum() / n)
        fa = A @ w + b; a = 1.0
        for _ in range(50):
            q = 1 / (1 + np.exp(-a * fa)); a += np.sum((y_[idx] - q) * fa) / (np.sum(q * (1 - q) * fa * fa) + 1e-9)
        return lambda r: a * (Z(r) @ w + b)
    return fit
QS = np.linspace(0.05, 0.95, 15)
def build(X, g, h, depth, minleaf, fps, rng, lam=1.0):
    nodes = []
    def grow(ix, d):
        G, Hh = g[ix].sum(), h[ix].sum(); leaf = -G / (Hh + lam)
        if d == 0 or len(ix) < 2 * minleaf: nodes.append(("leaf", leaf)); return len(nodes) - 1
        fs = rng.choice(X.shape[1], fps, replace=False) if fps < X.shape[1] else range(X.shape[1]); bst = None; base = G * G / (Hh + lam)
        for f in fs:
            col = X[ix, f]
            for thr in np.unique(np.quantile(col, QS)):
                L = col <= thr; nl = L.sum()
                if nl < minleaf or len(ix) - nl < minleaf: continue
                GL, HL = g[ix][L].sum(), h[ix][L].sum(); gain = GL * GL / (HL + lam) + (G - GL) ** 2 / (Hh - HL + lam) - base
                if bst is None or gain > bst[0]: bst = (gain, f, thr)
        if bst is None or bst[0] <= 0: nodes.append(("leaf", leaf)); return len(nodes) - 1
        _, f, thr = bst; me = len(nodes); nodes.append(None)
        nodes[me] = ("split", f, thr, grow(ix[X[ix, f] <= thr], d - 1), grow(ix[X[ix, f] > thr], d - 1)); return me
    grow(np.arange(len(X)), depth)
    def pred(Z):
        out = np.zeros(len(Z))
        for i, z in enumerate(Z):
            k = 0
            while nodes[k][0] == "split": _, f, thr, a, b = nodes[k]; k = a if z[f] <= thr else b
            out[i] = nodes[k][1]
        return out
    return pred
def t_tree(depth=3):
    def fit(idx):
        w = WT[idx]; p0 = np.average(y_[idx], weights=w); f0 = math.log(p0 / (1 - p0))
        pr = build(X30[idx], (p0 - y_[idx]) * w, p0 * (1 - p0) * w, depth, 25, 30, np.random.default_rng(1))
        return lambda r: f0 + pr(X30[r])
    return fit
def t_forest(depth=6, mtry=6, ntree=50):
    def fit(idx):
        rng = np.random.default_rng(7); w = WT[idx]; trees = []
        for _ in range(ntree):
            bs = idx[rng.choice(len(idx), len(idx), replace=True, p=w / w.sum())]; yy = y_[bs]; p0 = yy.mean()
            trees.append((p0, build(X30[bs], p0 - yy, np.ones(len(bs)), depth, 10, mtry, rng, lam=0.0)))
        return lambda r: lg(np.mean([np.clip(p0 + t(X30[r]), 0.001, 0.999) for p0, t in trees], 0))
    return fit
def t_boost(rounds=100, depth=2, lr=0.05):
    def fit(idx):
        rng = np.random.default_rng(3); w = WT[idx]; p0 = np.average(y_[idx], weights=w); f0 = math.log(p0 / (1 - p0)); fa = np.full(len(idx), f0); trees = []
        for _ in range(rounds):
            sub = rng.random(len(idx)) < 0.7; q = 1 / (1 + np.exp(-fa)); g = (q - y_[idx]) * w; h = q * (1 - q) * w
            t = build(X30[idx][sub], g[sub], h[sub], depth, 20, 30, rng, lam=5.0); fa += lr * t(X30[idx]); trees.append(t)
        return lambda r: f0 + lr * sum(t(X30[r]) for t in trees)
    return fit
def t_mlp(hidden=8, decay=0.03, epochs=400, seeds=3):
    def fit(idx):
        Z = zstd(X30, idx); A = Z(idx); yy = y_[idx]; wv = WT[idx] / WT[idx].mean(); nets = []
        for sd in range(seeds):
            rng = np.random.default_rng(sd); P = [rng.normal(0, 0.3, (A.shape[1], hidden)), np.zeros(hidden), rng.normal(0, 0.3, hidden), np.zeros(1)]
            m = [np.zeros_like(x) for x in P]; v = [np.zeros_like(x) for x in P]
            for ep in range(1, epochs + 1):
                Hh = np.tanh(A @ P[0] + P[1]); q = 1 / (1 + np.exp(-(Hh @ P[2] + P[3][0]))); e = wv * (q - yy) / len(A); dH = np.outer(e, P[2]) * (1 - Hh ** 2)
                grads = [A.T @ dH + decay * P[0], dH.sum(0), Hh.T @ e + decay * P[2], np.array([e.sum()])]
                for k in range(4):
                    m[k] = 0.9 * m[k] + 0.1 * grads[k]; v[k] = 0.999 * v[k] + 0.001 * grads[k] ** 2
                    P[k] = P[k] - 0.01 * (m[k] / (1 - 0.9 ** ep)) / (np.sqrt(v[k] / (1 - 0.999 ** ep)) + 1e-8)
            nets.append([x.copy() for x in P])
        return lambda r: lg(np.mean([1 / (1 + np.exp(-(np.tanh(Z(r) @ P[0] + P[1]) @ P[2] + P[3][0]))) for P in nets], 0))
    return fit
BX = B.X; ZB = (BX - BX.mean(0)) / (BX.std(0) + 1e-9); PC20 = ZB @ np.linalg.svd(ZB, full_matrices=False)[2][:20].T
TYPES = {
    "Ridge logistic (your model)": t_ridge(),
    "LDA": t_lda(), "QDA": t_lda(quad=True, shrink=0.6), "Linear SVM": t_svm(),
    "Decision tree": t_tree(), "Random forest": t_forest(), "Boosting": t_boost(), "Neural net": t_mlp(),
    "PCA 20 components (all 246 measures)": t_ridge(X=PC20),
}
def base(tr, te, fit):
    """held-out base log-odds for the training rows (each tournament from a fit without it), and the test rows from all of tr"""
    out = np.zeros(len(tr)); s_ = seas[tr]
    for t in sorted(set(s_)):
        a = tr[s_ != t]; out[s_ == t] = fit(a)(tr[s_ == t])
    return out, fit(tr)(te)
def job(args):
    name, s = args; fit = TYPES[name]
    if s == "IN-SAMPLE":
        tr = np.where(~FF)[0]; m_tr, m_te = base(tr, tr, fit)
        return name, s, {k: run(m_tr, tr, m_te, tr, ex) for k, ex in EXTRAS.items()}, tr
    tr = np.where((seas != s) & ~FF)[0]; te = np.where((seas == s) & ~FF)[0]
    m_tr, m_te = base(tr, te, fit)
    return name, s, {k: run(m_tr, tr, m_te, te, ex) for k, ex in EXTRAS.items()}, te
if __name__ == "__main__":
    import time
    from concurrent.futures import ProcessPoolExecutor
    T0 = time.time(); keep = ~FF; E4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
    jobs = [(n, s) for n in TYPES for s in list(SEASONS) + ["IN-SAMPLE"]]
    SC = {}
    with ProcessPoolExecutor(8) as ex:
        for name, s, res, rows in ex.map(job, jobs):
            for k, v in res.items():
                key = (name, k, "in" if s == "IN-SAMPLE" else "out"); SC.setdefault(key, np.full(N, np.nan))[rows] = v
    PK = np.abs(B.simS - 0.5) < 1e-4; sim_r = np.where(PK, 0.5, (B.simS > 0.5) == yb).astype(float)
    print(f"Round of 64 to title: {int(keep.sum())} games (First Four out). Simulator {sim_r[keep].sum():.1f}.  ({time.time() - T0:.0f}s)")
    print(f"{'model type':38} {'styles':12} | {'held out':>8} {'R64-E8':>7} {'log-loss':>8} | {'in-sample':>9} {'overfit':>7}")
    for name in TYPES:
        for k in EXTRAS:
            o, i = SC[(name, k, "out")], SC[(name, k, "in")]
            ro = int(((o > 0) == yb)[keep].sum()); r4 = int(((o > 0) == yb)[E4].sum()); ri = int(((i > 0) == yb)[keep].sum())
            p = np.clip(1 / (1 + np.exp(-o)), 1e-6, 1 - 1e-6); ll = float(-np.mean(np.where(yb, np.log(p), np.log(1 - p))[keep]))
            print(f"{name:38} {k:12} | {ro:8d} {r4:7d} {ll:8.4f} | {ri:9d} {ri - ro:+7d}")
