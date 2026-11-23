# How much of the model survives without the hard-to-get data? Rounds of 64 to Elite Eight only, model only, each
# tournament held out (same machinery as m18: half-life 12, base levers refit without each tournament, round lines).
# Inputs, by how hard they are to get:
#   strength (3)     rating gap, schedule-strength gap, gap x pace       - rebuildable from public results
#   box (7)          d_ast, tempo, d_tov, orb, d_ft, d_p2, d_blk           - public box scores
#   game state (4)   pm_close2h, pm_ahead10, comeback10, nst_to             - play-by-play
#   play types (12)  pt_*                                                  - play-by-play + our own play-type tagging
#   player (4)       star_usage_rate x2, lost_minutes, star_three_share    - player game logs
#   who plays (6)    the rounds 1-2 lineup columns                          - game-day lineups
#   coach (2)        coach tournament history                               - public
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import m18_rebuild as R
    import m10_model2 as M
D = np.load("m3_data.npz", allow_pickle=True); NAMES = [str(n) for n in D["names"]]; sS, sW = D["seedS"], D["seedW"]
X_ALL = R.X30.copy(); yb, RND, seas = R.yb, R.RND, R.seas
EARLY4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
def kind(n):
    if n in ("gap", "sos gap", "gap x possessions"): return "strength"
    k = n[2:]
    if k.startswith("pt_"): return "play types"
    if k in ("pm_close2h", "pm_ahead10", "comeback10", "nst_to"): return "game state"
    if k in ("star_usage_rate", "lost_minutes", "star_three_share"): return "player"
    return "box"
KIND = [kind(n) for n in NAMES]
SEEDGAP = (sS - sW).astype(float)[:, None]                     # stronger-rated team's seed minus weaker's (negative = better seed)
def run(kinds, who, extra):
    cols = [i for i, k in enumerate(KIND) if k in kinds]; R.X30 = X_ALL[:, cols]
    groups = [(a, g, who and w) for a, g, w in M.GROUPS]; old = M.GROUPS; M.GROUPS = groups
    wts = R.weights(12); sc = np.zeros(len(yb))
    for s in R.SEASONS:
        tr = np.where(seas != s)[0]; te = np.where(seas == s)[0]
        m_tr, m_te = R.base_scores(tr, te, wts); sc[te] = R.model(m_tr, tr, m_te, te, wts, extra)
    M.GROUPS = old; R.X30 = X_ALL
    return int(((sc > 0) == yb)[EARLY4].sum()), len(cols)
CS = R.EXTRA["coach+star"]; CO = R.EXTRA["coach"]
ALL = {"strength", "box", "game state", "play types", "player"}
VARIANTS = [
    ("full model (as the 756)", ALL, True, CS),
    ("full + seed gap", ALL, True, np.column_stack([CS, SEEDGAP])),
    ("no who plays", ALL, False, CS),
    ("no who plays, no player stats", ALL - {"player"}, False, CO),
    ("public: strength + box + coach", {"strength", "box"}, False, CO),
    ("strength + coach", {"strength"}, False, CO),
    ("strength only", {"strength"}, False, None),
    ("seed gap only", set(), False, SEEDGAP),
]
n = int(EARLY4.sum()); print("games R64-E8:", n)
seed_r = np.where(sS == sW, 0.5, np.where(sS < sW, yb, ~yb))[EARLY4].sum(); sim = R.B.simS
sim_r = np.where(np.abs(sim - 0.5) < 1e-4, 0.5, (sim > 0.5) == yb)[EARLY4].sum()
print(f"{'seeds (pick the better seed)':36} {seed_r:6.1f} {seed_r / n:.1%}")
print(f"{'simulator':36} {sim_r:6.1f} {sim_r / n:.1%}")
for name, kinds, who, extra in VARIANTS:
    r, k = run(kinds, who, extra); print(f"{name:36} {r:6d} {r / n:.1%}   ({k} measures)")
