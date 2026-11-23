# Full rebuild with one rating input removed. The measure selection is redone from scratch (m56/dedup_model's picker:
# each candidate's z on top of the strength inputs, keep |z| >= 2, drop anything overlapping strength or an already-kept
# measure at |r| >= 0.3), picked from all games (as the original 27 were), then the full model is built and scored the
# same way as the 756: base score held out inside training, round lines (who plays + coach/star; coach/star; 15% line +
# 85% simulator in the Final Four/title), First Four out, each tournament held out.
#   A original model (3 strength + the original 27)                      -> should be 756
#   B selection re-run with all 3 strength inputs                         -> the method baseline
#   C full rebuild without "gap" (rating gap)          -> 2 strength inputs + a fresh pick
#   D full rebuild without "gap x possessions"         -> 2 strength inputs + a fresh pick
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"; os.environ.setdefault("OMP_NUM_THREADS", "1")
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import m56_fold_pick as F
STR0 = list(F.STR); KS = F.KS
iG = next(c for c in STR0 if KS[c] == "gap"); iP = next(c for c in STR0 if KS[c] == "gap x possessions")
VARIANTS = {"A original model (3 strength + original 27)": (STR0, "orig"),
            "B selection re-run, 3 strength inputs": (STR0, "pick"),
            "C full rebuild without rating gap": ([c for c in STR0 if c != iG], "pick"),
            "D full rebuild without rating gap x pace": ([c for c in STR0 if c != iP], "pick")}
ALL = np.where(~F.FF)[0]
def picks_for(name):
    strc, how = VARIANTS[name]; F.STR = list(strc)
    return list(F.kept) if how == "orig" else F.dedup_select(ALL, F.XC, 2.0)
def job(args):
    name, s = args; strc, _ = VARIANTS[name]; picks = picks_for(name); F.STR = list(strc)
    tr = np.where((F.seas != s) & ~F.FF)[0]; te = np.where((F.seas == s) & ~F.FF)[0]
    m_tr, m_te, cols = F.base(tr, te, lambda idx: picks)
    return name, te.tolist(), F.run(m_tr, tr, m_te, te).tolist()
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    D3 = np.load("m3_data.npz", allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
    info = {}
    for name in VARIANTS:
        p = picks_for(name); info[name] = p
    orig = set(F.kept)
    for name, p in info.items():
        print(f"{name}: {len(VARIANTS[name][0])} strength + {len(p)} measures | same as original 27: {len(orig & set(p))}"
              + (f" | new: {[KS[c] for c in p if c not in orig]} | dropped: {[KS[c] for c in orig if c not in p]}" if VARIANTS[name][1] == "pick" else ""))
    SC = {n: np.full(F.N, np.nan) for n in VARIANTS}
    with ProcessPoolExecutor(8) as ex:
        for name, te, v in ex.map(job, [(n, s) for n in VARIANTS for s in F.SEASONS]): SC[name][te] = v
    keep = ~F.FF; yb = F.yb; dogS = sS > sW; diff = keep & (sS != sW)
    RO = [("First round", "R64"), ("Second round", "R32"), ("Sweet 16", "S16"), ("Elite Eight", "E8"), ("Final Four", "F4"), ("Championship", "Title")]
    print(f"\n{'version':46} {'right':>5} " + " ".join(f"{b:>5}" for _, b in RO) + f" | {'upsets picked':>13} {'hit':>4}")
    for name, sc in SC.items():
        r = (sc > 0) == yb; up = diff & np.where(dogS, sc > 0, sc < 0)
        print(f"{name:46} {int(r[keep].sum()):5d} " + " ".join(f"{int(r[keep & (F.RND == a)].sum()):5d}" for a, _ in RO) + f" | {int(up.sum()):13d} {int((up & r).sum()):4d}")
