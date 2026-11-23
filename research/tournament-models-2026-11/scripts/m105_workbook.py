# Companion workbook for the "Model Review — Advisor Follow-ups" deck. Downloads\Model Review - Advisor Follow-ups.xlsx
# Sheets: Read me | Four predictors | Four boxes | PCA summary | PCA chart | Team points | 5-fold CV | Model types (LOSO)
# Box counts, shares and box centers are formulas over Team points, so they recalculate if rows change.
import json, math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.marker import Marker
from openpyxl.utils import get_column_letter
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
DST = r"C:\Users\crtra\Downloads\Model Review - Advisor Follow-ups.xlsx"
pca = json.load(open(OLD + r"\m103_out.json")); cv = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m102_out.json"))
F = lambda **k: Font(name="Arial", **k)
HEAD = PatternFill("solid", fgColor="15233B"); BAND = PatternFill("solid", fgColor="E9E2D2")
BOXFILL = {"Both right": "E3DDD0", "Model right, sim wrong": "F6DCCB", "Sim right, model wrong": "DCE7F5", "Both wrong": "D9D3C6"}
thin = Border(bottom=Side(style="thin", color="D5D9E0"))
wb = Workbook()
def sheet(name, title, note, first=False):
    ws = wb.active if first else wb.create_sheet(name)
    ws.title = name; ws["A1"] = title; ws["A1"].font = F(bold=True, size=13)
    if note: ws["A2"] = note; ws["A2"].font = F(italic=True, size=9)
    return ws
def header(ws, row, names, widths=None):
    for j, h in enumerate(names, 1):
        c = ws.cell(row=row, column=j, value=h); c.font = F(bold=True, color="FFFFFF"); c.fill = HEAD
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32
    for j, w in enumerate(widths or [], 1): ws.column_dimensions[get_column_letter(j)].width = w
def put(ws, row, vals, fmt=None, bold=False, fill=None):
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=row, column=j, value=v); c.font = F(size=10, bold=bold); c.border = thin
        if fmt and j in fmt: c.number_format = fmt[j]
        if fill: c.fill = PatternFill("solid", fgColor=fill)
# ---- Read me
ws = sheet("Read me", "Model Review — Advisor Follow-ups (companion workbook)", None, first=True)
lines = ["Numbers behind each slide of the deck 'Model Review — Advisor Follow-ups'.",
         "Games: NCAA tournament, Round of 64 to title, 2010-2026 (no 2020), First Four left out: 1,007 games.",
         "Model = ridge logistic regression with round lines (the workbook model, 756 right), each tournament held out of its own training.",
         "Four boxes: each game is model right/wrong x simulator right/wrong. Both teams in a game take that game's box (2,014 team points).",
         "PCA: each team point = that team's pre-tournament numbers the model uses (27 measures as season percentiles). Same team in different years = different points.",
         "5-fold CV: folds are whole tournaments (16 into 5 groups), repeated with 3 random splits = 15 validation folds; only the model type changes.",
         "Formulas: box counts, shares and box centers on 'Four boxes' and 'PCA summary' read the 'Team points' sheet.",
         "Sheets: Four predictors | Four boxes | PCA summary | PCA chart | Team points | 5-fold CV | Model types (LOSO)"]
for i, t in enumerate(lines, 3): ws.cell(row=i, column=1, value=t).font = F(size=10)
ws.column_dimensions["A"].width = 140
# ---- Four predictors
ws = sheet("Four predictors", "Four ways to pick a game", "Right = games picked right of 1,007 (pick'ems count half).")
header(ws, 4, ["", "Seed", "Closing spread", "Simulator", "Model"], [18, 30, 30, 34, 38])
rows = [["Data", "NCAA selection committee", "Betting market (BetIQ closing line)", "Alex's data, pre-tournament, updated daily", "Alex's data, pre-tournament"],
        ["Method", "Committee ranking", "Market consensus", "Possession-by-possession simulation", "Ridge logistic regression"],
        ["Predicts", "Better seed wins", "Point spread, so a favorite", "Game score, then spread and win %", "Probability of a win"],
        ["Inputs", "Resume, rankings, eye test", "All public information, money", "Team ratings, play types, pace, who plays", "Rating, schedule, pace + 27 measures, who plays, coach, star"],
        ["Right (of 1,007)", 710, 720.5, 722, 756]]
for i, r in enumerate(rows, 5):
    put(ws, i, r, bold=(i == 9), fill="E9E2D2" if i == 9 else None)
    for j in range(1, 6): ws.cell(row=i, column=j).alignment = Alignment(wrap_text=True, vertical="top")
