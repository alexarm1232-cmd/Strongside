import csv, collections
p=r"C:\Users\crtra\Downloads\Round of 64 - pre-tournament data 2010-2026.csv"
rows=list(csv.DictReader(open(p,encoding="utf-8-sig")))
print("rows",len(rows),"cols",len(rows[0]))
by=collections.Counter(r["Year"] for r in rows); print("per year",dict(by))
blank=collections.Counter(k for r in rows for k,v in r.items() if v in ("",None,"NA","nan")); print("blank cells",dict(blank))
print("W+L!=G:",[(r["Year"],r["Team"],r["G"],r["W"],r["L"]) for r in rows if int(r["W"])+int(r["L"])!=int(r["G"])][:10])
print("dupes:",[k for k,v in collections.Counter((r["Year"],r["Team"]) for r in rows).items() if v>1])
for y in sorted(by):
    sc=collections.Counter(int(r["Seed"]) for r in rows if r["Year"]==y)
    bad={s:c for s,c in sc.items() if c!=4}
    if bad: print("seed counts off",y,bad)
net=[(r["Year"],r["Team"]) for r in rows if abs(float(r["ORtg"])-float(r["DRtg"])-float(r["NetRtg"]))>0.05]; print("NetRtg != ORtg-DRtg:",len(net),net[:5])
chk=lambda r,a,b,c: abs(int(r[a])/max(int(r[b]),1)-float(r[c]))>0.001
print("pct mismatches:",sum(chk(r,"FGM","FGA","FG_Pct") or chk(r,"3PM","3PA","3P_Pct") or chk(r,"FTM","FTA","FT_Pct") for r in rows))
print("2PM check:",sum(int(r["2PM"])!=int(r["FGM"])-int(r["3PM"]) for r in rows), "TRB check:",sum(int(r["TRB"])!=int(r["ORB"])+int(r["DRB"]) for r in rows))
gs=sorted(int(r["G"]) for r in rows); print("games range",gs[0],gs[-1], "teams with G<25:",[(r["Year"],r["Team"],r["G"]) for r in rows if int(r["G"])<25])
for y,t in (("2010","Kentucky"),("2024","UConn"),("2018","Virginia"),("2019","Virginia"),("2026","Duke"),("2021","Oregon"),("2021","VCU"),("2011","VCU")):
    r=[x for x in rows if x["Year"]==y and x["Team"]==t]; print(y,t,[(x["G"],x["W"],x["L"],x["Seed"]) for x in r])
print("first rows years:",sorted(by)[:3], "...", "2021 teams missing?", by.get("2021"))
