# Round of 32 Upset Model candidates, built like the Round 1 Upset Model:
#   inputs = higher-seed / lower-seed / gap style measures only (no seed, no net rating, no strength stand-ins), pre-tournament only;
#   outcome = lower seed wins; ridge logistic penalty 30, half-life-12 season weights; scored fit-all, each year held out,
#   forward (fit 2010-17 -> 2018-26) and backward; average of 3 (with model 1 + simulator).
# Side test only (NOT model inputs - brackets are filled before Round 1): Round 1 box-score features.
import os, sys, json, math, re, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m256_r32_report.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("R = []")])
import numpy as np
REP = {d["c"]: d for d in json.load(open(os.path.join(HERE, "m256_report.json")))}
# ---- coach measures (pre-tournament)
CF = np.load(os.path.join(Q.OLD, "coach_feats.npy")); CC = json.load(open(os.path.join(Q.OLD, "coach_cols.json")))
for k in sorted({c.split(" ", 1)[1] for c in CC}):
    hv, lv = [], []
    for i in idx:
        r = rows[i]; g = G[r["i"]]; Hfav = r["H"] == g["fav"]
        hv.append(CF[r["i"], CC.index(("fav " if Hfav else "dog ") + k)]); lv.append(CF[r["i"], CC.index(("dog " if Hfav else "fav ") + k)])
    hv, lv = np.array(hv, float), np.array(lv, float)
    for nm, v in ((f"H coach {k}", hv), (f"L coach {k}", lv), (f"L-H coach {k}", lv - hv)):
        if np.std(v) > 1e-9: POOL[nm] = v
NM = list(POOL); PX = np.column_stack([POOL[c] for c in NM])
col = lambda c: PX[:, NM.index(c)]
def auc(s, yy):
    o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = yy.sum(); return (r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))
right = lambda pk, m=None: int((pk == (ys == 1)).sum()) if m is None else int((pk[m] == (ys[m] == 1)).sum())
nice = lambda c: c.replace("L-H ", "gap ", 1) if c.startswith("L-H ") else ("higher " + c[2:] if c.startswith("H ") else "lower " + c[2:])
allm = np.ones(nS, bool)
print(f"Round of 32: {nS} games, {int(ys.sum())} lower-seed wins | higher seed {right(np.zeros(nS) >= .5)}, model 1 {right(su >= .5)}, simulator {right(si >= .5)}, M1+sim avg {right((su + si) / 2 >= .5)}")
# ---- coach screen
print("\nCoach measures (z seed | beyond M1+sim | 10-17 | 18-26 | r net):")
cz = []
for c in NM:
    if " coach " not in c: continue
    v = col(c); cz.append((c, wald(v, ys, allm, [sg]), wald(v, ys, allm, [sg, lg(su), lg(si)]), wald(v, ys, early, [sg]), wald(v, ys, ~early, [sg]), np.corrcoef(v, rg)[0, 1]))
for c, a, b, e1, e2, rn in sorted(cz, key=lambda t: -abs(t[1]))[:10]: print(f"   {nice(c):40} {a:+.2f} | {b:+.2f} | {e1:+.1f} | {e2:+.1f} | {rn:+.2f}")
# ---- side test: Round 1 box score (not usable as inputs)
RB = json.load(open(os.path.join(HERE, "m258_r1box.json"))); KB = sorted(next(iter(next(iter(RB.values())).values())).keys())
print("\nSIDE TEST ONLY - Round 1 box score (z seed | beyond M1+sim | 10-17 | 18-26):")
bz = []
for k in KB:
    vv = {}
    for sd in "HL":
        a = np.array([RB.get(rows[i]["s"], {}).get(rows[i][sd], {}).get(k, np.nan) for i in idx], float); a[np.isnan(a)] = np.nanmean(a); vv[sd] = a
    for nm, v in ((f"H {k}", vv["H"]), (f"L {k}", vv["L"]), (f"L-H {k}", vv["L"] - vv["H"])):
        if np.std(v) > 1e-9: bz.append((nm, wald(v, ys, allm, [sg]), wald(v, ys, allm, [sg, lg(su), lg(si)]), wald(v, ys, early, [sg]), wald(v, ys, ~early, [sg])))
