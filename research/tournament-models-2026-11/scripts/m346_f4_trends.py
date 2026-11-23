# Final Four teams 2010-2026: pre-tournament profile vs every other team on the same seed lines (1-4 seeds mainly).
import os, sys, json, glob, contextlib, io
import numpy as np
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
from m210_followups import kk
t = open(os.path.join(HERE, "m242_bracket_in.js"), encoding="utf-8").read(); BI = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
TM = Q.TM
CONF = {}
for p in glob.glob(r"C:\Users\crtra\Downloads\basketball\data\seasons\*\*\*"):
    if os.path.isdir(p):
        code = os.path.basename(os.path.dirname(os.path.dirname(p)))
        if len(code) == 4 and code.isdigit(): CONF[("20" + code[:2] + "-" + code[2:], kk(os.path.basename(p)))] = os.path.basename(os.path.dirname(p))
K = ["adj_net", "adj_o", "adj_d", "tempo", "sos", "efg", "d_efg", "tov", "d_tov", "orb", "d_orb", "ftr", "d_ftr", "p3", "d_p3", "p2", "d_p2", "ft", "r3", "d_r3",
     "ast", "blk", "stl", "exp", "height", "big_height", "bench", "pm_close2h", "pm_late", "lead_max", "trail_max", "hold10", "comeback10", "pts3", "ptsft"]
LOWBAD = {"adj_d", "d_efg", "tov", "d_orb", "d_ftr", "d_p3", "d_p2", "d_r3", "trail_max"}   # lower is better
rows = []
for s, d in BI.items():
    tm = {}; w = dict(d["wins"])
    for g in d["games"]:
        tm[g["H"]] = g["sH"]; tm[g["L"]] = g["sL"]
        if g["H"] == g["L"]: w[g["H"]] = w.get(g["H"], 0) + 1
    allv = {k_: sorted([v[k_] for v in TM[s].values() if v.get(k_) is not None], reverse=k_ not in LOWBAD) for k_ in K}
    for team, seed in tm.items():
        v = next((TM[s][x] for x in TM[s] if kk(x) == kk(team)), None)
        if v is None: continue
        r = {"s": s, "team": team, "seed": seed, "wins": w.get(team, 0), "conf": CONF.get((s, kk(team)), "?")}
        for k_ in K:
            if v.get(k_) is None: continue
            r[k_] = v[k_]; r["rank_" + k_] = allv[k_].index(v[k_]) + 1
        rows.append(r)
F4 = [r for r in rows if r["wins"] >= 4]; CH = [r for r in rows if r["wins"] >= 6]
print(f"tournaments {len(BI)}, Final Four teams {len(F4)}, champions {len(CH)}")
print("\nSEEDS of Final Four teams:", dict(sorted(Counter(r["seed"] for r in F4).items())), "| champions:", dict(sorted(Counter(r["seed"] for r in CH).items())))
print("Final Four rate by seed:", {sd: f"{sum(r['seed'] == sd for r in F4)}/{sum(r['seed'] == sd for r in rows)}" for sd in range(1, 12)})
def rk(L, k_, cut): return sum(1 for r in L if r.get("rank_" + k_, 999) <= cut)
print("\nPRE-TOURNAMENT RANK (of ~350 D-I teams), net rating:")
for cut in (5, 10, 20, 30, 50):
    print(f"  top {cut:2}: Final Four {rk(F4, 'adj_net', cut)}/{len(F4)} | champions {rk(CH, 'adj_net', cut)}/{len(CH)}")
print("  median net rank: Final Four", int(np.median([r["rank_adj_net"] for r in F4])), "| champions", int(np.median([r["rank_adj_net"] for r in CH])))
print("  worst net rank in the Final Four:", sorted(((r["rank_adj_net"], r["s"], r["team"], r["seed"]) for r in F4), reverse=True)[:6])
print("\nOFFENSE & DEFENSE both top-N (adjusted):")
for n_ in (10, 20, 25, 40):
    both = lambda L: sum(1 for r in L if r["rank_adj_o"] <= n_ and r["rank_adj_d"] <= n_)
    pool = [r for r in rows if r["rank_adj_o"] <= n_ and r["rank_adj_d"] <= n_]
    print(f"  both top {n_}: Final Four {both(F4)}/{len(F4)} | champions {both(CH)}/{len(CH)} | all such teams reaching the Final Four {sum(r['wins'] >= 4 for r in pool)}/{len(pool)}")
print("  champions' offense / defense ranks:", sorted((r["s"][-2:], r["team"], r["rank_adj_o"], r["rank_adj_d"]) for r in CH))
# compare with same-seed non-Final Four teams (seeds 1-4, where 55 of 64 come from)
top = [r for r in rows if r["seed"] <= 4]; a = [r for r in top if r["wins"] >= 4]; b = [r for r in top if r["wins"] < 4]
print(f"\n1-4 SEEDS: {len(a)} made the Final Four vs {len(b)} did not. Biggest differences (standardized; + = Final Four teams higher):")
res = []
for k_ in K:
    x = np.array([r[k_] for r in a if k_ in r]); yv = np.array([r[k_] for r in b if k_ in r])
    if len(x) < 10: continue
    sd = np.concatenate([x, yv]).std() + 1e-9; d_ = (x.mean() - yv.mean()) / sd; tt = (x.mean() - yv.mean()) / np.sqrt(x.var() / len(x) + yv.var() / len(yv))
    res.append((k_, d_, tt, x.mean(), yv.mean()))
for k_, d_, tt, mx, my in sorted(res, key=lambda z: -abs(z[2]))[:14]: print(f"  {k_:12} effect {d_:+.2f} | t {tt:+.2f} | Final Four {mx:.3f} vs others {my:.3f}")
print("\nCONFERENCES of Final Four teams:", Counter(r["conf"] for r in F4).most_common(10))
print("   champions:", Counter(r["conf"] for r in CH).most_common())
print("\nby year:")
for s in sorted(BI):
    L = sorted([r for r in F4 if r["s"] == s], key=lambda r: -r["wins"])
    print("  ", int(s[:4]) + 1, " | ".join(f"{r['team']} ({r['seed']}, net #{r['rank_adj_net']}, O #{r['rank_adj_o']}, D #{r['rank_adj_d']})" for r in L))
