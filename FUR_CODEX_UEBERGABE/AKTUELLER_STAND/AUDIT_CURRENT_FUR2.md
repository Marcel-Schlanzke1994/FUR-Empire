# Current FUR-2 application audit

**Audit date:** 2026-11-06  
**Epic:** E00 — baseline  
**Truth source:** the root application in this workspace. `Neuer Ordner/` contains reference repositories only; they are not runtime dependencies and no source/assets were copied.

## Repository and source status

- The current product is the root Python/FastAPI game: `fur_empire/api.py`, `game.py`, `systems.py`, `identity.py`, `database.py`, and `worker.py`; the rule catalog is `fur_empire/rules/fur-2.json`; browser screens are in `static/`.
- Existing FUR-2 source is present and executable. The “code unavailable” branch of the supplied start prompt does not apply.
- No `.git` directory or Git remote exists in the workspace. A current Git status, safe feature branch, baseline tag, or history secret scan cannot be produced from this checkout. Repository metadata was not fabricated or initialized.
- The prompt's numbered package is not present as separate files: `00_START_HIER.md`, `agent/AGENTS.md`, `agent/BUILD_LOOP.md`, `docs/01..10_*.md`, `spec/FEATURES.json`, and `reference/*` are absent. The consolidated source is `agent/FUR_EMPIRE_GESAMTKONZEPT_UND_AGENT_ROADMAP.md`; `agent/FEATURE_INDEX.md` is the readable feature inventory and `agent/FUR_EMPIRE_FUR2_BACKLOG.json` is a separate historical gap comparison. `spec/FEATURES.json` and `TRACEABILITY.md` were reconstructed from the readable index and consolidated implementation order; provenance is explicit and no row is pre-verified.
- `agent/FEATURE_INDEX.md` parses to 344 unique IDs: 60 FUR-2 (`F2-*`), 55 original gap IDs (`W/K/E/A/P/T`), and 229 later expansion IDs. This inventory count is independently checked; it is not a completion count.

## Implemented FUR-2 surfaces found in source

| Area | Current evidence in code | Verification status |
|---|---|---|
| Accounts, sessions, CSRF, origin/host controls, recovery, TOTP | `fur_empire/api.py`, `fur_empire/identity.py`, `fur_empire/config.py` | Backend tests pass; each F2 row still needs one-to-one traceability mapping. |
| 64×64 world, 104 neutral posts, colony economy, build/research/training, quests | `fur_empire/game.py`, `fur_empire/rules/fur-2.json` | Backend tests pass; each F2 row still needs one-to-one traceability mapping. |
| Neutral missions, capture, transports, PvP, garrisons, resource ledger | `fur_empire/game.py`, `fur_empire/systems.py` | SQLite tests pass; isolated PostgreSQL multiplayer suite passes; exact row mapping remains open. |
| Alliances, diplomacy, chat, market, factions, events, seasons, moderation | `fur_empire/systems.py` | SQLite and isolated PostgreSQL tests pass; exact row mapping remains open. |
| SQLite, PostgreSQL, worker, backups, health/readiness, Docker stack | `fur_empire/database.py`, `fur_empire/manage.py`, `fur_empire/worker.py`, `compose.yaml` | Compose stack is healthy; backup files created; SQLite restore integrity is checked; isolated PG test suite passes. |
| Browser screens and authenticated command flow | `static/app.js`, `static/community.js`, `static/index.html` | ESLint, JavaScript syntax, 6 frontend tests pass. Browser/game screens still need accessibility/mobile acceptance per screen. |

## Baseline verification captured for E00

