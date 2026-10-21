import os
import csv
import json

# The upset tracker as a page of the website:   python tools/make_upset_page.py   (then tools/make_site.py)
# Puts the tracker's code (reports/upset_tracker/index.html, the same page as the claude.ai tracker) inside the
# Strongside header of dashboard/upsets_template.html, with its three data files built in, and writes
# dashboard/upsets.html. Run it again after tools/pdem_summary.py, tools/tournament_spreads.py or
# tools/pdem_wide_gap.py change those files.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
MAIN = os.path.join(ROOT, "dashboard")
DATA = {"games": "pdem_upset_games.csv", "spreads": "tournament_spreads.csv", "wide_games": "pdem_wide_gap.csv"}

def main():
    data = {k: list(csv.DictReader(open(os.path.join(REPORTS, f), encoding="utf-8"))) for k, f in DATA.items()}
    tracker = open(os.path.join(REPORTS, "upset_tracker", "index.html"), encoding="utf-8").read()
    page = open(os.path.join(MAIN, "upsets_template.html"), encoding="utf-8").read()
    line = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(os.path.join(MAIN, "upsets.html"), "w", encoding="utf-8") as out:
        out.write(page.replace("__DATA__", line, 1).replace("__TRACKER__", tracker, 1))
    print("dashboard/upsets.html:", ", ".join(f"{k} {len(v)} rows" for k, v in data.items()), f"({len(line) / 1e6:.1f} MB of data)")

if __name__ == "__main__":
    main()
