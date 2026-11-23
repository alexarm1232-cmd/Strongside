# Andrew F's tree, rebuilt as his slides describe, on pre-tournament data only.
# Round of 64 games; response = higher seed won; predictors = higher seed minus lower seed for his variables (37 of his
# 38; travel distance not available). CART (Gini, 10-fold CV weakest-link pruning) and a 500-tree random forest
# (mtry = sqrt(p), mean decrease Gini). Test years as on his slides: 2016 + 2026, then 2017 + 2025 (his 2008 / 2009 are
# outside our data). Also every year held out in turn, and the 756 model on the same games.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m110_cart_rf as T
import m99_model_types as Q
import numpy as np
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m148_andrew_tot.json")
B = Q.R.B; G = B.G; TM = B.TM
CNT = ["pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "orb", "reb", "ast", "stl", "blk", "to", "pf"]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; Tt = {}; rows = []
    for g in games:
        if g["date"] >= first or g["home"] not in DI or g["away"] not in DI: continue
        rows.append((g["home"], g["away"], g["neutral"], g["hs"] - g["as_"]))
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = Tt.setdefault(t, {"n": 0, "w": 0, "opps": []}); r["n"] += 1; r["w"] += int(a["pts"] > b["pts"]); r["opps"].append(o)
            for kk in CNT: r[kk] = r.get(kk, 0) + float(a[kk] or 0); r["o_" + kk] = r.get("o_" + kk, 0) + float(b[kk] or 0)
    teams = sorted({t for r in rows for t in r[:2]}); ix = {t: i for i, t in enumerate(teams)}
    A = np.zeros((len(rows) + 1, len(teams) + 1)); yv = np.zeros(len(rows) + 1)
    for j, (h, a_, neu, m) in enumerate(rows): A[j, ix[h]] = 1; A[j, ix[a_]] = -1; A[j, -1] = 0 if neu else 1; yv[j] = m
    A[-1, :-1] = 1; sol = np.linalg.lstsq(A, yv, rcond=None)[0]
    for t, r in Tt.items(): r["srs"] = float(sol[ix[t]])
    return s, Tt
VARS = ["NetRtg", "FGA", "FG", "TRB", "SRS", "DRtg", "SOS", "NetRtg_SOS", "AdjTempo", "DRtg_SOS", "WL_Pct", "ORtg_SOS", "Luck", "AST", "PF", "ORB",
        "STL", "FT", "ORtg", "ThreeP_Pct", "TRB_Pct", "FTA", "FG_Pct", "TOV", "FTr", "BLK_Pct", "eFG_Pct", "ThreeP", "FT_Pct", "AST_Pct", "FT_per_FGA",
        "BLK", "TS_Pct", "TOV_Pct", "ThreePA", "ThreePAr", "Seed"]
def team_vars(s, t, seed, BX):
    r = BX[s].get(t) or BX[s].get(t + "."); tm = TM[s][t]
    if r is None: return None
    op = [TM[s].get(o) or TM[s].get(o.rstrip(".")) or TM[s].get(o + ".") for o in r["opps"]]; op = [x for x in op if x]
    pyth = r["pts"] ** 11.5 / (r["pts"] ** 11.5 + r["o_pts"] ** 11.5)
    v = dict(NetRtg=tm["adj_net"], ORtg=tm["adj_o"], DRtg=tm["adj_d"], SOS=tm["sos"], AdjTempo=tm["tempo"], WL_Pct=r["w"] / r["n"], SRS=r["srs"],
             Luck=r["w"] / r["n"] - pyth, NetRtg_SOS=np.mean([x["adj_net"] for x in op]), ORtg_SOS=np.mean([x["adj_o"] for x in op]), DRtg_SOS=np.mean([x["adj_d"] for x in op]),
             FGA=r["fga"], FG=r["fgm"], TRB=r["reb"], AST=r["ast"], PF=r["pf"], ORB=r["orb"], STL=r["stl"], FT=r["ftm"], FTA=r["fta"], TOV=r["to"], BLK=r["blk"],
             ThreeP=r["tpm"], ThreePA=r["tpa"], FG_Pct=r["fgm"] / r["fga"], ThreeP_Pct=r["tpm"] / max(r["tpa"], 1), FT_Pct=r["ftm"] / max(r["fta"], 1),
             eFG_Pct=(r["fgm"] + .5 * r["tpm"]) / r["fga"], TS_Pct=r["pts"] / (2 * (r["fga"] + .475 * r["fta"])), TRB_Pct=r["reb"] / max(r["reb"] + r["o_reb"], 1),
             AST_Pct=r["ast"] / max(r["fgm"], 1), BLK_Pct=r["blk"] / max(r["o_fga"] - r["o_tpa"], 1), TOV_Pct=r["to"] / (r["fga"] + .44 * r["fta"] + r["to"]),
             FTr=r["fta"] / r["fga"], FT_per_FGA=r["ftm"] / r["fga"], ThreePAr=r["tpa"] / r["fga"], Seed=seed)
    return [v[x] for x in VARS]
def setup():
    BX = json.load(open(CACHE)); rows, Xr, yr, sr, hi = [], [], [], [], []
    for i, g in enumerate(G):
        if g["rnd"] != "First round": continue
        s = g["season"]; a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        if sa == sb: continue
        H, L, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); hw = g["fav_won"] if H == a else not g["fav_won"]
        vh, vl = team_vars(s, H, sH, BX), team_vars(s, L, sL, BX)
        if vh is None or vl is None: continue
        rows.append(i); Xr.append(np.array(vh) - np.array(vl)); yr.append(int(hw)); sr.append(s); hi.append(H == B.Sname[i])
    return np.array(rows), np.array(Xr, float), np.array(yr), np.array(sr), np.array(hi)
