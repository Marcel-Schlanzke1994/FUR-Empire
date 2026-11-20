#!/bin/sh
set -eu
umask 077
password_file="${DB_PASSWORD_FILE:-/run/secrets/db_password}"
export PGPASSWORD="$(cat "${password_file}")"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="/backups/fur-${stamp}.dump"
partial="${target}.partial"
cleanup() {
  if [ -n "${partial}" ]; then
    rm -f "${partial}"
  fi
}
trap cleanup EXIT
pg_dump --format=custom --file="${partial}"
pg_restore --list "${partial}" >/dev/null
mv "${partial}" "${target}"
partial=""
completed_at="$(date -u +%s)"
case "${completed_at}" in
  ''|*[!0-9]*) echo "Invalid UTC backup completion time." >&2; exit 1 ;;
esac
printf 'INSERT INTO backup_status (id, completed_at) VALUES (1, %s) ON CONFLICT (id) DO UPDATE SET completed_at=EXCLUDED.completed_at;\n' \
  "${completed_at}" | psql --no-psqlrc --set=ON_ERROR_STOP=1
printf 'Backup created: %s\n' "${target}"

# Retain at least ten old archives in addition to all backups from the last 30 days.
find /backups -maxdepth 1 -type f -name 'fur-????????T??????Z.dump' -mtime +30 | sort -r |
(
    retained=0
    while IFS= read -r archive; do
        retained=$((retained + 1))
        if [ "$retained" -le 10 ]; then
            continue
        fi
        pg_restore --list "$archive" >/dev/null
        rm -- "$archive"
    done
)
