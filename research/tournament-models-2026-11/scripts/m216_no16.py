import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
exec(open(os.path.join(H, "m214_pool32.py"), encoding="utf-8").read().split("print(\"added inputs")[0])
sl = np.array([r["sL"] for r in rows]); no16 = sl == 16
for lab, ins in (("locked 28", U), ("32 inputs", NEW)):
    X = np.column_stack([col(c) for c in ins]); out = np.zeros(n)
    for s in sorted(set(seas)): tr, te = seas != s, seas == s; out[te] = 1 / (1 + np.exp(-ridge(X[tr], y[tr], W[tr])(X[te])))
    f = 1 / (1 + np.exp(-ridge(X[early], y[early], W[early])(X[~early]))); b = 1 / (1 + np.exp(-ridge(X[~early], y[~early], W[~early])(X[early])))
    pk = (out >= .4) & ~no16; pf = (f >= .4) & ~no16[~early]; pb = (b >= .4) & ~no16[early]
    for j in np.where((out >= .4) & no16)[0]: print(f"   {lab}: had picked {int(rows[j]['s'][:4]) + 1} (16) {rows[j]['L']} over (1) {rows[j]['H']} at {out[j]:.0%} -> {'WON' if y[j] else 'lost'}")
    print(f"{lab:10} 1 seeds always: held out {int((pk == (y == 1)).sum())}/511 | upset picks {int(pk.sum())} ({int((pk & (y == 1)).sum())} hit) | forward {int((pf == (y[~early] == 1)).sum())}/255 | backward {int((pb == (y[early] == 1)).sum())}/288")