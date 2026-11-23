# Full-season adjusted ratings (same method as study_build: opponent-adjusted points per 100, home 1.4, 30 iterations),
# computed on ALL games incl. the tournament, plus the same on pre-tournament games as a check against our ratings.
# Then rerun the end-of-season variable importance with full-season NetRtg / ORtg / DRtg / SOS / tempo / opponent ratings.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m148_andrew_tree as A
import m150_imp_full_vs_pre as F
import numpy as np
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m151_ratings.json")
Q = A.Q; T = A.T
poss = lambda a: a["fga"] - a["orb"] + a["to"] + 0.475 * a["fta"]
def ratings(games):
    teams = sorted({t for g in games for t in (g["home"], g["away"])}); ix = {t: i for i, t in enumerate(teams)}; n = len(teams); rows = []; P_ = np.zeros(n); G_ = np.zeros(n)
    for g in games:
        for t, u in ((g["home"], g["away"]), (g["away"], g["home"])):
            P = (poss(g["side"][t]) + poss(g["side"][u])) / 2
            if P < 40: continue
            site = 0 if g["neutral"] else (1.4 if t == g["home"] else -1.4)
            rows.append((ix[t], ix[u], 100 * g["side"][t]["pts"] / P - site, 100 * g["side"][u]["pts"] / P + site)); P_[ix[t]] += P; G_[ix[t]] += 1
    Tt = np.array([r[0] for r in rows]); U = np.array([r[1] for r in rows]); O = np.array([r[2] for r in rows]); D = np.array([r[3] for r in rows])
    cnt = np.bincount(Tt, minlength=n); avg = O.mean(); ao = np.full(n, avg); ad = np.full(n, avg)
    for _ in range(30):
        ao = np.bincount(Tt, O - (ad[U] - avg), minlength=n) / np.maximum(cnt, 1); ad = np.bincount(Tt, D - (ao[U] - avg), minlength=n) / np.maximum(cnt, 1)
    net = ao - ad; sos = np.bincount(Tt, net[U], minlength=n) / np.maximum(cnt, 1)
    return {t: dict(adj_o=float(ao[i]), adj_d=float(ad[i]), adj_net=float(net[i]), sos=float(sos[i]), tempo=float(P_[i] / max(G_[i], 1))) for t, i in ix.items() if cnt[i] >= 8}
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); DI = set(td) | {t.rstrip(".") for t in td}
    games = [g for g in games if g["home"] in DI and g["away"] in DI and g["hs"] is not None]
    first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    return s, {"full": ratings(games), "pre": ratings([g for g in games if g["date"] < first])}
def team_vars_full(s, t, seed, BX, RT):
    r = BX[s].get(t) or BX[s].get(t + "."); tm = RT[s].get(t) or RT[s].get(t + ".") or RT[s].get(t.rstrip("."))
    if r is None or tm is None: return None
    op = [RT[s].get(o) or RT[s].get(o.rstrip(".")) or RT[s].get(o + ".") for o in r["opps"]]; op = [x for x in op if x]
    pyth = r["pts"] ** 11.5 / (r["pts"] ** 11.5 + r["o_pts"] ** 11.5)
    v = dict(NetRtg=tm["adj_net"], ORtg=tm["adj_o"], DRtg=tm["adj_d"], SOS=tm["sos"], AdjTempo=tm["tempo"], WL_Pct=r["w"] / r["n"], SRS=r["srs"],
             Luck=r["w"] / r["n"] - pyth, NetRtg_SOS=np.mean([x["adj_net"] for x in op]), ORtg_SOS=np.mean([x["adj_o"] for x in op]), DRtg_SOS=np.mean([x["adj_d"] for x in op]),
             FGA=r["fga"], FG=r["fgm"], TRB=r["reb"], AST=r["ast"], PF=r["pf"], ORB=r["orb"], STL=r["stl"], FT=r["ftm"], FTA=r["fta"], TOV=r["to"], BLK=r["blk"],
             ThreeP=r["tpm"], ThreePA=r["tpa"], FG_Pct=r["fgm"] / r["fga"], ThreeP_Pct=r["tpm"] / max(r["tpa"], 1), FT_Pct=r["ftm"] / max(r["fta"], 1),
             eFG_Pct=(r["fgm"] + .5 * r["tpm"]) / r["fga"], TS_Pct=r["pts"] / (2 * (r["fga"] + .475 * r["fta"])), TRB_Pct=r["reb"] / max(r["reb"] + r["o_reb"], 1),
             AST_Pct=r["ast"] / max(r["fgm"], 1), BLK_Pct=r["blk"] / max(r["o_fga"] - r["o_tpa"], 1), TOV_Pct=r["to"] / (r["fga"] + .44 * r["fta"] + r["to"]),
             FTr=r["fta"] / r["fga"], FT_per_FGA=r["ftm"] / r["fga"], ThreePAr=r["tpa"] / r["fga"], Seed=seed)
    return [v[x] for x in A.VARS]
