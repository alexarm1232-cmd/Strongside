# Every game with play-by-play, 2009-10 to 2025-26, laid out exactly like "A Games" in the tournament workbook
# (tools/tournament_workbook.py sheet_a): title + note rows, navy header on row 4, each game two rows (winner vs loser,
# then loser vs winner) with a line under the pair, Arial 10, PMPM shaded grey -> off-white -> peach on -20..+20,
# panes frozen at E5, a filter over the table. Seeds and spreads exist only for tournament games, so they stay blank.
# Written in write-only mode (185,000+ rows).
import os, sys, json, time
sys.path.insert(0, r"C:\Users\crtra\Downloads\basketball\tools")
import pdem as P
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
DST = r"C:\Users\crtra\Downloads\PMPM - every game 2010-2026.xlsx"
CODES = [c for c in sorted(os.listdir(P.SEASONS_DIR)) if len(c) == 4 and c.isdigit() and "0910" <= c <= "2526"]
MAXOT = 4
MINUTES = 40 + 5 * MAXOT
MINUTE_HEADS = [f"PMPM {i}" for i in range(1, 41)] + [f"PMPM OT{(i - 41) // 5 + 1}-{(i - 41) % 5 + 1}" for i in range(41, MINUTES + 1)]
OT_LABEL = {45: "OT", 50: "2OT", 55: "3OT", 60: "4OT"}
# ---- A Games' look (tournament_workbook.py)
font = lambda **k: Font(name="Arial", **k)
HEAD_FILL = PatternFill("solid", fgColor="14213D")
LOW, MID, HIGH = "A3A8B0", "F4F2EF", "EDBBA0"
_fills = {}
def shade(x, lo=-20, mid=0, hi=20):
    a, b, f = (LOW, MID, (x - lo) / (mid - lo)) if x <= mid else (MID, HIGH, (x - mid) / (hi - mid))
    f = min(max(f, 0), 1)
    rgb = "".join(f"{round(int(a[i:i + 2], 16) + (int(b[i:i + 2], 16) - int(a[i:i + 2], 16)) * f):02X}" for i in (0, 2, 4))
    if rgb not in _fills: _fills[rgb] = PatternFill("solid", fgColor=rgb)
    return _fills[rgb]
SMALL, CENTER, PAIR = font(size=10), Alignment(horizontal="center"), Border(bottom=Side(style="thin", color="8A8F98"))
HEAD = ["Year", "Date", "Round", "Team", "Seed", "Opponent", "Opp seed", "Closing spread", "Simulated spread", "Result", "Score",
        "Final margin", "OT", *MINUTE_HEADS]
NOTE = ("Each game is two rows next to each other: the winner vs the loser, then the loser vs the winner. PMPM (point margin per minute): "
        "the team's point margin at the end of each minute (plus = ahead), shaded grey (behind) to peach (ahead); overtime games carry on "
        "through each 5-minute overtime, up to four (blank if no overtime). Year = the season's end year. Round = Regular season or "
        "Postseason (conference tournaments, NCAA, NIT and others). Seed and spreads are tournament-only, so they are blank here. "
        "Games with a score but no play-by-play are on the Missing sheet.")
# ---- the games
pairs, missing, t0 = [], [], time.time()
for code in CODES:
    year = 2000 + int(code[2:])
    for gid, (row, path) in P.season_games(code).items():
        try: hs, as_ = int(row["home_score"]), int(row["away_score"])
        except (TypeError, ValueError, KeyError): continue
        if hs == as_: continue
        series = P.pdem(json.load(open(path, encoding="utf-8"))) if os.path.exists(path) else []
        if not series:
            missing.append([P.season_label(code), row.get("date", "").replace("/", "-"), row.get("away_team"), row.get("home_team"), f"{as_}-{hs}"]); continue
        home_won = hs > as_
        win, lose = (row["home_team"], row["away_team"]) if home_won else (row["away_team"], row["home_team"])
        wp, lp = max(hs, as_), min(hs, as_)
        m = [(h - a) if home_won else (a - h) for _, h, a in series][1:]          # winner's side, minutes 1..end
        minutes = len(m)
        margins = [m[i] if i < minutes else None for i in range(MINUTES)]
        date = row["date"].replace("/", "-"); rnd = "Postseason" if row.get("post") else "Regular season"
        ot = OT_LABEL.get(minutes, "" if minutes <= 40 else f"{(minutes - 40) // 5}OT")
        pairs.append([[year, date, rnd, win, None, lose, None, None, None, "W", f"{wp}-{lp}", wp - lp, ot, *margins],
                      [year, date, rnd, lose, None, win, None, None, None, "L", f"{lp}-{wp}", lp - wp, ot, *[None if x is None else -x + 0 for x in margins]]])
    print(f"{P.season_label(code)} read ({time.time() - t0:.0f}s)", flush=True)
pairs.sort(key=lambda p: (p[0][1], p[0][3]))
# ---- write
wb = Workbook(write_only=True)
ws = wb.create_sheet("All Games")
for j, w in enumerate([7, 11, 13, 18, 6, 18, 7, 9, 10, 7, 8, 8, 5], 1): ws.column_dimensions[get_column_letter(j)].width = w
for j in range(14, len(HEAD) + 1): ws.column_dimensions[get_column_letter(j)].width = 6 if j < 54 else 8
ws.freeze_panes = "E5"
last = 4 + 2 * len(pairs)
ws.auto_filter.ref = f"A4:{get_column_letter(len(HEAD))}{last}"
def cell(v, **st):
    c = WriteOnlyCell(ws, value=v)
    for k, x in st.items(): setattr(c, k, x)
    return c
ws.append([cell(f"Every game from both sides, 2009-10 to 2025-26 ({len(pairs):,} games)", font=font(bold=True, size=13))])
ws.append([cell(NOTE, font=font(size=9, italic=True))])
ws.append([])
HFONT, HALIGN = font(bold=True, color="FFFFFF"), Alignment(horizontal="center", vertical="center", wrap_text=True)
ws.append([cell(h, font=HFONT, fill=HEAD_FILL, alignment=HALIGN) for h in HEAD])
FMT1, FMT0 = '+0.0;−0.0;0.0', '+0;−0;0'
for p in pairs:
    for i, r in enumerate(p):
        out = []
        for j, v in enumerate(r, 1):
            st = {"font": SMALL}
            if j in (8, 9): st["number_format"] = FMT1
            if j == 12 or j > 13:
                st["number_format"] = FMT0
                if j > 13 and v is not None: st["fill"] = shade(v)
            if j not in (2, 4, 6): st["alignment"] = CENTER
            if i == 1: st["border"] = PAIR
            out.append(cell(v, **st))
        ws.append(out)
ms = wb.create_sheet("Missing")
ms.append([cell("Games with a score but no play-by-play (no PMPM)", font=font(bold=True, size=13))]); ms.append([])
ms.append([cell(h, font=HFONT, fill=HEAD_FILL, alignment=HALIGN) for h in ["Season", "Date", "Away", "Home", "Score (away-home)"]])
for r in sorted(missing, key=lambda r: (r[0], r[1])): ms.append([cell(v, font=SMALL) for v in r])
wb.save(DST)
print(f"saved {DST}: {len(pairs)} games, {2 * len(pairs)} rows, missing {len(missing)} ({time.time() - t0:.0f}s)")
