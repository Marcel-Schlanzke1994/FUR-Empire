# Owner handoff — not ready

## 2026-11-18 checkpoint

The selected draft boss payout is implemented as one damage-weighted share per contributing account, capped by the shared ore pool. The other boss values still need balance playtesting. The E11 implementation and local release checks are ongoing. Public launch requires a real domain and hosting, production SMTP and secrets, operator legal review and explicit deployment approval. Current development and acceptance can continue on isolated databases.

Local SQLite is currently at schema 119 after an unintended import-time test migration. All pre-existing rows matched the schema-110 backup, and both copies passed integrity and foreign-key checks. Both backups are retained under `backups/local-sqlite-preservation/`. Main and Staging retained their original schemas and counts.

This is not a final handoff. The 344-feature implementation and release gates are incomplete.

Latest continuation (2026-11-06): TERRA-009 now permits safe abandonment of secondary colonies under explicit exact-name confirmation, no outstanding jobs/inbound supplies/open offers, and same-transaction audit/ledger recording. SQLite and disposable PostgreSQL 18 domain regressions passed; API CSRF/home protection and UI escaping/confirmation checks passed. Full local suite: 145 passed / 68 skipped; Ruff, Black, strict mypy, ESLint, JavaScript syntax, and 23 frontend tests passed. Remaining constraints include the unimplemented item inventory, protected home colonies pending the TERRA-008 owner rule, and incomplete browser/mobile/accessibility acceptance. Inventory remains 106 partial / 6 unverified / 232 not audited / 0 verified; this is not a release candidate.

Current owner-relevant facts:

- Local SQLite and Docker PostgreSQL are separate persistent worlds; both were backed up before this run.
- The app remains local/loopback-only. No domain was purchased/configured and no public deployment was started.
- There is no Git repository metadata in this checkout, so no baseline tag or feature branch could be created.
- The prompt's split machine specs and reference documents are absent; a reconstructed inventory will retain that limitation.

Do not delete `data/`, `backups/`, `.secrets/`, or the reference archives. Do not run destructive migration/reset commands against the live data volume.



## Staging test instance

An isolated staging project is available through `Start-FUR-Empire-Staging.ps1` at `https://localhost:8443`, with local Mailpit at `http://127.0.0.1:8025`. Use `Stop-FUR-Empire-Staging.ps1` to stop it without deleting its test volume. The local staging certificate requires browser trust bypass/acceptance for local testing. API smoke passed; browser E2E and public readiness are not established.


## Latest continuation state — 2026-11-06

F2-001..F2-060 now carry partial code/test evidence; zero of 344 reconstructed feature IDs are verified. Latest full disposable PostgreSQL suite: 105 passed, 1 SQLite-only skip. Ruff, Black and strict mypy pass. The local main and loopback-only staging stacks were rebuilt without deleting their separate database volumes; health/readiness and authenticated staging API smoke pass. Known open FUR-2 gap: the reconstructed neutral market asks for at least ten goods, while current gameplay offers three resource types. See `RESUME_STATE.json` for next actions. No public release or production readiness is claimed.


## E04 verification update

Latest full disposable PostgreSQL run passed 106 tests with one SQLite-only skip; Ruff, Black and strict mypy passed. Traceability parity is 344/344; 66 partial, 278 open, zero verified. E04 rule-change simulation (ENG-013) and pagination (ENG-016) remain open. Outbox delivery/retry and sanitized request-ID error format now have tests. See RESUME_STATE.json for the next exact actions.

## E05 next implementation dependency

The current schema constrains a player to one colony and each database to one world. E05 work must add world identity and multiple colony identity with backward-compatible SQLite/PostgreSQL migrations, then prove old FUR-2 rows remain readable in disposable-database migration tests. No existing player data was migrated during this audit.
## Latest E05 progress

Implemented map search, arbitrary coordinate jumps, visible gold-star tile markers and up to 20 private saved outpost targets, with an additive migration and existing-player SQLite upgrade rehearsal. Disposable browser E2E confirmed save/reload. Main Docker and isolated staging were rebuilt without volume reset; both report healthy and ready. Evidence and known limits are recorded in `TRACEABILITY.md` for W09. Broader multiworld/multi-colony architecture is still open; this feature does not establish the 344-feature release gate or public production readiness.

