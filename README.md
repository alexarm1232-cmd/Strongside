# Strongside: college basketball ratings and simulators

A KenPom-style site for NCAA Division I men's basketball, built game by game from box scores and play-by-play.
Live at https://alexarm1232-cmd.github.io/Strongside/ . Seasons 2012-13 through 2025-26 are built; the data
collection reaches back to 2009-10.

## What the site has

- **Ratings**: offense and defense per 100 possessions, adjusted for opponent, home court (measured team by team)
  and blowouts; tempo, the four factors, strength of schedule, roster makeup (experience, continuity, height).
- **Players**: offensive and defensive ratings, usage, box plus-minus, win shares, on/off, basic per-game numbers.
- **Team pages**: schedule and game logs, play types and shot zones, lineups, and "without a player" estimates.
- **Team scatter**: any two of about 125 team numbers against each other (logos as markers, For/Against sides,
  conference and team focus, trend line and correlation, a sortable table), including the possession battle:
  offensive rebounds + turnovers forced minus the opponent's.
- **Game sim**: any two teams played possession by possession, thousands of times.
- **Tournament sim**: fill or load a 64-team bracket and play it out; the perfect-bracket chase on the real
  brackets (2013-2019, 2021-2026); a projected field from the ratings for any season (2020 had no tournament).
- **Pre-tournament / full season** views, a season picker, a Spread report (2025-26), and a Stat guide.
---

## Project Structure

Seasons are named by code: 2526 = 2025-26, 2425 = 2024-25, and so on. "full" means the full season, postseason included.
Run everything from the `basketball` folder.

```text
basketball/
├── dashboard/                 # builds the site pages:  python dashboard\main.py 2425   (no code = 2025-26)
│   ├── main.py, Kenstat.py, Playerstat.py, Shotstat.py, Spreadstat.py, dashboard_template.html
│   └── dashboard*.html + per-season data folders (2425/, 2425f/, ...), logos/
├── data/
│   ├── seasons/<code>[ full]/ # one folder per conference/team: games, box scores, rosters, play-by-play, shots
│   ├── ncaa stats/            # the stats.ncaa.org scraper (ncaa_scraper.py) and the CSVs it collects
│   ├── ncaa stats converted/  # those CSVs turned into per-team play-by-play (tools\ncaa_stats_reader.py)
│   └── removed non-D1/<code>/ # games against non-Division I teams, set aside
├── collect/<code>[ full]/     # one season's roster scripts (5rosterfetch, 7rostertrim); _template is what new seasons copy
├── tools/                     # build_from_ncaa_stats (a whole season from the scraped files, start to finish),
│                              #   make_season_codes (set up a season), transition_rosters (last season's roster for
│                              #   teams new to Division I, from their own athletics sites), ncaa_stats_reader/_season,
│                              #   use_ncaa_stats, copy_rosters, make_site, plus kaggle_plays and run_seasons.ps1 (older way)
├── logs/                      # output of the long runs
├── requirements.txt
└── README.md
