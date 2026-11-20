# FUR Empire server operations

Host 62.83.116.160 runs Debian 13 with 8 CPUs, 16 GB RAM and a 314 GB root filesystem. Application directory is /opt/fur-empire.

## Access
Use furdeploy with the dedicated ED25519 key and verified known-hosts file on the development computer. Passwordless sudo is available. SSH password authentication is disabled. Root key access is retained.

## Services and inspection
```sh
cd /opt/fur-empire
sudo docker compose ps
sudo sh deploy/monitor.sh
sudo docker compose exec -T app python -m fur_empire.manage readiness
sudo journalctl -u fur-monitor.service -n 30
sudo docker compose logs --tail 50 app worker proxy
```
Strict readiness additionally requires a verified administrator with MFA. It currently fails that requirement.

## Backups
Daily backup-scheduler creates PostgreSQL custom-format dumps under backups and records completion in backup_status.
```sh
sudo docker compose --profile ops run --rm backup
```
Initial schema and imported-player restore drills succeeded in separate databases. A manual off-host copy exists on the development computer. Automated external replication and retention enforcement remain pending. Monitor disk usage.

## Recovery
See deploy/ROLLBACK.md. Restore to a new database and validate compatibility before switching. Preserve source and failed database. Never automatically reverse migrations.

## Network
Public listeners are SSH 22 and Caddy 80/443. App binds to 127.0.0.1:8081. PostgreSQL has no published port. SMTP submission binds to Docker bridge and loopback and requires TLS plus SASL authentication.
UFW permits public TCP 22/80/443 and submission only from backend subnet to its gateway. Provider netcup Mail block remains active pending explicit confirmation.

## Mail
Postfix and OpenDKIM are installed. Public SPF, DKIM and DMARC were submitted. DKIM lookup passes. Internal test-mail delivery and application TLS authentication pass. External delivery is blocked by the provider SMTP policy and remains unverified.
Caddy certificates are checked hourly by fur-mail-tls.timer. Certificate changes reload Postfix. Mail credentials remain in .secrets only.

## Monitoring and limits
fur-monitor.timer checks every five minutes and records results in journald. It checks HTTP readiness, worker heartbeat, PostgreSQL, backup age and disk usage and reports container resources. External alerts are pending.
App and worker each have 1 GiB/2 CPU/256 PID limits, PostgreSQL 2 GiB/2 CPU/256 PID and Caddy 256 MiB/1 CPU/128 PID. Docker logs rotate at 10 MB with three files.
All containers use restart policies. A controlled full host reboot confirmed automatic service recovery.

## Updates
Transfer reviewed source while preserving .env, .secrets, backups and volumes. Run sudo sh /opt/fur-empire/deploy/release.sh. The process has completed successfully several times. Application-only rollback is documented but still awaits rehearsal.

## Local-to-production deployment and retention
Deploy-FUR-Empire.ps1 completed successfully, including SSH transfer, pre-update source archive, database backup, build, migration and healthy services.
Backup retention now keeps every dump from the last 30 days and at least ten additional older archives. Only regular files matching the FUR timestamp naming pattern are candidates, and pg_restore --list must validate each candidate before removal. Current archives are recent, so none were removed during the initial successful run. Scheduler was recreated to bind the updated script.
Testkommando was promoted to administrator after explicit owner selection. Email verification and MFA remain pending.

## Monitoring coverage
monitor.sh now explicitly requires app, worker, database, proxy and backup-scheduler containers to exist and be running. It also records restart counts. Initial normal-state run passed. A controlled stopped-scheduler detection drill is in progress with automatic scheduler restart on exit.

Owner supplied responsible operator as Talent Link Ltd & Co. KG, currently in formation. Production operator name updated to Talent Link Ltd & Co. KG (in Gründung). Public company address and designated company contact remain unspecified.
