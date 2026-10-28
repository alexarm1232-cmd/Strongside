import os
import json
import time
from collections import defaultdict

import Kenstat
import Playerstat
import Shotstat

# ---------------------------
# SPREAD REPORT
# ---------------------------
# Plays the whole season over again, one game day at a time, and writes down for every game what the game
# simulator would have had to work with THAT DAY: each team's ratings, tempo, four factors, shot zones and
# play types, and each player's numbers, all built from only the games played before it, plus who actually
# played in the game (so the simulator can sit the players who were out). Beside that go the real betting
# spread and the real result. The dashboard's "Spread report" page reads this file, plays every game in the
# simulator and reports how its spreads compare with the real ones.
#
# Run it on its own after the data changes (it takes a minute or two):   python main\Spreadstat.py

MAIN_FOLDER = os.path.dirname(os.path.abspath(__file__))
TEAMS_FOLDER = os.path.join(os.path.dirname(MAIN_FOLDER), "data/seasons/2526")
DRAFTKINGS_FILE = os.path.join(TEAMS_FOLDER, "draftkings_spreads_2026.json")   # the real spreads: DraftKings, from ESPN (collect/2526/11espnodds.py)
MARKET_FILE = os.path.join(TEAMS_FOLDER, "market_spreads_2026.json")    # BetIQ / TeamRankings: used only where there is no DraftKings line
REPORT_FILE = os.path.join(MAIN_FOLDER, "spreadreport.js")
SKIP_FIRST_GAMES = 5        # a game is left out until both teams have played this many
# November is for collecting data only: its games build the ratings and every other number, but none of them is
# compared with the real spread. The comparison starts on this date.
COMPARE_FROM = "2025/12/01"
ITERATIONS = 30             # the same number of passes the team ratings use
# The ratings as the dashboard makes them: Kenstat's blowout damping and every game counting the same. Other settings
# can be set from outside (Tourneystat.py turns the damping off): a game's weight halves every RATING_HALF_LIFE days
# back, and blowouts are damped on RATING_LOPSIDED. (2020-21 also phases in 2019-20's ratings, as the dashboard's
# ratings do: Kenstat.RATING_PRIOR.)
RATING_HALF_LIFE = None
RATING_LOPSIDED = None
PLAY_SHRINK = 30            # must match PLAY_SHRINK in the dashboard's play-type matchup
# Last season as a head start. Early in the season a team has too few games to judge, so each team's numbers lean on
# what its CURRENT players did in 2024-25 (wherever they played), fading as its games pile up and gone by HEAD_START_ENDS.
LAST_SEASON_FOLDER = os.path.join(os.path.dirname(MAIN_FOLDER), "data/seasons/2425")
LAST_SEASON_PAGE = os.path.join(MAIN_FOLDER, "dashboard_2425.html")      # built by: python dashboard/main.py 2425
HEAD_START_GAMES = 8        # on COMPARE_FROM the head start counts like this many games of the team's own
HEAD_START_ENDS = "2026/01/01"
HEAD_START_STEADY = 200     # a player's 2024-25 value is pulled toward a newcomer's until he has this many minutes behind it
# A box score misses much of what a player does (defense away from the ball, spacing, screens). His 2024-25 on/off
# (the team's net rating with him on the floor minus with him off) catches some of it, but is far noisier. So a
# player's value can be a blend: (1 - ONOFF_WEIGHT) parts box plus/minus to ONOFF_WEIGHT parts on/off. The on/off is
# first pulled toward zero as if ONOFF_STEADY more possessions of an average swing had been played, then put on the
# box plus/minus scale (the two are spread differently across players). 0 = box plus/minus only.
ONOFF_WEIGHT = 0.0
ONOFF_STEADY = 1500
# Adding up players' numbers understates how far apart teams really are (the best teams' newcomers are better than the
# average newcomer, and every player's number has been pulled toward the middle), so each team's head start is
# stretched away from the average team's by this much. It, and HEAD_START_GAMES, were set to bring the December
# spreads closest to the real ones.
HEAD_START_STRETCH = 3.0
# However strong, last season never moves a team more than this many points per 100 possessions from what its own
# games this season say
HEAD_START_CAP = 12
# The program itself. Players change, but how a school played last season still says a lot about how it will play
# (the coach, the system, the level it recruits and schedules at): a Big Ten team that finished 10th is not level with
# the 349th team after eight games, whatever those eight games say. So each team also leans on its OWN 2024-25 play
# types: what it scored on each kind of play, and what it allowed, against the D-I average on that kind of play
# (opponent-adjusted, as on the 2024-25 page). It is the same kind of evidence the simulator runs on, not a team
# rating. It counts like PROGRAM_GAMES games on COMPARE_FROM and fades out on the same calendar as the players' head
# start. 0 games = not used.
PROGRAM_GAMES = 3
# Early in the season, pulling every play type toward the plain D-I number flattens the gap between very good and
# very bad teams, and big favourites come out too small. So in December each play type is pulled instead toward what
# a team this good OVERALL would score on it (LEVEL_TYPE_SHRINK plays' worth), the team's overall level being pulled
# toward average as if it had LEVEL_SHRINK more points of average plays behind it. This fades out on the same
# calendar as the 2024-25 head start; from January the plain pull does better. None = never use it.
# PLAY_BLOWOUTS (counting an expected blowout for less, as the team ratings do) was tried and made the spreads far
# worse, so it is off: for play types a team's blowouts are its best evidence.
PLAY_BLOWOUTS = False
LEVEL_SHRINK = 600
LEVEL_TYPE_SHRINK = 80
level_share = 0.0       # how much of the December method is in use on the day being worked out (set in build_report)
# In November good teams mostly play weak ones, and after a handful of games the ratings cannot yet tell how weak:
# a team that has only been beaten by good teams looks about average. So a string of blowouts over weak teams passes
# for strength. With HEAD_START_SCHEDULE the strength-of-schedule adjustment judges each OPPONENT with its 2024-25
# head start blended in (the same blend, fading the same way), so beating a team of last year's weak players counts
# for what it is.
HEAD_START_SCHEDULE = True
# Name two teams here, e.g. ("Arkansas", "Louisville"), to have build_report print how their games' spreads were put together
EXPLAIN = None
# Where each game's home edge comes from:
#   "last"  - measured on 2024-25 only (what could be known before the season)
#   "full"  - measured on all of 2025-26 pooled with 2024-25, the number the dashboard shows (it looks ahead)
#   "decay" - 2025-26 games played before that day, with 2024-25 added in at a weight that fades to nothing by
#             HEAD_START_ENDS, the way the players' head start does
HOME_COURT = "last"
PLAY_ADJUST = "sos"         # how play types are adjusted for opponents: "sos" or "category" (see build_report)
# From this date on, games are still compared but never join the record, so every one of them is played as things
# stood the day before it (Tourneystat.py's pre-tournament view). None = each game day joins the record as usual.
FREEZE_FROM = None
USEFUL_MINUTES = 10         # a player averaging this many minutes (in the games he has played so far) is "useful"
MOST_PLAYERS = 14           # players sent to the simulator for each team, most minutes first

def date_number(day):
    """'2025/12/01' -> a day count, for measuring how far apart two dates are."""
    import datetime
    year, month, d = (int(part) for part in day.split('/'))
    return datetime.date(year, month, d).toordinal()

