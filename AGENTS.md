# FUR Empire contributor guide

FUR Empire is the main application in this workspace. The reference repositories are stored under `Neuer Ordner/` and must not be treated as the product source or executed as FUR runtime dependencies. In particular, the Laravel project inside `Neuer Ordner/OGameX-main/` is a code and architecture reference only. Never replace the root application with a reference repository.

## Project truth

- Read `README.md`, `docs/game-design/FUR_EMPIRE_SPEC.md`, and `docs/architecture/ARCHITECTURE.md` before changing gameplay or operational behavior.
- The root Python/FastAPI application is the game. SQLite is its local mode; Docker Compose, PostgreSQL, separate workers and Caddy describe the production stack.
- Preserve existing player data in `data/`. Tests must use temporary SQLite databases or an explicitly configured disposable PostgreSQL test database.
- Use only original FUR UI, game text, artwork, names, and rules. Do not copy reference assets, branding, or restricted source into the game. Keep source archive files intact.
- Check each reference repository's actual license before any direct code reuse. Prefer implementing mechanics independently from documented concepts.

## Implementation and verification

- Keep game rules authoritative on the server, transactionally consistent, idempotent, and covered by regression tests.
- Use parameterized SQL. Validate user-controlled data and escape it at HTML boundaries. Do not expose session secrets or account recovery material.
- Follow existing Python style and strict typing. After Python changes, run Ruff, Black check, strict mypy, and pytest. After UI changes, run ESLint, JavaScript syntax checks, and frontend tests.
- When relevant and available, run the PostgreSQL integration suite, `pip-audit`, and Docker Compose configuration/runtime checks from `.github/workflows/checks.yml`.
- Do not claim public production readiness based only on local tests. Describe unavailable external services and operational checks accurately.
- Do not run dependency upgrades or alter lockfiles unless explicitly required.

## Current scope

Genesis currently includes neutral-outpost progression, player combat and transport, alliances and diplomacy, messages, player market, seasonal events, moderation, account security, operations tooling, and local/production database support. Before describing a feature as missing or completed, confirm it in the current application and tests.

## Persistent development runner

- Automated work runs as the unprivileged `furdev` account in an isolated worktree. It must never
  write `/opt/fur-empire`, production databases, secrets, backups or player data.
- One worker is the default. Do not add parallel workers until measured queue latency and host
  capacity justify them and conflicting write protection is proven.
- The Development Director role selects dependency-ready backlog work and records assumptions.
  Coding and Game Systems roles implement only the selected task. QA & Security validates the
  resulting branch. DevOps prepares staging evidence; it does not release to production.
- Every automated code change uses an `agent/task-*` branch, passes configured local validation,
  and becomes a pull request. Required CI and human review remain mandatory.
- Destructive migrations, authentication/authorization changes, secrets, production access,
  financial behavior, data deletion and incompatible releases require an explicit approval record.
- Repository state and tests outrank runner memory. On restart, recover the queue and verify the
  checkout rather than assuming a previous session completed.
