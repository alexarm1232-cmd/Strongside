import os
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter
from upset_high_seeds import seasons, ROUNDS

# Every NCAA tournament game 2010-2026, from both sides:   python tools/tournament_workbook.py
# A  each game twice (X vs Y with X's closing spread, then Y vs X with Y's), with the team's margin at minutes 1-40
#    (from reports/pdem_all_ncaa_tournament.csv; plus = the team was ahead) and the closing line from
#    reports/tournament_spreads.csv (BetIQ; minus = the team was the favorite). First Four included.
# B  every tournament team: seed, exit round, November record and November record against that season's
#    pre-tournament top 40 (by Strongside net rating).
# C  win % and games by closing spread (rows) and round (columns), counted live from the A sheet with COUNTIFS.
# Each comes three times: all years, pre-NIL (2010-2021 tournaments) and post-NIL (2022 on; NIL began July 2021).
# Writes reports/tournament_workbook.xlsx.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
ROUND_NAMES = {"First Four": "First Four", **ROUNDS}
ORDER = list(ROUND_NAMES.values())
NIL = 2022                       # first tournament after NIL (July 2021)
ERAS = [("All years", lambda y: True), ("Pre-NIL", lambda y: y < NIL), ("Post-NIL", lambda y: y >= NIL)]
# closing-spread rows for C: (label, from, to), 5-point bands mirrored around the pick'em row
BUCKETS = [("−25+", -99, -25), ("−24.9 to −20", -24.9, -20), ("−19.9 to −15", -19.9, -15), ("−14.9 to −10", -14.9, -10),
           ("−9.9 to −5", -9.9, -5), ("−4.9 to −0.1", -4.9, -0.1), ("Pick'em (0)", 0, 0), ("+0.1 to +4.9", 0.1, 4.9),
           ("+5 to +9.9", 5, 9.9), ("+10 to +14.9", 10, 14.9), ("+15 to +19.9", 15, 19.9), ("+20 to +24.9", 20, 24.9),
           ("+25+", 25, 99)]

font = lambda **k: Font(name="Arial", **k)
HEAD_FILL = PatternFill("solid", fgColor="14213D")
thin = Side(style="thin", color="D5D9E0")

