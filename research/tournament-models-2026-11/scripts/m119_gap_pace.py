# Is "rating gap", "rating gap x pace" (and the weaker team's tempo) double counting? Correlations between them, the
# ridge weights each gets, and the 756 pipeline (m99: same round lines, 85% simulator in F4/title, each tournament held
# out) re-run with each one dropped from the base inputs.
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
names = [str(n) for n in np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["names"]]
X = Q.X30; keep = ~Q.FF
ig, ip, it = names.index("gap"), names.index("gap x possessions"), names.index("W tempo")
print("correlation gap vs gap x pace:", round(float(np.corrcoef(X[keep, ig], X[keep, ip])[0, 1]), 3),
      "| gap vs weaker tempo:", round(float(np.corrcoef(X[keep, ig], X[keep, it])[0, 1]), 3),
      "| gap x pace vs weaker tempo:", round(float(np.corrcoef(X[keep, ip], X[keep, it])[0, 1]), 3))
idx = np.where(keep)[0]; w = Q.t_ridge()(idx)                       # base step on all games
Z = Q.zstd(X, idx); A = np.column_stack([Z(idx), np.ones(len(idx))]); coef = np.linalg.lstsq(A, w(idx), rcond=None)[0][:-1]
share = np.abs(coef) / np.abs(coef).sum()
for i in (ig, ip, it): print(f"  ridge weight {names[i]:22} {coef[i]:+.3f}  ({share[i]:.1%} of all weight)")
def job(drop):
    cols = [c for c in range(30) if c not in drop]; fit = Q.t_ridge(X=X[:, cols]); out = np.zeros(Q.N)
    for s in Q.SEASONS:
        tr = np.where((Q.seas != s) & keep)[0]; te = np.where((Q.seas == s) & keep)[0]
        m_tr, m_te = Q.base(tr, te, fit); out[te] = Q.run(m_tr, tr, m_te, te, Q.EX)
    return int(((out > 0) == Q.yb)[keep].sum())
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    V = {"current (all 30)": [], "drop rating gap": [ig], "drop rating gap x pace": [ip], "drop weaker tempo": [it], "drop gap x pace and weaker tempo": [ip, it]}
    with ProcessPoolExecutor(5) as ex:
        for k, r in zip(V, ex.map(job, V.values())): print(f"  {k:36} {r}")
