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
WINS = {}
for g in G:
    if g["rnd"] == "First Four": continue
    w = g["fav"] if g["fav_won"] else g["dog"]; WINS[(g["season"], w)] = WINS.get((g["season"], w), 0) + 1
deep = np.array([WINS.get((seas[j], win[j]), 0) for j in range(len(y))])   # tournament wins of each Round 1 winner
LAB = {1: "lost in Round 2", 2: "Sweet 16", 3: "Elite 8", 4: "Final Four", 5: "title game", 6: "won it all"}
M = {"Average of 3 (45%)": a >= .45, "Upset Model 31 (40%)": pin >= .4, "Strongside Model": s_up >= .5, "Simulator": sim_up >= .5, "Higher seed": np.zeros(len(y), bool)}
print("all Round 1 winners:", {LAB[k]: int((deep == k).sum()) for k in range(1, 7)})
print("\nmodel | missed R1 winners | " + " | ".join(LAB.values()) + " | avg wins of missed teams")
for k, pk in M.items():
    miss = pk != (y == 1); print(f"{k}|{int(miss.sum())}|" + "|".join(str(int((miss & (deep == v)).sum())) for v in range(1, 7)) + f"|{deep[miss].mean():.2f}")
print("\nmissed teams that reached the Sweet 16 or further:")
for k, pk in M.items():
    miss = (pk != (y == 1)) & (deep >= 2)
    print(f"\n{k} ({int(miss.sum())}):")
    for j in np.where(miss)[0][np.argsort(-deep[miss])]:
        r = rows[j]; t = win[j]; sd = r["sL"] if y[j] else r["sH"]; print(f"   {int(r['s'][:4]) + 1} ({sd}) {t}: {LAB[deep[j]]}")