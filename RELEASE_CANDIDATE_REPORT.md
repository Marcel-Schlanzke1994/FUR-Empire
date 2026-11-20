# 2026-11-18 checkpoint — release gates remain open

The canonical inventory has 344 entries. Four are verified, 229 partial, 52 unverified and 59 unaudited. The current E11 work covers COMBAT-5, ruin exploration, the expedition catalog, a draft cooperative Terra boss and bounded CAMPS-3 invasions. Focused SQLite/PostgreSQL 18 and frontend tests passed. The full guarded SQLite regression passed 604 cases and skipped 299 optional PostgreSQL parametrizations. Focused PostgreSQL 18 evidence is available. Broad gameplay acceptance, a full mixed-adapter run, screen-reader and localization coverage, proposed balance, dependency audit and live operational gates remain open.

Local SQLite and both persistent PostgreSQL stacks were backed up and the copies upgraded to schema 119. Fresh disposable Compose app and worker reported health and readiness with zero quarantined jobs. Current scoped evidence, backup paths and pending work are in `PROGRESS_LOG.md`, `TRACEABILITY.md` and `RESUME_STATE.json`.

During the first full verification run, a test imported FastAPI before it selected its test database and migrated the live local SQLite file from schema 110 to 119. A read-only comparison against the pre-run backup found every pre-existing row unchanged in shared columns. Both backups passed integrity and foreign-key checks. The pytest setup now forces implicit app imports onto temporary databases, and the guarded full regression confirmed that the live file hash stayed unchanged. Live Main and Staging remained at schemas 79 and 106.

---

# Aktueller Stand 2026-11-09 — NICHT GETESTET / KEIN RELEASE CANDIDATE

Phase A aktiv. Neue Markt-, Heimat-, API- und Missionsänderungen sind ungetestet. 344/344 Vollimplementierung ist nicht erreicht. Migrationen030/031 nur vorbereitet; keine Anwendung, DB oder Deploymentumgebung gestartet/geändert. Aktuelle Details: `docs/implementation/DELTA.md`, Matrix und `RESUME_STATE.json`. Alle nachfolgenden Prüfergebnisse stammen aus früheren Ständen und sind keine Abnahme dieser Änderungen.

---

# Release candidate report — bootstrap status

**Status: NOT A RELEASE CANDIDATE for the 344-feature product.**

Latest checkpoint (2026-11-07 ENG-016 message and ranking pagination): 4 verified, 160 partial, 89 unverified, 91 not audited. Full local SQLite pytest rerun: 249 passed / 134 skipped / one existing Starlette-httpx deprecation warning (1080.02s). A prior full run had one intermittent SQLite lock failure in the concurrent-transfer stress test; that case passed twice in isolation and the complete rerun passed. Message/ranking API and adapter checks passed, including SQLite and disposable PostgreSQL 18; frontend: 44 passed. Ruff, Black check, strict mypy, ESLint, JavaScript syntax and 344-ID traceability passed. Persistent Main/Staging data and volumes were untouched; disposable PostgreSQL was removed. ENG-016 remains partial because other large read models still lack pagination. Not a release candidate.

The root app is a functioning local/controlled-test FUR-2 Genesis game. It is not the complete Terra + Orbit system described in the agent master blueprint. No release or completion claim is made for the 344 IDs.

## Evidence

- Baseline suites and quality checks are listed in `AUDIT_CURRENT_FUR2.md` and `docs/VERIFICATION.md`.
- Docker app, worker, and PostgreSQL were healthy and the app was loopback-only at `127.0.0.1:8081`.
- Local SQLite and PostgreSQL backups were created before feature work.
- Private staging API lifecycle smoke now verifies secure login/session, CSRF-protected state and a build command. `scripts/staging_smoke.py` runs this in CI against a fresh disposable stage. It is not browser E2E.

## Open gates

- E00 traceability and FUR-2 per-ID acceptance evidence.
- E01/E02+ feature implementation and migrations across Terra, multiple worlds/colonies, Orbit and other 344-ID scope.
- Git branch/history/secret scan unavailable because no `.git` metadata is present.
- Separate restore drill for the new PostgreSQL dump, multi-account/two-world end-to-end, deterministic combat replay, mobile/accessibility, and 30-minute load test.
- Public service prerequisites: domain/DNS, router reachability, SMTP and owner release approval remain outside this local audit.



## Private staging smoke update

A separate production-like private Docker staging stack now runs locally with PostgreSQL, app, worker, Mailpit and Caddy. Its runtime API smoke passed health, readiness, authenticated session/state/CSRF, and a build command; UI port and game TLS are bound only to loopback. This does not close browser E2E, remote CI, full license/image SBOM, full 344-feature, or public deployment gates. Status remains NOT A RELEASE CANDIDATE.


## 2026-11-06 latest regression/runtime update

The current code passed Ruff, Black check, strict mypy and 105 tests against disposable PostgreSQL 18, with one SQLite-only backup test skipped. Main and private staging Docker app/worker images were rebuilt without resetting persistent volumes; both readiness endpoints passed. The staging HTTPS API smoke exercised health, secure login, CSRF state and a build command. F2-001..F2-060 are partial mappings only, zero IDs are verified, and the 344-ID inventory remains reconstructed. The ten-goods neutral-market gap, browser E2E, full two-world/2–10 player acceptance, deterministic replay, accessibility/mobile, endurance, image SBOM/license gate, Git history/remote CI and public operational prerequisites remain open. This report remains NOT A RELEASE CANDIDATE.


## Latest E04 verification

ENG-005 Outbox SMTP success/retry and ENG-015 API request-ID/error-format regressions are included in the latest full disposable PostgreSQL run: 106 passed, 1 SQLite-only skip. Ruff, Black and strict mypy passed. All 344 inventory IDs align with traceability; 66 are partial, 278 open, none verified. ENG-013 rule simulation and ENG-016 pagination remain unaudited, along with the known F2-048 ten-goods gap. Status remains NOT A RELEASE CANDIDATE.

## E05 source audit update

The current SQLite/PostgreSQL schemas prove a single colony per player and a single world row per database. Current terrain is decorative, and E05 requirements for colonization, Fog of War, regions, NPC replenishment, relocation, multiple worlds and inter-colony logistics are not implemented. Five rows remain partial for existing bounded map/current-world/start/spawn behavior; the other twenty are explicitly unverified. A production release remains out of scope.
## E05 follow-up — map search and bookmarks

W09 has name/coordinate search, valid-sector jumps, authenticated per-player favorites (maximum 20) and gold star tile markers, with additive SQLite/PostgreSQL migration 004. Current validation: 85 local tests pass and 25 skip without disposable PostgreSQL; fresh disposable PostgreSQL 18 suite has 109 passed and 1 SQLite-only skip; frontend lint/syntax and 9 tests pass; Ruff, Black check and strict mypy pass. A disposable local-browser E2E passed login, edge-coordinate jump, favorite save and reload persistence. W09 is partial pending broader browser/accessibility acceptance. Public release is not authorized by this report.

The latest local main Docker and isolated staging app/worker images were rebuilt without resetting their PostgreSQL volumes. Main data counts remain three users, three colonies and one world; staging is separate. Both health/readiness probes pass. Public production is not deployed or claimed ready.


## E05 W01/W02 Update (2026-11-06)

Migration 005 now supports multiple owned colonies and founding on free sectors in the single Genesis world. Existing Main and staging data were backed up and migrated with volumes preserved; counts are 3/3/1 and 4/4/1 (users/colonies/worlds). Both stacks are healthy and ready. The implementation is partial: inter-colony logistics, other worlds, browser/accessibility acceptance and broader lifecycle/load checks remain open. Local SQLite: 88 passed/28 skipped; disposable PostgreSQL 18: 115 passed/1 SQLite-only skip; frontend: 9 passed; Ruff, Black and strict mypy passed. The overall release remains NOT A RELEASE CANDIDATE, with zero of 344 feature IDs verified.


## E05 W03 Versorgung eigener Kolonien (2026-11-06)

W03 now supports capacity-limited resource shipments between owned colonies in the same world. The worker credits the selected target's depot/reserve, records reports and returns carriers to the source colony. Ownership/world boundaries, replay, concurrent duplicate tokens, restart processing and browser form behavior have regression coverage; an isolated browser journey observed the target arrival report. Full mobile/accessibility and multi-account lifecycle acceptance remain open. Latest suites: SQLite 92 passed/32 skipped; disposable PostgreSQL 18 123 passed/one SQLite-only skip; frontend 10 passed; Ruff/Black/strict mypy passed. W03 is partial and the overall release remains NOT A RELEASE CANDIDATE.


