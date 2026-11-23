# Two patterns, regular season -> NCAA tournament (Round of 64 to Elite Eight, different seeds; favorite = better seed).
# A) "Duke" favorites: blow weaker teams out but do poorly in close games. Close = within 6 with 5 minutes left (minute 35).
#    close record = (W+1)/(N+2); closing = margin gained over the last 5 minutes of close games, beyond expectation;
#    blowout share = share of games WON by 20+.
#    Tested on all games, and on the tournament games that were themselves close at minute 35 (descriptive: you can't know
#    beforehand a game will be close, but it shows whether the close-game weakness shows up when it matters).
# B) Underdogs punching up: their regular-season games vs that season's top 40 (pre-tournament net rating): margin vs
#    expectation, record, and how often they were within 6 with 5 left.
# Each split also gets a logistic test AFTER the model's own chance (the 756, held out), so "the model already knew" is
# separated from "this adds something".
import os, sys, re, json, contextlib, io, math
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np, openpyxl
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM
    import m18_rebuild as R
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
G = json.load(open(os.path.join(HERE, "m88_games.json")))      # season, home, away, neutral, final (home), margin at 35 (home)
NET = {(s, clean(t)): v["adj_net"] for s in TM for t, v in TM[s].items()}
TOP40 = {}
for s in TM:
    for k, (t, v) in enumerate(sorted(TM[s].items(), key=lambda kv: -kv[1]["adj_net"])): TOP40[(s, clean(t))] = k < 40
rows = [(s, clean(h), clean(a), n, f, m) for s, h, a, n, f, m in G if (s, clean(h)) in NET and (s, clean(a)) in NET]
gap = np.array([NET[(r[0], r[1])] - NET[(r[0], r[2])] for r in rows]); home = np.array([0.0 if r[3] else 1.0 for r in rows])
fin = np.array([r[4] for r in rows], float); A = np.column_stack([gap, home]); coef = np.linalg.lstsq(A, fin, rcond=None)[0]
exp = A @ coef; res = fin - exp
from collections import defaultdict
T = defaultdict(lambda: defaultdict(list))
for k, (s, h, a, n, f, m35) in enumerate(rows):
    for team, opp, sg in ((h, a, 1), (a, h, -1)):
        d = T[(s, team)]; close = abs(m35) <= 6
        d["games"].append(1); d["blowwin"].append(sg * f >= 20)
        if close: d["cw"].append(sg * f > 0); d["cl"].append(sg * (f - m35) - sg * exp[k] / 8)
        if TOP40.get((s, opp)) and not TOP40.get((s, team)):
            d["t_res"].append(sg * res[k]); d["t_win"].append(sg * f > 0); d["t_close"].append(abs(m35) <= 6 or sg * f > 0)
def feats(d):
    return dict(close_rec=(sum(d["cw"]) + 1) / (len(d["cw"]) + 2), close_n=len(d["cw"]),
                closing=float(np.mean(d["cl"])) if d["cl"] else 0.0, blow=float(np.mean(d["blowwin"])),
                top_n=len(d["t_res"]), top_res=float(np.mean(d["t_res"])) if d["t_res"] else np.nan,
                top_w=sum(d["t_win"]), top_close=float(np.mean(d["t_close"])) if d["t_close"] else np.nan)
