# Weighted blend of the three upset chances: p = wu * Upset Model + wm * regular model (patched) + ws * simulator, pick the
# lower seed at a cutoff. Real games, each year held out. Weights on a 0.1 grid; also an honest version where the weights
# and cutoff for each year are picked from the other 15 years.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
G = Q.R.B.G; B = Q.R.B; kk = lambda s: (s or "").rstrip(". ")
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); rows = D["rows"]; y1 = np.array(D["y"])
pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
OUT_I = np.load(os.path.join(HERE, "m262_model_pre_I.npy")); OUT_G = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))
gi = np.array([r["i"] for r in rows]); hs = np.array([r["HisS"] for r in rows]); s1 = np.array([r["s"] for r in rows])
sig = lambda z: 1 / (1 + np.exp(-z))
mo1 = np.where(hs, sig(-OUT_I[gi]), sig(OUT_I[gi])); si1 = np.where(hs, 1 - B.simS[gi], B.simS[gi])
UPX = json.load(open(os.path.join(HERE, "m289_upset_r32.json")))["real"]
up2 = np.array([r["p"] for r in UPX]); y2 = np.array([r["up"] for r in UPX]); s2 = np.array([r["s"] for r in UPX])
g2 = [next(j for j, g in enumerate(G) if g["season"] == r["s"] and g["rnd"] == "Second round" and {kk(g["fav"]), kk(g["dog"])} == {kk(r["h"]), kk(r["l"])}) for r in UPX]
h2 = np.array([kk(B.Sname[i]) == kk(r["h"]) for i, r in zip(g2, UPX)]); g2 = np.array(g2)
mo2 = np.where(h2, sig(-OUT_G[g2]), sig(OUT_G[g2])); si2 = np.where(h2, 1 - B.simS[g2], B.simS[g2])
W = [(a / 10, b / 10, round(1 - a / 10 - b / 10, 1)) for a in range(11) for b in range(11 - a)]
CUTS = [c / 100 for c in range(30, 61)]
def table(up, mo, si, yy, ss, label):
    right = lambda p, c, m=None: int((((p >= c) == (yy == 1)) if m is None else ((p >= c) == (yy == 1))[m]).sum())
    best = []
    for w in W:
        p = w[0] * up + w[1] * mo + w[2] * si
        for c in CUTS: best.append((right(p, c), w, c))
    best.sort(key=lambda x: -x[0])
    print(f"\n{label}: best weight / cutoff combinations (upset, model, sim) on all years")
    for r_, w, c in best[:8]: print(f"   {w} @ {c:.2f}: {r_}")
    # honest: choose (w, c) on the other years
    pk = np.zeros(len(yy), bool); used = []
    P = {w: w[0] * up + w[1] * mo + w[2] * si for w in W}
    for s in sorted(set(ss)):
        tr, te = ss != s, ss == s
        sc = max(((right(P[w], c, tr), -abs(c - .45), w, c) for w in W for c in CUTS))
        pk[te] = P[sc[2]][te] >= sc[3]; used.append((sc[2], sc[3]))
    print(f"   honest (weights + cutoff chosen on the other 15 years): {int((pk == (yy == 1)).sum())} | upset picks {int(pk.sum())}, hit {int((pk & (yy == 1)).sum())}")
    from collections import Counter; print("   chosen most often:", Counter(used).most_common(3))
    for lab, w, c in (("upset alone", (1, 0, 0), .40 if 'Round 1' in label else .45), ("equal thirds", (1/3, 1/3, 1/3), .45), ("equal thirds", (1/3, 1/3, 1/3), .40),
                      ("half upset, quarter each", (.5, .25, .25), .40), ("half upset, quarter each", (.5, .25, .25), .45)):
        p = w[0] * up + w[1] * mo + w[2] * si; print(f"   {lab} {tuple(round(x, 2) for x in w)} @ {c:.2f}: {right(p, c)} ({int((p >= c).sum())} picks, {int(((p >= c) & (yy == 1)).sum())} hit)")
table(pho, mo1, si1, y1, s1, "Round 1 (511 games)")
table(up2, mo2, si2, y2, s2, "Round of 32 (256 real games; simulator = its recorded game-day chance)")
