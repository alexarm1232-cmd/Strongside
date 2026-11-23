# Sweet 16 / Elite 8: which version of the regular model picks the real games best? Each year held out.
#   line trained on: S16-title (current) | S16+E8 only | all rounds | R1-R2 | no line (base score only) | base + coach/star on all rounds
#   plus: net rating gap, higher seed, simulator game-file line, and simple averages.
import os, json, contextlib, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m302_full_brackets.py"), encoding="utf-8-sig").read(); src = src[:src.index("CACHE = {}")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
S16m, E8m = Q.S16, Q.E8; F4m = Q.F4T; R12 = np.isin(RND, ["First round", "Second round"])
ALLm = k.copy()
fit = Q.t_ridge(X=XX)
tgt = np.where((S16m | E8m) & k)[0]
LINES = {"line on S16-title (current)": S16m | E8m | F4m, "line on S16+E8 only": S16m | E8m, "line on all rounds": ALLm, "line on R1-R2": R12, "line on E8-title": E8m | F4m}
P = {lab: np.zeros(len(tgt)) for lab in list(LINES) + ["base score, no line", "base only, refit on S16+"]}
for s in SEASONS:
    te = tgt[seas[tgt] == s]
    if len(te) == 0: continue
    tr = np.where((seas != s) & k)[0]; m_tr, m_te = Q.base(tr, te, fit); pos = np.searchsorted(tgt, te)
    for lab, mask in LINES.items():
        a_ = mask[tr]; f = R.wlr(np.column_stack([m_tr[a_], Q.EX[tr][a_]]), y_[tr][a_], WT[tr][a_]); P[lab][pos] = 1 / (1 + np.exp(-f(np.column_stack([m_te, Q.EX[te]]))))
    P["base score, no line"][pos] = 1 / (1 + np.exp(-m_te))
    a_ = (S16m | E8m | F4m)[tr]; f = R.wlr(m_tr[a_][:, None], y_[tr][a_], WT[tr][a_]); P["base only, refit on S16+"][pos] = 1 / (1 + np.exp(-f(m_te[:, None])))
yy = y_[tgt]
# y_ = 1 when the "S" side (model's orientation side) wins; build comparable picks for seed / net / sim
Sside = [kk(B.Sname[i]) for i in tgt]
net = lambda s, t: TM[s].get(tname(s, t), {}).get("adj_net") or -30
def other(i): g = G[i]; return g["dog"] if kk(g["fav"]) == kk(B.Sname[i]) else g["fav"]
pnet = np.array([1.0 if net(seas[i], B.Sname[i]) > net(seas[i], other(i)) else 0.0 for i in tgt])
seedS = np.array([(G[i]["fseed"] if kk(G[i]["fav"]) == kk(B.Sname[i]) else G[i]["dseed"]) for i in tgt]); seedO = np.array([(G[i]["dseed"] if kk(G[i]["fav"]) == kk(B.Sname[i]) else G[i]["fseed"]) for i in tgt])
psd = np.where(seedS < seedO, 1.0, np.where(seedS > seedO, 0.0, pnet))
psim = np.array([B.simS[i] for i in tgt])
right = lambda p: int(((p >= .5) == (yy == 1)).sum())
isS = S16m[tgt]
print(f"real Sweet 16 + Elite 8 games: {len(tgt)} ({int(isS.sum())} S16, {int((~isS).sum())} E8)")
print(f"{'picker':38} | all | S16 | E8 | log loss")
ll = lambda p: float(-np.mean(yy * np.log(np.clip(p, 1e-6, 1)) + (1 - yy) * np.log(np.clip(1 - p, 1e-6, 1))))
rows = list(P.items()) + [("net rating", pnet), ("higher seed", psd), ("simulator (game-file line)", psim),
        ("current line + net 50/50 (vote-ish)", (P["line on S16-title (current)"] + pnet) / 2), ("current + all-rounds avg", (P["line on S16-title (current)"] + P["line on all rounds"]) / 2)]
for lab, p in rows:
    print(f"{lab:38} | {right(p):3} | {int(((p >= .5) == (yy == 1))[isS].sum()):3} | {int(((p >= .5) == (yy == 1))[~isS].sum()):2} | {ll(p) if p.min() > 0 and p.max() < 1 else float('nan'):.3f}")
