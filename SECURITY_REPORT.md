# Security report — bootstrap status

## 2026-11-18 focused checks

Ruin dispatch and recall use authenticated CSRF-protected commands. The active world and known sector are checked before travel, the mission seed stays server-side, and the intel read model is scoped by observer and world. Boss scheduling is restricted to administrators, attacks and claims are scoped to the active world and account, and a parallel-claims regression passed on SQLite and PostgreSQL 18.

The locked dependency scan reported four distinct advisories. `certifi 2026.7.22` was reported twice for `PYSEC-2026-4320`. `urllib3 2.7.0` was reported for `PYSEC-2026-4175`, `PYSEC-2026-4176` and `PYSEC-2026-4177`. The Node audit reported zero vulnerabilities. The Python dependency gate is open. Git history scanning and hosted CI evidence remain unavailable in this checkout.

The data-isolation incident and remediation are recorded in the progress log. Pytest now clears production database overrides and sets its root-level fallback to a temporary SQLite file before it imports application modules. Adapter tests continue to use the explicit disposable PostgreSQL URL.

## Existing controls observed

- Password hashing, server sessions, CSRF header, same-origin/host controls, rate limits, HTTP security headers, TOTP support, verified-email production gate, role checks, parameterized SQL, escaped user content, transaction/idempotency logic, worker quarantine, and Docker hardening are present in the root application.
- The local Docker listener remains bound to loopback (`127.0.0.1:8081`). No public profile was started in this run.
- `.env`, `.secrets/`, `data/`, backups, and `Neuer Ordner/` are not intended for commits. No Git history exists to inspect.
- The nine supplied repositories remain references only; no source or asset was copied into the product.
- CI now declares a full-history Gitleaks scan. It cannot be run against this local checkout because `.git` is absent; GitHub Actions has not yet executed it. Python `pip-audit` and `npm audit --audit-level=high` reported no known vulnerabilities. Python and Node CycloneDX SBOMs generated locally (21/87 components).

## Open security work

- Repository-history secret scan and safe branch checks are impossible locally without `.git` metadata; the configured CI scan still needs a real GitHub run. The SBOM job does not yet produce an image SBOM or consolidated license notices/gate.
- The supplied separate source-license pack is incomplete; its consolidated license table is research, not legal clearance. No direct reuse is planned.
- Complete abuse/rate-limit, world-boundary authorization, threat model, restore, and production proxy/mail review under E16/E19.
- Keep all new gameplay server-authoritative and ensure every world-owned entity is checked against the authenticated world/player before read/write.

**Status:** preliminary audit only; not a public production security approval.



## Staging-specific evidence

A private `fur-staging` Compose project is isolated from the main Docker project and its player data. App, worker, PostgreSQL and Mailpit have no host-published ports; Caddy publishes HTTPS 8443 and Mailpit UI 8025 to loopback only. Staging runs with strict session/origin settings and local-only SMTP capture. Login, session cookie, CSRF-protected command and readiness smoke passed. Local Caddy CA is not publicly trusted. This is not a production security approval; remote CI/history scanning, browser-driven E2E, full license gate, image SBOM and external deployment review remain open. The staging API smoke script validates the secure cookie and CSRF flow, but does not replace browser coverage.

## E05 restore and migration rehearsal — 2026-11-06

Current Main schema-8 backup restored into disposable PostgreSQL 18 and upgraded through schema 11. Row-count preservation was verified for users, colonies, worlds, normalized outposts and terrain. Temporary container was removed; persistent databases were not migrated. This validates one local restore path only, not production security or disaster-recovery readiness.

## TERRA-009 colony abandonment review — 2026-11-06

Secondary-colony abandonment is owner-scoped, requires an exact colony-name confirmation, rejects outstanding colony jobs/inbound supplies/open market escrow, preserves an immutable colony-state ledger snapshot and audit details, and updates the active-colony profile in the same transaction. API mutations retain CSRF protection and the UI escapes names/IDs and requires browser confirmation. Focused SQLite and disposable PostgreSQL 18 domain regressions, API CSRF/home-protection, and frontend escaping/confirmation checks passed. The home colony remains protected; no item inventory exists to resolve. This is focused feature evidence, not a comprehensive authorization/security audit.

## TERRA-012 world-scoped map favorites — 2026-11-06

Map favorites are private to the account and active world; the server validates that the target belongs to that world and its sector is known. The per-world quota now counts `(user_id, world_id)`, preventing a player's bookmarks in one world from consuming another world's quota. A two-world regression passed on SQLite and disposable PostgreSQL 18. This does not constitute a broader security audit; browser/accessibility acceptance remains open.

TERRA-012 route preview follow-up — 2026-11-07

