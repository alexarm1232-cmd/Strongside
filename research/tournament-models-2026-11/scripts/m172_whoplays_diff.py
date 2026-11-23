import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m165_retest as R
Q = R.Q; G = Q.R.B.G
NAMES = ["S value sat", "W value sat", "S star sat", "W star sat", "BPM of who played (S - W)", "value sat (S - W)"]
m = np.isin(Q.seas, ["2009-10", "2010-11"]) & ~Q.FF
O, N = R.OLD_F[m], R.NEW_F[m]
print(f"2010-11 tournament games: {int(m.sum())}")
for j, n in enumerate(NAMES):
    if j in (2, 3): print(f"   {n:26} games flagged old {int(O[:, j].sum())} -> new {int(N[:, j].sum())} | flag changed in {int((O[:, j] != N[:, j]).sum())} games")
    else: print(f"   {n:26} avg old {O[:, j].mean():+.2f} -> new {N[:, j].mean():+.2f} | avg size of change {np.abs(N[:, j] - O[:, j]).mean():.2f} | largest {np.abs(N[:, j] - O[:, j]).max():.2f}")
idx = np.where(m)[0]; ch = np.abs(R.NEW_F[idx, 4] - R.OLD_F[idx, 4]) + np.abs(R.NEW_F[idx, 5] - R.OLD_F[idx, 5])
print("\nbiggest changes:")
for i in idx[np.argsort(-ch)[:6]]:
    g = G[i]; print(f"   {g['season']} {g['rnd']:12} {Q.R.B.Sname[i]} (stronger) vs {g['dog'] if Q.R.B.Sname[i] == g['fav'] else g['fav']}: "
                    f"BPM of who played gap {R.OLD_F[i, 4]:+.2f} -> {R.NEW_F[i, 4]:+.2f} | value sat gap {R.OLD_F[i, 5]:+.2f} -> {R.NEW_F[i, 5]:+.2f}")
