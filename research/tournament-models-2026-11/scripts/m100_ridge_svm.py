# Ridge logistic (the 756) vs Linear SVM (757), both run exactly as m99 (as is, no styles). Game-by-game picks held out:
# the agree/split grid between them, each against the simulator, splits by round; and their input weights (base step fitted
# on every Round-of-64-to-title game, standardized inputs) side by side.
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
def job(args):
    name, s = args; fit = Q.TYPES[name]
    tr = np.where((Q.seas != s) & ~Q.FF)[0]; te = np.where((Q.seas == s) & ~Q.FF)[0]
    m_tr, m_te = Q.base(tr, te, fit); return name, te, Q.run(m_tr, tr, m_te, te, Q.EX)
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    NM = ["Ridge logistic (your model)", "Linear SVM"]; SC = {n: np.full(Q.N, np.nan) for n in NM}
    with ProcessPoolExecutor(8) as ex:
        for name, te, v in ex.map(job, [(n, s) for n in NM for s in Q.SEASONS]): SC[name][te] = v
    keep = ~Q.FF; yb = Q.yb; n = int(keep.sum())
    r = {k: ((SC[k] > 0) == yb)[keep] for k in NM}
    PK = np.abs(Q.B.simS - 0.5) < 1e-4; sim = np.where(PK, 0.5, (Q.B.simS > 0.5) == yb)[keep]
    out = {"n": n, "right": {k: int(v.sum()) for k, v in r.items()}}
    def grid(a, b, la, lb):
        g = {"both": int((a == 1) & (b == 1)).sum() if False else int(((a == 1) & (b == 1)).sum()), "none": int(((a == 0) & (b == 0)).sum()),
             la: int(((a == 1) & (b == 0)).sum()), lb: int(((a == 0) & (b == 1)).sum()), "half": int(((a == 0.5) | (b == 0.5)).sum())}
        print(la, "vs", lb, g); return g
    rr, sv = r[NM[0]].astype(float), r[NM[1]].astype(float)
    out["ridge_svm"] = grid(rr, sv, "ridge", "svm")
    out["svm_sim"] = grid(sv, sim, "svm", "sim")
    out["ridge_sim"] = grid(rr, sim, "ridge", "sim")
    same = ((SC[NM[0]] > 0) == (SC[NM[1]] > 0))[keep]; print("same pick", int(same.sum()), "of", n)
    RND = Q.RND[keep]; out["by_round"] = {}
    for rd in ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]:
        m = RND == rd; d = m & ~same
        out["by_round"][rd] = [int(m.sum()), int(d.sum()), int((rr[d] == 1).sum()), int((sv[d] == 1).sum())]
        print(rd, out["by_round"][rd])
    # input weights, base step on all games
    idx = np.where(keep)[0]
    def weights(fit_type):
        Z = Q.zstd(Q.X30, idx)(idx); f = fit_type(idx)
        # recover the linear weights by probing each standardized input (both base steps are linear in the inputs)
        base = f(idx); A = np.column_stack([Z, np.ones(len(idx))]); return np.linalg.lstsq(A, base, rcond=None)[0][:-1]
    names = [str(x) for x in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
    wr, ws = weights(Q.TYPES[NM[0]]), weights(Q.TYPES[NM[1]])
    wr_n, ws_n = wr / np.abs(wr).sum(), ws / np.abs(ws).sum()
    out["corr"] = float(np.corrcoef(wr, ws)[0, 1])
    order = np.argsort(-np.abs(wr_n))
    out["weights"] = [[names[j], round(float(wr_n[j]) * 100, 1), round(float(ws_n[j]) * 100, 1)] for j in order[:10]]
    out["top_rank_overlap"] = len(set(np.argsort(-np.abs(wr))[:10]) & set(np.argsort(-np.abs(ws))[:10]))
    print("corr", out["corr"], "top10 overlap", out["top_rank_overlap"]); print(out["weights"])
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m100_out.json"), "w"), indent=1)