def cart(X, y, tr, seed=0):
    rng = np.random.default_rng(seed); imp = np.zeros(X.shape[1]); full = T.grow(X, y, tr, 5, X.shape[1], rng, imp)
    seq = T.prune_seq(full); al = [a for a, _ in seq]
    cands = [math.sqrt(al[i] * al[i + 1]) if al[i] > 0 else al[i + 1] / 2 for i in range(len(al) - 1)] + [al[-1] + 1]
    folds = np.random.default_rng(seed).permutation(len(tr)) % 10; cv = np.zeros(len(cands))
    for f in range(10):
        a, b = tr[folds != f], tr[folds == f]; ft = T.grow(X, y, a, 5, X.shape[1], rng, np.zeros(X.shape[1]))
        for c, a_ in enumerate(cands): pt = T.prune_at(ft, a_); cv[c] += sum((T.predict(pt, X[i]) > 0.5) != y[i] for i in b)
    return T.prune_at(full, cands[int(np.argmin(cv))]), full
def forest(X, y, tr, ntree=500, seed=7):
    rng = np.random.default_rng(seed); imp = np.zeros(X.shape[1]); trees = []; os_ = np.zeros(len(y)); on = np.zeros(len(y)); m = int(math.sqrt(X.shape[1]))
    for _ in range(ntree):
        bs = tr[rng.integers(0, len(tr), len(tr))]; t = T.grow(X, y, bs, 1, m, rng, imp); trees.append(t)
        for i in np.setdiff1d(tr, bs): os_[i] += T.predict(t, X[i]); on[i] += 1
    return trees, imp / ntree, np.where(on > 0, os_ / np.maximum(on, 1), np.nan)
rfp = lambda trees, X, idx: np.array([np.mean([T.predict(t, X[i]) for t in trees]) for i in idx])
def show(node, depth=0, maxd=4, out=None):
    out = [] if out is None else out; pad = "  " * depth
    if "f" not in node or depth >= maxd: out.append(f"{pad}-> higher seed wins {node['p']:.0%} ({node['k']}/{node['n']})"); return out
    out.append(f"{pad}{VARS[node['f']]}_Diff <= {node['thr']:.3g}  [n={node['n']}, higher seed wins {node['p']:.0%}]")
    show(node["L"], depth + 1, maxd, out); out.append(f"{pad}{VARS[node['f']]}_Diff >  {node['thr']:.3g}"); show(node["R"], depth + 1, maxd, out); return out
