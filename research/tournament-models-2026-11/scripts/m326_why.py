# Full bracket with Round 1 = "upset unless both others >= 60% sure", Round of 32 = vote; later rounds as now
# (regular model Sweet 16 / Elite 8, 70% simulator + 30% model Final Four / title; model where no simulator run exists).
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
R32W = {}
for lab, r1 in (("vote / vote", "vote (current)"), ("60% rule / vote", "upset unless both others >= 60% sure"), ("60% rule / R32 upset alone", "upset unless both others >= 60% sure")):
    R32W[lab] = {}; PICKS[lab] = PICKS[r1]
    for s in SEASONS:
        pk = PICKS[r1][s]
        R32W[lab][s] = [up_pick(s, pk[2 * q], pk[2 * q + 1]) if "alone" in lab else vote([up_pick(s, pk[2 * q], pk[2 * q + 1]), model_pick(s, pk[2 * q], pk[2 * q + 1]), sim_pick(s, pk[2 * q], pk[2 * q + 1])]) for q in range(16)]
keep = dict(PICKS=PICKS, R32W=R32W, WON1=WON)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
PICKS, R32W = keep["PICKS"], keep["R32W"]
late = chooser_w(0)
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + k_] for r in order for k_ in range(4)]
A, Bk = "60% rule / vote", "60% rule / R32 upset alone"
diff = []; seeds = lambda s, t: seed(s, t)
for s in SEASONS:
    w = WON[s]; ra = fill(s, tree16(s, R32W[A][s]), late); rb = fill(s, tree16(s, R32W[Bk][s]), late)
    _, pa = score_late(s, ra); _, pb = score_late(s, rb)
    for x, y_ in zip(R32W[A][s], R32W[Bk][s]):
        if x != y_: diff.append((s, x, seeds(s, x), y_, seeds(s, y_), w.get(x, 0), w.get(y_, 0)))
    if pa != pb: print(int(s[:4]) + 1, "later-round points: vote", pa, "| upset alone", pb)
print("\nRound of 32 picks that differ:", len(diff))
print("vote pick (seed, rounds won) vs upset-alone pick (seed, rounds won)")
for s, x, sx, y_, sy, wx, wy in diff: print(f"  {int(s[:4]) + 1}: {x} ({sx}, won {wx}) vs {y_} ({sy}, won {wy})")
print("upset-alone pick was the lower seed:", sum(sy > sx for _, _, sx, _, sy, _, _ in diff))
print("R32 right: vote picks", sum(wx >= 2 for *_, wx, wy in diff), "| upset-alone picks", sum(wy >= 2 for *_, wx, wy in diff))
print("went on to win in the Sweet 16: vote picks", sum(wx >= 3 for *_, wx, wy in diff), "| upset-alone picks", sum(wy >= 3 for *_, wx, wy in diff))
print("reached Final Four: vote picks", sum(wx >= 4 for *_, wx, wy in diff), "| upset-alone picks", sum(wy >= 4 for *_, wx, wy in diff))

