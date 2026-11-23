# Round of 32 optimization, round 3 (everything pre-tournament; benchmark = model 1 rebuilt pre-tournament, variant G):
#  1. candidates vs pre-tournament model 1: alone, averaged with it, and as an upset override on top of it
#  2. style clusters (k-means on play-type mix, tempo, 3-point rate) for each side, screened
#  3. pairwise interactions among the candidate inputs, screened (beyond model 1 pre + simulator)
#  4. honest nested check: the whole selection (significant style measures + matchups + coach) redone inside each held-out year
import os, sys, json, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m260_r32_matchups.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("# (c) model 1 + upset override")])
import numpy as np
mp = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))[gi]; sp_all = 1 / (1 + np.exp(np.where(hsS, mp, -mp))); sp = sp_all[idx]
print(f"Round of 32: model 1 pre-tournament {right(sp >= .5)} (was {right(su >= .5)} with game-day lineups) | higher seed {right(np.zeros(nS) >= .5)} | simulator (game-day lineups) {right(si >= .5)}")
COACH2 = ["L coach car_s16", "L-H coach rec5_s16"]
CANDS = {"core 12 + coach + matchups": U(CORE12, COACH2, mk_), "kept 16 + matchups": U(KEPT16, mk_), "core 12 + matchups": U(CORE12, mk_), "core 12 + coach": U(CORE12, COACH2), "kept 16": KEPT16}
print("\n1. vs pre-tournament model 1 (held out). alone @40 | avg with M1-pre: best cutoff | override (M1-pre >= 50% OR R32 >= t)")
for lab, names in CANDS.items():
    _, ph, _, _ = evaluate(names); a2 = (ph + sp) / 2; b2 = max(range(35, 56), key=lambda c: right(a2 >= c / 100))
    ov = " ".join(f"{int(t * 100)}%:{right((sp >= .5) | (ph >= t))}" for t in (.45, .5, .55, .6))
    print(f"   {lab:32} AUC {auc(ph, ys):.3f} alone {right(ph >= .4)} | avg2 AUC {auc(a2, ys):.3f} {right(a2 >= b2 / 100)}@{b2} ({right(a2 >= .45)}@45 {right(a2 >= .5)}@50) | override {ov} | r with M1-pre {np.corrcoef(ph, sp)[0, 1]:+.2f}")
# 2. style clusters
SKc = [c for c in NM if c.startswith("H pt_share ")] ; SKc = [c[2:] for c in SKc] + ["tempo", "3pt/vol: r3"]
SKc = [c for c in SKc if ("H " + c) in NM and ("L " + c) in NM]
V = np.vstack([np.column_stack([col("H " + c) for c in SKc]), np.column_stack([col("L " + c) for c in SKc])]); Vz = (V - V.mean(0)) / (V.std(0) + 1e-9)
print(f"\n2. style clusters (k-means on {len(SKc)} style measures, both teams pooled)")
for K in (4, 6, 8):
    best = None
    for seed in range(10):
        rng = np.random.default_rng(seed); Cc = Vz[rng.choice(len(Vz), K, replace=False)]
        for _ in range(100):
            lab_ = np.argmin(((Vz[:, None, :] - Cc[None]) ** 2).sum(2), 1); Cc = np.array([Vz[lab_ == c].mean(0) if (lab_ == c).any() else Cc[c] for c in range(K)])
        wss = ((Vz - Cc[lab_]) ** 2).sum()
        if best is None or wss < best[0]: best = (wss, lab_, Cc)
    lab_ = best[1]; hl, ll = lab_[:nS], lab_[nS:]
    res = []
    for c in range(K):
        for side, arr in (("higher", hl), ("lower", ll)):
            v = (arr == c).astype(float)
            if v.sum() < 8: continue
            res.append((wald(v, ys, allm, [sg]), wald(v, ys, allm, [sg, lg(sp), lg(si)]), f"{side} seed in cluster {c} ({int(v.sum())} games)"))
        v = ((hl == c) & (ll != c)).astype(float) - ((ll == c) & (hl != c)).astype(float)
    res.sort(key=lambda t: -abs(t[0]))
    print(f"   K={K}: " + "; ".join(f"{t[2]} z {t[0]:+.2f} beyond {t[1]:+.2f}" for t in res[:4]))
    top = Cc = best[2]
    for c in range(K):
        prof = sorted(zip(SKc, top[c]), key=lambda t: -abs(t[1]))[:3]
        if any(abs(t[0]) >= 2 and str(c) in t[2].split("cluster ")[1][:2] for t in res[:4]): print(f"      cluster {c}: " + ", ".join(f"{n} {v:+.1f}" for n, v in prof))