def run_split(test):
    rows, X, y, sr, hi = setup(); te = np.where(np.isin(sr, test))[0]; tr = np.where(~np.isin(sr, test))[0]
    tree, full = cart(X, y, tr); trees, imp, oob = forest(X, y, tr)
    pc_tr = np.array([T.predict(tree, X[i]) for i in tr]); pc_te = np.array([T.predict(tree, X[i]) for i in te]); prf = rfp(trees, X, te)
    ok = ~np.isnan(oob[tr])
    res = dict(test=test, n_tr=len(tr), n_te=len(te), leaves=len(T.leaves(tree)), full_leaves=len(T.leaves(full)),
               cart_tr_auc=T.auc(pc_tr, y[tr]), cart_te_auc=T.auc(pc_te, y[te]), rf_oob_auc=T.auc(oob[tr][ok], y[tr][ok]), rf_te_auc=T.auc(prf, y[te]),
               cart_te_right=int(((pc_te > .5) == y[te]).sum()), rf_te_right=int(((prf > .5) == y[te]).sum()), seed_right=int(y[te].sum()),
               conf=[[int(((prf <= .5) & (y[te] == 0)).sum()), int(((prf <= .5) & (y[te] == 1)).sum())], [int(((prf > .5) & (y[te] == 0)).sum()), int(((prf > .5) & (y[te] == 1)).sum())]],
               tree=show(tree), imp=sorted(zip(VARS, imp), key=lambda x: -x[1]))
    return res
def loso_job(s):
    rows, X, y, sr, hi = setup(); te = np.where(sr == s)[0]; tr = np.where(sr != s)[0]
    tree, _ = cart(X, y, tr); trees, _, _ = forest(X, y, tr, ntree=300)
    return s, te.tolist(), [T.predict(tree, X[i]) for i in te], rfp(trees, X, te).tolist()
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
    rows, X, y, sr, hi = setup(); print(f"Round of 64 games: {len(y)}, higher seed won {y.mean():.1%}")
    # the 756 model, each tournament held out, on the same games (as 'higher seed wins' log-odds)
    k = ~Q.FF; fit = Q.t_ridge(); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    mod = np.where(hi, out[rows], -out[rows])
    with ProcessPoolExecutor(6) as ex:
        splits = list(ex.map(run_split, [["2015-16", "2025-26"], ["2016-17", "2024-25"]])); lo = list(ex.map(loso_job, sorted(set(sr))))
    json.dump(dict(splits=splits), open(os.path.join(HERE, "m148_out.json"), "w"), default=str)
    for r in splits:
        te = np.where(np.isin(sr, r["test"]))[0]
        print(f"\n=== test {r['test']} ({r['n_te']} games; trained on {r['n_tr']})")
        print(f"CART: {r['leaves']} leaves after pruning (full tree {r['full_leaves']}) | training AUC {r['cart_tr_auc']:.3f} | test AUC {r['cart_te_auc']:.3f} | test right {r['cart_te_right']}/{r['n_te']}")
        print(f"Random forest: OOB AUC {r['rf_oob_auc']:.3f} | test AUC {r['rf_te_auc']:.3f} | test right {r['rf_te_right']}/{r['n_te']} | confusion [[pred 0: {r['conf'][0]}], [pred 1: {r['conf'][1]}]]")
        print(f"Higher seed: {r['seed_right']}/{r['n_te']} | 756 model: {int(((mod[te] > 0) == y[te]).sum())}/{r['n_te']}, AUC {T.auc(mod[te], y[te]):.3f}")
        print("Tree (top 4 levels):"); print("\n".join(r["tree"]))
        print("RF importance top 12:", ", ".join(f"{a} {b:.2f}" for a, b in r["imp"][:12]))
    pc = np.zeros(len(y)); pr = np.zeros(len(y))
    for s, te, a, b in lo: pc[te] = a; pr[te] = b
    print(f"\n=== every year held out in turn ({len(y)} games)")
    print(f"CART {int(((pc > .5) == y).sum())} right, AUC {T.auc(pc, y):.3f} | RF {int(((pr > .5) == y).sum())} right, AUC {T.auc(pr, y):.3f} | 756 model {int(((mod > 0) == y).sum())} right, AUC {T.auc(mod, y):.3f} | higher seed {int(y.sum())}")
