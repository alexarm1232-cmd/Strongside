# Side test: does the Round 1 result carry into the Round of 32? (momentum)
#  - big upset in Round 1 (team seeded 11+, 12+, ... 15+ that beat a better seed)
#  - Round 1 margin, close win (<= 5) vs blowout (>= 15), margin over the simulator's expected margin for that game
# Tested with the seed gap controlled, and beyond model 1 + simulator; both eras; plus actual vs predicted by seed.
import os, sys, json, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RNDS"] = "Second round"
src = open(os.path.join(HERE, "m247_s16_model.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("allm = np.ones")])
import numpy as np
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
su, si = s_up[idx], sim_up[idx]; lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
R1 = {}
for g in G:
    if g["rnd"] != "First round": continue
    w = g["fav"] if g["fav_won"] else g["dog"]; mar = abs(g["fav_margin"]); exp_ = g["sim_line"] if g["fav_won"] else -g["sim_line"]
    ws, ls = (g["fseed"], g["dseed"]) if g["fav_won"] else (g["dseed"], g["fseed"])
    R1[(g["season"], w)] = dict(mar=mar, over=mar - exp_, seed=ws, oppseed=ls)
FT = {}; miss = 0
for side in "HL":
    vals = []
    for i in idx:
        r = rows[i]; d = R1.get((r["s"], r[side]))
        if d is None: miss += 1; d = dict(mar=np.nan, over=np.nan, seed=r["s" + side], oppseed=np.nan)
        vals.append(d)
    FT[side] = vals
print(f"Round of 32: {nS} games, {int(ys.sum())} lower-seed wins | Round 1 result missing for {miss} team slots")
FE = {}
for side in "HL":
    mar = np.array([d["mar"] for d in FT[side]], float); ov = np.array([d["over"] for d in FT[side]], float)
    mar[np.isnan(mar)] = np.nanmean(mar); ov[np.isnan(ov)] = np.nanmean(ov)
    sd_ = np.array([d["seed"] for d in FT[side]], float); op = np.array([d["oppseed"] for d in FT[side]], float)
    up = (sd_ > op)
    FE[f"{side} R1 margin"] = mar; FE[f"{side} R1 margin over simulator"] = ov
    FE[f"{side} R1 close win (<=5)"] = (mar <= 5).astype(float); FE[f"{side} R1 blowout (>=15)"] = (mar >= 15).astype(float)
    FE[f"{side} R1 upset win"] = up.astype(float)
    for k in (10, 11, 12, 13, 14, 15): FE[f"{side} R1 upset as {k}+ seed"] = (up & (sd_ >= k)).astype(float)
for b in ("R1 margin", "R1 margin over simulator"): FE[f"L-H {b}"] = FE[f"L {b}"] - FE[f"H {b}"]
allm = np.ones(nS, bool)
def mwz(v, yy):
    o = np.argsort(v, kind="mergesort"); r = np.empty(len(v)); r[o] = np.arange(1, len(v) + 1)
    for u in np.unique(v):
        t = v == u
        if t.sum() > 1: r[t] = r[t].mean()
    n1 = yy.sum(); n0 = len(yy) - n1; return (r[yy == 1].sum() - n1 * (n1 + 1) / 2 - n1 * n0 / 2) / math.sqrt(n1 * n0 * (len(yy) + 1) / 12)
nice = lambda c: c.replace("L-H ", "gap (lower − higher): ").replace("H ", "higher seed: ", 1).replace("L ", "lower seed: ", 1) if c[:2] in ("H ", "L ") or c.startswith("L-H") else c
print(f"\n{'measure':52} {'teams':>5} {'z seed':>7} {'beyond M1+sim':>13} {'10-17':>6} {'18-26':>6} {'MW':>6} {'r seed gap':>10}")
for c, v in FE.items():
    if np.std(v) < 1e-9: print(f"{nice(c):52}  (no variation)"); continue
    try: zs = wald(v, ys, allm, [sg]); zd = wald(v, ys, allm, [sg, lg(su), lg(si)]); e1 = wald(v, ys, early, [sg]); e2 = wald(v, ys, ~early, [sg])
    except Exception as ex: print(f"{nice(c):52}  (fit failed)"); continue
    cnt = int(v.sum()) if set(np.unique(v)) <= {0, 1} else ""
    print(f"{nice(c):52} {cnt!s:>5} {zs:+7.2f} {zd:+13.2f} {e1:+6.1f} {e2:+6.1f} {mwz(v, ys):+6.2f} {np.corrcoef(v, sg)[0, 1]:+10.2f}")
# actual vs predicted, by the lower seed's seed (every 10+ seed in the Round of 32 got there with a Round 1 upset)
sL = np.array([rows[i]["sL"] for i in idx]); sH = np.array([rows[i]["sH"] for i in idx])
print("\nlower seed in the Round of 32 | games | won | actual | model 1 said | simulator said")
for lo, hi in ((5, 9), (10, 10), (11, 11), (12, 12), (13, 15), (10, 15), (11, 15), (12, 15)):
    m = (sL >= lo) & (sL <= hi)
    if m.sum(): print(f"   seed {lo}-{hi:<2} | {int(m.sum()):3} | {int(ys[m].sum()):3} | {ys[m].mean():5.0%} | {su[m].mean():5.0%} | {si[m].mean():5.0%}")
mar_L = FE["L R1 margin"]; ov_L = FE["L R1 margin over simulator"]
print("\nlower seed's Round 1 win | games | lower seed won R32 | model 1 said | simulator said")
for lab, m in (("close (<= 5)", mar_L <= 5), ("6-14", (mar_L > 5) & (mar_L < 15)), ("blowout (>= 15)", mar_L >= 15)):
    print(f"   {lab:16} | {int(m.sum()):3} | {ys[m].mean():5.0%} ({int(ys[m].sum())}) | {su[m].mean():5.0%} | {si[m].mean():5.0%}")
for lab, m in (("beat sim by 10+", ov_L >= 10), ("within 10 of sim", np.abs(ov_L) < 10), ("10+ under sim", ov_L <= -10)):
    print(f"   {lab:16} | {int(m.sum()):3} | {ys[m].mean():5.0%} ({int(ys[m].sum())}) | {su[m].mean():5.0%} | {si[m].mean():5.0%}")
mar_H = FE["H R1 margin"]
print("\nhigher seed's Round 1 win | games | lower seed won R32 | model 1 said | simulator said")
for lab, m in (("close (<= 5)", mar_H <= 5), ("6-14", (mar_H > 5) & (mar_H < 15)), ("blowout (>= 15)", mar_H >= 15)):
    print(f"   {lab:16} | {int(m.sum()):3} | {ys[m].mean():5.0%} ({int(ys[m].sum())}) | {su[m].mean():5.0%} | {si[m].mean():5.0%}")
json.dump({k: v.tolist() for k, v in FE.items()}, open(os.path.join(HERE, "m257_momentum.json"), "w"))
