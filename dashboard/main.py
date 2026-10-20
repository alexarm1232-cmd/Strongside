import os
import sys
import json
import re
import webbrowser
from collections import Counter
from pathlib import Path
from difflib import SequenceMatcher
# --- IMPORT YOUR MATH ENGINE ---
import Kenstat

# ---------------------------
# SEASONS
# ---------------------------
# Each season has its own data folder and its own dashboard page; the dropdown in the page header switches
# between them.   python dashboard/main.py            builds this season
#                 python dashboard/main.py 2425       builds last season (its data does not change, so once is enough)
#                 python dashboard/main.py all        builds both
#   teams: the data folder   page: the dashboard file   data: where its per-team files go (inside "dashboard")
#   this / last: the roster files it reads (roster_2026.json ...)   neutral_from: Kenstat's fallback date
#   spreads: whether this is the current season (the name is left from the Spread report, since removed from the site)
SEASONS = {
    "2526": {"label": "2025-26", "teams": "data/seasons/2526", "page": "dashboard.html", "data": "", "this": 2026, "last": 2025,
             "neutral_from": "2026/03/09", "spreads": True, "before": "data/seasons/2425"},
    "2425": {"label": "2024-25", "teams": "data/seasons/2425", "page": "dashboard_2425.html", "data": "2425/", "this": 2025, "last": 2024,
             "neutral_from": "2025/03/10", "spreads": False},
}
# Earlier seasons (set up by make_season_codes.py): code -> (the year the season ended, the Monday of championship week).
# Their shots mostly have no spot on the floor, so play types go by the kind of shot (see Shotstat.KIND_ZONES).
for code, (ended, neutral_from) in {"2324": (2024, "2024/03/11"), "2223": (2023, "2023/03/06"), "2122": (2022, "2022/03/07"),
                                    "2021": (2021, "2021/03/08"), "1920": (2020, "2020/03/09"), "1819": (2019, "2019/03/11"),
                                    "1718": (2018, "2018/03/05"), "1617": (2017, "2017/03/06"), "1516": (2016, "2016/03/07"),
                                    "1415": (2015, "2015/03/09"), "1314": (2014, "2014/03/10"), "1213": (2013, "2013/03/11"),
                                    "1112": (2012, "2012/03/05"), "1011": (2011, "2011/03/07"), "0910": (2010, "2010/03/08")}.items():
    SEASONS[code] = {"label": f"{ended - 1}-{ended % 100:02d}", "teams": "data/seasons/" + code, "page": f"dashboard_{code}.html",
                     "data": code + "/", "this": ended, "last": ended - 1, "neutral_from": neutral_from, "spreads": False, "kind_zones": True}
# The full-season view of a season: the same thing with the games after Selection Sunday counted too (the NCAA
# tournament and the other postseason events). Its data is a second folder, made by postseason.py, and it gets its own
# page; the switch in the page header goes between the two.   python dashboard/main.py 2526f
# (2019-20 has none: the season stopped before the postseason, in March 2020.)
for code in ("2526", "2425", "2324", "2223", "2122", "2021", "1819", "1718", "1617", "1516", "1415", "1314", "1213", "1112", "1011", "0910"):
    page = SEASONS[code]["page"]
    SEASONS[code + "f"] = dict(SEASONS[code], teams=f"data/seasons/{code} full", page=page.replace(".html", "_full.html"),
                               data=code + "f/", spreads=False, view="full", base=code)
    SEASONS[code]["full"] = code + "f"
CURRENT_SEASON = "2526"
SEASON_KEY = next((arg for arg in sys.argv[1:] if arg in SEASONS), CURRENT_SEASON)
SEASON = SEASONS[SEASON_KEY]
# The other modules copy these when they are loaded, so they are set first
Kenstat.THIS_SEASON, Kenstat.LAST_SEASON, Kenstat.NEUTRAL_FROM = SEASON["this"], SEASON["last"], SEASON["neutral_from"]
import Playerstat
import Shotstat
Shotstat.KIND_ZONES = bool(SEASON.get("kind_zones"))

