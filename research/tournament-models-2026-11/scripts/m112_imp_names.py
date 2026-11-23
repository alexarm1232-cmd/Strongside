# Readable names for the 39 inputs and the random-forest importance ranking (mean decrease in Gini), both scopes.
import json
out = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m110_out.json"))
F = out["features"]
PT = {"pt_ppp": "pts/play on", "pt_share": "share of", "pt_d_ppp": "pts/play allowed on", "pt_d_share": "opp. share of"}
BASE = {"gap": "Rating gap", "sos gap": "Schedule-strength gap", "gap x possessions": "Rating gap × pace", "pm_close2h": "close 2nd-half margin",
        "pm_ahead10": "margin when up 10+", "comeback10": "comebacks from 10 down", "d_ast": "assists allowed", "d_tov": "turnovers forced",
        "d_ft": "opp. free throws", "d_p2": "opp. 2-pt %", "d_blk": "shots blocked by opp.", "orb": "offensive rebounding", "tempo": "tempo",
        "nst_to": "non-steal turnovers", "star_usage_rate": "star usage", "lost_minutes": "lost minutes", "star_three_share": "star's 3-pt share"}
def nice(f):
    if f in BASE: return BASE[f]
    if f[:2] in ("S ", "W "):
        side = "Stronger" if f[0] == "S" else "Weaker"; k = f[2:]
        for p, w in PT.items():
            if k.startswith(p + " "): return f"{side}: {w} {k[len(p) + 1:]}"
        return f"{side}: {BASE.get(k, k)}"
    return f
for sc in ("Round of 64", "Round of 64 to title"):
    imp = out[f"importance|{sc}"]; o = sorted(range(len(F)), key=lambda j: -imp[j])
    print(f"== {sc}"); [print(f"{r + 1:2d}. {nice(F[j]):48} {imp[j]:6.2f}") for r, j in enumerate(o)]
json.dump({f: nice(f) for f in F}, open(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\m112_names.json", "w"), indent=1)
