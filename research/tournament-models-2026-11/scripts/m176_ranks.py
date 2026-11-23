import json, sys
R = json.load(open(sys.argv[1]))
V = "NetRtg FGA FG TRB SRS DRtg SOS NetRtg_SOS AdjTempo DRtg_SOS WL_Pct ORtg_SOS Luck AST PF ORB STL FT ORtg ThreeP_Pct TRB_Pct FTA FG_Pct TOV FTr BLK_Pct eFG_Pct ThreeP FT_Pct AST_Pct FT_per_FGA BLK TS_Pct TOV_Pct ThreePA ThreePAr Seed".split()
import importlib.util
for w in ("full", "pre"):
    n, miss, imp, oob, single = R[w]
    order = sorted(range(len(imp)), key=lambda j: -imp[j])
    names = __import__("m148_andrew_tree").VARS
    print(w, "top6:", [names[j] for j in order[:6]], "| FG", order.index(names.index("FG")) + 1, "FGA", order.index(names.index("FGA")) + 1, "TRB", order.index(names.index("TRB")) + 1)
