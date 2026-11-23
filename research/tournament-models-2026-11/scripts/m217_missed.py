# What do the upsets the locked 28-input Upset Model MISSES have in common that it doesn't track?
# Missed = upset happened, model gave it < 40% (held out). Compared against the games it also called "no upset" where the
# higher seed did win. Every measure not already in the 28 (full pool + supporting-cast BPM + close-game halves).
# Candidates are then added to the 28 and tested held out, forward, backward, and with an HONEST nested version where the
# misses and the picked measures are found inside the training years only.
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from m210_followups import F, rows, y, n, seas, sg, U, ridge, auc, kk, col
import m99_model_types as Q
W = Q.WT[[r["i"] for r in rows]]; ROOT = r"C:\Users\crtra\Downloads\basketball"
# extra sources from the last round
HV = json.load(open(os.path.join(HERE, "m210_halves.json")))
for kx in ("all_h1", "all_h2", "c10_h1", "c10_h2", "c10_win", "c10_share", "c5_h1", "c5_h2", "c5_win"):
    for side in "HL":
        v = np.array([(HV.get(r["s"], {}).get(kk(r[side])) or {}).get(kx, np.nan) for r in rows], float); v[np.isnan(v)] = np.nanmean(v); F[f"{side} half: {kx}"] = v
t = open(os.path.join(ROOT, "dashboard", "tourneyreport.js"), encoding="utf-8").read()
T = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1]); PL = {}
for gi, e in enumerate(T["inputs"]["live"]):
    g = T["games"][gi]
    for nm, blk in ((kk(g[3]), e[1]), (kk(g[4]), e[2])): PL[(str(g[9]), nm)] = np.array(blk[1], float)
G = Q.R.B.G
def cast(P, how):
    g_, mins, bpm = P[:, 0], P[:, 1], P[:, 2]; mpg = mins / np.maximum(g_, 1); rot = np.where(mpg >= 10)[0]
    if len(rot) < 3: return np.nan
    top = rot[np.argsort(-mins[rot])[:2]] if how == "min" else rot[np.argsort(-bpm[rot])[:2]]; rest = np.setdiff1d(rot, top)
    return float(np.average(bpm[rest], weights=mins[rest])) if len(rest) else np.nan
for how in ("min", "bpm"):
    for side in "HL":
        v = np.array([cast(PL[(str(G[r["i"]]["gid"]), kk(r[side]))], how) if (str(G[r["i"]]["gid"]), kk(r[side])) in PL else np.nan for r in rows])
        v[np.isnan(v)] = np.nanmean(v); F[f"{side} cast_bpm_{how}"] = v
used = {c.split(" ", 1)[1] for c in U}
CAND = {}
for k in sorted({k[2:] for k in F}):
    if k in used: continue
    for lab in ("L", "H", "L-H"):
        if lab == "L-H" and not ("L " + k in F and "H " + k in F): continue
        if lab != "L-H" and lab + " " + k not in F: continue
        v = col(f"{lab} {k}")
        if v.std() > 0: CAND[f"{lab} {k}"] = v
TM = Q.R.B.TM; rg = np.array([TM[r["s"]][r["L"]]["adj_net"] - TM[r["s"]][r["H"]]["adj_net"] for r in rows])
early = np.array([int(s[:4]) < 2018 for s in seas])

def heldout(X, mask_tr=None):
    out = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    return out
def zc(v, m):
    vv = (v[m] - v[m].mean()) / (v[m].std() + 1e-12); Xs = np.column_stack([sg[m], vv, np.ones(m.sum())]); w = np.zeros(3); yy = y[m]
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]) + 1e-9 * np.eye(3); w += np.linalg.solve(Hm, Xs.T @ (yy - p))
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
def screen(p, m):
    """among games in m the model called 'no upset' (p < .4): which measures separate the missed upsets from the higher-seed wins"""
    low = m & (p < .4); res = []
    for nm, v in CAND.items():
        if v[low].std() == 0: continue
        res.append((abs(zc(v, low)), nm, zc(v, low)))
    res.sort(reverse=True); return res, low
