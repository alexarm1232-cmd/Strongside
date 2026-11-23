# Pod picking prep: chances for every possible Round of 32 pairing in every pod (upset R32 model, regular model, simulator).
import os, sys, json, contextlib, io, subprocess, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m320_weigh_upset.py"), encoding="utf-8-sig").read(); src = src[:src.index("print(f\"\\n{'Round 1 rule'")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
allp = {}
for s in SEASONS:
    g = BI[s]["games"]; L = []
    for q in range(16):
        A = [t for t in (g[2 * q]["H"], g[2 * q]["L"])]; Bt = [t for t in (g[2 * q + 1]["H"], g[2 * q + 1]["L"])]
        A = list(dict.fromkeys(A)); Bt = list(dict.fromkeys(Bt))
        L += [(a, b) for a in A for b in Bt]
    allp[s] = L
json.dump({s: [list(x) for x in v] for s, v in allp.items()}, open(os.path.join(HERE, "m328_pairs.json"), "w"))
print(subprocess.run([sys.executable, os.path.join(HERE, "m328_upset_pairs.py")], capture_output=True, text=True).stdout.strip())
NEW = []; RQ = []
for s, prs in allp.items():
    for a, b in prs:
        S_, W_, x, _ = features(s, kk(a), kk(b)); NEW.append(x); RQ.append((s, a, b, S_, W_, ex_of(s, S_, W_)))
Xe = np.vstack([XX, np.array(NEW)]); fit2 = Q.t_ridge(X=Xe); MZ2 = {}
for s in SEASONS:
    tr = np.where((seas != s) & k)[0]; te = np.array([N + j for j, r in enumerate(RQ) if r[0] == s])
    m_tr, m_te = Q.base(tr, te, fit2); a_ = E12[tr]
    f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_])
    z = f(np.column_stack([m_te, np.array([RQ[j - N][5] for j in te])]))
    for j, zz in zip(te, z): r = RQ[j - N]; MZ2[(s, r[1], r[2])] = (r[3], r[4], float(zz))
pickle.dump(MZ2, open(os.path.join(HERE, "m328_mz.pkl"), "wb"))
miss = {}
for s, prs in allp.items():
    for a, b in prs:
        if f"{a}|{b}" not in SR[s] and f"{b}|{a}" not in SR[s]: miss.setdefault(s, []).append([a, b])
json.dump(miss, open(os.path.join(HERE, "m328_need.json"), "w"))
print("pairs", sum(map(len, allp.values())), "| simulator runs missing:", sum(map(len, miss.values())))
