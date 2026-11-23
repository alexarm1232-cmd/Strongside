# Pod bracket (60% rule + pod Round of 32) with the Sweet 16 picked by the late line + a pod-strength gap; rest unchanged.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
for s_, v in json.load(open(os.path.join(HERE, "m335_sim_extra.json"))).items():
    for k_, q in v.items(): a, b = k_.split("|"); put(s_, a, b, q)
PF = json.load(open(os.path.join(HERE, "m340_pod_feats.json")))
POD = {o["season"]: o for o in json.load(open(os.path.join(HERE, "m335_full.json")))["pod"]}
def other(i): g = G[i]; return g["dog"] if kk(g["fav"]) == kk(B.Sname[i]) else g["fav"]
val = lambda s, t, key: (PF.get(s, {}).get(kk(t)) or {}).get(key)
LATE_ = Q.S16 | Q.E8 | Q.F4T; fitb = Q.t_ridge(X=XX)
def line_with(key):
    """per season: P(a beats b) for bracket Sweet 16 pairs with the extra gap input"""
    gv = np.array([(lambda a, b: np.nan if a is None or b is None else a - b)(val(seas[i], B.Sname[i], key), val(seas[i], other(i), key)) for i in range(len(G))], float)
    def run(reqs):
        rows = []; info = []
        for s, a, b in reqs:
            S_, W_, x, _ = features(s, kk(a), kk(b)); rows.append(x); va, vb = val(s, S_, key), val(s, W_, key)
            info.append((s, a, b, S_, ex_of(s, S_, W_), (va - vb) if va is not None and vb is not None else np.nan))
        Xe = np.vstack([XX, np.array(rows)]); fx = Q.t_ridge(X=Xe); out = {}
        for s in SEASONS:
            te = np.array([N + j for j, r in enumerate(info) if r[0] == s])
            if len(te) == 0: continue
            tr = np.where((seas != s) & k)[0]; m_tr, m_te = Q.base(tr, te, fx); a_ = LATE_[tr]
            mu = np.nanmean(gv[tr][a_]); sd = np.nanstd(gv[tr][a_]) + 1e-9; etr = np.nan_to_num((gv[tr][a_] - mu) / sd)
            ete = np.nan_to_num((np.array([info[j - N][5] for j in te]) - mu) / sd)
            f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_], etr]), y_[tr][a_], WT[tr][a_])
            z = f(np.column_stack([m_te, np.array([info[j - N][4] for j in te]), ete]))
            for j, zz in zip(te, z):
                s_, a, b, S_, _, _ = info[j - N]; pS = 1 / (1 + np.exp(-zz)); out[(s_, a, b)] = pS if kk(a) == S_ else 1 - pS
        return out
    return run
late = chooser_w(0); miss = set(); FFMISS = set()
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + j] for r in order for j in range(4)]
def run_bracket(s16p):
    tot = []; cs = np.zeros(6, int)
    for s in SEASONS:
        o = POD[s]; r2 = [e["pick"] for e in o["rounds"][1]]
        def ch(s_, a, b, r):
            if r == 3 and s16p is not None:
                p = s16p.get((s_, a, b)); p = p if p is not None else 1 - s16p[(s_, b, a)]; return a if p >= .5 else b
            if r >= 5 and SIM.get((s_, a, b)) is None: FFMISS.add((s_, a, b))
            return late(s_, a, b, r)
        c, pts = score_late(s, fill(s, tree16(s, r2), ch)); c12 = o["score"][:2]; cs += c12 + list(c); tot.append(c12[0] + 2 * c12[1] + pts)
    return cs, tot
base_cs, base_tot = run_bracket(None)
print(f"{'Sweet 16 picker':48} | S16 | E8 | F4 | T | total | better/worse years")
print(f"{'current line (pod bracket as published)':48} | {base_cs[2]:3} | {base_cs[3]:2} | {base_cs[4]:2} | {base_cs[5]} | {sum(base_tot):5} |")
for key, lab in (("pod_others_net_mean", "+ own pod-mates' strength"), ("other_pod_net_mean", "+ other pod's strength"), ("region_net_mean", "+ region strength")):
    reqs = []
    for s in SEASONS:
        r2 = [e["pick"] for e in POD[s]["rounds"][1]]; t16 = tree16(s, r2); reqs += [(s, t16[2 * i], t16[2 * i + 1]) for i in range(8)]
    P16 = line_with(key)(reqs); cs, tot = run_bracket(P16)
    print(f"{lab:48} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {sum(tot):5} | {sum(a > b for a, b in zip(tot, base_tot))}/{sum(a < b for a, b in zip(tot, base_tot))}")
print("Final Four / title pairs without a simulator run (model used):", len([x for x in need if x[0] in SEASONS]))

print('F4/title missing:', sorted(FFMISS))

