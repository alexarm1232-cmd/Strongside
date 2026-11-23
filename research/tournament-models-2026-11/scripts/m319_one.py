import json
from collections import Counter
B={d["season"]:d for d in json.load(open("m285_brackets.json"))}
t=open("m242_bracket_in.js",encoding="utf-8").read(); BI=json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}")+1])
K=("upset","model","sim"); NM={"upset":"upset models","model":"regular model","sim":"simulator"}
def seedof(g,t): return next(x["sH"] if x["H"]==t else x["sL"] for x in g if t in (x["H"],x["L"]))
for rnd in ("r1","r2"):
    rows=[]; base=[]
    for s,d in B.items():
        g=BI[s]["games"]; w=dict(BI[s]["wins"])
        for x in g:
            if x["H"]==x["L"]: w[x["H"]]=w.get(x["H"],0)+1
        n = 32 if rnd=="r1" else 16
        for j in range(n):
            if rnd=="r1":
                x=g[j]
                if x["H"]==x["L"]: continue
                win=x["won"]; ok={k:d["brackets"][k]["r1"][j]["pick"]==win for k in K}
                pk={k:d["brackets"][k]["r1"][j] for k in K}; hs,ls=x["sH"],x["sL"]; up = win==x["L"]
            else:
                pk={k:d["brackets"][k]["r2"][j] for k in K}; ok={k:w.get(pk[k]["pick"],0)>=2 for k in K}
                pod=[t_ for x in g[4*j:4*j+4] for t_ in (x["H"],x["L"])]; win=next((t_ for t_ in pod if w.get(t_,0)>=2),None)
                ss=sorted(seedof(g,t_) for t_ in pod if t_); hs=None; up = win is not None and seedof(g,win)>min(seedof(g,t_) for t_ in pod[:4] if t_) and seedof(g,win)>min(seedof(g,t_) for t_ in pod[4:] if t_)
                up = win is not None and seedof(g,win) not in (min(ss),)  # winner not the pod's best seed
                ls=seedof(g,win) if win else None
            c=sum(ok.values()); rec=dict(s=s,ok=ok,pk=pk,up=up,hs=hs,ls=ls,win=win)
            base.append(rec)
            if c==1: rows.append(rec)
    print(f"\n===== {'Round 1' if rnd=='r1' else 'Round of 32'}: {len(rows)} games with exactly 1 of 3 right")
    who=Counter(next(k for k in K if r["ok"][k]) for r in rows); print("  the lone right picker:", {NM[k]:v for k,v in who.items()})
    print(f"  winner was the upset (lower seed / not pod's top seed): {sum(r['up'] for r in rows)} of {len(rows)}  (all games: {sum(r['up'] for r in base)} of {len(base)})")
    for k in K:
        sub=[r for r in rows if r["ok"][k]]
        if not sub: continue
        ups=sum(r["up"] for r in sub)
        pr=[r["pk"][k]["p"] for r in sub]; other=[r["pk"][o]["p"] for r in sub for o in K if o!=k]
        print(f"  {NM[k]} alone right ({len(sub)}): picked the upset {ups}, its avg confidence {sum(pr)/len(pr):.2f}, other two avg confidence {sum(other)/len(other):.2f}")
    if rnd=="r1":
        m=Counter(f"{r['hs']} v {r['ls']}" for r in rows); a=Counter(f"{r['hs']} v {r['ls']}" for r in base)
        print("  by matchup (1-of-3 games / all games):", ", ".join(f"{k}: {m[k]}/{a[k]}" for k in sorted(a,key=lambda z:int(z.split()[0]))))
    else:
        m=Counter(r["ls"] for r in rows); print("  winner's seed:", dict(sorted(m.items())))
    yr=Counter(int(r["s"][:4])+1 for r in rows); print("  by year:", dict(sorted(yr.items())))
    # confidence of the outvoted right picker vs the wrong ones: margin from 50%
    close=sum(1 for r in rows if max(abs(r["pk"][k]["p"]-.5) for k in K if not r["ok"][k])<.1); print(f"  games where both wrong pickers were under 60% sure: {close} of {len(rows)}")