## E05 W04 information-hiding update (2026-11-06)

Unscouted opponent colony/outpost defense and garrison details are now omitted from normal player state responses and shown as unknown in the mission UI. Server-side battle simulation still uses actual values. Regression coverage checks response redaction and UI policy. Persistent spy missions, intel levels/expiry, sector Fog of War, and alliance reconnaissance remain unimplemented; W04 remains partial.


W04 validation: SQLite 92 passed/32 skipped; disposable PostgreSQL 18 123 passed/one SQLite-only skip; frontend 11 passed; Ruff/Black/strict mypy passed. This validates the current test scope only; scouting actions, sector fog, accessibility, multiworld and launch gates remain open.


## E05 W04 reconnaissance follow-up (2026-11-06)

Persistent Ranger reconnaissance is now implemented with schema migration 006. One or two Rangers reveal HQ/buildings; three or more reveal military composition and defense. Reports are private to the observer, become stale after one hour, and only fresh level-2 data permits a combat preview. PvP protections are rechecked on arrival and Rangers return on abort. W04 remains partial because sector Fog of War, alliance sharing, browser/accessibility acceptance and full multiplayer lifecycle are still open.

Validation after implementation: SQLite **95 passed, 35 skipped**; disposable PostgreSQL 18 **127 passed, 1 SQLite-only skip**, plus the tier-1 test on both adapters **2 passed**; frontend **11 passed**; Ruff, Black check, strict mypy passed. Main and private staging stacks were rebuilt with volumes preserved and migrated to schema 006; both readiness probes pass and account/colony/world counts remain unchanged. Pre-upgrade custom-format dumps are in `backups/pre-intel-20261106-1435/`. No public deployment or release readiness is claimed; overall status remains **NOT A RELEASE CANDIDATE** with zero features verified.

## E05 W05 terrain and runtime update

Schema 007 now stores the 4,096 terrain cells; server pathfinding, water blocking, resource production and defense modifiers are active. Both private Docker stacks were rebuilt and are healthy at schema 7 with readiness true and all existing user/colony/world counts preserved. Full local SQLite: 99 passed/39 skipped. Full disposable PostgreSQL before the insert-batching optimization: 137 passed/1 SQLite-only skip; focused PostgreSQL terrain suite after optimization: 8 passed. Frontend 12 passed; Ruff/Black/strict mypy passed. The redundant optimized full-suite rerun was interrupted and is not treated as evidence. Latest backups exist but have not been restore-drilled. W05 remains partial; the 344-ID inventory is reconstructed, 89 partial, 14 unverified, 241 not audited, none verified. **NOT A RELEASE CANDIDATE.**

## Current release decision

The local main game and isolated loopback-only staging are running and ready for private validation. Browser/accessibility, complete 2–10 player and two-world lifecycle, latest-backup restore, 30-minute load, deterministic replay, full dependency/image license SBOM, Git history/remote CI, and all 344 feature acceptance gates remain incomplete. No public production readiness is claimed.

## E06 queue planning rollout — 2026-11-06

The verified build/research queue planning, reorder and cancellation code is now running on main and isolated staging. Both readiness endpoints return ready with zero quarantined jobs; the current databases are at schema 008 with 4,096 terrain cells. Main data remains 3 users/3 colonies/1 world; staging remains isolated at 4/4/1. The code was rolled out without resetting volumes. Queue features remain partial pending browser, accessibility and full lifecycle acceptance. **NOT A RELEASE CANDIDATE.**

## E06 ECO-010 market history rollout — 2026-11-06

Migration 008 and anonymous market-history code are running on main and loopback-only staging. Both readiness endpoints pass with zero quarantined jobs. Both databases report schema 008, an empty `market_trades` table, 4,096 terrain rows and unchanged data counts: main 3/3/1, staging 4/4/1 (users/colonies/worlds). Full local Python suite: 113 passed/52 skipped; focused market test passed on SQLite and disposable PostgreSQL 18; frontend and static checks passed. ECO-010 remains partial. **NOT A RELEASE CANDIDATE.**

The subsequent ECO-006 prerequisite audit adds one test without runtime changes. Current full Python suite is **114 passed/52 skipped**; Ruff, Black, strict mypy and frontend checks remain green. Current inventory is 344 unique IDs: 97 partial, 14 unverified, 233 not audited, zero verified. No public production-readiness claim is made.

The ECO-010 regression now also proves same-hour weighted aggregation and excludes a trade older than 30 days; focused SQLite and disposable PostgreSQL 18 cases both passed. Additional F2-053/F2-055 boundary and score regressions pass. Current full suite is **116 passed/53 skipped**. Main and private staging report PostgreSQL/worker healthy and zero quarantined jobs; readiness still says `production=false` and `admin_mfa_ready=false`. The stacks remain private test deployments and this does not change the release decision.

ECO-011 now supports alliance cargo shipments between same-world member home colonies, terrain-based travel, capacity, delivery-time membership revalidation, cancellation/refunds, and overflow storage. SQLite and disposable PostgreSQL 18 adapter tests passed; frontend ESLint, syntax and 15 UI tests passed. The full Python suite is **118 passed/55 skipped**; Ruff, Black and strict mypy passed. This code-only change has not been rolled out to Main or private staging. ECO-011 remains partial; no release readiness claim is made.

## E06 ECO-009 update

The overview now displays server-calculated production details for each resource: base production, current bonuses, terrain modifier, effective rate, storage capacity, estimated time to full and vacation pause. SQLite regression and UI syntax/lint suite pass. This is partial acceptance only; multi-browser/mobile accessibility and forecasts across future rule/event changes remain open.


## E06 queue cancellation update

E04/ECO-004 now partially supports canceling active build and research jobs with a proportional refund of the unspent-duration share. Reports, resource ledger, reserve overflow handling, transaction boundaries, command idempotency and legacy in-flight jobs are covered. Reordering and planned follow-up queues are still absent. Latest local full SQLite run: 103 passed/43 skipped; focused disposable PostgreSQL 18 cancellation tests: 4 passed; frontend: 13 passed; Ruff/Black/strict mypy passed. Main and loopback-only staging were rebuilt without volume reset; both readiness probes return true at schema 7 and preserve account/colony/world counts. Overall remains NOT A RELEASE CANDIDATE, 0/344 features verified.

## E05 W06 data foundation — 2026-11-06

Schema 009 and application paths now normalize outposts by world ID, stable target ID, order, and unique sector. The migration backfills existing JSON and synchronizes the legacy compatibility mirror. SQLite full suite: 120 passed/56 skipped; disposable PostgreSQL 18 focused suite: 18 passed. Main and staging remain untouched at schema 008. W06 is partial: active world selection, world creation/settings, world-bound commands/missions, UI/browser acceptance, and latest-backup restore drill remain open. Inventory is 344 IDs: 99 partial, 13 unverified, 232 not audited, 0 verified. **NOT A RELEASE CANDIDATE.**

## E05 W06 schema context — 2026-11-06

Migration 010 now allows positive world IDs, persists world settings, and backfills active world from each player's current colony. SQLite and disposable PostgreSQL 18 upgrade rehearsals preserved existing data and accepted world 2; focused cross-adapter test: 2 passed. Migration is not applied to Main or staging. Player/admin world creation, joining and switching, full world routing, UI/browser acceptance and restore drill remain open. W06 remains partial. **NOT A RELEASE CANDIDATE.**

## E05 W06 seeded worlds — 2026-11-06

The code now creates seeded worlds, supports player join and active-world switching, and routes map, terrain, colonies, missions, PvP targets, rankings, supply, market history, chat, intel and bookmarks by world. Open market escrow stays tied to its originating colony. SQLite: 124 passed/59 skipped; disposable PostgreSQL 18: focused world/migration/market/message cases 10 passed and the outpost suite 18 passed. Ruff, Black, strict mypy and frontend checks pass. Persistent Main/staging remain untouched at schema 008. Browser/accessibility/mobile, 2–10-player/endurance acceptance, latest-backup restore through schema 011, mutable settings and global alliance/event/season policy remain open. W06 remains partial; **NOT A RELEASE CANDIDATE.**

## E05 W06 API and browser acceptance — 2026-11-06

Manual browser acceptance on a disposable SQLite database passed: admin created an eight-post seeded world, a second player joined with a separate home colony, and switched back to Genesis. It found a strict API schema mismatch returning 422 for world actions; the command contract and API regression test now cover world create/join/select and their fields. Active-world labels in the sidebar, footer and map now follow the selected world. Full SQLite: 125 passed/59 skipped; Ruff, Black, strict mypy and frontend lint/syntax/tests passed. Disposable DB/server were removed. Reusable browser E2E, full map/travel/chat/market journeys, mobile/accessibility, settings lifecycle, cross-world global policies, schema-011 restore, 2–10 player/endurance and production gates remain open. W06 partial; NOT A RELEASE CANDIDATE.

