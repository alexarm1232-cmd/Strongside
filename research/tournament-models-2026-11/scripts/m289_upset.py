# upset R32 model chances for the vote pairs + real-game R32 upset chances
import os, json, contextlib, io
HERE = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read(); src = src[:src.index('print("\\nBRACKETS')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
VP = json.load(open(os.path.join(HERE, "m289_vote_pairs.json"))); out = {}
for s, prs in VP.items():
    out[s] = []
    for a, b in prs:
        h, l, pu = pr32("separate", s, a, b); out[s].append(l if pu >= .45 else h)
real = [{"s": r["s"], "h": r["h"][1], "l": r["l"][1], "up": int(r["up"]), "p": float(p)} for r, p in zip(REAL, MODELS["separate"][2])]
json.dump({"vote_r32_upset_pick": out, "real": real}, open(os.path.join(HERE, "m289_upset_r32.json"), "w")); print("ok")
