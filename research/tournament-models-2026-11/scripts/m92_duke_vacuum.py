# The "Duke" idea on its own: some teams blow weaker teams out but are bad in close games, and it costs them close
# tournament games. Close = within 6 with 5 minutes left (end of minute 35). No upset picking, no model.
#   1) Is close-game play a lasting trait or luck? Split each team-season's close games in two at random (odd/even) and
#      correlate the halves: close record, and "closing" (points gained in the last 5 minutes beyond the rating's 1/8
#      share). Also this season vs the same team next season.
#   2) Do blowout teams close worse than their rating says? Among team-seasons, blowout-win share vs closing, with the
#      team's own rating held fixed.
#   3) Close tournament games (within 6 with 5 left, both teams' rows): does the regular-season close record, or the
#      "Duke type" (blowout share above median, close record at/below median, among tournament teams), win fewer of them
#      than other teams, raw and vs what the rating gap predicts in close games?
import os, sys, re, json, contextlib, io, math, random
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np, openpyxl
__file__ = os.path.join(OLD, "overfit_test.py")
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("overfit_test.py", encoding="utf-8").read().split("# orient by our ratings")[0])   # TM
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
G = json.load(open(os.path.join(HERE, "m88_games.json")))
NET = {(s, clean(t)): v["adj_net"] for s in TM for t, v in TM[s].items()}
rows = [(s, clean(h), clean(a), n, f, m) for s, h, a, n, f, m in G if (s, clean(h)) in NET and (s, clean(a)) in NET]
gap = np.array([NET[(r[0], r[1])] - NET[(r[0], r[2])] for r in rows]); home = np.array([0.0 if r[3] else 1.0 for r in rows])
fin = np.array([r[4] for r in rows], float); A = np.column_stack([gap, home]); coef = np.linalg.lstsq(A, fin, rcond=None)[0]; exp = A @ coef
from collections import defaultdict
T = defaultdict(lambda: defaultdict(list))
for k, (s, h, a, n, f, m35) in enumerate(rows):
    for team, sg in ((h, 1), (a, -1)):
        d = T[(s, team)]; d["blow"].append(sg * f >= 20)
        if abs(m35) <= 6: d["cw"].append(sg * f > 0); d["cl"].append(sg * (f - m35) - sg * exp[k] / 8)
def corr(x, y): x, y = np.asarray(x, float), np.asarray(y, float); return float(np.corrcoef(x, y)[0, 1]), len(x)
def pval_r(r, n): t = r * math.sqrt((n - 2) / (1 - r * r)); return 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
# ---- 1) lasting or luck
random.seed(7)
h1w, h2w, h1c, h2c = [], [], [], []
for k, d in T.items():
    n = len(d["cw"])
    if n < 8: continue
    idx = list(range(n)); random.shuffle(idx); a, b = idx[::2], idx[1::2]
    h1w.append(np.mean([d["cw"][i] for i in a])); h2w.append(np.mean([d["cw"][i] for i in b]))
    h1c.append(np.mean([d["cl"][i] for i in a])); h2c.append(np.mean([d["cl"][i] for i in b]))
r1, n1 = corr(h1w, h2w); r2, _ = corr(h1c, h2c)
print("1) IS CLOSE-GAME PLAY A LASTING TRAIT?  (team-seasons with 8+ close games, close games split in two at random)")
print(f"   close record, half vs half: r = {r1:+.3f} (p = {pval_r(r1, n1):.3f}, {n1} team-seasons)")
print(f"   closing (last-5-min points beyond rating), half vs half: r = {r2:+.3f} (p = {pval_r(r2, n1):.3f})")
nxt = lambda s: f"{int(s[:4]) + 1}-{int(s[5:]) + 1:02d}"
yw, yn, yc, ycn = [], [], [], []
for (s, t), d in T.items():
    e = T.get((nxt(s), t))
    if e and len(d["cw"]) >= 6 and len(e["cw"]) >= 6:
        yw.append(np.mean(d["cw"])); yn.append(np.mean(e["cw"])); yc.append(np.mean(d["cl"])); ycn.append(np.mean(e["cl"]))