## E05 W06 current backup restore through schema 011 — 2026-11-06

Fresh Main backup created and retained at backups/fur-20261106T182638Z.dump. A disposable PostgreSQL 18 container restored the schema-8 backup, then applied migrations 009–011 successfully. Verified schema 11 and preserved 3 users, 3 colonies, 1 world, 104 outposts and 4,096 terrain cells; disposable container removed. Main and staging remain healthy at schema 8. W06 stays partial: settings lifecycle, global-world policy, reusable browser/mobile/accessibility and broad player/endurance acceptance are open. **NOT A RELEASE CANDIDATE.**

## E05 W06 editable world settings — 2026-11-06

Admins can rename worlds and open or close new-player joins; server role checks, name validation, audit records, API/UI form binding and join-gate regression are implemented. The focused multiplayer scenario passed on SQLite and disposable PostgreSQL 18 (2 passed). Full SQLite is 125 passed/59 skipped; Ruff, Black, strict mypy and 17 frontend tests pass. Generated seed/outpost regeneration policy, reusable browser E2E, full mobile/accessibility and 2–10 player endurance, global world policies, hosted CI and other release gates remain open. W06 partial; **NOT A RELEASE CANDIDATE.**

## W06 settings browser evidence — 2026-11-06

Disposable SQLite browser acceptance passed for the admin UI path: world rename and closing the player join gate were reflected in the visible world card and form. The temporary server/database were removed. Persistent Docker stacks stayed healthy; this does not change the release status. W06 and the overall project remain partial / NOT A RELEASE CANDIDATE.


## W07 implementation evidence — 2026-11-06

Neutral outpost resources replenish at one unit per minute up to 400 × tier; owned posts do not refill. Scheduling is persisted per world and overdue raids evaluate stock at their due timestamp. Map UI displays neutral resource stocks; handbook documents the rule. Focused SQLite tests and SQLite/PostgreSQL 18 worker-cycle acceptance passed; full SQLite suite was 129 passed/59 skipped before one later adapter-parameterized test was added. W07 remains partial pending browser/mobile/accessibility and broader lifecycle acceptance. No release-readiness claim.


## W07 final acceptance update — 2026-11-06

Disposable SQLite browser acceptance confirmed the server-refilled neutral outpost stock appeared as 1/1/1 on the map. The PostgreSQL 18 worker-cycle regression and SQLite counterpart both passed. Full SQLite suite: 130 passed/60 skipped; frontend: 19 passed; Ruff, Black, strict mypy, ESLint and JS syntax passed. Temporary artifacts were removed. W07 remains partial because mobile/accessibility and broad multiplayer lifecycle gates remain. Overall release status is unchanged and is not production-ready.

## E05 W08 region control — 2026-11-06

Region rules and map summary are implemented. Full SQLite suite passed 135 tests with 61 skips; focused region/capture tests passed; frontend suite passed 20 tests; Ruff, Black and strict mypy passed. The parameterized PostgreSQL W08 adapter case was skipped because FUR_TEST_POSTGRES was unset. W08 remains partial until browser/mobile/accessibility and PostgreSQL adapter acceptance complete. The overall inventory now has 101 partial, 11 unverified, 232 not audited and 0 verified; the release gate remains closed. No persistent deployment changed.

## W08 responsive browser evidence — 2026-11-06

A disposable SQLite browser showed all region cards at 710px in two columns with no clipped content; the accessibility tree exposed section/list/headings. The 390px device and screen-reader checks and PostgreSQL adapter evidence remain open; W08 partial and overall release remains closed.

## TERRA-005 regional bonus cap — 2026-11-06

Regional production is separated from personal ranking and explicitly capped at 32 percentage points; a synthetic all-regions SQLite regression verifies the bound. Full SQLite: 136 passed/61 skipped, one existing deprecation warning. Python and frontend gates pass. TERRA-005 remains partial pending PostgreSQL, mobile/accessibility, and any dedicated score presentation decision. Overall release remains closed.

Latest follow-up: TERRA-012's 20-favorite quota is now per world, matching the existing private world-scoped storage/read path. Its two-world regression passed on SQLite and disposable PostgreSQL 18; full SQLite is 146 passed / 69 skipped, frontend 23 passed, and code-quality checks pass. The route preview was implemented in the following continuation; browser/accessibility acceptance remains open. Inventory counts and release status are unchanged: NOT A RELEASE CANDIDATE.

TERRA-012 route-preview update (2026-11-07): favorite targets can now show a temporary Dijkstra path from the active colony using only known walkable terrain; unknown sectors and water are excluded. The map highlights route cells and provides an accessible coordinate disclosure. Frontend suite now has 24 passing tests, including water detour and fog boundary cases. Browser/mobile/screen-reader acceptance remains open; inventory counts remain 106 partial / 6 unverified / 232 not audited / 0 verified, so release status remains NOT A RELEASE CANDIDATE.

## TERRA-011 conversion implementation — 2026-11-07

The mixed SQLite/PostgreSQL 18 suite passed 225 tests with one skipped backup/restore drill. All 25 frontend tests and Ruff, Black check, strict mypy, ESLint and JavaScript syntax checks passed. Persistent Docker Main/Staging are healthy and unchanged. This does not clear the release gate: the 344-feature inventory remains 107 partial, 5 unverified, 232 not audited and 0 verified; browser/mobile/accessibility, additional operations evidence and owner approval of the new FUR-3 balance remain open. Not a release candidate.

## E05 TERRA-014 Spawn- und Kolonieschutz — 2026-11-07

Die Mindestdistanz von sechs Sektoren zu bestehenden Kolonien gilt jetzt einheitlich für Genesis-Startplätze, Weltbeitritt und Expansion. Neue automatische Starts wählen nur zulässige freie Positionen; explizit angeforderte geschützte Startfelder werden abgewiesen. Expansion bleibt zusätzlich an bekannte freie Landfelder und begehbare Wege gebunden. Der Claim und die Kostenbuchung erfolgen transaktional; vorhandene weltgebundene Unique-Indizes sichern die Kachelbelegung ohne temporäre Reservierungsdaten. Keine Migration und keine Änderung bestehender Koloniekoordinaten.

Regressionen decken Spawnabstand, Doppelclaims, Reichweite und bekannte Spielerlisten/Fog-Sicht ab. Vollständige lokale SQLite-Suite nach Änderungen: 153 passed, 74 PostgreSQL-Fälle mangels DSN übersprungen, eine bestehende Starlette/httpx-Warnung (124.53s). Gezielt PostgreSQL 18: Spawnabstand 1 passed; der zuvor vollständige SQLite/PostgreSQL-18-Mischlauf vor diesem Spawnpaket: 225 passed, 1 separater Restore/Backup-Skip. Ruff, Black check, strict mypy, ESLint, JavaScript-Syntax und 25 Frontendtests bestanden. Keine Browser-/Mobile-/Screenreaderabnahme behauptet. Inventar: 107 partial, 5 unverified, 232 not audited, 0 verified; keine Releasefreigabe.

## E05 TERRA-013 Allianzgebiete — 2026-11-07

Regionskontrolle leitet jetzt zusätzlich Allianzgebiete aus dem tatsächlichen Außenpostenbesitz ihrer Mitglieder ab. Sie verwendet dieselbe Mindestzahl von zwei und strikte Mehrheit wie die bestehende Einzelspieler-Kontrolle; ein Gleichstand bleibt neutral. Die Anzeige erscheint nur nach vollständiger Erkundung der Region. Die Zuordnung wird aus aktueller Mitgliedschaft neu abgeleitet und invalidiert den Regionscache bei Beitritt/Austritt. Produktionsbonus und persönlicher Ranglistenwert bleiben unverändert; keine Migration.

Regressions für Aggregation, Gleichstand, Membership-Cache-Invalidierung und escaped UI bestanden. SQLite/PostgreSQL-18-Adapterlauf: 2 passed; disposable Container entfernt. Vollständige lokale Suite: 157 passed, 75 skipped, eine bestehende Starlette/httpx-Warnung (141.65s). Frontend 25 passed; Ruff, Black check, strict mypy, ESLint und JavaScript-Syntax bestanden. Browser/Mobile/Screenreader-Abnahme bleibt offen. Inventar: 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-003 start progression — 2026-11-07

