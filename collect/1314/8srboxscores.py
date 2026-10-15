import os
import sys
import json
import html
import shutil
import requests
import time
import re
from datetime import date

# ---------------------------
# SETTINGS
# ---------------------------
BASE_DIR = "data/seasons/1314"
SEASON = 2014                   # 2014 = the 2013-14 season
LAST_DATE = "2014/03/16"        # games after this are left out
SCHOOLS_FILE = os.path.join(BASE_DIR, "sr_schools.json")   # made by 5rosterfetch.py
SCHEDULE_FILE = "sr_schedule_{}.json"   # saved inside each team folder so the schedule page is only fetched once
BACKUP_FOLDER = "boxscores_ncaa"        # the NCAA version of each box score is moved here before it is replaced
DELAY_SECONDS = 4               # Sports Reference blocks anything faster than ~20 pages a minute. Do not lower this.
SCHEDULE_URL = "https://www.sports-reference.com/cbb/schools/{}/men/{}-schedule.html"
SITE = "https://www.sports-reference.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
SOURCE = "sports-reference"

# The NCAA box scores leave players out of some games (the player lines don't add up to the team line).
# This replaces the PLAYER lines in every box score with the ones from Sports Reference, game by game.
# The team totals line is kept from the NCAA file: it is complete, and it counts team rebounds, which
# Sports Reference's totals do not. Files keep their NCAA game id so the play-by-play still lines up.

class Blocked(Exception):
    pass

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
    # Some tables are tucked inside HTML comments, so unwrap those
    return response.text.replace("<!--", "").replace("-->", "")

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

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def table_rows(page, table_id):
    """Rows of one table as dicts of column -> text ('_html' holds the row's raw HTML)."""
    match = re.search(r'<table[^>]*\bid="' + re.escape(table_id) + r'"[\s\S]*?</table>', page)
    rows = []
    for row_html in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", match.group(0) if match else ""):
        cells = re.findall(r'<(?:td|th)[^>]*data-stat="([^"]+)"[^>]*>([\s\S]*?)</(?:td|th)>', row_html)
        if cells:
            row = {stat: html.unescape(re.sub(r"<[^>]+>", "", text)).strip() for stat, text in cells}
            row["_html"] = row_html
            rows.append(row)
    return rows

def to_int(text):
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return 0

# ---------------------------
# SCHEDULE (which Sports Reference page is which NCAA game)
# ---------------------------
def load_schedule(team, team_path, slug):
    """This team's games on Sports Reference: date, box score link, both scores."""
    cache_path = os.path.join(team_path, SCHEDULE_FILE.format(SEASON))
    saved = read_json(cache_path)
    if saved is not None and all("site" in g for g in saved):   # older saved schedules have no game site
        return saved

    page = fetch(SCHEDULE_URL.format(slug, SEASON))
    games = []
    for row in table_rows(page or "", "schedule"):
        link = re.search(r'href="(/cbb/boxscores/(\d{4})-(\d{2})-(\d{2})[^"]*)"', row["_html"])
        if not link: continue
        games.append({
            "date": f"{link.group(2)}/{link.group(3)}/{link.group(4)}",
            "url": link.group(1),
            "opponent": row.get("opp_name", ""),
            "pts": to_int(row.get("pts")),
            "opp_pts": to_int(row.get("opp_pts")),
            # where it was played: "N" neutral floor, "@" away, "" home
            "site": row.get("game_location", ""),
            "arena": row.get("arena", ""),
        })
    if page:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(games, f, indent=1)
    return games

def days_apart(a, b):
    return abs((date(*map(int, a.split("/"))) - date(*map(int, b.split("/")))).days)

