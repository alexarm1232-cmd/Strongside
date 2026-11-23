import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"]); n = len(y)
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows]); sL = np.array([r["sL"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (p + s_up + sim_up) / 3; U = int(y.sum())
def stats(pk): return int((pk == (y == 1)).sum()), int(pk.sum()), int((pk & (y == 1)).sum())
print(f"{U} upsets in 511 games; 75% = {int(np.ceil(.75 * U))} caught")
srt = np.sort(avg[y == 1])[::-1]; need = int(np.ceil(.75 * U)); cut = srt[need - 1]
print(f"lowest average needed to catch 75%: {cut:.1%}\n")
print("average at least | upsets caught | games right /511 | upset picks | hit rate | wrong upset picks")
for c in (.50, .45, .42, .40, .38, .36, .35, .34, .33, .32, round(float(cut), 4), .30, .28, .25):
    r, k, h = stats(avg >= c); print(f"{c:.1%}|{h}/{U} ({h / U:.0%})|{r}|{k}|{h / max(k, 1):.0%}|{k - h}")
r, k, h = stats(np.zeros(n, bool)); print(f"\nalways higher seed: {r}/511")
for lab, pk in (("Upset Model (29) at 40%", p >= .4), ("3-way vote", ((p >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2), ("average at 50%", avg >= .5)):
    r, k, h = stats(pk); print(f"{lab}: {r}/511 | catches {h}/{U} ({h / U:.0%}) | picks {k}")
pk = avg >= cut
print(f"\nat the 75% cutoff ({cut:.1%}), by matchup: games | upsets | caught | upset picks | games right")
for hs in range(1, 9):
    m = sL == 17 - hs; print(f"{hs} vs {17 - hs}|{int(m.sum())}|{int(y[m].sum())}|{int((pk & m & (y == 1)).sum())}|{int((pk & m).sum())}|{int(((pk == (y == 1)) & m).sum())}")
# honest: cutoff picked on 2010-17 to catch 75% there, applied to 2018-26
early = np.array([int(s[:4]) < 2018 for s in seas])
ce = np.sort(avg[early & (y == 1)])[::-1][int(np.ceil(.75 * (early & (y == 1)).sum())) - 1]
m = ~early; pk2 = avg[m] >= ce
print(f"\nhonest check: cutoff set on 2010-17 = {ce:.1%}; on 2018-26 it catches {int((pk2 & (y[m] == 1)).sum())}/{int(y[m].sum())} upsets ({(pk2 & (y[m] == 1)).sum() / y[m].sum():.0%}), games right {int((pk2 == (y[m] == 1)).sum())}/255 vs vote {int(((((p >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2)[m] == (y[m] == 1)).sum())}/255 and higher seed {int((y[m] == 0).sum())}/255")
# bracket points-style: expected upsets per year
print(f"upset picks per year at the 75% cutoff: {pk.sum() / 16:.1f} (actual upsets per year {U / 16:.1f})")