def game_rows():
    spreads = {r["game_id"]: r for r in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8"))}
    rows = []
    for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")):
        s = spreads[g["game_id"]]
        wp, lp = int(g["winner_pts"]), int(g["loser_pts"])
        margins = [int(g[f"m{i}"]) for i in range(1, 41)]
        for team, opp, seed, oseed, sign, pts, opts in ((g["winner"], g["loser"], g["winner_seed"], g["loser_seed"], 1, wp, lp),
                                                        (g["loser"], g["winner"], g["loser_seed"], g["winner_seed"], -1, lp, wp)):
            line = float(s["spread"]) if team == s["favorite"] else -float(s["spread"])
            rows.append([int(g["date"][:4]), g["date"].replace("/", "-"), ROUND_NAMES[g["round"]], team, int(seed), opp, int(oseed),
                         line + 0.0, "W" if sign == 1 else "L", f"{pts}-{opts}", pts - opts, "Yes" if int(g["minutes"]) > 40 else "",
                         *[sign * m + 0 for m in margins]])
    rows.sort(key=lambda r: (r[0], r[1], ORDER.index(r[2]), r[3]))
    return rows

def team_rows(games):
    pages = seasons()
    teams = {}
    for r in games:                                      # one entry per team per year; the last game is its exit
        t = teams.setdefault((r[0], r[3]), {"seed": r[4], "w": 0, "l": 0, "exit": None, "season": None})
        t["w" if r[8] == "W" else "l"] += 1
        if r[8] == "L": t["exit"] = r[2]
    season_of = {}
    for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")):
        season_of[int(g["date"][:4])] = g["season"]
    rows, missing = [], []
    for (year, name), t in teams.items():
        sched, top = pages[season_of[year]]
        if name not in sched: missing.append(f"{year} {name}")
        nov = [x for x in sched.get(name, []) if x["d"][5:7] == "11"]
        vs = [x for x in nov if x["opp"] in top]
        rows.append([year, name, t["seed"], t["exit"] or "Champion", t["w"], t["l"], None,
                     sum(x["pf"] > x["pa"] for x in nov), sum(x["pf"] < x["pa"] for x in nov), None,
                     sum(x["pf"] > x["pa"] for x in vs), sum(x["pf"] < x["pa"] for x in vs), None, None])
    if missing: print("   no schedule for:", missing)
    exits = ORDER + ["Champion"]
    rows.sort(key=lambda r: (r[0], r[2], -exits.index(r[3]), r[1]))
    return rows

def header(ws, row, names, height=33):
    for j, h in enumerate(names, 1):
        c = ws.cell(row=row, column=j, value=h)
        c.font = font(bold=True, color="FFFFFF", size=10)
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = height

def title(ws, text, note):
    ws["A1"] = text
    ws["A1"].font = font(bold=True, size=13)
    ws["A2"] = note
    ws["A2"].font = font(size=9, italic=True)

def sheet_a(wb, name, era, rows):
    ws = wb.create_sheet(name)
    title(ws, f"Every NCAA tournament game from both sides — {era.lower()}",
          "Each game is listed twice: once as the winner vs the loser, once the other way round. Closing spread from that team's side "
          "(minus = favorite; BetIQ). Minutes 1–40: the team's score margin at the end of each minute (plus = ahead). First Four included.")
    head = ["Year", "Date", "Round", "Team", "Seed", "Opponent", "Opp seed", "Closing spread", "Result", "Score", "Final margin", "OT",
            *[f"Min {i}" for i in range(1, 41)]]
    H = 4
    header(ws, H, head)
    for i, r in enumerate(rows):
        n = H + 1 + i
        for j, v in enumerate(r, 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10)
            if j == 8: c.number_format = '+0.0;−0.0;0.0'
            if j == 11 or j > 12: c.number_format = '+0;−0;0'
            if j not in (2, 4, 6): c.alignment = Alignment(horizontal="center")
    last = H + len(rows)
    # minute margins shaded orange (behind) to blue (ahead)
    ws.conditional_formatting.add(f"M{H + 1}:{get_column_letter(len(head))}{last}",
                                  ColorScaleRule(start_type="num", start_value=-20, start_color="E8743B",
                                                 mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                 end_type="num", end_value=20, end_color="2F6EBA"))
    for j, w in enumerate([7, 11, 13, 18, 6, 18, 7, 9, 7, 8, 8, 5], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for j in range(13, len(head) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 6
    ws.freeze_panes = f"E{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"
    return last

def sheet_b(wb, name, era, rows):
    ws = wb.create_sheet(name)
    title(ws, f"Every NCAA tournament team — {era.lower()}",
          "November = the team's games in November of that season. Top 40 = that season's pre-tournament top 40 by Strongside net "
          "rating; the top-40 record counts November games only. Exit round = the round the team lost in. First Four included.")
    head = ["Year", "Team", "Seed", "Exit round", "Tourney W", "Tourney L", "Tourney record", "Nov W", "Nov L", "November record",
            "Nov top-40 W", "Nov top-40 L", "November record vs top 40", "Nov top-40 games"]
    H = 4
    header(ws, H, head, 45)
    for i, r in enumerate(rows):
        n = H + 1 + i
        for j, v in enumerate(r, 1):
            if v is not None: ws.cell(row=n, column=j, value=v)
        ws.cell(row=n, column=7, value=f'=E{n}&"-"&F{n}')
        ws.cell(row=n, column=10, value=f'=H{n}&"-"&I{n}')
        ws.cell(row=n, column=13, value=f'=K{n}&"-"&L{n}')
        ws.cell(row=n, column=14, value=f"=K{n}+L{n}")
        for j in range(1, len(head) + 1):
            c = ws.cell(row=n, column=j)
            c.font = font(size=10)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j in (2, 4) else "center")
    last = H + len(rows)
    t = last + 2
    ws.cell(row=t, column=1, value="Totals").font = font(bold=True, size=10)
    for col in "EFHIKL":
        ws[f"{col}{t}"] = f"=SUM({col}{H + 1}:{col}{last})"
    ws[f"G{t}"], ws[f"J{t}"], ws[f"M{t}"], ws[f"N{t}"] = f'=E{t}&"-"&F{t}', f'=H{t}&"-"&I{t}', f'=K{t}&"-"&L{t}', f"=K{t}+L{t}"
    for j in range(2, len(head) + 1):
        ws.cell(row=t, column=j).font = font(bold=True, size=10)
        ws.cell(row=t, column=j).alignment = Alignment(horizontal="center")
    for j, w in enumerate([7, 19, 6, 13, 9, 9, 10, 7, 7, 11, 10, 10, 13, 10], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"C{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"

def sheet_c(wb, name, era, a_name, a_last):
    ws = wb.create_sheet(name)
    title(ws, f"Win % by closing spread and round — {era.lower()}",
          "Straight-up wins, not covers. Spread from the team's side (minus = favorite). Every game counts twice, once from each side, "
          "so each row mirrors its opposite (−9.9 to −5 wins = +5 to +9.9 losses). Counted live from the games sheet.")
    rng = lambda col: f"'{a_name}'!${col}$5:${col}${a_last}"
    rounds, spread, result = rng("C"), rng("H"), rng("I")
    cols = ORDER + ["All rounds"]
    H = 5
    for c, h in ((1, "Closing spread"), (2, "From"), (3, "To")):
        ws.merge_cells(start_row=H - 1, start_column=c, end_row=H, end_column=c)
        cell = ws.cell(row=H - 1, column=c, value=h)
    for k, rd in enumerate(cols):
        j = 4 + 2 * k
        ws.merge_cells(start_row=H - 1, start_column=j, end_row=H - 1, end_column=j + 1)
        ws.cell(row=H - 1, column=j, value=rd)
        ws.cell(row=H, column=j, value="Win %")
        ws.cell(row=H, column=j + 1, value="Games")
    width = 3 + 2 * len(cols)
    for r in (H - 1, H):
        for j in range(1, width + 1):
            c = ws.cell(row=r, column=j)
            c.font = font(bold=True, color="FFFFFF", size=10)
            c.fill = HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = Border(left=Side(style="thin", color="FFFFFF")) if j >= 4 and j % 2 == 0 else Border()
    ws.row_dimensions[H - 1].height = 30
    for i, (label, lo, hi) in enumerate(BUCKETS):
        n = H + 1 + i
        ws.cell(row=n, column=1, value=label)
        ws.cell(row=n, column=2, value=lo)
        ws.cell(row=n, column=3, value=hi)
        for k, rd in enumerate(cols):
            j = 4 + 2 * k
            G, W = get_column_letter(j + 1), get_column_letter(j)
            where = f'{spread},">="&$B{n},{spread},"<="&$C{n}' + (f',{rounds},{W}${H - 1}' if rd != "All rounds" else "")
            ws.cell(row=n, column=j + 1, value=f"=COUNTIFS({where})")
            ws.cell(row=n, column=j, value=f'=IF({G}{n}=0,"",COUNTIFS({where},{result},"W")/{G}{n})').number_format = "0%"
        for j in range(1, width + 1):
            c = ws.cell(row=n, column=j)
            c.font = font(size=10, bold=j == 1, color="8A8F98" if j in (2, 3) else None)
            c.border = Border(bottom=thin, left=Side(style="thin", color="D5D9E0") if j >= 4 and j % 2 == 0 else None)
            c.alignment = Alignment(horizontal="left" if j == 1 else "center")
        ws.row_dimensions[n].height = 22
    last = H + len(BUCKETS)
    t = last + 1
    ws.cell(row=t, column=1, value="All spreads").font = font(bold=True, size=10)
    for k in range(len(cols)):
        G = get_column_letter(5 + 2 * k)
        c = ws.cell(row=t, column=5 + 2 * k, value=f"=SUM({G}{H + 1}:{G}{last})")
        c.font, c.alignment = font(bold=True, size=10), Alignment(horizontal="center")
    # the gradient: 0% orange, 50% white, 100% blue, the same scale in every round
    for k in range(len(cols)):
        W = get_column_letter(4 + 2 * k)
        ws.conditional_formatting.add(f"{W}{H + 1}:{W}{last}",
                                      ColorScaleRule(start_type="num", start_value=0, start_color="E8743B",
                                                     mid_type="num", mid_value=0.5, mid_color="FFFFFF",
                                                     end_type="num", end_value=1, end_color="2F6EBA"))
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = ws.column_dimensions["C"].width = 6
    for j in range(4, width + 1):
        ws.column_dimensions[get_column_letter(j)].width = 9 if j % 2 == 0 else 7
    ws.cell(row=t + 2, column=1, value="Each win % cell is shaded from orange (0%) through white (50%) to blue (100%). "
                                       "Cells with few games are noisy; check the Games column next to them.").font = font(size=9, italic=True)
    ws.freeze_panes = f"D{H + 1}"

def readme(wb, n_games, n_teams):
    ws = wb.active
    ws.title = "Read me"
    lines = [("NCAA tournament workbook, 2010–2026", True),
             (f"{n_games} games (First Four included; no 2020 tournament), each listed twice, and {n_teams} team seasons.", False),
             ("", False),
             ("A — Games: every game from both sides, with the team's closing spread and its margin at minutes 1–40.", False),
             ("B — Teams: every tournament team with its seed, exit round, November record and November record vs the top 40.", False),
             ("C — Spread grid: win % and number of games by closing spread and round, shaded orange → white → blue.", False),
             ("", False),
             ("Each part comes three ways: All years · Pre-NIL (2010–2021 tournaments) · Post-NIL (2022–2026; NIL began July 2021).", False),
             ("", False),
             ("Sources: minute margins from Strongside's play-by-play (reports/pdem_all_ncaa_tournament.csv); closing lines from BetIQ's", False),
             ("custom trend tool (betiq.teamrankings.com), minus = favorite; November games and the pre-tournament top 40 from the", False),
             ("Strongside pre-tournament pages. BetIQ's game-by-game tool gives closing lines only, so opening lines are not included.", False),
             ("Built by tools/tournament_workbook.py.", False)]
    for i, (text, bold) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = font(bold=bold, size=13 if bold else 10)
    ws.column_dimensions["A"].width = 120

def main():
    games = game_rows()
    teams = team_rows(games)
    wb = Workbook()
    readme(wb, len(games) // 2, len(teams))
    a_last = {}
    for era, keep in ERAS:
        a_last[era] = sheet_a(wb, f"A Games {era}", era, [r for r in games if keep(r[0])])
    for era, keep in ERAS:
        sheet_b(wb, f"B Teams {era}", era, [r for r in teams if keep(r[0])])
    for era, keep in ERAS:
        sheet_c(wb, f"C Spread grid {era}", era, f"A Games {era}", a_last[era])
    path = os.path.join(REPORTS, "tournament_workbook.xlsx")
    wb.save(path)
    print(f"{len(games)} game rows, {len(teams)} team rows -> {path}")
    for era, keep in ERAS:
        g = [r for r in games if keep(r[0])]
        print(f"   {era}: {len(g)} game rows, {sum(keep(r[0]) for r in teams)} teams")
    return games

if __name__ == "__main__":
    main()
