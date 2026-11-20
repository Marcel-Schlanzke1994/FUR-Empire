

## 2026-11-08 — ENG-016 admin audit pagination

The admin dashboard previously showed only the latest 100 audit records with no path to older entries. It now loads 50 records initially and provides an accessible older-page button backed by a current-role-checked, rate-limited keyset endpoint. Cursors are validated by audit row and use stable `(created,id)` ordering. The API returns only fields the view renders (`id`, `action`, `target`, `created`), excluding actor and details.

Full local SQLite suite: **268 passed, 145 skipped, one existing Starlette/httpx warning (481.77s)**. Focused SQLite API/domain cases: **2 passed, 1 optional PostgreSQL parameterization skipped**; domain cursor test on disposable PostgreSQL 18.6: **2 passed** (SQLite + PostgreSQL); frontend **54 passed**. Ruff/Black/mypy, ESLint, JavaScript syntax and 344-ID traceability pass. Test PostgreSQL container removed; persistent Main/Staging data and runtime unchanged. ENG-016 remains partial; not a release candidate.


## 2026-11-08 — ENG-016 public diplomacy chronicle pagination

The public alliance diplomacy chronicle had a fixed 100-event cap with no way to reach older immutable events. The state response now carries the newest 50 entries; an accessible load-more control retrieves stable `(created,id)` keyset pages from an authenticated, rate-limited endpoint. Cursor IDs are validated; alliances, tags, and event types remain unchanged.

Full local SQLite suite: **269 passed, 145 skipped, one existing Starlette/httpx warning (533.24s)**. Focused SQLite diplomacy/API tests: **2 passed, 1 optional PostgreSQL parameterization skipped**; disposable PostgreSQL 18.6 + SQLite adapter pair: **2 passed**. Frontend **54 passed**; Ruff, Black, strict mypy, ESLint, JavaScript syntax and 344-ID traceability pass. Temporary PG removed; persistent Main/Staging unchanged. ENG-016 remains partial; not a release candidate.


## 2026-11-08 — ENG-016 live-event state pagination

Active live events could grow without a cap because administrators may schedule arbitrary overlapping events. State responses now include up to 50 newest active events and an authenticated, rate-limited keyset endpoint loads older active entries. Schema 26 adds the event-feed index. The displayed-page limit does not affect gameplay: production bonus is aggregated over every currently active event in SQL; expired events remain excluded.

Full SQLite pytest: **271 passed, 146 skipped, one existing Starlette/httpx warning (513.70s)**. Focused live-event API/domain tests passed on SQLite; disposable PostgreSQL 18.6 + SQLite adapter pair **2 passed**. Frontend **55 passed**; Ruff, Black (21 files), strict mypy (16 source files), ESLint, JavaScript syntax and 344-ID traceability pass. Temporary PG removed; Main/Staging and player data unchanged. ENG-016 remains partial; not a release candidate.


## 2026-11-08 — ENG-016 account session inventory pagination

The Kontosicherheit endpoint now returns at most 50 live sessions and has owner-scoped keyset pagination by creation time and opaque session ID. Cursor lookup requires the authenticated owner; response objects still omit token and CSRF values. Device-specific and bulk session revocation remain intact. Schema 27 adds a `(user_id,created,session_id,expires)` feed index. Legacy schema-16 upgrade simulations now remove this newer index before dropping historical columns, accurately representing their old layout.

Full SQLite pytest: **273 passed, 147 skipped, one existing Starlette/httpx warning (525.17s)**. Focused SQLite session API/upgrade/index coverage passed; disposable PostgreSQL 18.6 + SQLite migration/index matrix **4 passed**. Frontend **55 passed**; Ruff, Black (21 files), strict mypy (16 source files), ESLint, JavaScript syntax and 344-ID traceability pass. Temporary PG removed; persistent services/data unchanged. ENG-016 remains partial; no release claim.

## 2026-11-08 — ENG-016 paginated alliance relationship state

Removed the unbounded diplomacy-relations array from the main state response. Alliance directory rows now carry their relationship status within the existing 50-row keyset page, and the UI reads each row's status. This keeps the directory's negotiation controls while avoiding a second full-table response.

Verification: full local SQLite pytest **273 passed, 147 skipped, one existing Starlette/httpx warning (517.31s)**. Focused SQLite + disposable PostgreSQL 18.6 diplomacy-domain case passed. Frontend **55 passed**; Ruff, Black check, strict mypy, ESLint, JavaScript syntax and 344-ID traceability pass. Test container removed; persistent Main/Staging and player data unchanged. ENG-016 remains partial; no release readiness is claimed.

## 2026-11-08 — ENG-016 private map-note pagination

Private notes are now returned in 50-row keyset pages ordered by `(updated DESC,id ASC)`. The cursor is validated for the signed-in owner and active world. The authenticated `/api/v1/notes` endpoint and accessible “Weitere Notizen laden” control retain access to older notes; state responses no longer grow with every saved note.

Verification: full local SQLite pytest **274 passed, 148 skipped, one existing Starlette/httpx warning (642.35s)**. Focused SQLite + disposable PostgreSQL 18 notes cursor cases **2 passed**; the temporary PostgreSQL container and test database were removed. Frontend **55 passed**; Ruff, Black check, strict mypy, ESLint, JavaScript syntax and 344-ID traceability pass. Main/Staging, persistent databases and player data unchanged. ENG-016 remains partial; no release readiness is claimed.

