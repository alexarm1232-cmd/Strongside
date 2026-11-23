# The course's methods on the model's data, NumPy only (no sklearn here). Same inputs for every method: the 30 measures,
# who plays (6) and coach + star (3) = 39 columns, oriented stronger-rated (S) vs weaker (W); y = S won. Each tournament held
# out (trained on the other 15, First Four rows left out of training), scored on the Round of 64 to Elite Eight (959 games):
# games right and log-loss. Settings are fixed up front, not tuned on these results.
#   A) forward in time: train only on EARLIER tournaments, 2017-18 on (Ch3 "final test fit")
#   B) PCA (ML11A): all 246 candidate measures squeezed to k components in place of the chosen 27 (+3 strength)
#   C) LDA, QDA (Ch4B), linear SVM (Ch9), decision tree, random forest, boosting (Ch8), a small neural net (ML10)
#   D) clustering (ML11B): k-means on team style (play-type mix + tempo); upsets by underdog style vs the model's expectation
import os, sys, contextlib, io, math, time
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
FF = RND == "First Four"; E4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
CS = R.EXTRA["coach+star"]; WT = R.weights(12)
X39 = np.column_stack([R.X30, M.F, CS]); N = len(y)
def score(nm, p, note=""):
    p = np.clip(p, 1e-6, 1 - 1e-6); right = int(((p > 0.5) == yb)[E4].sum())
    ll = float(-np.mean(np.where(yb, np.log(p), np.log(1 - p))[E4]))
    print(f"   {nm:44} right {right:4d} ({right / E4.sum():.1%})  log-loss {ll:.4f} {note}", flush=True); return right
def loso(fit_predict):
    p = np.zeros(N)
    for s in R.SEASONS:
        tr = np.where((seas != s) & ~FF)[0]; te = np.where(seas == s)[0]; p[te] = fit_predict(tr, te)
    return p
# ---- the current model (round lines), for reference
BASE = {s: (tr, te) + R.base_scores(tr, te, WT) for s in R.SEASONS for tr, te in [(np.where(seas != s)[0], np.where(seas == s)[0])]}
def current(extra=CS, x30=None):
    if x30 is not None: R.X30 = x30
    sc = np.zeros(N)
    for s in R.SEASONS:
        tr = np.where(seas != s)[0]; te = np.where(seas == s)[0]
        m_tr, m_te = R.base_scores(tr, te, WT) if x30 is not None else BASE[s][2:]
        sc[te] = R.model(m_tr, tr, m_te, te, WT, extra)
    return 1 / (1 + np.exp(-sc))
