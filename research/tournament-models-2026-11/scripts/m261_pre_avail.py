# Pre-tournament availability (what you could know when filling out the bracket): for every team-season, rotation players
# (10+ mpg over the pre-tournament season) who did NOT appear in the team's last 2 pre-tournament games.
#   miss_share  share of team minutes those players carried;  star_out  the top-minutes player missed both;  n_out  how many
import os, json, glob
ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"; HERE = os.path.dirname(os.path.abspath(__file__))
def num(x):
    try: return float(x)
    except Exception: return 0.0
OUT = {}
for y in range(2010, 2027):
    code = f"{str(y - 1)[2:]}{str(y)[2:]}"; season = f"{y - 1}-{str(y)[2:]}"
    if not os.path.isdir(os.path.join(ROOT, code)): continue
    OUT[season] = {}
    for tdir in glob.glob(os.path.join(ROOT, code, "*", "*")):
        bx = os.path.join(tdir, "boxscores"); gs = os.path.join(tdir, "game_scores.json")
        if not os.path.isdir(bx) or not os.path.exists(gs): continue
        team = os.path.basename(tdir)
        try: dates = {str(g["game_id"]): g["date"] for g in json.load(open(gs, encoding="utf-8"))}
        except Exception: continue
        games = []
        for f in glob.glob(os.path.join(bx, "*.json")):
            gid = os.path.basename(f)[:-5]
            try: J = json.load(open(f, encoding="utf-8"))
            except Exception: continue
            T = [t for t in J.get("teams", []) if t.get("team_name", "").rstrip(". ") == team.rstrip(". ")]
            if not T: continue
            pl = {r.get("Name"): num(r.get("MIN")) for r in (T[0].get("starters_table") or []) + (T[0].get("bench_table") or []) if r.get("Name") and num(r.get("MIN")) > 0}
            games.append((dates.get(gid, "0000"), pl))
        if len(games) < 10: continue
        games.sort(key=lambda t: t[0]); tot = {}; cnt = {}
        for _, pl in games:
            for nm, m in pl.items(): tot[nm] = tot.get(nm, 0) + m; cnt[nm] = cnt.get(nm, 0) + 1
        allmin = sum(tot.values()) or 1; rot = [nm for nm in tot if tot[nm] / len(games) >= 10]
        last = set(games[-1][1]) | set(games[-2][1])
        out = [nm for nm in rot if nm not in last]; top = max(tot, key=tot.get)
        OUT[season][team] = {"miss_share": sum(tot[nm] for nm in out) / allmin, "star_out": float(top not in last), "n_out": float(len(out))}
    print(season, len(OUT[season]), flush=True)
json.dump(OUT, open(os.path.join(HERE, "m261_pre_avail.json"), "w"))
