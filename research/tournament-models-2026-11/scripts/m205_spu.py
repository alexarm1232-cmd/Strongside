import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import m99_model_types as Q
D = json.load(open(os.path.join(H, "m186_r64_features.json"))); F = {k: np.array(v) for k, v in D["F"].items()}; rows = D["rows"]; y = np.array(D["y"])
U = json.load(open(os.path.join(H, "m188_out.json")))["inputs"]; seas = np.array([r["s"] for r in rows]); W = Q.WT[[r["i"] for r in rows]]
def col(name):
    lab, k = name.split(" ", 1); return F["L " + k] - F["H " + k] if lab == "L-H" else F[lab + " " + k]
X = np.column_stack([col(c) for c in U]); tr = seas != "2023-24"
mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9; A = np.column_stack([(X[tr] - mu) / sd, np.ones(tr.sum())]); b = np.zeros(A.shape[1]); P = 30 * np.eye(A.shape[1]); P[-1, -1] = 0
for _ in range(60):
    p = 1 / (1 + np.exp(-A @ b)); Hm = A.T @ (A * (W[tr] * p * (1 - p))[:, None]) + P; b += np.linalg.solve(Hm, A.T @ (W[tr] * (y[tr] - p)) - P @ b)
Z = (X - mu) / sd; C = Z * b[:-1]
j = next(k for k, r in enumerate(rows) if r["s"] == "2023-24" and r["L"] == "Saint Peter's")
o15 = np.array([r["sL"] == 15 and k != j for k, r in enumerate(rows)])
lo = lambda v: 1 / (1 + np.exp(-v))
print(f"Saint Peter's vs Tennessee: upset chance {lo(C[j].sum() + b[-1]):.0%} | average other 15 seed: {lo((C[o15].sum(1) + b[-1])).mean():.0%} (n {int(o15.sum())})")
print(f"total push (log-odds): Saint Peter's {C[j].sum():+.2f} vs other 15s average {C[o15].sum(1).mean():+.2f}")
d = C[j] - C[o15].mean(0); order = np.argsort(-d)
print("\ninput | SPU push | avg 15-seed push | difference | SPU raw value vs 15-seed average")
for k in order[:8]: print(f"{U[k]}|{C[j,k]:+.2f}|{C[o15,k].mean():+.2f}|{d[k]:+.2f}|{X[j,k]:+.2f} vs {X[o15,k].mean():+.2f}")
print("... pulling the other way:")
for k in order[-4:]: print(f"{U[k]}|{C[j,k]:+.2f}|{C[o15,k].mean():+.2f}|{d[k]:+.2f}|{X[j,k]:+.2f} vs {X[o15,k].mean():+.2f}")
TW = {}
for g in Q.R.B.G:
    if g["rnd"] != "First Four": w = g["fav"] if g["fav_won"] else g["dog"]; TW[(g["season"], w)] = TW.get((g["season"], w), 0) + 1
print("\ntournament wins 2021-23: Saint Peter's", [TW.get((s, "Saint Peter's"), 0) for s in ("2020-21", "2021-22", "2022-23")], "| Tennessee", [TW.get((s, "Tennessee"), 0) for s in ("2020-21", "2021-22", "2022-23")])
