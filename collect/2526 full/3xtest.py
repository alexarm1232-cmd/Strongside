from pathlib import Path

# --- CONFIG ---
MASTER_FOLDER = Path("data/seasons/2526 full")
ID_FILE = "games.json"
SCORE_FILE = "game_scores.json"

def audit_teams():
    # Find every folder that contains a games.json
    all_id_files = list(MASTER_FOLDER.rglob(ID_FILE))
    total_teams = len(all_id_files)
    
    teams_with_scores = []
    teams_missing_scores = []

    for id_path in all_id_files:
        team_folder = id_path.parent
        score_path = team_folder / SCORE_FILE
        
        if score_path.exists():
            teams_with_scores.append(team_folder.name)
        else:
            teams_missing_scores.append(team_folder.name)

    # --- OUTPUT SUMMARY ---
    print("-" * 30)
    print(f"TEAM AUDIT SUMMARY")
    print("-" * 30)
    print(f"Total Teams Found:     {total_teams}")
    print(f"Teams with Scores:     {len(teams_with_scores)}")
    print(f"Teams Missing Scores:  {len(teams_missing_scores)}")
    print("-" * 30)

    if teams_missing_scores:
        print("\n[!] MISSING SCORE FILES IN:")
        for team in sorted(teams_missing_scores):
            print(f"  -> {team}")
    else:
        print("\n[SUCCESS] All teams are fully updated!")

if __name__ == "__main__":
    audit_teams()