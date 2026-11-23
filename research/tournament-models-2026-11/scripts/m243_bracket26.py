import json, os, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(H, "m242_bracket_in.js"), encoding="utf-8").read(); BI = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])["2025-26"]
G, W, SD = BI["games"], BI["wins"], BI["seeds"]
R = [[g["pick"]["avg"] for g in G],
     ["Michigan", "Alabama", "Iowa St", "Virginia", "Arizona", "Arkansas", "Purdue", "Gonzaga", "Houston", "Illinois", "Vanderbilt", "Florida", "Duke", "St. John's (NY)", "Michigan St", "UConn"],
     ["Michigan", "Iowa St", "Arizona", "Purdue", "Houston", "Florida", "Duke", "Michigan St"],
     ["Michigan", "Arizona", "Houston", "Duke"], ["Arizona", "Duke"], ["Duke"]]
PR = {2: [86.8, 53.6, 73.6, 52.2, 85.5, 57.8, 73.2, 64.2, 80.7, 81.6, 56.2, 74.6, 89.4, 52.8, 59.1, 68.6], 3: [79.7, 61.3, 73.7, 59.6, 53.3, 61.3, 80.4, 52.4],
      4: [63.6, 66.8, 50.0, 74.1], 5: [50.2, 64.7], 6: [54.5]}   # simulator win % of the picked team
OK, BAD, INK, MUTED = "#1f6fd1", "#d4581f", "#15233B", "#6b7280"
fig, ax = plt.subplots(figsize=(22, 14), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb"); ax.axis("off")
ax.set_xlim(0, 13); ax.set_ylim(-1, 33)
def lab(t): return f"{SD.get(t, '')} {t}"
def ypos(rd, i):  # center y of slot i in round rd (0 = Round of 64 teams), per half of 32 lines
    span = 2 ** rd; return 32 - (i * span + span / 2)
# Round of 64: 64 team lines per side split: left = games 0-15 (teams 0-31), right = games 16-31
for half in (0, 1):
    xs = [0.0, 1.55, 2.95, 4.2, 5.25] if half == 0 else [11.4, 9.85, 8.45, 7.2, 6.15]
    al = "left" if half == 0 else "right"
    for gi_ in range(16):
        g = G[half * 16 + gi_]
        for k, tm in enumerate((g["H"], g["L"])):
            y = ypos(0, gi_ * 2 + k) / 1.0
            picked = tm == R[0][half * 16 + gi_]
            col = INK if not picked else (OK if W.get(tm, 0) >= 1 else BAD)
            ax.text(xs[0], y, lab(tm) + ("  ✓" if picked and W.get(tm, 0) >= 1 else ("  ✗" if picked else "")), fontsize=10, ha=al, va="center", color=col if picked else MUTED, fontweight="bold" if picked else "normal")
    for rd in range(1, 4):
        n = 16 // 2 ** rd; off = half * n
        for i in range(n):
            tm = R[rd][off + i]; ok = W.get(tm, 0) >= rd + 1; y = ypos(rd + 1, i)
            p = PR[rd + 1][off + i]
            ax.text(xs[rd], y, f"{lab(tm)} ({p:.0f}%) " + ("✓" if ok else "✗") if half == 0 else ("✓ " if ok else "✗ ") + f"{lab(tm)} ({p:.0f}%)", fontsize=11, ha=al, va="center", color=OK if ok else BAD, fontweight="bold")
# Final Four and champion in the center
ch = R[5][0]
for k, (x, tm) in enumerate(((5.55, R[4][0]), (7.45, R[4][1]))):
    ok = W.get(tm, 0) >= 5
    ax.text(x, 17.6, f"{lab(tm)} ({PR[5][k]:.0f}%) " + ("✓" if ok else "✗"), fontsize=13, ha="center", color=OK if ok else BAD, fontweight="bold")
ax.text(6.5, 18.9, "Title game", fontsize=12, color=MUTED, ha="center")
ax.text(6.5, 13.2, f"Champion pick\n{lab(ch)} ({PR[6][0]:.0f}%)  " + ("✓" if W.get(ch, 0) >= 6 else "✗"), fontsize=17, ha="center", color=OK if W.get(ch, 0) >= 6 else BAD, fontweight="bold")
ax.text(6.5, 10.6, "Real result: Michigan won the title over UConn;\nIllinois and Arizona were the other Final Four teams", fontsize=11.5, ha="center", color=INK)
for x, t_ in ((0.0, "Round of 64"), (1.55, "Sweet 16"), (2.95, "Elite 8"), (4.2, "Final Four")):
    ax.text(x, 32.9, t_, fontsize=12, color=MUTED, ha="left")
for x, t_ in ((11.4, "Round of 64"), (9.85, "Sweet 16"), (8.45, "Elite 8"), (7.2, "Final Four")):
    ax.text(x, 32.9, t_, fontsize=12, color=MUTED, ha="right")
right = [sum(1 for t in R[r] if W.get(t, 0) >= r + 1) for r in range(6)]; pts = sum(n * p for n, p in zip(right, (1, 2, 4, 8, 16, 32)))
ax.text(6.5, 33.9, "2026 bracket: average of 3 for Round 1, simulator from Round 2 on", fontsize=19, ha="center", color=INK, fontweight="bold")
ax.text(6.5, -0.6, f"Right by round: {right[0]}/32 · {right[1]}/16 · {right[2]}/8 · {right[3]}/4 · {right[4]}/2 · {right[5]}/1  =  {pts} of 192 points    "
        "(blue ✓ = team really won that game, orange ✗ = it lost; % = simulator win chance for the picked team)", fontsize=11.5, ha="center", color=INK)
out = r"C:\Users\crtra\Downloads\basketball\logs\bracket_2026_average3_sim.png"; fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="#fcfcfb"); print(out, right, pts)