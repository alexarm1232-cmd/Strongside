import os
import re
import json
import math
from collections import defaultdict

BLACKLIST = ["Bryan", "Team Totals", "Undefined"]

# Home-court edge in points per 100 possessions, per side (home offense +1.6, home defense -1.6). This is only the
# starting value: measure_home_court() replaces it with the edge measured from the games (about 2.3), and fills
# HOME_EDGES with each team's own.
HOME_ADV = 1.6
HOME_EDGES = {}     # team (no trailing dots) -> its own home edge; a team not listed gets HOME_ADV

def home_edge(team):
    """The home edge used when this team is at home, per side per 100 possessions."""
    return HOME_EDGES.get(team.rstrip('. '), HOME_ADV)
# Each game in game_scores.json is marked neutral-site or not (8srboxscores.py fills that in from
# Sports Reference). For a game without the mark, this date is the fallback: games on/after it are
# conference tournaments and treated as neutral site.
NEUTRAL_FROM = "2026/03/09"

def is_neutral(game):
    """True when a game_scores.json entry was played on a neutral floor."""
    if 'neutral' in game:
        return bool(game['neutral'])
    return game['date'] >= NEUTRAL_FROM
# Blowout damping: a game that was expected to be lopsided AND was lopsided counts less.
# At a 20-per-100 runaway the game counts half; close games and upsets count in full.
# Smaller = more damping (below ~15 the ratings get unstable and predict worse).
LOPSIDED_SCALE = 20
# Strength of schedule: how much one game's margin (per 100 possessions) bounces around what the
# ratings predict. 16 per 100 is about 11 points a game; it turns a rating gap into a win chance.
SOS_SIGMA = 16

def load_home_teams(root_folder):
    """game_id -> home team name, for games played at a school's own arena."""
    home_teams = {}
    for root, dirs, files in os.walk(root_folder):
        if 'game_scores.json' in files:
            try:
                with open(os.path.join(root, 'game_scores.json'), 'r', encoding='utf-8') as open_f:
                    for g in json.load(open_f):
                        if not is_neutral(g):
                            home_teams[str(g['game_id'])] = g['home_team'].rstrip('. ')
            except: continue
    return home_teams

def parse_attempts(stat_str):
    try:
        if isinstance(stat_str, str) and '-' in stat_str:
            return int(stat_str.split('-')[1])
        return int(stat_str) if stat_str else 0
    except (IndexError, ValueError, AttributeError):
        return 0

def parse_made(stat_str):
    try:
        return int(stat_str.split('-')[0])
    except (IndexError, ValueError, AttributeError):
        return 0

def player_lines(tm):
    """One team's player lines for a game, without the feed's double entries: it sometimes lists the same
    stat line twice under two spellings of one name ('B Saragba' / 'Bessanty Saragba'). The longer name is kept."""
    lines = {}
    for p in tm['starters_table'] + tm['bench_table']:
        last_name = p['Name'].split()[-1].lower() if p['Name'].split() else ''
        signature = (last_name,) + tuple(str(p.get(k)) for k in ('MIN', 'PTS', 'FG', '3PT', 'FT', 'REB', 'AST', 'PF', 'TO', 'STL', 'BLK'))
        if float(p['MIN'] or 0) <= 0:
            signature += (p['Name'],)   # players who did not play all have the same empty line
        if signature not in lines or len(p['Name']) > len(lines[signature]['Name']):
            lines[signature] = p
    return list(lines.values())

