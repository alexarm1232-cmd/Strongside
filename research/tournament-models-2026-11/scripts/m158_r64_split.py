# Round of 64 study (the user's 5 steps):
#  1) Round of 64 only.  2) one row per game, higher seed (HS) vs lower seed (LS); HSW = 1 if the higher seed won.
#  3) CSV of PRE-TOURNAMENT data only: published-site pre-tournament ratings (net, offense, defense, tempo, SOS, W-L,
#     conference) + box-score per-game basics from regular season + conference tournament games (before the first NCAA
#     game, First Four included in the cutoff).  4) test = 2016 + 2026, train = the other years.
#  5) the user's model (same 30 inputs, ridge logistic lam 30, half-life 12, base held out inside training, round-1 line with
#     who plays + coach/star) refit on Round of 64 games only; training and testing AUC on HSW.
import os, sys, json, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
B = Q.R.B; G = B.G
SITE = json.load(open(os.path.join(HERE, "m152_site_ratings.json")))
BX = json.load(open(os.path.join(HERE, "m148_andrew_tot.json")))          # pre-tournament box totals (date < first NCAA game)
norm = lambda n: re.sub(r"[^a-z0-9]", "", n.lower().replace("&amp;", "&").replace("saint", "st").replace("state", "st"))
def site(s, t):
    d = SITE[s]["pre"]; return d.get(t) or next((v for k, v in d.items() if norm(k) == norm(t)), None)
def box(s, t): return BX[s].get(t) or BX[s].get(t + ".") or BX[s].get(t.rstrip("."))
def team_cols(s, t):
    r, b = site(s, t), box(s, t); n = b["n"]
    return {"Conf": r["conf"], "W": int(r["w"]), "L": int(r["l"]), "WinPct": round(r["w"] / (r["w"] + r["l"]), 4),
            "NetRtg": r["n"], "ORtg": r["o"], "DRtg": r["d"], "Tempo": r["t"], "SOS_Net": r["sos"], "SOS_ORtg": r["sos_o"], "SOS_DRtg": r["sos_d"],
            "G_box": n, "PPG": round(b["pts"] / n, 2), "OppPPG": round(b["o_pts"] / n, 2), "Margin": round((b["pts"] - b["o_pts"]) / n, 2),
            "FGM": round(b["fgm"] / n, 2), "FGA": round(b["fga"] / n, 2), "FG_Pct": round(b["fgm"] / b["fga"], 4),
            "3PM": round(b["tpm"] / n, 2), "3PA": round(b["tpa"] / n, 2), "3P_Pct": round(b["tpm"] / max(b["tpa"], 1), 4),
            "FTM": round(b["ftm"] / n, 2), "FTA": round(b["fta"] / n, 2), "FT_Pct": round(b["ftm"] / max(b["fta"], 1), 4),
            "ORB": round(b["orb"] / n, 2), "TRB": round(b["reb"] / n, 2), "AST": round(b["ast"] / n, 2), "STL": round(b["stl"] / n, 2),
            "BLK": round(b["blk"] / n, 2), "TOV": round(b["to"] / n, 2), "PF": round(b["pf"] / n, 2)}
TEST = os.environ.get("TEST", "2015-16,2025-26").split(",")
rows, gidx, hs_is_S, hsw, seas_r = [], [], [], [], []
for i, g in enumerate(G):
    if g["rnd"] != "First round": continue
    a, b_ = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
    H, L, sH, sL = (a, b_, sa, sb) if sa < sb else (b_, a, sb, sa); y = int(g["fav_won"] if H == a else not g["fav_won"])
    hc, lc = team_cols(g["season"], H), team_cols(g["season"], L)
    row = {"Year": int("20" + g["season"][-2:]), "Season": g["season"], "Split": "Test" if g["season"] in TEST else "Train", "Round": "Round of 64",
           "Date": g["date"].replace("/", "-"), "HS_Team": H, "HS_Seed": sH, "LS_Team": L, "LS_Seed": sL, "Seed_Diff": sH - sL, "HSW": y}
    for k, v in hc.items(): row["HS_" + k] = v
    for k, v in lc.items(): row["LS_" + k] = v
    for k, v in hc.items():
        if k != "Conf": row["Diff_" + k] = round(v - lc[k], 4)
    rows.append(row); gidx.append(i); hs_is_S.append(H == B.Sname[i]); hsw.append(y); seas_r.append(g["season"])
gidx, hs_is_S, hsw, seas_r = np.array(gidx), np.array(hs_is_S), np.array(hsw), np.array(seas_r)
# ---- step 5: the user's model on Round of 64 only
def auc(sc, y):
    o = np.argsort(sc); rk = np.empty(len(sc)); rk[o] = np.arange(1, len(sc) + 1); n1 = y.sum(); return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
tr = gidx[~np.isin(seas_r, TEST)]; te = gidx[np.isin(seas_r, TEST)]
fit = Q.t_ridge()
m_tr, m_te = Q.base(tr, te, fit); p_te = Q.run(m_tr, tr, m_te, te, Q.EX)          # test: trained on the other years' R64 games
m_tr2, m_in = Q.base(tr, tr, fit); p_tr = Q.run(m_tr2, tr, m_in, tr, Q.EX)          # training: the fitted model scored on its own games
toHS = lambda p, idx: np.where(hs_is_S[np.searchsorted(gidx, idx)], p, -p)
yt, ye = hsw[~np.isin(seas_r, TEST)], hsw[np.isin(seas_r, TEST)]
hs_tr, hs_te = toHS(p_tr, tr), toHS(p_te, te)
print(f"\nYOUR MODEL, refit on Round of 64 only (train {len(tr)} games, test {len(te)})")
print(f"  training AUC {auc(hs_tr, yt):.3f} | right {int(((hs_tr > 0) == yt).sum())}/{len(yt)}")
print(f"  testing  AUC {auc(hs_te, ye):.3f} | right {int(((hs_te > 0) == ye).sum())}/{len(ye)} | higher seed always {int(ye.sum())}/{len(ye)}")
pr = (hs_te > 0).astype(int); print(f"  test confusion: pred0/act0 {int(((pr==0)&(ye==0)).sum())} pred0/act1 {int(((pr==0)&(ye==1)).sum())} pred1/act0 {int(((pr==1)&(ye==0)).sum())} pred1/act1 {int(((pr==1)&(ye==1)).sum())}")
for s in TEST:
    m = seas_r[np.isin(seas_r, TEST)] == s; print(f"  {s}: {int(((hs_te[m] > 0) == ye[m]).sum())}/{int(m.sum())}")
# for reference: the regular 756 pipeline (trained on all rounds of the other years), scored on the same 64 test games
k = ~Q.FF; tr_all = np.where(k & ~np.isin(Q.seas, TEST))[0]
ma, mb = Q.base(tr_all, te, fit); pa = toHS(Q.run(ma, tr_all, mb, te, Q.EX), te)
print(f"  (reference: model trained on all rounds of the other years -> test AUC {auc(pa, ye):.3f}, right {int(((pa > 0) == ye).sum())}/64)")
#json.dump(dict(train_auc=auc(hs_tr, yt), test_auc=auc(hs_te, ye)), open(os.path.join(HERE, "m156_out.json"), "w"))