Cross-database CI-style verification follow-up: complete pytest suite with SQLite and disposable PostgreSQL 18.6 adapters **421 passed, 1 intentionally skipped, one existing Starlette/httpx deprecation warning (2465.91s, exit 0)**. This includes the private-note cursor on both adapters. Temporary PostgreSQL container removed; persistent Main/Staging services, volumes and player data were not touched.

## 2026-11-08 — ENG-016 vacation eligibility avoids global colony scan

Vacation activation now checks queued jobs only in the requesting player’s colonies and tests inbound operations through the maintained `incoming_attack_index`. This preserves the existing account-wide, cross-world guard while avoiding JSON parsing for every other player’s colonies.

Verification: focused SQLite + disposable PostgreSQL 18.6 vacation/index regression **2 passed**. Full SQLite pytest after the change: **274 passed, 148 skipped, one existing Starlette/httpx warning (497.28s)**. Ruff, Black check, strict mypy, frontend 55, ESLint, JavaScript syntax and 344-ID traceability pass. The prior full SQLite/PostgreSQL 18.6 CI-style run was **421 passed, 1 intentionally skipped (2465.91s)** before this follow-up. Temporary PostgreSQL containers removed; Main/Staging and player data untouched. ENG-016 remains partial.

## 2026-11-08 — ENG-016 indexed colony-name lookup (schema 28)

Added `colonies.name_key` with a `(name_key)` index and migration backfill from current display names. Existing colony state JSON is unchanged, including legitimate duplicate default names across worlds. Name changes, map colonization and outpost conversion now use the indexed global collision lookup rather than parsing every colony state. Ordinary colony saves maintain the normalized key.

Verification: full SQLite pytest **275 passed, 149 skipped, one existing Starlette/httpx warning (501.92s)**. Full SQLite/PostgreSQL 18.6 CI-style suite **423 passed, 1 intentional skip, one existing warning (2330.32s, exit 0)**. Focused name-index migration, case-insensitive global rename and colonization adapter matrix **8 passed**. Ruff, Black (25 files), strict mypy (16 files), frontend 55, ESLint, JavaScript syntax and 344-ID traceability pass. Disposable PostgreSQL removed; Main/Staging and player data untouched. ENG-016 remains partial; no release readiness is claimed.

## 2026-11-08 — Private Staging schema-28 rollout

Before rollout, created and validated the custom-format backup `backups/fur-staging-pre-schema28-20261108.dump`. Rebuilt/recreated only the Staging app and worker (`--no-deps`); Main, Staging PostgreSQL/volume, Mailpit and proxy were not recreated. Staging now reports schema 28 and the `colonies_name_key` index; app and worker are healthy, health returns 200, readiness is `ready=true`, and the database still contains 5 users and 5 colonies.

The pre-rollout archive restored successfully in an isolated PostgreSQL 18 container. User/profile core, world, 104 outposts, 4096 terrain cells, and colony identity/name/world/coordinate digests match the live Staging database. The full colony-state digest differs because the worker continued normal resource/job progression during the comparison. Restore-check containers were removed. Staging remains loopback-only at https://localhost:8443; Main and public production were not changed.


## 2026-11-08 — ENG-016 paginated world and colony directories

The main state now returns at most 50 worlds and 50 owned colonies. Authenticated keyset endpoints load later entries, validate cursors against existing worlds or the signed-in owner, and return only the fields required by the selector. The accessible Imperium screen adds load-more controls. Colony slot count now correctly counts the active world only, matching the server-enforced per-world slot limit. The 24-hour commander-name cooldown the owner confirmed is already enforced transactionally, shown in the account UI, and covered at the exact 24-hour boundary.

Verification: full SQLite suite **277 passed, 150 skipped, one existing Starlette/httpx deprecation warning (480.92s)**. Focused SQLite + disposable PostgreSQL 18 colony cursor regression **2 passed**; world-directory API test passed. Frontend **56 passed**; Ruff, Black check (5 changed files), strict mypy (16 source files), ESLint, JavaScript syntax, staging Compose validation and 344-ID traceability passed. Private Staging backup `backups/fur-staging-pre-empire-pagination-20261108.dump` (**227,052 bytes**) passed `pg_restore --list`; rebuilt/recreated only Staging app and worker. Health 200, readiness true, served JS contains both pagination controls, schema remains 28, users/colonies remain 5/5. Main, Staging DB/volume, Mailpit and proxy were not recreated. ENG-016 remains partial; no public production readiness is claimed.


Follow-up within the 2026-11-08 ENG-016 directory package: gameplay retains the full active-world colony list (rule cap four; defensive query cap five) for map markers and same-world supply, while `empire_colonies` carries the bounded 50-row cross-world directory. The two-world join/switch regression confirms exact active-world counts and complete directory entries on SQLite and PostgreSQL 18 (4 executions passed). Final full SQLite suite after this separation: **277 passed, 150 skipped, one existing warning (492.55s)**. Frontend 56; all Python/UI/traceability gates pass. Final private Staging app/worker are healthy and ready; served app.js contains both load-more controls; schema 28 and 5 users/5 colonies remain.
