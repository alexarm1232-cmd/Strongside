# Does giving the tree more inputs (more things to split on) help? Same trees as m114, but on all 246 candidate measures
# plus who plays (6) and coach + star (3) = 255 inputs instead of the model's 39. Every game, each tournament held out.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
XBIG = np.column_stack([C.R.B.X, C.M.F, C.R.EXTRA["coach+star"]])
def job(args):
    kind, s = args; C.X = XBIG; m = ~C.FF
    tr = np.where(m & (C.seas != s))[0]; te = np.where(m & (C.seas == s))[0]
    t = C.grow(C.X, C.y, tr, 1 if kind == "full1" else 5, C.X.shape[1], np.random.default_rng(0), np.zeros(C.X.shape[1]))
    if kind == "cp": t = C.prune_at(t, 0.01 * C.err(t))
    return kind, te.tolist(), [C.predict(t, C.X[i]) for i in te], len(C.leaves(t))
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    KINDS = ["full1", "full5", "cp"]; P = {k: np.full(len(C.y), np.nan) for k in KINDS}; LV = {k: [] for k in KINDS}
    with ProcessPoolExecutor(8) as ex:
        for kind, te, p, nl in ex.map(job, [(k, s) for k in KINDS for s in C.R.SEASONS]): P[kind][te] = p; LV[kind].append(nl)
    idx = np.where(~C.FF)[0]; y = C.y
    old = {"full1": 673, "full5": 688, "cp": 705}
    print(f"inputs: {XBIG.shape[1]}")
    for k, nm in (("full1", "Full tree, leaves to 1 game"), ("full5", "Full tree, 5+ games a leaf"), ("cp", "Pruned tree (cp 0.01)")):
        r = int(((P[k][idx] > 0.5) == y[idx]).sum())
        print(f"{nm:30} 255 inputs: {r} (AUC {C.auc(P[k][idx], y[idx]):.3f}, ~{np.mean(LV[k]):.0f} leaves) | 39 inputs: {old[k]} | change {r - old[k]:+d}")
