import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
O = json.load(open(os.path.join(H, "m230_out.json"))); pin = np.array(O["p_all"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
a = (pin + s_up + sim_up) / 3
G = Q.R.B.G; print("rounds:", sorted({g["rnd"] for g in G}))
R2W = {(g["season"], g["fav"] if g["fav_won"] else g["dog"]) for g in G if g["rnd"] == "Second round"}
win = np.array([r["L"] if y[j] else r["H"] for j, r in enumerate(rows)]); w2 = np.array([(seas[j], win[j]) in R2W for j in range(len(y))])
print("Round 1 winners who also won in Round 2:", int(w2.sum()))
M = {"Average of 3 (45%)": a >= .45, "Upset Model 31 (40%)": pin >= .4, "Strongside Model": s_up >= .5, "Simulator": sim_up >= .5, "Higher seed": np.zeros(len(y), bool)}
def st(pk, m):
    ok = pk == (y == 1); return int(ok[m].sum()), int((~ok & w2 & m).sum()), int((pk & (y == 1) & m).sum()), int((pk & m).sum())
print("\nTOTAL: model | R1 right /511 | missed teams that won again (of 32/yr) | upsets picked right | upset picks")
for k, pk in M.items(): r = st(pk, np.ones(len(y), bool)); print(f"{k}|{r[0]}|{r[1]} of {int(w2.sum())}|{r[2]} of 143|{r[3]}")
print("\nYEAR: year | upsets | " + " | ".join(M) + "   (each: right / missed 2-game winners / upsets hit)")
for s in sorted(set(seas)):
    m = seas == s; print(f"{int(s[:4]) + 1}|{int(y[m].sum())}|" + "|".join("{}/{}/{}".format(*st(pk, m)[:3]) for pk in M.values()))