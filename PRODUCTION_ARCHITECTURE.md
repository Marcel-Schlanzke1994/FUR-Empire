# FUR Empire production architecture

Internet → netcup DNS → Caddy HTTPS → FastAPI application → PostgreSQL 18.
A separate Python worker advances authoritative game jobs and delivers outbox messages. No separate frontend build service is used. HTML, CSS and Vanilla JavaScript are served from the application image.

## Host and isolation
Debian 13 VPS at 62.83.116.160 with 8 CPUs and 16 GB RAM. Docker Compose services are app, worker, db, proxy and backup-scheduler.
App runs as UID 10001 with read-only root filesystem, dropped capabilities and no-new-privileges. Temporary writes use tmpfs. PostgreSQL data and Caddy certificate state use named persistent volumes.
PostgreSQL transactions use the existing advisory-lock serialization. Existing production mode requires PostgreSQL. SQLite source data was migrated from a preserved rehearsal copy.

## Traffic
Only Caddy exposes web traffic. App HTTP is bound to loopback 8081. Database has no published port. Caddy forwards trusted proxy headers from its fixed edge-network address. WWW redirects to the apex. Valid TLS certificates are issued and renewed by Caddy.
The application uses secure HttpOnly SameSite cookies, CSRF checks, rate limiting and existing server-side authorization.
SMTP uses Postfix on the host bridge with TLS and SASL. The SMTP gateway is currently tied to the existing Docker backend address. Fresh-host network discovery still needs implementation.

## Storage and restart
All application containers restart unless stopped. Docker is enabled at boot. A controlled full reboot passed.
Daily custom-format PostgreSQL dumps are stored in /opt/fur-empire/backups. Restore drills succeeded in isolated databases. One manual copy is on the development computer.
No upload storage dependency was identified during this deployment.

## Capacity and monitoring
App and worker each have 1 GiB RAM and 2 CPU limits. PostgreSQL has 2 GiB and 2 CPUs. Caddy has 256 MiB and 1 CPU.
Systemd timers check service readiness and backup age every five minutes and synchronize mail TLS state hourly. Docker logs rotate.
Measured idle usage was approximately 69 MiB app, 56 MiB worker and 84–89 MiB PostgreSQL. These measurements do not establish concurrent-player capacity.

## Remaining acceptance
External SMTP policy confirmation and delivery test, administrator MFA, full Python/PostgreSQL test completion, combat acceptance, rollback rehearsal, backup retention and automated off-host replication remain open.