def job(which):
    RT = {s: d[which] for s, d in json.load(open(CACHE)).items()}
    BX = json.load(open(F.CACHE if which == "full" else A.CACHE)); Xr, yr = [], []
    for g in A.G:
        if g["rnd"] != "First round" or g["fseed"] == g["dseed"]: continue
        a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        H, L, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); hw = g["fav_won"] if H == a else not g["fav_won"]
        vh, vl = team_vars_full(g["season"], H, sH, BX, RT), team_vars_full(g["season"], L, sL, BX, RT)
        if vh is None or vl is None: continue
        Xr.append(np.array(vh) - np.array(vl)); yr.append(int(hw))
    X, y = np.array(Xr, float), np.array(yr); idx = np.arange(len(y)); imps, oobs = [], []
    for seed in (7, 11, 23):
        _, imp, oob = A.forest(X, y, idx, ntree=500, seed=seed); imps.append(imp); oobs.append(oob)
    oob = np.nanmean(oobs, 0); ok = ~np.isnan(oob)
    return which, len(y), np.mean(imps, 0).tolist(), T.auc(oob[ok], y[ok]), {v: T.auc(X[:, j], y) for j, v in enumerate(A.VARS)}
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in A.G}))), open(CACHE, "w"))
    RTall = json.load(open(CACHE)); a, b, c = [], [], []
    for s, d in RTall.items():
        for t, v in A.TM[s].items():
            x = d["pre"].get(t) or d["pre"].get(t + ".") or d["pre"].get(t.rstrip("."))
            if x: a.append(v["adj_net"]); b.append(x["adj_net"])
    print(f"check: recomputed pre-tournament net vs our ratings: corr {np.corrcoef(a, b)[0,1]:.4f}, mean abs diff {np.mean(np.abs(np.array(a) - np.array(b))):.3f}")
    m = RTall["2025-26"]["full"]; p = RTall["2025-26"]["pre"]
    for t in ("Michigan", "Duke", "Arizona"): print(f"2025-26 {t}: pre net {p[t]['adj_net']:+.2f} -> full-season net {m[t]['adj_net']:+.2f}")
    with ProcessPoolExecutor(2) as ex: R = {w: r for w, *r in ex.map(job, ["full", "pre"])}
    old = json.load(open(os.path.join(HERE, "m150_out.json")))
    nF, iF, oF, sF = R["full"]; nP, iP, oP, sP = R["pre"]; iO = old["full"][1]
    rk = lambda imp: {v: r for r, (v, _) in enumerate(sorted(zip(A.VARS, imp), key=lambda x: -x[1]), 1)}
    rF, rP, rO = rk(iF), rk(iP), rk(iO)
    his = "NetRtg FGA FG TRB SRS DRtg SOS NetRtg_SOS AdjTempo DRtg_SOS WL_Pct ORtg_SOS Luck AST PF ORB STL FT ORtg ThreeP_Pct TRB_Pct FTA FG_Pct TOV FTr BLK_Pct eFG_Pct ThreeP FT_Pct AST_Pct FT_per_FGA BLK TS_Pct TOV_Pct Distance ThreePA ThreePAr Seed".split()
    print(f"\ngames {nF} | forest OOB AUC: full season (ratings full too) {oF:.3f} | pre-tournament {oP:.3f}")
    print(f"{'variable':12} {'FULL imp':>8} {'rank':>4} {'AUC':>6} | {'PRE imp':>7} {'rank':>4} {'AUC':>6} | last run rank | Andrew")
    for v in sorted(A.VARS, key=lambda v: rF[v]):
        j = A.VARS.index(v); print(f"{v:12} {iF[j]:8.2f} {rF[v]:4d} {sF[v]:6.3f} | {iP[j]:7.2f} {rP[v]:4d} {sP[v]:6.3f} | {rO[v]:4d} | {his.index(v) + 1}")
