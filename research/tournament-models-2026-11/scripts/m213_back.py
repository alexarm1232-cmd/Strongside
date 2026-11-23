import os, sys, runpy
sys.argv = ["x"]; H = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"; sys.path.insert(0, H)
src = open(os.path.join(H, "m210_followups.py"), encoding="utf-8").read().split("    # (3) close-game halves")[0]
src += '''
    early = np.array([int(s[:4]) < 2018 for s in seas])
    print(f"   always higher seed 2010-17: {int((y[early] == 0).sum())}/{int(early.sum())}")
    sp = rep("L d_tov", "L stl") + ["L d_nst_to"]
    for lab, ins in (("locked 28", U), ("steals split", sp), ("add L stl", U + ["L stl"]), ("cast BPM gap (top 2 BPM out)", rep("L-H depth_bpm", "L-H cast_bpm (no top-2 BPM)")),
                     ("cast BPM gap (top 2 minutes out)", rep("L-H depth_bpm", "L-H cast_bpm (no top-2 minutes)")), ("add H pt_share Drive & Kick", U + ["H pt_share Drive & Kick"])):
        X = np.column_stack([col(c) for c in ins]); pf = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
        print(f"   backward {lab:34} right {int(((pf >= .4) == (y[early] == 1)).sum())}/{int(early.sum())} | AUC {auc(pf, y[early]):.3f}")'''
exec(compile(src.replace('if __name__ == "__main__":', 'if True:'), "m211", "exec"), {"__file__": os.path.join(H, "m210_followups.py"), "__name__": "m211"})