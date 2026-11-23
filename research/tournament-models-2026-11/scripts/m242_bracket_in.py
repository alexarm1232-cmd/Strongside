# Stage 1 for bracket scoring: per year, the 32 Round of 64 games in bracket order (adjacent pairs meet next), each
# team's simulator block key (its Round of 64 game id + name as in tourneyreport.js), each strategy's Round 1 pick, and
# every team's real tournament wins. Written as dashboard/_bracket_in.js for the simulator page to read.
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
ROOT = r"C:\Users\crtra\Downloads\basketball"; kk = lambda s: (s or "").rstrip(". ")
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
pho = np.array(json.load(open(os.path.join(H, "m230_out.json")))["p_heldout"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (pho + s_up + sim_up) / 3
G = Q.R.B.G
t = open(os.path.join(ROOT, "dashboard", "tourneyreport.js"), encoding="utf-8").read(); T = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
TG = {str(g[9]): (kk(g[3]), kk(g[4])) for g in T["games"]}
R1 = {r["i"]: j for j, r in enumerate(rows)}
ORDER = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
out = {}
for s in sorted({g["season"] for g in G}):
    idx = [i for i, g in enumerate(G) if g["season"] == s and g["rnd"] in ORDER]
    by = {rd: [i for i in idx if G[i]["rnd"] == rd] for rd in ORDER}
    teams = lambda i: (kk(G[i]["fav"]), kk(G[i]["dog"]))
    wins = {}
    for i in idx: w = kk(G[i]["fav"] if G[i]["fav_won"] else G[i]["dog"]); wins[w] = wins.get(w, 0) + 1
    def feed(i, rd_i):
        """bracket-ordered list of Round of 64 'slots' under game i"""
        if rd_i == 0: return [i]
        res = []
        for tm in teams(i):
            ch = next((j for j in by[ORDER[rd_i - 1]] if tm in teams(j)), None)
            res += feed(ch, rd_i - 1) if ch is not None else [("bye", tm, rd_i - 1)]
        return res
    slots = feed(by["Championship"][0], 5)
    games = []
    for sl in slots:
        if isinstance(sl, tuple):   # 2021 VCU-Oregon no-contest: Oregon advances, no Round 1 points
            tm = sl[1]; games.append({"bye": tm, "seedA": None}); continue
        j = R1[sl]; r = rows[j]; gid = str(G[sl]["gid"]); nm = TG.get(gid)
        Hn, Ln = kk(r["H"]), kk(r["L"])
        assert nm and Hn in nm and Ln in nm, (s, gid, nm, Hn, Ln)
        games.append({"gid": gid, "H": Hn, "L": Ln, "sH": r["sH"], "sL": r["sL"], "won": Ln if y[j] else Hn,
                      "pick": {"avg": Ln if avg[j] >= .45 else Hn, "upset": Ln if pho[j] >= .4 else Hn, "sim": Ln if sim_up[j] >= .5 else Hn,
                               "orig": Ln if s_up[j] >= .5 else Hn, "chalk": Hn}})
    # the bye team still needs a block: its Round of 32 game's id
    for g in games:
        if "bye" in g:
            i2 = next(i for i in by["Second round"] if g["bye"] in teams(i)); g["gid"] = str(G[i2]["gid"]); g["H"] = g["L"] = g["won"] = g["bye"]
            g["sH"] = g["sL"] = next(G[i2]["fseed"] if kk(G[i2]["fav"]) == g["bye"] else G[i2]["dseed"] for _ in [0]); g["pick"] = {k: g["bye"] for k in ("avg", "upset", "sim", "orig", "chalk")}
    seeds = {}
    for g in games: seeds[g["H"]] = g["sH"]; seeds[g["L"]] = g["sL"]
    out[s] = {"games": games, "wins": wins, "seeds": seeds}
    assert len(games) == 32, (s, len(games))
open(os.path.join(ROOT, "dashboard", "_bracket_in.js"), "w", encoding="utf-8").write("window.BRACKET_IN = " + json.dumps(out) + ";")
print("seasons", len(out), "| e.g. 2026 first 4 games:", [(g["H"], g["L"], g["pick"]["avg"]) for g in out["2025-26"]["games"][:4]])