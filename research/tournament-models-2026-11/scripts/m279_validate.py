import json, glob, os, contextlib, io, sys
sys.path.insert(0, ".")
with contextlib.redirect_stdout(io.StringIO()):
    import m99_model_types as Q
G = Q.R.B.G; DS = r"C:\Users\crtra\Downloads\basketball\data\seasons"; kk = lambda s: (s or "").rstrip(". ")
FL = json.load(open(os.path.join(r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad", "m277_flagged" + os.environ.get("TAG", "") + ".json")))
R2 = {}
for g in G:
    if g["rnd"] == "Second round":
        for t in (g["fav"], g["dog"]): R2[(g["season"], kk(t))] = g
sat = played = lost = nobox = 0
for s, t, nm, mins, mpg, left in FL:
    g = R2.get((s, kk(t)))
    if not g: lost += 1; continue
    y = int(s[:4]) + 1; code = f"{str(y-1)[2:]}{str(y)[2:]}"
    f = [p for p in glob.glob(os.path.join(DS, code + " full", "*", "*", "boxscores", str(g["gid"]) + ".json")) if kk(os.path.basename(os.path.dirname(os.path.dirname(p)))) == kk(t)]
    if not f: nobox += 1; continue
    J = json.load(open(f[0], encoding="utf-8")); T = [x for x in J["teams"] if kk(x.get("team_name")) == kk(t)]
    rows = (T[0].get("starters_table") or []) + (T[0].get("bench_table") or []) if T else []
    r = next((r for r in rows if r.get("Name") == nm), None)
    m = float(r.get("MIN") or 0) if r and str(r.get("MIN") or "0").replace(".","",1).isdigit() else 0.0
    if m > 0: played += 1
    else: sat += 1
print(f"flagged {len(FL)}: team lost in R1 {lost} | no R32 box {nobox} | sat out the R32 {sat} | played in the R32 {played}")


