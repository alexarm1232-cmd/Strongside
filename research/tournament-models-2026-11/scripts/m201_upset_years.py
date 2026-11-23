import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
p = np.array(json.load(open(os.path.join(H, "m188_out.json")))["p_noseed"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
pick = p >= 0.40
print("year|games|upsets|Upset Model right|upset picks|picks hit|Strongside right|Simulator right|Higher seed right")
T = np.zeros(8, int)
for s in sorted(set(seas)):
    m = seas == s; r = [int(m.sum()), int(y[m].sum()), int((pick[m] == (y[m] == 1)).sum()), int(pick[m].sum()), int((pick[m] & (y[m] == 1)).sum()),
                       int(((m1_up[m] >= .5) == (y[m] == 1)).sum()), int(((sim_up[m] >= .5) == (y[m] == 1)).sum()), int((y[m] == 0).sum())]
    T += r; print(f"{int(s[:4]) + 1}|" + "|".join(map(str, r)))
print("TOTAL|" + "|".join(map(str, T)))
u, st = [], []
for s in sorted(set(seas)):
    m = seas == s; u.append(int((pick[m] == (y[m] == 1)).sum())); st.append(int(((m1_up[m] >= .5) == (y[m] == 1)).sum()))
u, st = np.array(u), np.array(st); print(f"Upset Model vs Strongside by year: better {int((u > st).sum())}, tied {int((u == st).sum())}, worse {int((u < st).sum())}")
