# Resume FUR Empire agent implementation

Read `RESUME_STATE.json`, `PROGRESS_LOG.md`, `AUDIT_CURRENT_FUR2.md`, `TRACEABILITY.md`, root `AGENTS.md`, the current game spec and architecture, then continue the exact `next_actions` in the resume state. Continue the active goal; do not restart the audit, overwrite backups, claim features verified without exact evidence, or stop at a demo. The product is the root Python/FastAPI app. Keep `Neuer Ordner/` source archives intact and treat them as references only. Current data backups are recorded in `RESUME_STATE.json`.


## Latest checkpoint — 2026-11-07

ACC-002 and ACC-009 are partial account-security implementations; T02 is partial with replay/double-spend/crash and eight-worker concurrency coverage. Latest full local suite: 218 passed/116 skipped/one existing warning; focused disposable PostgreSQL 18 cases passed. Feature counts: 2 verified, 134 partial, 26 unverified, 182 not audited. ACC-004 awaits the owner’s account-name cooldown rule. See `RESUME_STATE.json` and `PROGRESS_LOG.md`; persistent Main/Staging data remain untouched.

## Latest checkpoint — 2026-11-07

ACC-004 now implements the owner-selected 24-hour commander-name cooldown, case-insensitive uniqueness, password plus active-TOTP reauthentication, migration 018, custom-colony-name preservation and player-name projection updates. ACC-006 is a reauthenticated CSRF-protected allowlisted account JSON export. Full local suite: 221 passed/118 skipped/one existing warning (575.65s); focused disposable PostgreSQL 18 ACC-004/ACC-006 adapter set: 4 passed; frontend 36; Ruff, Black (21 files), strict mypy (16), ESLint, JS syntax and traceability pass. Inventory: 2 verified, 136 partial, 26 unverified, 180 not audited. Both features remain partial pending browser/mobile/accessibility; export also needs complete data inventory and privacy/legal review. Migration 018 is source-only; persistent Main/Staging and player data unchanged.

ACC-005 audit found no avatar upload/storage/validation/moderation and no accepted-format/size/retention policy; ACC-007 has no delete/anonymize flow and lacks retention/shared-content rules; ACC-008 has only verification/reset email with no game notification preferences or category/consent policy. All three are unverified. Current inventory: 2 verified, 136 partial, 29 unverified, 177 not audited. Continue with the next independently contract-defined package; do not infer destructive retention or identity recovery rules.

Latest ENG-003 follow-up: expeditions now pin exact SHA-256 of the active FUR-3 expedition rules at dispatch; processing rejects altered/unavailable snapshots before resolving. Outcome, audit and report include the digest. Focused SQLite rules tests 4 passed (2 PG skips because FUR_TEST_POSTGRES unset); full suite 222 passed/118 skipped/one existing warning in 502.52s; Ruff, Black and strict mypy passed. Counts 2 verified, 137 partial, 29 unverified, 176 not audited. Continue auditing/implementing E08/E06 dependency items; keep speculative FUR-3 separate and do not mark ENG-003 verified while Orbit catalog is absent.

Latest continuation 2026-11-08: E01/E07 moved to partial after catalog-driven declaration/validation/server enforcement/UI display of existing FUR-2 unlocks (Lab 1 for research; Barracks 1/2/3 for units). No new balance values. E02 specialty buildings audited and marked unverified because prices/unlocks/slots/energy/effects are undefined. Full local pytest 223 passed/118 skipped/one existing warning (1026.82s); focused prerequisite 5 passed/1 PG skip; frontend 37; Ruff, Black, strict mypy, ESLint, JS syntax and traceability pass. Current counts 2 verified, 139 partial, 30 unverified, 173 not audited. Continue E06/E08 with defined FUR-2 contracts; do not invent FUR-3 effects or deploy source-only changes to persistent runtime.

Latest continuation 2026-11-08: E04 build/research jobs now pin rule version, catalog SHA-256, base cost and formula. Replanning preserves these original reserved prices across catalog changes; legacy jobs infer the base cost from stored reservation and target level only when consistent. No migration or persistent database change. Regression test passed; Ruff, Black and strict mypy passed. Full Python suite: 224 passed/118 skipped/one existing warning (429.57s). Counts remain 2 verified, 139 partial, 30 unverified, 173 not audited. Continue E06/E08; E04 remains partial pending full browser/mobile/accessibility and lifecycle acceptance.

