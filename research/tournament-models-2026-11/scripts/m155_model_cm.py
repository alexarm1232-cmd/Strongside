import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
k = ~Q.FF; fit = Q.t_ridge(); out = np.zeros(Q.N)
for s in Q.SEASONS:
    tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
def cm(m):
    p = out[m] > 0; y = Q.yb[m]
    return dict(n=int(m.sum()), pS_wS=int((p & y).sum()), pS_wW=int((p & ~y).sum()), pW_wS=int((~p & y).sum()), pW_wW=int((~p & ~y).sum()))
c = cm(k); print("all", c)
print(f"right {c['pS_wS'] + c['pW_wW']} | stronger-team wins called {c['pS_wS']}/{c['pS_wS'] + c['pW_wS']} | upsets called {c['pW_wW']}/{c['pW_wW'] + c['pS_wW']} | upset picks hit {c['pW_wW']}/{c['pW_wW'] + c['pW_wS']} | stronger picks hit {c['pS_wS']}/{c['pS_wS'] + c['pS_wW']}")
for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]:
    print(r, cm(k & (Q.RND == r)))
