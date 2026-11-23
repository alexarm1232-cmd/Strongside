# Round of 32: honest cutoffs (each year's cutoff picked from the other 15 years only, like the Round 1 average's 397 check),
# forward / backward with the cutoff picked in the training era, and year by year. Pre-tournament model 1 (variant G) only.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m264_r32_optimize.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(\"\\n1. vs pre-tournament")])
import numpy as np
CUTS = [c / 100 for c in range(30, 61)]
def honest(score_fn):
    """score_fn(cut) -> boolean picks over all games; cutoff per held-out year chosen on the other years"""
    P = {c: score_fn(c) for c in CUTS}; pk = np.zeros(nS, bool); used = []
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; c = max(CUTS, key=lambda c: (right(P[c], tr), -abs(c - .45))); pk[te] = P[c][te]; used.append(c)
    return pk, used
def era(score_fn):
    P = {c: score_fn(c) for c in CUTS}
    cf = max(CUTS, key=lambda c: (right(P[c], early), -abs(c - .45))); cb = max(CUTS, key=lambda c: (right(P[c], ~early), -abs(c - .45)))
    return right(P[cf], ~early), right(P[cb], early), cf, cb
print(f"Round of 32: {nS} games | model 1 pre-tournament {right(sp >= .5)} (2018-26 {right(sp >= .5, ~early)}/{int((~early).sum())}, 2010-17 {right(sp >= .5, early)}/{int(early.sum())}) | higher seed {right(np.zeros(nS) >= .5)}")
print(f"\n{'combo':58} | honest-cutoff right | cutoffs used | fwd (cut from 10-17) | bwd (cut from 18-26) | upsets picked (hit)")
OUT = {}
for lab, names in CANDS.items():
    pa, ph, fw, _ = evaluate(names)   # ph held out by year; fw = forward/backward era fits
    for kind, fn_ho, fn_era in (("alone", lambda c, ph=ph: ph >= c, lambda c, fw=fw: fw >= c),
                                ("avg with M1-pre", lambda c, ph=ph: (ph + sp) / 2 >= c, lambda c, fw=fw: (fw + sp) / 2 >= c),
                                ("override on M1-pre", lambda c, ph=ph: (sp >= .5) | (ph >= c), lambda c, fw=fw: (sp >= .5) | (fw >= c))):
        pk, used = honest(fn_ho); f_, b_, cf, cb = era(fn_era)
        OUT[(lab, kind)] = pk
        print(f"{lab + ' | ' + kind:58} | {right(pk):3} | {min(used):.2f}-{max(used):.2f} | {f_:3}/{int((~early).sum())} @{cf:.2f} | {b_:3}/{int(early.sum())} @{cb:.2f} | {int(pk.sum())} ({int((pk & (ys == 1)).sum())})")
best = max(OUT, key=lambda k: right(OUT[k])); pk = OUT[best]
print(f"\nbest honest combo: {best[0]} | {best[1]} = {right(pk)} vs model 1 pre-tournament {right(sp >= .5)}")
print("year | games | model 1 pre | best combo | upset picks (hit) | higher seed")
for s in SEASONS:
    m = Ss == s; print(f"   {int(s[:4]) + 1} | {int(m.sum())} | {right(sp >= .5, m)} | {right(pk, m)} | {int(pk[m].sum())} ({int((pk & m & (ys == 1)).sum())}) | {right(np.zeros(nS) >= .5, m)}")
