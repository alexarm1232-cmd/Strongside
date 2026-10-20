import os
import json
import math
from collections import defaultdict

from Kenstat import THIS_SEASON
from Playerstat import norm_name, match_name

# Shot data comes from the "shots" folder in each team folder (saved by collect/2526/9espnshots.py).
# A shot is [side, player, period, seconds left, kind, made, points, x, y, assisted by], with the basket
# at x = 25, y = 0 and everything in feet.

# ---------------------------
# ZONES
# ---------------------------
ZONES = ["rim", "short", "mid", "corner3", "arc3"]
RIM_FEET = 4.5          # at the rim: within this many feet of the basket
SHORT_FEET = 10         # short two: out to here; any two beyond it is mid-range
CORNER_Y = 5            # a three from no more than this far out from the basket line is a corner three

# What led to the shot, from the clock
TRANSITION_SECONDS = 8  # a shot this soon after the team's own defensive rebound or steal
PUTBACK_SECONDS = 4     # a shot this soon after the team's own offensive rebound
CONTEXTS = ["halfcourt", "transition", "putback"]

def zone_of(points, x, y):
    if points == 3:
        return 3 if y <= CORNER_Y else 4
    distance = math.hypot(x - 25, y)
    return 0 if distance <= RIM_FEET else 1 if distance <= SHORT_FEET else 2

# The finer map used on the shot charts: eleven areas, left and right kept apart.
# 0 rim | 1-2 short twos (left, right) | 3-5 mid-range (left, middle, right) | 6-10 threes (left corner, left wing, top, right wing, right corner)
MID_SPLIT_DEGREES = 30      # mid-range: within this many degrees of straight-on is "middle"
THREE_SPLIT_DEGREES = 25    # threes: within this many degrees of straight-on is "top"

def court_area(points, x, y):
    side = math.degrees(math.atan2(x - 25, y))      # 0 = straight out from the basket, negative = the left side
    if points == 3:
        if y <= CORNER_Y: return 6 if x < 25 else 10
        return 8 if abs(side) <= THREE_SPLIT_DEGREES else 7 if side < 0 else 9
    distance = math.hypot(x - 25, y)
    if distance <= RIM_FEET: return 0
    if distance <= SHORT_FEET: return 1 if x < 25 else 2
    return 4 if abs(side) <= MID_SPLIT_DEGREES else 3 if side < 0 else 5

def new_tally():
    """zones: [attempts, makes] for each zone. ft: [attempts, makes]. contexts: [attempts, makes, points] for each.
    assisted: [assisted makes, makes]."""
    return {"z": [[0, 0] for _ in ZONES], "ft": [0, 0], "c": [[0, 0, 0] for _ in CONTEXTS], "a": [0, 0]}

def add_shot(tally, zone, context, made, points, assisted):
    tally["z"][zone][0] += 1
    tally["z"][zone][1] += made
    tally["c"][context][0] += 1
    tally["c"][context][1] += made
    tally["c"][context][2] += points if made else 0
    if made:
        tally["a"][0] += 1 if assisted else 0
        tally["a"][1] += 1

# ---------------------------
# PLAY TYPES
# ---------------------------
# Twelve kinds of play, worked out from four things the shot data does give: where the shot was taken, whether it
# was assisted and by whom, whether the shooter (and the passer) plays like a perimeter player or a big, and the clock.
#   Rim Attack       a perimeter player's own drive or slash: unassisted at the rim or in close, floaters and pull-ups included
#   Drive & Kick     a perimeter player's three off another perimeter player's pass (the defense collapsed on a drive)
#   Dribble Jumper   a three with no assist: off the dribble, in isolation, or around a screen
#   Mid-Range        an assisted two from mid-range, whoever passed it (unless a big found a perimeter shooter: Inside Out)
#   Perimeter Cut    a perimeter player finishing at the rim or in close off a pass
#   Big Cut & Roll   a big finishing at the rim or in close off a perimeter player's pass, usually after a screen
#   Post-Up          a big scoring on his own at the rim or in close (or on a turnaround)
#   Inside Out       a big, usually doubled, finding a perimeter shooter for a three or a mid-range shot
#   Pick & Pop       an assisted three by a big
#   High-Low         one big finding another at the rim or in close
#   Rebound Scores   a shot straight off the team's own offensive rebound: putbacks and kick-outs
#   Transition       rim to rim: a shot soon after the team's own defensive rebound or steal
PLAY_TYPES = ["Rim Attack", "Drive & Kick", "Dribble Jumper", "Mid-Range", "Perimeter Cut", "Big Cut & Roll",
              "Post-Up", "Inside Out", "Pick & Pop", "High-Low", "Rebound Scores", "Transition"]
