import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
O = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m165_outs.npy"))
k = ~Q.FF; a = (O[0] > 0) == Q.yb; b = (O[1] > 0) == Q.yb
for i in np.where(k & (a != b))[0]:
    g = Q.R.B.G[i]
    print(f"{g['season']} {g['rnd']:12} {g['fav']} vs {g['dog']}: before {'right' if a[i] else 'wrong'} -> after {'right' if b[i] else 'wrong'} | base log-odds {O[0][i]:+.2f} -> {O[1][i]:+.2f}")
d = np.abs(O[1] - O[0])
print("average change in the model's log-odds: 2010-11 games", round(float(d[k & np.isin(Q.seas, ['2009-10', '2010-11'])].mean()), 3), "| other years", round(float(d[k & ~np.isin(Q.seas, ['2009-10', '2010-11'])].mean()), 3))
