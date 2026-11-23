# Full brackets filled out before Round 1, 2010-2026, scored 1-2-4-8-16-32 against what happened.
# Rounds 1-2 from each picker; Sweet 16 to title from the regular model (patched 752 version: Sweet 16 to title share one
# line, base score + coach + star, no simulator), each year from a model trained on the other 15.
#   Vote of the 3 -> regular | Blend -> regular | Upset models -> regular | Regular model all the way | Higher seed all the way
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m282_bracket_r1r2.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
S16E8, F4T_ = Q.S16 | Q.E8, Q.F4T; LATE = S16E8 | F4T_
B3 = {d["season"]: d for d in json.load(open(os.path.join(HERE, "m293_brackets_three.json")))}
B4 = {d["season"]: d for d in json.load(open(os.path.join(HERE, "m285_brackets.json")))}
CACHE = {}
def predict(reqs):
    """reqs: list of (s, a, b) -> fills CACHE with P(a beats b), late-round line, held out by season"""
    reqs = [r for r in dict.fromkeys(reqs) if r not in CACHE and (r[0], r[2], r[1]) not in CACHE]
    if not reqs: return
    rows = []; info = []
    for s, a, b in reqs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); rows.append(x); info.append((s, a, b, S_, ex_of(s, S_, W_)))
    Xe = np.vstack([XX, np.array(rows)]); fitx = Q.t_ridge(X=Xe)
    for s in SEASONS:
        te = np.array([N + j for j, r in enumerate(info) if r[0] == s])
        if len(te) == 0: continue
        tr = np.where((seas != s) & k)[0]; m_tr, m_te = Q.base(tr, te, fitx); a_ = LATE[tr]
        f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
        z = f(np.column_stack([m_te, np.array([info[j - N][4] for j in te])]))
        for j, zz in zip(te, z):
            s_, a, b, S_, _ = info[j - N]; pS = 1 / (1 + np.exp(-zz)); CACHE[(s_, a, b)] = pS if kk(a) == S_ else 1 - pS
def p(s, a, b):
    return CACHE[(s, a, b)] if (s, a, b) in CACHE else 1 - CACHE[(s, b, a)]
# real results: rounds won, with the 2021 no-contest counted
WON = {}
for s in SEASONS:
    w = dict(BI[s]["wins"])
    for g in BI[s]["games"]:
        if g["H"] == g["L"]: w[g["H"]] = w.get(g["H"], 0) + 1
    WON[s] = w
region_of = {}
for s in SEASONS:
    for j, g in enumerate(BI[s]["games"]):
        for t in (g["H"], g["L"]): region_of[(s, t)] = j // 8
FFPAIR = {}
for s in SEASONS:
    ff = [g for g in G if g["season"] == s and g["rnd"] == "Final Four"]
    prs = []
    for g in ff:
        ra = next((region_of[(s, t)] for t in (g["fav"], g["dog"]) if (s, t) in region_of), None)
        rb = [region_of.get((s, t)) for t in (g["fav"], g["dog"])]
        prs.append(tuple(sorted(rb)))
    FFPAIR[s] = prs
nm2 = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -99
def chalk_pick(s, a, b):
    sa, sb = seed_of(s, a), seed_of(s, b)
    if sa != sb: return a if sa < sb else b
    return a if nm2(s, a) >= nm2(s, b) else b
PTS = [1, 2, 4, 8, 16, 32]
def later_rounds(s, r32winners, chooser):
    """r32winners: 16 teams in bracket order -> list of rounds of picks [S16(8), E8(4), F4(2), title(1)]"""
    out = []; cur = r32winners
    s16 = [chooser(s, cur[2 * i], cur[2 * i + 1]) for i in range(8)]; out.append(s16)
    e8 = [chooser(s, s16[2 * i], s16[2 * i + 1]) for i in range(4)]; out.append(e8)
    f4 = [chooser(s, e8[a], e8[b]) for a, b in FFPAIR[s]]; out.append(f4)
    out.append([chooser(s, f4[0], f4[1])]); return out
