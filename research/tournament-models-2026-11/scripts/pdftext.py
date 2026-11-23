# Minimal PDF text pull: inflate every FlateDecode stream, read (..)Tj / [..]TJ strings, with ToUnicode CMaps when present.
import sys, re, zlib
def inflate(data):
    out = []
    for m in re.finditer(rb"stream\r?\n", data):
        st = m.end(); en = data.find(b"endstream", st)
        if en < 0: continue
        try: out.append(zlib.decompress(data[st:en].rstrip(b"\r\n")))
        except Exception:
            try: out.append(zlib.decompressobj().decompress(data[st:en]))
            except Exception: pass
    return out
def cmaps(streams):
    M = {}
    for s in streams:
        if b"beginbfchar" in s or b"beginbfrange" in s:
            for a, b in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", s):
                try: M.setdefault(len(a) // 2, {})[int(a, 16)] = bytes.fromhex(b.decode()).decode("utf-16-be", "ignore")
                except Exception: pass
    return M
def unesc(b):
    b = re.sub(rb"\\([nrtbf()\\])", lambda m: {b"n": b"\n", b"r": b"", b"t": b" ", b"b": b"", b"f": b"", b"(": b"(", b")": b")", b"\\": b"\\"}[m.group(1)], b)
    return re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 255]), b)
def text(s):
    out = []
    for blk in re.findall(rb"BT(.*?)ET", s, re.S):
        line = []
        for tok in re.finditer(rb"\[(.*?)\]\s*TJ|\((.*?)(?<!\\)\)\s*Tj|<([0-9A-Fa-f]+)>\s*Tj|(T\*|Td|TD|')", blk, re.S):
            if tok.group(1) is not None:
                for p, kern in re.findall(rb"\((.*?)(?<!\\)\)|(-?\d+\.?\d*)", tok.group(1), re.S):
                    if p: line.append(unesc(p).decode("latin-1"))
                    elif kern and float(kern) < -200: line.append(" ")
            elif tok.group(2) is not None: line.append(unesc(tok.group(2)).decode("latin-1"))
            elif tok.group(3): line.append("\x00HEX" + tok.group(3).decode())
            else: line.append("\n")
        out.append("".join(line))
    return "\n".join(out)
for src, dst in zip(sys.argv[1::2], sys.argv[2::2]):
    data = open(src, "rb").read(); S = inflate(data); M = cmaps(S)
    t = "\n".join(text(s) for s in S if b"BT" in s)
    def hx(m):
        h = m.group(1)
        for w in (2, 1):
            if w in M and len(h) % (2 * w) == 0: return "".join(M[w].get(int(h[i:i + 2 * w], 16), "") for i in range(0, len(h), 2 * w))
        return ""
    t = re.sub(r"\x00HEX([0-9A-Fa-f]+)", hx, t)
    open(dst, "w", encoding="utf-8").write(t); print(dst, len(S), "streams", len(t), "chars")