The browser computes a non-mutating route preview only over terrain already disclosed to that player and treats unknown sectors and impassable water as blocked. The rendered route coordinates and destination use escaped text; the route is not persisted. Frontend unit coverage passed, but browser and assistive-technology acceptance remain outstanding.

## TERRA-011 conversion security review — 2026-11-07

The command uses the existing authenticated, CSRF-protected, idempotent transaction path. It validates active-world ownership, cleared status, exact target-name confirmation, visibility, slot, HQ, spacing, reachability, costs and stored stock/garrison types before mutation. SQL is parameterized; conversion state, map/outpost removal, bookmark cleanup, capture-score adjustment and audit roll back together on error. The browser escapes target IDs/names and asks for explicit confirmation. SQLite and disposable PostgreSQL 18 positive/rejection cases pass; API contract and frontend escaping tests pass. This is scoped feature evidence, not a full authorization or penetration audit. Browser/accessibility acceptance and owner review of the new rule are pending.

## TERRA-014 spawn/claim boundary review — 2026-11-07

Genesis and world-join placement enforce the same six-sector separation from existing colonies; explicit starts inside the protected radius are rejected. Expansion checks same-world ownership, known/free land, a walkable path and distance before its transactional resource debit/claim. Existing world/sector uniqueness remains the final duplicate-claim guard; no reservation state or migration was added. Local regression suite and one disposable PostgreSQL 18 spawn-spacing test passed. This is focused evidence, not a full authorization/security audit. Browser/mobile/accessibility review remains open.

## TERRA-013 alliance boundary review — 2026-11-07

Alliance regional boundaries are derived from actual world outpost owners and current alliance membership using the existing minimum-two/strict-majority threshold. Ties have no controller. The payload continues to suppress all control counts until a region is fully surveyed; membership changes participate in cache invalidation. No alliance production or personal score was introduced. SQLite/PostgreSQL 18 adapter cases and escaped frontend rendering tests passed. This is scoped feature evidence, not a complete security audit; browser/mobile/accessibility review remains open.

## TERRA-003 starting-resource check — 2026-11-07

The fresh colony is placed on non-water terrain and receives fixed starter resources plus all three level-1 resource producers. The test asserts that every resource stock covers the largest corresponding level-1 building cost and that the account is within its 3,600-second newbie shield. This verifies resource availability at creation, not the fairness of terrain/resource-target distance across seeds. SQLite/PostgreSQL 18 adapter cases pass; no broader security claim.

TERRA-003 final adapter/full-suite follow-up (2026-11-07): fresh-account starting resources/production and newbie shield passed SQLite and disposable PostgreSQL 18 adapter cases. No cross-world terrain/target parity, browser/mobile/accessibility security acceptance or comprehensive security audit is implied.

Traceability guard (2026-11-07): CI now checks all feature IDs and prevents duplicate/missing rows or status drift. This is an inventory-integrity control, not a security audit.

TERRA-001 generation regression (2026-11-07): verified seed determinism for terrain/outpost metadata and walkable resource-target reachability on the tested seed across SQLite/PostgreSQL 18. This is not a broad seed-space or security proof; full seed matrix remains open.

TERRA-002 race follow-up (2026-11-07): synchronized same-sector claims verify a single winner and single resource debit on SQLite/PostgreSQL 18. This does not replace authorization/fog audits or broad stress testing; cross-table consistency remains enforced in the serialized command transaction.

TERRA-004 multiworld privacy follow-up (2026-11-07): sector observations remain observer/world-scoped across a world switch on SQLite and PostgreSQL 18. Unknown terrain stays omitted. This does not complete alliance-sharing, all mutation endpoint tests, or a broad security audit.

TERRA-005 adapter follow-up (2026-11-07): full capped territory bonus is verified on SQLite/PostgreSQL 18 and remains outside personal ranking. Browser/accessibility display and broad account authorization review remain open.


ECO-006 (2026-11-07): Added concurrency regression ensuring a queued prerequisite does not authorize research before the building is completed; SQLite and PostgreSQL 18 passed. This is targeted authorization/race evidence only and does not constitute a full security audit.


ECO-010 (2026-11-07): Added SQLite/PostgreSQL 18 evidence that market aggregates exclude trades from other worlds and disclose no account identifiers. This is focused data-isolation coverage, not a complete endpoint or security audit.


F2-004 (2026-11-07): Stale CSRF state is refreshed only after the exact server mismatch response; frontend retries once, preserving request body/idempotency token. Server-side Origin/CSRF gates remain authoritative. API and frontend regression tests pass. Multi-tab browser acceptance remains; this targeted fix is not a complete security audit.


OPS-008 (2026-11-07): A route-level negative regression now verifies the command rate limit rejects request 91 after 90 unauthenticated attempts. Existing focused tests cover CSRF/session rotation, escaped untrusted HTML and foreign colony supply denial. This remains partial; exhaustive IDOR matrix, broader XSS/browser tests and penetration testing are outstanding.

