import numpy as np, contextlib, io
src = open("m275_who_r1_only.py", encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("for lab, VER in VARS.items()")])
# M: shared R1+R32 line WITH who plays (trained on both rounds), used for Round 1 only; Round of 32 from the shared line without who plays
def run(m_tr, tr, m_te, te):
    out = mk([(S16E8 | F4T, "m ex")])(m_tr, tr, m_te, te)
    a = E12[tr]
    for spec, b in (("m who ex", R1m[te]), ("m ex", R2m[te])):
        cols = lambda m, idx: np.column_stack([{"m": m[:, None], "who": M.F[idx], "ex": Q.EX[idx]}[c] for c in spec.split()])
        f = R.wlr(cols(m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = f(cols(m_te[b], te[b]))
    return out
out = np.zeros(N)
for s in Q.SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.where((seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = run(m_tr, tr, m_te, te)
print(int(((out[k] > 0) == yk[k]).sum()), [int(((out[k & (RND == r)] > 0) == yk[k & (RND == r)]).sum()) for r in RN])
print("R1 games", int((k & R1m).sum()), "R32 games", int((k & R2m).sum()))
np.save("m262_model_pre_M.npy", out)
