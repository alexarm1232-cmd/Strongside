# Upset Models per round group with their OWN inputs: R64 keeps the user's 28; R32, S16 and E8+F4+title each pick inputs
# from their own games: |z| >= 2 with the seed gap controlled, drop overlap with the net rating gap (|r| >= 0.3), one per
# overlap group (|r| >= 0.3). Scored two ways: inputs picked on all years, and inputs re-picked inside each held-out fold.
import os, sys, json, math, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
B = Q.R.B; G = B.G; TM = B.TM
ns = {"__file__": os.path.join(Q.OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(Q.OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS = ns["X"], ns["KS"]
rows = []
for i, g in enumerate(G):
    if g["rnd"] == "First Four": continue
    a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
    H, L, sH, sL = (a, b, sa, sb) if sa <= sb else (b, a, sb, sa)
    up = int((g["fav_won"] and L == a) or (not g["fav_won"] and L == b))
    rows.append(dict(i=i, s=g["season"], r=g["rnd"], H=H, L=L, sH=sH, sL=sL, up=up, HisS=(H == B.Sname[i])))
n = len(rows); y = np.array([r["up"] for r in rows]); seas = np.array([r["s"] for r in rows]); rnd = np.array([r["r"] for r in rows])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); W = Q.WT[gi]
sgap = np.array([r["sL"] - r["sH"] for r in rows], float); rgap = np.array([TM[r["s"]][r["H"]]["adj_net"] - TM[r["s"]][r["L"]]["adj_net"] for r in rows])
F = {}
for k in sorted({k[2:] for k in KS if k[:2] in ("S ", "W ")}):
    if "S " + k in KS and "W " + k in KS and k not in ("adj_net", "adj_o", "adj_d"):
        sv, wv = X[gi, KS.index("S " + k)], X[gi, KS.index("W " + k)]; F["H " + k] = np.where(hsS, sv, wv); F["L " + k] = np.where(hsS, wv, sv)
def add(src, keys_, label=""):
    for k in keys_:
        for side in "HL":
            v = []
            for r in rows:
                d = src.get(r["s"], {}); t = r[side]; x = (d.get(t) or d.get(t + ".") or {}).get(k)
                arr = [vv.get(k) for vv in d.values() if vv.get(k) is not None and vv.get(k) == vv.get(k)]
                v.append(np.nan if x is None or x != x or not arr else float(np.searchsorted(np.sort(arr), x, side="right") / len(arr)))
            v = np.array(v); v[np.isnan(v)] = 0.5; F[f"{side} {label}{k}"] = v
add(json.load(open(os.path.join(HERE, "m186_vol.json"))), ["r3", "tpa_pg", "p3", "p3_sd", "hot", "cold", "pts_sd", "mar_sd", "max3", "hot_vol"], "3pt/vol: ")
add(json.load(open(os.path.join(HERE, "m144_basic.json"))), ["ppg", "papg", "margin", "win_pct", "fg_pct", "fg3_pct", "ft_pct", "rpg", "apg", "topg", "spg", "bpg", "opp_fg_pct"], "basic: ")
add(json.load(open(os.path.join(HERE, "m129_pg.json"))), ["guard_exp", "top2_guard_exp"], "guards: ")
add(json.load(open(os.path.join(HERE, "m135_ret.json"))), ["returning"])
SEAS = sorted({g["season"] for g in G}); TW = {}
for g in G:
    if g["rnd"] != "First Four": w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
for side in "HL":
    F[f"{side} tourney wins last 3"] = np.array([sum(TW.get((p, r[side]), 0) for p in SEAS[max(0, SEAS.index(r["s"]) - 3):SEAS.index(r["s"])]) for r in rows], float)
CAND = {}
for k in sorted({k[2:] for k in F}):
    if "L " + k in F: CAND["L " + k] = F["L " + k]
    if "H " + k in F: CAND["H " + k] = F["H " + k]
    if "L " + k in F and "H " + k in F: CAND["L-H " + k] = F["L " + k] - F["H " + k]
CAND = {k: v for k, v in CAND.items() if v.std() > 0}
def zc(v, m):
    Xs = np.column_stack([sgap[m], v[m], np.ones(m.sum())]); w = np.zeros(3); yy = y[m]
    for _ in range(40):
        p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]) + 1e-6 * np.eye(3); w += np.linalg.solve(Hm, Xs.T @ (yy - p))
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
def select(m):
    zs = {k: zc(v, m) for k, v in CAND.items()}
    order = sorted([k for k in zs if abs(zs[k]) >= 2], key=lambda k: -abs(zs[k])); kept = []
    for c in order:
        v = CAND[c][m]
        if abs(np.corrcoef(v, rgap[m])[0, 1]) >= 0.3: continue
        if any(abs(np.corrcoef(v, CAND[k][m])[0, 1]) >= 0.3 for k in kept): continue
        kept.append(c)
    return kept, zs
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
def auc(s, yy):
    if yy.sum() in (0, len(yy)): return float("nan")
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
# Round 1 Upset Model: all 12 play types offense AND defense (points per play, lower-minus-higher seed gaps) + the 28 measures
# picked together + starters' BPM gap. No seed, no net rating input. Forward test and each year held out.
R1 = rnd == "First round"; early = np.array([int(s[:4]) < 2017 for s in seas]); TR, TE = R1 & early, R1 & ~early
PT = ["Rim Attack", "Drive & Kick", "Dribble Jumper", "Mid-Range", "Perimeter Cut", "Big Cut & Roll", "Post-Up", "Inside Out", "Pick & Pop", "High-Low", "Rebound Scores", "Transition"]
U28 = json.load(open(os.path.join(HERE, "m188_out.json")))["inputs"]
V39 = list(dict.fromkeys(U28 + [f"L-H pt_ppp {t}" for t in PT])); V46 = list(dict.fromkeys(U28 + ["L-H starters_bpm"] + [f"L-H pt_ppp {t}" for t in PT] + [f"L-H pt_d_ppp {t}" for t in PT])); ALLIN = V46
ALLIN = [c for c in ALLIN if c in CAND]
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
print(f"inputs: {len(ALLIN)} ({len(U28)} picked together + starters BPM + play types; duplicates counted once)")
def run(ins, lam=30.0):
    Xg = np.column_stack([CAND[c] for c in ins])
    p = 1 / (1 + np.exp(-ridge(Xg[TR], y[TR], W[TR], lam)(Xg[TE]))); out = np.zeros(n)
    for s in sorted(set(seas[R1])):
        tr, te = R1 & (seas != s), R1 & (seas == s); out[te] = 1 / (1 + np.exp(-ridge(Xg[tr], y[tr], W[tr], lam)(Xg[te])))
    ins_auc = auc(1 / (1 + np.exp(-ridge(Xg[R1], y[R1], W[R1], lam)(Xg[R1]))), y[R1])
    return p, out, ins_auc
