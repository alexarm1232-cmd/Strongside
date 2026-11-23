# Round of 32 model with EVERY significant measure (|z| >= 2, seed gap controlled, from m248), no overlap filter;
# variants: only those pointing the same way in both eras; plus honest version (all |z|>=2 re-picked inside each fold).
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m249_r1_on_r32.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
Z = json.load(open(os.path.join(HERE, f"m248_z_{RNDS[0].replace(' ', '')}_{len(RNDS)}.json")))
SIG = [d["m"] for d in Z if abs(d["z"]) >= 2]
BOTH = [d["m"] for d in Z if abs(d["z"]) >= 2 and np.sign(d["e1"]) == np.sign(d["e2"])]
print(f"Round of 32: {nS} games, {int(ys.sum())} upsets | higher seed 187, simulator 192, original model 203, original+simulator avg 202 (50%)")
print(f"{'model':52} {'inputs':>6} | fit all yrs: AUC, right@40/50 | held out: AUC, right@40/50 | avg of 3 held out: right@45/50")
for lam in (30.0, 100.0):
    for lab, names in ((f"all significant (|z|>=2), ridge {lam:.0f}", SIG), (f"significant + same sign both eras, ridge {lam:.0f}", BOTH), (f"R32 leaders (14), ridge {lam:.0f}", LEAD)):
        p_ho, p_all = ho(names, lam); show(lab, p_ho, p_all, len(names))
# honest: every |z|>=2 measure re-picked inside each fold (no overlap filter)
pool_j = {c: NM.index(c) for c in NM}
def zsel(tr):
    out = []
    for c, j in pool_j.items():
        try:
            if abs(wald(PX[:, j], ys, tr, [sg])) >= 2: out.append(c)
        except Exception: pass
    return out
for lam in (30.0, 100.0):
    p = np.zeros(nS); cnt = []
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; names = zsel(tr); cnt.append(len(names)); Xg = X_of(names); f, _ = fit(Xg[tr], ys[tr], Ws[tr], lam); p[te] = f(Xg[te])
    av = (p + s_up_ + sim_up_) / 3
    print(f"{'honest: all |z|>=2 re-picked in each fold, ridge %d' % lam:52} {round(np.mean(cnt)):6} | {'':27} | {auc(p, ys):.3f} {right(p >= .4)} {right(p >= .5)} | {right(av >= .45)} {right(av >= .5)}  (AUC {auc(av, ys):.3f})")
# weights of the all-significant model fit on all years
_, b = fit(X_of(SIG), ys, Ws, 30.0)
print("\nAll-significant model, all years, standardized weights (+ = helps the worse seed):")
for i in np.argsort(-np.abs(b[:-1])): print(f"   {SIG[i]:44} {b[i]:+.3f}")
