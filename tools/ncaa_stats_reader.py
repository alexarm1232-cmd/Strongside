import os
import re
import csv
import sys
import json
from datetime import date, timedelta
from collections import defaultdict, Counter

# Reads the play-by-play collected from stats.ncaa.org ("data/ncaa stats" folder) and writes it in the layout the
# dashboard already reads, for each of our games:
#   playbyplay/<game id>.json   the plays in order with the running score, substitutions included (on/off, lineups)
#   shots/<game id>.json        every shot: who, when, what kind, made or missed, who assisted (play types), plus
#                               "tags": the site's own notes on each shot (in the paint, fast break, second chance,
#                               off a turnover, blocked) and the exact shot type, in the same order as the shots
#   cbbd/<game id>.json         the player on every turnover
#
#     python tools/ncaa_stats_reader.py 2425            reads every season it finds, writes only 2024-25
#
# Nothing the dashboard uses is changed: everything goes to "data/ncaa stats converted\<season>", in the same
# conference / team folder layout as the season's own folder, so it can be checked first and copied in later.
# Games are matched to ours by date and the two teams, not by the site's game numbers.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SOURCE_DIR = os.path.join(ROOT, "data/ncaa stats")
OUT_DIR = os.path.join(ROOT, "data/ncaa stats converted")
SOURCE = "stats.ncaa.org"
SEASON_CODES = {"2009-2010": "0910", "2010-2011": "1011", "2011-2012": "1112", "2012-2013": "1213", "2013-2014": "1314",
                "2014-2015": "1415", "2015-2016": "1516", "2016-2017": "1617", "2017-2018": "1718", "2018-2019": "1819",
                "2019-2020": "1920", "2020-2021": "2021", "2021-2022": "2122", "2022-2023": "2223", "2023-2024": "2324",
                "2024-2025": "2425", "2025-2026": "2526"}
FOLDERS = {"2526": ["data/seasons/2526", "data/seasons/2526 full"]}       # where each season's games are listed
csv.field_size_limit(10 ** 9)

def season_folders(code):
    names = FOLDERS.get(code, [f"data/seasons/{code}", f"data/seasons/{code} full"])
    return [os.path.join(ROOT, n) for n in names if os.path.isdir(os.path.join(ROOT, n))]

