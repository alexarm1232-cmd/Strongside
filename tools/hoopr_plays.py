import os
import sys
import csv
import gzip
import json
import re
from datetime import date, timedelta
from collections import defaultdict, Counter

# Turns the ESPN play-by-play downloaded through hoopR (tools/hoopr_pbp.R -> data/hoopr/<year>/play_by_play.csv.gz)
# into the files the dashboard already reads, the same way tools/kaggle_plays.py does for the Kaggle files:
#     python tools/hoopr_plays.py 0809          (or several seasons: 0809 0708 0607 0506)
#
# For every game it writes, in both teams' folders (the pre-tournament folder and the full-season one):
#   playbyplay/<game id>.json   the plays in order with the running score, substitutions included (on/off, lineups)
#   shots/<game id>.json        every shot (who, when, what kind, made or missed, who assisted, where when ESPN says)
#                               and the rebounds, turnovers and steals around them: what play types are built from
#   cbbd/<game id>.json         the player on every turnover
# Play texts are written in the same wording kaggle_plays.py uses, so everything downstream reads them the same way.
#
# Run it after the season's game list exists (data/seasons/<code>/.../game_scores.json). ESPN's games are matched to
# ours through the schedule itself (the same date, give or take a day, and the same final score), not by name.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
HOOPR_DIR = os.path.join(ROOT, "data", "hoopr")
SEASONS = {"0506": 2006, "0607": 2007, "0708": 2008, "0809": 2009}   # season code -> hoopR's season (the year it ends)
SOURCE = "espn-hoopr"
WORDS = {"LayUpShot": "layup", "DunkShot": "dunk", "TipShot": "tip in", "JumpShot": "jump shot", "HookShot": "hook shot"}
EVENT_KINDS = ("rebound", "turnover", "steal")
csv.field_size_limit(10 ** 9)

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def our_games(base):
    """Game id -> its date, the two teams, the score and the team folders that hold it."""
    games = {}
    if not os.path.isdir(base): return games
    for conf in sorted(os.listdir(base)):
        conf_path = os.path.join(base, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            team_path = os.path.join(conf_path, team)
            listed = {str(g).strip() for g in read_json(os.path.join(team_path, "games.json"), [])}
            for g in read_json(os.path.join(team_path, "game_scores.json"), []):
                game_id = str(g.get("game_id"))
                try:
                    home_score, away_score = int(g["home_score"]), int(g["away_score"])
                except (TypeError, ValueError, KeyError):
                    continue        # never played
                if game_id not in listed: continue
                game = games.setdefault(game_id, {"id": game_id, "date": g["date"], "home": g["home_team"], "away": g["away_team"],
                                                  "home_score": home_score, "away_score": away_score, "folders": []})
                game["folders"].append(team_path)
    return games

def num(v, default=None):
    try: return int(float(v))
    except (TypeError, ValueError): return default

def load_plays(year):
    """ESPN game id -> {date, home id, away id, final scores, plays in order}."""
    path = os.path.join(HOOPR_DIR, str(year), "play_by_play.csv.gz")
    games = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
        for n, r in enumerate(csv.DictReader(f)):
            gid = r.get("game_id")
            g = games.get(gid)
            if g is None:
                g = games[gid] = {"date": (r.get("game_date") or "")[:10], "home_id": r.get("home_team_id"), "away_id": r.get("away_team_id"),
                                  "home_name": r.get("home_team_name") or r.get("home_team_location") or "",
                                  "away_name": r.get("away_team_name") or r.get("away_team_location") or "", "plays": []}
            order = num(r.get("game_play_number")) or num(r.get("sequence_number")) or n
            g["plays"].append((order, n, r))
    for g in games.values():
        g["plays"].sort(key=lambda p: (p[0], p[1]))
        last = g["plays"][-1][2] if g["plays"] else {}
        g["final"] = (num(last.get("home_score"), 0), num(last.get("away_score"), 0))
    return games

def match_games(ours, theirs):
    """ESPN game id -> our game id, and ESPN team id -> our team name (same date +-1 day and same final score)."""
    spot = defaultdict(list)
    for g in ours.values():
        spot[(g["date"], max(g["home_score"], g["away_score"]), min(g["home_score"], g["away_score"]))].append(g)
    def ours_on(day, scores):
        found = []
        try: d0 = date(*map(int, day.split("-")))
        except Exception: return found
        for shift in (0, -1, 1):
            found += spot.get(((d0 + timedelta(days=shift)).strftime("%Y/%m/%d"), max(scores), min(scores)), [])
        return found
    votes = defaultdict(Counter)
    for g in theirs.values():
        found = ours_on(g["date"], g["final"])
        if len(found) == 1 and g["final"][0] != g["final"][1]:
            o = found[0]; espn_home_won = g["final"][0] > g["final"][1]; our_home_won = o["home_score"] > o["away_score"]
            winner = o["home"] if our_home_won else o["away"]; loser = o["away"] if our_home_won else o["home"]
            votes[g["home_id"]][winner if espn_home_won else loser] += 1
            votes[g["away_id"]][loser if espn_home_won else winner] += 1
    names = {}
    for team_id, counts in votes.items():
        (name, count), = counts.most_common(1)
        if count >= 3 and count >= 0.7 * sum(counts.values()): names[team_id] = name
    by_teams = defaultdict(list)
    for g in ours.values(): by_teams[frozenset((g["home"], g["away"]))].append(g)
    matched = {}
    for gid, g in theirs.items():
        if g["home_id"] not in names or g["away_id"] not in names: continue
        try: day = date(*map(int, g["date"].split("-")))
        except Exception: continue
        options = [o for o in by_teams.get(frozenset((names[g["home_id"]], names[g["away_id"]])), [])
                   if abs((date(*map(int, o["date"].split("/"))) - day).days) <= 1]
        if len(options) == 1: matched[gid] = options[0]["id"]
    return matched, names

def seconds_left(r):
    m, s = num(r.get("clock_minutes")), num(r.get("clock_seconds"))
    if m is not None and s is not None: return m * 60 + s
    parts = re.findall(r"\d+", r.get("clock_display_value") or "")
    return int(parts[0]) * 60 + int(parts[1]) if len(parts) >= 2 else None

def who(text, *cuts):
    """The player's name: the text before the first of the given words."""
    for c in cuts:
        i = text.find(c)
        if i > 0: return text[:i].strip()
    return ""

def convert(game, espn, home_side):
    """One game -> (play-by-play file, shots file, turnovers file). home_side: our side (0 home, 1 away) of ESPN's home team."""
    plays, shots, others, turnovers = [], [], [], []
    for _, _, r in espn["plays"]:
        tid = r.get("team_id")
        if tid == espn["home_id"]: s = home_side
        elif tid == espn["away_id"]: s = 1 - home_side
        else: s = None
        period = num(r.get("period_number")) or num(r.get("period")) or 1
        left = seconds_left(r)
        if left is None: continue
        eh, ea = num(r.get("home_score"), 0), num(r.get("away_score"), 0)
        home_now, away_now = (eh, ea) if home_side == 0 else (ea, eh)
        text, kind = (r.get("text") or "").strip(), (r.get("type_text") or "").strip()
        low = text.lower(); out = []
        team_name = game["home"] if s == 0 else game["away"] if s == 1 else ""
        if s is not None and " enters the game for " in text:
            a, b = text.rstrip(".").split(" enters the game for ", 1)
            out = [f"Subbing in for {team_name}-{a.strip()}", f"Subbing out for {team_name}-{b.strip()}"]
        elif s is not None and str(r.get("shooting_play")).upper() in ("TRUE", "1") and (" made " in low or " missed " in low):
            made = " made " in low; name = r.get("athlete_name_1") or who(text, " made ", " missed ")
            if "free throw" in low:
                shots.append([s, name, period, left, "MadeFreeThrow" if made else "MissedFreeThrow", int(made), 1, None, None, ""])
                out = [f"{name} {'makes' if made else 'misses'} free throw"]
            else:
                points = 3 if "three point" in low else 2
                assist = who(text.split("Assisted by", 1)[1], ".") if "Assisted by" in text else ""
                x, y = r.get("coordinate_x_raw") or r.get("coordinate_x"), r.get("coordinate_y_raw") or r.get("coordinate_y")
                try: x, y = float(x), float(y)
                except (TypeError, ValueError): x = y = None
                if x is not None and (abs(x) > 200 or abs(y) > 200): x = y = None
                shot_kind = kind if kind in WORDS else "JumpShot"
                shots.append([s, name, period, left, shot_kind, int(made), points, x, y, assist if made else ""])
                t = f"{name} {'makes' if made else 'misses'} {'three' if points == 3 else 'two'} point {WORDS.get(shot_kind, 'jump shot')}"
                out = [t + (f" ({assist} assists)" if made and assist else "")]
        elif s is not None and "rebound" in low:
            which = "Offensive Rebound" if "offensive" in low else "Defensive Rebound" if "defensive" in low else None
            if which: others.append([s, period, left, which])
            name = who(text, " Offensive", " Defensive", " Deadball", " Team")
            out = [f"{name} {which.lower() if which else 'deadball rebound'}".strip()]
        elif s is not None and "turnover" in low:
            name = who(text, " Turnover", " turnover"); others.append([s, period, left, "Turnover"]); turnovers.append([s, period, left, name])
            out = [f"{name} turnover".strip()]
        elif s is not None and "steal" in low:
            name = who(text, " Steal", " steal"); others.append([s, period, left, "Steal"]); out = [f"{name} steal"]
        elif s is not None and "block" in low:
            out = [f"{who(text, ' Block', ' block')} block"]
        elif s is not None and low.startswith("foul on "):
            out = [f"{text[8:].rstrip('.').strip()} foul"]
        for t in out:
            plays.append({"period": period, "period_name": "", "clock": "%02d:%02d" % divmod(left, 60), "seconds_left": left, "team": team_name,
                          "is_home": s == 0, "home_score": home_now, "away_score": away_now, "text": t})
    head = {"game_id": game["id"], "source": SOURCE, "date": game["date"], "home_team": game["home"], "away_team": game["away"]}
    return dict(head, game_info="", status="", plays=plays), dict(head, shots=shots, events=others), dict(head, turnovers=turnovers, floor=[])

def main():
    codes = [a for a in sys.argv[1:] if a in SEASONS]
    if not codes:
        print("Name the seasons to do, e.g.  python tools/hoopr_plays.py 0809     Known: " + " ".join(SEASONS)); return
    for code in codes:
        year = SEASONS[code]
        if not os.path.exists(os.path.join(HOOPR_DIR, str(year), "play_by_play.csv.gz")):
            print(f"{code}: no data/hoopr/{year}/play_by_play.csv.gz yet. Run tools/hoopr_pbp.R {year} first."); continue
        print(f"{year - 1}-{year % 100:02d}: reading the hoopR play-by-play ...", flush=True)
        theirs = load_plays(year)
        for base in (os.path.join(ROOT, "data", "seasons", code), os.path.join(ROOT, "data", "seasons", code + " full")):
            ours = our_games(base)
            if not ours:
                print(f"   {os.path.basename(base)}: no games listed yet (the season's game list comes first)"); continue
            # a season built from the hoopR files (tools/hoopr_season.py) uses ESPN's own game ids, with ESPN's home team
            # as ours: those games match by id; any others by date and final score
            direct = {gid: gid for gid in theirs if gid in ours}
            matched, names = match_games(ours, {g: v for g, v in theirs.items() if g not in direct}); written = 0
            for gid, our_id in list(direct.items()) + list(matched.items()):
                game = ours[our_id]; espn = theirs[gid]
                home_side = 0 if gid in direct else (0 if names[espn["home_id"]] == game["home"] else 1)
                files = convert(game, espn, home_side)
                if not files[0]["plays"]: continue
                for folder in game["folders"]:
                    for sub, data in zip(("playbyplay", "shots", "cbbd"), files):
                        os.makedirs(os.path.join(folder, sub), exist_ok=True)
                        with open(os.path.join(folder, sub, our_id + ".json"), "w", encoding="utf-8") as out:
                            json.dump(data, out, separators=(",", ":"))
                written += 1
            print(f"   {os.path.basename(base)}: {len(theirs)} ESPN games, {len(ours)} on our list: {written} written, "
                  f"{len(ours) - written} of ours have no play-by-play ({len(names)} teams matched)", flush=True)

if __name__ == "__main__":
    main()

