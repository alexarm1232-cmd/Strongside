# Round 1 with the Upset Model weighted more; Round of 32 = vote of the 3 on each bracket's own matchups. Bracket filled before Round 1.
import os, sys, json, contextlib, io, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m282_bracket_r1r2.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D186 = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
sig = lambda z: 1 / (1 + np.exp(-z))
R1P = {}
for r, p in zip(D186["rows"], pho):
    i = r["i"]; hs = r["HisS"]; R1P[str(G[i]["gid"])] = (float(p), float(sig(-OUT_I[i]) if hs else sig(OUT_I[i])), float(1 - B.simS[i] if hs else B.simS[i]))
def rule_vote(u, m, si): return ((u >= .4) + (m >= .5) + (si >= .5)) >= 2
def rule_upset(u, m, si): return u >= .4
def rule_over(x):
    def f(u, m, si):
        up = u >= .4; mo, so = m >= .5, si >= .5
        if mo == so != up and min(abs(m - .5), abs(si - .5)) + .5 >= x: return mo   # both others disagree, each at least x sure
        return up
    return f
def rule_blend(w, c): return lambda u, m, si: w * u + (1 - w) / 2 * (m + si) >= c
R1OPT = {"vote (current)": rule_vote, "upset model alone @40": rule_upset}
for x in (.6, .65, .7, .75): R1OPT[f"upset unless both others >= {int(x * 100)}% sure"] = rule_over(x)
for w in (.5, .6, .75):
    for c in (.40, .45): R1OPT[f"blend {w:.2f} upset + rest @{int(c * 100)}"] = rule_blend(w, c)
def r1picks(s, rule):
    out = []
    for g in BI[s]["games"]:
        if g["H"] == g["L"]: out.append(g["H"]); continue
        out.append(g["L"] if rule(*R1P[str(g["gid"])]) else g["H"])
    return out
PICKS = {lab: {s: r1picks(s, f) for s in SEASONS} for lab, f in R1OPT.items()}
pairs = {s: sorted({(pk[s][2 * q], pk[s][2 * q + 1]) for pk in PICKS.values() for q in range(16)}) for s in SEASONS}
json.dump({s: [list(x) for x in v] for s, v in pairs.items()}, open(os.path.join(HERE, "m320_pairs.json"), "w"))
print(subprocess.run([sys.executable, os.path.join(HERE, "m320_upset_pairs.py")], capture_output=True, text=True).stdout.strip())
UPP = json.load(open(os.path.join(HERE, "m320_upset_p.json")))
NEW = []; RQ = []
for s, prs in pairs.items():
    for a, b in prs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); NEW.append(x); RQ.append((s, a, b, S_, W_, ex_of(s, S_, W_)))
Xe = np.vstack([XX, np.array(NEW)]); fit2 = Q.t_ridge(X=Xe); MZ = {}
for s in SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.array([N + j for j, r in enumerate(RQ) if r[0] == s])
    m_tr, m_te = Q.base(tr, te, fit2); a_ = E12[tr]
    f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
    z = f(np.column_stack([m_te, np.array([RQ[j - N][5] for j in te])]))
    for j, zz in zip(te, z): r = RQ[j - N]; MZ[(s, r[1], r[2])] = (r[3], r[4], float(zz))
SR = json.load(open(os.path.join(HERE, "m283_sim_r32.json")))
X = os.path.join(HERE, "m320_sim_extra.json")
if os.path.exists(X):
    for s, v in json.load(open(X)).items(): SR[s].update(v)
need = set()
def model_pick(s, a, b):
    S_, W_, z = MZ[(s, a, b)]
    if abs(z) < 1e-12: return chalk2(s, a, b)
    w = S_ if z > 0 else W_; return a if kk(a) == w else b
def sim_pick(s, a, b):
    p = SR[s].get(f"{a}|{b}")
    if p is None:
        q = SR[s].get(f"{b}|{a}")
        if q is None: need.add((s, a, b)); return None
        p = 1 - q
    return chalk2(s, a, b) if abs(p - .5) < 1e-9 else (a if p > .5 else b)
def up_pick(s, a, b): h, l, pu = UPP[f"{s}|{a}|{b}"]; return l if pu >= .45 else h
def vote(v):
    v = [x for x in v if x is not None]
    return max(set(v), key=v.count) if len(v) == 3 or (len(v) == 2 and v[0] == v[1]) else None
WON = {}
for s in SEASONS:
    w = dict(BI[s]["wins"])
    for g in BI[s]["games"]:
        if g["H"] == g["L"]: w[g["H"]] = w.get(g["H"], 0) + 1
    WON[s] = w
print(f"\n{'Round 1 rule':40} | R1 | R32 (vote) | points | R32 if upset R32 model alone | unresolved R32 (sim missing)")
RES = {}
for lab in R1OPT:
    r1 = r2 = r2u = unres = 0; yr = []
    for s in SEASONS:
        g = BI[s]["games"]; pk = PICKS[lab][s]; a1 = sum(p == x["won"] for p, x in zip(pk, g) if x["H"] != x["L"]); a2 = 0
        for q in range(16):
            a, b = pk[2 * q], pk[2 * q + 1]; v = vote([up_pick(s, a, b), model_pick(s, a, b), sim_pick(s, a, b)])
            if v is None: unres += 1; continue
            a2 += WON[s].get(v, 0) >= 2; r2u += WON[s].get(up_pick(s, a, b), 0) >= 2
        r1 += a1; r2 += a2; yr.append(a1 + 2 * a2)
    RES[lab] = yr; print(f"{lab:40} | {r1} | {r2:3} | {r1 + 2 * r2:4} | {r2u:3} | {unres}")
miss = {}
for s, a, b in sorted(need): miss.setdefault(s, []).append([a, b])
json.dump(miss, open(os.path.join(HERE, "m320_need.json"), "w")); print("sim pairs needed:", sum(len(v) for v in miss.values())); print(json.dumps(miss))
json.dump({"by_year": RES, "picks": PICKS}, open(os.path.join(HERE, "m320_out.json"), "w"))
