# Round of 32: the 42 significant measures with duplicates removed (keep the strongest |z| of any pair with |r| >= cut).
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m250_r32_all_sig.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"Round of 32:")])
ZD = {d["m"]: d["z"] for d in Z}
def dedup(names, cut, Xsrc=lambda c: fullcol(c)[idx]):
    kept = []
    for c in sorted(names, key=lambda c: -abs(ZD[c])):
        v = Xsrc(c)
        if all(abs(np.corrcoef(v, Xsrc(k))[0, 1]) < cut for k in kept): kept.append(c)
    return kept
print(f"Round of 32: {nS} games, {int(ys.sum())} upsets | higher seed 187, simulator 192, original model 203, original+simulator avg 202")
print(f"{'model':52} {'inputs':>6} | fit all yrs: AUC, right@40/50 | held out: AUC, right@40/50 | avg of 3 held out: right@45/50")
SETS = {}
for cut in (.8, .6, .5, .4):
    SETS[cut] = dedup(SIG, cut); p_ho, p_all = ho(SETS[cut]); show(f"42 significant, dupes removed (|r| >= {cut})", p_ho, p_all, len(SETS[cut]))
p_ho, p_all = ho(LEAD); show("R32 leaders (|r| >= 0.3, for reference)", p_ho, p_all, len(LEAD))
# honest: |z|>=2 picked inside each fold, then dupes removed inside the fold
for cut in (.6, .5):
    p = np.zeros(nS); cnt = []
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; zz = {}
        for c in NM:
            try:
                z = wald(PX[:, NM.index(c)], ys, tr, [sg])
                if abs(z) >= 2: zz[c] = z
            except Exception: pass
        kept = []
        for c in sorted(zz, key=lambda c: -abs(zz[c])):
            v = fullcol(c)[idx][tr]
            if all(abs(np.corrcoef(v, fullcol(k)[idx][tr])[0, 1]) < cut for k in kept): kept.append(c)
        cnt.append(len(kept)); Xg = X_of(kept); f, _ = fit(Xg[tr], ys[tr], Ws[tr]); p[te] = f(Xg[te])
    av = (p + s_up_ + sim_up_) / 3
    print(f"{'honest: picked + deduped inside each fold, |r| >= %.1f' % cut:52} {round(np.mean(cnt)):6} | {'':27} | {auc(p, ys):.3f} {right(p >= .4)} {right(p >= .5)} | {right(av >= .45)} {right(av >= .5)}  (AUC {auc(av, ys):.3f})")
for cut in (.6, .5):
    print(f"\nKept at |r| >= {cut} ({len(SETS[cut])}):", ", ".join(f"{c} ({ZD[c]:+.2f})" for c in SETS[cut]))
    print("   removed:", ", ".join(c for c in SIG if c not in SETS[cut]))
json.dump({str(k): v for k, v in SETS.items()}, open(os.path.join(HERE, "m251_sets.json"), "w"))