def clean(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# ---------------------------
# OUR GAMES
# ---------------------------
def our_games(code):
    """(date, frozenset of the two team names) -> our game: id, home, away and the team folders that hold it.
    The pre-tournament folder and the full-season one (postseason) are both read; the first is laid out the same."""
    games, teams = {}, {}
    for base in season_folders(code):
        for conf in os.listdir(base):
            conf_path = os.path.join(base, conf)
            if not os.path.isdir(conf_path): continue
            for team in os.listdir(conf_path):
                team_path = os.path.join(conf_path, team)
                teams.setdefault(clean(team), (conf, team))
                for g in read_json(os.path.join(team_path, "game_scores.json"), []):
                    key = (g.get("date", ""), frozenset((clean(g.get("home_team")), clean(g.get("away_team")))))
                    games.setdefault(key, {"id": str(g.get("game_id")), "home": g.get("home_team"), "away": g.get("away_team"),
                                           "date": g.get("date")})
    return games, teams

# ---------------------------
# THE SITE'S FILES
# ---------------------------
DATE = re.compile(r"^(\d\d)/(\d\d)/(\d{4})")

def game_dates():
    """contest id -> the game's date (from the box score file, where the date sits in the header rows)."""
    dates = {}
    path = os.path.join(SOURCE_DIR, "individual_stats.csv")
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["contest_id"] in dates: continue
            m = DATE.match(r.get("col0") or "")
            if m:
                dates[r["contest_id"]] = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    return dates

def contests(season_label):
    """Yields (contest id, rows) one game at a time, in the order the file has them."""
    path = os.path.join(SOURCE_DIR, "play_by_play.csv")
    current, rows = None, []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["season"] != season_label: continue
            if r["contest_id"] != current:
                if rows: yield current, rows
                current, rows = r["contest_id"], []
            rows.append(r)
    if rows: yield current, rows

# ---------------------------
# ONE GAME
# ---------------------------
SHOT = re.compile(r"^(\d)pt\s+([a-z]+)\s*(.*?)\s*(made|missed)\s*$")
FREE = re.compile(r"^freethrow\s+(\d)of(\d)\s*(.*?)\s*(made|missed)\s*$")
KIND = {"layup": "LayUpShot", "drivinglayup": "LayUpShot", "reverselayup": "LayUpShot", "alleyoop": "LayUpShot",
        "fingerroll": "LayUpShot", "dunk": "DunkShot", "tipinlayup": "TipShot", "tipin": "TipShot", "putback": "TipShot"}

# The site's older play-by-play (all of 2017-18 and earlier, and some games up to 2019-20) reads
# "JACKSON,JORDAN missed Three Point Jumper" instead of "Jordan Jackson, 3pt jumpshot missed". Those rows are
# turned into the newer wording first, so everything after works the same for both.
OLD_ROW = re.compile(r"^((?:[A-Z0-9 .'\-]+,[A-Z0-9 .'\-]+?)|TEAM)\s+((?:[a-z]|[A-Z][a-z]).*)$")
OLD_SHOTS = {"three point jumper": (3, "jumpshot"), "two point jumper": (2, "jumpshot"), "layup": (2, "layup"),
             "dunk": (2, "dunk"), "tip in": (2, "tipin")}
OLD_ACTIONS = {"enters game": "substitution in", "leaves game": "substitution out", "assist": "assist",
               "offensive rebound": "rebound offensive", "defensive rebound": "rebound defensive",
               "deadball rebound": "rebound deadball", "turnover": "turnover", "steal": "steal",
               "blocked shot": "block", "commits foul": "foul personal"}

def old_style(text):
    """(who, action) in the newer wording for an older-style row, or None when the row is not one."""
    m = OLD_ROW.match(text.strip())
    if not m:
        return None
    name, action = m.group(1).strip(), m.group(2).strip().lower()
    if name == "TEAM":
        who = ""
    else:
        last, _, first = name.partition(",")
        who = " ".join(w.capitalize() for w in f"{first} {last}".split())
    shot = re.match(r"^(made|missed) (.+)$", action)
    if shot:
        result, kind = shot.group(1), shot.group(2).strip()
        if kind == "free throw":
            return who, f"freethrow 1of1 {result}"
        points, shot_type = OLD_SHOTS.get(kind, (3 if "three" in kind else 2, "jumpshot"))
        return who, f"{points}pt {shot_type} {result}"
    if "timeout" in action:
        return who, "timeout"
    return who, OLD_ACTIONS.get(action, action)

def seconds(clock):
    parts = re.findall(r"\d+", clock or "")
    return int(parts[0]) * 60 + int(parts[1]) if len(parts) >= 2 else None

def convert(rows, game, side_of_name):
    """The site's rows for one game -> (play-by-play, shots, turnovers) in our layout. side_of_name: the site's team
    name (cleaned) -> 0 for our home team, 1 for our away team."""
    plays, shots, tags, events, turnovers = [], [], [], [], []
    waiting = defaultdict(list)       # (period, clock, side) -> made shots waiting for their assist, and assists waiting for a shot
    for r in rows:
        period, left = int(r["period_num"] or 0), seconds(r["time"])
        if not period or left is None: continue
        try:
            away_now, home_now = int(r["away_score"] or 0), int(r["home_score"] or 0)
        except ValueError:
            away_now = home_now = None
        # A row the site lists in both teams' columns at once comes through as "away play | home play"
        parts = r["play"].split(" | ")
        names = [r["away_team"], r["home_team"]] if len(parts) == 2 and " / " in r["team"] else [r["team"]] * len(parts)
        for team_name, part in zip(names, parts):
            side = side_of_name.get(clean(team_name))
            if side is None: continue
            our_team = game["home"] if side == 0 else game["away"]
            # "Name, action". The split is at the LAST comma: some names have one of their own ("Paul McNeil, jr.")
            # and the actions never do.
            older = old_style(part)
            if older:
                who, action = older
            else:
                name_part, comma, action_part = part.strip().rpartition(",")
                who, action = (name_part.strip(), action_part.strip().lower()) if comma else ("", part.strip().lower())
            if who.lower() == "team": who = ""
            home_score, away_score = (home_now, away_now)
            text = f"{who}, {action}" if who else action
            key = (period, left, side)
            if action.startswith("substitution"):
                if not who: continue
                text = f"Subbing {'in' if action.endswith('in') else 'out'} for {our_team}-{who}"
            elif (s := SHOT.match(action)):
                points, shot_type, notes, result = int(s.group(1)), s.group(2), s.group(3), s.group(4)
                note_list = [n for n in re.split(r"[;\s]+", notes) if n]
                row = [side, who, period, left, KIND.get(shot_type, "JumpShot"), int(result == "made"), points, None, None, ""]
                shots.append(row)
                tags.append([shot_type] + note_list)
                if result == "made":
                    if waiting[key] and isinstance(waiting[key][0], str):     # the assist came first
                        row[9] = waiting[key].pop(0)
                    else:
                        waiting[key].append(row)
            elif (s := FREE.match(action)):
                made = s.group(4) == "made"
                shots.append([side, who, period, left, "MadeFreeThrow" if made else "MissedFreeThrow", int(made), 1, None, None, ""])
                tags.append(["freethrow"] + [n for n in re.split(r"[;\s]+", s.group(3)) if n])
            elif action == "assist":
                pending = [x for x in waiting[key] if isinstance(x, list) and not x[9]]
                if pending:
                    pending[0][9] = who
                    waiting[key].remove(pending[0])
                else:
                    waiting[key].append(who)
            elif action.startswith("rebound"):
                if "offensive" in action and "deadball" not in action:
                    events.append([side, period, left, "Offensive Rebound"])
                elif "defensive" in action and "deadball" not in action:
                    events.append([side, period, left, "Defensive Rebound"])
            elif action.startswith("turnover"):
                events.append([side, period, left, "Turnover"])
                turnovers.append([side, period, left, who])
            elif action == "steal":
                events.append([side, period, left, "Steal"])
            plays.append({"period": period, "period_name": r["period"], "clock": r["time"], "seconds_left": left, "team": our_team,
                          "is_home": side == 0, "home_score": home_score, "away_score": away_score, "text": text})
    head = {"game_id": game["id"], "source": SOURCE, "date": game["date"], "home_team": game["home"], "away_team": game["away"]}
    return (dict(head, game_info="", status="", plays=plays), dict(head, shots=shots, tags=tags, events=events),
            dict(head, turnovers=turnovers, floor=[]))

# ---------------------------
# MAIN
# ---------------------------
def main():
    wanted = [a for a in sys.argv[1:] if a in SEASON_CODES.values()]
    if not wanted:
        print("Name the seasons to convert, e.g.  python tools/ncaa_stats_reader.py 2425")
        return
    dates = game_dates()
    for label, code in SEASON_CODES.items():
        if code not in wanted: continue
        ours, teams = our_games(code)
        if not ours:
            print(f"{code}: no games listed in data/seasons/{code}; build that season's game list first.")
            continue
        out = os.path.join(OUT_DIR, code)
        seen = written = no_date = no_match = 0
        subs_both = 0
        unmatched = Counter()
        for contest, rows in contests(label):
            seen += 1
            day = dates.get(contest)
            if not day:
                no_date += 1
                continue
            pair = frozenset((clean(rows[0]["home_team"]), clean(rows[0]["away_team"])))
            game = None
            for shift in (0, -1, 1):
                game = ours.get(((day + timedelta(days=shift)).strftime("%Y/%m/%d"), pair))
                if game: break
            if not game:
                no_match += 1
                unmatched.update(n for n in (rows[0]["home_team"], rows[0]["away_team"]) if clean(n) not in teams)
                continue
            side_of_name = {clean(game["home"]): 0, clean(game["away"]): 1}
            files = convert(rows, game, side_of_name)
            subbed = {p["team"] for p in files[0]["plays"] if p["text"].startswith("Subbing")}
            subs_both += len(subbed) == 2
            for name in (game["home"], game["away"]):
                if clean(name) not in teams: continue
                conf, folder = teams[clean(name)]
                for sub, data in zip(("playbyplay", "shots", "cbbd"), files):
                    path = os.path.join(out, conf, folder, sub)
                    os.makedirs(path, exist_ok=True)
                    with open(os.path.join(path, game["id"] + ".json"), "w", encoding="utf-8") as f:
                        json.dump(data, f, separators=(",", ":"))
            written += 1
        print(f"{label}: {seen} games in the files | {written} matched to ours and written to {out} | "
              f"{no_match} not on our list | {no_date} with no date | substitutions for both teams in {subs_both} of {written}")
        if unmatched:
            print("   teams in unmatched games that are not ours (non-Division I, or a name to check):", unmatched.most_common(12))

if __name__ == "__main__":
    main()
