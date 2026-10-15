import os
import sys
import json

# The name matching between box scores and rosters lives with the player stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dashboard"))
import Playerstat

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/2223"
SEASON = 2023
ROSTER_FILE = f"roster_{SEASON}.json"

# The roster files come from Sports Reference and count the whole season, postseason included.
# The box scores stop on 2023/03/12. This rewrites each player's games and minutes from the box scores,
# so the rosters cover the same games as everything else. The Sports Reference numbers are kept
# as "season_games" / "season_minutes". Add  --check  to see what would change without saving.

def trim_rosters(save=True):
    teams_changed = 0
    players_changed = 0
    minutes_before = minutes_after = 0
    not_in_box = []     # on the roster with minutes, but no box score line found
    more_than_season = []   # box scores show more minutes than the whole-season number

    for conf in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conf)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            team_path = os.path.join(conf_path, team)
            roster_path = os.path.join(team_path, ROSTER_FILE)
            if not os.path.exists(roster_path): continue

            with open(roster_path, "r", encoding="utf-8") as f:
                roster_data = json.load(f)
            _, _, box_players, _ = Playerstat.load_team_boxscores(team_path, team)
            if not box_players:
                print(f"{team}: no box scores, left alone")
                continue

            roster = {Playerstat.norm_name(p["name"]): p for p in roster_data["players"]}
            matches = Playerstat.match_roster(box_players, roster)
            games, minutes = {}, {}
            for box_key, roster_key in matches.items():
                if roster_key:
                    games[roster_key] = games.get(roster_key, 0) + int(box_players[box_key]["G"])
                    minutes[roster_key] = minutes.get(roster_key, 0) + box_players[box_key]["MP"]

            changed = False
            for key, p in roster.items():
                p.setdefault("season_games", p["games"])
                p.setdefault("season_minutes", p["minutes"])
                new_games, new_minutes = games.get(key, 0), round(minutes.get(key, 0))
                minutes_before += p["season_minutes"]
                minutes_after += new_minutes
                if key not in games and p["season_minutes"] >= 40:
                    not_in_box.append(f"{team}: {p['name']} ({p['season_minutes']} min)")
                if new_minutes > p["season_minutes"] + 10:
                    more_than_season.append(f"{team}: {p['name']} (box {new_minutes}, season {p['season_minutes']})")
                if (p["games"], p["minutes"]) != (new_games, new_minutes):
                    p["games"], p["minutes"] = new_games, new_minutes
                    changed = True
                    players_changed += 1

            if changed:
                teams_changed += 1
                if save:
                    with open(roster_path, "w", encoding="utf-8") as f:
                        json.dump(roster_data, f, indent=1)

    print("-" * 30)
    print(f"{'ROSTERS UPDATED.' if save else 'CHECK ONLY, nothing saved.'}")
    print(f"Teams changed: {teams_changed}")
    print(f"Players changed: {players_changed}")
    print(f"Total minutes: {minutes_before} for the whole season -> {minutes_after} through the box scores")
    print(f"Roster players with 40+ season minutes and no box score line: {len(not_in_box)}")
    for line in not_in_box: print("   " + line)
    print(f"Players with more box score minutes than season minutes: {len(more_than_season)}")
    for line in more_than_season: print("   " + line)
    print("-" * 30)

if __name__ == "__main__":
    trim_rosters(save="--check" not in sys.argv)
