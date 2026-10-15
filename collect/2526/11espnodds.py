import os
import sys
import json
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2526"
SHOTS_FOLDER = "shots"          # made by 9espnshots.py; each file there carries the game's ESPN id
ODDS_FILE = os.path.join(BASE_DIR, "draftkings_spreads_2026.json")
FIRST_DATE = "2025/11/01"       # every game: the line, and where ESPN says the game was played
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
WORKERS = 4                     # requests in flight at once
DELAY_SECONDS = 0.4             # each worker's wait after a request
PROVIDER = "DraftKings"

# ESPN's page for every game carries the betting line it showed for it, from DraftKings. This saves that line for
# each of our games, under the NCAA game id the box scores use:
#   "spread": the line for the team ESPN lists as home (-10.5 = that team was favoured by 10.5),
#   "home_id" / "away_id": ESPN's ids for its home and away teams (ESPN's home team is not always the one our
#   schedule calls home, so the line is tied to the team by id; espn_teams.json turns the ids into our names),
#   "total": the over/under, "home_ml" / "away_ml": the money lines, "details": the line as ESPN words it ("MTSU -10.5"),
#   "neutral": whether ESPN marks the game as played on a neutral floor (kept even when there is no line)
# A game ESPN has no DraftKings line for is saved with "spread": null, so it is not asked for again.
# Run it again at any time: it only fetches games it does not have yet.

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def load_our_games():
    """NCAA game id -> the ESPN id, date and the two teams (as the shot files name them)."""
    games = {}
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            shots_dir = os.path.join(conf_path, team, SHOTS_FOLDER)
            if not os.path.isdir(shots_dir): continue
            for f in os.listdir(shots_dir):
                if not f.endswith(".json") or f[:-5] in games: continue
                shots = read_json(os.path.join(shots_dir, f))
                if not shots or not shots.get("espn_id"): continue
                date = shots.get("date", "").replace("-", "/")
                if date < FIRST_DATE: continue
                games[f[:-5]] = {"espn_id": str(shots["espn_id"]), "date": date, "home_team": shots["home_team"], "away_team": shots["away_team"]}
    return games

def fetch_line(game):
    """The DraftKings line ESPN shows for one game, or None when the request failed (so it is tried again next run)."""
    try:
        response = requests.get(SUMMARY_URL, params={"event": game["espn_id"]}, headers=HEADERS, timeout=30)
    except Exception:
        time.sleep(3)
        return None
    time.sleep(DELAY_SECONDS)
    if response.status_code in (403, 429):
        time.sleep(60)
        return None
    if response.status_code != 200:
        return None
    try:
        data = response.json()
    except Exception:
        return None
    line = dict(game, provider=None, spread=None, total=None, home_ml=None, away_ml=None, details=None, home_id=None, away_id=None, neutral=None)
    # where the game was played, as ESPN has it
    event = ((data.get("header") or {}).get("competitions") or [{}])[0]
    line["neutral"] = bool(event.get("neutralSite"))
    for side in event.get("competitors") or []:
        line[side.get("homeAway", "") + "_id"] = str((side.get("team") or {}).get("id") or "")
    listed = [p for p in data.get("pickcenter") or [] if (p.get("provider") or {}).get("name") == PROVIDER and p.get("spread") is not None]
    if listed:
        pick = listed[0]
        home, away = pick.get("homeTeamOdds") or {}, pick.get("awayTeamOdds") or {}
        size = abs(float(pick["spread"]))
        # the favourite is named outright, so the sign does not depend on how the number happens to be written
        spread = -size if home.get("favorite") else size if away.get("favorite") else float(pick["spread"])
        line.update(provider=PROVIDER, spread=spread, total=pick.get("overUnder"), home_ml=home.get("moneyLine"), away_ml=away.get("moneyLine"), details=pick.get("details"))
        if home.get("teamId") and away.get("teamId"):
            line.update(home_id=str(home["teamId"]), away_id=str(away["teamId"]))
    return line

def main():
    games = load_our_games()
    saved = read_json(ODDS_FILE, {"source": "DraftKings, as shown on ESPN's page for each game", "games": {}})
    # a line saved before the team ids were kept is fetched again
    todo = [(game_id, game) for game_id, game in sorted(games.items(), key=lambda item: item[1]["date"])
            if game_id not in saved["games"] or "neutral" not in saved["games"][game_id]]
    print(f"{len(games)} games; {len(todo)} still to fetch.", flush=True)
    lock, done, failed = threading.Lock(), [0], [0]

    def work(item):
        game_id, game = item
        line = fetch_line(game)
        with lock:
            if line is None:
                failed[0] += 1
            else:
                saved["games"][game_id] = line
            done[0] += 1
            if done[0] % 250 == 0 or done[0] == len(todo):
                with open(ODDS_FILE, "w", encoding="utf-8") as f:
                    json.dump(saved, f, separators=(",", ":"))
                print(f"   {done[0]} of {len(todo)} ({failed[0]} to try again)", flush=True)

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            list(pool.map(work, todo))
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")
    with open(ODDS_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, separators=(",", ":"))
    have = [g for g in saved["games"].values() if g.get("spread") is not None]
    print("-" * 30)
    print(f"Games with a {PROVIDER} line: {len(have)} of {len(saved['games'])} fetched ({len(games) - len(saved['games'])} not fetched yet)")
    print("-" * 30)

if __name__ == "__main__":
    main()
