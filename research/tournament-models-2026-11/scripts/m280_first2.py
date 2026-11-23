import os, sys, numpy as np, contextlib, io, json
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"; sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
k = ~Q.FF; RND = Q.RND; yk = Q.yb; seas = Q.seas
old = np.load(os.path.join(HERE, "m170_model_out.npy")); pat = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))
for r in ("First round", "Second round"):
    m = k & (RND == r)
    print(r, int(m.sum()), "sim", int(((Q.SIM[m] > 0) == yk[m]).sum()), "model old", int(((old[m] > 0) == yk[m]).sum()), "model patched", int(((pat[m] > 0) == yk[m]).sum()))
    # sim/old/pat:", [(s[:4], int(((Q.SIM[m & (seas == s)] > 0) == yk[m & (seas == s)]).sum())) for s in Q.SEASONS][:2])

