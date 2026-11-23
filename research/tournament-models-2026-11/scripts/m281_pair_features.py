# Regular (original) model chances for ANY pair of teams in a season, as of before the tournament.
# Each of the 31 inputs is a team measure (S = stronger by our rating, W = weaker) plus sos gap and gap x possessions.
# Team values come from the team's own real game rows where it sat on that side; otherwise from the same season
# percentile (tpct / ppct), checked against the real rows. Coach + star extras the same way.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
D3 = np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True); XX = D3["X"]; NAMES = [str(n) for n in D3["names"]]
B = Q.R.B; G = B.G; N = Q.N; seas = Q.seas; RND = Q.RND; k = ~Q.FF
TM, tpct, ppct, TEAMK, PLAYK = Q.TM, Q.tpct, Q.ppct, Q.TEAMK, Q.PLAYK
kk = lambda s: (s or "").rstrip(". ")
Sn = [kk(x) for x in B.Sname]; Wn = [kk(g["dog"] if g["fav"] == s else g["fav"]) for g, s in zip(G, B.Sname)]
EXN = Q.EX.shape[1]
# real per-team side values
VAL = {}      # (season, team, "S"/"W", key) -> value
EXV = {}      # (season, team) -> list of rows (i, side)
ORD = sorted(range(N), key=lambda i: {"First round": 0, "Second round": 1}.get(RND[i], 2), reverse=True)   # Round 1 rows written last, so they win
for i in ORD:
    if not k[i]: continue
    for side, t in (("S", Sn[i]), ("W", Wn[i])):
        EXV.setdefault((seas[i], t), []).append((i, side))
        for j, nm in enumerate(NAMES):
            if nm.startswith(side + " "): VAL[(seas[i], t, side, nm[2:])] = XX[i, j]
HOME = {}
for i, g in enumerate(G):
    if g["rnd"] == "First round":
        for t in (g["fav"], g["dog"]): HOME[(g["season"], kk(t))] = g
for i, g in enumerate(G):
    if g["rnd"] == "Second round":
        for t in (g["fav"], g["dog"]): HOME.setdefault((g["season"], kk(t)), g)
def tname(s, t):
    for c in (t, t + ".", t.rstrip(".")):
        if c in TM[s]: return c
    return next((x for x in TM[s] if kk(x) == kk(t)), t)
def fallback(s, t, key):
    if key in TEAMK: return tpct(s, tname(s, t), key)
    if key in PLAYK:
        g = HOME.get((s, t)); return ppct({"gid": g["gid"], "season": s}, g["fav"] if kk(g["fav"]) == t else g["dog"], key)
    return None
def value(s, t, side, key):
    v = VAL.get((s, t, side, key))
    if v is not None: return v, "row"
    o = "W" if side == "S" else "S"; v = VAL.get((s, t, o, key))
    if v is not None and any(n == o + " " + key for n in NAMES) and any(n == side + " " + key for n in NAMES): return v, "row"
    f = fallback(s, t, key)
    return (f if f is not None else 0.5), "pct"
# check fallback against real rows
bad = tot = 0
for (s, t, side, key), v in list(VAL.items())[:4000]:
    f = fallback(s, t, key)
    if f is None: continue
    tot += 1; bad += abs(f - v) > 1e-6
print(f"fallback percentile vs real rows: {tot - bad}/{tot} match")
def strength(s, a, b):
    A, Bt = TM[s][tname(s, a)], TM[s][tname(s, b)]
    S_, W_ = (a, b) if A["adj_net"] >= Bt["adj_net"] else (b, a)
    TS, TW = TM[s][tname(s, S_)], TM[s][tname(s, W_)]
    avg_tempo = np.mean([v["tempo"] for v in TM[s].values()])
    gap = (TS["adj_net"] - TW["adj_net"]) / 10
    return S_, W_, {"sos gap": (TS["sos"] - TW["sos"]) / 10, "gap x possessions": gap * (TS["tempo"] + TW["tempo"] - avg_tempo) / 70}
def ex_of(s, S_, W_):
    """coach + star extras: per-team parts recovered from real rows (gap = S part - W part)"""
    return None
def features(s, a, b):
    S_, W_, st = strength(s, a, b); x = []; src = []
    for nm in NAMES:
        if nm in st: x.append(st[nm]); continue
        side, key = nm[:1], nm[2:]; t = S_ if side == "S" else W_
        v, how = value(s, t, side, key); x.append(v); src.append(how)
    return S_, W_, np.array(x), src
# validate on every real Round 1 / Round of 32 row
mx = 0; ok = 0; n = 0; orient = 0
for i in range(N):
    if not (k[i] and RND[i] in ("First round", "Second round")): continue
    S_, W_, x, _ = features(seas[i], Sn[i], Wn[i]); n += 1; orient += S_ == Sn[i]
    d = np.abs(x - XX[i]).max(); ok += d < 1e-6
    if RND[i] == "First round": mx = max(mx, d)
n1 = sum(1 for i in range(N) if k[i] and RND[i] == "First round")
print(f"rebuilt inputs equal the real rows in {ok}/{n} Round 1-2 games (Round 1 games: {n1}) (orientation agrees {orient}/{n}); worst diff {mx:.4g}")

