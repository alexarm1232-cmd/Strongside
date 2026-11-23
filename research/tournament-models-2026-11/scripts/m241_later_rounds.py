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
# ---- later rounds with the SAME 31 Upset Model inputs (no re-picking): refit per round group, each year held out
kk = lambda s: (s or "").rstrip(". ")
HV = json.load(open(os.path.join(HERE, "m210_halves.json")))
ROOT = r"C:\Users\crtra\Downloads\basketball"
t = open(os.path.join(ROOT, "dashboard", "tourneyreport.js"), encoding="utf-8").read()
T = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1]); PL = {}
for gi_, e in enumerate(T["inputs"]["live"]):
    g = T["games"][gi_]
    for nm, blk in ((kk(g[3]), e[1]), (kk(g[4]), e[2])): PL[(str(g[9]), nm)] = np.array(blk[1], float)
def cast(P):
    g_, mins, bpm = P[:, 0], P[:, 1], P[:, 2]; mpg = mins / np.maximum(g_, 1); rot = np.where(mpg >= 10)[0]
    if len(rot) < 3: return np.nan
    top = rot[np.argsort(-bpm[rot])[:2]]; rest = np.setdiff1d(rot, top); return float(np.average(bpm[rest], weights=mins[rest])) if len(rest) else np.nan
for side in "HL":
    v = np.array([cast(PL[(str(G[r["i"]]["gid"]), kk(r[side]))]) if (str(G[r["i"]]["gid"]), kk(r[side])) in PL else np.nan for r in rows])
    print(f"cast BPM missing ({side}): {int(np.isnan(v).sum())}"); v[np.isnan(v)] = np.nanmean(v); F[f"{side} cast_bpm_bpm"] = v
col = lambda c: (F["L " + c.split(" ", 1)[1]] - F["H " + c.split(" ", 1)[1]]) if c.startswith("L-H ") else F[c]
INS = json.load(open(os.path.join(HERE, "m230_out.json")))["inputs"]
X = np.column_stack([col(c) for c in INS])
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
def auc(s, yy):
    if yy.sum() in (0, len(yy)): return float("nan")
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
sig = lambda z: 1 / (1 + np.exp(-z))
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
R1 = rnd == "First round"; early = np.array([int(s_[:4]) < 2018 for s_ in seas])
f64 = ridge(X[R1], y[R1], W[R1])   # the Round 1 Upset Model as is (fit on all Round 1 games)
GROUPS = {"Round of 32": rnd == "Second round", "Sweet 16": rnd == "Sweet 16", "Elite 8 + Final Four + title": np.isin(rnd, ["Elite Eight", "Final Four", "Championship"]), "Sweet 16 to title": np.isin(rnd, ["Sweet 16", "Elite Eight", "Final Four", "Championship"])}
right = lambda pk, m: int((pk[m] == (y[m] == 1)).sum())
for gname, M in GROUPS.items():
    nG = int(M.sum()); ups = int(y[M].sum())
    ho = np.zeros(n); allfit = sig(ridge(X[M], y[M], W[M])(X))
    for s_ in sorted(set(seas[M])):
        tr, te = M & (seas != s_), M & (seas == s_); ho[te] = sig(ridge(X[tr], y[tr], W[tr])(X[te]))
    fw = sig(ridge(X[M & early], y[M & early], W[M & early])(X)); bw = sig(ridge(X[M & ~early], y[M & ~early], W[M & ~early])(X))
    r64 = sig(f64(X))
    print(f"\n=== {gname}: {nG} games, {ups} upsets ({ups / nG:.0%}) | higher seed every time {nG - ups}")
    print("   model | AUC fit all yrs | right fit all yrs | AUC held out | right held out | upset picks held out (hit) | fwd (18-26) | back (10-17)")
    def line(lab, pa, ph, cut, pf=None, pb=None):
        fwbw = f"{right(pf >= cut, M & ~early)}/{int((M & ~early).sum())} | {right(pb >= cut, M & early)}/{int((M & early).sum())}" if pf is not None else "— | —"
        print(f"   {lab:34} | {auc(pa[M], y[M]):.3f} | {right(pa >= cut, M)} | {auc(ph[M], y[M]):.3f} | {right(ph >= cut, M)} | {int((ph[M] >= cut).sum())} ({int(((ph >= cut) & M & (y == 1)).sum())}) | {fwbw}")
    line("Upset Model refit on this round (40%)", allfit, ho, .4, fw, bw)
    line("Upset Model refit on this round (50%)", allfit, ho, .5, fw, bw)
    line("Round 1 Upset Model as is (40%)", r64, r64, .4)
    line("Original model", s_up, s_up, .5); line("Simulator", sim_up, sim_up, .5)
    a_all, a_ho = (allfit + s_up + sim_up) / 3, (ho + s_up + sim_up) / 3
    line("Average of 3, refit Upset (45%)", a_all, a_ho, .45, (fw + s_up + sim_up) / 3, (bw + s_up + sim_up) / 3)
    line("Average of 3, refit Upset (50%)", a_all, a_ho, .5, (fw + s_up + sim_up) / 3, (bw + s_up + sim_up) / 3)
    line("Average of original + simulator (50%)", (s_up + sim_up) / 2, (s_up + sim_up) / 2, .5)