# Reddit ideas: (1) extreme tempo = dictates the game; possession length x tempo; (2) offense-heavy vs defense-heavy
# teams at the same strength, and champions' pre-tournament offense/defense ranks; (3) over-seeded teams (seed better
# than the rating's implied seed by 2+ lines); (4) offensive rebounding (already in: S orb).
# Each: z on top of the 3 strength inputs (all 1,007 games, R64-title), then added to the exact 756 pipeline.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
B = Q.R.B; TM = B.TM; G = B.G; X, KS = B.X, B.KS
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
c = lambda k: X[:, KS.index(k)]
seedS, seedW = np.array(B.sS, float), np.array(B.sW, float)
# implied seed: rank by adj_net among that season's tournament teams, 4 per line
imp = {}
for s in sorted({g["season"] for g in G}):
    ts = sorted({t for g in G if g["season"] == s for t in (g["fav"], g["dog"])}, key=lambda t: -TM[s][t]["adj_net"])
    for r, t in enumerate(ts): imp[(s, t)] = min(16, r // 4 + 1)
iS = np.array([imp[(g["season"], B.Sname[i])] for i, g in enumerate(G)], float); iW = np.array([imp[(g["season"], Wn[i])] for i, g in enumerate(G)], float)
overS, overW = iS - seedS, iW - seedW              # + = seeded better than the rating says (over-seeded)
F = {"S extreme tempo": np.abs(c("S tempo") - .5), "W extreme tempo": np.abs(c("W tempo") - .5),
     "S poss length x tempo": (c("S apl_o") - .5) * (c("S tempo") - .5), "W poss length x tempo": (c("W apl_o") - .5) * (c("W tempo") - .5),
     "S offense-heavy": c("S adj_o") + c("S adj_d") - 1, "W offense-heavy": c("W adj_o") + c("W adj_d") - 1,
     "S over-seeded (lines)": overS, "W over-seeded (lines)": overW,
     "S over-seeded 2+": (overS >= 2).astype(float), "W over-seeded 2+": (overW >= 2).astype(float)}
# fatigue: games in the 7 days before, and days since the last game (all pre-game, from the schedule)
import json, datetime as dt
sys.path.insert(0, Q.OLD); import upset_data as U
from concurrent.futures import ProcessPoolExecutor as _P
def _sched(s):
    code = s[2:4] + s[5:7]; games, td = U.load(code); d = {}
    for g in games:
        for t in (g["home"], g["away"]): d.setdefault(t, []).append(g["date"])
    return s, d
_cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m132_sched.json")
if os.path.exists(_cache): SCH = json.load(open(_cache))
else: SCH = None
def fat(s, t, date):
    D = [dt.date(*map(int, x.split("/"))) for x in (SCH.get(s, {}).get(t) or SCH.get(s, {}).get(t + ".") or [])]
    d0 = dt.date(*map(int, date.split("/"))); prev = [x for x in D if x < d0]
    if not prev: return 0.0, 7.0
    return float(sum((d0 - x).days <= 7 for x in prev)), float(min(7, (d0 - max(prev)).days))
k = ~Q.FF
def zt(v):
    Xs = np.column_stack([Q.X30[k][:, :3], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[3] / np.sqrt(np.linalg.inv(H)[3, 3])
if SCH:
    A = np.array([fat(g["season"], B.Sname[i], g["date"]) + fat(g["season"], Wn[i], g["date"]) for i, g in enumerate(G)])
    F.update({"S games last 7 days": A[:, 0], "S rest days": A[:, 1], "W games last 7 days": A[:, 2], "W rest days": A[:, 3], "games last 7 gap": A[:, 0] - A[:, 2], "rest gap": A[:, 1] - A[:, 3]})
V = {"current 756 (30)": None, "+ over-seeded 2+ (S, W)": ["S over-seeded 2+", "W over-seeded 2+"], "+ fatigue (S, W games last 7, rest)": ["S games last 7 days", "W games last 7 days", "S rest days", "W rest days"], "+ extreme tempo (S, W)": ["S extreme tempo", "W extreme tempo"],
     "+ offense-heavy (S, W)": ["S offense-heavy", "W offense-heavy"], "+ over-seeded lines (S, W)": ["S over-seeded (lines)", "W over-seeded (lines)"]}
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
    return name, held, insr, auc, out
if __name__ == "__main__" and not SCH:
    with _P(6) as ex: json.dump(dict(ex.map(_sched, sorted({g['season'] for g in G}))), open(_cache, 'w'))
    print('schedules cached; rerun'); sys.exit()
if __name__ == "__main__":
    for f, v in F.items(): print(f"z on top of strength  {f:24} {zt(v):+.2f}")
    # over-seeded teams: how far they went vs what the rating expects (all teams seeded 1-10 that were 2+ lines over-seeded)
    rows = []
    for s in sorted({g["season"] for g in G}):
        gs = [g for g in G if g["season"] == s and g["rnd"] != "First Four"]
        for t in {x for g in gs for x in (g["fav"], g["dog"])}:
            mine = [g for g in gs if t in (g["fav"], g["dog"])]; seed = mine[0]["fseed"] if mine[0]["fav"] == t else mine[0]["dseed"]
            if seed <= 10: rows.append((imp[(s, t)] - seed, len([g for g in mine if (g["fav"] == t) == g["fav_won"]])))
    ov = [w for d, w in rows if d >= 2]; ok = [w for d, w in rows if abs(d) <= 1]
    print(f"\nseeds 1-10: over-seeded 2+ lines {len(ov)} teams, avg tournament wins {np.mean(ov):.2f}, R64 exits {np.mean(np.array(ov)==0):.0%}")
    print(f"            seeded within 1 line of rating {len(ok)} teams, avg wins {np.mean(ok):.2f}, R64 exits {np.mean(np.array(ok)==0):.0%}")
    # champions' pre-tournament offense / defense rank (D-I)
    print()
    for s in sorted({g["season"] for g in G}):
        ch = [g for g in G if g["season"] == s and g["rnd"] == "Championship"]
        if not ch: continue
        g = ch[0]; t = g["fav"] if g["fav_won"] else g["dog"]
        ro = 1 + sum(v["adj_o"] > TM[s][t]["adj_o"] for v in TM[s].values()); rd = 1 + sum(v["adj_d"] < TM[s][t]["adj_d"] for v in TM[s].values())
        rn = 1 + sum(v["adj_net"] > TM[s][t]["adj_net"] for v in TM[s].values())
        print(f"champion {s} {t:16} net #{rn:<3} offense #{ro:<3} defense #{rd}")
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(4) as ex:
        for name, held, insr, auc, out in ex.map(job, V):
            res[name] = out; print(f"{name:30} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f}", flush=True)

