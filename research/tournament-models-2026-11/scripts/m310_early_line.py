# Advancement chances with the right line per round: Rounds 1-2 from the shared R1+R32 line (base + coach + star, no who plays),
# Sweet 16 on from the late line. Then rerun expected points / champion-first.
import os, json, contextlib, io, pickle, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m309_more.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
E12M = np.isin(RND, ["First round", "Second round"]); C12 = {}
PK2 = os.path.join(HERE, "m310_pairs12.pkl")
if os.path.exists(PK2): C12.update(pickle.load(open(PK2, "rb")))
def predict12(reqs):
    reqs = [r for r in dict.fromkeys(reqs) if r not in C12 and (r[0], r[2], r[1]) not in C12]
    if not reqs: return
    rows = []; info = []
    for s, a, b in reqs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); rows.append(x); info.append((s, a, b, S_, ex_of(s, S_, W_)))
    Xe = np.vstack([XX, np.array(rows)]); fitx = Q.t_ridge(X=Xe)
    for s in SEASONS:
        te = np.array([N + j for j, r in enumerate(info) if r[0] == s])
        if len(te) == 0: continue
        tr = np.where((seas != s) & k)[0]; m_tr, m_te = Q.base(tr, te, fitx); a_ = E12M[tr]
        f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
        z = f(np.column_stack([m_te, np.array([info[j - N][4] for j in te])]))
        for j, zz in zip(te, z):
            s_, a, b, S_, _ = info[j - N]; pS = 1 / (1 + np.exp(-zz)); C12[(s_, a, b)] = pS if kk(a) == S_ else 1 - pS
reqs = []
for s in SEASONS:
    tm = [t for t in field(s)[0] if t]; reqs += [(s, a, b) for a, b in itertools.combinations(tm, 2)]
predict12(reqs); pickle.dump(C12, open(PK2, "wb"))
p12 = lambda s, a, b: C12[(s, a, b)] if (s, a, b) in C12 else 1 - C12[(s, b, a)]

_adv_old = adv
def adv(s, pf, early=None):
    """P(win round r); rounds 1-2 use `early` (default the R1+R32 line), Sweet 16 on use pf"""
    early = early or p12
    slots, _ = field(s); lvl = [{t: 1.0} if t else {} for t in slots]; out = {t: [0] * 7 for t in slots if t}
    for r in range(1, 7):
        q = early if r <= 2 else pf; nxt = []
        for i in range(0, len(lvl), 2):
            L, R_ = lvl[i], lvl[i + 1]
            if not R_: d = dict(L)
            else:
                d = {a: L[a] * sum(R_[b] * q(s, a, b) for b in R_) for a in L}
                d.update({b: R_[b] * sum(L[a] * q(s, b, a) for a in L) for b in R_})
            for t in d: out[t][r] = d[t]
            nxt.append(d)
        lvl = nxt
    return out
if __name__ == "__main__":
    print("check 2016 Villanova vs UNC Asheville, R1+R32 line:", round(p12("2015-16", "Villanova", "UNC Asheville"), 3),
          "| late line:", round(pm("2015-16", "Villanova", "UNC Asheville"), 3))
    # the R1+R32 line's own Round 1 / Round 2 picks on real games, as a sanity check
    c = n = 0
    for s in SEASONS:
        for gg in BI[s]["games"]:
            if gg["H"] == gg["L"]: continue
            c += (gg["H"] if p12(s, gg["H"], gg["L"]) >= .5 else gg["L"]) == gg["won"]; n += 1
    print(f"R1+R32 line on real Round 1 games: {c}/{n}")
    yrs = [int(s[:4]) + 1 for s in SEASONS]
    def show(name, tot): print(f"{name:44} | {sum(tot):5} | {sum(t >= 100 for t in tot):3} | " + " ".join(f"{t:3}" for t in tot))
    OUT = {}
    for key in ("vote", "blend"):
        base = {o["season"]: o for o in FULL[key]}
        early = {s: base[s]["score"][0] + 2 * base[s]["score"][1] for s in SEASONS}
        print(f"\n===== Rounds 1-2 = {key}\n{'method':44} | total | >=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
        rows = {"Current": [base[s]["points"] for s in SEASONS]}
        ep = lambda s, pf: early[s] + score_late(s, ep_fill(s, r2_tree(s, base[s]), adv(s, pf)))[1]
        rows["Expected points, model"] = [ep(s, pm) for s in SEASONS]
        rows["Expected points, model+net 50/50"] = [ep(s, mixp((.5, pm), (.5, pnet))) for s in SEASONS]
        rows["Champion-first, model"] = [score_all(s, champion_first(s, base[s], pm))[1] for s in SEASONS]
        rows["Champion-first, model+net 50/50"] = [score_all(s, champion_first(s, base[s], mixp((.5, pm), (.5, pnet))))[1] for s in SEASONS]
        for n_, v in rows.items(): show(n_, v)
        OUT[key] = rows
    print("\nchampions: EP model pick | real champ title chance")
    for s in SEASONS:
        o = {x["season"]: x for x in FULL["vote"]}[s]; A = adv(s, pm); rd = ep_fill(s, r2_tree(s, o), A)
        real = next(t for t in WON[s] if WON[s][t] >= 6); top = max(A, key=lambda t: A[t][6])
        print(int(s[:4]) + 1, rd[3][0], "| top:", top, f"{A[top][6]:.2f}", "| real:", real, f"{A[real][6]:.2f}")
    json.dump(OUT, open(os.path.join(HERE, "m310_out.json"), "w"))
