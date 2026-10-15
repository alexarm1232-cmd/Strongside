# Basketball Project — NCAA stats Simulator

## Project Overview
This project calculates **college basketball team and player stats game-by-game** using **NCAA API data**, rather than season totals. It includes advanced statistics, player on/off adjustments, lineup analysis, and a **game simulator** that can simulate matchups multiple times. 

The goal is to create a **KenPom-like platform** with interactive visuals, team pages, and simulation results — all based on real box scores and play-by-play data.

---

## Key Features

### 1. Team and Player Statistics
- **Team stats per game**:
  - Offensive and defensive efficiency (user-defined formulas)
  - Pace (possessions per game)
  - 4 factors (effective FG%, turnover rate, offensive rebounding, free throw rate)
  - SOS (Strength of Schedule) adjusted offense and defense
  - Basic stats: points, rebounds, assists, turnovers, shooting percentages
  - Bench rankings, team balance (top-heavy vs distributed scoring)
- **Player stats per game**:
  - Points, rebounds, assists, etc.
  - Usage and minutes played
  - On/off data to measure team performance with/without specific players
- **Points per shot type**:
  - Offensive points per shot and defensive points allowed per shot by zone/type
  - Uses play-by-play data to calculate shot efficiency

### 2. Player On/Off Adjustments
- Ability to select **one or multiple players** to exclude from stats calculations
- Estimates how team performance changes **if certain players are out**
- Supports game-by-game **rolling averages**

### 3. Game Simulation
- Simulate **any two teams on a neutral floor** for:
  - Single games
  - 100-game matchups
- Outputs:
  - Average box scores for all players
  - Total wins and losses
  - Win margins
  - Optional explanation for outcomes based on team stats and lineup logic
- **Player exclusion in simulations** supported

### 4. Interactive XY Graphs
- Compare teams using **any two statistics** for X and Y axes
- Team logos used as plot markers
- Filter by:
  - All teams
  - Power conferences
  - High-major conferences
  - Specific conferences
- Axes and data update dynamically

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
├── collect/<code>[ full]/     # the numbered scripts that download one season's data:  python "collect\2425\5rosterfetch.py"
├── tools/                     # project-wide jobs: make_site, make_season_codes, ncaa_stats_reader/_season,
│   │                          #   use_ncaa_stats, postseason, fix_team_totals, copy_rosters, kaggle_plays, run_*.ps1
│   └── one-off runs/          # runners used once (kept for reference)
├── logs/                      # output of the long runs
├── requirements.txt
└── README.md