# ---------------------------
# SETTINGS
# ---------------------------
MAIN_FOLDER = os.path.dirname(os.path.abspath(__file__))
# The data folder sits inside the "data" folder next to "dashboard", so this works no matter where you run it from
TEAMS_FOLDER = os.path.join(os.path.dirname(MAIN_FOLDER), SEASON["teams"])
JSON_FILENAME = "game_scores.json"
SIMILARITY_THRESHOLD = 0.85
# The page design lives in the template; the finished dashboard is rebuilt from it on every run
TEMPLATE_FILE = os.path.join(MAIN_FOLDER, "dashboard_template.html")
DASHBOARD_FILE = os.path.join(MAIN_FOLDER, SEASON["page"])
# Team logos (logos/teams.json maps each team folder name to its picture)
LOGO_FOLDER = os.path.join(MAIN_FOLDER, "logos")
# Game-by-game player lines, one file per team, rebuilt on every run
GAMELOG_FOLDER = os.path.join(MAIN_FOLDER, SEASON["data"] + "gamelogs")
# Who was on the floor together and what happened, one file per team, for the "without a player" page
LINEUP_FOLDER = os.path.join(MAIN_FOLDER, SEASON["data"] + "lineups")
# Every shot with its spot on the floor, one file per team, for the shot charts
SHOT_FOLDER = os.path.join(MAIN_FOLDER, SEASON["data"] + "shots")
HOME_COURT_USUAL = Kenstat.HOME_ADV      # the measured usual home edge, set when the teams are loaded
# The saved on/off tallies are kept apart for each season
if SEASON["data"]:
    Playerstat.ONOFF_CACHE = os.path.join(MAIN_FOLDER, f"onoff_cache_{SEASON_KEY}.json")
# Kenstat keys sent to the dashboard
STAT_KEYS = ["n", "o", "d", "t", "efg", "tov", "orb", "ftr", "d_efg", "d_tov", "d_orb", "d_ftr",
             "sos", "sos_o", "sos_d", "ncsos"]
ROSTER_KEYS = ["exp", "cont", "ht", "ht_g", "ht_f"]

# ---------------------------
# DATA HELPERS
# ---------------------------
def clean_name(name):
    if not name: return ""
    return re.sub(r'[^\w\s]', '', str(name)).lower().strip()

def similar(a, b):
    ca, cb = clean_name(a), clean_name(b)
    if ca == cb: return 1.0
    return SequenceMatcher(None, ca, cb).ratio()

def get_team_record_data(team_folder_name, team_path):
    json_path = os.path.join(team_path, JSON_FILENAME)
    wins, losses = 0, 0
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                games = json.load(f)
                f_name_clean = clean_name(team_folder_name)
                for game in games:
                    try:
                        h_name = game.get("home_team", "")
                        a_name = game.get("away_team", "")
                        h_score = int(game.get("home_score", 0))
                        a_score = int(game.get("away_score", 0))

                        if similar(f_name_clean, h_name) >= SIMILARITY_THRESHOLD:
                            if h_score > a_score: wins += 1
                            elif a_score > h_score: losses += 1
                        elif similar(f_name_clean, a_name) >= SIMILARITY_THRESHOLD:
                            if a_score > h_score: wins += 1
                            elif h_score > a_score: losses += 1
                    except (ValueError, TypeError):
                        continue
        except Exception:
            pass
    return wins, losses

def get_season_label():
    """Season name from the game dates, e.g. '2025-26'."""
    for root, dirs, files in os.walk(TEAMS_FOLDER):
        if JSON_FILENAME in files:
            try:
                with open(os.path.join(root, JSON_FILENAME), "r") as f:
                    years = sorted(int(game["date"][:4]) for game in json.load(f))
                return f"{years[0]}-{str(years[-1])[2:]}" if years[0] != years[-1] else str(years[0])
            except Exception:
                continue
    return ""

def load_logos():
    """Team folder name -> logo path the dashboard can use, e.g. 'logos/alabama.svg'."""
    try:
        with open(os.path.join(LOGO_FOLDER, "teams.json"), "r", encoding="utf-8") as f:
            logo_files = json.load(f)
    except Exception:
        return {}
    return {name: f"logos/{filename}" for name, filename in logo_files.items()
            if os.path.exists(os.path.join(LOGO_FOLDER, filename))}

