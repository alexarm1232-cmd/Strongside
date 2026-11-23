import os, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"])
up = np.array(json.load(open(os.path.join(H, "m188_out.json")))["p_noseed"])
cur = None
for j in sorted(np.where(up >= .5)[0], key=lambda j: (rows[j]["s"], -up[j])):
    r = rows[j]; yr = int(r["s"][:4]) + 1
    if yr != cur: cur = yr; print(f"\n{yr}")
    print(f"  ({r['sL']}) {r['L']} over ({r['sH']}) {r['H']} | {up[j]:.0%} | {'HIT' if y[j] else 'miss'}")
pk = up >= .5; print(f"\ntotal {int(pk.sum())} picks, {int((pk & (y == 1)).sum())} hit")
