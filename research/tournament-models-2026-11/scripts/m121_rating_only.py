# The 756 pipeline (m99: base score held out inside training, round lines with who plays + coach/star in rounds 1-2,
# coach/star in Sweet 16/Elite 8, 15% line + 85% simulator in Final Four/title, First Four out, each tournament held out)
# with the base score built from ONLY rating gap and rating gap x pace (and each alone), against the full 30 inputs.
# Games right by round, upset picks (worse seed) and hits.
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
D3 = np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
ig, ip = names.index("gap"), names.index("gap x possessions")
V = {"all 30 inputs (current model)": list(range(30)), "drop rating gap (keep gap x pace)": [c for c in range(30) if c != ig],
     "drop gap x pace (keep rating gap)": [c for c in range(30) if c != ip]}
def job(name):
    fit = Q.t_ridge(X=Q.X30[:, V[name]]); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & ~Q.FF)[0]; te = np.where((Q.seas == s) & ~Q.FF)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    return name, out
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    keep = ~Q.FF; yb = Q.yb; dogS = sS > sW; diff = keep & (sS != sW)
    RO = [("First round", "R64"), ("Second round", "R32"), ("Sweet 16", "S16"), ("Elite Eight", "E8"), ("Final Four", "F4"), ("Championship", "Title")]
    print(f"{'base inputs':34} {'right':>5} " + " ".join(f"{b:>5}" for _, b in RO) + f" | {'upsets picked':>13} {'hit':>4}")
    with ProcessPoolExecutor(4) as ex:
        for name, sc in ex.map(job, V):
            r = (sc > 0) == yb
            up = diff & np.where(dogS, sc > 0, sc < 0)
            print(f"{name:34} {int(r[keep].sum()):5d} " + " ".join(f"{int(r[keep & (Q.RND == a)].sum()):5d}" for a, _ in RO)
                  + f" | {int(up.sum()):13d} {int((up & r).sum()):4d}")
    PK = np.abs(Q.B.simS - 0.5) < 1e-4; sim = np.where(PK, 0.5, (Q.B.simS > 0.5) == yb)
    print(f"{'(simulator)':34} {sim[keep].sum():5.0f}")
