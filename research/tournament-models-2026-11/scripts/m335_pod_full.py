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
P1S, P2S = {}, {}
R1B, R32B, R1P_SHOW, R32P_SHOW = {}, {}, {}, {}
for s in SEASONS:
    g = BI[s]["games"]; r1n = []; r2n = []; sh1 = []; sh2 = []
    for q in range(16):
        a, w = pod(s, q, PICKS[R1][s], "model", "model"); r1n += a; r2n.append(w)
    for j, x in enumerate(g):
        if x["H"] == x["L"]: sh1.append(None); continue
        d = p1(s, x, "avg3"); sh1.append(round(d[r1n[j]], 3))
    for q in range(16):
        a, b = r1n[2 * q], r1n[2 * q + 1]; w = r2n[q]; o = b if w == a else a; sh2.append(round(p2(s, w, o, "model"), 3))
    R1B[s], R32B[s], R1P_SHOW[s], R32P_SHOW[s] = r1n, r2n, sh1, sh2
keep = dict(R1B=R1B, R32B=R32B, R1P_SHOW=R1P_SHOW, R32P_SHOW=R32P_SHOW)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
globals().update(keep)
X2 = os.path.join(HERE, "m335_sim_extra.json")
if os.path.exists(X2):
    for s, v in json.load(open(X2)).items():
        for k_, q in v.items(): a, b = k_.split("|"); put(s, a, b, q)
miss = set(); OUT = []
for s in SEASONS:
    g = BI[s]["games"]; w = WON[s]; seeds = {}
    for x in g: seeds[x["H"]] = x["sH"]; seeds[x["L"]] = x["sL"]
    teams_of = lambda lo, hi: [t for x in g[lo:hi] for t in {x["H"], x["L"]}]
    real = lambda lo, hi, r: next((t for t in teams_of(lo, hi) if w.get(t, 0) >= r), None)
    R = []
    r1 = [{"a": x["H"], "b": x["L"], "pick": R1B[s][j], "p": R1P_SHOW[s][j], "real": x["won"], "bye": x["H"] == x["L"]} for j, x in enumerate(g)]
    for e in r1: e["right"] = e["pick"] == e["real"] or e["bye"]
    R.append(r1)
    r2 = [{"a": r1[2 * q]["pick"], "b": r1[2 * q + 1]["pick"], "pick": R32B[s][q], "p": R32P_SHOW[s][q], "real": real(4 * q, 4 * q + 4, 2), "right": w.get(R32B[s][q], 0) >= 2} for q in range(16)]
    R.append(r2); prev = r2
    predict([(s, prev[2 * i]["pick"], prev[2 * i + 1]["pick"]) for i in range(8)])
    for r, n in ((3, 8), (4, 4)):
        cur = []
        for i in range(n):
            a, b = prev[2 * i]["pick"], prev[2 * i + 1]["pick"]; predict([(s, a, b)]); pp = pm(s, a, b); pk = a if pp >= .5 else b; span = 32 // n
            cur.append({"a": a, "b": b, "pick": pk, "p": round(pp if pk == a else 1 - pp, 3), "real": real(i * span, (i + 1) * span, r), "right": w.get(pk, 0) >= r})
        R.append(cur); prev = cur
    e8 = [x["pick"] for x in prev]; f4 = []
    for ra, rb in FFPAIR[s]:
        a, b = e8[ra], e8[rb]; predict([(s, a, b)]); q = SIM.get((s, a, b))
        if q is None: miss.add((s, a, b)); q = pm(s, a, b)
        mix = .7 * q + .3 * pm(s, a, b); pk = a if mix >= .5 else b
        tm = teams_of(ra * 8, ra * 8 + 8) + teams_of(rb * 8, rb * 8 + 8)
        f4.append({"a": a, "b": b, "pick": pk, "p": round(mix if pk == a else 1 - mix, 3), "real": next((t for t in tm if w.get(t, 0) >= 5), None), "right": w.get(pk, 0) >= 5, "regions": [ra, rb]})
    R.append(f4); a, b = f4[0]["pick"], f4[1]["pick"]; predict([(s, a, b)]); q = SIM.get((s, a, b))
    if q is None: miss.add((s, a, b)); q = pm(s, a, b)
    mix = .7 * q + .3 * pm(s, a, b); pk = a if mix >= .5 else b
    R.append([{"a": a, "b": b, "pick": pk, "p": round(mix if pk == a else 1 - mix, 3), "real": next((t for t in w if w[t] >= 6), None), "right": w.get(pk, 0) >= 6}])
    score = [sum(e["right"] for e in R[0] if not e["bye"])] + [sum(e["right"] for e in R[k_]) for k_ in range(1, 6)]
    OUT.append({"season": s, "year": int(s[:4]) + 1, "seeds": seeds, "rounds": R, "score": score, "points": sum(c * pt for c, pt in zip(score, PTS))})
print("pod bracket:", sum(o["points"] for o in OUT), [sum(o["score"][i] for o in OUT) for i in range(6)], "champions", [(o["year"], o["rounds"][5][0]["pick"]) for o in OUT if o["rounds"][5][0]["right"]])
print("by year:", [o["points"] for o in OUT])
mm = {}
for s, a, b in sorted(miss): mm.setdefault(s, []).append([a, b])
print("missing simulator Final Four / title pairs:", json.dumps(mm))
ALL = {"pod": OUT, "vote": json.load(open(os.path.join(HERE, "m307_full.json")))["vote"]}
json.dump(ALL, open(os.path.join(HERE, "m335_full.json"), "w"), separators=(",", ":"))
