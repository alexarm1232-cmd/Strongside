# 2009-10 and 2010-11 steals / blocks straight from data/ncaa stats/individual_stats.csv, where those seasons name the
# columns ST and BLKS. Team-totals row of each game's box (the table's last row), matched to our games by contest id;
# each side matched by its total points to the game's final score. Same games as the CSV: dated before the First Four.
import os, sys, csv, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); G = Q.R.B.G
csv.field_size_limit(10 ** 9)
num = lambda x: int(float(str(x).replace(",", "") or 0)) if str(x or "").strip() else 0
LABEL = {"2009-10": "2009-2010", "2010-11": "2010-2011"}
tables = defaultdict(list)
with open(r"C:\Users\crtra\Downloads\basketball\data\ncaa stats\individual_stats.csv", encoding="utf-8", errors="replace", newline="") as f:
    for r in csv.DictReader(f):
        if r["season"] in LABEL.values() and r["table_num"] != "1": tables[(r["contest_id"], r["table_num"])].append(r)
tot = defaultdict(list)          # contest id -> [(points, steals, blocks)] per team
for (cid, _), rows in tables.items():
    t = rows[-1]
    if (t.get("Name") or "").strip(): tot[cid].append((num(t["PTS"]), num(t.get("ST") or t.get("STL")), num(t.get("BLKS") or t.get("BLK"))))
sys.path.insert(0, Q.OLD); import upset_data as U
out = {}; problems = []
for s in LABEL:
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    teams = {t for g in G if g["season"] == s and g["rnd"] == "First round" for t in (g["fav"], g["dog"])}; seen = set(); O = {}
    for g in games:
        if g["date"] >= first or g["hs"] is None or g["id"] in seen or (g["home"] not in teams and g["away"] not in teams): continue
        seen.add(g["id"]); T = tot.get(str(g["id"]))
        h = [x for x in (T or []) if x[0] == g["hs"]]; a = [x for x in (T or []) if x[0] == g["as_"]]
        if not T or len(T) != 2 or not h or not a or g["hs"] == g["as_"]: problems.append((s, g["id"], g["home"], g["away"])); continue
        for t, me, op in ((g["home"], h[0], a[0]), (g["away"], a[0], h[0])):
            if t not in teams: continue
            r = O.setdefault(t, {"stl": 0, "blk": 0, "opp_stl": 0, "opp_blk": 0, "g": 0})
            r["g"] += 1; r["stl"] += me[1]; r["blk"] += me[2]; r["opp_stl"] += op[1]; r["opp_blk"] += op[2]
    out[s] = O
    print(f"{s}: {len(O)} teams | steals/game {sum(v['stl'] for v in O.values()) / sum(v['g'] for v in O.values()):.2f} | blocks/game {sum(v['blk'] for v in O.values()) / sum(v['g'] for v in O.values()):.2f}")
print("games that couldn't be matched:", len(problems), problems[:6])
json.dump(out, open(os.path.join(HERE, "m160_raw_stl_blk.json"), "w"))
