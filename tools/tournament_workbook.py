import os
import csv
from statistics import NormalDist
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from upset_high_seeds import seasons, ROUNDS

# Every NCAA tournament game 2010-2026, from both sides:   python tools/tournament_workbook.py
# A Games   each game as two rows side by side (X vs Y with X's closing spread, then Y vs X with Y's), with the team's margin
#           at the end of every minute, overtimes included (from reports/pdem_all_ncaa_tournament.csv, turned from the lower
#           seed's side to the team's; plus = the team was ahead) and the closing line from
#           reports/tournament_spreads.csv (BetIQ; minus = the team was the favorite). First Four included.
# B Teams   every tournament team: seed, exit round, November record and November record against that season's
#           pre-tournament top 40 (by Strongside net rating), laid out like reports/upset_high_seeds.xlsx, with Era
#           (pre/post NIL) and Half (first/second half of the years) columns to filter on and totals for each split.
# Closing pages    win % and games by closing spread (1-point rows) and round (columns), one page per split: all years,
#                  pre-NIL (2010-2021 tournaments), post-NIL (2022 on; NIL began July 2021), first half (2010-2017),
#                  second half (2018-2026). (Were the C pages.)
# Simulator pages  the same, by Strongside's simulator spread (reports/tourney_sim_spreads.csv: the Tourney spreads page's
#                  1,000,000-run replay, each game from the winner's side) instead of the closing spread. (Were the D pages.)
# Seeds pages      the same, by the team's own seed.
# Only these three are written now, all years only; the other splits, the A and B pages and the read-me below are kept
# in the code but not used.
# Everything is written as plain values with the colours filled in (no formulas or conditional formats), so the sheets
# read the same in any viewer, including ones that don't calculate. Writes reports/tournament_workbook.xlsx.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
ROUND_NAMES = {"First Four": "First Four", **ROUNDS}
ORDER = list(ROUNDS.values())    # First Four games are left out of every page (game_rows skips them)
NIL = 2022                       # first tournament after NIL (July 2021)
HALF = 2018                      # 2010-2017 and 2018-2026 are eight tournaments each (none in 2020)
SPLITS = [("All years", 2010, 2026), ("Pre-NIL", 2010, NIL - 1), ("Post-NIL", NIL, 2026),
          ("First half", 2010, HALF - 1), ("Second half", HALF, 2026)]
# closing-spread rows for C: (label, from, to), 5-point bands mirrored around the pick'em row
BUCKETS = [("−25+", -99, -25), ("−24.9 to −20", -24.9, -20), ("−19.9 to −15", -19.9, -15), ("−14.9 to −10", -14.9, -10),
           ("−9.9 to −5", -9.9, -5), ("−4.9 to −0.1", -4.9, -0.1), ("Pick'em (0)", 0, 0), ("+0.1 to +4.9", 0.1, 4.9),
           ("+5 to +9.9", 5, 9.9), ("+10 to +14.9", 10, 14.9), ("+15 to +19.9", 15, 19.9), ("+20 to +24.9", 20, 24.9),
           ("+25+", 25, 99)]
# the Closing and Simulator pages' rows: 1-point bands up to 24, mirrored around the pick'em row
TABLE_BUCKETS = ([("−24+", -99, -24)] + [(f"−{hi + 0.9:g} to −{hi}", -round(hi + 0.9, 1), -hi) for hi in range(23, 0, -1)] + [("−0.9 to −0.1", -0.9, -0.1)] +
                 [("Pick'em (0)", 0, 0), ("+0.1 to +0.9", 0.1, 0.9)] + [(f"+{lo} to +{lo + 0.9:g}", lo, round(lo + 0.9, 1)) for lo in range(1, 24)] + [("+24+", 24, 99)])
# the Seeds pages' rows: the team's own seed
SEED_BUCKETS = [(f"{s} seed", s, s) for s in range(1, 17)]

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

SIM = {}                         # (date, team) -> the simulator's spread from that team's side (D pages), filled by game_rows
NEW = {}                         # (date, team) -> the separate upset model's spread from that team's side, filled by game_rows
MODEL = {}                       # (date, team) -> the report model's spread from that team's side (Model pages), filled by game_rows
SIM_WP, MODEL_WP = {}, {}        # (date, team) -> that team's win chance in the simulator / the report model
MODEL_CONF = {}                  # (date, team) -> the model's confidence in its own pick (same on both rows of a game)
MODEL_CALL = {}                  # (date, team) -> the model picked the simulator's underdog

