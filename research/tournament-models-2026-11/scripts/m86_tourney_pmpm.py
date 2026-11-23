# 1) Copy sheet "A Games" of tournament_workbook v13.xlsx into its own workbook (values, fills, fonts, widths, merges).
# 2) Does in-tournament PMPM help? A game's own PMPM is only known after it, so each team brings the PMPM of its
#    PREVIOUS tournament game (Round of 32 on). Gap features, stronger minus weaker: average margin over minutes 1-40,
#    halftime margin, final margin, worst margin. Round of 64 games carry 0 (no earlier game). Held out by tournament,
#    scored on the Round of 32 to Elite Eight (where the feature exists) and on all of R64-E8.
import os, sys, re, copy, contextlib, io
os.environ["GROUPING"] = "v2"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np, openpyxl
from openpyxl.utils import get_column_letter
SRC = r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx"; DST = r"C:\Users\crtra\Downloads\A Games - PMPM.xlsx"
wb = openpyxl.load_workbook(SRC); ws = wb["A Games"]
out = openpyxl.Workbook(); o = out.active; o.title = "A Games"
for row in ws.iter_rows():
    for c in row:
        n = o.cell(row=c.row, column=c.column, value=c.value)
        if c.has_style:
            n.font, n.fill, n.border = copy.copy(c.font), copy.copy(c.fill), copy.copy(c.border)
            n.alignment, n.number_format = copy.copy(c.alignment), c.number_format
for k, d in ws.column_dimensions.items(): o.column_dimensions[k].width = d.width
for r in ws.merged_cells.ranges: o.merge_cells(str(r))
o.freeze_panes = ws.freeze_panes
out.save(DST); print("saved", DST)

# ---- the test
with contextlib.redirect_stdout(io.StringIO()):
    import m18_rebuild as R
yb, RND, seas, BG = R.yb, R.RND, R.seas, R.B.G
rows = list(ws.iter_rows(min_row=5, values_only=True)); head = list(ws.iter_rows(min_row=4, max_row=4, values_only=True))[0]
ix = {h: j for j, h in enumerate(head)}
clean = lambda n: re.sub(r"[^a-z0-9]", "", str(n).lower())
ORDER = ["First Four", "First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
RN = {"First Four": "First Four", "Round of 64": "First round", "First round": "First round", "Round of 32": "Second round",
      "Second round": "Second round", "Sweet 16": "Sweet 16", "Elite Eight": "Elite Eight", "Elite 8": "Elite Eight",
      "Final Four": "Final Four", "Championship": "Championship", "Title": "Championship", "National Championship": "Championship"}
G = {}                                                          # (season, team, round) -> features of that game
unknown = set()
for r in rows:
    if not r[ix["Year"]] or r[ix["Round"]] is None: continue
    rd = RN.get(str(r[ix["Round"]]).strip())
    if rd is None: unknown.add(r[ix["Round"]]); continue
    y = int(r[ix["Year"]]); s = f"{y - 1}-{str(y)[2:]}"
    m = [r[ix[f"PMPM {k}"]] for k in range(1, 41)]
    if any(v is None for v in m): continue
    G[(s, clean(r[ix["Team"]]), rd)] = [float(np.mean(m)), float(m[19]), float(r[ix["Final margin"]]), float(min(m))]
print("rounds not recognised:", unknown, "| team-games read:", len(G))
S_name = R.B.Sname; W_name = np.array([g["dog"] if g["fav"] == s else g["fav"] for g, s in zip(BG, S_name)])
F = np.zeros((len(BG), 4)); have = np.zeros(len(BG), bool); miss = 0
for i in range(len(BG)):
    rd = RND[i]
    if rd in ("First Four", "First round"): continue
    prev = ORDER[ORDER.index(rd) - 1]
    def last(team):                                              # its previous game: the round before (First Four for R64 handled above)
        return G.get((seas[i], clean(team), prev))
    a, b = last(S_name[i]), last(W_name[i])
    if a is None or b is None: miss += 1; continue
    F[i] = np.array(a) - np.array(b); have[i] = True
print("later-round games with both teams' previous game:", int(have.sum()), "missing:", miss)
CS = R.EXTRA["coach+star"]; WT = R.weights(12)
BASE = {s: (tr, te) + R.base_scores(tr, te, WT) for s in R.SEASONS for tr, te in [(np.where(seas != s)[0], np.where(seas == s)[0])]}
def run(extra):
    sc = np.zeros(len(yb))
    for s, (tr, te, m_tr, m_te) in BASE.items(): sc[te] = R.model(m_tr, tr, m_te, te, WT, extra)
    return ((sc > 0) == yb).astype(int)
LATE = np.isin(RND, ["Second round", "Sweet 16", "Elite Eight"]); E4 = LATE | (RND == "First round")
b = run(CS); print(f"\n{'':44} {'R32-E8':>7} {'R64-E8':>7}\n{'current model':44} {b[LATE].sum():7d} {b[E4].sum():7d}")
NM = ["avg margin over the game", "halftime margin", "final margin", "worst margin"]
r = run(np.column_stack([CS, F])); print(f"{'+ all 4 previous-game PMPM gaps':44} {r[LATE].sum():7d} {r[E4].sum():7d}")
for k, nm in enumerate(NM):
    r = run(np.column_stack([CS, F[:, k]])); print(f"{'+ previous game ' + nm:44} {r[LATE].sum():7d} {r[E4].sum():7d}")
