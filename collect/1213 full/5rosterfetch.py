import os
import sys
import json
import html
import requests
import time
import re

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/1213 full"
ROSTER_FILE = "roster_{}.json"   # saved inside each team folder, e.g. data/seasons/2526/SEC/Alabama/roster_2026.json
SCHOOLS_FILE = os.path.join(BASE_DIR, "sr_schools.json")
SEASONS = [2013, 2012]          # 2013 = the 2012-13 season. The season before is needed for continuity and 5th-years.
DELAY_SECONDS = 4               # Sports Reference blocks anything faster than ~20 pages a minute. Do not lower this.
INDEX_URL = "https://www.sports-reference.com/cbb/seasons/men/{}-school-stats.html"
TEAM_URL = "https://www.sports-reference.com/cbb/schools/{}/men/{}.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

# Our folder name -> Sports Reference school name, for the ones that are spelled differently
NAME_FIXES = {
    "A&M-Corpus Christi": "TAMUCC", "Alcorn": "Alcorn State", "App State": "Appalachian State",
    "Ark.-Pine Bluff": "Arkansas-Pine Bluff", "Army West Point": "Army", "BYU": "Brigham Young",
    "Boston U": "Boston University", "CSU Bakersfield": "Cal State Bakersfield", "CSUN": "Cal State Northridge",
    "Central Ark": "Central Arkansas", "Central Conn. St": "Central Connecticut State", "Central Mich": "Central Michigan",
    "Charleston So": "Charleston Southern", "Col. of Charleston": "College of Charleston", "ETSU": "East Tennessee State",
    "Eastern Ill": "Eastern Illinois", "Eastern Ky": "Eastern Kentucky", "Eastern Mich": "Eastern Michigan",
    "Eastern Wash": "Eastern Washington", "FGCU": "Florida Gulf Coast", "FIU": "Florida International",
    "Fla. Atlantic": "Florida Atlantic", "Ga. Southern": "Georgia Southern", "LIU": "Long Island University",
    "LMU (CA)": "Loyola Marymount", "LSU": "Louisiana State", "LSU New Orleans": "New Orleans",
    "Lamar University": "Lamar", "Loyola Chicago": "Loyola (IL)", "Loyola Maryland": "Loyola (MD)",
    "Middle Tenn": "Middle Tennessee", "Mississippi Val": "Mississippi Valley State", "N.C. A&T": "North Carolina A&T",
    "N.C. Central": "North Carolina Central", "NIU": "Northern Illinois", "Nicholls": "Nicholls State",
    "North Ala": "North Alabama", "Northern Ariz": "Northern Arizona", "Northern Colo": "Northern Colorado",
    "Northern Ky": "Northern Kentucky", "Ole Miss": "Mississippi", "Penn": "Pennsylvania",
    "Prairie View": "Prairie View A&M", "SFA": "Stephen F. Austin", "SIUE": "SIU Edwardsville",
    "SMU": "Southern Methodist", "Saint Francis": "Saint Francis (PA)", "Saint Mary's (CA)": "Saint Mary's",
    "Seattle U": "Seattle", "South Fla": "South Florida", "Southeast Mo. St": "Southeast Missouri State",
    "Southeastern La": "Southeastern Louisiana", "Southern Ill": "Southern Illinois", "Southern Ind": "Southern Indiana",
    "Southern Miss": "Southern Mississippi", "Southern U": "Southern", "St. Thomas (MN)": "St. Thomas",
    "TCU": "Texas Christian", "UAlbany": "Albany (NY)", "UConn": "Connecticut", "UIC": "Illinois-Chicago",
    "UIW": "Incarnate Word", "ULM": "Louisiana-Monroe", "UMES": "Maryland-Eastern Shore",
    "UMass Lowell": "Massachusetts-Lowell", "UNCW": "UNC Wilmington", "UNI": "Northern Iowa",
    "UNLV": "Nevada-Las Vegas", "USC Upstate": "South Carolina Upstate", "UT Martin": "Tennessee-Martin",
    "UTRGV": "Texas-Rio Grande Valley", "VCU": "Virginia Commonwealth", "West Ga": "West Georgia",
    "Western Caro": "Western Carolina", "Western Ill": "Western Illinois", "Western Ky": "Western Kentucky",
    "Western Mich": "Western Michigan",
}

class Blocked(Exception):
    pass

def clean_string(s):
    """Lowercase, 'St' -> 'State', punctuation and dashes removed, for comparing school names."""
    s = s.lower().replace("&", "and")
    s = re.sub(r"\bst\b\.?", "state", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())