SCRAMBLE, TRANSITION = 10, 11       # SCRAMBLE = Rebound Scores
# The data does not record screens, so "usually after a screen" cannot be checked: every catch-and-finish by a big
# off a perimeter player's pass is a Big Cut & Roll, and every assisted three by a big is a Pick & Pop.

# Perimeter player or big is not all-or-nothing: each player gets a share between 0 (all perimeter) and 1 (all big),
# and his plays are split between the two readings. Half of it is how he plays, from his estimated position
# (1 = point guard ... 5 = center, worked out from his box score in Playerstat): at or below PERIMETER_POSITION that
# half is all perimeter, at or above BIG_POSITION all big. The other half is how he is built, from the roster.
PERIMETER_POSITION = 2.5
BIG_POSITION = 4.5
BIG_FORWARD_INCHES = 80     # built like a big: a listed center, or a listed forward this tall (6'8") or taller

def big_share_of(position):
    return min(1.0, max(0.0, (position - PERIMETER_POSITION) / (BIG_POSITION - PERIMETER_POSITION)))

# A perimeter passer is further split into ball-handler and wing, again by estimated position: at or below
# HANDLER_POSITION he is all ball-handler, and by PERIMETER_POSITION all wing. (The play types no longer tell the
# two apart; the split is kept for when they do.)
HANDLER_POSITION = 1.3

def handler_share_of(position):
    return min(1.0, max(0.0, (PERIMETER_POSITION - position) / (PERIMETER_POSITION - HANDLER_POSITION)))

def half_court_play(shooter, group, passer):
    """shooter: 'P' perimeter or 'B' big. passer: None when unassisted, else 'H' ball-handler or 'W' wing (both are
    perimeter passers, and count the same here) or 'B' big.
    group: 'R' rim and short twos, 'M' mid-range, 'C' corner threes, 'T' other threes."""
    three = group in ('C', 'T')
    if passer is None:
        if three: return 2                                          # Dribble Jumper
        return 0 if shooter == 'P' else 6                           # Rim Attack (pull-ups and floaters too) / Post-Up
    from_big = passer == 'B'
    if shooter == 'P':
        if group == 'R': return 4                                   # Perimeter Cut
        if from_big: return 7                                       # Inside Out: a big finds a shooter, three or mid-range
        return 1 if three else 3                                    # Drive & Kick / Mid-Range
    if three: return 8                                              # Pick & Pop
    if group == 'M': return 3                                       # Mid-Range
    return 9 if from_big else 5                                     # High-Low / Big Cut & Roll

# Where a trip to the line is counted when it did not come with a made basket: the plays that draw fouls
FOUL_PLAYS = {'P': [0, 4], 'B': [6, 5, 9]}
# Turnovers are not tied to a play in the data, so they are shared out by how likely each kind of play is to end
# in one: plays the player creates himself most, plays where he catches on the move less, catch-and-shoot least.
TURNOVER_WEIGHT = [1.0, 0.2, 1.0, 0.2, 0.5, 0.5, 1.0, 0.2, 0.2, 0.5, 0.2, 1.0]