for c, a, b, e1, e2 in sorted(bz, key=lambda t: -abs(t[1]))[:12]: print(f"   {nice(c):40} {a:+.2f} | {b:+.2f} | {e1:+.1f} | {e2:+.1f}")
print(f"   ({sum(abs(t[1]) >= 2 for t in bz)} of {len(bz)} at |z|>=2; ~{round(len(bz) * .046)} by chance)")
# ---- models
def fitp(names, tr, te, lam=30.0):
    X = np.column_stack([col(c) for c in names]); f, b = fit(X[tr], ys[tr], Ws[tr], lam); return f(X[te]), b
def evaluate(names, lam=30.0):
    X = np.column_stack([col(c) for c in names]); f, b = fit(X, ys, Ws, lam); pa = f(X)
    ph = np.zeros(nS)
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; ph[te] = fitp(names, tr, te, lam)[0]
    fw = np.zeros(nS); fw[~early] = fitp(names, early, ~early, lam)[0]; fw[early] = fitp(names, ~early, early, lam)[0]
    return pa, ph, fw, b
RES = {}
def report(lab, names, lam=30.0, show=True):
    pa, ph, fw, b = evaluate(names, lam); av = (ph + su + si) / 3
    bestav = max(range(35, 56), key=lambda c: right(av >= c / 100))
    R = dict(k=len(names), auc_all=auc(pa, ys), r_all=right(pa >= .4), auc_ho=auc(ph, ys), r35=right(ph >= .35), r40=right(ph >= .4), r45=right(ph >= .45), r50=right(ph >= .5),
             picks=int((ph >= .4).sum()), hits=int(((ph >= .4) & (ys == 1)).sum()), fwd=right(fw >= .4, ~early), bwd=right(fw >= .4, early),
             av45=right(av >= .45), avbest=(right(av >= bestav / 100), bestav), auc_av=auc(av, ys), r_m1=np.corrcoef(ph, su)[0, 1], r_sim=np.corrcoef(ph, si)[0, 1])
    RES[lab] = (names, R, ph)
    if show:
        print(f"{lab:46} {R['k']:3} | {R['auc_all']:.3f} {R['r_all']:3} | {R['auc_ho']:.3f} {R['r35']:3} {R['r40']:3} {R['r45']:3} {R['r50']:3} | {R['picks']:3} ({R['hits']:2}) | "
              f"{R['fwd']:3}/{int((~early).sum())} {R['bwd']:3}/{int(early.sum())} | {R['av45']:3} {R['avbest'][0]:3}@{R['avbest'][1]} {R['auc_av']:.3f} | {R['r_m1']:+.2f} {R['r_sim']:+.2f}")
    return R
HDR = (f"\n{'model':46} {'k':>3} | fit-all AUC r@40 | held-out AUC r@35 r@40 r@45 r@50 | picks@40 (hit) | fwd@40 bwd@40 | avg3 @45 best AUC | r M1 r sim")
CORE12 = ["H pt_d_share Post-Up", "H pt_ppp Big Cut & Roll", "L pt_share Post-Up", "L-H big_height", "H ftr", "H pt_d_ppp High-Low", "L pt_d_ppp Transition",
          "L pt_ppp Inside Out", "L-H pt_d_ppp Rim Attack", "L pt_share Mid-Range", "H exp", "H bench_minutes"]
ROBUST4 = ["H pt_d_share Post-Up", "H pt_ppp Big Cut & Roll", "H pt_d_ppp High-Low", "L pt_ppp Inside Out"]
KEPT16 = json.load(open(os.path.join(HERE, "m256_kept.json")))["kept"]
elig = [c for c, d in REP.items() if not d["strength"] and abs(d["rnet"]) < .3 and c in NM]
RELAX = [c for c in elig if abs(REP[c]["zs"]) >= 2 or abs(REP[c]["zd"]) >= 2]
DIST = [c for c in elig if abs(REP[c]["zd"]) >= 2]
BOTH = [c for c in elig if abs(REP[c]["zs"]) >= 2 and abs(REP[c]["zd"]) >= 2]
PTS = ["Rim Attack", "Dribble Jumper", "Transition", "Pick & Pop", "Post-Up", "Perimeter Cut", "Inside Out", "Drive & Kick", "Big Cut & Roll", "High-Low", "Mid-Range"]
DEF = []
for pt in PTS:
    cands = [f"{s} pt_d_{k} {pt}" for s in ("H", "L", "L-H") for k in ("ppp", "share") if f"{s} pt_d_{k} {pt}" in REP and f"{s} pt_d_{k} {pt}" in NM]
    if cands: DEF.append(max(cands, key=lambda c: abs(REP[c]["zd"])))
