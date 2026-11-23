# Ideas from the links: tournament experience (program's NCAA wins last 1 and last 3 tournaments), returning minutes,
# late-season form (last 10 games before the tournament: avg margin, and margin minus season avg), seed.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
B = Q.R.B; G = B.G
Wn = [g["dog"] if s == g["fac"] else g["fav"] for g, s in zip(G, B.Sname)] if False else [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
SEAS = sorted({g["season"] for g in G}); k = ~Q.FF
# tournament wins by (season, team), First Four excluded
TW = {}
for g in G:
    if g["rnd"] == "First Four": continue
    w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
def prior(s, t, n):
    i = SEAS.index(s); prev = SEAS[max(0, i - n):i]
    if not prev: return np.nan
    return sum(TW.get((p, t), 0) for p in prev)
RET = json.load(open(os.path.join(HERE, "m135_ret.json"))); GM = json.load(open(os.path.join(HERE, "m134_games.json")))
def form(s, t):
    rows = sorted((r for r in GM[s] if t in (r[1], r[2])), key=lambda r: r[0])
    m = [r[4] if r[1] == t else -r[4] for r in rows]
    if len(m) < 12: return np.nan, np.nan, np.nan
    return float(np.mean(m[-10:])), float(np.mean(m[-10:]) - np.mean(m)), float(np.mean(np.array(m[-10:]) > 0))
def col(f):
    a = np.array([f(g["season"], B.Sname[i]) for i, g in enumerate(G)], float); b = np.array([f(g["season"], Wn[i]) for i, g in enumerate(G)], float)
    for v in (a, b): v[np.isnan(v)] = np.nanmean(v)
    return a, b
F = {}
for n in (1, 3):
    a, b = col(lambda s, t: prior(s, t, n)); F[f"S tourney wins last {n}"], F[f"W tourney wins last {n}"] = a, b
a, b = col(lambda s, t: RET.get(s, {}).get(t, {}).get("returning", np.nan)); F["S returning minutes"], F["W returning minutes"] = a, b
FM = {(g["season"], t): form(g["season"], t) for g in G for t in (g["fav"], g["dog"])}
for j, nm in enumerate(("last-10 margin", "last-10 margin vs season", "last-10 win %")):
    a, b = col(lambda s, t: FM[(s, t)][j]); F["S " + nm], F["W " + nm] = a, b
F["S seed"], F["W seed"] = np.array(B.sS, float), np.array(B.sW, float)
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
V = {"current 756 (30)": None, "+ S tourney wins last 3 only": ["S tourney wins last 3"], "+ S returning minutes only": ["S returning minutes"], "+ S last-10 win % only": ["S last-10 win %"]}; _V0 = {"x": None, "+ tourney wins last 3 (S, W)": ["S tourney wins last 3", "W tourney wins last 3"],
     "+ returning minutes (S, W)": ["S returning minutes", "W returning minutes"],
     "+ last-10 form vs season (S, W)": ["S last-10 margin vs season", "W last-10 margin vs season"],
     "+ seeds (S, W)": ["S seed", "W seed"]}
def job(name):
    XX = Q.X30 if V[name] is None else np.column_stack([Q.X30] + [F[f] for f in V[name]])
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    return name, held, insr, auc
if __name__ == "__main__":

    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(5) as ex:
        for name, held, insr, auc in ex.map(job, V):
            print(f"{name:34} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f}", flush=True)

