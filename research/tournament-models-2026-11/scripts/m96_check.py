# What is available: sklearn, the full candidate measure matrix (B.X / B.KS), team measure keys (TEAMK).
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
try:
    import sklearn; print("sklearn", sklearn.__version__)
except ImportError: print("no sklearn")
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])
    import m18_rebuild as R
B = R.B
print("B.X", B.X.shape, "nan share", float(np.isnan(B.X).mean()))
print("KS sample", B.KS[:8], "...", len(B.KS))
print("X30", R.X30.shape, "M.F", R.M.F.shape if hasattr(R, "M") else None)
print("TEAMK", len(TEAMK), [k for k in TEAMK][:40])
print("PLAYK", len(PLAYK), list(PLAYK)[:15])
s0 = sorted(TM)[0]; t0 = next(iter(TM[s0])); print("TM keys", list(TM[s0][t0].keys())[:30])
