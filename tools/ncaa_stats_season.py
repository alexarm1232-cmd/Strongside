import os
import re
import csv
import sys
import json
import shutil
from datetime import date, timedelta
from collections import defaultdict, Counter

# Builds a season's game list and box scores straight from the stats.ncaa.org files ("data/ncaa stats" folder),
# in place of the NCAA scoreboard (steps 2 and 3) and the Sports Reference box scores (step 8):
#     python tools/ncaa_stats_season.py 2223
# Writes, for every game between two of the season's Division I teams:
#   games.json, game_scores.json   in both teams' folders: date, the two teams, the score, neutral floor or not
#   boxscores/<game id>.json       every player's line and the team totals (which count team rebounds)
# The pre-tournament folder ("data/seasons/2223") gets the games up to Selection Sunday; the full-season folder
# ("data/seasons/2223 full") gets every game, postseason included. Game ids are the site's own (contest ids).
# A team's earlier games.json / game_scores.json are kept as games_before_ncaa_stats.json / ..._before_ncaa_stats.json.
# Rosters still come from Sports Reference (5rosterfetch.py), and the play-by-play from ncaa_stats_reader.py.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SOURCE_DIR = os.path.join(ROOT, "data/ncaa stats")
SOURCE = "stats.ncaa.org"
SEASONS = {   # code: (the site's season label, Selection Sunday)
    "2526": ("2025-2026", date(2026, 3, 15)), "2425": ("2024-2025", date(2025, 3, 16)), "2324": ("2023-2024", date(2024, 3, 17)),
    "2223": ("2022-2023", date(2023, 3, 12)), "2122": ("2021-2022", date(2022, 3, 13)), "2021": ("2020-2021", date(2021, 3, 14)),
    "1920": ("2019-2020", date(2020, 3, 15)), "1819": ("2018-2019", date(2019, 3, 17)), "1718": ("2017-2018", date(2018, 3, 11)),
    "1617": ("2016-2017", date(2017, 3, 12)), "1516": ("2015-2016", date(2016, 3, 13)), "1415": ("2014-2015", date(2015, 3, 15)),
    "1314": ("2013-2014", date(2014, 3, 16)), "1213": ("2012-2013", date(2013, 3, 17)), "1112": ("2011-2012", date(2012, 3, 11)),
    "1011": ("2010-2011", date(2011, 3, 13)), "0910": ("2009-2010", date(2010, 3, 14)),
}
DATE = re.compile(r"^(\d\d)/(\d\d)/(\d{4})")
csv.field_size_limit(10 ** 9)

