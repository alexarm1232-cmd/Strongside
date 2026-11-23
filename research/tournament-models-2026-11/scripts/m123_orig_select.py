# Re-run the ORIGINAL selection that produced the 27 (dedup_model.py: the report's significant measures in z order,
# drop any that overlaps the strength inputs at |r| >= 0.3, then one per overlap group) with one rating input removed
# from the strength inputs. Prints how many measures come out and whether they are the same 27.
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"; os.environ["CUT"] = "0.3"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
ns = {"__file__": os.path.join(OLD, "dedup_model.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(OLD, "dedup_model.py"), encoding="utf-8").read().split("models = {")[0], ns)
X, KS, STR, kept, REPORT, zrep, CUT = ns["X"], ns["KS"], ns["STR"], ns["kept"], ns["REPORT"], ns["zrep"], ns["CUT"]
C = np.corrcoef(X.T)
def select(strength):
    cand = sorted(REPORT, key=lambda c: -zrep.get(KS[c], (0, 0))[0]); out = []
    for c in cand:
        if max(abs(C[c, s]) for s in strength) >= CUT: continue
        if all(abs(C[c, k]) < CUT for k in out): out.append(c)
    return out
iG = next(c for c in STR if KS[c] == "gap"); iP = next(c for c in STR if KS[c] == "gap x possessions")
for name, st in (("all 3 strength inputs", STR), ("without rating gap", [c for c in STR if c != iG]), ("without rating gap x pace", [c for c in STR if c != iP])):
    k = select(st)
    print(f"{name:28} strength {len(st)} + measures {len(k)} = {len(st) + len(k)} inputs | same as the original 27: {set(k) == set(kept)}"
          + (f" | added {[KS[c] for c in k if c not in kept]} removed {[KS[c] for c in kept if c not in k]}" if set(k) != set(kept) else ""))
