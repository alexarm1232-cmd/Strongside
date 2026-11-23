# Round 1 box-score features for every Round 1 winner (fed into its Round of 32 game): workload/fatigue, foul trouble,
# shooting vs its own pre-tournament level, bench use, star usage. Pre-tournament levels come from the regular-season folders.
import os, sys, json, glob, contextlib, io, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
G = Q.R.B.G; ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"
def mk(s):
    try: m, a = str(s).split("-"); return int(m), int(a)
    except Exception: return 0, 0
def num(x):
    try: return float(x)
    except Exception: return 0.0
def side(J, team):
    T = [t for t in J.get("teams", []) if t.get("team_name", "").rstrip(". ") == team.rstrip(". ")]
    if not T: return None
    return (T[0].get("starters_table") or []) + (T[0].get("bench_table") or []), [r for r in (T[0].get("starters_table") or [])]
def line(rows):
    o = dict(min=0, pts=0, m3=0, a3=0, fm=0, fa=0, fgm=0, fga=0, to=0, pf=0, reb=0, oreb=0, ast=0)
    for r in rows:
        m3, a3 = mk(r.get("3PT")); fm, fa = mk(r.get("FT")); gm, ga = mk(r.get("FG"))
        o["min"] += num(r.get("MIN")); o["pts"] += num(r.get("PTS")); o["m3"] += m3; o["a3"] += a3; o["fm"] += fm; o["fa"] += fa; o["fgm"] += gm; o["fga"] += ga
        o["to"] += num(r.get("TO")); o["pf"] += num(r.get("PF")); o["reb"] += num(r.get("REB")); o["oreb"] += num(r.get("OREB")); o["ast"] += num(r.get("AST"))
    return o
OUT = {}
for g in G:
    if g["rnd"] != "First round": continue
    w = g["fav"] if g["fav_won"] else g["dog"]; y = int(g["season"][:4]) + 1; code = f"{str(y - 1)[2:]}{str(y)[2:]}"
    f = glob.glob(os.path.join(ROOT, code + " full", "*", w.rstrip(". ") + "*", "boxscores", str(g["gid"]) + ".json"))
    if not f: continue
    tdir_name = os.path.basename(os.path.dirname(os.path.dirname(f[0])))
    s_ = side(json.load(open(f[0], encoding="utf-8")), tdir_name)
    if not s_: continue
    rows, starters = s_; L = line(rows)
    pmins = sorted([num(r.get("MIN")) for r in rows], reverse=True)
    # pre-tournament season levels (regular folder)
    reg = glob.glob(os.path.join(ROOT, code, "*", tdir_name, "boxscores", "*.json"))
    S = dict(m3=0, a3=0, fm=0, fa=0, to=0, pts=0, n=0, top5=[], pf=0); PP = {}
    for rf in reg:
        try: sj = side(json.load(open(rf, encoding="utf-8")), tdir_name)
        except Exception: continue
        if not sj: continue
        rr = sj[0]; l2 = line(rr); S["n"] += 1
        for k in ("m3", "a3", "fm", "fa", "to", "pts", "pf"): S[k] += l2[k]
        S["top5"].append(sum(sorted([num(r.get("MIN")) for r in rr], reverse=True)[:5]))
        for r in rr:
            nm = r.get("Name"); PP.setdefault(nm, [0, 0, 0]); PP[nm][0] += num(r.get("PTS")); PP[nm][1] += num(r.get("MIN")); PP[nm][2] += 1
    if S["n"] < 10: continue
    star = max(PP, key=lambda nm: PP[nm][0] / max(PP[nm][2], 1) if PP[nm][2] >= 10 else 0)
    srow = next((r for r in rows if r.get("Name") == star), None)
    star_min = num(srow.get("MIN")) if srow else 0.0; star_pts = num(srow.get("PTS")) if srow else 0.0
    rec = {"r1_top5_min": sum(pmins[:5]), "r1_max_min": pmins[0] if pmins else 0, "r1_ot": float(L["min"] > 205),
           "r1_top5_min_vs_season": sum(pmins[:5]) - st.mean(S["top5"]),
           "r1_p3": L["m3"] / max(L["a3"], 1), "r1_3pm": L["m3"], "r1_p3_vs_season": L["m3"] / max(L["a3"], 1) - S["m3"] / max(S["a3"], 1),
           "r1_3pa_vs_season": L["a3"] - S["a3"] / S["n"], "r1_ft_vs_season": L["fm"] / max(L["fa"], 1) - S["fm"] / max(S["fa"], 1),
           "r1_to_vs_season": L["to"] - S["to"] / S["n"], "r1_pts_vs_season": L["pts"] - S["pts"] / S["n"],
           "r1_pf4": float(sum(num(r.get("PF")) >= 4 for r in rows)), "r1_fouled_out": float(sum(num(r.get("PF")) >= 5 for r in rows)),
           "r1_bench_pts_share": sum(num(r.get("PTS")) for r in rows if r not in starters) / max(L["pts"], 1),
           "r1_star_min": star_min, "r1_star_pts_vs_avg": star_pts - PP[star][0] / PP[star][2], "r1_star_min_vs_avg": star_min - PP[star][1] / PP[star][2],
           "r1_oreb": L["oreb"], "r1_ast_rate": L["ast"] / max(L["fgm"], 1)}
    OUT.setdefault(g["season"], {})[w] = rec
print("seasons", len(OUT), "teams", sum(len(v) for v in OUT.values()))
json.dump(OUT, open(os.path.join(HERE, "m258_r1box.json"), "w"))
