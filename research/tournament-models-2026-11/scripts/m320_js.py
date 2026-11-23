import json
M=json.load(open("m320_need.json"))
code=lambda s: "dashboard.html" if s=="2025-26" else f"dashboard_{s[2:4]}{s[5:7]}.html"
acts=[]
JS="const c=n=>n.replace(/[. ]+$/,''); const nm=n=>teamByName[n]||teamByName[Object.keys(teamByName).find(k=>c(k)===c(n))]; const out=[]; for(const [a,b] of P){const A=nm(a),B=nm(b); if(!A||!B){out.push(null);continue;} const r=await simGames(A,B,'N',new Set(),new Set(),10000,()=>{},undefined,true).promise; out.push(+(r.acc.tally[1]/r.acc.tally[0]).toFixed(4));} DATA.meta.season+' '+JSON.stringify(out)"
for s,v in M.items():
    acts.append({"name":"navigate","input":{"url":"http://localhost:8765/"+code(s),"tabId":"TAB"}})
    acts.append({"name":"javascript_tool","input":{"action":"javascript_exec","tabId":"TAB","text":"const P="+json.dumps(v)+"; "+JS}})
open("m320_actions.json","w").write(json.dumps(acts))
print(len(acts))