The starting kit guarantees all three resource lines without capturing an outpost during the one-hour newbie shield; SQLite and disposable PostgreSQL 18 focused adapter cases passed (2 total). The local full suite is 158 passed / 75 skipped with one existing deprecation warning; Ruff/Black/strict mypy passed. Terrain/neutral-target parity and browser/mobile/accessibility remain unverified. This does not change release status: 108 partial, 4 unverified, 232 not audited and 0 verified.

TERRA-003 final adapter/full-suite follow-up (2026-11-07): Ein zusätzlicher parametrischer Neuspieler-Test sichert das Startpaket auf beiden Datenbankadaptern. SQLite und disposable PostgreSQL 18: 2 passed. Anschließender vollständiger lokaler Lauf einschließlich neuer Regressionen: 159 passed, 76 skipped, eine bestehende Starlette/httpx-Warnung in 131.78s. Ruff, Black check (23 Dateien), strict mypy (15 Quelldateien), ESLint, JS-Syntax und Frontend 25/25 bestanden. Persistente Main-/Staging-Container healthy und unverändert.

## Traceability coverage audit and CI guard — 2026-11-07

The 344-feature source inventory and TRACEABILITY.md were reconciled by exact ID. The audit found a stale TERRA-004 status plus obsolete duplicate TERRA-005/TERRA-006 rows; these were corrected/removed. No inventory ID was missing after reconciliation: 344 unique rows, zero duplicates, zero status drift. Added `scripts/check_traceability.py`, a standard-library validator for unique IDs, complete coverage, valid statuses and exact status parity; wired it into `.github/workflows/checks.yml`. Local validator, Ruff, Black and strict mypy pass. Epic-level items without audited implementation evidence remain `pending audit`; no implementation status was inflated. Full local game suite remains 159 passed/76 skipped (131.78s, one existing warning). The reconstructed-source provenance gap remains documented.

## E05 TERRA-001 seeded-world reproducibility — 2026-11-07

A regression creates two worlds with the same configured seed and verifies all 4,096 terrain values plus ordered neutral outpost positions, tiers and stocks match. It joins a player into one copy and verifies a neutral resource outpost is reachable via non-water path within 3,600 seconds. SQLite/PostgreSQL 18 adapter cases: 2 passed; temporary container removed. Full SQLite suite: 160 passed, 77 skipped, one existing Starlette/httpx warning in 144.48s. The traceability check passes all 344 IDs exactly once with no status drift. TERRA-001 remains partial because broader seed-matrix/start-parity and browser/mobile/accessibility acceptance are open; feature inventory stays 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-002 concurrent colony claims — 2026-11-07

The same-sector race regression now synchronizes two players at a barrier before both commands execute. It proves exactly one colony is created and verifies the winner alone pays one colonization cost; the losing account's resources remain unchanged. Both SQLite and a disposable PostgreSQL 18 adapter passed (2 total); the temporary database container was removed. The world-scoped unique index remains the final duplicate-claim guard, with the serialized transaction handling cross-entity checks. Full local suite: 160 passed, 77 skipped, one existing warning in 130.34s; 25 frontend tests, Ruff, Black check, strict mypy, ESLint, JS syntax and 344-ID traceability gate pass. Broader load/browser/accessibility evidence remains open. Inventory remains 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-004 Fog-Isolation beim Weltwechsel — 2026-11-07

Neue Mehrweltenregression erzeugt eine alte Sichtbeobachtung in Genesis, wechselt in eine zweite Welt und beweist, dass dieselbe Koordinate dort unbekannt bleibt und keine Terraininformation preisgibt. Nach Rückkehr nach Genesis erscheint die Beobachtung dort wieder mit dem korrekten stale-Status und Originalzeitstempel. SQLite und disposable PostgreSQL 18: 2 passed; Container entfernt. Vollständige lokale Suite: 161 passed, 78 skipped, eine bestehende Starlette/httpx-Warnung (129.91s). Ruff, Black-Check (24 Dateien), strict mypy (15 Quelldateien plus Traceability-Skript), ESLint, JS-Syntax und 25 Frontendtests bestanden; 344-ID-Traceability-Validator grün. TERRA-004 bleibt partial: Browser/Mobile/Tastatur/Screenreader und Allianzfreigabe-Regeln offen. Gesamtinventar: 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-005 Regionsbonus-Kappung und Ranglistentrennung — 2026-11-07

Ein neuer adapterparametrisierter Test ordnet reale Außenposten allen 16 Regionen zu, erreicht den vollen Produktionsbonus von 32 Prozentpunkten und vergleicht davor/danach die persönliche Rangliste. Der Bonus wird nicht in persönliche Basenpunkte eingerechnet. SQLite und disposable PostgreSQL 18 bestanden: 2 adapter cases. Vollständige lokale Suite: 162 passed, 79 skipped, eine bestehende Starlette/httpx-Warnung (127.21s). Traceability 344/344, Ruff, Black-Check (24 Dateien), strict mypy (15 Quelldateien plus Validator), ESLint, JavaScript-Syntax und 25 Frontendtests bestanden. Status partial bis Browser/Mobile/Accessibility-Abnahme und einer Produktentscheidung, falls eine separate territoriale Rangliste gewünscht ist. Inventar: 108 partial, 4 unverified, 232 not audited, 0 verified.


## ECO-006 verification update — 2026-11-07

Concurrent queued prerequisites now have SQLite/PostgreSQL 18 regression coverage (2 passed); full local suite 163 passed / 80 skipped, one existing Starlette/httpx warning. Ruff, Black, strict mypy and 344-ID traceability pass. ECO-001 energy is confirmed absent from the root FUR-2 rule catalog and remains unverified pending owner balance rules. Inventory: 108 partial, 5 unverified, 231 not audited, 0 verified. Release status remains NOT A RELEASE CANDIDATE; no browser/mobile/accessibility or public-production claim is made.


## ECO-010 market-history isolation — 2026-11-07

SQLite and disposable PostgreSQL 18 now verify other-world market events are excluded from the active world's anonymous weighted history (2 adapter cases). Full local suite: 163 passed / 80 skipped / one existing warning in 129.12s. Python checks and 344-ID traceability pass. Inventory remains 108 partial, 5 unverified, 231 not audited, 0 verified. Release status remains NOT A RELEASE CANDIDATE; no player-facing browser/accessibility acceptance is claimed.


## F2-004 CSRF session resynchronization — 2026-11-07

Stale token after another-tab login now triggers one state refresh and one same-body retry; server Origin/CSRF validation is unchanged. API rotation regression and frontend retry regression pass; frontend 26 passed. Full Python suite 164 passed / 80 skipped / one existing warning in 126.79s. Ruff, Black, strict mypy, ESLint, JS syntax, and traceability pass. Browser multi-tab acceptance remains. Inventory: 108 partial, 5 unverified, 231 not audited, 0 verified; release remains NOT A RELEASE CANDIDATE.


F2-004 update is now deployed to the private loopback staging app only. Staging app health/readiness pass and served JS contains the fix; database/worker/proxy and Main container were left untouched. No public production readiness is claimed.

Main local Docker app now serves the F2-004 fix at 127.0.0.1:8081 and passes health/readiness. Only the app image/container was replaced; Main PostgreSQL volume and worker were not changed. Staging remains healthy at localhost:8443.


OPS-008 rate-limit negative test passes; latest full suite: 165 passed / 80 skipped / one existing warning (131.03s), frontend 26 passed, required quality and traceability checks pass. Inventory now 109 partial, 5 unverified, 230 not audited, 0 verified. Local Docker Main and private staging are healthy with the F2-004 fix; this is not public production approval.

OPS-016 health/readiness regression passes; full suite 166 passed/80 skipped/one existing warning (127.50s). Inventory: 110 partial, 5 unverified, 229 not audited, 0 verified. Local/private Docker only; public release not approved.


OPS-004/OPS-015 now verified with a current schema-12 PostgreSQL 18 isolated dump/restore. Database logical SHA-256, pending mission SHA-256, resources, membership, 104 outposts, 4096 terrain cells and 136 intel rows were preserved. Six SQLite/PostgreSQL migration cases passed. Full suite: 166 passed/80 skipped/one existing warning. Inventory: 2 verified, 110 partial, 5 unverified, 227 not audited; still NOT A RELEASE CANDIDATE.

OPS-009 worker rollback/retry is now verified across SQLite/PostgreSQL (2 adapter cases), and OPS-013 multiworld isolation evidence covers eight adapter cases. Latest full suite 167 passed/81 skipped/one existing warning (203.22s); frontend 26 passed and required quality gates pass. Inventory: 2 verified, 112 partial, 5 unverified, 225 not audited. Release remains NOT A RELEASE CANDIDATE.


## Current validation update — 2026-11-07

