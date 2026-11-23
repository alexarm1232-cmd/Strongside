import json, sys, os
M=json.load(open("m328_need.json")); f="m328_sim.json"
d=json.load(open(f)) if os.path.exists(f) else {}
RAW=json.loads(sys.argv[1])
for s,v in RAW.items():
    assert len(v)==len(M[s]),(s,len(v),len(M[s])); d[s]={f"{a}|{b}":x for (a,b),x in zip(M[s],v)}
json.dump(d,open(f,"w")); print(sorted(d))
done=set(d); nxt=[s for s in M if s not in done][:4]
for s in nxt: print(s, json.dumps(M[s],separators=(",",":")))
