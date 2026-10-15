import os
import re
import sys
import json
import time
import shutil
import subprocess
from datetime import date, timedelta
import requests
from fix_team_totals import ncaa_box

# Builds a "full season" copy of a season's data, postseason included, next to the pre-tournament one, so the
# dashboard can show either:   python tools/postseason.py 2526 copy     copies the season's folder to "... full"
#                              python tools/postseason.py 2526 games    adds the games played after Selection Sunday
#                              python tools/postseason.py 2526 scripts  makes "collect/2526 full": the season's scripts,
#                                                                 pointed at the full folder and run through the final
# The pre-tournament folder is never touched. After "scripts", the season's usual steps are run from the new scripts
# folder (8, 7, 6 or 9/10/11); they only fetch what the added games need.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
SEASONS = {     # code: (data folder, scripts folder, Selection Sunday, the day of the final)
    "2526": ("data/seasons/2526", "collect/2526", date(2026, 3, 15), date(2026, 4, 6)),
    "2425": ("data/seasons/2425", "collect/2425", date(2025, 3, 16), date(2025, 4, 7)),
    "2324": ("data/seasons/2324", "collect/2324", date(2024, 3, 17), date(2024, 4, 8)),
}
SCOREBOARD = "https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1/{}/all-conf"
BOX = "https://ncaa-api.henrygd.me/game/{}/boxscore"

def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def full_folder(code):
    return os.path.join(ROOT, f"data/seasons/{code} full")

def clean(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def copy(code):
    source, dest = os.path.join(ROOT, SEASONS[code][0]), full_folder(code)
    if os.path.isdir(dest):
        print(f"{dest} is already there.")
        return
    shutil.copytree(source, dest)
    for name in ("cbbd_tried.json", "cbbd_spots_tried.json"):      # so teams are asked again for their added games
        if os.path.exists(os.path.join(dest, name)):
            os.remove(os.path.join(dest, name))
    print(f"Copied {source} to {dest}")

def games(code):
    base = full_folder(code)
    _, _, sunday, final = SEASONS[code]
    folders = {}
    for conf in os.listdir(base):
        conf_path = os.path.join(base, conf)
        if os.path.isdir(conf_path):
            for team in os.listdir(conf_path):
                if os.path.isdir(os.path.join(conf_path, team)):
                    folders[clean(team)] = os.path.join(conf_path, team)
    added = skipped = boxes = 0
    kinds = {}
    day = sunday + timedelta(days=1)
    while day <= final:
        label = day.strftime("%Y/%m/%d")
        try:
            listed = requests.get(SCOREBOARD.format(label), timeout=25).json().get("games", [])
        except Exception:
            listed = []
        time.sleep(0.4)
        for entry in listed:
            g = entry.get("game", {})
            home, away = g.get("home", {}), g.get("away", {})
            names = (home.get("names", {}).get("short", ""), away.get("names", {}).get("short", ""))
            if not str(home.get("score") or "").strip() or not str(away.get("score") or "").strip(): continue
            if clean(names[0]) not in folders or clean(names[1]) not in folders:        # only games between two of our teams, by exact name
                skipped += 1
                continue
            game_id = str(g.get("gameID"))
            event = "NCAA tournament" if g.get("bracketRound") or g.get("bracketId") else "other postseason"
            kinds[event] = kinds.get(event, 0) + 1
            row = {"game_id": game_id, "date": label, "away_team": names[1], "away_score": str(away.get("score")),
                   "home_team": names[0], "home_score": str(home.get("score")), "post": True, "event": event}
            box = None
            for name in names:
                folder = folders[clean(name)]
                listed_ids = [str(x) for x in read_json(os.path.join(folder, "games.json"), [])]
                if game_id not in listed_ids:
                    with open(os.path.join(folder, "games.json"), "w", encoding="utf-8") as out:
                        json.dump(listed_ids + [game_id], out, indent=2)
                scores = read_json(os.path.join(folder, "game_scores.json"), [])
                if not any(str(s.get("game_id")) == game_id for s in scores):
                    with open(os.path.join(folder, "game_scores.json"), "w", encoding="utf-8") as out:
                        json.dump(scores + [row], out, indent=4)
                # the schedule saved from Sports Reference may be from before these games were played
                for f in os.listdir(folder):
                    if f.startswith("sr_schedule_"):
                        os.remove(os.path.join(folder, f))
                path = os.path.join(folder, "boxscores", game_id + ".json")
                if not os.path.exists(path):
                    if box is None:
                        try:
                            raw = requests.get(BOX.format(game_id), timeout=25)
                            box = ncaa_box(raw.json()) if raw.status_code == 200 else False
                        except Exception:
                            box = False
                        time.sleep(0.4)
                    if box and len(box["teams"]) == 2:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "w", encoding="utf-8") as out:
                            json.dump(box, out, indent=4)
                        boxes += 1
            added += 1
        day += timedelta(days=1)
    print(f"{code}: {added} postseason games between two of our teams ({kinds}); {skipped} left out (a team that is not ours); {boxes} NCAA box scores saved")

def scripts(code):
    data, codes, sunday, final = SEASONS[code]
    dest = os.path.join(ROOT, codes + " full")
    os.makedirs(dest, exist_ok=True)
    full = f"data/seasons/{code} full"
    for name in os.listdir(os.path.join(ROOT, codes)):
        path = os.path.join(ROOT, codes, name)
        if name == "cbbd_key.txt":
            shutil.copyfile(path, os.path.join(dest, name))
        if not name.endswith(".py"): continue
        text = open(path, encoding="utf-8").read()
        text = text.replace(f'"{data}"', f'"{full}"')
        text = text.replace("date(%d, %d, %d)" % (sunday.year, sunday.month, sunday.day), "date(%d, %d, %d)" % (final.year, final.month, final.day))
        text = text.replace(sunday.strftime("%Y/%m/%d"), final.strftime("%Y/%m/%d"))
        with open(os.path.join(dest, name), "w", encoding="utf-8", newline="") as out:
            out.write(text)
    print(f"Scripts for the full season are in {dest}")

if __name__ == "__main__":
    code, step = (sys.argv[1:3] + [None, None])[:2]
    if code not in SEASONS or step not in ("copy", "games", "scripts"):
        print("e.g.  python tools/postseason.py 2526 copy     then  games  then  scripts")
    else:
        {"copy": copy, "games": games, "scripts": scripts}[step](code)
