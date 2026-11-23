src = open("m305b_export_full.py", encoding="utf-8-sig").read(); src = src[:src.index("ALL = {}")]
import contextlib, io, json
with contextlib.redirect_stdout(io.StringIO()): exec(src)
ALL = json.load(open(os.path.join(HERE, "m305_full.json")))
SIMT = {}   # known sim title probs
for SP in (SIMP, SIMB):
    for s, v in SP.items(): a, b, q = v[2]; SIMT[(s, a, b)] = q; SIMT[(s, b, a)] = 1 - q
need = []; reqs = []
for key in ALL:
    for o in ALL[key]:
        s = o["season"]
        for e in o["rounds"][4]: reqs.append((s, e["a"], e["b"]))
predict(reqs)
newp = {}
for key in ALL:
    for o in ALL[key]:
        s = o["season"]; w = []
        for e in o["rounds"][4]:
            sp = e["p"] if e["pick"] == e["a"] else 1 - e["p"]          # sim chance a wins
            mix = .7 * sp + .3 * p(s, e["a"], e["b"]); w.append(e["a"] if mix >= .5 else e["b"])
        if (s, w[0], w[1]) not in SIMT: need.append((s, w[0], w[1]))
        newp[(key, s)] = w
print("title pairs needing a simulator run:", sorted(set(need)))
json.dump({f"{k[0]}|{k[1]}": v for k, v in newp.items()}, open(os.path.join(HERE, "m306_f4w.json"), "w"))

