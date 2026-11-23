# Basic pre-tournament season totals for every Round of 64 team, 2010-2026: one row per team per year.
# All of the team's games dated before the First Four (non-D-I opponents included), + published-site pre-tournament
# net / offensive / defensive rating.
import os, sys, json, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m157_totals_all.json")
G = Q.R.B.G
CNT = ["pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "orb", "reb", "ast", "stl", "blk", "to", "pf"]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    teams = {t for g in G if g["season"] == s and g["rnd"] == "First round" for t in (g["fav"], g["dog"])}; T = {}; seen = set()
    for g in games:
        if g["date"] >= first or g["hs"] is None or g["id"] in seen: continue
        seen.add(g["id"])
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            if t not in teams or t not in g["side"] or o not in g["side"]: continue
            a, b = g["side"][t], g["side"][o]; r = T.setdefault(t, {"g": 0, "w": 0})
            r["g"] += 1; r["w"] += int((g["hs"] - g["as_"]) * (1 if t == g["home"] else -1) > 0); r["pts_box_off"] = r.get("pts_box_off", 0) + int(a["pts"] != (g["hs"] if t == g["home"] else g["as_"]))
            for k in CNT: r[k] = r.get(k, 0) + float(a[k] or 0); r["opp_" + k] = r.get("opp_" + k, 0) + float(b[k] or 0)
    return s, T
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
    TT = json.load(open(CACHE)); SITE = json.load(open(os.path.join(HERE, "m152_site_ratings.json")))
    norm = lambda n: re.sub(r"[^a-z0-9]", "", n.lower().replace("&amp;", "&").replace("saint", "st").replace("state", "st"))
    site = lambda s, t: SITE[s]["pre"].get(t) or next(v for k, v in SITE[s]["pre"].items() if norm(k) == norm(t))
    seeds = {}
    for g in G:
        if g["rnd"] == "First round": seeds[(g["season"], g["fav"])] = g["fseed"]; seeds[(g["season"], g["dog"])] = g["dseed"]
    rows = []; mism = []
    for (s, t), seed in sorted(seeds.items(), key=lambda x: (x[0][0], x[1], x[0][1])):
        r = TT[s].get(t); st = site(s, t); g_ = r["g"]
        if g_ != st["w"] + st["l"] or r["w"] != st["w"]: mism.append((s, t, r["w"], g_ - r["w"], int(st["w"]), int(st["l"])))
        i = lambda k: int(round(r[k]))
        rows.append({"Year": int("20" + s[-2:]), "Season": s, "Team": t, "Conf": st["conf"], "Seed": seed, "G": g_, "W": int(st["w"]), "L": int(st["l"]),
                     "NetRtg": st["n"], "ORtg": st["o"], "DRtg": st["d"], "Tempo": st["t"],
                     "PTS": i("pts"), "Opp_PTS": i("opp_pts"), "FGM": i("fgm"), "FGA": i("fga"), "FG_Pct": round(r["fgm"] / r["fga"], 4),
                     "3PM": i("tpm"), "3PA": i("tpa"), "3P_Pct": round(r["tpm"] / max(r["tpa"], 1), 4), "2PM": i("fgm") - i("tpm"), "2PA": i("fga") - i("tpa"), "2P_Pct": round((r["fgm"] - r["tpm"]) / max(r["fga"] - r["tpa"], 1), 4), "FTM": i("ftm"), "FTA": i("fta"), "FT_Pct": round(r["ftm"] / max(r["fta"], 1), 4),
                     "ORB": i("orb"), "DRB": i("reb") - i("orb"), "TRB": i("reb"), "AST": i("ast"), "STL": i("stl"), "BLK": i("blk"), "TOV": i("to"), "PF": i("pf"),
                     "Opp_FGM": i("opp_fgm"), "Opp_FGA": i("opp_fga"), "Opp_FG_Pct": round(r["opp_fgm"] / r["opp_fga"], 4), "Opp_3PM": i("opp_tpm"), "Opp_3PA": i("opp_tpa"), "Opp_3P_Pct": round(r["opp_tpm"] / max(r["opp_tpa"], 1), 4), "Opp_2PM": i("opp_fgm") - i("opp_tpm"), "Opp_2PA": i("opp_fga") - i("opp_tpa"), "Opp_2P_Pct": round((r["opp_fgm"] - r["opp_tpm"]) / max(r["opp_fga"] - r["opp_tpa"], 1), 4), "Opp_FTM": i("opp_ftm"), "Opp_FTA": i("opp_fta"), "Opp_FT_Pct": round(r["opp_ftm"] / max(r["opp_fta"], 1), 4),
                     "Opp_ORB": i("opp_orb"), "Opp_DRB": i("opp_reb") - i("opp_orb"), "Opp_TRB": i("opp_reb"), "Opp_AST": i("opp_ast"), "Opp_STL": i("opp_stl"), "Opp_BLK": i("opp_blk"), "Opp_TOV": i("opp_to"), "Opp_PF": i("opp_pf")})
    PB = json.load(open(os.path.join(HERE, "m160_raw_stl_blk.json")))   # 2009-10 / 2010-11: the raw stats.ncaa file names these columns ST and BLKS
    for x in rows:
        v = PB.get(x["Season"], {}).get(x["Team"])
        if v:
            assert v["g"] == x["G"], (x["Season"], x["Team"], v["g"], x["G"])
            x.update({"STL": v["stl"], "BLK": v["blk"], "Opp_STL": v["opp_stl"], "Opp_BLK": v["opp_blk"]})
    out = r"C:\Users\crtra\Downloads\Round of 64 - pre-tournament data 2010-2026.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} team rows x {len(rows[0])} columns -> {out}")
    print(f"record from box scores differs from the site's pre-tournament W-L for {len(mism)} teams:", mism[:8])
    m = [x for x in rows if x["Team"] == "Michigan" and x["Year"] == 2026][0]; print({k: m[k] for k in ("Team", "Seed", "G", "W", "L", "NetRtg", "PTS", "FGA", "TRB")})