OPS-010 property regressions are partial with deterministic SQLite replay and SQLite/PostgreSQL 18 invariant-sequence evidence. Full local suite: 169 passed, 82 skipped, one existing Starlette/httpx deprecation warning (181.49s). Full disposable PostgreSQL 18 suite: 250 passed, 1 SQLite-only skip, same warning (819.00s). Ruff, Black check (24 files), strict mypy (15 application + 4 scripts), ESLint, JavaScript syntax, frontend (26), and 344-ID traceability pass. Inventory: 2 verified, 113 partial, 5 unverified, 224 not audited. This is not a release candidate: broad product acceptance, mobile/accessibility, provenance, 30-minute load and external production checks remain open.


## W10 continuation — 2026-11-07

Initial neutral NPC frontier simulation and a fog-scoped map panel are implemented. Focused SQLite and PostgreSQL 18 cases pass; full SQLite suite: 172 passed/83 skipped, one existing deprecation warning. UI tests 27 and all listed static gates pass. W10 remains partial; 2 verified/114 partial/4 unverified/224 not audited across the reconstructed inventory. Not a release candidate.


## K03 continuation — 2026-11-07

Scouting now has explicit regression evidence that PvP disable and vacation activation during travel are rechecked at arrival, prevent report creation, and return Rangers exactly once on SQLite/PostgreSQL 18. Full SQLite suite: 174 passed/85 skipped; frontend 27 and code-quality gates pass. K03 is partial because counterintelligence interception rules and browser/device acceptance are open. Inventory: 2 verified, 115 partial, 4 unverified, 223 not audited. Not a release candidate.


## K07 continuation — 2026-11-07

Outbound recalls now cover six mission types; focused SQLite/PostgreSQL 18 adapter suite passed 12 cases. K07 remains partial: configurable retreat thresholds, after-arrival/battle retreat and browser/device lifecycle acceptance remain open. The full 344-feature release gate remains incomplete.


## K07 Vollgate — 2026-11-07

K07 partial, 12 fokussierte SQLite/PostgreSQL-18 Fälle bestanden. Gesamtgates: Ruff, Black (24), strict mypy app/scripts, ESLint, JS-Syntax, 28 Frontendtests und 180 passed/91 skipped SQLite-Suite bestanden; eine bestehende DeprecationWarning. Traceability 344/344 ohne Statusabweichung. Lokaler Main-Stack bereit; private Staging-App/Worker healthy, aber HTTPS readiness wegen TLS InternalError an 127.0.0.1:8443 unbestätigt. Kein öffentlicher Rollout. Inventar bleibt 2 verified, 116 partial, 4 unverified, 222 not audited; daher kein Release Candidate.


Staging TLS Follow-up: the apparent failure was caused by probing 127.0.0.1 while local Caddy serves a localhost certificate. Configured https://localhost:8443 returns health ok and readiness true with certificate verification skipped for the local CA. This confirms service readiness, not browser trust or public readiness.


## E07 K04 / WAR-005 — 2026-11-07

Neutrale Gefechtsprobe mit gemeinsamem deterministischem Resolver, Sicht-/Einheitenvalidierung, CSRF-Schutz und UI umgesetzt; Regressionen beweisen keine Gameplay-State-Mutation. Vollsuite 182 passed/92 skipped; Frontend 29; Ruff/Black/mypy/ESLint/JS und Traceability 344/344 grün. Main und private Staging App/Worker healthy; readiness true. 2 verified, 118 partial, 4 unverified, 220 not audited: kein Release Candidate. Keine PvP-Simulation, Verlustspannen oder manuelle Geräteabnahme behauptet.


PostgreSQL adapter follow-up: K04/WAR-005 focused checks now pass on SQLite and disposable PostgreSQL 18 (3 passing test executions including API), using a no-volume temporary container that was removed. Main/Staging DB container start times are unchanged.


## WAR-020 E07 Combat Grid — 2026-11-07

A 24,336-case deterministic FUR-2 grid covers the three existing units, opposing compositions, tactics, neutral tiers and terrain. It verifies determinism and conservation/bounds, not counter-balance; WAR-020 partial. Full suite 183 passed/92 skipped, frontend 29 and all code gates green. K01/K02 marked unverified after source audit: missing original rules pack and no quantitative FUR-3 coefficients/roster. Inventory 2 verified, 119 partial, 6 unverified, 217 not audited; not a release candidate.

## 2026-11-07 continuation — K13

K13 mission templates are implemented and deployed on local Main and private loopback Staging at schema 13 after pre-migration backups. Health/readiness are true and existing persistent data counts were preserved. Current inventory: 2 verified, 120 partial, 6 unverified, 216 not audited. Gates: full SQLite 185 passed / 93 skipped / one existing warning; focused PostgreSQL 18/API/migration 3 passed and 1 skipped; frontend 30 passed; Ruff, Black, strict mypy, ESLint, JS syntax and traceability passed. The schema-13 backup restore drill remains outstanding because the disposable schema-13 restore attempt failed at pg_dump before the restore stage. Browser/mobile/accessibility acceptance and broader 344-feature acceptance remain open. **NOT A RELEASE CANDIDATE.**

Follow-up on the schema-13 restore check: passed in a disposable PostgreSQL 18 network. Exact logical DB and pending-mission SHA-256 matched after custom-format restore; 104 outposts, 4096 terrain cells, resources and alliance membership were preserved. Temporary resources removed; Main/Staging untouched.

K11 movement audit: the current unit catalog has no speed/range values, and terrain path time is independent of army composition. The original reference manual/gap file named in the prompt is absent. K11 remains unverified pending approved/versioned movement rules. Inventory: 2 verified, 120 partial, 7 unverified, 215 not audited.

K05/K06 source audit: shared alliance combat and allied-base garrisons are not present. Existing alliance PvP/ownership safeguards remain active. Deterministic rules for operation consent/lifecycle, loss/capture attribution, and allied garrison recall/loss are absent; both remain unverified. Inventory: 2 verified, 120 partial, 9 unverified, 213 not audited.

## 2026-11-07 continuation — K08 / schema 014

K08 now has server-authoritative, deterministic FUR-3 expedition missions with versioned outcomes, unit escrow, loss/reward resolution and return/recall. Migration 014 adds expedition mission-template support and preserves existing rows. Also corrected missing mission dialog mode/cargo fields discovered during acceptance review. Focused SQLite/PostgreSQL 18, API, frontend and quality checks passed; full suite pending. Private Main/Staging backups were created and staging archive listing verified before rollout. The feature remains partial pending full browser/mobile/accessibility and load/lifecycle acceptance.

## 2026-11-07 — K08 and schema 014 checkpoint

K08 deterministic FUR-3 expeditions are implemented with versioned weighted outcomes, unit escrow, capacity-limited rewards, private reports/audits and exactly-once return/recall. Migration 014 extends mission-template modes while preserving saved rows. Fixed absent mission mode/cargo controls in the dialog markup. Full local suite: 189 passed / 96 skipped (one existing deprecation warning); PostgreSQL 18 focused expedition/recall 21 passed, migration 014 2 adapter cases passed; frontend 31; Ruff, Black, strict mypy, ESLint, JS syntax and traceability pass. Main and private Staging are healthy/ready at schema 14 with original persistent counts preserved. Schema-14 disposable PostgreSQL backup/restore passed matching logical DB and mission SHA-256, resources/alliance and 104 outposts/4096 terrain cells. Pre-upgrade backups were created and archive-listed. Browser/mobile/accessibility and endurance acceptance remain open. Inventory: 2 verified, 121 partial, 9 unverified, 212 not audited. **NOT A RELEASE CANDIDATE.**

## 2026-11-07 continuation — K12 / E08 source audit

K12 partial: structured one-round FUR-2 reports now preserve participants, attack/defense power, per-unit sent/lost/survivor counts and loot for PvE/PvP, with escaped expandable UI and old-report compatibility. Focused SQLite/PostgreSQL 18: 4 executions passed; full SQLite: 190 passed / 97 skipped; frontend 32; all Python/JS quality checks and traceability pass. K09 debris/salvage and K10 artillery/missiles are unverified because current FUR-2 contains no lifecycle/economy or weapon rules; approved FUR-3 contracts are needed before adding effects. Inventory: 2 verified, 122 partial, 11 unverified, 209 not audited. **NOT A RELEASE CANDIDATE.**

## 2026-11-07 — WAR-016 and K14 audit

PvP protection/diplomacy checks now have arrival-transition regressions for PvP being switched off, defender vacation starting, beginner protection becoming active, and an accepted NAP during transit. In every case, arrival cancels the attack, creates no battle report, returns the entire army once, and emits only one abort report. Tests: SQLite 4 and disposable PostgreSQL 18 4 passed. Full local suite: 194 passed / 101 skipped / one existing deprecation warning. Ruff, Black, strict mypy, 32 frontend tests, ESLint, JS syntax and traceability pass.

