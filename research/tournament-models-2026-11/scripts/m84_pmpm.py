# Does regular-season PMPM help the model? reports/regular_season_pmpm.xlsx, sheet "Situations": per team-season, 9
# measures from games before that season's tournament (pre-game data). Each enters as the stronger-minus-weaker gap,
# added to the round lines beside coach + star (same machinery as m18/m82: half-life 12, each tournament held out).
# Scored on the Rounds of 64 to Elite Eight (959 games), where the model alone picks; baseline = the current model.
#   all 9 together      no choosing, so no selection bias
#   each one alone      picking the best of these afterwards is optimistic
#   best one, chosen on the other 15 tournaments, scored on the held-out one (honest version of "each one alone")
import os, sys, re, contextlib, io
os.environ["GROUPING"] = "v2"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np, openpyxl
with contextlib.redirect_stdout(io.StringIO()):
    import m18_rebuild as R
yb, RND, seas, BG = R.yb, R.RND, R.seas, R.B.G
EARLY4 = np.isin(RND, ["First round", "Second round", "Sweet 16", "Elite Eight"])
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\basketball\reports\regular_season_pmpm.xlsx", read_only=True)
rows = wb["Situations"].iter_rows(values_only=True); head = next(rows)
MCOL = [j for j, h in enumerate(head) if j >= 2 and h != "Rank"]; MNAME = [head[j] for j in MCOL]
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
TBL = {(r[0], clean(r[1])): [r[j] for j in MCOL] for r in rows if r[0]}
S_name = R.B.Sname
W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
GAP = np.zeros((len(BG), len(MCOL))); miss = 0
for i, g in enumerate(BG):
    a, b = TBL.get((seas[i], clean(S_name[i]))), TBL.get((seas[i], clean(W_name[i])))
    if a is None or b is None or any(v is None for v in a + b): miss += 1; continue
    GAP[i] = np.array(a, float) - np.array(b, float)
print(f"games {len(BG)}, without PMPM for both teams: {miss}")
CS = R.EXTRA["coach+star"]; WT = R.weights(12)
BASE = {}
for s in R.SEASONS:                                             # base scores don't depend on the extras: fit once
    tr = np.where(seas != s)[0]; te = np.where(seas == s)[0]; BASE[s] = (tr, te) + R.base_scores(tr, te, WT)
def run(extra):
    sc = np.zeros(len(yb))
    for s, (tr, te, m_tr, m_te) in BASE.items(): sc[te] = R.model(m_tr, tr, m_te, te, WT, extra)
    return ((sc > 0) == yb).astype(int)
n = int(EARLY4.sum()); base = run(CS); b0 = base[EARLY4].sum()
print(f"\n{'current model':58} {b0:4d} {b0 / n:.1%}")
allr = run(np.column_stack([CS, GAP])); print(f"{'+ all 9 PMPM measures':58} {allr[EARLY4].sum():4d} {allr[EARLY4].mean():.1%}  ({allr[EARLY4].sum() - b0:+d})")
single = {}
for k, nm in enumerate(MNAME):
    r = run(np.column_stack([CS, GAP[:, k]])); single[nm] = r
    print(f"+ {nm[:56]:56} {r[EARLY4].sum():4d} {r[EARLY4].mean():.1%}  ({r[EARLY4].sum() - b0:+d})")
hon = np.zeros(len(yb), int)                                    # best single chosen without the held-out tournament
for s in R.SEASONS:
    other = EARLY4 & (seas != s); best = max(single, key=lambda nm: single[nm][other].sum())
    hon[seas == s] = single[best][seas == s]
print(f"\n{'best single, chosen on the other 15 tournaments':58} {hon[EARLY4].sum():4d} {hon[EARLY4].mean():.1%}  ({hon[EARLY4].sum() - b0:+d})")
d = allr[EARLY4] - base[EARLY4]; print("all 9 vs current: games it fixed", int((d > 0).sum()), "broke", int((d < 0).sum()))
