import os
import importlib.util

# Reuse the matching and checking rules from 8srboxscores.py, so both scripts agree on what a problem is
spec = importlib.util.spec_from_file_location("srbox", os.path.join(os.path.dirname(os.path.abspath(__file__)), "8srboxscores.py"))
srbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srbox)

# Lists every problem game left after running 8srboxscores.py. Nothing is downloaded or changed.
#   - no Sports Reference game found for one of our games
#   - a game that was found but did not get imported (scores differ, teams could not be told apart...)
#   - an imported box score whose player lines still don't add up to the team's points and minutes

def audit_teams():
    team_folders = srbox.get_team_folders()
    problems = 0
    clean_teams = 0
    not_started = []

    conference = None
    for team, team_path in team_folders.items():
        schedule = srbox.read_json(os.path.join(team_path, srbox.SCHEDULE_FILE.format(srbox.SEASON)))
        if schedule is None:
            not_started.append(team)
            continue

        lines = []
        matched, unmatched = srbox.match_games(schedule, team_path)
        for game in unmatched:
            lines.append(f"{game}: no Sports Reference game found")

        games = {str(g.get("game_id")): g for g in srbox.read_json(os.path.join(team_path, "game_scores.json"), [])}
        for game_id in sorted(matched, key=lambda g: games[g].get("date", "")):
            g = games[game_id]
            label = f"{g.get('date')}  {g.get('away_team')} {g.get('away_score')} at {g.get('home_team')} {g.get('home_score')}  (game {game_id})"
            box = srbox.read_json(os.path.join(team_path, "boxscores", f"{game_id}.json"))
            if not box:
                lines.append(f"{label}: box score file is missing")
            elif box.get("source") != srbox.SOURCE:
                lines.append(f"{label}: not imported")
            else:
                for t in box.get("teams", []):
                    players = t["starters_table"] + t["bench_table"]
                    minutes = sum(float(p["MIN"] or 0) for p in players)
                    short = t["team_totals"]["PTS"] - sum(p["PTS"] for p in players)
                    # A basket credited to the team rather than a player (2 or 3 points) is normal, not a problem
                    if minutes < 195 or not 0 <= short <= 3:
                        lines.append(f"{label}: {t['team_name']} player lines don't add up ({minutes:.0f} minutes, {short} points unaccounted for)")

        if lines:
            if os.path.basename(os.path.dirname(team_path)) != conference:
                conference = os.path.basename(os.path.dirname(team_path))
                print(f"\n===== {conference} =====")
            print(f"--- {team}: {len(lines)} problem games ---")
            for line in lines:
                print("   " + line)
            problems += len(lines)
        else:
            clean_teams += 1

    print("-" * 30)
    print(f"Problem games: {problems}")
    print(f"Teams fully imported with no problems: {clean_teams}")
    print(f"Teams not started yet: {len(not_started)}")
    print("-" * 30)

if __name__ == "__main__":
    audit_teams()
