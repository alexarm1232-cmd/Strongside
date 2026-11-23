# Steals and blocks for 2009-10 and 2010-11 from play-by-play (the stats.ncaa box scores those years list 0).
# Same games as the totals: every game dated before the First Four. Team side from each play's is_home flag.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); G = Q.R.B.G
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    teams = {t for g in G if g["season"] == s and g["rnd"] == "First round" for t in (g["fav"], g["dog"])}
    out = {}; seen = set(); nopbp = 0
    for g in games:
        if g["date"] >= first or g["hs"] is None or g["id"] in seen: continue
        if g["home"] not in teams and g["away"] not in teams: continue
        seen.add(g["id"]); c = {True: [0, 0], False: [0, 0]}; ok = False
        try:
            for p in json.load(open(g["pbp"], encoding="utf-8"))["plays"]:
                t = p.get("text", "").lower(); ok = True
                if "steal" in t: c[bool(p.get("is_home"))][0] += 1
                elif "block" in t: c[bool(p.get("is_home"))][1] += 1
        except Exception: pass
        if not ok: nopbp += 1
        for t, home in ((g["home"], True), (g["away"], False)):
            if t not in teams: continue
            r = out.setdefault(t, {"stl": 0, "blk": 0, "opp_stl": 0, "opp_blk": 0, "g": 0, "g_pbp": 0})
            r["g"] += 1; r["g_pbp"] += int(ok)
            r["stl"] += c[home][0]; r["blk"] += c[home][1]; r["opp_stl"] += c[not home][0]; r["opp_blk"] += c[not home][1]
    return s, out, nopbp
if __name__ == "__main__":
    with ProcessPoolExecutor(2) as ex: R = list(ex.map(_load, ["2009-10", "2010-11"]))
    json.dump({s: o for s, o, _ in R}, open(os.path.join(HERE, "m159_pbp_stl_blk.json"), "w"))
    for s, o, n in R:
        miss = [(t, v["g"] - v["g_pbp"]) for t, v in o.items() if v["g_pbp"] < v["g"]]
        spg = sum(v["stl"] for v in o.values()) / sum(v["g"] for v in o.values()); bpg = sum(v["blk"] for v in o.values()) / sum(v["g"] for v in o.values())
        print(f"{s}: {len(o)} teams | avg steals/game {spg:.2f}, blocks/game {bpg:.2f} | team-games without play-by-play: {sum(m for _, m in miss)} ({len(miss)} teams)", miss[:5])
    print("check vs 2011-12 box-score averages:")