# 3. pairwise interactions
base_in = U(CORE12, COACH2)
INT = {}
for a_i in range(len(base_in)):
    for b_i in range(a_i + 1, len(base_in)):
        a, b = base_in[a_i], base_in[b_i]; INT[f"{nice(a)} x {nice(b)}"] = zsd(col(a)) * zsd(col(b))
ir = []
for c, v in INT.items():
    try: ir.append((c, wald(v, ys, allm, [sg]), wald(v, ys, allm, [sg, lg(sp), lg(si)]), wald(v, ys, early, [sg]), wald(v, ys, ~early, [sg])))
    except Exception: pass
ir.sort(key=lambda t: -max(abs(t[1]), abs(t[2])))
print(f"\n3. {len(ir)} pairwise interactions: {sum(abs(t[1]) >= 2 for t in ir)} at |z|>=2, {sum(abs(t[2]) >= 2 for t in ir)} beyond (~{round(len(ir) * .046)} by chance). Top 8:")
for c, a, b, e1, e2 in ir[:8]: print(f"   {c[:90]:90} {a:+.2f} | beyond {b:+.2f} | {e1:+.1f} {e2:+.1f}")
isig = [c for c, a, b, e1, e2 in ir if abs(a) >= 2.5 and np.sign(e1) == np.sign(e2)]
if isig:
    for c in isig: POOL["INT " + c] = INT[c]
    NM = list(POOL); PX = np.column_stack([POOL[c] for c in NM])
    print(HDR); report("core 12 + coach + matchups + strong interactions", U(CANDS["core 12 + coach + matchups"], ["INT " + c for c in isig]))
# 4. honest nested selection
print("\n4. honest check: whole selection redone inside each held-out year (style |z|>=2 seed or beyond, net-linked out, overlap 0.3; matchups |z|>=2 same sign both halves; coach |z|>=2)")
ELIG = [c for c in NM if not STRENGTH.search(c) and not c.startswith("INT ") and abs(np.corrcoef(col(c), rg)[0, 1]) < .3]
def select(tr):
    yrs = sorted(set(Ss[tr])); h1 = tr & np.isin(Ss, yrs[:len(yrs) // 2]); h2 = tr & ~h1
    zs = {}
    for c in ELIG:
        try:
            a = wald(col(c), ys, tr, [sg]); b = wald(col(c), ys, tr, [sg, lg(sp), lg(si)])
            if max(abs(a), abs(b)) >= 2: zs[c] = (a, b)
        except Exception: pass
    keep = []
    for c in sorted(zs, key=lambda c: -max(abs(zs[c][0]), abs(zs[c][1]))):
        if c.startswith("MU "):
            try:
                if np.sign(wald(col(c), ys, h1, [sg])) != np.sign(zs[c][0]) or np.sign(wald(col(c), ys, h2, [sg])) != np.sign(zs[c][0]): continue
            except Exception: continue
        if all(abs(np.corrcoef(col(c)[tr], col(k)[tr])[0, 1]) < .3 for k in keep): keep.append(c)
    return keep
ph = np.zeros(nS); ks = []
for s in SEASONS:
    tr, te = Ss != s, Ss == s; sel = select(tr); ks.append(len(sel)); f, _ = fit(np.column_stack([col(c) for c in sel])[tr], ys[tr], Ws[tr]); ph[te] = f(np.column_stack([col(c) for c in sel])[te])
a2 = (ph + sp) / 2
print(f"   inputs per fold ~{np.mean(ks):.0f} | held-out AUC {auc(ph, ys):.3f} | right @40 {right(ph >= .4)} @50 {right(ph >= .5)} | avg with M1-pre AUC {auc(a2, ys):.3f} @45 {right(a2 >= .45)} @50 {right(a2 >= .5)}")
json.dump({"sp": sp.tolist(), "honest": ph.tolist()}, open(os.path.join(HERE, "m264_out.json"), "w"))
