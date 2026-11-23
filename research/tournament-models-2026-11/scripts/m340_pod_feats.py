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
netv = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
OUT = {}
for s in SEASONS:
    g = BI[s]["games"]
    for q in range(16):
        A = list(dict.fromkeys([g[2 * q]["H"], g[2 * q]["L"]])); Bm = list(dict.fromkeys([g[2 * q + 1]["H"], g[2 * q + 1]["L"]])); tm = A + Bm
        win = {}
        for t in A: win[t] = p1(s, g[2 * q], "model")[t] * sum(p1(s, g[2 * q + 1], "model")[o] * p2(s, t, o, "model") for o in Bm)
        for t in Bm: win[t] = p1(s, g[2 * q + 1], "model")[t] * sum(p1(s, g[2 * q], "model")[o] * p2(s, t, o, "model") for o in A)
        qr = q // 2; other_pod = 2 * qr + (1 - q % 2); go = [x for x in (g[2 * other_pod]["H"], g[2 * other_pod]["L"], g[2 * other_pod + 1]["H"], g[2 * other_pod + 1]["L"])]
        reg = q // 4; rteams = {x for qq in range(reg * 4, reg * 4 + 4) for x in (g[2 * qq]["H"], g[2 * qq]["L"], g[2 * qq + 1]["H"], g[2 * qq + 1]["L"])}
        for t in tm:
            oth = [o for o in tm if o != t]; r1opp = [o for o in (A if t in A else Bm) if o != t]
            OUT.setdefault(s, {})[kk(t)] = {
                "pod_win_chance": win[t], "pod_others_net_mean": float(np.mean([netv(s, o) for o in oth])), "pod_others_net_max": float(max(netv(s, o) for o in oth)),
                "r1_opponent_net": float(np.mean([netv(s, o) for o in r1opp])) if r1opp else -30.0,
                "other_pod_net_mean": float(np.mean([netv(s, o) for o in go])), "other_pod_net_max": float(max(netv(s, o) for o in go)),
                "region_net_mean": float(np.mean([netv(s, o) for o in rteams if o != t])),
                "path_net_sum": float(np.mean([netv(s, o) for o in oth]) + max(netv(s, o) for o in go))}
json.dump(OUT, open(os.path.join(HERE, "m340_pod_feats.json"), "w")); print("teams", sum(map(len, OUT.values())))
