# Full bracket with Round 1 = "upset unless both others >= 60% sure", Round of 32 = vote; later rounds as now
# (regular model Sweet 16 / Elite 8, 70% simulator + 30% model Final Four / title; model where no simulator run exists).
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
R32W = {}
for lab in ("vote (current)", "upset unless both others >= 60% sure", "upset unless both others >= 65% sure"):
    R32W[lab] = {}
    for s in SEASONS:
        pk = PICKS[lab][s]; R32W[lab][s] = [vote([up_pick(s, pk[2 * q], pk[2 * q + 1]), model_pick(s, pk[2 * q], pk[2 * q + 1]), sim_pick(s, pk[2 * q], pk[2 * q + 1])]) for q in range(16)]
keep = dict(PICKS=PICKS, R32W=R32W, WON1=WON)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
PICKS, R32W = keep["PICKS"], keep["R32W"]
late = chooser_w(0)
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + k_] for r in order for k_ in range(4)]
yrs = [int(s[:4]) + 1 for s in SEASONS]
print(f"{'Round 1 rule':38} | R1 | R32 | S16 | E8 | F4 | T | total | >=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
for lab in R32W:
    cs = np.zeros(6, int); tot = []
    for s in SEASONS:
        g = BI[s]["games"]; pk = PICKS[lab][s]; w = WON[s]
        c1 = sum(p == x["won"] for p, x in zip(pk, g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in R32W[lab][s])
        rd = fill(s, tree16(s, R32W[lab][s]), late); c, pts = score_late(s, rd)
        cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
    print(f"{lab:38} | {cs[0]} | {cs[1]} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {sum(tot):5} | {sum(t >= 100 for t in tot):5} | " + " ".join(f"{t:3}" for t in tot))
print("Final Four / title pairs without a simulator run (model used):", len(need))
miss = {}
for s, a, b in sorted(need):
    if (s, b, a) in need and b < a: continue
    miss.setdefault(s, []).append([a, b])
json.dump(miss, open(os.path.join(HERE, "m321_need.json"), "w")); print(json.dumps(miss))