def load_teams():
    """Returns (teams, players) for the dashboard."""
    if not os.path.exists(TEAMS_FOLDER):
        return [], [], {}, {"scale": 1.0, "players": 0}

    # 1. RUN THE KENSTAT ENGINE, with home court measured from the games: this season's, pooled with the season
    # before when its data is there (the building does not move). The measured edge goes into the ratings themselves.
    global HOME_COURT_USUAL
    home_court = {}
    try:
        before = os.path.join(os.path.dirname(MAIN_FOLDER), SEASON["before"]) if SEASON.get("before") else None
        kenstat_results = Kenstat.measure_home_court(TEAMS_FOLDER, before)
        HOME_COURT_USUAL, home_court = Kenstat.HOME_ADV, dict(Kenstat.HOME_EDGES)
    except Exception as e:
        print(f"Kenstat Error: {e}")
        kenstat_results = {}
    # both teams' net ratings going into each game (the team pages' quad lists show the gap)
    try:
        nets_before = Kenstat.nets_before_games(TEAMS_FOLDER)
    except Exception as e:
        print(f"Ratings-before-each-game Error: {e}")
        nets_before = {}

    # Windows drops trailing dots/spaces from folder names ("Alabama St." -> "Alabama St"),
    # so strip them from the Kenstat names before matching.
    display_names = {name.rstrip(". "): name.strip() for name in kenstat_results}
    kenstat_results = {name.rstrip(". "): stats for name, stats in kenstat_results.items()}

    logos = load_logos()

    # 3. ROSTER STATS (experience, continuity, height), keyed by team folder name
    try:
        roster_stats = Kenstat.get_roster_stats(TEAMS_FOLDER)
    except Exception as e:
        print(f"Roster Stats Error: {e}")
        roster_stats = {}

    # the AP poll ranks the Champion picker uses (tools/ap_polls.py), keyed by team folder name
    try:
        with open(os.path.join(TEAMS_FOLDER, "ap_polls.json"), encoding="utf-8") as f:
            ap_teams = {name.rstrip(". "): ranks for name, ranks in json.load(f)["teams"].items()}
    except Exception:
        ap_teams = {}

    teams_output = []
    for conference in os.listdir(TEAMS_FOLDER):
        conf_path = os.path.join(TEAMS_FOLDER, conference)
        if os.path.isdir(conf_path):
            for team_folder in os.listdir(conf_path):
                team_path = os.path.join(conf_path, team_folder)
                if os.path.isdir(team_path):
                    # Get W-L Record
                    w, l = get_team_record_data(team_folder, team_path)

                    # 2. MATCH KENSTAT DATA (a stat is None when Kenstat has no rating for the team)
                    key = team_folder.rstrip(". ")
                    metrics = kenstat_results.get(key, {})

                    team = {"name": display_names.get(key, team_folder), "conf": conference, "w": w, "l": l, "logo": logos.get(key), "folder": team_folder}
                    for stat in STAT_KEYS:
                        value = metrics.get(stat)
                        team[stat] = value if isinstance(value, (int, float)) else None
                    team["box"] = metrics.get("box")      # per-game box score, the team's own ("o") and its opponents' ("d")
                    team["ap"] = ap_teams.get(key) or {}  # AP poll: preseason, week 6, last before the tournament
                    for stat in ROSTER_KEYS:
                        team[stat] = roster_stats.get(team_folder, {}).get(stat)
                    # "hca": the team's home edge per side per 100 possessions (what the simulators use);
                    # "hc": the same as points a game at the team's own tempo (what the tables show)
                    if key in home_court and team.get("t"):
                        team["hca"] = round(home_court[key], 2)
                        team["hc"] = round(2 * home_court[key] * team["t"] / 100, 2)
                    teams_output.append(team)

    # 4. PLAYER STATS (ratings, on/off, box plus/minus), built on the team ratings above
    try:
        players_output, schedules, game_logs, lineups, stints = Playerstat.get_player_stats(TEAMS_FOLDER, kenstat_results)
    except Exception as e:
        print(f"Player Stats Error: {e}")
        players_output, schedules, game_logs, lineups, stints = [], {}, {}, {}, {}
    # How far real results fall short of what box scores predict when a player sits (for the "without a player" page)
    try:
        without_check = Playerstat.without_calibration(players_output, lineups)
    except Exception as e:
        print(f"Without-a-player Check Error: {e}")
        without_check = {"scale": 1.0, "players": 0}

    # 5. SHOTS (zones, what led to the shot, and where on the floor), from ESPN's play-by-play
    # each player's estimated position (1 point guard ... 5 center) decides how far his plays read as a big's
    positions = {}
    for player in players_output:
        positions.setdefault(player["team"], {})[Playerstat.norm_name(player["name"])] = player["posn"]
    try:
        shot_stats = Shotstat.get_shot_stats(TEAMS_FOLDER, positions, stints)
    except Exception as e:
        print(f"Shot Stats Error: {e}")
        shot_stats = {}
    # league-wide FG% by court area, carried to the dashboard with the other league-wide numbers
    without_check["areas"] = shot_stats.pop("__league__", {"areas": []})["areas"]
    by_folder = {}
    for player in players_output:
        by_folder.setdefault(player["team"], {})[Playerstat.norm_name(player["name"])] = player
    rated = [stats["o"] for stats in kenstat_results.values() if isinstance(stats.get("o"), (int, float))]
    league_average = sum(rated) / len(rated) if rated else None      # the average offense (and defense), points per 100 possessions
    for folder, shots in shot_stats.items():
        # ESPN spells some names differently, so each of its players is matched to ours
        ours = by_folder.get(folder, {})
        renamed = {}
        for espn_name, tally in shots["players"].items():
            key = Playerstat.match_name(espn_name, ours) if ours else None
            if key:
                ours[key]["shot"] = {"z": tally["z"], "ft": tally["ft"], "c": tally["c"], "a": tally["a"], "pt": tally["pt"], "big": tally["big"]}
                renamed[espn_name] = ours[key]["name"]
        # Nicknames ('Boopie Miller' / 'Kevin Miller'): a player still unmatched takes the ESPN name whose
        # field goal attempts equal his, when exactly one does
        for player in ours.values():
            if "shot" in player or not player["fga"]: continue
            same = [name for name, tally in shots["players"].items()
                    if name not in renamed and sum(z[0] for z in tally["z"]) == player["fga"]]
            if len(same) == 1:
                tally = shots["players"][same[0]]
                player["shot"] = {"z": tally["z"], "ft": tally["ft"], "c": tally["c"], "a": tally["a"], "pt": tally["pt"], "big": tally["big"]}
                renamed[same[0]] = player["name"]
        shots["chart"]["players"] = [renamed.get(name, name) for name in shots["chart"]["players"]]

        # Turnovers are counted as plays worth nothing. Where the CollegeBasketballData.com files cover every game
        # they are already in, one by one. Otherwise they are estimated: a player's own from his box scores, the
        # team's as the sum of those, and the ones a defense forces from its defensive turnover rate.
        counted = shots.get("turnovers_counted")
        team_poss = sum(game["poss"] for game in schedules.get(folder, [])) or 1
        forced = 0 if counted else (kenstat_results.get(folder.rstrip(". "), {}).get("d_tov") or 0) / 100 * team_poss
        shots["o"]["pt"] = Shotstat.add_turnovers(shots["o"]["pt"], 0 if counted else sum(round(pl["tpg"] * pl["g"]) for pl in ours.values()))
        shots["d"]["pt"] = Shotstat.add_turnovers(shots["d"]["pt"], forced)
        # "pta": the same play types adjusted for strength of schedule, using the schedule numbers the ratings page
        # shows. A team's points on every kind of play are scaled by how the defenses it faced compare with the average
        # defense, and what it allowed by how the offenses it faced compare with the average offense.
        rating = kenstat_results.get(folder.rstrip(". "), {})
        for side, faced in (("o", rating.get("sos_d")), ("d", rating.get("sos_o"))):
            factor = league_average / faced if faced and league_average else 1.0
            shots[side]["pta"] = [[plays, round(points * factor, 1)] for plays, points in shots[side]["pt"]]
        # what opponents ran, and how it went, while each player was on the floor (the names can be ours or ESPN's)
        # and what the team itself ran while he was on the floor
        against, alongside = {}, {}
        for merged, source in ((against, shots["defenders"]), (alongside, shots["teammates"])):
            for name, plays in source.items():
                key = Playerstat.match_name(name, ours) if ours else None
                if key:
                    merged[key] = [[a[0] + b[0], a[1] + b[1]] for a, b in zip(merged[key], plays)] if key in merged else plays
        # play types by the five on the floor, for the "without a player" page (players it cannot name are -1)
        listed, number_of, by_five = [], {}, {}
        def number(name):
            if name not in number_of:
                key = Playerstat.match_name(name, ours) if ours else None
                if key and ours[key]["name"] not in listed: listed.append(ours[key]["name"])
                number_of[name] = listed.index(ours[key]["name"]) if key else -1
            return number_of[name]
        for five, own, theirs in shots["fives"]:
            row = by_five.setdefault(tuple(sorted(number(name) for name in five)), [[0.0] * (2 * len(Shotstat.PLAY_TYPES)), [0.0] * (2 * len(Shotstat.PLAY_TYPES))])
            for sums, plays in zip(row, (own, theirs)):
                for i, (count, points) in enumerate(plays or []):
                    sums[2 * i] += count
                    sums[2 * i + 1] += points
        shots["chart"]["fives"] = {"players": listed, "rows": [[list(five), [round(v, 2) for v in own], [round(v, 2) for v in theirs]]
                                                                for five, (own, theirs) in by_five.items()]}
        for key, player in ours.items():
            if "shot" in player:
                player["shot"]["pt"] = Shotstat.add_turnovers(player["shot"]["pt"], 0 if counted else round(player["tpg"] * player["g"]))
            if key in against:
                player["dpt"] = Shotstat.add_turnovers(against[key], forced * player["poss"] / team_poss)
            if key in alongside:
                player["wpt"] = Shotstat.add_turnovers(alongside[key], 0 if counted else sum(round(pl["tpg"] * pl["g"]) for pl in ours.values()) * player["poss"] / team_poss)

    # same team names the teams list uses, so the dashboard can link players, opponents and logos to their team
    shown_name = lambda name: display_names.get(name.rstrip(". "), name)
    for player in players_output:
        player["team"] = shown_name(player["team"])
    used_files = set()
    logs_output = {}   # file name -> (team name, that team's player game logs)
    for team in teams_output:
        folder = team.pop("folder")
        team["sched"] = schedules.get(folder, [])
        # the games behind the shot and play-type numbers (only games with shot spots), and their possessions
        shots = shot_stats.get(folder)
        counted = set(shots["used"]) if shots else set()
        shot_games = [game for game in team["sched"] if game.get("id") in counted]
        for game in team["sched"]:
            # "nt" / "no": this team's and the opponent's net rating going into the game (None early in the season)
            before = nets_before.get(game.get("id"), {})
            game["nt"], game["no"] = before.get(folder.rstrip(". ")), before.get(game["opp"].rstrip(". "))
            game["opp"] = shown_name(game["opp"])
            game.pop("id", None)
        # each team's game logs go in their own small file, which the dashboard only loads when a player is opened
        filename = re.sub(r"[^a-z0-9]+", "_", folder.lower()).strip("_") or "team"
        while filename in used_files:
            filename += "_"
        used_files.add(filename)
        team["log"] = f"{SEASON['data']}gamelogs/{filename}.js"
        team["five"] = f"{SEASON['data']}lineups/{filename}.js"
        team["shot"] = {"o": shots["o"], "d": shots["d"], "g": len(shot_games), "poss": round(sum(game["poss"] for game in shot_games), 1)} if shots else None
        team["shots"] = f"{SEASON['data']}shots/{filename}.js"
        logs_output[filename] = (team["name"], game_logs.get(folder, {}), lineups.get(folder, {"players": [], "rows": []}),
                                 shots["chart"] if shots else {"players": [], "o": [], "d": []})
    return teams_output, players_output, logs_output, without_check