F = {k: feats(d) for k, d in T.items()}
# ---- tournament games
D3 = np.load("m3_data.npz", allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
BG, RND, seas, yb = R.B.G, R.RND, R.seas, R.yb
S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
v = np.load("m56_scores.npz")["fixed 27 (picked from all games)"]
E4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"]) & (sS != sW)
dogS = sS > sW; up = np.where(dogS, yb, ~yb).astype(float); mz = np.where(dogS, v, -v)
FAV = np.where(dogS, W_name, S_name); DOG = np.where(dogS, S_name, W_name)
fseed = np.minimum(sS, sW); dseed = np.maximum(sS, sW)
ff = [F.get((seas[i], clean(FAV[i]))) for i in range(len(BG))]; df = [F.get((seas[i], clean(DOG[i]))) for i in range(len(BG))]
ok = E4 & np.array([a is not None and b is not None for a, b in zip(ff, df)])
# tournament closeness at minute 35, from the A Games sheet (team-side margins)
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx", read_only=True); ws = wb["A Games"]
head = list(next(ws.iter_rows(min_row=4, max_row=4, values_only=True))); ix = {h: j for j, h in enumerate(head)}
M35 = {}
for r in ws.iter_rows(min_row=5, values_only=True):
    if r[ix["Year"]] and r[ix["PMPM 35"]] is not None: M35[(int(r[ix["Year"]]), str(r[ix["Date"]]), clean(r[ix["Team"]]))] = r[ix["PMPM 35"]]
tclose = np.zeros(len(BG), bool)
for i in range(len(BG)):
    y = int(seas[i][:4]) + 1; d = str(BG[i]["date"]).replace("/", "-")
    m = M35.get((y, d, clean(FAV[i])))
    if m is not None: tclose[i] = abs(m) <= 6
erf = lambda z: math.erf(z / math.sqrt(2))
def adj_p(x, mask):
    """p for x predicting upsets after the model's log-odds (logistic, Wald)"""
    xs = (x[mask] - x[mask].mean()) / (x[mask].std() + 1e-12); Z = np.column_stack([np.ones(mask.sum()), mz[mask], xs]); y = up[mask]; w = np.zeros(3)
    for _ in range(50):
        p = 1 / (1 + np.exp(-Z @ w)); H = Z.T @ (Z * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Z.T @ (y - p))
    z = w[2] / np.sqrt(np.linalg.inv(H)[2, 2]); return w[2], 2 * (1 - 0.5 * (1 + erf(abs(z))))
pm = 1 / (1 + np.exp(-mz))
def split(name, x, mask, hi_label, lo_label, cut=None):
    cut = np.median(x[mask]) if cut is None else cut
    hi, lo = mask & (x > cut), mask & (x <= cut)
    eff, p = adj_p(x, mask)
    print(f"   {name:46} {hi_label}: {up[hi].mean():5.1%} of {int(hi.sum()):3d} (model expected {1 - pm[hi].mean() if False else pm[hi].mean():5.1%})"
          f" | {lo_label}: {up[lo].mean():5.1%} of {int(lo.sum()):3d} (exp {pm[lo].mean():5.1%}) | after model p={p:.3f}")
g = lambda arr, key: np.array([a[key] if a else np.nan for a in arr], float)
f_close, f_closing, f_blow = g(ff, "close_rec"), g(ff, "closing"), g(ff, "blow")
print(f"games: {int(ok.sum())}, upsets {int(up[ok].sum())}; of them close at minute 35: {int((ok & tclose).sum())}, upsets {int(up[ok & tclose].sum())}")
print("\nA) FAVORITES: upset rate (the underdog wins), with the model's average expected upset chance in brackets")
print(" all games")
split("favorite's close-game record", f_close, ok, "good", "poor")
split("favorite's closing (last 5 min of close games)", f_closing, ok, "good", "poor")
split("favorite's blowout-win share", f_blow, ok, "high", "low")
duke = (f_blow > np.nanmedian(f_blow[ok])) & (f_close <= np.nanmedian(f_close[ok]))
print(f"   'Duke type' (blowouts above median AND close record at/below median): {int((ok & duke).sum())} games, upsets "
      f"{up[ok & duke].mean():.1%} (model expected {pm[ok & duke].mean():.1%}) vs others {up[ok & ~duke].mean():.1%} (exp {pm[ok & ~duke].mean():.1%})")
print(" only tournament games close with 5 minutes left")
cm = ok & tclose
split("favorite's close-game record", f_close, cm, "good", "poor")
split("favorite's closing (last 5 min of close games)", f_closing, cm, "good", "poor")
print(f"   'Duke type' in close games: {int((cm & duke).sum())} games, upsets {up[cm & duke].mean():.1%} vs others {up[cm & ~duke].mean():.1%}")
print(" favorites seeded 1-4 only")
top = ok & (fseed <= 4)
split("favorite's close-game record", f_close, top, "good", "poor")
print(f"   'Duke type' 1-4 seeds: {int((top & duke).sum())} games, upsets {up[top & duke].mean():.1%} (exp {pm[top & duke].mean():.1%}) vs others {up[top & ~duke].mean():.1%} (exp {pm[top & ~duke].mean():.1%})")
print(f"   'Duke type' 1-4 seeds in close games: {int((top & duke & tclose).sum())} games, upsets {up[top & duke & tclose].mean():.1%} vs others {up[top & ~duke & tclose].mean():.1%}")
print("\nB) UNDERDOGS PUNCHING UP (games vs that season's top 40; underdogs not in the top 40 themselves, 2+ such games)")
t_n, t_res, t_w, t_cl = g(df, "top_n"), g(df, "top_res"), g(df, "top_w"), g(df, "top_close")
pu = ok & (t_n >= 2) & ~np.isnan(t_res)
print(f"   underdogs with 2+ top-40 games: {int(pu.sum())} games (upsets {up[pu].mean():.1%}); with 0-1: {int((ok & ~pu).sum())} (upsets {up[ok & ~pu].mean():.1%})")
split("margin vs top 40, beyond expectation", t_res, pu, "punched up", "did not")
split("stayed close or won vs top 40 (share)", t_cl, pu, "high", "low")
wonany = pu & (t_w >= 1)
print(f"   beat a top-40 team at least once: {up[wonany].mean():.1%} of {int(wonany.sum())} (exp {pm[wonany].mean():.1%}) vs never: "
      f"{up[pu & ~wonany].mean():.1%} of {int((pu & ~wonany).sum())} (exp {pm[pu & ~wonany].mean():.1%})")
print(" underdogs seeded 10-16 only")
lowd = pu & (dseed >= 10)
split("margin vs top 40, beyond expectation", t_res, lowd, "punched up", "did not")
print(f"   beat a top-40 team: {up[lowd & (t_w >= 1)].mean():.1%} of {int((lowd & (t_w >= 1)).sum())} vs never: {up[lowd & (t_w < 1)].mean():.1%} of {int((lowd & (t_w < 1)).sum())}")
# examples: Duke-type 1-4 seeds that lost
print("\nexamples: 'Duke type' 1-4 seed favorites that lost (season, team, seed, round, close record, blowout share, close at 35?)")
ex = np.where(top & duke & (up == 1))[0]
for i in ex: print(f"   {seas[i]} {FAV[i]:16} {int(fseed[i])}-seed lost to {DOG[i]:16} ({int(dseed[i])}) {RND[i]:12} close rec {f_close[i]:.2f} blowouts {f_blow[i]:.0%} close-late {'yes' if tclose[i] else 'no'}")
dk = [k for k in F if k[1] == "duke"]
print("\nDuke by season (close record, close games, blowout-win share):", [(k[0], round(F[k]["close_rec"], 2), F[k]["close_n"], f"{F[k]['blow']:.0%}") for k in sorted(dk)][-8:])
