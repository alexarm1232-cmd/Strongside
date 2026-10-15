# Runs a season's usual steps on its "full season" folder; they only fetch what the added postseason games need.
#   powershell -ExecutionPolicy Bypass -File run_postseason.ps1 2526 2324
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Seasons)
Set-Location 'C:\Users\crtra\Downloads\basketball'
$env:PYTHONIOENCODING = 'utf-8'
New-Item -ItemType Directory -Force logs\postseason | Out-Null
$log = 'C:\Users\crtra\Downloads\basketball\logs\postseason_log.txt'
function Note($text) { [System.IO.File]::AppendAllText($log, ("[{0}] {1}" -f (Get-Date -Format 'ddd HH:mm'), $text) + "`r`n") }
foreach ($code in $Seasons) {
    $codes = "collect\$code full"
    foreach ($script in '8srboxscores.py', '8srboxscores.py', '7rostertrim.py', '6playbyplay.py', '9espnshots.py', '10cbbdplays.py', '11cbbdsubs.py') {
        if (-not (Test-Path "$codes\$script")) { continue }
        if ($script -eq '11cbbdsubs.py' -and $code -eq '2526') { continue }
        $out = "logs\postseason\${code}_" + ($script -replace '\.py$', '') + ".txt"
        Note "start $code $script"
        $process = Start-Process python -ArgumentList "-u `"$codes\$script`"" -RedirectStandardOutput $out -RedirectStandardError "$out.errors" -NoNewWindow -PassThru
        $process.WaitForExit()
        Note ("end   $code $script :: " + ((Get-Content $out -Tail 4 -Encoding utf8) -join ' | '))
    }
    Note "===== $code finished ====="
}
Note '===== all done ====='
