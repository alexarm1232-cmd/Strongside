# Add 2021 Oregon (7 seed; Round 1 vs VCU was a no-contest, so it was missing) to the Round of 64 CSV, built exactly like m157.
import os, sys, json, csv, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import m99_model_types as Q
sys.path.insert(0, Q.OLD); import upset_data as U
S, T_ = "2020-21", "Oregon"
CNT = ["pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "orb", "reb", "ast", "stl", "blk", "to", "pf"]
games, td = U.load("2021"); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
r = {"g": 0, "w": 0}; seen = set()
for g in games:
    if g["date"] >= first or g["hs"] is None or g["id"] in seen: continue
    seen.add(g["id"])
    for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
        if t != T_ or t not in g["side"] or o not in g["side"]: continue
        a, b = g["side"][t], g["side"][o]; r["g"] += 1; r["w"] += int((g["hs"] - g["as_"]) * (1 if t == g["home"] else -1) > 0)
        for k in CNT: r[k] = r.get(k, 0) + float(a[k] or 0); r["opp_" + k] = r.get("opp_" + k, 0) + float(b[k] or 0)
print("first NCAA date", first, "| Oregon box-score games", r["g"], "wins", r["w"])
SITE = json.load(open(os.path.join(HERE, "m152_site_ratings.json")))
norm = lambda n: re.sub(r"[^a-z0-9]", "", n.lower().replace("&amp;", "&").replace("saint", "st").replace("state", "st"))
st = SITE[S]["pre"].get(T_) or next(v for k, v in SITE[S]["pre"].items() if norm(k) == norm(T_))
print("site pre-tournament:", {k: st[k] for k in ("conf", "w", "l", "n", "o", "d", "t")})
i = lambda k: int(round(r[k]))
row = {"Year": 2021, "Season": S, "Team": T_, "Conf": st["conf"], "Seed": 7, "G": r["g"], "W": int(st["w"]), "L": int(st["l"]),
       "NetRtg": st["n"], "ORtg": st["o"], "DRtg": st["d"], "Tempo": st["t"],
       "PTS": i("pts"), "Opp_PTS": i("opp_pts"), "FGM": i("fgm"), "FGA": i("fga"), "FG_Pct": round(r["fgm"] / r["fga"], 4),
       "3PM": i("tpm"), "3PA": i("tpa"), "3P_Pct": round(r["tpm"] / max(r["tpa"], 1), 4), "2PM": i("fgm") - i("tpm"), "2PA": i("fga") - i("tpa"), "2P_Pct": round((r["fgm"] - r["tpm"]) / max(r["fga"] - r["tpa"], 1), 4), "FTM": i("ftm"), "FTA": i("fta"), "FT_Pct": round(r["ftm"] / max(r["fta"], 1), 4),
       "ORB": i("orb"), "DRB": i("reb") - i("orb"), "TRB": i("reb"), "AST": i("ast"), "STL": i("stl"), "BLK": i("blk"), "TOV": i("to"), "PF": i("pf"),
       "Opp_FGM": i("opp_fgm"), "Opp_FGA": i("opp_fga"), "Opp_FG_Pct": round(r["opp_fgm"] / r["opp_fga"], 4), "Opp_3PM": i("opp_tpm"), "Opp_3PA": i("opp_tpa"), "Opp_3P_Pct": round(r["opp_tpm"] / max(r["opp_tpa"], 1), 4), "Opp_2PM": i("opp_fgm") - i("opp_tpm"), "Opp_2PA": i("opp_fga") - i("opp_tpa"), "Opp_2P_Pct": round((r["opp_fgm"] - r["opp_tpm"]) / max(r["opp_fga"] - r["opp_tpa"], 1), 4), "Opp_FTM": i("opp_ftm"), "Opp_FTA": i("opp_fta"), "Opp_FT_Pct": round(r["opp_ftm"] / max(r["opp_fta"], 1), 4),
       "Opp_ORB": i("opp_orb"), "Opp_DRB": i("opp_reb") - i("opp_orb"), "Opp_TRB": i("opp_reb"), "Opp_AST": i("opp_ast"), "Opp_STL": i("opp_stl"), "Opp_BLK": i("opp_blk"), "Opp_TOV": i("opp_to"), "Opp_PF": i("opp_pf")}
print(row)
out = r"C:\Users\crtra\Downloads\Round of 64 - pre-tournament data 2010-2026.csv"
if "--write" in sys.argv:
    shutil.copy(out, os.path.join(HERE, "r64_csv_backup_before_oregon.csv"))
    with open(out, encoding="utf-8-sig", newline="") as f: rd = csv.DictReader(f); fields = rd.fieldnames; rows = list(rd)
    assert not any(x["Year"] == "2021" and x["Team"] == T_ for x in rows)
    assert list(row) == fields, "column mismatch"
    # same order as m157: season, seed, team
    pos = next(j for j, x in enumerate(rows) if (x["Season"], int(x["Seed"]), x["Team"]) > (S, 7, T_))
    rows.insert(pos, {k: str(v) for k, v in row.items()})
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print("inserted at row", pos + 2, "| total rows", len(rows))