def match_games(schedule, team_path):
    """NCAA game id -> Sports Reference box score link, matched on the date and the two scores."""
    ncaa_games = read_json(os.path.join(team_path, "game_scores.json"), [])
    listed = {str(g).strip() for g in read_json(os.path.join(team_path, "games.json"), [])}
    matched, unmatched_ncaa = {}, []
    used = set()
    games = [g for g in ncaa_games if str(g.get("game_id")) in listed and g.get("date", "") <= LAST_DATE]
    leftover = []
    for g in games:
        scores = sorted([to_int(g.get("home_score")), to_int(g.get("away_score"))])
        options = [s for s in schedule if s["url"] not in used and sorted([s["pts"], s["opp_pts"]]) == scores
                   and days_apart(s["date"], g["date"]) <= 1]
        if options:
            best = min(options, key=lambda s: days_apart(s["date"], g["date"]))
            used.add(best["url"])
            matched[str(g.get("game_id"))] = best["url"]
        else:
            leftover.append(g)
    # The two sites sometimes disagree on the final score. A team only plays once a day, so for a game
    # still unmatched, the one Sports Reference game left on the same date is the same game.
    for g in leftover:
        options = [s for s in schedule if s["url"] not in used and s["date"] == g["date"]]
        if len(options) == 1:
            used.add(options[0]["url"])
            matched[str(g.get("game_id"))] = options[0]["url"]
        else:
            unmatched_ncaa.append(f"{g.get('date')} {g.get('away_team')} at {g.get('home_team')}")
    return matched, unmatched_ncaa

def save_game_sites(team_path, schedule, matched):
    """Mark each game in game_scores.json as neutral-site or not, from Sports Reference's schedule."""
    by_url = {s["url"]: s for s in schedule}
    scores_path = os.path.join(team_path, "game_scores.json")
    scores = read_json(scores_path, [])
    changed = False
    for g in scores:
        game = by_url.get(matched.get(str(g.get("game_id"))))
        if game and (g.get("neutral") != (game["site"] == "N") or g.get("arena") != game["arena"]):
            g["neutral"], g["arena"] = game["site"] == "N", game["arena"]
            changed = True
    if changed:
        with open(scores_path, "w", encoding="utf-8") as out:
            json.dump(scores, out, indent=4)

# ---------------------------
# BOX SCORE PAGE
# ---------------------------
def parse_box_score(page):
    """School id -> starters, bench and the totals row, in the same layout 4boxscorefetch.py writes."""
    teams = {}
    for slug in re.findall(r'<table[^>]*\bid="box-score-basic-([^"]+)"', page):
        starters, bench, totals = [], [], None
        current = starters
        for row in table_rows(page, "box-score-basic-" + slug):
            name = row.get("player", "")
            if name == "Reserves":
                current = bench
                continue
            line = {
                "Name": name,
                "MIN": str(to_int(row.get("mp"))),
                "PTS": to_int(row.get("pts")),
                "FG": f"{to_int(row.get('fg'))}-{to_int(row.get('fga'))}",
                "3PT": f"{to_int(row.get('fg3'))}-{to_int(row.get('fg3a'))}",
                "FT": f"{to_int(row.get('ft'))}-{to_int(row.get('fta'))}",
                "REB": to_int(row.get("trb")),
                "AST": to_int(row.get("ast")),
                "PF": to_int(row.get("pf")),
                "TO": to_int(row.get("tov")),
                "OREB": to_int(row.get("orb")),
                "DREB": to_int(row.get("drb")),
                "STL": to_int(row.get("stl")),
                "BLK": to_int(row.get("blk"))
            }
            if name == "School Totals":
                del line["Name"], line["MIN"]
                totals = line
            elif "/cbb/players/" in row["_html"]:
                current.append(line)
        if totals:
            teams[slug] = {"starters_table": starters, "bench_table": bench, "team_totals": totals}
    return teams

def is_done(path):
    data = read_json(path)
    return bool(data) and data.get("source") == SOURCE

def players_add_up(team_entry):
    players = team_entry["starters_table"] + team_entry["bench_table"]
    minutes = sum(float(p["MIN"] or 0) for p in players)
    return minutes >= 195 and sum(p["PTS"] for p in players) == team_entry["team_totals"]["PTS"]

