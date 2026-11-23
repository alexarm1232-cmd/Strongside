# Leak test: FGA / FGM season totals pulled AFTER the tournament (sports-reference season pages) include tournament games,
# so teams that advanced have bigger totals. Compare R64 AUC of the FGA/FGM total gap: pre-tournament vs end of season.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "m147_totals.json")
B = Q.R.B; G = B.G; k = ~Q.FF
Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
def _load(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999"); T = {}
    for g in games:
        for t in (g["home"], g["away"]):
            if t not in g["side"]: continue
            a = g["side"][t]; r = T.setdefault(t, [0.0] * 4)
            r[2] += a["fga"]; r[3] += a["fgm"]
            if g["date"] < first: r[0] += a["fga"]; r[1] += a["fgm"]
    return s, T
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_load, sorted({g["season"] for g in G}))), open(CACHE, "w"))
    T = json.load(open(CACHE))
    get = lambda s, t, j: (T[s].get(t) or T[s].get(t + ".") or [np.nan] * 4)[j]
    def gapcol(j): return np.array([get(g["season"], B.Sname[i], j) - get(g["season"], Wn[i], j) for i, g in enumerate(G)])
    def auc(sc, y):
        ok = ~np.isnan(sc); sc, y = sc[ok], y[ok]; o = np.argsort(sc); rk = np.empty(len(sc)); rk[o] = np.arange(1, len(sc) + 1); n1 = y.sum()
        return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
    r64 = k & (Q.RND == "First round"); y = Q.yb.astype(int)
    for nm, j in (("FGA total, pre-tournament", 0), ("FGM total, pre-tournament", 1), ("FGA total, end of season (incl. tournament)", 2), ("FGM total, end of season (incl. tournament)", 3)):
        v = gapcol(j); print(f"{nm:46} R64 AUC {auc(v[r64], y[r64]):.3f} | all rounds {auc(v[k], y[k]):.3f}")
    names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]; gap = Q.X30[:, names.index("gap")]
    print(f"{'rating gap alone (pre-tournament)':46} R64 AUC {auc(gap[r64], y[r64]):.3f} | all rounds {auc(gap[k], y[k]):.3f}")
