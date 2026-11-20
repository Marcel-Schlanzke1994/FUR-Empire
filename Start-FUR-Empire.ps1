$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 oder neuer muss installiert sein.' }
}
& $python -c 'import fastapi, uvicorn, argon2' 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installation fehlgeschlagen. Internetverbindung prüfen.' }
}
$url = 'http://127.0.0.1:8080'
try {
    $health = Invoke-RestMethod "$url/api/v1/health" -TimeoutSec 2
    if ($health.status -eq 'ok') { Start-Process $url; exit 0 }
} catch { Write-Host 'Starte lokale Spielwelt ...' }
$browserJob = Start-Job -ScriptBlock {
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8080/api/v1/health' -TimeoutSec 1
            if ($health.status -eq 'ok') { Start-Process 'http://127.0.0.1:8080'; return }
        } catch { Start-Sleep -Milliseconds 500 }
    }
}
Write-Host 'FUR EMPIRE läuft unter http://127.0.0.1:8080'
Write-Host 'Dieses Fenster offen lassen. Mit Strg+C den Server stoppen.'
& $python -m uvicorn fur_empire.api:app --host 127.0.0.1 --port 8080
$serverExitCode = $LASTEXITCODE
Stop-Job $browserJob -ErrorAction SilentlyContinue
Remove-Job $browserJob -Force -ErrorAction SilentlyContinue
exit $serverExitCode