OPS-008 full validation (2026-11-07): rate-limit regression passed; complete suite 165 passed/80 skipped/one existing warning, plus frontend security regressions. No broad penetration test or complete IDOR route matrix has been performed.

Dependency scan (2026-11-07): pip-audit on 
equirements.lock with --no-deps --disable-pip passed and reported no known vulnerabilities. It warned that transitive dependencies/hashes were not fully audited; no dependencies were changed.

OPS-015 restore drill (2026-11-07): disposable PostgreSQL 18 restore verified logical DB and mission SHA-256, plus resources and scoped map rows. No production data touched. This is backup integrity evidence, not an application penetration test.

OPS-013 targeted isolation suite: eight SQLite/PostgreSQL adapter cases passed for world chat/offers, colony resource dispatch denial, anonymized market history, terrain/outpost state and private fog observations. No separate items subsystem exists; exhaustive endpoint/object authorization and browser validation remain open.


OPS-010 property regression update (2026-11-07): deterministic seeded economic commands and idempotent replay pass on SQLite and disposable PostgreSQL 18 with nonnegative resource/reserve/unit assertions. This is game-state correctness evidence only; it does not replace fuzzing, endpoint authorization review or penetration testing.


W10 NPC fog boundary (2026-11-07): the API aggregates faction outpost counts/pressure only from currently visible neutral posts. A regression places the visible posts explicitly and verifies threat calculations; unknown/stale coordinates are not used for the aggregate. Frontend faction names are HTML-escaped. This does not replace a complete authorization/security review.

W10 final privacy regression: a not-visible neutral outpost with stored NPC pressure is not included in the map faction aggregate; two focused SQLite tests and one adapter scenario on SQLite/PostgreSQL 18 pass. This is scoped fog-disclosure coverage only.


K03 arrival-time scout authorization (2026-11-07): focused SQLite/PostgreSQL 18 regressions disable PvP or activate defender vacation protection after dispatch. Arrival rejects disclosure, emits one abort report, and returns Ranger units once; repeat advancement has no duplicate effect. This complements but does not replace a full security review.


K07 mission recall (2026-11-07): recall operates only on the authenticated active colony’s own outbound job ID and supported job kinds. Return army/cargo remains transactional and is audited; idempotency prevents duplicate recalls. Focused SQLite/PostgreSQL 18 tests cover all six supported kinds. This is scoped behavior evidence, not a complete security review.


K07 scoped security evidence (2026-11-07): recall is owner/colony/job scoped, transactional, audited and idempotent; SQLite/PostgreSQL 18 coverage spans six mission types. No full security audit is implied. Main and staging app/worker were updated app-only; database containers and volumes were not changed. Local staging HTTPS probe failed TLS InternalError; staging readiness is unconfirmed.


K04/WAR-005 scope checks (2026-11-07): CSRF-protected authenticated read-only gameplay projection rejects unknown sectors, owned posts and unavailable units; tests compare persistent colony/outpost JSON and audit/ledger counts before/after. The API rate limiter still records its operational request counter. This is scoped evidence, not a full security audit. App-only rollout kept DB containers and data volumes unchanged.

PostgreSQL adapter follow-up: the fog-scope/no-gameplay-mutation regression also passed on disposable PostgreSQL 18; the temporary no-volume test container was removed.


WAR-020 grid adds 24,336 deterministic combat-input cases checking repeatability, bounded casualties and no unit creation. This is gameplay correctness coverage, not a penetration/security audit. A temporary local browser page was served from isolated SQLite only; no login/session UI flow was exercised. Temporary server/database were removed.

## 2026-11-07 continuation — K13 and migration 013

K13 endpoints enforce session CSRF, per-route rate limiting, strict payload/name/unit bounds, account ownership, case-insensitive duplicate prevention and a ten-profile cap. SQL migration is additive with owner foreign-key cascade and scoped uniqueness; pre-migration Main/Staging PostgreSQL backups were created and archive listings validated before rollout. Both local services are healthy/ready and existing data counts match. No public deployment occurred. Schema-13 restore drill remains unverified because PostgreSQL client binaries are unavailable on the host; no persistent data was used for restore attempts.

Schema-13 restore follow-up passed in an isolated PostgreSQL 18 environment using two disposable databases. Exact logical database and pending-mission checksums matched, and temporary resources were cleaned up. Persistent Main/Staging data were not used.

## 2026-11-07 K08 / schema 014 security scope

