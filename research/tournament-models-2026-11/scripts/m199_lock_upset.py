import json, os
H = os.path.dirname(os.path.abspath(__file__))
ins = json.load(open(os.path.join(H, "m188_out.json")))["inputs"]
spec = {"name": "Strongside Upset Model (Round 1)", "round": "Round of 64 only", "outcome": "lower seed wins",
        "inputs": ins, "seed_gap": False, "net_rating": False, "model": "ridge logistic, penalty 30, half-life-12 season weights, inputs standardized",
        "pick_upset_when": 0.40, "results_each_year_held_out": {"games_right": 391, "of": 511, "auc": 0.790, "upset_picks": 133, "upset_hits": 78},
        "features_file": "m186_r64_features.json", "built": "2026-11-18"}
json.dump(spec, open(os.path.join(H, "upset_model_r64.json"), "w"), indent=1)
print(len(ins), "inputs saved")
for c in ins: print("  ", c)
