# More Sweet 16 -> title tests: champion-first, forward-chosen sharpness / model-net mix, title by simulator on top of expected points.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m308_late.py"), encoding="utf-8-sig").read(); src = src[:src.index("res = {}")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
logit = lambda q: np.log(q / (1 - q))
def sharp(pf, t):
    return lambda s, a, b: 1 / (1 + np.exp(-t * logit(pf(s, a, b))))
def real_r1(s):  # tree-order R1 games with real winners
    g = BI[s]["games"]; _, order = field(s); return [g[r * 8 + j] for r in order for j in range(8)]
def tree_r12(s, o):
    _, order = field(s); r1 = [e["pick"] for e in o["rounds"][0]]; r2 = [e["pick"] for e in o["rounds"][1]]
    return [r1[r * 8 + j] for r in order for j in range(8)], [r2[r * 4 + k] for r in order for k in range(4)]
def score_all(s, rounds):
    w = WON[s]; g = real_r1(s)
    c = [sum(pk == x["won"] for pk, x in zip(rounds[0], g) if x["H"] != x["L"])] + [sum(w.get(t, 0) >= r for t in rounds[r - 1]) for r in range(2, 7)]
    return c, sum(ci * pt for ci, pt in zip(c, PTS))
def champion_first(s, o, pf, late="h2h"):
    """user's way: champion = best title chance; other three Final Four teams = best chance to win their region; force their paths;
    keep the vote's Rounds 1-2 elsewhere; Sweet 16 / Elite 8 rest by model"""
    A = adv(s, pf); slots, _ = field(s); r1, r2 = tree_r12(s, o)
    ch = max(A, key=lambda t: A[t][6]); reg = [slots[i * 16:(i + 1) * 16] for i in range(4)]
    forced = {}
    for R_ in reg:
        tm = [t for t in R_ if t]; f = ch if ch in tm else max(tm, key=lambda t: A[t][4]); forced[f] = 4
    forced[ch] = 6
    half = [t for t in forced if t != ch and (slots.index(t) < 32) == (slots.index(ch) < 32)]
    other = [t for t in forced if t != ch and t not in half]; fin = max(other, key=lambda t: A[t][5]); forced[fin] = 5
    def must(t, r): return forced.get(t, 0) >= r
    r1n = []
    for i in range(32):
        a, b = slots[2 * i], slots[2 * i + 1]
        r1n.append(a if (b is None or must(a, 1)) else b if must(b, 1) else r1[i])
    r2n = []
    for i in range(16):
        a, b = r1n[2 * i], r1n[2 * i + 1]
        r2n.append(a if must(a, 2) else b if must(b, 2) else (r2[i] if r2[i] in (a, b) else (a if pf(s, a, b) >= .5 else b)))
    def chooser(s_, a, b, r):
        if must(a, r): return a
        if must(b, r): return b
        return a if pf(s_, a, b) >= .5 else b
    return [r1n, r2n] + fill(s, r2n, chooser)
def full_ep(s, pf):
    """expected-points bracket for all six rounds (chance from the late-round line throughout)"""
    A = adv(s, pf); slots, _ = field(s)
    def best(lo, hi, r):
        if r == 0: return {slots[lo]: 0.0} if slots[lo] else {}
        m = (lo + hi) // 2; L, R_ = best(lo, m, r - 1), best(m, hi, r - 1)
        if not R_: return {t: v + PTS[r - 1] * A[t][r] for t, v in L.items()}
        bl, br = max(L.values()), max(R_.values()); d = {}
        for t, v in L.items(): d[t] = v + br + PTS[r - 1] * A[t][r]
        for t, v in R_.items(): d[t] = v + bl + PTS[r - 1] * A[t][r]
        return d
    out = {r: [] for r in range(1, 7)}
    def trace(lo, hi, r, t):
        if r == 0: return
        out[r].append((lo, t)); m = (lo + hi) // 2; L, R_ = best(lo, m, r - 1), best(m, hi, r - 1)
        if t in L: trace(lo, m, r - 1, t); (trace(m, hi, r - 1, max(R_, key=R_.get)) if R_ else None)
        else: trace(lo, m, r - 1, max(L, key=L.get)); trace(m, hi, r - 1, t)
    D = best(0, 64, 6); trace(0, 64, 6, max(D, key=D.get))
    return [[t for _, t in sorted(out[r])] for r in range(1, 7)]

yrs = [int(s[:4]) + 1 for s in SEASONS]
def show(name, tot):
    print(f"{name:44} | {sum(tot):5} | {sum(t >= 100 for t in tot):3} | " + " ".join(f"{t:3}" for t in tot))
for key in ("vote", "blend"):
    base = {o["season"]: o for o in FULL[key]}
    early = {s: base[s]["score"][0] + 2 * base[s]["score"][1] for s in SEASONS}
    print(f"\n===== Rounds 1-2 = {key}\n{'method':44} | total | >=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
    show("Current", [base[s]["points"] for s in SEASONS])
    ep = lambda s, pf: early[s] + score_late(s, ep_fill(s, r2_tree(s, base[s]), adv(s, pf)))[1]
    show("Expected points, model", [ep(s, pm) for s in SEASONS])
    # sharpness / mix chosen each year from the other years (forward-fair)
    TS = [.5, .75, 1, 1.5, 2, 3]; WS = [0, .25, .5, .75, 1]
    grid_t = {t: {s: ep(s, sharp(pm, t)) for s in SEASONS} for t in TS}
    grid_w = {w: {s: ep(s, mixp((w, pm), (1 - w, pnet))) for s in SEASONS} for w in WS}
    for t in TS: show(f"  EP model, sharpness {t} (all years, in-sample)", [grid_t[t][s] for s in SEASONS])
    show("EP model, sharpness picked on other years", [grid_t[max(TS, key=lambda t: sum(v for y, v in grid_t[t].items() if y != s))][s] for s in SEASONS])
    for w in WS: show(f"  EP {w:.2f} model + {1 - w:.2f} net (in-sample)", [grid_w[w][s] for s in SEASONS])
    show("EP model/net mix picked on other years", [grid_w[max(WS, key=lambda w: sum(v for y, v in grid_w[w].items() if y != s))][s] for s in SEASONS])
    show("Champion-first (yours), model", [score_all(s, champion_first(s, base[s], pm))[1] for s in SEASONS])
    show("Champion-first, model+net 50/50", [score_all(s, champion_first(s, base[s], mixp((.5, pm), (.5, pnet))))[1] for s in SEASONS])
    show("Champion-first, net rating", [score_all(s, champion_first(s, base[s], pnet))[1] for s in SEASONS])
print("\n(no vote) Full expected-points bracket, all 6 rounds:")
show("Full EP, model", [score_all(s, full_ep(s, pm))[1] for s in SEASONS])
show("Full EP, model+net", [score_all(s, full_ep(s, mixp((.5, pm), (.5, pnet))))[1] for s in SEASONS])
# champions picked
print("\nchampions picked (EP model / champion-first model) vs real:")
for s in SEASONS:
    o = {x["season"]: x for x in FULL["vote"]}[s]; rd = ep_fill(s, r2_tree(s, o), adv(s, pm)); A = adv(s, pm)
    top = max(A, key=lambda t: A[t][6]); real = next(t for t in WON[s] if WON[s][t] >= 6)
    print(int(s[:4]) + 1, rd[3][0], "|", top, f"{A[top][6]:.2f}", "| real:", real, f"{A.get(real, [0]*7)[6]:.2f}", "| current:", o["rounds"][5][0]["pick"])
