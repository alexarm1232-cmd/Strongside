# The 12 Round 1 misses (2025 + 2026): higher seed minus lower seed on Andrew's top variables, pre-tournament (the CSV)
# vs end of season (totals through the title game), plus each team's tournament wins.
import csv, json, re
D = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
O = r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
CSV = {(r["Season"], r["Team"]): r for r in csv.DictReader(open(r"C:\Users\crtra\Downloads\Round of 64 - pre-tournament data 2010-2026.csv", encoding="utf-8"))}
FULL = json.load(open(D + r"\m150_full.json")); SITE = json.load(open(D + r"\m152_site_ratings.json"))
G = json.load(open(O + r"\study_games_all.json"))
norm = lambda n: re.sub(r"[^a-z0-9]", "", n.lower().replace("saint", "st").replace("state", "st"))
def get(d, t): return d.get(t) or d.get(t + ".") or next((v for k, v in d.items() if norm(k) == norm(t)), None)
wins = {}
for g in G:
    if g["rnd"] == "First Four": continue
    w = g["fav"] if g["fav_won"] else g["dog"]; wins[(g["season"], w)] = wins.get((g["season"], w), 0) + 1
games = [("2025-26", "Ohio St", "TCU"), ("2025-26", "North Carolina", "VCU"), ("2025-26", "Wisconsin", "High Point"), ("2025-26", "Georgia", "Saint Louis"),
         ("2025-26", "Clemson", "Iowa"), ("2025-26", "Villanova", "Utah St"), ("2024-25", "Missouri", "Drake"), ("2024-25", "Kansas", "Arkansas"),
         ("2024-25", "Clemson", "McNeese"), ("2024-25", "Marquette", "New Mexico"), ("2024-25", "Memphis", "Colorado St"), ("2024-25", "Mississippi St", "Baylor")]
print("season|higher seed|lower seed (won)|tourney wins H/L|NetRtg diff pre/full|FGA diff pre/full|FG diff pre/full|TRB diff pre/full")
for s, H, L in games:
    cH, cL = get({k[1]: v for k, v in CSV.items() if k[0] == s}, H), get({k[1]: v for k, v in CSV.items() if k[0] == s}, L)
    fH, fL = get(FULL[s], H), get(FULL[s], L); sH, sL = get(SITE[s]["full"], H), get(SITE[s]["full"], L)
    pre = lambda k: int(cH[k]) - int(cL[k])
    full = lambda k: int(round(fH[k] - fL[k]))
    print(f"{s}|{H} ({cH['Seed']})|{L} ({cL['Seed']})|{wins.get((s, H), 0)}/{wins.get((s, L), 0)}|"
          f"{float(cH['NetRtg']) - float(cL['NetRtg']):+.1f} / {sH['n'] - sL['n']:+.1f}|{pre('FGA'):+d} / {full('fga'):+d}|{pre('FGM'):+d} / {full('fgm'):+d}|{pre('TRB'):+d} / {full('reb'):+d}")