def add_four_factors(totals, prefix, s, opp_s, poss):
    """Add one game's four-factor ingredients for the offense whose totals are s (opp_s = the defense)."""
    totals[prefix + 'fgm'] += parse_made(s['FG'])
    totals[prefix + 'fga'] += parse_attempts(s['FG'])
    totals[prefix + '3pm'] += parse_made(s['3PT'])
    totals[prefix + 'fta'] += parse_attempts(s['FT'])
    totals[prefix + 'to'] += s['TO']
    totals[prefix + 'poss'] += poss
    totals[prefix + 'or'] += s['OREB']
    totals[prefix + 'opp_dr'] += opp_s['REB'] - opp_s['OREB']   # the DREB field is not filled in
    # the rest of the box score, for the per-game numbers (the scatter page)
    totals[prefix + 'g'] += 1
    totals[prefix + '3pa'] += parse_attempts(s['3PT'])
    totals[prefix + 'ftm'] += parse_made(s['FT'])
    for key, field in (('pts', 'PTS'), ('reb', 'REB'), ('ast', 'AST'), ('stl', 'STL'), ('blk', 'BLK'), ('pf', 'PF')):
        try:
            totals[prefix + key] += float(s.get(field) or 0)
        except (TypeError, ValueError):
            pass

BOX_KEYS = ('pts', 'fgm', 'fga', '3pm', '3pa', 'ftm', 'fta', 'or', 'reb', 'ast', 'to', 'stl', 'blk', 'pf', 'poss', 'min', 'bpts', 'bmin')

def add_bench(totals, prefix, tm):
    """A side's minutes, and the points and minutes from its bench, for one game."""
    starters = {p['Name'] for p in tm['starters_table']}
    for p in player_lines(tm):
        try:
            minutes, points = float(p.get('MIN') or 0), float(p.get('PTS') or 0)
        except (TypeError, ValueError):
            continue
        totals[prefix + 'min'] += minutes
        if p['Name'] not in starters:
            totals[prefix + 'bmin'] += minutes
            totals[prefix + 'bpts'] += points

def box_per_game(totals, prefix):
    """A side's box score per game: 'o_' = the team's own, 'd_' = its opponents'."""
    games = totals[prefix + 'g']
    return {key: round(totals[prefix + key] / games, 2) for key in BOX_KEYS} if games else None

def four_factors(totals, prefix):
    pct = lambda num, den: round(100 * num / den, 1) if den else "--"
    return (pct(0.5 * totals[prefix + '3pm'] + totals[prefix + 'fgm'], totals[prefix + 'fga']),
            pct(totals[prefix + 'to'], totals[prefix + 'poss']),
            pct(totals[prefix + 'or'], totals[prefix + 'or'] + totals[prefix + 'opp_dr']),
            pct(totals[prefix + 'fta'], totals[prefix + 'fga']))

def win50_rating(opponent_nets):
    """Net rating of the team that would be expected to win exactly half its games against these opponents."""
    if not opponent_nets:
        return None
    low, high = -100.0, 100.0
    for _ in range(40):
        mid = (low + high) / 2
        expected_wins = sum(0.5 * (1 + math.erf((mid - net) / (SOS_SIGMA * math.sqrt(2)))) for net in opponent_nets)
        if expected_wins < len(opponent_nets) / 2:
            low = mid
        else:
            high = mid
    return round((low + high) / 2, 2)