- Local suite: **47 passed, 19 skipped**. The skips are PostgreSQL parametrizations when `FUR_TEST_POSTGRES` is unset.
- Isolated PostgreSQL 18 multiplayer suite: **37 passed, 1 skipped** (SQLite-only backup scenario).
- Ruff, Black check, strict mypy, ESLint, JavaScript syntax, 6 frontend tests, and `docker compose config --quiet`: passed.
- After extending the CI workflow, the local frontend ESLint, syntax checks and 6 tests passed. Python and Node CycloneDX SBOM generation succeeded locally (21 Python and 87 Node components); `pip-audit` and `npm audit --audit-level=high` found no known vulnerabilities. The GitHub-hosted workflow itself has not run from this checkout.
- Docker app, worker, and PostgreSQL: healthy at audit start. App port remains loopback-only at `127.0.0.1:8081`; `/api/v1/health` and `/api/v1/ready` returned success.
- A local SQLite backup and a Docker PostgreSQL custom dump were created under `backups/agent-start-20261106/` and `backups/` respectively. SQLite backup integrity returned `ok`. The current PostgreSQL dump restored into a new disposable database; 25 tables, one world row, three users, and three colonies were present. The disposable database and temporary container copy were removed afterward.
- Prior checks in `docs/VERIFICATION.md` include a PostgreSQL restore drill, browser navigation, and read-only request smoke test. They do not satisfy the new prompt's multiworld, 2–10-account, two-world, 30-minute performance, or deterministic replay requirements.

## Feature reality and initial gaps

The current app is a playable FUR-2 Genesis game, not the proposed 344-feature Terra/Orbit product. The 60 FUR-2 rows are candidate existing functionality and must be individually mapped to source, migration, API, UI, policy, tests, and help before being called `verified`.

The supplied 55-item gap list and 229 expansion IDs include systems not found in the existing FUR-2 scope, such as multi-colony/multiworld, gameplay terrain and fog-of-war, a larger round-based role combat system, simulator, espionage, joint alliance attacks, NPC campaigns/world bosses, inventory/crafting, Orbit/space fleets and stations, and full localization/mobile acceptance. These remain unverified and are not to be represented as implemented based on roadmap text alone.

## E00 gate status

- **Complete:** project truth identified; root contributor instructions, game spec, and architecture read; 344 IDs counted and the explicitly reconstructed machine inventory/traceability created; existing player data preserved by separate backups; baseline tests run; original repositories left intact; source inventory recorded (9 reference repositories, 16,110 files); direct foreign code/assets are not part of the new FUR core.
- **Open:** no Git metadata means no safe branch/tag/diff/history scan; the split package inputs are missing; one-to-one FUR-2 evidence mapping and legal review of source licenses remain; mobile/accessibility and 30-minute performance gates are not run.
- **Migration rule:** keep the existing FUR-2 world and rows compatible. Any new world/multi-colony/Orbit model must be additive, explicitly versioned, tested on disposable databases, and must never convert or overwrite the live SQLite/PostgreSQL player data in-place without a verified restore path.



## E01 staging runtime update

The separate private staging project is now implemented and running for local validation. It uses its own `fur_staging` database/volume, app, worker, internal Mailpit and Caddy; published ports are loopback-only. HTTPS health/readiness, demo login, authenticated state/CSRF and one build mutation succeeded via the API. This is API-level smoke evidence, not browser E2E or production approval. Latest Python checks are recorded in `PROGRESS_LOG.md`; no F2 row is yet individually accepted.


## F2-001..F2-007 account security evidence

Authentication, registration controls, email verification gate, sessions, TOTP, recovery, and account security have now been mapped individually in `TRACEABILITY.md`. Regression coverage includes registration disabled while existing login works, session expiry/logout, TOTP replay prevention, expired recovery tokens, password reauthentication for email change, verified-email production gating, and production admin MFA policy. All seven remain `partial`; UI/browser and selected operational coverage is still outstanding. The suite after this addition passed 56 tests with 19 PostgreSQL cases skipped because `FUR_TEST_POSTGRES` is not configured.


## F2-008..F2-014 world and resource evidence

