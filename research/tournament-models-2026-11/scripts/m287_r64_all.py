import os, json, contextlib, io
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read(); src = src[:src.index('print("\\nBRACKETS')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
import numpy as np
D = json.load(open(os.path.join(HERE, "m186_r64_features.json"))); O = json.load(open(os.path.join(HERE, "m230_out.json")))
for lab, key in (("held out (400)", "p_heldout"), ("all years (412)", "p_all")):
    P1.clear()
    for r, p in zip(D["rows"], O[key]): P1[(r["s"], kk(r["L"]))] = float(p); P1[(r["s"], kk(r["H"]))] = 1 - float(p)
    for c2 in (40, 45):
        pts, a, b, u = bracket(up40, "separate", c2 / 100); print(f"R64 Upset Model {lab} @40, R32 @{c2}: points {pts} | R1 {a} | R32 {b} | R32 upset picks {u}")
