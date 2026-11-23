# 45% average of the three (Upset Model 29, Strongside, simulator) on every Round 1 game, by year. All three chances are
# already held out by tournament (Upset + Strongside fit without that year; the simulator never fits on results).
# Honest version: the cutoff for each year is picked on the OTHER 15 years only, then applied to that year.
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"]); n = len(y)
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (p + s_up + sim_up) / 3
vote = ((p >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2
grid = np.round(np.arange(.30, .601, .01), 2)
right = lambda pk, m: int((pk[m] == (y[m] == 1)).sum())
nest = np.zeros(n, bool); chosen = {}
for s in sorted(set(seas)):
    tr, te = seas != s, seas == s
    sc = [right(avg >= c, tr) for c in grid]; best = max(sc); c = float(np.median([g for g, v in zip(grid, sc) if v == best]))   # middle of the tied best
    chosen[s] = c; nest[te] = avg[te] >= c
print("year | upsets | avg 45% | avg, cutoff from other years (cutoff) | vote | Upset 40% | Strongside | simulator | higher seed")
T = np.zeros(7, int)
for s in sorted(set(seas)):
    m = seas == s; r = [right(avg >= .45, m), right(nest, m), right(vote, m), right(p >= .4, m), right(s_up >= .5, m), right(sim_up >= .5, m), int((y[m] == 0).sum())]
    T += r; print(f"{int(s[:4]) + 1}|{int(y[m].sum())}|{r[0]}|{r[1]} ({chosen[s]:.0%})|{r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}")
print("TOTAL|143|" + "|".join(map(str, T)))
for lab, pk in (("avg 45%", avg >= .45), ("avg, cutoff from other years", nest), ("vote", vote), ("Upset 40%", p >= .4)):
    print(f"{lab:30} right {right(pk, np.ones(n, bool))}/511 | upset picks {int(pk.sum())} ({int((pk & (y == 1)).sum())} hit, {(pk & (y == 1)).sum() / max(pk.sum(), 1):.0%}) | upsets caught {int((pk & (y == 1)).sum())}/143")
a, v = avg >= .45, vote
print(f"\navg 45% vs vote: same pick {int((a == v).sum())}/511 | disagree {int((a != v).sum())}: avg right {int(((a == (y == 1)) & (a != v)).sum())}, vote right {int(((v == (y == 1)) & (a != v)).sum())}")
w = {"avg better": 0, "same": 0, "vote better": 0}
for s in sorted(set(seas)):
    m = seas == s; d = right(a, m) - right(v, m); w["avg better" if d > 0 else "vote better" if d < 0 else "same"] += 1
print("years:", w)