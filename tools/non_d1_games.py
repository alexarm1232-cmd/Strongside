import os
import re
import csv
import sys
import json
from datetime import date
from collections import defaultdict, Counter

# Adds every game a Division I team played against a school outside Division I to the season's data, from the
# stats.ncaa.org files, so it is in the team's schedule, record, game logs and ratings like any other game:
#     python tools/non_d1_games.py              every built season
#     python tools/non_d1_games.py 2526 2425    only these
# For each such game it writes, in the Division I team's folder (the pre-tournament folder up to Selection Sunday,
# the full-season folder always): boxscores/<game id>.json with both teams' lines, and an entry in games.json and
# game_scores.json marked "non_d1". The ratings treat every school outside Division I as one opponent (Kenstat.NON_D1).
# Running it again replaces the entries it wrote before. Rebuild the pages afterwards (dashboard/main.py).
# Two passes over individual_stats.csv cover every season: the first reads each game's heading (date, the two teams
# in visitor-home order, arena), the second the box scores of just the games against schools outside Division I.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ncaa_stats_season import SEASONS, SOURCE, SOURCE_DIR, DATE, clean, line, minutes, pick, team_folders

SEASONS_DIR = os.path.join(ROOT, "data", "seasons")
csv.field_size_limit(10 ** 9)

def read_headings(labels):
    """contest id -> {season, date, arena, listed: [names] in visitor-home order}"""
    games = {}
    with open(os.path.join(SOURCE_DIR, "individual_stats.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["table_num"] != "1" or r["season"] not in labels: continue
            g = games.setdefault(r["contest_id"], {"season": r["season"], "date": None, "arena": "", "listed": []})
            col0 = (r.get("col0") or "").strip()
            m = DATE.match(col0)
            if m:
                g["date"] = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            elif r.get("S") not in (None, "") and col0:
                g["listed"].append(col0)
            elif col0 and not col0.lower().startswith("attendance") and not g["arena"]:
                g["arena"] = col0
    return games

def read_boxes(wanted):
    """contest id -> {cleaned team name: box} for just these games (the same box ncaa_stats_season.py writes)."""
    tables = defaultdict(lambda: defaultdict(list))
    with open(os.path.join(SOURCE_DIR, "individual_stats.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if r["contest_id"] in wanted and r["table_num"] != "1":
                tables[r["contest_id"]][r["table_num"]].append(r)
    boxes = {}
    for cid, by_table in tables.items():
        for rows in by_table.values():
            total = rows[-1] if rows else None
            if not total or not total.get("Name"): continue
            players = [r for r in rows[:-1] if (r.get("Name") or "").strip() and (r.get("Name") or "").strip().upper() != "TEAM"]
            boxes.setdefault(cid, {})[clean(total["Name"])] = {
                "team_name": total["Name"].strip(), "starters_table": [line(r) for r in players[:5]],
                "bench_table": [line(r) for r in players[5:]], "team_totals": line(total, with_name=False)}
    return boxes

def usual_arena(rows, team):
    """The arena most of the team's home games were in."""
    counts = Counter(r.get("arena") for r in rows if clean(r.get("home_team")) == clean(team) and r.get("arena")
                     and not r.get("neutral") and not r.get("non_d1"))
    return counts.most_common(1)[0][0] if counts else ""

def main():
    built = sorted(c for c in os.listdir(SEASONS_DIR) if c.isdigit() and c in SEASONS)
    codes = [a for a in sys.argv[1:] if a in SEASONS] or built
    print("Reading the game headings...", flush=True)
    headings = read_headings({SEASONS[c][0] for c in codes})
    found = {}          # contest id -> (season code, our team's cleaned name)
    for code in codes:
        label = SEASONS[code][0]
        folders = team_folders(os.path.join(SEASONS_DIR, code + " full") if os.path.isdir(os.path.join(SEASONS_DIR, code + " full")) else os.path.join(SEASONS_DIR, code))
        for cid, g in headings.items():
            if g["season"] != label or not g["date"] or len(g["listed"]) != 2: continue
            ours = [n for n in g["listed"] if clean(n) in folders]
            if len(ours) == 1:
                found[cid] = (code, folders)
    print(f"Reading the box scores of {len(found)} games against schools outside Division I...", flush=True)
    boxes = read_boxes(set(found))

    for code in codes:
        label, sunday = SEASONS[code]
        pre, full = os.path.join(SEASONS_DIR, code), os.path.join(SEASONS_DIR, code + " full")
        written, skipped, no_box, opponents = 0, 0, 0, Counter()
        new_rows = defaultdict(list)          # (base folder, conference, team) -> rows
        for cid, (c, folders) in found.items():
            if c != code: continue
            g = headings[cid]
            away, home = g["listed"]
            mine = home if clean(home) in folders else away
            other = away if mine == home else home
            box = boxes.get(cid, {})
            if clean(mine) not in box or clean(other) not in box:
                no_box += 1
                continue
            conf, team = folders[clean(mine)]
            for base in (pre, full):
                if base == pre and g["date"] > sunday: continue
                if not os.path.isdir(os.path.join(base, conf, team)): continue
                new_rows[(base, conf, team)].append((cid, g, home, away, box))
            opponents[other] += 1
        for (base, conf, team), games in new_rows.items():
            folder = os.path.join(base, conf, team)
            path = os.path.join(folder, "game_scores.json")
            rows = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
            rows = [r for r in rows if not r.get("non_d1")]          # the ones this tool wrote before go
            have = {(r["date"], clean(r["home_team"]), clean(r["away_team"])) for r in rows}
            arena_home = usual_arena(rows, team)
            os.makedirs(os.path.join(folder, "boxscores"), exist_ok=True)
            for cid, g, home, away, box in games:
                day = g["date"].strftime("%Y/%m/%d")
                if (day, clean(home), clean(away)) in have:            # already in the game list (an older source)
                    skipped += 1
                    continue
                at_home = clean(home) == clean(team)
                # names as stats.ncaa.org has them, the same as the team's other box scores (the ratings go by them)
                hb, ab = box[clean(home)], box[clean(away)]
                neutral = g["date"] > sunday or (at_home and bool(arena_home) and bool(g["arena"]) and g["arena"] != arena_home)
                row = {"game_id": cid, "date": day, "away_team": ab["team_name"], "away_score": str(ab["team_totals"]["PTS"]),
                       "home_team": hb["team_name"], "home_score": str(hb["team_totals"]["PTS"]), "neutral": neutral,
                       "arena": g["arena"], "source": SOURCE, "non_d1": True}
                if g["date"] > sunday:
                    row["post"] = True
                rows.append(row)
                with open(os.path.join(folder, "boxscores", cid + ".json"), "w", encoding="utf-8") as out:
                    json.dump({"game_id": cid, "game_info": "", "source": SOURCE, "teams": [ab, hb]}, out, indent=1)
                written += 1
            rows.sort(key=lambda r: r["date"])
            with open(path, "w", encoding="utf-8") as out:
                json.dump(rows, out, indent=4)
            with open(os.path.join(folder, "games.json"), "w", encoding="utf-8") as out:
                json.dump([r["game_id"] for r in rows], out, indent=2)
        print(f"{code}: {sum(opponents.values())} games against schools outside Division I | {written} team-folder entries written, "
              f"{skipped} already listed, {no_box} without a box score | most played: {opponents.most_common(3)}")

if __name__ == "__main__":
    main()
