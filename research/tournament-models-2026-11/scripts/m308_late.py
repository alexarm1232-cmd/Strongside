# Sweet 16 -> title: many ways to pick, Rounds 1-2 fixed to the vote (and blend). Scored 4-8-16-32 + early points.
import os, json, contextlib, io, itertools, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m302_full_brackets.py"), encoding="utf-8-sig").read(); src = src[:src.index('print(f"{\'Full bracket')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
FULL = json.load(open(os.path.join(HERE, "m307_full.json")))

# ---- field in tree order (regions reordered so Final Four pairs sit side by side) ----
def field(s):
    g = BI[s]["games"]; order = [r for pr in FFPAIR[s] for r in pr]
    slots = []
    for r in order:
        for x in g[r * 8:(r + 1) * 8]: slots += [x["H"], None if x["H"] == x["L"] else x["L"]]
    return slots, order
PK = os.path.join(HERE, "m308_pairs.pkl")
if os.path.exists(PK): CACHE.update(pickle.load(open(PK, "rb")))
reqs = []
for s in SEASONS:
    tm = [t for t in field(s)[0] if t]
    reqs += [(s, a, b) for a, b in itertools.combinations(tm, 2)]
predict(reqs); pickle.dump(CACHE, open(PK, "wb"))

def adv(s, pf):
    """P(team wins round r), r=1..6, from the real field with head-to-head chance pf(s,a,b)"""
    slots, _ = field(s); lvl = [{t: 1.0} if t else {} for t in slots]; out = {t: [0] * 7 for t in slots if t}
    for r in range(1, 7):
        nxt = []
        for i in range(0, len(lvl), 2):
            L, R_ = lvl[i], lvl[i + 1]; d = {}
            if not R_: d = dict(L)
            else:
                for a in L: d[a] = L[a] * sum(R_[b] * pf(s, a, b) for b in R_)
                for b in R_: d[b] = R_[b] * sum(L[a] * pf(s, b, a) for a in L)
            for t in d: out[t][r] = d[t]
            nxt.append(d)
        lvl = nxt
    return out

# ---- bracket from Rounds 1-2 picks to a full tree in tree order ----
def r2_tree(s, o):
    """16 Round-2 winners in tree order"""
    r2 = [e["pick"] for e in o["rounds"][1]]; _, order = field(s)
    return [r2[r * 4 + k] for r in order for k in range(4)]
def fill(s, top16, chooser):
    rounds = []; cur = top16
    for r in range(3, 7):
        cur = [chooser(s, cur[2 * i], cur[2 * i + 1], r) for i in range(len(cur) // 2)]; rounds.append(cur)
    return rounds
def ep_fill(s, top16, A):
    """pick S16-title to maximize expected points, A = advancement chances"""
    def best(lo, hi, r):          # node covering top16[lo:hi], round r -> {team: best subtree score if team wins}
        if r == 2: return {top16[lo]: 0.0}
        m = (lo + hi) // 2; L, R_ = best(lo, m, r - 1), best(m, hi, r - 1)
        bl, br = max(L.values()), max(R_.values()); d = {}
        for t, v in L.items(): d[t] = v + br + PTS[r - 1] * A[t][r]
        for t, v in R_.items(): d[t] = v + bl + PTS[r - 1] * A[t][r]
        return d
    def trace(lo, hi, r, t, out):
        if r == 2: return
        m = (lo + hi) // 2; L, R_ = best(lo, m, r - 1), best(m, hi, r - 1)
        out[r].append((lo, t))
        if t in L: trace(lo, m, r - 1, t, out); trace(m, hi, r - 1, max(R_, key=R_.get), out)
        else: trace(lo, m, r - 1, max(L, key=L.get), out); trace(m, hi, r - 1, t, out)
    D = best(0, 16, 6); ch = max(D, key=D.get); out = {r: [] for r in range(3, 7)}; trace(0, 16, 6, ch, out)
    return [[t for _, t in sorted(out[r])] for r in range(3, 7)]
def score_late(s, rounds):
    w = WON[s]; c = [sum(w.get(t, 0) >= r for t in rounds[r - 3]) for r in range(3, 7)]
    return c, sum(ci * PTS[r - 1] for ci, r in zip(c, range(3, 7)))
def oracle(s, top16):
    w = WON[s]; return fill(s, top16, lambda s_, a, b, r: a if w.get(a, 0) >= w.get(b, 0) else b)

# ---- head-to-head chance sources ----
pm = lambda s, a, b: p(s, a, b)
seed = lambda s, t: seed_of(s, t)
net = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
# seed-vs-seed history and net-gap logistic, each year from the other years' real games (all rounds, no First Four)
GM = [(x["season"], x["fav"], x["dog"], bool(x["fav_won"]), x["fseed"], x["dseed"]) for x in G
      if x["rnd"] != "First Four" and x["season"] in SEASONS]
def fit_logit(xs, ys):
    b = 0.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-b * xs)); b += np.sum(xs * (ys - q)) / (np.sum(xs * xs * q * (1 - q)) + 1e-9)
    return b
