import json
G = json.load(open(r"C:\Users\crtra\AppData\Local\Temp\claude\C--Users-crtra-Downloads-basketball\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad\study_games_all.json"))
pairs = [("2025-26", "Ohio St", "TCU"), ("2025-26", "North Carolina", "VCU"), ("2025-26", "Wisconsin", "High Point"), ("2025-26", "Georgia", "Saint Louis"),
         ("2025-26", "Clemson", "Iowa"), ("2025-26", "Villanova", "Utah St"), ("2024-25", "Missouri", "Drake"), ("2024-25", "Kansas", "Arkansas"),
         ("2024-25", "Clemson", "McNeese"), ("2024-25", "Marquette", "New Mexico"), ("2024-25", "Memphis", "Colorado St"), ("2024-25", "Mississippi St", "Baylor")]
for s, H, L in pairs:
    g = next(g for g in G if g["season"] == s and g["rnd"] == "First round" and {g["fav"].rstrip("."), g["dog"].rstrip(".")} == {H, L})
    pH = g["sim_p"] if g["fav"].rstrip(".") == H else 1 - g["sim_p"]
    print(f"{s}|{H}|{L}|sim favorite {g['fav']}|line {g['sim_line']}|sim win% higher seed {pH:.1%}|lower seed {1 - pH:.1%}|pickem {bool(g.get('pickem'))}")
