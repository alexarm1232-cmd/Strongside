# Pick each pod (4 teams) as a unit: pod-win chance = P(win R1) x sum over possible opponents P(opp wins R1) x P(beat opp).
# Round of 32 pick = most likely pod winner; it wins its Round 1 game; the pod's other Round 1 game uses the Round 1 rule.
# Scored on Rounds 1-2 and the full bracket (later rounds as now).
import os, json, contextlib, io, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
UPP.update(json.load(open(os.path.join(HERE, "m328_upset_p.json")))); MZ.update(pickle.load(open(os.path.join(HERE, "m328_mz.pkl"), "rb")))
for s, v in json.load(open(os.path.join(HERE, "m328_sim.json"))).items(): SR[s].update(v)
def p2(s, a, b, how):
    """chance a beats b in the Round of 32"""
    h, l, pu = UPP.get(f"{s}|{a}|{b}") or (lambda r: (r[0], r[1], r[2]))(UPP[f"{s}|{b}|{a}"]); pa_u = pu if a == l else 1 - pu
    key = (s, a, b) if (s, a, b) in MZ else (s, b, a); S_, W_, z = MZ[key]; pS = float(sig(z)); pa_m = pS if kk(a) == S_ else 1 - pS
    q = SR[s].get(f"{a}|{b}"); pa_s = q if q is not None else 1 - SR[s][f"{b}|{a}"]
    return {"avg3": (pa_u + pa_m + pa_s) / 3, "model": pa_m, "upset+model": (pa_u + pa_m) / 2, "model+sim": (pa_m + pa_s) / 2, "upset": pa_u}[how]
def p1(s, g, how):
    """chance each team wins its Round 1 game -> dict"""
    if g["H"] == g["L"]: return {g["H"]: 1.0}
    u, m, si = R1P[str(g["gid"])]; pl = {"avg3": (u + m + si) / 3, "model": m, "upset+model": (u + m) / 2, "model+sim": (m + si) / 2, "upset": u}[how]
    return {g["L"]: pl, g["H"]: 1 - pl}
def pod(s, q, r1rule_picks, h1, h2):
    g = BI[s]["games"]; A, Bm = p1(s, g[2 * q], h1), p1(s, g[2 * q + 1], h1)
    win = {}
    for t, pt in A.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in Bm.items())
    for t, pt in Bm.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in A.items())
    w = max(win, key=win.get)
    r1 = list(r1rule_picks[2 * q:2 * q + 2])
    if w in A: r1[0] = w
    else: r1[1] = w
    return r1, w
R1 = "upset unless both others >= 60% sure"
def pod_dist(s, q, h1="model", h2="model"):
    g = BI[s]["games"]; A, Bm = p1(s, g[2 * q], h1), p1(s, g[2 * q + 1], h1); win = {}
    for t, pt in A.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in Bm.items())
    for t, pt in Bm.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in A.items())
    return win, set(A)
def picks_with(s, q, r1rule, w):
    _, Aset = pod_dist(s, q); r1 = list(r1rule[2 * q:2 * q + 2])
    if w in Aset: r1[0] = w
    else: r1[1] = w
    return r1
DIST = {(s, q): pod_dist(s, q)[0] for s in SEASONS for q in range(16)}
BASE = {}
for r1lab in ("vote (current)", R1):
    tag = "vote" if r1lab.startswith("vote") else "60%"
    BASE[tag] = {"r1": PICKS[r1lab], "vote32": {s: [vote([up_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), model_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), sim_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1])]) for q in range(16)] for s in SEASONS},
                 "pods": {s: {q: {t: picks_with(s, q, PICKS[r1lab][s], t) for t in DIST[(s, q)]} for q in range(16)} for s in SEASONS}}
keep = dict(DIST=DIST, BASE=BASE)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
DIST, BASE = keep["DIST"], keep["BASE"]; late = chooser_w(0)
predict([(s, a, b) for s in SEASONS for k_ in range(8) for a in DIST[(s, 2 * k_)] for b in DIST[(s, 2 * k_ + 1)]])
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + j] for r in order for j in range(4)]
def bracket(tag, s, mode):
    """mode: vote | pod32 | pod16 -> (r1 picks, r32 winners, forced s16 winners or None)"""
    B0 = BASE[tag]
    if mode == "vote": return B0["r1"][s], B0["vote32"][s], None
    r1 = []; r2 = []; s16 = []
    for k_ in range(8):
        qa, qb = 2 * k_, 2 * k_ + 1; Da, Db = DIST[(s, qa)], DIST[(s, qb)]
        if mode == "pod16":
            reach = {t: Da[t] * sum(Db[o] * pm(s, t, o) for o in Db) for t in Da}
            reach.update({t: Db[t] * sum(Da[o] * pm(s, t, o) for o in Da) for t in Db})
            w = max(reach, key=reach.get); wa = w if w in Da else max(Da, key=Da.get); wb = w if w in Db else max(Db, key=Db.get); s16.append(w)
        else:
            wa, wb = max(Da, key=Da.get), max(Db, key=Db.get)
        r1 += B0["pods"][s][qa][wa] + B0["pods"][s][qb][wb]; r2 += [wa, wb]
    return r1, r2, (s16 if mode == "pod16" else None)
print(f"{'Round 1 rule | method':40} | R1 | R32 | S16 | E8 | F4 | T | R1-2 pts | total | better/worse yrs vs vote")
BY = {}
for tag in ("vote", "60%"):
    for mode in ("vote", "pod32", "pod16"):
        cs = np.zeros(6, int); tot = []
        for s in SEASONS:
            g = BI[s]["games"]; w = WON[s]; r1, r2, s16 = bracket(tag, s, mode)
            ch = late if s16 is None else (lambda S16: (lambda s_, a, b, r: (a if a in S16 else b) if r == 3 else late(s_, a, b, r)))(set(s16))
            c1 = sum(p_ == x["won"] for p_, x in zip(r1, g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in r2)
            c, pts = score_late(s, fill(s, tree16(s, r2), ch)); cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
        BY[(tag, mode)] = tot; base = BY[(tag, "vote")]
        print(f"{tag + ' | ' + mode:40} | {cs[0]} | {cs[1]} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {cs[0] + 2 * cs[1]:4} | {sum(tot):5} | {sum(a > b for a, b in zip(tot, base))}/{sum(a < b for a, b in zip(tot, base))}")
