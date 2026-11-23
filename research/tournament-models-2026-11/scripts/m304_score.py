src = open("m302_full_brackets.py", encoding="utf-8").read(); src = src[:src.index('print(f"{\'Full bracket')]
import contextlib, io, json
with contextlib.redirect_stdout(io.StringIO()): exec(src)
SF = json.load(open(os.path.join(HERE, "m304_sim_ff.json")))
LAB = {"Vote of the 3 -> regular": "vote", "Regular model all the way": "reg", "Blend -> regular": "blend"}
print(f"{'Full bracket (S16/E8 regular, F4/title simulator)':52} | R64 | R32 | S16 | E8 | F4 | Title | points")
YR = {}
for lab, short in LAB.items():
    key, src_ = BRK[lab]; tot = [0] * 6; yr = []; champs = []
    for s in SEASONS:
        r1, r2 = r12(s, key, src_)
        s16 = [model_pick(s, r2[2*i], r2[2*i+1]) for i in range(8)]; e8 = [model_pick(s, s16[2*i], s16[2*i+1]) for i in range(4)]
        f4 = SF[s][short]["f4w"]; ch = [SF[s][short]["champ"]]
        assert all(t in e8 for t in f4)
        w = WON[s]; y = 0
        for ri, picks in enumerate([r1, r2, s16, e8, f4, ch]):
            c = sum(pk == g["won"] for pk, g in zip(picks, BI[s]["games"]) if g["H"] != g["L"]) if ri == 0 else sum(w.get(pk, 0) >= ri + 1 for pk in picks)
            tot[ri] += c; y += c * PTS[ri]
        yr.append(y); champs.append((int(s[:4]) + 1, ch[0], w.get(ch[0], 0) >= 6))
    YR[lab] = yr; print(f"{lab:52} | {tot[0]:3} | {tot[1]:3} | {tot[2]:3} | {tot[3]:2} | {tot[4]:2} | {tot[5]:5} | {sum(c * p for c, p in zip(tot, PTS))}")
    if short == "vote": print("   vote champions:", champs)
print("year | " + " | ".join(LAB.values()))
for i, s in enumerate(SEASONS): print(int(s[:4]) + 1, "|", " | ".join(f"{YR[k][i]:4}" for k in YR))
