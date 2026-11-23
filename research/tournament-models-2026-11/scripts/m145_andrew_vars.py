# Andrew F's variables we haven't tested, built from pre-tournament D-I box scores: FGA and FGM (season totals and per
# game), fouls, FTM, 3PM, 3PA per game, total rebound %, assist % (AST/FGM), block % (BLK / opp 2PA), FT made per FGA,
# Luck (win % minus Pythagorean win % from points, exp 11.5), SRS (least-squares margin rating = margin adjusted for
# schedule), opponents' average offense and defense rating (ORtg_SOS, DRtg_SOS from our adjusted ratings).
# z on top of strength for S, W and the gap (Andrew used gaps), then anything significant goes into the 756.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m145_andrew.json")
B = Q.R.B; G = B.G; TM = B.TM; k = ~Q.FF
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
KEYS = ["fga_total", "fgm_total", "fga_pg", "fgm_pg", "pf_pg", "ftm_pg", "tpm_pg", "tpa_pg", "trb_pct", "ast_pct", "blk_pct", "ft_per_fga", "luck", "srs", "opp_ortg", "opp_drtg"]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; T = {}; rows = []; opps = {}
    for g in games:
        if g["date"] >= first or g["home"] not in DI or g["away"] not in DI: continue
        rows.append((g["home"], g["away"], g["neutral"], g["hs"] - g["as_"]))
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = T.setdefault(t, {}); opps.setdefault(t, []).append(o)
            r["n"] = r.get("n", 0) + 1; r["w"] = r.get("w", 0) + (a["pts"] > b["pts"])
            for kk in ("pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "reb", "ast", "blk", "pf"): r[kk] = r.get(kk, 0) + float(a[kk] or 0)
            r["oreb"] = r.get("oreb", 0) + float(b["reb"] or 0); r["opts"] = r.get("opts", 0) + float(b["pts"]); r["o2pa"] = r.get("o2pa", 0) + float(b["fga"] - b["tpa"])
    teams = sorted({t for r in rows for t in r[:2]}); ix = {t: i for i, t in enumerate(teams)}
    A = np.zeros((len(rows) + 1, len(teams) + 1)); y = np.zeros(len(rows) + 1)
    for j, (h, a_, neu, m) in enumerate(rows): A[j, ix[h]] = 1; A[j, ix[a_]] = -1; A[j, -1] = 0 if neu else 1; y[j] = m
    A[-1, :-1] = 1; sol = np.linalg.lstsq(A, y, rcond=None)[0]
    out = {}
    for t, r in T.items():
        n = r["n"]
        if n < 10 or r["fga"] <= 0: continue
        pyth = r["pts"] ** 11.5 / (r["pts"] ** 11.5 + r["opts"] ** 11.5)
        out[t] = dict(fga_total=r["fga"], fgm_total=r["fgm"], fga_pg=r["fga"] / n, fgm_pg=r["fgm"] / n, pf_pg=r["pf"] / n, ftm_pg=r["ftm"] / n,
                      tpm_pg=r["tpm"] / n, tpa_pg=r["tpa"] / n, trb_pct=r["reb"] / max(r["reb"] + r["oreb"], 1), ast_pct=r["ast"] / max(r["fgm"], 1),
                      blk_pct=r["blk"] / max(r["o2pa"], 1), ft_per_fga=r["ftm"] / r["fga"], luck=r["w"] / n - pyth, srs=float(sol[ix[t]]) if t in ix else 0.0,
                      opps=opps[t])
    return s, out
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
if os.path.exists(CACHE):
    AS = json.load(open(CACHE))
    for s, d in AS.items():          # opponents' average adjusted offense / defense (our ratings)
        for t, v in d.items():
            os_ = [TM[s].get(o) or TM[s].get(o + ".") or TM[s].get(o.rstrip(".")) for o in v["opps"]]; os_ = [x for x in os_ if x]
            v["opp_ortg"] = float(np.mean([x["adj_o"] for x in os_])) if os_ else np.nan; v["opp_drtg"] = float(np.mean([x["adj_d"] for x in os_])) if os_ else np.nan
    def pct(s, t, key):
        arr = np.sort([v[key] for v in AS[s].values() if v.get(key) == v.get(key)]); x = (AS[s].get(t) or AS[s].get(t + ".") or {}).get(key)
        return np.nan if x is None or x != x else float(np.searchsorted(arr, x, side="right") / len(arr))
    F = {}
    for kk in KEYS:
        for sd in "SW":
            v = np.array([pct(g["season"], B.Sname[i] if sd == "S" else Wn[i], kk) for i, g in enumerate(G)]); v[np.isnan(v)] = 0.5; F[f"{sd} {kk}"] = v
def job(args):
    name, cols = args; XX = Q.X30 if cols is None else np.column_stack([Q.X30] + [F[f] if isinstance(f, str) else f for f in cols])
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
    from concurrent.futures import ProcessPoolExecutor
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
        print("cached; rerun"); sys.exit()
    names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]; gap = Q.X30[:, names.index("gap")]
    sig = []
    for kk in KEYS:
        zs = {"S": zt(F["S " + kk]), "W": zt(F["W " + kk]), "gap": zt(F["S " + kk] - F["W " + kk])}
        print(f"{kk:11} z: S {zs['S']:+.2f}  W {zs['W']:+.2f}  gap {zs['gap']:+.2f}  | gap corr with rating gap {np.corrcoef((F['S ' + kk] - F['W ' + kk])[k], gap[k])[0,1]:+.2f}")
        for nm, z in zs.items():
            if abs(z) >= 2: sig.append((kk, nm, z))
    print("significant (|z| >= 2):", sig)
    jobs = [("current 756 (30)", None)]
    for kk, nm, z in sig:
        jobs.append((f"+ {nm} {kk}", [F["S " + kk] - F["W " + kk]] if nm == "gap" else [f"{nm} {kk}"]))
    if len(sig) > 1: jobs.append(("+ all significant together", [F["S " + kk] - F["W " + kk] if nm == "gap" else F[f"{nm} {kk}"] for kk, nm, z in sig]))
    jobs.append(("+ all 16 Andrew gaps", [F["S " + kk] - F["W " + kk] for kk in KEYS]))
    with ProcessPoolExecutor(6) as ex:
        for name, held, insr, auc in ex.map(job, jobs):
            print(f"{name:32} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f}", flush=True)