# ---------------------------
# DASHBOARD
# ---------------------------
def build_dashboard():
    """Run the numbers and write dashboard.html. Returns the file path."""
    teams, players, logs, without_check = load_teams()
    added = write_team_files(teams, logs)
    data = {
        "meta": {"season": get_season_label(), "without": without_check, "garbage": Playerstat.GARBAGE_MARGIN,
                 "home": Kenstat.HOME_ADV, "home_measured": round(HOME_COURT_USUAL, 2), "spreads": SEASON["spreads"],
                 # every season with a page built, for the dropdown in the header (newest first)
                 "seasons": season_list(),
                 # "pre" = through Selection Sunday, "full" = the postseason too; "views" has both pages when both are built
                 "view": SEASON.get("view", "pre"), "views": view_pages(), "ap": ap_weeks()},
        "teams": teams,
        "players": players,
    }

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    # "</" is escaped so a team name can never close the page's script block
    page = template.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(page)
    write_seasons_file()
    if added is not None:
        print(f"   full season: {added[0]} of {added[1]} team files written as postseason add-ons to the pre-tournament files")
    return DASHBOARD_FILE

# ---------------------------
# EACH TEAM'S FILES (shots, game logs, lineups)
# ---------------------------
# A full-season page does not store a second copy of the season. Its files hold only what the postseason adds
# ("add-ons"), and the page loads the pre-tournament file first and adds them on. Where a team's file cannot be split
# that way, the whole file is written as before. So: build the pre-tournament page first, then the full season.
KINDS = (("shots", "SHOTS", "shots", "shotsAdd"), ("gamelogs", "GAMELOGS", "log", "logAdd"), ("lineups", "LINEUPS", "five", "fiveAdd"))

