# Ridge vs linear SVM head to head (no simulator): the 29 games they pick differently (teams, seeds, round, each pick,
# each one's win chance, winner), who picks the underdog in those, and summary numbers (win chances, log-loss, how far
# apart their chances are). Picks from m100's job: the 756 pipeline, each tournament held out, only the model type differs.
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m99_model_types as Q
from m100_ridge_svm import job
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    NM = ["Ridge logistic (your model)", "Linear SVM"]; SC = {n: np.full(Q.N, np.nan) for n in NM}
    with ProcessPoolExecutor(8) as ex:
        for name, te, v in ex.map(job, [(n, s) for n in NM for s in Q.SEASONS]): SC[name][te] = v
    keep = ~Q.FF; yb = Q.yb
    D3 = np.load(os.path.join(Q.OLD, "m3_data.npz"), allow_pickle=True); sS, sW = D3["seedS"], D3["seedW"]
    pr, ps = 1 / (1 + np.exp(-SC[NM[0]])), 1 / (1 + np.exp(-SC[NM[1]]))
    S, W = Q.B.Sname, Q.Wn
    RN = {"First round": "Round of 64", "Second round": "Round of 32", "Sweet 16": "Sweet 16", "Elite Eight": "Elite Eight", "Final Four": "Final Four", "Championship": "Title"}
    rows = []
    for i in np.where(keep & ((pr > 0.5) != (ps > 0.5)))[0]:
        pick = lambda p: (S[i], int(sS[i])) if p > 0.5 else (W[i], int(sW[i]))
        win = (S[i], int(sS[i])) if yb[i] else (W[i], int(sW[i]))
        rows.append(dict(season=int(Q.seas[i][:4]) + 1, round=RN[Q.RND[i]], a=S[i], sa=int(sS[i]), b=W[i], sb=int(sW[i]),
                         ridge=pick(pr[i])[0], ridge_p=round(float(max(pr[i], 1 - pr[i])), 3), svm=pick(ps[i])[0], svm_p=round(float(max(ps[i], 1 - ps[i])), 3),
                         winner=win[0], right="Ridge" if pick(pr[i])[0] == win[0] else "SVM"))
    rows.sort(key=lambda r: (r["season"], list(RN.values()).index(r["round"])))
    for r in rows: print(r)
    # underdog picks in the splits (by seed; equal seeds skipped)
    dog_r = sum(1 for r in rows if r["sa"] != r["sb"] and ((r["ridge"] == r["a"]) == (r["sa"] > r["sb"])))
    dog_s = sum(1 for r in rows if r["sa"] != r["sb"] and ((r["svm"] == r["a"]) == (r["sa"] > r["sb"])))
    dog_hit_r = sum(1 for r in rows if r["sa"] != r["sb"] and ((r["ridge"] == r["a"]) == (r["sa"] > r["sb"])) and r["right"] == "Ridge")
    dog_hit_s = sum(1 for r in rows if r["sa"] != r["sb"] and ((r["svm"] == r["a"]) == (r["sa"] > r["sb"])) and r["right"] == "SVM")
    k = keep; ll = lambda p: float(-np.mean(np.where(yb, np.log(np.clip(p, 1e-6, 1)), np.log(np.clip(1 - p, 1e-6, 1)))[k]))
    upset_all = lambda p: int((k & (sS != sW) & np.where(sS > sW, p > 0.5, p < 0.5)).sum())
    upset_hit = lambda p: int((k & (sS != sW) & np.where(sS > sW, p > 0.5, p < 0.5) & ((p > 0.5) == yb)).sum())
    out = dict(rows=rows, dog=[dog_r, dog_hit_r, dog_s, dog_hit_s],
               ll=[ll(pr), ll(ps)], corr=float(np.corrcoef(pr[k], ps[k])[0, 1]), mean_gap=float(np.mean(np.abs(pr - ps)[k])),
               max_gap=float(np.max(np.abs(pr - ps)[k])), split_gap=float(np.mean([abs(r["ridge_p"] - r["svm_p"]) for r in rows])),
               split_conf=[float(np.mean([r["ridge_p"] for r in rows])), float(np.mean([r["svm_p"] for r in rows]))],
               upsets=[upset_all(pr), upset_hit(pr), upset_all(ps), upset_hit(ps)],
               conf=[float(np.mean(np.maximum(pr, 1 - pr)[k])), float(np.mean(np.maximum(ps, 1 - ps)[k]))])
    print({k_: v for k_, v in out.items() if k_ != "rows"})
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "m101_out.json"), "w"), indent=1)