put(ws, 10, ["Right %", "=B9/1007", "=C9/1007", "=D9/1007", "=E9/1007"], fmt={2: "0.0%", 3: "0.0%", 4: "0.0%", 5: "0.0%"})
# ---- Team points (data; written before the formula sheets reference it)
tp = wb.create_sheet("Team points"); tp["A1"] = "Every team in every game, with its box and PCA position"; tp["A1"].font = F(bold=True, size=13)
tp["A2"] = "Sorted by box, then winners before losers, then year, round, team. PC1/PC2 = first two principal components of the team's 27 pre-tournament measures."; tp["A2"].font = F(italic=True, size=9)
cols = ["Team", "Year", "Opponent", "Seed", "Opp seed", "Round", "Box", "Won", "PC1", "PC2"]
header(tp, 4, cols, [20, 7, 20, 6, 8, 13, 24, 6, 8, 8])
ORDER = ["Both right", "Model right, sim wrong", "Sim right, model wrong", "Both wrong"]
RO = ["Round of 64", "Round of 32", "Sweet 16", "Elite Eight", "Final Four", "Title"]
pts = sorted(pca["points"], key=lambda p: (ORDER.index(p["quad"]), not p["won"], p["year"], RO.index(p["round"]), p["team"]))
spans = {}                                                     # (box, won) -> first and last row, for the chart's series
for i, p in enumerate(pts, 5):
    put(tp, i, [p["team"], p["year"], p["opp"], p["seed"], p["opp_seed"], p["round"], p["quad"], "W" if p["won"] else "L", p["pc1"], p["pc2"]],
        fmt={9: "0.00", 10: "0.00"})
    tp.cell(row=i, column=7).fill = PatternFill("solid", fgColor=BOXFILL[p["quad"]])
    s = spans.setdefault((p["quad"], p["won"]), [i, i]); s[1] = i
last = 4 + len(pts); tp.freeze_panes = "B5"; tp.auto_filter.ref = f"A4:J{last}"
RNG = lambda col: f"'Team points'!${col}$5:${col}${last}"
# ---- Four boxes (formulas)
ws = sheet("Four boxes", "The four boxes: model right/wrong x simulator right/wrong", "Games = team points / 2 (both teams share the game's box). Formulas read 'Team points'.")
header(ws, 4, ["Box", "Games", "Share of games", "Team points", "Avg seed", "Avg PC1", "Avg PC2"], [26, 10, 14, 12, 10, 10, 10])
for i, q in enumerate(ORDER, 5):
    put(ws, i, [q, f"=D{i}/2", f"=B{i}/SUM($B$5:$B$8)", f"=COUNTIF({RNG('G')},A{i})", f"=AVERAGEIF({RNG('G')},A{i},{RNG('D')})",
                f"=AVERAGEIF({RNG('G')},A{i},{RNG('I')})", f"=AVERAGEIF({RNG('G')},A{i},{RNG('J')})"],
        fmt={2: "0", 3: "0.0%", 5: "0.00", 6: "0.00", 7: "0.00"}, fill=BOXFILL[q])
put(ws, 9, ["Total", "=SUM(B5:B8)", "=SUM(C5:C8)", "=SUM(D5:D8)"], fmt={2: "0", 3: "0.0%"}, bold=True)
ws["A11"] = "As a grid"; ws["A11"].font = F(bold=True, size=11)
header(ws, 12, ["", "Simulator right", "Simulator wrong"])
put(ws, 13, ["Model right", "=B5", "=B6"], fmt={2: "0", 3: "0"}); put(ws, 14, ["Model wrong", "=B7", "=B8"], fmt={2: "0", 3: "0"})
put(ws, 16, ["Model edge in split games", "=B6-B7"], fmt={2: "+0;-0;0"}, bold=True)
put(ws, 17, ["Model's share of split games", "=B6/(B6+B7)"], fmt={2: "0.0%"})
# ---- PCA summary
ws = sheet("PCA summary", "PCA of the teams' pre-tournament stats", "Box centers are formulas over 'Team points'; tests and loadings from the analysis (2,000-shuffle permutation tests).")
header(ws, 4, ["Component", "Variance explained", "Cumulative"], [44, 18, 14, 14])
for i, v in enumerate(pca["pve"][:5], 5):
    put(ws, i, [f"PC{i - 4}", v, f"=SUM($B$5:B{i})"], fmt={2: "0.0%", 3: "0.0%"})