def read_team_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    except Exception:
        return None

def take_away(full_rows, base_rows, full_key, base_key=None):
    """The rows of full_rows that are not in base_rows (compared as a multiset through the two key functions, which
    turn player numbers into names), or None when base_rows is not all inside full_rows."""
    left = Counter((base_key or full_key)(r) for r in base_rows)
    extra = []
    for r in full_rows:
        k = full_key(r)
        if left[k] > 0:
            left[k] -= 1
        else:
            extra.append(r)
    return None if any(v > 0 for v in left.values()) else extra

def shots_add_on(full, base):
    def named(names):
        # an offense row ends with the shooter's number in that file's player list; a defense row has none
        return lambda r: json.dumps(r[:5] + [names[r[5]] if isinstance(r[5], int) and 0 <= r[5] < len(names) else r[5]] if len(r) > 5 else r)
    o = take_away(full["o"], base["o"], named(full["players"]), named(base["players"]))
    d = take_away(full["d"], base["d"], json.dumps)
    if o is None or d is None:
        return None
    fives = None
    if full.get("fives") or base.get("fives"):
        ff, fb = full.get("fives") or {"players": [], "rows": []}, base.get("fives") or {"players": [], "rows": []}
        key = lambda names, five: tuple(sorted(names[i] if 0 <= i < len(names) else "" for i in five))
        before = {key(fb["players"], r[0]): r for r in fb["rows"]}
        rows = []
        for r in ff["rows"]:
            b = before.pop(key(ff["players"], r[0]), None)
            diff = []
            for mine, theirs in ((r[1], b[1] if b else None), (r[2], b[2] if b else None)):
                if mine is None:
                    diff.append(None)
                elif theirs is None:
                    diff.append(mine)
                else:
                    diff.append([round(x - y, 2) for x, y in zip(mine, theirs)])
            if any(part and any(abs(x) > 1e-9 for x in part) for part in diff):
                rows.append([r[0]] + diff)
        if before:
            return None
        fives = {"players": ff["players"], "rows": rows}
    return {"players": full["players"], "o": o, "d": d, "fives": fives}

