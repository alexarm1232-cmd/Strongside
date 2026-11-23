import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
up = np.array(json.load(open(os.path.join(H, "m188_out.json")))["p_noseed"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
def auc(s, yy):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
votes = (up >= .5).astype(int) + (m1_up >= .5).astype(int) + (sim_up >= .5).astype(int)
vote = votes >= 2; avg = (up + m1_up + sim_up) / 3
R = {"Vote (2 of 3, each at 50%)": vote, "Average of the three win chances (50%)": avg >= .5, "Upset Model alone (50%)": up >= .5, "Upset Model alone (40%, locked)": up >= .4,
     "Strongside Model": m1_up >= .5, "Simulator": sim_up >= .5, "Higher seed": np.zeros(len(y), bool)}
for k, pk in R.items():
    print(f"{k:42} right {int((pk == (y == 1)).sum())}/511 | upset picks {int(pk.sum())} ({int((pk & (y == 1)).sum())} hit)")
print(f"average AUC {auc(avg, y):.3f} (Upset {auc(up, y):.3f}, Strongside {auc(m1_up, y):.3f}, Simulator {auc(sim_up, y):.3f})")
print(f"how the votes split: 3-0 {int(((votes == 0) | (votes == 3)).sum())} games | 2-1 {int(((votes == 1) | (votes == 2)).sum())} games")
print("\nyear|vote|average|Upset 40%|Strongside|Simulator|Higher seed")
T = np.zeros(6, int)
for s in sorted(set(seas)):
    m = seas == s; r = [int((pk[m] == (y[m] == 1)).sum()) for pk in (vote, avg >= .5, up >= .4, m1_up >= .5, sim_up >= .5, np.zeros(len(y), bool))]
    T += r; print(f"{int(s[:4]) + 1}|" + "|".join(map(str, r)))
print("TOTAL|" + "|".join(map(str, T)))
