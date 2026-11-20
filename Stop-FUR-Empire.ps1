$ErrorActionPreference = 'Stop'
$expectedPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$listener = @(Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $listener) {
    Write-Host 'FUR Empire läuft nicht auf Port 8080.'
    exit 0
}
$serverProcessId = $listener[0].OwningProcess
$serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $serverProcessId"
if ($serverProcess -and $serverProcess.CommandLine.Contains($expectedPython) -and $serverProcess.CommandLine.Contains('fur_empire.api:app')) {
    Stop-Process -Id $serverProcessId
    Write-Host 'FUR Empire gestoppt. Der Spielstand bleibt gespeichert.'
} else {
    Write-Host 'Auf Port 8080 läuft kein eindeutig erkanntes FUR-Empire-Programm. Andere Prozesse bleiben unverändert.'
}