def get_efficiency_ratings(root_folder, iterations=30):
    processed_ids = set()
    total_pts, total_poss = 0, 0
    all_game_performances = []
    game_counts = defaultdict(int)
    game_tempos = defaultdict(list)
    schedules = defaultdict(list)
    team_conf = {}
    factor_totals = defaultdict(lambda: defaultdict(float))
    home_teams = load_home_teams(root_folder)

    for root, dirs, files in os.walk(root_folder):
        if root.split(os.sep)[-1].lower() == 'boxscores':
            # Folders are <conference>/<team>/boxscores
            team_folder = os.path.dirname(root)
            team_conf[os.path.basename(team_folder).rstrip('. ')] = os.path.basename(os.path.dirname(team_folder))
            for f in files:
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as open_f:
                            data = json.load(open_f)
                            g_id = str(data.get('game_id') or f).strip()
                            t0, t1 = data['teams'][0], data['teams'][1]
                            n0, n1 = t0['team_name'], t1['team_name']

                            def get_raw_stats(tm):
                                s = tm['team_totals']
                                p = parse_attempts(s['FG']) - s['OREB'] + s['TO'] + (0.475 * parse_attempts(s['FT']))
                                return s['PTS'], p

                            pts0, poss0 = get_raw_stats(t0)
                            pts1, poss1 = get_raw_stats(t1)

                            # Both teams get the same possession count for the game (average of the two estimates)
                            poss = (poss0 + poss1) / 2
                            eff0, eff1 = pts0/poss*100, pts1/poss*100

                            # Tempo = possessions per 40 minutes. Overtime periods are read off the
                            # player minutes (200 team-minutes in regulation, +25 per overtime).
                            def get_team_minutes(tm):
                                return sum(float(p['MIN'] or 0) for p in player_lines(tm))

                            overtimes = max(0, round((max(get_team_minutes(t0), get_team_minutes(t1)) - 200) / 25))
                            tempo = poss * 40 / (40 + 5 * overtimes)
                            game_tempos[n0].append(tempo)
                            game_tempos[n1].append(tempo)

                            # Four factors: 'o_' = what the team did with the ball, 'd_' = what it allowed
                            s0, s1 = t0['team_totals'], t1['team_totals']
                            add_four_factors(factor_totals[n0], 'o_', s0, s1, poss0)
                            add_four_factors(factor_totals[n0], 'd_', s1, s0, poss1)
                            add_four_factors(factor_totals[n1], 'o_', s1, s0, poss1)
                            add_four_factors(factor_totals[n1], 'd_', s0, s1, poss0)
                            add_bench(factor_totals[n0], 'o_', t0)
                            add_bench(factor_totals[n0], 'd_', t1)
                            add_bench(factor_totals[n1], 'o_', t1)
                            add_bench(factor_totals[n1], 'd_', t0)

                            # Shift each side's scoring back to a neutral floor (0 = neutral site)
                            home = home_teams.get(f[:-5])
                            h0 = h1 = 0
                            if home == n0.rstrip('. '):
                                h0, h1 = home_edge(home), -home_edge(home)
                            elif home == n1.rstrip('. '):
                                h0, h1 = -home_edge(home), home_edge(home)

                            all_game_performances.append({'team': n0, 'opp': n1, 'raw_o': eff0 - h0, 'raw_d': eff1 - h1})
                            all_game_performances.append({'team': n1, 'opp': n0, 'raw_o': eff1 - h1, 'raw_d': eff0 - h0})
                            game_counts[n0] += 1
                            game_counts[n1] += 1

                            if g_id not in processed_ids:
                                processed_ids.add(g_id)
                                # (opponent, this team's home edge in that game: + at home, - on the road, 0 neutral)
                                schedules[n0].append((n1, h0))
                                schedules[n1].append((n0, h1))
                                total_pts += (pts0 + pts1)
                                total_poss += (poss0 + poss1)
                    except: continue

    league_avg = (total_pts / total_poss) * 100
    real_teams = {name for name, count in game_counts.items() if count >= 5 and name not in BLACKLIST}

    curr_adj_o = {name: league_avg for name in real_teams}
    curr_adj_d = {name: league_avg for name in real_teams}

    for i in range(iterations):
        temp_o, temp_d, temp_w = defaultdict(float), defaultdict(float), defaultdict(float)
        for game in all_game_performances:
            t, o = game['team'], game['opp']
            if t in real_teams:
                opp_o_adj = curr_adj_o.get(o, league_avg)
                opp_d_adj = curr_adj_d.get(o, league_avg)

                # Weight by how lopsided the game was expected to be AND actually was
                expected = (curr_adj_o[t] - curr_adj_d[t]) - (opp_o_adj - opp_d_adj)
                actual = game['raw_o'] - game['raw_d']
                if expected < 0:
                    expected, actual = -expected, -actual   # look at it from the favourite's side
                lopsided = max(0, min(expected, actual))
                weight = 1 / (1 + (lopsided / LOPSIDED_SCALE) ** 2)

                # Additive opponent adjustment: credit for how far the opponent is from average
                temp_o[t] += weight * (game['raw_o'] - (opp_d_adj - league_avg))
                temp_d[t] += weight * (game['raw_d'] - (opp_o_adj - league_avg))
                temp_w[t] += weight

        for name in real_teams:
            if temp_w[name]:
                curr_adj_o[name] = temp_o[name] / temp_w[name]
                curr_adj_d[name] = temp_d[name] / temp_w[name]

        # Re-centre on the league average so offense/defense can't drift apart between passes
        mean_o = sum(curr_adj_o.values()) / len(curr_adj_o)
        mean_d = sum(curr_adj_d.values()) / len(curr_adj_d)
        for name in real_teams:
            curr_adj_o[name] += league_avg - mean_o
            curr_adj_d[name] += league_avg - mean_d

    # Package into a dictionary for the dashboard
    stats_output = {}
    for name in real_teams:
        # Strength of schedule from the opponents' final ratings (non-conference = opponent from another conference)
        # Where the game was played counts: an opponent is tougher on its own floor and easier on yours
        opponents = [(curr_adj_o[o] - edge, curr_adj_d[o] + edge, o) for o, edge in schedules[name] if o in real_teams]
        non_conf = [g for g in opponents if team_conf.get(g[2].rstrip('. ')) != team_conf.get(name.rstrip('. '))]
        opp_net = lambda games: [opp_o - opp_d for opp_o, opp_d, _ in games]
        efg, tov, orb, ftr = four_factors(factor_totals[name], 'o_')
        d_efg, d_tov, d_orb, d_ftr = four_factors(factor_totals[name], 'd_')
        stats_output[name] = {
            "efg": efg, "tov": tov, "orb": orb, "ftr": ftr,
            "d_efg": d_efg, "d_tov": d_tov, "d_orb": d_orb, "d_ftr": d_ftr,
            "o": round(curr_adj_o[name], 2),
            "d": round(curr_adj_d[name], 2),
            "n": round(curr_adj_o[name] - curr_adj_d[name], 2),
            "t": round(sum(game_tempos[name]) / len(game_tempos[name]), 1),
            "sos": win50_rating(opp_net(opponents)),
            "sos_o": round(sum(g[0] for g in opponents) / len(opponents), 2) if opponents else None,
            "sos_d": round(sum(g[1] for g in opponents) / len(opponents), 2) if opponents else None,
            "ncsos": win50_rating(opp_net(non_conf)),
            "box": {"o": box_per_game(factor_totals[name], 'o_'), "d": box_per_game(factor_totals[name], 'd_')}
        }

    return stats_output