def new_plays():
    return {"exact": [[0.0, 0.0] for _ in PLAY_TYPES],                  # [plays, points] known for certain
            "made_in": defaultdict(lambda: defaultdict(float)),         # (role, group) -> play type -> makes
            "missed": defaultdict(float),                               # (role, group) -> half-court misses
            "ft": defaultdict(lambda: [0.0, 0.0]),                      # role -> [trips, points] in the half court
            "to": [0.0]}                                                # half-court turnovers (when each one is known)

def share_misses(tally, fallback=None):
    """Half-court misses by play type. A miss has no assist to go by, so misses are shared among the play types the
    same way that kind of shooter's makes from that area were (the player's own makes when he has five or more
    there, otherwise the team's)."""
    missed = [0.0 for _ in PLAY_TYPES]
    for (role, group), count in tally["missed"].items():
        makes = tally["made_in"].get((role, group), {})
        if sum(makes.values()) < 5 and fallback is not None:
            makes = fallback["made_in"].get((role, group), makes)
        total = sum(makes.values())
        if total:
            for play, n in makes.items():
                missed[play] += count * n / total
        else:
            missed[half_court_play(role, group, None)] += count
    return missed

def finish_plays(tally, fallback=None):
    """[plays, points] for each play type."""
    plays = [list(row) for row in tally["exact"]]
    for play, count in enumerate(share_misses(tally, fallback)):
        plays[play][0] += count
    for role, (trips, points) in tally["ft"].items():
        weights = [plays[play][0] for play in FOUL_PLAYS[role]]
        total = sum(weights)
        for play, weight in zip(FOUL_PLAYS[role], weights if total else [1] + [0] * (len(weights) - 1)):
            plays[play][0] += trips * weight / (total or 1)
            plays[play][1] += points * weight / (total or 1)
    # Half-court turnovers are known one by one (who and when) but not which play they ended, so they go to the
    # half-court plays by how likely each is to end in one. Transition and scramble turnovers were placed by the clock.
    weights = [plays[i][0] * TURNOVER_WEIGHT[i] if i not in (SCRAMBLE, TRANSITION) else 0 for i in range(len(plays))]
    total = sum(weights)
    for i, weight in enumerate(weights if total else [1] + [0] * (len(plays) - 1)):
        plays[i][0] += tally["to"][0] * weight / (total or 1)
    return [[round(n, 2), round(pts, 2)] for n, pts in plays]

def merge_plays(into, add):
    """Adds one raw tally of plays (see new_plays) to another."""
    for i, (plays, points) in enumerate(add["exact"]):
        into["exact"][i][0] += plays
        into["exact"][i][1] += points
    for key, by_play in add["made_in"].items():
        for play, makes in by_play.items():
            into["made_in"][key][play] += makes
    for key, count in add["missed"].items():
        into["missed"][key] += count
    for role, (trips, points) in add["ft"].items():
        into["ft"][role][0] += trips
        into["ft"][role][1] += points
    into["to"][0] += add["to"][0]

# Points per play by play type, adjusted play type by play type for the opponents faced: scoring 1.2 a play in
# transition means less against defenses that give up 1.3 there than against ones that give up 1.0.
# (The dashboard and the Spread report adjust by strength of schedule instead, which tracked the real spreads
# better; this finer adjustment is kept as Spreadstat's "category" option.)
# The two numbers below, and PLAY_SHRINK in the dashboard and Spreadstat, were chosen as the ones that brought the
# simulator's spreads closest to this season's real spreads (the Spread report).
ADJUST_PASSES = 10
ADJUST_PRIOR_PLAYS = 15     # an opponent's own number is trusted as if it had this many more plays at the D-I average

