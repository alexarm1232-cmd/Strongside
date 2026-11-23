# Lock candidate: Round of 32 Upset Model = core 12 style inputs + 4 style matchups (16 inputs, no seed, no net, no strength,
# pre-tournament only), ridge 30, half-life 12; Round of 32 pick = 50/50 average with model 1 (pre-tournament), upset at 40%.
# Fixed settings (no tuning on these numbers beyond what m266 showed). Also: Round 1 picker rebuilt pre-tournament
# (R64 Upset Model + model 1 pre, no simulator because its inputs use each game's out list).
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m265_r32_honest_cut.py"), encoding="utf-8").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src[:src.index("print(f\"Round of 32:")])
import numpy as np
INS = U(CORE12, mk_); CUT = .40
pa, ph, fw, b = evaluate(INS, 30.0); bl = (ph + sp) / 2; blf = (fw + sp) / 2
X = np.column_stack([col(c) for c in INS]); mu, sd = X.mean(0), X.std(0)
print(f"Round of 32 Upset Model: {len(INS)} inputs | r with model 1 pre {np.corrcoef(ph, sp)[0, 1]:+.2f}")
print(f"   alone, held out: AUC {auc(ph, ys):.3f} | right @40 {right(ph >= .4)} | fit on all years AUC {auc(pa, ys):.3f} right @40 {right(pa >= .4)}")
print(f"   averaged with model 1 pre @40, held out: {right(bl >= CUT)} / {nS} | AUC {auc(bl, ys):.3f} | upset picks {int((bl >= CUT).sum())} (hit {int(((bl >= CUT) & (ys == 1)).sum())})")
print(f"   forward (fit 2010-17 -> 2018-26): {right(blf >= CUT, ~early)}/112 (model 1 pre {right(sp >= .5, ~early)}) | backward: {right(blf >= CUT, early)}/144 (model 1 pre {right(sp >= .5, early)})")
print(f"   model 1 pre alone: {right(sp >= .5)} | upset picks {int((sp >= .5).sum())} (hit {int(((sp >= .5) & (ys == 1)).sum())}) | higher seed {right(np.zeros(nS) >= .5)}")
print("   by cutoff (averaged): " + " | ".join(f"{c}%: {right(bl >= c / 100)} ({int((bl >= c / 100).sum())} picks, {int(((bl >= c / 100) & (ys == 1)).sum())} hit)" for c in (35, 38, 40, 42, 45, 50)))
print("\n   inputs, standardized weights fit on all years (+ = helps the lower seed):")
for i in np.argsort(-np.abs(b[:-1])): print(f"      {nice(INS[i]) if not INS[i].startswith('MU ') else 'matchup: ' + INS[i][3:]:70} {b[i]:+.3f}")
print("\n   year | model 1 pre | R32 average | upset picks (hit)")
for s in SEASONS:
    m = Ss == s; pk = bl >= CUT; print(f"      {int(s[:4]) + 1} | {right(sp >= .5, m)} | {right(pk, m)} | {int(pk[m].sum())} ({int((pk & m & (ys == 1)).sum())})")
json.dump({"name": "Round of 32 Upset Model (candidate)", "inputs": INS, "ridge": 30, "half_life": 12, "weights": b.tolist(), "mu": mu.tolist(), "sd": sd.tolist(),
           "pick_rule": "average with model 1 (pre-tournament variant G) 50/50, pick the lower seed at 40%",
           "matchups": {"MU lower uses x higher leaks: Pick & Pop": "z(L pt_share Pick & Pop) * z(H pt_d_ppp Pick & Pop)",
                        "MU lower good at x higher leaks: Perimeter Cut": "z(L pt_ppp Perimeter Cut) * z(H pt_d_ppp Perimeter Cut)",
                        "MU lower uses x higher allows often: Perimeter Cut": "z(L pt_share Perimeter Cut) * z(H pt_d_share Perimeter Cut)",
                        "MU edge (lower off vs higher def) - (higher off vs lower def): Rim Attack": "(z(L pt_ppp RA) + z(H pt_d_ppp RA)) - (z(H pt_ppp RA) + z(L pt_d_ppp RA))"},
           "p_heldout": ph.tolist(), "blend_heldout": bl.tolist()}, open(os.path.join(HERE, "upset_model_r32_candidate.json"), "w"), indent=1)
# ---- Round 1 picker, pre-tournament
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); r1 = D["rows"]; y1 = np.array(D["y"]); pho = np.array(json.load(open(os.path.join(HERE, "m230_out.json")))["p_heldout"])
g1 = np.array([r["i"] for r in r1]); h1 = np.array([r["HisS"] for r in r1]); m_pre = np.load(os.path.join(HERE, "m262_model_pre_G.npy"))[g1]; m_old = np.load(os.path.join(HERE, "m170_model_out.npy"))[g1]
up_pre = 1 / (1 + np.exp(np.where(h1, m_pre, -m_pre))); up_old = 1 / (1 + np.exp(np.where(h1, m_old, -m_old))); simu = np.where(h1, 1 - B.simS[g1], B.simS[g1])
r_ = lambda p, c: int(((p >= c) == (y1 == 1)).sum())
s1 = np.array([r["s"] for r in r1]); S1 = sorted(set(s1))
def honest1(p):
    pk = np.zeros(len(p), bool)
    for s in S1:
        tr, te = s1 != s, s1 == s; c = max([c / 100 for c in range(30, 61)], key=lambda c: (int(((p[tr] >= c) == (y1[tr] == 1)).sum()), -abs(c - .45))); pk[te] = p[te] >= c
    return int((pk == (y1 == 1)).sum())
print(f"\nRound 1 ({len(y1)} games), held out:")
print(f"   Upset Model @40: {r_(pho, .4)} | model 1 old (who plays) @50: {r_(up_old, .5)} | model 1 pre @50: {r_(up_pre, .5)} | simulator (game-day out lists) @50: {r_(simu, .5)}")
a3o = (pho + up_old + simu) / 3; a2p = (pho + up_pre) / 2
print(f"   average of 3 as used (Upset + model 1 old + simulator) @45: {r_(a3o, .45)} | honest cutoff {honest1(a3o)}")
print(f"   PRE-TOURNAMENT average of 2 (Upset + model 1 pre) @45: {r_(a2p, .45)} | @40 {r_(a2p, .40)} | honest cutoff {honest1(a2p)} | AUC {auc(a2p, y1):.3f}")
