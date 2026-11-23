# Over-seeded teams: seed better than the team's rating says. Rating seed = where our pre-tournament rating ranks the team
# in that year's field, 4 teams per seed line (1-4 -> 1 seed, ...). Over-seeding = rating seed - real seed (+3 = seeded
# 3 lines better than rated). Test in Round 1 and Round of 32 games: does the higher seed's over-seeding (or the lower
# seed's under-seeding) predict upsets beyond each model's own held-out chance?
import os, sys, json, contextlib, io, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
G = Q.R.B.G; B = Q.R.B; TM = Q.TM; kk = lambda s: (s or "").rstrip(". ")
def tname(s, t):
    for c in (t, t + ".", t.rstrip(".")):
        if c in TM[s]: return c
    return next((x for x in TM[s] if kk(x) == kk(t)), t)
FIELD = {}
for g in G:
    for side, sd in (("fav", "fseed"), ("dog", "dseed")): FIELD.setdefault(g["season"], {})[kk(g[side])] = g[sd]
RSEED = {}
for s, teams in FIELD.items():
    order = sorted(teams, key=lambda t: -(TM[s].get(tname(s, t), {}).get("adj_net") or -99))
    for r, t in enumerate(order): RSEED[(s, t)] = min(16, r // 4 + 1)
over = lambda s, t: RSEED[(s, kk(t))] - FIELD[s][kk(t)]
allo = np.array([over(s, t) for s in FIELD for t in FIELD[s]])
print(f"over-seeding across {len(allo)} tournament teams: mean {allo.mean():+.2f}, sd {allo.std():.2f}; 3+ lines over-seeded: {(allo >= 3).sum()}, 3+ under-seeded: {(allo <= -3).sum()}")
sig = lambda z: 1 / (1 + np.exp(-z)); logit = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
def wald(y, X):
    A = np.column_stack([X, np.ones(len(y))]); b = np.zeros(A.shape[1])
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (p * (1 - p))[:, None]) + 1e-8 * np.eye(A.shape[1]); b += np.linalg.solve(H, A.T @ (y - p))
    return b, b / np.sqrt(np.diag(np.linalg.inv(H)))
OUT_I = np.load(os.path.join(HERE, "m262_model_pre_I.npy")); OUT_G = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
UPX = json.load(open(os.path.join(HERE, "m289_upset_r32.json")))["real"]
def build(rnd):
    Y, HO, LO, PM, PU, PS, SG = [], [], [], [], [], [], []
    if rnd == 1:
        for r, pu in zip(D186["rows"], pho):
            i = r["i"]; s = r["s"]; hs = r["HisS"]
            Y.append(D186["y"][len(Y)]); HO.append(over(s, r["H"])); LO.append(over(s, r["L"])); PU.append(pu)
            PM.append(sig(-OUT_I[i]) if hs else sig(OUT_I[i])); PS.append(1 - B.simS[i] if hs else B.simS[i]); SG.append(r["sL"] - r["sH"])
    else:
        for r in UPX:
            i = next(j for j, g in enumerate(G) if g["season"] == r["s"] and g["rnd"] == "Second round" and {kk(g["fav"]), kk(g["dog"])} == {kk(r["h"]), kk(r["l"])})
            hs = kk(B.Sname[i]) == kk(r["h"]); s = r["s"]
            Y.append(r["up"]); HO.append(over(s, r["h"])); LO.append(over(s, r["l"])); PU.append(r["p"])
            PM.append(sig(-OUT_G[i]) if hs else sig(OUT_G[i])); PS.append(1 - B.simS[i] if hs else B.simS[i]); SG.append(FIELD[s][kk(r["l"])] - FIELD[s][kk(r["h"])])
    return [np.array(v, float) for v in (Y, HO, LO, PM, PU, PS, SG)]
for rnd, lab in ((1, "ROUND 1 (511)"), (2, "ROUND OF 32 (256)")):
    Y, HO, LO, PM, PU, PS, SG = build(rnd)
    print(f"\n{lab}: upset rate {Y.mean():.0%}")
    hi = HO >= 3; print(f"   higher seed over-seeded 3+ lines: {int(hi.sum())} games, upsets {int(Y[hi].sum())} ({Y[hi].mean():.0%}) | regular model expected {PM[hi].mean():.0%}, upset model {PU[hi].mean():.0%}, seed-gap-only baseline {Y[~hi].mean():.0%} elsewhere")
    lu = LO <= -3; print(f"   lower seed under-seeded 3+ lines: {int(lu.sum())} games, upsets {int(Y[lu].sum())} ({Y[lu].mean():.0%}) | regular model expected {PM[lu].mean():.0%}, upset model {PU[lu].mean():.0%}")
    for nm, P in (("seed gap only", None), ("regular model", PM), ("upset model", PU), ("simulator", PS)):
        base = SG[:, None] if P is None else logit(P)[:, None]
        for vn, V in (("higher seed over-seeding", HO), ("lower seed over-seeding", LO), ("over-seeding gap (higher - lower)", HO - LO), ("higher seed over-seeded 3+", (HO >= 3).astype(float))):
            b, z = wald(Y, np.column_stack([base, V])); print(f"   beyond {nm:14}: {vn:34} z {z[1]:+.2f}")
