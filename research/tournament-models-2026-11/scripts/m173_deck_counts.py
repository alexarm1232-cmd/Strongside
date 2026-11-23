import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
out = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m170_model_out.npy"))
k = ~Q.FF; yb = Q.yb; sim = Q.R.B.simS
mr = (out > 0) == yb; sr = (sim > 0.5) == yb
print("model right", int(mr[k].sum()), "| sim right", int(sr[k].sum()))
print("boxes: both right", int((mr & sr)[k].sum()), "| model right sim wrong", int((mr & ~sr)[k].sum()), "| sim right model wrong", int((~mr & sr)[k].sum()), "| both wrong", int((~mr & ~sr)[k].sum()))
p = out > 0
c = dict(pS_wS=int((p & yb)[k].sum()), pS_wW=int((p & ~yb)[k].sum()), pW_wS=int((~p & yb)[k].sum()), pW_wW=int((~p & ~yb)[k].sum())); print("confusion", c)
print(f"sens {c['pS_wS']/(c['pS_wS']+c['pW_wS']):.3f} spec {c['pW_wW']/(c['pW_wW']+c['pS_wW']):.3f} upset-pick hit {c['pW_wW']/(c['pW_wW']+c['pW_wS']):.3f} stronger-pick hit {c['pS_wS']/(c['pS_wS']+c['pS_wW']):.3f}")
for r in ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]:
    m = k & (Q.RND == r); a = int((p & yb)[m].sum()); b = int((~p & yb)[m].sum()); cc = int((p & ~yb)[m].sum()); d = int((~p & ~yb)[m].sum())
    print(f"{r:13} games {int(m.sum())} right {a + d} sens {a}/{a + b} spec {d}/{d + cc}")
for s in Q.SEASONS:
    m = k & (Q.seas == s); print(s, "splits model", int((mr & ~sr)[m].sum()), "sim", int((~mr & sr)[m].sum()))
