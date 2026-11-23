import os, json, contextlib, io
from collections import Counter
src = open("m322_r32_override.py", encoding="utf-8-sig").read(); src = src[:src.index("RULES = {")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
for r1lab in ("vote (current)", "upset unless both others >= 60% sure"):
    cnt = Counter(); lone = Counter(); lone_up = Counter(); dead = 0; real = 0; tot = 0; agree_wrong = 0
    conf2 = []
    for s in SEASONS:
        pk = PICKS[r1lab][s]; w = WON[s]
        for q in range(16):
            a, b = pk[2*q], pk[2*q+1]; tot += 1
            alive = [t for t in (a, b) if w.get(t, 0) >= 1]
            if not any(w.get(t, 0) >= 2 for t in (a, b)): dead += 1; continue   # neither team won the pod
            real += 1
            P = {"R32 upset model": up_pick(s,a,b), "regular model": model_pick(s,a,b), "simulator": sim_pick(s,a,b)}
            ok = {k: w.get(v,0) >= 2 for k, v in P.items()}; c = sum(ok.values()); cnt[c] += 1
            if c == 1:
                k = next(k for k in ok if ok[k]); lone[k] += 1
                h, l, pu = UPP[f"{s}|{a}|{b}"]; lone_up[k] += P[k] == l
            if c == 2:
                k = next(k for k in ok if not ok[k]); conf2.append(k)
    print(f"\n== Round 1 = {r1lab}: {tot} Round of 32 games in the bracket")
    print(f"   neither of our two teams won the pod (game can't be right): {dead}")
    print(f"   winnable games: {real} -> right by 0 of 3: {cnt[0]} | 1 of 3: {cnt[1]} | 2 of 3: {cnt[2]} | 3 of 3: {cnt[3]}")
    print(f"   lone right picker (1 of 3): {dict(lone)}  (of those, picked the lower seed: {dict(lone_up)})")
    print(f"   the one wrong picker when 2 of 3 right: {dict(Counter(conf2))}")
