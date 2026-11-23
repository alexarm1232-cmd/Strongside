# Do regular-season PMPM traits pick tournament upsets? Regular season = games not flagged postseason.
# Expected margin of a game = a fit on the two teams' pre-tournament net ratings (+ home edge); residual = actual - expected.
# Per team-season:
#   vs stronger      mean residual vs opponents rated above it          vs weaker   mean residual vs opponents rated below
#   plays up         vs stronger - vs weaker
#   swing            spread (sd) of its residuals: how up-and-down it is
#   close share      share of its games within 6 points with 5 minutes left (end of minute 35)
#   close wins       its win share in those games (shrunk: (W+1)/(N+2))
#   finishing        mean residual of the last 5 minutes (margin change from minute 35 to the end, minus the expected 1/8)
#   blowout share    share of its games decided by 20+
# Test, tournament games Round of 64 to Elite Eight with different seeds (underdog = worse seed, upset = it won):
#   1) does the underdog-minus-favorite gap predict upsets AFTER the model's own chance? logistic: upset ~ model logit + gap
#      (Wald p; 8 traits, so p < 0.05/8 = 0.006 is the bar)
#   2) the raw trend: upset rate when the underdog's trait is above vs below the favorite's, in model-chance bands
#   3) picks: each trait added to the model's round lines, each tournament held out (as m84) - games right and upsets hit
import os, sys, re, json, contextlib, io, math
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLD); sys.path.insert(0, r"C:\Users\crtra\Downloads\basketball\tools"); os.chdir(OLD)
import numpy as np
import pdem as P
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM
    import m18_rebuild as R
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
CACHE = os.path.join(HERE, "m88_games.json")
if not os.path.exists(CACHE):                                  # one pass over the play-by-play: home side margins
    G = []
    for code in sorted(c for c in os.listdir(P.SEASONS_DIR) if len(c) == 4 and c.isdigit() and "0910" <= c <= "2526"):
        for gid, (row, path) in P.season_games(code).items():
            if row.get("post") or not os.path.exists(path): continue
            try: hs, as_ = int(row["home_score"]), int(row["away_score"])
            except (TypeError, ValueError, KeyError): continue
            s = P.pdem(json.load(open(path, encoding="utf-8")))
            if len(s) < 41: continue
            G.append([P.season_label(code), row["home_team"], row["away_team"], bool(row.get("neutral")), hs - as_, s[35][1] - s[35][2]])
    json.dump(G, open(CACHE, "w"))
G = json.load(open(CACHE)); print("regular-season games with play-by-play:", len(G))
NET = {(s, clean(t)): v["adj_net"] for s in TM for t, v in TM[s].items()}
rows = [(s, clean(h), clean(a), n, f, m35, NET[(s, clean(h))], NET[(s, clean(a))]) for s, h, a, n, f, m35 in G
        if (s, clean(h)) in NET and (s, clean(a)) in NET]
print("both teams rated:", len(rows))
gap = np.array([r[6] - r[7] for r in rows]); home = np.array([0.0 if r[3] else 1.0 for r in rows]); fin = np.array([r[4] for r in rows], float)
A = np.column_stack([gap, home]); coef = np.linalg.lstsq(A, fin, rcond=None)[0]; exp = A @ coef; res = fin - exp
late = np.array([r[4] - r[5] for r in rows], float); late_res = late - exp / 8
print(f"expected margin = {coef[0]:.3f} x net gap + {coef[1]:.2f} home")
from collections import defaultdict
T = defaultdict(lambda: defaultdict(list))
for k, (s, h, a, n, f, m35, nh, na) in enumerate(rows):
    for team, opp_net, own_net, sign in ((h, na, nh, 1), (a, nh, na, -1)):
        d = T[(s, team)]; rr = sign * res[k]
        d["res"].append(rr); d["up" if opp_net > own_net else "down"].append(rr)
        close = abs(m35) <= 6; d["close"].append(close)
        if close: d["cw"].append(sign * f > 0)
        d["late"].append(sign * late_res[k]); d["blow"].append(abs(f) >= 20)
def traits(d):
    up = np.mean(d["up"]) if d["up"] else 0.0; dn = np.mean(d["down"]) if d["down"] else 0.0
    return [up, dn, up - dn, float(np.std(d["res"])), float(np.mean(d["close"])), (sum(d["cw"]) + 1) / (len(d["cw"]) + 2),
            float(np.mean(d["late"])), float(np.mean(d["blow"]))]
