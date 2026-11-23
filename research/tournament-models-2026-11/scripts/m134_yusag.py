# YUSAG-style rating: weighted least squares, margin = rating(home) - rating(away) + HCA (0 if neutral), pre-tournament
# D-I games only. Weights: recency 0.5-1.0 on a sigmoid of relative recency (flat after ~0.4-0.5), and an unweighted one.
# Then: corr with our rating gap, z on top of strength, swap for the rating gap (and gap x pace), and add to the 756.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
B = Q.R.B; G = B.G; TM = B.TM
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m134_games.json")
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    return s, [(g["date"], g["home"], g["away"], g["neutral"], g["hs"] - g["as_"]) for g in games if g["date"] < first and g["hs"] is not None]
def ratings(rows, recency):
    teams = sorted({t for r in rows for t in r[1:3]}); ix = {t: i for i, t in enumerate(teams)}
    dates = sorted({r[0] for r in rows}); dpos = {d: i / max(1, len(dates) - 1) for i, d in enumerate(dates)}
    A = np.zeros((len(rows), len(teams) + 1)); y = np.zeros(len(rows)); w = np.ones(len(rows))
    for j, (d, h, a, neu, m) in enumerate(rows):
        A[j, ix[h]] = 1; A[j, ix[a]] = -1; A[j, -1] = 0 if neu else 1; y[j] = m
        if recency: w[j] = 0.5 + 0.5 / (1 + np.exp(-15 * (dpos[d] - 0.2)))
    A = np.vstack([A, np.r_[np.ones(len(teams)), 0]]); y = np.r_[y, 0]; w = np.r_[w, 1e3]   # ratings sum to 0
    sw = np.sqrt(w); sol = np.linalg.lstsq(A * sw[:, None], y * sw, rcond=None)[0]
    return {t: sol[ix[t]] for t in teams}
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
ig, ip = names.index("gap"), names.index("gap x possessions")
k = ~Q.FF
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
if os.path.exists(CACHE):
    GM = json.load(open(CACHE)); YU = {}
    for s, rows in GM.items(): YU[s] = (ratings(rows, True), ratings(rows, False))
    def gapcol(j):
        out = []
        for i, g in enumerate(G):
            R_ = YU[g["season"]][j]; a, b = R_.get(B.Sname[i]) or R_.get(B.Sname[i] + "."), R_.get(Wn[i]) or R_.get(Wn[i] + ".")
            out.append(np.nan if a is None or b is None else (a - b) / 10)
        return np.array(out)
    yw, yu = gapcol(0), gapcol(1)
    pace = np.where(np.abs(Q.X30[:, ig]) > 1e-9, Q.X30[:, ip] / np.where(np.abs(Q.X30[:, ig]) > 1e-9, Q.X30[:, ig], 1), 1)
    V = {"current 756 (30)": Q.X30}
    for nm, v in (("recency-weighted", yw), ("unweighted", yu)):
        X_ = Q.X30.copy(); X_[:, ig] = v; X_[:, ip] = v * pace; V[f"swap: {nm} margin rating"] = X_
        V[f"add: {nm} margin gap"] = np.column_stack([Q.X30, v])
def job(name):
    XX = V[name]; fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in ["First round","Second round","Sweet 16","Elite Eight","Final Four","Championship"]]
    return name, held, insr, auc, rr
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
        print("games cached; rerun"); sys.exit()
    print("missing:", int(np.isnan(yw).sum()))
    for nm, v in (("recency-weighted", yw), ("unweighted", yu)):
        print(f"{nm:17} corr with our rating gap {np.corrcoef(v[k], Q.X30[k, ig])[0,1]:.3f} | z on top of strength {zt(v):+.2f}")
    # alone: who picks more winners straight up, our rating or the margin rating (higher-rated team)
    for nm, v in (("our rating", Q.X30[:, ig]), ("recency-weighted", yw), ("unweighted", yu)):
        print(f"higher-rated team wins, {nm:17}: {int(((v[k] > 0) == Q.yb[k]).sum())} of {int(k.sum())}")
    with ProcessPoolExecutor(5) as ex:
        for name, held, insr, auc, rr in ex.map(job, V):
            print(f"{name:38} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
