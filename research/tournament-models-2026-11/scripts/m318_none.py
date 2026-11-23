import json
B={d["season"]:d for d in json.load(open("m285_brackets.json"))}
t=open("m242_bracket_in.js",encoding="utf-8").read(); BI=json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}")+1])
V={d["season"]:d for d in json.load(open("m293_brackets_three.json"))}
r1z=r1v=r1n=0; r2z=r2v=r2n=0; one1=two1=0; one2=two2=0
for s,d in B.items():
    g=BI[s]["games"]; w=dict(BI[s]["wins"])
    for x in g:
        if x["H"]==x["L"]: w[x["H"]]=w.get(x["H"],0)+1
    P=[d["brackets"][k] for k in ("upset","model","sim")]
    for j,x in enumerate(g):
        if x["H"]==x["L"]: continue
        r1n+=1; c=sum(p["r1"][j]["pick"]==x["won"] for p in P)
        r1z+=c==0; one1+=c==1; two1+=c==2
        r1v+=V[s]["brackets"]["vote"]["r1"][j]["pick"]==x["won"]
    for q in range(16):
        r2n+=1; c=sum(w.get(p["r2"][q]["pick"],0)>=2 for p in P)
        r2z+=c==0; one2+=c==1; two2+=c==2
        r2v+=w.get(V[s]["brackets"]["vote"]["r2"][q]["pick"],0)>=2
print("R1",r1n,"none",r1z,"one",one1,"two",two1,"all3",r1n-r1z-one1-two1,"vote",r1v)
print("R32",r2n,"none",r2z,"one",one2,"two",two2,"all3",r2n-r2z-one2-two2,"vote",r2v)