X28 = np.column_stack([col(c) for c in U]); p28 = heldout(X28)
res, low = screen(p28, np.ones(n, bool))
miss = low & (y == 1); ok = low & (y == 0)
print(f"Upset Model (28) held out: {int(((p28 >= .4) == (y == 1)).sum())}/511 | upsets 143: caught {int(((p28 >= .4) & (y == 1)).sum())}, missed {int(miss.sum())} | 'no upset' calls where the higher seed won: {int(ok.sum())}")
print("missed upsets by matchup:", {f"{17 - h} over {h}": int((miss & (np.array([r['sH'] for r in rows]) == h)).sum()) for h in range(1, 9)})
print(f"\nmeasures NOT in the 28 that separate the {int(miss.sum())} missed upsets from the {int(ok.sum())} correct 'no upset' calls ({len(res)} tests; ~{int(len(res) * .046)} pass |z|>=2 by chance)")
print("measure | missed upsets avg | higher-seed wins avg | z (seed controlled) | same sign both eras | r with net rating gap")
top = []
for _, nm, z in res[:40]:
    v = CAND[nm]; e1, e2 = zc(v, low & early), zc(v, low & ~early)
    print(f"{nm}|{v[miss].mean():.3f}|{v[ok].mean():.3f}|{z:+.2f}|{'yes' if np.sign(e1) == np.sign(e2) else 'no'} ({e1:+.1f}/{e2:+.1f})|{np.corrcoef(v, rg)[0, 1]:+.2f}")
# candidates: top by z, same sign in both eras, |r with net rating| < .6, not overlapping each other (|r| < .7)
for _, nm, z in res:
    v = CAND[nm]
    if abs(np.corrcoef(v, rg)[0, 1]) >= .6 or np.sign(zc(v, low & early)) != np.sign(zc(v, low & ~early)): continue
    if any(abs(np.corrcoef(v, CAND[o])[0, 1]) >= .7 for o in top): continue
    top.append(nm)
    if len(top) == 12: break
def full(ins):
    X = np.column_stack([col(c) if c in U else CAND[c] for c in ins]); p = heldout(X)
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    return int(((p >= .4) == (y == 1)).sum()), auc(p, y), int(((f >= .4) == (y[~early] == 1)).sum()), int(((b >= .4) == (y[early] == 1)).sum()), int((p >= .4).sum()), int(((p >= .4) & (y == 1)).sum())
b0 = full(U)
print(f"\nadding each candidate to the 28 (held out /511 | forward /255 | backward /288 | fwd+back /543)")
print(f"   {'locked 28':46} {b0[0]} | AUC {b0[1]:.3f} | fwd {b0[2]} | back {b0[3]} | {b0[2] + b0[3]} | picks {b0[4]} ({b0[5]} hit)")
good = []
for c in top:
    r = full(U + [c]); print(f"   + {c:44} {r[0]} ({r[0] - b0[0]:+d}) | AUC {r[1]:.3f} | fwd {r[2]} | back {r[3]} | {r[2] + r[3]} ({r[2] + r[3] - b0[2] - b0[3]:+d}) | picks {r[4]} ({r[5]} hit)")
    if r[0] > b0[0] and r[2] + r[3] > b0[2] + b0[3]: good.append(c)
if good:
    r = full(U + good); print(f"   + all that helped both ways ({len(good)}): {good}\n     {r[0]} ({r[0] - b0[0]:+d}) | AUC {r[1]:.3f} | fwd {r[2]} | back {r[3]} | {r[2] + r[3]} ({r[2] + r[3] - b0[2] - b0[3]:+d}) | picks {r[4]} ({r[5]} hit)")
# honest nested: for each held-out year, find the misses and pick the top 3 measures using the training years only
print("\nHONEST version (misses + measures picked inside the training years only, top 3 added each fold):")
for k_ in (1, 3, 5):
    out = np.zeros(n); picked = {}
    for s in sorted(set(seas)):
        tr = seas != s; pin = np.zeros(n)
        for s2 in sorted(set(seas[tr])):
            a, bb = tr & (seas != s2), seas == s2; pin[bb] = 1 / (1 + np.exp(-ridge(X28[a], y[a], W[a])(X28[bb])))
        rs, lw = screen(pin, tr); sel = []
        for _, nm, z in rs:
            v = CAND[nm]
            if abs(np.corrcoef(v[tr], rg[tr])[0, 1]) >= .6 or any(abs(np.corrcoef(v[tr], CAND[o][tr])[0, 1]) >= .7 for o in sel): continue
            sel.append(nm)
            if len(sel) == k_: break
        for c in sel: picked[c] = picked.get(c, 0) + 1
        X = np.column_stack([X28] + [CAND[c] for c in sel]); out[seas == s] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[seas == s])))
    print(f"   top {k_}: held out {int(((out >= .4) == (y == 1)).sum())}/511 (locked {b0[0]}) | AUC {auc(out, y):.3f} | picked most often: {sorted(picked.items(), key=lambda x: -x[1])[:6]}")
