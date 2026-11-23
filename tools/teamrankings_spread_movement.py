import os
import re
import csv
import json
import time
import html as htmllib
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from tournament_spreads import name_match

# Point-spread line movement for every NCAA tournament game, 2010-2026, from TeamRankings' matchup pages:
#     python tools/teamrankings_spread_movement.py          (resumes; games already saved are skipped)
# A game's page is /ncaa-basketball/matchup/<mascot>-<mascot>-<date>/spread-movement. Each page draws two charts (the
# line from each team's side) whose points are written in the page itself, lists the day's other games with their page
# addresses, and links both teams' pages (/ncaa-basketball/team/<school>-<mascot>), which tells us each team's mascot.
# So the first game of each tournament day is found from mascots already learned (both orders tried), and that page's
# day list gives every other game that day. Our games come from reports/tournament_spreads.csv, whose BetIQ names are
# TeamRankings' own names. TeamRankings' robots.txt allows these pages with a 10-second crawl delay, which is kept.
# Writes data/teamrankings/spread_movement/<game_id>.json (both charts' points, open/high/low/last, the three-book
# history table) and reports/tournament_spread_movement.csv (one row per chart point per team).

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "teamrankings", "spread_movement")
REPORTS = os.path.join(ROOT, "reports")
BASE = "https://www.teamrankings.com"
UA = "Strongside college basketball research (personal project; 1 request per 10 s, per robots.txt)"
DELAY = 10.0
# the first tournament days have no earlier games to learn mascots from: one known page each to start from
SEED_SLUGS = {"2010-03-16": ["eagles-golden-lions", "golden-lions-eagles"],
              "2010-03-18": ["monarchs-fighting-irish"],
              "2010-03-19": ["golden-lions-blue-devils", "blue-devils-golden-lions"],
              # First Four days whose teams had no mascot learned yet (both orders tried)
              "2011-03-15": ["bulldogs-trojans", "trojans-bulldogs", "tigers-blazers", "blazers-tigers"],
              "2011-03-16": ["roadrunners-hornets", "hornets-roadrunners", "trojans-rams", "rams-trojans"],
              "2012-03-13": ["hilltoppers-delta-devils", "delta-devils-hilltoppers", "cougars-gaels", "gaels-cougars"],
              "2012-03-14": ["catamounts-cardinals", "cardinals-catamounts", "golden-bears-bulls", "bulls-golden-bears"],
              "2013-03-19": ["aggies-flames", "flames-aggies", "gaels-blue-raiders", "blue-raiders-gaels"],
              "2013-03-20": ["dukes-blackbirds", "blackbirds-dukes", "explorers-broncos", "broncos-explorers"],
              "2014-03-19": ["mustangs-tigers", "tigers-mustangs", "volunteers-hawkeyes", "hawkeyes-volunteers"],
              "2015-03-18": ["pirates-jaspers", "jaspers-pirates", "flyers-broncos", "broncos-flyers"]}

_last = [0.0]
def get(path):
    """One page, at most one request per DELAY seconds; None if TeamRankings has no such page."""
    wait = _last[0] + DELAY - time.time()
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    try:
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise
    # a matchup address with the teams in the wrong order lands on the daily schedule instead of an error page
    return page if "graph-container-fav" in page else None

def text(s):
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()

