import numpy as np, contextlib, io
src = open("m266_r32_tune.py", encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("WS = [")])
INS = U(KEPT16, COACH2, mk_); pa, ph, fw, b = evaluate(INS, 10.0)
for i in np.argsort(-np.abs(b[:-1])): print(f"{INS[i]:75} {b[i]:+.3f}")
pk = ph >= .45; w=t=l=0
for s in SEASONS:
    m = Ss == s; a, c = right(pk, m), right(np.zeros(nS) >= .5, m); print(int(s[:4])+1, c, a, int(pk[m].sum()), int((pk & m & (ys==1)).sum()))
