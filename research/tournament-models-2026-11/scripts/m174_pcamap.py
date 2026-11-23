import re, subprocess, sys
D = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
f = D + r"\artifact-files\a70f401f-70e4-4b38-bf99-cfbd57c96e9f\project\slides\pcamap.html"
out = open(D + r"\deck_rerun\m106_svgpaths_wl.py.txt", encoding="utf-8", errors="replace").read().splitlines()
P = {}; cur = None
for line in out:
    m = re.match(r"## (.+) \| (won|lost) \| (\d+)", line)
    if m: cur = (m.group(1), m.group(2)); continue
    if cur and line.startswith("M"): P[cur] = line.strip(); cur = None
order = [("Both wrong", "lost"), ("Both wrong", "lost"), ("Both wrong", "won"), ("Both right", "lost"), ("Both right", "lost"), ("Both right", "won"),
         ("Sim right, model wrong", "lost"), ("Sim right, model wrong", "lost"), ("Sim right, model wrong", "won"),
         ("Model right, sim wrong", "lost"), ("Model right, sim wrong", "lost"), ("Model right, sim wrong", "won")]
h = open(f, encoding="utf-8").read(); it = iter(order)
h = re.sub(r'd="M[^"]{60,}"', lambda m: 'd="' + P[next(it)] + '"', h)
for a, b in (("Both right (669 games)", "Both right (674 games)"), ("Both wrong (198)", "Both wrong (200)"), ("Model right, sim wrong (87)", "Model right, sim wrong (85)"), ("Sim right, model wrong (53)", "Sim right, model wrong (48)")):
    assert a in h; h = h.replace(a, b)
open(f, "w", encoding="utf-8").write(h); print("pcamap updated", {k: v.count("M") for k, v in P.items()})
