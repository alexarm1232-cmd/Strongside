import os, json, contextlib, io
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
src = open(os.path.join(HERE, "m292_blend_bracket.py"), encoding="utf-8-sig").read(); src = src[:src.index("R32OPT = {")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
D2 = json.load(open(os.path.join(HERE, "m290_brackets_two.json")))
t1 = 0; t2 = 0
for d in D2:
    s = d["season"]; r1 = []
    for g in BI[s]["games"]:
        if g["H"] == g["L"]: r1.append({"pick": g["H"], "p": None}); continue
        u, m, si = R1P[str(g["gid"])]; p = (u + m + si) / 3; pk = g["L"] if p >= .45 else g["H"]
        r1.append({"pick": pk, "p": round(p if pk == g["L"] else 1 - p, 3)})
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; h, l, pu = UPP[f"{s}|{a}|{b}"]; S_, W_, z = MZ[(s, a, b)]
        pS = float(sig(z)); pm = pS if kk(l) == S_ else 1 - pS; p = .5 * pu + .5 * pm; pk = l if p >= .42 else h
        r2.append({"pick": pk, "p": round(p if pk == l else 1 - p, 3)})
    assert [g["a"] for g in d["games"]] == [g["H"] for g in BI[s]["games"]]
    d["brackets"]["blend"] = {"r1": r1, "r2": r2}
    t1 += sum(r1[j]["pick"] == g["won"] for j, g in enumerate(d["games"]) if not g["bye"]); t2 += sum(r2[q]["pick"] == d["r2won"][q] for q in range(16))
print(t1, t2, t1 + 2 * t2)
json.dump(D2, open(os.path.join(HERE, "m293_brackets_three.json"), "w"), separators=(",", ":"))
