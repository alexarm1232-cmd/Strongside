# Draw the full CART tree (trained on all 1,007 games, leaves down to 1 game) as one SVG image: leaves spread evenly
# along the bottom, each split drawn as a bracket, leaves colored by who wins there (stronger-rated team = blue,
# weaker = orange), the top two levels of splits labeled. Saved to fulltree.svg for upload to the deck.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
names = json.load(open(os.path.join(C.HERE, "m112_names.json")))
idx = np.where(~C.FF)[0]
tree = C.grow(C.X, C.y, idx, 1, C.X.shape[1], np.random.default_rng(0), np.zeros(C.X.shape[1]))
def depth(n): return 0 if "f" not in n else 1 + max(depth(n["L"]), depth(n["R"]))
D = depth(tree); L = len(C.leaves(tree)); W, H, TOP, BOT = 1664, 640, 70, 20
dy = (H - TOP - BOT) / D; k = [0]; parts = []; labels = []
def place(n, d):
    y = TOP + d * dy
    if "f" not in n:
        x = 6 + k[0] * (W - 12) / (L - 1); k[0] += 1
        col = "#2F6DB5" if n["p"] > 0.5 else "#D9622B"
        parts.append(f'<path d="M{x:.1f} {y:.1f}h0" stroke="{col}" stroke-width="7" stroke-linecap="round"/>')
        return x, y
    xl, yl = place(n["L"], d + 1); xr, yr = place(n["R"], d + 1); x = (xl + xr) / 2
    w = max(0.8, 3.2 - 0.25 * d)
    parts.append(f'<path d="M{xl:.1f} {yl:.1f}V{y + dy * 0.5:.1f}H{xr:.1f}V{yr:.1f}M{x:.1f} {y + dy * 0.5:.1f}V{y:.1f}" fill="none" stroke="#4A5568" stroke-width="{w:.1f}"/>')
    if d <= 1: labels.append((x, y, names[C.FEAT[n["f"]]], n["thr"], n["n"], n["k"] / n["n"]))
    return x, y
place(tree, 0)
txt = []
for x, y, nm, thr, n, p in labels:
    txt.append(f'<text x="{x:.0f}" y="{y - 30:.0f}" font-family="Arial" font-size="20" font-weight="bold" fill="#15233B" text-anchor="middle">{nm.replace("&", "&amp;")} ≤ {thr:.2f}</text>')
    txt.append(f'<text x="{x:.0f}" y="{y - 8:.0f}" font-family="Arial" font-size="18" fill="#4A5568" text-anchor="middle">{n} games · stronger won {p:.0%}</text>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#FBFAF6"/>'
       + "".join(parts) + "".join(txt) + "</svg>")
open(os.path.join(C.HERE, "fulltree.svg"), "w", encoding="utf-8").write(svg)
print("leaves", L, "depth", D, "svg bytes", len(svg)); print(labels)
print("leaves where stronger wins:", sum(1 for l in C.leaves(tree) if l["p"] > 0.5), "of", L,
      "| leaves with <= 3 games:", sum(1 for l in C.leaves(tree) if l["n"] <= 3))
