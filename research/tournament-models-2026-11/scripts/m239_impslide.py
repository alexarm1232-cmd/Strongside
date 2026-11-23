import json, os, html
H = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(H, "m238_imp.json")))
N = {"L pt_d_ppp Rim Attack": "Underdog rim-attack defense", "L-H pt_d_ppp Dribble Jumper": "Dribble-jumper defense gap", "H pt_ppp Big Cut & Roll": "Favorite Big Cut & Roll offense",
     "H pt_d_share Dribble Jumper": "Favorite dribble jumpers allowed", "H d_blk": "Favorite gets shots blocked", "L pt_d_share Dribble Jumper": "Underdog dribble jumpers allowed",
     "L-H pt_d_ppp Transition": "Transition defense gap", "H pm_close2h": "Favorite close 2nd-half margin", "L pt_d_ppp Pick & Pop": "Underdog Pick & Pop defense",
     "L pt_d_share Post-Up": "Underdog post-ups allowed", "H star_usage_rate": "Favorite star usage", "H 3pt/vol: mar_sd": "Favorite margin swings", "H basic: ppg": "Favorite points per game",
     "L-H returning": "Returning-minutes gap", "H big_height": "Favorite big-man height", "L-H ftr": "Free-throw rate gap", "L-H tourney wins last 3": "Tournament experience gap",
     "L-H pt_ppp Big Cut & Roll": "Big Cut & Roll scoring gap", "L-H depth_bpm": "Bench BPM gap", "L d_tov": "Underdog turnovers forced", "L-H pt_d_ppp Rim Attack": "Rim-attack defense gap",
     "L-H pt_d_ppp Drive & Kick": "Drive & Kick defense gap", "L-H pt_d_ppp Inside Out": "Inside Out defense gap", "L pt_d_ppp Dribble Jumper": "Underdog dribble-jumper defense",
     "L pt_d_ppp Inside Out": "Underdog Inside Out defense", "L pt_d_ppp Perimeter Cut": "Underdog perimeter-cut defense", "L-H pt_d_ppp Pick & Pop": "Pick & Pop defense gap",
     "H pt_d_ppp Transition": "Favorite transition defense", "H orb": "Favorite offensive rebounding", "L-H cast_bpm_bpm": "Supporting-cast BPM gap", "L pt_d_share Perimeter Cut": "Underdog perimeter cuts allowed"}
imp = D["imp"]; mx = max(v for v, _, _ in imp); RH = 36; BAR = 290
els = []
for i, (v, c, w) in enumerate(imp):
    col, row = (0, i) if i < 16 else (1, i - 16); x0 = col * 850; yy = 30 + row * RH
    L = max(v, 0) / mx * BAR; color = "#B04A17" if w > 0 else "#15233B"
    els.append(f'<text x="{x0 + 440}" y="{yy + 8}" text-anchor="end" font-size="24" fill="#15233B" font-family="Public Sans, Arial, sans-serif">{html.escape(N[c])}</text>')
    els.append(f'<rect x="{x0 + 456}" y="{yy - 13}" width="{max(L, 2):.1f}" height="24" rx="4" fill="{color}"/>')
    els.append(f'<text x="{x0 + 466 + max(L, 2):.1f}" y="{yy + 8}" font-size="24" fill="#4A5568" font-family="Public Sans, Arial, sans-serif">{v:.3f}</text>')
svg = f'<svg aria-label="Variable importance of the Upset Model: drop in AUC when each input is shuffled; supporting-cast BPM gap is largest at 0.036, then tournament experience gap 0.015" width="1664" height="610" viewBox="0 0 1664 610">' + "".join(els) + "</svg>"
sec = f'''<section id="upsetimp" class="alt">
<div class="head">
<p class="eyebrow">Upset Model · variable importance</p>
<h2>Supporting-cast BPM and tournament experience matter most</h2>
</div>
{svg}
<div class="row" style="gap:40px;align-items:center;margin-top:-20px">
<div class="key"><div class="dot" style="background:#B04A17"></div>Higher value means more upsets</div>
<div class="key"><div class="dot" style="background:#15233B"></div>Higher value means fewer upsets</div>
</div>
<p class="source">Importance = drop in AUC when that one input is shuffled (average of 200 shuffles); model fit on all 511 Round 1 games, AUC 0.836.</p>
<aside>Read it like Andrew's variable importance chart: the longer the bar, the more the model leans on that input. The supporting-cast BPM gap (players with 10+ minutes, the top two removed) is three times anything else, and it tracks team strength closely (0.95 with the net-rating gap). After it come tournament experience, the favorite's margin in close second halves, the favorite's star usage and the favorite's scoring. The 15 play-type defense inputs each add a little; none is large alone.</aside>
</section>
'''
out = os.path.join(H, "artifact-files", "9b2ee873-e5f0-4ac4-97fb-388bf1e96da6", "project", "slides", "upsetimp.html")
open(out, "w", encoding="utf-8").write(sec); print(out, len(sec))