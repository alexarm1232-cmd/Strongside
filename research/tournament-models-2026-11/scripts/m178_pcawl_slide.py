import re
D = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
out = open(D + r"\deck_rerun\m106_svgpaths_wl.py.txt", encoding="utf-8", errors="replace").read().splitlines()
P = {}; cur = None
for line in out:
    m = re.match(r"## (.+) \| (won|lost) \| (\d+)", line)
    if m: cur = (m.group(1), m.group(2)); continue
    if cur and line.startswith("M"): P[cur] = line.strip(); cur = None
COL = [("Both right", "#C9C2B3", 12, "0.8"), ("Both wrong", "#8E6CC9", 12, "0.9"), ("Sim right, model wrong", "#2F6DB5", 16, "1"), ("Model right, sim wrong", "#D9622B", 16, "1")]
def svg(which, label):
    paths = "".join(f'<path d="{P[(q, which)]}" stroke="{c}" stroke-width="{w}" opacity="{o}"/>' for q, c, w, o in COL)
    return (f'<svg aria-label="{label}" width="780" height="480" viewBox="60 20 1040 640" style="display:block">'
            f'<rect x="60" y="20" width="1040" height="640" fill="#F5F2EA"/>'
            f'<path d="M722 20V660M60 340H1100" stroke="#C9C2B3" stroke-width="2"/>'
            f'<g stroke-linecap="round" fill="none">{paths}</g>'
            f'<path d="M60 660H1100M60 20V660" stroke="#4A5568" stroke-width="3"/></svg>')
html = f'''<section id="pcawl" class="alt" style="gap:32px">
<div class="head">
<p class="eyebrow">PCA map · winners only and losers only</p>
<h2>Winners sit on the stronger side, except in the games nobody called</h2>
</div>
<div class="row" style="gap:48px;align-items:start">
<div class="col" style="gap:8px;flex:0 0 780px">
<p style="font-size:28px"><b>Winners</b> <span class="muted">· 1,007 teams · average PC1 +0.63</span></p>
{svg("won", "PCA map of the 1,007 winning teams only, colored by box; most sit right of center, but the purple both-wrong and orange model-right winners sit to the left")}
</div>
<div class="col" style="gap:8px;flex:0 0 780px">
<p style="font-size:28px"><b>Losers</b> <span class="muted">· 1,007 teams · average PC1 −0.63</span></p>
{svg("lost", "PCA map of the 1,007 losing teams only, colored by box; most sit left of center, but the purple both-wrong losers sit to the right")}
</div>
</div>
<div class="row" style="gap:36px">
<div class="key"><div class="dot" style="background:#C9C2B3"></div><p>Both right</p></div>
<div class="key"><div class="dot" style="background:#8E6CC9"></div><p>Both wrong</p></div>
<div class="key"><div class="dot" style="background:#D9622B"></div><p>Model right, sim wrong</p></div>
<div class="key"><div class="dot" style="background:#2F6DB5"></div><p>Sim right, model wrong</p></div>
</div>
<p class="source">Same axes as the full map: PC1 across (stronger rating, tougher schedule, better when ahead), PC2 up. Average PC1, winners vs losers: both right +1.16 vs −1.16 · model right, sim wrong −0.36 vs +0.09 · sim right, model wrong +0.48 vs −0.19 · both wrong −0.73 vs +0.75.</p>
<aside>Split by result, the map shows what the boxes mean. In the games both methods called, the winner was the stronger-looking team (winners far right, losers far left). In the games both missed, it flips: the winners sit left and the losers right, so those were upsets by strength. In the games only the model got right, the winners also sit left of the losers: the model called upsets the simulator did not.</aside>
</section>
'''
open(D + r"\artifact-files\9b2ee873-e5f0-4ac4-97fb-388bf1e96da6\project\slides\pcawl.html", "w", encoding="utf-8").write(html)
print(len(html), "bytes")