def read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as open_f:
            return json.load(open_f)
    except Exception:
        return default

# ---------------------------
# THE SEASON'S GAMES, AS THE RATINGS READ THEM
# ---------------------------
def load_season(root_folder):
    """Reads every box score the way Kenstat.get_efficiency_ratings does, but keeps each game's date.
    Returns (visits, games, folders, paths):
      visits: one entry for each box score file in each team folder (so a game between two of our teams is there
              twice, exactly as the ratings count it), in date order
      games:  game id -> date, the two teams, score, where it was played
      folders: team folder name (no trailing dots) -> conference
      paths:   team folder name (no trailing dots) -> (the folder's real name, its path)"""
    listed = {}         # game id -> its game_scores.json entry
    folders, paths = {}, {}
    for conference in sorted(os.listdir(root_folder)):
        conf_path = os.path.join(root_folder, conference)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            team_path = os.path.join(conf_path, team)
            if not os.path.isdir(team_path): continue
            folders[team.rstrip('. ')] = conference
            paths[team.rstrip('. ')] = (team, team_path)
            for g in read_json(os.path.join(team_path, 'game_scores.json'), []):
                listed.setdefault(str(g['game_id']), g)
    home_teams = Kenstat.load_home_teams(root_folder)
    d1 = Kenstat.d1_names(root_folder)

    visits, games, undated = [], {}, 0
    for root, dirs, files in os.walk(root_folder):
        if root.split(os.sep)[-1].lower() != 'boxscores': continue
        for f in files:
            if not f.endswith('.json'): continue
            try:
                data = read_json(os.path.join(root, f))
                g_id = str(data.get('game_id') or f).strip()
                t0, t1 = data['teams'][0], data['teams'][1]
                # a school outside Division I is rated as the one pooled opponent, as Kenstat does
                n0, n1 = (n if n.rstrip('. ') in d1 else Kenstat.NON_D1 for n in (t0['team_name'], t1['team_name']))
                s0, s1 = t0['team_totals'], t1['team_totals']
                poss0 = Kenstat.parse_attempts(s0['FG']) - s0['OREB'] + s0['TO'] + 0.475 * Kenstat.parse_attempts(s0['FT'])
                poss1 = Kenstat.parse_attempts(s1['FG']) - s1['OREB'] + s1['TO'] + 0.475 * Kenstat.parse_attempts(s1['FT'])
                pts0, pts1 = s0['PTS'], s1['PTS']
                poss = (poss0 + poss1) / 2
                eff0, eff1 = pts0 / poss * 100, pts1 / poss * 100
                minutes = lambda tm: sum(float(p['MIN'] or 0) for p in Kenstat.player_lines(tm))
                overtimes = max(0, round((max(minutes(t0), minutes(t1)) - 200) / 25))
                tempo = poss * 40 / (40 + 5 * overtimes)
                home = home_teams.get(f[:-5])
                h0 = h1 = 0
                if home == n0.rstrip('. '): h0, h1 = Kenstat.home_edge(home), -Kenstat.home_edge(home)
                elif home == n1.rstrip('. '): h0, h1 = -Kenstat.home_edge(home), Kenstat.home_edge(home)
            except Exception:
                continue
            info = listed.get(f[:-5]) or listed.get(g_id)
            if not info:
                undated += 1
                continue
            date = info['date']
            visits.append({"id": g_id, "date": date, "n0": n0, "n1": n1, "o0": eff0 - h0, "o1": eff1 - h1,
                           "pts": pts0 + pts1, "poss_sum": poss0 + poss1, "poss": poss, "tempo": tempo})
            if g_id not in games:
                # "file" is the game's file name, which the shot files share (a box score does not always carry its id)
                games[g_id] = {"id": g_id, "file": f[:-5], "date": date, "n0": n0, "n1": n1, "pts0": pts0, "pts1": pts1, "poss": poss, "h0": h0,
                               "o0": eff0 - h0, "o1": eff1 - h1,       # each side's points per 100, moved to a neutral floor
                               "home": n0 if h0 > 0 else n1 if h1 > 0 else None}
    visits.sort(key=lambda v: v["date"])
    if undated:
        print(f"   {undated} box scores have no date in game_scores.json and are left out")
    return visits, games, folders, paths

def rate(perfs, real, league_avg, count, today=None, prior=None):
    """Kenstat's rating passes over one set of games. perfs: (team, opponent, offense, defense, day number) with teams
    as numbers; real: which teams have enough games to be rated; today: the day being rated for (used by
    RATING_HALF_LIFE); prior: for each team, (offense, defense) above or below average from last season, or None
    (see Kenstat.RATING_PRIOR). Returns (offense, defense) lists."""
    adj_o, adj_d = [league_avg] * count, [league_avg] * count
    scale = RATING_LOPSIDED or Kenstat.LOPSIDED_SCALE
    rated = [i for i in range(count) if real[i]]
    if not rated:
        return adj_o, adj_d
    recency = [0.5 ** ((today - p[4]) / RATING_HALF_LIFE) if RATING_HALF_LIFE and today else 1.0 for p in perfs]
    for _ in range(ITERATIONS):
        temp_o, temp_d, temp_w = [0.0] * count, [0.0] * count, [0.0] * count
        for (t, o, raw_o, raw_d, _), recent in zip(perfs, recency):
            if not real[t]: continue
            opp_o, opp_d = adj_o[o], adj_d[o]        # an unrated opponent stays at the league average
            expected = (adj_o[t] - adj_d[t]) - (opp_o - opp_d)
            actual = raw_o - raw_d
            if expected < 0:
                expected, actual = -expected, -actual
            lopsided = max(0, min(expected, actual))
            weight = recent / (1 + (lopsided / scale) ** 2)
            temp_o[t] += weight * (raw_o - (opp_d - league_avg))
            temp_d[t] += weight * (raw_d - (opp_o - league_avg))
            temp_w[t] += weight
        for i in rated:
            if prior and prior[i]:
                temp_o[i] += Kenstat.PRIOR_GAMES * (league_avg + prior[i][0])
                temp_d[i] += Kenstat.PRIOR_GAMES * (league_avg + prior[i][1])
                temp_w[i] += Kenstat.PRIOR_GAMES
        for i in rated:
            if temp_w[i]:
                adj_o[i] = temp_o[i] / temp_w[i]
                adj_d[i] = temp_d[i] / temp_w[i]
        mean_o = sum(adj_o[i] for i in rated) / len(rated)
        mean_d = sum(adj_d[i] for i in rated) / len(rated)
        for i in rated:
            adj_o[i] += league_avg - mean_o
            adj_d[i] += league_avg - mean_d
    return adj_o, adj_d

# ---------------------------
# SHOTS AND PLAY TYPES, GAME BY GAME
# ---------------------------
def new_zones():
    return [[0, 0] for _ in Shotstat.ZONES]

