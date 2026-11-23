# Follow-ups on the 14-16 seed traits, each tested on ALL 511 Round of 64 games (and on the 192 games with a 14-16 seed):
#  (1) steals vs turnovers forced: how alike they are, and swapping them in the Upset Model
#  (2) supporting-cast BPM: minutes-weighted BPM of 10+ mpg players after removing the top 2 (by minutes, or by BPM),
#      tested in place of the Upset Model's depth gap
#  (3) first-half and second-half margin in CLOSE games over the season (within 10 / within 5 at the end of regulation)
#  (4) three-point measures, all of them, plus a few matchups
# Upset Model = the locked 28 inputs (391/511 at 40%, AUC 0.790), each year held out, same ridge as m188.
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from concurrent.futures import ProcessPoolExecutor
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
ROOT = r"C:\Users\crtra\Downloads\basketball"
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
n = len(rows); seas = np.array([r["s"] for r in rows]); sL = np.array([r["sL"] for r in rows]); sg = np.array([r["sL"] - r["sH"] for r in rows], float)
U = json.load(open(os.path.join(HERE, "m188_out.json")))["inputs"]
kk = lambda s: (s or "").rstrip(". ")
CACHE = os.path.join(HERE, "m210_halves.json")

def _halves(s):
    sys.path.insert(0, OLD); import upset_data as UD
    want = {kk(r["H"]) for r in rows if r["s"] == s} | {kk(r["L"]) for r in rows if r["s"] == s}
    games, _ = UD.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    acc = {}
    for g in games:
        if g["date"] >= first or not g["pbp"] or not ({g["home"], g["away"]} & want): continue
        try: plays = json.load(open(g["pbp"], encoding="utf-8"))["plays"]
        except Exception: continue
        if len(plays) < 60: continue
        h1 = reg = None; hs = as_ = 0
        for p in plays:
            per = p.get("period", 1)
            if per >= 2 and h1 is None: h1 = hs - as_
            if per >= 3 and reg is None: reg = hs - as_
            if p.get("home_score") is not None and p.get("away_score") is not None: hs, as_ = p["home_score"], p["away_score"]
        if h1 is None: continue
        if reg is None: reg = hs - as_
        for t, sign in ((g["home"], 1), (g["away"], -1)):
            if t not in want: continue
            a = acc.setdefault(t, [])
            a.append((sign * h1, sign * (reg - h1), sign * (hs - as_)))
    out = {}
    for t, L in acc.items():
        A = np.array(L, float); h1, h2, fin = A[:, 0], A[:, 1], A[:, 2]; reg = h1 + h2; d = {"n": len(A)}
        for nm, m in (("all", np.ones(len(A), bool)), ("c10", np.abs(reg) <= 10), ("c5", np.abs(reg) <= 5)):
            if m.sum() >= 4:
                d[nm + "_h1"] = float(h1[m].mean()); d[nm + "_h2"] = float(h2[m].mean()); d[nm + "_n"] = int(m.sum())
                d[nm + "_win"] = float((fin[m] > 0).mean()); d[nm + "_share"] = float(m.mean())
        out[t] = d
    return s, out

