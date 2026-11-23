# Random-forest variable importance (mean decrease in Gini) on the model's 30 inputs, every game (Round of 64 to title,
# 1,007), 500 trees, mtry = floor(sqrt(30)) = 5. Drawn as Andrew-style dot plot with all 30 inputs, two columns of 15 on
# one shared scale, saved as varimp30.svg for upload.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import m110_cart_rf as C
names = json.load(open(os.path.join(C.HERE, "m112_names.json")))
C.X = C.R.X30.copy()
idx = np.where(~C.FF)[0]
trees, imp, oob = C.forest(idx, ntree=500, seed=7)
F30 = C.FEAT[:C.X.shape[1]]; o = list(np.argsort(-imp))
print("OOB AUC", round(C.auc(oob[idx], C.y[idx]), 4))
for r, j in enumerate(o): print(f"{r + 1:2d}. {names[F30[j]]:46} {imp[j]:6.2f}")
json.dump({"importance": imp.tolist(), "order": [int(j) for j in o], "oob_auc": C.auc(oob[idx], C.y[idx])}, open(os.path.join(C.HERE, "m118_out.json"), "w"))
# dot plot
W, H = 1664, 660; COLW = 832; LAB = 470; PL = LAB + 20; PW = COLW - PL - 30; TOP = 20; RH = 38
mx = math.ceil(max(imp) / 5) * 5
sx = lambda v, c: c * COLW + PL + v / mx * PW
el = [f'<rect width="{W}" height="{H}" fill="#F5F2EA"/>']
for c in range(2):
    x0 = c * COLW + PL; el.append(f'<rect x="{x0}" y="{TOP - 10}" width="{PW}" height="{16 * RH}" fill="#FBFAF6" stroke="#4A5568" stroke-width="1.5"/>')
    for t in range(0, mx + 1, 5):
        xt = sx(t, c); el.append(f'<path d="M{xt:.1f} {TOP + 16 * RH - 10}v8" stroke="#4A5568" stroke-width="1.5"/>')
        el.append(f'<text x="{xt:.1f}" y="{TOP + 16 * RH + 20}" font-family="Arial" font-size="20" fill="#4A5568" text-anchor="middle">{t}</text>')
for r, j in enumerate(o):
    c, row = divmod(r, 16); y = TOP + row * RH + 10
    el.append(f'<path d="M{c * COLW + PL} {y}h{PW}" stroke="#DCD5C6" stroke-width="1" stroke-dasharray="3 5"/>')
    el.append(f'<text x="{c * COLW + LAB + 10}" y="{y + 7}" font-family="Arial" font-size="21" fill="#15233B" text-anchor="end">{r + 1}. {names[F30[j]].replace("&", "&amp;")}</text>')
    top3 = r < 3
    el.append(f'<circle cx="{sx(imp[j], c):.1f}" cy="{y}" r="8" fill="{"#D9622B" if top3 else "#FBFAF6"}" stroke="{"#B04A17" if top3 else "#15233B"}" stroke-width="3"/>')
el.append(f'<text x="{W / 2}" y="{H - 8}" font-family="Arial" font-size="20" fill="#4A5568" text-anchor="middle">Mean decrease in Gini</text>')
open(os.path.join(C.HERE, "varimp30.svg"), "w", encoding="utf-8").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(el) + "</svg>")
print("scale max", mx)


