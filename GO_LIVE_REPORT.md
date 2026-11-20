# FUR Empire go-live report

Status is partially deployed with public HTTPS. Full production acceptance remains open.

## Verified
- Domain apex and www point to 62.83.116.160 on authoritative DNS.
- Valid public TLS, HTTP redirect and www canonical redirect.
- Public frontend HTTP 200 and backend readiness true.
- Registration, secure cookies, login, authenticated state, CSRF logout and HTTP 401 after logout.
- Test email delivered internally and consumed through normal verification API.
- Test wood build completed, identical-token retry stored once.
- Barracks and laboratory completed. Research, ranger training and test alliance creation accepted.
- PostgreSQL persistence across service restart and full VPS reboot.
- Imported 4,848 rows from preserved local SQLite copy, initially one player/colony.
- Database backup and isolated restore drill passed. Daily backup scheduler and manual off-host copy.
- Monitoring timer and certificate refresh timer pass.
- Release script completed multiple deployments.
- Ruff, Black, strict mypy and 105 frontend tests passed.
- Targeted certifi/urllib3 updates deployed. Lockfile audit reports no known vulnerabilities.

## Open
- User action-time confirmation to remove netcup Mail block, then external delivery test.
- Admin email verification and MFA.
- Full Python suite still running. PostgreSQL integration suite pending.
- Research and training completion, multiplayer interaction, combat and browser/mobile acceptance.
- Application rollback rehearsal, automated external backup and retention enforcement.
- SMTP gateway discovery/configuration for fresh deployments and Staging isolation verification.
- Rotate credentials previously disclosed in chat through user-controlled credential flows.
- Complete operator-facing operations documentation and final acceptance.

Tests use GoLiveTest20261120 and alliance GLTEST. Imported player data is preserved. Test credentials are stored only under .secrets.

## Multiplayer verification
Second test account accepted the GLTEST invitation through the public command API. An alliance chat message sent by the first account appeared in the second account's messages. Database confirms two GLTEST members.
The test script's final additional assertion used the absent field alliance and failed after the chat assertion had passed. Membership was verified independently in PostgreSQL. No application failure was observed.
One public frontend GET measured HTTP 200 in 0.225 seconds from the development computer. This single measurement is not a load-capacity estimate.

## Public asset verification
All 17 static resources directly referenced by the public HTML returned HTTP 200 with nonempty content, including app/community JavaScript, CSS, wordmark, favicon and navigation graphics.
Rewrote PRODUCTION_ARCHITECTURE.md to reflect installed services and current limits rather than historical setup notes. A follow-up app/worker restart and test-state persistence check is in progress.

## Application rollback rehearsal
With database schema unchanged, stopped app/worker, switched to the pre-UI-change image, started both and confirmed readiness true. An EXIT handler restored the current image and both services passed healthchecks. A backup preceded the drill. No database downgrade was attempted.
Added Deploy-FUR-Empire.ps1 as the local source packaging/SSH transfer entry point. It preserves server source in releases before extraction and invokes release.sh. PowerShell syntax validation passed; a full invocation remains pending.

## Deployment entry point and PostgreSQL integration
Full local Deploy-FUR-Empire.ps1 transfer/build/update invocation started. Private staging Compose configuration validation passed after current changes.
A separate disposable PostgreSQL 18 container named fur-go-live-test-pg was created locally, bound only to loopback port 55439, for PostgreSQL-selected regression tests. It uses no production data.
Production inventory shows Testkommando is the imported player account, with no admin or MFA configured. User selection of an owner/admin account was requested. Test accounts remain ordinary players.

## Local-to-production deployment and retention
Deploy-FUR-Empire.ps1 completed successfully, including SSH transfer, pre-update source archive, database backup, build, migration and healthy services.
Backup retention now keeps every dump from the last 30 days and at least ten additional older archives. Only regular files matching the FUR timestamp naming pattern are candidates, and pg_restore --list must validate each candidate before removal. Current archives are recent, so none were removed during the initial successful run. Scheduler was recreated to bind the updated script.
Testkommando was promoted to administrator after explicit owner selection. Email verification and MFA remain pending.