def load_shot_games(root_folder, positions):
    """Team folder -> game file -> that game's shots from the team's side, still as raw tallies so they can be
    added up to any date: its play types and its opponents' ("plays_o", "plays_d"), shots by zone for and
    against ("o", "d": [attempts, makes] for each zone), free throws, assisted makes, and each player's shots
    by zone under the name the shot data uses for him."""
    big_share, handler_share = Shotstat.load_roles(root_folder, positions)
    shot_games = {}
    for conference in sorted(os.listdir(root_folder)):
        conf_path = os.path.join(root_folder, conference)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            shots_dir = os.path.join(conf_path, team, "shots")
            if not os.path.isdir(shots_dir): continue
            by_game = shot_games.setdefault(team.rstrip('. '), {})
            for f in os.listdir(shots_dir):
                if not f.endswith('.json'): continue
                game = read_json(os.path.join(shots_dir, f))
                if not game: continue
                if game.get("home_team", "").rstrip('. ') == team.rstrip('. '): my_side = 0
                elif game.get("away_team", "").rstrip('. ') == team.rstrip('. '): my_side = 1
                else: continue
                offense, defense = Shotstat.new_plays(), Shotstat.new_plays()
                spare = lambda: defaultdict(Shotstat.new_plays)
                Shotstat.count_plays(game, my_side, big_share, handler_share, offense, defense, spare(), spare(), spare(),
                                     (spare(), spare()), [], read_json(os.path.join(conf_path, team, "cbbd", f)))
                opponent = game.get("away_team" if my_side == 0 else "home_team", "").rstrip('. ')
                one = {"plays_o": offense, "plays_d": defense, "opponent": opponent, "o": new_zones(), "d": new_zones(), "ft": [0, 0], "a": [0, 0], "players": {}}
                for mine, player, zone, context, made, points, x, y, assisted, _, _ in Shotstat.read_game(game, my_side):
                    if zone is None:
                        if mine:
                            one["ft"][0] += 1
                            one["ft"][1] += made
                        continue
                    side = one["o"] if mine else one["d"]
                    side[zone][0] += 1
                    side[zone][1] += made
                    if mine:
                        own = one["players"].setdefault(player, new_zones())
                        own[zone][0] += 1
                        own[zone][1] += made
                        if made:
                            one["a"][0] += 1 if assisted else 0
                            one["a"][1] += 1
                by_game[f[:-5]] = one
    return shot_games

def play_points(mine, theirs, league, per_possession):
    """The dashboard's playMatchup(): points per possession an offense is expected to score against a defense, worked
    out from play types alone. mine / theirs: [plays, points] by play type, opponent-adjusted (the offense's own, and
    what the defense allows). per_possession: plays per possession, the offense's and the defense's against the
    D-I average."""
    if not mine or not theirs or not league or not per_possession:
        return None
    league_total = sum(row[0] for row in league)
    if not league_total: return None
    league_share = [row[0] / league_total for row in league]
    league_ppp = [row[1] / row[0] if row[0] else 1.0 for row in league]
    def profile(pt):
        total = sum(row[0] for row in pt) or 1
        plain = [(points + PLAY_SHRINK * league_ppp[i]) / (plays + PLAY_SHRINK) for i, (plays, points) in enumerate(pt)]
        if LEVEL_SHRINK is None or level_share <= 0:
            return [(plays / total, plain[i]) for i, (plays, _) in enumerate(pt)]
        usual = sum(plays * league_ppp[i] for i, (plays, _) in enumerate(pt))        # what an average team would score on this mix
        level = (sum(points for _, points in pt) + LEVEL_SHRINK) / (usual + LEVEL_SHRINK)
        early = [(points + LEVEL_TYPE_SHRINK * league_ppp[i] * level) / (plays + LEVEL_TYPE_SHRINK) for i, (plays, points) in enumerate(pt)]
        return [(plays / total, (1 - level_share) * plain[i] + level_share * early[i]) for i, (plays, _) in enumerate(pt)]
    m, t = profile(mine), profile(theirs)
    mix = [m[i][0] * t[i][0] / (league_share[i] or 1) for i in range(len(m))]
    mix_total = sum(mix) or 1
    return per_possession * sum(mix[i] / mix_total * (m[i][1] + t[i][1] - league_ppp[i]) for i in range(len(m)))

# ---------------------------
# THE REAL SPREADS
# ---------------------------
def load_market(games, folders):
    """The real spread for each game: game id -> {"spread": the line for our first team (n0; negative = favoured),
    "total", "type", "book"}. DraftKings' line is used wherever ESPN has one; the betting site's line fills in the rest."""
    site, _ = load_site_lines(games, folders)
    draftkings = (read_json(DRAFTKINGS_FILE) or {}).get("games", {})
    espn_id = {name.rstrip('. '): str(team_id) for name, team_id in (read_json(os.path.join(TEAMS_FOLDER, "espn_teams.json")) or {}).items()}
    lines = {}
    for g in games.values():
        old = site.get(g["id"])
        kind = old["type"] if old else ("Conference Tournament" if g["date"] >= Kenstat.NEUTRAL_FROM else "Regular Season")
        line = draftkings.get(g["file"])
        # ESPN's number is the line for the team IT lists as home, which is not always the one our schedule does,
        # so the line is tied to our teams by ESPN's team ids
        mine, other = espn_id.get(g["n0"].rstrip('. ')), espn_id.get(g["n1"].rstrip('. '))
        if line and line.get("spread") is not None and mine and other and {line.get("home_id"), line.get("away_id")} == {mine, other}:
            lines[g["id"]] = {"spread": line["spread"] if line["home_id"] == mine else -line["spread"], "total": line.get("total"), "type": kind, "book": "DraftKings"}
        elif old and old["spread"] is not None:
            lines[g["id"]] = {"spread": old["spread"], "total": old["total"], "type": kind, "book": "BetIQ"}
    return lines, "DraftKings (the line shown on ESPN's page for each game)"

def load_site_lines(games, folders):
    """Matches the betting site's games to ours. Its team names are spelled differently, so each of its names is
    tied to one of ours by the games themselves: same date, same score. Returns game id -> its row for our first
    team (n0), plus where the spreads came from."""
    market = read_json(MARKET_FILE)
    if not market:
        return {}, None
    by_score = defaultdict(list)        # (date, score as the row's team sees it) -> rows
    for row in market["rows"]:
        by_score[(row["date"].replace('-', '/'), row["score"])].append(row)
    votes = defaultdict(lambda: defaultdict(int))
    for g in games.values():
        for name, score in ((g["n0"], f"{g['pts0']}-{g['pts1']}"), (g["n1"], f"{g['pts1']}-{g['pts0']}")):
            for row in by_score.get((g["date"], score), []):
                votes[name.rstrip('. ')][row["team"]] += 1
    theirs = {}                          # our team -> the site's name for it
    for name, counts in votes.items():
        best = max(counts, key=counts.get)
        if name in folders and counts[best] >= 3:
            theirs[name] = best
    by_pair = {(row["date"].replace('-', '/'), row["team"], row["opp"]): row for row in market["rows"]}
    matched = {}
    for g in games.values():
        a, b = theirs.get(g["n0"].rstrip('. ')), theirs.get(g["n1"].rstrip('. '))
        if a and b and (g["date"], a, b) in by_pair:
            matched[g["id"]] = by_pair[(g["date"], a, b)]
    return matched, market.get("source")

