# Round of 32, style only: drop strength stand-ins (BPM gaps/levels, margins/leads, shooting-efficiency levels) from the
# 42 significant measures, remove duplicates (|r| >= 0.5), then add defensive play types the way the Round 1 model has them.
import os, sys, json, contextlib, io, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m251_r32_dedup.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"Round of 32:")])
STRENGTH = re.compile(r"bpm|pm_|margin|lead_max|trail_max|efg|fg_pct|\bp2\b|\bp3\b|ptsft|net|adj_")
def zR(c):
    if c not in ZD:
        ZD[c] = wald(fullcol(c)[idx], ys, np.ones(nS, bool), [sg])
    return ZD[c]
STYLE = [c for c in SIG if not STRENGTH.search(c)]
DROPPED = [c for c in SIG if STRENGTH.search(c)]
STY = dedup(STYLE, .5)
print(f"{', '.join(RNDS)}: {nS} games, {int(ys.sum())} upsets | higher seed {right(np.zeros(nS) >= .5)}, simulator {right(sim_up_ >= .5)}, original model {right(s_up_ >= .5)}, original+simulator avg {right((s_up_ + sim_up_) / 2 >= .5)}")
print(f"{len(SIG)} measures at |z|>=2 (~{round(len(NM) * .046)} by chance)")
print("dropped as strength:", ", ".join(DROPPED))
print(f"style measures kept after removing duplicates ({len(STY)}):", ", ".join(f"{c} ({ZD[c]:+.2f})" for c in STY))
PTS = ["Rim Attack", "Dribble Jumper", "Transition", "Pick & Pop", "Post-Up", "Perimeter Cut", "Inside Out", "Drive & Kick", "Big Cut & Roll", "High-Low", "Mid-Range", "Catch & Shoot", "Off Screen", "Spot-Up"]
# A: the Round 1 model's defensive play-type inputs as they are
D_R1 = [c for c in INS if "pt_d_" in c]
# B: per defensive play type, the strongest Round of 32 version (H / L / L-H, points per play or share)
D_R32 = []
for pt in PTS:
    cands = [f"{s} pt_d_{k} {pt}" for s in ("H", "L", "L-H") for k in ("ppp", "share")]
    cands = [c for c in cands if c.split(" ", 1)[1] in [b for b in bases] or ("H " + c.split(" ", 1)[1]) in F]
    cands = [c for c in cands if ("H " + c.split(" ", 1)[1]) in F]
    if cands: D_R32.append(max(cands, key=lambda c: abs(zR(c))))
# C: per defensive play type, points per play only (Round 1 style), L and L-H versions, strongest
D_PPP = []
for pt in PTS:
    cands = [f"{s} pt_d_ppp {pt}" for s in ("L", "L-H", "H") if ("H pt_d_ppp " + pt) in F]
    if cands: D_PPP.append(max(cands, key=lambda c: abs(zR(c))))
print(f"\nRound 1 defensive play-type inputs ({len(D_R1)}): " + ", ".join(f"{c} (R32 z {zR(c):+.2f})" for c in D_R1))
print(f"Best Round of 32 version per defensive play type ({len(D_R32)}): " + ", ".join(f"{c} ({zR(c):+.2f})" for c in D_R32))
print(f"Best points-per-play version per defensive play type ({len(D_PPP)}): " + ", ".join(f"{c} ({zR(c):+.2f})" for c in D_PPP))
print(f"\n{'model':58} {'inputs':>6} | fit all yrs: AUC, right@40/50 | held out: AUC, right@40/50 | avg of 3 held out: right@45/50")
def uniq(*ls): return list(dict.fromkeys(sum(ls, [])))
for lab, names in (("style only (strength removed, deduped)", STY),
                   ("style + Round 1 defensive play types", uniq(STY, D_R1)),
                   ("style + best R32 defensive play type each", uniq(STY, D_R32)),
                   ("style + best defensive points per play each", uniq(STY, D_PPP)),
                   ("style + R32 def play types, deduped", dedup(uniq(STY, D_R32), .5)),
                   ("style + def points per play, deduped", dedup(uniq(STY, D_PPP), .5))):
    p_ho, p_all = ho(names); show(lab, p_ho, p_all, len(names))
# honest version of the main idea: inside each fold, |z|>=2 style measures (strength removed), deduped, + best def play type each
p = np.zeros(nS); cnt = []
for s in SEASONS:
    tr, te = Ss != s, Ss == s; zz = {}
    for c in NM:
        if STRENGTH.search(c): continue
        try:
            z = wald(PX[:, NM.index(c)], ys, tr, [sg])
            if abs(z) >= 2: zz[c] = z
        except Exception: pass
    for pt in PTS:
        cands = [f"{s_} pt_d_{k} {pt}" for s_ in ("H", "L", "L-H") for k in ("ppp", "share") if f"{s_} pt_d_{k} {pt}" in NM]
        if cands:
            zc = {c: wald(PX[:, NM.index(c)], ys, tr, [sg]) for c in cands}; b_ = max(zc, key=lambda c: abs(zc[c])); zz.setdefault(b_, zc[b_])
    kept = []
    for c in sorted(zz, key=lambda c: -abs(zz[c])):
        v = fullcol(c)[idx][tr]
        if all(abs(np.corrcoef(v, fullcol(k)[idx][tr])[0, 1]) < .5 for k in kept): kept.append(c)
    cnt.append(len(kept)); Xg = X_of(kept); f, _ = fit(Xg[tr], ys[tr], Ws[tr]); p[te] = f(Xg[te])
av = (p + s_up_ + sim_up_) / 3
print(f"{'honest: style + def play types picked inside each fold':58} {round(np.mean(cnt)):6} | {'':27} | {auc(p, ys):.3f} {right(p >= .4)} {right(p >= .5)} | {right(av >= .45)} {right(av >= .5)}  (AUC {auc(av, ys):.3f})")
best = uniq(STY, D_R32); _, b = fit(X_of(best), ys, Ws)
print("\nstyle + best R32 defensive play type each, all years, standardized weights (+ = helps the worse seed):")
for i in np.argsort(-np.abs(b[:-1])): print(f"   {best[i]:44} {b[i]:+.3f}   (z {zR(best[i]):+.2f}, r net {np.corrcoef(fullcol(best[i])[idx], rg)[0, 1]:+.2f})")
FINAL = dedup(uniq(STY, D_R32), .5); pf, _ = ho(FINAL); avf = (pf + s_up_ + sim_up_) / 3
print(f"\nby round (style + def play types deduped, held out @40% | avg of 3 @45% | original | simulator | higher seed):")
for rd in RNDS:
    m = rnd[idx] == rd
    print(f"   {rd:13} {int(m.sum()):3} games | {right(pf >= .4, m)} | {right(avf >= .45, m)} | {right(s_up_ >= .5, m)} | {right(sim_up_ >= .5, m)} | {right(np.zeros(nS) >= .5, m)}")
print("final inputs:", FINAL)
json.dump({"style": STY, "def_r1": D_R1, "def_r32": D_R32, "def_ppp": D_PPP, "final": FINAL}, open(os.path.join(HERE, f"m252_sets_{len(RNDS)}.json"), "w"))
