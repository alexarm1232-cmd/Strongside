import os
import sys
import csv
import json
import time
import subprocess

# ---------------------------
# TOURNAMENT SPREAD REPORT
# ---------------------------
# Every NCAA tournament game 2010-2026 (First Four included), set up for the simulator the way the old Spread report
# was (Spreadstat.py): each team's ratings, tempo, four factors, shots, play types and players, built from only the
# games played before it, plus who really played in it. Beside that goes BetIQ's closing spread
# (reports/tournament_spreads.csv) and the final score. The dashboard's "Tourney spreads" page plays every game in the
# simulator and reports how far its spreads are from the closing ones.
# Each game is set up as the teams stood that morning: a First Four game from everything through Selection Sunday, a
# round-of-64 game from that plus the First Four, a round-of-32 game from that plus the round of 64, and so on. Only the
# players who really played in the game take the floor in the simulator. ("pre", every game as things stood going into
# the tournament, is there too but not built unless asked for: python dashboard/Tourneystat.py 1819 pre.)
# Only this season's games count: nothing is carried over from the season before (no head start, no program history),
# and each team's home edge, used to put its regular-season games on a neutral floor, is measured on this season alone.
#
#     python dashboard/Tourneystat.py               every season, each in its own run (the season is fixed when the
#                                                   modules load), then joins them into dashboard/tourneyreport.js
#     python dashboard/Tourneystat.py 1819 live     one season in one view (what the full run calls)

MAIN_FOLDER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(MAIN_FOLDER)
SPREADS_FILE = os.path.join(ROOT, "reports", "tournament_spreads.csv")
PARTS_FOLDER = os.path.join(ROOT, "logs", "tourneystat")
REPORT_FILE = os.path.join(MAIN_FOLDER, "tourneyreport.js")
MODES = ("live",)
CODES = ["0910", "1011", "1112", "1213", "1314", "1415", "1516", "1617", "1718", "1819", "2021", "2122", "2223", "2324", "2425", "2526"]

def tournament_lines():
    """Season label ('2018-19') -> game id -> its row in tournament_spreads.csv."""
    out = {}
    for row in csv.DictReader(open(SPREADS_FILE, encoding="utf-8")):
        out.setdefault(row["season"], {})[row["game_id"]] = row
    return out

def label(code):
    return f"20{code[:2]}-{code[2:]}"

def one_season(code, mode):
    sys.argv = [sys.argv[0], code + "f"]            # main.py sets the season from the command line when it loads
    import main
    import Spreadstat
    lines = tournament_lines()[label(code)]
    first_day = min(row["date"] for row in lines.values())
    Spreadstat.TEAMS_FOLDER = os.path.join(ROOT, main.SEASONS[code + "f"]["teams"])
    Spreadstat.LAST_SEASON_FOLDER = os.path.join(ROOT, main.SEASONS[code]["teams"])    # home court: this season's own games
    Spreadstat.COMPARE_FROM = Spreadstat.HEAD_START_ENDS = first_day                  # no head start on any game compared
    Spreadstat.PROGRAM_GAMES = 0
    Spreadstat.load_last_season = lambda paths: ({}, 0.0)
    Spreadstat.FREEZE_FROM = first_day if mode == "pre" else None
    # Every game of the season counts the same: a blowout is not damped the way the dashboard's ratings damp it, and an
    # old game counts as much as a recent one.
    Spreadstat.RATING_LOPSIDED = float("inf")
    Spreadstat.REPORT_FILE = os.path.join(PARTS_FOLDER, f"{code}_{mode}.js")

    def load_market(games, folders):
        """Only the NCAA tournament games, with the closing line for our first team (n0; minus = favoured)."""
        market = {}
        for g in games.values():
            row = lines.get(str(g["id"])) or lines.get(str(g["file"]))
            if not row: continue
            fav = row["favorite"].rstrip(". ")
            if fav not in (g["n0"].rstrip(". "), g["n1"].rstrip(". ")):
                print(f"   {row['date']} {row['winner']}-{row['loser']}: favorite {fav} is neither team")
                continue
            spread = float(row["spread"])
            market[g["id"]] = {"spread": spread if fav == g["n0"].rstrip(". ") else -spread, "total": float(row["total"]) if row["total"] else None,
                               "type": row["round"], "book": "BetIQ"}
        found = len(market)
        if found != len(lines):
            print(f"   {found} of {len(lines)} tournament games found in the box scores")
        return market, "BetIQ closing lines"
    Spreadstat.load_market = load_market
    os.makedirs(PARTS_FOLDER, exist_ok=True)
    report = Spreadstat.build_report(Spreadstat.TEAMS_FOLDER)
    # which tournament game each row is (Spreadstat's rows carry the date and teams, not the id)
    ids = {}
    for game_id, row in lines.items():
        ids[(row["date"], frozenset((row["winner"].rstrip(". "), row["loser"].rstrip(". "))))] = game_id
    report["ids"] = [ids.get((r[0], frozenset((r[1].rstrip(". "), r[2].rstrip(". "))))) for r in report["rows"]]
    with open(Spreadstat.REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, separators=(",", ":"))
    missing = [g for g in lines if g not in set(report["ids"])]
    print(f"{label(code)} {mode}: {len(report['rows'])} of {len(lines)} tournament games set up" + (f"; missing {missing}" if missing else ""))