BRK = {"Vote of the 3 -> regular": ("vote", B3), "Blend -> regular": ("blend", B3), "Upset models -> regular": ("upset", B3),
       "Regular model all the way": ("model", B4), "Higher seed all the way": ("seed", B4)}
def r12(s, key, src_): b = src_[s]["brackets"][key]; return [x["pick"] for x in b["r1"]], [x["pick"] for x in b["r2"]]
# batch the regular model's chances round by round
for depth in range(4):
    reqs = []
    for lab, (key, src_) in BRK.items():
        if key == "seed": continue
        for s in SEASONS:
            _, r2 = r12(s, key, src_); cur = r2
            try:
                rounds = later_rounds(s, cur, lambda s_, a, b: a if p(s_, a, b) >= .5 else b)
            except KeyError:
                pass
            # collect the pairs needed at the first missing depth
            def collect(s_, a, b):
                if (s_, a, b) not in CACHE and (s_, b, a) not in CACHE: reqs.append((s_, a, b)); raise KeyError
                return a if p(s_, a, b) >= .5 else b
            try: later_rounds(s, cur, collect)
            except KeyError: pass
    if not reqs: break
    # a KeyError stops at the first missing pair per bracket-year; gather all missing at this depth by a softer pass
    predict(reqs)
    # second sweep at the same depth until no new pairs
    while True:
        more = []
        for lab, (key, src_) in BRK.items():
            if key == "seed": continue
            for s in SEASONS:
                _, r2 = r12(s, key, src_)
                def col2(s_, a, b):
                    if (s_, a, b) not in CACHE and (s_, b, a) not in CACHE: more.append((s_, a, b)); return a
                    return a if p(s_, a, b) >= .5 else b
                later_rounds(s, r2, col2)
        if not more: break
        predict(more)
model_pick = lambda s, a, b: a if p(s, a, b) >= .5 else b
print(f"{'Full bracket':28} | R64 | R32 | S16 | E8 | F4 | Title | champions | points (1-2-4-8-16-32)")
YR = {}; RES = {}
for lab, (key, src_) in BRK.items():
    tot = [0] * 6; champs = 0; yr = []
    for s in SEASONS:
        r1, r2 = r12(s, key, src_); ch = chalk_pick if key == "seed" else model_pick
        rounds = [r1, r2] + later_rounds(s, r2, ch); w = WON[s]; y = 0
        for ri, picks in enumerate(rounds):
            if ri == 0:
                c = sum(pk == g["won"] for pk, g in zip(picks, BI[s]["games"]) if g["H"] != g["L"])
            else:
                c = sum(w.get(pk, 0) >= ri + 1 for pk in picks)
            tot[ri] += c; y += c * PTS[ri]
        champs += w.get(rounds[5][0], 0) >= 6; yr.append(y)
    pts = sum(c * pp for c, pp in zip(tot, PTS)); YR[lab] = yr; RES[lab] = (tot, champs, pts)
    print(f"{lab:28} | {tot[0]:3} | {tot[1]:3} | {tot[2]:3} | {tot[3]:2} | {tot[4]:2} | {tot[5]:5} | {champs:9} | {pts}")
print("\nmax per round: 511 | 256 | 128 | 64 | 32 | 16  (1,086 points a year max, 192 x 16 minus the 2021 no-contest)")
print("\npoints by year:")
print("year | " + " | ".join(k.split(" ")[0] for k in YR))
for i, s in enumerate(SEASONS): print(int(s[:4]) + 1, "|", " | ".join(f"{YR[k][i]:4}" for k in YR))
json.dump({"by_year": YR, "seasons": SEASONS, "res": {k: v for k, v in RES.items()}}, open(os.path.join(HERE, "m302_out.json"), "w"))
