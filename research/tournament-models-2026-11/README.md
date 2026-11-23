# NCAA tournament models and brackets: research log (November 2026)

This folder holds the work done in the Claude Code session that ran from November 18 to 22, 2026: the scripts, the key results and the two bracket pages. Everything is scored on the 2010–2026 tournaments (16 tournaments, no 2020). The First Four is left out everywhere. Each year is predicted by a model trained on the other 15 years, unless a section says otherwise.

> **Note:** the scripts were written in a temporary working folder and were copied here as a record. Many of them load earlier outputs by file name, and some load the old data folder through `m99_model_types.py` (`Q.OLD`). They will not all run as they are from this folder.

## Where things ended up: the main bracket (1,634 points)

A bracket is filled out before Round 1 and scored 1-2-4-8-16-32 (192 points a year at most).

| Round | How the pick is made |
|---|---|
| Round 1 | Take the **Round 1 Upset Model's** pick, unless both the regular model and the simulator disagree and are each at least 60% sure |
| Round of 32 | **Pod pick**: each team's chance to win its four-team pod (win Round 1, then beat whoever comes out of the other game, regular model chances). The likeliest pod winner is the pick, and it also wins its Round 1 game |
| Sweet 16 | Regular model (late-round line) **plus pod strength**: the gap in the average pre-tournament net rating of the other three teams in each team's Round of 32 pod |
| Elite Eight | Regular model (late-round line) |
| Final Four and title | 70% simulator (10,000 games, pre-tournament dashboard, nobody out) + 30% regular model |

| Bracket | R1 | R32 | S16 | E8 | F4 | Title | Points | Champions right |
|---|---|---|---|---|---|---|---|---|
| **Pod + pod strength (main)** | 410 | 180 | 64 | 26 | 13 | 6 | **1,634** | 2010 Duke, 2012 Kentucky, 2013 Louisville, 2018 Villanova, 2019 Virginia, 2024 UConn |
| Pod bracket | 410 | 180 | 67 | 27 | 12 | 4 | 1,574 | 2012, 2018, 2019, 2024 |
| Vote of the 3 (previous) | 395 | 179 | 66 | 27 | 13 | 4 | 1,569 | 2012, 2018, 2019, 2024 |

**Caveat on the pod-strength gain.** It comes almost entirely from two title games (2010 and 2013). Its Sweet 16 count is actually lower (64 vs 67). It beats the plain pod bracket in 6 years and loses in 6, and it was the best of 8 pod-strength measures tried. The user chose to keep it as the main bracket.

Pages (built with `tools`-style templates; open them in a browser):
- `pages/full_brackets.html`: full brackets for every year, switchable between the three brackets above.
- `pages/rounds12_brackets.html`: Rounds 1–2 brackets (vote, blend and upset models).
- Bracket data: `results/m343_full.json` (all three brackets) and `results/m335_full.json`.

## The models

- **Regular model ("model 1"):** a ridge logistic model on 31 matchup inputs: strength gap, gap × pace, the four factors, steals and blocks, coach and star inputs. A separate line is fit for each round group:
  - **Rounds 1–2:** the line fit on R1–R2 games. The "who plays" input is used in Round 1 only.
  - **Sweet 16 to title:** the line fit on S16–title games.

  The patched version gets 752 of 1,007 real games right.
- **Round 1 Upset Model:** 31 inputs, all hand-picked. It deliberately leaves out seed, net rating and other strength stand-ins. It predicts "the lower seed wins" and calls the upset at 40%. Held out it gets 400/511 right (AUC 0.800). Spec: `results/upset_model_r64.json`.
- **Round of 32 Upset Model:** 22 inputs, ridge 10, upset called at 45%. Held out it gets 208/256 right. Spec: `results/upset_model_r32_candidate.json`.
- **Simulator:** the dashboard's game simulator. It is run on pre-tournament dashboards with nobody out. Pairs simulated for this work are in:
  - `results/m283_sim_r32.json`, `m312_sim.json`, `m320_sim_extra.json`, `m328_sim.json`: Round of 32, Sweet 16 and Elite Eight matchups
  - `results/m304_sim_ff.json`, `m335_sim_extra.json`: Final Four and title matchups

