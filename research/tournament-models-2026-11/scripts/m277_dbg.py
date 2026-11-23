import json, glob, os
ROOT = r"C:\Users\crtra\Downloads\basketball"
p = json.load(open(os.path.join(ROOT, "logs", "tourneystat", "2425_live.js"), encoding="utf-8"))
kk = lambda s: (s or "").rstrip(". ")
rows = p["rows"]; 
r2 = [k for k, r in enumerate(rows) if r[10] == "Second round"][0]; t = rows[r2][1]
r1 = [k for k, r in enumerate(rows) if r[10] == "First round" and t in (rows[k][1], rows[k][2])][0]
print(rows[r1][:3], rows[r2][:3])
def team(k, t):
    lg, a, b = p["inputs"][k]; return a if kk(rows[k][1]) == kk(t) else b
A, Bt = team(r1, t), team(r2, t)
print(type(A), len(A), [type(x) for x in A][:4])
print(A[0] if not isinstance(A[0], list) else A[0][:5])
pa, pb = A[1], Bt[1]
for x, y in list(zip(pa, pb))[:6]: print(x[:3], x[-1], "|", y[:3], y[-1])
