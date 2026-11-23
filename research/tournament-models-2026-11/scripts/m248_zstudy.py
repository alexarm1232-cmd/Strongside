# z-score study per round group, like the Round 1 study: every game in the group, every H / L / L-H measure.
# Wald z = measure added to the seed gap (logistic, + = helps the worse seed); MW z = Mann-Whitney, upsets vs not (raw);
# both eras; r with the net gap; overlap groups (|r| >= 0.3, strongest first).
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m247_s16_model.py"), encoding="utf-8").read()
exec(src[:src.index("allm = np.ones")])
def mwz(v, yy):
    o = np.argsort(v, kind="mergesort"); r = np.empty(len(v)); r[o] = np.arange(1, len(v) + 1)
    for u in np.unique(v):   # ties -> average rank
        t = v == u
        if t.sum() > 1: r[t] = r[t].mean()
    n1 = yy.sum(); n0 = len(yy) - n1; U = r[yy == 1].sum() - n1 * (n1 + 1) / 2
    return (U - n1 * n0 / 2) / math.sqrt(n1 * n0 * (len(yy) + 1) / 12)
allm = np.ones(nS, bool); res = []
for j, c in enumerate(NM):
    try: z = wald(PX[:, j], ys, allm, [sg]); e1 = wald(PX[:, j], ys, early, [sg]); e2 = wald(PX[:, j], ys, ~early, [sg])
    except Exception: continue
    res.append(dict(m=c, z=z, mw=mwz(PX[:, j], ys), e1=e1, e2=e2, rnet=float(np.corrcoef(PX[:, j], rg)[0, 1]), j=j))
res.sort(key=lambda d: -abs(d["z"]))
lead = []
for d in res:
    if abs(d["z"]) < 2: break
    hit = next((L for L in lead if abs(np.corrcoef(PX[:, d["j"]], PX[:, L["j"]])[0, 1]) >= .3), None)
    d["grp"] = hit["m"] if hit else "(leads its group)"
    if not hit: lead.append(d)
npass = sum(abs(d["z"]) >= 2 for d in res)
print(f"\n##### {', '.join(RNDS)}: {nS} games, {int(ys.sum())} upsets | {len(res)} measures, {npass} at |z|>=2 (~{round(len(res) * .046)} by chance)")
print(f"{'measure':44} {'z(seed ctl)':>11} {'MW z':>6} {'10-17':>6} {'18-26':>6} {'both':>5} {'r net':>6}  overlap group")
for d in res[:max(npass, 10)]:
    print(f"{d['m']:44} {d['z']:+11.2f} {d['mw']:+6.2f} {d['e1']:+6.1f} {d['e2']:+6.1f} {'yes' if np.sign(d['e1']) == np.sign(d['e2']) else 'no':>5} {d['rnet']:+6.2f}  {d.get('grp', '')}")
json.dump([{k: v for k, v in d.items() if k != "j"} for d in res], open(os.path.join(HERE, f"m248_z_{RNDS[0].replace(' ', '')}_{len(RNDS)}.json"), "w"))
