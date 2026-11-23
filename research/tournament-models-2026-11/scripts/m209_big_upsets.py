import os, json, math, numpy as np
H = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
U = json.load(open(os.path.join(H, "m188_out.json")))["inputs"]; used = {c.split(" ", 1)[1] for c in U}
sL = np.array([r["sL"] for r in rows]); big = sL >= 14
win, lose = big & (y == 1), big & (y == 0)
print(f"14-16 seed games {int(big.sum())}: winners {int(win.sum())} (14s {int((win & (sL == 14)).sum())}, 15s {int((win & (sL == 15)).sum())}, 16s {int((win & (sL == 16)).sum())})")
for j in np.where(win)[0]: print(f"   {int(rows[j]['s'][:4]) + 1} ({rows[j]['sL']}) {rows[j]['L']} over ({rows[j]['sH']}) {rows[j]['H']}")
def mw_z(a, b):    # Mann-Whitney z
    allv = np.concatenate([a, b]); r = np.argsort(np.argsort(allv)) + 1; R1 = r[:len(a)].sum(); n1, n2 = len(a), len(b)
    U_ = R1 - n1 * (n1 + 1) / 2; mu = n1 * n2 / 2; sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12); return (U_ - mu) / sd
res = []
cands = dict(F)
for k in {k[2:] for k in F}:
    if "L " + k in F and "H " + k in F: cands["L-H " + k] = F["L " + k] - F["H " + k]
for name, v in cands.items():
    base = name.split(" ", 1)[1]
    if base in used or v[big].std() == 0: continue
    z = mw_z(v[win], v[lose]); sgn = np.sign(z)
    # consistency: in each seed line with winners, winners' mean past the losers' mean in the same direction
    lines = []
    for sl in (14, 15, 16):
        w, l = win & (sL == sl), lose & (sL == sl)
        if w.sum(): lines.append(np.sign(v[w].mean() - v[l].mean()) == sgn)
    past = int((v[win] > np.median(v[lose])).sum()) if z > 0 else int((v[win] < np.median(v[lose])).sum())
    res.append((abs(z), name, z, v[win].mean(), v[lose].mean(), past, all(lines)))
res.sort(reverse=True)
print(f"\nmeasures NOT in the Upset Model, ranked by Mann-Whitney z (tests run: {len(res)}; about {int(len(res) * 0.046)} pass |z| >= 2 by chance)")
print("name | winners avg | losers avg | z | winners past losers' median | same direction in 14s, 15s and 16s")
for _, name, z, a, b, past, cons in res[:30]: print(f"{name}|{a:.2f}|{b:.2f}|{z:+.2f}|{past}/17|{'yes' if cons else 'no'}")
