import json, numpy as np
P = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m103_out.json"))["points"]
for won in (True, False):
    for q in ["Both right", "Model right, sim wrong", "Sim right, model wrong", "Both wrong"]:
        x = np.array([[p["pc1"], p["pc2"]] for p in P if p["quad"] == q and p["won"] == won])
        print(("WIN " if won else "LOSE"), f"{q:24} n {len(x):4} PC1 {x[:,0].mean():+.2f} PC2 {x[:,1].mean():+.2f}")
    x = np.array([[p["pc1"], p["pc2"]] for p in P if p["won"] == won]); print(("WIN " if won else "LOSE"), "ALL", len(x), f"PC1 {x[:,0].mean():+.2f} PC2 {x[:,1].mean():+.2f}")
