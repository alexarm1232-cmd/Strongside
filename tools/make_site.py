import os
import shutil

# Builds the folder that gets published as the website:   python tools\make_site.py
# It holds only what the pages need: the season pages, their data files and the logos. Nothing else from the project
# goes in: no raw downloads, no scripts, no API key. Run it again after rebuilding any page, then push the folder.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
MAIN = os.path.join(ROOT, "dashboard")
# The project folder is the Strongside repository; GitHub Pages publishes its "docs" folder
SITE = os.path.join(ROOT, "docs")
# folders of per-team data files the pages load: this season's, and one per other season and view
DATA_FOLDERS = ["gamelogs", "lineups", "shots", "logos"]
HOME = "dashboard.html"

def main():
    if os.path.isdir(SITE):
        for name in os.listdir(SITE):
            if name == ".git": continue             # the repository itself is left alone
            path = os.path.join(SITE, name)
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    os.makedirs(SITE, exist_ok=True)
    pages = [f for f in os.listdir(MAIN) if f.startswith("dashboard") and f.endswith(".html") and f != "dashboard_template.html"]
    for f in pages + [f for f in ("seasons.js", "upsets.html", "tourneyreport.js") if os.path.exists(os.path.join(MAIN, f))]:
        shutil.copyfile(os.path.join(MAIN, f), os.path.join(SITE, f))
    folders = list(DATA_FOLDERS)
    for name in os.listdir(MAIN):               # the other seasons' folders: 2425, 2425f, 2324 ...
        path = os.path.join(MAIN, name)
        if os.path.isdir(path) and any(os.path.isdir(os.path.join(path, sub)) for sub in ("gamelogs", "lineups", "shots")):
            folders.append(name)
    for name in folders:
        if os.path.isdir(os.path.join(MAIN, name)):
            shutil.copytree(os.path.join(MAIN, name), os.path.join(SITE, name), ignore=shutil.ignore_patterns("*.py", "*.pyc", "__pycache__", "*.json"))
    # the address with nothing after it opens the current season, at whatever page was asked for
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as out:
        out.write(f'<!doctype html>\n<meta charset="utf-8">\n<title>Strongside</title>\n'
                  f'<script>location.replace("{HOME}" + location.hash);</script>\n'
                  f'<noscript><a href="{HOME}">Open Strongside</a></noscript>\n')
    open(os.path.join(SITE, ".nojekyll"), "w").close()      # tells GitHub Pages to serve the files exactly as they are
    files = sum(len(f) for _, _, f in os.walk(SITE) if ".git" not in _)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(SITE) if ".git" not in d for f in fs)
    biggest = max(((os.path.getsize(os.path.join(d, f)), os.path.relpath(os.path.join(d, f), SITE)) for d, _, fs in os.walk(SITE) if ".git" not in d for f in fs))
    print(f"site folder: {files} files, {size / 1e6:.0f} MB; pages: {sorted(pages)}")
    print(f"largest file: {biggest[1]} ({biggest[0] / 1e6:.1f} MB)")
    # nothing that should stay private may be in there
    leaks = [os.path.relpath(os.path.join(d, f), SITE) for d, _, fs in os.walk(SITE) for f in fs
             if f.lower().endswith((".py", ".txt", ".ps1", ".csv")) or "key" in f.lower() or "cache" in f.lower()]
    print("files that should not be published:", leaks or "none")

if __name__ == "__main__":
    main()
