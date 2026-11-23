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
def r1chance(s, g, a, how):
    """chance a wins its Round 1 game g"""
    d = p1(s, g, how); return d.get(a, 0.0)
def pod_rank(s, q, how):
    """rank the 4 pod teams by average chance to beat the other 3 (Round 1 line for same-game pairs, Round of 32 line otherwise)"""
    g = BI[s]["games"]; A = list(dict.fromkeys([g[2 * q]["H"], g[2 * q]["L"]])); Bm = list(dict.fromkeys([g[2 * q + 1]["H"], g[2 * q + 1]["L"]]))
    tm = A + Bm; sc = {}
    for t in tm:
        v = []
        for o in tm:
            if o == t: continue
            same = (t in A) == (o in A)
            v.append(r1chance(s, g[2 * q] if t in A else g[2 * q + 1], t, how) if same else p2(s, t, o, how))
        sc[t] = sum(v) / len(v)
    return sorted(tm, key=lambda t: -sc[t]), set(A)
def forced_r1(r1rule, q, w, Aset):
    r1 = list(r1rule[2 * q:2 * q + 2])
    if w in Aset: r1[0] = w
    else: r1[1] = w
    return r1
HOWS = ("model", "avg3", "upset")
RANK = {(s, q, h): pod_rank(s, q, h) for s in SEASONS for q in range(16) for h in HOWS}
BASE = {}
for r1lab in ("vote (current)", R1):
    tag = "vote" if r1lab.startswith("vote") else "60%"
    BASE[tag] = {"r1": PICKS[r1lab], "vote32": {s: [vote([up_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), model_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1]), sim_pick(s, PICKS[r1lab][s][2 * q], PICKS[r1lab][s][2 * q + 1])]) for q in range(16)] for s in SEASONS}}
FR = {(tag, s, q, w): forced_r1(BASE[tag]["r1"][s], q, w, RANK[(s, q, "model")][1]) for tag in BASE for s in SEASONS for q in range(16) for w in RANK[(s, q, "model")][0]}
keep = dict(RANK=RANK, BASE=BASE, FR=FR)
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
RANK, BASE, FR = keep["RANK"], keep["BASE"], keep["FR"]; late = chooser_w(0)
import itertools
reqs = []
for s in SEASONS:
    sl, order = field(s)
    tm = [t for t in sl if t]
    reqs += [(s, a, b) for a, b in itertools.combinations(tm, 2)]
predict(reqs)
def tree16(s, r2):
    _, order = field(s); return [r2[r * 4 + j] for r in order for j in range(4)]
def grp_rank(s, teams):
    sc = {t: sum(pm(s, t, o) for o in teams if o != t) / (len(teams) - 1) for t in teams}; return sorted(teams, key=lambda t: -sc[t])
def build(tag, s, how, top):
    """top: None (pods only) | 's16' (rank 8-team quarters first) | 'e8' (rank 16-team regions first, then quarters)"""
    r1 = []; r2 = []; forced = {}
    g = BI[s]["games"]
    for reg in range(4):
        pods = list(range(reg * 4, reg * 4 + 4)); teams = lambda qs: [t for q in qs for t in RANK[(s, q, how)][0]]
        if top == "e8":
            w = grp_rank(s, teams(pods))[0]; forced[w] = 4
        for half in (pods[:2], pods[2:]):
            ft = [t for t in teams(half) if forced.get(t, 0) >= 3]
            if top in ("s16", "e8") and not ft:
                w = grp_rank(s, teams(half))[0]; forced[w] = max(forced.get(w, 0), 3)
            for q in half:
                order_, Aset = RANK[(s, q, how)]; f = [t for t in order_ if forced.get(t, 0) >= 2]
                w = f[0] if f else order_[0]; forced[w] = max(forced.get(w, 0), 2)
                r1 += FR[(tag, s, q, w)]; r2.append(w)
    return r1, r2, forced
def chooser_forced(forced):
    def ch(s_, a, b, r):
        fa, fb = forced.get(a, 0) >= r, forced.get(b, 0) >= r
        if fa and not fb: return a
        if fb and not fa: return b
        return late(s_, a, b, r)
    return ch
print(f"{'Round 1 rule | method':58} | R1 | R32 | S16 | E8 | F4 | T | R1-2 | total | better/worse vs vote")
BY = {}
for tag in ("vote", "60%"):
    rows_ = [("vote", None, None)] + [(f"rank pods ({h})", h, None) for h in HOWS] + [(f"rank quarters (S16 line) -> pods ({h})", h, "s16") for h in HOWS] + [(f"rank regions -> quarters -> pods ({h})", h, "e8") for h in ("model",)]
    for lab, how, top in rows_:
        cs = np.zeros(6, int); tot = []
        for s in SEASONS:
            g = BI[s]["games"]; w = WON[s]
            if how is None: r1, r2, forced = BASE[tag]["r1"][s], BASE[tag]["vote32"][s], {}
            else: r1, r2, forced = build(tag, s, how, top)
            c1 = sum(p_ == x["won"] for p_, x in zip(r1, g) if x["H"] != x["L"]); c2 = sum(w.get(t, 0) >= 2 for t in r2)
            c, pts = score_late(s, fill(s, tree16(s, r2), chooser_forced(forced))); cs += [c1, c2] + list(c); tot.append(c1 + 2 * c2 + pts)
        BY[(tag, lab)] = tot; base = BY[(tag, "vote")]
        print(f"{tag + ' | ' + lab:58} | {cs[0]} | {cs[1]} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]} | {cs[0] + 2 * cs[1]:4} | {sum(tot):5} | {sum(a > b for a, b in zip(tot, base))}/{sum(a < b for a, b in zip(tot, base))}")
