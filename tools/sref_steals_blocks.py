import os
import re
import csv
import time
import json
import urllib.request

# Season steal and block totals for 2009-10 and 2010-11 (our box scores carry none for those two seasons):
#     python tools/sref_steals_blocks.py
# From Sports Reference's season-wide school pages (allowed by its robots.txt), four pages in all:
#     /cbb/seasons/men/<year>-school-stats.html     each school's own totals (G, STL, BLK, ...)
#     /cbb/seasons/men/<year>-opponent-stats.html   its opponents' totals against it
# These are full-season totals (tournament and non-D-I games included), not just our regular-season D-I games.
# Saves the raw pages in data/sports_reference/ and writes data/sports_reference/steals_blocks.csv.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sports_reference")
UA = "Strongside college basketball research (personal project; a handful of requests)"
BASE = "https://www.sports-reference.com/cbb/seasons/men/"

def page(name):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    html = urllib.request.urlopen(urllib.request.Request(BASE + name, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8", "replace")
    open(path, "w", encoding="utf-8").write(html)
    time.sleep(6)
    return html

def rows(html):
    """school -> {stat: value} from the page's main table (it may sit inside an HTML comment)"""
    html = html.replace("<!--", "").replace("-->", "")
    out = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        name = re.search(r'data-stat="school_name"[^>]*>(?:<a[^>]*>)?([^<]+)', tr)
        if not name: continue
        cells = dict(re.findall(r'data-stat="([a-z_0-9]+)"[^>]*>([^<]*)<', tr))
        if not cells.get("g", "").strip().isdigit(): continue          # the table repeats its header rows
        out[name.group(1).replace("&amp;", "&").replace("&nbsp;", "").replace("NCAA", "").strip()] = cells
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    result = []
    for year, season in ((2010, "2009-10"), (2011, "2010-11")):
        own = rows(page(f"{year}-school-stats.html"))
        opp = rows(page(f"{year}-opponent-stats.html"))
        for school, c in own.items():
            o = opp.get(school, {})
            num = lambda d, k: float(d[k]) if d.get(k, "").strip() not in ("", None) else None
            result.append({"season": season, "school": school, "games": num(c, "g"), "stl": num(c, "stl"), "blk": num(c, "blk"),
                           "opp_stl": num(o, "opp_stl"), "opp_blk": num(o, "opp_blk"), "tov": num(c, "tov"), "opp_tov": num(o, "opp_tov"),
                           "fga": num(c, "fga"), "fg3a": num(c, "fg3a"), "opp_fga": num(o, "opp_fga"), "opp_fg3a": num(o, "opp_fg3a")})
        print(season, len(own), "schools,", len(opp), "with opponent totals")
    with open(os.path.join(OUT, "steals_blocks.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0])); w.writeheader(); w.writerows(result)
    print(len(result), "rows -> data/sports_reference/steals_blocks.csv")

if __name__ == "__main__":
    main()
