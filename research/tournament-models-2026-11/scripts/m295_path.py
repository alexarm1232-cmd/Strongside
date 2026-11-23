# Path-aware brackets, no cutoffs, nothing fit to results: for each 4-team pod choose the Round of 32 pick that maximizes
# expected points = P(R1 picks right) + R32_WEIGHT * P(R32 pick reaches the Sweet 16); Round 1 picks follow that path, the
# other Round 1 game goes to its favorite. Probabilities are the held-out model chances. Options fixed up front:
#   A regular model in both rounds | B upset models in both rounds | C even mix (R1: thirds of upset/regular/sim; R32: half upset, half regular)
# R32_WEIGHT 2 (the scoring) and 4 (Round of 32 counts double what the scoring says).
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m294_recency.py"), encoding="utf-8-sig").read(); src = src[:src.index("W1 = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
def p_r1(s, g, opt):
    """chance each team wins its Round 1 game -> dict"""
    if g["H"] == g["L"]: return {g["H"]: 1.0}
    u, m, si = R1P[str(g["gid"])]
    pl = {"A": m, "B": u, "C": (u + m + si) / 3}[opt]; return {g["L"]: pl, g["H"]: 1 - pl}
def q(s, a, b, opt):
    """chance a beats b in the Round of 32"""
    key = (a, b) if f"{s}|{a}|{b}" in UPP else (b, a)
    h, l, pu = UPP[f"{s}|{key[0]}|{key[1]}"]; S_, W_, z = MZ[(s, key[0], key[1])]; pS = 1 / (1 + np.exp(-z)); pm = pS if kk(l) == S_ else 1 - pS
    pl = {"A": pm, "B": pu, "C": (pu + pm) / 2}[opt]; pa = pl if a == l else 1 - pl
    return pa
def run(opt, w2):
    r1 = r2 = ups = 0; yr = []
    for s in SEASONS:
        g = BI[s]["games"]; wins = BI[s]["wins"]; y1 = y2 = 0
        for qd in range(16):
            G1, G2 = g[2 * qd], g[2 * qd + 1]; P1_, P2_ = p_r1(s, G1, opt), p_r1(s, G2, opt)
            best = None
            for side, (Pm, Po) in ((0, (P1_, P2_)), (1, (P2_, P1_))):
                for t in Pm:
                    reach = Pm[t] * sum(Po[o] * q(s, t, o, opt) for o in Po)
                    other = max(Po, key=Po.get); ev = Pm[t] + Po[other] + w2 * reach
                    if best is None or ev > best[0]: best = (ev, side, t, other)
            _, side, t, other = best
            picks = (t, other) if side == 0 else (other, t)
            for GG, pk in ((G1, picks[0]), (G2, picks[1])):
                if GG["H"] != GG["L"]: y1 += pk == GG["won"]; ups += pk == GG["L"]
            y2 += wins.get(t, 0) >= 2
        r1 += y1; r2 += y2; yr.append(y1 + 2 * y2)
    return r1, r2, r1 + 2 * r2, ups, yr
NAMES = {"A": "regular model", "B": "upset models", "C": "even mix of the models"}
print(f"{'chances from':26} R32 weight | R1 /511 | R32 /256 | points | R1 upset picks | 2015-2026 points")
YRS = [int(s[:4]) + 1 for s in SEASONS]
for opt in "ABC":
    for w2 in (2, 4):
        a, b, p, u, yr = run(opt, w2); f = sum(v for v, y in zip(yr, YRS) if y >= 2015)
        print(f"{NAMES[opt]:26} {w2:10} | {a:7} | {b:8} | {p:6} | {u:14} | {f}")
        if opt == "C" and w2 == 2: json.dump(yr, open(os.path.join(HERE, "m295_C2_years.json"), "w"))
print("reference: upset models 40/45 = 400 | 172 | 744 (2015-2026: 527); blend thirds -> 50/50 = 400 | 182 | 764 (528); vote = 395 | 178 | 751 (523)")
