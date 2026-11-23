import numpy as np, sys, os
sys.path.insert(0, os.getcwd()); import m99_model_types as Q
out = np.load(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m170_model_out.npy"); m = (Q.RND == "First round") & ~Q.FF
r = [int(((out[m & (Q.seas == s)] > 0) == Q.yb[m & (Q.seas == s)]).sum()) for s in Q.SEASONS]
print("R64 by year:", dict(zip(Q.SEASONS, r)), "best", max(r), "avg", round(sum(r) / len(r), 1))

