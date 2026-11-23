src = open("m302_full_brackets.py", encoding="utf-8").read(); src = src[:src.index('print(f"{\'Full bracket')]
import contextlib, io, json
with contextlib.redirect_stdout(io.StringIO()): exec(src)
SIMP = {"2009-10": [("Kansas St","Kansas",.2958),("Duke","West Virginia",.6214),("Kansas","Duke",.535)],
"2010-11": [("Wisconsin","Georgetown",.6256),("Ohio St","Duke",.5651),("Wisconsin","Ohio St",.3681)],
"2011-12": [("Kentucky","Michigan St",.5594),("Ohio St","Georgetown",.6996),("Kentucky","Ohio St",.5204)],
"2012-13": [("Louisville","Gonzaga",.5335),("Florida","Miami (FL)",.6792),("Louisville","Florida",.4723)],
"2013-14": [("Arizona","Louisville",.4698),("Florida","Michigan St",.5727),("Louisville","Florida",.5638)],
"2014-15": [("Duke","Virginia",.4842),("Kentucky","Wisconsin",.5949),("Virginia","Kentucky",.346)],
"2015-16": [("North Carolina","Michigan St",.4952),("Kansas","Oregon",.6544),("Michigan St","Kansas",.4805)],
"2016-17": [("Gonzaga","Florida",.6743),("North Carolina","Oregon",.5883),("Gonzaga","North Carolina",.6171)],
"2017-18": [("North Carolina","Virginia",.3777),("Villanova","Syracuse",.8158),("Virginia","Villanova",.5204)],
"2018-19": [("Duke","Gonzaga",.492),("Virginia","North Carolina",.6301),("Gonzaga","Virginia",.4422)],
"2020-21": [("Baylor","Houston",.5415),("Gonzaga","Michigan",.6474),("Baylor","Gonzaga",.3601)],
"2021-22": [("Kansas","Villanova",.5279),("Gonzaga","Baylor",.637),("Kansas","Gonzaga",.3276)],
"2022-23": [("Alabama","Kentucky",.7124),("UCLA","Houston",.4775),("Alabama","Houston",.4891)],
"2023-24": [("UConn","Baylor",.7148),("Purdue","Kentucky",.7064),("UConn","Purdue",.5655)],
"2024-25": [("Florida","Auburn",.5234),("Duke","Tennessee",.6314),("Florida","Duke",.4813)],
"2025-26": [("Houston","Duke",.3917),("Michigan","Arizona",.4981),("Duke","Arizona",.5068)]}
OUT = []
for s in SEASONS:
    d = B3[s]; g = BI[s]["games"]; w = WON[s]; seeds = {}
    for x in g: seeds[x["H"]] = x["sH"]; seeds[x["L"]] = x["sL"]
    teams_of = lambda lo, hi: [t for x in g[lo:hi] for t in {x["H"], x["L"]}]
    def real(lo, hi, r): return next((t for t in teams_of(lo, hi) if w.get(t, 0) >= r), None)
    R = []
    r1 = [{"a": x["H"], "b": x["L"], "pick": d["brackets"]["vote"]["r1"][j]["pick"], "p": d["brackets"]["vote"]["r1"][j]["p"], "real": x["won"], "bye": x["H"] == x["L"]} for j, x in enumerate(g)]
    for e in r1: e["right"] = e["pick"] == e["real"]
    R.append(r1)
    r2 = []
    for q in range(16):
        a, b = r1[2*q]["pick"], r1[2*q+1]["pick"]; pk = d["brackets"]["vote"]["r2"][q]
        r2.append({"a": a, "b": b, "pick": pk["pick"], "p": pk["p"], "real": real(4*q, 4*q+4, 2), "right": w.get(pk["pick"], 0) >= 2})
    R.append(r2)
    prev = r2
    for r, n in ((3, 8), (4, 4)):
        cur = []
        for i in range(n):
            a, b = prev[2*i]["pick"], prev[2*i+1]["pick"]; pk = model_pick(s, a, b); pp = p(s, a, b)
            span = 32 // n
            cur.append({"a": a, "b": b, "pick": pk, "p": round(pp if pk == a else 1 - pp, 3), "real": real(i*span, (i+1)*span, r), "right": w.get(pk, 0) >= r})
        R.append(cur); prev = cur
    e8 = [x["pick"] for x in prev]; f4 = []
    for (ra, rb), (a, b, pa) in zip(FFPAIR[s], SIMP[s][:2]):
        assert {a, b} == {e8[ra], e8[rb]}, (s, a, b, e8)
        pk = a if pa >= .5 else b
        tm = teams_of(ra*8, ra*8+8) + teams_of(rb*8, rb*8+8)
        f4.append({"a": a, "b": b, "pick": pk, "p": round(pa if pk == a else 1 - pa, 3), "real": next((t for t in tm if w.get(t, 0) >= 5), None), "right": w.get(pk, 0) >= 5, "regions": [ra, rb]})
    R.append(f4)
    a, b, pa = SIMP[s][2]; pk = a if pa >= .5 else b
    R.append([{"a": a, "b": b, "pick": pk, "p": round(pa if pk == a else 1 - pa, 3), "real": next((t for t in w if w[t] >= 6), None), "right": w.get(pk, 0) >= 6}])
    sc = [sum(e["right"] for e in R[0] if not e["bye"])] + [sum(e["right"] for e in R[i]) for i in range(1, 6)]
    OUT.append({"season": s, "year": int(s[:4]) + 1, "seeds": seeds, "rounds": R, "score": sc, "points": sum(c * pt for c, pt in zip(sc, PTS))})
print(sum(o["points"] for o in OUT), [sum(o["score"][i] for o in OUT) for i in range(6)])
json.dump(OUT, open(os.path.join(HERE, "m305_full.json"), "w"), separators=(",", ":"))
