# Re-run the Round of 32 candidate and the Round 1 averages with model 1 = variant I (who plays kept, no simulator).
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_load = np.load
np.load = lambda f, *a, **kw: _load(str(f).replace("m262_model_pre_G", "m262_model_pre_I"), *a, **kw)
src = open(os.path.join(HERE, "m267_r32_lock.py"), encoding="utf-8-sig").read()
body = src[:src.index("json.dump(")] + src[src.index("# ---- Round 1 picker"):]
exec(body)
print("\nhonest cutoff, R32 average:", end=" ")
pkh = np.zeros(nS, bool)
for s in SEASONS:
    tr, te = Ss != s, Ss == s
    c = max([c / 100 for c in range(30, 61)], key=lambda c: (right(bl >= c, tr), -abs(c - .45))); pkh[te] = bl[te] >= c
print(int((pkh == (ys == 1)).sum()))
print("Round 1 cutoffs, Upset + model 1 (who plays, no sim):", {c: r_(a2p, c / 100) for c in (35, 40, 42, 45, 50)})
