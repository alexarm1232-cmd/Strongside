# Coordinates for the PCA map slide: each box's team points as one SVG path of dots ("Mx yh0" with round caps),
# on a 1040 x 640 plot area; plus centroids and axis ticks. Printed so they can be placed in the slide by hand.
import json, numpy as np
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
d = json.load(open(OLD + r"\m103_out.json"))
P = d["points"]; x = np.array([p["pc1"] for p in P]); y = np.array([p["pc2"] for p in P])
lo_x, hi_x = np.percentile(x, 0.5), np.percentile(x, 99.5); lo_y, hi_y = np.percentile(y, 0.5), np.percentile(y, 99.5)
lo_x, hi_x = np.floor(lo_x), np.ceil(hi_x); lo_y, hi_y = np.floor(lo_y), np.ceil(hi_y)
W, H, L, T = 1040, 640, 60, 20
sx = lambda v: L + (min(max(v, lo_x), hi_x) - lo_x) / (hi_x - lo_x) * W
sy = lambda v: T + H - (min(max(v, lo_y), hi_y) - lo_y) / (hi_y - lo_y) * H
print("range", lo_x, hi_x, lo_y, hi_y)
for q in ["Both right", "Both wrong", "Sim right, model wrong", "Model right, sim wrong"]:
    pts = [p for p in P if p["quad"] == q]
    print(q, len(pts)); print("".join(f"M{sx(p['pc1']):.0f} {sy(p['pc2']):.0f}h0" for p in pts))
for q, (cx, cy, n) in d["centroids"].items(): print("centroid", q, round(sx(cx)), round(sy(cy)))
for v in range(int(lo_x), int(hi_x) + 1, 2): print("xtick", v, round(sx(v)))
for v in range(int(lo_y), int(hi_y) + 1, 2): print("ytick", v, round(sy(v)))
print("zero", round(sx(0)), round(sy(0)))