def fetch(url):
    """Download one page, then wait. Returns None if the page does not exist."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    time.sleep(DELAY_SECONDS)
    if response.status_code == 404:
        return None
    if response.status_code in (403, 429):
        raise Blocked(f"Sports Reference refused the request ({response.status_code}).")
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text

def get_team_folders():
    """Team name -> its folder."""
    teams = {}
    for conference in sorted(os.listdir(BASE_DIR)):
        conf_path = os.path.join(BASE_DIR, conference)
        if os.path.isdir(conf_path):
            for team in sorted(os.listdir(conf_path)):
                if os.path.isdir(os.path.join(conf_path, team)):
                    teams[team] = os.path.join(conf_path, team)
    return teams

def load_school_slugs(teams):
    """Our team name -> Sports Reference school id (e.g. 'Alabama' -> 'alabama'). Saved so it is only looked up once."""
    cache_path = SCHOOLS_FILE
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Looking up school names...")
    page = fetch(INDEX_URL.format(SEASONS[0]))
    found = re.findall(r'data-stat="school_name"[^>]*><a href=["\']/cbb/schools/([^/]+)/men/\d+\.html["\'][^>]*>([^<]+)</a>', page or "")
    by_name = {clean_string(html.unescape(name)): slug for slug, name in found}

    slugs = {}
    for team in teams:
        slug = by_name.get(clean_string(NAME_FIXES.get(team, team)))
        if slug:
            slugs[team] = slug
        else:
            print(f"  No Sports Reference match for '{team}' - add it to NAME_FIXES")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(slugs, f, indent=1)
    return slugs

def read_table(page, table_id):
    """Rows of one table as dicts of column -> text, plus the player id from the row's player link."""
    match = re.search(r'<table[^>]*\bid="' + re.escape(table_id) + r'"[\s\S]*?</table>', page)
    if not match:
        return []
    rows = []
    for row_html in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", match.group(0)):
        cells = re.findall(r'<(?:td|th)[^>]*data-stat="([^"]+)"[^>]*>([\s\S]*?)</(?:td|th)>', row_html)
        player = re.search(r'/cbb/players/([^"\'.]+)\.html', row_html)
        if cells and player:
            row = {stat: html.unescape(re.sub(r"<[^>]+>", "", text)).strip() for stat, text in cells}
            row["id"] = player.group(1)
            rows.append(row)
    return rows

def to_int(text):
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None

def height_inches(text):
    parts = re.findall(r"\d+", text or "")
    return int(parts[0]) * 12 + int(parts[1]) if len(parts) >= 2 else None

def parse_team_page(page):
    # Some tables are tucked inside HTML comments, so unwrap those first
    page = page.replace("<!--", "").replace("-->", "")
    totals = {row["id"]: row for row in read_table(page, "players_totals")}

    players = []
    for row in read_table(page, "roster"):
        season_line = totals.get(row["id"], {})
        players.append({
            "id": row["id"],
            "name": row.get("player", ""),
            "class": row.get("class", ""),
            "pos": row.get("pos", ""),
            "height": row.get("height", ""),
            "height_in": height_inches(row.get("height")),
            "weight": to_int(row.get("weight")),
            "games": to_int(season_line.get("games")) or 0,
            "minutes": to_int(season_line.get("mp")) or 0,
        })
    return players

def mark_fifth_years(team_folders):
    """A senior who was already listed as a senior last season is in a 5th year (works across transfers)."""
    last_class = {}
    for folder in team_folders.values():
        path = os.path.join(folder, ROSTER_FILE.format(SEASONS[1]))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for player in json.load(f)["players"]:
                    last_class[player["id"]] = player["class"]

    count = 0
    for folder in team_folders.values():
        path = os.path.join(folder, ROSTER_FILE.format(SEASONS[0]))
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            roster = json.load(f)
        for player in roster["players"]:
            player["last_season_class"] = last_class.get(player["id"])
            player["fifth_year"] = player["class"] == "SR" and last_class.get(player["id"]) == "SR"
            count += player["fifth_year"]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(roster, f, indent=1)
    return count

def main():
    team_folders = get_team_folders()
    teams = list(team_folders)
    slugs = load_school_slugs(teams)

    # Optional: name some teams to fetch only those, e.g.  python "collect\5rosterfetch.py" Alabama Duke
    wanted = [w.lower() for w in sys.argv[1:]]
    if wanted:
        teams = [t for t in teams if t.lower() in wanted]

    todo = []
    for season in SEASONS:
        for team in teams:
            dest = os.path.join(team_folders[team], ROSTER_FILE.format(season))
            if team in slugs and not os.path.exists(dest):
                todo.append((season, team, dest))

    print(f"{len(todo)} pages to fetch (about {len(todo) * (DELAY_SECONDS + 1) // 60 + 1} minutes). Already-saved pages are skipped.")
    try:
        for i, (season, team, dest) in enumerate(todo, 1):
            try:
                page = fetch(TEAM_URL.format(slugs[team], season))
            except Blocked:
                raise
            except Exception as e:
                print(f"[{i}/{len(todo)}] {season} {team}: failed ({e}) - will retry next run")
                continue

            # A missing page (school was not in D-I that season) is saved as an empty roster so it is not asked for again
            players = parse_team_page(page) if page else []
            with open(dest, "w", encoding="utf-8") as f:
                json.dump({"team": team, "school": slugs[team], "season": season, "players": players}, f, indent=1)
            print(f"[{i}/{len(todo)}] {season} {team}: {len(players)} players" + ("" if page else " (no page for this season)"))
    except Blocked as e:
        print(f"\n{e}\nStopping. Wait a few hours before running this again; everything fetched so far is saved.")
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    print(f"5th-year seniors marked: {mark_fifth_years(team_folders)}")

if __name__ == "__main__":
    main()
