# FUR Empire development-system state

Last verified: 2026-11-20 (Europe/Berlin).

The product source is the root Python/FastAPI application. Reference repositories below
`Neuer Ordner/` are excluded from runtime and version control. Production runs on the netcup
Debian 13 host at `62.83.116.160` under `/opt/fur-empire` using PostgreSQL 18, separate app and
worker containers, Caddy and a backup scheduler. The application and worker were healthy during
the audit; strict readiness remains false only because administrator MFA is not yet verified.

The development runner lives in `development_runner/`. It uses a WAL-mode SQLite database for
tasks, dependencies, approvals, sessions, attempts, test evidence and commit references. The first
deployment supports exactly one coding worker. Production source and player data are not writable
by that worker.

Authoritative project truth remains, in order: repository source, automated tests, verified live
state, then documentation. See the existing architecture in `docs/architecture/ARCHITECTURE.md`,
game contract in `docs/game-design/FUR_EMPIRE_SPEC.md`, implementation matrix in
`docs/implementation/IMPLEMENTATION_MATRIX.md`, and chronological evidence in `PROGRESS_LOG.md`.