X30_ORIG = R.X30.copy()
print("REFERENCE")
base_right = score("current model (ridge logistic + round lines)", current())
def ridge_logit(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; Z = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(Z.shape[1])
    P = lam * np.eye(Z.shape[1]); P[-1, -1] = 0
    for _ in range(40):
        q = 1 / (1 + np.exp(-Z @ b)); H = Z.T @ (Z * (w * q * (1 - q))[:, None]) + P; b += np.linalg.solve(H, Z.T @ (w * (ytr - q)) - P @ b)
    return lambda X: 1 / (1 + np.exp(-(np.column_stack([(X - mu) / sd, np.ones(len(X))]) @ b)))
score("plain ridge logistic, all 39 columns at once", loso(lambda tr, te: ridge_logit(X39[tr], y[tr], WT[tr])(X39[te])))

# ---- A) forward in time
print("\nA) FORWARD IN TIME (train only on earlier tournaments), seasons 2017-18 to 2025-26")
later = [s for s in R.SEASONS if s >= "2017-18"]; LATE = np.isin(seas, later) & E4
pf = np.full(N, np.nan); pl = current()
for s in later:
    tr = np.where(seas < s)[0]; te = np.where(seas == s)[0]
    m_tr, m_te = R.base_scores(tr, te, WT); pf[te] = 1 / (1 + np.exp(-R.model(m_tr, tr, m_te, te, WT, CS)))
for nm, p in (("each tournament held out (as now)", pl), ("earlier tournaments only", pf)):
    r = int(((p > 0.5) == yb)[LATE].sum()); print(f"   {nm:44} right {r} of {int(LATE.sum())} ({r / LATE.sum():.1%})")
sim = R.B.simS; simr = np.where(np.abs(sim - 0.5) < 1e-4, 0.5, (sim > 0.5) == yb)
print(f"   {'simulator, same games':44} right {simr[LATE].sum():.1f} of {int(LATE.sum())}")

# ---- B) PCA
print("\nB) PCA: all 246 candidate measures -> k components (in place of the chosen 30), round lines + coach/star kept")
BX = R.B.X; Zs = (BX - BX.mean(0)) / (BX.std(0) + 1e-9); U, S_, Vt = np.linalg.svd(Zs, full_matrices=False)
pve = S_ ** 2 / (S_ ** 2).sum()
for k in (5, 10, 20, 40):
    pcs = Zs @ Vt[:k].T
    score(f"{k} components ({pve[:k].sum():.0%} of the variation)", current(x30=pcs))
    R.X30 = X30_ORIG
pcs = np.column_stack([X30_ORIG[:, :3], (Zs @ Vt[:20].T)])
score("3 strength + 20 components", current(x30=pcs)); R.X30 = X30_ORIG

# ---- C) other classifiers on the 39 columns
print("\nC) OTHER CLASSIFIERS (39 columns, each tournament held out)")
def standardize(tr, te, X=X39):
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9; return (X[tr] - mu) / sd, (X[te] - mu) / sd
def lda(tr, te, quad=False, shrink=0.2):
    A, B = standardize(tr, te); yy = y[tr]; out = []
    mus = [A[yy == c].mean(0) for c in (0, 1)]; pri = [np.mean(yy == c) for c in (0, 1)]
    pooled = np.cov(A.T); covs = [np.cov(A[yy == c].T) for c in (0, 1)] if quad else [pooled, pooled]
    covs = [(1 - shrink) * C + shrink * np.eye(len(C)) * np.trace(C) / len(C) for C in covs]
    ll = []
    for c in (0, 1):
        Ci = np.linalg.inv(covs[c]); d = B - mus[c]; _, logdet = np.linalg.slogdet(covs[c])
        ll.append(-0.5 * np.einsum("ij,jk,ik->i", d, Ci, d) - 0.5 * logdet + math.log(pri[c]))
    return 1 / (1 + np.exp(ll[0] - ll[1]))
score("LDA", loso(lda)); score("QDA (shrunk covariances)", loso(lambda tr, te: lda(tr, te, True, 0.3)))
def svm(tr, te, C=0.01, it=600):
    A, B = standardize(tr, te); s = 2 * y[tr] - 1; w = np.zeros(A.shape[1]); b = 0.0; n = len(A)
    for t in range(1, it + 1):
        mg = s * (A @ w + b); act = mg < 1; lr = 0.5 / math.sqrt(t)
        w -= lr * (C * w - (s[act, None] * A[act]).sum(0) / n); b -= lr * (-(s[act]).sum() / n)
    f = B @ w + b; fa = A @ w + b                               # Platt-style scaling of the margin to a chance, fit on training
    a = 1.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-a * fa)); a += np.sum((y[tr] - q) * fa) / (np.sum(q * (1 - q) * fa * fa) + 1e-9)
    return 1 / (1 + np.exp(-a * f))
