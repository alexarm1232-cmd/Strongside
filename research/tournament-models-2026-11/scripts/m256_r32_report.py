# Round of 32 report before building: every measure (432 + new player-level volume 3s), with
#   z (seed gap controlled), z beyond model 1 + simulator (distinctness), r with the net-rating gap, r with model 1 / simulator,
#   both eras, Mann-Whitney. Strength stand-ins and net-linked measures (|r net| >= 0.3) are out; overlaps removed (|r| >= 0.3).
import os, sys, json, math, re, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RNDS"] = "Second round"
src = open(os.path.join(HERE, "m247_s16_model.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("allm = np.ones")])
import numpy as np
P3 = json.load(open(os.path.join(HERE, "m255_player3.json")))
K3 = ["vol_n", "vol_3pa_share", "vol_p3", "vol_hot_rate", "vol_hot50", "vol_cold", "team_any_hot", "team_two_hot", "team_5plus_game", "top_3pa", "top_p3", "top_hot", "top_sd", "shooters_35"]
miss = sum(1 for r in [rows[i] for i in idx] for sd in "HL" if not (P3.get(r["s"], {}).get(r[sd]) or P3.get(r["s"], {}).get(r[sd] + ".")))
add(P3, K3, "vol3: ")
for b in ["vol3: " + k for k in K3]:
    h, l = F["H " + b][idx], F["L " + b][idx]
    for nm, v in ((f"H {b}", h), (f"L {b}", l), (f"L-H {b}", l - h)):
        if np.std(v) > 1e-9 and nm not in POOL: POOL[nm] = v
NM = list(POOL); PX = np.column_stack([POOL[c] for c in NM])
m1 = np.load(os.path.join(HERE, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
su, si = s_up[idx], sim_up[idx]; lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
allm = np.ones(nS, bool)
def mwz(v, yy):
    o = np.argsort(v, kind="mergesort"); r = np.empty(len(v)); r[o] = np.arange(1, len(v) + 1)
    for u in np.unique(v):
        t = v == u
        if t.sum() > 1: r[t] = r[t].mean()
    n1 = yy.sum(); n0 = len(yy) - n1; return (r[yy == 1].sum() - n1 * (n1 + 1) / 2 - n1 * n0 / 2) / math.sqrt(n1 * n0 * (len(yy) + 1) / 12)
STRENGTH = re.compile(r"bpm|pm_|margin|lead_max|trail_max|efg|fg_pct|\bp2\b|ptsft|net|adj_|win_pct|ppg|papg")
def nice(c):
    side, rest = c.split(" ", 1); return {"H": "higher seed", "L": "lower seed", "L-H": "gap (lower − higher)"}[side] + ": " + rest
R = []
for j, c in enumerate(NM):
    v = PX[:, j]
    try:
        zs = wald(v, ys, allm, [sg]); zd = wald(v, ys, allm, [sg, lg(su), lg(si)])
        e1 = wald(v, ys, early, [sg]); e2 = wald(v, ys, ~early, [sg])
    except Exception: continue
    R.append(dict(c=c, zs=zs, zd=zd, e1=e1, e2=e2, mw=mwz(v, ys), rnet=np.corrcoef(v, rg)[0, 1], rm1=np.corrcoef(v, su)[0, 1], rsim=np.corrcoef(v, si)[0, 1], j=j,
                  strength=bool(STRENGTH.search(c)), vol="3pt/vol" in c or "vol3:" in c))
print(f"Round of 32: {nS} games, {int(ys.sum())} lower-seed wins | {len(R)} measures | volume-3 box-score rows missing for {miss} of {2 * nS} team slots")
print(f"by chance: ~{round(len(R) * .046)} pass |z|>=2")
elig = [d for d in R if not d["strength"] and abs(d["rnet"]) < .3]
print(f"out as strength stand-ins: {sum(d['strength'] for d in R)} | out for net-rating link (|r| >= 0.3): {sum((not d['strength']) and abs(d['rnet']) >= .3 for d in R)} | eligible {len(elig)}")
print(f"eligible at |z seed|>=2: {sum(abs(d['zs']) >= 2 for d in elig)} | at |z beyond model 1 + sim|>=2: {sum(abs(d['zd']) >= 2 for d in elig)} | both: {sum(abs(d['zs']) >= 2 and abs(d['zd']) >= 2 for d in elig)}")
cand = sorted([d for d in elig if abs(d["zs"]) >= 2 or abs(d["zd"]) >= 2], key=lambda d: -max(abs(d["zd"]), abs(d["zs"])))
kept, dropped = [], []
for d in cand:
    hit = next((k for k in kept if abs(np.corrcoef(PX[:, d["j"]], PX[:, k["j"]])[0, 1]) >= .3), None)
    (dropped if hit else kept).append(d); d["over"] = hit["c"] if hit else ""
hdr = f"{'measure':58} {'z seed':>7} {'z beyond M1+sim':>15} {'10-17':>6} {'18-26':>6} {'MW':>6} {'r net':>6} {'r M1':>6} {'r sim':>6}"
row = lambda d: f"{nice(d['c']):58} {d['zs']:+7.2f} {d['zd']:+15.2f} {d['e1']:+6.1f} {d['e2']:+6.1f} {d['mw']:+6.2f} {d['rnet']:+6.2f} {d['rm1']:+6.2f} {d['rsim']:+6.2f}"
print(f"\n=== A. KEPT: significant, no net link, no overlap ({len(kept)})\n" + hdr)
for d in kept: print(row(d))
print(f"\n=== B. Dropped for overlap ({len(dropped)}): measure -> overlaps with")
for d in dropped: print(f"   {nice(d['c'])}  ->  {nice(d['over'])}  (z seed {d['zs']:+.2f}, beyond {d['zd']:+.2f})")
print("\n=== C. Every volume-3 / hot-shooting measure (team game logs + player box scores)\n" + hdr)
for d in sorted([d for d in R if d["vol"]], key=lambda d: -abs(d["zs"])): print(row(d) + ("  [net-linked]" if abs(d["rnet"]) >= .3 else ""))
print("\n=== D. Strongest strength / net-linked measures left out (for reference)")
for d in sorted([d for d in R if d["strength"] or abs(d["rnet"]) >= .3], key=lambda d: -abs(d["zs"]))[:10]: print("   " + row(d))
json.dump([{k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in d.items()} for d in R], open(os.path.join(HERE, "m256_report.json"), "w"))
json.dump({"kept": [d["c"] for d in kept]}, open(os.path.join(HERE, "m256_kept.json"), "w"))
