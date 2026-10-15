import os
import re
import json
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

import Kenstat
from Kenstat import parse_attempts, parse_made, player_lines, is_neutral, THIS_SEASON

# Players under 10% of their team's available minutes for the season are never sent to the dashboard
# (same cutoff, measured the same way, as experience and height in Kenstat). The Players page has its
# own, higher minutes filter on top of this.
MIN_SHARE = 0.10
# On/off is shown for every player, however few possessions he sat. (Raise this to hide small samples:
# a number built on fewer than about 300 possessions off the floor is mostly luck.)
MIN_ONOFF_POSS = 1
# Reading every play-by-play file takes about a minute, so each team's on/off tallies are saved here
# and only worked out again when that team's box score or play-by-play files change.
ONOFF_VERSION = 11  # raise this when the on/off method changes, so saved tallies are worked out again
# Garbage time is judged by the lead AND the time left, not by a flat number: a 20-point lead with 15 minutes to
# play is still a game, a 13-point lead with 90 seconds left is not. A game counts as decided once the lead, less
# SAFE_LEAD_CUSHION points, squared, is more than the seconds left in regulation (Bill James's "safe lead" rule):
# 30 points with 12 minutes left, 25 with 8, 20 with under 5, 15 with under 2 and a half. The game simulator
# takes its rotations from the time before that, since afterwards benches empty.
SAFE_LEAD_CUSHION = 3
GARBAGE_MARGIN = 20     # only sent to the dashboard as a label; the rule above decides

def game_decided(lead, seconds_left):
    lead = abs(lead) - SAFE_LEAD_CUSHION
    return lead > 0 and lead * lead > seconds_left
ONOFF_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onoff_cache.json")
CLASS_LABELS = {"FR": ("Fr", 1), "SO": ("So", 2), "JR": ("Jr", 3), "SR": ("Sr", 4)}
# Listed position -> spot on the 1 (point guard) to 5 (center) scale. Rosters only say G, F or C.
LISTED_POSITION = {"G": 1.5, "F": 3.5, "C": 5.0}

# Share of free throw attempts that end a possession. Basketball Reference's page uses 0.4, an NBA figure;
# college uses 0.475 (KenPom's number, and the one the team ratings use). Everything else in the offensive
# and defensive rating follows the Basketball Reference page as written.
FT_WEIGHT = 0.475

BOX_STATS = ["PTS", "REB", "AST", "PF", "TO", "OREB", "STL", "BLK"]

# ---------------------------
# NAMES
# ---------------------------
def norm_name(name):
    """'Semetri (TT) Carr' / 'Kennard Davis Jr.' / 'Aleksej Kostić' -> comparable lowercase form."""
    name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    name = re.sub(r"\(.*?\)", " ", name)
    name = re.sub(r"[^a-z ]", "", name.replace("-", " "))
    words = [w for w in name.split() if w not in ("jr", "sr", "ii", "iii", "iv", "v", "ll", "lll")]   # "lll" = III typed with Ls
    return " ".join(words)

def norm_full(name):
    """norm_name without dropping Jr./III: only used to keep apart two teammates whose names differ by nothing else
    ('Marvin McGhee' and 'Marvin McGhee III')."""
    name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    name = re.sub(r"\(.*?\)", " ", name)
    return " ".join(re.sub(r"[^a-z ]", "", name.replace("-", " ")).split())

def match_name(name, candidates):
    """Find the same player in another list of names (candidates: normalized name -> anything)."""
    if norm_full(name) in candidates and norm_full(name) != norm_name(name):     # one of two teammates with the same name
        return norm_full(name)
    key = norm_name(name)
    if key in candidates:
        return key
    # Same words in another order ('Ibrahim Olajuwon' / 'Olajuwon Ibrahim'), or one source carries an extra
    # surname ('KyeRon Lindsay-Martin' / 'KyeRon Lindsay')
    words = set(key.split())
    overlap = [c for c in candidates if len(words & set(c.split())) >= 2 and (words <= set(c.split()) or set(c.split()) <= words)]
    if len(overlap) == 1:
        return overlap[0]
    last = key.split()[-1] if key else ""
    same_last = [c for c in candidates if c.split() and c.split()[-1] == last and c[:1] == key[:1]]
    if len(same_last) == 1:
        return same_last[0]
    best = max(candidates, key=lambda c: SequenceMatcher(None, key, c).ratio(), default=None)
    return best if best and SequenceMatcher(None, key, best).ratio() >= 0.82 else None

# ---------------------------
# BOX SCORE TOTALS
# ---------------------------
def game_possessions(s):
    """Same possession estimate the team ratings use."""
    return parse_attempts(s['FG']) - s['OREB'] + s['TO'] + (FT_WEIGHT * parse_attempts(s['FT']))

def add_line(totals, s):
    for stat in BOX_STATS:
        totals[stat] += s[stat]
    totals['FGM'] += parse_made(s['FG'])
    totals['FGA'] += parse_attempts(s['FG'])
    totals['3PM'] += parse_made(s['3PT'])
    totals['3PA'] += parse_attempts(s['3PT'])
    totals['FTM'] += parse_made(s['FT'])
    totals['FTA'] += parse_attempts(s['FT'])

def same_players(team_path, team_folder, players, games):
    """One player listed under two spellings ('Carl Daugherty' / 'Carl Daughtery', 'Des Watson' / 'Desmond Watson',
    'Boopie Miller' / 'Kevin Miller'): the spelling with fewer games -> the one with more. It happens when a few of a
    team's box scores come from another source than the rest. Two names are one player when they never appear in the
    same game and either the names match or the NCAA and Sports Reference versions of a box score give them the
    identical stat line."""
    played = {key: {g for g, game in games.items() if key in game["minutes"]} for key in players}
    paired = ncaa_aliases(team_path, team_folder, players)
    same = {}
    for a in sorted(players, key=lambda k: len(played[k])):
        for b in sorted(players, key=lambda k: -len(played[k])):
            if a == b or b in same or len(played[b]) < len(played[a]) or played[a] & played[b]: continue
            if paired.get(a) == b or paired.get(b) == a or match_name(players[a]['name'], {b: 1}) == b:
                same[a] = b
                break
    return same

