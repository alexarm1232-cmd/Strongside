import os, json, contextlib, io
src = open("m322_r32_override.py", encoding="utf-8-sig").read(); src = src[:src.index("RULES = {")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
for r1lab in ("vote (current)", "upset unless both others >= 60% sure"):
    T = {"real matchup (both our teams won Round 1)": [0,0,0], "one of our teams lost in Round 1": [0,0,0]}
    for s in SEASONS:
        pk = PICKS[r1lab][s]; w = WON[s]
        for q in range(16):
            a, b = pk[2*q], pk[2*q+1]
            if not any(w.get(t,0) >= 2 for t in (a,b)): continue
            key = list(T)[0] if all(w.get(t,0) >= 1 for t in (a,b)) else list(T)[1]
            u = up_pick(s,a,b); v = vote([u, model_pick(s,a,b), sim_pick(s,a,b)])
            T[key][0] += 1; T[key][1] += w.get(u,0) >= 2; T[key][2] += w.get(v,0) >= 2
    print(r1lab); [print(f"   {k}: {n} games | upset model {a} | vote {b}") for k,(n,a,b) in T.items()]