## E06 ECO-009 implementation

Production transparency now shows terrain-aware effective rates, current additive bonuses, storage/capacity, time-to-cap, and vacation pause, calculated by the authenticated server state. Validation: local full suite 100 passed/40 skipped; frontend 12 passed; Ruff, Black check and strict mypy passed. Main and loopback-only staging were rebuilt with database volumes preserved; both app/worker/db services are healthy and ready at schema 7, retaining 4,096 terrain cells and previous account/colony/world counts. ECO-009 remains partial, not verified. Current inventory: 90 partial, 14 unverified, 240 not audited, 0 verified. The PostgreSQL full-suite evidence is from W05 before this read-model change; this change has not yet run against the PostgreSQL adapter.


## Latest E06 update

The overview now exposes current terrain-aware production details (ECO-009, partial). Active build/research jobs can be canceled with proportional remaining-time refunds (E04/ECO-004, partial); reordering and planned follow-up stages remain open. Latest local full suite: 103 passed/43 skipped; focused PostgreSQL 18 cancellation suite: 4 passed; UI tests: 13 passed; Ruff, Black and strict mypy pass. Main and private staging are healthy/ready at schema 7 with user data preserved. Inventory parity is 344 IDs: 92 partial, 14 unverified, 238 unaudited, zero verified. Not a release candidate.

## Queue planning rollout

Queue-planning code is now deployed to local main and isolated loopback staging. Both report ready with zero quarantined jobs; schema remains 007 with 4,096 terrain cells. Existing data is preserved: main 3 users/3 colonies/1 world, staging 4/4/1. Latest validation is full SQLite 109 passed/48 skipped, PostgreSQL 18 targeted queue suite 14 passed, frontend 13 passed and Python quality checks passed. Browser/accessibility/full lifecycle acceptance and all 344-feature gates remain incomplete.

## Market history rollout

Anonymous aggregated market history is deployed on main and private loopback staging. Both databases are schema 008 and ready, with 4,096 terrain cells and an empty new trade-history table. Persistent data remains main 3 users/3 colonies/1 world and staging 4/4/1. ECO-010 is partial; no historical backfill was possible. Browser/accessibility, full gameplay acceptance and all 344 feature gates remain incomplete.

## E05 W06 continuation — 2026-11-06

World creation/join/switch now has API and temporary-browser coverage; current Main backup restored and migrated from schema 8 to 11 on disposable PostgreSQL 18. Latest full SQLite suite: 125 passed/59 skipped; latest UI suite: 16 passed. Persistent Docker remains healthy at schema 8 and has not received migrations 009–011. Do not treat W06 or the product as complete: editable settings, global-state policy, reusable browser/accessibility/mobile, 2–10 player endurance, hosted CI, full image SBOM/license gate, and all 344 feature gates remain incomplete.

## W06 settings continuation — 2026-11-06

Administrator world rename and joinability controls are now implemented and covered by SQLite and PostgreSQL 18 focused tests; world updates are audited. Current Main schema-8 backup restore through schema 11 passed on a disposable PostgreSQL container. Full local suite: 125 passed/59 skipped, 17 frontend tests passed, Python quality checks passed. Persistent Docker remains schema 8. Seed/outpost regeneration policy, reusable browser/accessibility/mobile acceptance, broad player lifecycle/endurance, global-world rules and the full 344-feature release gate remain incomplete.


## W06 continuation — 2026-11-06

Disposable browser check now covers the admin world-settings UI: world rename and join-gate closure were visibly reflected. Test DB/server were removed. Main and private staging health endpoints respond `ok`; containers remain healthy and persistent data was not modified. World systems remain partial; no production-readiness claim. The overall inventory is still 0/344 verified, with the next work in RESUME_STATE.json.


## W07 continuation — 2026-11-06

Neutral outpost stock now renews at one unit per resource per minute to 400 × tier; owned outposts are unchanged. Worker chronology, old-world baseline, world isolation and both supported DB adapters have focused coverage. Neutral stock appears on the map and the guide describes the rule. W07 remains partial pending browser/mobile/accessibility/player lifecycle acceptance. Persistent Main/Staging have not been rebuilt or migrated.


