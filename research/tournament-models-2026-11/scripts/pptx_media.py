import sys, zipfile, re, os
z = zipfile.ZipFile(sys.argv[1]); out = sys.argv[2]
for n in ("ppt/slides/_rels/slide12.xml.rels", "ppt/slides/_rels/slide7.xml.rels", "ppt/slides/_rels/slide4.xml.rels", "ppt/slides/_rels/slide8.xml.rels"):
    r = z.read(n).decode(); imgs = re.findall(r'Target="\.\./media/([^"]+)"', r); print(n, imgs)
    for m in imgs:
        open(os.path.join(out, n.split("/")[-1].split(".")[0] + "_" + m), "wb").write(z.read("ppt/media/" + m))
