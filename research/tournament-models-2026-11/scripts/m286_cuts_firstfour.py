# (1) Upset models at other cutoffs (Round 1 and Round of 32 at 40 / 45 / 50), on the real games and as a pre-filled bracket.
# (2) Is coming out of the First Four (as an 11-14 seed, not a 16) significant in Round 1 and the Round of 32?
import os, sys, json, contextlib, io, math
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read()
src = src[:src.index('print("\\nBRACKETS')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
import numpy as np
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); r1rows = D186["rows"]; y1 = np.array(D186["y"])
pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
ph32 = MODELS["separate"][2]
print("REAL GAMES, each year held out")
print("   Round 1 Upset Model:", " | ".join(f"@{c}: {int(((pho >= c / 100) == (y1 == 1)).sum())}/511 ({int((pho >= c / 100).sum())} upset picks, {int(((pho >= c / 100) & (y1 == 1)).sum())} hit)" for c in (40, 45, 50)))
print("   Round of 32 Upset Model:", " | ".join(f"@{c}: {int(((ph32 >= c / 100) == (yR == 1)).sum())}/{nR} ({int((ph32 >= c / 100).sum())} picks, {int(((ph32 >= c / 100) & (yR == 1)).sum())} hit)" for c in (40, 45, 50)))
print("\nBRACKETS filled out before Round 1 (R1 x1 + R32 x2), 16 years")
print("   R1 cut | R32 cut | points | R1 right | R32 right | R32 upset picks")
for c1 in (40, 45, 50):
    f1 = lambda s, g, c1=c1: g["L"] if P1.get((s, g["L"]), 0) >= c1 / 100 else g["H"]
    for c2 in (40, 45, 50):
        pts, a, b, u = bracket(f1, "separate", c2 / 100); print(f"   {c1:5}  | {c2:6}  | {pts:6} | {a:8} | {b:9} | {u}")
# ---- (2) First Four
Q_ = None
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q_
G = Q_.R.B.G; kk = lambda s: (s or "").rstrip(". ")
FFW = {}
for g in G:
    if g["rnd"] == "First Four":
        w = g["fav"] if g["fav_won"] else g["dog"]; sd = g["fseed"] if g["fav_won"] else g["dseed"]
        if sd != 16: FFW[(g["season"], kk(w))] = sd
print(f"\nFIRST FOUR winners seeded 11-14 (not 16): {len(FFW)} teams, seeds {sorted(set(FFW.values()))}")
def logit(p): p = np.clip(p, 1e-4, 1 - 1e-4); return np.log(p / (1 - p))
def wald(y, X):
    A = np.column_stack([X, np.ones(len(y))]); b = np.zeros(A.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-A @ b)); H = A.T @ (A * (p * (1 - p))[:, None]) + 1e-8 * np.eye(A.shape[1]); b += np.linalg.solve(H, A.T @ (y - p))
    se = np.sqrt(np.diag(np.linalg.inv(H))); return b, b / se
# Round 1: is the lower seed a First Four winner?
ffL = np.array([(r["s"], kk(r["L"])) in FFW for r in r1rows]); sL = np.array([r["sL"] for r in r1rows]); sH = np.array([r["sH"] for r in r1rows])
for sd in sorted(set(FFW.values())):
    m = (sL == sd) & (np.array([int(r["s"][:4]) + 1 for r in r1rows]) >= 2011)
    a, b_ = m & ffL, m & ~ffL
    print(f"   Round 1, {sd} seeds since 2011: First Four winners {int(y1[a].sum())}-{int(a.sum() - y1[a].sum())} ({y1[a].mean():.0%}, Upset Model said {pho[a].mean():.0%}) | others {int(y1[b_].sum())}-{int(b_.sum() - y1[b_].sum())} ({y1[b_].mean():.0%}, model said {pho[b_].mean():.0%})")
m = np.isin(sL, list(set(FFW.values()))) & (np.array([int(r["s"][:4]) + 1 for r in r1rows]) >= 2011)
a = m & ffL
print(f"   Round 1, all 11-14 seeds since 2011: First Four winners {int(y1[a].sum())}-{int(a.sum() - y1[a].sum())} ({y1[a].mean():.0%}) vs others {int(y1[m & ~ffL].sum())}-{int((m & ~ffL).sum() - y1[m & ~ffL].sum())} ({y1[m & ~ffL].mean():.0%})")
b, z = wald(y1[m].astype(float), np.column_stack([sL[m] - sH[m], ffL[m].astype(float)])); print(f"   Round 1 z for First Four, seed gap controlled: {z[1]:+.2f} (coef {b[1]:+.2f})")
b, z = wald(y1[m].astype(float), np.column_stack([logit(pho[m]), ffL[m].astype(float)])); print(f"   Round 1 z for First Four beyond the Upset Model's chance: {z[1]:+.2f}")
# exact-ish permutation within seed lines: shuffle the FF flag among same-seed same-era teams
rng = np.random.default_rng(0); obs = y1[a].sum(); cnt = 0; idx = np.where(m)[0]
for _ in range(20000):
    f = np.zeros(len(y1), bool)
    for sd in sorted(set(FFW.values())):
        pool = idx[sL[idx] == sd]; k_ = int((ffL & (sL == sd) & m).sum())
        if k_: f[rng.choice(pool, k_, replace=False)] = True
    cnt += y1[f].sum() >= obs
print(f"   Round 1 permutation (FF label shuffled within seed line): p = {cnt / 20000:.3f} for winning {int(obs)} or more")
# Round of 32: a First Four team still alive
ffR = np.array([(r["l"][0], kk(r["l"][1])) in FFW for r in REAL]); ffRh = np.array([(r["h"][0], kk(r["h"][1])) in FFW for r in REAL])
print(f"\n   Round of 32: First Four team as the lower seed {int(ffR.sum())} games, won {int(yR[ffR].sum())} ({yR[ffR].mean() if ffR.any() else 0:.0%}); Round of 32 model said {ph32[ffR].mean() if ffR.any() else 0:.0%}")
sLR = np.array([TEAM[r["l"]]["seed"] for r in REAL]); same = np.isin(sLR, [11, 12, 13, 14]) & ~ffR & (np.array([int(r["s"][:4]) + 1 for r in REAL]) >= 2011)
print(f"   other 11-14 seeds in the Round of 32 since 2011: {int(same.sum())} games, won {int(yR[same].sum())} ({yR[same].mean():.0%}); model said {ph32[same].mean():.0%}")
if ffR.sum() >= 3:
    mm = ffR | same; b, z = wald(yR[mm].astype(float), np.column_stack([logit(ph32[mm]), ffR[mm].astype(float)])); print(f"   Round of 32 z for First Four beyond the model's chance (11-14 seeds): {z[1]:+.2f}")
for (s_, t_), sd in sorted(FFW.items()):
    w1 = BI[s_]["wins"].get(t_, BI[s_]["wins"].get(t_ + ".", 0)) if s_ in BI else None
    print(f"      {int(s_[:4]) + 1} {sd:2} {t_:24} tournament wins after the First Four: {w1}")
