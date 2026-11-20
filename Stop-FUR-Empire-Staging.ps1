$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

docker compose --project-name fur-staging --env-file .env.staging --file compose.yaml --file compose.staging.yaml --profile staging down
if ($LASTEXITCODE -ne 0) { throw 'Der private Staging-Stack konnte nicht gestoppt werden.' }
Write-Host 'Staging-Container gestoppt; PostgreSQL- und Caddy-Volumes bleiben erhalten.'
