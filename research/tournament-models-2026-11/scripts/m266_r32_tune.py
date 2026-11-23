# Round of 32: tune the blend honestly. For each input set and ridge strength, blend p = w * R32 + (1 - w) * model 1 pre;
# (w, cutoff) picked from the other 15 years for each held-out year. Also forward / backward with (w, cut) from the training era.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m265_r32_honest_cut.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"Round of 32:")])
import numpy as np
WS = [.3, .4, .5, .6, .7]; CUTS2 = [c / 100 for c in range(35, 56)]
def tune(ph, fw):
    P = {(w, c): (w * ph + (1 - w) * sp) >= c for w in WS for c in CUTS2}
    key = lambda m: (lambda wc: (right(P[wc], m), -abs(wc[0] - .5), -abs(wc[1] - .45)))
    pk = np.zeros(nS, bool); used = []
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; wc = max(P, key=key(tr)); pk[te] = P[wc][te]; used.append(wc)
    PF = {(w, c): (w * fw + (1 - w) * sp) >= c for w in WS for c in CUTS2}
    wf = max(PF, key=key(early)); wb = max(PF, key=key(~early))
    return pk, used, right(PF[wf], ~early), right(PF[wb], early), wf, wb
SETS = {"kept 16 + matchups": U(KEPT16, mk_), "kept 16 + coach + matchups": U(KEPT16, COACH2, mk_), "core 12 + coach + matchups": U(CORE12, COACH2, mk_),
        "core 12 + matchups": U(CORE12, mk_), "kept 16": KEPT16}
print(f"model 1 pre-tournament {right(sp >= .5)} | fwd {right(sp >= .5, ~early)}/112 | bwd {right(sp >= .5, early)}/144")
print(f"{'set, ridge':40} | blend AUC (w=.5) | honest (w,cut) right | (w,cut) used | fwd | bwd | upset picks (hit)")
BEST = None
for lab, names in SETS.items():
    for lam in (10.0, 30.0, 60.0):
        _, ph, fw, _ = evaluate(names, lam); pk, used, f_, b_, wf, wb = tune(ph, fw)
        ws_ = sorted({u[0] for u in used}); cs_ = sorted({u[1] for u in used})
        r_ = right(pk); print(f"{lab + f', ridge {lam:.0f}':40} | {auc((ph + sp) / 2, ys):.3f} | {r_:3} | w {ws_[0]}-{ws_[-1]} cut {cs_[0]:.2f}-{cs_[-1]:.2f} | {f_:3} {wf} | {b_:3} {wb} | {int(pk.sum())} ({int((pk & (ys == 1)).sum())})")
        if BEST is None or (r_, f_ + b_) > BEST[0]: BEST = ((r_, f_ + b_), lab, lam, names)
print("\nbest:", BEST[1], "ridge", BEST[2], "honest", BEST[0][0], "fwd+bwd", BEST[0][1], "of 256")
json.dump({"set": BEST[1], "ridge": BEST[2], "inputs": BEST[3]}, open(os.path.join(HERE, "m266_best.json"), "w"))
