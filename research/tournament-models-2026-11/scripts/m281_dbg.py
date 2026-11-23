exec(open("m281_pair_features.py", encoding="utf-8").read().split("# validate on every")[0])
from collections import Counter
c = Counter(); worst = {}
for i in range(N):
    if not (k[i] and RND[i] in ("First round", "Second round")): continue
    S_, W_, x, _ = features(seas[i], Sn[i], Wn[i]); d = np.abs(x - XX[i])
    for j in np.where(d > 1e-6)[0]: c[NAMES[j]] += 1; worst[NAMES[j]] = max(worst.get(NAMES[j], 0), d[j])
for nm, v in c.most_common(): print(f"{nm:35} {v:4} worst {worst[nm]:.3f}")
