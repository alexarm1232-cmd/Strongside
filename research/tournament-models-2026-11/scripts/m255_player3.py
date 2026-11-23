# Player-level volume 3-point shooting from pre-tournament box scores (data/seasons/<code>/<conf>/<team>/boxscores; the
# NCAA tournament lives only in the "full" folders, so these are regular season + conference tournaments).
# Volume shooter = 4+ three-point attempts per game over 10+ games. "Hot" = 4+ threes made in a game.
import os, json, glob, math, statistics as st
ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"
HERE = os.path.dirname(os.path.abspath(__file__))
def mk(s):
    try: m, a = str(s).split("-"); return int(m), int(a)
    except Exception: return 0, 0
def mins(x):
    try: return float(x)
    except Exception: return 0.0
OUT = {}
for y in range(2010, 2027):
    code = f"{str(y - 1)[2:]}{str(y)[2:]}"; season = f"{y - 1}-{str(y)[2:]}"; d = os.path.join(ROOT, code)
    if not os.path.isdir(d): continue
    OUT[season] = {}
    for tdir in glob.glob(os.path.join(d, "*", "*")):
        bx = os.path.join(tdir, "boxscores")
        if not os.path.isdir(bx): continue
        team = os.path.basename(tdir); P = {}; games = []
        for f in glob.glob(os.path.join(bx, "*.json")):
            try: J = json.load(open(f, encoding="utf-8"))
            except Exception: continue
            T = [t for t in J.get("teams", []) if t.get("team_name", "").rstrip(". ") == team.rstrip(". ")]
            if not T: T = J.get("teams", [])[:1] if len(J.get("teams", [])) == 1 else []
            if not T: continue
            rows = (T[0].get("starters_table") or []) + (T[0].get("bench_table") or [])
            g = []
            for r in rows:
                nm = r.get("Name"); m3, a3 = mk(r.get("3PT")); mn = mins(r.get("MIN"))
                if not nm or mn <= 0: continue
                P.setdefault(nm, []).append((m3, a3)); g.append((nm, m3, a3))
            if g: games.append(g)
        if len(games) < 10: continue
        vol = {nm: v for nm, v in P.items() if len(v) >= 10 and sum(a for _, a in v) / len(v) >= 4.0}
        team3a = sum(a for g in games for _, _, a in g) or 1
        vg = [x for v in vol.values() for x in v]
        top = max(P, key=lambda nm: sum(a for _, a in P[nm]) / max(len(P[nm]), 1) if len(P[nm]) >= 10 else 0)
        tv = P[top]
        rec = {"vol_n": len(vol), "vol_3pa_share": sum(a for v in vol.values() for _, a in v) / team3a,
               "vol_p3": (sum(m for m, _ in vg) / max(sum(a for _, a in vg), 1)) if vg else 0.0,
               "vol_hot_rate": (sum(m >= 4 for m, _ in vg) / len(vg)) if vg else 0.0,
               "vol_hot50": (sum(a >= 5 and m / a >= .5 for m, a in vg) / len(vg)) if vg else 0.0,
               "vol_cold": (sum(a >= 4 and m / a <= .2 for m, a in vg) / len(vg)) if vg else 0.0,
               "team_any_hot": sum(any(nm in vol and m >= 4 for nm, m, _ in g) for g in games) / len(games),
               "team_two_hot": sum(sum(nm in vol and m >= 3 for nm, m, _ in g) >= 2 for g in games) / len(games),
               "team_5plus_game": sum(any(m >= 5 for _, m, _ in g) for g in games) / len(games),
               "top_3pa": sum(a for _, a in tv) / len(tv), "top_p3": sum(m for m, _ in tv) / max(sum(a for _, a in tv), 1),
               "top_hot": sum(m >= 4 for m, _ in tv) / len(tv), "top_sd": st.pstdev([m for m, _ in tv]),
               "shooters_35": sum(1 for v in P.values() if len(v) >= 10 and sum(a for _, a in v) / len(v) >= 2 and sum(m for m, _ in v) / max(sum(a for _, a in v), 1) >= .35),
               "games": len(games)}
        OUT[season][team] = rec
    print(season, len(OUT[season]), "teams", flush=True)
json.dump(OUT, open(os.path.join(HERE, "m255_player3.json"), "w"))
