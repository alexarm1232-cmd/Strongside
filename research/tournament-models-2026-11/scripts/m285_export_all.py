# All four Rounds 1-2 brackets per year as one JSON for the page: games (bracket order), seeds, real winners, each picker's picks.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m282_bracket_r1r2.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
UP = json.load(open(os.path.join(HERE, "m284_upset_picks.json")))
sig = lambda z: 1 / (1 + np.exp(-z))
DATA = []
for s in SEASONS:
    games = BI[s]["games"]; wins = BI[s]["wins"]
    seeds = {}
    for g in games: seeds[g["H"]] = g["sH"]; seeds[g["L"]] = g["sL"]
    r2won = []
    for q in range(16):
        ts = [t for g in games[2 * q:2 * q + 2] for t in (g["H"], g["L"])]
        r2won.append(next((t for t in ts if wins.get(t, 0) >= 2), None))
    B_ = {}
    # higher seed
    r1 = [{"pick": g["H"], "p": None} for g in games]
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; r2.append({"pick": chalk2(s, a, b), "p": None})
    B_["seed"] = {"r1": r1, "r2": r2}
    # regular model
    r1 = []
    for g in games:
        pk = r1_model_pick(s, g)
        if g["H"] == g["L"]: r1.append({"pick": pk, "p": None}); continue
        i = gid2i[str(g["gid"])]; pS = float(sig(OUT_I[i])); r1.append({"pick": pk, "p": round(pS if kk(B.Sname[i]) == kk(pk) else 1 - pS, 3)})
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; S_, W_, z = PZ[(s, kk(a), kk(b))]; w = r32_model_pick(s, a, b)
        pS = float(sig(z)); r2.append({"pick": w, "p": round(pS if kk(w) == S_ else 1 - pS, 3)})
    B_["model"] = {"r1": r1, "r2": r2}
    # simulator
    r1 = []
    for g in games:
        pk = r1_sim_pick(s, g)
        if g["H"] == g["L"]: r1.append({"pick": pk, "p": None}); continue
        i = gid2i[str(g["gid"])]; pS = float(B.simS[i]); r1.append({"pick": pk, "p": round(pS if kk(B.Sname[i]) == kk(pk) else 1 - pS, 3)})
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; w = r32_sim_pick(s, a, b)
        p = SR[s].get(f"{a}|{b}"); p = p if p is not None else 1 - SR[s][f"{b}|{a}"]
        r2.append({"pick": w, "p": round(p if w == a else 1 - p, 3)})
    B_["sim"] = {"r1": r1, "r2": r2}
    B_["upset"] = UP[s]
    DATA.append({"season": s, "year": int(s[:4]) + 1, "seeds": seeds,
                 "games": [{"a": g["H"], "b": g["L"], "won": g["won"], "bye": g["H"] == g["L"]} for g in games],
                 "r2won": r2won, "brackets": B_})
# score check
for key in ("seed", "model", "sim", "upset"):
    r1r = sum(int(d["brackets"][key]["r1"][j]["pick"] == g["won"]) for d in DATA for j, g in enumerate(d["games"]) if not g["bye"])
    r2r = sum(int(d["brackets"][key]["r2"][q]["pick"] == d["r2won"][q]) for d in DATA for q in range(16))
    print(key, r1r, r2r, r1r + 2 * r2r)
json.dump(DATA, open(os.path.join(HERE, "m285_brackets.json"), "w"), separators=(",", ":"))
