import os
import sys

# Puts the current dashboard_template.html into pages that are already built, keeping each page's data:
#     python tools/reskin_pages.py                  every built page
#     python tools/reskin_pages.py dashboard.html   only these
# A page is the template with its data dropped in where the template says __DATA__, so a change to the page's own code
# (layout, tables, buttons) does not need the numbers worked out again. Seconds instead of the best part of an hour.
# Only for template changes: when main.py or the stat modules change what goes into the data, rebuild with main.py.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
MAIN = os.path.join(ROOT, "dashboard")
TEMPLATE = os.path.join(MAIN, "dashboard_template.html")
MARK = "const DATA = "

def main():
    template = open(TEMPLATE, encoding="utf-8").read()
    if template.count(MARK + "__DATA__;") != 1:
        raise SystemExit("the template's data line is not 'const DATA = __DATA__;' - reskin needs updating")
    names = [a for a in sys.argv[1:] if a.endswith(".html")] or sorted(
        f for f in os.listdir(MAIN) if f.startswith("dashboard") and f.endswith(".html") and f != "dashboard_template.html")
    for name in names:
        path = os.path.join(MAIN, name)
        page = open(path, encoding="utf-8").read()
        start = page.find(MARK)
        end = page.find("\n", start)
        line = page[start + len(MARK):end].rstrip()
        if start < 0 or not line.endswith(";") or not line.startswith("{"):
            print(f"{name}: data line not found - skipped (rebuild it with main.py)")
            continue
        # the data was written on one line by main.py (json.dumps, with "</" already escaped)
        with open(path, "w", encoding="utf-8") as out:
            out.write(template.replace("__DATA__", line[:-1]))
        print(f"{name}: new template, same data ({len(line) / 1e6:.1f} MB)")

if __name__ == "__main__":
    main()
