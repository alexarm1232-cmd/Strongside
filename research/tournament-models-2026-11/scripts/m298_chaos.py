# Can a "chaos region" be seen before the tournament? 64 regions (16 years x 4). Chaos = upsets (lower seed won) in the
# region's 8 Round 1 games + 4 real Round of 32 games. Pre-declared region measures (all pre-tournament), each tested
# against (a) raw upsets and (b) upsets beyond what the models expected. Plus: is chaos more spread out than chance?
import os, sys, json, contextlib, io, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m294_recency.py"), encoding="utf-8-sig").read(); src = src[:src.index("W1 = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
TMx = Q.TM
def tv(s, t, key):
    d = TMx[s].get(tname(s, t)) or {}; return d.get(key)
VB = json.load(open(os.path.join(HERE, "m293_brackets_three.json"))); VBy = {d["season"]: d for d in VB}
rows = []
for s in SEASONS:
    g = BI[s]["games"]; wins = BI[s]["wins"]; d = VBy[s]
    for k in range(4):
        G8 = g[8 * k:8 * k + 8]; teams = [t for x in G8 for t in ({x["H"], x["L"]})]
        sd_ = {x["H"]: x["sH"] for x in G8}; sd_.update({x["L"]: x["sL"] for x in G8})
        up1 = exp1 = n1 = 0
        for x in G8:
            if x["H"] == x["L"] or x["sH"] == x["sL"]: continue
            u, m, si = R1P[str(x["gid"])]; exp1 += (u + m + si) / 3; up1 += x["won"] == x["L"]; n1 += 1
        up2 = exp2 = 0
        for q in range(4 * k, 4 * k + 4):
            A = [t for x in g[2 * q:2 * q + 2] for t in {x["H"], x["L"]}]
            w = d["r2won"][q]; losers = [t for t in A if t != w and wins.get(t, 0) >= 1 or (t != w and any(x["H"] == x["L"] == t for x in g[2*q:2*q+2]))]
            r1w = [x["won"] for x in g[2 * q:2 * q + 2]]
            if len(r1w) == 2 and w in r1w:
                o = r1w[0] if r1w[1] == w else r1w[1]; h, l = (w, o) if sd_[w] < sd_[o] else (o, w)
                if sd_[h] != sd_[l]:
                    key = (h, l) if f"{s}|{h}|{l}" in UPP else (l, h)
                    hh, ll, pu = UPP[f"{s}|{key[0]}|{key[1]}"]; S_, W_, z = MZ[(s, key[0], key[1])]; pS = 1 / (1 + np.exp(-z)); pm = pS if kk(ll) == S_ else 1 - pS
                    exp2 += (pu + pm) / 2 if ll == l else 1 - (pu + pm) / 2; up2 += w == l
        net = {t: tv(s, t, "adj_net") for t in teams}; net = {t: v for t, v in net.items() if v is not None}
        top = min(teams, key=lambda t: sd_[t])
        fav = [x["H"] for x in G8 if x["H"] != x["L"]]; dog = [x["L"] for x in G8 if x["H"] != x["L"]]
        gaps = [net[x["H"]] - net[x["L"]] for x in G8 if x["H"] != x["L"] and x["H"] in net and x["L"] in net]
        f = {"expected upsets (models)": exp1 + exp2,
             "1 seed's rating": net.get(top, np.nan),
             "avg Round 1 rating gap": np.mean(gaps),
             "spread of ratings (sd)": np.std(list(net.values())),
             "seeds 9-16 avg rating": np.mean([net[t] for t in teams if sd_[t] >= 9 and t in net]),
             "underdogs' 3-pt rate": np.mean([tv(s, t, "r3") or np.nan for t in dog]),
             "favorites' tempo": np.mean([tv(s, t, "tempo") or np.nan for t in fav]),
             "underdogs' tempo": np.mean([tv(s, t, "tempo") or np.nan for t in dog])}
        rows.append(dict(s=s, k=k, ups=up1 + up2, exp=exp1 + exp2, vote=sum(d["brackets"]["vote"]["r1"][j]["pick"] == g[j]["won"] for j in range(8 * k, 8 * k + 8) if g[j]["H"] != g[j]["L"]) + 2 * sum(d["brackets"]["vote"]["r2"][q]["pick"] == d["r2won"][q] for q in range(4 * k, 4 * k + 4)), **f))
ups = np.array([r["ups"] for r in rows], float); expv = np.array([r["exp"] for r in rows]); resid = ups - expv; vote = np.array([r["vote"] for r in rows], float)
print(f"64 regions: upsets per region mean {ups.mean():.2f} (range {int(ups.min())}-{int(ups.max())}), models expected {expv.mean():.2f}")
def corr_p(x, y):
    m = np.isfinite(x) & np.isfinite(y); r = np.corrcoef(x[m], y[m])[0, 1]; n = m.sum(); t = r * math.sqrt((n - 2) / (1 - r * r));
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2)))); return r, p
print(f"\n{'region measure (pre-tournament)':30} | r with upsets (p) | r with upsets beyond expected (p) | r with vote points (p)")
for key in rows[0]:
    if key in ("s", "k", "ups", "exp", "vote"): continue
    x = np.array([r[key] for r in rows], float); a = corr_p(x, ups); b = corr_p(x, resid); c = corr_p(x, vote)
    print(f"{key:30} | {a[0]:+.2f} ({a[1]:.2f}) | {b[0]:+.2f} ({b[1]:.2f}) | {c[0]:+.2f} ({c[1]:.2f})")
# is chaos more spread out than chance? simulate regions from the models' own game chances
var_obs = ups.var()
print(f"\nvariance of upsets per region: observed {var_obs:.2f} | if each game were a coin flip at the models' chances: about {np.mean([r['exp'] for r in rows]) - 0:.2f} mean, variance check below")
# year effect: do the 4 regions of a year move together?
yr = {}
for r, e in zip(rows, resid): yr.setdefault(r["s"], []).append(e)
ym = np.array([np.mean(v) for v in yr.values()]); within = np.mean([np.var(v, ddof=1) for v in yr.values()])
print(f"year effect: variance of year averages {ym.var(ddof=1):.2f} vs expected from regions alone {within / 4:.2f} (ratio {ym.var(ddof=1) / (within / 4):.2f}; ~1 = no year effect)")
json.dump(rows, open(os.path.join(HERE, "m298_regions.json"), "w"), default=float)
