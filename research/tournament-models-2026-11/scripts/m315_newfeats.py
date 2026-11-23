# New pre-tournament measures from the game logs (not in the 286 pool): rest, conference-tournament load, late-season form,
# win streak, won last game, home dependence, travel distance to the Round 1 site. Saved per (season, team).
import os, json, glob, math, re, datetime as dt
from collections import Counter
ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"; HERE = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, HERE)
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
from m210_followups import kk
G = Q.R.B.G
ST = {"AL": (32.8, -86.8), "AK": (61.4, -152.3), "AZ": (34.2, -111.7), "AR": (34.9, -92.4), "CA": (36.8, -119.4), "CO": (39.0, -105.5),
      "CT": (41.6, -72.7), "DE": (39.0, -75.5), "DC": (38.9, -77.0), "FL": (28.6, -82.4), "GA": (32.7, -83.4), "HI": (20.8, -156.3),
      "ID": (44.2, -114.6), "IL": (40.0, -89.2), "IN": (39.9, -86.3), "IA": (42.1, -93.5), "KS": (38.5, -98.4), "KY": (37.5, -85.3),
      "LA": (31.1, -92.0), "ME": (45.4, -69.2), "MD": (39.0, -76.8), "MA": (42.3, -71.8), "MI": (43.3, -84.5), "MN": (46.3, -94.3),
      "MS": (32.7, -89.7), "MO": (38.4, -92.5), "MT": (47.0, -109.6), "NE": (41.5, -99.8), "NV": (39.3, -116.6), "NH": (43.7, -71.6),
      "NJ": (40.2, -74.7), "NM": (34.4, -106.1), "NY": (42.9, -75.5), "NC": (35.6, -79.4), "ND": (47.5, -100.5), "OH": (40.3, -82.8),
      "OK": (35.6, -97.5), "OR": (43.9, -120.6), "PA": (40.9, -77.8), "RI": (41.7, -71.5), "SC": (33.9, -80.9), "SD": (44.4, -100.2),
      "TN": (35.9, -86.4), "TX": (31.5, -99.3), "UT": (39.3, -111.7), "VT": (44.1, -72.7), "VA": (37.5, -78.9), "WA": (47.4, -120.5),
      "WV": (38.6, -80.6), "WI": (44.6, -89.9), "WY": (43.0, -107.6), "PR": (18.2, -66.5)}
def where(arena):
    m = re.search(r",\s*([A-Z]{2})\b", arena or ""); return ST.get(m.group(1)) if m else None
def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b)); h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))
D = lambda s: dt.datetime.strptime(s, "%Y/%m/%d")
seasons = sorted({g["season"] for g in G})
OUT = {}; miss = Counter()
for s in seasons:
    code = s[2:4] + s[5:7]; tg = [g for g in G if g["season"] == s]
    ff = [D(g["date"]) for g in tg if g["rnd"] == "First Four"]; r1 = [D(g["date"]) for g in tg if g["rnd"] == "First round"]
    if not r1: continue
    cut = min(ff) if ff else min(r1)
    want = {}
    for g in tg:
        if g["rnd"] == "First round":
            for t in (g["fav"], g["dog"]): want[kk(t)] = (D(g["date"]), g["gid"])
    files = {kk(os.path.basename(os.path.dirname(p))): p for p in glob.glob(os.path.join(ROOT, code, "*", "*", "game_scores.json"))}
    for t, (d1, gid) in want.items():
        p = files.get(t)
        if not p: miss[s] += 1; continue
        gs = json.load(open(p, encoding="utf-8-sig")); me = os.path.basename(os.path.dirname(p)); rec = []
        site = None
        for x in gs:
            try: a, h = int(x["away_score"]), int(x["home_score"])
            except (TypeError, ValueError): continue
            d = D(x["date"]); home = kk(x["home_team"]) == t
            if d.date() == d1.date() or str(x.get("game_id")) == str(gid): site = x.get("arena")
            if d >= cut: continue
            mg = (h - a) if home else (a - h); rec.append((d, mg, "N" if x.get("neutral") else ("H" if home else "A"), x.get("arena")))
        rec.sort()
        if len(rec) < 10: miss[s] += 1; continue
        mg = [r[1] for r in rec]; last = rec[-1][0]
        streak = 0
        for r in reversed(rec):
            if r[1] > 0: streak += 1
            else: break
        hm = [r[1] for r in rec if r[2] == "H"]; aw = [r[1] for r in rec if r[2] != "H"]; nu = [r[1] for r in rec if r[2] == "N"]
        homecity = Counter(r[3] for r in rec if r[2] == "H").most_common(1)
        hl = where(homecity[0][0]) if homecity else None; sl = where(site)
        OUT.setdefault(s, {})[t] = {
            "rest_days": (d1 - last).days, "games_last7": sum((cut - r[0]).days <= 7 for r in rec),
            "games_last14": sum((cut - r[0]).days <= 14 for r in rec),
            "form_last10": sum(mg[-10:]) / 10 - sum(mg) / len(mg), "form_last5": sum(mg[-5:]) / 5 - sum(mg) / len(mg),
            "win_streak": streak, "won_last": int(mg[-1] > 0), "wins_last10": sum(m > 0 for m in mg[-10:]),
            "home_dependence": (sum(hm) / len(hm) if hm else 0) - (sum(aw) / len(aw) if aw else 0),
            "away_share": len(aw) / len(rec), "neutral_games": len(nu),
            "travel_km": km(hl, sl) if hl and sl else None, "same_state_site": int(bool(hl and sl and hl == sl)),
            "margin_sd_late": (sum((m - sum(mg[-10:]) / 10) ** 2 for m in mg[-10:]) / 10) ** .5}
print({s: len(v) for s, v in OUT.items()}); print("missing:", dict(miss))
tk = [v["travel_km"] for s in OUT for v in OUT[s].values()]
print("travel known:", sum(x is not None for x in tk), "of", len(tk))
json.dump(OUT, open(os.path.join(HERE, "m315_feats.json"), "w"))
