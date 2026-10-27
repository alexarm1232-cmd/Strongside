import os
import re
import csv
import sys
import json
import glob

# PMPM, point margin per minute: a game's margin at the end of every minute played (minute 0 is the tip, 40 the
# end of regulation, each overtime five more). In a tournament game between two seeds it is from the lower seed's side
# (the bigger seed number): minus while the lower seed is behind, plus while it is ahead. Otherwise it is from the
# eventual winner's side.
#     python tools/pdem.py 2526 tournament        every game of the 2026 NCAA tournament (First Four included)
#     python tools/pdem.py 2526 upsets            only its upsets: the winner seeded 4 or more lines below the loser
#     python tools/pdem.py 2526 upsets 5          ... 5 or more lines below
#     python tools/pdem.py all upsets             the upsets of every tournament with a bracket on the site
#     python tools/pdem.py all tournament         every game of every one of those tournaments
#     python tools/pdem.py 2526 Duke              every game a team played that season
#     python tools/pdem.py 2526 6534658 6534657   these games, by game id
# Writes reports/pdem_<what>.csv, one row per game (the margin after each minute in columns m0, m1, ...), and
# reports/pdem_<what>_long.csv, one row per game-minute, for charts and models.
# Reads the season's play-by-play (data/seasons/<code> full/.../playbyplay/<game id>.json): each play has the period,
# the seconds left in it and both scores, so the score at the end of a minute is the score after the last play at or
# before that moment.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SEASONS_DIR = os.path.join(ROOT, "data", "seasons")
REPORTS = os.path.join(ROOT, "reports")
TEMPLATE = os.path.join(ROOT, "dashboard", "dashboard_template.html")
SEEDS = [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]        # the order of a region's slots in the bracket
ROUNDS = ["First Four", "First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]

def season_label(code):
    return f"20{code[:2]}-{code[2:]}"

def bracket(code):
    """The season's real bracket from the site's template: (the 64 teams in slot order, the winners of each round)."""
    text = open(TEMPLATE, encoding="utf-8").read()
    at = text.find(f"'{season_label(code)}': {{")
    if at < 0:
        raise SystemExit(f"No bracket for {season_label(code)} in the template.")
    block = text[at:text.find("]],", at)]
    names = lambda part: re.findall(r"'((?:[^'\\]|\\.)*)'|\"([^\"]*)\"", part)
    flat = lambda part: [a or b for a, b in names(part)]
    slots = flat(block[block.find("slots:"):block.find("winners:")])
    winners_part = block[block.find("winners:"):]
    rounds = [flat(r) for r in re.findall(r"\[([^\[\]]*)\]", winners_part)]
    return slots, rounds

def elapsed(play):
    """Seconds played when this play happened: two 20-minute halves, then 5-minute overtimes."""
    period, left = play["period"], play.get("seconds_left") or 0
    if period <= 2:
        return (period - 1) * 1200 + (1200 - left)
    return 2400 + (period - 3) * 300 + (300 - left)

def pdem(pbp):
    """[(minute, home score, away score)] at the end of each minute, minute 0 included."""
    plays = sorted(((elapsed(p), i, p["home_score"], p["away_score"]) for i, p in enumerate(pbp["plays"])
                    if p.get("home_score") is not None), key=lambda x: (x[0], x[1]))
    if not plays:
        return []
    last_period = max(p["period"] for p in pbp["plays"])
    minutes = 40 + 5 * max(0, last_period - 2)
    out, k, home, away = [], 0, 0, 0
    for m in range(minutes + 1):
        while k < len(plays) and plays[k][0] <= 60 * m:
            home, away = plays[k][2], plays[k][3]
            k += 1
        out.append((m, home, away))
    if k < len(plays):                    # anything logged after the last whistle (a late correction) counts at the end
        out[-1] = (minutes, plays[-1][2], plays[-1][3])
    return out

def season_games(code):
    """game id -> (its game_scores.json entry, the path of its play-by-play file)."""
    games = {}
    base = os.path.join(SEASONS_DIR, code + " full")
    if not os.path.isdir(base): base = os.path.join(SEASONS_DIR, code)
    for path in glob.glob(os.path.join(base, "*", "*", "game_scores.json")):
        folder = os.path.dirname(path)
        for row in json.load(open(path, encoding="utf-8")):
            pbp = os.path.join(folder, "playbyplay", str(row["game_id"]) + ".json")
            if str(row["game_id"]) not in games or (os.path.exists(pbp) and not os.path.exists(games[str(row["game_id"])][1])):
                games[str(row["game_id"])] = (row, pbp)
    return games

def tournament_games(code, games, upsets=None):
    """The season's NCAA tournament games (with the round and seeds), or only its upsets of this many seed lines."""
    slots, rounds = bracket(code)
    clean = lambda name: name.rstrip(". ")
    field = {clean(t) for t in slots}
    seed = {clean(t): SEEDS[i % 16] for i, t in enumerate(slots)}
    won = {clean(t): sum(clean(t) in {clean(x) for x in r} for r in rounds) for t in slots}   # rounds each team won
    info = {}
    for gid, (row, _) in games.items():
        teams = [clean(row["home_team"]), clean(row["away_team"])]
        # bracket teams play no other postseason event, so a postseason game with one of them is a tournament game
        if not row.get("post") or not any(t in field for t in teams): continue
        hs, as_ = int(row["home_score"]), int(row["away_score"])
        winner, loser = (teams[0], teams[1]) if hs > as_ else (teams[1], teams[0])
        rnd = 0 if loser not in field else won.get(loser, 0) + 1          # First Four: the loser never made the 64
        ws, ls = seed.get(winner, ""), seed.get(loser, "") or seed.get(winner, "")   # a First Four loser shares its slot's seed
        info[gid] = {"round": ROUNDS[rnd], "winner_seed": ws, "loser_seed": ls,
                     "seed_gap": ws - ls if ws != "" and ls != "" else ""}
    if upsets is not None:
        info = {gid: v for gid, v in info.items() if v["seed_gap"] != "" and v["seed_gap"] >= upsets}
    return info

def series_rows(code, games, chosen, info):
    rows, missing = [], []
    for gid in chosen:
        row, path = games[gid]
        if not os.path.exists(path):
            missing.append(f"{row['date']} {row['away_team']} at {row['home_team']}"); continue
        series = pdem(json.load(open(path, encoding="utf-8")))
        hs, as_ = int(row["home_score"]), int(row["away_score"])
        home_won = hs > as_
        winner, loser = (row["home_team"], row["away_team"]) if home_won else (row["away_team"], row["home_team"])
        extra = info.get(gid, {})
        # whose side: the lower seed (the bigger number) when the seeds differ, else the winner
        lower_won = extra.get("seed_gap", 0) == "" or extra.get("seed_gap", 0) >= 0
        side_home = home_won if lower_won else not home_won
        margins = [(h - a) if side_home else (a - h) for _, h, a in series]
        final = (hs - as_) if side_home else (as_ - hs)
        if margins and margins[-1] != final:
            print(f"   note: {row['date']} {winner}-{loser}: the play-by-play ends at {margins[-1]:+d}, the final score says {final:+d}")
        rows.append({"season": season_label(code), "game_id": gid, "date": row["date"], **extra,
                     "lower_seed_won": ("yes" if lower_won and extra.get("seed_gap", 0) not in ("", 0) else
                                        "no" if extra.get("seed_gap", 0) not in ("", 0) else "") if extra else "",
                     "winner": winner, "loser": loser, "winner_pts": max(hs, as_), "loser_pts": min(hs, as_),
                     "final_margin": final, "site": "neutral" if row.get("neutral") else f"at {row['home_team']}",
                     "minutes": len(margins) - 1, "margins": margins})
    return rows, missing

def write(rows, what, with_round):
    os.makedirs(REPORTS, exist_ok=True)
    most = max(r["minutes"] for r in rows)
    head = [k for k in rows[0] if k != "margins"]
    wide = os.path.join(REPORTS, f"pdem_{what}.csv")
    with open(wide, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(head + [f"m{m}" for m in range(most + 1)])
        for r in rows:
            out.writerow([r.get(k, "") for k in head] + r["margins"] + [""] * (most - r["minutes"]))
    long = os.path.join(REPORTS, f"pdem_{what}_long.csv")
    with open(long, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(["season", "game_id", "date"] + (["round", "winner_seed", "loser_seed"] if with_round else []) + ["winner", "loser", "minute", "margin"])
        for r in rows:
            for m, v in enumerate(r["margins"]):
                out.writerow([r["season"], r["game_id"], r["date"]] + ([r.get("round", ""), r.get("winner_seed", ""), r.get("loser_seed", "")] if with_round else [])
                             + [r["winner"], r["loser"], m, v])
    print(f"{len(rows)} games ({sum(r['minutes'] > 40 for r in rows)} went to overtime)")
    print(f"   {os.path.relpath(wide, ROOT)}\n   {os.path.relpath(long, ROOT)}")

def main():
    args = sys.argv[1:]
    built = sorted((c for c in os.listdir(SEASONS_DIR) if re.fullmatch(r"\d{4}", c)), reverse=True)
    if args and args[0] == "all":
        codes, rest = [c for c in built if f"'{season_label(c)}': {{" in open(TEMPLATE, encoding="utf-8").read()], args[1:]
    else:
        code = next((a for a in args if a in built), "2526")
        codes, rest = [code], [a for a in args if a != code]
    upsets = None
    if rest and rest[0] == "upsets":
        upsets = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 4
    tournament = not rest or rest[0] in ("tournament", "upsets")
    rows, missing = [], []
    for code in codes:
        games = season_games(code)
        if tournament:
            info = tournament_games(code, games, upsets)
            chosen = list(info)
        else:
            info = {}
            ids = [a for a in rest if a.isdigit()]
            team = " ".join(a for a in rest if not a.isdigit()).lower().rstrip(". ")
            chosen = ids or [gid for gid, (row, _) in games.items()
                             if team in (row["home_team"].lower().rstrip(". "), row["away_team"].lower().rstrip(". "))]
        got, lost = series_rows(code, games, chosen, info)
        rows += got
        missing += lost
        if len(codes) > 1:
            print(f"{season_label(code)}: {len(got)} games")
    if not rows:
        raise SystemExit("No games found.")
    if missing:
        print(f"   no play-by-play for {len(missing)}: {missing[:6]}")
    order = {r: i for i, r in enumerate(ROUNDS)}
    rows.sort(key=lambda r: (r["date"], order.get(r.get("round"), 0), r["winner"]))
    name = ("all" if len(codes) > 1 else season_label(codes[0]).replace("-", ""))
    if tournament:
        what = f"{name}_ncaa_tournament" + (f"_upsets_{upsets}plus" if upsets is not None else "")
    else:
        what = f"{name}_" + (re.sub(r"[^a-z0-9]+", "_", " ".join(rest).lower()).strip("_") or "games")
    write(rows, what, tournament)

if __name__ == "__main__":
    main()