ws["A11"] = "What each component measures (top weights)"; ws["A11"].font = F(bold=True, size=11)
header(ws, 12, ["Measure", "Weight", "Component"])
r = 13
for pc in ("PC1", "PC2"):
    for name, w in pca["loadings"][pc]: put(ws, r, [name, w, pc], fmt={2: "+0.000;-0.000"}); r += 1
r += 1; ws.cell(row=r, column=1, value="Do the boxes sit in different places?").font = F(bold=True, size=11); r += 1
header(ws, r, ["Comparison", "p (all components)", "p (PC1-2 only)", "Different?"]); r += 1
for k, t in pca["tests"].items():
    put(ws, r, [k, t["all_p"], t["pc12_p"], "yes" if t["all_p"] < 0.05 else "no"], fmt={2: "0.000", 3: "0.000"}); r += 1
r += 1; ws.cell(row=r, column=1, value="Box centers (formulas)").font = F(bold=True, size=11); r += 1
header(ws, r, ["Box", "Avg PC1", "Avg PC2", "Team points"]); r += 1
for q in ORDER:
    put(ws, r, [q, f"=AVERAGEIF({RNG('G')},A{r},{RNG('I')})", f"=AVERAGEIF({RNG('G')},A{r},{RNG('J')})", f"=COUNTIF({RNG('G')},A{r})"],
        fmt={2: "0.00", 3: "0.00"}, fill=BOXFILL[q]); r += 1
# ---- PCA chart: one scatter series per box, reading Team points
cs = wb.create_sheet("PCA chart"); cs["A1"] = "PCA map: every team point, colored by box"; cs["A1"].font = F(bold=True, size=13)
cs["A2"] = ("x = PC1 (stronger rating, tougher schedule, better when ahead); y = PC2 (down = offensive rebounding, forced turnovers). "
            "Solid dot = winner, hollow ring = loser, in the box's color."); cs["A2"].font = F(italic=True, size=9)
ch = ScatterChart(); ch.title = "Team points by box (solid = won, ring = lost)"; ch.style = 13; ch.x_axis.title = "PC1"; ch.y_axis.title = "PC2"
ch.height, ch.width = 16, 26
COL = {"Both right": "C9C2B3", "Both wrong": "A7A191", "Sim right, model wrong": "2F6DB5", "Model right, sim wrong": "D9622B"}
for q in ["Both right", "Both wrong", "Sim right, model wrong", "Model right, sim wrong"]:
    for won in (False, True):
        a, b = spans[(q, won)]
        xs = Reference(tp, min_col=9, min_row=a, max_row=b); ys = Reference(tp, min_col=10, min_row=a, max_row=b)
        s = Series(ys, xs, title=f"{q} – {'won' if won else 'lost'}")
        s.marker = Marker(symbol="circle", size=5 if q.startswith("Both") else 7)
        if won: s.marker.graphicalProperties.solidFill = COL[q]
        else: s.marker.graphicalProperties.noFill = True
        s.marker.graphicalProperties.line.solidFill = COL[q]; s.graphicalProperties.line.noFill = True
        ch.series.append(s)
cs.add_chart(ch, "A4")
# ---- PCA by year: 16 small charts (same axes), each reading its own block of 'PCA by year data'
yd = wb.create_sheet("PCA by year data"); yd["A1"] = "Team points grouped by year, box and result (feeds the 'PCA by year' charts)"; yd["A1"].font = F(bold=True, size=13)
header(yd, 3, ["Year", "Box", "Result", "Team", "Opponent", "PC1", "PC2"], [7, 24, 8, 20, 20, 8, 8])
yc = wb.create_sheet("PCA by year"); yc["A1"] = "PCA map by year (same axes for every year; solid = won, ring = lost)"; yc["A1"].font = F(bold=True, size=13)
yc["A2"] = "Each chart is one tournament. Axes fixed at PC1 -7 to 4 and PC2 -5 to 5, the same as the full map."; yc["A2"].font = F(italic=True, size=9)
r = 4; years = sorted({p["year"] for p in pts})
for n, y in enumerate(years):
    ch = ScatterChart(); ch.style = 13; ch.height, ch.width = 7.5, 11.5; ch.legend = None
    g = lambda q: sum(1 for p in pts if p["year"] == y and p["quad"] == q) // 2
    ch.title = f"{y}: splits model {g('Model right, sim wrong')}, sim {g('Sim right, model wrong')}"
    ch.x_axis.scaling.min, ch.x_axis.scaling.max, ch.y_axis.scaling.min, ch.y_axis.scaling.max = -7, 4, -5, 5
    for q in ["Both right", "Both wrong", "Sim right, model wrong", "Model right, sim wrong"]:
        for won in (False, True):
            rows_ = [p for p in pts if p["year"] == y and p["quad"] == q and p["won"] == won]
            if not rows_: continue
            a = r
            for p in rows_:
                put(yd, r, [y, q, "W" if won else "L", p["team"], p["opp"], p["pc1"], p["pc2"]], fmt={6: "0.00", 7: "0.00"}); r += 1
            s = Series(Reference(yd, min_col=7, min_row=a, max_row=r - 1), Reference(yd, min_col=6, min_row=a, max_row=r - 1), title=f"{q} – {'won' if won else 'lost'}")
            s.marker = Marker(symbol="circle", size=4 if q.startswith("Both") else 6)
            if won: s.marker.graphicalProperties.solidFill = COL[q]
            else: s.marker.graphicalProperties.noFill = True
            s.marker.graphicalProperties.line.solidFill = COL[q]; s.graphicalProperties.line.noFill = True
            ch.series.append(s)
    yc.add_chart(ch, f"{get_column_letter(1 + (n % 4) * 7)}{4 + (n // 4) * 15}")