BNET, BSEED = {}, {}
for s in SEASONS:
    rows = [x for x in GM if x[0] != s]; ys = np.array([x[3] for x in rows], float)
    xs = np.array([net(x[0], x[1]) - net(x[0], x[2]) for x in rows]); BNET[s] = fit_logit(xs, ys)
    xs = np.array([np.log(x[5] / x[4]) for x in rows]); BSEED[s] = fit_logit(xs, ys)
print("real games used for seed/net lines:", len(GM))
pnet = lambda s, a, b: 1 / (1 + np.exp(-BNET[s] * (net(s, a) - net(s, b))))
pseed = lambda s, a, b: 1 / (1 + np.exp(-BSEED[s] * np.log(seed(s, b) / seed(s, a))))
def mixp(*ws):
    def f(s, a, b):
        z = sum(w * np.log(q(s, a, b) / (1 - q(s, a, b))) for w, q in ws); return 1 / (1 + np.exp(-z))
    return f
pick_by = lambda pf: (lambda s, a, b, r: a if pf(s, a, b) >= .5 else b)
chalk = lambda s, a, b, r: a if (seed(s, a), -net(s, a)) <= (seed(s, b), -net(s, b)) else b

METHODS = {
 "Regular model (S16-title)": ("h2h", pm),
 "Higher seed": ("chalk", None),
 "Pre-tourney net rating": ("h2h", pnet),
 "Model + net rating (50/50)": ("h2h", mixp((.5, pm), (.5, pnet))),
 "Model + seed (50/50)": ("h2h", mixp((.5, pm), (.5, pseed))),
 "Expected points, model": ("ep", pm),
 "Expected points, net rating": ("ep", pnet),
 "Expected points, model+net": ("ep", mixp((.5, pm), (.5, pnet))),
 "Expected points, seed history": ("ep", pseed),
}
res = {}
for key in ("vote", "blend"):
    print(f"\n===== Rounds 1-2 = {key}")
    rows = {}
    base = {o["season"]: o for o in FULL[key]}
    early = {s: base[s]["score"][0] + 2 * base[s]["score"][1] for s in SEASONS}
    cur = {s: sum(c * pt for c, pt in zip(base[s]["score"][2:], PTS[2:])) for s in SEASONS}
    rows["Current (model S16/E8, 70/30 F4/T)"] = [cur[s] for s in SEASONS]
    rows["Best possible (oracle)"] = [score_late(s, oracle(s, r2_tree(s, base[s])))[1] for s in SEASONS]
    for name, (kind, pf) in METHODS.items():
        yr = []
        for s in SEASONS:
            t16 = r2_tree(s, base[s])
            if kind == "chalk": rd = fill(s, t16, chalk)
            elif kind == "h2h": rd = fill(s, t16, pick_by(pf))
            else: rd = ep_fill(s, t16, adv(s, pf))
            yr.append(score_late(s, rd)[1])
        rows[name] = yr
    yrs = [int(s[:4]) + 1 for s in SEASONS]
    print(f"{'S16-title method':36} | late | total | yrs>=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
    for n, yr in rows.items():
        tot = [early[s] + v for s, v in zip(SEASONS, yr)]
        print(f"{n:36} | {sum(yr):4} | {sum(tot):5} | {sum(t >= 100 for t in tot):8} | " + " ".join(f"{t:3}" for t in tot))
    print(f"{'(early points R1+R32)':36} | {'':4} | {sum(early.values()):5} | {'':8} | " + " ".join(f"{early[s]:3}" for s in SEASONS))
    res[key] = rows
json.dump(res, open(os.path.join(HERE, "m308_out.json"), "w"))
