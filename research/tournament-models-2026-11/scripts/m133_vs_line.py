import os, sys, contextlib, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
ns = {"__file__": os.path.join(Q.OLD, "overfit_test.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(Q.OLD, "overfit_test.py"), encoding="utf-8").read().split("KS = list(rows[0])")[0] + "\nimport numpy as np\nclose_=np.array(closeright)", ns)
close_ = ns["close_"]; G = ns["G"]
# closing line's pick, in terms of "stronger team (S) wins": closeright says whether the line favorite won
B = Q.R.B; k = ~Q.FF; fit = Q.t_ridge(); out = np.zeros(Q.N)
for s in Q.SEASONS:
    tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
    m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
model_right = ((out > 0) == Q.yb)
have = k & (close_ != 0.5)
line_right = close_ == 1.0
print("games with a line:", int(have.sum()), "| model right", int(model_right[have].sum()), "| line right", int(line_right[have].sum()))
dis = have & (model_right != line_right)   # they picked different teams iff exactly one is right
print("disagree:", int(dis.sum()), "| model right", int((model_right & dis).sum()), "| line right", int((line_right & dis).sum()))
for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]:
    m = dis & (Q.RND == r); print(f"  {r:13} disagree {int(m.sum()):3}  model {int((model_right & m).sum()):3}  line {int((line_right & m).sum()):3}")
from math import comb
n = int(dis.sum()); w = int((model_right & dis).sum())
p = sum(comb(n, i) for i in range(max(w, n - w), n + 1)) / 2 ** n * 2
print(f"sign test two-sided p = {min(1, p):.3f}")
