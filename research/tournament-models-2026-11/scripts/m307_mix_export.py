# Final Four and title = 70% simulator + 30% regular model; rebuild both full brackets' last two rounds and rescore.
import os, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m306_mix.py"), encoding="utf-8-sig").read(); src = src[:src.index("need = []")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
SIMT.update({("2010-11", "Louisville", "Ohio St"): .3045, ("2010-11", "Ohio St", "Louisville"): 1 - .3045,
             ("2013-14", "Arizona", "Florida"): .5206, ("2013-14", "Florida", "Arizona"): 1 - .5206,
             ("2018-19", "Duke", "Virginia"): .4352, ("2018-19", "Virginia", "Duke"): 1 - .4352,
             ("2025-26", "Duke", "Michigan"): .523, ("2025-26", "Michigan", "Duke"): 1 - .523})
for key in ALL:
    for o in ALL[key]:
        s = o["season"]; w = WON[s]; f4w = []
        reqs = [(s, e["a"], e["b"]) for e in o["rounds"][4]]; predict(reqs)
        for e in o["rounds"][4]:
            sp = e["p"] if e["pick"] == e["a"] else 1 - e["p"]
            mix = .7 * sp + .3 * p(s, e["a"], e["b"]); pk = e["a"] if mix >= .5 else e["b"]
            e.update(pick=pk, p=round(mix if pk == e["a"] else 1 - mix, 3), right=w.get(pk, 0) >= 5, sim=round(sp, 3)); f4w.append(pk)
        a, b = f4w; predict([(s, a, b)]); sp = SIMT[(s, a, b)]; mix = .7 * sp + .3 * p(s, a, b); pk = a if mix >= .5 else b
        o["rounds"][5] = [{"a": a, "b": b, "pick": pk, "p": round(mix if pk == a else 1 - mix, 3), "real": next((t for t in w if w[t] >= 6), None), "right": w.get(pk, 0) >= 6}]
        o["score"][4] = sum(e["right"] for e in o["rounds"][4]); o["score"][5] = int(o["rounds"][5][0]["right"])
        o["points"] = sum(c * pt for c, pt in zip(o["score"], PTS))
    print(key, sum(o["points"] for o in ALL[key]), [sum(o["score"][i] for o in ALL[key]) for i in range(6)],
          "champions:", [(o["year"], o["rounds"][5][0]["pick"]) for o in ALL[key] if o["rounds"][5][0]["right"]])
json.dump(ALL, open(os.path.join(HERE, "m307_full.json"), "w"), separators=(",", ":"))
