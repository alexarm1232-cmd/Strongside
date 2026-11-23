# Simulator in the Sweet 16 / Elite 8: sim share w in {0,.3,.5,.7,1}; Final Four + title stay 70% sim + 30% model.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m308_late.py"), encoding="utf-8-sig").read(); src = src[:src.index("res = {}")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
src = open(os.path.join(HERE, "m305b_export_full.py"), encoding="utf-8-sig").read()
SIMP = eval(src[src.index("SIMP = ") + 7:src.index("SIMB = dict")])
blk = src[src.index("SIMB.update(") + 12:src.index("ALL = {}")].rstrip().rstrip(")")
SIMB_U = eval(blk)
SIM = {}
def put(s, a, b, q): SIM[(s, a, b)] = q; SIM[(s, b, a)] = 1 - q
for SP in (SIMP, SIMB_U):
    for s, v in SP.items():
        for a, b, q in v: put(s, a, b, q)
for (s, a, b), q in {("2010-11", "Louisville", "Ohio St"): .3045, ("2013-14", "Arizona", "Florida"): .5206,
                     ("2018-19", "Duke", "Virginia"): .4352, ("2025-26", "Duke", "Michigan"): .523}.items(): put(s, a, b, q)
X = os.path.join(HERE, "m313_extra.json")
if os.path.exists(X):
    for s, v in json.load(open(X)).items():
        for k_, q in v.items(): a, b = k_.split("|"); put(s, a, b, q)
for s, v in json.load(open(os.path.join(HERE, "m312_sim.json"), encoding="utf-8-sig")).items():
    for k_, q in v.items(): a, b = k_.split("|"); put(s, a, b, q)
need = set()
def ps(s, a, b):
    if (s, a, b) in SIM: return SIM[(s, a, b)]
    need.add((s, a, b)); return None
def chooser_w(w):
    def ch(s, a, b, r):
        q = ps(s, a, b); m = pm(s, a, b)
        if r <= 4: x = m if w == 0 else (w * q + (1 - w) * m if q is not None else m)
        else: x = .7 * q + .3 * m if q is not None else m
        return a if x >= .5 else b
    return ch
yrs = [int(s[:4]) + 1 for s in SEASONS]
OUT = {}
for key in ("vote", "blend"):
    base = {o["season"]: o for o in FULL[key]}
    early = {s: base[s]["score"][0] + 2 * base[s]["score"][1] for s in SEASONS}
    print(f"\n===== Rounds 1-2 = {key}\n{'Sweet 16 / Elite 8 picker':34} | S16 | E8 | F4 | T | total | >=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
    print(f"{'Current file':34} | {sum(base[s]['score'][2] for s in SEASONS):3} | {sum(base[s]['score'][3] for s in SEASONS):2} | {sum(base[s]['score'][4] for s in SEASONS):2} | {sum(base[s]['score'][5] for s in SEASONS):1} | {sum(base[s]['points'] for s in SEASONS):5} |")
    for w in (0, .3, .5, .7, 1):
        tot = []; cs = np.zeros(4, int)
        for s in SEASONS:
            rd = fill(s, r2_tree(s, base[s]), chooser_w(w)); c, pts = score_late(s, rd); cs += c; tot.append(early[s] + pts)
        nm_ = f"{int(w * 100)}% simulator + {int(100 - w * 100)}% model"
        print(f"{nm_:34} | {cs[0]:3} | {cs[1]:2} | {cs[2]:2} | {cs[3]:1} | {sum(tot):5} | {sum(t >= 100 for t in tot):5} | " + " ".join(f"{t:3}" for t in tot))
        OUT[f"{key}|{w}"] = tot
print("\nmissing simulator pairs (Final Four/title fell back to model):", len(need))
miss = {}
for s, a, b in sorted(need):
    if (s, b, a) in need and (s, b, a) < (s, a, b): continue
    miss.setdefault(s, []).append([a, b])
json.dump(miss, open(os.path.join(HERE, "m313_need.json"), "w")); print(json.dumps(miss))
# real-game check: Sweet 16 on, simulator line in the game file vs the model
rows = []
for g in G:
    if g["rnd"] not in ("Sweet 16", "Elite Eight", "Final Four", "Championship") or g["season"] not in SEASONS: continue
    rows.append((g["season"], g["fav"], g["dog"], g["fav_won"], g["sim_p"], g["rnd"]))
predict([(s, a, b) for s, a, b, *_ in rows])
for lab, rr in (("Sweet 16 + Elite 8", [r for r in rows if r[5] in ("Sweet 16", "Elite Eight")]), ("Final Four + title", [r for r in rows if r[5] not in ("Sweet 16", "Elite Eight")])):
    sm = sum((r[4] >= .5) == r[3] for r in rr); mo = sum((pm(r[0], r[1], r[2]) >= .5) == r[3] for r in rr)
    mx = sum(((.5 * r[4] + .5 * pm(r[0], r[1], r[2])) >= .5) == r[3] for r in rr); fv = sum(r[3] for r in rr)
    print(f"real {lab} games ({len(rr)}): simulator (game-file line) {sm} | model {mo} | 50/50 {mx} | game-file favorite {fv}")
json.dump(OUT, open(os.path.join(HERE, "m313_out.json"), "w"))
