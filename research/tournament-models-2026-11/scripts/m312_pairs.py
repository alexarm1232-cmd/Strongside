import json, os, itertools
HERE=os.getcwd(); A=json.load(open("m307_full.json"))
P={}
for key in A:
    for o in A[key]:
        s=o["season"]; r2=[e["pick"] for e in o["rounds"][1]]
        for r in range(4):
            P.setdefault(s,{}).setdefault(r,set()).update(r2[r*4:r*4+4])
out={s:sorted({tuple(sorted(pr)) for r in d for pr in itertools.combinations(sorted(d[r]),2)}) for s,d in P.items()}
json.dump(out,open("m312_pairs.json","w")); print({s:len(v) for s,v in out.items()}, sum(map(len,out.values())))
