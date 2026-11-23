import json
D = json.load(open("m293_brackets_three.json")); P = ("vote", "blend", "upset")
for p in P:
    L = []
    for d in D:
        sd = d["seeds"]
        for q in range(16):
            G2 = d["games"][2*q:2*q+2]; ts = [t for g in G2 for t in (g["a"], g["b"])]; top = min(ts, key=lambda t: sd[t])
            j = 2*q if top in (G2[0]["a"], G2[0]["b"]) else 2*q + 1
            pk = d["brackets"][p]["r2"][q]["pick"]
            if sd[top] <= 2 and d["brackets"][p]["r1"][j]["pick"] == top and pk != top: L.append((d["year"], top, sd[top], pk, sd[pk], d["r2won"][q], d["brackets"][p]["r2"][q]["p"]))
    print(f"{p}: picked a 1/2 seed it had alive to lose in the Round of 32: {len(L)} times, right {sum(x[3] == x[5] for x in L)}, top seed actually won {sum(x[1] == x[5] for x in L)}")
    for x in L: print("     ", x)
