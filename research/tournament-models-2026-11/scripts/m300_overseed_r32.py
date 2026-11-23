# Add the higher seed's over-seeding to each Round of 32 picker as a held-out adjustment:
#   logit(p_new) = a * logit(p_picker) + b * over-seeding + c, fit on the real Round of 32 games of the OTHER 15 years.
# Then: (1) real Round of 32 games, each picker at its usual cutoff; (2) the vote bracket (Round 1 unchanged).
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m294_recency.py"), encoding="utf-8-sig").read(); src = src[:src.index("W1 = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
src2 = open(os.path.join(HERE, "m299_overseed.py"), encoding="utf-8-sig").read(); src2 = src2[:src2.index("for rnd, lab in")]
with contextlib.redirect_stdout(io.StringIO()): exec(src2)
Y, HO, LO, PM, PU, PS, SG = build(2)
SEAS2 = np.array([r["s"] for r in UPX])
def fitadj(P, m):
    A = np.column_stack([logit(P[m]), HO[m]]); b, _ = wald(Y[m], A); return b
def adj(P, ho, b): return sig(b[0] * logit(P) + b[1] * ho + b[2])
CUT = {"upset": .45, "regular": .5, "sim": .5}; PP = {"upset": PU, "regular": PM, "sim": PS}
print("REAL Round of 32 games (256), held out by year:")
B_ = {}
for nm, P in PP.items():
    newp = np.zeros(len(Y))
    for s in sorted(set(SEAS2)):
        tr, te = SEAS2 != s, SEAS2 == s; b = fitadj(P, tr); B_[(nm, s)] = b; newp[te] = adj(P[te], HO[te], b)
    old = int(((P >= CUT[nm]) == (Y == 1)).sum()); new = int(((newp >= CUT[nm]) == (Y == 1)).sum())
    print(f"   {nm:8} @{CUT[nm]:.2f}: {old} -> {new} with over-seeding | upset picks {int((P >= CUT[nm]).sum())} -> {int((newp >= CUT[nm]).sum())}")
    b = fitadj(P, np.ones(len(Y), bool)); print(f"            all-years weight on over-seeding {b[1]:+.3f} per seed line")
# ---- vote bracket with adjusted Round of 32 picks
VP = json.load(open(os.path.join(HERE, "m289_vote_pairs.json"))); SR = json.load(open(os.path.join(HERE, "m283_sim_r32.json")))
VB = {d["season"]: d for d in json.load(open(os.path.join(HERE, "m293_brackets_three.json")))}
seedof = lambda s, t: FIELD[s][kk(t)]
def comp_pl(s, a, b):
    """each component's chance that the lower seed of (a, b) wins, plus labels"""
    h, l = (a, b) if seedof(s, a) <= seedof(s, b) else (b, a)
    key = (a, b) if f"{s}|{a}|{b}" in UPP else (b, a)
    hh, ll, pu = UPP[f"{s}|{key[0]}|{key[1]}"]; pu = pu if ll == l else 1 - pu
    S_, W_, z = MZ[(s, key[0], key[1])]; pS = 1 / (1 + np.exp(-z)); pm = pS if kk(l) == S_ else 1 - pS
    q = SR[s].get(f"{a}|{b}"); q = q if q is not None else 1 - SR[s][f"{b}|{a}"]; ps = q if l == a else 1 - q
    return h, l, {"upset": pu, "regular": pm, "sim": ps}
for mode in ("as is", "with over-seeding"):
    r2 = 0; yrs = []
    for s in SEASONS:
        d = VB[s]; y2 = 0
        for q in range(16):
            a, b = VP[s][q]; h, l, P = comp_pl(s, a, b)
            if seedof(s, h) == seedof(s, l):
                w = d["brackets"]["vote"]["r2"][q]["pick"]
            else:
                votes = []
                for nm, p in P.items():
                    if mode != "as is": p = float(adj(np.array([p]), np.array([over(s, h)]), B_[(nm, s)])[0])
                    votes.append(l if p >= CUT[nm] else h)
                w = max(set(votes), key=votes.count)
            y2 += w == d["r2won"][q]
        r2 += y2; yrs.append(y2)
    r1 = sum(sum(VB[s]["brackets"]["vote"]["r1"][j]["pick"] == g["won"] for j, g in enumerate(VB[s]["games"]) if not g["bye"]) for s in SEASONS)
    print(f"\nVOTE bracket, Round of 32 {mode}: Round 1 {r1} | Round of 32 {r2} | points {r1 + 2 * r2} | by year {yrs}")
