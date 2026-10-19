import os
import re
import sys
import json
import time
import html
import requests

# Teams that moved up to Division I have no "last season" roster on Sports Reference (it only covers Division I), so
# their continuity and experience would start from nothing. This fills in that season from the school's own athletics
# site (the season stats page for games and minutes, the roster page for class, position and height):
#     python tools/transition_rosters.py            every team below
#     python tools/transition_rosters.py 2223       only that season's
# Writes roster_<year>.json, in the same layout as the Sports Reference ones, into the team's folder in both the
# pre-tournament and the full-season data. Most athletics sites run on Sidearm, whose pages this reads.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

# season code of the first Division I season -> [(team folder, the athletics site, its level the year before)]
TRANSITIONS = {
    "1314": [("UMass Lowell", "https://goriverhawks.com", "Division II"), ("Abilene Christian", "https://acusports.com", "Division II"),
             ("UIW", "https://uiwcardinals.com", "Division II"), ("Grand Canyon", "https://gculopes.com", "Division II")],
    "1819": [("North Ala", "https://roarlions.com", "Division II"), ("California Baptist", "https://cbulancers.com", "Division II")],
    "1920": [("Merrimack", "https://merrimackathletics.com", "Division II")],
    "2021": [("Bellarmine", "https://athletics.bellarmine.edu", "Division II"), ("UC San Diego", "https://ucsdtritons.com", "Division II"),
             ("Tarleton St", "https://tarletonsports.com", "Division II"), ("Utah Tech", "https://utahtechtrailblazers.com", "Division II")],
    "2122": [("St. Thomas (MN)", "https://tommiesports.com", "Division III")],
    "2223": [("Queens (NC)", "https://queensathletics.com", "Division II"), ("Stonehill", "https://stonehillskyhawks.com", "Division II"),
             ("Lindenwood", "https://lindenwoodlions.com", "Division II"), ("Southern Ind", "https://gousieagles.com", "Division II"),
             ("East Texas A&M", "https://lionathletics.com", "Division II")],
}

def fetch(url):
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=40)
            time.sleep(1.5)
            if response.status_code == 200 and len(response.text) > 5000:
                return response.text
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    return None

def text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment or "")).split() and " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split()) or ""

def first_last(name):
    last, comma, first = name.partition(",")
    return f"{first.strip()} {last.strip()}".strip() if comma else name.strip()

def season_stats_newer(page):
    """The same from Sidearm's newer pages: the first table whose header has GP and MIN, read by column position."""
    for table in re.findall(r"<table[\s\S]*?</table>", page):
        head = [text(h) for h in re.findall(r"<th[^>]*>([\s\S]*?)</th>", table)]
        if "GP" not in head or "MIN" not in head:
            continue
        # the header has a top row of groups (MINUTES, SCORING...) before the real column names
        cols = head[len(head) - head[::-1].index("#") - 1:] if "#" in head else head
        try:
            gp, gs, mins = cols.index("GP"), cols.index("GS"), cols.index("MIN")
        except ValueError:
            continue
        out = []
        for row in re.findall(r"<tr[^>]*s-table-body__row[^>]*>([\s\S]*?)</tr>", table):
            cells = [text(c) for c in re.findall(r"<td[^>]*>([\s\S]*?)</td>", row)]
            if len(cells) <= mins or "," not in cells[1]:
                continue
            number = lambda v: int(float(v)) if re.match(r"^[\d.]+$", v or "") else 0
            out.append((first_last(cells[1]), number(cells[gp]), number(cells[gs]), number(cells[mins])))
        if out:
            return out
    return []

def season_stats(page):
    """[(name, games, starts, minutes)] from the 'Overall Individual Statistics' table."""
    at = page.find("Overall Individual Statistics")
    if at < 0:
        return season_stats_newer(page)
    table = page[at:page.find("</table>", at)]
    out = []
    for row in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", table.split("<tbody", 1)[-1]):
        name = re.search(r"<a[^>]*>([^<]+)</a>", row) or re.search(r'class="text-no-wrap"[^>]*>([\s\S]*?)</td>', row)
        cells = dict(re.findall(r'data-label="([^"]+)"[^>]*>([\s\S]*?)</td>', row))
        if not name or "MIN" not in cells:
            continue
        name = first_last(text(name.group(1)))
        if name.lower() in ("team", "total", "totals", "opponents"):
            continue
        number = lambda key: int(float(text(cells.get(key, "0")) or 0)) if re.match(r"^[\d.]+$", text(cells.get(key, "0")) or "0") else 0
        out.append((name, number("GP"), number("GS"), number("MIN")))
    return out

