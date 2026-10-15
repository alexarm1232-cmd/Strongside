# The 2023-24 token steps again, for all teams (the first pass only knew 26 teams' names). Logs beside the others.
Set-Location 'C:\Users\crtra\Downloads\basketball'
$env:PYTHONIOENCODING = 'utf-8'
$log = 'C:\Users\crtra\Downloads\basketball\logs\overnight_log_2324_shots.txt'
function Note($text) { [System.IO.File]::AppendAllText($log, ("[{0}] {1}" -f (Get-Date -Format 'ddd HH:mm'), $text) + "`r`n") }
foreach ($step in @(@('2324_10_cbbdplays_all_teams', '10cbbdplays.py'), @('2324_11_cbbdsubs_all_teams', '11cbbdsubs.py'))) {
    Note ("start " + $step[0])
    $out = "logs\overnight\" + $step[0] + ".txt"
    $process = Start-Process python -ArgumentList ("-u `"collect\2324\" + $step[1] + "`"") -RedirectStandardOutput $out -RedirectStandardError "$out.errors" -NoNewWindow -PassThru
    $process.WaitForExit()
    Note ("end   " + $step[0] + " :: " + ((Get-Content $out -Tail 4 -Encoding utf8) -join ' | '))
}
Note '===== 2023-24 shots and plays finished for all teams ====='
