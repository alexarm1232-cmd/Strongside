# Round of 32 % thresholds, scored on the FULL bracket (Round 1 = 60% rule; later rounds as now).
#  A: R32 upset model alone, upset at c        B: upset model's pick unless both others disagree, each >= x sure
#  C: vote, unless the upset model is >= y sure of its pick (then its pick)   D: regular model + simulator average, unless upset model >= y sure
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
def probs(s, a, b):
    h, l, pu = UPP[f"{s}|{a}|{b}"]; pa_u = pu if a == l else 1 - pu
    S_, W_, z = MZ[(s, a, b)]; pS = float(sig(z)); pa_m = pS if kk(a) == S_ else 1 - pS
    q = SR[s].get(f"{a}|{b}"); pa_s = q if q is not None else 1 - SR[s][f"{b}|{a}"]
    return pa_u, pa_m, pa_s, h, l
conf = lambda p, t, a: p if t == a else 1 - p
def rule(kind, x):
    def f(s, a, b):
        pu, pm, ps, h, l = probs(s, a, b); up = up_pick(s, a, b); mo = model_pick(s, a, b); si = sim_pick(s, a, b)
        if kind == "vote": return vote([up, mo, si])
        if kind == "A": return l if conf(pu, l, a) >= x else h
        if kind == "B": return mo if (mo == si != up and min(conf(pm, mo, a), conf(ps, si, a)) >= x) else up
        if kind == "C": return up if conf(pu, up, a) >= x else vote([up, mo, si])
        if kind == "D":
            if conf(pu, up, a) >= x: return up
            v = (pm + ps) / 2; return a if v > .5 else b if v < .5 else chalk2(s, a, b)
        if kind == "M": return mo
        if kind == "S": return si
    return f
R1 = "upset unless both others >= 60% sure"; RULES = {"vote (current)": rule("vote", 0), "regular model alone": rule("M", 0), "simulator alone": rule("S", 0)}
for c in (.45, .5, .55, .6, .65, .7): RULES[f"A upset model alone, upset at {int(c * 100)}%"] = rule("A", c)
for x in (.55, .6, .65, .7, .75, .8): RULES[f"B upset unless both others >= {int(x * 100)}%"] = rule("B", x)
for y in (.6, .65, .7, .75, .8, .85): RULES[f"C vote unless upset model >= {int(y * 100)}%"] = rule("C", y)
for y in (.6, .7, .8, 1.01): RULES[f"D model+sim avg unless upset >= {int(y * 100)}%" if y < 1 else "D model+sim average alone"] = rule("D", y)
R32W = {lab: {s: [f(s, PICKS[R1][s][2 * q], PICKS[R1][s][2 * q + 1]) for q in range(16)] for s in SEASONS} for lab, f in RULES.items()}
keep = dict(PICKS=PICKS[R1], R32W=R32W)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
P1, R32W = keep["PICKS"], keep["R32W"]
late = chooser_w(0)
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + k_] for r in order for k_ in range(4)]
BY = {}; F4need = set()
print(f"{'Round of 32 rule (Round 1 = 60% rule)':44} | R32 | S16 | E8 | F4 | T | R1-2 pts | total | better/worse yrs vs vote")
for lab in RULES:
    cs = np.zeros(6, int); tot = []
    for s in SEASONS:
        g = BI[s]["games"]; pk = P1[s]; w = WON[s]
        c1 = sum(p_ == x["won"] for p_, x in zip(pk, g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in R32W[lab][s])
        n0 = len(need); rd = fill(s, tree16(s, R32W[lab][s]), late); c, pts = score_late(s, rd)
        for e in rd[2:]:
            pass
        cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
    BY[lab] = tot; base = BY["vote (current)"]
    print(f"{lab:44} | {cs[1]:3} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {cs[0] + 2 * cs[1]:4} | {sum(tot):5} | {sum(a > b for a, b in zip(tot, base))}/{sum(a < b for a, b in zip(tot, base))}")
keys = list(RULES); tot = 0; ch = []
for i in range(16):
    b = max(keys, key=lambda k_: sum(BY[k_][j] for j in range(16) if j != i)); tot += BY[b][i]; ch.append(b)
print(f"\nrule chosen on the other 15 years each time: {tot} (vote {sum(BY['vote (current)'])}); chosen: {sorted(set(ch))}")
for fam in "ABCD":
    ks = ["vote (current)"] + [k_ for k_ in keys if k_.startswith(fam + " ")]; t2 = 0; c2 = []
    for i in range(16):
        b = max(ks, key=lambda k_: sum(BY[k_][j] for j in range(16) if j != i)); t2 += BY[b][i]; c2.append(b)
    print(f"  family {fam} (or vote), chosen on other years: {t2}; chosen: {sorted(set(c2))}")
json.dump(BY, open(os.path.join(HERE, "m327_out.json"), "w"))
