#!/bin/sh
set -eu

interval="${BACKUP_INTERVAL_SECONDS:-86400}"
case "${interval}" in
  ''|*[!0-9]*) echo "BACKUP_INTERVAL_SECONDS must be an integer." >&2; exit 2 ;;
esac
if [ "${#interval}" -gt 7 ]; then
  echo "BACKUP_INTERVAL_SECONDS must be between 3600 and 2592000." >&2
  exit 2
fi
if [ "${interval}" -lt 3600 ] || [ "${interval}" -gt 2592000 ]; then
  echo "BACKUP_INTERVAL_SECONDS must be between 3600 and 2592000." >&2
  exit 2
fi

while :; do
  /bin/sh /scripts/backup.sh
  sleep "${interval}"
done
