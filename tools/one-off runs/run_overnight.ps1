# The overnight collection for 2023-24 only.
#   powershell -File run_overnight.ps1 sr      Sports Reference steps (rosters, box scores), then the dashboard build
#   powershell -File run_overnight.ps1 espn    ESPN shots and the CollegeBasketballData.com step (other sites, so they run alongside)
# Progress is written to overnight_log_2324.txt (Sports Reference steps and the dashboard build) and
# overnight_log_2324_shots.txt (shots and plays); each step's full output is in the logs\overnight folder.
# Nothing is started after 3 PM, and anything still running then is stopped (every script picks up where it left off).
param([string]$Chain = 'sr')
Set-Location 'C:\Users\crtra\Downloads\basketball'
$env:PYTHONIOENCODING = 'utf-8'
$deadline = Get-Date '2026-10-13 15:00'
# each chain keeps its own log, so the two never write to one file at the same moment
$log = 'C:\Users\crtra\Downloads\basketball\logs\overnight_log_2324.txt'
if ($Chain -ne 'sr') { $log = 'C:\Users\crtra\Downloads\basketball\logs\overnight_log_2324_shots.txt' }
New-Item -ItemType Directory -Force logs\overnight | Out-Null

function Note($text) {
    $line = ("[{0}] {1}" -f (Get-Date -Format 'ddd HH:mm'), $text) + "`r`n"
    for ($n = 0; $n -lt 5; $n++) {
        try { [System.IO.File]::AppendAllText($log, $line); return } catch { Start-Sleep -Seconds 2 }
    }
}

function RunStep($label, $arguments) {
    for ($try = 1; $try -le 5; $try++) {
        if ((Get-Date) -ge $deadline) { Note "not started: $label (it is past 3 PM)"; return $false }
        $out = "logs\overnight\$label.txt"
        if ($try -gt 1) { $out = "logs\overnight\$label.try$try.txt" }
        Note "start $label"
        $process = Start-Process python -ArgumentList $arguments -RedirectStandardOutput $out -RedirectStandardError "$out.errors" -NoNewWindow -PassThru
        $wait = [int][math]::Max(1000, ($deadline - (Get-Date)).TotalMilliseconds)
        if (-not $process.WaitForExit($wait)) {
            $process.Kill()
            Note "STOPPED at 3 PM: $label (run it again to pick up where it left off)"
            return $false
        }
        Note ("end   $label :: " + ((Get-Content $out -Tail 4 -Encoding utf8) -join ' | '))
        if (Select-String -Path $out -Pattern 'refused the request' -Quiet) {
            Note 'Sports Reference refused a request; waiting 90 minutes before trying again'
            $pause = [int][math]::Min(5400, [math]::Max(1, ($deadline - (Get-Date)).TotalSeconds))
            Start-Sleep -Seconds $pause
        } else { return $true }
    }
    return $false
}

function WaitFor($flag) {
    while (-not (Test-Path $flag) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 60 }
    return (Test-Path $flag)
}

function SportsReference($code) {
    RunStep "${code}_5_rosters" "-u `"collect\$code\5rosterfetch.py`"" | Out-Null
    RunStep "${code}_8_boxscores" "-u `"collect\$code\8srboxscores.py`"" | Out-Null
    RunStep "${code}_8_boxscores_second_pass" "-u `"collect\$code\8srboxscores.py`"" | Out-Null
    RunStep "${code}_8xtest" "-u `"collect\$code\8xtest.py`"" | Out-Null
    RunStep "${code}_7_rostertrim" "-u `"collect\$code\7rostertrim.py`"" | Out-Null
    if (WaitFor "logs\overnight\espn_$code.done") {
        RunStep "${code}_dashboard_build" "-u dashboard\main.py $code quiet" | Out-Null
    } else { Note "$code dashboard not built: the shots were not finished" }
}

function Shots($code) {
    RunStep "${code}_9_espnshots" "-u `"collect\$code\9espnshots.py`"" | Out-Null
    RunStep "${code}_10_cbbdplays" "-u `"collect\$code\10cbbdplays.py`"" | Out-Null
    if (Test-Path "collect\$code\11cbbdsubs.py") {
        RunStep "${code}_11_cbbdsubs" "-u `"collect\$code\11cbbdsubs.py`"" | Out-Null
    }
    Set-Content "logs\overnight\espn_$code.done" 'done'
}

Note '===== started ====='
if ($Chain -eq 'sr') {
    $began = Get-Date
    SportsReference '2324'
    $took = (Get-Date) - $began
    Note ("===== 2023-24 finished; it took {0:N1} hours =====" -f $took.TotalHours)
    Note '2022-23 is not part of this run'
} else {
    Shots '2324'
    Note '===== 2023-24 shots and plays finished ====='
    while (-not (Test-Path 'logs\overnight\go_2223.flag') -and -not (Test-Path 'logs\overnight\stop_2223.flag') -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 60 }
    if (Test-Path 'logs\overnight\go_2223.flag') {
        Shots '2223'
        Note '===== 2022-23 shots and plays finished ====='
    }
}
Note '===== nothing more to run ====='