def adjust_plays(logs):
    """logs: team -> list of (opponent, the team's [plays, points] by play type in one game, its opponents' the same).
    Returns (team -> (points per play by type on offense, the same allowed on defense), both adjusted for the
    opponents faced, D-I points per play by type). Each game's scoring is moved by how far that opponent is from
    the D-I average on that play type (additive, like the team ratings), then the passes are repeated so the
    opponents' own numbers are adjusted too."""
    count = len(PLAY_TYPES)
    plays, points = [0.0] * count, [0.0] * count
    for games in logs.values():
        for _, own, _ in games:
            for i, (n, pts) in enumerate(own):
                plays[i] += n
                points[i] += pts
    league = [points[i] / plays[i] if plays[i] else 1.0 for i in range(count)]
    totals = {}      # team -> ([plays, points] by type on offense, the same on defense)
    for team, games in logs.items():
        own_sum, their_sum = [[0.0, 0.0] for _ in range(count)], [[0.0, 0.0] for _ in range(count)]
        for _, own, theirs in games:
            for i in range(count):
                own_sum[i][0] += own[i][0]; own_sum[i][1] += own[i][1]
                their_sum[i][0] += theirs[i][0]; their_sum[i][1] += theirs[i][1]
        totals[team] = (own_sum, their_sum)
    steady = lambda row, value, i: (row[0] * value + ADJUST_PRIOR_PLAYS * league[i]) / (row[0] + ADJUST_PRIOR_PLAYS)
    offense = {team: [row[1] / row[0] if row[0] else league[i] for i, row in enumerate(t[0])] for team, t in totals.items()}
    defense = {team: [row[1] / row[0] if row[0] else league[i] for i, row in enumerate(t[1])] for team, t in totals.items()}
    for _ in range(ADJUST_PASSES):
        # how far each team is from the D-I average on each play type, pulled toward it when the sample is thin
        off_gap = {team: [steady(totals[team][0][i], offense[team][i], i) - league[i] for i in range(count)] for team in totals}
        def_gap = {team: [steady(totals[team][1][i], defense[team][i], i) - league[i] for i in range(count)] for team in totals}
        new_offense, new_defense = {}, {}
        for team, games in logs.items():
            own_pts, their_pts = [row[1] for row in totals[team][0]], [row[1] for row in totals[team][1]]
            for opponent, own, theirs in games:
                faced_d, faced_o = def_gap.get(opponent), off_gap.get(opponent)
                if faced_d:
                    for i in range(count):
                        own_pts[i] -= own[i][0] * faced_d[i]
                        their_pts[i] -= theirs[i][0] * faced_o[i]
            new_offense[team] = [own_pts[i] / totals[team][0][i][0] if totals[team][0][i][0] else league[i] for i in range(count)]
            new_defense[team] = [their_pts[i] / totals[team][1][i][0] if totals[team][1][i][0] else league[i] for i in range(count)]
        offense, defense = new_offense, new_defense
    return {team: (offense[team], defense[team]) for team in totals}, league

def add_turnovers(plays, turnovers):
    """The same [plays, points] list with this many turnovers added as plays worth nothing."""
    weights = [n * w for (n, _), w in zip(plays, TURNOVER_WEIGHT)]
    total = sum(weights)
    if not total or not turnovers:
        return [[round(n, 1), round(pts, 1)] for n, pts in plays]
    return [[round(n + turnovers * w / total, 1), round(pts, 1)] for (n, pts), w in zip(plays, weights)]

# Older seasons' shots mostly have no spot on the floor, only what kind of shot it was. With KIND_ZONES on (main.py
# sets it for those seasons) such a shot is still counted: a layup, dunk or tip-in as a shot at the rim, any other
# two as mid-range, a three as a three. That is all the play types need. It is left off the shot charts.
KIND_ZONES = False

