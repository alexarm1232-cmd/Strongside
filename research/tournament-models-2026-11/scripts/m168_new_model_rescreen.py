# New model: sos gap + rating gap x pace + the 27 measures (29 inputs), corrected 2010-11 steals/blocks.
# (a) every candidate measure: report z before vs after the fix (study_results.json)
# (b) every candidate measure not in the model: z on top of the new strength inputs (sos gap, gap x pace); any |z| >= 2
#     goes into the model one at a time (exact 756 pipeline, each tournament held out)
# (c) steals + blocks per game ("stocks") made and allowed, each team and the gap, from the corrected box scores
import os, sys, json, contextlib, io, shutil
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import m99_model_types as Q
OLD = Q.OLD
ns = {"__file__": os.path.join(OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS = ns["X"], ns["KS"]
m27 = [str(n) for n in np.load(os.path.join(OLD, "_before_stl_fix", "m3_data.npz"), allow_pickle=True)["names"]][3:]
NAMES = ["sos gap", "gap x possessions"] + m27
XM = np.column_stack([X[:, KS.index(n)] for n in NAMES]); STRC = XM[:, :2]
k = ~Q.FF; RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
def zt(v):
    Xs = np.column_stack([STRC[k], v[k], np.ones(k.sum())]); yy = Q.yb[k].astype(float); w = np.zeros(Xs.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-Xs @ w)); H = Xs.T @ (Xs * (p * (1 - p))[:, None]); w += np.linalg.solve(H, Xs.T @ (yy - p))
    return w[2] / np.sqrt(np.linalg.inv(H)[2, 2])
# (c) stocks from m144's per-team per-game box averages (rebuilt from the corrected box scores)
B = Q.R.B; G = B.G; Wn = [g["dog"] if s == g["fav"] else g["fav"] for g, s in zip(G, B.Sname)]
BS = json.load(open(os.path.join(HERE, "m144_basic.json")))
TOT = json.load(open(os.path.join(HERE, "m148_andrew_tot.json"))) if os.path.exists(os.path.join(HERE, "m148_andrew_tot.json")) else None
def pct_of(vals, x): arr = np.sort(vals); return float(np.searchsorted(arr, x, side="right") / len(arr))
def stocks(s, t, allowed):
    d = BS[s]; v = d.get(t) or d.get(t + ".") or d.get(t.rstrip("."))
    return None if v is None else (v["spg"] + v["bpg"]) if not allowed else None
EXTRA = {}
# allowed stocks need opponent steals/blocks per game: recompute from the corrected box scores
def _allowed(s):
    sys.path.insert(0, OLD); import upset_data as U
    games, td = U.load(s[2:4] + s[5:7]); first = min((g["date"] for g in games if g["ncaa"]), default="9999")
    DI = set(td) | {t.rstrip(".") for t in td}; T = {}
    for g in games:
        if g["date"] >= first or g["home"] not in DI or g["away"] not in DI: continue
        for t, o in ((g["home"], g["away"]), (g["away"], g["home"])):
            a, b = g["side"][t], g["side"][o]; r = T.setdefault(t, [0, 0.0, 0.0])
            r[0] += 1; r[1] += a["stl"] + a["blk"]; r[2] += b["stl"] + b["blk"]
    return s, {t: (r[1] / r[0], r[2] / r[0]) for t, r in T.items() if r[0] >= 10}
def job(args):
    name, extra = args; XX = XM if extra is None else np.column_stack([XM, extra])
    fit = Q.t_ridge(X=XX); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = Q.run(m_tr, tr, m_te, tr, Q.EX)
    yk = Q.yb[k]; held = int(((out[k] > 0) == yk).sum()); insr = int(((ins > 0) == yk).sum())
    s_ = out[k]; y_ = yk.astype(int); o = np.argsort(s_); rk = np.empty(len(s_)); rk[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); auc = (rk[y_ == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y_) - n1))
    rr = [int(((out[k & (Q.RND == r)] > 0) == Q.yb[k & (Q.RND == r)]).sum()) for r in RN]
    return name, held, insr, auc, rr
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    # save the adopted model's inputs as m3_data.npz (re-selected version kept as m3_data_reselected26.npz)
    dst = os.path.join(OLD, "m3_data.npz"); keep = os.path.join(OLD, "m3_data_reselected26.npz")
    if not os.path.exists(keep): shutil.copy(dst, keep)
    old = dict(np.load(dst, allow_pickle=True)); old["X"] = XM; old["names"] = np.array(NAMES); np.savez(dst, **old)
    print("adopted model saved:", len(NAMES), "inputs (sos gap, gap x pace + 27 measures)")
    # (a)
    zo = {**{"S " + r["key"]: r["z"] for r in json.load(open(os.path.join(OLD, "_before_stl_fix", "study_results.json")))["fav"]},
          **{"W " + r["key"]: r["z"] for r in json.load(open(os.path.join(OLD, "_before_stl_fix", "study_results.json")))["dog"]}}
    Rn = json.load(open(os.path.join(OLD, "study_results.json")))
    zn = {**{"S " + r["key"]: r["z"] for r in Rn["fav"]}, **{"W " + r["key"]: r["z"] for r in Rn["dog"]}}
    moved = sorted(((abs(zn[c] - zo[c]), c) for c in zn if c in zo and abs(zn[c] - zo[c]) >= 0.05), reverse=True)
    print(f"\n(a) report z: {len(moved)} of {len(zn)} measures moved by 0.05 or more; all of them:")
    for _, c in moved: print(f"   {c:30} {zo[c]:+.2f} -> {zn[c]:+.2f}{'   (in model)' if c in m27 else ''}")
    # (b)
    cand = [c for c in range(len(KS)) if KS[c] not in NAMES and KS[c] not in ("gap",) and X[:, c].std() > 0]
    Z = sorted(((zt(X[:, c]), KS[c]) for c in cand), key=lambda t: -abs(t[0]))
    sig = [(z, n) for z, n in Z if abs(z) >= 2]
    print(f"\n(b) {len(cand)} candidate measures not in the model; |z| >= 2 on top of sos gap + gap x pace: {len(sig)}")
    for z, n in Z[:25]: print(f"   {n:30} z {z:+.2f}")
    # (c)
    with ProcessPoolExecutor(6) as ex: AL = dict(ex.map(_allowed, sorted({g["season"] for g in G})))
    def col(i_side, j):
        out = np.full(Q.N, 0.5)
        for i, g in enumerate(G):
            s = g["season"]; t = B.Sname[i] if i_side == "S" else Wn[i]; d = AL[s]; v = d.get(t) or d.get(t + ".") or d.get(t.rstrip("."))
            if v: out[i] = pct_of([x[j] for x in d.values()], v[j])
        return out
    ST = {"S stocks per game": col("S", 0), "W stocks per game": col("W", 0), "S stocks allowed per game": col("S", 1), "W stocks allowed per game": col("W", 1)}
    ST["stocks gap (S - W)"] = ST["S stocks per game"] - ST["W stocks per game"]; ST["stocks allowed gap (S - W)"] = ST["S stocks allowed per game"] - ST["W stocks allowed per game"]
    for s_ in ("2009-10", "2010-11", "2011-12"): print(f"   check {s_}: D-I avg steals+blocks per game {np.mean([v[0] for v in AL[s_].values()]):.2f}")
    print("\n(c) steals + blocks per game, z on top of sos gap + gap x pace:")
    for n, v in ST.items(): print(f"   {n:28} z {zt(v):+.2f}")
    jobs = [("NEW MODEL: gap x pace only (29)", None)] + [(f"+ {n}", np.array([X[:, KS.index(n)]]).T) for z, n in sig]
    jobs += [("+ stocks per game (S, W)", np.column_stack([ST["S stocks per game"], ST["W stocks per game"]])),
             ("+ stocks allowed per game (S, W)", np.column_stack([ST["S stocks allowed per game"], ST["W stocks allowed per game"]])),
             ("+ stocks gap + stocks allowed gap", np.column_stack([ST["stocks gap (S - W)"], ST["stocks allowed gap (S - W)"]]))]
    print()
    with ProcessPoolExecutor(6) as ex:
        for name, held, insr, auc, rr in ex.map(job, jobs):
            print(f"{name:40} held {held} | in-sample {insr} | overfit {insr-held:+d} | AUC {auc:.4f} | by round {'/'.join(map(str, rr))}", flush=True)
