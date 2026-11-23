import numpy as np, os, contextlib, io
src = open("m266_r32_tune.py", encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("WS = [")])
CUTS = [c/100 for c in range(30, 61)]
def honest(p):
    pk = np.zeros(nS, bool)
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; c = max(CUTS, key=lambda c: (right(p >= c, tr), -abs(c - .45))); pk[te] = p[te] >= c
    return right(pk), int(pk.sum()), int((pk & (ys == 1)).sum())
SETS = {"core 12 + matchups": U(CORE12, mk_), "kept 16 + matchups": U(KEPT16, mk_), "kept 16 + coach + matchups": U(KEPT16, COACH2, mk_),
        "core 12": CORE12, "kept 16": KEPT16, "matchups only": mk_, "core 12 + coach + matchups": U(CORE12, COACH2, mk_)}
print("higher seed", right(np.zeros(nS) >= .5), "| model 1 (who plays, no sim) alone 203")
print(f"{'set':32} ridge | AUC | @40 | @45 | @50 | honest (picks, hit) | fwd/112 bwd/144 @40")
for lab, n in SETS.items():
    for lam in (10.0, 30.0, 60.0):
        _, ph, fw, _ = evaluate(n, lam)
        print(f"{lab:32} {lam:4.0f} | {auc(ph, ys):.3f} | {right(ph>=.4)} | {right(ph>=.45)} | {right(ph>=.5)} | {honest(ph)} | {right(fw>=.4, ~early)} {right(fw>=.4, early)}")
