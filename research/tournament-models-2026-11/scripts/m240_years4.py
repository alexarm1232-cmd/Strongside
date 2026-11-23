import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
O = json.load(open(os.path.join(H, "m230_out.json"))); pin = np.array(O["p_all"]); pho = np.array(O["p_heldout"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
a = (pin + s_up + sim_up) / 3; ah = (pho + s_up + sim_up) / 3
cols = {"avg 45% held out": ah >= .45, "Upset 31 held out 40%": pho >= .4, "Original (usual, held out)": s_up >= .5, "Higher seed": np.zeros(len(y), bool)}
for s in sorted(set(seas)):
    m = seas == s; print(int(s[:4]) + 1, [int((pk[m] == (y[m] == 1)).sum()) for pk in cols.values()])
for k, pk in cols.items():
    per = [int((pk[seas == s] == (y[seas == s] == 1)).sum()) for s in sorted(set(seas))]; print(k, "best", max(per), "avg", round(np.mean(per), 1), "total", sum(per))