def read_game(game, my_side):
    """One game's shots in order, each tagged with its zone and what led to it.
    Yields (mine, player, zone, context, made, points, x, y, assist name, period, seconds left); zone is None for a free throw."""
    timeline = [(e[1] or 0, -(e[2] or 0), 0, e) for e in game.get("events", [])] + \
               [(s[2] or 0, -(s[3] or 0), 1, s) for s in game.get("shots", [])]
    timeline.sort(key=lambda item: item[:3])
    last = None     # the most recent rebound / turnover / steal: (side, period, seconds left, kind)
    for period, _, is_shot, row in timeline:
        if not is_shot:
            last = (row[0], row[1], row[2], row[3])
            continue
        side, player, _, left, kind, made, points, x, y, assist = row
        mine = side == my_side
        context = 0
        if last and last[0] == side and last[1] == period and left is not None and last[2] is not None:
            since = last[2] - left
            if last[3] == "Offensive Rebound" and 0 <= since <= PUTBACK_SECONDS:
                context = 2
            elif last[3] in ("Defensive Rebound", "Steal") and 0 <= since <= TRANSITION_SECONDS:
                context = 1
        if "FreeThrow" in kind:
            yield mine, player, None, context, made, 1, None, None, "", period, left
            continue
        if kind == "TipShot":
            context = 2
        if x is None or y is None:
            if KIND_ZONES:
                zone = 4 if points == 3 else 0 if kind in ("LayUpShot", "DunkShot", "TipShot") else 2
                yield mine, player, zone, context, made, points, None, None, assist, period, left
            continue
        yield mine, player, zone_of(points, x, y), context, made, points, x, y, assist, period, left

def load_roles(root_folder, positions=None):
    """Returns big_share(team name, ESPN player name): 0 = all perimeter ... 1 = all big, and
    handler_share(team name, ESPN player name): how much of his perimeter side is ball-handler rather than wing.
    positions: team folder name -> {normalized player name: position on the 1-5 scale}."""
    folders = {}
    for conference in os.listdir(root_folder):
        conf_path = os.path.join(root_folder, conference)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                folders[team.rstrip('. ')] = (team, os.path.join(conf_path, team))
    rosters, known, handlers = {}, {}, {}
    def big_share(team, player):
        team = team.rstrip('. ')
        if (team, player) not in known:
            share = None
            if team in folders and player:
                folder, path = folders[team]
                # how he plays: his estimated position
                estimated = (positions or {}).get(folder, {})
                key = match_name(player, estimated) if estimated else None
                by_play = big_share_of(estimated[key]) if key else None
                if key: handlers[(team, player)] = handler_share_of(estimated[key])
                # how he is built: a listed center, or a forward 6'8" or taller
                if team not in rosters:
                    try:
                        with open(os.path.join(path, f"roster_{THIS_SEASON}.json"), 'r', encoding='utf-8') as open_f:
                            rosters[team] = {norm_name(p['name']): p for p in json.load(open_f)['players']}
                    except: rosters[team] = {}
                key = match_name(player, rosters[team]) if rosters[team] else None
                listing = rosters[team].get(key) if key else None
                by_size = None
                if listing:
                    position = (listing.get('pos') or '')[:1]
                    by_size = 1.0 if position == 'C' or (position == 'F' and (listing.get('height_in') or 0) >= BIG_FORWARD_INCHES) else 0.0
                    handlers.setdefault((team, player), 0.6 if position == 'G' else 0.0)    # no position estimate: go by the listing
                # the two count equally when both are known
                both = [v for v in (by_play, by_size) if v is not None]
                share = sum(both) / len(both) if both else None
            known[(team, player)] = share if share is not None else 0.0
        return known[(team, player)]
    def handler_share(team, player):
        big_share(team, player)
        return handlers.get((team.rstrip('. '), player), 0.0)
    return big_share, handler_share

def on_floor(stints, period, left, same_second=False):
    """The five on the floor for a play at this time. stints: [period, seconds left, five] each time the lineup
    changed, in order. Substitutions logged at the very same second as the play have not happened yet, unless
    same_second is set (stints taken from the plays themselves, where the entry is the five for that play)."""
    five = []
    started = False
    for stint_period, stint_left, players in stints:
        if stint_period != period: continue
        if not started or (left is not None and (stint_left >= left if same_second else stint_left > left)):
            five = players
            started = True
    return five

