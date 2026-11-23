# Overlap rule on the Round 1 upset measures: candidates = |z| >= 2 with the seed gap controlled; drop any that overlaps
# the net rating gap (|r| >= 0.3 with the higher-minus-lower-seed rating gap, across the 511 games); then, in z order,
# keep one per overlap group (|r| >= 0.3 with one already kept). Same 0.3 cut as the usual selection rule.
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
TM = Q.R.B.TM; n = len(rows)
sgap = np.array([r["sL"] - r["sH"] for r in rows], float)
gap = np.array([TM[r["s"]][r["H"]]["adj_net"] - TM[r["s"]][r["L"]]["adj_net"] for r in rows])
seas = np.array([r["s"] for r in rows]); early = np.array([int(s[:4]) < 2018 for s in seas])
def z_of(v, m=None):
    m = np.ones(n, bool) if m is None else m
    Xs = np.column_stack([sgap[m], v[m], np.ones(m.sum())]); w = np.zeros(3); yy = y[m]
    for _ in range(60):
        p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(Hm, Xs.T @ (yy - p))
    return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
cands = {}
for k in sorted({k[2:] for k in F}):
    for lab in ("L", "H", "L-H"):
        if lab == "L-H":
            if "L " + k not in F or "H " + k not in F: continue
            v = F["L " + k] - F["H " + k]
        else:
            if lab + " " + k not in F: continue
            v = F[lab + " " + k]
        if np.std(v) == 0: continue
        z = z_of(v)
        if abs(z) >= 2: cands[f"{lab} {k}"] = (z, v)
order = sorted(cands, key=lambda c: -abs(cands[c][0]))
kept, dropped_rating, dropped_overlap = [], [], []
for c in order:
    z, v = cands[c]; rg = abs(np.corrcoef(v, gap)[0, 1]); rs = abs(np.corrcoef(v, sgap)[0, 1])
    if rg >= 0.3: dropped_rating.append((c, z, rg)); continue
    hit = next((k for k in kept if abs(np.corrcoef(v, cands[k][1])[0, 1]) >= 0.3), None)
    if hit: dropped_overlap.append((c, z, hit, abs(np.corrcoef(v, cands[hit][1])[0, 1]))); continue
    kept.append(c)
print(f"candidates with |z| >= 2 (seed gap controlled): {len(order)}")
print(f"\nDROPPED, overlaps net rating (|r| >= 0.3 with the rating gap): {len(dropped_rating)}")
for c, z, r in dropped_rating: print(f"   {c:42} z {z:+.2f}  r with rating gap {r:.2f}")
print(f"\nDROPPED, overlaps a stronger measure already kept: {len(dropped_overlap)}")
for c, z, h, r in dropped_overlap: print(f"   {c:42} z {z:+.2f}  overlaps {h} (r {r:.2f})")
print(f"\nKEPT: {len(kept)}")
hp = next(j for j, r in enumerate(rows) if r["s"] == "2025-26" and r["L"] == "High Point"); m26 = seas == "2025-26"
for c in kept:
    z, v = cands[c]; rk = int((v[m26] > v[hp]).sum()) + 1 if z > 0 else int((v[m26] < v[hp]).sum()) + 1
    print(f"   {c:42} z {z:+.2f} | eras {z_of(v, early):+.2f} / {z_of(v, ~early):+.2f} | r with rating gap {abs(np.corrcoef(v, gap)[0,1]):.2f}, with seed gap {abs(np.corrcoef(v, sgap)[0,1]):.2f} | High Point rank {rk}/32")
json.dump(kept, open(os.path.join(HERE, "m187_kept.json"), "w"))
