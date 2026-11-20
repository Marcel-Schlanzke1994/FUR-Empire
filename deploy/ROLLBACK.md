# Recovery and rollback

Run commands on the production host from /opt/fur-empire with sudo.

Before a release, deploy/release.sh saves the previous image ID under releases/ and tags the image fur-empire-app:before-UTC_TIMESTAMP. A PostgreSQL dump is created before migration.

For an application-only failure with a verified unchanged database schema, stop app and worker, retag the recorded previous image as fur-empire-app and fur-empire-worker, then run docker compose up -d --no-build --wait app worker and sh deploy/monitor.sh.

If a migration changed the schema, retain the failed state and stop application writes. Restore the selected dump into a NEW database first using createdb and pg_restore --exit-on-error. Validate player counts and application compatibility there before switching configuration. Preserve the failed database and all backups. Never automatically reverse migrations.

Restore drills have successfully restored the initial schema and imported-player dumps into separate databases. An application rollback rehearsal is still pending.

## Application rollback rehearsal
With database schema unchanged, stopped app/worker, switched to the pre-UI-change image, started both and confirmed readiness true. An EXIT handler restored the current image and both services passed healthchecks. A backup preceded the drill. No database downgrade was attempted.
Added Deploy-FUR-Empire.ps1 as the local source packaging/SSH transfer entry point. It preserves server source in releases before extraction and invokes release.sh. PowerShell syntax validation passed; a full invocation remains pending.
