# CART at rpart's default complexity (cp = 0.01: a split is kept only if it cuts the misclassification risk by 1% of the
# root's), instead of m110's CV-chosen pruning (which pruned the Round-of-64 tree to the root). Held out by tournament and
# on Andrew's test years; the full-data tree for each scope printed; random-forest importance ranking from m110.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
def cart_cp(tr, cp=0.01):
    full = C.grow(C.X, C.y, tr, 5, C.X.shape[1], np.random.default_rng(0), np.zeros(C.X.shape[1]))
    return C.prune_at(full, cp * C.err(full))
def show(nd, depth=0, lines=None, side="root"):
    lines = [] if lines is None else lines
    lab = f"{side}: n={nd['n']} stronger team won {nd['k']} ({nd['p']:.1%})"
    if "f" in nd:
        lines.append("  " * depth + lab + f"  -> split on [{C.FEAT[nd['f']]}] at {nd['thr']:.3f}")
        show(nd["L"], depth + 1, lines, f"<= {nd['thr']:.3f}"); show(nd["R"], depth + 1, lines, f"> {nd['thr']:.3f}")
    else: lines.append("  " * depth + lab + "  [leaf]")
    return lines
def job(args):
    scope, s = args; m = C.SCOPES[scope]
    tr = np.where(m & (C.seas != s))[0]; te = np.where(m & (C.seas == s))[0]; t = cart_cp(tr)
    return scope, te.tolist(), [C.predict(t, C.X[i]) for i in te]
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    out = json.load(open(os.path.join(C.HERE, "m110_out.json")))
    TEST = ["2009-10", "2015-16", "2025-26"]
    P = {sc: np.full(len(C.y), np.nan) for sc in C.SCOPES}
    with ProcessPoolExecutor(8) as ex:
        for scope, te, pc in ex.map(job, [(sc, s) for sc in C.SCOPES for s in C.R.SEASONS]): P[scope][te] = pc
    for scope, m in C.SCOPES.items():
        idx = np.where(m)[0]
        out[f"loso|{scope}"]["cart_cp"] = dict(right=int(((P[scope][idx] > 0.5) == C.y[idx]).sum()), auc=C.auc(P[scope][idx], C.y[idx]))
        tr = np.where(m & ~np.isin(C.seas, TEST))[0]; te = np.where(m & np.isin(C.seas, TEST))[0]; t = cart_cp(tr)
        out[f"split|{scope}"].update(cartcp_train_auc=C.auc([C.predict(t, C.X[i]) for i in tr], C.y[tr]),
                                     cartcp_test_auc=C.auc([C.predict(t, C.X[i]) for i in te], C.y[te]),
                                     cartcp_test_right=int(sum((C.predict(t, C.X[i]) > 0.5) == C.y[i] for i in te)))
        tf = cart_cp(idx); out[f"treecp|{scope}"] = tf
        print(f"\n=== {scope}: held out cp-tree {out[f'loso|{scope}']['cart_cp']} | split", {k: round(v, 3) if isinstance(v, float) else v for k, v in out[f'split|{scope}'].items()})
        print("\n".join(show(tf)))
        imp = np.array(out[f"importance|{scope}"]); o = np.argsort(-imp)
        print("RF importance (mean decrease Gini):", [(C.FEAT[j], round(float(imp[j]), 2)) for j in o[:12]])
    json.dump(out, open(os.path.join(C.HERE, "m110_out.json"), "w"))
