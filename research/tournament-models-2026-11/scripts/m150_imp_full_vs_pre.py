# Variable importance of Andrew's 37 variables, all years (511 R64 games, 2010-2026), random forest 500 trees:
# (1) end-of-season box-score stats (all games incl. the NCAA tournament, like a season page pulled after March)
# (2) pre-tournament only. SRS, luck, win %, opponent averages and all counts/rates are rebuilt each way.
# NetRtg / ORtg / DRtg / SOS / tempo come from our pre-tournament adjusted ratings in both (no post-tournament version).
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m148_andrew_tree as A
import numpy as np
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m150_full.json")
Q = A.Q; T = A.T
def _load_full(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); DI = set(td) | {t.rstrip(".") for t in td}; Tt = {}; rows = []
    for g in games:
        if g["home"] not in DI or g["away"] not in DI: continue
        rows.append((g["home"], g["away"], g["neutral"], g["hs"] - g["as_"]))
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = Tt.setdefault(t, {"n": 0, "w": 0, "opps": []}); r["n"] += 1; r["w"] += int(a["pts"] > b["pts"]); r["opps"].append(o)
            for kk in A.CNT: r[kk] = r.get(kk, 0) + float(a[kk] or 0); r["o_" + kk] = r.get("o_" + kk, 0) + float(b[kk] or 0)
    teams = sorted({t for r in rows for t in r[:2]}); ix = {t: i for i, t in enumerate(teams)}
    M = np.zeros((len(rows) + 1, len(teams) + 1)); yv = np.zeros(len(rows) + 1)
    for j, (h, a_, neu, m) in enumerate(rows): M[j, ix[h]] = 1; M[j, ix[a_]] = -1; M[j, -1] = 0 if neu else 1; yv[j] = m
    M[-1, :-1] = 1; sol = np.linalg.lstsq(M, yv, rcond=None)[0]
    for t, r in Tt.items(): r["srs"] = float(sol[ix[t]])
    return s, Tt
def build(BX):
    G = A.G; B = A.B; Xr, yr = [], []
    for i, g in enumerate(G):
        if g["rnd"] != "First round" or g["fseed"] == g["dseed"]: continue
        a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        H, L, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); hw = g["fav_won"] if H == a else not g["fav_won"]
        vh, vl = A.team_vars(g["season"], H, sH, BX), A.team_vars(g["season"], L, sL, BX)
        if vh is None or vl is None: continue
        Xr.append(np.array(vh) - np.array(vl)); yr.append(int(hw))
    return np.array(Xr, float), np.array(yr)
def job(which):
    BX = json.load(open(A.CACHE if which == "pre" else CACHE)); X, y = build(BX); idx = np.arange(len(y))
    imps = []; oob_all = []
    for seed in (7, 11, 23):                       # 3 forests of 500, averaged, so close ranks are steadier
        trees, imp, oob = A.forest(X, y, idx, ntree=500, seed=seed); imps.append(imp); oob_all.append(oob)
    imp = np.mean(imps, 0); oob = np.nanmean(oob_all, 0); ok = ~np.isnan(oob)
    single = {v: T.auc(X[:, j], y) for j, v in enumerate(A.VARS)}
    return which, len(y), imp.tolist(), T.auc(oob[ok], y[ok]), single
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load_full, sorted({g["season"] for g in A.G}))), open(CACHE, "w"))
    with ProcessPoolExecutor(2) as ex: R = {w: (n, imp, oob, single) for w, n, imp, oob, single in ex.map(job, ["full", "pre"])}
    json.dump(R, open(os.path.join(HERE, "m150_out.json"), "w"))
    nF, iF, oF, sF = R["full"]; nP, iP, oP, sP = R["pre"]
    rF = {v: r for r, (v, _) in enumerate(sorted(zip(A.VARS, iF), key=lambda x: -x[1]), 1)}
    rP = {v: r for r, (v, _) in enumerate(sorted(zip(A.VARS, iP), key=lambda x: -x[1]), 1)}
    print(f"games {nF} | forest OOB AUC: end-of-season {oF:.3f} | pre-tournament {oP:.3f}")
    print(f"{'variable':12} {'end-of-season':>14} {'rank':>5} {'AUC alone':>9}   {'pre-tourney':>11} {'rank':>5} {'AUC alone':>9}   Andrew rank")
    his = "NetRtg FGA FG TRB SRS DRtg SOS NetRtg_SOS AdjTempo DRtg_SOS WL_Pct ORtg_SOS Luck AST PF ORB STL FT ORtg ThreeP_Pct TRB_Pct FTA FG_Pct TOV FTr BLK_Pct eFG_Pct ThreeP FT_Pct AST_Pct FT_per_FGA BLK TS_Pct TOV_Pct Distance ThreePA ThreePAr Seed".split()
    for v in sorted(A.VARS, key=lambda v: rF[v]):
        j = A.VARS.index(v)
        print(f"{v:12} {iF[j]:14.2f} {rF[v]:5d} {sF[v]:9.3f}   {iP[j]:11.2f} {rP[v]:5d} {sP[v]:9.3f}   {his.index(v) + 1}")
