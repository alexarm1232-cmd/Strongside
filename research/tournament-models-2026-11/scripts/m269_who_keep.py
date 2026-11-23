# Model 1 with "who plays" kept in Rounds 1-2, simulator out (Sweet 16 to title share one "m ex" line, like variant G).
import os, sys, json, numpy as np, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "m262b.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("RN = [")])
RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]; yk = Q.yb
VARS = {"A": [(E12, "m who ex"), (S16E8, "m ex"), (F4T, "blend")],
        "I": [(E12, "m who ex"), (S16E8 | F4T, "m ex")],
        "J": [(E12, "m who ex"), (S16E8, "m ex"), (F4T, "m ex")],
        "G": [(E12, "m ex"), (S16E8 | F4T, "m ex")]}
def mk(VER):
    def run(m_tr, tr, m_te, te):
        cols = lambda spec, m, idx: np.column_stack([{"m": m[:, None], "who": M.F[idx], "ex": Q.EX[idx]}[c] for c in spec.split()])
        out = np.zeros(len(te))
        for grp, spec in VER:
            b = grp[te]; a = grp[tr]
            if not b.any(): continue
            if spec == "blend":
                f = R.wlr(cols("m ex", m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = 0.15 * f(cols("m ex", m_te[b], te[b])) + 0.85 * Q.SIM[te][b]
            else:
                f = R.wlr(cols(spec, m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = f(cols(spec, m_te[b], te[b]))
        return out
    return run
for v, VER in VARS.items():
    run = mk(VER); out = np.zeros(N)
    for s in Q.SEASONS:
        tr = np.where((seas != s) & k)[0]; te = np.where((seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = run(m_tr, tr, m_te, te)
    held = int(((out[k] > 0) == yk[k]).sum()); rr = [int(((out[k & (RND == r)] > 0) == yk[k & (RND == r)]).sum()) for r in RN]
    print(f"{v}: {held}/{int(k.sum())} | {'/'.join(map(str, rr))}")
    if v in "IJ": np.save(os.path.join(HERE, f"m262_model_pre_{v}.npy"), out)