WAR-016 is partial: existing PvP/age/vacation/alliance/NAP protections apply at dispatch and arrival. The live rule allows attacks without a formal war declaration; no authoritative contract defines whether that should be required. Browser/device lifecycle acceptance remains open. K14 audit found no active defensive structures beyond the shield wall and no turret/trap/repair contract; it is unverified pending approved FUR-3 values. Inventory: 2 verified, 123 partial, 12 unverified, 207 not audited.

## 2026-11-07 — WAR-017 and WAR-019 source audit

WAR-017 source audit confirms only a per-client API rate limit and a 30-concurrent-job colony cap; neither limits repeat attacks on one target or reduces farm yields. No approved time window, caps, exemptions or reset rules are present, so WAR-017 is unverified rather than shipping an arbitrary limit.

WAR-019 is partial: K12 structured reports are visible in each participant account state; a new third-player regression confirms uninvolved players receive no battle details. The report UI escapes dynamic names. There is no immutable replay input/seed commitment or anonymized public-share workflow. Targeted report privacy test passed on SQLite and disposable PostgreSQL 18. Full local suite: 194 passed / 101 skipped / one existing deprecation warning. Quality gates and 344-ID traceability pass. Inventory: 2 verified, 124 partial, 13 unverified, 205 not audited.

## 2026-11-07 — WAR-018 ranking audit

The current deterministic personal score is buildings ×10, technologies ×20 and captures ×100. Existing regression covers exact weights and stable ties; region production bonus remains separate. No attack, defense, support category or alliance military ranking is implemented. WAR-018 is unverified until scoring/credit attribution rules are approved; combat losses, shared operations and support cannot be assigned invented points. Inventory: 2 verified, 124 partial, 14 unverified, 204 not audited.

## 2026-11-07 — WAR-007 reconciliation and WAR-018 ranking audit

WAR-007 was previously still marked not audited despite the existing implementation: recall replaces eligible outbound missions with one idempotent return job, retaining unit/cargo escrow through return. Six mission kinds have SQLite/PostgreSQL 18 coverage. The traceability/index now classify it partial; after-arrival retreat, configurable thresholds, and device/browser acceptance remain.

WAR-018 audit: the current personal ranking formula is buildings ×10, technologies ×20 and captures ×100 with stable tie order. No military categories or alliance score exist. Scoring attribution for attack, defense, losses and support is unspecified; no arbitrary ranking points were added. Inventory: 2 verified, 125 partial, 14 unverified, 203 not audited. Full latest local suite remains 194 passed / 101 skipped; traceability checked against 344 IDs.

## 2026-11-07 — WAR-008 tactical retreat audit

FUR-2 combat is a single atomic round. Source has no retreat threshold, mid-battle state, casualty checkpoint or retreat return-position rule. WAR-007 outbound recall is a separate pre-arrival mission command and does not satisfy tactical retreat. The FUR-3 outline mentions retreat but supplies no contract. WAR-008 is unverified pending the retreat/casualty/return policy. Inventory: 2 verified, 125 partial, 15 unverified, 202 not audited.

## Current continuation checkpoint — 2026-11-07

Still **NOT A RELEASE CANDIDATE**. Latest local suite: 218 passed / 116 skipped / one existing warning; targeted disposable PostgreSQL 18 regressions passed for ACC-002, ACC-009 and T02; frontend 35 and all local quality/traceability/configuration gates passed. Current feature inventory is 2 verified, 134 partial, 26 unverified and 182 not audited. Source migration 017 has not been applied to Main or Staging; no current app image was rebuilt. Persistent player data remains untouched. Interactive browser/mobile/accessibility, 30-minute load, multiworld lifecycle, and external production operations remain unverified.

## E04 queue repricing checkpoint

The E04 queue package now binds new build/research jobs to rule version, active-catalog SHA-256, base cost and formula. Replanning retains reserved prices across catalog changes; legacy jobs infer their base cost from saved reservations only when consistent with the saved target level. This adds no schema migration. Verification: focused regression passed; Ruff, Black check and strict mypy passed; full local pytest 224 passed / 118 skipped / one existing Starlette-httpx deprecation warning (429.57s). PostgreSQL integration tests were skipped because `FUR_TEST_POSTGRES` is unset. Inventory: 2 verified, 139 partial, 30 unverified, 173 not audited. E04 remains partial pending browser/mobile/accessibility and broad lifecycle acceptance. Persistent databases/player data unchanged; this is not a release candidate.

## E08 faction catalog audit

FUR-2 has the documented one-time faction choice and passive bonuses, with regression tests. The proposed three technologies and two special units per faction lack rules, costs, unlocks and balance caps. E08 and ECO-016 are unverified pending an approved catalog; no rules were invented. Inventory: 2 verified, 139 partial, 32 unverified, 171 not audited. No player data/runtime changes.

Latest verification after extending the E04 snapshot regression to both build and research: 2 focused tests passed; full local pytest 225 passed / 118 skipped / one existing warning (408.77s). Ruff, Black (25 Python files), strict mypy (16 source files), and traceability (344 unique IDs, no status drift) passed.

## E06 / ECO-010 market-history time bounds

Market-history queries now enforce both ends of the 30-day window, excluding future-dated rows, and an adapter regression confirms that no more than the latest 60 hour buckets are returned. The product specification explicitly says there is no historical backfill; the inventory no longer lists that intended behavior as a missing feature. The statistics are world-scoped. Full SQLite + disposable PostgreSQL 18 suite passed; frontend, Ruff, Black, strict mypy and 344-ID traceability pass. A later desktop/mobile browser and accessibility-tree acceptance verified aggregate list semantics, no horizontal overflow and no trader identities. E06/ECO-010 are verified; temporary test resources were removed and persistent Main/Staging remained untouched.

## E06 / ECO-013 production presets — 2026-11-07

Schema migration 019 adds owner-scoped build, research and training templates with case-insensitive names and a ten-template cap. Save/list/delete and queue endpoints are CSRF protected; applying a template invokes the ordinary game command and rechecks the active colony's prerequisites, resources, limits and idempotency key. Personal account export includes only the owner's production templates. Full SQLite + disposable PostgreSQL 18 suite: 348 passed / 1 skipped / one existing warning (1377.57s); focused migration/API cases: 4 passed; frontend: 38 passed; Ruff, Black, strict mypy, ESLint, JavaScript checks, Compose configuration and traceability pass. Interactive browser input was unavailable in this session, so no manual browser, mobile or screen-reader acceptance is claimed. Migration 019 remains source-only; persistent Main/Staging databases and player data were not modified. ECO-013 remains partial. Current inventory: 4 verified, 140 partial, 36 unverified, 164 not audited. Release remains NOT A RELEASE CANDIDATE.

## 2026-11-07 — Current ENG-016 continuation checkpoint

The alliance directory is bounded to 50 entries per stable `lower(tag), id` keyset page and has an authenticated, rate-limited API plus an escaped, accessible load-more control. SQLite and disposable PostgreSQL 18 adapter regressions pass. The full local suite passes: **251 passed, 135 skipped, one existing Starlette/httpx deprecation warning (942.10s, exit 0)**. The 24-hour ACC-004 commander-name cooldown was confirmed by the owner and is already implemented with adapter coverage.

Current inventory: **4 verified / 160 partial / 89 unverified / 91 not audited**. ENG-016 remains partial: alliance rosters/applications, player lists and reports still need bounded read paths. This is not a release candidate; browser/mobile/accessibility, extended load and external production operations remain unverified. No migration was applied, and Main/Staging, persistent player data, Docker stacks and dependency lockfiles were not changed.

## 2026-11-07 — ENG-016 alliance roster continuation

Alliance member output is now bounded to 50 rows and paged by stable role/name/user-ID order. The member endpoint rechecks current alliance membership and cursor scope; the UI retains existing member-management actions and announces page loading accessibly. SQLite and disposable PostgreSQL 18 adapter regressions pass. Full local test suite: **253 passed, 136 skipped, one existing Starlette/httpx deprecation warning (1136.71s, exit 0)**. Frontend: **46 passed**. Ruff, Black, strict mypy, ESLint, JavaScript syntax, Compose config and 344-ID traceability pass.

Inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Applications/invitations, player lists and reports remain open, along with interactive browser/mobile/accessibility, extended load and external production checks. This remains **NOT A RELEASE CANDIDATE**. No migration, production database, persistent player data, Docker stack or dependency lockfile changed.

