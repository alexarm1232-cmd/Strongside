# Full-bracket scoring when the vote's Round 1 / Round of 32 upsets are overruled for protected teams.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m313_sim_s16.py"), encoding="utf-8-sig").read(); src = src[:src.index("yrs = [")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
src = open(os.path.join(HERE, "m310_early_line.py"), encoding="utf-8-sig").read(); src = src[src.index("E12M ="):src.index('if __name__')]
src = src.replace("predict12(reqs); pickle.dump(C12, open(PK2, \"wb\"))", "predict12(reqs)")
with contextlib.redirect_stdout(io.StringIO()): exec(src)
src = open(os.path.join(HERE, "m309_more.py"), encoding="utf-8-sig").read(); src = src[src.index("def real_r1"):src.index("def champion_first")]
exec(src)
late = chooser_w(0)
def build(s, o, protect):
    slots, _ = field(s); r1, r2 = tree_r12(s, o)
    r1n = [slots[2 * i] if slots[2 * i + 1] is None else (slots[2 * i] if slots[2 * i] in protect else slots[2 * i + 1] if slots[2 * i + 1] in protect else r1[i]) for i in range(32)]
    r2n = []
    for i in range(16):
        a, b = r1n[2 * i], r1n[2 * i + 1]
        if a in protect and b not in protect: r2n.append(a)
        elif b in protect and a not in protect: r2n.append(b)
        elif r2[i] in (a, b): r2n.append(r2[i])
        else: r2n.append(a if p12(s, a, b) >= .5 else b)
    return [r1n, r2n] + fill(s, r2n, late)
def prot_sets(s):
    A = adv(s, pm); sl = [t for t in field(s)[0] if t]; out = {}
    out["1 seeds"] = {t for t in sl if seed(s, t) == 1}
    out["1-2 seeds"] = {t for t in sl if seed(s, t) <= 2}
    out["1-3 seeds"] = {t for t in sl if seed(s, t) <= 3}
    reg = [field(s)[0][i * 16:(i + 1) * 16] for i in range(4)]
    out["model's region favorite"] = {max([t for t in R_ if t], key=lambda t: A[t][4]) for R_ in reg}
    out["model's top 2 per region"] = {t for R_ in reg for t in sorted([t for t in R_ if t], key=lambda t: -A[t][4])[:2]}
    out["model's top 8 title chances"] = set(sorted(sl, key=lambda t: -A[t][6])[:8])
    return out
yrs = [int(s[:4]) + 1 for s in SEASONS]
for key in ("vote", "blend"):
    base = {o["season"]: o for o in FULL[key]}
    print(f"\n===== Rounds 1-2 = {key}\n{'protected from upsets':30} | R1 | R32 | S16 | E8 | F4 | T | total | >=100 | " + " ".join(f"{y % 100:02d}" for y in yrs))
    PS = {s: prot_sets(s) for s in SEASONS}
    for lab in ["none"] + list(PS[SEASONS[0]]):
        tot = []; cs = np.zeros(6, int)
        for s in SEASONS:
            c, pts = score_all(s, build(s, base[s], set() if lab == "none" else PS[s][lab])); cs += c; tot.append(pts)
        print(f"{lab:30} | {cs[0]:3} | {cs[1]:3} | {cs[2]:3} | {cs[3]:2} | {cs[4]:2} | {cs[5]:1} | {sum(tot):5} | {sum(t >= 100 for t in tot):5} | " + " ".join(f"{t:3}" for t in tot))
print("\nsimulator pairs missing (Final Four/title used model there):", len(need))
