# "Weaker teams punch up" on its own (no model, no upset picking). Weaker team = not in that season's top 40 (pre-tournament
# net rating). Punching up = its margin vs top-40 opponents beyond what the ratings expect (home edge included).
#   1) Is it a lasting trait? Split each team-season's top-40 games in two at random and correlate the halves; also
#      this season vs next. Compare with its margin vs everyone else (is punching up separate from just being underrated?).
#   2) Tournament: weaker teams vs top-40 opponents. Actual win rate and margin vs what the ratings expect, split by
#      regular-season punching up (teams with 2+ top-40 games). Expected win = normal chance from the expected margin and
#      the regular season's spread of results.
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
TOP = {}
for s in TM:
    for k, (t, v) in enumerate(sorted(TM[s].items(), key=lambda kv: -kv[1]["adj_net"])): TOP[(s, clean(t))] = k < 40
rows = [(s, clean(h), clean(a), n, f) for s, h, a, n, f, m in G if (s, clean(h)) in NET and (s, clean(a)) in NET]
gap = np.array([NET[(r[0], r[1])] - NET[(r[0], r[2])] for r in rows]); home = np.array([0.0 if r[3] else 1.0 for r in rows])
fin = np.array([r[4] for r in rows], float); A = np.column_stack([gap, home]); coef = np.linalg.lstsq(A, fin, rcond=None)[0]
res = fin - A @ coef; SD = float(res.std())
from collections import defaultdict
T = defaultdict(lambda: defaultdict(list))
for k, (s, h, a, n, f) in enumerate(rows):
    for team, opp, sg in ((h, a, 1), (a, h, -1)):
        if TOP[(s, team)]: continue
        T[(s, team)]["top" if TOP[(s, opp)] else "rest"].append(sg * res[k])
        if TOP[(s, opp)]: T[(s, team)]["topwin"].append(sg * f > 0)
def r_p(x, y):
    r = float(np.corrcoef(x, y)[0, 1]); n = len(x); t = r * math.sqrt((n - 2) / (1 - r * r))
    return r, n, 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
print(f"regular season: expected margin = {coef[0]:.3f} x rating gap + {coef[1]:.2f} home; spread of results (sd) {SD:.1f} pts")
print("\n1) IS PUNCHING UP A LASTING TRAIT?  (teams outside the top 40)")
random.seed(7); a1, a2, rest_a, rest_b = [], [], [], []
for k, d in T.items():
    if len(d["top"]) < 4 or len(d["rest"]) < 8: continue
    idx = list(range(len(d["top"]))); random.shuffle(idx)
    a1.append(np.mean([d["top"][i] for i in idx[::2]])); a2.append(np.mean([d["top"][i] for i in idx[1::2]]))
    rest_a.append(np.mean(d["rest"]))
r, n, p = r_p(a1, a2); print(f"   margin beyond rating vs top 40, half vs half: r = {r:+.3f} (p = {p:.3f}, {n} team-seasons with 4+ top-40 games)")
top_all = [(np.mean(T[k]["top"]), np.mean(T[k]["rest"])) for k in T if len(T[k]["top"]) >= 4 and len(T[k]["rest"]) >= 8]
r, n, p = r_p([x[0] for x in top_all], [x[1] for x in top_all])
print(f"   vs top 40 compared with vs everyone else (same team-season): r = {r:+.3f} (p = {p:.3f})")
nxt = lambda s: f"{int(s[:4]) + 1}-{int(s[5:]) + 1:02d}"
pr = [(np.mean(d["top"]), np.mean(T[(nxt(s), t)]["top"])) for (s, t), d in list(T.items())
      if len(d["top"]) >= 3 and (nxt(s), t) in T and len(T[(nxt(s), t)]["top"]) >= 3]
r, n, p = r_p([x[0] for x in pr], [x[1] for x in pr]); print(f"   this season vs next season (3+ top-40 games each): r = {r:+.3f} (p = {p:.3f}, {n} pairs)")
# does it hold beyond being underrated overall? punch-up minus rest, half vs half
d1, d2 = [], []
for k, d in T.items():
    if len(d["top"]) < 4 or len(d["rest"]) < 8: continue
    it = list(range(len(d["top"]))); ir = list(range(len(d["rest"]))); random.shuffle(it); random.shuffle(ir)
    d1.append(np.mean([d["top"][i] for i in it[::2]]) - np.mean([d["rest"][i] for i in ir[::2]]))
    d2.append(np.mean([d["top"][i] for i in it[1::2]]) - np.mean([d["rest"][i] for i in ir[1::2]]))