def turnover_context(events, side, period, left):
    """0 half court, 1 transition, 2 scramble, for a turnover at this time, judged like a shot would be."""
    before = None
    for e_side, e_period, e_left, kind in events:
        if e_period == period and e_left is not None and left is not None and e_left > left and "Turnover" not in kind:
            if before is None or e_left < before[2]:
                before = (e_side, e_period, e_left, kind)
    if before and before[0] == side:
        since = before[2] - left
        if before[3] == "Offensive Rebound" and since <= PUTBACK_SECONDS: return 2
        if before[3] in ("Defensive Rebound", "Steal") and since <= TRANSITION_SECONDS: return 1
    return 0

def count_plays(game, my_side, big_share, handler_share, offense, defense, players, defenders, teammates, fives, stints, plays_file=None):
    """Adds one game's plays to the team's own tally, its opponents' tally, each of its players' tallies,
    and the tallies of each of its players who was on the floor: defenders for the opponents' plays,
    teammates for the team's own. fives: (the team's plays, its opponents' plays), each by the five on the floor."""
    names = (game.get("home_team", ""), game.get("away_team", ""))
    # CollegeBasketballData.com's file for the game, when there is one: its fives are used for who was on the
    # floor, and its turnovers (each with a player and a time) are counted as plays.
    same_second = False
    if plays_file:
        floor = [[e[0], e[1], e[3]] for e in plays_file.get("floor", []) if e[2] == my_side]
        if floor:       # (a file with turnovers but no fives leaves the play-by-play's own lineups in use)
            stints, same_second = floor, True
        for side, period, left, player in plays_file.get("turnovers", []):
            mine = side == my_side
            five = on_floor(stints, period, left, True)
            tallies = [offense, players[player]] + [teammates[k] for k in five] if mine else [defense] + [defenders[k] for k in five]
            if five: tallies.append(fives[0 if mine else 1][tuple(sorted(five))])
            context = turnover_context(game.get("events", []), side, period, left)
            for tally in tallies:
                if context:
                    tally["exact"][SCRAMBLE if context == 2 else TRANSITION][0] += 1
                else:
                    tally["to"][0] += 1
    trip = None          # the free throw trip being read: [key, mine, player, shots, points, context, tallies]
    last_make = None     # (key, {play type: share}) of the latest made basket, for and-ones
    def roles(team, player):
        share = big_share(team, player)
        return [(role, weight) for role, weight in (('P', 1 - share), ('B', share)) if weight > 0]
    def passer_roles(team, player):
        share, handler = big_share(team, player), handler_share(team, player)
        return [(role, weight) for role, weight in (('H', (1 - share) * handler), ('W', (1 - share) * (1 - handler)), ('B', share)) if weight > 0]
    def close_trip():
        nonlocal trip
        if not trip: return
        key, mine, player, shots, points, context, tallies = trip
        for tally in tallies:
            if shots == 1 and last_make and last_make[0] == key:       # and-one: the point belongs to the basket's play
                for play, share in last_make[1].items():
                    tally["exact"][play][1] += points * share
            elif context:
                play = SCRAMBLE if context == 2 else TRANSITION
                tally["exact"][play][0] += 1
                tally["exact"][play][1] += points
            else:
                for role, weight in roles(names[my_side if mine else 1 - my_side], player):
                    tally["ft"][role][0] += weight
                    tally["ft"][role][1] += points * weight
        trip = None

    for mine, player, zone, context, made, points, x, y, assist, period, left in read_game(game, my_side):
        key = (mine, player, period, left)
        if zone is None and trip and trip[0] == key:        # another free throw in the same trip
            trip[3] += 1
            trip[4] += made
            continue
        close_trip()
        five = on_floor(stints, period, left, same_second)
        tallies = [offense, players[player]] + [teammates[k] for k in five] if mine else [defense] + [defenders[k] for k in five]
        if five: tallies.append(fives[0 if mine else 1][tuple(sorted(five))])
        if zone is None:            # a new trip to the line
            trip = [key, mine, player, 1, made, context, tallies]
            continue
        team = names[my_side if mine else 1 - my_side]
        group = 'C' if zone == 3 else 'T' if zone == 4 else 'M' if zone == 2 else 'R'
        shooter = roles(team, player)
        passers = passer_roles(team, assist) if assist else [(None, 1.0)]
        shares = {}      # play type -> share of this shot
        if context:
            shares[SCRAMBLE if context == 2 else TRANSITION] = 1.0
        elif made:
            for role, weight in shooter:
                for passer, passer_weight in passers:
                    play = half_court_play(role, group, passer)
                    shares[play] = shares.get(play, 0) + weight * passer_weight
        for tally in tallies:
            if shares:
                for play, share in shares.items():
                    tally["exact"][play][0] += share
                    tally["exact"][play][1] += (points if made else 0) * share
                if made and not context:
                    for role, weight in shooter:
                        for passer, passer_weight in passers:
                            tally["made_in"][(role, group)][half_court_play(role, group, passer)] += weight * passer_weight
            else:           # a half-court miss
                for role, weight in shooter:
                    tally["missed"][(role, group)] += weight
        if made:
            last_make = (key, shares)
    close_trip()

