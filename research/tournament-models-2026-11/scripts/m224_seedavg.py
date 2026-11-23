import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); sL = np.array([r["sL"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (p + s_up + sim_up) / 3
print("matchup|games|actual upset rate|Upset Model|Strongside|Simulator|Average of 3")
for h in range(1, 9):
    m = sL == 17 - h; print(f"{h} vs {17 - h}|{int(m.sum())}|{y[m].mean():.1%} ({int(y[m].sum())})|{p[m].mean():.1%}|{s_up[m].mean():.1%}|{sim_up[m].mean():.1%}|{avg[m].mean():.1%}")
print(f"all|511|{y.mean():.1%}|{p.mean():.1%}|{s_up.mean():.1%}|{sim_up.mean():.1%}|{avg.mean():.1%}")