The map viewport uses shared 64/20 geometry constants and has a frontend regression covering four world edges, exactly 400 unique cells per viewport, and collective coverage of all 4,096 sectors. Server tests assert 104 unique in-bounds posts and the tier-8 Citadel, exact starting resources, each resource production formula with carry across polls, and delivery overflow plus partial reserve claims. These rows remain partial for the acceptance gaps recorded in `TRACEABILITY.md`.


## F2-015..F2-033 building and queue evidence

Regression coverage now includes capped reserve claims without losing unclaimed balances; all building costs/target-level scaling; headquarters speed, power and capture gate; level-10 cap and single build queue; research lab gate/queue/duration/cost; all three FUR-2 unit stats and barracks gates; training costs/time/queue/count range; tactics and logistics effects; and Warden wall defense. All rows remain partial because complete browser/operational and legacy-world acceptance is not established.

E05/W09 implementation update: the map now filters posts by name or coordinate, jumps to any valid coordinate in the 64×64 map, and stores up to 20 private per-player outpost favorites. Additive migration 004 and an SQLite pre-upgrade preservation rehearsal are covered. W09 remains partial pending browser and assistive-technology acceptance. The broader E05 one-world/one-colony model remains unchanged and unaudited for multiworld migration.

## F2-015..F2-034 current evidence

F2-034 is partial. Its directive predicates and reward amounts are in `Game.quests`; claims are one-time, and resource overflow now goes into the reserve. Regression coverage: `test_quest_reward_once` and `test_quest_reward_overflow_is_preserved_in_reserve_and_claimed_once`. Full disposable PostgreSQL result after this code change: 93 passed, 1 SQLite-only skip; Ruff, Black check and strict mypy passed. No feature is verified yet.

## F2-038 and F2-040..F2-041

Transport and garrison evidence has been expanded with regression tests for reserve overflow, capacity, retry/restart, double dispatch prevention and one-time arrival. The tests exposed and fixed garrison return accounting: pending recall units are excluded from available garrison, while persisted garrison units are correctly decremented. The full disposable PostgreSQL suite passed 99 tests with one SQLite-only skip; Python quality checks passed. Features remain partial pending browser and full lifecycle acceptance.

## F2-039 capture bonuses

The added regression validates the exact +100 ranking score and +5 percentage-point production gain after a level-3 command-center capture, in addition to existing capture gate/persistence checks. Targeted test and Python quality checks pass. A full test run after this latest test addition remains outstanding; F2-039 is partial, not verified.


## F2-039..F2-060 audit update

Current traceability rows F2-001..F2-060 have partial implementation/test mapping; none is `verified`. New regressions prove capture score/production bonuses, mission cap, vacation entry conditions/duration and neutral market 50/60% rates. Remaining explicit acceptance gap: F2-048 asks for ten neutral-market goods but the current UI/domain has only the three resource types. Exact constraint boundaries and complete browser journeys also remain for several F2 rows.

Latest validation: Ruff, Black check and strict mypy passed; full disposable PostgreSQL 18 suite **105 passed, 1 skipped** (SQLite-only backup). Main and private staging Docker stacks rebuilt without volume reset; local and HTTPS staging readiness passed; authenticated staging API smoke passed.


## 2026-11-06 — E04 engine evidence: outbox delivery and API failure contract

- Added `test_email_outbox_delivery_is_committed_and_retry_is_visible`: a locally mocked SMTP success marks an outbox item sent, clears its message body, and sets recipient/Message-ID; SMTP failure increments attempts but preserves a pending retry and message body. No external email was sent.
- Extended the authenticated API test to assert a request ID header and a sanitized domain error body without stacktrace.
- Mapped ENG-004..012, ENG-014, ENG-015 and ENG-017 as partial with per-ID evidence. ENG-013 rule-change impact simulation and ENG-016 true read-model pagination remain `not_audited`; their acceptance is not implemented.
- Ruff, Black check and strict mypy passed. Full suite on fresh disposable PostgreSQL 18: **106 passed, 1 skipped** (SQLite-only backup); all PostgreSQL parametrizations passed. Temporary DB removed; one existing Starlette/httpx TestClient deprecation warning remains.
- Feature inventory and traceability both contain 344 IDs with exact status parity: 66 partial, 278 open/un-audited, 0 verified. The list is reconstructed due missing original source pack.

