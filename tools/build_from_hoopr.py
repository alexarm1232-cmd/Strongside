import os
import sys
import shutil

# Builds whole seasons from the ESPN data downloaded through hoopR (tools/hoopr_pbp.R), for the seasons stats.ncaa.org
# has no box scores or play-by-play for (2005-06 to 2008-09), start to finish:
#     python tools/build_from_hoopr.py 0809 0708 0607 0506
# Give the seasons newest first: each season's "this year" rosters are copied from the season after it. The same steps
# as tools/build_from_ncaa_stats.py, with the hoopR builders in place of the stats.ncaa.org ones:
#   1. games and box scores                  tools/hoopr_season.py
#   2. play-by-play, shots and turnovers     tools/hoopr_plays.py
#   3. rosters                               copied from the next season, the rest from collect/<code>/5rosterfetch.py
#   4. rosters trimmed to the box scores     collect/<code>/7rostertrim.py (and the same for the full season)
#   5. the pages                             dashboard/main.py <code> and <code>f
# Progress goes to logs/build_from_ncaa_stats.txt (the same log); each step's output to logs/build_from_ncaa_stats/.

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_from_ncaa_stats import ROOT, SEASONS, STEP_LOGS, log, run, full_season_scripts

def build(code, newer):
    ended = 2000 + int(code[2:])
    pre, full = os.path.join(SEASONS, code), os.path.join(SEASONS, code + " full")
    log(f"{code} ({ended - 1}-{code[2:]}) from hoopR")
    run(f"{code}_games_hoopr", "tools/hoopr_season.py", code)
    for name in os.listdir(pre):
        if os.path.isfile(os.path.join(pre, name)) and name.endswith(".json"):
            shutil.copyfile(os.path.join(pre, name), os.path.join(full, name))
    run(f"{code}_plays_hoopr", "tools/hoopr_plays.py", code)
    if newer:
        run(f"{code}_rosters_copied", "tools/copy_rosters.py", newer, code, str(ended))
    run(f"{code}_rosters", f"collect/{code}/5rosterfetch.py")
    run(f"{code}_rostertrim", f"collect/{code}/7rostertrim.py")
    for year in (ended, ended - 1):
        run(f"{code}_full_rosters_{year}", "tools/copy_rosters.py", code, code + " full", str(year))
    full_season_scripts(code)
    run(f"{code}_full_rostertrim", f"collect/{code} full/7rostertrim.py")
    for key in (code, code + "f"):
        run(f"{key}_page", "dashboard/main.py", key, "quiet")

def main():
    codes = [a for a in sys.argv[1:] if a.isdigit() and len(a) == 4]
    if not codes:
        print("Name the seasons, newest first, e.g.  python tools/build_from_hoopr.py 0809 0708"); return
    os.makedirs(STEP_LOGS, exist_ok=True)
    built = sorted(c for c in os.listdir(SEASONS) if c.isdigit())
    for code in codes:
        newer = next((c for c in built if int(c[:2]) == int(code[:2]) + 1), None)
        try:
            build(code, newer)
        except RuntimeError as failed:
            log(f"{code}: stopped at {failed}; see logs/build_from_ncaa_stats/{failed}.txt"); return
    log("all done")

if __name__ == "__main__":
    main()