def load_team_boxscores(team_path, team_folder, same=None):
    """Season totals for the team, its opponents and each player, plus what on/off needs from each game.
    same: spellings to fold into another (worked out on a first pass; see same_players)."""
    known = same or {}
    team, opp = defaultdict(float), defaultdict(float)
    # Two teammates with the same name apart from a Jr. or III, both playing in one game, are two people: each keeps
    # his full name as his key (otherwise their lines would be added together as one player)
    twins = set()
    players = {}
    games = {}
    box_dir = os.path.join(team_path, "boxscores")
    if not os.path.isdir(box_dir):
        return team, opp, players, games

    files = []
    for f in os.listdir(box_dir):
        if not f.endswith('.json'): continue
        try:
            with open(os.path.join(box_dir, f), 'r', encoding='utf-8') as open_f:
                files.append((f, json.load(open_f)))
        except: continue
    for f, data in files:
        for t in data.get('teams', []):
            if t.get('team_name', '').rstrip('. ') != team_folder.rstrip('. '): continue
            spelled = defaultdict(set)
            for p in player_lines(t):
                if float(p['MIN'] or 0) > 0:
                    spelled[norm_name(p['Name'])].add(norm_full(p['Name']))
            twins |= {k for k, full in spelled.items() if len(full) > 1}
    for f, data in files:
        try:
            mine = [t for t in data['teams'] if t['team_name'].rstrip('. ') == team_folder.rstrip('. ')]
            if len(mine) != 1 or len(data['teams']) != 2: continue
            mine = mine[0]
            other = next(t for t in data['teams'] if t is not mine)

            add_line(team, mine['team_totals'])
            add_line(opp, other['team_totals'])
            # Both teams get the same possession count for the game, like the team ratings
            poss = (game_possessions(mine['team_totals']) + game_possessions(other['team_totals'])) / 2
            team['POSS'] += poss
            team['G'] += 1

            minutes = {}
            lines = {}   # this game's stat line for each player, for the game logs
            name_key = lambda p: norm_full(p['Name']) if norm_name(p['Name']) in twins else norm_name(p['Name'])
            starters = {known.get(name_key(p), name_key(p)) for p in mine['starters_table']}
            for p in player_lines(mine):
                mp = float(p['MIN'] or 0)
                if mp <= 0: continue
                spelled = name_key(p)
                key = known.get(spelled, spelled)
                if key in minutes: continue   # the feed sometimes lists one stat line twice under two names
                minutes[key] = mp
                lines[key] = (key in starters, p)
                line = players.setdefault(key, defaultdict(float))
                if spelled == key or 'name' not in line:
                    line['name'] = p['Name']
                add_line(line, p)
                line['MP'] += mp
                line['G'] += 1
                line['GS'] += key in starters
                team['MP'] += mp
            games[f[:-5]] = {"poss": poss, "minutes": minutes, "lines": lines, "team_name": mine['team_name'],
                             "tm": mine['team_totals'], "op": other['team_totals'],
                             "opp": other['team_name'], "pts": mine['team_totals']['PTS'], "opp_pts": other['team_totals']['PTS']}
        except: continue
    if same is None:
        found = same_players(team_path, team_folder, players, games)
        if found:
            return load_team_boxscores(team_path, team_folder, found)
    return team, opp, players, games

# ---------------------------
# OFFENSIVE / DEFENSIVE RATING (Dean Oliver, as laid out by Basketball Reference)
# ---------------------------
def div(a, b):
    return a / b if b else 0.0

def offensive_rating(p, tm, opp):
    """Returns (points produced per 100 possessions the player used, how many possessions he used)."""
    mp_share = div(p['MP'], tm['MP'] / 5)
    tm_ft_part = (1 - (1 - div(tm['FTM'], tm['FTA'])) ** 2) * tm['FTA'] * FT_WEIGHT
    tm_scoring_poss = tm['FGM'] + tm_ft_part
    tm_orb_pct = div(tm['OREB'], tm['OREB'] + (opp['REB'] - opp['OREB']))
    tm_play_pct = div(tm_scoring_poss, tm['FGA'] + tm['FTA'] * FT_WEIGHT + tm['TO'])
    tm_orb_weight = div((1 - tm_orb_pct) * tm_play_pct, (1 - tm_orb_pct) * tm_play_pct + tm_orb_pct * (1 - tm_play_pct))

    q_ast = (mp_share * (1.14 * div(tm['AST'] - p['AST'], tm['FGM']))
             + div(div(tm['AST'], tm['MP']) * p['MP'] * 5 - p['AST'], div(tm['FGM'], tm['MP']) * p['MP'] * 5 - p['FGM']) * (1 - mp_share))
    fg_share = 1 - 0.5 * div(p['PTS'] - p['FTM'], 2 * p['FGA']) * q_ast
    others_eff = div((tm['PTS'] - tm['FTM']) - (p['PTS'] - p['FTM']), 2 * (tm['FGA'] - p['FGA']))
    orb_credit = 1 - div(tm['OREB'], tm_scoring_poss) * tm_orb_weight * tm_play_pct

    fg_part = p['FGM'] * fg_share
    ast_part = 0.5 * others_eff * p['AST']
    ft_part = (1 - (1 - div(p['FTM'], p['FTA'])) ** 2) * FT_WEIGHT * p['FTA']
    orb_part = p['OREB'] * tm_orb_weight * tm_play_pct
    scoring_poss = (fg_part + ast_part + ft_part) * orb_credit + orb_part

    missed_fg_poss = (p['FGA'] - p['FGM']) * (1 - 1.07 * tm_orb_pct)
    missed_ft_poss = ((1 - div(p['FTM'], p['FTA'])) ** 2) * FT_WEIGHT * p['FTA']
    total_poss = scoring_poss + missed_fg_poss + missed_ft_poss + p['TO']

    pprod_fg = 2 * (p['FGM'] + 0.5 * p['3PM']) * fg_share
    pprod_ast = 2 * div(tm['FGM'] - p['FGM'] + 0.5 * (tm['3PM'] - p['3PM']), tm['FGM'] - p['FGM']) * 0.5 * others_eff * p['AST']
    pprod_orb = p['OREB'] * tm_orb_weight * tm_play_pct * div(tm['PTS'], tm_scoring_poss)
    points_produced = (pprod_fg + pprod_ast + p['FTM']) * orb_credit + pprod_orb

    return (100 * points_produced / total_poss if total_poss > 0 else None), total_poss

