import os
import re
import csv
import sys
import glob
import gzip
import json
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
from difflib import SequenceMatcher

# Builds a season's game list and box scores from the ESPN data downloaded through hoopR (tools/hoopr_pbp.R ->
# data/hoopr/<year>/schedule, team_box, player_box), for the seasons stats.ncaa.org has no box scores for. It writes the
# same files tools/ncaa_stats_season.py does:
#     python tools/hoopr_season.py 0809          (or several: 0809 0708 0607 0506)
#   games.json, game_scores.json   in both teams' folders: date, the two teams, the score, neutral floor or not
#   boxscores/<game id>.json       every player's line and the team totals
# The pre-tournament folder ("data/seasons/0809") gets the games up to Selection Sunday; the full-season folder
# ("data/seasons/0809 full") gets every game, postseason included. Game ids are ESPN's. Only games between two of the
# season's Division I teams (the folders tools/make_season_codes.py made) are kept.
# ESPN's teams are matched to our folders by their ESPN team id, learned from the later seasons' espn_teams.json files
# (an ESPN id never changes), then by name for any team those files do not have. Unmatched teams are listed at the end.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
HOOPR_DIR = os.path.join(ROOT, "data", "hoopr")
SOURCE = "espn-hoopr"
SEASONS = {"0809": (2009, date(2009, 3, 15)), "0708": (2008, date(2008, 3, 16)), "0607": (2007, date(2007, 3, 11)),
           "0506": (2006, date(2006, 3, 12))}       # code -> (hoopR season, Selection Sunday)
csv.field_size_limit(10 ** 9)

clean = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&", "and").replace("state", "st"))

def rows(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
        yield from csv.DictReader(f)

def pick(r, *names, default=""):
    for n in names:
        v = r.get(n)
        if v not in (None, "", "NA"): return v
    return default

def num(v):
    try: return int(float(v))
    except (TypeError, ValueError): return 0

def made_att(r, made, att, combined):
    """'3-7' from separate made / attempted columns, or from one 'm-a' column (older hoopR versions)."""
    if r.get(made) not in (None, "", "NA"): return f"{num(r[made])}-{num(r.get(att))}"
    m = re.findall(r"\d+", r.get(combined) or "")
    return f"{m[0]}-{m[1]}" if len(m) >= 2 else "0-0"

def eastern_day(stamp):
    """ESPN's UTC start time -> the US Eastern date the game was played on."""
    try: t = datetime.fromisoformat((stamp or "").replace("Z", "+00:00")[:19])
    except ValueError: return None
    return (t - timedelta(hours=5)).date()

def team_folders(base):
    folders = {}
    for conf in os.listdir(base):
        conf_path = os.path.join(base, conf)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                if os.path.isdir(os.path.join(conf_path, team)): folders[team] = conf
    return folders

def known_espn_ids():
    """ESPN team id -> our team names, from every season's espn_teams.json (newest seasons last, so they win)."""
    ids = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "seasons", "*", "espn_teams.json"))):
        try: m = json.load(open(path, encoding="utf-8"))
        except Exception: continue
        for name, tid in m.items(): ids[str(tid)].append(name)
    return ids

def match_teams(espn_teams, folders):
    """ESPN team id -> our folder name. espn_teams: id -> set of ESPN names."""
    known = known_espn_ids(); by_clean = {clean(t): t for t in folders}; out = {}
    for tid, names in espn_teams.items():
        # compared without punctuation: the folders drop a trailing period ("Ohio St") the espn_teams files keep
        hit = next((by_clean[clean(n)] for n in reversed(known.get(tid, [])) if clean(n) in by_clean), None)
        if not hit: hit = next((by_clean[clean(n)] for n in names if clean(n) in by_clean), None)
        if not hit:
            best = max(((SequenceMatcher(None, n.lower(), t.lower()).ratio(), t) for n in names for t in folders), default=(0, None))
            if best[0] >= 0.92: hit = best[1]
        if hit: out[tid] = hit
    return out