# ---- 5-fold CV
ws = sheet("5-fold CV", "5-fold cross-validation: average validation AUC by model type",
           "15 validation folds (5 folds x 3 random splits of whole tournaments). Same pipeline; only the model type changes. Sign-test p: folds better than ridge vs a 50/50 coin.")
header(ws, 4, ["Model type", "Avg AUC", "SD over folds", "Min", "Max", "Split 1", "Split 2", "Split 3", "Games right (avg)", "Right %", "AUC vs ridge", "Folds better (of 15)", "Sign-test p"],
       [36, 10, 12, 8, 8, 9, 9, 9, 14, 10, 12, 14, 11])
res = cv["results"]; order = sorted(res, key=lambda k: -res[k]["auc"])
def sign_p(k, n=15):
    tail = lambda kk: sum(math.comb(n, i) for i in range(kk, n + 1)) / 2 ** n
    lo = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * min(tail(k), lo))
for i, name in enumerate(order, 5):
    v = res[name]; ridge = name.startswith("Ridge")
    put(ws, i, [name.replace(" (your model)", " (our model)"), v["auc"], v["sd"], v["lo"], v["hi"], *v["per_split"], v["right"], f"=I{i}/1007",
                None if ridge else v["diff_vs_ridge"], None if ridge else v["folds_better"], None if ridge else sign_p(v["folds_better"])],
        fmt={2: "0.000", 3: "0.000", 4: "0.000", 5: "0.000", 6: "0.000", 7: "0.000", 8: "0.000", 9: "0.0", 10: "0.0%", 11: "+0.000;-0.000", 13: "0.000"},
        fill="E9E2D2" if ridge else None)
# ---- LOSO model types
ws = sheet("Model types (LOSO)", "Model types, each tournament held out (leave-one-tournament-out)", "Games right of 1,007; overfit = in-sample minus held out. Settings fixed in advance.")
header(ws, 4, ["Model type", "Held out", "In-sample", "Overfit", "Log-loss", "With team styles", "Change with styles"], [36, 10, 10, 9, 10, 15, 16])
loso = [("Ridge logistic (our model)", 756, 769, 0.5255, 731), ("Linear SVM", 757, 770, 0.5244, 735), ("LDA", 752, 772, 0.5250, 737),
        ("Neural net", 747, 768, 0.5247, 740), ("Boosting", 743, 790, 0.5350, 721), ("QDA", 737, 783, 0.5387, 717),
        ("Random forest", 736, 821, 0.5396, 711), ("Decision tree", 727, 743, 0.5424, 704), ("PCA 20 components", 725, 733, 0.5481, 702)]
for i, (n, h, ins, ll, st) in enumerate(loso, 5):
    put(ws, i, [n, h, ins, f"=C{i}-B{i}", ll, st, f"=F{i}-B{i}"], fmt={4: "+0;-0;0", 5: "0.0000", 7: "+0;-0;0"}, fill="E9E2D2" if i == 5 else None)
# ---- Andrew's method (CART + random forest) on our data
from openpyxl.chart import BarChart
tf = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m110_out.json"))
nm = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m112_names.json"))
ws = sheet("Tree & forest", "Andrew's method (CART + random forest) on our data and our model's 39 inputs",
           "Response: the stronger-rated team won. Gini splits; CART at rpart default cp = 0.01; random forest 500 trees, mtry 6. Same games for every method.")
