# Rewrite only STL / BLK in the existing 2009-10 and 2010-11 stats.ncaa.org box scores, using tools/ncaa_stats_season.py's
# own (now fixed) reader, so the values are exactly what a rebuild would write. Players are matched by position in the
# table and checked by name; anything that doesn't line up is left alone and counted.
import os, sys, json, glob
ROOT = r"C:\Users\crtra\Downloads\basketball"; sys.path.insert(0, os.path.join(ROOT, "tools"))
import ncaa_stats_season as N
stats = {"files": 0, "changed": 0, "no_source": 0, "team_mismatch": 0, "name_mismatch": 0}
for code in ("0910", "1011"):
    label = N.SEASONS[code][0]; games = N.read_games(label)
    for base in (code, code + " full"):
        for f in glob.glob(os.path.join(ROOT, "data", "seasons", base, "*", "*", "boxscores", "*.json")):
            stats["files"] += 1; box = json.load(open(f, encoding="utf-8"))
            src = games.get(str(box.get("game_id")))
            if not src: stats["no_source"] += 1; continue
            changed = False
            for t in box["teams"]:
                b = src["boxes"].get(N.clean(t["team_name"]))
                if not b: stats["team_mismatch"] += 1; continue
                for key in ("starters_table", "bench_table"):
                    if len(t.get(key, [])) != len(b[key]): stats["name_mismatch"] += 1; continue
                    for p, q in zip(t[key], b[key]):
                        if p.get("Name") != q["Name"]: stats["name_mismatch"] += 1; continue
                        if (p["STL"], p["BLK"]) != (q["STL"], q["BLK"]): p["STL"], p["BLK"] = q["STL"], q["BLK"]; changed = True
                tt = t.get("team_totals") or {}
                if (tt.get("STL"), tt.get("BLK")) != (b["team_totals"]["STL"], b["team_totals"]["BLK"]):
                    tt["STL"], tt["BLK"] = b["team_totals"]["STL"], b["team_totals"]["BLK"]; changed = True
            if changed:
                with open(f, "w", encoding="utf-8") as out: json.dump(box, out, indent=1)
                stats["changed"] += 1
    print(code, "done", stats, flush=True)
