# Pre-tournament "deep run" measures + pre-tournament absences, for every NCAA team 2010-2026 (games before the first NCAA game).
import os, sys, json, glob, re, datetime as dt
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
from m210_followups import kk
ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"
G = Q.R.B.G; TM = Q.TM
D = lambda s: dt.datetime.strptime(s, "%Y/%m/%d")
def mins(x):
    try: return float(x)
    except (TypeError, ValueError):
        m = re.match(r"(\d+):(\d+)", str(x or "")); return int(m.group(1)) + int(m.group(2)) / 60 if m else 0.0
def net_of(s, t):
    for k_, v in TM.get(s, {}).items():
        if kk(k_) == t: return v.get("adj_net")
    return None
OUT = {}
for s in sorted({g["season"] for g in G}):
    code = s[2:4] + s[5:7]; tg = [g for g in G if g["season"] == s]
    first = min(D(g["date"]) for g in tg)
    field = {kk(t) for g in tg for t in (g["fav"], g["dog"])}
    nets = sorted(((net_of(s, t) or -99), t) for t in {kk(x) for x in TM.get(s, {})}); top30 = {t for _, t in nets[-30:]}
    files = {kk(os.path.basename(os.path.dirname(p))): os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, code, "*", "*", "game_scores.json"))}
    for t in field:
        d = files.get(t)
        if not d: continue
        gs = json.load(open(os.path.join(d, "game_scores.json"), encoding="utf-8-sig")); games = []
        for x in gs:
            try: a, h = int(x["away_score"]), int(x["home_score"])
            except (TypeError, ValueError): continue
            if D(x["date"]) >= first: continue
            home = kk(x["home_team"]) == t; opp = kk(x["away_team"] if home else x["home_team"]); mg = (h - a) if home else (a - h)
            games.append((D(x["date"]), str(x["game_id"]), opp, mg))
        games.sort()
        if len(games) < 10: continue
        # box scores: minutes / points per player per game
        pl = defaultdict(dict)
        for _, gid, _, _ in games:
            p = os.path.join(d, "boxscores", gid + ".json")
            if not os.path.exists(p): continue
            try: bx = json.load(open(p, encoding="utf-8-sig"))
            except Exception: continue
            tms = bx.get("teams") or []
            me = next((z for z in tms if kk(z.get("team_name", "")) == t), None)
            if me is None and len(tms) == 2:
                me = next((z for z in tms if kk(z.get("team_name", "")) not in {g_[2] for g_ in games if g_[1] == gid}), None)
            if me is None: continue
            for row in (me.get("starters_table") or []) + (me.get("bench_table") or []):
                nm = row.get("Name"); m_ = mins(row.get("MIN"))
                if nm and nm.lower() not in ("team", "totals") and m_ > 0: pl[nm][gid] = (m_, float(row.get("PTS") or 0))
        gids = [g_[1] for g_ in games]; have = [g_ for g_ in gids if any(g_ in v for v in pl.values())]
        vs_f = [g_ for g_ in games if g_[2] in field]; vs_t = [g_ for g_ in games if g_[2] in top30]; close = [g_ for g_ in games if abs(g_[3]) <= 5]
        rec = {"games_vs_field": len(vs_f), "winpct_vs_field": (sum(g_[3] > 0 for g_ in vs_f) / len(vs_f)) if vs_f else None,
               "margin_vs_field": (sum(g_[3] for g_ in vs_f) / len(vs_f)) if vs_f else None,
               "margin_vs_top30": (sum(g_[3] for g_ in vs_t) / len(vs_t)) if vs_t else None, "games_vs_top30": len(vs_t),
               "late_margin_vs_field": (lambda L: sum(g_[3] for g_ in L) / len(L) if L else None)(vs_f[-6:]),
               "close_winpct": (sum(g_[3] > 0 for g_ in close) / len(close)) if close else None, "close_games": len(close)}
        if len(have) >= 8:
            tot = {nm: sum(v[0] for v in gm.values()) for nm, gm in pl.items()}; ng = len(have)
            stars = sorted(tot, key=lambda n: -tot[n])[:2]; allmin = sum(tot.values())
            cl = [g_[1] for g_ in close if g_[1] in have]
            mpg = lambda n, L: sum(pl[n].get(x, (0, 0))[0] for x in L) / max(len(L), 1)
            rec["star_mpg"] = mpg(stars[0], have); rec["top2_minutes_share"] = sum(tot[n] for n in stars) / allmin
            rec["star_close_minutes_ratio"] = (sum(mpg(n, cl) for n in stars) / max(sum(mpg(n, have) for n in stars), 1)) if len(cl) >= 2 else None
            # pre-tournament absences: rotation players (>= 15 mpg in games they played, >= 10 games) missing all of the last 3 games with box scores
            last3 = have[-3:]; season_pts = {nm: sum(v[1] for v in gm.values()) for nm, gm in pl.items()}; allpts = sum(season_pts.values()) or 1
            out_ = [n for n, gm in pl.items() if len(gm) >= 10 and tot[n] / len(gm) >= 15 and not any(x in gm for x in last3)]
            rec["absent_minutes_share"] = sum(tot[n] for n in out_) / allmin; rec["absent_points_share"] = sum(season_pts[n] for n in out_) / allpts
            rec["absent_players"] = out_; rec["top_scorer_absent"] = int(max(season_pts, key=season_pts.get) in out_)
        OUT.setdefault(s, {})[t] = rec
n = sum(len(v) for v in OUT.values()); print("teams", n)
ab = [(s, t, r["absent_players"], round(r["absent_points_share"], 2)) for s, v in OUT.items() for t, r in v.items() if r.get("absent_points_share", 0) >= .1]
print("teams missing >= 10% of their points in the last 3 games:", len(ab)); [print("  ", x) for x in sorted(ab, key=lambda z: -z[3])[:25]]
json.dump(OUT, open(os.path.join(HERE, "m337_feats.json"), "w"))
