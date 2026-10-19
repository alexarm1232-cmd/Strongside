import os
import sys
import json
import requests
import time
import re
from datetime import date, timedelta
from collections import Counter, defaultdict
from difflib import SequenceMatcher

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/1213 full"
SHOTS_FOLDER = "shots"          # saved inside each team folder, e.g. data/seasons/2526/SEC/Alabama/shots/6505422.json
LAST_DATE = "2013/03/17"        # games after this are left out, same as the box scores
TEAM_IDS_FILE = os.path.join(BASE_DIR, "espn_teams.json")   # our team name -> ESPN's team id, learned as games are matched
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
DELAY_SECONDS = 0.5
MAX_PASSES = 12                 # the whole list is gone through again until every game is saved or nothing new turns up
SOURCE = "espn"

# ESPN's play-by-play gives every shot a spot on the floor. This saves, for each of our games, every shot
# (who, when, what kind, made or missed, where, who assisted) plus the rebounds, turnovers and steals around them.
# Files keep the NCAA game id so they line up with the box scores and the play-by-play.
#
# A saved file looks like:
#   "shots":  [side, player, period, seconds left, kind, made, points, x, y, assisted by]     side 0 = home_team, 1 = away_team
#   "events": [side, period, seconds left, kind]                                             rebounds, turnovers, steals
# x and y are in feet with the basket at x = 25, y = 0 (x runs across the floor, y out from the baseline).

def clean_string(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"\bst\b\.?", "state", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())

def alike(a, b):
    return SequenceMatcher(None, clean_string(a), clean_string(b)).ratio()

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def fetch(url, params):
    """One request, then a short wait. Returns None when ESPN has nothing or refuses."""
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f"   request failed ({e})")
        time.sleep(5)
        return None
    time.sleep(DELAY_SECONDS)
    if response.status_code in (403, 429):
        print(f"   ESPN refused the request ({response.status_code}); waiting two minutes")
        time.sleep(120)
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except Exception:
        return None

# ---------------------------
# OUR GAMES
# ---------------------------
def load_our_games():
    """Game id -> its date, teams, scores and the team folders that hold it."""
    games = {}
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            team_path = os.path.join(conf_path, team)
            if not os.path.isdir(team_path): continue
            listed = {str(g).strip() for g in read_json(os.path.join(team_path, "games.json"), [])}
            for g in read_json(os.path.join(team_path, "game_scores.json"), []):
                game_id = str(g.get("game_id"))
                if game_id not in listed or g.get("date", "") > LAST_DATE: continue
                if not str(g.get("home_score") or "").strip() or not str(g.get("away_score") or "").strip(): continue
                game = games.setdefault(game_id, {
                    "id": game_id, "date": g["date"], "home": g["home_team"], "away": g["away_team"],
                    "home_score": int(g["home_score"]), "away_score": int(g["away_score"]), "folders": []})
                game["folders"].append(team_path)
    return games

def is_saved(game):
    return all(os.path.exists(os.path.join(folder, SHOTS_FOLDER, game["id"] + ".json")) for folder in game["folders"])

# ---------------------------
# MATCHING OUR GAME TO ESPN'S
# ---------------------------
scoreboards = {}

def espn_games_on(day):
    """ESPN's D-I games for one date (YYYY/MM/DD): id, the two teams and the score."""
    if day not in scoreboards:
        data = fetch(SCOREBOARD_URL, {"dates": day.replace("/", ""), "groups": "50", "limit": "400"})
        events = []
        for e in (data or {}).get("events", []):
            sides = {}
            for c in e.get("competitions", [{}])[0].get("competitors", []):
                team = c.get("team", {})
                sides[c.get("homeAway")] = {"id": str(team.get("id")), "names": [team.get("location", ""), team.get("displayName", ""), team.get("shortDisplayName", "")],
                                            "score": int(c.get("score") or 0)}
            if "home" in sides and "away" in sides:
                events.append({"id": str(e["id"]), "home": sides["home"], "away": sides["away"]})
        if data is None:
            return []           # not kept, so the date is asked for again on the next pass
        scoreboards[day] = events
    return scoreboards[day]

def name_fit(our_name, espn_team, team_ids):
    if team_ids.get(our_name) == espn_team["id"]:
        return 1.0
    return max(alike(our_name, n) for n in espn_team["names"])

def find_espn_game(game, team_ids):
    """The ESPN game that is this game, and which of ESPN's two teams is our home team. Returns (event, flipped)."""
    y, m, d = map(int, game["date"].split("/"))
    best = None
    for shift in (0, -1, 1):        # the two sites sometimes put a late game on different dates
        day = (date(y, m, d) + timedelta(days=shift)).strftime("%Y/%m/%d")
        for e in espn_games_on(day):
            for flipped in (False, True):    # flipped: ESPN's home team is our away team (neutral-site games)
                home, away = (e["away"], e["home"]) if flipped else (e["home"], e["away"])
                names = (name_fit(game["home"], home, team_ids) + name_fit(game["away"], away, team_ids)) / 2
                scores = home["score"] == game["home_score"] and away["score"] == game["away_score"]
                # the score and the names both have a say; a matching score with poor names is another game that ended the same
                fit = names + (0.6 if scores else 0) - (0.1 if shift else 0)
                if (scores and names >= 0.55) or names >= 0.9:
                    if not best or fit > best[0]:
                        best = (fit, e, flipped)
        if best and best[0] >= 1.4:
            break
    return (best[1], best[2]) if best else (None, False)

# ---------------------------
# ONE GAME'S SHOTS
# ---------------------------
EVENT_KINDS = ("rebound", "turnover", "steal")

def seconds_left(clock):
    parts = re.findall(r"\d+", clock or "")
    return int(parts[0]) * 60 + int(parts[1]) if len(parts) >= 2 else None