# ---------------------------
# HOME COURT, TEAM BY TEAM
# ---------------------------
# The ratings give every team the same home edge (HOME_ADV). This measures it from the games themselves: how much
# better each team does at home than on the road, against what the ratings expected each time.
#   at home a team beats expectations by its own edge;  on the road it falls short by the other team's edge.
# So (average at home - average on the road) / 2 is the team's own edge plus the usual one. Averaged over every team
# that is twice the usual edge (home_court_usual), and taking the usual edge away from a team's number leaves its own.
# Two things came out of measuring it on 2024-25 and 2025-26:
#   - the usual edge is about 2.3 per side per 100 possessions, well above the 1.6 the ratings started with. The
#     ratings and the simulators both use the measured one (measure_home_court).
#   - teams differ from each other far less than one season's numbers suggest. A team's number bounces by about 3 per
#     100 from luck alone, and barely carries over from one season to the next, so it is pulled nearly all the way
#     back to the usual edge: it counts as if HOME_COURT_PRIOR more games at the usual edge had been played.
# Seasons can be pooled, since the building does not move.
HOME_COURT_PRIOR = 270

def home_court_tallies(root_folder, ratings):
    """Team (no trailing dots) -> [sum of its home games' margins over expectation, home games, the same on the road,
    road games], in points per 100 possessions, neutral-site games left out.
    ratings: get_efficiency_ratings() for the same folder."""
    home_teams = load_home_teams(root_folder)
    net = {name.rstrip('. '): stats["o"] - stats["d"] for name, stats in ratings.items()}
    tallies = defaultdict(lambda: [0.0, 0, 0.0, 0])
    seen = set()
    for root, dirs, files in os.walk(root_folder):
        if root.split(os.sep)[-1].lower() != 'boxscores': continue
        for f in files:
            if not f.endswith('.json') or f in seen: continue
            home = home_teams.get(f[:-5])
            if not home: continue
            try:
                with open(os.path.join(root, f), 'r', encoding='utf-8') as open_f:
                    data = json.load(open_f)
                t0, t1 = data['teams'][0], data['teams'][1]
                names = [t0['team_name'].rstrip('. '), t1['team_name'].rstrip('. ')]
                if home not in names or names[0] not in net or names[1] not in net: continue
                def possessions(tm):
                    totals = tm['team_totals']
                    return parse_attempts(totals['FG']) - totals['OREB'] + totals['TO'] + 0.475 * parse_attempts(totals['FT'])
                poss = (possessions(t0) + possessions(t1)) / 2
                margin = (t0['team_totals']['PTS'] - t1['team_totals']['PTS']) / poss * 100     # the first team's, per 100
            except Exception:
                continue
            seen.add(f)
            if names[1] == home:
                names, margin = names[::-1], -margin
            over = margin - (net[names[0]] - net[names[1]])       # how far the home team beat expectations
            # A runaway counts less, exactly as it does in the ratings. Most runaways are a strong team at home, and
            # their extra margin is the mismatch, not the building: counted in full they make every home court look bigger.
            expected, actual = net[names[0]] - net[names[1]] + 2 * home_edge(names[0]), margin
            if expected < 0:
                expected, actual = -expected, -actual
            weight = 1 / (1 + (max(0, min(expected, actual)) / LOPSIDED_SCALE) ** 2)
            tallies[names[0]][0] += weight * over
            tallies[names[0]][1] += weight
            tallies[names[1]][2] -= weight * over
            tallies[names[1]][3] += weight
    return dict(tallies)