r, n, p = r_p(d1, d2); print(f"   playing UP specifically (vs top 40 minus vs the rest), half vs half: r = {r:+.3f} (p = {p:.3f})")
# ---- 2) tournament
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx", read_only=True); ws = wb["A Games"]
head = list(next(ws.iter_rows(min_row=4, max_row=4, values_only=True))); ix = {h: j for j, h in enumerate(head)}
TG = []
for rr in ws.iter_rows(min_row=5, values_only=True):
    if not rr[ix["Year"]] or rr[ix["Round"]] == "First Four": continue
    y = int(rr[ix["Year"]]); s = f"{y - 1}-{str(y)[2:]}"; t, o = clean(rr[ix["Team"]]), clean(rr[ix["Opponent"]])
    if (s, t) in NET and (s, o) in NET and not TOP[(s, t)] and TOP[(s, o)]:
        TG.append((s, t, o, rr[ix["Result"]] == "W", float(rr[ix["Final margin"]]), int(rr[ix["Seed"]]), rr[ix["Team"]], rr[ix["Opponent"]], rr[ix["Round"]]))
em = np.array([coef[0] * (NET[(g[0], g[1])] - NET[(g[0], g[2])]) for g in TG])
ew = np.array([0.5 * (1 + math.erf(x / SD / math.sqrt(2))) for x in em])
won = np.array([g[3] for g in TG], float); mar = np.array([g[4] for g in TG]); seed = np.array([g[5] for g in TG])
pu = np.array([np.mean(T[(g[0], g[1])]["top"]) if len(T[(g[0], g[1])]["top"]) >= 2 else np.nan for g in TG])
nt = np.array([len(T[(g[0], g[1])]["top"]) for g in TG]); bw = np.array([sum(T[(g[0], g[1])]["topwin"]) for g in TG])
print(f"\n2) TOURNAMENT: teams outside the top 40 vs top-40 opponents: {len(TG)} games, won {won.mean():.1%} (ratings expected {ew.mean():.1%})")
def line(lab, m):
    print(f"   {lab:44} won {won[m].mean():5.1%} of {int(m.sum()):3d} (expected {ew[m].mean():5.1%}, {100 * (won[m].mean() - ew[m].mean()):+5.1f}) | "
          f"margin {mar[m].mean():+5.1f} vs expected {em[m].mean():+5.1f} ({mar[m].mean() - em[m].mean():+.1f})")
has = ~np.isnan(pu); med = np.nanmedian(pu)
line("0-1 regular-season top-40 games", ~has)
line("2+ top-40 games, punched up (above median)", has & (pu > med))
line("2+ top-40 games, did not (at/below median)", has & (pu <= med))
line("beat a top-40 team in the regular season", bw >= 1)
line("never beat one", (bw == 0) & (nt >= 1))
print(" 10-16 seeds only")
lo = seed >= 10
line("punched up", lo & has & (pu > med)); line("did not", lo & has & (pu <= med))
line("beat a top-40 team", lo & (bw >= 1)); line("never beat one (1+ tries)", lo & (bw == 0) & (nt >= 1))
# correlation, continuous
r, n, p = r_p(pu[has], (mar - em)[has]); print(f"\n   punching up vs tournament margin beyond expectation, all 2+ game teams: r = {r:+.3f} (p = {p:.3f}, {n} games)")
print("\nbiggest punch-up teams that won as a 10-16 seed vs a top-40 team:")
order = np.argsort(-np.nan_to_num(pu, nan=-99))
k = 0
for i in order:
    if lo[i] and won[i] == 1 and has[i]:
        print(f"   {TG[i][0]} ({seed[i]}) {TG[i][6]:18} beat {TG[i][7]:18} {TG[i][8]:12} punched up {pu[i]:+.1f} pts over {nt[i]} top-40 games ({bw[i]} wins)"); k += 1
    if k >= 10: break
