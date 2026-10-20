import requests
import json
import time
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

# --- SETTINGS ---
MASTER_FOLDER = Path("data/seasons/1011 full")
START_DATE = date(2010, 11, 8)
END_DATE = date(2011, 3, 13)
MATCH_THRESHOLD = 0.85

# 1. Build team lookup
team_files = {file_path.parent.name.lower(): file_path for file_path in MASTER_FOLDER.glob("*/**/games.json")}
print(f"Found {len(team_files)} teams in your directory.")

def match_team_name(name):
    if not name: return None
    name = name.lower()
    best_match, best_ratio = None, 0
    for team in team_files:
        ratio = SequenceMatcher(None, name, team).ratio()
        if ratio > best_ratio:
            best_ratio, best_match = ratio, team
    return best_match if best_ratio >= MATCH_THRESHOLD else None

all_scores_found = defaultdict(list)

# 2. Fetch with corrected 2026 nesting
current_day = START_DATE
while current_day <= END_DATE:
    date_str = current_day.strftime("%Y/%m/%d")
    url = f"https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1/{date_str}/all-conf"

    try:
        print(f"   Scanning: {date_str}...", end="\r")
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            raw_data = resp.json()
            # CRITICAL FIX: The 2026 API wraps games in a 'game' object
            for entry in raw_data.get("games", []):
                g = entry.get("game", {}) # This was the missing link
                
                gid = str(g.get('gameID'))
                h_name = g.get('home', {}).get('names', {}).get('short')
                a_name = g.get('away', {}).get('names', {}).get('short')
                
                h_folder = match_team_name(h_name)
                a_folder = match_team_name(a_name)

                game_data = {
                    "game_id": gid,
                    "date": date_str,
                    "away_team": a_name,
                    "away_score": g.get('away', {}).get('score'),
                    "home_team": h_name,
                    "home_score": g.get('home', {}).get('score')
                }

                if h_folder: all_scores_found[h_folder].append(game_data)
                if a_folder: all_scores_found[a_folder].append(game_data)
    except Exception as e:
        pass
    
    current_day += timedelta(days=1)
    time.sleep(0.05)

# 3. Save Output (Strictly based on your CURATED games.json)
print("\n\n--- Writing game_scores.json files ---")
files_created = 0

for team_name, score_list in all_scores_found.items():
    json_path = team_files[team_name]
    
    # Check your existing IDs
    with open(json_path, 'r') as f:
        curated_ids = [str(gid) for gid in json.load(f)]

    # Only include what you previously kept
    final_output = [gm for gm in score_list if gm['game_id'] in curated_ids]

    if final_output:
        out_file = json_path.parent / "game_scores.json"
        with open(out_file, 'w', encoding="utf-8") as f:
            json.dump(final_output, f, indent=4)
        files_created += 1
        print(f"   [SUCCESS] {team_name} saved.")

print(f"\nFinished! Created {files_created} 'game_scores.json' files.")