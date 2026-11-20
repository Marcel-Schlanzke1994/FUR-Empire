#!/bin/sh
set -eu
cd /opt/fur-empire
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8081/api/v1/ready
docker compose exec -T worker python -m fur_empire.manage check-worker
docker compose exec -T db pg_isready -U fur -d fur
docker compose exec -T db psql -U postgres -d fur -Atc "SELECT CASE WHEN completed_at > extract(epoch from now())-90000 THEN 'backup_recent' ELSE 'backup_stale' END FROM backup_status WHERE id=1" | grep -qx backup_recent
df -P / | awk 'NR==2 {if ($5+0 > 85) exit 1}'
for service in app worker db proxy backup-scheduler; do
    container=$(docker compose --profile public --profile ops ps -q "$service")
    test -n "$container"
    test "$(docker inspect --format '{{.State.Running}}' "$container")" = true
    docker inspect --format '{{.Name}} restarts={{.RestartCount}}' "$container"
done
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}'
docker compose ps --format json
