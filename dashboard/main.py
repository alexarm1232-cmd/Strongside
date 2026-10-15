import os
import sys
import json
import re
import webbrowser
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
#   spreads: whether the season has a Spread report
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
for code in ("2526", "2425", "2324", "2223"):
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
    data = {
        "meta": {"season": get_season_label(), "without": without_check, "garbage": Playerstat.GARBAGE_MARGIN,
                 "home": Kenstat.HOME_ADV, "home_measured": round(HOME_COURT_USUAL, 2), "spreads": SEASON["spreads"],
                 # every season with a page built, for the dropdown in the header (newest first)
                 "seasons": season_list(),
                 # "pre" = through Selection Sunday, "full" = the postseason too; "views" has both pages when both are built
                 "view": SEASON.get("view", "pre"), "views": view_pages()},
        "teams": teams,
        "players": players,
    }

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    # "</" is escaped so a team name can never close the page's script block
    page = template.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(page)

    os.makedirs(GAMELOG_FOLDER, exist_ok=True)
    os.makedirs(LINEUP_FOLDER, exist_ok=True)
    os.makedirs(SHOT_FOLDER, exist_ok=True)
    for filename, (team_name, team_logs, team_lineups, team_shots) in logs.items():
        with open(os.path.join(SHOT_FOLDER, filename + ".js"), "w", encoding="utf-8") as f:
            f.write(f"SHOTS[{json.dumps(team_name)}] = {json.dumps(team_shots, separators=(',', ':'))};\n")
        with open(os.path.join(GAMELOG_FOLDER, filename + ".js"), "w", encoding="utf-8") as f:
            f.write(f"GAMELOGS[{json.dumps(team_name)}] = {json.dumps(team_logs, separators=(',', ':'))};\n")
        with open(os.path.join(LINEUP_FOLDER, filename + ".js"), "w", encoding="utf-8") as f:
            f.write(f"LINEUPS[{json.dumps(team_name)}] = {json.dumps(team_lineups, separators=(',', ':'))};\n")
    return DASHBOARD_FILE

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