Latest continuation 2026-11-07: E08 and ECO-016 audited against the actual FUR-2 effects and master concept. Only existing passive Pioneer/Warden/Syndicate bonuses are concretely specified and implemented. The concept's faction-specific technologies, units and actions lack IDs, effects, costs, unlock prerequisites and balance caps; both IDs are unverified pending a complete approved catalog. No speculative game rules were added. Full pytest remains 224 passed/118 skipped/one existing warning; Ruff, Black, strict mypy and traceability pass. Counts: 2 verified, 139 partial, 32 unverified, 171 not audited. E04 remains partial; persistent database/player data untouched.

Latest verification after adding the E04 research queue snapshot regression: focused build+research tests 2 passed; full pytest 225 passed/118 skipped/one existing warning (408.77s); Ruff, Black, strict mypy and 344-ID traceability pass. E08/ECO-016 status remains unverified pending an approved balanced faction catalog. Counts: 2 verified, 139 partial, 32 unverified, 171 not audited.

Latest package 2026-11-07: ECO-010 market-history query now excludes future timestamps and has regression coverage for the 60-hour-bucket cap. Backfill is explicitly not part of the FUR-2 spec; history is already world-scoped. Full suite on SQLite + disposable PostgreSQL 18: 344 passed/1 skipped/one existing warning (1194.19s); Ruff, Black, strict mypy and 344-ID traceability pass. Temporary no-volume PostgreSQL removed; persistent Main/Staging untouched. E06/ECO-010 remains partial pending browser/mobile/accessibility acceptance. Counts remain 2 verified, 139 partial, 32 unverified, 171 not audited.

Latest checkpoint 2026-11-07: E06/ECO-010 verified after disposable browser acceptance at 710px desktop and 390px mobile. Both completed-trade aggregates render anonymously; accessibility tree exposes a labeled list and two listitems; no horizontal overflow. Frontend 37 passed, ESLint and JavaScript syntax passed. Full SQLite + disposable PostgreSQL 18 suite: 344 passed/1 skipped/one existing warning (1194.19s); Ruff/Black/mypy and 344-ID traceability pass. Temporary browser server/DB and PostgreSQL container removed; Main/Staging untouched. Current counts: 4 verified, 137 partial, 32 unverified, 171 not audited. Continue the active goal; E08/ECO-016 await a complete faction catalog.


## Latest checkpoint — 2026-11-07

E06/ECO-013 production presets are implemented as partial: schema 019 adds account-owned build/research/train templates; save/list/delete and queue UI routes enforce CSRF; queueing calls the normal game command with active-colony checks, production email verification and idempotency. Personal export includes only owned presets. Full SQLite + disposable PostgreSQL 18 suite: 348 passed, 1 skipped, one existing Starlette/httpx warning (1377.57s). Focused API/migration tests 4 passed; frontend 38 passed; Ruff, Black, strict mypy, ESLint, JS syntax, traceability, Docker Compose configuration and Main/Staging readiness passed. Interactive browser actions were unavailable, so mobile/accessibility acceptance remains open. Migration 019 is source-only; persistent Docker databases, volumes and player data unchanged. Inventory: 4 verified, 140 partial, 36 unverified, 164 not audited. Continue the active goal; do not claim full game completion or public production readiness.


## Latest checkpoint — 2026-11-07

E09/A05/SOC-010/SOC-011 contacts and blocklists implemented as partial in source migration 020. Contact requests require acceptance; pending request lifecycle and account-only lists are supported. Blocking removes an accepted contact, denies private messages both ways, hides the blocker's identity from the blocked player, and leaves moderation/old messages independent. Full SQLite + disposable PostgreSQL 18 suite: 355 passed/1 skipped (backup/restore drill; PostgreSQL dump/restore tested separately)/one existing warning in 1354.48s; focused PostgreSQL social adapter: 6 passed; frontend 39 passed; Ruff, Black check, strict mypy, ESLint, JS syntax, traceability, Main/Staging Compose configuration and readiness passed. Main/Staging report ready with zero quarantined jobs; migration 020 remains unapplied to persistent databases. `pip-audit --local` found four local pip 26.1.1 advisories; do not upgrade or alter locks silently. Counts: 4 verified, 143 partial, 36 unverified, 161 not audited. Browser/mobile/screen-reader and broad 344-feature acceptance remain open. Continue active goal and audit a fully specified adjacent feature; release remains NOT A RELEASE CANDIDATE.