def read_summary(summary, event, flipped):
    """ESPN's game summary -> our shots and events lists (side 0 = our home team, 1 = our away team)."""
    names = {}
    for team in summary.get("boxscore", {}).get("players", []):
        for block in team.get("statistics", []):
            for a in block.get("athletes", []):
                athlete = a.get("athlete", {})
                names[str(athlete.get("id"))] = athlete.get("displayName", "")
    espn_home_id = event["home"]["id"]
    def side_of(play):
        team_id = str(play.get("team", {}).get("id"))
        if team_id not in (event["home"]["id"], event["away"]["id"]): return None
        espn_home = team_id == espn_home_id
        return (1 if espn_home else 0) if flipped else (0 if espn_home else 1)

    shots, events = [], []
    for play in summary.get("plays", []):
        side = side_of(play)
        if side is None: continue
        period = play.get("period", {}).get("number")
        left = seconds_left(play.get("clock", {}).get("displayValue"))
        kind = play.get("type", {}).get("text", "")
        people = [str(p.get("athlete", {}).get("id")) for p in play.get("participants", [])]
        if play.get("shootingPlay"):
            spot = play.get("coordinate") or {}
            x, y = spot.get("x"), spot.get("y")
            if x is None or y is None or abs(x) > 200 or abs(y) > 200:   # free throws carry a meaningless spot
                x = y = None
            made = bool(play.get("scoringPlay"))
            shots.append([side, names.get(people[0], "") if people else "", period, left, kind, int(made), play.get("scoreValue") or 0,
                          x, y, names.get(people[1], "") if made and len(people) > 1 else ""])
        elif any(word in kind.lower() for word in EVENT_KINDS):
            events.append([side, period, left, kind])
    return shots, events

def save_game(game, event, flipped, summary):
    shots, events = read_summary(summary, event, flipped)
    if not shots:
        return 0
    data = {"game_id": game["id"], "espn_id": event["id"], "date": game["date"], "source": SOURCE,
            "home_team": game["home"], "away_team": game["away"], "shots": shots, "events": events}
    for folder in game["folders"]:
        os.makedirs(os.path.join(folder, SHOTS_FOLDER), exist_ok=True)
        with open(os.path.join(folder, SHOTS_FOLDER, game["id"] + ".json"), "w", encoding="utf-8") as out:
            json.dump(data, out, separators=(",", ":"))
    return len(shots)

# ---------------------------
# MAIN
# ---------------------------
def main():
    games = load_our_games()
    # Optional: name some teams to do only their games, e.g.  python "collect\9espnshots.py" Alabama Duke
    wanted = [w.lower() for w in sys.argv[1:]]
    if wanted:
        games = {i: g for i, g in games.items() if any(os.path.basename(f).lower() in wanted for f in g["folders"])}
    team_ids = read_json(TEAM_IDS_FILE, {})
    votes = defaultdict(Counter)

    print(f"{len(games)} games listed. Already-saved games are skipped; this can be stopped and run again.", flush=True)
    quiet_passes = 0
    try:
        for attempt in range(1, MAX_PASSES + 1):
            todo = sorted((g for g in games.values() if not is_saved(g)), key=lambda g: (g["date"], g["id"]))
            if not todo:
                break
            print(f"\n===== Pass {attempt}: {len(todo)} games to get =====", flush=True)
            saved = 0
            scoreboards.clear()
            for n, game in enumerate(todo, 1):
                label = f"[{n}/{len(todo)}] {game['date']}  {game['away']} {game['away_score']} at {game['home']} {game['home_score']}"
                event, flipped = find_espn_game(game, team_ids)
                if not event:
                    print(f"{label}: not found on ESPN's scoreboard", flush=True)
                    continue
                summary = fetch(SUMMARY_URL, {"event": event["id"]})
                if not summary:
                    print(f"{label}: no answer from ESPN - will retry", flush=True)
                    continue
                count = save_game(game, event, flipped, summary)
                if not count:
                    print(f"{label}: ESPN has no play-by-play for it (game {event['id']})", flush=True)
                    continue
                saved += 1
                home, away = (event["away"], event["home"]) if flipped else (event["home"], event["away"])
                votes[game["home"]][home["id"]] += 1
                votes[game["away"]][away["id"]] += 1
                print(f"{label}: {count} shots", flush=True)
                if saved % 200 == 0:
                    remember_team_ids(team_ids, votes)
            remember_team_ids(team_ids, votes)
            print(f"Pass {attempt}: saved {saved}, still missing {len(todo) - saved}", flush=True)
            quiet_passes = 0 if saved else quiet_passes + 1
            if quiet_passes >= 2:     # two passes in a row with nothing new: what is left is not on ESPN
                break
            if len(todo) - saved:
                time.sleep(20)
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")
    remember_team_ids(team_ids, votes)

    missing = [g for g in games.values() if not is_saved(g)]
    print("-" * 30)
    print(f"Games with shots saved: {len(games) - len(missing)} of {len(games)}")
    print(f"Games still missing: {len(missing)}")
    for g in sorted(missing, key=lambda g: g["date"])[:60]:
        print(f"   {g['date']}  {g['away']} at {g['home']}  (game {g['id']})")
    print("-" * 30)

def remember_team_ids(team_ids, votes):
    """Each team's ESPN id is whichever one it was matched to most often."""
    for team, counts in votes.items():
        team_ids[team] = counts.most_common(1)[0][0]
    try:
        with open(TEAM_IDS_FILE, "w", encoding="utf-8") as out:
            json.dump(team_ids, out, indent=1, sort_keys=True)
    except Exception:
        pass

if __name__ == "__main__":
    main()