## 2026-11-07 — ENG-016 application-list continuation

The active alliance view now surfaces application actions. Outgoing requests are private to the player; incoming requests are restricted to current leaders/officers. Each direction uses a 50-row newest-first keyset page, and the public directory carries the viewer's application id for correct apply/withdraw controls. SQLite and disposable PostgreSQL 18 pagination regressions pass. Full local pytest: **256 passed, 137 skipped, one existing Starlette/httpx deprecation warning (1095.39s, exit 0)**. Frontend: **47 passed**. Ruff, Black, strict mypy, ESLint, JavaScript syntax, Compose config and 344-ID traceability pass.

Inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Invitations, player selection lists and reports still need review/pagination. Browser/mobile/accessibility, endurance/load and external production checks remain outstanding. This is **NOT A RELEASE CANDIDATE**. No migration, persistent database, player data, Docker stack or dependency lockfile changed.

## 2026-11-07 — ENG-016 invitation-list continuation

Incoming invitations are now scoped to the current player's account; outgoing invitations are restricted to current alliance leaders/officers. Both use 50-item keyset pages and role/owner-scoped cursor validation. The active UI retains accept, decline and cancel actions with accessible page controls. SQLite and disposable PostgreSQL 18 directory/member/application/invitation matrix: **8 passed**. Full local pytest: **258 passed, 138 skipped, one existing Starlette/httpx deprecation warning (1172.36s, exit 0)**. Frontend: **48 passed**. Ruff, Black, strict mypy, ESLint, JS syntax, Compose config and traceability pass.

Inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Forum reports, player lists and market offers still need bounded read models. Browser/mobile/accessibility, endurance/load and external production checks remain unverified; this remains **NOT A RELEASE CANDIDATE**. No migration, persistent data, Docker stack or dependency lockfile changed.

## 2026-11-07 — ENG-016 alliance forum-report pagination

Alliance forum report queues now page 50 rows at a time in stable creation-time/ID order. Ordinary members can read only their own reports; current alliance leaders/officers can read the alliance queue. The authenticated, rate-limited endpoint rechecks membership and cursor visibility, and the moderator UI provides an accessible load-more control.

Verification: full local pytest **259 passed, 139 skipped, one existing Starlette/httpx deprecation warning (1095.17s, exit 0)**; focused SQLite/API report pagination **2 passed**. The PostgreSQL variant was skipped because `FUR_TEST_POSTGRES` is unset and Docker is unavailable. Frontend **48 passed**; Ruff, Black, strict mypy, ESLint, JavaScript syntax and 344-ID traceability passed. Inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Player-selection lists and market offers remain unbounded work. Browser/mobile/accessibility, endurance/load and external production operations remain unverified. This is **NOT A RELEASE CANDIDATE**. No migration, persistent data, Docker stack or dependency lockfile changed.

## 2026-11-07 — ENG-016 market-offer pagination

Open market offers now page 50 items at a time, restricted to open, unexpired offers in the player's current world. The rate-limited authenticated endpoint validates same-world cursors; the market UI keeps existing accept/cancel actions and adds an accessible load-more control.

Verification: full local pytest **261 passed, 140 skipped, one existing Starlette/httpx deprecation warning (1279.19s, exit 0)**; market API/system tests **3 passed**, two PostgreSQL adapter variants skipped because FUR_TEST_POSTGRES is unset and Docker is unavailable. Frontend **49 passed**; Ruff, Black, strict mypy, ESLint, JavaScript syntax and 344-ID traceability passed. Inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Player directory and alliance invite-candidate lists remain open, along with browser/mobile/accessibility, endurance/load and external production checks. This remains **NOT A RELEASE CANDIDATE**. No migration, persistent database, player data, Docker stack or dependency lockfile changed.

## 2026-11-07 — ENG-016 alliance invite-candidate pagination

The active alliance invitation selector now pages 50 candidates at a time. Only unaffiliated home colonies in the active world with currently visible sectors are returned; name/ID ordering is stable, and the authenticated endpoint rechecks current manager membership. The UI provides an accessible load-more control.

Verification: full local pytest **263 passed, 141 skipped, one existing Starlette/httpx deprecation warning (944.79s, exit 0)**; focused candidate tests **3 passed**, with two PostgreSQL variants skipped because FUR_TEST_POSTGRES is unset and Docker unavailable. Frontend **50 passed**; Ruff, Black, strict mypy, ESLint, JavaScript syntax and 344-ID traceability passed. Counts remain **4 verified / 160 partial / 89 unverified / 91 not audited**. World player and private-message/social selectors remain capped at 400. Browser/mobile/accessibility, endurance/load and external production checks remain open. This is **NOT A RELEASE CANDIDATE**. No migration, persistent data, Docker stack or dependency lockfile changed.

## 2026-11-08 — ENG-016 world player-directory pagination

The authenticated active-world player endpoint now retains the existing first 400 entries and reports whether more exist. Later pages return 50 rows using a stable joined-timestamp/user-ID cursor. Cursor ownership is validated against a home colony in the current world. Reconnaissance reports are fetched only for the current page and remain observer/world scoped, with unknown intel as the default. The map directory, social/contact candidates and private-message recipient selector share the appended client state and expose accessible load-more controls. No migration.

Verification: full local pytest **263 passed, 141 skipped, one existing Starlette/httpx deprecation warning (472.31s, exit 0)**; focused player/candidate API and system tests **3 passed, 2 PostgreSQL parameterizations skipped**; frontend **51 passed**. Ruff, Black check, strict mypy, ESLint and JavaScript syntax passed. PostgreSQL validation remains unavailable (`FUR_TEST_POSTGRES` unset; Docker engine unavailable). Inventory stays **4 verified / 160 partial / 89 unverified / 91 not audited**. ENG-016 remains partial; interactive browser/mobile/accessibility, endurance/load and public production acceptance remain open. No persistent database, player data, deployment stack or dependency lockfile changed.

Engine-Verfügbarkeitsnachtrag (2026-11-08): Docker Desktop startete während der Fortsetzung. Mit einem temporären, volumenlosen PostgreSQL 18.6 auf 127.0.0.1:55432 lief die komplette Suite erneut: **403 passed, 1 intentional backup/restore skip, one existing Starlette/httpx warning (2018.45s, exit 0)**. Der Testcontainer wurde entfernt. Main und privates Staging blieben unverändert; beide Compose-Konfigurationen validierten, Main health/readiness und loopback Staging readiness meldeten `ready=true`. Das stellt keine öffentliche Erreichbarkeit oder Produktionsfreigabe fest.

## 2026-11-08 — ENG-016 alliance-supply target pagination

The map's alliance-supply recipient list now returns 50 same-alliance home colonies in the active world at a time. Stable cursor order is normalized account name plus colony ID; the page endpoint rechecks current alliance membership, world and cursor. The accessible map control merges later recipients without duplicate IDs. Player directory sorting was adjusted to retain the established joined/name order, with user ID as the final tie-breaker.

Verification: full SQLite pytest **264 passed, 142 skipped, one existing Starlette/httpx warning (420.82s, exit 0)**. Focused supply recipient paging, actual delivery and player-list ordering on SQLite and disposable PostgreSQL 18.6: **6 passed**. Frontend **51 passed**. Ruff, Black check, strict mypy, ESLint, JavaScript syntax and 344-ID traceability pass. The prior full combined SQLite/PostgreSQL 18.6 run for the immediately preceding slice was **403 passed, one intentional separately verified backup/restore skip, one existing warning (2018.45s)**. Main/Staging Compose configs validate; Main health/readiness and loopback Staging readiness remain true. Temporary PostgreSQL container was removed; persistent stacks and player data were not changed. Overall status remains **NOT A RELEASE CANDIDATE**.

## 2026-11-08 — ENG-016 privileged operations-list pagination

The admin/moderator dashboard now loads at most 50 accounts and 50 failed worker jobs per state response. The two rate-limited follow-up APIs recheck the current admin/moderator role; account pages use name/ID order, failures use created/ID order. The dashboard retains the total failure count and adds accessible load-more controls.

Verification: full SQLite pytest **266 passed, 143 skipped, one existing Starlette/httpx warning (477.26s, exit 0)**. Admin user/failure pages plus existing moderation behavior passed on SQLite and disposable PostgreSQL 18.6: **4 passed**. Frontend **52 passed**. Ruff, Black check, strict mypy, ESLint and JavaScript checks pass; `pip-audit` found no known vulnerabilities and `npm audit` reported zero vulnerabilities. The traceability gate confirms 344 unique IDs with no status drift. Persistent Main/Staging containers and data volumes were not modified. ENG-016 remains partial; no release readiness is claimed.


