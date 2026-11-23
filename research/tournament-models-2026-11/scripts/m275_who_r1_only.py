# Model 1 with "who plays" in Round 1 only (removed from the Round of 32).
import os, sys, json, numpy as np, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "m269_who_keep.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("for v, VER in VARS.items()")])
R1m = RND == "First round"; R2m = RND == "Second round"
VARS = {
 "A  as in the project (who plays R1+R32, simulator F4/title)": [(E12, "m who ex"), (S16E8, "m ex"), (F4T, "blend")],
 "I  who plays R1+R32, no simulator": [(E12, "m who ex"), (S16E8 | F4T, "m ex")],
 "K1 who plays R1 only (own R1 line), simulator kept": [(R1m, "m who ex"), (R2m, "m ex"), (S16E8, "m ex"), (F4T, "blend")],
 "K2 who plays R1 only (R1 line + shared R1/R32 line for R32), simulator kept": [(R1m, "m who ex"), (S16E8, "m ex"), (F4T, "blend")],
 "L1 who plays R1 only (own R1 line), no simulator": [(R1m, "m who ex"), (R2m, "m ex"), (S16E8 | F4T, "m ex")],
 "L2 who plays R1 only (R1 line + shared R1/R32 line for R32), no simulator": [(R1m, "m who ex"), (S16E8 | F4T, "m ex")],
 "G  no who plays, no simulator (fully pre-tournament)": [(E12, "m ex"), (S16E8 | F4T, "m ex")],
}
def mk2(VER, shared_r32):
    base = mk(VER)
    if not shared_r32: return base
    def run(m_tr, tr, m_te, te):
        out = base(m_tr, tr, m_te, te)
        a = E12[tr]; b = R2m[te]
        if b.any():
            cols = lambda m, idx: np.column_stack([m[:, None], Q.EX[idx]])
            f = R.wlr(cols(m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = f(cols(m_te[b], te[b]))
        return out
    return run
for lab, VER in VARS.items():
    run = mk2(VER, lab.startswith(("K2", "L2"))); out = np.zeros(N)
    for s in Q.SEASONS:
        tr = np.where((seas != s) & k)[0]; te = np.where((seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = run(m_tr, tr, m_te, te)
    held = int(((out[k] > 0) == yk[k]).sum()); rr = [int(((out[k & (RND == r)] > 0) == yk[k & (RND == r)]).sum()) for r in RN]
    print(f"{lab:78} {held}/{int(k.sum())} | {'/'.join(map(str, rr))}")