## What was tested and what happened (most recent first)

| Idea | Result | Script(s) |
|---|---|---|
| Ramp pre-tournament net rating into each round's chance (0 in R1, growing each round) | **Worse at every step** (1,598 down to 1,456). The model and simulator already contain net rating: the simulator tracks the net gap at 0.88–0.97, and adding net again costs 6 Sweet 16+ games | m347, m348 |
| Final Four profile (64 teams) | Champions: 12 of 16 were 1 seeds, all were top-30 net, 11 of 16 had a top-5 offense. Among 1–4 seeds, offense separates Final Four teams about twice as much as defense. No 6 seed reached the Final Four | m346 |
| Lower seeds from stronger conferences | They do win more, but mainly through seed and strength. The regular model already accounts for it. Adding it to the upset models: R1 388–391 (vs 400), R32 207–208 (vs 208) | m344, m345 |
| Pod strength in the Sweet 16 | +60 on the full bracket from two title games (the main bracket above). Fewer Sweet 16 games right | m340–m343 |
| Deep-run measures for the Sweet 16 (form vs tournament teams, close games, star minutes) and pre-tournament absences (players out for the last 3 games) | None helps on the 128 real Sweet 16 games. The current line gets 91 right (71%) | m337–m339 |
| Other versions of the Sweet 16/Elite Eight line | The current S16–title line is best: 134/192 real games, vs net 120, seed 119, simulator 118 | m336 |
| Pod picking through the Round of 32 | 770 points for Rounds 1–2 (best), 1,574 for the full bracket. The best of 16 versions; choosing the version from the other years only gives 1,548 | m328–m330, m335 |
| Pod picking / ranking through the Sweet 16 | More Sweet 16 games right (69–73) but fewer Elite Eight and Final Four games: 1,528–1,563 | m332–m334 |
| Round of 32 % thresholds (upset model cutoff, overrides, vote unless the upset model is confident) | None beats the vote: 1,475–1,569 vs 1,571. The upset model alone in the Round of 32 scores 1,509, because its Cinderellas get dropped later and the top seeds it knocks out would have gone deep | m322–m327 |
| Weighting the upset model more in Round 1 | **60% rule** (upset model's pick unless both others are ≥60% sure): R1 407, Rounds 1–2 759 vs 753. It was the rule chosen in every leave-one-year-out fold | m320, m321 |
| Games 0 of 3 pickers got right | Round 1: 58 / 58 / 81 / 314 games right by 0 / 1 / 2 / 3 pickers. Round of 32: 46 / 30 / 51 / 129 | m318, m319, m323 |
| New game-log measures for the upset models (rest, conference-tournament load, form, streaks, home dependence) | At most +3 games: chance level | m315, m316 |
| Ridge penalty × season half-life grid for both upset models | The locked settings are already at the top | m317 |
| Simulator in the Sweet 16/Elite Eight | Worse: on real games the model gets 133 right and the simulator 118. In the Final Four and title the simulator is better (36 vs 31 of 48), which supports 70/30 | m312, m313 |
| Expected-points brackets, champion-first, model + net mixes for the late rounds | No edge that held up on unseen years | m308–m311 |
| Earlier in the session | Steals/blocks fix; who plays limited to Round 1; locking the Round of 32 model; feeding Round 1 picks into the Round of 32 (no gain); vote / blend / recency / chaos regions / over-seeding / Sweet 16 model feasibility | m262–m307 |

## Data note

`Round of 64 - pre-tournament data 2010-2026.csv` lives in the user's Downloads folder and is not in this repo. It was built by `scripts/m157_team_totals_csv.py`. 2021 Oregon was added with `scripts/m331_add_oregon.py`, so it now has 1,023 rows; 2021 VCU is still out because of the no-contest. All internal checks pass.
