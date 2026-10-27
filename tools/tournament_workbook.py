import os
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from upset_high_seeds import seasons, ROUNDS

# Every NCAA tournament game 2010-2026, from both sides:   python tools/tournament_workbook.py
# A Games   each game as two rows side by side (X vs Y with X's closing spread, then Y vs X with Y's), with the team's margin
#           at the end of every minute, overtimes included (from reports/pdem_all_ncaa_tournament.csv, turned from the lower
#           seed's side to the team's; plus = the team was ahead) and the closing line from
#           reports/tournament_spreads.csv (BetIQ; minus = the team was the favorite). First Four included.
# B Teams   every tournament team: seed, exit round, November record and November record against that season's
#           pre-tournament top 40 (by Strongside net rating), laid out like reports/upset_high_seeds.xlsx, with Era
#           (pre/post NIL) and Half (first/second half of the years) columns to filter on and totals for each split.
# C pages   win % and games by closing spread (rows) and round (columns), one page per split: all years, pre-NIL
#           (2010-2021 tournaments), post-NIL (2022 on; NIL began July 2021), first half (2010-2017), second half (2018-2026).
# Everything is written as plain values with the colours filled in (no formulas or conditional formats), so the sheets
# read the same in any viewer, including ones that don't calculate. Writes reports/tournament_workbook.xlsx.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
ROUND_NAMES = {"First Four": "First Four", **ROUNDS}
ORDER = list(ROUND_NAMES.values())
NIL = 2022                       # first tournament after NIL (July 2021)
HALF = 2018                      # 2010-2017 and 2018-2026 are eight tournaments each (none in 2020)
SPLITS = [("All years", 2010, 2026), ("Pre-NIL", 2010, NIL - 1), ("Post-NIL", NIL, 2026),
          ("First half", 2010, HALF - 1), ("Second half", HALF, 2026)]
# closing-spread rows for C: (label, from, to), 5-point bands mirrored around the pick'em row
BUCKETS = [("−25+", -99, -25), ("−24.9 to −20", -24.9, -20), ("−19.9 to −15", -19.9, -15), ("−14.9 to −10", -14.9, -10),
           ("−9.9 to −5", -9.9, -5), ("−4.9 to −0.1", -4.9, -0.1), ("Pick'em (0)", 0, 0), ("+0.1 to +4.9", 0.1, 4.9),
           ("+5 to +9.9", 5, 9.9), ("+10 to +14.9", 10, 14.9), ("+15 to +19.9", 15, 19.9), ("+20 to +24.9", 20, 24.9),
           ("+25+", 25, 99)]

MINUTES = 50                     # regulation plus two overtimes, the longest tournament game here
OT_LABEL = {45: "1 OT", 50: "2 OT"}
MINUTE_HEADS = [f"PMPM {i}" for i in range(1, 41)] + [f"PMPM OT{(i - 41) // 5 + 1}-{(i - 41) % 5 + 1}" for i in range(41, MINUTES + 1)]

font = lambda **k: Font(name="Arial", **k)
HEAD_FILL = PatternFill("solid", fgColor="14213D")
thin = Side(style="thin", color="D5D9E0")
LOW, MID, HIGH = "A3A8B0", "F4F2EF", "EDBBA0"      # the gradient: grey (low) -> off-white -> peach (high)
YELLOW, ORANGE, RED = "FFF2A8", "FFC98B", "F4A6A6"
era = lambda y: "Pre-NIL" if y < NIL else "Post-NIL"
half = lambda y: "First half" if y < HALF else "Second half"
_fills = {}

def shade(x, lo, mid, hi):
    """The gradient's fill for x on a lo / mid / hi scale (clamped at the ends)."""
    a, b, f = (LOW, MID, (x - lo) / (mid - lo)) if x <= mid else (MID, HIGH, (x - mid) / (hi - mid))
    f = min(max(f, 0), 1)
    rgb = "".join(f"{round(int(a[i:i + 2], 16) + (int(b[i:i + 2], 16) - int(a[i:i + 2], 16)) * f):02X}" for i in (0, 2, 4))
    if rgb not in _fills: _fills[rgb] = PatternFill("solid", fgColor=rgb)
    return _fills[rgb]

