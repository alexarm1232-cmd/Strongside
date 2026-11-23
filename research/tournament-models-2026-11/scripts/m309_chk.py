import os, contextlib, io
src = open("m308_late.py", encoding="utf-8-sig").read(); src = src[:src.index("res = {}")]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
for s,t in (("2015-16","Villanova"),("2010-11","UConn"),("2022-23","UConn"),("2012-13","Louisville")):
    A=adv(s,pm); print(s,t,[round(x,3) for x in A[t][1:]], "seed",seed(s,t),"net",net(s,t))
    slots,_=field(s); reg=[x for x in slots[(slots.index(t)//16)*16:(slots.index(t)//16+1)*16] if x]
    print("  vs region:", [(o, round(pm(s,t,o),2)) for o in reg if o!=t][:15])
