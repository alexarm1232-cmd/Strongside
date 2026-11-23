# Save the full PCA map's inline <svg> (follow-ups deck slide) as a standalone SVG image, for upload to the Session Review deck.
import re
D = r"C:\Users\crtra\AppData\Local\Temp\claude\86481a0a115882d3\adacc821-ed64-4cd0-b0cd-6a0299e7fdea\scratchpad"
html = open(D + r"\deck3\project\slides\pcamap.html", encoding="utf-8").read()
svg = re.search(r"<svg.*?</svg>", html, re.S).group(0)
svg = re.sub(r'^<svg [^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="700" viewBox="0 0 1120 700">', svg)
open(D + r"\pca_map.svg", "w", encoding="utf-8").write(svg); print(len(svg))
