import os
import sys
import json
import shutil

# Puts the converted stats.ncaa.org play-by-play (made by ncaa_stats_reader.py) into a season's data, in place of the
# play-by-play it had:   python tools/use_ncaa_stats.py 2425
# Each team's old play-by-play folder is first moved aside to "playbyplay_before_ncaa_stats" (kept, not deleted), so
# it can be put back. Only the play-by-play is replaced: the shot files keep their spots on the floor and the
# turnover files stay as they are. For a team that has no shot or turnover files at all (a season built from the
# stats.ncaa.org files alone), those are copied in too. Both the pre-tournament folder and the full-season one are done.
#     python tools/use_ncaa_stats.py 2425 undo     puts the old play-by-play back

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
FOLDERS = {"2526": ["data/seasons/2526", "data/seasons/2526 full"]}
BACKUP = "playbyplay_before_ncaa_stats"

def main():
    code = next((a for a in sys.argv[1:] if a.isdigit() and len(a) == 4), None)
    undo = "undo" in sys.argv[1:]
    staged_root = os.path.join(ROOT, "data/ncaa stats converted", code or "")
    if not code or not os.path.isdir(staged_root):
        print("Convert the season first:  python tools/ncaa_stats_reader.py " + (code or "2425"))
        return
    for name in FOLDERS.get(code, [f"data/seasons/{code}", f"data/seasons/{code} full"]):
        base = os.path.join(ROOT, name)
        if not os.path.isdir(base): continue
        teams = replaced = kept = 0
        for conf in sorted(os.listdir(base)):
            conf_path = os.path.join(base, conf)
            if not os.path.isdir(conf_path): continue
            for team in sorted(os.listdir(conf_path)):
                team_path = os.path.join(conf_path, team)
                current, backup = os.path.join(team_path, "playbyplay"), os.path.join(team_path, BACKUP)
                if undo:
                    if os.path.isdir(backup):
                        if os.path.isdir(current): shutil.rmtree(current)
                        os.rename(backup, current)
                        teams += 1
                    continue
                staged = os.path.join(staged_root, conf, team, "playbyplay")
                if not os.path.isdir(staged): continue
                listed = {str(g) for g in json.load(open(os.path.join(team_path, "games.json"), encoding="utf-8"))} if os.path.exists(os.path.join(team_path, "games.json")) else set()
                if os.path.isdir(current) and not os.path.isdir(backup):
                    shutil.copytree(current, backup)          # the old play-by-play, kept
                os.makedirs(current, exist_ok=True)
                for f in os.listdir(staged):
                    if f[:-5] in listed:                      # only this folder's games (the pre-tournament one has no postseason)
                        shutil.copyfile(os.path.join(staged, f), os.path.join(current, f))
                        replaced += 1
                for sub_folder in ("shots", "cbbd"):          # only where the season has none of its own
                    source_dir, target = os.path.join(staged_root, conf, team, sub_folder), os.path.join(team_path, sub_folder)
                    if os.path.isdir(source_dir) and not os.path.isdir(target):
                        os.makedirs(target)
                        for f in os.listdir(source_dir):
                            if f[:-5] in listed:
                                shutil.copyfile(os.path.join(source_dir, f), os.path.join(target, f))
                kept += len([f for f in os.listdir(current) if f.endswith(".json")]) - len([f for f in os.listdir(staged) if f[:-5] in listed])
                teams += 1
        print(f"{name}: " + (f"old play-by-play put back for {teams} teams" if undo else
              f"{teams} teams, {replaced} team-games now from stats.ncaa.org, {kept} kept from before (no stats.ncaa.org file for them)"))

if __name__ == "__main__":
    main()