def ridge(Xtr, ytr, w, lam=30.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A = np.column_stack([(Xtr - mu) / sd, np.ones(len(Xtr))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(60):
        p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (w * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (w * (ytr - p)) - P @ b)
    return lambda Xq: np.column_stack([(Xq - mu) / sd, np.ones(len(Xq))]) @ b
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
def zc(v, m=None, ctrl=True):
    m = np.ones(n, bool) if m is None else m; vv = (v[m] - v[m].mean()) / (v[m].std() + 1e-12)
    Xs = np.column_stack(([sg[m]] if ctrl else []) + [vv, np.ones(m.sum())]); w = np.zeros(Xs.shape[1]); yy = y[m]
    for _ in range(60):
        p = 1 / (1 + np.exp(-Xs @ w)); Hm = Xs.T @ (Xs * (p * (1 - p))[:, None]) + 1e-9 * np.eye(Xs.shape[1]); w += np.linalg.solve(Hm, Xs.T @ (yy - p))
    j = 1 if ctrl else 0; return w[j] / math.sqrt(np.linalg.inv(Hm)[j, j])
def mw(v, m):
    a, b = v[m & (y == 1)], v[m & (y == 0)]; allv = np.concatenate([a, b]); r = np.argsort(np.argsort(allv)) + 1
    U_ = r[:len(a)].sum() - len(a) * (len(a) + 1) / 2; return (U_ - len(a) * len(b) / 2) / math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12)
def col(name):
    lab, k = name.split(" ", 1); return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]

if __name__ == "__main__":
    import m99_model_types as Q
    W = Q.WT[[r["i"] for r in rows]]
    def run(ins):
        X = np.column_stack([col(c) for c in ins]); out = np.zeros(n)
        for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
        return int(((out >= .4) == (y == 1)).sum()), auc(out, y), int((out >= .4).sum()), int(((out >= .4) & (y == 1)).sum())
    base = run(U); big = sL >= 14
    def line(name, v=None):
        v = col(name) if v is None else v
        return f"{name:44} all R64: z {zc(v):+.2f} (seed controlled), AUC alone {auc(v, y):.3f} | 14-16 seeds: z {mw(v, big):+.2f}"
    def model(label, ins):
        r = run(ins); return f"   {label:58} right {r[0]}/511 ({r[0] - base[0]:+d}) | AUC {r[1]:.3f} | upset picks {r[2]} ({r[3]} hit)"
    print(f"Upset Model as locked: right {base[0]}/511 at 40% | AUC {base[1]:.3f} | upset picks {base[2]} ({base[3]} hit)")

    # (1) steals vs turnovers forced
    print("\n=== (1) STEALS vs TURNOVERS FORCED (underdog) ===")
    for a, b in (("L stl", "L d_tov"), ("L basic: spg", "L d_tov"), ("L stl", "L basic: spg"), ("L d_nst_to", "L stl")):
        if a.split(" ", 1)[1] and ("L " + a.split(" ", 1)[1]) in F and ("L " + b.split(" ", 1)[1]) in F: print(f"   r({a}, {b}) = {np.corrcoef(col(a), col(b))[0, 1]:+.2f}")
    for nm in ("L d_tov", "L stl", "L basic: spg", "L d_nst_to", "L-H d_tov", "L-H stl", "L-H basic: spg"):
        if ("L " + nm.split(" ", 1)[1]) in F: print("   " + line(nm))
    rep = lambda old, new: [new if c == old else c for c in U]
    print(model("swap L d_tov -> L stl (steals per possession)", rep("L d_tov", "L stl")))
    print(model("swap L d_tov -> L basic: spg (steals per game)", rep("L d_tov", "L basic: spg")))
    print(model("keep L d_tov, add L stl", U + ["L stl"]))
    print(model("keep L d_tov, add L basic: spg", U + ["L basic: spg"]))
    if "L d_nst_to" in F: print(model("split: L stl + L d_nst_to (non-steal turnovers forced)", rep("L d_tov", "L stl") + ["L d_nst_to"]))

    # (2) supporting-cast BPM from the simulator's pre-game player lines
    t = open(os.path.join(ROOT, "dashboard", "tourneyreport.js"), encoding="utf-8").read()
    T = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1]); live = T["inputs"]["live"]
    PL = {}
    for gi, entry in enumerate(live):
        g = T["games"][gi]
        for nm, blk in ((kk(g[3]), entry[1]), (kk(g[4]), entry[2])): PL[(str(g[9]), nm)] = np.array(blk[1], float)
    G = Q.R.B.G
    def cast(P, how):
        g_, mins, bpm = P[:, 0], P[:, 1], P[:, 2]; mpg = mins / np.maximum(g_, 1); rot = np.where(mpg >= 10)[0]
        if len(rot) < 3: return np.nan
        top = rot[np.argsort(-mins[rot])[:2]] if how == "min" else rot[np.argsort(-bpm[rot])[:2]]
        rest = np.setdiff1d(rot, top); return float(np.average(bpm[rest], weights=mins[rest])) if len(rest) else np.nan
    miss = 0
    for how, lab in (("min", "cast_bpm (no top-2 minutes)"), ("bpm", "cast_bpm (no top-2 BPM)")):
        for side in "HL":
            v = []
            for r in rows:
                P = PL.get((str(G[r["i"]]["gid"]), kk(r[side])))
                v.append(cast(P, how) if P is not None and P.ndim == 2 else np.nan)
            v = np.array(v); miss += int(np.isnan(v).sum()); v[np.isnan(v)] = np.nanmean(v); F[f"{side} {lab}"] = v
    print(f"\n=== (2) SUPPORTING-CAST BPM: 10+ min players minus the top 2 (missing filled with the mean: {miss}) ===")
    for nm in ("L-H depth_bpm", "L starters_bpm", "L-H cast_bpm (no top-2 minutes)", "L cast_bpm (no top-2 minutes)", "H cast_bpm (no top-2 minutes)",
               "L-H cast_bpm (no top-2 BPM)", "L cast_bpm (no top-2 BPM)", "H cast_bpm (no top-2 BPM)"):
        print("   " + line(nm))
    print(f"   r(L-H cast_bpm minutes, L-H depth_bpm) = {np.corrcoef(col('L-H cast_bpm (no top-2 minutes)'), col('L-H depth_bpm'))[0, 1]:+.2f}")
    print(model("swap depth gap -> cast BPM gap (top 2 by minutes out)", rep("L-H depth_bpm", "L-H cast_bpm (no top-2 minutes)")))
    print(model("swap depth gap -> cast BPM gap (top 2 by BPM out)", rep("L-H depth_bpm", "L-H cast_bpm (no top-2 BPM)")))
    print(model("swap depth gap -> L cast BPM (top 2 by minutes out)", rep("L-H depth_bpm", "L cast_bpm (no top-2 minutes)")))

    # (3) close-game halves
    if not os.path.exists(CACHE):
        with ProcessPoolExecutor(6) as ex: json.dump(dict(ex.map(_halves, sorted(set(seas)))), open(CACHE, "w"))
    HV = json.load(open(CACHE)); keys = ["all_h1", "all_h2", "c10_h1", "c10_h2", "c10_win", "c10_share", "c5_h1", "c5_h2", "c5_win"]
    for kx in keys:
        for side in "HL":
            v = np.array([(HV.get(r["s"], {}).get(kk(r[side])) or {}).get(kx, np.nan) for r in rows], float)
            v[np.isnan(v)] = np.nanmean(v); F[f"{side} half: {kx}"] = v
    cnt = np.array([(HV.get(r["s"], {}).get(kk(r["L"])) or {}).get("c10_n", 0) for r in rows])
    print(f"\n=== (3) HALF MARGINS IN CLOSE GAMES (pre-tournament; close = within 10 / within 5 at end of regulation; underdogs avg {cnt.mean():.1f} close-10 games) ===")
    print("   averages, points per game:   winners (upsets) vs losers, all 511 | 14-16 seeds")
    for kx in keys:
        for lab in ("L", "H", "L-H"):
            v = col(f"{lab} half: {kx}")
            print(f"   {lab:3} {kx:9} {v[y == 1].mean():+6.2f} vs {v[y == 0].mean():+6.2f} | z {zc(v):+.2f} (seed controlled) | 14-16: {v[big & (y == 1)].mean():+6.2f} vs {v[big & (y == 0)].mean():+6.2f}, z {mw(v, big):+.2f}")
    for nm in ("L-H half: c10_h1", "L-H half: c10_h2", "H half: c10_h2", "L half: c10_h1", "L-H half: c5_h2", "H half: c5_h2"):
        print(model("add " + nm, U + [nm]))
    print(model("add L-H c10_h1 + L-H c10_h2", U + ["L-H half: c10_h1", "L-H half: c10_h2"]))

    # (4) threes
    print("\n=== (4) THREE-POINT MEASURES (all R64, z with the seed gap controlled; 14-16 Mann-Whitney z) ===")
    tk = sorted({k[2:] for k in F if any(s in k for s in ("p3", "r3", "pts3", "3pt/vol", "fg3", "three", "Pick & Pop", "Drive & Kick"))})
    F["H 3pt streak (hot+cold)"] = F["H 3pt/vol: hot"] + F["H 3pt/vol: cold"]; F["L 3pt streak (hot+cold)"] = F["L 3pt/vol: hot"] + F["L 3pt/vol: cold"]
    F["L 3pt matchup: L r3 + H d_p3"] = F["L r3"] + F["H d_p3"]; F["H 3pt matchup: L r3 + H d_p3"] = F["L 3pt matchup: L r3 + H d_p3"]
    F["L 3pt matchup: L p3 - H d_p3"] = F["L p3"] - F["H d_p3"]; F["H 3pt matchup: L p3 - H d_p3"] = F["L 3pt matchup: L p3 - H d_p3"]
    F["H 3pt matchup: H r3 + L d_p3"] = F["H r3"] + F["L d_p3"]; F["L 3pt matchup: H r3 + L d_p3"] = F["H 3pt matchup: H r3 + L d_p3"]
    F["H 3pt reliance x cold"] = F["H pts3"] * F["H 3pt/vol: cold"]; F["L 3pt reliance x cold"] = F["H 3pt reliance x cold"]
    tk += ["3pt streak (hot+cold)", "3pt matchup: L r3 + H d_p3", "3pt matchup: L p3 - H d_p3", "3pt matchup: H r3 + L d_p3", "3pt reliance x cold"]
    used = {c.split(" ", 1)[1] for c in U}; res = []
    for k in tk:
        for lab in ("L", "H", "L-H"):
            if lab == "L-H" and k.startswith("3pt matchup") or (lab == "L" and k in ("3pt matchup: H r3 + L d_p3", "3pt reliance x cold")) or (lab == "H" and k.startswith("3pt matchup: L")): continue
            if ("L " + k) not in F: continue
            v = col(f"{lab} {k}")
            if v.std() == 0: continue
            res.append((abs(zc(v)), f"{lab} {k}", zc(v), mw(v, big), k in used))
    res.sort(reverse=True)
    for _, nm, z, z2, u in res[:30]: print(f"   {nm:46} z {z:+.2f} | 14-16 z {z2:+.2f}{'  (already in model)' if u else ''}")
    print(f"   ({len(res)} three-point tests; about {int(len(res) * .046)} pass |z| >= 2 by chance)")
    for _, nm, z, z2, u in [r for r in res if not r[4]][:6]: print(model("add " + nm, U + [nm]))
