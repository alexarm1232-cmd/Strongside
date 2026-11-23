# Point guard / backcourt experience for every tournament team, pre-tournament only.
# PG = the roster guard with the most assists in box scores dated before that season's first NCAA tournament game.
# Experience in years: FR 1, SO 2, JR 3, SR 4, GR 5, +1 for a fifth year. Writes m135_ret.json {season: {team: {...}}}.
import os, sys, json, re, glob
from concurrent.futures import ProcessPoolExecutor
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = r"C:\Users\crtra\Downloads\basketball"
CLASS = {"FR": 1, "SO": 2, "JR": 3, "SR": 4, "GR": 5}
def norm(n): n = re.sub(r"[^a-z ]", "", n.lower().replace("-", " ")); return " ".join(w for w in n.split() if w not in ("jr", "sr", "ii", "iii", "iv", "v"))
def yrs(p): return CLASS.get(p.get("class"), 2.5) + (1 if p.get("fifth_year") else 0)
def season(s):
    sys.path.insert(0, OLD); import upset_data as U
    code = s[2:4] + s[5:7]; year = int("20" + code[2:])
    G = json.load(open(os.path.join(OLD, "study_games_all.json"))); teams = {t for g in G if g["season"] == s for t in (g["fav"], g["dog"])}
    games, td = U.load(code); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    pre = {g["id"] for g in games if g["date"] < first}; out = {}
    for t in teams:
        d = td.get(t) or td.get(t + ".")
        if not d: continue
        ro = None
        for dd in (d, d.replace(code + " full", code)):
            try: ro = json.load(open(os.path.join(dd, f"roster_{year}.json"), encoding="utf-8"))["players"]; break
            except Exception: pass
        if not ro: continue
        prev = None
        for dd in (d, d.replace(code + " full", code)):
            try: prev = json.load(open(os.path.join(dd, f"roster_{year - 1}.json"), encoding="utf-8"))["players"]; break
            except Exception: pass
        if not prev: continue
        now = {norm(p["name"]) for p in ro} | {p.get("id") for p in ro}
        tot = sum(p.get("minutes") or 0 for p in prev)
        if tot <= 0: continue
        back = sum(p.get("minutes") or 0 for p in prev if norm(p["name"]) in now or p.get("id") in now)
        out[t] = dict(returning=back / tot)
    return s, out, len(teams)
if __name__ == "__main__":
    G = json.load(open(os.path.join(OLD, "study_games_all.json"))); S = sorted({g["season"] for g in G})
    res = {}
    with ProcessPoolExecutor(6) as ex:
        for s, out, n in ex.map(season, S):
            res[s] = out; print(s, f"{len(out)}/{n} teams", flush=True)
    json.dump(res, open(os.path.join(HERE, "m135_ret.json"), "w"), indent=0)
    for s in ("2018-19", "2023-24"):
        for t in list(res.get(s, {}))[:6]: print(s, t, res[s][t])



