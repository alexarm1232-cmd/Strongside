# Waits for 6playbyplay.py to finish, then runs the rest of the 2024-25 collection scripts one after another.
# Everything each script prints goes to overnight_log.txt in this folder.
#   6 (already running)  ->  7  ->  8xtest, 8, 8xtest, and 8 again for as long as it keeps fixing games  ->  9  ->  10  ->  11  ->  7 again
param([int]$WaitForProcess = 0)

$root = Split-Path -Parent $PSScriptRoot
$codes = $PSScriptRoot
$log = Join-Path $codes "overnight_log.txt"
$MaxPassesOf8 = 6       # 8srboxscores.py is tried again this many times at most
Set-Location $root

function Note($text) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $text" | Out-File -FilePath $log -Append -Encoding utf8 }
function Run($step) {
    Note "START $step"
    $started = Get-Date
    & python -u (Join-Path $codes $step) *>> $log
    Note "END   $step  (exit code $LASTEXITCODE, $([int]((Get-Date) - $started).TotalMinutes) minutes)"
}
# Runs 8xtest.py and returns how many games still have a problem (teams it has not reached count as problems too)
function Check8 {
    Note "START 8xtest.py"
    $out = & python -u (Join-Path $codes "8xtest.py") 2>&1 | ForEach-Object { "$_" }
    $out | Out-File -FilePath $log -Append -Encoding utf8
    $problems = 0; $waiting = 0
    foreach ($line in $out) {
        if ($line -match '^Problem games: (\d+)') { $problems = [int]$Matches[1] }
        if ($line -match '^Teams not started yet: (\d+)') { $waiting = [int]$Matches[1] }
    }
    Note "END   8xtest.py  ($problems problem games, $waiting teams not started)"
    return $problems + 40 * $waiting
}

Note "Waiting for 6playbyplay.py to finish."
while ($true) {
    $running = Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'py*' -and $_.CommandLine -like '*2425*6playbyplay*' }
    if (-not $running -and -not ($WaitForProcess -and (Get-Process -Id $WaitForProcess -ErrorAction SilentlyContinue))) { break }
    Start-Sleep -Seconds 30
}
Note "6playbyplay.py is done."

Run "7rostertrim.py"

# 8, checked before and after, and repeated while a pass still fixes something (a game that failed on a timeout
# is picked up by the next pass; one the site does not have never will be)
$left = Check8
for ($pass = 1; $pass -le $MaxPassesOf8; $pass++) {
    Run "8srboxscores.py"
    $now = Check8
    Note "8srboxscores.py pass ${pass}: $left -> $now problems"
    if ($now -ge $left -or $now -eq 0) { $left = $now; break }
    $left = $now
}

foreach ($step in "9espnshots.py", "10cbbdplays.py", "11espnodds.py", "7rostertrim.py") { Run $step }
Note "ALL DONE"
