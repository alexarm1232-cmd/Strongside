# ORIGINAL MODEL (model 1) only. Round of 32 "who plays" = the team's Round 1 lineup (optionally minus players who look hurt
# in Round 1's play-by-play). Round 1 keeps its own who plays. Same pipeline as m262b / m269.
import os, sys, json, numpy as np, contextlib, io, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "m269_who_keep.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("for v, VER in VARS.items()")])
F_ACT = M.F.copy()
F_R1 = np.load(os.path.join(HERE, "m277_who_r32_from_r1_noinj.npy")); F_INJ = np.load(os.path.join(HERE, "m277_who_r32_from_r1.npy")); FA = np.load(os.path.join(HERE, "m277_who_r32_from_r1_a.npy")); FC = np.load(os.path.join(HERE, "m277_who_r32_from_r1_c.npy"))
R2m = RND == "Second round"
def score(F, VER, shared_noWho_r32=False):
    M.F[:] = F
    run = mk(VER); out = np.zeros(N)
    for s in Q.SEASONS:
        tr = np.where((seas != s) & k)[0]; te = np.where((seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = run(m_tr, tr, m_te, te)
    M.F[:] = F_ACT
    held = int(((out[k] > 0) == yk[k]).sum()); rr = [int(((out[k & (RND == r)] > 0) == yk[k & (RND == r)]).sum()) for r in RN]
    return held, rr, out
NOSIM = [(E12, "m who ex"), (S16E8 | F4T, "m ex")]; SIM = [(E12, "m who ex"), (S16E8, "m ex"), (F4T, "blend")]
for lab, F, VER in (("actual Round of 32 lineup (game day), no simulator  [754]", F_ACT, NOSIM),
                    ("Round 1 lineup carried into the Round of 32, no simulator", F_R1, NOSIM),
                    ("Round 1 lineup minus Round 1 injuries (play-by-play), no simulator", F_INJ, NOSIM),
                    ("R1 lineup minus injuries, stricter rule a (41 flagged), no simulator", FA, NOSIM), ("R1 lineup minus injuries, strictest rule c (25 flagged), no simulator", FC, NOSIM), ("actual Round of 32 lineup, simulator in Final Four/title  [759]", F_ACT, SIM),
                    ("Round 1 lineup carried into the Round of 32, simulator in F4/title", F_R1, SIM),
                    ("Round 1 lineup minus Round 1 injuries, simulator in F4/title", F_INJ, SIM)):
    h, rr, _ = score(F, VER); print(f"{lab:72} {h}/{int(k.sum())} | {'/'.join(map(str, rr))}")
print("(752 = no who plays in the Round of 32, shared line, no simulator)")

