import json, contextlib, io
src=open("m302_full_brackets.py",encoding="utf-8").read(); src=src[:src.index('print(f"{\'Full bracket')]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
A=json.load(open(os.path.join(HERE,"m307_full.json")))
names={2:"S16",3:"E8",4:"F4",5:"Title"}
for key in A:
    print(key)
    for ri in range(2,6):
        live=liveR=one=oneR=dead=right=n=0
        for o in A[key]:
            w=WON[o["season"]]
            for e in o["rounds"][ri]:
                n+=1; ia=w.get(e["a"],0)>=ri; ib=w.get(e["b"],0)>=ri   # reached this round
                r=w.get(e["pick"],0)>=ri+1; right+=r
                if ia and ib: live+=1; liveR+=r
                elif ia or ib: one+=1; oneR+=r
                else: dead+=1
        print(f"  {names[ri]:5} right {right:3}/{n:3} | both teams really there: {liveR}/{live} | one there: {oneR}/{one} | neither there: {dead}")
