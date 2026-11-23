import os, sys, runpy
sys.argv = ["x"]; H = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"; sys.path.insert(0, H)
src = open(os.path.join(H, "m210_followups.py"), encoding="utf-8").read().split("    # (3) close-game halves")[0]
src += '''
    TM = Q.R.B.TM; rg = np.array([TM[r["s"]][r["L"]]["adj_net"] - TM[r["s"]][r["H"]]["adj_net"] for r in rows])
    for nm in ("L-H cast_bpm (no top-2 BPM)", "L-H cast_bpm (no top-2 minutes)", "L-H depth_bpm", "L stl"):
        print(f"   r({nm}, net rating gap) = {np.corrcoef(col(nm), rg)[0, 1]:+.2f}")
    for nm in ("H 3pt/vol: hot", "L-H 3pt/vol: hot", "H 3pt/vol: cold", "L 3pt/vol: tpa_pg", "L 3pt/vol: r3", "H p3", "H pts3", "L p3"):
        print("   " + line(nm))
    print(model("add H 3pt/vol: hot", U + ["H 3pt/vol: hot"]))
    best = rep("L d_tov", "L stl") + ["L d_nst_to"]
    best = [("L-H cast_bpm (no top-2 BPM)" if c == "L-H depth_bpm" else c) for c in best]
    print(model("steals split + cast BPM gap (top 2 BPM out)", best))
    print(model("steals split + cast BPM gap + H pt_share Drive & Kick", best + ["H pt_share Drive & Kick"]))
    print(model("steals split + cast BPM gap + H 3pt hot", best + ["H 3pt/vol: hot"]))
    early = np.array([int(s[:4]) < 2018 for s in seas])
    for lab, ins in (("locked 28", U), ("steals split + cast BPM gap", best)):
        X = np.column_stack([col(c) for c in ins]); pf = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early])))
        print(f"   forward test (fit 2010-17, score 2018-26) {lab:30} right {int(((pf >= .4) == (y[~early] == 1)).sum())}/255 | AUC {auc(pf, y[~early]):.3f}")
'''
exec(compile(src.replace('if __name__ == "__main__":', 'if True:'), "m211", "exec"), {"__file__": os.path.join(H, "m210_followups.py"), "__name__": "m211"})