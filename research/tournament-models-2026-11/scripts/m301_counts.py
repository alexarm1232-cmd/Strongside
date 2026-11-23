import contextlib, io, sys
sys.path.insert(0, ".")
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
G = Q.R.B.G
for rd in ("First round", "Second round", "Sweet 16", "Elite Eight"):
    gs = [g for g in G if g["rnd"] == rd]; uneq = [g for g in gs if g["fseed"] != g["dseed"]]
    up = sum(1 for g in uneq if (g["fseed"] < g["dseed"]) != bool(g["fav_won"]))
    print(rd, len(gs), "unequal seeds", len(uneq), "lower seed won", up)
