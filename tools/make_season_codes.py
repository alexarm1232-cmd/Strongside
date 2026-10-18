import os
import re
import sys
import json
import time
import requests

# Sets up a season:  python tools/make_season_codes.py 1617     (or several: 1617 1516 ...)
#     add  check  to only list the teams and conferences it finds, without writing anything
#
# It makes  "data/seasons/1617"  (one folder per Division I team, inside its conference that season) and
# "collect/1617"  (the roster scripts, with that season's year). The teams and their conferences come from Sports
# Reference's standings page for the season, so a school is in exactly when it was in Division I, and in the conference
# it was in then. Games, box scores and play-by-play come from the stats.ncaa.org files (tools/build_from_ncaa_stats.py);
# the only things still collected per season are the rosters:
#   1build.py        the team folders (this script already makes them)
#   5rosterfetch.py  each team's roster this season and last (height, class, minutes), from Sports Reference
#   7rostertrim.py   the roster minutes matched to the box scores

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
TEMPLATE = os.path.join(ROOT, "collect/_template")      # the scripts that are copied (made from the 2024-25 ones)
STANDINGS_URL = "https://www.sports-reference.com/cbb/seasons/men/{}-standings.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
DELAY_SECONDS = 4               # Sports Reference blocks anything faster than ~20 pages a minute

# season code -> (the year Sports Reference calls it, first game day, Selection Sunday). 2019-20 stops the day before
# the season was called off.
SEASONS = {
    "2324": (2024, (2023, 11, 6), (2024, 3, 17)),
    "2223": (2023, (2022, 11, 7), (2023, 3, 12)),
    "2122": (2022, (2021, 11, 9), (2022, 3, 13)),
    "2021": (2021, (2020, 11, 25), (2021, 3, 14)),
    "1920": (2020, (2019, 11, 5), (2020, 3, 11)),
    "1819": (2019, (2018, 11, 6), (2019, 3, 17)),
    "1718": (2018, (2017, 11, 10), (2018, 3, 11)),
    "1617": (2017, (2016, 11, 11), (2017, 3, 12)),
    "1516": (2016, (2015, 11, 13), (2016, 3, 13)),
    "1415": (2015, (2014, 11, 14), (2015, 3, 15)),
    "1314": (2014, (2013, 11, 8), (2014, 3, 16)),
    "1213": (2013, (2012, 11, 9), (2013, 3, 17)),
    "1112": (2012, (2011, 11, 7), (2012, 3, 11)),
    "1011": (2011, (2010, 11, 8), (2011, 3, 13)),
    "0910": (2010, (2009, 11, 9), (2010, 3, 14)),
}

# Sports Reference's conference table -> our conference folder
CONFERENCES = {
    "aac": "American", "acc": "ACC", "america-east": "America East", "atlantic-10": "Atlantic 10", "atlantic-sun": "ASUN",
    "big-12": "Big 12", "big-east": "Big East", "big-sky": "Big Sky", "big-south": "Big South", "big-ten": "Big Ten",
    "big-west": "Big West", "coastal": "CAA", "colonial": "CAA", "cusa": "CUSA", "horizon": "Horizon",
    "independent": "Independent", "ivy": "Ivy League", "maac": "MAAC", "mac": "MAC", "meac": "MEAC", "mvc": "MVC",
    "mwc": "Mountain West", "northeast": "NEC", "ovc": "OVC", "pac-12": "Pac-12", "pac-10": "Pac-10", "great-west": "Great West", "patriot": "Patriot", "sec": "SEC",
    "southern": "SoCon", "southland": "Southland", "summit": "Summit League", "sun-belt": "Sun Belt", "swac": "SWAC",
    "wac": "WAC", "wcc": "WCC",
}

# Schools that were in Division I then but are not in the 2024-25 or 2025-26 folders: Sports Reference's school id ->
# the name the NCAA's scoreboard uses (which is what the team folders are called)
OLD_SCHOOLS = {
    "hartford": "Hartford", "st-francis-ny": "St. Francis Brooklyn", "savannah-state": "Savannah St.",
    "centenary-la": "Centenary (LA)", "winston-salem": "Winston-Salem",
}
SCRIPTS = ["1build.py", "5rosterfetch.py", "7rostertrim.py"]

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def known_schools():
    """Sports Reference school id -> our team folder name, from the seasons already built."""
    names = dict(OLD_SCHOOLS)
    for folder in ("data/seasons/2425", "data/seasons/2526"):
        for team, slug in (read_json(os.path.join(ROOT, folder, "sr_schools.json")) or {}).items():
            names[slug] = team
        # folder names lose a trailing dot on Windows ("Alabama St." -> "Alabama St"); the scripts' own table keeps it
    spelled = {}
    for line in open(os.path.join(TEMPLATE, "1build.py"), encoding="utf-8").read().split('"""')[1].strip().splitlines():
        if "\t" in line:
            spelled[line.split("\t")[0].rstrip(". ")] = line.split("\t")[0]
    return {slug: spelled.get(team.rstrip(". "), team) for slug, team in names.items()}

