import json
for fn in ("m285_brackets.json", "m293_brackets_three.json"):
    D = json.load(open(fn))
    for d in D:
        for q in range(16):
            if d["r2won"][q] is None:
                G2 = d["games"][2*q:2*q+2]; bye = [g for g in G2 if g["bye"]]
                print(fn, d["year"], "pod", q, [(g["a"], g["b"], g["won"]) for g in G2], {p: d["brackets"][p]["r2"][q]["pick"] for p in d["brackets"]})
                if bye: d["r2won"][q] = "Oregon" if d["year"] == 2021 else None
    json.dump(D, open(fn, "w"), separators=(",", ":"))
