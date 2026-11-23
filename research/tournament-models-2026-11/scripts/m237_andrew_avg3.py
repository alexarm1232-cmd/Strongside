# The games the 45% average (Upset 29 + Strongside + simulator) gets wrong: 111 of 511. What they look like, and what
# separates them, using every measure we have (including ones not in any model).
import os, sys, json, math, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
exec(open(os.path.join(H, "m217_missed.py"), encoding="utf-8").read().split("def heldout")[0])
U29 = json.load(open(os.path.join(H, "m219_out.json")))["inputs"]
ALL = dict(CAND); ALL.update({c: col(c) for c in U29})
gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
m1 = np.load(os.path.join(H, "m170_model_out.npy"))[gi]; s_up = 1 / (1 + np.exp(np.where(hsS, m1, -m1))); simS = Q.R.B.simS[gi]; sim_up = np.where(hsS, 1 - simS, simS)
STL, CAST, PCS = "L-H stl", "L-H cast_bpm_bpm", "L pt_d_share Perimeter Cut"
print("is 'share of perimeter cuts allowed' already in? the model has", [c for c in U29 if "Perimeter Cut" in c])
print(f"   r(L pt_d_share Perimeter Cut, L pt_d_ppp Perimeter Cut) = {np.corrcoef(ALL[PCS], col('L pt_d_ppp Perimeter Cut'))[0, 1]:+.2f}")
print(f"   r with net rating gap: steals gap {np.corrcoef(ALL[STL], rg)[0, 1]:+.2f} | cast BPM gap {np.corrcoef(ALL[CAST], rg)[0, 1]:+.2f} | perimeter cut share {np.corrcoef(ALL[PCS], rg)[0, 1]:+.2f}")
print(f"   r steals gap vs L d_tov (in model) {np.corrcoef(ALL[STL], col('L d_tov'))[0, 1]:+.2f} | cast BPM gap vs L-H depth_bpm (in model) {np.corrcoef(ALL[CAST], col('L-H depth_bpm'))[0, 1]:+.2f}")
# Andrew's test, average method: Round of 64 only, one row per game, outcome HSW (higher seed won), his test years held out.
# Original model: trained on every round of the other years (the usual way). Upset Model (31): trained on the other years'
# Round of 64 games. Average = mean of the two upset chances. AUC on HSW; games right; confusion matrix (0 = HS lost).
NEW = json.load(open(os.path.join(H, "m230_out.json")))["inputs"]; XU = np.column_stack([ALL[c] for c in NEW])
k = ~Q.FF; gi = np.array([r["i"] for r in rows]); hsS = np.array([r["HisS"] for r in rows])
hsw = 1 - y
ANDREW = {("2015-16", "2025-26"): {"forest": (None, 0.885), "tree": (0.90, 0.786)}, ("2016-17", "2024-25"): {"forest": (0.853, 0.904), "tree": (0.897, 0.804)}}
def mat(pred_hsw, yy):
    tp = int(((pred_hsw == 1) & (yy == 1)).sum()); fn = int(((pred_hsw == 0) & (yy == 1)).sum()); fp = int(((pred_hsw == 1) & (yy == 0)).sum()); tn = int(((pred_hsw == 0) & (yy == 0)).sum())
    return f"pred0/act0 {tn} | pred0/act1 {fn} | pred1/act0 {fp} | pred1/act1 {tp} | sensitivity {tp / max(tp + fn, 1):.1%} | specificity {tn / max(tn + fp, 1):.1%}"
for TEST in (("2015-16", "2025-26"), ("2016-17", "2024-25")):
    te_r = np.isin(seas, TEST); tr_r = ~te_r
    trG = np.where(~np.isin(Q.seas, TEST) & k)[0]; teG = gi[te_r]
    fit = Q.t_ridge(); m_tr, m_te = Q.base(trG, teG, fit); o_te = Q.run(m_tr, trG, m_te, teG, Q.EX)
    m_a, m_in = Q.base(trG, trG, fit); o_in = Q.run(m_a, trG, m_in, trG, Q.EX); pos = {g: j for j, g in enumerate(trG)}
    o_tr = np.array([o_in[pos[g]] for g in gi[tr_r]])
    s_te = 1 / (1 + np.exp(np.where(hsS[te_r], o_te, -o_te))); s_tr = 1 / (1 + np.exp(np.where(hsS[tr_r], o_tr, -o_tr)))   # upset chances
    f = ridge(XU[tr_r], y[tr_r], W[tr_r]); u_te = 1 / (1 + np.exp(-f(XU[te_r]))); u_tr = 1 / (1 + np.exp(-f(XU[tr_r])))
    yt, ytr = hsw[te_r], hsw[tr_r]
    print(f"\n=== test years {int(TEST[0][:4]) + 1} + {int(TEST[1][:4]) + 1} ({int(te_r.sum())} games, {int((yt == 0).sum())} upsets) | higher seed every time: {int(yt.sum())}/{int(te_r.sum())}")
    m_tr_, m_te_ = sim_up[tr_r], sim_up[te_r]
    a_tr, a_te = (s_tr + u_tr + m_tr_) / 3, (s_te + u_te + m_te_) / 3
    for lab, ptr, pte, cut in (("Original model", s_tr, s_te, .5), ("Upset Model 31 (40%)", u_tr, u_te, .4), ("Simulator", m_tr_, m_te_, .5), ("Average of 3 (50%)", a_tr, a_te, .5), ("Average of 3 (45%)", a_tr, a_te, .45)):
        pred = (pte < cut).astype(int)
        print(f"   {lab:26} training AUC {auc(1 - ptr, ytr):.3f} | testing AUC {auc(1 - pte, yt):.3f} | test games right {int((pred == yt).sum())}/{int(te_r.sum())} | upset picks {int((pred == 0).sum())} ({int(((pred == 0) & (yt == 0)).sum())} hit)")
        print(f"      {mat(pred, yt)}")
    A = ANDREW[TEST]; print(f"   Andrew (his slides, test incl. 2008/2009): forest training {A['forest'][0]} testing {A['forest'][1]} | tree training {A['tree'][0]} testing {A['tree'][1]}")