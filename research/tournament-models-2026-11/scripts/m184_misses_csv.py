import csv, json, re, sys
D = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
O = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
sys.path.insert(0, O); import upset_data as U
CSV = {(r["Season"], r["Team"]): r for r in csv.DictReader(open(r"C:\Users\crtra\Downloads\Round of 64 - pre-tournament data 2010-2026.csv", encoding="utf-8"))}
games = [("2025-26", "Ohio St", "TCU"), ("2025-26", "North Carolina", "VCU"), ("2025-26", "Wisconsin", "High Point"), ("2025-26", "Georgia", "Saint Louis"),
         ("2025-26", "Clemson", "Iowa"), ("2025-26", "Villanova", "Utah St"), ("2024-25", "Missouri", "Drake"), ("2024-25", "Kansas", "Arkansas"),
         ("2024-25", "Clemson", "McNeese"), ("2024-25", "Marquette", "New Mexico"), ("2024-25", "Memphis", "Colorado St"), ("2024-25", "Mississippi St", "Baylor")]
T = {}
for s in ("2024-25", "2025-26"):
    gs, td = U.load(s[2:4] + s[5:7]); first = min(g["date"] for g in gs if g["ncaa"])
    for g in gs:
        if g["date"] < first or not g["ncaa"]: continue
        for t in (g["home"], g["away"]):
            a = g["side"][t]; r = T.setdefault((s, t), {"g": 0, "fga": 0, "fgm": 0, "reb": 0}); r["g"] += 1
            for k in ("fga", "fgm", "reb"): r[k] += a[k]
z = {"g": 0, "fga": 0, "fgm": 0, "reb": 0}
print("season|higher|lower (won)|tourney games H/L|FGA diff pre -> end|FG diff pre -> end|TRB diff pre -> end|NetRtg diff pre")
for s, H, L in games:
    cH, cL = CSV[(s, H)], CSV[(s, L)]; tH, tL = T.get((s, H), z), T.get((s, L), z)
    d = lambda k, kk: (int(cH[k]) - int(cL[k]), int(int(cH[k]) + tH[kk] - int(cL[k]) - tL[kk]))
    a, b, c = d("FGA", "fga"), d("FGM", "fgm"), d("TRB", "reb")
    print(f"{s}|{H} ({cH['Seed']})|{L} ({cL['Seed']})|{tH['g']}/{tL['g']}|{a[0]:+d} -> {a[1]:+d}|{b[0]:+d} -> {b[1]:+d}|{c[0]:+d} -> {c[1]:+d}|{float(cH['NetRtg']) - float(cL['NetRtg']):+.1f}")

