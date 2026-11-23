# Andrew Fridline's method (CART + random forest, Gini, variable importance by mean decrease in Gini) on OUR data and OUR
# model's inputs: the 30 model inputs (rating gap, schedule gap, gap x pace + the 27 picked measures), who plays (6) and
# coach + star (3) = 39. Response = the stronger-rated team won (the model's own response). First Four out.
#   CART: Gini splits, grown to min leaf 5, then cost-complexity pruned on misclassification (as rpart), the pruning level
#         chosen by 10-fold CV on the training data (minimum CV error).
#   RF:   500 trees, bootstrap, mtry = floor(sqrt(39)) = 6, grown out (node size 1), Gini; out-of-bag (OOB) predictions;
#         importance = mean decrease in Gini (sum of weighted impurity drops per variable / number of trees).
# Tested (a) Andrew's way: test years 2010, 2016, 2026 (2010 in place of his 2008: our data starts 2010), train on the rest;
# and (b) our way: each tournament held out. Scopes: Round of 64 (as Andrew) and Round of 64 to title.
# Our model's held-out picks (the 756) are scored on exactly the same games for comparison.
import os, sys, json, math, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"; os.environ.setdefault("OMP_NUM_THREADS", "1")
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import m18_rebuild as R
    import m10_model2 as M
NAMES30 = [str(n) for n in np.load("m3_data.npz", allow_pickle=True)["names"]]
WHO = ["S missing rotation value", "W missing rotation value", "S star out", "W star out", "Lineup quality gap (who played)", "Missing value gap"]
EXN = ["Coach NCAA appearances gap", "Coach recent Sweet 16s gap", "Star usage gap"]
FEAT = NAMES30 + WHO + EXN
X = np.column_stack([R.X30, M.F, R.EXTRA["coach+star"]]); y = R.yb.astype(int); seas = R.seas; RND = R.RND
FF = RND == "First Four"; R64 = RND == "First round"
v756 = np.load("m56_scores.npz")["fixed 27 (picked from all games)"]           # our model, held out by tournament
# ---------------- trees
def gini(p): return 2 * p * (1 - p)
def grow(Xs, ys, idx, minleaf, mtry, rng, imp, depth=0):
    """returns nested dict; imp accumulates n-weighted Gini decrease per feature"""
    n = len(idx); k = ys[idx].sum(); node = {"n": n, "k": int(k), "p": k / n}
    if n < 2 * minleaf or k == 0 or k == n: return node
    feats = rng.choice(Xs.shape[1], mtry, replace=False) if mtry < Xs.shape[1] else range(Xs.shape[1])
    best = None; g0 = n * gini(k / n)
    for f in feats:
        col = Xs[idx, f]; o = np.argsort(col, kind="mergesort"); cs = col[o]; yc = np.cumsum(ys[idx][o])
        nl = np.arange(1, n); ok = (cs[1:] > cs[:-1]) & (nl >= minleaf) & (n - nl >= minleaf)
        if not ok.any(): continue
        kl = yc[:-1]; kr = k - kl; nr = n - nl
        score = nl * gini(kl / nl) + nr * gini(kr / nr); score[~ok] = np.inf
        j = int(np.argmin(score))
        if best is None or score[j] < best[0]: best = (score[j], f, (cs[j] + cs[j + 1]) / 2)
    if best is None or best[0] >= g0 - 1e-12: return node
    s, f, thr = best; imp[f] += g0 - s
    L = idx[Xs[idx, f] <= thr]; Rr = idx[Xs[idx, f] > thr]
    node.update(f=int(f), thr=float(thr), L=grow(Xs, ys, L, minleaf, mtry, rng, imp, depth + 1), R=grow(Xs, ys, Rr, minleaf, mtry, rng, imp, depth + 1))
    return node
def predict(node, x):
    while "f" in node: node = node["L"] if x[node["f"]] <= node["thr"] else node["R"]
    return node["p"]
def err(node): return min(node["k"], node["n"] - node["k"])          # misclassified if this node were a leaf
def leaves(node): return [node] if "f" not in node else leaves(node["L"]) + leaves(node["R"])
def prune_seq(tree):
    """weakest-link pruning: list of (alpha, pruned tree copy) from full tree to root"""
    import copy
    t = copy.deepcopy(tree); seq = [(0.0, copy.deepcopy(t))]
    while "f" in t:
        best = None; stack = [t]
        while stack:
            nd = stack.pop()
            if "f" not in nd: continue
            lv = leaves(nd); g = (err(nd) - sum(err(l) for l in lv)) / (len(lv) - 1)
            if best is None or g < best[0]: best = (g, nd)
            stack += [nd["L"], nd["R"]]
        g, nd = best
        for key in ("f", "thr", "L", "R"): nd.pop(key)
        seq.append((max(g, seq[-1][0]), copy.deepcopy(t)))
    return seq
def prune_at(tree, alpha):
    seq = prune_seq(tree); best = seq[0][1]
    for a, t in seq:
        if a <= alpha: best = t
    return best
