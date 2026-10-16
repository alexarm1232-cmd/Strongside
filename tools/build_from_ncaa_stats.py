import os
import sys
import shutil
import subprocess
from datetime import datetime

# Builds whole seasons from the stats.ncaa.org files (data/ncaa stats), start to finish:
#     python tools/build_from_ncaa_stats.py 2122 2021 1920 1819
# Give the seasons newest first: each season's "this year" rosters are copied from the season after it, so only one
# year of rosters per season is downloaded from Sports Reference. For each season:
#   1. set aside any shot / play files from earlier sources (kept as <folder>_before_ncaa_stats)
#   2. games and box scores                  tools/ncaa_stats_season.py
#   3. play-by-play, shots and turnovers     tools/ncaa_stats_reader.py, then tools/use_ncaa_stats.py
#   4. rosters                               copied from the next season, the rest from collect/<code>/5rosterfetch.py
#   5. rosters trimmed to the box scores     collect/<code>/7rostertrim.py (and the same for the full season)
#   6. the pages                             dashboard/main.py <code> and <code>f
# Progress goes to logs/build_from_ncaa_stats.txt; each step's full output to logs/build_from_ncaa_stats/.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SEASONS = os.path.join(ROOT, "data", "seasons")
LOG = os.path.join(ROOT, "logs", "build_from_ncaa_stats.txt")
STEP_LOGS = os.path.join(ROOT, "logs", "build_from_ncaa_stats")
NO_FULL_SEASON = {"1920"}       # the 2019-20 season stopped before the postseason
OLD_SOURCES = ("playbyplay", "shots", "cbbd")

def log(text):
    line = f"{datetime.now():%m/%d %H:%M} {text}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run(label, *args):
    out = os.path.join(STEP_LOGS, label + ".txt")
    with open(out, "w", encoding="utf-8") as f:
        done = subprocess.run([sys.executable, "-u", *args], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                              env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    tail = open(out, encoding="utf-8", errors="replace").read().strip().splitlines()[-1:] or [""]
    log(f"   {label}: {'ok' if done.returncode == 0 else 'FAILED'} | {tail[0][:160]}")
    if done.returncode != 0:
        raise RuntimeError(label)

def team_folders(base):
    for conf in sorted(os.listdir(base)):
        conf_path = os.path.join(base, conf)
        if os.path.isdir(conf_path):
            for team in sorted(os.listdir(conf_path)):
                if os.path.isdir(os.path.join(conf_path, team)):
                    yield os.path.join(conf_path, team)

def set_aside_old_sources(base):
    moved = 0
    for team in team_folders(base):
        for name in OLD_SOURCES:
            path, kept = os.path.join(team, name), os.path.join(team, name + "_before_ncaa_stats")
            if os.path.isdir(path) and not os.path.exists(kept):
                os.rename(path, kept)
                moved += 1
    return moved

def full_season_scripts(code):
    """collect/<code> full: the season's scripts pointed at the full-season folder (only 7rostertrim.py is used here)."""
    source, dest = os.path.join(ROOT, "collect", code), os.path.join(ROOT, "collect", code + " full")
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(source):
        if name.endswith(".py"):
            text = open(os.path.join(source, name), encoding="utf-8").read()
            with open(os.path.join(dest, name), "w", encoding="utf-8", newline="") as out:
                out.write(text.replace(f'"data/seasons/{code}"', f'"data/seasons/{code} full"'))

def build(code, newer):
    ended = 2000 + int(code[2:])
    pre, full = os.path.join(SEASONS, code), os.path.join(SEASONS, code + " full")
    has_full = code not in NO_FULL_SEASON
    log(f"{code} ({ended - 1}-{code[2:]})")
    log(f"   set aside earlier shot/play folders: {set_aside_old_sources(pre)}")
    run(f"{code}_games", "tools/ncaa_stats_season.py", code)
    if has_full:
        for name in os.listdir(pre):
            if os.path.isfile(os.path.join(pre, name)) and name.endswith(".json"):
                shutil.copyfile(os.path.join(pre, name), os.path.join(full, name))
    elif os.path.isdir(full):
        shutil.rmtree(full)          # made by the games step; nothing in it differs from the season itself
    run(f"{code}_plays_convert", "tools/ncaa_stats_reader.py", code)
    run(f"{code}_plays_use", "tools/use_ncaa_stats.py", code)
    if newer:
        run(f"{code}_rosters_copied", "tools/copy_rosters.py", newer, code, str(ended))
    run(f"{code}_rosters", f"collect/{code}/5rosterfetch.py")
    run(f"{code}_rostertrim", f"collect/{code}/7rostertrim.py")
    keys = [code]
    if has_full:
        for year in (ended, ended - 1):
            run(f"{code}_full_rosters_{year}", "tools/copy_rosters.py", code, code + " full", str(year))
        full_season_scripts(code)
        run(f"{code}_full_rostertrim", f"collect/{code} full/7rostertrim.py")
        keys.append(code + "f")
    for key in keys:
        run(f"{key}_page", "dashboard/main.py", key, "quiet")

def main():
    codes = [a for a in sys.argv[1:] if a.isdigit() and len(a) == 4]
    if not codes:
        print("Name the seasons, newest first, e.g.  python tools/build_from_ncaa_stats.py 2122 2021")
        return
    os.makedirs(STEP_LOGS, exist_ok=True)
    built = sorted(c for c in os.listdir(SEASONS) if c.isdigit())
    for code in codes:
        newer = next((c for c in built if int(c[:2]) == int(code[:2]) + 1), None)
        try:
            build(code, newer)
        except RuntimeError as failed:
            log(f"{code}: stopped at {failed}; see logs/build_from_ncaa_stats/{failed}.txt")
            return
    log("all done")

if __name__ == "__main__":
    main()
