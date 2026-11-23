# Export the upset models' Rounds 1-2 bracket picks (R64 Upset Model @40 -> R32 standalone @45) with chances.
import os, sys, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read()
src = src[:src.index('print("\\nBRACKETS')] if 'print("\\nBRACKETS' in src else src
with contextlib.redirect_stdout(io.StringIO()): exec(src)
out = {}
for s in SEASONS:
    games = BI[s]["games"]; r1 = []
    for g in games:
        if g["H"] == g["L"]: r1.append({"pick": g["H"], "p": None}); continue
        pl = P1.get((s, g["L"]), 0.0); r1.append({"pick": g["L"] if pl >= .4 else g["H"], "p": round(pl if pl >= .4 else 1 - pl, 3)})
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; h, l, pu = pr32("separate", s, a, b)
        w = l if pu >= .45 else h; r2.append({"pick": w, "p": round(pu if w == l else 1 - pu, 3)})
    out[s] = {"r1": r1, "r2": r2}
json.dump(out, open(os.path.join(HERE, "m284_upset_picks.json"), "w"))
print("saved", len(out))
