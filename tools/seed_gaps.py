import os
import csv
import glob
import json
import pdem_ratings

# Three seedings of each NCAA tournament, side by side:   python tools/seed_gaps.py
#   real   the committee's seeds;
#   mixed  ("our_seed") the committee's process on the real field, with Strongside's net rating doing the ranking;
#   pure   our own field (every automatic qualifier, then the best other teams by net rating until the field is the
#          real one's size) seeded by net rating with the same seed-line rule.
# The real field (all 68 teams, First Four losers included) and seeds come from reports/tournament_spreads.csv;
# each team's net rating is its Selection Sunday rating from the season's pre-tournament page.
# The mixed seeds follow the committee's steps, with our net rating in place of its judgment:
#   1. the 68 teams in order of net rating make the "true seed list";
#   2. the First Four is the four lowest automatic qualifiers and the four lowest at-large teams on that list
#      (an automatic qualifier is a team whose last game before Selection Sunday was a win, which only a conference
#      tournament champion's is; a one-bid conference's team is one either way);
#   3. down the list, each team takes the next of the 64 bracket spots, four to a seed line, except that the second
#      team of a First Four pair shares its partner's spot.
# Placing teams in regions and pods (geography, conference separation) does not change seed lines, so it is left out.
# Writes reports/seed_gaps.csv: one row per team in either field, with the gaps in seed lines (real minus mixed, and
# real minus pure: plus means the committee seeded the team worse than its net rating would) and which field it is in.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
PAGES = os.path.join(ROOT, "dashboard")
# teams that could not be picked: postseason bans (NCAA academic-progress or self-imposed), the cases known to us
BANNED = {("2012-13", "UConn"), ("2014-15", "Syracuse"), ("2015-16", "Louisville"), ("2015-16", "SMU"), ("2015-16", "Missouri")}

def pre_pages():
    for path in [os.path.join(PAGES, "dashboard.html")] + glob.glob(os.path.join(PAGES, "dashboard_*.html")):
        if path.endswith(("_full.html", "_template.html", "upsets.html")): continue
        data = pdem_ratings.page_data(path)
        if data["meta"].get("view", "pre") == "pre":
            yield data["meta"]["season"], data["teams"]

def won_last(team):
    """a team in the field whose last game before Selection Sunday was a win has won its conference tournament: any
    other team in the field ended its season before the NCAAs with a loss there"""
    games = sorted(team.get("sched", []), key=lambda g: g["d"])
    return bool(games) and games[-1]["pf"] > games[-1]["pa"]

def seed_lines(entrants, auto):
    """team -> (seed line, in a First Four game), for a field in order of the true seed list"""
    autos = [t["name"] for t in entrants if t["name"] in auto]
    larges = [t["name"] for t in entrants if t["name"] not in auto]
    # First Four pairs: the last four of each kind, in pairs by rank; the lower of each pair shares its partner's
    # spot. Before 2011 the field was 65, with one opening-round game between the two lowest automatic qualifiers.
    extra = len(entrants) - 64
    pairs = [autos[-4:-2], autos[-2:], larges[-4:-2], larges[-2:]] if extra >= 4 else [autos[-2:]] if extra == 1 else []
    partner = {b: a for a, b in pairs}
    in_play_in = {n for p in pairs for n in p}
    spot, spots, out = 0, {}, {}
    for t in entrants:
        if t["name"] in partner: spots[t["name"]] = spots[partner[t["name"]]]
        else: spot += 1; spots[t["name"]] = spot
        out[t["name"]] = (min(16, (spots[t["name"]] - 1) // 4 + 1), t["name"] in in_play_in)
    return out

def main():
    field, real = {}, {}
    for s in csv.DictReader(open(os.path.join(REPORTS, "tournament_spreads.csv"), encoding="utf-8")):
        for team, seed in ((s["winner"], s["winner_seed"]), (s["loser"], s["loser_seed"])):
            field.setdefault(s["season"], set()).add(team)
            real[(s["season"], team)] = int(seed)
    # 2021: VCU (a 10 seed) was in the field but its game with Oregon was cancelled, so no spread row has it
    field["2020-21"].add("VCU"); real[("2020-21", "VCU")] = 10
    rows = []
    for season, teams in sorted(pre_pages()):
        if season not in field: continue
        by_name = {t["name"]: t for t in teams}
        missing = [n for n in field[season] if n not in by_name or by_name[n].get("n") is None]
        if missing: print(season, "no rating for", missing)
        entrants = sorted((by_name[n] for n in field[season] if n not in missing), key=lambda t: -t["n"])
        bids = {}
        for t in entrants: bids[t["conf"]] = bids.get(t["conf"], 0) + 1
        # a team that left its conference tournament early (2021) also ends on a win, so of the teams that ended on a
        # win in the same conference tournament (their last opponents' conference) only the latest one is its champion
        conf_of = {t["name"]: t["conf"] for t in teams}
        latest = {}
        for t in entrants:
            if not won_last(t): continue
            g = max(t["sched"], key=lambda g: g["d"])
            key = conf_of.get(g["opp"], t["conf"])
            if g["d"] > latest.get(key, ("", ""))[0]: latest[key] = (g["d"], t["name"])
        auto = {name for d, name in latest.values()} | {t["name"] for t in entrants if bids[t["conf"]] == 1}
        print(season, len(auto), "automatic qualifiers")
        mixed = seed_lines(entrants, auto)
        # purely ours: the same automatic qualifiers, then the best of everyone else by net rating until the field is
        # as big as the real one, seeded by net rating with the same seed-line rule
        rated = sorted((t for t in teams if t.get("n") is not None and (season, t["name"]) not in BANNED), key=lambda t: -t["n"])
        ours_field = [t for t in rated if t["name"] in auto]
        ours_field += [t for t in rated if t["name"] not in auto][:len(entrants) - len(ours_field)]
        ours_field.sort(key=lambda t: -t["n"])
        pure = seed_lines(ours_field, auto)
        rank_all = {t["name"]: i for i, t in enumerate(rated, 1)}
        for t in sorted({t["name"]: t for t in entrants + ours_field}.values(), key=lambda t: -t["n"]):
            name, r = t["name"], real.get((season, t["name"]))
            m, p = mixed.get(name, (None, "")), pure.get(name, (None, ""))
            rows.append({"season": season, "year": int(season[:4]) + 1, "team": name, "conf": t["conf"],
                         "bid": "auto" if name in auto else "at-large", "net": round(t["n"], 1), "net_rank": rank_all[name],
                         "pure_seed": p[0] or "", "our_seed": m[0] or "", "real_seed": r or "",
                         "gap": r - m[0] if r and m[0] else "", "pure_gap": r - p[0] if r and p[0] else "",
                         "first_four": "yes" if m[1] else "", "in": "both" if r and p[0] else "real only" if r else "ours only"})
    with open(os.path.join(REPORTS, "seed_gaps.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "teams,", len({r["season"] for r in rows}), "tournaments")

if __name__ == "__main__":
    main()
