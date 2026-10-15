import os
import sys
import csv
import json
from datetime import date, timedelta
from collections import defaultdict, Counter

# Turns the NCAA play-by-play that was published through Kaggle (the "MEvents" files of the 2020 March Madness
# competitions: every Division I game of 2014-15 through 2018-19) into the files the dashboard already reads:
#     python tools/kaggle_plays.py 1819          (or several seasons: 1819 1718 ...)
#
# For every game it writes, in both teams' folders:
#   playbyplay/<game id>.json   the plays in order, substitutions included: what on/off and the lineups are built from
#   shots/<game id>.json        every shot (who, when, what kind, made or missed, who assisted; where, when the file
#                               says) and the rebounds, turnovers and steals around them: what play types are built from
#   cbbd/<game id>.json         the player on every turnover
# so for these seasons 6playbyplay.py, 9espnshots.py and 10cbbdplays.py are not needed.
#
# Run it after 2gameupdate.py and 3scores.py: it needs the season's game list to know which game is which. Kaggle's
# teams are matched to ours through the schedule itself (the same date and the same final score), not by name.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
KAGGLE_DIR = r"C:\Users\crtra\Downloads\2020DataFiles\2020DataFiles\2020-Mens-Data"     # where the MEvents files are
SEASONS = {"1415": 2015, "1516": 2016, "1617": 2017, "1718": 2018, "1819": 2019}        # season code -> Kaggle's season
SOURCE = "kaggle"
# Shot kinds, named the way ESPN names them (what the dashboard's shot code expects)
KINDS = {"lay": "LayUpShot", "drive": "LayUpShot", "alley": "LayUpShot", "dunk": "DunkShot", "tip": "TipShot"}
WORDS = {"lay": "layup", "drive": "driving layup", "alley": "alley-oop", "dunk": "dunk", "tip": "tip in", "hook": "hook shot"}

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def our_games(base):
    """Game id -> its date, the two teams, the score and the team folders that hold it."""
    games = {}
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