def roster_details(page, label=None):
    """name -> {class, pos, height, weight} from the roster page. With a season label, a page that is not that season's
    roster (some sites show the current one for any season) gives nothing, so no player gets the wrong year's class."""
    if label and page:
        title = (re.search(r"<title>([\s\S]*?)</title>", page) or [None, ""])[1]
        heading = " ".join(re.findall(r"<h1[^>]*>([\s\S]*?)</h1>", page)[:2])
        if label not in text(title) + " " + text(heading):
            return {}
    details = {}
    # Sidearm's newer pages: one card per player
    for block in re.split(r'class="s-person-card', page or "")[1:]:
        name = re.search(r"<h3[^>]*>([^<]+)</h3>", block)
        if not name:
            continue
        item = lambda label_text: text((re.search(r'<span class="sr-only">%s</span>([\s\S]*?)</span>' % label_text, block) or [None, ""])[1])
        details.setdefault(text(name.group(1)), {"class": item("Academic Year"), "pos": item("Position"),
                                                 "height": item("Height").replace("''", '"'), "weight": item("Weight")})
    for block in re.split(r'<li class="sidearm-roster-player', page or "")[1:]:
        name = re.search(r'sidearm-roster-player-name[\s\S]*?<a[^>]*>([^<]+)</a>', block)
        if not name:
            continue
        field = lambda cls: text((re.search(r'class="%s[^"]*"[^>]*>([\s\S]*?)</span>' % cls, block) or [None, ""])[1])
        details[text(name.group(1))] = {"class": field("sidearm-roster-player-academic-year"), "pos": field("sidearm-roster-player-position"),
                                        "height": field("sidearm-roster-player-height"), "weight": field("sidearm-roster-player-weight")}
    return details

def norm(name):
    return re.sub(r"[^a-z]", "", name.lower())

def year_class(text_class):
    t = text_class.lower().replace(".", "").replace("-", " ")
    for key, value in (("gr", "GR"), ("fr", "FR"), ("so", "SO"), ("jr", "JR"), ("sr", "SR"), ("first", "FR"), ("second", "SO"),
                       ("third", "JR"), ("fourth", "SR"), ("fifth", "GR")):
        if key in t.split() or t.startswith(key) or (" " + key) in t:
            return value
    return ""

def inches(height):
    m = re.match(r"^\s*(\d)\s*[-' ]\s*(\d{1,2})", height or "")
    return int(m.group(1)) * 12 + int(m.group(2)) if m else None

def team_folders(code, team):
    found = []
    for base in (os.path.join(ROOT, "data", "seasons", code), os.path.join(ROOT, "data", "seasons", code + " full")):
        if not os.path.isdir(base): continue
        for conf in os.listdir(base):
            path = os.path.join(base, conf, team)
            if os.path.isdir(path):
                found.append(path)
    return found

def main():
    wanted = [a for a in sys.argv[1:] if a in TRANSITIONS] or list(TRANSITIONS)
    for code in wanted:
        year = 2000 + int(code[2:]) - 1                      # the season before the first Division I one
        label = f"{year - 1}-{year % 100:02d}"
        for team, site, level in TRANSITIONS[code]:
            stats_page = fetch(f"{site}/sports/mens-basketball/stats/{label}")
            stats = season_stats(stats_page or "")
            if not stats:
                print(f"{code} {team}: no {label} season stats found at {site} - needs a look")
                continue
            # a season page with only a handful of games on it (Abilene Christian's 2012-13 has three) is not a season
            if sum(s[3] for s in stats) < 2000:
                print(f"{code} {team}: {label} at {site} has only {sum(s[3] for s in stats)} minutes (a few games) - not used")
                continue
            details = roster_details(fetch(f"{site}/sports/mens-basketball/roster/{label}") or "", label)
            by_norm = {norm(n): d for n, d in details.items()}
            players = []
            for name, games, starts, minutes in sorted(stats, key=lambda s: -s[3]):
                d = by_norm.get(norm(name), {})
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                players.append({"id": f"{slug}-tr", "name": name, "class": year_class(d.get("class", "")), "pos": (d.get("pos") or "")[:1].upper(),
                                "height": d.get("height", ""), "height_in": inches(d.get("height")),
                                "weight": int(re.sub(r"\D", "", d["weight"])) if d.get("weight") and re.search(r"\d", d["weight"]) else None,
                                "games": games, "minutes": minutes})
            roster = {"team": team.rstrip(". "), "school": re.sub(r"[^a-z0-9]+", "-", team.lower()).strip("-"), "season": year,
                      "source": f"{site.split('//')[1]} ({level} season, not on Sports Reference)", "players": players}
            folders = team_folders(code, team)
            for folder in folders:
                with open(os.path.join(folder, f"roster_{year}.json"), "w", encoding="utf-8") as out:
                    json.dump(roster, out, indent=1)
            with_class = sum(1 for p in players if p["class"])
            print(f"{code} {team}: {label} from {site} - {len(players)} players, {sum(p['minutes'] for p in players)} minutes, "
                  f"{with_class} with a class | written to {len(folders)} folders")

if __name__ == "__main__":
    main()