def main():
    codes = [a for a in sys.argv[1:] if a in SEASONS]
    if not codes:
        print("Name the seasons, e.g.  python tools/hoopr_season.py 0809     Known: " + " ".join(SEASONS)); return
    for code in codes:
        year, sunday = SEASONS[code]; src = os.path.join(HOOPR_DIR, str(year))
        pre, full = os.path.join(ROOT, "data", "seasons", code), os.path.join(ROOT, "data", "seasons", code + " full")
        if not os.path.isdir(pre):
            print(f"{code}: run  python tools/make_season_codes.py {code}  first"); continue
        if not all(os.path.exists(os.path.join(src, f)) for f in ("schedule.csv.gz", "player_box.csv.gz")):
            print(f"{code}: run  tools/hoopr_pbp.R {year}  first"); continue
        folders = team_folders(pre)
        if not os.path.isdir(full):
            # the full-season folder has the same teams
            for team, conf in folders.items(): os.makedirs(os.path.join(full, conf, team), exist_ok=True)
        print(f"{year - 1}-{year % 100:02d}: reading the hoopR schedule and box scores ...", flush=True)
        sched, espn_teams = {}, defaultdict(set)
        for r in rows(os.path.join(src, "schedule.csv.gz")):
            gid = pick(r, "id", "game_id")
            if pick(r, "status_type_completed", default="TRUE").upper() not in ("TRUE", "1"): continue
            day = eastern_day(pick(r, "date", "start_date", "game_date_time")) or None
            if day is None:
                try: day = date.fromisoformat(pick(r, "game_date")[:10])
                except ValueError: continue
            h, a = pick(r, "home_id", "home_team_id"), pick(r, "away_id", "away_team_id")
            for tid, side in ((h, "home"), (a, "away")):
                espn_teams[tid] |= {pick(r, f"{side}_location"), pick(r, f"{side}_display_name"), pick(r, f"{side}_short_display_name"), pick(r, f"{side}_name")} - {""}
            sched[gid] = {"date": day, "home": h, "away": a, "neutral": pick(r, "neutral_site").upper() in ("TRUE", "1"),
                          "arena": pick(r, "venue_full_name", "venue_name")}
        team_of = match_teams(espn_teams, folders)
        players = defaultdict(lambda: defaultdict(list))        # game id -> team id -> player lines
        for r in rows(os.path.join(src, "player_box.csv.gz")):
            gid, tid = pick(r, "game_id"), pick(r, "team_id")
            if gid not in sched or tid not in team_of: continue
            if pick(r, "did_not_play").upper() in ("TRUE", "1"): continue
            line = {"Name": pick(r, "athlete_display_name", "athlete_name"), "MIN": str(num(pick(r, "minutes", "min"))), "PTS": num(pick(r, "points", "pts")),
                    "FG": made_att(r, "field_goals_made", "field_goals_attempted", "fg"),
                    "3PT": made_att(r, "three_point_field_goals_made", "three_point_field_goals_attempted", "fg3"),
                    "FT": made_att(r, "free_throws_made", "free_throws_attempted", "ft"),
                    "REB": num(pick(r, "rebounds", "reb")), "AST": num(pick(r, "assists", "ast")), "PF": num(pick(r, "fouls", "pf")),
                    "TO": num(pick(r, "turnovers", "to")), "OREB": num(pick(r, "offensive_rebounds", "oreb")),
                    "DREB": num(pick(r, "defensive_rebounds", "dreb")), "STL": num(pick(r, "steals", "stl")), "BLK": num(pick(r, "blocks", "blk"))}
            players[gid][tid].append((pick(r, "starter").upper() in ("TRUE", "1"), line))
        team_reb = {}
        if os.path.exists(os.path.join(src, "team_box.csv.gz")):
            for r in rows(os.path.join(src, "team_box.csv.gz")):
                v = pick(r, "total_rebounds", "rebounds")
                if v: team_reb[(pick(r, "game_id"), pick(r, "team_id"))] = num(v)
        def totals(lines, gid, tid):
            t = {"PTS": 0, "FG": "0-0", "3PT": "0-0", "FT": "0-0"}
            for k in ("FG", "3PT", "FT"):
                m = sum(int(l[k].split("-")[0]) for l in lines); a = sum(int(l[k].split("-")[1]) for l in lines); t[k] = f"{m}-{a}"
            for k in ("PTS", "REB", "AST", "PF", "TO", "OREB", "DREB", "STL", "BLK"): t[k] = sum(l[k] for l in lines)
            t["REB"] = max(t["REB"], team_reb.get((gid, tid), 0))      # the team line counts team rebounds
            return t
        lists = defaultdict(list); kept = no_box = 0
        for gid, g in sched.items():
            h, a = team_of.get(g["home"]), team_of.get(g["away"])
            if not h or not a or h == a: continue
            ph, pa = players[gid].get(g["home"]), players[gid].get(g["away"])
            if not ph or not pa: no_box += 1; continue
            boxes = {}
            for tid, name, plist in ((g["home"], h, ph), (g["away"], a, pa)):
                starters = [l for s, l in plist if s][:5]; bench = [l for s, l in plist if not (s and l in starters)]
                lines = starters + bench
                boxes[name] = {"team_name": name, "starters_table": starters, "bench_table": bench, "team_totals": totals(lines, gid, tid)}
            post = g["date"] > sunday
            row = {"game_id": gid, "date": g["date"].strftime("%Y/%m/%d"), "away_team": a, "away_score": str(boxes[a]["team_totals"]["PTS"]),
                   "home_team": h, "home_score": str(boxes[h]["team_totals"]["PTS"]), "neutral": g["neutral"] or post, "arena": g["arena"], "source": SOURCE}
            if post: row["post"] = True
            box = {"game_id": gid, "game_info": "", "source": SOURCE, "teams": [boxes[a], boxes[h]]}
            for which, base in (("pre", pre), ("full", full)):
                if which == "pre" and post: continue
                for name in (h, a):
                    folder = os.path.join(base, folders[name], name)
                    os.makedirs(os.path.join(folder, "boxscores"), exist_ok=True)
                    with open(os.path.join(folder, "boxscores", gid + ".json"), "w", encoding="utf-8") as out:
                        json.dump(box, out, indent=1)
                    lists[(base, name)].append(row)
            kept += 1
        for (base, name), rs in lists.items():
            folder = os.path.join(base, folders[name], name); rs.sort(key=lambda r: r["date"])
            with open(os.path.join(folder, "games.json"), "w", encoding="utf-8") as out: json.dump([r["game_id"] for r in rs], out, indent=2)
            with open(os.path.join(folder, "game_scores.json"), "w", encoding="utf-8") as out: json.dump(rs, out, indent=4)
        matched = set(team_of.values()); missing = sorted(set(folders) - matched)
        per_team = Counter(name for (base, name) in lists if base == pre)
        print(f"   {len(sched)} ESPN games; {kept} between two of our {len(folders)} teams written ({no_box} more had no box score)")
        print(f"   teams with no ESPN match ({len(missing)}): {', '.join(missing) or 'none'}")
        thin = sorted(t for t in folders if per_team.get(t, 0) and len(json.load(open(os.path.join(pre, folders[t], t, 'games.json')))) < 15)
        if thin: print(f"   teams with fewer than 15 pre-tournament games ({len(thin)}): {', '.join(thin)}")

if __name__ == "__main__":
    main()