## E05 source audit

The existing product model has one `world` row per database and one `colonies` row per account. Terrain is decorative in the browser. Multiple colonies, new worlds, colonization, Fog of War, regions, NPC resupply, terrain effects, relocation/abandonment and inter-colony logistics are absent. Five requirements have partial implementation evidence for current map/world basics, but their complete acceptance remains open; the other twenty E05 rows are unverified with explicit current-code findings. Any multiworld change needs a temp-database migration rehearsal before touching persistent player data.


## E05 follow-up (2026-11-06)

The earlier single-colony finding is superseded by migration 005: each account now has stable colony records, an active-base pointer and up to four bases in the current world. Colonization is gated by HQ level, slots, cost, free sector and distance; unique DB constraints back concurrency safety. Existing Main/staging PostgreSQL stores were backed up and upgraded without volume reset. Both report schema v5 and retain all preexisting accounts/colonies. W01/W02 remain partial pending browser/accessibility acceptance, own-colony logistics, and multiworld support.


## E05 W03 update (2026-11-06)

Kolonieversorgung ist nun implementiert: Ressourcen können aus einer aktiven Basis mit Trägern an eine andere eigene Basis derselben Welt geschickt werden. Zustellung und Rückkehr laufen workerbasiert und transaktional; DB-Ledger, Berichte und Depotüberlauf bleiben mit der richtigen Kolonie verknüpft. Fremde, gleiche oder andere-Welt-Ziele werden abgelehnt. Isolationstests umfassen SQLite/PostgreSQL, idempotente parallele Wiederholung und Worker-Neustart; ein Browserlauf bestätigte den Ankunftsbericht. W03 bleibt partial bis vollständiger Accessibility-/Mobile-/Mehrspieler-Abnahme; zwischenwelter Versorgung ist nicht verfügbar.


## E05 W04 security update (2026-11-06)

Ordinary player state responses no longer expose other players' defense aggregates, garrison counts or unit compositions; opposing captured posts similarly omit defense and garrison data. Players can send Ranger-only scouting missions: one or two Rangers reveal HQ/buildings, while at least three also reveal military composition and defense. Server checks PvP, newcomer, vacation, ban, alliance and NAP protection both when dispatching and when the mission arrives. Reports are private to the observer, expire after one hour and remain labeled stale; only fresh tier-2 data drives combat predictions. Rangers return even when arrival is blocked. Cross-adapter regressions cover redaction, privacy, both tiers, expiry, returns and protections. Sector-level fog, alliance sharing, browser and accessibility acceptance remain open, so W04 is partial.

## E05 W05 terrain update

The former decorative terrain is now persistent and server-authoritative under migration 007. Stable seed generation retains existing object coordinates; weighted routes avoid water; forest, mountain and pass affect travel time; resource production and defense use terrain modifiers. Tests cover SQLite and PostgreSQL behavior, though full browser/accessibility acceptance and endurance remain open. Main and private staging are on schema 7 and ready, each with 4,096 terrain cells; pre-upgrade dumps are under `backups/pre-terrain-20261106-1540/` and are not yet restore-drilled. W05 is partial. Overall release remains NOT A RELEASE CANDIDATE.

## E06 boundary

E06 is now the current audit target. The authoritative codebase still has a compact FUR-2 ruleset; the expanded E06/ECO list is reconstructed input. Inspect rule behavior and every acceptance path before implementing any expansion. Never apply a multiworld schema change to persistent main/staging until an additive migration has been rehearsed against disposable SQLite and PostgreSQL data and a restore path has been verified.

## E06 ECO-009 implementation evidence