def write_box_score(team, team_path, game_id, slug, sr_teams, url):
    """Replace one team's copy of a box score. Returns a short note on what happened."""
    box_path = os.path.join(team_path, "boxscores", f"{game_id}.json")
    backup_path = os.path.join(team_path, BACKUP_FOLDER, f"{game_id}.json")
    ncaa = read_json(backup_path) or read_json(box_path)
    if not ncaa or len(ncaa.get("teams", [])) != 2:
        return build_box_score(team, team_path, game_id, slug, sr_teams, url)

    mine_index = [i for i, t in enumerate(ncaa["teams"]) if t["team_name"].rstrip(". ") == team.rstrip(". ")]
    other_slugs = [s for s in sr_teams if s != slug]
    if len(mine_index) != 1 or slug not in sr_teams or len(other_slugs) != 1:
        return "could not tell the two teams apart"
    sr_by_index = {mine_index[0]: sr_teams[slug], 1 - mine_index[0]: sr_teams[other_slugs[0]]}

    # When the two sites disagree on the final score, Sports Reference is taken as right:
    # its team totals are used for that game too, and the score in game_scores.json is corrected.
    scores_differ = any(ncaa_team["team_totals"]["PTS"] != sr_by_index[i]["team_totals"]["PTS"] for i, ncaa_team in enumerate(ncaa["teams"]))

    new_data = {"game_id": ncaa.get("game_id"), "game_info": ncaa.get("game_info", ""), "source": SOURCE, "source_url": SITE + url, "teams": []}
    if scores_differ:
        new_data["score_corrected"] = True
    for i, ncaa_team in enumerate(ncaa["teams"]):
        new_data["teams"].append({
            "team_name": ncaa_team["team_name"],
            "starters_table": sr_by_index[i]["starters_table"],
            "bench_table": sr_by_index[i]["bench_table"],
            # NCAA totals normally: complete, and they count team rebounds
            "team_totals": sr_by_index[i]["team_totals"] if scores_differ else ncaa_team["team_totals"]
        })

    if scores_differ:
        scores_path = os.path.join(team_path, "game_scores.json")
        scores = read_json(scores_path, [])
        points = {t["team_name"].rstrip(". "): t["team_totals"]["PTS"] for t in new_data["teams"]}
        for g in scores:
            if str(g.get("game_id")) == str(game_id):
                for side in ("home", "away"):
                    name = str(g.get(side + "_team", "")).rstrip(". ")
                    if name in points:
                        g[side + "_score"] = str(points[name])
        with open(scores_path, "w", encoding="utf-8") as out:
            json.dump(scores, out, indent=4)

    if not os.path.exists(backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copyfile(box_path, backup_path)
    with open(box_path, "w", encoding="utf-8") as out:
        json.dump(new_data, out, indent=4)
    return "ok (score corrected to Sports Reference)" if scores_differ else "ok"

def build_box_score(team, team_path, game_id, slug, sr_teams, url):
    """The NCAA has no box score for this game (it has none for older seasons), so the whole of it comes from Sports
    Reference: both teams' player lines and the team totals. Those totals do not count team rebounds."""
    game = next((g for g in read_json(os.path.join(team_path, "game_scores.json"), []) if str(g.get("game_id")) == str(game_id)), None)
    other_slugs = [s for s in sr_teams if s != slug]
    if not game or slug not in sr_teams or len(other_slugs) != 1:
        return "could not tell the two teams apart"
    names = [str(game.get("home_team", "")), str(game.get("away_team", ""))]
    mine = [n for n in names if n.rstrip(". ") == team.rstrip(". ")]
    if len(mine) != 1:
        return "could not tell the two teams apart"
    entries = {mine[0]: sr_teams[slug], names[1 - names.index(mine[0])]: sr_teams[other_slugs[0]]}
    new_data = {"game_id": str(game_id), "game_info": "", "source": SOURCE, "source_url": SITE + url, "teams": [
        {"team_name": name, "starters_table": entries[name]["starters_table"], "bench_table": entries[name]["bench_table"],
         "team_totals": entries[name]["team_totals"]} for name in names]}
    # Sports Reference's score is the one that stands
    scores_path = os.path.join(team_path, "game_scores.json")
    scores = read_json(scores_path, [])
    corrected = False
    for g in scores:
        if str(g.get("game_id")) == str(game_id):
            for side, name in (("home", names[0]), ("away", names[1])):
                points = str(entries[name]["team_totals"]["PTS"])
                if str(g.get(side + "_score")) != points:
                    g[side + "_score"], corrected = points, True
    if corrected:
        with open(scores_path, "w", encoding="utf-8") as out:
            json.dump(scores, out, indent=4)
    os.makedirs(os.path.join(team_path, "boxscores"), exist_ok=True)
    with open(os.path.join(team_path, "boxscores", f"{game_id}.json"), "w", encoding="utf-8") as out:
        json.dump(new_data, out, indent=4)
    return "ok (score corrected to Sports Reference)" if corrected else "ok"

# ---------------------------
# MAIN
# ---------------------------
def main():
    team_folders = get_team_folders()
    slugs = read_json(SCHOOLS_FILE)
    if not slugs:
        print(f"{SCHOOLS_FILE} is missing. Run 5rosterfetch.py first; it looks up the Sports Reference school names.")
        return
    folder_of_slug = {slug: team for team, slug in slugs.items()}

    # Optional: name some teams to do only those, e.g.  python "collect\\8srboxscores.py" "East Carolina" Nevada
    wanted = [w.lower() for w in sys.argv[1:]]
    # Teams are done in folder order: each conference A to Z, and each team A to Z inside it
    teams = [t for t in team_folders if t in slugs and (not wanted or t.lower() in wanted)]

    replaced = already = problems = 0
    print(f"{len(teams)} teams. About 4 seconds a page; already-replaced games are skipped, so this can be stopped and run again.")
    try:
        conference = None
        for n, team in enumerate(teams, 1):
            team_path = team_folders[team]
            if os.path.basename(os.path.dirname(team_path)) != conference:
                conference = os.path.basename(os.path.dirname(team_path))
                print(f"\n===== {conference} =====")
            try:
                schedule = load_schedule(team, team_path, slugs[team])
            except Blocked:
                raise
            except Exception as e:
                print(f"[{n}/{len(teams)}] {team}: schedule failed ({e}) - will retry next run")
                continue
            matched, unmatched = match_games(schedule, team_path)
            save_game_sites(team_path, schedule, matched)

            # Every game on the team's schedule gets its own line, in date order
            games = sorted((g for g in read_json(os.path.join(team_path, "game_scores.json"), []) if str(g.get("game_id")) in matched),
                           key=lambda g: g.get("date", ""))
            print(f"[{n}/{len(teams)}] {team}: {len(games)} games")
            for line in unmatched:
                print(f"   {line}: no Sports Reference game found")
                problems += 1

            for i, g in enumerate(games, 1):
                game_id = str(g.get("game_id"))
                url = matched[game_id]
                label = f"   {i:>2}/{len(games)}  {g.get('date')}  {g.get('away_team')} {g.get('away_score')} at {g.get('home_team')} {g.get('home_score')}"
                if is_done(os.path.join(team_path, "boxscores", f"{game_id}.json")):
                    print(f"{label}: already done")
                    already += 1
                    continue
                try:
                    page = fetch(SITE + url)
                except Blocked:
                    raise
                except Exception as e:
                    print(f"{label}: failed ({e}) - will retry next run")
                    continue
                sr_teams = parse_box_score(page or "")

                # One page covers both teams, so the opponent's copy is replaced now too
                notes, corrected = [], []
                for slug in sr_teams:
                    other_team = folder_of_slug.get(slug)
                    if not other_team or other_team not in team_folders: continue
                    other_path = team_folders[other_team]
                    if game_id not in {str(g).strip() for g in read_json(os.path.join(other_path, "games.json"), [])}: continue
                    note = write_box_score(other_team, other_path, game_id, slug, sr_teams, url)
                    if note.startswith("ok"):
                        replaced += 1
                        if note != "ok": corrected.append(other_team)
                    else:
                        notes.append(f"{other_team}: {note}")
                        problems += 1
                if slugs[team] not in sr_teams:
                    notes.append(f"{team} not found on {SITE + url}")
                    problems += 1
                result = "imported" + (" - score corrected to Sports Reference" if corrected else "")
                print(f"{label}: {result if not notes else 'PROBLEM - ' + '; '.join(notes)}")
    except Blocked as e:
        print(f"\n{e}\nStopping. Wait a few hours before running this again; everything fetched so far is saved.")
    except KeyboardInterrupt:
        print("\nStopped. Run it again to pick up where it left off.")

    print("-" * 30)
    print(f"Box scores replaced this run: {replaced}")
    print(f"Already replaced before this run: {already}")
    print(f"Problems (listed above): {problems}")
    print("-" * 30)

if __name__ == "__main__":
    main()
