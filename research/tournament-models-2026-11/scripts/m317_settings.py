# Same inputs, different settings: ridge penalty x season half-life, each year held out; plus a 2-stage "pairwise interactions" check
import os, sys, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
U31 = json.load(open(os.path.join(HERE, "m230_out.json")))["inputs"]
ALL = dict(CAND); ALL.update({c: col(c) for c in U31 if c not in ALL})
gi = [r["i"] for r in rows]
def rfit(X, yy, w, lam):
    mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.column_stack([(X - mu) / sd, np.ones(len(X))]); b = np.zeros(A.shape[1]); P = lam * np.eye(A.shape[1]); P[-1, -1] = 0
    for _ in range(40):
        q = 1 / (1 + np.exp(-A @ b)); H_ = A.T @ (A * (w * q * (1 - q))[:, None]) + P; b += np.linalg.solve(H_, A.T @ (w * (yy - q)) - P @ b)
    return lambda Z: 1 / (1 + np.exp(-(np.column_stack([(Z - mu) / sd, np.ones(len(Z))]) @ b)))
X1 = np.column_stack([ALL[c] for c in U31])
print("ROUND 1 (31 inputs), held out, right @40 | AUC   [locked = ridge 30, half-life 12]")
for hl in (6, 12, 24, 999):
    w = Q.R.weights(hl)[gi] if hl < 999 else np.ones(n)
    line = []
    for lam in (3, 10, 30, 60, 120):
        p = np.zeros(n)
        for s in sorted(set(seas)): tr, te = seas != s, seas == s; p[te] = rfit(X1[tr], y[tr], w[tr], lam)(X1[te])
        line.append(f"ridge {lam}: {int(((p >= .4) == (y == 1)).sum())} {auc(p, y):.3f}")
    print(f"  half-life {hl if hl < 999 else 'none':>4} | " + " | ".join(line))
src = open(os.path.join(HERE, "m266_r32_tune.py"), encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("WS = [")])
INS = U(KEPT16, COACH2, mk_); X2 = np.column_stack([col(c) for c in INS]); gi2 = [rows[i]["i"] for i in idx]
print("\nROUND OF 32 (22 inputs), held out, right @45 | AUC   [locked = ridge 10, half-life 12]")
for hl in (6, 12, 24, 999):
    w = Q.R.weights(hl)[gi2] if hl < 999 else np.ones(nS)
    line = []
    for lam in (3, 10, 30, 60):
        p = np.zeros(nS)
        for s in SEASONS: tr, te = Ss != s, Ss == s; p[te] = rfit(X2[tr], ys[tr], w[tr], lam)(X2[te])
        line.append(f"ridge {lam}: {right(p >= .45)} {auc(p, ys):.3f}")
    print(f"  half-life {hl if hl < 999 else 'none':>4} | " + " | ".join(line))