def parse(page, date):
    """Everything we keep from one spread-movement page."""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    teams = [t.strip() for t in re.split(r"\s+(?:vs\.|@)\s+", text(h1.group(1)).split(":")[0])] if h1 else []
    odds = re.search(r"Odds:\s*([^<]*?),\s*Total Points:\s*([^<]*?)<", page)
    # the page names its favorite in full ("Kansas State by 15"); the h1 uses short names ("Kansas St")
    fav_full = htmllib.unescape(odds.group(1)).split(" by ")[0].strip() if odds and " by " in odds.group(1) else None
    fav_name = max(teams, key=lambda t: name_match(t, fav_full)) if fav_full and len(teams) == 2 else None
    charts = {}
    for side in ("fav", "dog"):
        m = re.search(r"renderTo: 'graph-container-" + side + r"'.*?yAxis: \{\s*title: \{\s*text: '([^']*)'.*?data: (\[.*?\])\s*,\s*color", page, re.S)
        if m:
            pts = json.loads(m.group(2))
            name = htmllib.unescape(m.group(1)).strip()
            guess = False
            if not name and fav_name:
                # older pages leave the charts' titles blank and the order varies: the chart that closes below zero
                # (the last point that isn't a pick'em) is the favorite's
                last = next((v for _, v in reversed(pts) if v != 0), 0)
                other = next(t for t in teams if t != fav_name)
                name = fav_name if last < 0 else other if last > 0 else (fav_name if side == "fav" else other)
                guess = last == 0
            charts[side] = {"team": name, "label_guess": guess,
                            "points": [[datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), v] for t, v in pts]}
    summary = {}
    for lab in ("Open", "High", "Last", "Low"):               # the favorite's side (the first of the two tables)
        m = re.search(r"<strong>" + lab + r"</strong></td>\s*<td[^>]*>(.*?)</td>", page, re.S)
        if m: summary[lab.lower()] = text(m.group(1))
    history = []
    hist = re.search(r"Spread History(.*?)(?:<h2|<footer|</main)", page, re.S)
    if hist:
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", hist.group(1), re.S):
            cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if cells and any(cells): history.append(cells)
    team_slugs = [s for s in dict.fromkeys(re.findall(r'href="/ncaa-basketball/team/([a-z0-9-]+)"', page))]
    day = []
    for href, label in re.findall(r'href="(/ncaa-basketball/matchup/[a-z0-9-]+-' + date + r')"[^>]*>(.*?)</a>', page, re.S):
        label = text(label)
        if " vs. " in label or " @ " in label:
            a, b = re.split(r"\s+(?:vs\.|@)\s+", label.split(",")[0], maxsplit=1)
            day.append({"a": a.strip(), "b": b.strip(), "path": href})
    return {"teams": teams, "charts": charts, "odds": htmllib.unescape(odds.group(1)).strip() if odds else None,
            "total": odds.group(2).strip() if odds else None, "summary": summary, "history": history,
            "team_slugs": team_slugs, "day": list({d["path"]: d for d in day}.values())}

def learn(mascots, slug, teams, team_slugs):
    """Each team's mascot from the page's matchup slug and the two team-page slugs (school-mascot)."""
    if len(teams) != 2 or len(team_slugs) < 2: return
    parts = slug.split("-")
    for i in range(1, len(parts)):
        left, right = "-".join(parts[:i]), "-".join(parts[i:])
        for sa, sb in ((team_slugs[0], team_slugs[1]), (team_slugs[1], team_slugs[0])):
            if (sa == left or sa.endswith("-" + left)) and (sb == right or sb.endswith("-" + right)):
                mascots[teams[0]], mascots[teams[1]] = left, right
                return

def best(name, pool, floor=1.1):
    """The pool name most like ours (exact first)."""
    if name in pool: return name
    scored = max(((name_match(name, p), p) for p in pool), default=(0, None))
    return scored[1] if scored[0] >= floor else None

