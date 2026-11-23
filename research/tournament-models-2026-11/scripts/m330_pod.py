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
VARS = {}
for h1 in ("avg3", "model"):
    for h2 in ("avg3", "model", "upset+model", "model+sim"):
        VARS[f"pod: R1 chance {h1}, R32 chance {h2}"] = (h1, h2)
R1B, R32B = {}, {}
for r1lab in ("vote (current)", R1):
    tag = "vote" if r1lab.startswith("vote") else "60%"
    R1B[f"{tag} | vote (current)"] = PICKS[r1lab]
    R32B[f"{tag} | vote (current)"] = {s: [vote([up_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), model_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), sim_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1])]) for q in range(16)] for s in SEASONS}
    for lab, (h1, h2) in VARS.items():
        R1B[f"{tag} | {lab}"] = {}; R32B[f"{tag} | {lab}"] = {}
        for s in SEASONS:
            r1n = []; r2n = []
            for q in range(16):
                a, w = pod(s, q, PICKS[r1lab][s], h1, h2); r1n += a; r2n.append(w)
            R1B[f"{tag} | {lab}"][s] = r1n; R32B[f"{tag} | {lab}"][s] = r2n
keep = dict(R1B=R1B, R32B=R32B)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
R1B, R32B = keep["R1B"], keep["R32B"]; late = chooser_w(0)
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + k_] for r in order for k_ in range(4)]
BY = {}
print(f"{'Round 1 rule | Round of 32 method':72} | R1 | R32 | R1-2 pts | S16 | E8 | F4 | T | total | better/worse yrs")
for lab in R1B:
    cs = np.zeros(6, int); tot = []
    for s in SEASONS:
        g = BI[s]["games"]; w = WON[s]
        c1 = sum(p_ == x["won"] for p_, x in zip(R1B[lab][s], g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in R32B[lab][s])
        c, pts = score_late(s, fill(s, tree16(s, R32B[lab][s]), late)); cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
    BY[lab] = tot; base = BY[lab.split(" | ")[0] + " | vote (current)"]
    print(f"{lab:72} | {cs[0]} | {cs[1]} | {cs[0] + 2 * cs[1]:4} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {sum(tot):5} | {sum(a > b for a, b in zip(tot, base))}/{sum(a < b for a, b in zip(tot, base))}")
for tag in ("vote", "60%"):
    ks = [k_ for k_ in BY if k_.startswith(tag + " |")]; t2 = 0; ch = []
    for i in range(16):
        b = max(ks, key=lambda k_: sum(BY[k_][j] for j in range(16) if j != i)); t2 += BY[b][i]; ch.append(b)
    print(f"Round 1 = {tag}: method chosen on the other 15 years each time = {t2} (current {sum(BY[tag + ' | vote (current)'])}); chosen {sorted(set(ch))}")
json.dump(BY, open(os.path.join(HERE, "m330_out.json"), "w"))