# ---------------------------
# LAST SEASON, PLAYER BY PLAYER
# ---------------------------
def load_last_season(paths):
    """What each of this season's players did in 2024-25. Returns (team folder -> {player (as the box scores name him)
    -> (his 2024-25 box plus/minus, the share of his team's minutes he played)}, the value of an average first-year player).
    Players are followed from team to team by their Sports Reference id, which is in both seasons' roster files, so a
    transfer brings his numbers with him. A box plus/minus is points per 100 possessions better than an average
    player, measured against the whole of Division I, so it means the same thing whatever team it was earned on."""
    import re
    try:
        with open(LAST_SEASON_PAGE, 'r', encoding='utf-8') as open_f:
            last = json.loads(re.search(r"const DATA = (\{.*?\});\s*\n", open_f.read(), re.S).group(1))
    except Exception:
        return {}, 0.0
    # last season's players by team and name, then by the id on last season's roster
    by_name = defaultdict(dict)
    for p in last["players"]:
        by_name[p["team"].rstrip('. ')][Playerstat.norm_name(p["name"])] = p
    # on/off, steadied and put on the box plus/minus scale (see ONOFF_WEIGHT)
    steadied = lambda p: p["onoff"] * (p.get("poss") or 0) / ((p.get("poss") or 0) + ONOFF_STEADY)
    regulars = [p for p in last["players"] if p.get("onoff") is not None and p.get("bpm") is not None and (p.get("min") or 0) >= 200]
    def spread(values):
        mean = sum(values) / len(values)
        return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
    scale = spread([p["bpm"] for p in regulars]) / (spread([steadied(p) for p in regulars]) or 1) if regulars else 0.0
    def value(p):
        if ONOFF_WEIGHT and p.get("onoff") is not None:
            return (1 - ONOFF_WEIGHT) * p["bpm"] + ONOFF_WEIGHT * scale * steadied(p)
        return p["bpm"]
    first_years = [p for p in last["players"] if p.get("cls") == "Fr" and p.get("min")]
    newcomer = sum(value(p) * p["min"] for p in first_years) / sum(p["min"] for p in first_years) if first_years else 0.0
    by_id = {}
    for conference in os.listdir(LAST_SEASON_FOLDER):
        conf_path = os.path.join(LAST_SEASON_FOLDER, conference)
        if not os.path.isdir(conf_path): continue
        for team in os.listdir(conf_path):
            roster = read_json(os.path.join(conf_path, team, f"roster_{Kenstat.LAST_SEASON}.json"), {}).get("players", [])
            names = by_name.get(team.rstrip('. '), {})
            for listed in roster:
                key = Playerstat.match_name(listed["name"], names) if names else None
                if key and names[key].get("min"):
                    minutes = names[key]["min"]
                    # his value, and how much of the game he was on the floor for (0 to 1)
                    by_id[listed["id"]] = ((value(names[key]) * minutes + newcomer * HEAD_START_STEADY) / (minutes + HEAD_START_STEADY),
                                           (names[key].get("share") or 0) / 100)
    # this season's players, by the name the box scores use
    values = {}
    for folder, (real_name, team_path) in paths.items():
        roster = read_json(os.path.join(team_path, f"roster_{Kenstat.THIS_SEASON}.json"), {}).get("players", [])
        ids = {Playerstat.norm_name(listed["name"]): listed["id"] for listed in roster}
        values[folder] = {"ids": ids, "known": {key: by_id[i] for key, i in ids.items() if i in by_id}}
    return values, newcomer

def load_program():
    """Team folder -> (offense, defense): for each play type, the team's 2024-25 points per play over the D-I average
    on that kind of play (opponent-adjusted; pulled toward 1 as if PLAY_SHRINK more average plays had been run)."""
    import re
    try:
        with open(LAST_SEASON_PAGE, 'r', encoding='utf-8') as open_f:
            last = json.loads(re.search(r"const DATA = (\{.*?\});\s*\n", open_f.read(), re.S).group(1))
    except Exception:
        return {}
    teams = [t for t in last["teams"] if (t.get("shot") or {}).get("o", {}).get("pta")]
    count = len(Shotstat.PLAY_TYPES)
    league = []
    for i in range(count):
        plays = sum(t["shot"]["o"]["pt"][i][0] for t in teams)
        league.append(sum(t["shot"]["o"]["pt"][i][1] for t in teams) / plays if plays else 1.0)
    def ratios(rows):
        return [((rows[i][1] + PLAY_SHRINK * league[i]) / (rows[i][0] + PLAY_SHRINK)) / league[i] if league[i] else 1.0 for i in range(count)]
    return {t["name"].rstrip('. '): (ratios(t["shot"]["o"]["pta"]), ratios(t["shot"]["d"]["pta"])) for t in teams}

# ---------------------------
# ONE TEAM, AS IT STOOD ON A GIVEN DAY
# ---------------------------
class TeamSoFar:
    """Everything a team has done in the games played so far."""
    def __init__(self):
        self.tm, self.op = defaultdict(float), defaultdict(float)       # box score totals, the team's and its opponents'
        self.factors = defaultdict(float)                               # four-factor ingredients, as Kenstat adds them up
        self.players = {}                                               # player -> his box score totals
        self.zones = {}                                                 # player -> his shots by zone
        self.o, self.d = new_zones(), new_zones()                       # the team's shots by zone, and its opponents'
        self.ft, self.a = [0, 0], [0, 0]
        self.plays_o, self.plays_d = Shotstat.new_plays(), Shotstat.new_plays()
        self.done_o = self.done_d = None                                # [plays, points] by play type, as of now

    def add_box(self, box):
        Playerstat.add_line(self.tm, box["tm"])
        Playerstat.add_line(self.op, box["op"])
        self.tm['POSS'] += box["poss"]
        self.tm['G'] += 1
        for key, (starter, line) in box["lines"].items():
            player = self.players.setdefault(key, defaultdict(float))
            player['name'] = line['Name']
            Playerstat.add_line(player, line)
            player['MP'] += box["minutes"][key]
            player['G'] += 1
            self.tm['MP'] += box["minutes"][key]
        Kenstat.add_four_factors(self.factors, 'o_', box["tm"], box["op"], Playerstat.game_possessions(box["tm"]))
        Kenstat.add_four_factors(self.factors, 'd_', box["op"], box["tm"], Playerstat.game_possessions(box["op"]))

    def add_shots(self, shots, key_of):
        for mine, add in ((self.o, shots["o"]), (self.d, shots["d"])):
            for zone in range(len(mine)):
                mine[zone][0] += add[zone][0]
                mine[zone][1] += add[zone][1]
        for k in (0, 1):
            self.ft[k] += shots["ft"][k]
            self.a[k] += shots["a"][k]
        for name, zones in shots["players"].items():
            key = key_of(name)
            if not key: continue
            own = self.zones.setdefault(key, new_zones())
            for zone in range(len(own)):
                own[zone][0] += zones[zone][0]
                own[zone][1] += zones[zone][1]
        Shotstat.merge_plays(self.plays_o, shots["plays_o"])
        Shotstat.merge_plays(self.plays_d, shots["plays_d"])
        self.done_o, self.done_d = Shotstat.finish_plays(self.plays_o), Shotstat.finish_plays(self.plays_d)

    def four_factors(self):
        number = lambda v: v if isinstance(v, (int, float)) else None
        offense, defense = Kenstat.four_factors(self.factors, 'o_'), Kenstat.four_factors(self.factors, 'd_')
        return [number(offense[1]), number(offense[2]), number(offense[3]), number(defense[1]), number(defense[2]), number(defense[3])]

    def snapshot(self, offense, defense, tempo, style, played_today, listed):
        """What the simulator gets for this team: the team's numbers, then each player's (most minutes first), then the
        names of the useful players who did not play in the game about to be simulated."""
        if not self.tm['G'] or not self.tm['MP']:
            return None
        factors = self.four_factors()
        if any(v is None for v in factors):
            return None
        players = {k: p for k, p in self.players.items() if p['MP'] > 0}
        bpm, _ = Playerstat.box_plus_minus(players, self.tm, offense - defense, listed)
        twos = sum(z[0] for z in self.o[:3]) or 1
        threes = sum(z[0] for z in self.o[3:]) or 1
        rows, out = [], []
        for key in sorted(players, key=lambda k: -players[k]['MP'])[:MOST_PLAYERS]:
            p = players[key]
            zones = self.zones.get(key)
            if not zones or sum(z[0] for z in zones) < 0.5 * p['FGA']:
                # no shot locations for him: his twos and threes are spread over the floor the way the team's are
                zones = [[(p['FGA'] - p['3PA']) * z[0] / twos, (p['FGM'] - p['3PM']) * z[0] / twos] for z in self.o[:3]] + \
                        [[p['3PA'] * z[0] / threes, p['3PM'] * z[0] / threes] for z in self.o[3:]]
            here = 1 if (not played_today or key in played_today) else 0
            rows.append([int(p['G']), round(p['MP'], 1), round(bpm[key], 2)] + [round(z[0], 1) for z in zones] + [round(z[1], 1) for z in zones] +
                        [int(p['FTA']), int(p['FTM']), int(p['REB']), int(p['AST']), int(p['TO']), int(p['STL']), int(p['BLK']), here])
            if not here and p['MP'] / p['G'] >= USEFUL_MINUTES:
                out.append(p['name'])
        team = ([round(offense, 2), round(defense, 2), round(tempo, 2), round(style, 3)] + factors + [int(self.tm['G']), round(self.tm['MP'], 1)] +
                [z[0] for z in self.o] + [z[1] for z in self.o] + [z[0] for z in self.d] + [z[1] for z in self.d] + self.ft + self.a)
        return [team, rows, out]

