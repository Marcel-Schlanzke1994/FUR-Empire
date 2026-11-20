#!/bin/sh
# Run from a verified, fully transferred source tree on the production host.
set -eu
cd /opt/fur-empire
exec 9>/run/lock/fur-empire-release.lock
flock -n 9
docker compose config --quiet
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p releases
docker image inspect fur-empire-app --format '{{.Id}}' > "releases/$stamp.previous-image"
docker tag fur-empire-app "fur-empire-app:before-$stamp"
docker compose --profile ops run --rm backup
docker compose build app
docker tag fur-empire-app fur-empire-worker
docker compose stop app worker
# On failure leave services stopped for inspection. Never downgrade schema automatically.
docker compose run --rm --no-deps app python -m fur_empire.manage migrate
docker compose up -d --no-build --wait app worker
sh deploy/monitor.sh
printf 'Release completed: %s
' "$stamp"
