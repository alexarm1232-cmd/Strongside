import json
from collections import Counter
B={d["season"]:d for d in json.load(open("m285_brackets.json"))}
t=open("m242_bracket_in.js",encoding="utf-8").read(); BI=json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}")+1])
K=("upset","model","sim")
# R1: upset model upset picks the other two overruled
hit=miss=0; tot={k:0 for k in K}
for s,d in B.items():
    for j,x in enumerate(BI[s]["games"]):
        if x["H"]==x["L"]: continue
        pk={k:d["brackets"][k]["r1"][j]["pick"] for k in K}
        for k in K: tot[k]+=pk[k]==x["won"]
        if pk["upset"]==x["L"] and pk["model"]==x["H"] and pk["sim"]==x["H"]:
            hit+= x["won"]==x["L"]; miss+= x["won"]==x["H"]
print("R1 right alone:",tot)
print(f"R1 upset-model upset picks outvoted by both others: {hit+miss} -> upset happened {hit}, higher seed won {miss}")
# R32: lone-right cases, were the others' R32 picks already dead after R1?
dead=alive=0; why=Counter()
for s,d in B.items():
    g=BI[s]["games"]; w=dict(BI[s]["wins"])
    for x in g:
        if x["H"]==x["L"]: w[x["H"]]=w.get(x["H"],0)+1
    for q in range(16):
        pk={k:d["brackets"][k]["r2"][q]["pick"] for k in K}; ok={k:w.get(pk[k],0)>=2 for k in K}
        if sum(ok.values())!=1: continue
        k=next(k for k in K if ok[k])
        for o in K:
            if o==k: continue
            if pk[o]==pk[k]: why["same team, impossible"]+=1
            elif w.get(pk[o],0)>=1: why["other pick won R1, lost R32"]+=1
            else: why["other pick already lost in R1"]+=1
print("R32 lone-right: what happened to the two wrong picks:",dict(why))