score("linear SVM", loso(svm))
# trees
QS = np.linspace(0.05, 0.95, 15)
def build(X, g, h, depth, minleaf, feats_per_split, rng, lam=1.0):
    """regression tree on gradients g / hessians h (Newton leaves); returns a predict function"""
    nodes = []
    def grow(idx, d):
        G, H = g[idx].sum(), h[idx].sum(); leaf = -G / (H + lam)
        if d == 0 or len(idx) < 2 * minleaf: nodes.append(("leaf", leaf)); return len(nodes) - 1
        fs = rng.choice(X.shape[1], feats_per_split, replace=False) if feats_per_split < X.shape[1] else range(X.shape[1])
        best = None; base = G * G / (H + lam)
        for f in fs:
            col = X[idx, f]
            for thr in np.unique(np.quantile(col, QS)):
                L = col <= thr; nl = L.sum()
                if nl < minleaf or len(idx) - nl < minleaf: continue
                GL, HL = g[idx][L].sum(), h[idx][L].sum(); gain = GL * GL / (HL + lam) + (G - GL) ** 2 / (H - HL + lam) - base
                if best is None or gain > best[0]: best = (gain, f, thr)
        if best is None or best[0] <= 0: nodes.append(("leaf", leaf)); return len(nodes) - 1
        _, f, thr = best; me = len(nodes); nodes.append(None)
        L = idx[X[idx, f] <= thr]; Rr = idx[X[idx, f] > thr]
        nodes[me] = ("split", f, thr, grow(L, d - 1), grow(Rr, d - 1)); return me
    grow(np.arange(len(X)), depth)
    def pred(Z):
        out = np.zeros(len(Z))
        for i, z in enumerate(Z):
            k = 0
            while nodes[k][0] == "split": _, f, thr, a, b = nodes[k]; k = a if z[f] <= thr else b
            out[i] = nodes[k][1]
        return out
    return pred
def tree1(tr, te):
    A, B = X39[tr], X39[te]; p0 = y[tr].mean(); f0 = math.log(p0 / (1 - p0))
    g = (p0 - y[tr]) * WT[tr]; h = p0 * (1 - p0) * WT[tr]
    return 1 / (1 + np.exp(-(f0 + build(A, g, h, 4, 25, 39, np.random.default_rng(1))(B))))
score("one decision tree (depth 4)", loso(tree1))
def forest(tr, te, ntree=150):
    rng = np.random.default_rng(7); A, B = X39[tr], X39[te]; out = np.zeros(len(te))
    for _ in range(ntree):
        bs = rng.choice(len(tr), len(tr), replace=True, p=WT[tr] / WT[tr].sum()); yy = y[tr][bs]
        p0 = yy.mean(); g = p0 - yy; h = np.ones(len(bs))        # leaf = mean(y) - p0, so p0 + leaf = the leaf's win share
        out += np.clip(p0 + build(A[bs], g, h, 6, 10, 6, rng, lam=0.0)(B), 0.001, 0.999)
    return out / ntree
score("random forest (150 trees, 6 of 39 columns per split)", loso(forest))
def boost(tr, te, rounds=200, lr=0.05, depth=2):
    rng = np.random.default_rng(3); A, B = X39[tr], X39[te]; p0 = y[tr].mean(); fa = np.full(len(tr), math.log(p0 / (1 - p0))); fb = np.full(len(te), fa[0])
    for _ in range(rounds):
        sub = rng.random(len(tr)) < 0.7; q = 1 / (1 + np.exp(-fa)); g = (q - y[tr]) * WT[tr]; h = q * (1 - q) * WT[tr]
        pr = build(A[sub], g[sub], h[sub], depth, 20, 39, rng, lam=5.0); fa += lr * pr(A); fb += lr * pr(B)
    return 1 / (1 + np.exp(-fb))
score("boosting (200 small trees)", loso(boost))
def mlp(tr, te, hidden=8, epochs=400, decay=3e-2, seeds=5):
    A, B = standardize(tr, te); yy = y[tr]; out = np.zeros(len(te))
    for sd in range(seeds):
        rng = np.random.default_rng(sd); W1 = rng.normal(0, 0.3, (A.shape[1], hidden)); b1 = np.zeros(hidden); w2 = rng.normal(0, 0.3, hidden); b2 = 0.0
        m = [np.zeros_like(W1), np.zeros(hidden), np.zeros(hidden), 0.0]; v = [np.zeros_like(W1), np.zeros(hidden), np.zeros(hidden), 0.0]
        for ep in range(1, epochs + 1):
            Hh = np.tanh(A @ W1 + b1); q = 1 / (1 + np.exp(-(Hh @ w2 + b2))); e = (q - yy) / len(A)
            gw2 = Hh.T @ e + decay * w2; gb2 = e.sum(); dH = np.outer(e, w2) * (1 - Hh ** 2); gW1 = A.T @ dH + decay * W1; gb1 = dH.sum(0)
            for k, (gr) in enumerate((gW1, gb1, gw2, gb2)):
                m[k] = 0.9 * m[k] + 0.1 * gr; v[k] = 0.999 * v[k] + 0.001 * gr * gr
                step = 0.01 * (m[k] / (1 - 0.9 ** ep)) / (np.sqrt(v[k] / (1 - 0.999 ** ep)) + 1e-8)
                if k == 0: W1 -= step
                elif k == 1: b1 -= step
                elif k == 2: w2 -= step
                else: b2 -= step
        out += 1 / (1 + np.exp(-(np.tanh(B @ W1 + b1) @ w2 + b2)))
    return out / seeds