def flag(nov_l, top40_games):
    """B's highlight: red = both, yellow = 2+ November losses, orange = no November games vs the top 40."""
    if nov_l >= 2 and top40_games == 0: return RED
    if nov_l >= 2: return YELLOW
    if top40_games == 0: return ORANGE
    return None

def game_rows():
    spreads = {r["game_id"]: r for r in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8"))}
    pairs = []
    for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")):
        s = spreads[g["game_id"]]
        wp, lp = int(g["winner_pts"]), int(g["loser_pts"])
        minutes = int(g["minutes"])
        # PMPM margins are from the lower seed's side (the winner's when the seeds are equal); turn them to the winner's side.
        # Minutes 1-40, then each overtime's five minutes (41-45, 46-50); blank where the game didn't go that long.
        side = 1 if int(g["final_margin"]) > 0 else -1
        margins = [side * int(g[f"m{i}"]) if i <= minutes else None for i in range(1, MINUTES + 1)]
        pair = []
        for team, opp, seed, oseed, sign, pts, opts in ((g["winner"], g["loser"], g["winner_seed"], g["loser_seed"], 1, wp, lp),
                                                        (g["loser"], g["winner"], g["loser_seed"], g["winner_seed"], -1, lp, wp)):
            line = float(s["spread"]) if team == s["favorite"] else -float(s["spread"])
            pair.append([int(g["date"][:4]), g["date"].replace("/", "-"), ROUND_NAMES[g["round"]], team, int(seed), opp, int(oseed),
                         line + 0.0, "W" if sign == 1 else "L", f"{pts}-{opts}", pts - opts, OT_LABEL.get(minutes, ""),
                         *[None if m is None else sign * m + 0 for m in margins]])
        pairs.append(pair)
    # each game's two rows stay together, the winner first
    pairs.sort(key=lambda p: (p[0][0], p[0][1], ORDER.index(p[0][2]), min(p[0][3], p[1][3])))
    return [row for pair in pairs for row in pair]

def team_rows(games):
    """[year, exit round, seed, team, tourney W, tourney L, Nov W, Nov L, Nov top-40 W, Nov top-40 L]"""
    pages = seasons()
    teams = {}
    for r in games:                                      # one entry per team per year; its loss is its exit
        t = teams.setdefault((r[0], r[3]), {"seed": r[4], "w": 0, "l": 0, "exit": None})
        t["w" if r[8] == "W" else "l"] += 1
        if r[8] == "L": t["exit"] = r[2]
    season_of = {int(g["date"][:4]): g["season"] for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8"))}
    rows, missing = [], []
    for (year, name), t in teams.items():
        sched, top = pages[season_of[year]]
        if name not in sched: missing.append(f"{year} {name}")
        nov = [x for x in sched.get(name, []) if x["d"][5:7] == "11"]
        vs = [x for x in nov if x["opp"] in top]          # November games against the top 40 only
        rows.append([year, t["exit"] or "Champion", t["seed"], name, t["w"], t["l"],
                     sum(x["pf"] > x["pa"] for x in nov), sum(x["pf"] < x["pa"] for x in nov),
                     sum(x["pf"] > x["pa"] for x in vs), sum(x["pf"] < x["pa"] for x in vs)])
    if missing: print("   no schedule for:", missing)
    exits = ORDER + ["Champion"]
    rows.sort(key=lambda r: (-exits.index(r[1]), r[0], r[2], r[3]))     # deepest exit round first, then year, then seed
    return rows

def header(ws, row, names, height):
    for j, h in enumerate(names, 1):
        c = ws.cell(row=row, column=j, value=h)
        c.font = font(bold=True, color="FFFFFF")
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = height

def title(ws, text, note):
    ws["A1"] = text
    ws["A1"].font = font(bold=True, size=13)
    ws["A2"] = note
    ws["A2"].font = font(size=9, italic=True)
    ws.row_dimensions[1].height = 16.5

def sheet_a(wb, rows):
    ws = wb.create_sheet("A Games")
    title(ws, "Every NCAA tournament game from both sides, 2010–2026",
          "Each game is two rows next to each other: the winner vs the loser, then the loser vs the winner. Closing spread from that team's side "
          "(minus = favorite; BetIQ). PMPM (point margin per minute): the team's point margin at the end of each minute (plus = ahead), shaded grey "
          "(behind) to peach (ahead); overtime games carry on through each 5-minute overtime (blank if no overtime). First Four included.")
    head = ["Year", "Date", "Round", "Team", "Seed", "Opponent", "Opp seed", "Closing spread", "Result", "Score", "Final margin", "OT",
            *MINUTE_HEADS]
    H = 4
    header(ws, H, head, 45)
    small, center = font(size=10), Alignment(horizontal="center")
    pair_line = Side(style="thin", color="8A8F98")
    for i, r in enumerate(rows):
        n = H + 1 + i
        for j, v in enumerate(r, 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = small
            if j == 8: c.number_format = '+0.0;−0.0;0.0'
            if j == 11 or j > 12:
                c.number_format = '+0;−0;0'
                if j > 12 and v is not None: c.fill = shade(v, -20, 0, 20)
            if j not in (2, 4, 6): c.alignment = center
            if i % 2: c.border = Border(bottom=pair_line)          # a line under each game's pair of rows
    last = H + len(rows)
    for j, w in enumerate([7, 11, 13, 18, 6, 18, 7, 9, 7, 8, 8, 5], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for j in range(13, len(head) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 6 if j < 53 else 8
    ws.freeze_panes = f"E{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"

def sheet_b(wb, rows):
    """Laid out like reports/upset_high_seeds.xlsx; Era and Half are there to filter on."""
    ws = wb.create_sheet("B Teams")
    title(ws, "Every NCAA tournament team, 2010–2026",
          f"{len(rows)} teams (First Four included). November = the team's games in November of that season. Top 40 = that season's "
          "pre-tournament top 40 by Strongside net rating; the top-40 record counts November games only. Filter on Era (NIL began July 2021) "
          f"or Half (first half 2010–{HALF - 1}, second half {HALF}–2026); totals for each split are under the table.")
    key = [("Key:", None), ("2+ November losses", YELLOW), ("No November games vs top 40 (not battle tested)", ORANGE), ("Both", RED)]
    for i, (text, fill) in enumerate(key):
        c = ws.cell(row=3, column=1 + i * 2, value=text)
        c.font = font(size=9, bold=fill is None)
        if fill: c.fill = PatternFill("solid", fgColor=fill)
    head = ["Year", "Exit round", "Seed", "Team", "Era", "Half", "Tourney record", "Nov W", "Nov L", "November record",
            "Nov top-40 W", "Nov top-40 L", "November record vs top 40", "Nov top-40 games"]
    H = 5
    header(ws, H, head, 48.75)
    for i, (year, exit_, seed, name, tw, tl, nw, nl, vw, vl) in enumerate(rows):
        n = H + 1 + i
        colour = flag(nl, vw + vl)
        fill = PatternFill("solid", fgColor=colour) if colour else None
        for j, v in enumerate([year, exit_, seed, name, era(year), half(year), f"{tw}-{tl}", nw, nl, f"{nw}-{nl}",
                               vw, vl, f"{vw}-{vl}", vw + vl], 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j in (2, 4, 5, 6) else "center")
            if fill: c.fill = fill
    last = H + len(rows)
    # totals for each split, side by side under the table
    t = last + 2
    sub = ["Totals", "Teams", "", "", "", "", "", "Nov W", "Nov L", "November record", "Nov top-40 W", "Nov top-40 L",
           "November record vs top 40", "Nov top-40 games"]
    header(ws, t, sub, 33)
    for k, (split, y0, y1) in enumerate(SPLITS):
        n = t + 1 + k
        sel = [r for r in rows if y0 <= r[0] <= y1]
        nw, nl, vw, vl = (sum(r[i] for r in sel) for i in (6, 7, 8, 9))
        for j, v in enumerate([f"{split} ({y0}–{y1})", len(sel), "", "", "", "", "", nw, nl, f"{nw}-{nl}", vw, vl, f"{vw}-{vl}", vw + vl], 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10, bold=j == 1)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j == 1 else "center")
    t2 = t + len(SPLITS) + 2
    header(ws, t2, ["Highlighted teams", "Teams", "2+ November losses", "No November games vs top 40", "Both", "", "", "", "", "", "", "", "", ""], 33)
    for k, (split, y0, y1) in enumerate(SPLITS):
        n = t2 + 1 + k
        sel = [r for r in rows if y0 <= r[0] <= y1]
        counts = [len(sel), sum(r[7] >= 2 for r in sel), sum(r[8] + r[9] == 0 for r in sel),
                  sum(r[7] >= 2 and r[8] + r[9] == 0 for r in sel)]
        for j, v in enumerate([f"{split} ({y0}–{y1})"] + counts, 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10, bold=j == 1)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j == 1 else "center")
    ws.cell(row=t2 + len(SPLITS) + 1, column=1,
            value="The 2+ losses and no-top-40 counts each include the teams in Both.").font = font(size=9, italic=True)
    widths = [10.9, 16, 17.7, 19, 12, 13, 11.6, 9.7, 11.6, 15.3, 13.6, 13.6, 15.3, 13.6]
    ws.column_dimensions["A"].width = 24                 # wide enough for the split names in the totals
    for j, w in enumerate(widths[1:], 2):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"A{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"

EXIT_SCORE = {"Round of 64": 1, "Round of 32": 2, "Sweet 16": 3, "Elite Eight": 4, "Final Four": 5, "Championship": 6, "Champion": 7}

def sheet_b_upsets(wb, teams):
    """The 169 higher seeds upset by a team 4+ seed lines worse (as in reports/upset_high_seeds.xlsx) against the average
    team at their seed in B. Exit score: out in the round of 64 = 1 ... lost the final = 6, champion = 7. First Four losers
    have no score and are left out of the seed averages (every upset team reached the round of 64)."""
    ws = wb.create_sheet("B Upset teams vs seed")
    upset = {(int(g["date"][:4]), g["higher_team"]) for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_seed_gap_4plus.csv"), encoding="utf-8"))
             if g["lower_won"] == "yes"}
    by_seed = {}
    for r in teams:
        if r[1] in EXIT_SCORE: by_seed.setdefault(r[2], []).append(r)
    avg = lambda rows, f: sum(f(r) for r in rows) / len(rows)
    stats = [("exit", lambda r: EXIT_SCORE[r[1]]), ("nw", lambda r: r[6]), ("nl", lambda r: r[7]),
             ("vw", lambda r: r[8]), ("vl", lambda r: r[9]), ("vg", lambda r: r[8] + r[9])]
    seed_avg = {s: {k: avg(rows, f) for k, f in stats} for s, rows in by_seed.items()}
    picked = [r for r in teams if (r[0], r[3]) in upset]
    assert len(picked) == len(upset), (len(picked), len(upset))

    title(ws, f"The {len(picked)} upset higher seeds against the average team at their seed",
          "Higher seeds beaten by a team 4+ seed lines worse, 2010–2026 (the teams in upset_high_seeds.xlsx). Exit score: out in the "
          "round of 64 = 1, round of 32 = 2, Sweet 16 = 3, Elite Eight = 4, Final Four = 5, lost the final = 6, champion = 7. "
          "Seed average = every B team at that seed that reached the round of 64 (First Four losers left out). Diff = team minus seed average.")
    key = [("Key:", None), ("2+ November losses", YELLOW), ("No November games vs top 40 (not battle tested)", ORANGE), ("Both", RED)]
    for i, (text, fill) in enumerate(key):
        c = ws.cell(row=3, column=1 + i * 2, value=text)
        c.font = font(size=9, bold=fill is None)
        if fill: c.fill = PatternFill("solid", fgColor=fill)

    def table(top, head, rows, height=48.75, fills=None, fmt=None):
        header(ws, top, head, height)
        for i, vals in enumerate(rows):
            n = top + 1 + i
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=n, column=j, value=round(v, 2) if isinstance(v, float) else v)
                c.font = font(size=10, bold=fmt == "bold" and j == 1)
                c.border = Border(bottom=thin)
                c.alignment = Alignment(horizontal="left" if j in (2, 4) and fmt != "bold" else "center")
                if isinstance(v, float): c.number_format = '+0.00;−0.00;0.00' if "Diff" in head[j - 1] else "0.00"
                if fills and fills[i]: c.fill = fills[i]
        return top + len(rows)

    # per seed: all teams at the seed against the upset teams at the seed
    seeds = sorted({r[2] for r in picked})
    seed_rows = []
    for s in seeds:
        mine = [r for r in picked if r[2] == s]
        a, u = seed_avg[s], {k: avg(mine, f) for k, f in stats}
        seed_rows.append([s, len(by_seed[s]), len(mine), a["exit"], u["exit"], u["exit"] - a["exit"], a["nl"], u["nl"], u["nl"] - a["nl"],
                          a["vg"], u["vg"], u["vg"] - a["vg"], f"{a['vw']:.1f}-{a['vl']:.1f}", f"{u['vw']:.1f}-{u['vl']:.1f}"])
    ws.cell(row=5, column=1, value="By seed").font = font(bold=True, size=11)
    end = table(6, ["Seed", "Teams at seed", "Upset teams", "Seed avg exit score", "Upset teams avg exit score", "Diff exit score",
                    "Seed avg Nov L", "Upset teams avg Nov L", "Diff Nov L", "Seed avg Nov top-40 games",
                    "Upset teams avg Nov top-40 games", "Diff Nov top-40 games", "Seed avg Nov top-40 record",
                    "Upset teams avg Nov top-40 record"], seed_rows, fmt="bold")
    # exit-score difference shaded: grey = went out earlier than the seed's average
    for i in range(len(seed_rows)):
        ws.cell(row=7 + i, column=6).fill = shade(seed_rows[i][5], -3, 0, 3)

    # per team, laid out like upset_high_seeds.xlsx
    order = ORDER + ["Champion"]
    picked.sort(key=lambda r: (-order.index(r[1]), r[0], r[2], r[3]))
    team_rows_, fills = [], []
    for year, exit_, seed, name, tw, tl, nw, nl, vw, vl in picked:
        a = seed_avg[seed]
        team_rows_.append([year, exit_, seed, name, EXIT_SCORE[exit_], a["exit"], EXIT_SCORE[exit_] - a["exit"],
                           f"{nw}-{nl}", nl, a["nl"], nl - a["nl"], f"{vw}-{vl}", vw + vl, a["vg"], vw + vl - a["vg"]])
        colour = flag(nl, vw + vl)
        fills.append(PatternFill("solid", fgColor=colour) if colour else None)
    top = end + 3
    ws.cell(row=top - 1, column=1, value="Each upset team").font = font(bold=True, size=11)
    last = table(top, ["Year", "Exit round", "Seed", "Team (upset)", "Exit score", "Seed avg exit score", "Diff exit score",
                       "November record", "Nov L", "Seed avg Nov L", "Diff Nov L", "November record vs top 40",
                       "Nov top-40 games", "Seed avg Nov top-40 games", "Diff Nov top-40 games"], team_rows_, fills=fills)
    t = last + 2
    allp = {k: avg(picked, f) for k, f in stats}
    exp = {k: avg(picked, lambda r, k=k: seed_avg[r[2]][k]) for k, _ in stats}
    ws.cell(row=t, column=1, value=f"All {len(picked)} upset teams").font = font(bold=True, size=10)
    for j, v in ((5, allp["exit"]), (6, exp["exit"]), (7, allp["exit"] - exp["exit"]), (9, allp["nl"]), (10, exp["nl"]),
                 (11, allp["nl"] - exp["nl"]), (13, allp["vg"]), (14, exp["vg"]), (15, allp["vg"] - exp["vg"])):
        c = ws.cell(row=t, column=j, value=round(v, 2))
        c.font, c.alignment = font(bold=True, size=10), Alignment(horizontal="center")
        c.number_format = '+0.00;−0.00;0.00' if j in (7, 11, 15) else "0.00"
    ws.cell(row=t + 1, column=1, value="Averages over the upset teams; the seed-average columns weight each seed by how many upset teams it has.").font = font(size=9, italic=True)
    for j, w in enumerate([10.9, 16, 12, 19, 12, 13, 12, 13, 9.7, 12, 11, 15.3, 13.6, 14, 13.6], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"A{top + 1}"
    ws.auto_filter.ref = f"A{top}:O{last}"
    print(f"   upset teams: exit score {allp['exit']:.2f} vs seed average {exp['exit']:.2f}; Nov L {allp['nl']:.2f} vs {exp['nl']:.2f};"
          f" top-40 games {allp['vg']:.2f} vs {exp['vg']:.2f}")

def sheet_c(wb, split, y0, y1, games):
    ws = wb.create_sheet(f"C {split}")
    years = f"{y0}–{y1}" + (" (no 2020 tournament)" if y0 <= 2020 <= y1 else "")
    title(ws, f"Win % by closing spread and round — {split.lower()}, {years}",
          "Straight-up wins, not covers. Spread from the team's side (minus = favorite). Every game counts twice, once from each side, "
          "so each row mirrors its opposite (−9.9 to −5 wins = +5 to +9.9 losses).")
    sel = [r for r in games if y0 <= r[0] <= y1]
    cols = ORDER + ["All rounds"]
    H = 5
    ws.merge_cells(start_row=H - 1, start_column=1, end_row=H, end_column=1)
    ws.cell(row=H - 1, column=1, value="Closing spread")
    S = 3                                                # columns per round: win %, record, games
    for k, rd in enumerate(cols):
        j = 2 + S * k
        ws.merge_cells(start_row=H - 1, start_column=j, end_row=H - 1, end_column=j + S - 1)
        ws.cell(row=H - 1, column=j, value=rd)
        for d, h in enumerate(("Win %", "Record", "Games")):
            ws.cell(row=H, column=j + d, value=h)
    width = 1 + S * len(cols)
    for r in (H - 1, H):
        for j in range(1, width + 1):
            c = ws.cell(row=r, column=j)
            c.font = font(bold=True, color="FFFFFF", size=10)
            c.fill = HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = Border(left=Side(style="thin", color="FFFFFF")) if j >= 2 and (j - 2) % S == 0 else Border()
    ws.row_dimensions[H - 1].height = 30
    grid = [[[r for r in sel if lo <= r[7] <= hi and (rd == "All rounds" or r[2] == rd)] for rd in cols] for _, lo, hi in BUCKETS]
    most = max(len(cell) for row in grid for cell in row[:-1]) or 1          # the All rounds column has its own scale
    most_all = max(len(row[-1]) for row in grid) or 1
    for i, (label, lo, hi) in enumerate(BUCKETS):
        n = H + 1 + i
        c = ws.cell(row=n, column=1, value=label)
        c.font, c.alignment, c.border = font(size=10, bold=True), Alignment(horizontal="left"), Border(bottom=thin)
        for k, cell in enumerate(grid[i]):
            j = 2 + S * k
            wins = sum(r[8] == "W" for r in cell)
            pct = ws.cell(row=n, column=j, value=wins / len(cell) if cell else "–")
            rec = ws.cell(row=n, column=j + 1, value=f"{wins}-{len(cell) - wins}" if cell else "–")
            cnt = ws.cell(row=n, column=j + 2, value=len(cell))
            pct.number_format = "0%"
            pct.fill = rec.fill = shade(wins / len(cell), 0, 0.5, 1) if cell else shade(0.5, 0, 0.5, 1)
            top = most_all if k == len(cols) - 1 else most
            cnt.fill = shade(len(cell) / top, -1, 0, 1)
            for c in (pct, rec, cnt):
                c.font = font(size=10, color="8A8F98" if not cell else None)
                c.alignment = Alignment(horizontal="center")
                c.border = Border(bottom=Side(style="thin", color="FFFFFF"), left=Side(style="thin", color="FFFFFF"))
        ws.row_dimensions[n].height = 22
    last = H + len(BUCKETS)
    t = last + 1
    ws.cell(row=t, column=1, value="All spreads").font = font(bold=True, size=10)
    for k in range(len(cols)):
        for d, v in ((1, f"{sum(sum(r[8] == 'W' for r in row[k]) for row in grid)}-{sum(sum(r[8] == 'L' for r in row[k]) for row in grid)}"),
                     (2, sum(len(row[k]) for row in grid))):
            c = ws.cell(row=t, column=2 + S * k + d, value=v)
            c.font, c.alignment = font(bold=True, size=10), Alignment(horizontal="center")
    ws.column_dimensions["A"].width = 16
    for j in range(2, width + 1):
        ws.column_dimensions[get_column_letter(j)].width = (8, 9, 7)[(j - 2) % S]
    ws.cell(row=t + 2, column=1, value="Win % and record are shaded grey (0%) through off-white (50%) to peach (100%); games are shaded off-white to peach "
                                       "by how many there are; – = no games. Cells with few games are noisy.").font = font(size=9, italic=True)
    ws.freeze_panes = f"B{H + 1}"

def readme(wb, n_games, n_teams):
    ws = wb.active
    ws.title = "Read me"
    lines = [("NCAA tournament workbook, 2010–2026", True),
             (f"{n_games} games (First Four included; no 2020 tournament), each listed twice, and {n_teams} team seasons.", False),
             ("", False),
             ("A Games — every game from both sides, with the team's closing spread and its PMPM (point margin per minute) for minutes 1–40 and any overtime.", False),
             ("B Teams — every tournament team: seed, exit round, November record and November record vs the top 40.", False),
             ("    Filter on Era (Pre-NIL / Post-NIL) or Half (First half / Second half); totals for each split are under the table.", False),
             ("C pages — win % and games by closing spread and round, all shaded, one page per split:", False),
             ("    All years · Pre-NIL (2010–2021) · Post-NIL (2022–2026; NIL began July 2021) · "
              f"First half (2010–{HALF - 1}) · Second half ({HALF}–2026)", False),
             ("", False),
             ("Sources: PMPM from Strongside's play-by-play (reports/pdem_all_ncaa_tournament.csv); closing lines from BetIQ's", False),
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
    sheet_a(wb, games)
    sheet_b(wb, teams)
    sheet_b_upsets(wb, teams)
    for split, y0, y1 in SPLITS:
        sheet_c(wb, split, y0, y1, games)
    path = os.path.join(REPORTS, "tournament_workbook.xlsx")
    wb.save(path)
    print(f"{len(games)} game rows, {len(teams)} team rows -> {path}")
    return games

if __name__ == "__main__":
    main()
