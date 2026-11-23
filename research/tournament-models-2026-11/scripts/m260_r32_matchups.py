# Round of 32, round 2 of testing:
#  (a) style MATCHUP measures (new): for each play type, lower seed's use of it x how well the higher seed defends it, and vice versa
#      (z-scored products), plus summed "style edge" across play types; screened like everything else (seed gap controlled, beyond M1+sim).
#  (b) ridge strength variants for the best sets;  (c) "model 1 + upset override": keep model 1's pick unless the R32 model is confident;
#  (d) best sets + significant matchups.
import os, sys, json, math, re, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m259_r32_models.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(HDR)")])
import numpy as np
zsd = lambda v: (v - v.mean()) / (v.std() + 1e-12)
PTN = sorted({c.split("pt_share ", 1)[1] for c in NM if c.startswith("H pt_share ")})
PTN = [p for p in PTN if all(f"{s} {k} {p}" in NM for s in "HL" for k in ("pt_share", "pt_ppp", "pt_d_share", "pt_d_ppp"))]
print("play types with full data:", PTN)
MU = {}
for p in PTN:
    Ls, Lp, Lds, Ldp = (zsd(col(f"L {k} {p}")) for k in ("pt_share", "pt_ppp", "pt_d_share", "pt_d_ppp"))
    Hs, Hp, Hds, Hdp = (zsd(col(f"H {k} {p}")) for k in ("pt_share", "pt_ppp", "pt_d_share", "pt_d_ppp"))
    MU[f"MU lower uses x higher leaks: {p}"] = Ls * Hdp           # lower seed runs it a lot AND higher seed gives up points on it
    MU[f"MU lower good at x higher leaks: {p}"] = Lp * Hdp
    MU[f"MU higher uses x lower leaks: {p}"] = Hs * Ldp
    MU[f"MU higher good at x lower leaks: {p}"] = Hp * Ldp
    MU[f"MU lower uses x higher allows often: {p}"] = Ls * Hds
    MU[f"MU edge (lower off vs higher def) - (higher off vs lower def): {p}"] = (Lp + Hdp) - (Hp + Ldp)
# summed style edges: usage-weighted
w = lambda side, p: col(f"{side} pt_share {p}")
MU["MU summed: lower usage-weighted (lower ppp + higher def ppp)"] = sum(w("L", p) * (zsd(col(f"L pt_ppp {p}")) + zsd(col(f"H pt_d_ppp {p}"))) for p in PTN)
MU["MU summed: higher usage-weighted (higher ppp + lower def ppp)"] = sum(w("H", p) * (zsd(col(f"H pt_ppp {p}")) + zsd(col(f"L pt_d_ppp {p}"))) for p in PTN)
MU["MU summed: net style edge for lower seed"] = MU["MU summed: lower usage-weighted (lower ppp + higher def ppp)"] - MU["MU summed: higher usage-weighted (higher ppp + lower def ppp)"]
MU["MU size: lower big height x higher post-up allowed share"] = zsd(col("L big_height")) * zsd(col("H pt_d_share Post-Up"))
MU["MU size: lower post-up share x higher post-up def ppp"] = zsd(col("L pt_share Post-Up")) * zsd(col("H pt_d_ppp Post-Up"))
mz = []
for c, v in MU.items():
    try: mz.append((c, wald(v, ys, allm, [sg]), wald(v, ys, allm, [sg, lg(su), lg(si)]), wald(v, ys, early, [sg]), wald(v, ys, ~early, [sg]), np.corrcoef(v, rg)[0, 1]))
    except Exception: pass
mz.sort(key=lambda t: -max(abs(t[1]), abs(t[2])))
print(f"\n(a) {len(mz)} matchup measures; {sum(abs(t[1]) >= 2 for t in mz)} at |z seed|>=2, {sum(abs(t[2]) >= 2 for t in mz)} beyond M1+sim (~{round(len(mz) * .046)} by chance)")
print("   measure | z seed | beyond M1+sim | 10-17 | 18-26 | r net")
for c, a, b, e1, e2, rn in mz[:15]: print(f"   {c[3:]:70} {a:+.2f} | {b:+.2f} | {e1:+.1f} | {e2:+.1f} | {rn:+.2f}")
for c, v in MU.items(): POOL[c] = v
NM = list(POOL); PX = np.column_stack([POOL[c] for c in NM])
# (b) ridge variants
print(HDR)
SETS = {"kept 16": KEPT16, "core 12 + coach": U(CORE12, ["L coach car_s16", "L-H coach rec5_s16"]), "core 12 + best def play types": U(CORE12, DEF), "core 12": CORE12}
for lab, names in SETS.items():
    for lam in (10.0, 30.0, 100.0): report(f"{lab}, ridge {lam:.0f}", names, lam)
# (d) + significant matchups (|z| >= 2 either way, both-era same sign, r net < .3, not overlapping each other at .5)
msig = [c for c, a, b, e1, e2, rn in mz if (abs(a) >= 2 or abs(b) >= 2) and np.sign(e1) == np.sign(e2) and abs(rn) < .3]
mk_ = []
for c in msig:
    if all(abs(np.corrcoef(MU[c], MU[k])[0, 1]) < .5 for k in mk_): mk_.append(c)
print(f"\nsignificant matchup measures used ({len(mk_)}):", [c[3:] for c in mk_])
if mk_:
    print(HDR)
    for lab, names in SETS.items(): report(f"{lab} + matchups", U(names, mk_))
    report("matchups only", mk_)
# (c) model 1 + upset override (held out): pick the upset if model 1 >= 50% OR the R32 model >= t
print("\n(c) model 1 with an upset override from the R32 model (held out): override cutoff -> games right / upsets picked (hit)")
for lab in list(RES)[:]:
    if not any(lab.startswith(s) for s in ("kept 16, ridge 30", "core 12 + coach, ridge 30", "core 12 + best def play types, ridge 30", "kept 16 + matchups", "core 12 + best def play types + matchups")): continue
    ph = RES[lab][2]
    line_ = []
    for t in (.45, .5, .55, .6):
        pk = (su >= .5) | (ph >= t); line_.append(f"{int(t * 100)}%: {right(pk)} / {int(pk.sum())} ({int((pk & (ys == 1)).sum())})")
    print(f"   {lab:44} " + " | ".join(line_))
print(f"   model 1 alone: {right(su >= .5)} / {int((su >= .5).sum())} ({int(((su >= .5) & (ys == 1)).sum())})")
json.dump({lab: {"inputs": v[0], "R": {k: (list(x) if isinstance(x, tuple) else float(x)) for k, x in v[1].items()}, "p_heldout": v[2].tolist()} for lab, v in RES.items()},
          open(os.path.join(HERE, "m260_results.json"), "w"))
json.dump({c: v.tolist() for c, v in MU.items()}, open(os.path.join(HERE, "m260_matchups.json"), "w"))