for label, INS in (("original 28", U28), ("28 + offensive play types", V39), ("46 inputs", V46)):
    ALLIN = [c for c in INS if c in CAND]; lam = 30.0
    p, out, ia = run(ALLIN, lam)
    print(f"\n== {label}: {len(ALLIN)} inputs")
    print(f"   forward (fit 2010-17, test 2018-26): AUC {auc(p, y[TE]):.3f} | right at 50% {int(((p >= .5) == (y[TE] == 1)).sum())} · 45% {int(((p >= .45) == (y[TE] == 1)).sum())} · 40% {int(((p >= .4) == (y[TE] == 1)).sum())} of 255 | upset picks at 40% {int((p >= .4).sum())} ({int(((p >= .4) & (y[TE] == 1)).sum())} hit)")
    print(f"   each year held out, all 511:          AUC {auc(out[R1], y[R1]):.3f} | right at 50% {int(((out[R1] >= .5) == (y[R1] == 1)).sum())} · 45% {int(((out[R1] >= .45) == (y[R1] == 1)).sum())} · 40% {int(((out[R1] >= .4) == (y[R1] == 1)).sum())} of 511 | upset picks at 40% {int((out[R1] >= .4).sum())} ({int(((out[R1] >= .4) & (y[R1] == 1)).sum())} hit) | training AUC {ia:.3f}")
print(f"\n2018-26: Strongside {int(((m1_up[TE] >= .5) == (y[TE] == 1)).sum())} (AUC {auc(m1_up[TE], y[TE]):.3f}) | Simulator {int(((sim_up[TE] >= .5) == (y[TE] == 1)).sum())} | Higher seed {int((y[TE] == 0).sum())}")
print(f"all 511:  Strongside {int(((m1_up[R1] >= .5) == (y[R1] == 1)).sum())} (AUC {auc(m1_up[R1], y[R1]):.3f}) | Simulator {int(((sim_up[R1] >= .5) == (y[R1] == 1)).sum())} | Higher seed {int((y[R1] == 0).sum())}")
json.dump({"inputs": V39}, open(os.path.join(HERE, "m200_inputs39.json"), "w"))

