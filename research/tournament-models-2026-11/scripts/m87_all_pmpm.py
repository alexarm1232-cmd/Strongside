# PMPM (point margin per minute) for every game with play-by-play, 2009-10 to 2025-26, using tools/pdem.py's own
# reader (season_games, pdem). One sheet per season, one row per game from the winner's side (plus = winner ahead),
# minutes 1-40 then each overtime minute. Written in write-only mode (it is large).
import os, sys, json, time
sys.path.insert(0, r"C:\Users\crtra\Downloads\basketball\tools")
import pdem as P
from openpyxl import Workbook
from openpyxl.styles import Font
DST = r"C:\Users\crtra\Downloads\PMPM - every game 2010-2026.xlsx"
CODES = [c for c in sorted(os.listdir(P.SEASONS_DIR)) if len(c) == 4 and c.isdigit() and "0910" <= c <= "2526"]
MAXOT = 4                                                     # overtime columns kept: 4 overtimes = 20 minutes
wb = Workbook(write_only=True)
readme = wb.create_sheet("Read me")
for line in ["PMPM for every game with play-by-play, 2009-10 to 2025-26, one sheet per season (2019-20 has regular-season games only).",
             "PMPM = point margin per minute: the margin at the end of each minute, from the WINNER's side (plus = the winner was ahead).",
             "Minutes 1-40 are regulation; OT1-1 ... OT4-5 are each overtime minute (blank if no overtime).",
             "Built from data/seasons/<season>/.../playbyplay with tools/pdem.py's reader. Games without play-by-play are listed on 'Missing'.",
             "Postseason = yes for conference tournaments, NCAA, NIT and other postseason games."]:
    readme.append([line])
HEAD = ["Season", "Date", "Winner", "Loser", "Site", "Winner pts", "Loser pts", "Final margin", "OT", "Postseason"] + \
       [f"PMPM {m}" for m in range(1, 41)] + [f"OT{o}-{k}" for o in range(1, MAXOT + 1) for k in range(1, 6)]
missing_rows, total, t0 = [], 0, time.time()
for code in CODES:
    games = P.season_games(code); ws = wb.create_sheet(P.season_label(code)); ws.append(HEAD); n = 0
    rows = []
    for gid, (row, path) in games.items():
        try: hs, as_ = int(row["home_score"]), int(row["away_score"])
        except (TypeError, ValueError, KeyError): continue
        if not os.path.exists(path):
            missing_rows.append([P.season_label(code), row.get("date"), row.get("away_team"), row.get("home_team")]); continue
        series = P.pdem(json.load(open(path, encoding="utf-8")))
        if not series: missing_rows.append([P.season_label(code), row.get("date"), row.get("away_team"), row.get("home_team")]); continue
        home_won = hs > as_
        win, lose = (row["home_team"], row["away_team"]) if home_won else (row["away_team"], row["home_team"])
        m = [(h - a) if home_won else (a - h) for _, h, a in series][1:]
        reg, ot = m[:40], m[40:40 + 5 * MAXOT]
        site = "neutral" if row.get("neutral") else f"at {row['home_team']}"
        rows.append([P.season_label(code), row["date"], win, lose, site, max(hs, as_), min(hs, as_), abs(hs - as_),
                     (len(m) - 40) // 5 if len(m) > 40 else 0, "yes" if row.get("post") else "no"]
                    + reg + [None] * (40 - len(reg)) + ot + [None] * (5 * MAXOT - len(ot)))
    rows.sort(key=lambda r: (r[1], r[2]))
    for r in rows: ws.append(r)
    total += len(rows); print(f"{P.season_label(code)}: {len(rows)} games  ({time.time() - t0:.0f}s)", flush=True)
ms = wb.create_sheet("Missing"); ms.append(["Season", "Date", "Away", "Home"])
for r in missing_rows: ms.append(r)
wb.save(DST); print("TOTAL", total, "games; missing play-by-play:", len(missing_rows), "->", DST)