def load_events(season):
    """(day number, winner id, loser id) -> [final scores, the game's events in order]."""
    games = {}
    with open(os.path.join(KAGGLE_DIR, f"MEvents{season}.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for n, r in enumerate(csv.DictReader(f)):
            key = (int(r["DayNum"]), r["WTeamID"], r["LTeamID"])
            game = games.get(key)
            if game is None:
                game = games[key] = [(int(r["WFinalScore"]), int(r["LFinalScore"])), []]
            game[1].append((int(r["ElapsedSeconds"]), n, r["EventTeamID"], r["EventPlayerID"], r["EventType"], r["EventSubType"],
                            int(r["WCurrentScore"] or 0), int(r["LCurrentScore"] or 0), float(r["X"] or 0), float(r["Y"] or 0)))
    for game in games.values():
        game[1].sort()          # by the clock, then the order the file lists them
    return games

def day_zero(season):
    with open(os.path.join(KAGGLE_DIR, "MDataFiles_Stage1", "MSeasons.csv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if int(r["Season"]) == season:
                month, day, year = map(int, r["DayZero"].split("/"))
                return date(year, month, day)
    raise SystemExit(f"Season {season} is not in MSeasons.csv")

def match_games(ours, theirs, zero):
    """Kaggle's game key -> our game id, and Kaggle's team id -> our team name."""
    spot = defaultdict(list)        # (date, winner's score, loser's score) -> our games
    for g in ours.values():
        spot[(g["date"], max(g["home_score"], g["away_score"]), min(g["home_score"], g["away_score"]))].append(g)
    def ours_on(key, scores):
        found = []
        for shift in (0, -1, 1):        # the two sources sometimes put a late game on different dates
            day = (zero + timedelta(days=key[0] + shift)).strftime("%Y/%m/%d")
            found += spot.get((day, scores[0], scores[1]), [])
        return found
    winner_of = lambda g: (g["home"], g["away"]) if g["home_score"] > g["away_score"] else (g["away"], g["home"])
    # 1. each team: the name it shares a date and a score with most often
    votes = defaultdict(Counter)
    for key, (scores, _) in theirs.items():
        found = ours_on(key, scores)
        if len(found) == 1:
            winner, loser = winner_of(found[0])
            votes[key[1]][winner] += 1
            votes[key[2]][loser] += 1
    names = {}
    for team_id, counts in votes.items():
        (name, count), = counts.most_common(1)
        if count >= 3 and count >= 0.7 * sum(counts.values()):
            names[team_id] = name
    # 2. each game: our game on that date between those two teams
    by_teams = defaultdict(list)
    for g in ours.values():
        by_teams[frozenset((g["home"], g["away"]))].append(g)
    matched = {}
    for key, (scores, _) in theirs.items():
        if key[1] not in names or key[2] not in names: continue
        day = zero + timedelta(days=key[0])
        options = [g for g in by_teams.get(frozenset((names[key[1]], names[key[2]])), [])
                   if abs((date(*map(int, g["date"].split("/"))) - day).days) <= 1]
        if len(options) == 1:
            matched[key] = options[0]["id"]
    return matched, names

def our_spot(x, y):
    """Kaggle's spot (0-100 along the floor, 0-100 across it) -> ours: feet, x across the floor and y out from the
    basket's end. 0, 0 means the spot was not recorded."""
    if not x and not y: return None, None
    x, y = 9.4 * x, 5 * y
    if x < 470:
        return round(50 - y / 10), round(x / 10 - 5)
    return round(y / 10), round((940 - x) / 10 - 5)

def convert(game, events, side_of, players):
    """One game -> (the play-by-play file, the shots file, the turnovers file). side_of: Kaggle team id -> 0 home, 1 away."""
    home_won = game["home_score"] > game["away_score"]
    plays, shots, others, turnovers = [], [], [], []
    made = []           # made baskets waiting for their assist: [elapsed, side, the shot row, the play row]
    score = [0, 0]      # home, away
    for elapsed, _, team_id, player_id, kind, detail, w_now, l_now, x, y in events:
        if team_id not in side_of:
            continue
        s = side_of[team_id]
        # a time on the line between two periods belongs to the one that is ending
        period = 1 if elapsed <= 1200 else 2 if elapsed <= 2400 else 3 + (elapsed - 2401) // 300
        ends = 1200 if period == 1 else 2400 if period == 2 else 2400 + 300 * (period - 2)
        left = ends - elapsed
        name = players.get(player_id, "")
        team_name = game["home"] if s == 0 else game["away"]
        # the file's own running score is mostly blank, so the score is counted up from the made shots
        if kind in ("made1", "made2", "made3"):
            score[s] += int(kind[-1])
        home_now, away_now = score
        text = None
        if kind == "sub":
            if elapsed == 0 or not name: continue       # a starter being "sent in" before the tip is not a substitution
            text = f"Subbing {'in' if detail == 'in' else 'out'} for {team_name}-{name}"
        elif kind in ("made1", "miss1"):
            text = f"{name} {'makes' if kind == 'made1' else 'misses'} free throw"
            shots.append([s, name, period, left, "MadeFreeThrow" if kind == "made1" else "MissedFreeThrow", int(kind == "made1"), 1, None, None, ""])
        elif kind in ("made2", "miss2", "made3", "miss3"):
            points, is_made = int(kind[-1]), kind.startswith("made")
            sx, sy = our_spot(x, y)
            shots.append([s, name, period, left, KINDS.get(detail, "JumpShot"), int(is_made), points, sx, sy, ""])
            text = f"{name} {'makes' if is_made else 'misses'} {'three' if points == 3 else 'two'} point {WORDS.get(detail, 'jump shot')}"
        elif kind == "assist":
            # the assist is listed beside the basket it led to: the latest basket by that team in the last few seconds
            for waiting in reversed(made):
                if waiting[1] == s and 0 <= elapsed - waiting[0] <= 3 and not waiting[2][9]:
                    waiting[2][9] = name
                    waiting[3]["text"] += f" ({name} assists)"
                    break
            continue
        elif kind == "reb":
            which = "Offensive Rebound" if detail == "off" else "Defensive Rebound" if detail == "def" else None
            if which:
                others.append([s, period, left, which])
            text = f"{name} {which.lower() if which else 'deadball rebound'}".strip()
        elif kind == "turnover":
            others.append([s, period, left, "Turnover"])
            turnovers.append([s, period, left, name])
            text = f"{name} turnover".strip()
        elif kind == "steal":
            others.append([s, period, left, "Steal"])
            text = f"{name} steal"
        elif kind == "block":
            text = f"{name} block"
        elif kind == "foul":
            text = f"{name} foul".strip()
        if text is None:
            continue
        play = {"period": period, "period_name": "", "clock": "%02d:%02d" % divmod(left, 60), "seconds_left": left, "team": team_name,
                "is_home": s == 0, "home_score": home_now, "away_score": away_now, "text": text}
        plays.append(play)
        if kind in ("made2", "made3"):
            made.append([elapsed, s, shots[-1], play])
    head = {"game_id": game["id"], "source": SOURCE, "date": game["date"], "home_team": game["home"], "away_team": game["away"]}
    return (dict(head, game_info="", status="", plays=plays), dict(head, shots=shots, events=others), dict(head, turnovers=turnovers, floor=[]))

def main():
    codes = [a for a in sys.argv[1:] if a in SEASONS]
    if not codes:
        print("Name the seasons to do, e.g.  python tools/kaggle_plays.py 1819     Known: " + " ".join(SEASONS))
        return
    players = {}
    with open(os.path.join(KAGGLE_DIR, "MPlayers.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            players[r["PlayerID"]] = f"{r['FirstName']} {r['LastName']}".strip()
    for code in codes:
        season = SEASONS[code]
        base = os.path.join(ROOT, "data/seasons/" + code)
        ours = our_games(base) if os.path.isdir(base) else {}
        if not ours:
            print(f"{code}: no games listed in data/seasons/{code} yet. Run that season's 2gameupdate.py and 3scores.py first.")
            continue
        print(f"{season - 1}-{season % 100:02d}: reading MEvents{season}.csv ...", flush=True)
        theirs = load_events(season)
        matched, names = match_games(ours, theirs, day_zero(season))
        written = 0
        for key, game_id in matched.items():
            game = ours[game_id]
            scores, events = theirs[key]
            home_won = game["home_score"] > game["away_score"]
            sides = {key[1]: 0 if home_won else 1, key[2]: 1 if home_won else 0}       # Kaggle team id -> 0 home, 1 away
            files = convert(game, events, sides, players)
            for folder in game["folders"]:
                for sub, data in zip(("playbyplay", "shots", "cbbd"), files):
                    os.makedirs(os.path.join(folder, sub), exist_ok=True)
                    with open(os.path.join(folder, sub, game_id + ".json"), "w", encoding="utf-8") as out:
                        json.dump(data, out, separators=(",", ":"))
            written += 1
        unmatched_ours = len(ours) - len(set(matched.values()))
        print(f"   {len(theirs)} games in the file, {len(ours)} on our list: {written} written, "
              f"{unmatched_ours} of ours have no play-by-play, {len(theirs) - len(matched)} of theirs are not on our list "
              f"({len(names)} teams matched)", flush=True)

if __name__ == "__main__":
    main()
