#!/bin/sh
set -eu
cd /opt/fur-empire
docker compose exec -T app python -m fur_empire.manage readiness
curl --fail --silent --show-error http://127.0.0.1:8081/api/v1/ready
docker compose ps
df -h /
docker stats --no-stream
