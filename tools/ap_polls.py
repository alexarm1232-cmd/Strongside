import os
import re
import sys
import json
import time
import requests
from datetime import date, timedelta

# The AP poll for each season, from Sports Reference's season poll page, for the Champion picker:
#     python tools/ap_polls.py               every season that is built
#     python tools/ap_polls.py 2526 2425     only these
# Writes data/seasons/<code>/ap_polls.json (and the same in the full-season folder): each ranked team's place in
#   pre    the preseason poll
#   w6     the week 6 poll, counted the AP's way (the preseason poll is week 1)
#   last   the last poll released before the NCAA tournament (through 2023 that is the AP's "Final" poll, released the
#          day after Selection Sunday; since 2024 the AP also has a poll after the tournament, which is not used)
# Teams are matched through their Sports Reference school id (sr_schools.json in each season's folder).

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SEASONS_DIR = os.path.join(ROOT, "data", "seasons")
CACHE = os.path.join(ROOT, "data", "ap_polls")
URL = "https://www.sports-reference.com/cbb/seasons/men/{}-polls.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ncaa_stats_season import SEASONS as SELECTION        # code -> (label, Selection Sunday)

def page(year):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{year}.html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    response = requests.get(URL.format(year), headers=HEADERS, timeout=40)
    time.sleep(4)                       # Sports Reference blocks anything faster than ~20 pages a minute
    if response.status_code != 200:
        raise SystemExit(f"Sports Reference answered {response.status_code} for {year}; wait a while and try again.")
    with open(path, "w", encoding="utf-8") as out:
        out.write(response.text)
    return response.text

def polls(code):
    year = 2000 + int(code[2:])
    sunday = SELECTION[code][1]
    html = page(year).replace("<!--", "").replace("-->", "")
    at = html.find('id="ap-polls"')
    if at < 0:
        return None, None
    table = html[at:html.find("</table>", at)]
    # each week column: its data-stat ("week6") and its label ("Pre", "12/8", "Final")
    labels = dict(re.findall(r'data-stat="(week\d+)"[^>]*>([^<]+)</th>', table))
    def day(label):
        m = re.match(r"^(\d{1,2})/(\d{1,2})$", label.strip())
        if not m: return None
        month, d = int(m.group(1)), int(m.group(2))
        return date(year - 1 if month >= 9 else year, month, d)
    # The last poll before the tournament. Through 2023 the AP's "Final" poll came out the day after Selection Sunday,
    # before the tournament; since 2024 a dated poll comes out then and "Final"/"Post" follows the tournament.
    dated = [w for w, label in labels.items() if day(label) and day(label) <= sunday + timedelta(days=3)]
    latest = max(dated, key=lambda w: int(w[4:])) if dated else None
    final = next((w for w, label in labels.items() if label.strip() == "Final"), None)
    last = latest if latest and day(labels[latest]) >= sunday - timedelta(days=1) else (final or latest)
    weeks = {"pre": "week1", "w6": "week6" if "week6" in labels else None, "last": last}
    teams = {}
    for row in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", table):
        slug = re.search(r"/cbb/schools/([^/]+)/men/", row)
        if not slug: continue
        cells = dict(re.findall(r'data-stat="(week\d+)"[^>]*>(?:<strong>)?(\d*)', row))
        teams[slug.group(1)] = {key: int(cells[w]) for key, w in weeks.items() if w and cells.get(w)}
    return teams, {key: labels.get(w) for key, w in weeks.items()}

def main():
    codes = [a for a in sys.argv[1:] if a.isdigit()] or sorted(c for c in os.listdir(SEASONS_DIR) if c.isdigit() and c in SELECTION)
    for code in codes:
        schools = json.load(open(os.path.join(SEASONS_DIR, code, "sr_schools.json"), encoding="utf-8"))
        team_of = {slug: team for team, slug in schools.items()}
        ranks, weeks = polls(code)
        if ranks is None:
            print(f"{code}: no AP poll table found")
            continue
        out = {"source": "Sports Reference season poll page (AP)", "weeks": weeks,
               "teams": {team_of[s]: r for s, r in ranks.items() if s in team_of and r}}
        unmatched = [s for s, r in ranks.items() if s not in team_of and r]
        for folder in (code, code + " full"):
            if os.path.isdir(os.path.join(SEASONS_DIR, folder)):
                with open(os.path.join(SEASONS_DIR, folder, "ap_polls.json"), "w", encoding="utf-8") as f:
                    json.dump(out, f, indent=1)
        top = sorted(((r.get("pre", 99), t) for t, r in out["teams"].items()))[:3]
        print(f"{code}: weeks {weeks} | {len(out['teams'])} ranked teams | preseason top 3 {[t for _, t in top]}"
              + (f" | not matched: {unmatched}" if unmatched else ""))

if __name__ == "__main__":
    main()