U = lambda *ls: list(dict.fromkeys(sum(ls, [])))
print(HDR)
for lab, names in (("robust 4 (hold up in both eras)", ROBUST4), ("core 12 (significant beyond M1+sim)", CORE12), ("kept 16 (overlap removed)", KEPT16),
                   (f"distinct: every |z beyond M1+sim|>=2", DIST), (f"both |z seed| and |z beyond| >= 2", BOTH), (f"relaxed: all eligible significant (no overlap rule)", RELAX),
                   ("core 12 + best defensive play type each", U(CORE12, DEF)), ("robust 4 + best defensive play type each", U(ROBUST4, DEF))):
    report(lab, names)
# ---- greedy forward build from the eligible pool, judged on held-out right@40 then AUC (selection uses held-out -> optimistic;
#      checked with forward/backward, which the greedy step never sees directly)
print("\nGreedy build (start: robust 4; add the eligible measure that most improves held-out games right @40, ties by AUC; stop when nothing helps)")
POOLG = [c for c in elig if abs(REP[c]["zs"]) >= 1.5 or abs(REP[c]["zd"]) >= 1.5]
cur = list(ROBUST4); best = report("greedy start", cur, show=False); step = 0
while True:
    cand = []
    for c in POOLG:
        if c in cur or any(abs(np.corrcoef(col(c), col(k))[0, 1]) >= .5 for k in cur): continue
        _, ph, _, _ = evaluate(cur + [c]); cand.append((right(ph >= .4), auc(ph, ys), c))
    if not cand: break
    cand.sort(reverse=True); r_, a_, c = cand[0]
    if (r_, a_) <= (best["r40"], best["auc_ho"]): break
    cur.append(c); step += 1; best = report(f"greedy +{step}: {nice(c)}"[:46], cur)
GREEDY = list(cur)
# ---- coach add-on to the best sets
coach_sig = [c for c, a, b, e1, e2, rn in cz if (abs(a) >= 2 or abs(b) >= 2) and abs(rn) < .3]
if coach_sig:
    print(HDR); report("core 12 + significant coach measures", U(CORE12, coach_sig)); report("greedy + significant coach measures", U(GREEDY, coach_sig))
# ---- aggressive view: cutoffs for the main candidates
print("\nAggressive cutoffs (held out): cutoff -> games right / upset picks (hit)")
for lab in ("robust 4 (hold up in both eras)", "core 12 (significant beyond M1+sim)", "core 12 + best defensive play type each"):
    ph = RES[lab][2]; print(f"   {lab:44} " + " | ".join(f"{c}%: {right(ph >= c / 100)} / {int((ph >= c / 100).sum())} ({int(((ph >= c / 100) & (ys == 1)).sum())})" for c in (30, 35, 40, 45, 50)))
print(f"   {'model 1 (for reference)':44} " + " | ".join(f"{c}%: {right(su >= c / 100)} / {int((su >= c / 100).sum())} ({int(((su >= c / 100) & (ys == 1)).sum())})" for c in (30, 35, 40, 45, 50)))
json.dump({lab: {"inputs": v[0], "R": {k: (list(x) if isinstance(x, tuple) else float(x)) for k, x in v[1].items()}, "p_heldout": v[2].tolist()} for lab, v in RES.items()},
          open(os.path.join(HERE, "m259_results.json"), "w"))
print("\ngreedy inputs:", GREEDY); print("core 12 + DEF:", U(CORE12, DEF))
