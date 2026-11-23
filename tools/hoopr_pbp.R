# Downloads ESPN men's college basketball play-by-play (plus each season's schedule and box scores) through the
# hoopR package, for the seasons before the ones the project already has (it starts at 2009-10):
#
#     "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" tools\hoopr_pbp.R                 2005-06 through 2008-09
#     "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" tools\hoopr_pbp.R 2008 2009       only those seasons
#
# Seasons are named by the year they end in (2009 = the 2008-09 season). hoopR's play-by-play starts with 2006.
# Run it from the project folder. For each season it writes, in data/hoopr/<year>/:
#   play_by_play.csv.gz   every play ESPN has: clock, running score, text, play type, team, shot spot
#   schedule.csv.gz       every game: date, the two teams, the final score, neutral site or not
#   team_box.csv.gz       each team's line in each game
#   player_box.csv.gz     each player's line in each game
# A season already downloaded is skipped (delete its folder to fetch it again). ESPN does not have play-by-play for
# every game in these early seasons, mostly the smaller conferences; the summary at the end says how many it has.
# tools/hoopr_plays.py then turns the play-by-play into the files the dashboard reads.

args <- commandArgs(trailingOnly = TRUE)
seasons <- if (length(args)) as.integer(args) else 2006:2009
if (any(is.na(seasons))) stop("Name seasons by the year they end in, e.g. 2009 for 2008-09")

for (pkg in c("hoopR", "data.table", "R.utils")) {     # R.utils lets data.table read the .gz files back
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message("Installing ", pkg, " ...")
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}
suppressPackageStartupMessages({ library(hoopR); library(data.table) })

out_root <- file.path("data", "hoopr")
dir.create(out_root, showWarnings = FALSE, recursive = TRUE)

save_part <- function(fetch, path, label, year) {
  if (file.exists(path)) { message(sprintf("  %s: already saved", label)); return(invisible(NULL)) }
  d <- tryCatch(fetch(year), error = function(e) { message(sprintf("  %s: failed (%s)", label, conditionMessage(e))); NULL })
  if (is.null(d) || !nrow(d)) { message(sprintf("  %s: nothing for %d", label, year)); return(invisible(NULL)) }
  d <- as.data.table(d)
  # list columns (nested ESPN fields) cannot go in a CSV
  keep <- names(d)[!vapply(d, is.list, logical(1))]
  fwrite(d[, ..keep], path)
  message(sprintf("  %s: %s rows", label, format(nrow(d), big.mark = ",")))
  invisible(d)
}

summary_rows <- list()
for (year in seasons) {
  message(sprintf("%d-%02d season (%d):", year - 1, year %% 100, year))
  dir <- file.path(out_root, year)
  dir.create(dir, showWarnings = FALSE)
  save_part(function(y) load_mbb_schedule(seasons = y), file.path(dir, "schedule.csv.gz"), "schedule", year)
  save_part(function(y) load_mbb_team_box(seasons = y), file.path(dir, "team_box.csv.gz"), "team box scores", year)
  save_part(function(y) load_mbb_player_box(seasons = y), file.path(dir, "player_box.csv.gz"), "player box scores", year)
  save_part(function(y) load_mbb_pbp(seasons = y), file.path(dir, "play_by_play.csv.gz"), "play-by-play", year)
  pbp_path <- file.path(dir, "play_by_play.csv.gz"); sch_path <- file.path(dir, "schedule.csv.gz")
  n_games <- if (file.exists(sch_path)) uniqueN(fread(sch_path, select = "id")$id) else NA
  n_pbp <- if (file.exists(pbp_path)) uniqueN(fread(pbp_path, select = "game_id")$game_id) else 0
  summary_rows[[length(summary_rows) + 1]] <- data.table(season = sprintf("%d-%02d", year - 1, year %% 100),
                                                         games_on_schedule = n_games, games_with_play_by_play = n_pbp)
}
message("\nSummary:")
print(rbindlist(summary_rows))
