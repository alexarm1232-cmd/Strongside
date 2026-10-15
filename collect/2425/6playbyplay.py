import os
import sys
import json
import requests
import time
import re

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2425"
PBP_FOLDER = "playbyplay"       # saved inside each team folder, e.g. data/seasons/2526/SEC/Alabama/playbyplay/6505422.json
# Same data that is shown on https://www.ncaa.com/game/{id}/play-by-play
API_URL = "https://ncaa-api.henrygd.me/game/{}/play-by-play"
DELAY_SECONDS = 0.4

def build_team_map():
    team_map = {}
    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if os.path.isdir(conf_path):
            for team in sorted(os.listdir(conf_path)):
                team_path = os.path.join(conf_path, team)
                if os.path.isdir(team_path):
                    team_map[team] = team_path
    return team_map

def build_game_map(team_directory_map):
    """Game id -> every team folder that lists it in games.json (both teams, when both are ours)."""
    game_map = {}
    for team_folder, team_path in team_directory_map.items():
        games_file = os.path.join(team_path, "games.json")
        if not os.path.exists(games_file): continue

        with open(games_file, "r") as f:
            try:
                games_list = json.load(f)
            except: continue

        for game_id in games_list:
            game_id = str(game_id).strip()
            if team_folder not in game_map.setdefault(game_id, []):
                game_map[game_id].append(team_folder)
    return game_map

def clock_to_seconds(clock):
    """'19:41' -> 1181 seconds left in the period."""
    parts = re.findall(r"\d+", clock or "")
    return int(parts[0]) * 60 + int(parts[1]) if len(parts) >= 2 else None

def transform_to_play_list(raw_data, game_id):
    """Processes raw API JSON into one flat, time-ordered list of plays."""
    names = {str(t.get("teamId")): t.get("nameShort", "") for t in raw_data.get("teams", [])}
    home = next((t for t in raw_data.get("teams", []) if t.get("isHome")), {})
    away = next((t for t in raw_data.get("teams", []) if not t.get("isHome")), {})

    structured_output = {
        "game_id": game_id,
        "game_info": raw_data.get("description", "Unknown Game"),
        "status": raw_data.get("status", ""),
        "home_team": home.get("nameShort", ""),
        "away_team": away.get("nameShort", ""),
        "plays": []
    }

    plays = structured_output["plays"]
    for period in raw_data.get("periods", []):
        for p in period.get("playbyplayStats", []):
            text = (p.get("homeText") or p.get("visitorText") or p.get("eventDescription") or "").strip()
            text = text.replace("jumpshot", "jump shot")

            # The feed repeats some plays with the space after the name missing
            # ("Jeremy Elyzeemisses three point jump shot"). Skip those copies.
            squeezed = re.sub(r"\s", "", text)
            last = plays[-1] if plays else None
            if last and last["period"] == period.get("periodNumber") and last["clock"] == p.get("clock", ""):
                if squeezed == re.sub(r"\s", "", last["text"]) and text != last["text"]:
                    continue

            # It also lists assisted baskets and stolen turnovers twice, the second time
            # with "(... assists)" / "(... steals)" added. Keep only the fuller one.
            i = len(plays) - 1
            while i >= 0 and plays[i]["period"] == period.get("periodNumber") and plays[i]["clock"] == p.get("clock", ""):
                if squeezed.startswith(re.sub(r"\s", "", plays[i]["text"]) + "("):
                    del plays[i]
                    break
                i -= 1

            plays.append({
                "period": period.get("periodNumber"),
                "period_name": period.get("periodDisplay", ""),
                "clock": p.get("clock", ""),
                "seconds_left": clock_to_seconds(p.get("clock")),
                "team": names.get(str(p.get("teamId")), ""),
                "is_home": bool(p.get("isHome")),
                "home_score": p.get("homeScore"),
                "away_score": p.get("visitorScore"),
                "text": text
            })
    return structured_output

def get_play_by_play():
    team_directory_map = build_team_map()

    # Optional: name some teams to fetch only those, e.g.  python "collect\6playbyplay.py" Alabama Duke
    wanted = [w.lower() for w in sys.argv[1:]]
    if wanted:
        team_directory_map = {t: p for t, p in team_directory_map.items() if t.lower() in wanted}

    game_map = build_game_map(team_directory_map)
    total_files_created = 0
    skipped = 0
    failed = 0

    print(f"{len(game_map)} games listed. Already-saved games are skipped.")
    try:
        for game_id, team_folders in game_map.items():
            destinations = [os.path.join(team_directory_map[t], PBP_FOLDER, f"{game_id}.json") for t in team_folders]
            if all(os.path.exists(d) for d in destinations):
                skipped += 1
                continue

            try:
                response = requests.get(API_URL.format(game_id), timeout=10)
                time.sleep(DELAY_SECONDS)
                if response.status_code != 200:
                    print(f"Game {game_id}: no play-by-play ({response.status_code})")
                    failed += 1
                    continue

                play_data = transform_to_play_list(response.json(), game_id)
                if not play_data["plays"]:
                    print(f"Game {game_id}: no plays listed yet")
                    failed += 1
                    continue

                for dest in destinations:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "w", encoding="utf-8") as out:
                        json.dump(play_data, out, indent=1)
                    total_files_created += 1

                print(f"Game {game_id}: {play_data['game_info']} - {len(play_data['plays'])} plays -> {', '.join(team_folders)}")
            except Exception as e:
                print(f"Error on {game_id}: {e}")
                failed += 1
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    print("-" * 30)
    print(f"SYNC COMPLETE.")
    print(f"Total play-by-play files created: {total_files_created}")
    print(f"Games already saved: {skipped}")
    print(f"Games with no play-by-play: {failed}")
    print("-" * 30)

if __name__ == "__main__":
    get_play_by_play()
