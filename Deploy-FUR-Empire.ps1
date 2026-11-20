[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$furIdentity = Join-Path $env:USERPROFILE '.ssh/fur-empire-netcup-ed25519'
$furKnown = Join-Path $env:USERPROFILE '.ssh/fur-empire-known-hosts'
$furArchive = Join-Path $PSScriptRoot 'build-artifacts/fur-production-source.tar.gz'
$furOptions = @('-i', $furIdentity, '-o', "UserKnownHostsFile=$furKnown", '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes')
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force build-artifacts | Out-Null
    & tar -czf $furArchive --exclude=__pycache__ --exclude=*.pyc Dockerfile requirements.lock fur_empire static deploy compose.yaml .dockerignore
    if ($LASTEXITCODE -ne 0) { throw 'Source packaging failed.' }
    & scp @furOptions $furArchive 'furdeploy@62.83.116.160:/home/furdeploy/fur-production-source.tar.gz'
    if ($LASTEXITCODE -ne 0) { throw 'Source transfer failed.' }
    $furRemote = @'
set -eu
cd /opt/fur-empire
exec 8>/run/lock/fur-empire-source.lock
flock -n 8
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p releases
tar -czf "releases/source-before-$stamp.tar.gz" Dockerfile requirements.lock fur_empire static deploy compose.yaml .dockerignore
tar -xzf /home/furdeploy/fur-production-source.tar.gz
sh deploy/release.sh
'@
    $furRemote | & ssh @furOptions 'furdeploy@62.83.116.160' 'tr -d "\r" | sudo sh'
    if ($LASTEXITCODE -ne 0) { throw 'Deployment failed. Inspect preserved release state on the VPS.' }
} finally {
    Pop-Location
}
