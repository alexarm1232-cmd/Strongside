# helper: Round of 32 Upset Model upset chance for any list of pairs (reads m328_pairs.json, writes m328_upset_p.json)
import os, json, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "m274_feed_locked.py"), encoding="utf-8-sig").read(); src = src[:src.index('print("\\nBRACKETS')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
PR = json.load(open(os.path.join(HERE, "m328_pairs.json"))); out = {}
for s, prs in PR.items():
    for a, b in prs:
        h, l, pu = pr32("separate", s, a, b); out[f"{s}|{a}|{b}"] = [h, l, float(pu)]
json.dump(out, open(os.path.join(HERE, "m328_upset_p.json"), "w")); print("upset pairs", len(out))
