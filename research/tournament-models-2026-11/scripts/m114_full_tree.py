# The full (unpruned) CART tree on every game, Round of 64 to title (1,007), same 39 inputs and response as m110.
# Grown out two ways: leaves down to 1 game, and leaves of at least 5 games. Each tournament held out (trained on the
# other 15), plus in-sample (trained and scored on all games) to show the overfit. By round, against our model (the 756),
# the cp = 0.01 tree, and always picking the stronger-rated team.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
def full(tr, minleaf): return C.grow(C.X, C.y, tr, minleaf, C.X.shape[1], np.random.default_rng(0), np.zeros(C.X.shape[1]))
def cp(tr): t = full(tr, 5); return C.prune_at(t, 0.01 * C.err(t))
def job(args):
    kind, s = args; m = ~C.FF
    tr = np.where(m & (C.seas != s))[0]; te = np.where(m & (C.seas == s))[0]
    t = full(tr, 1) if kind == "full1" else full(tr, 5) if kind == "full5" else cp(tr)
    return kind, te.tolist(), [C.predict(t, C.X[i]) for i in te]
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    KINDS = ["full1", "full5", "cp"]; P = {k: np.full(len(C.y), np.nan) for k in KINDS}
    with ProcessPoolExecutor(8) as ex:
        for kind, te, p in ex.map(job, [(k, s) for k in KINDS for s in C.R.SEASONS]): P[kind][te] = p
    idx = np.where(~C.FF)[0]; y = C.y; rnd = C.RND
    ins = {k: full(idx, 1 if k == "full1" else 5) for k in ("full1", "full5")}
    lv = {k: len(C.leaves(t)) for k, t in ins.items()}
    insr = {k: int(sum((C.predict(t, C.X[i]) > 0.5) == y[i] for i in idx)) for k, t in ins.items()}
    model = (C.v756 > 0) == y; strong = np.ones(len(y), bool) & (y == 1)
    name = {"full1": f"Full tree, leaves down to 1 game ({lv['full1']} leaves)", "full5": f"Full tree, leaves of 5+ games ({lv['full5']} leaves)", "cp": "Pruned tree (cp 0.01)"}
    print(f"{'method':48} {'held out':>9} {'AUC':>6} {'in-sample':>10}")
    print(f"{'Our model':48} {int(model[idx].sum()):9d} {C.auc(C.v756[idx], y[idx]):6.3f}")
    for k in KINDS:
        print(f"{name[k]:48} {int(((P[k][idx] > 0.5) == y[idx]).sum()):9d} {C.auc(P[k][idx], y[idx]):6.3f} {insr.get(k, ''):>10}")
    print(f"{'Always the stronger-rated team':48} {int(strong[idx].sum()):9d}")
    print("\nby round (games right):")
    RO = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
    print(f"{'round':14} {'games':>5} {'model':>6} {'full1':>6} {'full5':>6} {'cp':>6} {'stronger':>9}")
    for r in RO:
        m = idx[rnd[idx] == r]
        print(f"{r:14} {len(m):5d} {int(model[m].sum()):6d} " + " ".join(f"{int(((P[k][m] > 0.5) == y[m]).sum()):6d}" for k in KINDS) + f" {int(strong[m].sum()):9d}")
    json.dump({k: P[k].tolist() for k in KINDS} | {"leaves": lv, "insample": insr}, open(os.path.join(C.HERE, "m114_out.json"), "w"))
