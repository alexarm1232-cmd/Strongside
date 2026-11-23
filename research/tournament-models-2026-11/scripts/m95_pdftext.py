# Pull the text out of the course slide PDFs (page count + the slide titles / text), to see what topics they cover.
import sys, os
FILES = ["Ch2-blankslides.pdf", "Ch3-blankslides.pdf", "Ch4A-blankslides.pdf", "Ch4B-blankslides.pdf", "Ch8-blankslides.pdf",
         "Ch9-blankslides.pdf", "ML10 blank.pdf", "ML11A-blank.pdf", "ML11B-blank.pdf"]
try:
    from pypdf import PdfReader
except ImportError:
    try: from PyPDF2 import PdfReader
    except ImportError: PdfReader = None
if PdfReader is None:
    import fitz
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_text")
os.makedirs(OUT, exist_ok=True)
for f in FILES:
    path = os.path.join(r"C:\Users\crtra\Downloads", f)
    if PdfReader:
        pages = [p.extract_text() or "" for p in PdfReader(path).pages]
    else:
        pages = [p.get_text() for p in fitz.open(path)]
    open(os.path.join(OUT, f + ".txt"), "w", encoding="utf-8").write("\n\n=== PAGE ===\n".join(pages))
    first = [" ".join(p.split())[:90] for p in pages if p.strip()]
    print(f"## {f}: {len(pages)} pages, {sum(len(p) for p in pages)} chars")
    for line in first[:: max(1, len(first) // 12)][:14]: print("   ", line)
