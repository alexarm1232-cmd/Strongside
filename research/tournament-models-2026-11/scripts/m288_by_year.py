import os, json, contextlib, io
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read(); src = src[:src.index('print("\\nBRACKETS')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
def year(s, c1, c2):
    games = BI[s]["games"]; wins = BI[s]["wins"]; pk = []; r1 = r2 = 0
    for g in games:
        if g["H"] == g["L"]: pk.append(g["H"]); continue
        p = g["L"] if P1.get((s, g["L"]), 0) >= c1 / 100 else g["H"]; pk.append(p); r1 += p == g["won"]
    for q in range(16):
        h, l, pu = pr32("separate", s, pk[2 * q], pk[2 * q + 1]); w = l if pu >= c2 / 100 else h; r2 += wins.get(w, 0) >= 2
    return r1, r2, r1 + 2 * r2
SET = [(40, 45), (40, 40), (45, 45), (50, 50)]
print("year | " + " | ".join(f"{a}/{b}: R64 R32 pts" for a, b in SET))
T = {k: [0, 0, 0] for k in SET}
for s in SEASONS:
    row = []
    for k in SET:
        r = year(s, *k); row.append(f"{r[0]:2} {r[1]:2} {r[2]:3}"); T[k] = [T[k][j] + r[j] for j in range(3)]
    print(int(s[:4]) + 1, "|", " | ".join(row))
print("total |", " | ".join(f"{T[k][0]} {T[k][1]} {T[k][2]}" for k in SET))
