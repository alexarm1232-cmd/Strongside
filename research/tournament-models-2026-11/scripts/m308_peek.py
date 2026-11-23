import json
A=json.load(open("m307_full.json")); PTS=[1,2,4,8,16,32]
for key in A:
    print(key)
    for o in A[key]:
        sc=o["score"]; early=sc[0]+2*sc[1]; late=sum(c*p for c,p in zip(sc[2:],PTS[2:]))
        # ceiling for later rounds given the S16 teams: each S16 team that is real gets credit up to its real wins, bracket-consistent -> compute by tree
        print(o["year"], "early",early,"late",late,"total",o["points"], sc)