def season_teams(code, year):
    """[(our team name, conference folder, Sports Reference school id)] for the season, and the schools with no name."""
    cache = os.path.join(ROOT, "collect/" + code, f"sr_standings_{year}.html")
    if os.path.exists(cache):
        page = open(cache, encoding="utf-8").read()
    else:
        response = requests.get(STANDINGS_URL.format(year), headers=HEADERS, timeout=30)
        time.sleep(DELAY_SECONDS)
        if response.status_code != 200:
            raise SystemExit(f"Sports Reference answered {response.status_code} for {year}; wait a while and try again.")
        response.encoding = "utf-8"
        page = response.text
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as out:
            out.write(page)
    page = page.replace("<!--", "").replace("-->", "")
    names = known_schools()
    teams, unknown, seen = [], [], set()
    for table_id, body in re.findall(r'<table[^>]*\bid="standings_([^"]+)"([\s\S]*?)</table>', page):
        conference = CONFERENCES.get(table_id)
        for slug, school in re.findall(r'/cbb/schools/([^/]+)/men/%d\.html["\'][^>]*>([^<]+)<' % year, body):
            if slug in seen: continue
            seen.add(slug)
            if slug in names and conference:
                teams.append((names[slug], conference, slug))
            else:
                unknown.append((slug, school, table_id))
    return teams, unknown

def adapt(name, text, code, year, first, last, teams):
    folder = "data/seasons/" + code
    label = f"{year - 1}-{year % 100:02d}"
    text = text.replace("data/seasons/2425", folder)
    text = text.replace("date(2024, 11, 4)", "date(%d, %d, %d)" % first).replace("date(2025, 3, 16)", "date(%d, %d, %d)" % last)
    text = text.replace("2025/03/16", "%d/%02d/%02d" % last).replace("2024/11/01", "%d/%02d/01" % first[:2])
    text = text.replace("2025 = the 2024-25 season", f"{year} = the {label} season")
    text = re.sub(r"^SEASON = 2025\b", f"SEASON = {year}", text, flags=re.M)
    text = text.replace("SEASONS = [2025, 2024]", f"SEASONS = [{year}, {year - 1}]")
    if name == "1build.py":
        head, _, tail = text.split('"""', 2)
        text = head + '"""\n' + "\n".join(f"{team}\t{conference}" for team, conference, _ in teams) + '\n"""' + tail
    return text

def main():
    check = "check" in sys.argv[1:]
    codes = [a for a in sys.argv[1:] if a in SEASONS]
    if not codes:
        print("Name the seasons to set up, e.g.  python tools/make_season_codes.py 2324 2223     Known: " + " ".join(SEASONS))
        return
    for code in codes:
        year, first, last = SEASONS[code]
        teams, unknown = season_teams(code, year)
        conferences = sorted({conference for _, conference, _ in teams})
        print(f"{year - 1}-{year % 100:02d}: {len(teams)} Division I teams in {len(conferences)} conferences")
        for slug, school, table in unknown:
            print(f"   NOT SET UP: {school} ({slug}, {table}) - add it to OLD_SCHOOLS" + ("" if table in CONFERENCES else " and its conference to CONFERENCES"))
        if check:
            continue
        codes_dir = os.path.join(ROOT, "collect/" + code)
        teams_dir = os.path.join(ROOT, "data/seasons/" + code)
        os.makedirs(codes_dir, exist_ok=True)
        for name in SCRIPTS:
            text = open(os.path.join(TEMPLATE, name), encoding="utf-8").read()
            with open(os.path.join(codes_dir, name), "w", encoding="utf-8", newline="") as out:
                out.write(adapt(name, text, code, year, first, last, teams))
        # the team folders (what 1build.py makes), and Sports Reference's id for each school, so nothing has to be looked up
        for team, conference, _ in teams:
            folder = os.path.join(teams_dir, conference, team)
            os.makedirs(folder, exist_ok=True)
            if not os.path.exists(os.path.join(folder, "games.json")):
                with open(os.path.join(folder, "games.json"), "w", encoding="utf-8") as out:
                    json.dump([], out, indent=2)
        with open(os.path.join(teams_dir, "sr_schools.json"), "w", encoding="utf-8") as out:
            json.dump({team.rstrip(". "): slug for team, _, slug in teams}, out, indent=1)
        print(f"   scripts in  collect/{code}   team folders in  data/seasons/{code}")

if __name__ == "__main__":
    main()