def defensive_rating(p, tm, opp):
    """Points allowed per 100 possessions the player faced."""
    tm_drb = tm['REB'] - tm['OREB']   # the DREB field is not filled in
    p_drb = p['REB'] - p['OREB']
    dor_pct = div(opp['OREB'], opp['OREB'] + tm_drb)
    dfg_pct = div(opp['FGM'], opp['FGA'])
    fm_weight = div(dfg_pct * (1 - dor_pct), dfg_pct * (1 - dor_pct) + (1 - dfg_pct) * dor_pct)

    stops1 = p['STL'] + p['BLK'] * fm_weight * (1 - 1.07 * dor_pct) + p_drb * (1 - fm_weight)
    stops2 = ((div(opp['FGA'] - opp['FGM'] - tm['BLK'], tm['MP']) * fm_weight * (1 - 1.07 * dor_pct)
               + div(opp['TO'] - tm['STL'], tm['MP'])) * p['MP']
              + div(p['PF'], tm['PF']) * FT_WEIGHT * opp['FTA'] * (1 - div(opp['FTM'], opp['FTA'])) ** 2)
    stop_pct = div((stops1 + stops2) * tm['MP'], tm['POSS'] * p['MP'])   # opponent minutes = team minutes

    team_drtg = 100 * div(opp['PTS'], tm['POSS'])
    d_pts_per_scoring_poss = div(opp['PTS'], opp['FGM'] + (1 - (1 - div(opp['FTM'], opp['FTA'])) ** 2) * opp['FTA'] * FT_WEIGHT)
    return team_drtg + 0.2 * (100 * d_pts_per_scoring_poss * (1 - stop_pct) - team_drtg)

# ---------------------------
# BOX PLUS/MINUS 2.0 (Daniel Myers, as laid out by Basketball Reference)
# ---------------------------
#                 position 1 (PG)   position 5 (C)
BPM_BY_POSITION = {
    "AST":  (0.580, 1.034),
    "ORB":  (0.613, 0.181),
    "DRB":  (0.116, 0.181),
    "STL":  (1.369, 1.008),
    "BLK":  (1.327, 0.703),
}
BPM_PTS, BPM_3PM, BPM_TO, BPM_PF = 0.860, 0.389, -0.964, -0.367
#          role 1 (creator)  role 5 (receiver)
BPM_FGA = (-0.560, -0.780)
BPM_FTA = (-0.246, -0.343)
BPM_POSITION_CONSTANT = -0.818   # at position 1, fading to 0 at position 3 and above
BPM_ROLE_CONSTANT = 2.774        # -2.774 at role 1, 0 at role 3, +2.774 at role 5
BPM_PRIOR_MINUTES = 50           # each estimate is blended with 50 minutes of a default value

def between(low_high, spot):
    """Coefficient for a player at `spot` on the 1-5 scale."""
    return low_high[0] + (spot - 1) / 4 * (low_high[1] - low_high[0])

def centre_on_three(values, minutes):
    """Shift a team's position (or role) numbers so the minutes-weighted average is 3, keeping each within 1-5."""
    total = sum(minutes.values())
    shift = 0.0
    for _ in range(50):
        clamped = {k: min(5.0, max(1.0, v + shift)) for k, v in values.items()}
        shift += 3.0 - sum(clamped[k] * minutes[k] for k in clamped) / total
    return {k: min(5.0, max(1.0, v + shift)) for k, v in values.items()}

def box_plus_minus(players, tm, team_net, listed_positions):
    """Returns (player key -> BPM, player key -> position on the 1 (point guard) to 5 (center) scale, estimated from his box score).
    team_net is the team's adjusted net rating; the players' BPMs add up to it."""
    minutes = {k: p['MP'] for k, p in players.items()}
    tsa = lambda s: s['FGA'] + 0.44 * s['FTA']
    tm_pts_per_tsa = div(tm['PTS'], tsa(tm))
    tm_threshold_pts = 0.33 * tsa(tm)   # team points above (team efficiency - 0.33) per shot attempt

    positions, roles = {}, {}
    for k, p in players.items():
        on_floor = div(p['MP'], tm['MP'] / 5)   # share of the game the player is out there
        pct = lambda stat, team_stat: div(stat, team_stat * on_floor)
        position = (2.130 + 8.668 * pct(p['REB'], tm['REB']) - 2.486 * pct(p['STL'], tm['STL']) + 0.992 * pct(p['PF'], tm['PF'])
                    - 3.536 * pct(p['AST'], tm['AST']) + 1.667 * pct(p['BLK'], tm['BLK']))
        positions[k] = (position * p['MP'] + listed_positions.get(k, 3.0) * BPM_PRIOR_MINUTES) / (p['MP'] + BPM_PRIOR_MINUTES)
        threshold_pts = p['PTS'] - tsa(p) * (tm_pts_per_tsa - 0.33)
        role = 6.00 - 6.642 * pct(p['AST'], tm['AST']) - 8.544 * pct(threshold_pts, tm_threshold_pts)
        roles[k] = (role * p['MP'] + 4.0 * BPM_PRIOR_MINUTES) / (p['MP'] + BPM_PRIOR_MINUTES)
    positions = centre_on_three(positions, minutes)
    roles = centre_on_three(roles, minutes)

    raw = {}
    for k, p in players.items():
        per100 = lambda stat: 100 * div(stat, tm['POSS'] * div(p['MP'], tm['MP'] / 5))
        pos, role = positions[k], roles[k]
        # Points are judged against one point per shot attempt, after taking out how well the whole team shoots
        adjusted_pts = p['PTS'] - tsa(p) * (tm_pts_per_tsa - 1.0)
        total = (BPM_PTS * per100(adjusted_pts) + BPM_3PM * per100(p['3PM']) + BPM_TO * per100(p['TO']) + BPM_PF * per100(p['PF'])
                 + between(BPM_BY_POSITION["AST"], pos) * per100(p['AST'])
                 + between(BPM_BY_POSITION["ORB"], pos) * per100(p['OREB'])
                 + between(BPM_BY_POSITION["DRB"], pos) * per100(p['REB'] - p['OREB'])
                 + between(BPM_BY_POSITION["STL"], pos) * per100(p['STL'])
                 + between(BPM_BY_POSITION["BLK"], pos) * per100(p['BLK'])
                 + between(BPM_FGA, role) * per100(p['FGA'])
                 + between(BPM_FTA, role) * per100(p['FTA']))
        total += max(0.0, 3 - pos) * (BPM_POSITION_CONSTANT / 2)
        total += (role - 3) * (BPM_ROLE_CONSTANT / 2)
        raw[k] = total

    # Team adjustment: one constant for the whole team so that five players' worth of BPM equals the team's net rating
    adjustment = team_net / 5 - sum(raw[k] * minutes[k] for k in raw) / sum(minutes.values())
    return {k: v + adjustment for k, v in raw.items()}, positions

