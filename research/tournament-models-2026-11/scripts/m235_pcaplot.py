import json, os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(H, "m234_pca.json"))); P = D["points"]
CATS = [("Higher seed picked right", "#2a78d6", "o"), ("Upset picked right", "#1baf7a", "^"), ("Upset missed", "#eb6834", "s"), ("Upset picked wrong", "#6250d6", "D")]
plt.rcParams.update({"font.family": "Arial", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(15, 7.2), sharex=True, sharey=True, facecolor="#fcfcfb")
for ax, side, title in ((axes[0], "H", "Higher seeds"), (axes[1], "L", "Lower seeds")):
    ax.set_facecolor("#fcfcfb")
    for c, col, mk in CATS:
        for won in (True, False):
            q = [p for p in P if p["c"] == c and p["side"] == side and p["w"] == won]
            if not q: continue
            ax.scatter([p["x"] for p in q], [p["y"] for p in q], s=30 if c != "Higher seed picked right" else 18, marker=mk,
                       facecolors=col if won else "none", edgecolors=col, linewidths=1.1, alpha=.85 if c != "Higher seed picked right" else .45, zorder=3 if c != "Higher seed picked right" else 2)
        q = [p for p in P if p["c"] == c and p["side"] == side]
        cx, cy = np.mean([p["x"] for p in q]), np.mean([p["y"] for p in q])
        ax.scatter([cx], [cy], s=260, marker=mk, facecolors=col, edgecolors="#0b0b0b", linewidths=1.6, zorder=5)
    ax.axhline(0, color="#e1e0d9", lw=1, zorder=1); ax.axvline(0, color="#e1e0d9", lw=1, zorder=1)
    ax.set_title(f"{title} in Round 1 games", fontsize=13, color="#0b0b0b", loc="left")
    ax.set_xlabel(f"PC1 ({D['pve'][0]:.0%}): ← stronger cast, holds leads · more perimeter cuts allowed →", color="#52514e")
    for sp in ax.spines.values(): sp.set_color("#c3c2b7")
    ax.tick_params(colors="#898781")
axes[0].set_ylabel(f"PC2 ({D['pve'][1]:.0%}): ↑ offensive rebounding, assisted shots allowed", color="#52514e")
from matplotlib.lines import Line2D
n = {c: sum(1 for p in P if p["c"] == c and p["side"] == "H") for c, _, _ in CATS}
hand = [Line2D([], [], marker=mk, ls="", color=col, markerfacecolor=col, markersize=9, label=f"{c} ({n[c]} games)") for c, col, mk in CATS]
hand += [Line2D([], [], marker="o", ls="", color="#52514e", markerfacecolor="#52514e", markersize=8, label="filled = won the game"),
         Line2D([], [], marker="o", ls="", color="#52514e", markerfacecolor="none", markersize=8, label="hollow = lost"),
         Line2D([], [], marker="o", ls="", color="#52514e", markerfacecolor="#888", markeredgecolor="#0b0b0b", markersize=13, label="large outlined = group center")]
fig.legend(handles=hand, loc="upper center", ncol=4, frameon=False, fontsize=10.5, bbox_to_anchor=(.5, 1.0))
fig.suptitle("PCA of Round 1 teams, colored by how the 45% average of three did (2010–2026, 511 games)", y=1.06, fontsize=15, color="#0b0b0b")
fig.tight_layout(); out = r"C:\Users\crtra\Downloads\basketball\logs\pca_average3_round1.png"; fig.savefig(out, dpi=130, bbox_inches="tight", facecolor="#fcfcfb"); print(out)