## W07 browser acceptance — 2026-11-06

A disposable browser session confirmed neutral outpost stocks refill server-side and are visible in the map. SQLite/PostgreSQL 18 worker-cycle tests passed; the full local suite and UI quality checks are green. Temporary DB, server and PG container were removed; persistent stacks remain healthy. W07 is partial pending mobile/accessibility and broader player lifecycle acceptance.


## W08 continuation — 2026-11-06

Regions A1–D4, strict-majority/two-outpost control, world-scoped +2% production bonus and map summary are implemented. Full SQLite passed 135/61 skipped (one existing deprecation warning); focused region/capture tests and 20 frontend tests pass. Ruff, Black check and strict mypy pass. PostgreSQL W08 adapter was skipped because FUR_TEST_POSTGRES is unset; browser, mobile and accessibility acceptance remain pending. Inventory is 101 partial / 11 unverified / 232 not audited / 0 verified; NOT A RELEASE CANDIDATE. Next: finish current quality gates, then browser/mobile/accessibility and adapter evidence. Persistent Docker Main/Staging were not changed.


Disposable browser acceptance at 710px passed for all 16 region cards and semantic section/list/headings. The temporary server and DB were removed. Still pending: 390px/mobile and screen-reader acceptance plus PostgreSQL adapter test.


TERRA-005 regional production is separate from ranking and capped at 32 percentage points; full SQLite and frontend checks pass. PostgreSQL and device/screen-reader acceptance remain open. TERRA-013 alliance boundaries require an explicit rule for aggregating allied ownership before implementing them.

TERRA-012 follow-up: map favorites are private and limited to 20 per world. The quota fix and two-world test passed on SQLite and disposable PostgreSQL 18; full local suite is 146 passed / 69 skipped, with frontend and quality checks green. Saved route presentation and browser/accessibility acceptance remain open. Persistent Docker stacks remain healthy and unchanged.

TERRA-012 now includes a temporary, fog-safe route preview to bookmarked targets and an expandable coordinate list. The client uses only known walkable terrain; unknown sectors and water cannot be traversed in the preview. Twenty-four frontend tests pass. Browser/mobile/screen-reader checks and durable route storage remain incomplete; no route is claimed persisted.

Browser acceptance attempt (2026-11-07): An isolated SQLite demo login screen opened in the in-app browser, but the available documented CUA surface did not provide form input/click actions. No authenticated map or route E2E is claimed. Temporary server and demo database were removed.

## TERRA-011 — owner review pending

The outpost conversion action is implemented and covered by SQLite/PostgreSQL 18 and frontend tests. Its FUR-3 costs, eligibility, transfer semantics and score/region changes are a new proposal, not an established FUR-2 rule. Owner approval remains open. No browser/mobile/accessibility acceptance is claimed. Latest complete mixed-adapter suite: 225 passed, 1 skipped; release remains closed with 107 partial, 5 unverified, 232 not audited and 0 verified.

## E05 TERRA-014 Spawn- und Kolonieschutz — 2026-11-07

Die Mindestdistanz von sechs Sektoren zu bestehenden Kolonien gilt jetzt einheitlich für Genesis-Startplätze, Weltbeitritt und Expansion. Neue automatische Starts wählen nur zulässige freie Positionen; explizit angeforderte geschützte Startfelder werden abgewiesen. Expansion bleibt zusätzlich an bekannte freie Landfelder und begehbare Wege gebunden. Der Claim und die Kostenbuchung erfolgen transaktional; vorhandene weltgebundene Unique-Indizes sichern die Kachelbelegung ohne temporäre Reservierungsdaten. Keine Migration und keine Änderung bestehender Koloniekoordinaten.

Regressionen decken Spawnabstand, Doppelclaims, Reichweite und bekannte Spielerlisten/Fog-Sicht ab. Vollständige lokale SQLite-Suite nach Änderungen: 153 passed, 74 PostgreSQL-Fälle mangels DSN übersprungen, eine bestehende Starlette/httpx-Warnung (124.53s). Gezielt PostgreSQL 18: Spawnabstand 1 passed; der zuvor vollständige SQLite/PostgreSQL-18-Mischlauf vor diesem Spawnpaket: 225 passed, 1 separater Restore/Backup-Skip. Ruff, Black check, strict mypy, ESLint, JavaScript-Syntax und 25 Frontendtests bestanden. Keine Browser-/Mobile-/Screenreaderabnahme behauptet. Inventar: 107 partial, 5 unverified, 232 not audited, 0 verified; keine Releasefreigabe.

