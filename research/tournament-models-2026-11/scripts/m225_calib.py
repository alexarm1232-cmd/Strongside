# Recalibrating the Upset Model (29) AFTER it scores, so its chances match what happens, while keeping its order.
# Each year's adjustment is learned on the OTHER years' held-out chances only.
#  A) seed-line shift: one shift per matchup (1v16 ... 8v9) -> order within a seed line unchanged
#  B) global squeeze: a * logit + b (Platt) -> order across all games unchanged
#  C) seed-line shift + global squeeze
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); rows = D["rows"]; y = np.array(D["y"]); n = len(y)
p = np.array(json.load(open(os.path.join(H, "m219_out.json")))["p"])
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows]); sL = np.array([r["sL"] for r in rows]); seas = np.array([r["s"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
lg = lambda q: np.log(np.clip(q, 1e-4, 1 - 1e-4) / (1 - np.clip(q, 1e-4, 1 - 1e-4))); sig = lambda z: 1 / (1 + np.exp(-z))
L = lg(p); OH = np.column_stack([(sL == 17 - h).astype(float) for h in range(1, 9)])
def logit_fit(X, yy, off, lam=1.0):
    w = np.zeros(X.shape[1])
    for _ in range(60):
        q = sig(X @ w + off); Hm = X.T @ (X * (q * (1 - q))[:, None]) + lam * np.eye(X.shape[1]); w += np.linalg.solve(Hm, X.T @ (yy - q) - lam * w)
    return w
def calib(kind):
    out = np.zeros(n)
    for s in sorted(set(seas)):
        tr, te = seas != s, seas == s
        if kind == "A": w = logit_fit(OH[tr], y[tr], L[tr]); out[te] = sig(L[te] + OH[te] @ w)
        if kind == "B": X = np.column_stack([L, np.ones(n)]); w = logit_fit(X[tr], y[tr], 0, 1e-6); out[te] = sig(X[te] @ w)
        if kind == "C": X = np.column_stack([L, OH]); w = logit_fit(X[tr], y[tr], 0, 1e-3); out[te] = sig(X[te] @ w)
    return out
def auc(s_, yy):
    o = np.argsort(s_, kind="mergesort"); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
V = {"Upset Model as is": p, "A) seed-line shift": calib("A"), "B) global squeeze": calib("B"), "C) seed-line shift + squeeze": calib("C")}
right = lambda pk: int((pk == (y == 1)).sum())
print("version | AUC | Brier (lower = better calibrated) | right at 50% | 45% | 40% | 35% | upset picks at 40% (hit)")
for k, q in V.items():
    print(f"{k}|{auc(q, y):.3f}|{np.mean((q - y) ** 2):.4f}|{right(q >= .5)}|{right(q >= .45)}|{right(q >= .4)}|{right(q >= .35)}|{int((q >= .4).sum())} ({int(((q >= .4) & (y == 1)).sum())})")
print("\naverage upset chance by matchup")
print("matchup|actual|" + "|".join(V))
for h in range(1, 9):
    m = sL == 17 - h; print(f"{h} vs {17 - h}|{y[m].mean():.1%}|" + "|".join(f"{q[m].mean():.1%}" for q in V.values()))
print("\nwithin-seed-line order kept? (AUC inside each matchup, as is vs A)")
for h in range(1, 9):
    m = sL == 17 - h
    if 0 < y[m].sum() < m.sum(): print(f"   {h} vs {17 - h}: {auc(p[m], y[m]):.3f} vs {auc(V['A) seed-line shift'][m], y[m]):.3f}")
print("\nin the average of 3 and the vote:")
for k, q in V.items():
    a = (q + s_up + sim_up) / 3; v = ((q >= .5).astype(int) + (s_up >= .5) + (sim_up >= .5)) >= 2
    best = max(range(35, 56), key=lambda c: right(a >= c / 100))
    print(f"   {k:30} avg 45% {right(a >= .45)} | avg 50% {right(a >= .5)} | (best cutoff on all years {best}%: {right(a >= best / 100)}) | vote {right(v)} | avg AUC {auc(a, y):.3f}")
# honest: average with each year's cutoff from the other years
for k in ("Upset Model as is", "A) seed-line shift", "C) seed-line shift + squeeze"):
    q = V[k]; a = (q + s_up + sim_up) / 3; pk = np.zeros(n, bool)
    for s in sorted(set(seas)):
        tr, te = seas != s, seas == s; g = np.arange(.30, .61, .01); sc = [int(((a[tr] >= c) == (y[tr] == 1)).sum()) for c in g]; c = np.median(g[np.array(sc) == max(sc)]); pk[te] = a[te] >= c
    print(f"   honest avg (cutoff from other years) with {k:30} {right(pk)}/511 | upset picks {int(pk.sum())} ({int((pk & (y == 1)).sum())} hit)")
print("\nkey games: as is -> A) seed-line shift -> C)")
for yr, team in ((2024, "Grambling"), (2024, "Long Beach St"), (2024, "Saint Peter's"), (2018, "SFA"), (2024, "James Madison"), (2010, "Ohio"), (2021, "Abilene Christian"), (2026, "High Point"), (2024, "Oakland"), (2026, "Saint Louis"), (2011, "VCU")):
    j = next((k for k, r in enumerate(rows) if int(r["s"][:4]) + 1 == yr and r["L"] == team), None)
    if j is None: continue
    r = rows[j]; print(f"   {yr} ({r['sL']}) {team} vs ({r['sH']}) {r['H']}: {p[j]:.0%} -> {V['A) seed-line shift'][j]:.0%} -> {V['C) seed-line shift + squeeze'][j]:.0%} | {'UPSET' if y[j] else 'higher seed won'}")
json.dump({k: v.tolist() for k, v in V.items()}, open(os.path.join(H, "m225_calib.json"), "w"))