# ---------------------------
# ON/OFF (from play-by-play)
# ---------------------------
def sub_name(text, team_name):
    """'Subbing in for BYU-Khadim Mboup' -> ('in', 'Khadim Mboup')."""
    m = re.match(r"Subbing (in|out) for (.*)$", text)
    if not m: return None
    rest = m.group(2)
    name = rest[len(team_name) + 1:] if rest.startswith(team_name + "-") else rest.partition("-")[2]
    # the feed has the odd "Subbing in for <team>-Team" row; that is nobody
    return (m.group(1), name) if norm_name(name) not in ("", "team") else None

def ncaa_aliases(team_path, team_folder, players):
    """NCAA spelling of a player's name -> his box score key, for players the two sources name differently.
    The play-by-play uses NCAA names ('Boopie Miller'); the box scores now carry Sports Reference names
    ('Kevin Miller'). The NCAA copy of each box score is kept in boxscores_ncaa, so the two spellings
    are paired game by game through the identical stat line."""
    votes = defaultdict(lambda: defaultdict(int))
    backup_dir = os.path.join(team_path, "boxscores_ncaa")
    if not os.path.isdir(backup_dir):
        return {}
    line_of = lambda p: (p['PTS'], p['FG'], p['3PT'], p['FT'], p['REB'], p['AST'], p['PF'], p['TO'])
    for f in os.listdir(backup_dir):
        try:
            with open(os.path.join(backup_dir, f), 'r', encoding='utf-8') as open_f:
                old = json.load(open_f)
            with open(os.path.join(team_path, "boxscores", f), 'r', encoding='utf-8') as open_f:
                new = json.load(open_f)
            pick = lambda data: next(t for t in data['teams'] if t['team_name'].rstrip('. ') == team_folder.rstrip('. '))
            old_lines, new_lines = defaultdict(list), defaultdict(list)
            for p in player_lines(pick(old)):
                if float(p['MIN'] or 0) > 0: old_lines[line_of(p)].append(p['Name'])
            for p in player_lines(pick(new)):
                if float(p['MIN'] or 0) > 0: new_lines[line_of(p)].append(p['Name'])
            for line, names in old_lines.items():
                # only a stat line that one player on each side has can pair two names
                if len(names) == 1 and len(new_lines.get(line, [])) == 1:
                    votes[norm_name(names[0])][norm_name(new_lines[line][0])] += 1
        except: continue
    aliases = {}
    for ncaa_name, choices in votes.items():
        best = max(choices, key=choices.get)
        if ncaa_name != best and best in players and choices[best] >= 2:
            aliases[ncaa_name] = best
    return aliases

