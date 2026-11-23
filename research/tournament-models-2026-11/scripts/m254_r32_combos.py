# Round of 32 combos, same yardstick as the Round 1 model (inputs chosen on all years, fit with each year held out).
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["RNDS"] = "Second round"
src = open(os.path.join(HERE, "m252_r32_style.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"\\n{'model':58}")])
def uniq(*ls): return list(dict.fromkeys(sum(ls, [])))
SETS = {"21 inputs (dupes removed, strength in)": dedup(SIG, .5), "20 style inputs + def play types": dedup(uniq(STY, D_R32), .5), "14 style only": STY}
r64u = p64
print(f"Round of 32: {nS} games | higher seed {right(np.zeros(nS) >= .5)}, simulator {right(sim_up_ >= .5)}, original {right(s_up_ >= .5)}")
print("combo | AUC | best cutoff (35-55%) right | right @ 40/45/50")
def rep(lab, p):
    best = max(range(35, 56), key=lambda c: right(p >= c / 100))
    print(f"   {lab:70} | {auc(p, ys):.3f} | {right(p >= best / 100)} @ {best}% | {right(p >= .4)} / {right(p >= .45)} / {right(p >= .5)}")
rep("original model", s_up_); rep("simulator", sim_up_); rep("original + simulator", (s_up_ + sim_up_) / 2)
rep("Round 1 Upset Model as is + original + simulator", (r64u + s_up_ + sim_up_) / 3)
for lab, names in SETS.items():
    p, _ = ho(names)
    rep(f"{lab}", p); rep(f"{lab} + original", (p + s_up_) / 2); rep(f"{lab} + original + simulator", (p + s_up_ + sim_up_) / 3)
    rep(f"{lab} + original + R1 Upset Model", (p + s_up_ + r64u) / 3)
    rep(f"{lab} x2 weight + original", (2 * p + s_up_) / 3)
