import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m132_reddit as R2
import numpy as np
Q = R2.Q; k = R2.k
oS, oW = R2.overS, R2.overW          # + = seeded better than the rating says (over-seeded), - = under-seeded
F = {"S over-seeded 2+": (oS >= 2) * 1.0, "W over-seeded 2+": (oW >= 2) * 1.0,
     "S under-seeded 2+": (oS <= -2) * 1.0, "W under-seeded 2+": (oW <= -2) * 1.0,
     "S under-seeded 1+": (oS <= -1) * 1.0, "W under-seeded 1+": (oW <= -1) * 1.0,
     "S lines off (signed)": oS, "W lines off (signed)": oW}
V = {"current 756 (30)": None, "+ under-seeded 2+ (S, W)": ["S under-seeded 2+", "W under-seeded 2+"],
     "+ over- and under-seeded 2+ (all 4)": ["S over-seeded 2+", "W over-seeded 2+", "S under-seeded 2+", "W under-seeded 2+"],
     "+ W under-seeded 2+ only": ["W under-seeded 2+"]}
def job(name):
    XX = Q.X30 if V[name] is None else np.column_stack([Q.X30] + [F[f] for f in V[name]])
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    return name, held, insr, auc
if __name__ == "__main__":
    for f, v in F.items(): print(f"z on top of strength  {f:22} {R2.zt(v):+.2f}   games with it: {int(v[k].sum()) if 'signed' not in f else '-'}")
    # how under-seeded teams (seeds 1-16, 2+ lines worse seed than rating) did vs teams seeded within 1 line
    G = R2.G; imp = R2.imp; rows = []
    for s in sorted({g["season"] for g in G}):
        gs = [g for g in G if g["season"] == s and g["rnd"] != "First Four"]
        for t in {x for g in gs for x in (g["fav"], g["dog"])}:
            mine = [g for g in gs if t in (g["fav"], g["dog"])]; seed = mine[0]["fseed"] if mine[0]["fav"] == t else mine[0]["dseed"]
            rows.append((imp[(s, t)] - seed, seed, len([g for g in mine if (g["fav"] == t) == g["fav_won"]])))
    for lo, hi, nm in ((-99, -2, "under-seeded 2+ lines"), (-1, 1, "within 1 line"), (2, 99, "over-seeded 2+ lines")):
        w = [x for d, sd, x in rows if lo <= d <= hi and sd <= 12]
        print(f"seeds 1-12, {nm:22} {len(w):4} teams, avg tournament wins {np.mean(w):.2f}, R64 exits {np.mean(np.array(w) == 0):.0%}")
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(4) as ex:
        for name, held, insr, auc in ex.map(job, V):
            print(f"{name:38} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f}", flush=True)
