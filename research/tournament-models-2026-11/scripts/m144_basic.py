# Basic stats in the model: seed, points per game, points allowed per game, scoring margin, win %, FG%, 3P%, FT%,
# rebounds, assists, turnovers, steals, blocks per game. Pre-tournament D-I games only; each as a percentile among that
# season's D-I teams for S and W. z on top of strength, then added to the exact 756 pipeline in a few packages.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m144_basic.json")
B = Q.R.B; G = B.G; k = ~Q.FF
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
KEYS = ["ppg", "papg", "margin", "win_pct", "fg_pct", "fg3_pct", "ft_pct", "rpg", "apg", "topg", "spg", "bpg", "opp_fg_pct"]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; T = {}
    for g in games:
        if g["date"] >= first or g["home"] not in DI or g["away"] not in DI: continue
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = T.setdefault(t, {})
            r["n"] = r.get("n", 0) + 1; r["w"] = r.get("w", 0) + (a["pts"] > b["pts"])
            for kk in ("pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "reb", "ast", "to", "stl", "blk"): r[kk] = r.get(kk, 0) + float(a[kk] or 0)
            r["opts"] = r.get("opts", 0) + float(b["pts"]); r["ofgm"] = r.get("ofgm", 0) + float(b["fgm"]); r["ofga"] = r.get("ofga", 0) + float(b["fga"])
    out = {}
    for t, r in T.items():
        n = r["n"]
        if n < 10 or r["fga"] <= 0: continue
        out[t] = dict(ppg=r["pts"] / n, papg=r["opts"] / n, margin=(r["pts"] - r["opts"]) / n, win_pct=r["w"] / n, fg_pct=r["fgm"] / r["fga"],
                      fg3_pct=r["tpm"] / max(r["tpa"], 1), ft_pct=r["ftm"] / max(r["fta"], 1), rpg=r["reb"] / n, apg=r["ast"] / n, topg=r["to"] / n,
                      spg=r["stl"] / n, bpg=r["blk"] / n, opp_fg_pct=r["ofgm"] / max(r["ofga"], 1))
    return s, out
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
if os.path.exists(CACHE):
    BS = json.load(open(CACHE))
    def pct(s, t, key):
        arr = np.sort([v[key] for v in BS[s].values()]); x = (BS[s].get(t) or BS[s].get(t + ".") or {}).get(key)
        return np.nan if x is None else float(np.searchsorted(arr, x, side="right") / len(arr))
    F = {}
    for kk in KEYS:
        for sd in "SW":
            v = np.array([pct(g["season"], B.Sname[i] if sd == "S" else Wn[i], kk) for i, g in enumerate(G)]); v[np.isnan(v)] = 0.5; F[f"{sd} {kk}"] = v
    F["S seed"], F["W seed"] = np.array(B.sS, float), np.array(B.sW, float)
    both = lambda ks: [f"{sd} {kk}" for kk in ks for sd in "SW"]
    V = {"current 756 (30)": None,
         "+ seed, PPG, points allowed (both teams)": both(["seed", "ppg", "papg"]),
         "+ seed, PPG, points allowed, margin, win %": both(["seed", "ppg", "papg", "margin", "win_pct"]),
         "+ all basics (14 per team, 28)": both(["seed"] + KEYS),
         "+ basic gaps (S - W, 14)": None}
    GAPS = np.column_stack([F[f"S {kk}"] - F[f"W {kk}"] for kk in ["seed"] + KEYS])
def job(name):
    if name == "+ basic gaps (S - W, 14)": XX = np.column_stack([Q.X30, GAPS])
    else: XX = Q.X30 if V[name] is None else np.column_stack([Q.X30] + [F[f] for f in V[name]])
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
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
        print("cached; rerun"); sys.exit()
    names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]; gap = Q.X30[:, names.index("gap")]
    for kk in ["seed"] + KEYS:
        print(f"{kk:11} z on top of strength: S {zt(F['S ' + kk]):+.2f}  W {zt(F['W ' + kk]):+.2f}  gap {zt(F['S ' + kk] - F['W ' + kk]):+.2f}  | corr of gap with rating gap {np.corrcoef((F['S ' + kk] - F['W ' + kk])[k], gap[k])[0,1]:+.2f}")
    with ProcessPoolExecutor(5) as ex:
        for name, held, insr, auc, rr in ex.map(job, V):
            print(f"{name:44} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
