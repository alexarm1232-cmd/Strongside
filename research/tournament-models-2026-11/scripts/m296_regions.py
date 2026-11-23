import json
D = json.load(open("m293_brackets_three.json")); P = ("vote", "blend", "upset")
reg = []; allmiss = {"r1": 0, "r2": 0}; tot = {"r1": 0, "r2": 0}; one_down = {p: [] for p in P}
for d in D:
    sd = d["seeds"]
    for k in range(4):
        pts = {}
        for p in P:
            b = d["brackets"][p]; r1 = sum(b["r1"][j]["pick"] == d["games"][j]["won"] for j in range(8 * k, 8 * k + 8) if not d["games"][j]["bye"])
            r2 = sum(b["r2"][q]["pick"] == d["r2won"][q] for q in range(4 * k, 4 * k + 4)); pts[p] = r1 + 2 * r2
        ts = [t for g in d["games"][8*k:8*k+8] for t in (g["a"], g["b"])]; one = min(ts, key=lambda t: sd[t])
        reg.append((pts["vote"], d["year"], one, pts))
    for j, g in enumerate(d["games"]):
        if g["bye"]: continue
        tot["r1"] += 1; allmiss["r1"] += all(d["brackets"][p]["r1"][j]["pick"] != g["won"] for p in P)
    for q in range(16):
        tot["r2"] += 1; allmiss["r2"] += all(d["brackets"][p]["r2"][q]["pick"] != d["r2won"][q] for p in P)
        ts = [t for g in d["games"][2*q:2*q+2] for t in (g["a"], g["b"])]; top = min(ts, key=lambda t: sd[t])
        for p in P:
            pk = d["brackets"][p]["r2"][q]["pick"]
            if sd[top] <= 2 and pk != top and d["brackets"][p]["r1"][[2*q, 2*q+1][[t in (d["games"][2*q]["a"], d["games"][2*q]["b"]) for t in [top]][0] and 0 or 1]]["pick"] == top:
                one_down[p].append((d["year"], top, sd[top], pk, sd[pk], d["r2won"][q]))
reg.sort()
print("worst regions for the vote (points of 24 max):")
for v, y, one, pts in reg[:12]: print(f"   {y} {one} region: vote {pts['vote']}, blend {pts['blend']}, upset {pts['upset']}")
print("best possible region = 24 (8 R1 + 4 R32 x2); average vote region:", round(sum(r[0] for r in reg) / len(reg), 1))
print("games ALL THREE missed:", allmiss, "of", tot)
for p in P:
    L = one_down[p]; print(f"\n{p}: picked a 1 or 2 seed (that it had winning Round 1) to LOSE in the Round of 32: {len(L)} times, right {sum(x[3] == x[5] for x in L)}")
    for x in L: print("     ", x)
