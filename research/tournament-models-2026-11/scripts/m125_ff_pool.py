import os, sys, contextlib, io
os.environ["GROUPING"]="v2"; os.environ["CUT"]="0.3"
OLD=r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0,OLD); os.chdir(OLD)
import numpy as np
ns={"__file__":os.path.join(OLD,"dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(OLD,"dedup_model.py"),encoding="utf-8").read().split("models = {")[0], ns)
X,KS,STR,kept,REPORT,zrep=ns["X"],ns["KS"],ns["STR"],ns["kept"],ns["REPORT"],ns["zrep"]
print("pool size",len(KS),"report",len(REPORT))
import re
ff=[i for i,k in enumerate(KS) if re.search(r"(?i)efg|tov|orb|drb|ft|_to\b|p2|p3",k) and "pt_" not in k]
C=np.corrcoef(X.T)
for i in ff:
    print(f"{KS[i]:24} inReport={i in REPORT} kept={i in kept} z={zrep.get(KS[i],(0,0))[0]:+.2f} maxR_strength={max(abs(C[i,s]) for s in STR):.2f}")