def lineups_add_on(full, base):
    named = lambda names: lambda r: json.dumps([r[0], sorted(names[i] if 0 <= i < len(names) else "" for i in r[1])] + r[2:])
    rows = take_away(full["rows"], base["rows"], named(full["players"]), named(base["players"]))
    return None if rows is None else {"players": full["players"], "rows": rows}

def logs_add_on(full, base):
    out = {}
    for player, entry in full.items():
        before = base.get(player)
        if before is None:
            out[player] = entry
            continue
        if entry.get("log", [])[:len(before.get("log", []))] != before.get("log", []):
            return None
        out[player] = dict(entry, log=entry.get("log", [])[len(before.get("log", [])):])
    return out if all(p in full for p in base) else None

ADD_ON = {"shots": shots_add_on, "gamelogs": logs_add_on, "lineups": lineups_add_on}

def write_team_files(teams, logs):
    """Writes each team's three files. Returns (add-ons written, files) on a full-season page, else None."""
    folders = {"shots": SHOT_FOLDER, "gamelogs": GAMELOG_FOLDER, "lineups": LINEUP_FOLDER}
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
    base_data = SEASONS[SEASON["base"]]["data"] if SEASON.get("view") == "full" and SEASON.get("base") in SEASONS else None
    by_name = {t["name"]: t for t in teams}
    added = files = 0
    for filename, (team_name, team_logs, team_lineups, team_shots) in logs.items():
        team = by_name.get(team_name, {})
        for (kind, store, field, add_field), content in zip(KINDS, (team_shots, team_logs, team_lineups)):
            files += 1
            path = os.path.join(folders[kind], filename + ".js")
            if base_data is not None:
                base = read_team_file(os.path.join(MAIN_FOLDER, base_data + kind, filename + ".js"))
                add_on = ADD_ON[kind](content, base) if base is not None else None
                if add_on is not None:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"{store}_ADD[{json.dumps(team_name)}] = {json.dumps(add_on, separators=(',', ':'))};\n")
                    team[field], team[add_field] = f"{base_data}{kind}/{filename}.js", f"{SEASON['data']}{kind}/{filename}.js"
                    added += 1
                    continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"{store}[{json.dumps(team_name)}] = {json.dumps(content, separators=(',', ':'))};\n")
    return (added, files) if base_data is not None else None

