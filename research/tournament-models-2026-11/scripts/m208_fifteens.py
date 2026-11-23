import os, sys, json, math, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
up = np.array(json.load(open(os.path.join(H, "m188_out.json")))["p_noseed"])
m15 = np.array([r["sL"] == 15 for r in rows]); idx = np.where(m15)[0]
order = idx[np.argsort(-up[idx])]
print("15-seed games ranked by the Upset Model's chance (winners marked):")
for rank, j in enumerate(order, 1):
    if y[j] or rank <= 10: print(f"  {rank:2}. {int(rows[j]['s'][:4]) + 1} ({rows[j]['sL']}) {rows[j]['L']} vs ({rows[j]['sH']}) {rows[j]['H']}: {up[j]:.0%} {'WON' if y[j] else ''}")
win, lose = m15 & (y == 1), m15 & (y == 0)
print(f"\nwinning 15s (7) avg chance {up[win].mean():.0%} | losing 15s (57) {up[lose].mean():.0%}")
for cut in (0.5, 0.4, 0.3, 0.25, 0.2):
    pk = m15 & (up >= cut); print(f"  pick every 15 seed at {cut:.0%}+: {int(pk.sum())} picks, {int((pk & (y == 1)).sum())} of 7 winners, {int((pk & (y == 0)).sum())} wrong -> 2-15 games right {int(((up[m15] >= cut) == (y[m15] == 1)).sum())}/64 (always the 2 seed: 57)")
# what separates winning 15s from losing 15s (every measure, standardized gap between the groups; with 7 cases, descriptive only)
res = []
for k, v in F.items():
    a, b = v[win], v[lose]
    if b.std() == 0: continue
    d = (a.mean() - b.mean()) / v[m15].std(); hits = int((a > np.median(b)).sum()) if d > 0 else int((a < np.median(b)).sum())
    res.append((abs(d), k, d, a.mean(), b.mean(), hits))
res.sort(reverse=True)
print("\nmeasures that most separate the 7 winning 15 seeds from the 57 losers (effect size, and how many of the 7 are past the losers' median):")
for _, k, d, a, b, h in res[:16]: print(f"  {k:40} winners {a:.2f} vs losers {b:.2f} | effect {d:+.2f} | {h}/7")
