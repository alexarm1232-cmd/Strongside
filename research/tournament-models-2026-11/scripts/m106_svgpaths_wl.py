# PCA map paths split by box AND result: winners drawn as solid dots, losers as rings (a colored dot with a
# background-colored center drawn on top). Same plot area and scaling as m104.
import json, numpy as np
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
d = json.load(open(OLD + r"\m103_out.json")); P = d["points"]
lo_x, hi_x, lo_y, hi_y = -7.0, 4.0, -5.0, 5.0; W, H, L, T = 1040, 640, 60, 20
sx = lambda v: L + (min(max(v, lo_x), hi_x) - lo_x) / (hi_x - lo_x) * W
sy = lambda v: T + H - (min(max(v, lo_y), hi_y) - lo_y) / (hi_y - lo_y) * H
for q in ["Both wrong", "Both right", "Sim right, model wrong", "Model right, sim wrong"]:
    for won in (False, True):
        pts = [p for p in P if p["quad"] == q and p["won"] == won]
        print(f"## {q} | {'won' if won else 'lost'} | {len(pts)}")
        print("".join(f"M{sx(p['pc1']):.0f} {sy(p['pc2']):.0f}h0" for p in pts))