The economy overview previously omitted the terrain multiplier from its displayed rate and provided no breakdown or time-to-cap estimate. `Systems.view` now emits exact current production components and pause/capacity details; `static/app.js` presents them. Regression: `tests/test_terrain.py::test_state_explains_terrain_production_bonus_storage_and_vacation_pause`. Status partial; accessible browser and future-event forecast acceptance remain open. Current overall feature inventory: 90 partial, 14 unverified, 240 not audited, zero verified.


## E06 queue cancellation audit

Build/research cancellation is now implemented with stored start/duration/original costs and backward-compatible derivation for previously stored jobs. Refund is prorated to remaining time and any cap overflow is preserved in reserve. Same-token retry cannot double refund; completed orders, training and missions cannot be canceled. SQLite full suite, focused disposable PostgreSQL 18 tests and frontend regression pass. Queue reorder and follow-up plans are not implemented; E04 and ECO-004 stay partial.

## E06 queue planning/reorder runtime audit (2026-11-06)

The later implementation adds up to five planned build and research jobs per colony, projected target-level reservations, serialized starts, waiting-job reorder, repricing, and queue-local quarantine behavior. Latest regression evidence: full SQLite **109 passed/48 skipped**, focused disposable PostgreSQL 18 queue regressions **14 passed**, frontend **13 passed**, Ruff/Black/strict mypy passed. The main and loopback-only staging app/worker images are now rebuilt and healthy with volumes preserved. Readiness is true, zero jobs are quarantined, schema 007 and 4,096 terrain rows are present; main data remains 3/3/1 and staging 4/4/1 (users/colonies/worlds). ECO-003/E04/ECO-004 remain partial because full browser/accessibility/player lifecycle acceptance is still open.

## E06 ECO-010 market history implementation

Schema 008 adds immutable, account-free records for completed neutral exchanges and player-market fills. The API derives a maximum 60-row, hourly, weighted summary over the prior 30 days; the UI shows no buyer, seller, or account identity. No historical backfill is performed. SQLite full suite passes **113/52 skipped**; focused test passes on SQLite and disposable PostgreSQL 18; frontend and Python quality checks pass. Main and staging rollout completed without volume reset; both are ready at schema 008 with unchanged data counts. ECO-010 remains partial pending public-world/multiworld aggregation, history lifecycle decisions, manipulation analysis and browser/accessibility acceptance.

## E06 ECO-011 update (2026-11-06)

Same-world alliance members can dispatch cargo to each other's home colonies using carriers and terrain routing. Membership is validated at dispatch and rechecked on receipt. Cargo is reserved during transit; delivery applies normal depot/reserve overflow behavior. The sender can cancel before arrival to recover cargo and carriers. If alliance membership changes before arrival, cargo is refunded and carriers return. UI offers only allied home colonies in the active world. SQLite/PostgreSQL 18 scenario tests and a frontend rendering/escaping regression pass. No migration or persistent runtime rollout occurred. ECO-011 remains partial pending browser, accessibility, mobile and broader adversarial acceptance. Inventory: 98 partial, 14 unverified, 232 not audited, zero verified (344 unique IDs).

## Continuation checkpoint — 2026-11-07

The source-backed account/security and race-condition audits have continued in the root app. ACC-002 (TOTP recovery codes), ACC-009 (login protection), and T02 (idempotency/concurrency/worker crash behavior) are partial, not verified. Current reconstructed inventory: 344 unique IDs — 2 verified, 134 partial, 26 unverified, 182 not audited. Latest local suite: 218 passed, 116 skipped, one existing Starlette/httpx deprecation warning; disposable PostgreSQL 18 adapter cases passed for recovery-code handling, worker concurrency/retry, and account/network login throttling. Frontend: 35 passed; Ruff, Black, strict mypy, ESLint, JavaScript syntax, traceability, and Compose configuration checks passed. Main/Staging data and running images were not changed. Public-release, 30-minute performance, mobile/accessibility, original-source provenance, and owner-rule gates remain open.
