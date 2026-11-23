import json, re, os
os.chdir(r"C:\Users\crtra\Downloads\basketball")
for code in ("0910", "1011"):
    p = json.load(open(rf"logs\tourneystat\{code}_live.js", encoding="utf-8"))
    pl = [q for inp in p["inputs"] for side in inp[1:3] for q in side[1]]
    print(code, "tournament player rows", len(pl), "| steals sum", sum(q[18] for q in pl), "| blocks sum", sum(q[19] for q in pl))
pat = re.compile(r'\{"name": "([^"]+)", "conf": "[^"]*", "w": \d+, "l": \d+, "logo": "[^"]*", "n": ([-\d.]+)')
def nets(f): return {m.group(1): float(m.group(2)) for m in pat.finditer(open(f, encoding="utf-8").read())}
for code in ("0910", "1011"):
    a = nets(rf"data\_backup_stl_blk_20261118\dashboard\dashboard_{code}.html"); b = nets(rf"dashboard\dashboard_{code}.html")
    d = [abs(a[k] - b[k]) for k in a if k in b]; print(code, "net ratings: teams", len(d), "max change", max(d))
