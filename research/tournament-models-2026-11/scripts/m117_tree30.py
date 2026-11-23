# The tree on the model's 30 inputs only (3 strength + 27 picked measures; no who plays, no coach/star). Every game
# (Round of 64 to title, 1,007), each tournament held out: full tree (leaves to 1 game), 5+ games a leaf, pruned (cp 0.01);
# in-sample for the full tree; by round. Then the full tree trained on all games, drawn as fulltree30.svg.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
X30 = C.R.X30.copy(); FEAT30 = C.FEAT[:C.R.X30.shape[1]]
names = json.load(open(os.path.join(C.HERE, "m112_names.json")))
def fit(tr, kind):
    t = C.grow(X30, C.y, tr, 1 if kind == "full1" else 5, X30.shape[1], np.random.default_rng(0), np.zeros(X30.shape[1]))
    return C.prune_at(t, 0.01 * C.err(t)) if kind == "cp" else t
def pred(t, i):
    n = t
    while "f" in n: n = n["L"] if X30[i, n["f"]] <= n["thr"] else n["R"]
    return n["p"]
def job(args):
    kind, s = args; m = ~C.FF
    tr = np.where(m & (C.seas != s))[0]; te = np.where(m & (C.seas == s))[0]; t = fit(tr, kind)
    return kind, te.tolist(), [pred(t, i) for i in te]
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    KINDS = ["full1", "full5", "cp"]; P = {k: np.full(len(C.y), np.nan) for k in KINDS}
    with ProcessPoolExecutor(8) as ex:
        for kind, te, p in ex.map(job, [(k, s) for k in KINDS for s in C.R.SEASONS]): P[kind][te] = p
    idx = np.where(~C.FF)[0]; y = C.y; rnd = C.RND
    full = fit(idx, "full1"); f5 = fit(idx, "full5")
    lv = len(C.leaves(full)); ins1 = int(sum((pred(full, i) > 0.5) == y[i] for i in idx)); ins5 = int(sum((pred(f5, i) > 0.5) == y[i] for i in idx))
    out = {}
    for k in KINDS: out[k] = dict(right=int(((P[k][idx] > 0.5) == y[idx]).sum()), auc=C.auc(P[k][idx], y[idx]))
    print("held out:", out, "| full tree leaves", lv, "in-sample full", ins1, "5+", ins5, "leaves5", len(C.leaves(f5)))
    RO = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
    for r in RO:
        m = idx[rnd[idx] == r]; print(r, len(m), " ".join(f"{k}={int(((P[k][m] > 0.5) == y[m]).sum())}" for k in KINDS))
    # draw the full tree
    def depth(n): return 0 if "f" not in n else 1 + max(depth(n["L"]), depth(n["R"]))
    D = depth(full); W, H, TOP, BOT = 1664, 640, 70, 20; dy = (H - TOP - BOT) / D; k = [0]; parts = []; labels = []
    def place(n, d):
        yy = TOP + d * dy
        if "f" not in n:
            x = 6 + k[0] * (W - 12) / (lv - 1); k[0] += 1
            parts.append(f'<path d="M{x:.1f} {yy:.1f}h0" stroke="{"#2F6DB5" if n["p"] > 0.5 else "#D9622B"}" stroke-width="7" stroke-linecap="round"/>'); return x, yy
        xl, yl = place(n["L"], d + 1); xr, yr = place(n["R"], d + 1); x = (xl + xr) / 2; w = max(0.8, 3.2 - 0.25 * d)
        parts.append(f'<path d="M{xl:.1f} {yl:.1f}V{yy + dy * 0.5:.1f}H{xr:.1f}V{yr:.1f}M{x:.1f} {yy + dy * 0.5:.1f}V{yy:.1f}" fill="none" stroke="#4A5568" stroke-width="{w:.1f}"/>')
        if d <= 1: labels.append((x, yy, names[FEAT30[n["f"]]], n["thr"], n["n"], n["k"] / n["n"]))
        return x, yy
    place(full, 0)
    txt = []
    for x, yy, nm, thr, n, p in labels:
        txt.append(f'<text x="{x:.0f}" y="{yy - 30:.0f}" font-family="Arial" font-size="20" font-weight="bold" fill="#15233B" text-anchor="middle">{nm.replace("&", "&amp;")} ≤ {thr:.2f}</text>')
        txt.append(f'<text x="{x:.0f}" y="{yy - 8:.0f}" font-family="Arial" font-size="18" fill="#4A5568" text-anchor="middle">{n} games · stronger won {p:.0%}</text>')
    open(os.path.join(C.HERE, "fulltree30.svg"), "w", encoding="utf-8").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#FBFAF6"/>' + "".join(parts) + "".join(txt) + "</svg>")
    leaves = C.leaves(full)
    print("depth", D, "labels", [(l[2], round(l[3], 2), l[4], round(l[5], 3)) for l in labels])
    print("leaves stronger wins", sum(1 for l in leaves if l["p"] > 0.5), "of", lv, "| leaves <=3 games", sum(1 for l in leaves if l["n"] <= 3))

