# Upset Model trained per round group: R64 | R32 | S16 | E8+F4+title. Same 28 inputs (no seed gap, no net rating),
# ridge logistic lam 30 with half-life-12 weights, outcome = lower seed won (equal seeds: the simulator's favorite counts as
# the higher seed), each tournament held out within its round group. Compared with the Strongside Model and the simulator.
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
    H, L, sH, sL = (a, b, sa, sb) if sa <= sb else (b, a, sb, sa)          # tie: fav (simulator favorite) is H
    up = int((g["fav_won"] and L == a) or (not g["fav_won"] and L == b))
    rows.append(dict(i=i, s=g["season"], r=g["rnd"], H=H, L=L, sH=sH, sL=sL, up=up, HisS=(H == B.Sname[i])))
n = len(rows); y = np.array([r["up"] for r in rows]); seas = np.array([r["s"] for r in rows]); rnd = np.array([r["r"] for r in rows])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
F = {}
for k in sorted({k[2:] for k in KS if k[:2] in ("S ", "W ")}):
    if "S " + k in KS and "W " + k in KS:
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
add(json.load(open(os.path.join(HERE, "m186_vol.json"))), ["mar_sd"], "3pt/vol: ")
add(json.load(open(os.path.join(HERE, "m144_basic.json"))), ["ppg"], "basic: ")
add(json.load(open(os.path.join(HERE, "m135_ret.json"))), ["returning"])
SEAS = sorted({g["season"] for g in G}); TW = {}
for g in G:
    if g["rnd"] != "First Four": w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
for side in "HL":
    F[f"{side} tourney wins last 3"] = np.array([sum(TW.get((p, r[side]), 0) for p in SEAS[max(0, SEAS.index(r["s"]) - 3):SEAS.index(r["s"])]) for r in rows], float)
INPUTS = json.load(open(os.path.join(HERE, "m188_out.json")))["inputs"]
def col(name):
    lab, k = name.split(" ", 1); return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
XM = np.column_stack([col(c) for c in INPUTS]); W = Q.WT[gi]
def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
def auc(s, yy):
    if yy.sum() in (0, len(yy)): return float("nan")
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
GROUPS = [("Round of 64", ["First round"]), ("Round of 32", ["Second round"]), ("Sweet 16", ["Sweet 16"]), ("Elite 8 + Final Four + title", ["Elite Eight", "Final Four", "Championship"])]
p_up = np.zeros(n)
for gname, rr in GROUPS:
    m = np.isin(rnd, rr)
    for s in sorted(set(seas[m])):
        tr, te = m & (seas != s), m & (seas == s); p_up[te] = 1 / (1 + np.exp(-ridge(XM[tr], y[tr], W[tr])(XM[te])))
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))
simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
def right(p, cut): return (p >= cut) == (y == 1)
print(f"games {n} | upsets (lower seed won) {int(y.sum())} | equal-seed games {int(sum(r['sH'] == r['sL'] for r in rows))}")
print(f"{'round group':30} {'games':>5} {'upsets':>6} | {'Upset Model 50%':>16} {'45%':>5} {'40%':>5} {'AUC':>6} | {'Strongside':>10} {'Simulator':>9} {'Higher seed':>11}")
tot = {c: 0 for c in ("u50", "u45", "u40", "m1", "sim", "hs")}
for gname, rr in GROUPS + [("ALL ROUNDS", ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"])]:
    m = np.isin(rnd, rr)
    vals = dict(u50=int(right(p_up, .5)[m].sum()), u45=int(right(p_up, .45)[m].sum()), u40=int(right(p_up, .4)[m].sum()),
                m1=int(right(m1_up, .5)[m].sum()), sim=int(right(sim_up, .5)[m].sum()), hs=int((y[m] == 0).sum()))
    print(f"{gname:30} {int(m.sum()):5d} {int(y[m].sum()):6d} | {vals['u50']:16d} {vals['u45']:5d} {vals['u40']:5d} {auc(p_up[m], y[m]):6.3f} | {vals['m1']:10d} {vals['sim']:9d} {vals['hs']:11d}")
for gname, rr in GROUPS:
    m = np.isin(rnd, rr); pk = (p_up >= .4) & m
    print(f"   {gname}: at 40% the Upset Model picks {int(pk.sum())} upsets ({pk.sum() / 16:.1f} a year), {int((pk & (y == 1)).sum())} hit")
json.dump({"p_up": p_up.tolist(), "rows": rows}, open(os.path.join(HERE, "m192_out.json"), "w"))