NAMES = ["vs stronger (residual)", "vs weaker (residual)", "plays up (stronger - weaker)", "swing (sd of residuals)",
         "close share", "close wins", "finishing (last 5 min)", "blowout share"]
TR = {k: traits(d) for k, d in T.items() if len(d["res"]) >= 10}
# ---- tournament games
D = np.load("m3_data.npz", allow_pickle=True); sS, sW = D["seedS"], D["seedW"]
BG, RND, seas, yb = R.B.G, R.RND, R.seas, R.yb
S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
v = np.load("m56_scores.npz")["fixed 27 (picked from all games)"]
E4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"]) & (sS != sW)
dogS = sS > sW
X = np.full((len(BG), 8), np.nan); XSW = np.zeros((len(BG), 8))
for i in range(len(BG)):
    a, b = TR.get((seas[i], clean(S_name[i]))), TR.get((seas[i], clean(W_name[i])))
    if a is None or b is None: continue
    XSW[i] = np.array(a) - np.array(b)
    X[i] = XSW[i] if dogS[i] else -XSW[i]                       # underdog minus favorite
ok = E4 & ~np.isnan(X[:, 0]); n = int(ok.sum())
up = np.where(dogS, yb, ~yb).astype(float)                     # underdog won
mz = np.where(dogS, v, -v)                                     # model's log-odds for the underdog
print(f"tournament games R64-E8 with different seeds and both teams' traits: {n} (upsets {int(up[ok].sum())})")
def logit(Xm, y):
    Z = np.column_stack([np.ones(len(y)), Xm]); w = np.zeros(Z.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Z @ w)); H = Z.T @ (Z * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Z.T @ (y - p))
    se = np.sqrt(np.diag(np.linalg.inv(H))); return w, se
erf = lambda z: math.erf(z / math.sqrt(2))
print(f"\n1) does it predict upsets after the model's chance?  (bar for 8 traits: p < 0.006)")
print(f"   {'trait (underdog - favorite)':34} {'effect':>8} {'p':>7} | upset rate: dog's trait higher / lower")
for k, nm in enumerate(NAMES):
    xs = (X[ok, k] - X[ok, k].mean()) / X[ok, k].std()
    w, se = logit(np.column_stack([mz[ok], xs]), up[ok]); z = w[2] / se[2]; p = 2 * (1 - 0.5 * (1 + erf(abs(z))))
    hi = ok & (X[:, k] > 0); lo = ok & (X[:, k] <= 0)
    print(f"   {nm:34} {w[2]:+8.3f} {p:7.3f} | {up[hi].mean():5.1%} ({int(hi.sum())}) / {up[lo].mean():5.1%} ({int(lo.sum())})")
# 2) trend inside model-chance bands, for the strongest trait by p
print("\n2) upset rate by model-chance band, underdog's trait higher vs lower than the favorite's")
pm = 1 / (1 + np.exp(-mz))
for k, nm in enumerate(NAMES):
    line = f"   {nm:34}"
    for lo_, hi_ in ((0, .25), (.25, .4), (.4, .5)):
        band = ok & (pm >= lo_) & (pm < hi_)
        a_, b_ = band & (X[:, k] > 0), band & (X[:, k] <= 0)
        line += f" | {lo_:.0%}-{hi_:.0%}: {up[a_].mean():4.0%} vs {up[b_].mean():4.0%}"
    print(line)
# 3) picks, held out
CS = R.EXTRA["coach+star"]; WT = R.weights(12)
BASE = {s: (tr, te) + R.base_scores(tr, te, WT) for s in R.SEASONS for tr, te in [(np.where(seas != s)[0], np.where(seas == s)[0])]}
def run(extra):
    sc = np.zeros(len(yb))
    for s, (tr, te, m_tr, m_te) in BASE.items(): sc[te] = R.model(m_tr, tr, m_te, te, WT, extra)
    return sc
ALL4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
def show(nm, sc):
    right = ((sc > 0) == yb)[ALL4].sum(); dogpick = E4 & (np.where(dogS, sc > 0, sc < 0))
    print(f"   {nm:34} right {right:4d} | upset picks {int(dogpick.sum()):3d}, hit {int(up[dogpick].sum()):3d} ({up[dogpick].mean():.0%})")
print("\n3) picks, Round of 64 to Elite Eight (959 games), each tournament held out")
show("current model", run(CS))
show("+ all 8 traits", run(np.column_stack([CS, XSW])))
for k, nm in enumerate(NAMES): show("+ " + nm, run(np.column_stack([CS, XSW[:, k]])))
