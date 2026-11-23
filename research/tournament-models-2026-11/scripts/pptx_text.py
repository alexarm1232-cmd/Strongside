import sys, zipfile, re
z = zipfile.ZipFile(sys.argv[1])
sl = sorted([n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)], key=lambda n: int(re.findall(r"\d+", n)[0]))
for n in sl:
    x = z.read(n).decode("utf-8", "ignore"); t = re.findall(r"<a:t>([^<]*)</a:t>", x)
    print(f"--- {n.split('/')[-1]}: " + " | ".join(s for s in t if s.strip()))
ch = [n for n in z.namelist() if "chart" in n and n.endswith(".xml")]
for n in ch:
    x = z.read(n).decode("utf-8", "ignore"); v = re.findall(r"<c:v>([^<]*)</c:v>", x)
    if v: print(f"=== {n}: " + " | ".join(v[:120]))
