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
