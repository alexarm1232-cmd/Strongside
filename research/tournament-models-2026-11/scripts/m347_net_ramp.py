# Pick each pod (4 teams) as a unit: pod-win chance = P(win R1) x sum over possible opponents P(opp wins R1) x P(beat opp).
# Round of 32 pick = most likely pod winner; it wins its Round 1 game; the pod's other Round 1 game uses the Round 1 rule.
# Scored on Rounds 1-2 and the full bracket (later rounds as now).
import os, json, contextlib, io, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
UPP.update(json.load(open(os.path.join(HERE, "m328_upset_p.json")))); MZ.update(pickle.load(open(os.path.join(HERE, "m328_mz.pkl"), "rb")))
for s, v in json.load(open(os.path.join(HERE, "m328_sim.json"))).items(): SR[s].update(v)
def p2(s, a, b, how):
    """chance a beats b in the Round of 32"""
    h, l, pu = UPP.get(f"{s}|{a}|{b}") or (lambda r: (r[0], r[1], r[2]))(UPP[f"{s}|{b}|{a}"]); pa_u = pu if a == l else 1 - pu
    key = (s, a, b) if (s, a, b) in MZ else (s, b, a); S_, W_, z = MZ[key]; pS = float(sig(z)); pa_m = pS if kk(a) == S_ else 1 - pS
    q = SR[s].get(f"{a}|{b}"); pa_s = q if q is not None else 1 - SR[s][f"{b}|{a}"]
    return {"avg3": (pa_u + pa_m + pa_s) / 3, "model": pa_m, "upset+model": (pa_u + pa_m) / 2, "model+sim": (pa_m + pa_s) / 2, "upset": pa_u}[how]
def p1(s, g, how):
    """chance each team wins its Round 1 game -> dict"""
    if g["H"] == g["L"]: return {g["H"]: 1.0}
    u, m, si = R1P[str(g["gid"])]; pl = {"avg3": (u + m + si) / 3, "model": m, "upset+model": (u + m) / 2, "model+sim": (m + si) / 2, "upset": u}[how]
    return {g["L"]: pl, g["H"]: 1 - pl}
def pod(s, q, r1rule_picks, h1, h2):
    g = BI[s]["games"]; A, Bm = p1(s, g[2 * q], h1), p1(s, g[2 * q + 1], h1)
    win = {}
    for t, pt in A.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in Bm.items())
    for t, pt in Bm.items(): win[t] = pt * sum(po * p2(s, t, o, h2) for o, po in A.items())
    w = max(win, key=win.get)
    r1 = list(r1rule_picks[2 * q:2 * q + 2])
    if w in A: r1[0] = w
    else: r1[1] = w
    return r1, w
R1 = "upset unless both others >= 60% sure"
# net-rating chance, logistic on the pre-tournament net gap, each year fit on the other years' real games (no First Four)
netv = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
GMX = [(g["season"], g["fav"], g["dog"], bool(g["fav_won"])) for g in G if g["rnd"] != "First Four" and g["season"] in SEASONS]
def fit_logit(xs, ys_):
    b = 0.0
    for _ in range(50): q = 1 / (1 + np.exp(-b * xs)); b += np.sum(xs * (ys_ - q)) / (np.sum(xs * xs * q * (1 - q)) + 1e-9)
    return b
BN = {s: fit_logit(np.array([netv(x[0], x[1]) - netv(x[0], x[2]) for x in GMX if x[0] != s]), np.array([x[3] for x in GMX if x[0] != s], float)) for s in SEASONS}
pnet = lambda s, a, b: 1 / (1 + np.exp(-BN[s] * (netv(s, a) - netv(s, b))))
STEPS = [0, .05, .1, .15, .2, .25]
STAGE = {}
for a_ in STEPS:
    R1B, R32B = {}, {}
    for s in SEASONS:
        g = BI[s]["games"]; r1n = []; r2n = []
        for q in range(16):
            A, Bm = p1(s, g[2 * q], "model"), p1(s, g[2 * q + 1], "model"); win = {}
            pp = lambda t, o: (1 - a_) * p2(s, t, o, "model") + a_ * pnet(s, t, o)
            for t, pt in A.items(): win[t] = pt * sum(po * pp(t, o) for o, po in Bm.items())
            for t, pt in Bm.items(): win[t] = pt * sum(po * pp(t, o) for o, po in A.items())
            w = max(win, key=win.get); r1 = list(PICKS[R1][s][2 * q:2 * q + 2])
            if w in A: r1[0] = w
            else: r1[1] = w
            r1n += r1; r2n.append(w)
        R1B[s], R32B[s] = r1n, r2n
    STAGE[a_] = (R1B, R32B)
keep = dict(STAGE=STAGE, STEPS=STEPS, BN=BN)
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
globals().update(keep)
netv2 = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
pn = lambda s, a, b: 1 / (1 + np.exp(-BN[s] * (netv2(s, a) - netv2(s, b))))
FFMISS = set()
yrs = [int(s[:4]) + 1 for s in SEASONS]
print(f"{'net-rating share by round (R1/R32/S16/E8/F4+T)':48} | R1 | R32 | S16 | E8 | F4 | T | total | better/worse yrs vs current")
BASE = None
for a_ in STEPS:
    R1B, R32B = STAGE[a_]; reqs = []
    for s in SEASONS: r2 = R32B[s]; t16 = tree16(s, r2); reqs += [(s, t16[2 * i], t16[2 * i + 1]) for i in range(8)]
    P16 = line_with("pod_others_net_mean")(reqs); p16 = lambda s, a, b: P16[(s, a, b)] if (s, a, b) in P16 else 1 - P16[(s, b, a)]
    cs = np.zeros(6, int); tot = []
    for s in SEASONS:
        g = BI[s]["games"]; w = WON[s]
        def ch(s_, a, b, r):
            if r == 3: p = (1 - 2 * a_) * p16(s_, a, b) + 2 * a_ * pn(s_, a, b)
            elif r == 4: predict([(s_, a, b)]); p = (1 - 3 * a_) * pm(s_, a, b) + 3 * a_ * pn(s_, a, b)
            else:
                predict([(s_, a, b)]); q = SIM.get((s_, a, b))
                if q is None: FFMISS.add((s_, a, b)); q = pm(s_, a, b)
                p = (1 - 4 * a_) * (.7 * q + .3 * pm(s_, a, b)) + 4 * a_ * pn(s_, a, b)
            return a if p >= .5 else b
        c1 = sum(p_ == x["won"] for p_, x in zip(R1B[s], g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in R32B[s])
        c, pts = score_late(s, fill(s, tree16(s, R32B[s]), ch)); cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
    if BASE is None: BASE = tot
    lab = "/".join(f"{int(round(x * 100))}%" for x in (0, a_, 2 * a_, 3 * a_, 4 * a_))
    print(f"{lab:48} | {cs[0]} | {cs[1]} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {sum(tot):5} | {sum(x > y for x, y in zip(tot, BASE))}/{sum(x < y for x, y in zip(tot, BASE))}")
print("Final Four / title pairs without a simulator run (model used there):", sorted(FFMISS))