def main():
    os.makedirs(OUT, exist_ok=True)
    state_path = os.path.join(OUT, "_state.json")
    state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {"mascots": {}, "days": {}, "missing": {}}
    mascots, days = state["mascots"], state["days"]
    save = lambda: json.dump(state, open(state_path, "w", encoding="utf-8"), indent=1)
    games = list(csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8")))
    by_date = {}
    for g in games: by_date.setdefault(g["date"].replace("/", "-"), []).append(g)
    for date in sorted(by_date):
        todo = [g for g in by_date[date] if not os.path.exists(os.path.join(OUT, g["game_id"] + ".json"))]
        if not todo:
            state["missing"].pop(date, None)             # a day once marked as having no starting page, now done
            continue
        pages = {}                                                       # path -> parsed page fetched this run
        if date not in days:
            # find one page for the day: a seed, or a game whose two mascots we already know
            tries = [s for s in SEED_SLUGS.get(date, [])]
            for g in todo:
                fa, fb = best(g["betiq_favorite"], mascots), best(g["betiq_underdog"], mascots)
                if fa and fb: tries += [f"{mascots[fa]}-{mascots[fb]}", f"{mascots[fb]}-{mascots[fa]}"]
            for slug in dict.fromkeys(tries):
                path = f"/ncaa-basketball/matchup/{slug}-{date}"
                page = get(path + "/spread-movement")
                if page:
                    p = parse(page, date); learn(mascots, f"{slug}", p["teams"], p["team_slugs"])
                    if len(p["teams"]) != 2: continue
                    pages[path] = p; days[date] = p["day"] or [{"a": p["teams"][0], "b": p["teams"][1], "path": path}]
                    break
            if date not in days:
                print(f"{date}: no starting page found ({len(todo)} games) - add one to SEED_SLUGS", flush=True)
                state["missing"][date] = "no starting page"; save(); continue
        for g in todo:
            fav, dog = g["betiq_favorite"], g["betiq_underdog"]
            scored = max(((max(name_match(fav, d["a"]) + name_match(dog, d["b"]), name_match(fav, d["b"]) + name_match(dog, d["a"])), d)
                          for d in days[date]), key=lambda x: x[0], default=(0, None))
            if scored[0] < 2.2:
                # not in the day list (some pages list only part of the day): build the address from the two mascots
                fa, fb = best(fav, mascots), best(dog, mascots)
                d = None
                if fa and fb:
                    # TeamRankings files some late games under the next day (2017's Sweet 16): try the day either side too
                    day = datetime.strptime(date, "%Y-%m-%d")
                    near = [date] + [(day + timedelta(days=s)).strftime("%Y-%m-%d") for s in (1, -1)]
                    for slug, dd in [(s, n) for n in near for s in dict.fromkeys([f"{mascots[fa]}-{mascots[fb]}", f"{mascots[fb]}-{mascots[fa]}"])]:
                        path = f"/ncaa-basketball/matchup/{slug}-{dd}"
                        page = get(path + "/spread-movement")
                        if page:
                            p = parse(page, dd)
                            if len(p["teams"]) == 2 and name_match(fav, p["teams"][0]) + name_match(dog, p["teams"][1]) >= 2.2 or \
                               len(p["teams"]) == 2 and name_match(fav, p["teams"][1]) + name_match(dog, p["teams"][0]) >= 2.2:
                                pages[path] = p; d = {"a": p["teams"][0], "b": p["teams"][1], "path": path}; break
                if d is None:
                    print(f"{date} {fav} v {dog}: not in TeamRankings' day list", flush=True)
                    state["missing"][g["game_id"]] = f"{date} {fav} v {dog}"; continue
            else:
                d = scored[1]
            p = pages.get(d["path"])
            if p is None:
                page = get(d["path"] + "/spread-movement")
                if not page:
                    state["missing"][g["game_id"]] = f"{date} {fav} v {dog}: page missing"; continue
                p = parse(page, date)
                learn(mascots, d["path"].rsplit("/", 1)[1][:-len(date) - 1], p["teams"], p["team_slugs"])
                pages[d["path"]] = p
            # the page's line from our favorite's side should match BetIQ's closing spread
            fav_chart = next((c for c in p["charts"].values() if name_match(fav, c["team"]) >= 1.1), None)
            last = fav_chart["points"][-1][1] if fav_chart and fav_chart["points"] else None
            rec = {"game_id": g["game_id"], "date": date, "round": g["round"], "season": g["season"], "favorite": fav, "underdog": dog,
                   "betiq_spread": float(g["spread"]), "page": BASE + d["path"] + "/spread-movement", "last_point_fav": last, **p}
            rec.pop("day"); rec.pop("team_slugs")
            json.dump(rec, open(os.path.join(OUT, g["game_id"] + ".json"), "w", encoding="utf-8"), indent=1)
            state["missing"].pop(g["game_id"], None)
            n = sum(len(c["points"]) for c in p["charts"].values())
            print(f"{date} {g['round']:12} {fav} v {dog}: {n} points, last {last} (BetIQ {g['spread']})", flush=True)
        save()
    write_csv()
    print(f"missing: {len(state['missing'])}", state["missing"] if state["missing"] else "")

def write_csv():
    rows = []
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".json") or f.startswith("_"): continue
        r = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
        for side, c in r["charts"].items():
            opp = next((o["team"] for s, o in r["charts"].items() if s != side), "")
            for i, (t, v) in enumerate(c["points"]):
                rows.append([r["season"], r["date"], r["round"], r["game_id"], c["team"], opp, i + 1, t, v])
    rows.sort(key=lambda x: (x[1], x[3], x[4], x[6]))
    with open(os.path.join(REPORTS, "tournament_spread_movement.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["season", "date", "round", "game_id", "team", "opponent", "point", "time_utc", "line"])
        w.writerows(rows)
    print(f"{len(rows)} chart points -> reports/tournament_spread_movement.csv")

if __name__ == "__main__":
    main()
