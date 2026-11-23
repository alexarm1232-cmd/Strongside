import os, sys, json, numpy as np
from math import comb
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
up = np.array(json.load(open(os.path.join(H, "m188_out.json")))["p_noseed"]); U = json.load(open(os.path.join(H, "m188_out.json")))["inputs"]
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; m1_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
print(f"win-chance correlation: {np.corrcoef(lg(up), lg(m1_up))[0,1]:.2f} | average gap between their upset chances: {np.abs(up - m1_up).mean():.1%}")
for cut in (0.5, 0.4):
    a, b = up >= cut, m1_up >= .5; same = a == b; ra, rb = a == (y == 1), b == (y == 1); dis = ~same
    x, z = int((ra & dis).sum()), int((rb & dis).sum()); p = min(1, 2 * sum(comb(x + z, i) for i in range(max(x, z), x + z + 1)) / 2 ** (x + z))
    print(f"Upset Model at {cut:.0%}: same pick {int(same.sum())}/511 ({same.mean():.0%}) | both pick the upset {int((a & b).sum())} | only Upset Model {int((a & ~b).sum())} | only Strongside {int((~a & b).sum())} | disagreements {int(dis.sum())}: Upset right {x}, Strongside right {z} (p {p:.2f})")
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
mk = {n[2:] for n in names if n[:2] in ("S ", "W ")}
uk = {c.split(" ", 1)[1] for c in U}
print(f"\nStrongside measures {len(mk)} | Upset Model measures {len(uk)} | shared: {sorted(mk & uk)}")
