import json
D = json.load(open("m285_brackets.json")); SR = json.load(open("m283_sim_r32.json"))
pairs = {}; miss = {}; r1 = 0
for d in D:
    s = d["season"]; pk = []
    for j, g in enumerate(d["games"]):
        v = [d["brackets"][k]["r1"][j]["pick"] for k in ("upset", "model", "sim")]
        p = max(set(v), key=v.count); pk.append(p)
        if not g["bye"]: r1 += p == g["won"]
    pairs[s] = [[pk[2*q], pk[2*q+1]] for q in range(16)]
    miss[s] = [[a, b] for a, b in pairs[s] if f"{a}|{b}" not in SR[s] and f"{b}|{a}" not in SR[s]]
json.dump(pairs, open("m289_vote_pairs.json", "w"))
print("vote R1 right", r1, "| sim pairs missing", sum(len(v) for v in miss.values()))
for s, v in miss.items():
    if v: print(s, json.dumps(v))
