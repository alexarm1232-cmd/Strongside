# Collects and builds earlier seasons, one after another, newest first.
#
#   powershell -ExecutionPolicy Bypass -File run_seasons.ps1 start 2122 2021 1920 1819
#       starts both chains in the background for those seasons and returns straight away
#   powershell -ExecutionPolicy Bypass -File run_seasons.ps1 stop
#       asks them to stop: each finishes the step it is on (or is stopped at once with "stop now")
#
# Two chains run side by side, because they use different sites:
#   sr     game list, rosters and box scores (Sports Reference: one page every few seconds, so one season at a time),
#          then the dashboard build for the season
#   plays  ESPN shots and the CollegeBasketballData.com steps; for 2014-15 to 2018-19 the Kaggle play-by-play instead
# Progress: seasons_log.txt (sr) and seasons_log_plays.txt (plays). Each step's full output: logs\seasons folder.
# Every script picks up where it left off, so a season that was interrupted can simply be named again.
param([string]$Chain = 'start', [Parameter(ValueFromRemainingArguments = $true)][string[]]$Seasons)
$root = 'C:\Users\crtra\Downloads\basketball'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$order = '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516', '1415', '1314', '1213', '1112', '1011', '0910'
$kaggle = '1819', '1718', '1617', '1516', '1415'      # seasons whose play-by-play comes from the Kaggle files
$stopFlag = "$root\logs\seasons\stop.flag"
New-Item -ItemType Directory -Force "$root\logs\seasons" | Out-Null

if ($Chain -eq 'stop') {
    Set-Content $stopFlag 'stop'
    if ($Seasons -contains 'now') {
        Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'powershell.exe' -and $_.CommandLine -like '*run_seasons.ps1*' -and $_.ProcessId -ne $PID) -or
            ($_.Name -like 'python*' -and ($_.CommandLine -like '*collect*' -or $_.CommandLine -like '*kaggle_plays*' -or $_.CommandLine -like '*main.py*')) } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        'Stopped.'
    } else { 'Asked to stop: each chain finishes the step it is on, then ends.' }
    return
}
if ($Chain -eq 'start') {
    $Seasons = @($Seasons | Where-Object { $order -contains $_ })
    if (-not $Seasons) { 'Name the seasons, e.g.  run_seasons.ps1 start 2122 2021     Known: ' + ($order -join ' '); return }
    if (Test-Path $stopFlag) { Remove-Item $stopFlag }
    foreach ($c in 'sr', 'plays') {
        Start-Process powershell -ArgumentList (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$root\run_seasons.ps1", $c) + $Seasons) -WindowStyle Hidden
    }
    'Started: ' + ($Seasons -join ', ') + '. Progress is in seasons_log.txt and seasons_log_plays.txt.'
    return
}

$log = "$root\logs\seasons_log.txt"
if ($Chain -ne 'sr') { $log = "$root\logs\seasons_log_plays.txt" }
function Note($text) {
    $line = ("[{0}] {1}" -f (Get-Date -Format 'ddd HH:mm'), $text) + "`r`n"
    for ($n = 0; $n -lt 5; $n++) { try { [System.IO.File]::AppendAllText($log, $line); return } catch { Start-Sleep -Seconds 2 } }
}
function Stopping { return (Test-Path $stopFlag) }

function RunStep($label, $arguments) {
    for ($try = 1; $try -le 5; $try++) {
        if (Stopping) { Note "not started: $label (asked to stop)"; return $false }
        $out = "logs\seasons\$label.txt"
        if ($try -gt 1) { $out = "logs\seasons\$label.try$try.txt" }
        Note "start $label"
        $process = Start-Process python -ArgumentList $arguments -RedirectStandardOutput $out -RedirectStandardError "$out.errors" -NoNewWindow -PassThru
        $process.WaitForExit()
        Note ("end   $label :: " + ((Get-Content $out -Tail 4 -Encoding utf8) -join ' | '))
        if (Select-String -Path $out -Pattern 'refused the request' -Quiet) {
            Note 'Sports Reference refused a request; waiting 90 minutes before trying again'
            for ($minute = 0; $minute -lt 90 -and -not (Stopping); $minute++) { Start-Sleep -Seconds 60 }
        } else { return $true }
    }
    return $false
}
function WaitFor($flag) {
    while (-not (Test-Path $flag) -and -not (Stopping)) { Start-Sleep -Seconds 60 }
    return (Test-Path $flag)
}

Note ('===== started: ' + ($Seasons -join ', ') + ' =====')
foreach ($code in $Seasons) {
    if (Stopping) { break }
    $codes = "collect\$code"
    if ($Chain -eq 'sr') {
        RunStep "${code}_2_gameupdate" "-u `"$codes\2gameupdate.py`"" | Out-Null
        RunStep "${code}_3_scores" "-u `"$codes\3scores.py`"" | Out-Null
        Set-Content "logs\seasons\games_$code.done" 'done'
        # the next season on already downloaded this season's rosters as its "last year"
        $at = [array]::IndexOf($order, $code)
        if ($at -gt 0 -and (Test-Path ("data\seasons\" + $order[$at - 1]))) {
            $year = 2000 + [int]$code.Substring(2, 2)
            RunStep "${code}_rosters_reused" ("-u tools\copy_rosters.py " + $order[$at - 1] + " $code $year") | Out-Null
        }
        RunStep "${code}_5_rosters" "-u `"$codes\5rosterfetch.py`"" | Out-Null
        RunStep "${code}_8_boxscores" "-u `"$codes\8srboxscores.py`"" | Out-Null
        RunStep "${code}_8_boxscores_second_pass" "-u `"$codes\8srboxscores.py`"" | Out-Null
        RunStep "${code}_8xtest" "-u `"$codes\8xtest.py`"" | Out-Null
        RunStep "${code}_7_rostertrim" "-u `"$codes\7rostertrim.py`"" | Out-Null
        if (WaitFor "logs\seasons\plays_$code.done") {
            RunStep "${code}_dashboard_build" "-u dashboard\main.py $code quiet" | Out-Null
        }
        Note "===== $code finished ====="
    } else {
        if (-not (WaitFor "logs\seasons\games_$code.done")) { break }
        if ($kaggle -contains $code) {
            RunStep "${code}_kaggle_plays" "-u tools\kaggle_plays.py $code" | Out-Null
        } else {
            RunStep "${code}_9_espnshots" "-u `"$codes\9espnshots.py`"" | Out-Null
            RunStep "${code}_10_cbbdplays" "-u `"$codes\10cbbdplays.py`"" | Out-Null
            if (Test-Path "$codes\11cbbdsubs.py") { RunStep "${code}_11_cbbdsubs" "-u `"$codes\11cbbdsubs.py`"" | Out-Null }
        }
        if (-not (Stopping)) { Set-Content "logs\seasons\plays_$code.done" 'done' }
        Note "===== $code shots and plays finished ====="
    }
}
Note '===== nothing more to run ====='
