# Text of every slide in AndrewF_Presentation.pptx (no python-pptx here: read the slide XML), plus which images and
# charts each slide uses, so slide 12's variable-importance graph can be found.
import zipfile, re, os
P = r"C:\Users\crtra\Downloads\AndrewF_Presentation.pptx"
z = zipfile.ZipFile(P)
slides = sorted([n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)], key=lambda n: int(re.findall(r"\d+", n)[0]))
for n in slides:
    k = int(re.findall(r"\d+", n)[0]); x = z.read(n).decode("utf8")
    paras = re.findall(r"<a:p>(.*?)</a:p>", x, re.S)
    text = [" ".join(re.findall(r"<a:t>([^<]*)</a:t>", p)).strip() for p in paras]
    text = [t for t in text if t]
    rel = f"ppt/slides/_rels/slide{k}.xml.rels"; media = []
    if rel in z.namelist():
        media = re.findall(r'Target="([^"]+)"', z.read(rel).decode("utf8"))
        media = [m for m in media if "media" in m or "chart" in m or "embed" in m]
    notes = ""
    nn = f"ppt/notesSlides/notesSlide{k}.xml"
    print(f"\n===== SLIDE {k} ===== media: {media}")
    for t in text: print("  ", t)
print("\nMEDIA FILES:", [n for n in z.namelist() if n.startswith("ppt/media") or n.startswith("ppt/charts")])
