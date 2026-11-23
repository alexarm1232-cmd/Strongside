# 5-fold cross-validation, average validation AUC, for every model type (m99's pipeline: same inputs, round lines,
# half-life 12, 85% simulator in the Final Four/title, First Four out; only the model type differs).
# Folds are whole tournaments (16 tournaments -> 5 groups of 3-4), so no tournament is split between training and validation.
# Repeated with 3 random fold splits. AUC = chance the model ranks a random winner above a random loser (S wins vs not),
# on the validation fold's Round-of-64-to-title games; also accuracy.
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
def auc(score, y):
    o = np.argsort(score); r = np.empty(len(score)); r[o] = np.arange(1, len(score) + 1)
    # ties: average ranks
    s_sorted = score[o]; i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]: j += 1
        r[o[i:j + 1]] = (i + j + 2) / 2; i = j + 1
    n1 = y.sum(); n0 = len(y) - n1; return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
SPLITS = []
for rep in range(3):
    rng = np.random.default_rng(100 + rep); ss = list(Q.SEASONS); rng.shuffle(ss)
    SPLITS.append([ss[k::5] for k in range(5)])
def job(args):
    name, rep, k = args; val = SPLITS[rep][k]; fit = Q.TYPES[name]
    tr = np.where(~np.isin(Q.seas, val) & ~Q.FF)[0]; te = np.where(np.isin(Q.seas, val) & ~Q.FF)[0]
    m_tr, m_te = Q.base(tr, te, fit); sc = Q.run(m_tr, tr, m_te, te, Q.EX)
    yy = Q.yb[te].astype(int)
    return name, rep, k, float(auc(sc, yy)), int(((sc > 0) == Q.yb[te]).sum()), len(te)
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(n, r, k) for n in Q.TYPES for r in range(3) for k in range(5)]
    res = {}
    with ProcessPoolExecutor(8) as ex:
        for name, rep, k, a, right, n in ex.map(job, jobs): res.setdefault(name, []).append((rep, k, a, right, n))
    out = {}
    print(f"{'model type':38} {'mean AUC':>9} {'sd over folds':>13} {'min':>6} {'max':>6} | {'accuracy (avg of 3 splits)':>26}")
    for name in Q.TYPES:
        a = np.array([x[2] for x in res[name]]); right = np.mean([sum(x[3] for x in res[name] if x[0] == r) for r in range(3)])
        n = sum(x[4] for x in res[name] if x[0] == 0)
        out[name] = dict(auc=float(a.mean()), sd=float(a.std(ddof=1)), lo=float(a.min()), hi=float(a.max()), right=float(right), n=n,
                         per_split=[float(np.mean([x[2] for x in res[name] if x[0] == r])) for r in range(3)])
        print(f"{name:38} {a.mean():9.4f} {a.std(ddof=1):13.4f} {a.min():6.3f} {a.max():6.3f} | {right:8.1f} of {n} ({right / n:.1%})")
    # paired comparison of each type's fold AUCs with ridge (same folds)
    ridge = {(x[0], x[1]): x[2] for x in res["Ridge logistic (your model)"]}
    for name in Q.TYPES:
        d = np.array([x[2] - ridge[(x[0], x[1])] for x in res[name]]); out[name]["diff_vs_ridge"] = float(d.mean())
        out[name]["folds_better"] = int((d > 0).sum())
    json.dump(dict(splits=SPLITS, results=out), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m102_out.json"), "w"), indent=1)
    print({k: (round(v["diff_vs_ridge"], 4), v["folds_better"]) for k, v in out.items()})
