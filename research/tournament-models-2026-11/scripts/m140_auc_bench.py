import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
B = Q.R.B; G = B.G; k = ~Q.FF
SP = {r["game_id"]: r for r in csv.DictReader(open(r"C:\Users\crtra\Downloads\basketball\reports\tournament_spreads.csv", encoding="utf-8"))}
def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, int); o = np.argsort(s, kind="mergesort"); rk = np.empty(len(s))
    # average ranks for ties
    ss = s[o]; i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]: j += 1
        rk[o[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    n1 = y.sum(); return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
fit = Q.t_ridge(); out = np.zeros(Q.N)
for s in Q.SEASONS:
    tr = np.where((Q.seas != s) & k)[0]; te = np.where((Q.seas == s) & k)[0]
    m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
gap = Q.X30[:, names.index("gap")]; seed = np.array(B.sW, float) - np.array(B.sS, float); sim = Q.SIM
line = np.full(Q.N, np.nan)
for i, g in enumerate(G):
    r = SP.get(g["gid"])
    if r and r["spread"] not in ("", None):
        sp = abs(float(r["spread"])); line[i] = sp if r["favorite"].rstrip(". ") == B.Sname[i].rstrip(". ") else -sp
yk = Q.yb
have = k & ~np.isnan(line)
print(f"all 1,007 games:")
for nm, v in (("coin flip", np.zeros(Q.N)), ("seed difference", seed), ("rating gap alone", gap), ("simulator", sim), ("your model (held out)", out)):
    print(f"  {nm:24} AUC {auc(v[k], yk[k]):.3f}   right {int(((v[k] > 0) == yk[k]).sum()) if nm != 'coin flip' else '-'}")
print(f"games with a closing line ({int(have.sum())}):")
for nm, v in (("seed difference", seed), ("rating gap alone", gap), ("simulator", sim), ("closing line (Vegas)", line), ("your model (held out)", out)):
    print(f"  {nm:24} AUC {auc(v[have], yk[have]):.3f}")
for r in ["First round","Second round","Sweet 16","Elite Eight"]:
    m = have & (Q.RND == r); print(f"  {r:13} model {auc(out[m], yk[m]):.3f} | line {auc(line[m], yk[m]):.3f} | seed {auc(seed[m], yk[m]):.3f}")
m = have & np.isin(Q.RND, ["Final Four", "Championship"]); print(f"  F4 + title    model {auc(out[m], yk[m]):.3f} | line {auc(line[m], yk[m]):.3f} | seed {auc(seed[m], yk[m]):.3f}")