## 2026-11-08 — Current read-model checkpoint

ENG-016 now also pages owner-private friends, incoming/outgoing requests and blocks. Full local SQLite suite: **267 passed, 144 skipped, one existing Starlette/httpx warning**; the current social slice has focused SQLite/API/domain tests **3 passed**, while its two PostgreSQL parametrizations were skipped because FUR_TEST_POSTGRES was not configured. Frontend 52 and the project style/type/syntax/traceability gates pass. Feature inventory remains **4 verified / 160 partial / 89 unverified / 91 not audited**. Remaining read models and browser/device/accessibility, endurance/load, hosted CI and public production evidence are still open. No release readiness claim; Main/Staging and persistent player data were left untouched.


## 2026-11-08 — ENG-016 social pagination and invite-candidate privacy

The current implementation bounds all four owner-private social lists; it also removes an obsolete global candidate-name list that bypassed current-world visibility and directs the legacy invite selector to the currently visible, unaffiliated active-world candidate page.

Verification: full local SQLite suite **267 passed, 144 skipped, one existing Starlette/httpx warning (494.04s)**. Disposable PostgreSQL 18.6 + SQLite invite-candidate, invitation privacy and social-page matrix **6 passed**. Frontend 52; Ruff, Black, strict mypy, ESLint, JS syntax, pip-audit (no known vulnerabilities, hashes advisory), npm audit (0), and 344-ID traceability pass. Temporary PostgreSQL was removed; persistent Main/Staging remain untouched. Inventory 4/160/89/91. ENG-016 and the overall project remain partial; no public release claim.


The deprecated invite-candidate payload was removed after the above checkpoint. The full source suite passed 267/144 skipped (494.04s); current invite/privacy/social cases passed on SQLite and disposable PostgreSQL 18.6 (6 total). A frontend regression now guards against reintroducing the old client property; frontend remains 52/52. Other quality gates and 344-ID traceability remain green.


## 2026-11-08 — Incoming attack status payload

The warning bar now receives an exact count instead of attacker names and arrival timestamps. The source count still scans colony JSON job state and must be revisited for scale; combat resolution and vacation protection are unchanged.

Verification: full local suite **267 passed, 144 skipped, one existing warning (495.09s)**. Focused SQLite + disposable PostgreSQL 18.6 PvP/vacation guard matrix **4 passed**. Frontend 53; Ruff, Black, strict mypy, ESLint, JavaScript syntax, npm audit 0, pip-audit no known vulnerabilities, traceability 344/344. Test container removed; persistent Main/Staging unchanged. Overall project remains partial and is not a release candidate.


## 2026-11-08 — Incoming attack index follow-up

The count-only warning now uses an indexed derived table instead of scanning colony JSON on each state response. Schema 25 backfills existing player-target attacks; `Game.save` maintains the index in the authoritative colony transaction, including removal on resolution. PvE attack targets are excluded. Final full SQLite pytest: **268 passed, 145 skipped, one existing Starlette/httpx warning (544.38s)**. SQLite + disposable PostgreSQL 18.6 migration, PvP and vacation cases: **6 passed**; frontend **53 passed**; Ruff, Black (21 files), strict mypy (16 source files), ESLint, JavaScript syntax and traceability pass. Inventory remains 4 verified / 160 partial / 89 unverified / 91 not audited. This is not a release candidate; persistent Main/Staging data and runtime were not modified.


## 2026-11-08 — Admin audit log pagination

Added 50-entry keyset pagination for the moderator audit view, with validated `(created,id)` cursor, current-role recheck and rate limit. The response omits actor and internal audit details not displayed by the UI. Final full SQLite pytest: **268 passed, 145 skipped, one existing warning (481.77s)**. Focused SQLite API/domain tests: **2 passed, 1 optional PostgreSQL parameterization skipped**; PostgreSQL 18.6 + SQLite domain cursor pair: **2 passed**. Frontend 54 and style/type/syntax/traceability gates pass. Release remains blocked by outstanding feature and external acceptance evidence; persistent Main/Staging are unchanged.


## 2026-11-08 — Public diplomacy chronicle pagination

The diplomacy history now presents the newest 50 events and offers cursor-validated older pages via an authenticated, rate-limited endpoint. This preserves the immutable source records and existing `(created,id)` index. Full SQLite pytest: **269 passed, 145 skipped, one existing warning (533.24s)**; focused PostgreSQL 18.6 + SQLite adapter pair **2 passed**; frontend 54 and code/traceability gates pass. The project is still partial and is not a release candidate; persistent runtime/data are unchanged.


## 2026-11-08 — Live-event state pagination

The Live-Ereignisse view now returns at most 50 active rows and provides older-event pages using schema-26 feed index and an authenticated cursor endpoint. All active event bonuses are still included through a database aggregate, so page size does not change production behavior. Full SQLite pytest: **271 passed, 146 skipped, one existing warning (513.70s)**; focused SQLite + PostgreSQL 18.6 adapter pair **2 passed**; frontend **55** and quality/traceability checks pass. Remaining broad product and launch gates stay open. No persistent database or service was changed.


## 2026-11-08 — Account session inventory pagination

Active session inventory is now bounded to 50 entries and uses authenticated-owner-scoped `(created,session_id)` keyset cursors. Tokens/CSRF are never returned; existing revocation flows are unchanged. Schema 27 adds the supporting owner feed index. Full SQLite pytest: **273 passed, 147 skipped, one existing warning (525.17s)**; focused PostgreSQL 18.6 + SQLite migration/index checks **4 passed**; frontend 55 and required code gates pass. Broad product, browser/accessibility, endurance and public launch gates remain open. Persistent DBs/services were not modified.

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


## 2026-11-08 — ENG-016 Imperiumsverzeichnis

Welt- und eigene Kolonielisten im Hauptzustand sind auf 50 Einträge begrenzt; authentifizierte Cursor-Endpunkte laden weitere Seiten. Kolonie-Cursor sind auf den angemeldeten Eigentümer beschränkt. Die UI bietet zugängliche „Weitere laden“-Bedienelemente. Die angezeigte Slotanzahl zählt jetzt nur Kolonien der aktiven Welt. Der vom Eigentümer bestätigte 24-Stunden-Kommandantennamen-Cooldown war bereits in Server, UI und exaktem Grenztest umgesetzt.

Prüfung: vollständiges SQLite pytest **277 bestanden, 150 übersprungen, eine bekannte Starlette/httpx-Deprecation-Warnung (480.92s)**; Kolonie-Cursor SQLite + isoliertes PostgreSQL 18 **2 bestanden**, Welt-API-Regressionsfall bestanden; Frontend **56 bestanden**; Ruff, Black, strict mypy, ESLint, JavaScript-Syntax, Staging-Compose und 344-ID-Traceability bestanden. Privates Loopback-Staging wurde nach geprüftem Backup `backups/fur-staging-pre-empire-pagination-20261108.dump` (227052 Bytes) nur bei App/Worker aktualisiert. Health 200, readiness true, Asset enthält beide Pager; Schema 28, 5 Benutzer/5 Kolonien. Main und persistente Datenbank-Volumes unverändert. ENG-016 und das Gesamtprodukt bleiben unvollständig; kein öffentlicher Produktionsbetrieb behauptet.


Follow-up within the 2026-11-08 ENG-016 directory package: gameplay retains the full active-world colony list (rule cap four; defensive query cap five) for map markers and same-world supply, while `empire_colonies` carries the bounded 50-row cross-world directory. The two-world join/switch regression confirms exact active-world counts and complete directory entries on SQLite and PostgreSQL 18 (4 executions passed). Final full SQLite suite after this separation: **277 passed, 150 skipped, one existing warning (492.55s)**. Frontend 56; all Python/UI/traceability gates pass. Final private Staging app/worker are healthy and ready; served app.js contains both load-more controls; schema 28 and 5 users/5 colonies remain.


## 2026-11-12 runtime/test delta — still NOT A RELEASE CANDIDATE

The current source passed 646 Python tests against SQLite plus isolated PostgreSQL 18; 1 test skipped, with one existing Starlette/httpx deprecation warning. Frontend 66/66, Ruff, Black, strict mypy, ESLint, JavaScript syntax, pip-audit and 344-ID traceability passed. Main local Docker app/worker run current source on schema 79 and both health/readiness probes return 200. Existing player/world counts were preserved after a validated pre-deploy backup and isolated restore drill. This does not satisfy full 344-feature acceptance, balance approval, browser/device/accessibility/localization, 30-minute load, two-world player lifecycle, remote CI/history, legal/asset SBOM or public operations requirements. No public endpoint was deployed.