score("neural net (8 hidden units, 5 seeds averaged)", loso(mlp))

# ---- D) clustering team styles
print("\nD) CLUSTERING TEAM STYLES (k-means, 6 styles, on play-type mix + tempo + 3-point rate)")
SK = [k for k in TEAMK if k.startswith("pt_share")] + ["tempo", "r3"]
keys = [(s, t) for s in TM for t in TM[s] if all(TM[s][t].get(k) is not None for k in SK)]
V = np.array([[TM[s][t][k] for k in SK] for s, t in keys], float); Vz = (V - V.mean(0)) / (V.std(0) + 1e-9)
best = None
for seed in range(10):
    rng = np.random.default_rng(seed); C = Vz[rng.choice(len(Vz), 6, replace=False)]
    for _ in range(100):
        lab = np.argmin(((Vz[:, None, :] - C[None]) ** 2).sum(2), 1); C = np.array([Vz[lab == c].mean(0) for c in range(6)])
    wss = ((Vz - C[lab]) ** 2).sum()
    if best is None or wss < best[0]: best = (wss, lab, C)
_, lab, C = best
names = []
for c in range(6):
    o = np.argsort(-C[c]); nm = " + ".join(SK[j].replace("pt_share ", "") for j in o[:2]); names.append(nm);
STY = {k: l for k, l in zip(keys, lab)}
print(f"   {len(keys)} team-seasons, {len(SK)} style numbers; styles named by their two most above-average numbers:")
for c in range(6): print(f"     style {c}: {names[c]}  ({int((lab == c).sum())} team-seasons)")
import re
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
CL = {(s, clean(t)): l for (s, t), l in STY.items()}
D3 = np.load("m3_data.npz", allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
BG = R.B.G; S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
dogS = sS > sW; up = np.where(dogS, yb, ~yb).astype(float)
pm = current(); pdog = np.where(dogS, pm, 1 - pm)
DOG = np.where(dogS, S_name, W_name); FAV = np.where(dogS, W_name, S_name)
dc = np.array([CL.get((seas[i], clean(DOG[i])), -1) for i in range(N)]); fc = np.array([CL.get((seas[i], clean(FAV[i])), -1) for i in range(N)])
ok = E4 & (sS != sW) & (dc >= 0) & (fc >= 0)
print(f"   tournament games R64-E8, different seeds, both styles known: {int(ok.sum())}")
print(f"   {'underdog style':38} {'games':>5} {'upsets':>7} {'model expected':>15} {'diff':>6} {'z':>5}")
for c in range(6):
    m = ok & (dc == c); e = pdog[m].sum(); var = (pdog[m] * (1 - pdog[m])).sum()
    print(f"   {names[c]:38} {int(m.sum()):5d} {int(up[m].sum()):7d} {e:15.1f} {up[m].sum() - e:+6.1f} {(up[m].sum() - e) / math.sqrt(var):+5.1f}")
print(f"   {'favorite style':38}")
for c in range(6):
    m = ok & (fc == c); e = pdog[m].sum(); var = (pdog[m] * (1 - pdog[m])).sum()
    print(f"   {names[c]:38} {int(m.sum()):5d} {int(up[m].sum()):7d} {e:15.1f} {up[m].sum() - e:+6.1f} {(up[m].sum() - e) / math.sqrt(var):+5.1f}")
print(f"\n({time.time() - T0:.0f}s)")
