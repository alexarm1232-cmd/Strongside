import os
import json

BASE_DIR = "data/seasons/2526 full"

def audit_teams():
    differences_found = False
    
    if not os.path.exists(BASE_DIR):
        print(f"Error: {BASE_DIR} directory not found.")
        return

    # Walk through Conference > Team
    for conf in os.listdir(BASE_DIR):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        
        for team in os.listdir(conf_path):
            team_path = os.path.join(conf_path, team)
            games_json_path = os.path.join(team_path, "games.json")
            boxscore_dir = os.path.join(team_path, "boxscores")
            
            # 1. Get List of IDs from games.json
            expected_ids = []
            if os.path.exists(games_json_path):
                try:
                    with open(games_json_path, "r") as f:
                        data = json.load(f)
                        # Ensure all IDs are strings for comparison
                        expected_ids = [str(gid).strip() for gid in data]
                except Exception:
                    print(f"Error reading games.json for {team}")

            # 2. Get List of IDs actually downloaded
            existing_ids = []
            if os.path.exists(boxscore_dir):
                # Strip '.json' from filename to get the ID
                existing_ids = [f.replace('.json', '') for f in os.listdir(boxscore_dir) if f.endswith('.json')]

            # 3. Identify Missing IDs
            missing = [gid for gid in expected_ids if gid not in existing_ids]

            if missing:
                differences_found = True
                print(f"\n--- Mismatch Found: {team} ---")
                print(f"  Expected: {len(expected_ids)} | Found: {len(existing_ids)}")
                print(f"  Missing IDs: {', '.join(missing)}")

    if not differences_found:
        print("No differences - All boxscores accounted for.")

if __name__ == "__main__":
    audit_teams()