Expedition dispatch checks the active colony, known neutral target and available unit counts; units remain escrowed until the return/recall lifecycle resolves transactionally. Rewards are capacity limited and result/audit ownership is scoped. Focused SQLite/PostgreSQL 18 regressions cover deterministic outcomes, bounds, invalid targets, unavailable units, return-once, recall and template ownership/schema preservation. This is scoped feature evidence, not a full penetration test. Main and private Staging were upgraded only after pre-migration backups and remained healthy; no public deployment occurred.

## 2026-11-07 — WAR-016 arrival-time checks

Player attacks revalidate PvP enablement, both account-age windows, defender vacation, alliance membership and accepted NAP at arrival. Four adapter regressions change PvP/vacation/beginner protection/NAP after dispatch and verify no battle state mutation plus exactly-once army return. This is scoped gameplay authorization evidence, not a full penetration test. Formal war-declaration requirements remain unspecified.

## Current continuation security evidence — 2026-11-07

ACC-002 adds ten one-time TOTP recovery codes, stores only SHA-256 hashes, consumes a code transactionally at login, and requires password plus fresh TOTP to regenerate. ACC-009 adds five login attempts per account/client-network per minute using a hashed account bucket, alongside the existing client-wide auth limit. Login and password-reset responses are non-enumerating. These scoped controls have SQLite tests and disposable PostgreSQL 18 adapter coverage; the UI received frontend tests. Ruff, strict mypy, frontend lint/syntax and the full local suite pass. This is not a complete penetration test or public security approval. Distributed abuse detection, account lockout operational policy and browser/accessibility acceptance remain open; Main/Staging were not updated.

## 2026-11-07 account-security continuation

ACC-004 account-name changes require current-password verification and a fresh TOTP when enabled, enforce a case-insensitive unique name and a 24-hour cooldown, and audit the change. Schema 018 records only the last-change timestamp. ACC-006 personal-data export is CSRF protected and reauthenticated; it allowlists owned account/game data and excludes password, TOTP/recovery material, session tokens and communications containing third-party content. SQLite and disposable PostgreSQL 18 regressions passed. A complete privacy data inventory/legal-retention review and interactive browser/accessibility acceptance remain outstanding; this is not a legal-compliance claim.


## SOC-009 alliance bulletin boundary — 2026-11-07

Schema 022 stores announcements under the owning alliance. Every mutation re-resolves the authenticated actor's current membership and leader/officer role inside the normal transaction; update/archive queries include the authorized alliance ID. State returns bulletin content only for current members. Bodies are escaped in the UI, bounded to 2,000 characters and omitted from immutable audit details. API CSRF and membership-isolation tests passed on an isolated SQLite fixture; domain/migration cases also passed against disposable PostgreSQL 18. The migration was not applied to persistent databases. No browser-based signed-in authorization test was performed; this is feature-level evidence, not a security approval.

## E09 SOC-008 alliance forum review — 2026-11-07

SQLite and disposable PostgreSQL 18 regressions cover current-membership authorization, leader/officer moderation, duplicate pending report rejection, muted-write denial, archive behavior, CSRF and nonmember visibility. Report reasons and post bodies are not copied into audit details; escaped rendering is covered by frontend tests. Browser-driven authorization/XSS review, accessibility and mobile checks remain open. Migration 023 remains unapplied to persistent Main/Staging. This focused review is not a comprehensive security audit or production approval.

## E09 SOC-004 public diplomacy chronicle — 2026-11-07

Migration 024 stores only alliance tags, event type, actor alliance and timestamp. Every authenticated player receives at most the latest 100 events; no player identity, message text, or report content is exposed. SQLite and PostgreSQL triggers reject event UPDATE/DELETE, and the FK policy prevents deleting referenced alliances from erasing the history. Focused adapter tests cover nonmember visibility and immutability. The history includes only events after migration 024; older diplomacy has no retroactive record. This narrow review is not a full security or production approval.


## 2026-11-08 — Verzeichnis-Cursor-Scope

Die neuen Welt- und Kolonielisten geben maximal 50 Einträge zurück. Cursor für Kolonien werden über den Eigentümer der aktuellen Sitzung aufgelöst; fremde oder unbekannte Kolonie-IDs werden abgewiesen. Welt-Cursor akzeptieren nur vorhandene Welt-IDs. Die bestehende Authentifizierung und Rate-Limitierung gelten für beide Endpunkte. SQLite- und PostgreSQL-18-Domainregressionen bestanden. Keine neue Geheimnis- oder öffentliche Betriebsfläche wurde hinzugefügt.


## 2026-11-12 deployment note

The main local Docker app and worker run the current build on schema 79. The host listener is still bound to 127.0.0.1:8081; no public endpoint was enabled. A pre-deploy database dump was archive-validated and restored into isolated PostgreSQL 18 with matching row counts before updating the local stack. The test container was removed afterwards. This is operational evidence, not production security approval.