header(ws, 4, ["Test: Andrew's years (2010, 2016, 2026), Round of 64", "Train AUC", "Test AUC", "Right of 96"], [52, 14, 12, 12])
sp = tf["split|Round of 64"]
for i, r_ in enumerate([["CART (cp 0.01)", sp["cartcp_train_auc"], sp["cartcp_test_auc"], sp["cartcp_test_right"]],
                        ["CART (pruned by 10-fold CV: no splits kept)", sp["cart_train_auc"], sp["cart_test_auc"], sp["cart_test_right"]],
                        ["Random forest (train = out-of-bag)", sp["rf_oob_auc"], sp["rf_test_auc"], sp["rf_test_right"]],
                        ["Our model", None, sp["model_test_auc"], sp["model_test_right"]]], 5):
    put(ws, i, r_, fmt={2: "0.000", 3: "0.000"}, fill="E9E2D2" if r_[0] == "Our model" else None)
header(ws, 10, ["Each tournament held out", "R64 right (of 511)", "R64 AUC", "All rounds right (of 1,007)", "All rounds AUC"])
lr, la = tf["loso|Round of 64"], tf["loso|Round of 64 to title"]
for i, (n_, k) in enumerate([("Our model", "model"), ("Random forest", "rf"), ("CART (cp 0.01)", "cart_cp"), ("CART (pruned by CV)", "cart")], 11):
    put(ws, i, [n_, lr[k]["right"], lr[k]["auc"], la[k]["right"], la[k]["auc"]], fmt={3: "0.000", 5: "0.000"}, fill="E9E2D2" if k == "model" else None)
put(ws, 15, ["Always pick the stronger-rated team", 373, 0.5, 715, 0.5], fmt={3: "0.000", 5: "0.000"})
for c_ in "DE": ws.column_dimensions[c_].width = 22
ws["A18"] = "Variable importance (mean decrease in Gini), random forest on all games of each scope"; ws["A18"].font = F(bold=True, size=11)
header(ws, 19, ["Input", "Round of 64", "All rounds", "Rank (R64)"])
iR, iA = tf["importance|Round of 64"], tf["importance|Round of 64 to title"]
order = sorted(range(len(iR)), key=lambda j: -iR[j])
for k, j in enumerate(order):
    put(ws, 20 + k, [nm[tf["features"][j]], iR[j], iA[j], k + 1], fmt={2: "0.00", 3: "0.00"})
bc = BarChart(); bc.type = "bar"; bc.style = 10; bc.title = "Variable importance, Round of 64 (mean decrease in Gini)"
bc.add_data(Reference(ws, min_col=2, min_row=19, max_row=19 + len(order)), titles_from_data=True)
bc.set_categories(Reference(ws, min_col=1, min_row=20, max_row=19 + len(order))); bc.legend = None
bc.y_axis.title = "Mean decrease in Gini"; bc.x_axis.scaling.orientation = "maxMin"; bc.height, bc.width = 20, 18
ws.add_chart(bc, "G4")
# the CART tree as indented text
tt = wb.create_sheet("CART tree"); tt["A1"] = "CART tree, Round of 64, all 511 games (rpart default cp = 0.01)"; tt["A1"].font = F(bold=True, size=13)
tt["A2"] = "Each line: the condition to reach the node, games in it, and how often the stronger-rated team won. Indent = depth."; tt["A2"].font = F(italic=True, size=9)
rows_t = []
def walk(nd, depth, cond):
    lab = f"{'    ' * depth}{cond}: {nd['n']} games, stronger won {nd['k']} ({nd['k'] / nd['n']:.1%})"
    if "f" in nd:
        rows_t.append(lab + f"  -> split on {nm[tf['features'][nd['f']]]} at {nd['thr']:.3f}")
        walk(nd["L"], depth + 1, f"<= {nd['thr']:.3f}"); walk(nd["R"], depth + 1, f"> {nd['thr']:.3f}")
    else: rows_t.append(lab + "  [leaf]")
walk(tf["treecp|Round of 64"], 0, "All games")
for i, t_ in enumerate(rows_t, 4): tt.cell(row=i, column=1, value=t_).font = F(size=10, name="Consolas") if False else F(size=10)
tt.column_dimensions["A"].width = 120
for w in wb.worksheets:
    if w.title not in ("Read me", "PCA chart"): w.freeze_panes = w.freeze_panes or "A5"
wb.calculation.fullCalcOnLoad = True
wb.save(DST); print("saved", DST, "team points", len(pts))
