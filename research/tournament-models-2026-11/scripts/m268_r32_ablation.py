# Robustness of the Round of 32 candidate: remove each input (averaged with model 1 pre @40, held out), plus core-only / matchups-only.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m267_r32_lock.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"Round of 32 Upset Model:")])
import numpy as np
def blend_right(names):
    _, ph_, fw_, _ = evaluate(names, 30.0); b_ = (ph_ + sp) / 2; f_ = (fw_ + sp) / 2
    return right(b_ >= CUT), auc(b_, ys), right(f_ >= CUT, ~early) + right(f_ >= CUT, early)
full = blend_right(INS); print(f"full 16: {full[0]} | AUC {full[1]:.3f} | fwd+bwd {full[2]}/256   (model 1 pre 201, fwd+bwd 201)")
print(f"core 12 only: {blend_right(CORE12)} | matchups only: {blend_right(mk_)}")
print("drop one input -> right @40 | AUC | fwd+bwd")
for c in INS:
    r_ = blend_right([x for x in INS if x != c]); print(f"   - {c[3:] if c.startswith('MU ') else nice(c):70} {r_[0]:3} ({r_[0] - full[0]:+d}) | {r_[1]:.3f} | {r_[2]}")
# year-level paired comparison vs model 1 pre
pk = bl >= CUT; w = t_ = l_ = 0
for s in SEASONS:
    m = Ss == s; a, b_ = right(pk, m), right(sp >= .5, m); w += a > b_; t_ += a == b_; l_ += a < b_
from math import comb
n_ = w + l_; p = sum(comb(n_, k) for k in range(w, n_ + 1)) / 2 ** n_
print(f"\nyears better / same / worse than model 1 pre: {w} / {t_} / {l_} (one-sided sign test p = {p:.3f})")
