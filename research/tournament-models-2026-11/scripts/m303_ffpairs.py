src = open("m302_full_brackets.py", encoding="utf-8").read(); src = src[:src.index('print(f"{\'Full bracket')]
import contextlib, io, json
with contextlib.redirect_stdout(io.StringIO()): exec(src)
out = {}
for lab in ("Vote of the 3 -> regular", "Regular model all the way", "Blend -> regular"):
    key, src_ = BRK[lab]; out[lab] = {}
    for s in SEASONS:
        _, r2 = r12(s, key, src_)
        s16 = [model_pick(s, r2[2*i], r2[2*i+1]) for i in range(8)]; e8 = [model_pick(s, s16[2*i], s16[2*i+1]) for i in range(4)]
        out[lab][s] = {"e8": e8, "ff": [[e8[a], e8[b]] for a, b in FFPAIR[s]]}
json.dump(out, open(os.path.join(HERE, "m303_ff_pairs.json"), "w"))
for s in SEASONS: print(s, json.dumps(sorted({tuple(p) for lab in out for p in out[lab][s]["ff"]})))
