# Round of 32 "who plays" rebuilt from Round 1: each team's Round of 32 lineup = the players who played in its Round 1 game,
# minus players who look injured in Round 1 from the play-by-play (rotation player, 10+ mpg, whose last appearance came with
# 10+ minutes left in regulation, who played under half his season minutes per game, did not foul out, and the game was
# within 15 points when he left). Nothing from the Round of 32 game itself is used.
import os, sys, json, glob, re, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
B = Q.R.B; G = B.G; N = len(G); ROOT = r"C:\Users\crtra\Downloads\basketball"; DS = os.path.join(ROOT, "data", "seasons")
kk = lambda s: (s or "").rstrip(". ")
inp = {}
for path in glob.glob(os.path.join(ROOT, "logs", "tourneystat", "*_live.js")):
    p = json.load(open(path, encoding="utf-8"))
    for r, gid, (lg_, a, b) in zip(p["rows"], p["ids"], p["inputs"]):
        if gid: inp[str(gid)] = {kk(r[1]): a, kk(r[2]): b}
def lineup(pl, flags):
    tot = sum(q[1] for q in pl) or 1.0
    rot = [(q, f) for q, f in zip(pl, flags) if q[1] / max(q[0], 1) >= 10]
    miss = sum(q[1] / tot * 5 * (q[2] + 2) for q, f in rot if f == 0)
    stars = [(q, f) for q, f in zip(pl, flags) if q[1] / max(q[0], 1) >= 15]
    star = max(stars, key=lambda x: x[0][2]) if stars else None
    played = [q for q, f in zip(pl, flags) if f == 1]; pm = sum(q[1] for q in played) or 1.0
    return miss, float(star is not None and star[1] == 0), sum(q[1] * q[2] for q in played) / pm
num = lambda x: float(x) if str(x).replace(".", "", 1).isdigit() else 0.0
def code_of(season): y = int(season[:4]) + 1; return f"{str(y - 1)[2:]}{str(y)[2:]}"
def team_dir(code, team):
    for d in glob.glob(os.path.join(DS, code + " full", "*", "*")):
        if kk(os.path.basename(d)) == kk(team): return d
    return None
SEASON_MIN = {}
def season_minutes(code, team):
    key = (code, kk(team))
    if key in SEASON_MIN: return SEASON_MIN[key]
    PP = {}; reg = glob.glob(os.path.join(DS, code, "*", "*", "boxscores", "*.json"))
    tdirs = [d for d in glob.glob(os.path.join(DS, code, "*", "*")) if kk(os.path.basename(d)) == kk(team)]
    for td in tdirs:
        for rf in glob.glob(os.path.join(td, "boxscores", "*.json")):
            try: J = json.load(open(rf, encoding="utf-8"))
            except Exception: continue
            for T in J.get("teams", []):
                if kk(T.get("team_name")) != kk(team): continue
                for r in (T.get("starters_table") or []) + (T.get("bench_table") or []):
                    PP.setdefault(r.get("Name"), 0.0); PP[r.get("Name")] += num(r.get("MIN"))
    SEASON_MIN[key] = PP; return PP
stats = dict(teams=0, flagged=0, no_pbp=0, no_box=0, unmatched=0, no_inputs=0)
FLAGGED = []
def injured_names(g1, team):
    code = code_of(g1["season"]); td = team_dir(code, team)
    if not td: stats["no_box"] += 1; return set(), None
    bf = os.path.join(td, "boxscores", str(g1["gid"]) + ".json"); pf = os.path.join(td, "playbyplay", str(g1["gid"]) + ".json")
    if not os.path.exists(bf): stats["no_box"] += 1; return set(), None
    J = json.load(open(bf, encoding="utf-8")); T = [t for t in J.get("teams", []) if kk(t.get("team_name")) == kk(os.path.basename(td))]
    if not T: stats["no_box"] += 1; return set(), None
    rows = (T[0].get("starters_table") or []) + (T[0].get("bench_table") or [])
    if not os.path.exists(pf): stats["no_pbp"] += 1; return set(), rows
    P = json.load(open(pf, encoding="utf-8"))["plays"]; home = kk(P[0].get("team")) if P else ""
    smin = season_minutes(code, os.path.basename(td)); ngames = max(1, len(glob.glob(os.path.join(DS, code, "*", os.path.basename(td), "boxscores", "*.json"))))
    out = set()
    for r in rows:
        nm = r.get("Name") or ""; mins = num(r.get("MIN")); mpg = smin.get(nm, 0.0) / ngames
        if mpg < float(os.environ.get("MPG", 10)) or mins <= 0 or num(r.get("PF")) >= 5 or mins >= float(os.environ.get("FRAC", .5)) * mpg: continue
        last = names = None; last_name = nm.split()[-1] if nm.split() else nm
        for pl in P:
            if nm in pl.get("text", "") or (last_name and re.search(r"\b" + re.escape(nm.upper()) + r"\b", pl.get("text", "").upper())): last = pl
        if last is None: continue
        per = last.get("period", 1); left = last.get("seconds_left", 0) + (1200 if per == 1 else 0)
        if per > 2 or left < float(os.environ.get("LEFT", 600)): continue
        if abs(last.get("home_score", 0) - last.get("away_score", 0)) > 15: continue
        out.add(nm); FLAGGED.append((g1["season"], team, nm, round(mins), round(mpg, 1), round(left / 60, 1)))
    return out, rows