def game_rows():
    spreads = {r["game_id"]: r for r in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8"))}
    sims = {r["game_id"]: float(r["sim_spread_winner"]) for r in csv.DictReader(open(os.path.join(REPORTS, "tourney_sim_spreads.csv"), encoding="utf-8"))}
    news = {r["game_id"]: float(r["new_spread_winner"]) for r in csv.DictReader(open(os.path.join(REPORTS, "tourney_newmodel_spreads.csv"), encoding="utf-8"))}
    sim_wp = {r["game_id"]: float(r["sim_win_pct_winner"]) for r in csv.DictReader(open(os.path.join(REPORTS, "tourney_sim_spreads.csv"), encoding="utf-8"))}
    # the model: the report model recalibrated by round group, with who plays in rounds 1-2 (scratchpad m10_model2.py)
    model_rows = list(csv.DictReader(open(os.path.join(REPORTS, "tourney_model2_picks.csv"), encoding="utf-8")))
    model_picks = {r["game_id"]: r["model2_right"] == "1" for r in model_rows}
    model_conf = {r["game_id"]: float(r["model2_confidence"]) for r in model_rows}
    model_call = {r["game_id"]: r["model2_upset_call"] == "1" for r in model_rows}
    pairs = []
    for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_all_ncaa_tournament.csv"), encoding="utf-8")):
        if g["round"] == "First Four": continue
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
            if g["game_id"] in sims:
                SIM[(g["date"].replace("/", "-"), team)] = sign * sims[g["game_id"]] + 0.0
            if g["game_id"] in news:
                NEW[(g["date"].replace("/", "-"), team)] = sign * news[g["game_id"]] + 0.0
            key = (g["date"].replace("/", "-"), team)
            if g["game_id"] in sim_wp:
                SIM_WP[key] = sim_wp[g["game_id"]] if sign == 1 else 1 - sim_wp[g["game_id"]]
            if g["game_id"] in model_picks:
                # the model gives only a pick: -1 = it picks this team to win, +1 = it picks the opponent (so the Compare
                # page's "favorite" for the model is simply its pick). It picked the winner when its pick was right.
                picked_winner = model_picks[g["game_id"]]
                MODEL[key] = -1.0 if picked_winner == (sign == 1) else 1.0
                MODEL_CONF[key] = model_conf[g["game_id"]]; MODEL_CALL[key] = model_call[g["game_id"]]
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

A_NOTE = ("Each game is two rows next to each other: the winner vs the loser, then the loser vs the winner. Closing spread from that team's side "
          "(minus = favorite; BetIQ); simulated spread the same from Strongside's simulator (1,000,000 runs as the teams stood that morning, "
          "to one decimal). PMPM (point margin per minute): the team's point margin at the end of each minute (plus = ahead), shaded grey "
          "(behind) to peach (ahead); overtime games carry on through each 5-minute overtime (blank if no overtime).")

def sheet_a(wb, sections, name="A Games", heading="Every NCAA tournament game from both sides, 2010–2026",
            note=A_NOTE + " First Four included."):
    """sections: [(label or None, game rows)]; a label gets its own bold row above its games."""
    ws = wb.create_sheet(name)
    title(ws, heading, note)
    head = ["Year", "Date", "Round", "Team", "Seed", "Opponent", "Opp seed", "Closing spread", "Simulated spread", "Result", "Score",
            "Final margin", "OT", *MINUTE_HEADS]
    H = 4
    header(ws, H, head, 45)
    small, center = font(size=10), Alignment(horizontal="center")
    pair_line = Side(style="thin", color="8A8F98")
    n = H
    for label, rows in sections:
        if label:
            n += 1
            c = ws.cell(row=n, column=1, value=label)
            c.font = font(bold=True, size=11)
            ws.row_dimensions[n].height = 21
        for i, r in enumerate(rows):
            n += 1
            # the simulator's spread from the team's side goes next to the closing spread
            for j, v in enumerate(r[:8] + [SIM.get((r[1], r[3]))] + r[8:], 1):
                c = ws.cell(row=n, column=j, value=v)
                c.font = small
                if j in (8, 9): c.number_format = '+0.0;−0.0;0.0'
                if j == 12 or j > 13:
                    c.number_format = '+0;−0;0'
                    if j > 13 and v is not None: c.fill = shade(v, -20, 0, 20)
                if j not in (2, 4, 6): c.alignment = center
                if i % 2: c.border = Border(bottom=pair_line)          # a line under each game's pair of rows
    last = n
    for j, w in enumerate([7, 11, 13, 18, 6, 18, 7, 9, 10, 7, 8, 8, 5], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for j in range(14, len(head) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 6 if j < 54 else 8
    ws.freeze_panes = f"E{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"

SPREAD_UPSET = 5                 # a spread upset: the winner was a closing underdog of this many points or more

def seed_upsets():
    """(year, team) of the 169 higher seeds beaten by a team 4+ seed lines worse (reports/pdem_seed_gap_4plus.csv)."""
    return {(int(g["date"][:4]), g["higher_team"]) for g in csv.DictReader(open(os.path.join(REPORTS, "pdem_seed_gap_4plus.csv"), encoding="utf-8"))
            if g["lower_won"] == "yes"}

game_pairs = lambda games: [games[i:i + 2] for i in range(0, len(games), 2)]   # [winner's row, loser's row]
spread_upsets = lambda games: [p for p in game_pairs(games) if p[0][7] >= SPREAD_UPSET]

def sheet_a_seed_upsets(wb, games):
    upset = seed_upsets()
    picked = [p for p in game_pairs(games) if (p[1][0], p[1][3]) in upset and p[0][4] - p[1][4] >= 4]
    assert len(picked) == len(upset), (len(picked), len(upset))
    sections = []
    for s in sorted({p[1][4] for p in picked}):
        mine = [p for p in picked if p[1][4] == s]
        sections.append((f"{s} seeds upset — {len(mine)} game{'s' * (len(mine) != 1)}", [r for p in mine for r in p]))
    sheet_a(wb, sections, "A Upsets by seed", f"The {len(picked)} seed upsets, grouped by the beaten higher seed",
            "Games a team seeded 4+ lines worse won (the 169 teams in upset_high_seeds.xlsx and on B Upset teams vs seed). " + A_NOTE)

def sheet_a_spread_upsets(wb, games):
    picked = spread_upsets(games)
    sections = []
    for label, lo, hi in BUCKETS:
        if lo < SPREAD_UPSET: continue
        mine = [p for p in picked if lo <= p[0][7] <= hi]
        if mine:
            sections.append((f"Underdog {label} won — {len(mine)} game{'s' * (len(mine) != 1)}", [r for p in mine for r in p]))
    sheet_a(wb, sections, "A Spread upsets", f"The {len(picked)} spread upsets: the winner was a +{SPREAD_UPSET} or bigger closing underdog",
            f"Every game the closing underdog won when it was getting {SPREAD_UPSET}+ points, grouped by its spread; First Four included. " + A_NOTE)

def sheet_b_spread_upsets(wb, games, teams):
    """The favorites beaten in the spread upsets, with B's November columns."""
    ws = wb.create_sheet("B Spread upsets")
    by_team = {(r[0], r[3]): r for r in teams}
    picked = sorted(spread_upsets(games), key=lambda p: (p[1][7], p[0][0], p[0][1]))      # biggest favorite first
    title(ws, f"The {len(picked)} favorites beaten as {SPREAD_UPSET}+ point closing favorites",
          f"Each team lost a tournament game it was favored in by {SPREAD_UPSET} or more points at the close (BetIQ); First Four included. "
          "November = the team's games in November of that season; top 40 = that season's pre-tournament top 40. "
          "Filter on Era or Half; counts for each split are under the table.")
    key = [("Key:", None), ("2+ November losses", YELLOW), ("No November games vs top 40 (not battle tested)", ORANGE), ("Both", RED)]
    for i, (text, fill) in enumerate(key):
        c = ws.cell(row=3, column=1 + i * 2, value=text)
        c.font = font(size=9, bold=fill is None)
        if fill: c.fill = PatternFill("solid", fgColor=fill)
    head = ["Year", "Round lost", "Seed", "Team (beaten favorite)", "Closing spread", "Beaten by", "Opp seed", "Score", "Era", "Half",
            "Tourney record", "November record", "November record vs top 40", "Nov top-40 games"]
    H = 5
    header(ws, H, head, 48.75)
    rows = []
    for w, l in picked:
        t = by_team[(l[0], l[3])]
        rows.append(t)
        colour = flag(t[7], t[8] + t[9])
        fill = PatternFill("solid", fgColor=colour) if colour else None
        n = H + len(rows)
        for j, v in enumerate([l[0], l[2], l[4], l[3], l[7], w[3], w[4], l[9], era(l[0]), half(l[0]), f"{t[4]}-{t[5]}",
                               f"{t[6]}-{t[7]}", f"{t[8]}-{t[9]}", t[8] + t[9]], 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j in (2, 4, 6, 9, 10) else "center")
            if j == 5: c.number_format = '+0.0;−0.0;0.0'
            if fill: c.fill = fill
    last = H + len(rows)
    t2 = last + 2
    header(ws, t2, ["Highlighted teams", "Teams", "2+ November losses", "No November games vs top 40", "Both", "", "", "", "", "", "", "", "", ""], 33)
    for k, (split, y0, y1) in enumerate(SPLITS):
        n = t2 + 1 + k
        sel = [r for r in rows if y0 <= r[0] <= y1]
        counts = [len(sel), sum(r[7] >= 2 for r in sel), sum(r[8] + r[9] == 0 for r in sel), sum(r[7] >= 2 and r[8] + r[9] == 0 for r in sel)]
        for j, v in enumerate([f"{split} ({y0}–{y1})"] + counts, 1):
            c = ws.cell(row=n, column=j, value=v)
            c.font = font(size=10, bold=j == 1)
            c.border = Border(bottom=thin)
            c.alignment = Alignment(horizontal="left" if j == 1 else "center")
    ws.cell(row=t2 + len(SPLITS) + 1, column=1,
            value="The 2+ losses and no-top-40 counts each include the teams in Both.").font = font(size=9, italic=True)
    ws.column_dimensions["A"].width = 24
    for j, w in enumerate([16, 8, 22, 10, 18, 8, 9, 10, 12, 11, 13, 15.3, 13.6], 2):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"A{H + 1}"
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

def sheet_b_upsets(wb, teams):
    """The 169 higher seeds upset by a team 4+ seed lines worse (as in reports/upset_high_seeds.xlsx) against the teams at
    their seed in B that were not upset: average tournament, November and November top-40 records, as decimals (e.g.
    2.19-0.94). The non-upset teams are every other B team at the seed that reached the round of 64 (First Four losers
    left out)."""
    ws = wb.create_sheet("B Upset teams vs seed")
    upset = seed_upsets()
    by_seed = {}
    for r in teams:
        if r[1] != "First Four": by_seed.setdefault(r[2], []).append(r)
    avg = lambda rows, i: sum(r[i] for r in rows) / len(rows)
    # (W column, L column) in B's rows: tournament, November, November vs the top 40
    RECORDS = [("tournament", 4, 5), ("November", 6, 7), ("November vs top 40", 8, 9)]
    rec = lambda rows, w, l: f"{avg(rows, w):.2f}-{avg(rows, l):.2f}"
    picked = [r for r in teams if (r[0], r[3]) in upset]
    assert len(picked) == len(upset), (len(picked), len(upset))
    # the teams at each seed that were not upset
    others = {s: [r for r in rows if (r[0], r[3]) not in upset] for s, rows in by_seed.items()}

    title(ws, f"The {len(picked)} upset higher seeds against the teams at their seeds that were not upset",
          "Higher seeds beaten by a team 4+ seed lines worse, 2010–2026 (the teams in upset_high_seeds.xlsx). Records are averages "
          "(wins-losses per team, so they can be decimals). Non-upset teams = every other B team at that seed that reached the "
          "round of 64 (First Four losers left out). November vs top 40 = November games against that season's pre-tournament top 40.")

    def table(top, head, rows, fills=None, first_bold=False):
        header(ws, top, head, 48.75)
        for i, vals in enumerate(rows):
            n = top + 1 + i
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=n, column=j, value=v)
                c.font = font(size=10, bold=first_bold and j == 1)
                c.border = Border(bottom=thin)
                c.alignment = Alignment(horizontal="left" if j in (2, 4) and not first_bold else "center")
                if fills and fills[i]: c.fill = fills[i]
        return top + len(rows)

    # by seed: the average non-upset team at the seed next to the average upset team at the seed
    head = ["Seed", "Non-upset teams", "Upset teams"]
    for name, _, _ in RECORDS:
        head += [f"Non-upset teams avg {name} record", f"Upset teams avg {name} record"]
    seeds = sorted({r[2] for r in picked})
    seed_rows = []
    for s in seeds:
        mine = [r for r in picked if r[2] == s]
        row = [s, len(others[s]), len(mine)]
        for _, w, l in RECORDS:
            row += [rec(others[s], w, l), rec(mine, w, l)]
        seed_rows.append(row)
    ws.cell(row=4, column=1, value="By seed").font = font(bold=True, size=11)
    end = table(5, head, seed_rows, first_bold=True)
    t = end + 1
    rest = [r for s in seeds for r in others[s]]
    total = ["All", len(rest), len(picked)]
    for _, w, l in RECORDS:
        total += [rec(rest, w, l), rec(picked, w, l)]
    for j, v in enumerate(total, 1):
        c = ws.cell(row=t, column=j, value=v)
        c.font, c.alignment = font(bold=True, size=10), Alignment(horizontal="center")
    ws.cell(row=t + 1, column=1, value=f"All: every non-upset team at seeds {seeds[0]}–{seeds[-1]} against every upset team.").font = font(size=9, italic=True)

    # each upset team, laid out like upset_high_seeds.xlsx, with its seed's non-upset average records beside its own
    top = t + 4
    ws.cell(row=top - 1, column=1, value="Each upset team").font = font(bold=True, size=11)
    key = [("Key:", None), ("2+ November losses", YELLOW), ("No November games vs top 40 (not battle tested)", ORANGE), ("Both", RED)]
    for i, (text, fill) in enumerate(key):
        c = ws.cell(row=top - 1, column=3 + i * 2, value=text)
        c.font = font(size=9, bold=fill is None)
        if fill: c.fill = PatternFill("solid", fgColor=fill)
    order = ORDER + ["Champion"]
    picked.sort(key=lambda r: (-order.index(r[1]), r[0], r[2], r[3]))
    rows, fills = [], []
    for r in picked:
        row = [r[0], r[1], r[2], r[3]]
        for _, w, l in RECORDS:
            row += [f"{r[w]}-{r[l]}", rec(others[r[2]], w, l)]
        rows.append(row)
        colour = flag(r[7], r[8] + r[9])
        fills.append(PatternFill("solid", fgColor=colour) if colour else None)
    head = ["Year", "Exit round", "Seed", "Team (upset)"]
    for name, _, _ in RECORDS:
        head += [f"Team {name} record", f"Non-upset teams avg {name} record"]
    last = table(top, head, rows, fills=fills)
    for j, w in enumerate([10.9, 16, 12, 19, 14, 14, 14, 14, 15.3, 15.3], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"A{top + 1}"
    ws.auto_filter.ref = f"A{top}:{get_column_letter(len(head))}{last}"

M_NOTE = ("The model's spread: the model's own chance for the team (each game predicted by a version built without that tournament) "
          "turned into points on the simulator's scale (11.33 points per standard unit, measured on the simulator's own spreads and win %), "
          "from the team's side (minus = the model's pick). Straight-up wins. Every game counts twice, once from each side, so each row "
          "mirrors its opposite; the 'All favorites' row is the model's picks. A game the model calls within 0.05 of even goes to its pick's side.")
MODEL_POINTS = 11.33
def model_spread(r):
    """the model's chance for this row's team as a point spread (minus = the model's pick); None if no pick"""
    key = (r[1], r[3]); mod, conf = MODEL.get(key), MODEL_CONF.get(key)
    if mod is None or conf is None: return None
    p = min(max(conf if mod < 0 else 1 - conf, 1e-6), 1 - 1e-6)
    v = round(-MODEL_POINTS * NormalDist().inv_cdf(p), 1)
    return v if v != 0 else (-0.1 if mod < 0 else 0.1)

D_NOTE = ("The simulator's spread: each game played 1,000,000 times in Strongside's simulator (the Tourney spreads page) as the two teams "
          "stood that morning, with only the players who really played, to one decimal; from the team's side (minus = "
          "favorite). Straight-up wins. Every game counts twice, once from each side, so each row mirrors its opposite.")

NEW_NOTE = ("The new model's spread: a model separate from the simulator (no spread, rating, seed or simulator number), built from "
            "each team's season before the game (records vs strong and weak teams, box-score profile, matchups, play-by-play habits, "
            "roster, game-to-game swings) and fitted only on earlier tournament games (2010 and early 2011 on the other seasons); each "
            "game played 1,000,000 times around its margin. From the team's side (minus = favorite). Straight-up wins; every game counts twice.")

MODEL_NOTE = ("The model's spread: our own team ratings and schedule strength plus the 27 measures from the upset study that were "
              "significant and did not repeat each other. One number per game: the model's predicted margin, no simulated games. "
              "Every tournament is predicted by a model fitted without it. From the team's side "
              "(minus = favorite). Straight-up wins; every game counts twice. See the Model notes page.")

SEED_NOTE = ("Straight-up wins by the team's own seed in each round. Every game counts twice, once from each side "
             "(a 5 beating a 12 is a 5-seed win and a 12-seed loss).")

def sheet_c(wb, split, y0, y1, games, page="Closing", spread=lambda r: r[7], label="Closing spread", what="closing spread", note=None,
            buckets=TABLE_BUCKETS):
    """A Closing page (by the closing spread); with spread=the simulator's, a Simulator page; with spread=the seed and
    buckets=SEED_BUCKETS, a Seeds page."""
    ws = wb.create_sheet(f"{page} {split}")
    years = f"{y0}–{y1}" + (" (no 2020 tournament)" if y0 <= 2020 <= y1 else "")
    title(ws, f"Win % by {what} and round — {split.lower()}, {years}",
          note or "Straight-up wins, not covers. Spread from the team's side (minus = favorite). Every game counts twice, once from each side, "
                  "so each row mirrors its opposite (−5.9 to −5 wins = +5 to +5.9 losses).")
    sel = [r + [spread(r)] for r in games if y0 <= r[0] <= y1 and spread(r) is not None]
    key = len(sel[0]) - 1 if sel else 0                  # the spread these rows are sorted by, added at the end
    cols = ORDER + ["All rounds"]
    H = 5
    ws.merge_cells(start_row=H - 1, start_column=1, end_row=H, end_column=1)
    ws.cell(row=H - 1, column=1, value=label)
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
    grid = [[[r for r in sel if lo <= r[key] <= hi and (rd == "All rounds" or r[2] == rd)] for rd in cols] for _, lo, hi in buckets]
    most = max(len(cell) for row in grid for cell in row[:-1]) or 1          # the All rounds column has its own scale
    most_all = max(len(row[-1]) for row in grid) or 1
    for i, (label, lo, hi) in enumerate(buckets):
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
    last = H + len(buckets)
    t = last + 1
    # every row above pick'em added up: how the favorites did (the rows below are the same games from the underdog's side)
    favorites = [row for row, (_, lo, hi) in zip(grid, buckets) if hi < 0]
    if favorites: ws.cell(row=t, column=1, value="All favorites").font = font(bold=True, size=10)
    for k in range(len(cols) if favorites else 0):
        wins = sum(sum(r[8] == "W" for r in row[k]) for row in favorites)
        games = sum(len(row[k]) for row in favorites)
        for d, v in ((0, wins / games if games else "–"), (1, f"{wins}-{games - wins}" if games else "–"), (2, games)):
            c = ws.cell(row=t, column=2 + S * k + d, value=v)
            c.font, c.alignment = font(bold=True, size=10), Alignment(horizontal="center")
            if d == 0: c.number_format = "0.0%"
            if d < 2 and games: c.fill = shade(wins / games, 0, 0.5, 1)
    ws.column_dimensions["A"].width = 16
    for j in range(2, width + 1):
        ws.column_dimensions[get_column_letter(j)].width = (8, 9, 7)[(j - 2) % S]
    ws.cell(row=t + 2, column=1, value="Win % and record are shaded grey (0%) through off-white (50%) to peach (100%); games are shaded off-white to peach "
                                       "by how many there are; – = no games. Cells with few games are noisy.").font = font(size=9, italic=True)
    ws.freeze_panes = f"B{H + 1}"

def sheet_compare(wb, games, models, pairs=((2, 1), (2, 0), (1, 0))):
    """Favorites' straight-up record by round for each spread (closing, simulator, the models), side by side, then for
    each pair (indexes into models) how often they pick different favorites and who was right when they did."""
    ws = wb.create_sheet("Compare All years")
    title(ws, "Favorites picked — " + " vs ".join(n for n, _ in models) + ", all years, 2010–2026 (no 2020 tournament)",
          "Each game once, from the favorite's side by that spread; pick'ems (0) left out. Straight-up wins, not covers. "
          "For a model, the 'favorite' is simply its pick.")
    H = 5
    cols = ORDER + ["All rounds"]
    ws.cell(row=H, column=1, value="Round")
    for k, (name, _) in enumerate(models):
        for d, h in enumerate(("Win %", "Record", "Games")):
            ws.cell(row=H - 1 if d == 0 else H, column=2 + 3 * k + d, value=name if d == 0 else h)
        ws.cell(row=H, column=2 + 3 * k, value="Win %")
        ws.merge_cells(start_row=H - 1, start_column=2 + 3 * k, end_row=H - 1, end_column=4 + 3 * k)
    for r in (H - 1, H):
        for j in range(1, 2 + 3 * len(models)):
            c = ws.cell(row=r, column=j)
            c.font, c.fill = font(bold=True, color="FFFFFF", size=10), HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center")
    favs = [r for r in games if r[8] == "W" or r[8] == "L"]
    for i, rd in enumerate(cols):
        n = H + 1 + i
        ws.cell(row=n, column=1, value=rd).font = font(bold=(rd == "All rounds"), size=10)
        for k, (_, sp) in enumerate(models):
            # each game from its favorite's side only: the row whose spread is below zero
            cell = [r for r in favs if (rd == "All rounds" or r[2] == rd) and sp(r) is not None and sp(r) < 0]
            wins = sum(r[8] == "W" for r in cell)
            for d, v in ((0, wins / len(cell) if cell else "–"), (1, f"{wins}-{len(cell) - wins}" if cell else "–"), (2, len(cell))):
                c = ws.cell(row=n, column=2 + 3 * k + d, value=v)
                c.font, c.alignment = font(size=10, bold=(rd == "All rounds")), Alignment(horizontal="center")
                if d == 0: c.number_format = "0.0%"
                if d < 2 and cell: c.fill = shade(wins / len(cell), 0, 0.5, 1)
    # how often two of them pick different favorites, and who was right when they did (each game once, from the winner's
    # row: a spread below zero there means that one picked the winner; games either one calls a pick'em are left out)
    pairs = [(models[a], models[b]) for a, b in pairs]
    t = H + len(cols) + 2
    ws.cell(row=t - 1, column=1, value="Different favorites picked").font = font(bold=True, size=11)
    S2 = 5
    for k, ((na, a), (nb, b)) in enumerate(pairs):
        j = 2 + S2 * k
        ws.merge_cells(start_row=t, start_column=j, end_row=t, end_column=j + S2 - 1)
        ws.cell(row=t, column=j, value=f"{na} vs {nb.lower() if nb == 'Closing line' else nb}")
        for d, h in enumerate(("Games", "Different", "% different", f"{na} right", f"{nb} right")):
            ws.cell(row=t + 1, column=j + d, value=h)
    ws.cell(row=t + 1, column=1, value="Round")
    for r in (t, t + 1):
        for j in range(1, 2 + S2 * len(pairs)):
            c = ws.cell(row=r, column=j)
            c.font, c.fill = font(bold=True, color="FFFFFF", size=10), HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[t + 1].height = 30
    winners = [r for r in games if r[8] == "W"]
    for i, rd in enumerate(cols):
        n = t + 2 + i
        ws.cell(row=n, column=1, value=rd).font = font(bold=(rd == "All rounds"), size=10)
        for k, ((_, a), (_, b)) in enumerate(pairs):
            sel = [r for r in winners if (rd == "All rounds" or r[2] == rd) and a(r) and b(r)]
            diff = [r for r in sel if (a(r) < 0) != (b(r) < 0)]
            a_right = sum(a(r) < 0 for r in diff)
            vals = (len(sel), len(diff), len(diff) / len(sel) if sel else "–", a_right, len(diff) - a_right)
            for d, v in enumerate(vals):
                c = ws.cell(row=n, column=2 + S2 * k + d, value=v)
                c.font, c.alignment = font(size=10, bold=(rd == "All rounds")), Alignment(horizontal="center")
                if d == 2: c.number_format = "0.0%"
    ws.column_dimensions["A"].width = 22
    for j in range(2, 2 + S2 * len(pairs)):
        ws.column_dimensions[get_column_letter(j)].width = 11
    ws.freeze_panes = f"B{H + 1}"

def readme(wb, n_games, n_teams):
    ws = wb.active
    ws.title = "Read me"
    lines = [("NCAA tournament workbook, 2010–2026", True),
             (f"{n_games} games (First Four included; no 2020 tournament), each listed twice, and {n_teams} team seasons.", False),
             ("", False),
             ("A Games — every game from both sides, with the team's closing spread and its PMPM (point margin per minute) for minutes 1–40 and any overtime.", False),
             ("A Upsets by seed — the 169 seed upsets (winner seeded 4+ lines worse), grouped by the beaten higher seed.", False),
             (f"A Spread upsets — every game a +{SPREAD_UPSET} or bigger closing underdog won, grouped by its spread.", False),
             ("B Teams — every tournament team: seed, exit round, November record and November record vs the top 40.", False),
             ("    Filter on Era (Pre-NIL / Post-NIL) or Half (First half / Second half); totals for each split are under the table.", False),
             ("B Upset teams vs seed — the 169 upset higher seeds against the teams at their seed that were not upset.", False),
             (f"B Spread upsets — the favorites beaten as {SPREAD_UPSET}+ point closing favorites, with their November records.", False),
             ("C pages — win % and games by closing spread and round, all shaded, one page per split:", False),
             ("    All years · Pre-NIL (2010–2021) · Post-NIL (2022–2026; NIL began July 2021) · "
              f"First half (2010–{HALF - 1}) · Second half ({HALF}–2026)", False),
             ("D pages — the same, by Strongside's simulator spread instead of the closing spread (each game played 1,000,000 times as the", False),
             ("    teams stood that morning, only the players who really played; reports/tourney_sim_spreads.csv, from the Tourney spreads page).", False),
             ("", False),
             ("Sources: PMPM from Strongside's play-by-play (reports/pdem_all_ncaa_tournament.csv); closing lines from BetIQ's", False),
             ("custom trend tool (betiq.teamrankings.com), minus = favorite; November games and the pre-tournament top 40 from the", False),
             ("Strongside pre-tournament pages. BetIQ's game-by-game tool gives closing lines only, so opening lines are not included.", False),
             ("Built by tools/tournament_workbook.py.", False)]
    for i, (text, bold) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = font(bold=bold, size=13 if bold else 10)
    ws.column_dimensions["A"].width = 120

RIGHT_FILL, WRONG_FILL, EVEN_FILL = PatternFill("solid", fgColor="D9EAD3"), PatternFill("solid", fgColor="F4CCCC"), PatternFill("solid", fgColor="EEEEEE")

def sheet_model_games(wb, games):
    """Model games: every tournament game once, the closing line, the simulator and the model side by side, each one's
    pick marked right or wrong; filter on any column."""
    ws = wb.create_sheet("Model games")
    title(ws, "Every NCAA tournament game, 2010–2026: closing line vs simulator vs model",
          "One row per game, winner first. Spreads from the winner's side (minus = the winner was favored, plus = it was the underdog). "
          "Win % = the winner's chance. Model confidence = how sure the model is of its own pick (50–100%). Green = that one picked the winner, red = it picked the loser, grey = pick'em. "
          "Upset call = the model picked the simulator's underdog. Filter on any column.")
    head = ["Year", "Date", "Round", "Winner", "Seed", "Loser", "Seed", "Score", "Closing line", "Closing pick",
            "Simulator spread", "Simulator win %", "Simulator pick", "Model picked", "Model confidence", "Model pick", "Seed upset", "Model vs simulator",
            "Upset call"]
    H = 4
    header(ws, H, head, 32)
    winners = sorted([r for r in games if r[8] == "W"], key=lambda r: (r[1], ORDER.index(r[2]), r[3]))
    mark = lambda s: ("pick'em", EVEN_FILL) if s is None or s == 0 else (("right", RIGHT_FILL) if s < 0 else ("wrong", WRONG_FILL))
    tally = {"Closing pick": [0, 0, 0], "Simulator pick": [0, 0, 0], "Model pick": [0, 0, 0]}
    calls = [0, 0]                                       # the model's upset calls right, wrong
    for i, r in enumerate(winners):
        key = (r[1], r[3]); n = H + 1 + i
        sim, mod = SIM.get(key), MODEL.get(key)
        picks = {"Closing pick": mark(r[7]), "Simulator pick": mark(sim), "Model pick": mark(mod)}
        for k_, (word, _) in picks.items(): tally[k_][("right", "wrong", "pick'em").index(word)] += 1
        differ = "" if sim is None or mod is None or sim == 0 or mod == 0 or (sim < 0) == (mod < 0) else ("model right" if mod < 0 else "simulator right")
        call = "" if not MODEL_CALL.get(key) else ("upset right" if mod < 0 else "upset wrong")
        if call: calls[0 if mod < 0 else 1] += 1
        vals = [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[9], r[7], picks["Closing pick"][0], sim, SIM_WP.get(key), picks["Simulator pick"][0],
                None if mod is None else (r[3] if mod < 0 else r[5]), MODEL_CONF.get(key), picks["Model pick"][0], "yes" if r[4] > r[6] else "", differ, call]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=n, column=j, value=v); c.font = font(size=10); c.alignment = Alignment(horizontal="left" if j in (3, 4, 6) else "center")
            h_ = head[j - 1]
            if h_ in picks: c.fill = picks[h_][1]
            if (h_.endswith("win %") or h_.endswith("confidence")) and v is not None: c.number_format = "0.0%"
            if h_ in ("Closing line", "Simulator spread") and v is not None: c.number_format = "+0.0;-0.0;0.0"
            if h_ == "Model vs simulator" and v: c.fill = RIGHT_FILL if v == "model right" else WRONG_FILL
            if h_ == "Upset call" and v: c.fill = RIGHT_FILL if v == "upset right" else WRONG_FILL
    last = H + len(winners)
    t = last + 2
    ws.cell(row=t, column=1, value="Totals").font = font(bold=True, size=11)
    for i, (k_, (rt, wr, pk)) in enumerate(tally.items()):
        ws.cell(row=t + 1 + i, column=1, value=k_.replace(" pick", "")).font = font(size=10)
        ws.cell(row=t + 1 + i, column=2, value=f"{rt}-{wr}" + (f" ({pk} pick'em)" if pk else "")).font = font(size=10, bold=True)
        ws.cell(row=t + 1 + i, column=3, value=rt / (rt + wr) if rt + wr else None).number_format = "0.0%"
    n_ = t + 1 + len(tally)
    ws.cell(row=n_, column=1, value="Model upset calls").font = font(size=10)
    ws.cell(row=n_, column=2, value=f"{calls[0]}-{calls[1]}").font = font(size=10, bold=True)
    ws.cell(row=n_, column=3, value=calls[0] / sum(calls) if sum(calls) else None).number_format = "0.0%"
    for j, w in enumerate((6, 11, 13, 20, 6, 20, 6, 9, 9, 9, 10, 10, 10, 20, 11, 9, 8, 15, 13), 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = f"E{H + 1}"
    ws.auto_filter.ref = f"A{H}:{get_column_letter(len(head))}{last}"

LEECH_POS = [("Pick'em (0)", 0, 0), ("+0.1 to +0.9", 0.1, 0.9)] + [(f"+{lo} to +{lo + 0.9:g}", lo, round(lo + 0.9, 1)) for lo in range(1, 24)] + [("+24+", 24, 99)]
LEECH_NEG = [("Pick'em (0)", 0, 0), ("−0.1 to −0.9", -0.9, -0.1)] + [(f"−{lo} to −{lo + 0.9:g}", -round(lo + 0.9, 1), -lo) for lo in range(1, 24)] + [("−24+", -99, -24)]

def leech_split(games):
    """the games where the simulator favors one team and the model picks the other: (the simulator's underdog row,
    the simulator's favorite row) for each. A simulator pick'em (0.0) counts by which side its win % leans."""
    by_game = {}
    for r in games: by_game.setdefault((r[1], frozenset((r[3], r[5]))), []).append(r)
    out = []
    for pair in by_game.values():
        if len(pair) != 2: continue
        a, b = pair
        sa, ma = SIM.get((a[1], a[3])), MODEL.get((a[1], a[3]))
        if sa is None or ma is None: continue
        if sa == 0:
            fav_is_a = SIM_WP.get((a[1], a[3]), 0.5) > 0.5
        else:
            fav_is_a = sa < 0
        fav, dog = (a, b) if fav_is_a else (b, a)
        if MODEL.get((dog[1], dog[3]), 1) < 0: out.append((dog, fav))
    return out

def leech_games(games, mdl=None):
    """every game except the simulator's pick'ems (spread 0.0): (favorite row, underdog row, the model likes the underdog)"""
    mdl = MODEL if mdl is None else mdl
    by_game = {}
    for r in games: by_game.setdefault((r[1], frozenset((r[3], r[5]))), []).append(r)
    out = []
    for pair in by_game.values():
        if len(pair) != 2: continue
        a, b = pair; sa = SIM.get((a[1], a[3]))
        if sa is None or sa == 0 or mdl.get((a[1], a[3])) is None: continue
        fav, dog = (a, b) if sa < 0 else (b, a)
        out.append((fav, dog, mdl.get((dog[1], dog[3])) < 0))
    return out

def sheet_leech(wb, games, side, mdl=None, page=None):
    """The full chart (every spread band, both sides, each game counted twice like the Simulator page) for one way of
    picking: 'model' = the leech (the model's pick when it likes the simulator's underdog, the simulator's otherwise),
    'sim' = always the simulator's favorite. A row counts as a win when this page's pick in that game was right, so
    every band shows how often the page's pick was right in games at that spread. Pick'ems (0.0) are left out.
    mdl / page: another model's picks on its own page."""
    trip = leech_games(games, mdl)
    n = len(trip); flips = [t_ for t_ in trip if t_[2]]
    # the Simulator page's layout, each team's real result: the top half (favorites) is every favorite on both pages;
    # the bottom half (underdogs) is every underdog on the simulator page, and only the underdogs the model picked on
    # the model page - so the bottom half's win % shows what taking the model's upset picks does
    rows = [f for f, d, l in trip] + [d for f, d, l in trip]
    # the model flips a game when it picks the simulator's underdog: that underdog takes the favorite's side of the
    # chart (the same spread, mirrored) and the simulator's favorite moves to the underdog's side
    flipped = {(r[1], r[3]) for f, d, l in flips for r in (f, d)}
    spread = (lambda r: -SIM.get((r[1], r[3])) if (r[1], r[3]) in flipped else SIM.get((r[1], r[3]))) if side == "model" else (lambda r: SIM.get((r[1], r[3])))
    picks_right = sum(1 for f, d, l in trip if (d if (side == "model" and l) else f)[8] == "W")
    page = page or ("Leech – go with model" if side == "model" else "Leech – go with simulator")
    pk = sum(1 for r in games if SIM.get((r[1], r[3])) == 0) // 2
    if side == "model":
        note = (f"The simulator's chart ({n} games, its {pk} pick'ems left out), then the model flips the {len(flips)} games where it picks the simulator's "
                "underdog: that team moves to the favorite's side at the same spread, mirrored, and the simulator's favorite moves to the underdog's side. "
                f"Top half = the pick in every game: right {picks_right} of {n} ({picks_right / n:.1%}). Every game counts twice, so each row mirrors its opposite.")
    else:
        note = (f"Exactly what the simulator outputs ({n} games, its {pk} pick'ems left out): each team's real result by the simulator's spread, every game "
                f"counted twice. Top half = the simulator's pick in every game: right {picks_right} of {n} ({picks_right / n:.1%}). "
                "Compare with 'go with model', where the model flips the games it disagrees on.")
    sheet_c(wb, "", 2010, 2026, rows, page, spread, "Simulator spread", "the simulator's spread", note)
    ws = wb[f"{page} "]
    ws.title = page
    who = "the model"
    ws["A1"] = (f"Leech - the simulator's chart with {who}'s flips: win % by spread and round ({who}'s picks sit on the favorite's side)"
                if side == "model" else "Leech - the simulator's chart as it comes: win % by the simulator's spread and round")
    if side == "sim": return
    trip = flips
    # the games underneath
    t = ws.max_row + 2
    ws.cell(row=t, column=1, value=f"The {n} games").font = font(bold=True, size=11)
    head = ["Year", "Round", "Simulator favorite", "Seed", "Simulator underdog", "Seed", "Simulator line", "Simulator win % (fav)",
            "Model likes the underdog", "Winner", "Score", "This page's pick", "Right?"]
    for j, h in enumerate(head, 1):
        c = ws.cell(row=t + 1, column=j, value=h); c.font = font(bold=True, color="FFFFFF", size=10); c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[t + 1].height = 30
    for i, (f, d, likes_dog) in enumerate(sorted(trip, key=lambda p: p[0][1])):
        winner = d if d[8] == "W" else f; mine = d if (side == "model" and likes_dog) else f
        vals = [d[0], d[2], f[3], f[4], d[3], d[4], SIM.get((f[1], f[3])), SIM_WP.get((f[1], f[3])), "yes" if likes_dog else "",
                winner[3], winner[9], mine[3], "right" if mine[8] == "W" else "wrong"]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=t + 2 + i, column=j, value=v); c.font = font(size=10); c.alignment = Alignment(horizontal="left" if j in (2, 3, 5, 10, 12) else "center")
            if j == 7 and v is not None: c.number_format = "+0.0;-0.0;0.0"
            if j == 8 and v is not None: c.number_format = "0.0%"
            if j == 13: c.fill = RIGHT_FILL if v == "right" else WRONG_FILL

LEECH_BANDS = [("0.1 to 2.9", 0.1, 2.9), ("3 to 5.9", 3, 5.9), ("6 to 9.9", 6, 9.9), ("10 to 14.9", 10, 14.9), ("15+", 15, 99)]

def sheet_leech_compare(wb, games):
    """Leech compare: always the simulator's favorite vs the leech with the model (its pick when it likes the simulator's
    underdog), by round and by the simulator's line, with charts. Same games as the Leech pages (pick'ems left out)."""
    ws = wb.create_sheet("Leech compare")
    trip = leech_games(games)
    ways = [("Simulator", lambda f, d, l: f), ("Model", lambda f, d, l: d if l else f)]
    title(ws, "Leech compare — simulator vs model, 2010–2026",
          f"The same {len(trip)} games as the Leech pages (the simulator's pick'ems left out). Simulator = always its favorite; Model = the "
          "leech: the model's pick when it likes the simulator's underdog, the simulator's favorite otherwise. Flips = games where the model took the "
          "simulator's underdog, and how many of those it got right. 'Extra winners' = winners right minus the simulator's.")

    def table(top, label, groups):
        """groups: [(name, rows)]; returns the first data row and the last"""
        heads = [label] + [f"{n} {h}" for n, _ in ways for h in ("win %", "record")] + ["Model flips", "Model extra winners", "Games"]
        for j, h in enumerate(heads, 1):
            c = ws.cell(row=top, column=j, value=h); c.font = font(bold=True, color="FFFFFF", size=10); c.fill = HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[top].height = 30
        for i, (name, sel) in enumerate(groups):
            n = top + 1 + i; bold = name.startswith("All")
            rights = [sum(pick(f, d, l)[8] == "W" for f, d, l in sel) for _, pick in ways]
            fl = [t_ for t_ in sel if t_[2]]
            flips = f"{sum(t_[1][8] == 'W' for t_ in fl)}-{sum(t_[1][8] != 'W' for t_ in fl)}" if fl else "–"
            vals = [name]
            for r_ in rights: vals += [r_ / len(sel) if sel else None, f"{r_}-{len(sel) - r_}" if sel else "–"]
            vals += [flips, rights[1] - rights[0], len(sel)]
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=n, column=j, value=v); c.font = font(size=10, bold=bold); c.alignment = Alignment(horizontal="left" if j == 1 else "center")
                if j in (2, 4) and v is not None:
                    c.number_format = "0.0%"; c.fill = shade(v, 0, 0.5, 1)
                if j == 7: c.number_format = "+0;-0;0"
        return top + 1, top + len(groups)

    H = 4
    rounds = [(rd, [t_ for t_ in trip if t_[0][2] == rd]) for rd in ORDER] + [("All rounds", trip)]
    rounds = [(n, s) for n, s in rounds if s]
    r0, r1 = table(H, "Round", rounds)
    line = lambda t_: -SIM.get((t_[0][1], t_[0][3]))                  # the favorite's line, as a positive number
    bands = [(nm, [t_ for t_ in trip if lo <= round(line(t_), 1) <= hi]) for nm, lo, hi in LEECH_BANDS] + [("All lines", trip)]
    T2 = r1 + 3
    ws.cell(row=T2 - 1, column=1, value="By the simulator's line (the favorite's spread)").font = font(bold=True, size=11)
    b0, b1 = table(T2, "Simulator line", bands)
    for j, w in enumerate((16, 10, 10, 10, 10, 11, 11, 8), 1):
        ws.column_dimensions[get_column_letter(j)].width = w

    colors = ("8A8F98", "2F6DB5")                                       # simulator grey, model blue
    def chart(title_, cols, first, last, anchor, y_title, fmt, lo=None, hi=None):
        ch = BarChart(); ch.type = "col"; ch.grouping = "clustered"; ch.title = title_; ch.y_axis.title = y_title
        ch.y_axis.numFmt = fmt; ch.height, ch.width = 8, 18; ch.gapWidth = 60
        if lo is not None: ch.y_axis.scaling.min = lo
        if hi is not None: ch.y_axis.scaling.max = hi
        for col, colr in cols:
            ch.add_data(Reference(ws, min_col=col, min_row=first - 1, max_row=last), titles_from_data=True)
            s = ch.series[-1]; s.graphicalProperties.solidFill = colr; s.graphicalProperties.line.solidFill = colr
        ch.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
        ch.y_axis.delete = False; ch.x_axis.delete = False; ch.legend.position = "b"
        ws.add_chart(ch, anchor)
    chart("Winners picked right, by round", [(2, colors[0]), (4, colors[1])], r0, r1, f"J{H}", "Win %", "0%", 0, 1)
    chart("Model's extra winners vs the simulator, by round", [(7, colors[1])], r0, r1 - 1, f"J{H + 17}", "Games", "+0;-0;0")
    chart("Winners picked right, by the simulator's line", [(2, colors[0]), (4, colors[1])], b0, b1, f"J{H + 34}", "Win %", "0%", 0, 1)
    ws.freeze_panes = f"B{H + 1}"

CONF_BLOCKS = [(f"{lo}–{lo + 5}%", lo / 100, (lo + 5) / 100 if lo < 95 else 1.01) for lo in range(95, 45, -5)]

def sheet_model_scorecard(wb, games):
    """Model scorecard: every game once, by how sure the model was (5-point blocks of its confidence in its pick) and
    round: the model's win % and record, and the simulator's record on the same games beside it."""
    ws = wb.create_sheet("Model scorecard")
    title(ws, "Model scorecard — how often the model's pick won, by how sure it was and round, 2010–2026 (no 2020 tournament)",
          "Each game counted once. Confidence = the model's chance for the team it picked (each game predicted by a version built without "
          "that tournament). Win % and record = the model's picks in that block; Simulator = the simulator's record on the same games "
          "(its pick'ems left out). Win % is shaded grey (0%) through off-white (50%) to peach (100%); the simulator's record is green "
          "where the model won more of those games, red where the simulator did.")
    winners = [r for r in games if r[8] == "W"]
    cols = ORDER + ["All rounds"]
    S = 3
    H = 5
    ws.merge_cells(start_row=H - 1, start_column=1, end_row=H, end_column=1)
    ws.cell(row=H - 1, column=1, value="Model's confidence")
    for k, rd in enumerate(cols):
        j = 2 + S * k
        ws.merge_cells(start_row=H - 1, start_column=j, end_row=H - 1, end_column=j + S - 1)
        ws.cell(row=H - 1, column=j, value=rd)
        for d, h in enumerate(("Win %", "Record", "Simulator")):
            ws.cell(row=H, column=j + d, value=h)
    width = 1 + S * len(cols)
    for r in (H - 1, H):
        for j in range(1, width + 1):
            c = ws.cell(row=r, column=j); c.font = font(bold=True, color="FFFFFF", size=10); c.fill = HEAD_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[H - 1].height = 30
    def tally(sel):
        m_right = sum(MODEL.get((r[1], r[3]), 1) < 0 for r in sel)
        s_games = [r for r in sel if SIM.get((r[1], r[3])) not in (None, 0)]
        s_right = sum(SIM.get((r[1], r[3])) < 0 for r in s_games)
        return m_right, len(sel), s_right, len(s_games)
    blocks = CONF_BLOCKS + [("All games", 0.0, 1.01)]
    for i, (label, lo, hi) in enumerate(blocks):
        n = H + 1 + i; last = label == "All games"
        c = ws.cell(row=n, column=1, value=label); c.font = font(size=10, bold=True); c.border = Border(bottom=thin)
        for k, rd in enumerate(cols):
            j = 2 + S * k
            sel = [r for r in winners if (rd == "All rounds" or r[2] == rd) and MODEL_CONF.get((r[1], r[3])) is not None
                   and lo <= MODEL_CONF[(r[1], r[3])] < hi]
            if not sel:
                for d in range(S): ws.cell(row=n, column=j + d, value="–").alignment = Alignment(horizontal="center")
                continue
            mr, mn, sr, sn = tally(sel)
            pct = ws.cell(row=n, column=j, value=mr / mn); pct.number_format = "0%"; pct.fill = shade(mr / mn, 0, 0.5, 1)
            rec = ws.cell(row=n, column=j + 1, value=f"{mr}-{mn - mr}"); rec.fill = shade(mr / mn, 0, 0.5, 1)
            sim = ws.cell(row=n, column=j + 2, value=f"{sr}-{sn - sr}" if sn else "–")
            # compare on the same games: model wins per game vs simulator wins per game (the simulator skips its pick'ems)
            if sn and mr / mn > sr / sn + 1e-9: sim.fill = RIGHT_FILL
            elif sn and mr / mn < sr / sn - 1e-9: sim.fill = WRONG_FILL
            for c in (pct, rec, sim):
                c.font = font(size=10, bold=last); c.alignment = Alignment(horizontal="center")
                c.border = Border(bottom=Side(style="thin", color="FFFFFF"), left=Side(style="thin", color="FFFFFF"))
        ws.row_dimensions[n].height = 22
    ws.column_dimensions["A"].width = 18
    for j in range(2, width + 1):
        ws.column_dimensions[get_column_letter(j)].width = (7, 9, 9)[(j - 2) % S]
    ws.freeze_panes = f"B{H + 1}"

def sheet_model_notes(wb):
    ws = wb.create_sheet("Model notes")
    lines = [("The model: what it is and how it was tested", True), ("", False),
             ("What goes in", True),
             ("- Strength: our own adjusted efficiency margin and schedule strength (not the simulator's numbers, not the betting line).", False),
             ("- The upset study's significant measures, with repeats removed: when two measures moved together (correlation 0.3 or more) only the", False),
             ("  stronger one stayed, and measures that only re-measure strength were dropped. 27 remain: close second-half play, the ball-dominant", False),
             ("  star, zone-style defense, biggest leads / first halves, tempo, turnovers forced, offensive rebounding, comebacks, careless turnovers,", False),
             ("  mid-range share, missing players and a set of play types. Each game is oriented by our ratings (stronger vs weaker team).", False),
             ("- These 30 levers (3 strength + 27 measures) give a base chance. The tournament is split in three parts, each with one line:", False),
             ("  rounds 1-2 and Sweet 16 + Elite Eight each recalibrate the base chance on their own games, so its chances match how often", False),
             ("  teams really won there; the Final Four and title game get their own line trained on those games, blended 15% with 85% the", False),
             ("  simulator's chance (only 48 games: the line alone went 28-20 there, the simulator 36-12; at 85% the picks match the simulator's).", False),
             ("- First Four games are cut from everything: not used to fit the model, not predicted, and not on any page of this workbook.", False),
             ("- Rounds 1-2 also see who played in the game, for both teams: the value of the rotation players who sat, whether the best", False),
             ("  player sat, and the BPM of the players who played. (Before a game this comes from the injury report.)", False),
             ("- Every round also sees two more gaps between the teams: the coach's career NCAA tournament appearances and Sweet 16 runs in the", False),
             ("  last 5 seasons (from Sports Reference, before the season), and how much the top player's usage stands out from his teammates.", False),
             ("- Recent tournaments count more: a season counts half as much as one 12 years newer (stronger data in recent years).", False),
             ("- Through the Elite Eight it never sees the simulator's chance; it never sees the closing line. Confidence = its chance for its pick.", False),
             ("", False), ("How it was tested", True),
             ("- Every tournament is predicted by a model built on the other 15 tournaments only (the 30 levers refitted too), so no game's", False),
             ("  own result is ever used. All 1,007 games, 2010-2026, round of 64 through the final.", False),
             ("", False), ("Results (picking winners)", True),
             ("- Model 756-251 (75.1%, a pick in every game); simulator 722-285; closing line 714-280 plus 13 pick'ems.", False),
             ("- Round of 64 386/511 (75.5%), round of 32 202/256 (78.9%), Sweet 16 88/128 (68.8%), Elite Eight 44/64 (68.8%),", False),
             ("  Final Four 23/32 and title game 13/16 (the simulator's picks).", False),
             ("- Upset calls (it picked the simulator's underdog): 141, right 87 (62%). Where model and simulator disagree: model 87, simulator 53", False),
             ("  (p = 0.005). See the Compare and Model games pages.", False),
             ("- Calibration: picks it gave 50-60% were right 62%, 60-70% right 66%, 70-80% right 76%, 80-90% right 82%, 90%+ right 94%.", False),
             ("- Significance: ahead of the simulator in 11 of 16 tournaments, behind in 1; resampling whole tournaments, the 34-game edge never", False),
             ("  reached zero (plausible range 18-50).", False),
             ("- Overfitting check: the same version fitted on all 16 tournaments and scored on them gets 775, 19 more than held out - the same", False),
             ("  gap as the two-part version (20), so the split adds none. Choosing among the split versions with each tournament unseen also", False),
             ("  gives 756. Still the best of about 30 tried, and the Final Four idea came from seeing the model lose there, so the edge is a", False),
             ("  little optimistic.", False),             ("", False), ("Caveats", True),
             ("- The 27 measures were chosen after the upset study looked at all games, and who plays was left out of the later rounds after", False),
             ("  seeing it hurt there (only 192 games), so treat the edge as somewhat optimistic. One tournament can swing 5 games either way.", False),
             ("- Larger searches (40 groups of measures, re-weighting the levers, the simulator as an input) did no better on unseen tournaments.", False),
             ("  No version singles out the famous 15-over-2 upsets ahead of time.", False),
             ("", False), ("Built by: scratchpad m10_model2.py -> reports/tourney_model2_picks.csv; pages by tools/tournament_workbook.py.", False)]
    for i, (text, bold) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = font(bold=bold, size=12 if bold else 10)
    ws.column_dimensions["A"].width = 130

def main():
    games = game_rows()
    teams = team_rows(games)
    wb = Workbook()
    wb.remove(wb.active)
    # only the win % tables (the A and B pages and the read-me are still here in the code, not written; the earlier
    # "New model" page is replaced by the report model's Model page)
    split, y0, y1 = SPLITS[0]                             # all years only (the other splits are still in SPLITS)
    sheet_c(wb, split, y0, y1, games)
    sheet_c(wb, split, y0, y1, games, "Simulator", lambda r: SIM.get((r[1], r[3])), "Simulator spread", "the simulator's spread", D_NOTE)
    sheet_c(wb, split, y0, y1, games, "Seeds", lambda r: r[4], "Seed", "seed", SEED_NOTE, SEED_BUCKETS)
    sheet_compare(wb, games, [("Closing line", lambda r: r[7]), ("Simulator", lambda r: SIM.get((r[1], r[3]))),
                              ("Model", lambda r: MODEL.get((r[1], r[3])))])
    sheet_c(wb, split, y0, y1, games, "Model", model_spread, "Model spread", "the model's spread", M_NOTE)
    sheet_model_scorecard(wb, games)
    sheet_model_games(wb, games)
    sheet_model_notes(wb)
    path = os.path.join(REPORTS, "tournament_workbook.xlsx")
    wb.save(path)
    print(f"{len(games)} game rows, {len(teams)} team rows -> {path}")
    return games

if __name__ == "__main__":
    main()
