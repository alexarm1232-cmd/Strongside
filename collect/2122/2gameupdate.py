import requests
import json
import time
import re
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

# ---------------------------
# SETTINGS
# ---------------------------
MASTER_FOLDER = Path("data/seasons/2122")
START_DATE = date(2021, 11, 9)
END_DATE = date(2022, 3, 13)
RETRY_LIMIT = 3
TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 0.5 # Slightly faster for scoreboard
MATCH_THRESHOLD = 0.90

def clean_name(name):
    """Removes periods, parentheses, spaces, and non-letter characters."""
    if not name: return ""
    # Lowercase and remove anything that isn't a letter or number
    return re.sub(r'[^a-z0-9]', '', name.lower())

# Step 1: Build team lookup
# We store the 'clean' version of the folder name as the key for exact matching
team_files = {file_path.parent.name: file_path for file_path in MASTER_FOLDER.glob("*/**/games.json")}
# Pre-calculate clean versions of our local folder names
clean_team_lookup = {clean_name(name): name for name in team_files.keys()}

print(f"Found {len(team_files)} teams to update.")

def match_team_name(raw_name):
    if not raw_name: return None
    
    cleaned_api_name = clean_name(raw_name)
    
    # PRIORITY 1: Alpha-Exact Match (e.g., "st. thomas (mn)" -> "stthomasmn")
    if cleaned_api_name in clean_team_lookup:
        return clean_team_lookup[cleaned_api_name]
    
    # PRIORITY 2: Fuzzy Match (Fallback for major differences)
    best_match = None
    best_ratio = 0
    for folder_name in team_files.keys():
        ratio = SequenceMatcher(None, raw_name.lower(), folder_name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = folder_name
            
    if best_ratio >= MATCH_THRESHOLD:
        return best_match
        
    return None

# Open skipped games log
skipped_log_path = MASTER_FOLDER / "skipped_games.log"
skipped_log = open(skipped_log_path, "a", encoding="utf-8")

# Stats
total_games_added = 0
total_games_processed = 0
total_games_skipped = 0

current = START_DATE
while current <= END_DATE:
    # Use the current day and calculate the month logic
    month_start = current.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = min(next_month - timedelta(days=1), END_DATE)

    print(f"--- Fetching: {month_start.strftime('%B %Y')} ---")

    day = current # Use day-by-day to avoid skipping start date logic
    while day <= month_end:
        date_str = day.strftime("%Y/%m/%d")
        url = f"https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1/{date_str}/all-conf"

        success = False
        for attempt in range(1, RETRY_LIMIT + 1):
            try:
                resp = requests.get(url, timeout=TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
                games = data.get("games", [])
                success = True
                break
            except Exception as e:
                if attempt < RETRY_LIMIT:
                    time.sleep(2)
                else:
                    print(f"[{date_str}] Skipping after {RETRY_LIMIT} attempts: {e}")

        if success:
            team_new_games = defaultdict(list)
            for game_entry in games:
                game = game_entry.get("game", {})
                game_id = str(game.get("gameID")) # Keep as string for comparison
                if not game_id: continue

                home_raw = game.get("home", {}).get("names", {}).get("short", "")
                away_raw = game.get("away", {}).get("names", {}).get("short", "")

                home_match = match_team_name(home_raw)
                away_match = match_team_name(away_raw)

                if home_match and away_match:
                    team_new_games[home_match].append(game_id)
                    team_new_games[away_match].append(game_id)
                    total_games_processed += 1
                else:
                    total_games_skipped += 1
                    skipped_log.write(f"{date_str} | ID: {game_id} | H: {home_raw}->{home_match} | A: {away_raw}->{away_match}\n")

            # Update each team's games.json
            for team_name, new_game_ids in team_new_games.items():
                team_file = team_files[team_name]
                try:
                    existing = []
                    if team_file.exists():
                        with open(team_file, "r") as f:
                            existing = [str(g) for g in json.load(f)]
                    
                    unique_new = [gid for gid in new_game_ids if gid not in set(existing)]
                    if unique_new:
                        existing.extend(unique_new)
                        with open(team_file, "w") as f:
                            json.dump(existing, f, indent=2)
                        total_games_added += len(unique_new)
                except Exception as e:
                    print(f"Error updating {team_name}: {e}")

        day += timedelta(days=1)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    current = next_month

skipped_log.close()

# Summary
print(f"\n" + "="*30)
print(f"Update Complete")
print(f"New games found and linked: {total_games_added}")
print(f"Games successfully matched: {total_games_processed}")
print(f"Games failed to match: {total_games_skipped}")
print(f"Log: {skipped_log_path}")
print("="*30)