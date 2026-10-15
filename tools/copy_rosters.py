import os
import sys
import shutil

# One season's "this year" roster files are the next season back's "last year" ones, so they are copied instead of
# being downloaded from Sports Reference a second time:   python tools/copy_rosters.py 2324 2223 2023
#   (from the 2023-24 folders, into the 2022-23 folders, the roster_2023.json files)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder

def team_folders(code):
    base = os.path.join(ROOT, "data/seasons/" + code)
    teams = {}
    for conference in os.listdir(base):
        conf_path = os.path.join(base, conference)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                if os.path.isdir(os.path.join(conf_path, team)):
                    teams[team] = os.path.join(conf_path, team)
    return teams

def main():
    source_code, dest_code, year = sys.argv[1:4]
    name = f"roster_{year}.json"
    source, dest = team_folders(source_code), team_folders(dest_code)
    copied = 0
    for team, folder in dest.items():
        target = os.path.join(folder, name)
        if team in source and os.path.exists(os.path.join(source[team], name)) and not os.path.exists(target):
            shutil.copyfile(os.path.join(source[team], name), target)
            copied += 1
    print(f"{copied} of {len(dest)} teams' {name} copied from {source_code} to {dest_code}")

if __name__ == "__main__":
    main()
