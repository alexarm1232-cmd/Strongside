import os
import json
import requests
import time
import re
from difflib import SequenceMatcher

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2425"
API_URL = "https://ncaa-api.henrygd.me/game/{}/boxscore"
MATCH_THRESHOLD = 0.90 

def clean_string(s):
    """Removes all non-alphanumeric characters for strict comparison."""
    if not s: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

def similar(a, b):
    """Standard fuzzy matching ratio."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def transform_to_table_format(raw_data):
    """Processes raw API JSON into the Starters/Bench table format."""
    structured_output = {
        "game_id": raw_data.get("instanceId"),
        "game_info": raw_data.get("description", "Unknown Game"),
        "teams": []
    }
    for entry in raw_data.get('teamBoxscore', []):
        team_id = entry.get('teamId')
        team_meta = next((t for t in raw_data.get('teams', []) if int(t['teamId']) == team_id), {})
        team_name = team_meta.get('nameShort', f"Team {team_id}")
        
        team_data = {
            "team_name": team_name,
            "starters_table": [],
            "bench_table": [],
            "team_totals": {}
        }

        for p in entry.get('playerStats', []):
            stat_line = {
                "Name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                "MIN": p.get("minutesPlayed", "0"),
                "PTS": int(p.get("points", 0)),
                "FG": f"{p.get('fieldGoalsMade')}-{p.get('fieldGoalsAttempted')}",
                "3PT": f"{p.get('threePointsMade')}-{p.get('threePointsAttempted')}",
                "FT": f"{p.get('freeThrowsMade')}-{p.get('freeThrowsAttempted')}",
                "REB": int(p.get("totalRebounds", 0)),
                "AST": int(p.get("assists", 0)),
                "PF": int(p.get("personalFouls", 0)),
                "TO": int(p.get("turnovers", 0)),
                "OREB": int(p.get("offensiveRebounds", 0)),
                "DREB": int(p.get("defensiveRebounds", 0)),
                "STL": int(p.get("steals", 0)),
                "BLK": int(p.get("blockedShots", 0))
            }
            if p.get('isStarter'):
                team_data["starters_table"].append(stat_line)
            else:
                team_data["bench_table"].append(stat_line)

        t = entry.get('teamStats', {})
        team_data["team_totals"] = {
            "PTS": int(t.get("points", 0)),
            "FG": f"{t.get('fieldGoalsMade')}-{t.get('fieldGoalsAttempted')}",
            "3PT": f"{t.get('threePointsMade')}-{t.get('threePointsAttempted')}",
            "FT": f"{t.get('freeThrowsMade')}-{t.get('freeThrowsAttempted')}",
            "REB": int(t.get("totalRebounds", 0)),
            "AST": int(t.get("assists", 0)),
            "PF": int(t.get("personalFouls", 0)),
            "TO": int(t.get("turnovers", 0)),
            "OREB": int(t.get("offensiveRebounds", 0)),
            "DREB": int(t.get("defensiveRebounds", 0)),
            "STL": int(t.get("steals", 0)),
            "BLK": int(t.get("blockedShots", 0))
        }
        structured_output["teams"].append(team_data)
    return structured_output

def build_team_map():
    team_map = {}
    for conf in os.listdir(BASE_DIR):
        conf_path = os.path.join(BASE_DIR, conf)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                team_path = os.path.join(conf_path, team)
                if os.path.isdir(team_path):
                    team_map[team] = team_path
    return team_map

def get_box_scores():
    team_directory_map = build_team_map()
    processed_games = set()
    total_files_created = 0 # Counter for created files

    for team_folder, team_path in team_directory_map.items():
        games_file = os.path.join(team_path, "games.json")
        if not os.path.exists(games_file): continue
        
        with open(games_file, "r") as f:
            try:
                games_list = json.load(f)
            except: continue

        for game_id in games_list:
            game_id = str(game_id).strip()
            if game_id in processed_games: continue

            try:
                response = requests.get(API_URL.format(game_id), timeout=10)
                if response.status_code == 200:
                    raw_data = response.json()
                    table_data = transform_to_table_format(raw_data)
                    
                    saved_to = []
                    for team_entry in raw_data.get('teams', []):
                        api_names = [team_entry.get('nameShort', ""), team_entry.get('nameFull', "")]
                        clean_api_names = [clean_string(n) for n in api_names]
                        
                        best_match = None
                        highest_score = 0
                        
                        # PRIORITY 1: ALPHA-ONLY EXACT MATCH (Strips all but letters/numbers)
                        for folder_name in team_directory_map:
                            if clean_string(folder_name) in clean_api_names:
                                best_match = folder_name
                                highest_score = 1.0
                                break
                        
                        # PRIORITY 2: 90% FUZZY FALLBACK (Only if exact fails)
                        if highest_score < 1.0:
                            for folder_name in team_directory_map:
                                for name in api_names:
                                    score = similar(name, folder_name)
                                    if score > highest_score and score >= MATCH_THRESHOLD:
                                        highest_score = score
                                        best_match = folder_name
                        
                        if best_match:
                            target_path = team_directory_map[best_match]
                            box_dir = os.path.join(target_path, "boxscores")
                            os.makedirs(box_dir, exist_ok=True)
                            
                            with open(os.path.join(box_dir, f"{game_id}.json"), "w") as out:
                                json.dump(table_data, out, indent=4)
                            
                            saved_to.append(best_match)
                            total_files_created += 1
                    
                    processed_games.add(game_id)
                    if len(saved_to) >= 2:
                        print(f"Game {game_id}: {saved_to[0]} vs {saved_to[1]}")
                    elif len(saved_to) == 1:
                        print(f"Game {game_id}: Only matched {saved_to[0]}")
                    
                    time.sleep(0.4)
            except Exception as e:
                print(f"Error on {game_id}: {e}")

    print("-" * 30)
    print(f"SYNC COMPLETE.")
    print(f"Total box score files created: {total_files_created}")
    print("-" * 30)

if __name__ == "__main__":
    get_box_scores()