## Bounded public performance probe
20 public health endpoint requests with concurrency four all succeeded. Median 267 ms, p95 11,253 ms, maximum 11,482 ms. High outliers require connection/DNS timing investigation. This measures the probe path only and does not establish game capacity.
Runtime sample showed approximately 69 MiB app, 55 MiB worker, 39 MiB proxy and 41 MiB database. Monitoring reports success. Recreated backup scheduler created a fresh archive successfully.

## Public authorization checks
Ordinary verified player requests to admin users, audit and operations endpoints were rejected. Required paging cursor was supplied for users/audit so the authorization branch was exercised. Missing-CSRF game commands were rejected and foreign-origin commands returned HTTP 403.
Both original SQLite/default suite and PostgreSQL-selected regression processes remain live and produce continuing progress. Neither has a final result yet.

## Monitoring coverage
monitor.sh now explicitly requires app, worker, database, proxy and backup-scheduler containers to exist and be running. It also records restart counts. Initial normal-state run passed. A controlled stopped-scheduler detection drill is in progress with automatic scheduler restart on exit.

## Completed PvE acceptance
The neutral raid against Aschewacht completed through the production worker. Persisted report records attack 220 versus defense 55, victory, four ranger losses and twelve survivors. Return report records 160 wood, 160 stone and 160 ore delivered. Jobs queue is empty. This verifies dispatch, combat resolution, loss accounting, return and loot persistence for the FUR-2 neutral raid path.
Monitoring remains successful. Strict readiness still reports admin_mfa_ready false. Provider SMTP policy confirmation remains outstanding.

## Immediate live delivery preference
Owner requested immediate live delivery of working changes. Current language package deployment started after 110 frontend tests, five server i18n tests, account-language persistence/security test and isolated account-security regression passed. Original full suite had one account-security failure that did not reproduce in isolation, requiring broader follow-up.
The package includes partial four-language coverage, persistent account preference migration 122 and opt-in localized API error keys. It is not full four-language acceptance. Beta password confirmation/consent and full translation remain pending.

Owner supplied responsible operator as Talent Link Ltd & Co. KG, currently in formation. Production operator name updated to Talent Link Ltd & Co. KG (in Gründung). Public company address and designated company contact remain unspecified.

Four-language beta API lifecycle passed for registration, internal email verification, login, build submission, state reload, logout and relogin. This does not verify external email delivery or full browser coverage. Operator is Talent Link Ltd & Co. KG (in Gründung), with public address still pending.

## 2026-11-20: Structured report localization live
Release 20261120T115934Z deployed after a fresh PostgreSQL backup. New building, research, training, neutral combat and resource-return reports retain historical text and add translation keys and parameters. Browser renders these keys in de/en/es/fr and retains legacy text for older reports. No gameplay values changed.
Validation: 113 frontend tests passed; targeted report regression passed; Ruff, Black check and strict mypy passed. Public HTTPS readiness returned ready=true, quarantined=0 and scheduler lag=0. Public English catalog and report renderer were fetched successfully. Full Python and PostgreSQL regression runs remain pending, so full acceptance is not claimed.
Operator: Talent Link Ltd & Co. KG (in Gründung), as supplied by owner. Public company address and designated contact remain pending. External email delivery, owner admin MFA and complete translation coverage remain open.

## 2026-11-20: Four-language section headings
Added explicit central translation keys for 21 existing headings across colonies, worlds, inventory, trade, reports, rankings, first-campaign help and operations. ESLint, JavaScript syntax check and all 113 frontend tests passed. Existing game logic and player data unchanged. Local migration export moved from build-artifacts to .secrets to reduce accidental packaging exposure.

