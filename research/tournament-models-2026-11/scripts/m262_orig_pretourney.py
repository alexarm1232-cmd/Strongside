# The original model (model 1), rebuilt on pre-tournament data only. Its 31 inputs (sos gap, gap x pace, 27 measures, stocks)
# and coach + star extras are already pre-tournament. Two parts were not:
#   - Rounds 1-2 "who plays": who actually took the floor in that game (game-day lineup)
#   - Final Four / title: 85% the simulator's chance, and the simulator plays the game-day lineup
# Variants (each tournament held out, same settings as m170):
#   A as it was | B who-plays out | C who-plays out + no simulator (fully pre-tournament)
#   D C + pre-tournament availability (rotation players missing the last 2 pre-tournament games) in Rounds 1-2
#   E C + pre-tournament availability in every round
import os, sys, json, numpy as np, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
R, M, B = Q.R, Q.M, Q.B
XX = np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True)["X"]
fit = Q.t_ridge(X=XX); k = ~Q.FF; N = Q.N; seas = Q.seas; y_ = Q.y_; WT = Q.WT; RND = Q.RND
PA = json.load(open(os.path.join(HERE, "m261_pre_avail.json")))
def pa(s, t):
    d = PA.get(s, {}); v = d.get(t) or d.get(t + ".") or d.get(t.rstrip(".")) or d.get(t.rstrip(". "))
    return [v["miss_share"], v["star_out"]] if v else [0.0, 0.0]
miss = 0; AV = np.zeros((N, 5))
for i, g in enumerate(B.G):
    s = g["season"]; a, b = pa(s, B.Sname[i]), pa(s, Q.Wn[i])
    if a == [0.0, 0.0] and not (PA.get(s, {}).get(B.Sname[i]) or PA.get(s, {}).get(B.Sname[i].rstrip(". "))): miss += 1
    AV[i] = [a[0], b[0], a[1], b[1], a[0] - b[0]]
print(f"pre-tournament availability missing for ~{miss} stronger-team slots of {N}")
E12, S16E8, F4T = Q.E12, Q.S16 | Q.E8, Q.F4T
def make_run(v):
    VER = {"A": [(E12, "m who ex"), (S16E8, "m ex"), (F4T, "blend")], "B": [(E12, "m ex"), (S16E8, "m ex"), (F4T, "blend")],
           "C": [(E12, "m ex"), (S16E8, "m ex"), (F4T, "m ex")], "D": [(E12, "m ex av"), (S16E8, "m ex"), (F4T, "m ex")],
           "E": [(E12, "m ex av"), (S16E8, "m ex av"), (F4T, "m ex av")], "F": [(E12 | S16E8 | F4T, "m ex")]}[v]
    def run(m_tr, tr, m_te, te):
        cols = lambda spec, m, idx: np.column_stack([{"m": m[:, None], "who": M.F[idx], "ex": Q.EX[idx], "av": AV[idx]}[c] for c in spec.split()])
        out = np.zeros(len(te))
        for grp, spec in VER:
            b = grp[te]; a = grp[tr]
            if not b.any(): continue
            if spec == "blend":
                f = R.wlr(cols("m ex", m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = 0.15 * f(cols("m ex", m_te[b], te[b])) + 0.85 * Q.SIM[te][b]
            else:
                f = R.wlr(cols(spec, m_tr[a], tr[a]), y_[tr][a], WT[tr][a]); out[b] = f(cols(spec, m_te[b], te[b]))
        return out
    return run
RN = ["First round", "Second round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
yk = Q.yb
print(f"\n{'variant':72} | held out | in-sample | by round held out (R64/R32/S16/E8/F4/title)")
OUTS = {}
for v, lab in (("A", "A. as it was (who plays in Rounds 1-2, simulator in Final Four/title)"), ("B", "B. who plays removed"),
               ("C", "C. who plays removed + no simulator  = fully pre-tournament"), ("D", "D. C + pre-tournament availability, Rounds 1-2"),
               ("E", "E. C + pre-tournament availability, every round"), ("F", "F. fully pre-tournament, one line for every round")):
    run = make_run(v); out = np.zeros(N)
    for s in Q.SEASONS:
        tr = np.where((seas != s) & k)[0]; te = np.where((seas == s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); out[te] = run(m_tr, tr, m_te, te)
    tr = np.where(k)[0]; m_tr, m_te = Q.base(tr, tr, fit); ins = np.zeros(N); ins[tr] = run(m_tr, tr, m_te, tr)
    held = int(((out[k] > 0) == yk[k]).sum()); insr = int(((ins[k] > 0) == yk[k]).sum())
    rr = [int(((out[k & (RND == r)] > 0) == yk[k & (RND == r)]).sum()) for r in RN]
    OUTS[v] = out; print(f"{lab:72} | {held:4} / {int(k.sum())} | {insr:4} | {'/'.join(map(str, rr))}")
old = np.load(os.path.join(HERE, "m170_model_out.npy")); print(f"(check: saved model 1 output held out = {int(((old[k] > 0) == yk[k]).sum())})")
for v in "CDE": np.save(os.path.join(HERE, f"m262_model_pre_{v}.npy"), OUTS[v])
print("games per round:", [int((k & (RND == r)).sum()) for r in RN])