def ap_weeks():
    """Which AP polls the season's ranks come from ({pre, w6, last} -> the poll's label), or None without poll data."""
    try:
        with open(os.path.join(TEAMS_FOLDER, "ap_polls.json"), encoding="utf-8") as f:
            return json.load(f)["weeks"]
    except Exception:
        return None

def built(key):
    return key == SEASON_KEY or os.path.exists(os.path.join(MAIN_FOLDER, SEASONS[key]["page"]))

def season_list():
    """Every season with a page built, for the dropdown in the header (newest first). From a full-season page the
    dropdown goes to the other seasons' full-season pages where they exist."""
    here = SEASON.get("base", SEASON_KEY)
    full_view = SEASON.get("view") == "full"
    seasons = []
    for key, s in SEASONS.items():
        if s.get("view") == "full": continue
        show = s["full"] if full_view and s.get("full") and built(s["full"]) else key
        if built(show):
            seasons.append({"label": s["label"], "page": SEASONS[show]["page"], "here": key == here})
    return seasons

SEASONS_FILE = os.path.join(MAIN_FOLDER, "seasons.js")

def write_seasons_file():
    """seasons.js: every season with a page built, read by every page for the season dropdown. Rewritten on every
    build, so adding a season only needs its own pages built; the other pages pick it up from this file."""
    seasons = []
    for key, s in SEASONS.items():
        if s.get("view") == "full" or not built(key): continue
        full = s.get("full")
        seasons.append({"label": s["label"], "pre": s["page"], "full": SEASONS[full]["page"] if full and built(full) else None})
    seasons.sort(key=lambda s: s["label"], reverse=True)
    with open(SEASONS_FILE, "w", encoding="utf-8") as f:
        f.write("// Written by dashboard/main.py: the seasons with a page built, newest first\n"
                "window.STRONGSIDE_SEASONS = " + json.dumps(seasons, indent=1) + ";\n")

def view_pages():
    base = SEASON.get("base", SEASON_KEY)
    full = SEASONS[base].get("full")
    if not full or not built(base) or not built(full):
        return None
    return {"pre": SEASONS[base]["page"], "full": SEASONS[full]["page"]}

if __name__ == "__main__":
    if "all" in sys.argv[1:]:
        # each season is built by its own run, since the season is fixed when the modules load
        import subprocess
        for key, season in SEASONS.items():
            # only seasons whose box scores have been collected
            folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), season["teams"])
            if any(os.path.isdir(os.path.join(root, "boxscores")) for root, dirs, files in os.walk(folder) if root.count(os.sep) - folder.count(os.sep) == 2):
                subprocess.run([sys.executable, os.path.abspath(__file__), key, "quiet"])
    else:
        print(f"Calculating ratings ({SEASON['label']})...")
        path = build_dashboard()
        print(f"Dashboard saved to {path}")
        if "quiet" not in sys.argv[1:]:
            webbrowser.open(Path(path).as_uri())