## E05 TERRA-013 Allianzgebiete — 2026-11-07

Regionskontrolle leitet jetzt zusätzlich Allianzgebiete aus dem tatsächlichen Außenpostenbesitz ihrer Mitglieder ab. Sie verwendet dieselbe Mindestzahl von zwei und strikte Mehrheit wie die bestehende Einzelspieler-Kontrolle; ein Gleichstand bleibt neutral. Die Anzeige erscheint nur nach vollständiger Erkundung der Region. Die Zuordnung wird aus aktueller Mitgliedschaft neu abgeleitet und invalidiert den Regionscache bei Beitritt/Austritt. Produktionsbonus und persönlicher Ranglistenwert bleiben unverändert; keine Migration.

Regressions für Aggregation, Gleichstand, Membership-Cache-Invalidierung und escaped UI bestanden. SQLite/PostgreSQL-18-Adapterlauf: 2 passed; disposable Container entfernt. Vollständige lokale Suite: 157 passed, 75 skipped, eine bestehende Starlette/httpx-Warnung (141.65s). Frontend 25 passed; Ruff, Black check, strict mypy, ESLint und JavaScript-Syntax bestanden. Browser/Mobile/Screenreader-Abnahme bleibt offen. Inventar: 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-003 Startfortschritt — 2026-11-07

Audit und Regression bestätigen für neue Kolonien ein nicht überflutetes Startfeld, 1.200 Holz/1.000 Stein/800 Erz, je eine Stufe-1-Rohstoffproduktion und genug Startbestand für jede einzelne Stufe-1-Gebäudeart. Der Grundfortschritt benötigt keinen Außenposten und läuft während des bestehenden 3.600-Sekunden-Neulingsschutzes; die sechs-Sektoren-Abstandsregel bleibt bestehen. Das verifiziert die Ressourcenverfügbarkeit am Start, aber noch keine Terrainbonus- oder Distanzparität zu neutralen Zielen. Die Spielanleitung nennt das Startpaket jetzt explizit.

Lokale volle Suite nach der Genesis-Regression: 158 passed/75 skipped, eine bestehende Starlette/httpx-Warnung (126.64s). Ein zusätzlicher adapterparametrisierter Startpakettest passierte auf SQLite und Wegwerf-PostgreSQL 18: 2 passed; Container entfernt. Ruff, Black check (23 Dateien), strict mypy (15 Quelldateien) bestanden. Status bleibt partial; UI/Mobile/Accessibility und breite Spawnfairness offen. Inventar: 108 partial, 4 unverified, 232 not audited, 0 verified.

## E05 TERRA-015 Ruinenzyklus — Regel-Audit — 2026-11-07

Schema und Worker enthalten kein Aktivitätsdatum und keinen Ruinenzyklus. `profiles.joined` ist nur das Erstellungsdatum; `colonies.state.last` treibt die Simulation und kann nicht als Spieleraktivität dienen. Der explizite Nebenkolonie-Aufgeben-Befehl entfernt die Kolonie nach Auftrags-/Versorgungs-/Marktprüfungen dauerhaft und speichert lediglich eine Audit-/Ledger-Aufzeichnung, keine persistente Ruine. Inaktivitätsfrist, Vorwarnung, Umgang mit laufenden Missionen/Aufträgen/Beständen/Garnison sowie Ruinenaufbewahrung und Rückeroberung sind nicht festgelegt. Keine unautorisierte automatische Löschregel implementiert; Owner-Regelentscheidung bleibt nötig. Andere Featurearbeit läuft weiter.

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


## Offene Regelentscheidung ECO-001 (2026-11-07)

Im aktuellen Root-Regelkatalog und Produktionscode existieren keine Energieerzeugungs-/Verbrauchskoeffizienten und keine Drosselungsregel bei Unterdeckung. Vor Umsetzung muss der Eigentümer die Balancingwerte und das Verhalten bei Energiemangel festlegen. Bis dahin keine spekulative Produktionsänderung. ECO-006 parallel queued-prerequisite regression now passes on SQLite and PostgreSQL 18; broader technology graph and interactive UI acceptance remain open.


