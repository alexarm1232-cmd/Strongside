# Feeding test with the LOCKED standalone Round of 32 Upset Model (22 inputs, ridge 10, upset at 45%), against the actual brackets.
# Round 1 picks: R64 Upset Model (held out, upset at 40%). All years held out. Bracket points: R1 = 1, R32 = 2.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m263_feed_bracket.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("MODELS = {}")])
import numpy as np
LOCK = ["L-H star_usage_rate", "L coach car_s16", "H pt_d_share Post-Up", "L pt_ppp Inside Out", "L-H pt_ppp Pick & Pop", "H pt_ppp Big Cut & Roll",
        "L pt_d_ppp Transition", "H ftr", "H exp", "L pt_share Mid-Range", "L pt_share Post-Up", "L-H big_height", "L-H coach rec5_s16", "H pt_d_ppp High-Low",
        "L-H tourney wins last 3", "H bench_minutes", "H pt_share Perimeter Cut", "L-H pt_d_ppp Rim Attack"]
k0 = next(iter(TEAM.values())); miss = [c for c in LOCK if c.split(" ", 1)[1] not in k0]
print("inputs missing from team table:", miss)
LAM = 10.0
def feats2(h, l, feed=False):
    v = [raw(h, l, c) for c in LOCK]
    v += [zz(h, l, a) * zz(h, l, b) for _, a, b in PTM]
    v += [(zz(h, l, "L pt_ppp Rim Attack") + zz(h, l, "H pt_d_ppp Rim Attack")) - (zz(h, l, "H pt_ppp Rim Attack") + zz(h, l, "L pt_d_ppp Rim Attack"))]
    if feed:
        ph_, pl_ = P1.get(h, .5), P1.get(l, .5)
        v += [ph_, pl_, pl_ - ph_] if feed == "probs" else [pl_ - ph_]
    return v
feats = feats2
MODELS = {}
right = lambda p, c: int(((p >= c) == (yR == 1)).sum())
for lab, feed in (("separate", False), ("fed gap", "gap"), ("fed both", "probs")):
    X = np.array([feats2(r["h"], r["l"], feed) for r in REAL]); ph = np.zeros(nR); fits = {}
    for s in SEASONS:
        tr, te = sR != s, sR == s; f = ridge(X[tr], yR[tr], wR[tr], LAM); fits[s] = f
        if te.any(): ph[te] = f(X[te])
    MODELS[lab] = (feed, fits, ph)
    print(f"   {lab:10} real R32 games held out: AUC {auc(ph, yR):.3f} | right @40 {right(ph, .4)} @45 {right(ph, .45)} @50 {right(ph, .5)} / {nR}")
print(f"   higher seed every time: {int((yR == 0).sum())}")
src = open(os.path.join(HERE, "m263_feed_bracket.py"), encoding="utf-8-sig").read(); _a = src.index("def pr32"); _b = src.index("\n", src.index("chalk = lambda")); exec(src[_a:_b])
print("\nBRACKETS vs the actual results, 16 years, every year held out")
print(f"{'Round 1':22} {'Round of 32':34} points | R1 right | R32 right | R32 upset picks")
for r1lab, r1f in (("higher seed", chalk), ("R64 Upset Model @40", up40)):
    for r32lab, mode, cut in (("higher seed", "chalk", .5), ("separate @45", "separate", .45), ("separate @40", "separate", .4),
                              ("fed gap @45", "fed gap", .45), ("fed gap @40", "fed gap", .4), ("fed both @45", "fed both", .45), ("fed both @40", "fed both", .4)):
        pts, a, b, u = bracket(r1f, mode, cut); print(f"{r1lab:22} {r32lab:34} {pts:6} | {a:4} | {b:4} | {u}")
for lab in ("separate", "fed gap"):
    pts, a, b, u = bracket(None, "joint", .4, lab); print(f"{'joint pod pick':22} {lab:34} {pts:6} | {a:4} | {b:4} | {u}")