## Profile audit checkpoint — 2026-11-07

A07/SOC-012 reviewed against code and tests: only public name/aggregate score ranking exists; no profile/history route, title/badge model or privacy preferences. Public stats/history fields and retention require product policy, so both are unverified and no implementation was invented. Counts 4 verified, 143 partial, 38 unverified, 159 not audited. Continue independent roadmap items; keep goal active.


## Latest checkpoint — 2026-11-07

E09/SOC-013 + E10/A08 implemented as partial: schema 021 adds private account/world-scoped notes to coordinates and own reports, one editable/deletable note per target with a 500-character limit. Server enforces owner/world/report checks and audit; Messages UI escapes and binds forms to the standard command; personal export includes owner notes only. Full SQLite + disposable PostgreSQL 18 suite: 360 passed, one separate backup/restore drill skipped (PostgreSQL dump/restore tested independently), one existing warning (1658.81s); focused PostgreSQL note/social cases 6 passed; local note/API/export focus 5 passed; frontend 40 passed. Ruff, Black, strict mypy, ESLint, JavaScript syntax, 344-ID traceability, Main/Staging Compose configuration and readiness passed. Main/Staging ready with zero quarantined jobs; migrations 020/021 remain unapplied to persistent DBs. `pip-audit --local` reports four local pip 26.1.1 advisories; no upgrades/lock changes. Inventory 4 verified, 145 partial, 38 unverified, 157 not audited. A07/SOC-012 remain unverified pending profile privacy policy; A08 shared planning/report-sharing and browser/mobile/screen-reader acceptance remain open. Continue goal; release NOT A RELEASE CANDIDATE.


## SOC-014 audit checkpoint — 2026-11-07

Battle reports remain in private owner-colony state; no share table/command/recipient authorization/UI exists. Current combat objects may contain hidden identifiers. Share-field allowlist, revocation, retention and membership-change access are unspecified; SOC-014 is unverified pending approved safe-disclosure rules. No code or data change. Inventory: 4 verified, 145 partial, 39 unverified, 156 not audited. Continue active goal.


## SOC-015 moderation audit — 2026-11-07

Role-checked mute/hide and admin ban/unban are present with immutable audits and regressions; end-user message reports and appeals are absent. SOC-015 marked partial. Report/case and appeal workflows need defined privacy, review and response rules before implementation. Counts 4 verified, 146 partial, 39 unverified, 155 not audited. Continue active goal.


## SOC-016 audit checkpoint — 2026-11-07

No announcement/mailbox implementation exists in root app. Sender roles, public audience/world scope, recipient selection, retention/deletion and read receipts are unspecified; SOC-016 unverified pending product rules. Inventory: 4 verified, 146 partial, 40 unverified, 154 not audited.


## SOC-009 continuation — 2026-11-07

Migration 022 implements the moderated alliance bulletin. Leader/officer create/edit/archive, member-only chronological view (including archived records), 80-char titles, 2,000-char text, CSRF/idempotency, audit without body, server-side ACL, escaped UI. Full local pytest 239 passed/127 skipped/one existing warning; focused SQLite/API/disposable PostgreSQL 18: 5 passed; frontend 41; Ruff/Black/mypy/ESLint/JS syntax pass. browser/mobile/screenreader acceptance remains open; cursor pagination for older records now passes; migration is source-only and persistent Main/Staging untouched. Inventory 4 verified, 147 partial, 40 unverified, 153 not_audited. Continue active goal with the next independently specified roadmap item.


## 2026-11-18 checkpoint

Root source is at schema 119. Read the latest PROGRESS_LOG.md, TRACEABILITY.md and RESUME_STATE.json. E11 PVE-004–008 have focused evidence and remain partial. The selected boss payout is damage-weighted and capped. PVE-009 awaits the convoy PvE/PvP participation rule. The guarded full SQLite suite passed with 604 passed and 299 optional PostgreSQL skips; the disposable runtime reached readiness. Read the local SQLite incident record and preserve both backups before any operational change.
