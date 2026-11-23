# Do lower seeds from stronger conferences win more than expected? Real Round 1 (511) and Round of 32 (256) games.
# Conference strength = average pre-tournament net rating of every team in the conference that season.
import os, sys, json, glob, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
ROOT = r"C:\Users\crtra\Downloads\basketball\data\seasons"
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
U31 = json.load(open(os.path.join(HERE, "m230_out.json"))); pho = np.array(U31["p_heldout"])
CONF = {}; CSTR = {}
for s in sorted({r["s"] for r in rows}):
    code = s[2:4] + s[5:7]; nets = {}
    for p in glob.glob(os.path.join(r"C:\Users\crtra\Downloads\basketball\data\seasons", code, "*", "*")):
        if not os.path.isdir(p): continue
        conf = os.path.basename(os.path.dirname(p)); t = kk(os.path.basename(p)); CONF[(s, t)] = conf
        v = next((Q.TM[s][x]["adj_net"] for x in Q.TM.get(s, {}) if kk(x) == t), None)
        if v is not None: nets.setdefault(conf, []).append(v)
    for c, v in nets.items(): CSTR[(s, c)] = float(np.mean(v))
print("conf map", len(CONF), "conf strengths", len(CSTR), list(CONF.items())[:2], list(Q.TM["2018-19"])[:3], sorted({r["s"] for r in rows})[:2])
cs = lambda s, t: CSTR.get((s, CONF.get((s, kk(t)))), np.nan)
def tiers(vals):
    return np.digitize(vals, [np.nanpercentile(vals, 33), np.nanpercentile(vals, 67)])
def zfit(v, yy, controls):
    X = np.column_stack([np.ones(len(yy))] + controls + [(v - np.nanmean(v)) / np.nanstd(v)]); b = np.zeros(X.shape[1])
    for _ in range(40):
        q = 1 / (1 + np.exp(-X @ b)); H_ = X.T @ (X * (q * (1 - q))[:, None]) + 1e-6 * np.eye(X.shape[1]); b += np.linalg.solve(H_, X.T @ (yy - q))
    return b[-1] / np.sqrt(np.linalg.inv(H_)[-1, -1])
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
# ---------- Round 1
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1)))   # regular model (pre-tournament) chance of the upset
Lc = np.array([cs(r["s"], r["L"]) for r in rows]); Hc = np.array([cs(r["s"], r["H"]) for r in rows]); ok = np.isfinite(Lc) & np.isfinite(Hc)
sgv = np.array([np.log(r["sL"] / r["sH"]) for r in rows])
print(f"ROUND 1: {int(ok.sum())} of {len(rows)} games with conference data")
T = tiers(Lc[ok]); TN = ["weak conference", "middle", "strong conference"]
print(f"{'lower seed from':20} | games | upsets | rate | regular model expected | upset model expected")
for k_ in range(3):
    m = np.zeros(len(rows), bool); m[np.where(ok)[0][T == k_]] = True
    print(f"{TN[k_]:20} | {int(m.sum()):5} | {int(y[m].sum()):6} | {y[m].mean():.3f} | {s_up[m].mean():.3f} | {pho[m].mean():.3f}")
for lab, v in (("lower seed's conference strength", Lc), ("gap (lower minus higher seed's conference)", Lc - Hc)):
    print(f"  {lab}: z beyond seed {zfit(v[ok], y[ok], [sgv[ok]]):+.2f} | beyond regular model {zfit(v[ok], y[ok], [lg(s_up[ok])]):+.2f} | beyond upset model {zfit(v[ok], y[ok], [lg(pho[ok])]):+.2f}")
# by seed line, strong vs weak conference lower seeds
print("  by matchup (lower seed from strong half vs weak half of conferences): upset rate strong | weak")
med = np.nanmedian(Lc)
for h in range(1, 9):
    m = ok & (np.array([r["sL"] for r in rows]) == 17 - h)
    a, b = m & (Lc >= med), m & (Lc < med)
    print(f"    {h} v {17 - h}: {y[a].mean() if a.any() else float('nan'):.2f} ({int(a.sum())}) | {y[b].mean() if b.any() else float('nan'):.2f} ({int(b.sum())})")
# ---------- Round of 32
src = open(os.path.join(HERE, "m266_r32_tune.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("WS = [")])
INS = U(KEPT16, COACH2, mk_); _, ph32, _, _ = evaluate(INS, 10.0)
rw = [rows[i] for i in idx]
Lc2 = np.array([cs(r["s"], r["L"]) for r in rw]); Hc2 = np.array([cs(r["s"], r["H"]) for r in rw]); ok2 = np.isfinite(Lc2) & np.isfinite(Hc2)
sg2 = np.array([np.log(r["sL"] / r["sH"]) for r in rw])
print(f"\nROUND OF 32: {int(ok2.sum())} of {len(rw)} games")
T2 = tiers(Lc2[ok2])
print(f"{'lower seed from':20} | games | upsets | rate | regular model expected | R32 upset model expected")
for k_ in range(3):
    m = np.zeros(len(rw), bool); m[np.where(ok2)[0][T2 == k_]] = True
    print(f"{TN[k_]:20} | {int(m.sum()):5} | {int(ys[m].sum()):6} | {ys[m].mean():.3f} | {sp[m].mean():.3f} | {ph32[m].mean():.3f}")
for lab, v in (("lower seed's conference strength", Lc2), ("gap (lower minus higher seed's conference)", Lc2 - Hc2)):
    print(f"  {lab}: z beyond seed {zfit(v[ok2], ys[ok2].astype(float), [sg2[ok2]]):+.2f} | beyond regular model {zfit(v[ok2], ys[ok2].astype(float), [lg(sp[ok2])]):+.2f} | beyond R32 upset model {zfit(v[ok2], ys[ok2].astype(float), [lg(ph32[ok2])]):+.2f}")