def pool_tallies(*seasons):
    """Several seasons' tallies added together."""
    pooled = defaultdict(lambda: [0.0, 0, 0.0, 0])
    for tallies in seasons:
        for team, tally in (tallies or {}).items():
            for k in range(4):
                pooled[team][k] += tally[k]
    return dict(pooled)

def home_court_usual(tallies):
    """The usual home edge, per side per 100 possessions like HOME_ADV, measured from the tallies."""
    both = [(t[0] / t[1] - t[2] / t[3]) / 2 for t in tallies.values() if t[1] >= 5 and t[3] >= 5]
    return sum(both) / len(both) / 2 if both else HOME_ADV

def home_court_edge(tally, usual):
    """A team's own home edge, per side per 100 possessions, from its tally and the usual edge."""
    home_sum, home_games, road_sum, road_games = tally
    if not home_games or not road_games:
        return usual
    raw = (home_sum / home_games - road_sum / road_games) / 2 - usual
    games = 2 * home_games * road_games / (home_games + road_games)       # as many games each way as the shorter side allows
    return usual + (raw - usual) * games / (games + HOME_COURT_PRIOR)

def measure_home_court(root_folder, before_folder=None, passes=3):
    """Measures home court from the games and puts it into the ratings: sets HOME_ADV to the usual edge and
    HOME_EDGES to each team's own, then returns the ratings worked out with them.
    The measuring needs ratings and the ratings need the edge, so the two are repeated a few times until they agree.
    before_folder: an earlier season to pool with (its games are measured once, with the edge as it stands)."""
    global HOME_ADV, HOME_EDGES
    earlier = None
    if before_folder and os.path.isdir(before_folder):
        earlier = home_court_tallies(before_folder, get_efficiency_ratings(before_folder, iterations=30))
    for _ in range(passes):
        tallies = pool_tallies(home_court_tallies(root_folder, get_efficiency_ratings(root_folder, iterations=30)), earlier)
        usual = home_court_usual(tallies)
        HOME_EDGES = {team: home_court_edge(tally, usual) for team, tally in tallies.items()}
        HOME_ADV = usual
    return get_efficiency_ratings(root_folder, iterations=30)