# ---------------------------
# THE REPLAY
# ---------------------------
def build_report(root_folder=TEAMS_FOLDER):
    started = time.time()
    # Home court, as it could be known before the season: the usual edge and each team's own, measured on 2024-25.
    # It is set first, because the ratings neutralize every game with it.
    try:
        if HOME_COURT == "full":
            Kenstat.measure_home_court(root_folder, LAST_SEASON_FOLDER)
        else:
            Kenstat.measure_home_court(LAST_SEASON_FOLDER)
        last_tallies = Kenstat.home_court_tallies(LAST_SEASON_FOLDER, Kenstat.get_efficiency_ratings(LAST_SEASON_FOLDER, iterations=ITERATIONS)) if HOME_COURT == "decay" else {}
    except Exception as e:
        last_tallies = {}
        print(f"   home court could not be measured ({e}); using {Kenstat.HOME_ADV}")
    usual_edge, home_edge = Kenstat.HOME_ADV, dict(Kenstat.HOME_EDGES)
    print(f"   usual home edge measured on 2024-25: {usual_edge:.2f} per side per 100")
    program = load_program() if PROGRAM_GAMES else {}
    print("Reading the season's box scores...")
    visits, games, folders, paths = load_season(root_folder)
    names = sorted({v["n0"] for v in visits} | {v["n1"] for v in visits})
    number = {name: i for i, name in enumerate(names)}
    count = len(names)
    prior = [Kenstat.RATING_PRIOR.get(name.rstrip('. ')) for name in names] if Kenstat.RATING_PRIOR else None
    if prior:
        print(f"   last season's ratings count as {Kenstat.PRIOR_GAMES} rating entries for {sum(1 for p in prior if p)} teams")

    print("Team ratings and player positions (for the play types)...")
    final = Kenstat.get_efficiency_ratings(root_folder, iterations=ITERATIONS)
    final_by_folder = {name.rstrip(". "): stats for name, stats in final.items()}
    players = Playerstat.get_player_stats(root_folder, final_by_folder)[0]
    positions = {}
    for player in players:
        positions.setdefault(player["team"], {})[Playerstat.norm_name(player["name"])] = player["posn"]
    print("Each team's box scores and shots, game by game...")
    boxes, listed, shot_names = {}, {}, {}
    for folder, (real_name, team_path) in paths.items():
        _, _, season_players, by_game = Playerstat.load_team_boxscores(team_path, real_name)
        boxes[folder] = by_game
        roster = Playerstat.load_roster(team_path)
        roster_match = Playerstat.match_roster(season_players, roster)
        # each player's listed position (1 guard ... 5 center), which the box plus/minus leans on early in the season
        listed[folder] = {k: Playerstat.LISTED_POSITION.get((roster[r].get('pos') or '')[:1], 3.0) for k, r in roster_match.items() if r}
        known, cache = dict.fromkeys(season_players), {}
        def key_of(name, known=known, cache=cache):      # the shot data's name for a player -> ours
            if name not in cache:
                cache[name] = Playerstat.match_name(name, known) if known and name else None
            return cache[name]
        shot_names[folder] = key_of
    shot_games = load_shot_games(root_folder, positions)
    market, source = load_market(games, folders)
    last_season, newcomer = load_last_season(paths)
    print(f"   2024-25 numbers found for {sum(len(v['known']) for v in last_season.values())} of this season's players; a newcomer counts as {newcomer:+.2f}")
    print(f"   {len(games)} games, {len(market)} of them with a real spread")

    dates = sorted({g["date"] for g in games.values()})
    games_on = defaultdict(list)
    for g in games.values():
        games_on[g["date"]].append(g)

    # running totals, moved forward one game day at a time
    perfs = []                                   # every rating performance so far
    visit_count = [0] * count                    # Kenstat's own game count (a game between two of our teams counts twice)
    played = defaultdict(int)                    # team -> games played so far
    tempo_sum, tempo_n = [0.0] * count, [0] * count
    poss_sum = defaultdict(float)                # team -> possessions so far
    total_pts = total_poss = 0.0
    seen = set()
    so_far = defaultdict(TeamSoFar)              # team folder -> everything it has done so far
    raw_name = {name.rstrip('. '): name for name in names}      # team folder -> the name its box scores use
    play_logs = defaultdict(list)                # team folder -> its play types game by game, with the opponent
    game_logs = defaultdict(list)                # the same with each game's scoring both ways and its possessions, for weighing blowouts
    schedule = defaultdict(list)                 # team -> (opponent, the team's own home edge) for each game so far
    home_log = []                                # (home team, road team, the home team's margin per 100) for every game so far at a school's own arena
    at = 0
    rows, inputs, leagues, edges = [], [], [], []
    skipped_early = no_line = no_rating = no_data = before_start = 0

    for day, date in enumerate(dates):
        # 1. each of today's games, from everything before today
        today = [g for g in games_on[date] if g["n0"].rstrip('. ') in folders and g["n1"].rstrip('. ') in folders]
        if date < COMPARE_FROM:
            before_start += len(today)
            today = []
        ready = [g for g in today if min(played[g["n0"]], played[g["n1"]]) >= SKIP_FIRST_GAMES]
        skipped_early += len(today) - len(ready)
        if ready and total_poss:
            league_avg = total_pts / total_poss * 100
            real = [visit_count[i] >= 5 and names[i] not in Kenstat.BLACKLIST for i in range(count)]
            adj_o, adj_d = rate(perfs, real, league_avg, count, date_number(date), prior)
            rated = [i for i in range(count) if real[i] and tempo_n[i]]
            league_tempo = sum(tempo_sum[i] / tempo_n[i] for i in rated) / len(rated)
            # The 2024-25 head start. What a team of these players "should" be, from what each did last season, weighed
            # by the minutes he is playing now: its net rating is the sum of their box plus/minus, a newcomer counting as
            # an average first-year player. That is turned into a scoring level (half to the offense, half to the defense)
            # on the team's own mix of plays, and blended with what the team has really done. Its weight falls as the
            # team plays more games and as the calendar runs to HEAD_START_ENDS, and is smaller for a team whose
            # minutes mostly go to players with no Division I season behind them.
            span = max(1, date_number(HEAD_START_ENDS) - date_number(COMPARE_FROM))
            fade = max(0.0, min(1.0, (date_number(HEAD_START_ENDS) - date_number(date)) / span))
            global level_share
            level_share = fade
            def head_start(folder):                 # (net rating its players' numbers call for, share of minutes 2024-25 covers)
                team, known = so_far[folder], last_season.get(folder, {}).get("known", {})
                if not team.tm['MP'] or not known: return None
                # What each player has done so far THIS season. It stands in wherever last season has nothing to say:
                # for a freshman or anyone else with no 2024-25 numbers, and for the part of a player's minutes that is
                # new to him. (A role player on a great team who is now asked to carry one is only known in his old role.)
                index = number.get(raw_name.get(folder))
                own_net = adj_o[index] - adj_d[index] if index is not None and real[index] else 0.0
                playing = {k: p for k, p in team.players.items() if p['MP'] > 0}
                now, _ = Playerstat.box_plus_minus(playing, team.tm, own_net, listed[folder])
                net = covered = 0.0
                for key, p in playing.items():
                    share = p['MP'] / (team.tm['MP'] / 5)
                    so_far_value = (now[key] * p['MP'] + newcomer * HEAD_START_STEADY) / (p['MP'] + HEAD_START_STEADY)
                    last_value, last_share = known.get(key, (0.0, 0.0))
                    carried = min(share, last_share)              # the part of his minutes he also played last season
                    net += carried * last_value + (share - carried) * so_far_value
                    covered += carried / 5
                return net, covered, own_net
            head_starts = {folder: head_start(folder) for folder in list(so_far) if folder in folders} if fade > 0 else {}
            head_starts = {folder: found for folder, found in head_starts.items() if found}
            typical = sum(found[0] for found in head_starts.values()) / (len(head_starts) or 1)        # the average team's head start
            # Every team's points per play by play type, adjusted for the opponents it has faced so far.
            # PLAY_ADJUST "sos": by the team's strength of schedule, the same one the team ratings report: its points on
            # every kind of play are scaled by how the defenses it has faced compare with the average defense (and what it
            # allows, by the offenses it has faced). "category": play type by play type, against each opponent's own
            # number on that kind of play (Shotstat.adjust_plays).
            adjusted = Shotstat.adjust_plays(play_logs)[0] if PLAY_ADJUST == "category" else {}
            leans = {}
            def lean(folder):                       # (net rating last season points to, how many of the team's own games that counts like)
                if folder not in leans:
                    net = worth = 0.0
                    found = head_starts.get(folder) if fade > 0 else None
                    if found:                       # its players
                        players_net, covered, own_net = found
                        worth = HEAD_START_GAMES * fade * covered
                        net = worth * max(own_net - HEAD_START_CAP, min(own_net + HEAD_START_CAP, HEAD_START_STRETCH * (players_net - typical)))
                    leans[folder] = (net / worth, worth) if worth > 0 else None
                return leans[folder]
            def judged(o):                          # an opponent's offense and defense, with its head start blended in
                found = lean(names[o].rstrip('. ')) if HEAD_START_SCHEDULE and fade > 0 else None
                if not found: return adj_o[o], adj_d[o]
                net, worth = found
                weight = worth / (worth + played[names[o]])
                return (1 - weight) * adj_o[o] + weight * (league_avg + net / 2), (1 - weight) * adj_d[o] + weight * (league_avg - net / 2)
            def schedule_factors(name):             # (offense, defense) multipliers from the opponents faced so far
                faced = [(judged(o)[0] - edge, judged(o)[1] + edge) for o, edge in schedule[name] if real[o]]
                if not faced: return 1.0, 1.0
                return league_avg / (sum(f[1] for f in faced) / len(faced)), league_avg / (sum(f[0] for f in faced) / len(faced))
            weighed = {}
            def weighed_plays(folder, name):        # ([plays, points] by type on offense, the same on defense, possessions), blowouts counting for less
                if folder not in weighed:
                    own = [[0.0, 0.0] for _ in Shotstat.PLAY_TYPES]
                    theirs = [[0.0, 0.0] for _ in Shotstat.PLAY_TYPES]
                    possessions = 0.0
                    me = number.get(name)
                    for opponent, mine, allowed_plays, scored, gave_up, game_poss in game_logs.get(folder, []):
                        weight = 1.0
                        other = number.get(opponent)
                        if me is not None and other is not None and real[me] and real[other]:
                            expected = (adj_o[me] - adj_d[me]) - (adj_o[other] - adj_d[other])
                            actual = scored - gave_up
                            if expected < 0: expected, actual = -expected, -actual
                            weight = 1 / (1 + (max(0, min(expected, actual)) / Kenstat.LOPSIDED_SCALE) ** 2)
                        for i in range(len(own)):
                            own[i][0] += weight * mine[i][0]; own[i][1] += weight * mine[i][1]
                            theirs[i][0] += weight * allowed_plays[i][0]; theirs[i][1] += weight * allowed_plays[i][1]
                        possessions += weight * game_poss
                    weighed[folder] = (own, theirs, possessions)
                return weighed[folder]
            def adjusted_plays(folder, side, name=None):       # [plays, points] by type with the points adjusted, like "pta" on the dashboard
                done = so_far[folder].done_o if side == 0 else so_far[folder].done_d
                if not done: return done
                if PLAY_BLOWOUTS and game_logs.get(folder): done = weighed_plays(folder, name)[side]
                if PLAY_ADJUST == "sos":
                    factor = schedule_factors(name)[side]
                    return [[plays, points * factor] for plays, points in done]
                if folder not in adjusted: return done
                return [[plays, plays * adjusted[folder][side][i]] for i, (plays, _) in enumerate(done)]
            def with_head_start(folder, side, name):
                mine = adjusted_plays(folder, side, name)
                if not mine or fade <= 0: return mine
                # worth: how many of the team's own games each head start counts like
                net, worth = lean(folder) or (0.0, 0.0)             # its players' 2024-25 numbers: one level for every kind of play
                level = (league_avg + (net / 2 if side == 0 else -net / 2)) / league_avg
                ratios = program.get(folder)                        # the program's 2024-25 play types: a level for each kind of play
                program_worth = PROGRAM_GAMES * fade if ratios else 0.0
                total = played[name] + worth + program_worth
                if total <= played[name]: return mine
                return [[plays, (played[name] * points + worth * plays * type_ppp[i] * level
                                 + program_worth * plays * type_ppp[i] * (ratios[side][i] if ratios else 1.0)) / total]
                        for i, (plays, points) in enumerate(mine)]
            with_plays = [t.done_o for t in so_far.values() if t.done_o]
            league_plays = [[sum(pt[i][0] for pt in with_plays), sum(pt[i][1] for pt in with_plays)] for i in range(len(Shotstat.PLAY_TYPES))]
            type_ppp = [row[1] / row[0] if row[0] else 1.0 for row in league_plays]      # D-I points per play on each kind of play
            # the league as it stood: the averages every team is measured against
            every = [t.four_factors() for t in so_far.values() if t.tm['G']]
            every = [f for f in every if f[0] is not None and f[1] is not None and f[2] is not None]
            league = [round(league_avg, 3), round(league_tempo, 3)] + [round(sum(f[k] for f in every) / len(every), 3) for k in range(3)] + \
                     [sum(t.o[z][0] for t in so_far.values()) for z in range(5)] + [sum(t.o[z][1] for t in so_far.values()) for z in range(5)] + \
                     [sum(t.ft[k] for t in so_far.values()) for k in (0, 1)] + [sum(t.a[k] for t in so_far.values()) for k in (0, 1)]
            league_at = None
            if HOME_COURT == "decay":
                so_far_tallies = defaultdict(lambda: [0.0, 0, 0.0, 0])
                for h, r, margin in home_log:
                    if not (real[h] and real[r]): continue
                    expected = (adj_o[h] - adj_d[h]) - (adj_o[r] - adj_d[r])
                    over = margin - expected
                    expected, actual = expected + 2 * usual_edge, margin
                    if expected < 0: expected, actual = -expected, -actual
                    weight = 1 / (1 + (max(0, min(expected, actual)) / Kenstat.LOPSIDED_SCALE) ** 2)
                    th, tr = so_far_tallies[names[h].rstrip('. ')], so_far_tallies[names[r].rstrip('. ')]
                    th[0] += weight * over; th[1] += weight
                    tr[2] -= weight * over; tr[3] += weight
                pooled = Kenstat.pool_tallies(so_far_tallies, {team: [x * fade for x in tally] for team, tally in last_tallies.items()})
                usual_now = Kenstat.home_court_usual(pooled)
                edge_now = {team: Kenstat.home_court_edge(tally, usual_now) for team, tally in pooled.items()}
            else:
                usual_now, edge_now = usual_edge, home_edge
            for g in ready:
                # first team = the home team; on a neutral floor, the team the schedule lists as home
                first, second = (g["n1"], g["n0"]) if g["home"] == g["n1"] else (g["n0"], g["n1"])
                a, b = number[first], number[second]
                if not (real[a] and real[b]):
                    no_rating += 1
                    continue
                fa, fb = first.rstrip('. '), second.rstrip('. ')
                home = edge_now.get(fa, usual_now) if g["home"] else 0.0            # the home team's own edge (see HOME_COURT)
                rated_home = home
                ta, tb = so_far[fa], so_far[fb]
                def per_possession(t, name, side=0):        # plays per possession, the team's own (side 0) or what it allows (1)
                    folder = name.rstrip('. ')
                    if PLAY_BLOWOUTS and game_logs.get(folder):
                        own, theirs, possessions = weighed_plays(folder, name)
                        return sum(r[0] for r in (own, theirs)[side]) / possessions if possessions else 0
                    done = t.done_o if side == 0 else t.done_d
                    return sum(r[0] for r in done) / poss_sum[name] if done and poss_sum[name] else 0
                tempo_a, tempo_b = tempo_sum[a] / tempo_n[a], tempo_sum[b] / tempo_n[b]
                pace = tempo_a + tempo_b - league_tempo
                ratings_only = pace / 100 * ((adj_o[a] + adj_d[b] - league_avg + rated_home) - (adj_o[b] + adj_d[a] - league_avg - rated_home))
                # play types alone: no team ratings at all
                league_per = sum(r[0] for r in league_plays) / (sum(poss_sum[n] for n in poss_sum if n.rstrip('. ') in folders) or 1)
                allowed = lambda t, name: per_possession(t, name, 1)
                per_a = per_possession(ta, first) + allowed(tb, second) - league_per
                per_b = per_possession(tb, second) + allowed(ta, first) - league_per
                plain_a = play_points(adjusted_plays(fa, 0, first), adjusted_plays(fb, 1, second), league_plays, per_a)
                plain_b = play_points(adjusted_plays(fb, 0, second), adjusted_plays(fa, 1, first), league_plays, per_b)
                pts_a = play_points(with_head_start(fa, 0, first), with_head_start(fb, 1, second), league_plays, per_a)
                pts_b = play_points(with_head_start(fb, 0, second), with_head_start(fa, 1, first), league_plays, per_b)
                if not pts_a or not pts_b:
                    no_data += 1
                    continue
                # the simulator's spread with everyone available: play types alone, no team ratings
                formula = pace * (pts_a - pts_b + 2 * home / 100)
                style_a, style_b = 100 * pts_a, 100 * pts_b      # sent to the simulator: points per 100 each offense should score here
                if EXPLAIN and ({fa, fb} == set(EXPLAIN) or (fa, fb) in EXPLAIN):
                    print(f"EXPLAIN {date} {first} (first) v {second}: home edge {home}, pace {pace:.1f}")
                    for folder, name, index in ((fa, first, a), (fb, second, b)):
                        found = head_starts.get(folder)
                        factors = schedule_factors(name)
                        line = f"   {name}: games {played[name]}, own rating {adj_o[index]:.1f} / {adj_d[index]:.1f} (net {adj_o[index] - adj_d[index]:+.1f}), schedule factors off x{factors[0]:.3f} def x{factors[1]:.3f}"
                        if found:
                            worth = HEAD_START_GAMES * fade * found[1]
                            capped = max(found[2] - HEAD_START_CAP, min(found[2] + HEAD_START_CAP, HEAD_START_STRETCH * (found[0] - typical)))
                            line += f" | head start: players add up to {found[0]:+.1f} (average team {typical:+.1f}), stretched and capped {capped:+.1f}, covers {100 * found[1]:.0f}% of minutes, weight {worth / (worth + played[name]):.2f}"
                        print(line)
                    print(f"   points per 100: {first} {100 * pts_a:.1f} (this season only {100 * plain_a:.1f}), {second} {100 * pts_b:.1f} (this season only {100 * plain_b:.1f})")
                    print(f"   spread: {formula:+.1f} with head start, {pace * (plain_a - plain_b + 2 * home / 100):+.1f} this season only, {ratings_only:+.1f} team ratings")
                plain = pace * (plain_a - plain_b + 2 * home / 100) if plain_a and plain_b else formula      # the same without the 2024-25 head start
                line = market.get(g["id"])
                if not line or line["spread"] is None:
                    no_line += 1
                    continue
                who_played = lambda folder: set(boxes[folder].get(g["file"], {}).get("minutes", {}))
                block_a = ta.snapshot(adj_o[a], adj_d[a], tempo_a, style_a, who_played(fa), listed[fa])
                block_b = tb.snapshot(adj_o[b], adj_d[b], tempo_b, style_b, who_played(fb), listed[fb])
                if not block_a or not block_b:
                    no_data += 1
                    continue
                # the site's row is for our n0: a negative spread means that team was favoured
                market_margin = -line["spread"] if first == g["n0"] else line["spread"]
                actual = (g["pts0"] - g["pts1"]) if first == g["n0"] else (g["pts1"] - g["pts0"])
                if league_at is None:
                    league_at = len(leagues)
                    leagues.append(league)
                rows.append([date, first.strip(), second.strip(), 1 if g["home"] else 0, round(formula, 2), round(ratings_only, 2),
                             market_margin, actual, min(played[first], played[second]),
                             1 if folders[fa] == folders[fb] else 0, line["type"], line["total"], line["book"], round(plain, 2)])
                inputs.append([league_at, block_a, block_b])
                edges.append(round(home, 3))
        # 2. today's games join the record
        if FREEZE_FROM and date >= FREEZE_FROM:
            continue
        while at < len(visits) and visits[at]["date"] == date:
            v = visits[at]
            at += 1
            a, b = number[v["n0"]], number[v["n1"]]
            perfs.append((a, b, v["o0"], v["o1"], date_number(date)))
            perfs.append((b, a, v["o1"], v["o0"], date_number(date)))
            visit_count[a] += 1
            visit_count[b] += 1
            for i in (a, b):
                tempo_sum[i] += v["tempo"]
                tempo_n[i] += 1
            if v["id"] not in seen:
                seen.add(v["id"])
                total_pts += v["pts"]
                total_poss += v["poss_sum"]
                for name in (v["n0"], v["n1"]):
                    played[name] += 1
                    poss_sum[name] += v["poss"]
                edge = games[v["id"]]["h0"]         # the first team's home edge in this game (minus on the road, 0 neutral)
                if edge:
                    margin = v["o0"] - v["o1"] + 2 * edge       # back on the floor it was played on
                    home_log.append((a, b, margin) if edge > 0 else (b, a, -margin))
                schedule[v["n0"]].append((b, edge))
                schedule[v["n1"]].append((a, -edge))
        for g in games_on[date]:
            for name in (g["n0"].rstrip('. '), g["n1"].rstrip('. ')):
                if name not in folders: continue
                box = boxes[name].get(g["file"])
                if box:
                    so_far[name].add_box(box)
                shots = shot_games.get(name, {}).get(g["file"])
                if shots:
                    so_far[name].add_shots(shots, shot_names[name])
                    # one game has too few makes to say how its misses split among the play types, so the team's split so far is used
                    play_logs[name].append((shots["opponent"], Shotstat.finish_plays(shots["plays_o"], so_far[name].plays_o),
                                            Shotstat.finish_plays(shots["plays_d"], so_far[name].plays_d)))
                    first_side = name == g["n0"].rstrip('. ')
                    game_logs[name].append((g["n1"] if first_side else g["n0"], play_logs[name][-1][1], play_logs[name][-1][2],
                                            g["o0"] if first_side else g["o1"], g["o1"] if first_side else g["o0"], g["poss"]))
        if (day + 1) % 20 == 0:
            print(f"   {date}: {len(rows)} games so far", flush=True)

    # The same passes over the whole season must give the dashboard's own ratings: a check that this file reads
    # the season exactly as Kenstat does
    league_avg = total_pts / total_poss * 100
    real = [visit_count[i] >= 5 and names[i] not in Kenstat.BLACKLIST for i in range(count)]
    global RATING_LOPSIDED, RATING_HALF_LIFE
    own = RATING_LOPSIDED, RATING_HALF_LIFE          # (the check uses the dashboard's settings, whatever this run's are)
    RATING_LOPSIDED = RATING_HALF_LIFE = None
    adj_o, adj_d = rate(perfs, real, league_avg, count, prior=prior)
    RATING_LOPSIDED, RATING_HALF_LIFE = own
    worst = max((abs(adj_o[number[name]] - stats["o"]) + abs(adj_d[number[name]] - stats["d"]) for name, stats in final.items() if name in number), default=None)
    check = {"ratings_gap": round(worst, 3) if worst is not None else None}
    print(f"   check against the dashboard's ratings: largest gap {check['ratings_gap']} (should be about 0.01 or less)")

    report = {"built": time.strftime("%Y-%m-%d %H:%M"), "source": source, "skip": SKIP_FIRST_GAMES, "from": COMPARE_FROM, "head_start": {"program": PROGRAM_GAMES, "games": HEAD_START_GAMES, "ends": HEAD_START_ENDS, "newcomer": round(newcomer, 2), "stretch": HEAD_START_STRETCH, "cap": HEAD_START_CAP,
                             "players": sum(len(v["known"]) for v in last_season.values())}, "useful": USEFUL_MINUTES,
              "home": Kenstat.HOME_ADV, "home_measured": round(usual_edge, 2),
              "edges": edges,       # the home edge used in each game (0 on a neutral floor), per side per 100 possessions
              "counts": {"games": len([g for g in games.values() if g["n0"].rstrip('. ') in folders and g["n1"].rstrip('. ') in folders]),
                         "before": before_start, "early": skipped_early, "no_line": no_line, "other_book": sum(1 for r in rows if r[12] != "DraftKings"), "no_rating": no_rating, "no_data": no_data, "used": len(rows)},
              "check": check,
              "columns": ["date", "team", "opp", "home", "formula", "ratings", "market", "actual", "played", "conf", "type", "market_total", "book", "plain"],
              "rows": rows,
              # what the simulator needs to play each game: [which league line, first team, second team], where a team is
              # [its numbers, its players, the names of its useful players who sat out]
              # "plays": points per 100 possessions the team's offense should score against this opponent, from play types
              "team_columns": ["o", "d", "tempo", "plays", "tov", "orb", "ftr", "d_tov", "d_orb", "d_ftr", "games", "minutes",
                               "zone attempts x5", "zone makes x5", "allowed attempts x5", "allowed makes x5", "fta", "ftm", "assisted", "made"],
              "player_columns": ["games", "minutes", "bpm", "zone attempts x5", "zone makes x5", "fta", "ftm", "reb", "ast", "to", "stl", "blk", "played"],
              "league_columns": ["efficiency", "tempo", "tov", "orb", "ftr", "zone attempts x5", "zone makes x5", "fta", "ftm", "assisted", "made"],
              "leagues": leagues, "inputs": inputs}
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("window.SPREADS = " + json.dumps(report, separators=(",", ":")).replace("</", "<\\/") + ";\n")
    print(f"Saved {len(rows)} games to {REPORT_FILE} ({os.path.getsize(REPORT_FILE) / 1e6:.1f} MB) in {time.time() - started:.0f}s")
    return report

if __name__ == "__main__":
    report = build_report()
    rows = report["rows"]
    if rows:
        sat = sum(1 for _, a, b in report["inputs"] if a[2] or b[2])
        print(f"\nGames ready for the simulator: {len(rows)}  (left out: {report['counts']['before']} before {COMPARE_FROM}, {report['counts']['early']} with a team under {SKIP_FIRST_GAMES} games, {report['counts']['no_line']} with no real spread)")
        print(f"Games with at least one useful player out: {sat}")
        print("Open the dashboard's Spread report page and press the button to play them.")
