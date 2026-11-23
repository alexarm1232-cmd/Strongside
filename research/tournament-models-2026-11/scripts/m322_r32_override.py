# Round of 32 like the Round 1 rule: R32 Upset Model's pick unless both others disagree and are each >= x sure.
# Round 1 = vote or the 60% override. Each bracket's own Round of 32 matchups. Then full bracket for the leaders.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
def probs(s, a, b):
    """chance a wins: R32 upset model, regular model, simulator"""
    h, l, pu = UPP[f"{s}|{a}|{b}"]; pa_u = pu if a == l else 1 - pu
    S_, W_, z = MZ[(s, a, b)]; pS = float(sig(z)); pa_m = pS if kk(a) == S_ else 1 - pS
    q = SR[s].get(f"{a}|{b}"); pa_s = q if q is not None else 1 - SR[s][f"{b}|{a}"]
    return pa_u, pa_m, pa_s, h, l
def r32_rule(kind, x=None, w=None, c=None):
    def f(s, a, b):
        pu, pm, ps, h, l = probs(s, a, b)
        up = up_pick(s, a, b); mo = model_pick(s, a, b); si = sim_pick(s, a, b)
        if kind == "vote": return vote([up, mo, si])
        if kind == "upset": return up
        if kind == "over":
            conf = lambda p, t: p if t == a else 1 - p
            if mo == si != up and min(conf(pm, mo), conf(ps, si)) >= x: return mo
            return up
        if kind == "blend":
            pl = lambda p: p if l == a else 1 - p       # chance the lower seed wins
            v = w * pl(pu) + (1 - w) / 2 * (pl(pm) + pl(ps)); return l if v >= c else h
    return f
RULES = {"vote (current)": r32_rule("vote"), "R32 upset model alone @45": r32_rule("upset")}
for x in (.55, .6, .65, .7, .75): RULES[f"upset unless both others >= {int(x * 100)}%"] = r32_rule("over", x)
for w in (.5, .6):
    for c in (.42, .45): RULES[f"blend {w} upset + rest @{int(c * 100)}"] = r32_rule("blend", w=w, c=c)
yrs = [int(s[:4]) + 1 for s in SEASONS]; BY = {}
for r1lab in ("vote (current)", "upset unless both others >= 60% sure"):
    print(f"\n===== Round 1 = {r1lab}\n{'Round of 32 rule':34} | R1 | R32 | points | better/worse years vs vote")
    for lab, f in RULES.items():
        r1 = r2 = 0; yr = []
        for s in SEASONS:
            g = BI[s]["games"]; pk = PICKS[r1lab][s]; a1 = sum(p == x["won"] for p, x in zip(pk, g) if x["H"] != x["L"])
            a2 = sum(WON[s].get(f(s, pk[2 * q], pk[2 * q + 1]), 0) >= 2 for q in range(16)); r1 += a1; r2 += a2; yr.append(a1 + 2 * a2)
        BY[(r1lab, lab)] = yr; base = BY[(r1lab, "vote (current)")]
        print(f"{lab:34} | {r1} | {r2:3} | {r1 + 2 * r2:4} | {sum(a > b for a, b in zip(yr, base))}/{sum(a < b for a, b in zip(yr, base))}")
    keys = list(RULES); tot = 0; ch = []
    for i in range(16):
        b = max(keys, key=lambda k_: sum(BY[(r1lab, k_)][j] for j in range(16) if j != i)); tot += BY[(r1lab, b)][i]; ch.append(b)
    print(f"  rule chosen on the other 15 years each time: {tot} points, chosen: {sorted(set(ch))}")
json.dump({f"{a}||{b}": v for (a, b), v in BY.items()}, open(os.path.join(HERE, "m322_out.json"), "w"))
