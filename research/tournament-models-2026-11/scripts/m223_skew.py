import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"]); n = len(y)
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
avg = (p + s_up + sim_up) / 3; vote = ((p >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2
other = (s_up + sim_up) / 2; gap = p - other
print(f"upset chance, all 511: Upset avg {p.mean():.0%} | Strongside {s_up.mean():.0%} | simulator {sim_up.mean():.0%}")
print(f"correlations: Upset-Strongside {np.corrcoef(p, s_up)[0,1]:.2f} | Upset-sim {np.corrcoef(p, sim_up)[0,1]:.2f} | Strongside-sim {np.corrcoef(s_up, sim_up)[0,1]:.2f}")
sp = np.max([p, s_up, sim_up], 0) - np.min([p, s_up, sim_up], 0)
print(f"spread (highest minus lowest chance): median {np.median(sp):.0%} | 20+ pts {int((sp >= .2).sum())} games | 30+ pts {int((sp >= .3).sum())}")
print(f"Upset Model minus the other two's average: median {np.median(gap):+.0%} | Upset 15+ pts higher {int((gap >= .15).sum())} | 15+ pts lower {int((gap <= -.15).sum())}")
def grp(lab, m):
    print(f"\n{lab}: {int(m.sum())} games | upsets {int(y[m].sum())} ({y[m].mean() if m.sum() else 0:.0%}) | avg chance Upset {p[m].mean():.0%}, Strongside {s_up[m].mean():.0%}, sim {sim_up[m].mean():.0%}")
    for nm, pk in (("Upset Model 40%", p >= .4), ("vote", vote), ("average 45%", avg >= .45)): print(f"   {nm:16} right {int((pk[m] == (y[m] == 1)).sum())}/{int(m.sum())} | upset picks {int(pk[m].sum())}")
    print(f"   always higher seed {int((y[m] == 0).sum())}/{int(m.sum())}")
grp("Upset Model LIKES, both others don't (Upset >= 50%, Strongside and sim both < 40%)", (p >= .5) & (s_up < .4) & (sim_up < .4))
grp("Upset Model >= 40%, both others < 40%", (p >= .4) & (s_up < .4) & (sim_up < .4))
grp("Upset Model 15+ pts above the other two", gap >= .15)
grp("Upset Model DISLIKES, both others like (Upset < 40%, both others >= 50%)", (p < .4) & (s_up >= .5) & (sim_up >= .5))
grp("Upset Model 15+ pts below the other two", gap <= -.15)
print("\nthe 20 games where the Upset Model is most above the other two:")
for j in np.argsort(-gap)[:20]:
    r = rows[j]; print(f"   {int(r['s'][:4]) + 1} ({r['sL']}) {r['L']} vs ({r['sH']}) {r['H']}: Upset {p[j]:.0%} | Strongside {s_up[j]:.0%} | sim {sim_up[j]:.0%} | avg {avg[j]:.0%} -> {'UPSET' if y[j] else 'higher seed won'}")
print("\nthe 10 games where the Upset Model is most below the other two:")
for j in np.argsort(gap)[:10]:
    r = rows[j]; print(f"   {int(r['s'][:4]) + 1} ({r['sL']}) {r['L']} vs ({r['sH']}) {r['H']}: Upset {p[j]:.0%} | Strongside {s_up[j]:.0%} | sim {sim_up[j]:.0%} | avg {avg[j]:.0%} -> {'UPSET' if y[j] else 'higher seed won'}")
print("\nby how far the Upset Model is above the other two: games | upsets | actual upset rate | Upset Model's avg chance | other two's avg")
for lo, hi in ((-1, -.1), (-.1, 0), (0, .1), (.1, .2), (.2, 1)):
    m = (gap >= lo) & (gap < hi); print(f"   {lo:+.0%} to {hi:+.0%}|{int(m.sum())}|{int(y[m].sum())}|{y[m].mean():.0%}|{p[m].mean():.0%}|{other[m].mean():.0%}")