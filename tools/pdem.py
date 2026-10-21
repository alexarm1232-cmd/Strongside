import os
import re
import csv
import sys
import json
import glob

# PDEM, point difference each minute: for a game, the winning team's points minus the losing team's at the end of
# every minute played (minute 0 is the tip; 40 is the end of regulation; each overtime adds five more).
#     python tools/pdem.py                        every game of the 2026 NCAA tournament (First Four included)
#     python tools/pdem.py 2526 upsets            only its upsets: the winner seeded 4 or more lines below the loser
#     python tools/pdem.py 2526 upsets 5          ... 5 or more lines below
#     python tools/pdem.py 2425 tournament         another season's tournament (its bracket must be on the site)
#     python tools/pdem.py 2526 Duke               every game a team played that season
#     python tools/pdem.py 2526 6534658 6534657    these games, by game id
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

def main():
    args = sys.argv[1:]
    code = next((a for a in args if re.fullmatch(r"\d{4}", a) and os.path.isdir(os.path.join(SEASONS_DIR, a))), "2526")
    rest = [a for a in args if a != code]
    upsets = None
    if rest and rest[0] == "upsets":
        upsets = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 4
        rest = ["tournament"]
    games = season_games(code)
    info = {}                                  # game id -> extra columns (round, seeds)
    if not rest or rest == ["tournament"]:
        slots, rounds = bracket(code)
        seed = {team: SEEDS[i % 16] for i, team in enumerate(slots)}
        field = set(slots)
        clean = lambda s: s.rstrip(". ")
        chosen = []
        for gid, (row, _) in games.items():
            teams = [clean(row["home_team"]), clean(row["away_team"])]
            if not row.get("post") or not any(t in {clean(s) for s in field} for t in teams): continue
            chosen.append(gid)
        # the round: First Four games are the ones with a team not in the 64; then by how far the winner had come
        won = {clean(t): sum(clean(t) in {clean(x) for x in r} for r in rounds) for t in slots}
        for gid in chosen:
            row = games[gid][0]
            hs, as_ = int(row["home_score"]), int(row["away_score"])
            winner, loser = (row["home_team"], row["away_team"]) if hs > as_ else (row["away_team"], row["home_team"])
            if clean(loser) not in {clean(s) for s in field}:
                rnd = 0
            else:
                # games a team played in the 64: the loser's last one is this one
                rnd = won.get(clean(loser), 0) + 1
            ws = seed.get(next((s for s in slots if clean(s) == clean(winner)), ""), "")
            ls = seed.get(next((s for s in slots if clean(s) == clean(loser)), ""), "") or ws    # a First Four loser shares the slot's seed
            info[gid] = {"round": ROUNDS[rnd], "winner_seed": ws, "loser_seed": ls,
                         "seed_gap": ws - ls if ws != "" and ls != "" else ""}
        what = f"{season_label(code)}_ncaa_tournament".replace("-", "")
        if upsets is not None:
            chosen = [gid for gid in chosen if info[gid]["seed_gap"] != "" and info[gid]["seed_gap"] >= upsets]
            what += f"_upsets_{upsets}plus"
    else:
        ids = [a for a in rest if a.isdigit()]
        team = " ".join(a for a in rest if not a.isdigit())
        chosen = ids or [gid for gid, (row, _) in games.items()
                         if team.lower().rstrip(". ") in (row["home_team"].lower().rstrip(". "), row["away_team"].lower().rstrip(". "))]
        what = f"{code}_" + (re.sub(r"[^a-z0-9]+", "_", team.lower()).strip("_") if team else "games")
    if not chosen:
        raise SystemExit("No games found.")

    rows, missing = [], []
    for gid in chosen:
        row, path = games[gid]
        if not os.path.exists(path):
            missing.append(gid); continue
        series = pdem(json.load(open(path, encoding="utf-8")))
        hs, as_ = int(row["home_score"]), int(row["away_score"])
        home_won = hs > as_
        winner, loser = (row["home_team"], row["away_team"]) if home_won else (row["away_team"], row["home_team"])
        margins = [(h - a) if home_won else (a - h) for _, h, a in series]
        if margins and margins[-1] != abs(hs - as_):
            print(f"   note: {row['date']} {winner}-{loser}: the play-by-play ends at {margins[-1]:+d}, the final score says {abs(hs - as_):+d}")
        rows.append({"game_id": gid, "date": row["date"], **info.get(gid, {}), "winner": winner, "loser": loser,
                     "winner_pts": max(hs, as_), "loser_pts": min(hs, as_), "final_margin": abs(hs - as_),
                     "site": "neutral" if row.get("neutral") else f"at {row['home_team']}", "minutes": len(margins) - 1,
                     "margins": margins})
    order = {r: i for i, r in enumerate(ROUNDS)}
    rows.sort(key=lambda r: (r["date"], order.get(r.get("round"), 0), r["winner"]))

    os.makedirs(REPORTS, exist_ok=True)
    most = max(r["minutes"] for r in rows)
    head = [k for k in rows[0] if k != "margins"]
    wide = os.path.join(REPORTS, f"pdem_{what}.csv")
    with open(wide, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(head + [f"m{m}" for m in range(most + 1)])
        for r in rows:
            out.writerow([r[k] for k in head] + r["margins"] + [""] * (most - r["minutes"]))
    long = os.path.join(REPORTS, f"pdem_{what}_long.csv")
    with open(long, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(["game_id", "date"] + (["round"] if info else []) + ["winner", "loser", "minute", "margin"])
        for r in rows:
            for m, v in enumerate(r["margins"]):
                out.writerow([r["game_id"], r["date"]] + ([r.get("round", "")] if info else []) + [r["winner"], r["loser"], m, v])
    print(f"{len(rows)} games ({sum(r['minutes'] > 40 for r in rows)} went to overtime)" +
          (f"; no play-by-play for {len(missing)}: {missing}" if missing else ""))
    print(f"   {os.path.relpath(wide, ROOT)}\n   {os.path.relpath(long, ROOT)}")

if __name__ == "__main__":
    main()
