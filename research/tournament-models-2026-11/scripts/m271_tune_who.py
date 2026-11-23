import numpy as np, os, contextlib, io
_load = np.load
np.load = lambda f, *a, **kw: _load(str(f).replace("m262_model_pre_G", "m262_model_pre_I"), *a, **kw)
src = open("m266_r32_tune.py", encoding="utf-8-sig").read().replace('"m266_best.json"', '"m271_best_who.json"')
exec(src)