def team_on_off(team_path, games, players, aliases=None):
    """Returns (tally, by_game, lineups).
    lineups: "game id>the five on the floor (names joined by '|')" -> [possessions, points for, points against,
    then the same three counting only time when the score was within GARBAGE_MARGIN points].
    tally: normalized player name -> season points for/against and possessions with him on the floor and off it.
    by_game: game id -> the same three numbers [for, against, possessions] for the team and for each player while on."""
    aliases = aliases or {}
    pbp_dir = os.path.join(team_path, "playbyplay")
    tally = defaultdict(lambda: defaultdict(float))
    by_game = {}
    lineups = {}
    if not os.path.isdir(pbp_dir):
        return tally, by_game, lineups

    loaded = []
    names = {}   # player key -> the spellings seen in the play-by-play
    known = {}
    def key_of(name):
        """The box score's key for this player when he can be matched, so every spelling lands on one player."""
        if name not in known:
            known[name] = aliases.get(norm_name(name)) or match_name(name, players) or norm_name(name)
        return known[name]
    for game_id, game in games.items():
        try:
            with open(os.path.join(pbp_dir, game_id + ".json"), 'r', encoding='utf-8') as open_f:
                data = json.load(open_f)
        except: continue
        team_name = game["team_name"]
        if team_name == data.get("home_team"): at_home = True
        elif team_name == data.get("away_team"): at_home = False
        else: continue
        for p in data["plays"]:
            if p["team"] == team_name:
                sub = sub_name(p["text"], team_name)
                if sub and sub[1]:
                    names.setdefault(key_of(sub[1]), set()).add(sub[1])
        loaded.append((game_id, game, data, at_home))

    # Anyone named in a play is on the floor, so look for every spelling of every player (box score names too)
    for key, line in players.items():
        names.setdefault(key, set()).add(line['name'])
    spelling_to_key = {s: k for k, spellings in names.items() for s in spellings}
    if not spelling_to_key:
        return tally, by_game, lineups
    finder = re.compile(r"(?<![A-Za-z])(" + "|".join(re.escape(s) for s in sorted(spelling_to_key, key=len, reverse=True)) + r")(?![A-Za-z])")

    for game_id, game, data, at_home in loaded:
        team_name = game["team_name"]
        mine, theirs = ("home_score", "away_score") if at_home else ("away_score", "home_score")
        box_minutes = game["minutes"]

        periods = defaultdict(list)
        for p in data["plays"]:
            periods[p["period"]].append(p)
        total_seconds = sum(1200 if n <= 2 else 300 for n in periods)
        if not total_seconds: continue
        poss_per_second = game["poss"] / total_seconds
        game_team, game_on = [0.0, 0.0, 0.0], {}
        stints = []     # [period, seconds left, the five on the floor from then on] each time the lineup changes

        lineup, score = set(), [0, 0]
        for number in sorted(periods):
            rows = periods[number]
            # Who was on the floor when the period started: anyone whose first substitution this period
            # is checking OUT, plus anyone who is named in a play and never substituted at all.
            # (Plays alone can't decide it for the others: rows that share a clock time are not always in order.)
            first = {}
            for p in rows:
                sub = sub_name(p["text"], team_name) if p["team"] == team_name else None
                if sub:
                    first.setdefault(key_of(sub[1]), sub[0])
            for p in rows:
                if not p["text"].startswith("Subbing"):
                    for spelling in finder.findall(p["text"]):
                        first.setdefault(spelling_to_key[spelling], "play")
            start = {k for k, what in first.items() if what != "in"}
            if len(start) < 5:
                # Fill the gap with players who went the whole period without showing up in a play:
                # first those who finished the last period on the floor, then by minutes played in this game.
                quiet = sorted((k for k in box_minutes if k not in first),
                               key=lambda k: (k in lineup, box_minutes[k]), reverse=True)
                start |= set(quiet[:5 - len(start)])
            lineup = start

            clock = 1200 if number <= 2 else 300
            stints.append([number, clock, sorted(lineup) if len(lineup) == 5 else []])
            i = 0
            while i < len(rows):
                j = i
                while j < len(rows) and rows[j]["clock"] == rows[i]["clock"]:
                    j += 1
                group = rows[i:j]
                i = j
                seconds_left = group[0].get("seconds_left")
                game_left = clock + (1200 if number == 1 else 0)     # seconds left in regulation (or the overtime) as this stretch began
                elapsed = max(0, clock - seconds_left) if seconds_left is not None else 0
                clock = min(clock, seconds_left) if seconds_left is not None else clock
                # Points in this moment go to the five who were on the floor before any substitutions in it
                new_mine = max([score[0]] + [p[mine] or 0 for p in group])
                new_theirs = max([score[1]] + [p[theirs] or 0 for p in group])
                if len(lineup) == 5:
                    moment = (new_mine - score[0], new_theirs - score[1], elapsed * poss_per_second)
                    for n in range(3):
                        game_team[n] += moment[n]
                    for key in lineup:
                        on = game_on.setdefault(key, [0.0, 0.0, 0.0])
                        for n in range(3):
                            on[n] += moment[n]
                    five = lineups.setdefault(game_id + ">" + "|".join(sorted(lineup)), [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                    five[0] += moment[2]
                    five[1] += moment[0]
                    five[2] += moment[1]
                    if not game_decided(score[0] - score[1], game_left):   # the same three again, for time before the game was decided
                        five[3] += moment[2]
                        five[4] += moment[0]
                        five[5] += moment[1]
                    tally["__team__"]["tracked"] += elapsed
                tally["__team__"]["seconds"] += elapsed
                score = [new_mine, new_theirs]
                changed = False
                for p in group:
                    sub = sub_name(p["text"], team_name) if p["team"] == team_name else None
                    if sub:
                        (lineup.add if sub[0] == "in" else lineup.discard)(key_of(sub[1]))
                        changed = True
                if changed:
                    stints.append([number, clock, sorted(lineup) if len(lineup) == 5 else []])
        by_game[game_id] = {"team": [round(v, 3) for v in game_team], "on": {k: [round(v, 3) for v in on] for k, on in game_on.items()},
                            "stints": stints}

    # Season totals: what happened with him on, and the team's total minus that for when he was off
    for key in names:
        for n, stat in enumerate(("for", "against", "poss")):
            on = sum(g["on"].get(key, (0, 0, 0))[n] for g in by_game.values())
            tally[key]["on_" + stat] = on
            tally[key]["off_" + stat] = sum(g["team"][n] for g in by_game.values()) - on
    for five in lineups.values():
        five[0], five[3] = round(five[0], 3), round(five[3], 3)
    return tally, by_game, lineups

def folder_stamp(team_path):
    """Changes whenever a box score or play-by-play file is added or rewritten."""
    stamp = []
    for sub in ("boxscores", "playbyplay"):
        folder = os.path.join(team_path, sub)
        files = [e for e in os.scandir(folder) if e.name.endswith('.json')] if os.path.isdir(folder) else []
        stamp += [len(files), max((e.stat().st_mtime for e in files), default=0)]
    return stamp + [ONOFF_VERSION]

def on_off_swing(t):
    """Team net rating per 100 possessions with the player on the floor, minus with him off."""
    if not t or t.get("on_poss", 0) < MIN_ONOFF_POSS or t.get("off_poss", 0) < MIN_ONOFF_POSS:
        return None
    on = 100 * (t.get("on_for", 0) - t.get("on_against", 0)) / t["on_poss"]
    off = 100 * (t.get("off_for", 0) - t.get("off_against", 0)) / t["off_poss"]
    return on - off

# ---------------------------
# ROSTER (class, listed position)
# ---------------------------
def load_roster(team_path):
    try:
        with open(os.path.join(team_path, f"roster_{THIS_SEASON}.json"), 'r', encoding='utf-8') as open_f:
            return {norm_name(p['name']): p for p in json.load(open_f)['players']}
    except: return {}

def match_roster(players, roster):
    """Box score player key -> his key in the roster file (None when he can't be found there)."""
    roster_match = {k: match_name(k, roster) for k in players}
    # Nicknames ('Boopie Miller' is listed as 'Kevin Miller'): a player still unmatched takes the one
    # roster spot left with his last name, as long as he is the only unmatched player with that name.
    unclaimed = [r for r in roster if r not in roster_match.values()]
    unmatched = [k for k, r in roster_match.items() if not r]
    for k in unmatched:
        last = k.split()[-1]
        spots = [r for r in unclaimed if r.split()[-1] == last]
        if len(spots) == 1 and sum(other.split()[-1] == last for other in unmatched) == 1:
            roster_match[k] = spots[0]
    # Changed surname ('Cam Wilds' is listed as 'Cam Kearney'): same first name, and it is the only
    # roster spot with minutes that nobody has taken.
    unclaimed = [r for r in roster if r not in roster_match.values() and (roster[r].get('season_minutes') or roster[r].get('minutes'))]
    unmatched = [k for k, r in roster_match.items() if not r]
    if len(unclaimed) == 1 and len(unmatched) == 1 and unclaimed[0].split()[0] == unmatched[0].split()[0]:
        roster_match[unmatched[0]] = unclaimed[0]
    return roster_match

# ---------------------------
# MAIN ENTRY
# ---------------------------
def team_schedule(team_path, team_folder, games):
    """The team's games in date order: date, where it was played, opponent, score and possessions."""
    try:
        with open(os.path.join(team_path, "game_scores.json"), 'r', encoding='utf-8') as open_f:
            listed = {str(g['game_id']): g for g in json.load(open_f)}
    except: listed = {}
    schedule = []
    for game_id, game in games.items():
        info = listed.get(game_id)
        if not info: continue
        if is_neutral(info): where = "N"   # same rule as the team ratings
        elif info['home_team'].rstrip('. ') == team_folder.rstrip('. '): where = "H"
        else: where = "A"
        schedule.append({"id": game_id, "d": info['date'], "loc": where, "arena": info.get('arena', ''), "opp": game['opp'].strip(),
                         "pf": game['pts'], "pa": game['opp_pts'], "poss": round(game['poss'], 1)})
    schedule.sort(key=lambda g: g["d"])
    return schedule

# Quadrants: the opponent's net-rating rank and where the game was played (worst rank still in Quad 1, 2, 3)
QUAD_CUTS = {"H": (30, 75, 160), "N": (50, 100, 200), "A": (75, 135, 240)}

def quad_of(rank, where):
    for quad, cutoff in enumerate(QUAD_CUTS[where], 1):
        if rank <= cutoff:
            return quad
    return 4

def totals_for(game_ids, games):
    """Team, opponent and player totals over just these games (same sums load_team_boxscores makes for the season)."""
    team, opp, players = defaultdict(float), defaultdict(float), {}
    for game_id in game_ids:
        game = games[game_id]
        add_line(team, game["tm"])
        add_line(opp, game["op"])
        team['POSS'] += game["poss"]
        team['G'] += 1
        for key, (started, p) in game["lines"].items():
            line = players.setdefault(key, defaultdict(float))
            add_line(line, p)
            line['MP'] += float(p['MIN'] or 0)
            line['G'] += 1
            team['MP'] += float(p['MIN'] or 0)
    return team, opp, players

def quad_splits(schedule, games, team_ratings, ranks, listed, on_off_games):
    """Player key -> his advanced numbers in Quad 1, 2, 3 and 4 games (None for a quad he did not play in).
    Each entry is [games, minutes %, usage %, possessions, ORtg, DRtg, net, on/off, BPM]."""
    by_quad = {1: [], 2: [], 3: [], 4: []}
    for scheduled in schedule:
        opponent = scheduled["opp"].rstrip('. ')
        if opponent in ranks:
            by_quad[quad_of(ranks[opponent], scheduled["loc"])].append(scheduled)

    splits = {}
    for quad, played in by_quad.items():
        if not played: continue
        ids = [s["id"] for s in played]
        tm, opp, players = totals_for(ids, games)
        if not tm['POSS'] or not tm['MP']: continue

        # How well the team played in these games, on the same scale as its net rating: each game's margin
        # per 100 possessions, plus how good the opponent is, minus the home-court edge. BPM is tied to this.
        level = 0.0
        for s in played:
            game = games[s["id"]]
            edge = {"H": 2 * Kenstat.HOME_ADV, "A": -2 * Kenstat.HOME_ADV, "N": 0}[s["loc"]]     # read when used: main.py measures it first
            margin = 100 * (game["pts"] - game["opp_pts"]) / game["poss"]
            level += (margin + team_ratings[s["opp"].rstrip('. ')]['n'] - edge) * game["poss"]
        bpm, _ = box_plus_minus(players, tm, level / tm['POSS'], listed)

        team_total = [sum(on_off_games.get(i, {}).get("team", (0, 0, 0))[n] for i in ids) for n in range(3)]
        for key, p in players.items():
            if p['MP'] <= 0: continue
            share = p['MP'] / (tm['MP'] / 5)
            ortg, used = offensive_rating(p, tm, opp)
            drtg = defensive_rating(p, tm, opp)
            on = [sum(on_off_games.get(i, {}).get("on", {}).get(key, (0, 0, 0))[n] for i in ids) for n in range(3)]
            off = [team_total[n] - on[n] for n in range(3)]
            swing = None
            if on[2] >= 1 and off[2] >= 1:
                swing = round(100 * (on[0] - on[1]) / on[2] - 100 * (off[0] - off[1]) / off[2], 1)
            splits.setdefault(key, [None] * 4)[quad - 1] = [
                int(p['G']), round(100 * share, 1), round(100 * used / (tm['POSS'] * share), 1), round(tm['POSS'] * share),
                round(ortg, 1) if ortg is not None else None, round(drtg, 1),
                round(ortg - drtg, 1) if ortg is not None else None, swing, round(bpm[key], 1)]
    return splits

def game_log(key, schedule, games):
    """One player's box score line in each game he played. The first number is the game's place in the team's schedule."""
    rows = []
    for i, scheduled in enumerate(schedule):
        line = games[scheduled["id"]]["lines"].get(key)
        if not line: continue
        started, p = line
        minutes = float(p['MIN'] or 0)
        rows.append([i, int(started), int(minutes) if minutes == int(minutes) else round(minutes, 1),
                     p['PTS'], p['REB'], p['AST'], p['STL'], p['BLK'], p['TO'], p['PF'],
                     parse_made(p['FG']), parse_attempts(p['FG']), parse_made(p['3PT']), parse_attempts(p['3PT']),
                     parse_made(p['FT']), parse_attempts(p['FT'])])
    return rows

def get_player_stats(root_folder, team_ratings):
    """Returns (players, schedules, game_logs, lineups). lineups: team folder name -> who was on the floor together and
    what happened (see team_on_off). players: every player who got on the floor, with box score and
    advanced numbers. schedules: team folder name -> its games. game_logs: team folder name -> player name ->
    his line in each game and his advanced numbers by quad. team_ratings: team folder name -> Kenstat numbers ('o', 'd', 'n')."""
    ranks = {name: rank for rank, name in enumerate(sorted(team_ratings, key=lambda name: team_ratings[name]['n'], reverse=True), 1)}
    output = []
    schedules = {}
    game_logs = {}
    lineup_output = {}
    stint_output = {}       # team folder name -> game id -> who was on the floor when (for the shot data)
    try:
        with open(ONOFF_CACHE, 'r', encoding='utf-8') as open_f:
            cache = json.load(open_f)
    except: cache = {}
    new_cache = {}
    ws_rows = []            # what win shares need, gathered as each team is read (league numbers come at the end)

    for conference in sorted(os.listdir(root_folder)):
        conf_path = os.path.join(root_folder, conference)
        if not os.path.isdir(conf_path): continue
        for team_folder in sorted(os.listdir(conf_path)):
            team_path = os.path.join(conf_path, team_folder)
            rating = team_ratings.get(team_folder.rstrip('. '))
            if not os.path.isdir(team_path) or not rating: continue

            tm, opp, players, games = load_team_boxscores(team_path, team_folder)
            if not tm['POSS'] or not tm['MP']: continue
            schedules[team_folder] = team_schedule(team_path, team_folder, games)

            roster = load_roster(team_path)
            roster_match = match_roster(players, roster)
            listed = {k: LISTED_POSITION.get((roster[r].get('pos') or '')[:1], 3.0) for k, r in roster_match.items() if r}

            bpm, positions = box_plus_minus(players, tm, rating['n'], listed)
            stamp = folder_stamp(team_path)
            saved = cache.get(f"{conference}/{team_folder}")
            if saved and saved["stamp"] == stamp and "lineups" in saved and all("stints" in g for g in saved["games"].values()):
                on_off, on_off_games, five_man = saved["tally"], saved["games"], saved["lineups"]
            else:
                on_off, on_off_games, five_man = team_on_off(team_path, games, players, ncaa_aliases(team_path, team_folder, players))
            new_cache[f"{conference}/{team_folder}"] = {"stamp": stamp, "tally": on_off, "games": on_off_games, "lineups": five_man}
            stint_output[team_folder] = {game_id: g.get("stints", []) for game_id, g in on_off_games.items()}

            # Lineups for the dashboard, game by game: players are numbered (most minutes first), and each row is
            # [the game's place in the schedule, the five, possessions, points for, points against,
            #  then the same three without garbage time]
            stints = [(key.split(">")[0], key.split(">")[1].split("|"), v) for key, v in five_man.items() if v[0] > 0]
            order = sorted({k for _, keys, _ in stints for k in keys}, key=lambda k: -(players[k]['MP'] if k in players else 0))
            number = {k: i for i, k in enumerate(order)}
            place = {scheduled["id"]: i for i, scheduled in enumerate(schedules[team_folder])}
            rows = [[place[game_id], [number[k] for k in keys], round(v[0], 2), int(v[1]), int(v[2]), round(v[3], 2), int(v[4]), int(v[5])]
                    for game_id, keys, v in stints if game_id in place]
            lineup_output[team_folder] = {"players": [players[k]['name'] if k in players else k.title() for k in order], "rows": rows}

            splits = quad_splits(schedules[team_folder], games, team_ratings, ranks, listed, on_off_games)
            game_logs[team_folder] = {p['name']: {"log": game_log(k, schedules[team_folder], games), "quad": splits.get(k, [None] * 4)}
                                      for k, p in players.items()}
            for k, p in players.items():
                share = p['MP'] / (tm['MP'] / 5)
                ortg, used = offensive_rating(p, tm, opp)
                drtg = defensive_rating(p, tm, opp)
                listing = roster.get(roster_match[k]) if roster_match[k] else None
                label, year = CLASS_LABELS.get(listing['class'], (None, None)) if listing else (None, None)
                if listing and listing.get('fifth_year'):
                    label, year = "5th", 5
                swing = on_off_swing(on_off.get(k))
                games_played = p['G']
                per_game = lambda stat: round(p[stat] / games_played, 1)
                output.append({
                    "name": p['name'], "team": team_folder, "conf": conference,
                    "cls": label, "yr": year,
                    "ht": listing.get('height_in') if listing else None,
                    "pos": (listing.get('pos') or None) if listing else None,
                    # False for players under 10% of the team's minutes: they show on their team's page
                    # but are kept off the national Players table
                    "q": share >= MIN_SHARE and ortg is not None,
                    "g": int(games_played), "gs": int(p['GS']),
                    "min": round(p['MP']), "mpg": per_game('MP'), "share": round(100 * share, 1),
                    # possessions he was on the floor for: the team's possessions times his share of the minutes
                    "poss": round(tm['POSS'] * share),
                    # usage: share of the team's possessions he used (shot, turnover, trip to the line) while on the floor
                    "usg": round(100 * used / (tm['POSS'] * share), 1) if share > 0 else None,
                    "ppg": per_game('PTS'), "rpg": per_game('REB'), "apg": per_game('AST'), "spg": per_game('STL'),
                    "bpg": per_game('BLK'), "tpg": per_game('TO'), "fpg": per_game('PF'),
                    "fgm": int(p['FGM']), "fga": int(p['FGA']), "tpm": int(p['3PM']), "tpa": int(p['3PA']),
                    "ftm": int(p['FTM']), "fta": int(p['FTA']),
                    "po": round(ortg, 1) if ortg is not None else None, "pd": round(drtg, 1),
                    "pn": round(ortg - drtg, 1) if ortg is not None else None,
                    "onoff": round(swing, 1) if swing is not None else None,
                    "bpm": round(bpm[k], 1),
                    "posn": round(positions[k], 2),     # 1 point guard ... 5 center, estimated from the box score
                })
                produced = ortg * used / 100 if ortg is not None else 0.0
                ws_rows.append((output[-1], produced, used, drtg, p['MP'], tm['MP'], tm['POSS'], tm['G'], tm['PTS']))

    win_shares(ws_rows)
    try:
        with open(ONOFF_CACHE, 'w', encoding='utf-8') as open_f:
            json.dump(new_cache, open_f)
    except: pass
    return output, schedules, game_logs, lineup_output, stint_output

# ---------------------------
# WIN SHARES (Justin Kubatko, as laid out by Basketball Reference: basketball-reference.com/about/ws.html)
# ---------------------------
# One win share is one team win, split between offense and defense:
#   marginal offense = points produced - 0.92 x league points per possession x offensive possessions
#   marginal defense = (his minutes / team minutes) x team defensive possessions x (1.08 x league points per
#                      possession - his defensive rating / 100)
#   marginal points per win = 0.32 x league points per game x (team pace / league pace)
#   offensive (defensive) win shares = marginal offense (defense) / marginal points per win
# Points produced, offensive possessions and the defensive rating are the Dean Oliver ones above. League numbers are
# Division I's, from the games between two Division I teams. College games are 40 minutes, so the per-minute rate
# is win shares per 40 (Basketball Reference's NBA pages use 48).
def win_shares(rows):
    """rows: (output entry, points produced, offensive possessions, defensive rating, his minutes, team minutes,
    team possessions, team games). Adds "ows", "dws", "ws" and "ws40" to each entry."""
    teams = {}
    for entry, *_, tm_min, tm_poss, tm_games, tm_pts in rows:
        teams[entry["team"]] = (tm_poss, tm_games, tm_pts)
    if not teams: return
    lg_pts = sum(t[2] for t in teams.values())
    lg_poss = sum(t[0] for t in teams.values())
    lg_games = sum(t[1] for t in teams.values())
    lg_ppp = div(lg_pts, lg_poss)
    lg_ppg = div(lg_pts, lg_games)
    lg_pace = div(lg_poss, lg_games)
    for entry, produced, used, drtg, minutes, tm_min, tm_poss, tm_games, tm_pts in rows:
        per_win = 0.32 * lg_ppg * div(div(tm_poss, tm_games), lg_pace)
        if not per_win: continue
        offense = div(produced - 0.92 * lg_ppp * used, per_win) if used else 0.0
        defense = div(div(minutes, tm_min) * tm_poss * (1.08 * lg_ppp - drtg / 100), per_win)
        entry["ows"], entry["dws"] = round(offense, 2), round(defense, 2)
        entry["ws"] = round(offense + defense, 2)
        entry["ws40"] = round(div(offense + defense, minutes) * 40, 3) if minutes else None

# ---------------------------
# "WITHOUT A PLAYER" CHECK
# ---------------------------
MOST_MINUTES = 0.92   # nobody is projected past 92% of the minutes

def freed_minutes_model(roster, out):
    """Minutes share for each remaining player once `out` (a set of names) are gone: the freed minutes go to
    teammates with room to play more, players at the same listed position first. (The dashboard does the same sum.)"""
    stay = [p for p in roster if p['name'] not in out]
    freed = sum(p['share'] / 100 for p in roster if p['name'] in out)
    out_positions = {(p['pos'] or '?')[0] for p in roster if p['name'] in out}
    room = [max(0, MOST_MINUTES - p['share'] / 100) * p['share'] / 100 * (2 if (p['pos'] or '?')[0] in out_positions else 1) for p in stay]
    total_room = sum(room) or 1
    return stay, [p['share'] / 100 + freed * r / total_room for p, r in zip(stay, room)]

def without_calibration(players, lineups):
    """Compares, for every regular in the country, what his box score numbers say losing him costs the team with
    what actually happened in the possessions he sat (garbage time included). Returns the multiplier that makes the
    box estimate match reality on average, and how many players it is based on."""
    by_team = defaultdict(list)
    for p in players:
        by_team[p['team']].append(p)
    box, seen, weight = [], [], []
    for team, five in lineups.items():
        roster = by_team.get(team, [])
        number = {name: i for i, name in enumerate(five['players'])}
        everyone = [sum(r[k] for r in five['rows']) for k in (2, 3, 4)]
        if not everyone[0]: continue
        net_all = 100 * (everyone[1] - everyone[2]) / everyone[0]
        before = sum(p['share'] / 100 * p['bpm'] for p in roster)
        for x in roster:
            if x['share'] < 25 or x['name'] not in number: continue
            off = [sum(r[k] for r in five['rows'] if number[x['name']] not in r[1]) for k in (2, 3, 4)]
            if off[0] < 150: continue
            stay, minutes = freed_minutes_model(roster, {x['name']})
            box.append(sum(m * p['bpm'] for m, p in zip(minutes, stay)) - before)
            seen.append(100 * (off[1] - off[2]) / off[0] - net_all)
            weight.append(off[0])
    if len(box) < 50:
        return {"scale": 1.0, "players": len(box)}
    total = sum(weight)
    mean_box = sum(w * b for w, b in zip(weight, box)) / total
    mean_seen = sum(w * s for w, s in zip(weight, seen)) / total
    slope = (sum(w * (b - mean_box) * (s - mean_seen) for w, b, s in zip(weight, box, seen))
             / sum(w * (b - mean_box) ** 2 for w, b in zip(weight, box)))
    return {"scale": round(slope, 2), "players": len(box)}

if __name__ == "__main__":
    import Kenstat
    ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/seasons/2526")
    ratings = {name.rstrip('. '): s for name, s in Kenstat.get_efficiency_ratings(ROOT, iterations=30).items()}
    results = [p for p in get_player_stats(ROOT, ratings)[0] if p['q']]

    print(f"\nPlayers rated: {len(results)}\n")
    print(f"{'Rank':<5}{'Player':<26}{'Team':<22}{'Cl':<5}{'ORtg':>7}{'DRtg':>7}{'Net':>7}{'On/Off':>8}{'BPM':>7}")
    print("-" * 94)
    for i, p in enumerate(sorted(results, key=lambda p: p["bpm"], reverse=True)[:40], 1):
        swing = f"{p['onoff']:+.1f}" if p['onoff'] is not None else "--"
        print(f"{i:<5}{p['name'][:25]:<26}{p['team'][:21]:<22}{p['cls'] or '--':<5}{p['po']:>7}{p['pd']:>7}{p['pn']:>+7}{swing:>8}{p['bpm']:>+7}")
