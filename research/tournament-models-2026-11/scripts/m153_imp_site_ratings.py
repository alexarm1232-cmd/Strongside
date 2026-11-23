# Variable importance with the PUBLISHED site's ratings: NetRtg / ORtg / DRtg / tempo / SOS from the site (pre-tournament
# page vs full-season page); opponent averages from the same site ratings; box-score stats pre vs full as before.
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m151_imp_full_ratings as M
import numpy as np
from concurrent.futures import ProcessPoolExecutor
A, T = M.A, M.T; HERE = os.path.dirname(os.path.abspath(__file__))
SITE = json.load(open(os.path.join(HERE, "m152_site_ratings.json")))
norm = lambda n: re.sub(r"[^a-z0-9]", "", n.lower().replace("&amp;", "&").replace("saint", "st").replace("state", "st"))
def site_rt(which):
    RT = {}
    for s, d in SITE.items():
        dd = {}
        for nm, v in d[which].items():
            if v["n"] is None: continue
            e = dict(adj_net=v["n"], adj_o=v["o"], adj_d=v["d"], tempo=v["t"], sos=v["sos"]); dd[nm] = e; dd[norm(nm)] = e
        RT[s] = dd
    return RT
class Look(dict):
    def get(self, k, default=None):
        return dict.get(self, k) or dict.get(self, norm(k)) or default
def job(which):
    RT = {s: Look(d) for s, d in site_rt(which).items()}
    BX = json.load(open(M.F.CACHE if which == "full" else A.CACHE)); Xr, yr, miss = [], [], 0
    for g in A.G:
        if g["rnd"] != "First round" or g["fseed"] == g["dseed"]: continue
        a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        H, L, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); hw = g["fav_won"] if H == a else not g["fav_won"]
        vh, vl = M.team_vars_full(g["season"], H, sH, BX, RT), M.team_vars_full(g["season"], L, sL, BX, RT)
        if vh is None or vl is None: miss += 1; continue
        Xr.append(np.array(vh) - np.array(vl)); yr.append(int(hw))
    X, y = np.array(Xr, float), np.array(yr); idx = np.arange(len(y)); imps, oobs = [], []
    for seed in (7, 11, 23):
        _, imp, oob = A.forest(X, y, idx, ntree=500, seed=seed); imps.append(imp); oobs.append(oob)
    oob = np.nanmean(oobs, 0); ok = ~np.isnan(oob)
    return which, len(y), miss, np.mean(imps, 0).tolist(), T.auc(oob[ok], y[ok]), {v: T.auc(X[:, j], y) for j, v in enumerate(A.VARS)}
if __name__ == "__main__":
    with ProcessPoolExecutor(2) as ex: R = {w: r for w, *r in ex.map(job, ["full", "pre"])}
    json.dump(R, open(os.path.join(HERE, "m153_out.json"), "w"))
    nF, mF, iF, oF, sF = R["full"]; nP, mP, iP, oP, sP = R["pre"]
    rk = lambda imp: {v: r for r, (v, _) in enumerate(sorted(zip(A.VARS, imp), key=lambda x: -x[1]), 1)}
    rF, rP = rk(iF), rk(iP)
    his = "NetRtg FGA FG TRB SRS DRtg SOS NetRtg_SOS AdjTempo DRtg_SOS WL_Pct ORtg_SOS Luck AST PF ORB STL FT ORtg ThreeP_Pct TRB_Pct FTA FG_Pct TOV FTr BLK_Pct eFG_Pct ThreeP FT_Pct AST_Pct FT_per_FGA BLK TS_Pct TOV_Pct Distance ThreePA ThreePAr Seed".split()
    print(f"games full {nF} (missing {mF}) pre {nP} (missing {mP}) | forest OOB AUC: full season {oF:.3f} | pre-tournament {oP:.3f}")
    print(f"{'variable':12} {'FULL imp':>8} {'rank':>4} {'AUC':>6} | {'PRE imp':>7} {'rank':>4} {'AUC':>6} | Andrew")
    for v in sorted(A.VARS, key=lambda v: rF[v]):
        j = A.VARS.index(v); print(f"{v:12} {iF[j]:8.2f} {rF[v]:4d} {sF[v]:6.3f} | {iP[j]:7.2f} {rP[v]:4d} {sP[v]:6.3f} | {his.index(v) + 1}")