def match_rows(pl, rows, code, team):
    """map box-score names -> index in the tourneystat player list, by season minutes"""
    smin = season_minutes(code, team); M = {}
    for nm in [r.get("Name") for r in rows]:
        sm = smin.get(nm)
        if not sm: continue
        j = min(range(len(pl)), key=lambda k: abs(pl[k][1] - sm))
        if abs(pl[j][1] - sm) <= max(15, 0.06 * sm): M[nm] = j
    return M
R1 = {}
for g in G:
    if g["rnd"] == "First round":
        for t in (g["fav"], g["dog"]): R1[(g["season"], kk(t))] = g
F2 = Q.M.F.copy(); changed = 0; n32 = 0; same_flags = 0; tot_flags = 0
for i, g in enumerate(G):
    if g["rnd"] != "Second round": continue
    n32 += 1; d2 = inp.get(str(g["gid"]))
    if not d2: stats["no_inputs"] += 1; continue
    s_name = kk(B.Sname[i]); w_name = next((k for k in d2 if k != s_name), None)
    if s_name not in d2 or w_name is None: stats["no_inputs"] += 1; continue
    res = {}
    for t in (s_name, w_name):
        pl2 = d2[t][1]; flags = [q[-1] for q in pl2]
        g1 = R1.get((g["season"], t))
        d1 = inp.get(str(g1["gid"])) if g1 else None
        pl1 = d1[t][1] if (d1 and t in d1) else None
        if pl1 is not None:
            f1 = [q[-1] for q in pl1]
            inj, rows = injured_names(g1, t) if not os.environ.get("NOINJ") else (set(), None)
            if inj and rows:
                M = match_rows(pl1, rows, code_of(g["season"]), t)
                for nm in inj:
                    if nm in M: f1[M[nm]] = 0
                    else: stats["unmatched"] += 1
            stats["teams"] += 1
            if len(pl1) == len(pl2): same_flags += sum(a == b for a, b in zip(f1, flags)); tot_flags += len(flags)
            res[t] = lineup(pl1, f1)
        else: stats["no_inputs"] += 1; res[t] = lineup(pl2, flags)
    s, w = res[s_name], res[w_name]; new = [s[0], w[0], s[1], w[1], s[2] - w[2], s[0] - w[0]]
    changed += int(not np.allclose(new, F2[i])); F2[i] = new
print(f"Round of 32 games {n32} | teams rebuilt from Round 1 {stats['teams']} | games whose who-plays changed {changed}")
print(f"played flags equal to the actual Round of 32: {same_flags}/{tot_flags} ({same_flags / max(tot_flags, 1):.1%})")
print("stats:", stats); print(f"flagged as hurt in Round 1: {len(FLAGGED)}")
for f in FLAGGED[:40]: print("   ", f)
np.save(os.path.join(HERE, "m277_who_r32_from_r1" + ("_noinj" if os.environ.get("NOINJ") else "") + os.environ.get("TAG", "") + ".npy"), F2)
json.dump(FLAGGED, open(os.path.join(HERE, "m277_flagged" + os.environ.get("TAG", "") + ".json"), "w"))



