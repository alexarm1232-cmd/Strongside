src = open("m289_vote.py", encoding="utf-8").read(); src = src[:src.index("# ---- real games")]
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()): exec(src)
for d in D:
    s = d["season"]; r1 = []
    for j, g in enumerate(d["games"]):
        v = [d["brackets"][x]["r1"][j]["pick"] for x in ("upset", "model", "sim")]; p = vote(v)
        r1.append({"pick": p, "p": None if g["bye"] else f"{v.count(p)} of 3"})
    r2 = []
    for q in range(16):
        a, b = r1[2 * q]["pick"], r1[2 * q + 1]["pick"]; v = [UPX["vote_r32_upset_pick"][s][q], model_pick(s, a, b), sim_pick(s, a, b)]; p = vote(v)
        r2.append({"pick": p, "p": f"{v.count(p)} of 3"})
    d["brackets"]["vote"] = {"r1": r1, "r2": r2}
    for x in ("model", "sim", "seed"): d["brackets"].pop(x)
json.dump(D, open(os.path.join(HERE, "m290_brackets_two.json"), "w"), separators=(",", ":"))
print(sum(sum(d["brackets"]["vote"]["r1"][j]["pick"] == g["won"] for j, g in enumerate(d["games"]) if not g["bye"]) for d in D),
      sum(sum(d["brackets"]["vote"]["r2"][q]["pick"] == d["r2won"][q] for q in range(16)) for d in D))