def get_shot_stats(root_folder, positions=None, stints=None):
    """Team folder name -> {"o": the team's own shots, "d": shots against it, "players": {ESPN player name: tally},
    "defenders": {normalized player name: opponents' play types while he was on the floor},
    "teammates": {normalized player name: the team's own play types while he was on the floor},
    "fives": [[the five on the floor, the team's play types with them on, its opponents' play types]],
    "chart": {"players": [names], "o": [[x, y, made, zone, context, player number]], "d": [[x, y, made, zone, context]]}}.
    positions: team folder name -> {normalized player name: position 1-5}. stints: team folder name -> game id -> who was on the floor when."""
    output = {}
    league_areas = [[0, 0] for _ in range(11)]      # every D-I shot by court area: [attempts, makes]
    play_logs = defaultdict(list)                   # team -> its play types game by game, with the opponent
    big_share, handler_share = load_roles(root_folder, positions)
    for conference in sorted(os.listdir(root_folder)):
        conf_path = os.path.join(root_folder, conference)
        if not os.path.isdir(conf_path): continue
        for team in sorted(os.listdir(conf_path)):
            shots_dir = os.path.join(conf_path, team, "shots")
            if not os.path.isdir(shots_dir): continue
            offense, defense = new_tally(), new_tally()
            players = defaultdict(new_tally)
            plays_o, plays_d, plays_by, plays_against, plays_with = new_plays(), new_plays(), defaultdict(new_plays), defaultdict(new_plays), defaultdict(new_plays)
            plays_five = (defaultdict(new_plays), defaultdict(new_plays))
            team_stints = (stints or {}).get(team, {})
            numbers = {}
            chart_o, chart_d = [], []
            games = with_turnovers = 0
            used = []               # the games that had shot spots, and so are in these numbers
            game_plays = []         # (opponent, the team's plays in one game, its opponents' plays), as raw tallies
            for f in os.listdir(shots_dir):
                if not f.endswith('.json'): continue
                try:
                    with open(os.path.join(shots_dir, f), 'r', encoding='utf-8') as open_f:
                        game = json.load(open_f)
                except: continue
                if game.get("home_team", "").rstrip('. ') == team.rstrip('. '): my_side = 0
                elif game.get("away_team", "").rstrip('. ') == team.rstrip('. '): my_side = 1
                else: continue
                # ESPN did not record where shots were taken until February 2025. A game without shot spots cannot
                # be sorted into zones or play types, so it is left out whole (its free throws and turnovers too,
                # or they would be counted against half the shots).
                tries = [s for s in game.get("shots", []) if "FreeThrow" not in s[4]]
                if not tries or (not KIND_ZONES and sum(1 for s in tries if s[7] is not None and s[8] is not None) < 0.8 * len(tries)):
                    continue
                games += 1
                used.append(f[:-5])
                try:
                    with open(os.path.join(conf_path, team, "cbbd", f), 'r', encoding='utf-8') as open_f:
                        plays_file = json.load(open_f)
                    with_turnovers += 1
                except: plays_file = None
                game_o, game_d = new_plays(), new_plays()        # this game's plays on their own, for the opponent adjustment
                count_plays(game, my_side, big_share, handler_share, game_o, game_d, plays_by, plays_against, plays_with, plays_five, team_stints.get(f[:-5], []), plays_file)
                merge_plays(plays_o, game_o)
                merge_plays(plays_d, game_d)
                opponent = game.get("away_team" if my_side == 0 else "home_team", "").rstrip('. ')
                game_plays.append((opponent, game_o, game_d))
                for mine, player, zone, context, made, points, x, y, assisted, _, _ in read_game(game, my_side):
                    tally = offense if mine else defense
                    if zone is None:        # free throw
                        tally["ft"][0] += 1
                        tally["ft"][1] += made
                        if mine:
                            players[player]["ft"][0] += 1
                            players[player]["ft"][1] += made
                        continue
                    add_shot(tally, zone, context, made, points, bool(assisted))
                    if mine:
                        add_shot(players[player], zone, context, made, points, bool(assisted))
                        if x is not None:       # only a shot with a spot can go on the chart
                            chart_o.append([x, y, made, zone, context, numbers.setdefault(player, len(numbers))])
                            area = league_areas[court_area(points, x, y)]
                            area[0] += 1
                            area[1] += made
                    elif x is not None:
                        chart_d.append([x, y, made, zone, context])
            # one game has too few makes to say how its misses split among the play types, so the season's split is used
            play_logs[team.rstrip('. ')] = [(opponent, finish_plays(game_o, plays_o), finish_plays(game_d, plays_d)) for opponent, game_o, game_d in game_plays]
            if games:
                offense["pt"], defense["pt"] = finish_plays(plays_o), finish_plays(plays_d)
                for name, tally in players.items():
                    tally["pt"] = finish_plays(plays_by[name], plays_o)
                    tally["big"] = round(big_share(team, name), 2)
                output[team] = {"o": offense, "d": defense, "games": games, "used": used, "players": dict(players),
                                # True when (nearly) every game had its turnovers one by one, so none need estimating.
                                # A team missing a game or two is still counted; its turnovers run a few percent low.
                                "turnovers_counted": with_turnovers >= 0.9 * games,
                                "defenders": {key: finish_plays(tally, plays_d) for key, tally in plays_against.items()},
                                "teammates": {key: finish_plays(tally, plays_o) for key, tally in plays_with.items()},
                                # sorted, so a rebuild writes the same file (set order changes from run to run)
                                "fives": [[sorted(five), finish_plays(plays_five[0][five], plays_o) if five in plays_five[0] else None,
                                           finish_plays(plays_five[1][five], plays_d) if five in plays_five[1] else None]
                                          for five in sorted(set(plays_five[0]) | set(plays_five[1]), key=sorted)],
                                "chart": {"players": sorted(numbers, key=numbers.get), "o": chart_o, "d": chart_d}}
    output["__league__"] = {"areas": league_areas}
    return output

if __name__ == "__main__":
    ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/seasons/2526")
    stats = get_shot_stats(ROOT)
    stats.pop("__league__", None)
    print(f"\nTeams with shot data: {len(stats)}\n")
    print(f"{'Team':<24}" + "".join(f"{z:>16}" for z in ZONES))
    for team in ("Alabama", "Duke", "Houston", "Purdue"):
        if team not in stats: continue
        zones = stats[team]["o"]["z"]
        total = sum(z[0] for z in zones)
        worth = [2, 2, 2, 3, 3]
        print(f"{team:<24}" + "".join(f"{100 * z[0] / total:>8.1f}% {worth[i] * z[1] / max(z[0], 1):>5.2f}pt" for i, z in enumerate(zones)))
