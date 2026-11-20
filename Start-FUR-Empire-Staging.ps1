$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$envFile = Join-Path $PSScriptRoot '.env.staging'
$template = Join-Path $PSScriptRoot '.env.staging.example'
if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item -LiteralPath $template -Destination $envFile
}

$secretDirectory = Join-Path $PSScriptRoot '.secrets'
New-Item -ItemType Directory -Path $secretDirectory -Force | Out-Null
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    foreach ($name in @('staging_db_password', 'staging_db_admin_password', 'staging_smtp_password')) {
        $path = Join-Path $secretDirectory $name
        if (-not (Test-Path -LiteralPath $path)) {
            $bytes = New-Object byte[] 32
            $rng.GetBytes($bytes)
            $value = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
            try {
                $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
                try {
                    $writer = New-Object IO.StreamWriter($stream, [Text.UTF8Encoding]::new($false))
                    try { $writer.Write($value) } finally { $writer.Dispose() }
                } finally { $stream.Dispose() }
            } catch [IO.IOException] {
                if (-not (Test-Path -LiteralPath $path)) { throw }
            }
        }
    }
} finally {
    $rng.Dispose()
}

$stagingPushKey = Join-Path $secretDirectory 'staging_webpush_private_key'
if (-not (Test-Path -LiteralPath $stagingPushKey)) {
    New-Item -ItemType File -Path $stagingPushKey -Force | Out-Null
}

docker compose --project-name fur-staging --env-file $envFile --file compose.yaml --file compose.staging.yaml --profile staging up --build --detach --wait db app worker mailpit staging-proxy
if ($LASTEXITCODE -ne 0) { throw 'Der private Staging-Stack konnte nicht gestartet werden.' }

docker compose --project-name fur-staging --env-file $envFile --file compose.yaml --file compose.staging.yaml --profile staging exec --no-TTY app python -m fur_empire.manage seed-staging-demo --accounts 3
if ($LASTEXITCODE -ne 0) { throw 'Die einmaligen Staging-Testdaten konnten nicht initialisiert werden.' }

Write-Host 'Privates Staging läuft ausschließlich auf diesem PC:'
Write-Host 'Spiel: https://localhost:8443'
Write-Host 'Lokaler Mailcatcher: http://127.0.0.1:8025'
Write-Host 'Staging-Daten bleiben im separaten fur-staging-PostgreSQL-Volume erhalten.'
Write-Host 'Stoppen ohne Datenverlust: .\Stop-FUR-Empire-Staging.ps1'
