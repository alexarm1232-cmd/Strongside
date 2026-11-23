# Round 1 upset report (no model built). 511 Round of 64 games, outcome = the LOWER seed won. Net rating left out.
# Every team measure as a within-season percentile (all D-I teams), pre-tournament games only (before the First Four).
# Sources: the 246-measure study pool (re-oriented from stronger/weaker to higher/lower seed), basic box stats, Andrew's
# variables, steals+blocks, guard experience, returning minutes, tournament experience, and NEW 3-point volatility from
# game logs: 3PA rate, 3PA per game, 3P%, game-to-game SD of 3P%, hot-game share (3P% >= 40% on 15+ 3PA),
# cold-game share (3P% <= 25% on 15+ 3PA), SD of points scored, SD of margin, most threes made in a game.
import os, sys, json, contextlib, io, math
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
from concurrent.futures import ProcessPoolExecutor
CACHE = os.path.join(HERE, "m186_vol.json")
B = Q.R.B; G = B.G
def _vol(s):
    sys.path.insert(0, Q.OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; L = {}
    for g in games:
        if g["date"] >= first or g["hs"] is None: continue
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            if t not in DI or t not in g["side"] or o not in g["side"]: continue
            a, b = g["side"][t], g["side"][o]
            m = (g["hs"] - g["as_"]) * (1 if t == g["home"] else -1)
            L.setdefault(t, []).append((a["tpm"], a["tpa"], a["fga"], a["pts"], m, a["stl"] + a["blk"]))
    out = {}
    for t, rows in L.items():
        if len(rows) < 10: continue
        A = np.array(rows, float); tpm, tpa, fga, pts, mar = A[:, 0], A[:, 1], A[:, 2], A[:, 3], A[:, 4]
        q = tpa >= 15; p3g = np.where(tpa > 0, tpm / np.maximum(tpa, 1), np.nan)
        out[t] = dict(r3=tpa.sum() / fga.sum(), tpa_pg=tpa.mean(), p3=tpm.sum() / max(tpa.sum(), 1),
                      p3_sd=float(np.nanstd(p3g[tpa >= 10])) if (tpa >= 10).sum() >= 5 else np.nan,
                      hot=float((p3g[q] >= .40).mean()) if q.sum() >= 5 else np.nan, cold=float((p3g[q] <= .25).mean()) if q.sum() >= 5 else np.nan,
                      pts_sd=float(pts.std()), mar_sd=float(mar.std()), max3=float(tpm.max()), hot_vol=float(((tpm >= 12)).mean()))
    return s, out
if __name__ == "__main__":
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_vol, sorted({g["season"] for g in G}))), open(CACHE, "w"))
    VOL = json.load(open(CACHE))
    ns = {"__file__": os.path.join(Q.OLD, "dedup_model.py")}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open(os.path.join(Q.OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
    X, KS = ns["X"], ns["KS"]
    R1 = [i for i, g in enumerate(G) if g["rnd"] == "First round" and g["fseed"] != g["dseed"]]
    rows = []
    for i in R1:
        g = G[i]; a, b = g["fav"], g["dog"]; sa, sb = g["fseed"], g["dseed"]
        H, L_, sH, sL = (a, b, sa, sb) if sa < sb else (b, a, sb, sa); up = int((g["fav_won"] and L_ == a) or (not g["fav_won"] and L_ == b))
        rows.append(dict(i=i, s=g["season"], H=H, L=L_, sH=sH, sL=sL, up=up, HisS=(H == B.Sname[i])))
    n = len(rows); y = np.array([r["up"] for r in rows]); sgap = np.array([r["sL"] - r["sH"] for r in rows], float)
    seas = np.array([r["s"] for r in rows]); early = np.array([int(s[:4]) < 2018 for s in seas])
    F = {}
    # (1) study pool, re-oriented to higher (H) / lower (L) seed
    keys = sorted({k[2:] for k in KS if k[:2] in ("S ", "W ")})
    for k in keys:
        if "S " + k not in KS or "W " + k not in KS or k in ("adj_net", "adj_o", "adj_d"): continue
        sv, wv = X[[r["i"] for r in rows], KS.index("S " + k)], X[[r["i"] for r in rows], KS.index("W " + k)]
        hs = np.array([r["HisS"] for r in rows]); F["H " + k] = np.where(hs, sv, wv); F["L " + k] = np.where(hs, wv, sv)
    # (2) per-team sources -> within-season percentiles among all D-I teams in that source
    def add(src, keys_, label=""):
        for k in keys_:
            for side in "HL":
                v = []
                for r in rows:
                    d = src.get(r["s"], {}); t = r[side]; x = (d.get(t) or d.get(t + ".") or {}).get(k)
                    arr = [vv.get(k) for vv in d.values() if vv.get(k) is not None and vv.get(k) == vv.get(k)]
                    v.append(np.nan if x is None or x != x or not arr else float(np.searchsorted(np.sort(arr), x, side="right") / len(arr)))
                v = np.array(v); v[np.isnan(v)] = 0.5; F[f"{side} {label}{k}"] = v
    add(VOL, ["r3", "tpa_pg", "p3", "p3_sd", "hot", "cold", "pts_sd", "mar_sd", "max3", "hot_vol"], "3pt/vol: ")
    BS = json.load(open(os.path.join(HERE, "m144_basic.json")))
    add(BS, ["ppg", "papg", "margin", "win_pct", "fg_pct", "fg3_pct", "ft_pct", "rpg", "apg", "topg", "spg", "bpg", "opp_fg_pct"], "basic: ")
    for fn, ks, lab in (("m129_pg.json", ["guard_exp", "top2_guard_exp"], "guards: "), ("m135_ret.json", ["returning"], "")):
        add(json.load(open(os.path.join(HERE, fn))), ks, lab)
    # tournament wins last 3 (program experience)
    SEAS = sorted({g["season"] for g in G}); TW = {}
    for g in G:
        if g["rnd"] != "First Four": w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
    for side in "HL":
        F[f"{side} tourney wins last 3"] = np.array([sum(TW.get((p, r[side]), 0) for p in SEAS[max(0, SEAS.index(r["s"]) - 3):SEAS.index(r["s"])]) for r in rows], float)
    def z_of(v, ctrl):
        Xs = np.column_stack(([sgap] if ctrl else []) + [v, np.ones(n)]); w = np.zeros(Xs.shape[1])
        for _ in range(60):
            p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]) + 1e-9 * np.eye(Xs.shape[1]); w += np.linalg.solve(Hm, Xs.T @ (y - p))
        j = 1 if ctrl else 0; return w[j] / math.sqrt(np.linalg.inv(Hm)[j, j])
    def auc(v):
        o = np.argsort(v, kind="mergesort"); rk = np.empty(n); rk[o] = np.arange(1, n + 1); n1 = y.sum(); return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (n - n1))
    res = []
    names = sorted({k[2:] for k in F})
    for k in names:
        for lab, v in (("L", F.get("L " + k)), ("H", F.get("H " + k)), ("L-H", (F["L " + k] - F["H " + k]) if "L " + k in F and "H " + k in F else None)):
            if v is None or np.std(v) == 0: continue
            zc = z_of(v, True); z0 = z_of(v, False)
            ze = z_of(v[early], True) if False else None
            res.append((abs(zc), lab, k, zc, z0, auc(v)))
    res.sort(reverse=True)
    print(f"R64 games {n} | upsets {int(y.sum())} ({y.mean():.1%}) | tests run {len(res)} (about {int(0.046 * len(res))} would pass |z| >= 2 by chance alone)")
    print("\nTOP 40 by z with the seed gap controlled (z>0 = higher value -> more upsets):")
    for _, lab, k, zc, z0, a in res[:40]: print(f"  {lab:4} {k:38} z(seed-controlled) {zc:+.2f} | z(raw) {z0:+.2f} | AUC alone {a:.3f}")
    print("\n3-POINT / VOLATILITY measures:")
    for _, lab, k, zc, z0, a in sorted([r for r in res if r[2].startswith("3pt/vol")], key=lambda r: (r[2], r[1])): print(f"  {lab:4} {k:38} z(seed) {zc:+.2f} | z(raw) {z0:+.2f}")
    # era check for the top 15
    def zsub(v, m):
        Xs = np.column_stack([sgap[m], v[m], np.ones(m.sum())]); w = np.zeros(3); yy = y[m]
        for _ in range(60):
            p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(Hm, Xs.T @ (yy - p))
        return w[1] / math.sqrt(np.linalg.inv(Hm)[1, 1])
    print("\nTOP 15, same sign in both eras? (2010-17 | 2018-26)")
    for _, lab, k, zc, z0, a in res[:15]:
        v = F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
        print(f"  {lab:4} {k:38} {zsub(v, early):+.2f} | {zsub(v, ~early):+.2f}")
    # upset rate by seed line
    print("\nUpset rate by matchup:")
    for h in range(1, 9):
        m = np.array([r["sH"] == h for r in rows]); print(f"  {h} vs {17 - h}: {int(y[m].sum())}/{int(m.sum())} ({y[m].mean():.0%})")
    # High Point 2026 profile vs the 2026 lower seeds
    hp = next(j for j, r in enumerate(rows) if r["s"] == "2025-26" and r["L"] == "High Point")
    m26 = seas == "2025-26"
    print("\nHigh Point 2026 (lower seed) on the top measures: its value, and its rank among the 32 lower seeds in 2026")
    for _, lab, k, zc, z0, a in res[:20] + [r for r in res if r[2].startswith("3pt/vol") and r[1] == "L"]:
        v = F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
        rk = int((v[m26] > v[hp]).sum()) + 1 if zc > 0 else int((v[m26] < v[hp]).sum()) + 1
        print(f"  {lab:4} {k:38} value {v[hp]:+.2f} | rank {rk} of 32 in the upset direction (z {zc:+.2f})")
    json.dump({"F": {k: v.tolist() for k, v in F.items()}, "rows": rows, "y": y.tolist()}, open(os.path.join(HERE, "m186_r64_features.json"), "w"))