def join():
    """All the seasons' parts -> tourneyreport.js: one row per game, and each game's simulator inputs in both views."""
    lines = tournament_lines()
    games, leagues, inputs = [], [], {mode: [] for mode in MODES}
    for code in CODES:
        parts = {}
        for mode in MODES:
            path = os.path.join(PARTS_FOLDER, f"{code}_{mode}.js")
            if os.path.exists(path):
                parts[mode] = json.load(open(path, encoding="utf-8"))
        if len(parts) < len(MODES):
            print(f"   {label(code)}: not built")
            continue
        by_id = {mode: {gid: i for i, gid in enumerate(part["ids"]) if gid} for mode, part in parts.items()}
        offset = {}
        for mode, part in parts.items():
            offset[mode] = len(leagues)
            leagues.extend(part["leagues"])
        for gid, row in sorted(lines[label(code)].items(), key=lambda kv: (kv[1]["date"], kv[0])):
            if not all(gid in by_id[mode] for mode in MODES):
                continue
            first = parts["live"]["rows"][by_id["live"][gid]]
            date, team, opp, market, actual = first[0], first[1], first[2], first[6], first[7]
            seed = {row["winner"].rstrip(". "): int(row["winner_seed"]), row["loser"].rstrip(". "): int(row["loser_seed"])}
            games.append([label(code), date, row["round"], team, opp, seed.get(team.rstrip(". ")), seed.get(opp.rstrip(". ")), market, actual, gid])
            for mode in MODES:
                i = by_id[mode][gid]
                league, a, b = parts[mode]["inputs"][i]
                mode_row = parts[mode]["rows"][i]
                # the same game must have the same first team in both views
                assert mode_row[1] == team, (gid, mode_row[1], team)
                inputs[mode].append([league + offset[mode], a, b])
    report = {"built": time.strftime("%Y-%m-%d %H:%M"), "source": "BetIQ closing lines (betiq.teamrankings.com)",
              "columns": ["season", "date", "round", "team", "opp", "team_seed", "opp_seed", "market", "actual", "game_id"],
              "games": games, "leagues": leagues, "inputs": inputs, "modes": list(MODES)}
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("window.TOURNEY = " + json.dumps(report, separators=(",", ":")).replace("</", "<\\/") + ";\n")
    total = sum(len(v) for v in lines.values())
    print(f"Saved {len(games)} of {total} tournament games to {REPORT_FILE} ({os.path.getsize(REPORT_FILE) / 1e6:.1f} MB)")

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2:
        one_season(*args)
    elif args == ["join"]:
        join()
    else:
        os.makedirs(PARTS_FOLDER, exist_ok=True)
        for code in (args or CODES):
            for mode in MODES:
                started = time.time()
                with open(os.path.join(PARTS_FOLDER, f"{code}_{mode}.log"), "w", encoding="utf-8") as log:
                    done = subprocess.run([sys.executable, os.path.abspath(__file__), code, mode], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                tail = open(os.path.join(PARTS_FOLDER, f"{code}_{mode}.log"), encoding="utf-8").read().strip().splitlines()[-1:]
                print(f"{label(code)} {mode}: {'ok' if done.returncode == 0 else 'FAILED'} in {time.time() - started:.0f}s  {tail[0] if tail else ''}", flush=True)
        join()