def cart(tr, seed=0):
    rng = np.random.default_rng(seed); imp = np.zeros(X.shape[1])
    full = grow(X, y, tr, 5, X.shape[1], rng, imp)
    seq = prune_seq(full); alphas = [a for a, _ in seq]
    cands = [math.sqrt(alphas[i] * alphas[i + 1]) if alphas[i] > 0 else alphas[i + 1] / 2 for i in range(len(alphas) - 1)] + [alphas[-1] + 1]
    folds = np.random.default_rng(seed).permutation(len(tr)) % 10; cv = np.zeros(len(cands))
    for f in range(10):
        a, b = tr[folds != f], tr[folds == f]; ft = grow(X, y, a, 5, X.shape[1], rng, np.zeros(X.shape[1]))
        for c, al in enumerate(cands):
            pt = prune_at(ft, al); cv[c] += sum((predict(pt, X[i]) > 0.5) != y[i] for i in b)
    alpha = cands[int(np.argmin(cv))]; tree = prune_at(full, alpha)
    return tree
def forest(tr, ntree=500, seed=7):
    rng = np.random.default_rng(seed); imp = np.zeros(X.shape[1]); trees = []; oob_sum = np.zeros(len(y)); oob_n = np.zeros(len(y))
    mtry = int(math.sqrt(X.shape[1]))
    for _ in range(ntree):
        bs = tr[rng.integers(0, len(tr), len(tr))]; t = grow(X, y, bs, 1, mtry, rng, imp); trees.append(t)
        out = np.setdiff1d(tr, bs)
        for i in out: oob_sum[i] += predict(t, X[i]); oob_n[i] += 1
    return trees, imp / ntree, np.where(oob_n > 0, oob_sum / np.maximum(oob_n, 1), np.nan)
def rf_predict(trees, idx): return np.array([np.mean([predict(t, X[i]) for t in trees]) for i in idx])
def auc(s, yy):
    s = np.asarray(s, float); yy = np.asarray(yy); o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)       # average ranks for ties
    sums = np.bincount(inv, r); r = (sums / cnt)[inv]; n1 = yy.sum(); n0 = len(yy) - n1
    return float((r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
SCOPES = {"Round of 64": R64 & ~FF, "Round of 64 to title": ~FF}
def loso_job(args):
    scope, s = args; m = SCOPES[scope]
    tr = np.where(m & (seas != s))[0]; te = np.where(m & (seas == s))[0]
    t = cart(tr); trees, _, _ = forest(tr)
    return scope, te.tolist(), [predict(t, X[i]) for i in te], rf_predict(trees, te).tolist()
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    import time; T0 = time.time(); out = {"features": FEAT}
    # (a) Andrew's split, plus full fits for the tree picture and the importance chart
    TEST = ["2009-10", "2015-16", "2025-26"]
    for scope, m in SCOPES.items():
        tr = np.where(m & ~np.isin(seas, TEST))[0]; te = np.where(m & np.isin(seas, TEST))[0]
        t = cart(tr); trees, imp, oob = forest(tr)
        pc_tr = [predict(t, X[i]) for i in tr]; pc_te = [predict(t, X[i]) for i in te]; prf = rf_predict(trees, te)
        res = dict(n_train=len(tr), n_test=len(te),
                   cart_train_auc=auc(pc_tr, y[tr]), cart_test_auc=auc(pc_te, y[te]), rf_oob_auc=auc(oob[tr], y[tr]), rf_test_auc=auc(prf, y[te]),
                   model_test_auc=auc(v756[te], y[te]),
                   cart_test_right=int(sum((np.array(pc_te) > 0.5) == y[te])), rf_test_right=int(sum((prf > 0.5) == y[te])),
                   model_test_right=int(sum((v756[te] > 0) == y[te])), cart_leaves=len(leaves(t)))
        out[f"split|{scope}"] = res; print(scope, "Andrew split:", res, f"({time.time() - T0:.0f}s)", flush=True)
        # full-data fits: the tree to draw and the importance chart
        allm = np.where(m)[0]; tfull = cart(allm); trees_f, imp_f, oob_f = forest(allm)
        out[f"tree|{scope}"] = tfull; out[f"importance|{scope}"] = imp_f.tolist(); out[f"oob_auc_all|{scope}"] = auc(oob_f[allm], y[allm])
        print(" full fit: leaves", len(leaves(tfull)), "OOB AUC", round(out[f'oob_auc_all|{scope}'], 4), f"({time.time() - T0:.0f}s)", flush=True)
    # (b) each tournament held out
    jobs = [(sc, s) for sc in SCOPES for s in R.SEASONS]; P = {sc: {"cart": np.full(len(y), np.nan), "rf": np.full(len(y), np.nan)} for sc in SCOPES}
    with ProcessPoolExecutor(8) as ex:
        for scope, te, pc, pr in ex.map(loso_job, jobs): P[scope]["cart"][te] = pc; P[scope]["rf"][te] = pr
    for scope, m in SCOPES.items():
        idx = np.where(m)[0]; r = {}
        for k in ("cart", "rf"): r[k] = dict(right=int(((P[scope][k][idx] > 0.5) == y[idx]).sum()), auc=auc(P[scope][k][idx], y[idx]))
        r["model"] = dict(right=int(((v756[idx] > 0) == y[idx]).sum()), auc=auc(v756[idx], y[idx])); r["n"] = len(idx)
        out[f"loso|{scope}"] = r; print(scope, "held out by tournament:", r, flush=True)
    json.dump(out, open(os.path.join(HERE, "m110_out.json"), "w")); print(f"done ({time.time() - T0:.0f}s)")
