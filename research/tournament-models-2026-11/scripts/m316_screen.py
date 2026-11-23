# Screen the new game-log measures: add each (higher / lower / gap) to the locked Round 1 Upset Model (31, @40) and the locked
# Round of 32 Upset Model (22, ridge 10, @45); each year held out. Also z-score beyond seed.
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
NF = json.load(open(os.path.join(HERE, "m315_feats.json")))
KEYS = [k for k in next(iter(next(iter(NF.values())).values())) if k not in ("travel_km", "same_state_site")]
# ---------------- Round 1
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
U31 = json.load(open(os.path.join(HERE, "m230_out.json")))["inputs"]
ALL = dict(CAND); ALL.update({c: col(c) for c in U31 if c not in ALL})
def nf_cols(rws, kkf):
    out = {}
    for key in KEYS:
        v = {sd: np.array([float((NF.get(r["s"], {}).get(kkf(r[sd])) or {}).get(key, np.nan)) for r in rws]) for sd in "HL"}
        for sd in "HL": v[sd][np.isnan(v[sd])] = np.nanmean(v[sd])
        out[f"H {key}"], out[f"L {key}"], out[f"L-H {key}"] = v["H"], v["L"], v["L"] - v["H"]
    return out
N1 = nf_cols(rows, kk)
print("coverage R1:", int(sum(1 for r in rows if kk(r["H"]) in NF.get(r["s"], {}) and kk(r["L"]) in NF.get(r["s"], {}))), "of", len(rows))
def ho1(ins, extra=None):
    X = np.column_stack([ALL[c] for c in ins] + ([extra] if extra is not None else [])); p = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; p[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    return p
p0 = ho1(U31); r0 = int(((p0 >= .4) == (y == 1)).sum())
fw = lambda p: (int(((p >= .4) == (y == 1))[np.array([int(s[:4]) >= 2017 for s in seas])].sum()))
print(f"\nROUND 1 base (locked 31, held out @40): {r0}/511 AUC {auc(p0, y):.3f}")
def zbeyond(v, yy, sgv):
    Xz = np.column_stack([np.ones(len(yy)), sgv, (v - v.mean()) / (v.std() + 1e-9)]); b = np.zeros(3)
    for _ in range(30):
        q = 1 / (1 + np.exp(-Xz @ b)); H_ = Xz.T @ (Xz * (q * (1 - q))[:, None]); b += np.linalg.solve(H_ + 1e-6 * np.eye(3), Xz.T @ (yy - q))
    return b[2] / np.sqrt(np.linalg.inv(H_)[2, 2])
sgv1 = np.array([r["sL"] - r["sH"] for r in rows], float)
R1 = []
for c, v in N1.items():
    if v.std() < 1e-9: continue
    p = ho1(U31, v); R1.append((c, int(((p >= .4) == (y == 1)).sum()) - r0, auc(p, y) - auc(p0, y), zbeyond(v, y, sgv1)))
print(f"{'measure':28} | +games | +AUC | z (beyond seed gap)")
for c, d, a, z in sorted(R1, key=lambda t: (-t[1], -t[2])): print(f"{c:28} | {d:+3d} | {a:+.3f} | {z:+.2f}")
# ---------------- Round of 32
src = open(os.path.join(HERE, "m266_r32_tune.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("WS = [")])
INS = U(KEPT16, COACH2, mk_)
rws = [rows[i] for i in idx]; N2 = nf_cols(rws, kk)
def ho2(extra=None):
    X = np.column_stack([col(c) for c in INS] + ([extra] if extra is not None else [])); p = np.zeros(nS)
    for s in SEASONS:
        tr, te = Ss != s, Ss == s; f, _ = fit(X[tr], ys[tr], Ws[tr], 10.0); p[te] = f(X[te])
    return p
q0 = ho2(); b0 = right(q0 >= .45)
sgv2 = np.array([r["sL"] - r["sH"] for r in rws], float)
print(f"\nROUND OF 32 base (locked 22, ridge 10, held out @45): {b0}/256 AUC {auc(q0, ys):.3f}")
R2 = []
for c, v in N2.items():
    if v.std() < 1e-9: continue
    q = ho2(v); R2.append((c, right(q >= .45) - b0, auc(q, ys) - auc(q0, ys), zbeyond(v, ys.astype(float), sgv2)))
print(f"{'measure':28} | +games | +AUC | z (beyond seed gap)")
for c, d, a, z in sorted(R2, key=lambda t: (-t[1], -t[2])): print(f"{c:28} | {d:+3d} | {a:+.3f} | {z:+.2f}")
json.dump({"r1": R1, "r2": R2, "r1_base": r0, "r2_base": b0}, open(os.path.join(HERE, "m316_out.json"), "w"))