Current checklist:
- [x] Public HTTPS frontend, API and persistent production database deployed.
- [x] Backup and isolated restore drill, restart and rollback verification.
- [x] Four-language selection, account preference and beta API lifecycle verified.
- [ ] Complete translation of all advanced UI and server notifications.
- [ ] External email delivery and public registration browser acceptance.
- [ ] Owner admin email verification and authenticator setup.
- [ ] Public company address and designated contact.
- [ ] Final full Python/PostgreSQL regression outcomes and final production acceptance.

## 2026-11-20: Guide and core economy localization
Translated all five existing campaign-guide paragraphs and core building/research queue guidance, troop requirements and unit statistics in de/en/es/fr. Unit statistics use text-only interpolation parameters. Translation now runs after supplementary world panels are appended. Existing rules and server state remain unchanged. Complete advanced UI translation remains pending.

Release 20261120T120839Z completed with pre-deployment backup and healthy app/worker/database. Public HTTPS checks fetched guide paragraphs and troop interpolation templates in de/en/es/fr and readiness returned true. ESLint, JavaScript syntax and 113 frontend tests passed. Full Python suite currently passed its first 72 tests and continues; PostgreSQL-selected suite remains active. No final regression success is claimed.

## 2026-11-20: Localized active orders
Queue kind labels, empty state, cancel/refund/recall controls and move/cancel accessibility names now use central de/en/es/fr translations. Known build/research/training catalog identifiers determine display names without changing persisted jobs. Attribute translations now support the same text-only interpolation parameters as visible labels. A regression test checks dynamic names containing markup characters in translated accessible labels. ESLint, syntax and 114 frontend tests passed.

Release 20261120T121229Z completed. Pre-release PostgreSQL backup succeeded. All production services healthy with zero restarts at monitoring sample. Public HTTPS order catalogs fetched successfully in all four languages, readiness=true and quarantined=0. This verifies delivery, not complete authenticated browser acceptance.

## 2026-11-20: Campaign and recurring objectives localization
Campaign directives now translate all five names, completion/locking/claim states and reward summaries. Existing completed/locked button regression remains passing. Daily/weekly objective titles, status, period headings, pause controls and claim accessibility labels use central translations. UTC period boundaries are unchanged; the date formatter uses the selected locale. No rule snapshots or server reward calculations changed. ESLint, syntax and 114 frontend tests passed.

Release 20261120T121701Z completed with fresh backup and healthy runtime. Public HTTPS fetched campaign and recurring-objective catalogs in all four languages; readiness returned true with zero quarantined work. Full backend regressions and full authenticated four-language browser acceptance remain pending.

## 2026-11-20: Regression failure investigation
Full Python run exposed four migration assertion failures. Isolated reproduction confirmed each was the exact comparison 123 == 121, following addition of language preference and beta acceptance migrations. Updated 29 exact latest-schema assertions to 123. Legacy rehearsal now removes the new preference/acceptance tables and schema markers before upgrading its disposable copy from version 71, and requires version 123 afterwards. No production database or gameplay code changed. Targeted rerun is pending. Original long-running Python/PostgreSQL processes are preserved; their old imported assertions can still fail and do not represent a rerun of the corrected test source.

## Catalog consistency audit
All four catalogs contain 214 matching keys and identical interpolation parameter sets. Added a regression check preventing missing keys or broken dynamic placeholders across languages. This covers catalog consistency only; untranslated UI still remains. The 30-test schema regression run is active.

## 2026-11-20: Combat report labels
Localized troop deployment/loss/survivor labels, empty troop lists, battle detail summary, loot label and colony-defence heading in four languages. Existing per-round escaping and numeric loss assertions remain checked, with visible text extracted across translation spans. All 115 frontend tests passed. Catalog parity checks cover 221 matching translation keys. Full combat report translation remains incomplete (round headings, outcomes and some defence details still pending).
