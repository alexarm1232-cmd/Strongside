import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
import numpy as np
BX, KS = Q.R.B.X, Q.R.B.KS
print(BX.shape, Q.N)
for k in ["efg","d_efg","tov","d_tov","orb","d_orb","ftr","d_ftr"]:
    v = BX[:, KS.index("S "+k)]; print(k, round(float(np.nanmean(v)),3), round(float(np.nanstd(v)),3), int(np.isnan(v).sum()))
