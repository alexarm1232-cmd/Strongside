import json
SR = json.load(open("m283_sim_r32.json"))
add = {"2009-10": {"Duke|Louisville":0.7619,"Baylor|Old Dominion":0.6516,"Washington|New Mexico":0.5471,"Minnesota|Pittsburgh":0.5169},
"2010-11": {"San Diego St|Temple":0.6686,"Duke|Tennessee":0.8167,"Florida|UCLA":0.6236,"Notre Dame|Florida St":0.7054},
"2011-12": {"Florida|Missouri":0.3595,"North Carolina|Alabama":0.7143}, "2012-13": {"Saint Louis|Oregon":0.6193}, "2013-14": {"Arizona|Gonzaga":0.7119},
"2014-15": {"Wisconsin|Oregon":0.8658,"Oklahoma|Dayton":0.7395}, "2015-16": {"Gonzaga|Utah":0.5218}, "2016-17": {"North Carolina|Arkansas":0.7709},
"2017-18": {"Duke|Rhode Island":0.818,"Michigan St|Syracuse":0.7484,"Michigan|San Diego St":0.7366},
"2018-19": {"Oregon|Kansas St":0.3933,"Tennessee|Iowa":0.7336,"North Carolina|Washington":0.8306,"Duke|UCF":0.8502,"Gonzaga|Baylor":0.8338},
"2020-21": {"West Virginia|Syracuse":0.6171}, "2021-22": {"Kansas|Creighton":0.7509,"Duke|Michigan St":0.6886},
"2022-23": {"Gonzaga|Arizona St":0.769,"Missouri|Arizona":0.3154,"Marquette|Southern California":0.6574,"Fla. Atlantic|Purdue":0.3098},
"2024-25": {"Auburn|Creighton":0.826}, "2025-26": {"Houston|Texas A&M":0.8012}}
for s, v in add.items(): SR[s].update(v)
json.dump(SR, open("m283_sim_r32.json", "w"), indent=0); print("merged", sum(len(v) for v in add.values()))
