# Per-year PCA panels: same pooled PCA axes as the big map, 8 panels per slide (4 x 2) on a 1664 x 660 SVG.
# Per panel: plot box, axis cross at 0, then per box losers (ring = colored dot + background center) and winners (solid).
# Prints, per slide, the SVG body and each panel's label (year, games, model-vs-sim split record).
import json
OLD = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
P = json.load(open(OLD + r"\m103_out.json"))["points"]
lo_x, hi_x, lo_y, hi_y = -7.0, 4.0, -5.0, 5.0
PW, PH, GX, GY, TOP = 392, 250, 32, 24, 40          # plot width/height, gaps, room for the label above each plot
COL = {"Both wrong": "#8E6CC9", "Both right": "#C9C2B3", "Sim right, model wrong": "#2F6DB5", "Model right, sim wrong": "#D9622B"}
W = {"Both wrong": (6, 3), "Both right": (6, 3), "Sim right, model wrong": (10, 5), "Model right, sim wrong": (10, 5)}
years = sorted({p["year"] for p in P})
for s, ys in enumerate((years[:8], years[8:])):
    print(f"===== SLIDE {s + 1}: {ys[0]}-{ys[-1]}")
    body, labels = [], []
    for k, y in enumerate(ys):
        ox = (k % 4) * (PW + GX); oy = (k // 4) * (PH + GY + TOP) + TOP
        sx = lambda v: ox + (min(max(v, lo_x), hi_x) - lo_x) / (hi_x - lo_x) * PW
        sy = lambda v: oy + PH - (min(max(v, lo_y), hi_y) - lo_y) / (hi_y - lo_y) * PH
        body.append(f'<rect x="{ox}" y="{oy}" width="{PW}" height="{PH}" fill="#F5F2EA" stroke="#C9C2B3" stroke-width="1"/>')
        body.append(f'<path d="M{sx(0):.0f} {oy}V{oy + PH}M{ox} {sy(0):.0f}H{ox + PW}" stroke="#DCD5C6" stroke-width="1.5"/>')
        pts = [p for p in P if p["year"] == y]
        for q in ["Both wrong", "Both right", "Sim right, model wrong", "Model right, sim wrong"]:
            w, inner = W[q]
            for won in (False, True):
                d = "".join(f"M{sx(p['pc1']):.0f} {sy(p['pc2']):.0f}h0" for p in pts if p["quad"] == q and p["won"] == won)
                if not d: continue
                body.append(f'<path d="{d}" stroke="{COL[q]}" stroke-width="{w}"/>')
                if not won: body.append(f'<path d="{d}" stroke="#F5F2EA" stroke-width="{inner}"/>')
        g = lambda q: sum(1 for p in pts if p["quad"] == q) // 2
        labels.append((ox, oy - TOP, y, len(pts) // 2, g("Model right, sim wrong"), g("Sim right, model wrong")))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1664" height="618" viewBox="0 0 1664 618">'
           '<g stroke-linecap="round" fill="none">' + "".join(body) + "</g></svg>")
    path = rf"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\pca_years_{s + 1}.svg"
    open(path, "w", encoding="utf-8").write(svg); print("wrote", path, len(svg))
    for l in labels: print("LABEL", *l)
