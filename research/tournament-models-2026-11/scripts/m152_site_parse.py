# Pull every team's ratings from the published pages: name, n, o, d, t, sos, sos_o, sos_d (pre and full).
import sys, re, json, os
src = sys.argv[1]; out = {}
rec = re.compile(r'\{"name": "((?:[^"\\]|\\.)*)", "conf": ')
num = lambda key, s: (lambda m: None if m is None or m.group(1) == "null" else float(m.group(1)))(re.search(r'"' + key + r'": ([-\d.]+|null)', s))
for f in sorted(os.listdir(src)):
    code = f.replace("dashboard_", "").replace(".html", ""); full = code.endswith("_full"); code = code.replace("_full", "")
    season = "20" + code[:2] + "-" + code[2:]
    h = open(os.path.join(src, f), encoding="utf-8").read(); teams = {}
    for m in rec.finditer(h):
        seg = h[m.end(): m.end() + 900]
        if '"n": ' not in seg[:300]: continue
        cut = seg.find('"box"'); seg = seg[:cut if cut > 0 else 900]
        rec_ = {k: num(k, seg) for k in ("w", "l", "n", "o", "d", "t", "sos", "sos_o", "sos_d")}; cm = re.match(r'"((?:[^"\\]|\\.)*)"', seg); rec_["conf"] = cm.group(1) if cm else None; teams[json.loads('"' + m.group(1) + '"')] = rec_
    out.setdefault(season, {})["full" if full else "pre"] = teams
json.dump(out, open(sys.argv[2], "w"))
for s in sorted(out): print(s, {k: len(v) for k, v in out[s].items()}, "Michigan:", {k: (v.get("Michigan") or {}).get("n") for k, v in out[s].items()})