r3, n3 = corr(yw, yn); r4, _ = corr(yc, ycn)
print(f"   close record, this season vs next: r = {r3:+.3f} ({n3} team pairs);  closing, this season vs next: r = {r4:+.3f}")
# ---- 2) blowout teams close worse?
keys = [k for k, d in T.items() if len(d["cw"]) >= 6 and k in NET]
bl = np.array([np.mean(T[k]["blow"]) for k in keys]); cl = np.array([np.mean(T[k]["cl"]) for k in keys])
cr = np.array([np.mean(T[k]["cw"]) for k in keys]); rt = np.array([NET[k] for k in keys])
Z = np.column_stack([np.ones(len(keys)), rt, bl]); b = np.linalg.lstsq(Z, cl, rcond=None)[0]
resid = cl - Z @ b; se = math.sqrt(resid @ resid / (len(cl) - 3) * np.linalg.inv(Z.T @ Z)[2, 2])
print("\n2) DO BLOWOUT TEAMS CLOSE WORSE THAN THEIR RATING SAYS?  (team-seasons with 6+ close games)")
print(f"   {len(keys)} team-seasons. Closing vs blowout-win share, rating held fixed: {b[2]:+.2f} pts per 100% blowouts "
      f"(per 10 points of blowout share: {b[2] / 10:+.2f}; p = {2 * (1 - 0.5 * (1 + math.erf(abs(b[2] / se) / math.sqrt(2)))):.3f})")
top = rt >= np.percentile(rt, 90)
q = np.percentile(bl[top], [33, 67])
for lab, m in (("low blowouts", bl[top] <= q[0]), ("middle", (bl[top] > q[0]) & (bl[top] <= q[1])), ("high blowouts", bl[top] > q[1])):
    print(f"   top-10% rated teams, {lab:13}: close record {cr[top][m].mean():.1%}, closing {cl[top][m].mean():+.2f} pts ({int(m.sum())} team-seasons)")
# ---- 3) close tournament games
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx", read_only=True); ws = wb["A Games"]
head = list(next(ws.iter_rows(min_row=4, max_row=4, values_only=True))); ix = {h: j for j, h in enumerate(head)}
TG = []
for r in ws.iter_rows(min_row=5, values_only=True):
    if not r[ix["Year"]] or r[ix["PMPM 35"]] is None or r[ix["Round"]] == "First Four": continue
    y = int(r[ix["Year"]]); s = f"{y - 1}-{str(y)[2:]}"
    TG.append((s, clean(r[ix["Team"]]), clean(r[ix["Opponent"]]), r[ix["PMPM 35"]], r[ix["Result"]] == "W", r[ix["Round"]], r[ix["Team"]], r[ix["Opponent"]]))
tteams = {(s, t) for s, t, *_ in TG}
F = {k: (float(np.mean(T[k]["blow"])), (sum(T[k]["cw"]) + 1) / (len(T[k]["cw"]) + 2)) for k in tteams if k in T}
bmed = np.median([v[0] for v in F.values()]); cmed = np.median([v[1] for v in F.values()])
duke = lambda k: k in F and F[k][0] > bmed and F[k][1] <= cmed
close = [g for g in TG if abs(g[3]) <= 6 and (g[0], g[1]) in F and (g[0], g[2]) in NET and (g[0], g[1]) in NET]
win = np.array([g[4] for g in close], float); rg = np.array([NET[(g[0], g[1])] - NET[(g[0], g[2])] for g in close])
m35 = np.array([g[3] for g in close], float)
Z = np.column_stack([np.ones(len(close)), rg, m35]); w = np.zeros(3)                 # expected win in a close game: rating gap + margin at 35
for _ in range(50):
    p = 1 / (1 + np.exp(-Z @ w)); H = Z.T @ (Z * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Z.T @ (win - p))
ew = 1 / (1 + np.exp(-Z @ w))
isd = np.array([duke((g[0], g[1])) for g in close]); crec = np.array([F[(g[0], g[1])][1] for g in close])
print(f"\n3) CLOSE TOURNAMENT GAMES (within 6 with 5 left): {len(close) // 2} games, {len(close)} team rows")
for lab, m in (("'Duke type' teams", isd), ("all other teams", ~isd), ("close record above median", crec > cmed), ("close record at/below median", crec <= cmed)):
    print(f"   {lab:30} won {win[m].mean():5.1%} of {int(m.sum()):3d} | expected from rating + score {ew[m].mean():5.1%} | difference {100 * (win[m].mean() - ew[m].mean()):+.1f} pts")
# Duke's own close tournament games
print("\nDuke's tournament games within 6 with 5 left:")
for g in TG:
    if g[1] == "duke" and abs(g[3]) <= 6:
        k = (g[0], "duke"); print(f"   {g[0]} {g[5]:13} vs {g[7]:16} margin at 35 {g[3]:+d}  {'WON' if g[4] else 'lost'}  | regular season: close record {F[k][1]:.2f}, blowout wins {F[k][0]:.0%}{'  (Duke type)' if duke(k) else ''}")