## ECO-010 follow-up (2026-11-07)

Anonymous market history now has an explicit cross-world isolation regression on SQLite and PostgreSQL 18. Browser/accessibility acceptance, legacy historical backfill and manipulation analysis remain open; no account-level information is exposed in aggregate rows.


## F2-004 CSRF retry fix (2026-11-07)

After an exact stale-session CSRF rejection, the client refreshes /state once and retries with the same body/idempotency token. API and frontend regressions pass; browser multi-tab acceptance should still be performed against the running staging app.

Private staging app was updated for F2-004 only. Verify the multi-tab behavior in a browser at https://localhost:8443; staging is loopback-only. Main and all database volumes were not restarted or changed.

The stale-CSRF recovery is now deployed to the local Docker Main app (127.0.0.1:8081) and private staging (https://localhost:8443). Both app health/readiness checks pass. Public Internet access remains unconfigured and is not claimed.

Schema-12 isolated PostgreSQL 18 dump/restore now passes with logical DB + pending mission SHA-256 and resource comparison; temporary databases/container/network were removed. OPS-004/OPS-015 verified. Current repo/worktree has no Git repository, so no branch/commit/PR provenance is available.


## Current continuation status — 2026-11-07

OPS-010 now has deterministic seeded invariant regressions on SQLite and PostgreSQL 18; SQLite replay is compared across two independent databases. Full suite: SQLite 169 passed/82 skipped, PostgreSQL 18 250 passed/1 SQLite-only skipped; one existing Starlette/httpx deprecation warning. Ruff, Black, strict mypy, ESLint, JavaScript syntax, 26 frontend tests and 344-ID traceability pass. Current reconstructed inventory: 2 verified, 113 partial, 5 unverified, 224 not audited. The application is not fully accepted or publicly production-ready. Missing original specification/source files and absent Git metadata, owner decisions, browser/mobile/accessibility and endurance/load acceptance remain documented.


## W10 continuation — 2026-11-07

A first pass of three neutral NPC frontier factions now replenishes neutral outposts on a deterministic five-minute, tier-scaled schedule. Pressure and threat reporting are scoped to currently visible posts; there are no autonomous attacks on player holdings. Focused SQLite + PostgreSQL 18 adapter tests and full SQLite suite (172 passed/83 skipped) are green. Faction diplomacy, counter-strategy, NPC armies/combat, mobile/accessibility acceptance and wider 344-ID acceptance remain open. No persistent database was changed.


## K03 continuation — 2026-11-07

Ranger scout missions revalidate PvP/vacation protection at arrival. Two focused change-during-travel cases and the full scout suite pass on SQLite/PostgreSQL 18 (10 adapter executions); full local suite 174 passed/85 skipped. Counterintelligence detection/interception behavior and its probabilities are absent from the approved rule source and remain owner/design work; no rate was invented.


## K07 continuation — 2026-11-07

The UI can recall outbound raid, player attack, scout, transport, own-colony supply and garrison stationing missions. Units and cargo return after a minimum five-second duration derived from outbound progress; return is audited/idempotent. SQLite/PostgreSQL 18 focused adapter tests passed for all six types. No dynamic threshold or after-battle retreat policy has been introduced.


## K07 / lokaler Rollout — 2026-11-07

K07: Outbound-Rückruf für sechs Missionstypen, idempotent/auditiert, 12 SQLite/PostgreSQL-18 Adapterfälle bestanden. Main /health und /ready erfolgreich; Main und Staging App/Worker healthy. Nur App-/Worker-Images wurden ersetzt; DB-Container-Startzeiten und Staging-Abhängigkeiten unverändert. Staging HTTPS über 127.0.0.1:8443 hat TLS InternalError, daher readiness dort offen. Kein öffentliches Deployment. Restumfang groß: 222 nicht auditiert, 116 partial, vier unverified; vollständiger Browser-/Mobile-/Assistive-Tech-, 2–10-Spieler-Lifecycle-, 30-Minuten-Last- und Restore-Nachweis muss entsprechend dem Agentenprompt weitergeführt werden.


Staging TLS-Prüfung korrigiert: https://localhost:8443 (konfigurierter Hostname) liefert health ok und ready=true, sofern der Diagnoseclient das lokale Caddy-Zertifikat akzeptiert. Die vorherige Fehlermeldung entstand beim Aufruf über 127.0.0.1. Keine DB-/Volumeänderung; lokale Zertifikatsvertrauensstellung im Browser ist noch separat zu bestätigen.


## E07 K04 / WAR-005 — 2026-11-07

Gefechtsprobe für bekannte neutrale Außenposten implementiert; gemeinsamer exakter FUR-2-Resolver, keine Gameplay-State-Mutation, Fog- und Verfügbarkeitsprüfungen. Alle lokalen Gates grün; volle SQLite-Suite 182/92; PostgreSQL adapter case mangels FUR_TEST_POSTGRES übersprungen. Main und privates Loopback-Staging liefern neuen App-Code und sind healthy/ready. Nur App-/Workercontainer ersetzt, DB-Startzeiten/Volumes unverändert. Teilumfang bleibt offen: PvP, Verlustintervalle, manuelle Browser-/Mobil-/Assistive-Tech-Abnahme. Inventar 2 verifiziert, 118 partial, 4 ungeprüft, 220 nicht auditiert. Nächster Schritt: Regeln/Abhängigkeiten für K01/K02 aus Root-Spec/Regelkatalog klären, keine unbestätigte RNG-Regel erfinden.

Der gezielte Simulator-Domain-/API-Lauf besteht nun auch auf SQLite und disposable PostgreSQL 18 (3 Tests). Der temporäre No-Volume-PostgreSQL-Container wurde entfernt; persistente DBs blieben gesund und mit ursprünglichen Startzeiten bestehen.


E07 follow-up: WAR-020 partial, deterministic 24,336-case FUR-2 grid passes and full suite 183/92; all lint/type/frontend/traceability gates pass. K01/K02 marked unverified because source repository contains no numeric six-round combat or expanded counter-roster design and the referenced original manual/rules pack is absent. These are not a blocker to independent features; continue elsewhere without silently inventing active rules. Browser page was opened in a disposable SQLite instance but CUA exposed no documented input operation, so no gameplay browser acceptance is claimed. Temporary server/database removed.

## Latest continuation state — 2026-11-07

K13 account-owned mission templates are implemented; schema 013 is applied to local Main and private Staging after verified pre-migration archive creation. Both apps/workers are healthy and ready, and all existing persistent data counts were preserved. Current feature inventory: 2 verified, 120 partial, 6 unverified, 216 not audited; this is not production-ready. Latest gates and exact limitations are in `RESUME_STATE.json`. The schema-13 restore drill is still unverified because the disposable schema-13 restore attempt failed at pg_dump before the restore stage. Continue with E08 audit/implementation and source-backed mechanics; do not make public deployment or invent missing FUR-3 combat values.

Restore status update: the schema-13 backup/restore drill now passes in an isolated PostgreSQL 18 helper network with exact logical database and pending-mission SHA-256 equality; 104 outposts, 4096 terrain rows, resources and alliance membership preserved. No persistent data was used.

K11 audit found no unit speed/range values in the authoritative FUR-2 catalog and no original manual/gap archive in the workspace. The mechanics need approved numeric rules before safe implementation; K11 is explicitly unverified.

K05/K06 require gameplay contracts before implementation can safely preserve combat ownership and avoid trapped/doubled units. Explicit policy needs: joint attack consent/launch/withdrawal and loss/capture attribution; allied garrison consent/capacity/recall and combat-loss behavior. Existing PvP/ownership gates are unchanged.

## Latest owner handoff — 2026-11-07

The work continues; this is not a final handoff and the application is not a release candidate. K08 deterministic FUR-3 expeditions and schema 014 mission-template support are implemented. Main and loopback-only Staging are healthy/ready at schema 14 after pre-migration backups; existing data counts were preserved. A disposable PostgreSQL 18 schema-14 backup/restore passed with matching canonical database and mission hashes, resources/alliance, 104 outposts and 4096 terrain cells. No public deployment occurred.

Latest checks: full SQLite 189 passed/96 skipped (one existing deprecation warning); focused PostgreSQL 18 expedition/recall 21 passed and schema migration 2 adapter tests passed; frontend 31; Ruff, Black, strict mypy, ESLint, JS syntax and traceability all passed. Inventory: 2 verified, 121 partial, 9 unverified, 212 not audited. Remaining release gates include authenticated mission browser journeys, mobile/accessibility, 2–10-player and two-world lifecycle, 30-minute load, deterministic PvP replay, and complete feature acceptance. Source files for the original manual/gap contracts remain absent; K01/K02/K05/K06/K11 require owner-approved rule contracts before safe implementation.

## 2026-11-07 continuation — K12 / E08 source audit

K12 partial: structured one-round FUR-2 reports now preserve participants, attack/defense power, per-unit sent/lost/survivor counts and loot for PvE/PvP, with escaped expandable UI and old-report compatibility. Focused SQLite/PostgreSQL 18: 4 executions passed; full SQLite: 190 passed / 97 skipped; frontend 32; all Python/JS quality checks and traceability pass. K09 debris/salvage and K10 artillery/missiles are unverified because current FUR-2 contains no lifecycle/economy or weapon rules; approved FUR-3 contracts are needed before adding effects. Inventory: 2 verified, 122 partial, 11 unverified, 209 not audited. **NOT A RELEASE CANDIDATE.**

K12 rollout: rebuilt only app/worker images in local Main and loopback-only Staging, using their distinct Compose project names. Both pairs are healthy; `/api/v1/health` and `/api/v1/ready` return healthy/ready and both served `app.js` bundles contain the combat report renderer. PostgreSQL remains schema 14. Main counts 3 users/3 colonies/1 world/104 outposts/4096 terrain cells; Staging 5/5/1/104/4096. No database migration or public deployment occurred.

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

## Current continuation state — 2026-11-07

The reconstructed inventory now records 2 verified, 134 partial, 26 unverified and 182 not audited IDs. Latest full local suite: 218 passed / 116 skipped / one existing deprecation warning; focused PostgreSQL 18 suites passed for ACC-002, ACC-009 and T02. ACC-004 account-name rename awaits the owner’s cooldown decision; do not invent the duration. Source migration 017 is not deployed, and Main/Staging containers, databases, volumes and player data remain unchanged. Not a release candidate; browser/mobile/accessibility, 30-minute load and full 344-feature acceptance remain open.


## E09/SOC-009 rollout note — 2026-11-07

Source migration 022 and the moderated alliance-Pinnwand UI are implemented. Leader/officer create/edit/archive; current members read the newest 100 entries in reverse chronological order, including archived posts. Nonmembers receive an empty feed. Signed-in browser/mobile/screen-reader acceptance is still open. Keyset pagination can retrieve older archived or active entries in pages of 100. Migration 022 has not been applied to Main/Staging; do not assume their schema contains the feature. Any rollout requires the documented backup/migration procedure and runtime verification. The isolated UI login page was opened, but no signed-in browser workflow was tested.


## 2026-11-08 — ENG-016 Imperiumsverzeichnis

Welt- und eigene Kolonielisten im Hauptzustand sind auf 50 Einträge begrenzt; authentifizierte Cursor-Endpunkte laden weitere Seiten. Kolonie-Cursor sind auf den angemeldeten Eigentümer beschränkt. Die UI bietet zugängliche „Weitere laden“-Bedienelemente. Die angezeigte Slotanzahl zählt jetzt nur Kolonien der aktiven Welt. Der vom Eigentümer bestätigte 24-Stunden-Kommandantennamen-Cooldown war bereits in Server, UI und exaktem Grenztest umgesetzt.

Prüfung: vollständiges SQLite pytest **277 bestanden, 150 übersprungen, eine bekannte Starlette/httpx-Deprecation-Warnung (480.92s)**; Kolonie-Cursor SQLite + isoliertes PostgreSQL 18 **2 bestanden**, Welt-API-Regressionsfall bestanden; Frontend **56 bestanden**; Ruff, Black, strict mypy, ESLint, JavaScript-Syntax, Staging-Compose und 344-ID-Traceability bestanden. Privates Loopback-Staging wurde nach geprüftem Backup `backups/fur-staging-pre-empire-pagination-20261108.dump` (227052 Bytes) nur bei App/Worker aktualisiert. Health 200, readiness true, Asset enthält beide Pager; Schema 28, 5 Benutzer/5 Kolonien. Main und persistente Datenbank-Volumes unverändert. ENG-016 und das Gesamtprodukt bleiben unvollständig; kein öffentlicher Produktionsbetrieb behauptet.


Follow-up within the 2026-11-08 ENG-016 directory package: gameplay retains the full active-world colony list (rule cap four; defensive query cap five) for map markers and same-world supply, while `empire_colonies` carries the bounded 50-row cross-world directory. The two-world join/switch regression confirms exact active-world counts and complete directory entries on SQLite and PostgreSQL 18 (4 executions passed). Final full SQLite suite after this separation: **277 passed, 150 skipped, one existing warning (492.55s)**. Frontend 56; all Python/UI/traceability gates pass. Final private Staging app/worker are healthy and ready; served app.js contains both load-more controls; schema 28 and 5 users/5 colonies remain.


### Welt-Blueprint für isolierte Proben

`python -m fur_empire.manage snapshot-world --world 1 --output welt.json` exportiert aus der konfigurierten Datenbank Gelände, Außenposten-Topologie, Schutzsektoren und Regelkatalog. `python -m fur_empire.manage restore-world-blueprint --snapshot welt.json --database probe.sqlite3 --name Wiederaufbau` benötigt einen neuen Dateipfad und erstellt eine geschlossene Sandbox. Konten, Spielbestände, Missionen, Saisons und Orbit-Daten sind nur durch die vollständige Sicherung abgedeckt. Die Blueprint-Funktionen warten auf Phase-B-Abnahme.


Für eine vollständige SQLite-Probe: `python -m fur_empire.manage restore-world-backup --snapshot sicherung.sqlite3 --database neue-probe.sqlite3 --world 1`. Die Welt-ID dient der Regelprüfung. Der Restore kopiert alle Welten und globalen Kontodaten. Sicherung und Probe nur privat behandeln und die Probe vor dem Start vollständig isolieren. Phase-B-Abnahme steht aus.


Phase-B-Migrationsprobe: `python -m fur_empire.manage rehearse-sqlite-migration --snapshot sicherung.sqlite3 --database migrationsprobe.sqlite3`. Die Quelle bleibt schreibgeschützt. Nur die neue Datei wird migriert. Bei Abweichung bleibt die Probe zur Diagnose erhalten und darf nicht für den Betrieb verwendet werden.


## 2026-11-12 — aktueller FUR-3-Bewegungsslice / Docker-Stand

K11/WAR-006 ist als partieller, opt-in FUR-3-TERRA-COMBAT-3-Bewegungsentwurf implementiert. FUR-2-Reisezeit bleibt unverändert. Vollsuite SQLite + isolierte PostgreSQL 18: 646 passed, 1 skipped, eine bestehende Warnung; Ruff, Black (50 Dateien), strict mypy (33 Module), ESLint, JS-Syntax, Frontend 66/66, pip-audit und 344-ID-Traceability bestanden. Main-Docker-App und Worker wurden aktualisiert, Migration 079 angewendet, Health/Readiness 200; Nutzer-/Kolonie-/Welt-/Außenposten-/Terrainzähler blieben gleich. Vorheriges Backup `backups/fur-20261112T040016Z.dump` wurde mit pg_restore validiert und in einem isolierten PostgreSQL-Container tatsächlich restauriert. Docker-Listener bleibt loopback; kein öffentliches Hosting gestartet. Gesamtinventar: 4 verified, 185 partial, 70 unverified, 85 not audited. Gesamtprojekt bleibt ausdrücklich unvollständig und nicht release-ready; offene Geräte-/Browser-/Accessibilty-/Lokalisierungs-, Balance-, 30-Minuten-Last-, Zwei-Welten-/Spielerlebenszyklus- und Eigentümerregel-Abnahmen bestehen. Nächster Arbeitsgang: weitere priorisierte E07/E08-Kandidaten prüfen und nur belegte Verträge implementieren.
