# True shooting % vs eFG%. TS = pts / (2 * (FGA + 0.475 FTA)), offense and defense, from pre-tournament D-I games only,
# as a percentile among that season's D-I teams (like the other team measures). Tests: z on top of strength (TS and eFG
# side by side), add to the 756, and the four-factor net gap with TS in eFG's place.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m141_ts.json")
B = Q.R.B; G = B.G; X, KS = B.X, B.KS; k = ~Q.FF
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; T = {}
    for g in games:
        if g["date"] >= first or g["home"] not in DI or g["away"] not in DI: continue
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = T.setdefault(t, [0.0] * 8)
            for j, v in enumerate((a["pts"], a["fga"], a["fta"], a["fgm"] + 0.5 * a["tpm"], b["pts"], b["fga"], b["fta"], b["fgm"] + 0.5 * b["tpm"])): r[j] += float(v)
    return s, {t: dict(ts=r[0] / (2 * (r[1] + .475 * r[2])), d_ts=r[4] / (2 * (r[5] + .475 * r[6])), efg=r[3] / r[1], d_efg=r[7] / r[5]) for t, r in T.items() if r[1] > 0}
if os.path.exists(CACHE):
    TS = json.load(open(CACHE))
    def pct(s, t, key):
        arr = np.sort([v[key] for v in TS[s].values()]); x = (TS[s].get(t) or TS[s].get(t + ".") or {}).get(key)
        return np.nan if x is None else float(np.searchsorted(arr, x, side="right") / len(arr))
    col = lambda key, side: np.array([pct(g["season"], B.Sname[i] if side == "S" else Wn[i], key) for i, g in enumerate(G)])
    F = {f"{sd} {kk}": col(kk, sd) for sd in "SW" for kk in ("ts", "d_ts", "efg", "d_efg")}
    for v in F.values(): v[np.isnan(v)] = 0.5
    c = lambda kk: X[:, KS.index(kk)]
    def off(t, shoot): return .40 * shoot - .25 * c(t + " tov") + .20 * c(t + " orb") + .15 * c(t + " ftr")
    def dfn(t, dshoot): return -.40 * dshoot + .25 * c(t + " d_tov") - .20 * c(t + " d_orb") - .15 * c(t + " d_ftr")
    net_efg = (off("S", c("S efg")) + dfn("S", c("S d_efg"))) - (off("W", c("W efg")) + dfn("W", c("W d_efg")))
    net_ts = (off("S", F["S ts"]) + dfn("S", F["S d_ts"])) - (off("W", F["W ts"]) + dfn("W", F["W d_ts"]))
    V = {"current 756 (30)": None,
         "+ true shooting (S, W off/def)": np.column_stack([F["S ts"], F["S d_ts"], F["W ts"], F["W d_ts"]]),
         "+ eFG (S, W off/def)": np.column_stack([c("S efg"), c("S d_efg"), c("W efg"), c("W d_efg")]),
         "+ four-factor net gap, eFG": net_efg[:, None], "+ four-factor net gap, true shooting": net_ts[:, None]}
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
def job(name):
    XX = Q.X30 if V[name] is None else np.column_stack([Q.X30, V[name]]); fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    return name, held, insr, auc
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
        print("cached; rerun"); sys.exit()
    names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]; gap = Q.X30[:, names.index("gap")]
    print("check: my eFG percentile vs the pool's eFG, corr", round(float(np.corrcoef(F["S efg"][k], c("S efg")[k])[0, 1]), 3))
    for sd in "SW":
        for a, b in (("ts", "efg"), ("d_ts", "d_efg")):
            print(f"{sd} {a:5} z {zt(F[f'{sd} {a}']):+.2f} (corr w/ rating gap {np.corrcoef(F[f'{sd} {a}'][k], gap[k])[0,1]:+.2f})  |  {sd} {b:6} z {zt(c(f'{sd} {b}')):+.2f}")
    print(f"four-factor net gap  eFG z {zt(net_efg):+.2f} | TS z {zt(net_ts):+.2f}")
    with ProcessPoolExecutor(5) as ex:
        for name, held, insr, auc in ex.map(job, V):
            print(f"{name:40} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f}", flush=True)