def clean(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def number(text):
    try:
        return int(float(str(text).replace(",", "") or 0))
    except ValueError:
        return 0

def minutes(text):
    """'28:05' -> '28.08'"""
    parts = re.findall(r"\d+", str(text or ""))
    if len(parts) >= 2:
        return str(round(int(parts[0]) + int(parts[1]) / 60, 2))
    return str(number(text))

def pick(row, *names):
    """The first of these columns that has a value: the site has renamed some over the years (2012-13 and earlier
    say "Off Reb" / "Def Reb" where later seasons say "ORebs" / "DRebs")."""
    for name in names:
        if (row.get(name) or "").strip():
            return row[name]
    return ""

def line(row, with_name=True):
    out = {"PTS": number(row["PTS"]), "FG": f"{number(row['FGM'])}-{number(row['FGA'])}", "3PT": f"{number(row['3FG'])}-{number(row['3FGA'])}",
           "FT": f"{number(row['FT'])}-{number(row['FTA'])}", "REB": number(row["Tot Reb"]), "AST": number(row["AST"]),
           "PF": number(row["Fouls"]), "TO": number(row["TO"]), "OREB": number(pick(row, "ORebs", "Off Reb")),
           "DREB": number(pick(row, "DRebs", "Def Reb")), "STL": number(row["STL"]), "BLK": number(row["BLK"])}
    if with_name:
        out = dict({"Name": row["Name"].strip(), "MIN": minutes(pick(row, "MP", "Min"))}, **out)
    return out

def read_games(label):
    """contest id -> {date, arena, teams: [names in the order listed], boxes: {cleaned team name: box}}"""
    games = {}
    with open(os.path.join(SOURCE_DIR, "individual_stats.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["season"] != label: continue
            g = games.setdefault(r["contest_id"], {"date": None, "arena": "", "listed": [], "tables": defaultdict(list)})
            if r["table_num"] == "1":
                col0 = (r.get("col0") or "").strip()
                m = DATE.match(col0)
                if m:
                    g["date"] = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
                elif r.get("S") not in (None, "") and col0:
                    g["listed"].append(col0)
                elif col0 and not col0.lower().startswith("attendance") and not g["arena"]:
                    g["arena"] = col0
            else:
                g["tables"][r["table_num"]].append(r)
    for g in games.values():
        g["boxes"] = {}
        for rows in g["tables"].values():
            total = rows[-1] if rows else None
            if not total or not total.get("Name"): continue
            players = [r for r in rows[:-1] if (r.get("Name") or "").strip() and (r.get("Name") or "").strip().upper() != "TEAM"]
            played = [r for r in players if minutes(pick(r, "MP", "Min")) not in ("0", "0.0")]
            g["boxes"][clean(total["Name"])] = {
                "team_name": total["Name"].strip(),
                # the site lists the five starters first
                "starters_table": [line(r) for r in players[:5]],
                "bench_table": [line(r) for r in players[5:]],
                "team_totals": line(total, with_name=False),
                "played": len(played)}
        del g["tables"]
    return games

def home_and_away(label):
    """contest id -> (home team name, away team name) as the play-by-play has them."""
    sides = {}
    with open(os.path.join(SOURCE_DIR, "play_by_play.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["season"] == label and r["contest_id"] not in sides:
                sides[r["contest_id"]] = (r["home_team"], r["away_team"])
    return sides

def team_folders(base):
    folders = {}
    for conf in os.listdir(base):
        conf_path = os.path.join(base, conf)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                if os.path.isdir(os.path.join(conf_path, team)):
                    folders[clean(team)] = (conf, team)
    return folders

def existing_games(bases):
    """(date, the two teams) -> (game id, neutral, arena) from a season's game lists as they are now. A game that is
    already listed keeps its id, so whatever else is filed under it (shot spots, betting lines) stays attached."""
    known = {}
    for base in bases:
        if not os.path.isdir(base): continue
        for conf in os.listdir(base):
            conf_path = os.path.join(base, conf)
            if not os.path.isdir(conf_path): continue
            for team in os.listdir(conf_path):
                for name in ("game_scores.json",):
                    path = os.path.join(conf_path, team, name)
                    if not os.path.exists(path): continue
                    try:
                        rows = json.load(open(path, encoding="utf-8"))
                    except Exception:
                        continue
                    for r in rows:
                        key = (r.get("date"), frozenset((clean(r.get("home_team")), clean(r.get("away_team")))))
                        known.setdefault(key, (str(r.get("game_id")), r.get("neutral"), r.get("arena", "")))
    return known

def set_aside_boxscores(bases):
    """Box scores from another source go to boxscores_before_ncaa_stats (kept); an earlier run's own are cleared."""
    for base in bases:
        if not os.path.isdir(base): continue
        for conf in os.listdir(base):
            conf_path = os.path.join(base, conf)
            if not os.path.isdir(conf_path): continue
            for team in os.listdir(conf_path):
                box, kept = os.path.join(conf_path, team, "boxscores"), os.path.join(conf_path, team, "boxscores_before_ncaa_stats")
                if not os.path.isdir(box): continue
                if not os.path.exists(kept):
                    os.rename(box, kept)
                else:
                    shutil.rmtree(box)

def main():
    code = next((a for a in sys.argv[1:] if a in SEASONS), None)
    if not code:
        print("Name a season, e.g.  python tools/ncaa_stats_season.py 2223")
        return
    label, sunday = SEASONS[code]
    pre = os.path.join(ROOT, f"data/seasons/{code}")
    full = os.path.join(ROOT, f"data/seasons/{code} full")
    if not os.path.isdir(pre):
        print(f"{pre} does not exist; run make_season_codes.py {code} first.")
        return
    folders = team_folders(pre)
    known = existing_games([pre, full])
    print(f"Reading the {label} box scores...", flush=True)
    games = read_games(label)
    sides = home_and_away(label)
    # Which games are ours: both teams on the season's Division I list
    kept, not_ours, unnamed = [], Counter(), 0
    for cid, g in games.items():
        if not g["date"] or len(g["boxes"]) != 2:
            unnamed += 1
            continue
        home, away = sides.get(cid, (g["listed"][1], g["listed"][0]) if len(g["listed"]) == 2 else (None, None))
        if not home or clean(home) not in folders or clean(away) not in folders:
            not_ours.update(n for n in (home, away) if n and clean(n) not in folders)
            continue
        if clean(home) not in g["boxes"] or clean(away) not in g["boxes"]:
            unnamed += 1
            continue
        kept.append((cid, g, home, away))
    # A neutral floor: the game was not played in the home team's usual arena (the one most of its home games are in)
    usual = defaultdict(Counter)
    for cid, g, home, away in kept:
        if g["arena"]:
            usual[clean(home)][g["arena"]] += 1
    lists = defaultdict(list)       # (pre or full, team) -> game_scores rows
    boxes = matched = 0
    set_aside_boxscores([pre, full])
    for cid, g, home, away in kept:
        arena_counts = usual[clean(home)]
        home_arena = arena_counts.most_common(1)[0][0] if arena_counts else ""
        neutral = bool(g["arena"]) and bool(home_arena) and g["arena"] != home_arena and arena_counts[g["arena"]] <= 1
        arena = g["arena"]
        # a game the season already lists keeps its id (and its neutral-floor call), so files filed under it stay attached
        pair = frozenset((clean(home), clean(away)))
        before = next((known[k] for shift in (0, -1, 1)
                       for k in [((g["date"] + timedelta(days=shift)).strftime("%Y/%m/%d"), pair)] if k in known), None)
        if before:
            cid, neutral, arena = before[0], bool(before[1]), before[2] or arena
            matched += 1
        hb, ab = g["boxes"][clean(home)], g["boxes"][clean(away)]
        row = {"game_id": cid, "date": g["date"].strftime("%Y/%m/%d"), "away_team": away, "away_score": str(ab["team_totals"]["PTS"]),
               "home_team": home, "home_score": str(hb["team_totals"]["PTS"]), "neutral": neutral, "arena": arena, "source": SOURCE}
        if g["date"] > sunday:
            row["post"] = True
        box = {"game_id": cid, "game_info": "", "source": SOURCE,
               "teams": [{k: v for k, v in b.items() if k != "played"} for b in (ab, hb)]}
        for which, base in (("pre", pre), ("full", full)):
            if which == "pre" and g["date"] > sunday: continue
            for name in (home, away):
                conf, team = folders[clean(name)]
                folder = os.path.join(base, conf, team)
                os.makedirs(os.path.join(folder, "boxscores"), exist_ok=True)
                with open(os.path.join(folder, "boxscores", cid + ".json"), "w", encoding="utf-8") as out:
                    json.dump(box, out, indent=1)
                boxes += 1
                lists[(which, conf, team)].append(row)
    for (which, conf, team), rows in lists.items():
        folder = os.path.join(pre if which == "pre" else full, conf, team)
        for name in ("games.json", "game_scores.json"):
            path = os.path.join(folder, name)
            kept_copy = path.replace(".json", "_before_ncaa_stats.json")
            if os.path.exists(path) and not os.path.exists(kept_copy):
                shutil.copyfile(path, kept_copy)
        rows.sort(key=lambda r: r["date"])
        with open(os.path.join(folder, "games.json"), "w", encoding="utf-8") as out:
            json.dump([r["game_id"] for r in rows], out, indent=2)
        with open(os.path.join(folder, "game_scores.json"), "w", encoding="utf-8") as out:
            json.dump(rows, out, indent=4)
    pre_games = sum(1 for _, g, _, _ in kept if g["date"] <= sunday)
    neutral_games = sum(1 for r in {r["game_id"]: r for rows in lists.values() for r in rows}.values() if r["neutral"])
    if known:
        print(f"   {matched} of {len(kept)} games matched to games the season already listed (their ids kept); {len(kept) - matched} new")
    print(f"{label}: {len(games)} games in the files | {len(kept)} between two of our teams ({pre_games} up to Selection Sunday, "
          f"{len(kept) - pre_games} after) | {neutral_games} on a neutral floor | {boxes} team box score files written")
    print(f"   left out: {sum(not_ours.values())} team-games against schools not on our list, {unnamed} games with no usable box score")
    print("   schools not on our list, most games first:", not_ours.most_common(12))
    counts = Counter()
    for (which, conf, team), rows in lists.items():
        if which == "pre": counts[team] = len(rows)
    missing = [t for _, t in folders.values() if t not in counts]
    print("   games per team up to Selection Sunday: fewest", sorted((n, t) for t, n in counts.items())[:6], "| teams with none:", missing)

if __name__ == "__main__":
    main()
