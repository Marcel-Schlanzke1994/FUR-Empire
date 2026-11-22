# Terra development audit — 2026-11-22

## Scope and evidence

This is an audit of the local FUR Empire checkout and local SQLite mode. It is **not** a live VPS audit. The user-supplied plans and Delta Wars page are design references, not evidence of FUR runtime behavior. The active branch was `agent/task-complete-beta-integration` at `5f1740f`, with 25 modified tracked files and 12 untracked files before this audit. An isolated worktree at `build-artifacts/terra-director` contains a copy of that uncommitted source state. This review branch, `agent/task-terra-minimap`, was cut cleanly from `5f1740f` and contains only the new audit/minimap changes. The original checkout and `data/` were not edited.

## Verified local inventory

| Area | Finding | Evidence |
| --- | --- | --- |
| Runtime | Python/FastAPI API; separate game, systems and worker modules; static HTML/CSS/JavaScript | `fur_empire/api.py`, `game.py`, `systems.py`, `worker.py`, `static/` |
| Storage | SQLite local mode and PostgreSQL 18 Compose configuration | `fur_empire/database.py`, `compose.yaml` |
| Local player store | `data/empire.sqlite3`: 2,424,832 bytes, schema 124, one user and one colony; read-only `quick_check=ok` | SQLite read-only query on 2026-11-22 |
| Local schema/content | 146 SQLite tables, one world, 104 outposts and 4,096 terrain sectors | SQLite read-only aggregate queries |
| Map | Seeded 64×64 terrain, world-scoped outposts/colonies, per-observer fog, four-neighbor weighted path cost | `terrain.py`, `fog.py`, `game.py`, `test_terrain.py` |
| Simulation | Server-side commands and idempotency, due-time missions, one world write lock and worker processing | `game.py`, `database.py`, `worker.py` |
| Tests | 639 Python test functions matched by source search, 157 migration files, frontend tests and CI checks | `tests/`, `fur_empire/migrations/`, `.github/workflows/checks.yml` |
| Source surface | 261 files below `fur_empire/`; 66 FastAPI route decorators in `api.py` | file and decorator counts |
| Compose syntax | `docker compose config --quiet` succeeded; default services are `db`, `app`, `worker` | local Compose parser; no container start |
| Local services | No listeners on checked ports 8080, 8081, 8082, 8443 or 5432; Docker Desktop API unavailable | local port and `docker compose ps` read-only checks |

The source contains orbit modules and orbit UI, but the current directive limits new development to Terra. Existing code is not evidence that any feature is live or production-ready.

A read-only public GET of `https://fur-empire.de/api/v1/ready` returned HTTP 200 with `ready=true`, zero quarantined jobs and a reported scheduler lag of zero seconds on 2026-11-22. This proves only that the public readiness endpoint responded at that moment; it does not authenticate the deployed code, database schema, backup state or sustained worker health.

## Backup and restore drill

The local SQLite file was opened read-only and copied with SQLite's online backup API into an ignored private artifact directory. A second SQLite backup call restored it to a separate disposable file. Both copies returned `integrity_check=ok`, schema 124, one user and one colony. Backup size was 2,424,832 bytes and SHA-256 was `bd33f0f3f2912ae24b7c09e179f08995a4932d201d3765e6c3dd30157e172a66`. Neither backup nor restore targeted `data/`. The private files must not be committed, uploaded or treated as a production backup.

This proves a local SQLite restore path only. It does not prove an off-host backup, PostgreSQL restore, configuration/asset recovery, RPO/RTO, or the running beta's recoverability.

## Gates and risks

1. **BLOCKED — live source of truth:** batch SSH to `fur-empire.de` failed host-key verification. No bypass or production query was attempted. Verify the host key through an independent trusted channel before host access.
2. **BLOCKED — production restore:** Docker Desktop was unavailable locally, and there is no verified VPS access. PostgreSQL dumps, service topology, actual schema, disk capacity, worker lag and restore time remain unverified.
3. **IN_PROGRESS — local baseline:** the host Python environment cannot collect the full test suite because Starlette requests `httpx2`. The isolated environment now declares and installs it, and focused tests pass; the complete Python suite has not finished.
4. **Architecture risk:** a global write lock protects consistency but makes tick throughput and multiplayer scale an empirical question. No realistic load figure is available.
5. **Product risk:** current Terra missions resolve at arrival; they do not yet provide independently positioned, directly steerable unit groups with continuous combat and capture.

No production migration, deployment, service restart or feature enablement occurred.
