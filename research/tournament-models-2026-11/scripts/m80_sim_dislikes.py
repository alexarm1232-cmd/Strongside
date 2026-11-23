# Games where the simulator does not like the seed favorite (gives it under 50%): how did the model pick them?
# All real games Round of 64 to title, First Four out, equal seeds out. Model = the 756 (held out by tournament).
import os, sys, contextlib, io
os.environ["GROUPING"] = "v2"
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, OLD); os.chdir(OLD)
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import m18_rebuild as R
D = np.load("m3_data.npz", allow_pickle=True); sS, sW = D["seedS"], D["seedW"]
v = np.load("m56_scores.npz")["fixed 27 (picked from all games)"]; p = 1 / (1 + np.exp(-v)); sim = R.B.simS
RND, yb = R.RND, R.yb
ok = (RND != "First Four") & (sS != sW)
favS = sS < sW
fm = np.where(favS, p, 1 - p); fs = np.where(favS, sim, 1 - sim); fw = np.where(favS, yb, ~yb)
print("all seed-favorite games:", int(ok.sum()), "favorite won", f"{fw[ok].mean():.1%}")
m = ok & (fs < 0.5)
print(f"\nsimulator gives the favorite < 50%: {int(m.sum())} games, favorite won {int(fw[m].sum())} ({fw[m].mean():.1%})")
sim_right = int((~fw[m]).sum()); mod_right = int(((fm[m] >= 0.5) == fw[m]).sum())
print(f"  simulator (picks underdog) right {sim_right}/{int(m.sum())} = {sim_right / m.sum():.1%}")
print(f"  model right                    {mod_right}/{int(m.sum())} = {mod_right / m.sum():.1%}")
a = m & (fm < 0.5); b = m & (fm >= 0.5)
print(f"  model agrees (underdog):  {int(a.sum())} games, underdog won {int((~fw[a]).sum())} = {(~fw[a]).mean():.1%}")
print(f"  model sticks w/ favorite: {int(b.sum())} games, favorite won {int(fw[b].sum())} = {fw[b].mean():.1%}")
print("\nby round (games | sim right | model right | model sided w/ favorite: fav won)")
for rd in ("First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"):
    r = m & (RND == rd)
    if not r.any(): continue
    rb = r & (fm >= 0.5)
    print(f"  {rd:13} {int(r.sum()):>3} | {int((~fw[r]).sum()):>3} | {int(((fm[r] >= 0.5) == fw[r]).sum()):>3} | {int(fw[rb].sum())}/{int(rb.sum())}")
print("\nby how much the simulator dislikes the favorite")
for lo, hi in ((0.45, 0.5), (0.40, 0.45), (0.0, 0.40)):
    r = m & (fs >= lo) & (fs < hi)
    print(f"  sim fav {lo:.0%}-{hi:.0%}: {int(r.sum()):>3} games | fav won {fw[r].mean():.1%} | sim right {int((~fw[r]).sum())} | model right {int(((fm[r] >= 0.5) == fw[r]).sum())}")
