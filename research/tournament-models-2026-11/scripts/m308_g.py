import contextlib,io,os
src=open("m281_pair_features.py",encoding="utf-8-sig").read()
with contextlib.redirect_stdout(io.StringIO()): exec(src)
print(G[500]); print(set(g["rnd"] for g in G))