# ---------------------------
# ROSTER STATS (experience, continuity, height)
# ---------------------------
THIS_SEASON, LAST_SEASON = 2026, 2025
CLASS_YEARS = {"FR": 1, "SO": 2, "JR": 3, "SR": 4}
FIFTH_YEAR_YEARS = 5
MIN_SHARE = 0.10   # players under 10% of the available minutes don't count toward experience or height

def load_roster(team_path, season):
    try:
        with open(os.path.join(team_path, f"roster_{season}.json"), 'r', encoding='utf-8') as open_f:
            return json.load(open_f)['players']
    except: return []

def get_roster_stats(root_folder):
    """Team folder name -> minutes-weighted experience (years), continuity (%) and height (inches)."""
    roster_stats = {}
    for conference in os.listdir(root_folder):
        conf_path = os.path.join(root_folder, conference)
        if not os.path.isdir(conf_path): continue
        for team in os.listdir(conf_path):
            team_path = os.path.join(conf_path, team)
            players = load_roster(team_path, THIS_SEASON)
            team_minutes = sum(p['minutes'] for p in players)
            if not team_minutes: continue

            # Experience: class years weighted by minutes (five players share the floor, so 20% of all minutes = always on)
            exp_years, exp_minutes = 0, 0
            for p in players:
                if p['class'] in CLASS_YEARS and p['minutes'] / (team_minutes / 5) >= MIN_SHARE:
                    years = FIFTH_YEAR_YEARS if p.get('fifth_year') else CLASS_YEARS[p['class']]
                    exp_years += years * p['minutes']
                    exp_minutes += p['minutes']

            # Height: listed height weighted by minutes, same 10% cutoff as experience
            counted = [p for p in players if p['height_in'] and p['minutes'] / (team_minutes / 5) >= MIN_SHARE]
            ht_inches = sum(p['height_in'] * p['minutes'] for p in counted)
            ht_minutes = sum(p['minutes'] for p in counted)

            # Height by listed position. Rosters only say G, F or C, so it is guards vs frontcourt (forwards + centers).
            def position_height(letters):
                group = [p for p in counted if p['pos'][:1] in letters]
                minutes = sum(p['minutes'] for p in group)
                return round(sum(p['height_in'] * p['minutes'] for p in group) / minutes, 2) if minutes else None

            # Continuity: for each player, the smaller of his share of the team's minutes this season and last
            last_players = load_roster(team_path, LAST_SEASON)
            last_minutes = sum(p['minutes'] for p in last_players)
            last_share = {p['id']: p['minutes'] / last_minutes for p in last_players} if last_minutes else {}
            # a season from outside Division I (a team that moved up) has no Sports Reference ids, so its players are
            # matched by name instead
            by_name = lambda name: re.sub(r'[^a-z]', '', str(name).lower())
            last_by_name = {by_name(p['name']): p['minutes'] / last_minutes for p in last_players} if last_minutes else {}
            continuity = sum(min(p['minutes'] / team_minutes, last_share.get(p['id']) or last_by_name.get(by_name(p['name']), 0)) for p in players)

            roster_stats[team] = {
                "exp": round(exp_years / exp_minutes, 2) if exp_minutes else None,
                "cont": round(100 * continuity, 1) if last_minutes else None,
                "ht": round(ht_inches / ht_minutes, 2) if ht_minutes else None,
                "ht_g": position_height("G"),
                "ht_f": position_height("FC")
            }
    return roster_stats

if __name__ == "__main__":
    # Folder to search. It looks inside for a folder named "boxscores".
    ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seasons", "2526")

    results = get_efficiency_ratings(ROOT, iterations=30)

    print(f"\nTeams rated: {len(results)}\n")
    print(f"{'Rank':<5}{'Team':<30}{'Off':>8}{'Def':>8}{'Net':>8}")
    print("-" * 59)

    ranked = sorted(results.items(), key=lambda kv: kv[1]["n"], reverse=True)
    for i, (team, s) in enumerate(ranked, 1):
        print(f"{i:<5}{team:<30}{s['o']:>8}{s['d']:>8}{s['n']:>8}")
