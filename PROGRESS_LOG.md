

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


## 2026-11-09 — Phase A: integrierte Implementierung, keine Testläufe

Checkpoint UTC: 2026-11-08T23:17:06Z. Originaler Übergabekatalog mit 344 IDs zusätzlich zu historischen Trackern übernommen. Aktuelle Source-Baseline hatte bereits Schema29; Ausgangskopie mit SHA-256-Dateiinventar in `backups/implementation-20261109/`.

Implementiert: F2-048 zehn Neutralmarktgüter, serverseitiger Werttausch/Bestände/Cap, additive Inventarfelder, unveränderliche welt-/koloniegebundene Belege (Migration030), Export/Abandon-Schutz, echte Handels-UI und zehn Original-SVGs. TERRA-008 Heimatwechsel mit weltbezogener 24h-Frist, Regelhash und Audit (Migration031). Vorhandene Queue-/Expeditions-/Allianzversorgungsaktionen im API-Vertrag erreichbar gemacht. Spielerangriffe/Transporte pinnen neue Zielkolonien; Altjobs bleiben bei Ankunft in der Ursprungswelt. Allianzversorgung behält nach Heimatwechsel das ursprüngliche berechtigte Ziel.

Regressionen für Domain/API/SQLite/PostgreSQL/UI vorbereitet, **keine Tests oder sonstigen Prüfläufe ausgeführt**. Keine DB geöffnet/migriert, keine Prozesse gestartet/neu gestartet, kein Docker/Deployment, keine Abhängigkeiten geändert. Nur Source-Inspektion, Dateisicherung, Patches sowie die beiden Dokumentationsgeneratoren ausgeführt. Kein neues verified, kein Release Candidate. Nächster Punkt: ENG-001 / WorldPlayer- und Fortschrittsgrenzen sowie weiteres 344-ID-Layer-Audit.


ENG-001 in Phase A erweitert. Schema 032 speichert Weltmitgliedschaft und Fraktionswahl. Wirtschaft, Verteidigung, Verzeichnis und Export lesen die passende Welt. Regression für getrennte Wahlen vorbereitet. Keine Ausführung. Weiter mit ENG-002.


ENG-002 erweitert. Schema 033 vorbereitet. Frühere globale Ereignisse und Saisons werden Genesis zugeordnet. Saisonwelten schließen nach Archivierung für Neubeitritte. Weltspezifische Regression vorbereitet. Sandbox-Regeln und Saison-Neustart offen.


## 2026-11-09 — Phase A / ENG-002

Saisonwelt auf einen Wettbewerb begrenzt. Beitrittsgrenze ab Endzeit in Game.join_world und world_update abgesichert. Saisonformular und Regression ergänzt. Keine Prüfungen oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / ENG-002 Sandbox

Sandbox-Regel in Systems.pvp_enabled und admin_season integriert. Aktive Weltfreigabe in static/app.js und Hilfetext in static/community.js ergänzt. Regression vorbereitet, keine Prüfungen ausgeführt.


## 2026-11-09 — Phase A / ENG-003

Schema 034, unveränderliche Kataloge und Weltbindungen vorbereitet. Neue Terra-Kampfberichte führen den Digest. Regression vorbereitet. Keine Prüfungen oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / ENG-003 Orbit-Katalog

Originalvorschlag in das Runtime-Paket übernommen, 14 Schiffsklassen strikt validiert, Katalogsnapshot in bestehendes unveränderliches Register eingebunden und Orbit-Reisekalkulation samt vorbereiteter Regression ergänzt.


## 2026-11-09 — Phase A / ORB-001

Transaktionale Orbit-Freischaltung pro Konto und Welt einschließlich UI und vorbereiteter SQLite/PostgreSQL-Regression. Schema 035 ausschließlich als Code vorbereitet.


## 2026-11-09 — Phase A / ORB-002/003

Orbit-Systemkarte mit Welt- und Kontogrenzen, Imperium-Navigation und vorbereiteten Regressionen integriert. Keine Prüfung oder Migration ausgeführt.


## 2026-11-09 — Phase A / ORB-004

Pionierflug mit Platzschlüssel, privater Statusanzeige und einmaliger Worker-Gründung integriert. Regression für Konflikt, Wiederholung und Ankunft vorbereitet. Keine Prüfungen oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Wirtschaft

Schema 037 und Orbit-Ausbau mit Energiegrenze, Ätherproduktion und Restübertrag vorbereitet. Regression ergänzt. Keine Prüfungen oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Werft

Schema 038 vorbereitet. Erzförderung mit Restübertrag, Schiffbauforschung, Werft und persistente Schiffsgutschrift verbunden. Keine Tests oder Migrationen ausgeführt.


ORB-004 Phase A: reguläre Kolonieschiffe, Äthertreibstoff, Besitzprüfung und Drei-Kolonien-Limit integriert. Regression ergänzt. Keine Prüfungen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Fracht

Schema 039, persistente Frachtermissionen, verlustfreie Zielreserve und Rückflug integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Frachtrückruf

Rückruf und gemeinsames Slotlimit für Fracht und Kolonisation angeschlossen. Schema 040 und Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Aufklärung

Schema 041, Spähsonden und zeitlich begrenzte private Kartenbeobachtungen integriert. Regressionen vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Kampf

Schema 042, Angriffsflüge und deterministischer Kampf mit Seed-Commitment integriert. Keine Prüfungen oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Bergung

Schema 043, Trümmerfelder und Bergungsflüge integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Verteidigung

Schema 044 und stationäre Verteidigung mit Werftaktion und Kampfeinbindung vorbereitet. Regression ergänzt. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Mondentstehung

Schema 045, kampfgebundene Mondbildung und Trümmerbuchung integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Stationen

Schema 046 und Stationen mit Ausbau, Wartung und Garnison integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Mondscanner

Schema 047, Scannerbau, Aufklärungsstufe 2 und Abfangen angeschlossen. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Sprungtore

Schema 048, Sprungtorbau und atomare Schiffsversetzung integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Expeditionen

Schema 049 und Expeditionen mit Seed, Verlustrisiko, Fracht und Rückkehr integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Sensorphalanx

Schema 050 und private Flugbeobachtung integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Mondbelagerung

Schema 051, geschützter Spezialflug, Mondschaden und Scanner-Deaktivierung integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Allianzverbände

Schema 052, Beitritt, Kampfzusammenführung und Ergebnisverteilung integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Rückzug

Schema 053, Rückruf und taktische Verlustschwelle integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Vorlagen

Schema 054 und weltgebundene Werft- und Flottenvorlagen integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Flottenversorgung

Schema 055 und begrenzter Orbit-Unterhalt integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Wrackreparatur

Schema 056, Wrackbestand, Reparatur und Ressourcenschutz integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Orbit-Fracht

Schema 057, zeitgebundene Erzfrachten und Kolonieaufgabeschutz integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Raketen

Schema 058, Sternlanzen und Schleier-Abfänger integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Spezialereignisse

Schema 059, weltgebundene Spezialereignisse und gedeckelte Expeditionsbelohnungen integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Kolonieversetzung

TERRA-010 integriert. Keine Schemaänderung, keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Sektorregeln

Schema 060 und Gründungsschutz vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Ruinen

Schema 061 und Ruinen nach freiwilliger Kolonieaufgabe integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Inaktivität

Schema 062, Vorwarnung und reversibler Ruhemodus integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Spiel-Outbox

Schema 063, transaktionale Ereignisse und privates Weltprotokoll integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Befehlsherkunft

Schema 064, Herkunftsbindung und neue Hash-Signaturen vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Terra-Orbit-Scheduler

Schema 065 und gemeinsame chronologische Auftragsauswahl vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Quarantäne

Schema 066, Orbit-Wiederanlauf und Scheduler-Lag integriert. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Orbit-Ressourcenledger

Schema 067 und private Bestandsbuchungen vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Deterministische Produktion

Terra-Zeitintegration mit exaktem Festkomma und Rückwärtskompatibilität ergänzt. Keine Prüfungen ausgeführt.


## 2026-11-09 — Phase A / Missionsreferenzen

Schema 068 für Referenzintegrität vorbereitet. Keine Tests oder Migrationen ausgeführt.


## 2026-11-09 — Phase A / Welt-Blueprint

Betreiberexport und isolierter Restore implementiert. Keine Tests, CLI-Restores oder Migrationen ausgeführt.


ENG-012 Phase A: vollständiger SQLite-Restore mit Integritäts-, Fremdschlüssel- und Weltregelprüfung ergänzt. Regression vorbereitet. Keine Ausführung.


ENG-013 Phase A: Admin-Regelvorschau für Terra-Produktion und Kampfkraft, API-Regression vorbereitet. Keine Prüfungen ausgeführt.


ENG-014 Phase A: SQLite-Migrationsprobe und Bestandsvergleich implementiert. Regression vorbereitet, keine Ausführung.


ENG-015 Phase A: API-Fehlerhülle, Request-ID und Redaktion für Eingabe- und Serverfehler integriert. Regression vorbereitet. Keine Prüfungen ausgeführt.


ENG-016 Phase A: Orbit-Kampfberichte aus dem Status ausgelagert; private Keyset-Seiten und vorbereitete Cursor-Regression. Keine Prüfungen ausgeführt.


ENG-017 Phase A: Betriebsansicht, CLI-Backupmarker und Warnschwellen integriert. Keine Tests oder Migrationen ausgeführt.


ECO-001/ECO-007 Phase A: Terra-Energie und zwei Spezialmodule mit Bauqueue und Produktionsdrosselung integriert. Keine Prüfungen ausgeführt.


ECO-002 Phase A: Fusionsunterhalt und zeitgenauer Ablauf integriert, Regression vorbereitet. Keine Prüfungen ausgeführt.


ECO-007 Phase A: Scannerturm und Kommando-Uplink an Bau, Fog und Missionsgrenzen angeschlossen. Regression vorbereitet. Keine Prüfungen ausgeführt.


ECO-008 Phase A: Schema 070, weltgebundener Prestigeausbau und Uplink-Freischaltung integriert. Keine Tests oder Migrationen ausgeführt.


ECO-012 Phase A: Schema 071 und dauerhafte Terra-Handelsrouten integriert. Regression vorbereitet. Keine Tests oder Migrationen ausgeführt.


ECO-016 Phase A: Drei Fraktionstechnologien integriert und Regression vorbereitet. Keine Tests ausgeführt.


ECO-016 Phase A: Pioniervermessung und zielgebundener Gründungsrabatt integriert. Regression vorbereitet, keine Prüfungen ausgeführt.


ECO-016 Phase A: Wächterbefestigung, Kampf-/Aufklärungswirkung und Regression integriert. Keine Prüfungen ausgeführt.


ECO-016 Phase A: Schema 072, Syndikatkonvoi und einmalige Escrow-Lieferung integriert. Keine Tests oder Migrationen ausgeführt.

ECO-016 Phase A: Sechs Fraktionseinheiten mit Ausbildungsfreigabe, vorläufigen Werten und Terra-Missionsanbindung integriert. Regression für Freischaltung, Wiederholung und Ausbildungsabschluss vorbereitet. Keine Prüfungen ausgeführt.

ECO-016 Phase A: Schnellbau wirkt auf neue und neu geplante Bauaufträge, Bastionsprotokoll auf den Wächterwall. Werte vorläufig. Keine Prüfungen ausgeführt.
ECO-016 Phase A: Regressionen für Schnellbau und fraktionsgebundene Wallwirkung vorbereitet.

ECO-016 Phase A: Fernkolonisierung und Mobile Festung integriert. Forschungsanzeige um alle vier neuen Technologien ergänzt. Keine Prüfungen ausgeführt.

ECO-016 Phase A: Marktchiffre verkürzt Konvoi-Abfertigung um 60 Sekunden. Effiziente Bergung erhöht Expeditionsfunde vor dem Frachtlimit um zehn Prozent, bei Abfahrt festgeschrieben. Werte vorläufig. Keine Prüfungen ausgeführt.

## 2026-11-10 — Migration boot and bounded regression checkpoint

Fresh temporary SQLite initialization now completes schema migrations 1–72. The SQL identifier `returning` was reserved in SQLite; migration columns and runtime queries now consistently use `is_returning` (presentation aliases remain `returning`). Updated stale schema-version expectations and the production-details assertion uncovered during regression runs. Focused results: orbit battle/rules 9 passed; terrain 11 passed; world snapshot 3 passed; faction, convoy, trade route and ranking cases 9 passed; 9 PostgreSQL variants skipped because `FUR_TEST_POSTGRES` is unset. A full pytest run reached about 68% with multiple failures and an unusually long test, then was interrupted before a final report. Ruff reports 5 issues, Black check would reformat 14 files, and strict mypy reports 76 errors in `systems.py`, `game.py`, and `manage.py`. No persistent Main/Staging DB was changed. Phase A and public release remain unverified; next step is a bounded full failure/timing report and systematic repair.

## 2026-11-10 — Quality-gate follow-up

Applied Black formatting to the current Python source/tests/scripts, then fixed three Ruff findings. Current Ruff and Black check pass. Strict mypy remains blocked by 76 static typing errors in `fur_empire/systems.py`, `game.py`, and `manage.py`; the full pytest run remains unverified as recorded above. A post-format bounded regression run of orbit, terrain and backup/restore suites passed 23 tests with 11 PostgreSQL variants skipped. No gameplay feature was promoted to verified based on these focused tests.


## 2026-11-10 — PostgreSQL season archive regression

Full isolated SQLite/PostgreSQL 18 suite: 523 passed, 1 skipped, 2 failed in 6186.89s. Both failures had the same root cause: PostgreSQL returns SUM(ranking_score) as Decimal, which Python JSON cannot encode in season archive standings. Normalize archived score to integer. Targeted regression rerun with SQLite and disposable PostgreSQL 18: 4 passed in 60.34s. Ruff, Black check (44 files unchanged), strict mypy (29 source files), and 344-ID traceability check pass. The disposable PostgreSQL container was removed; persistent Main/Staging were not modified. A full post-fix suite run is still pending. The next proposed FUR-3 six-round Terra combat lacks approved hit/damage/armor/shield/initiative/retreat coefficients, so no balance values were invented; this remains a product contract requiring owner approval before implementation.


Post-fix full SQLite suite completed: 347 passed, 179 PostgreSQL adapter skips, one existing Starlette/httpx deprecation warning in 609.19s. The two PostgreSQL season-archive regressions also pass on both SQLite and disposable PostgreSQL 18 (4 total).


## 2026-11-10 — TERRA-015 current-state reconciliation

Audited current worker, command, schema, UI and tests. TERRA-015 inactivity rules are implemented: account activity is rate-limited to hourly refresh, warning starts at 30 idle days, seven-day notice is honored, pending jobs/offers/inbound activity/Terra-Orbit cargo defer dormancy, all Terra colonies pause without deletion, and owner reactivation resumes without retroactive production. Voluntary colony abandonment leaves a 24-hour visibility-gated ruin. Updated spec/FEATURES.json, TRACEABILITY.md, agent/FEATURE_INDEX.md, and docs/implementation/IMPLEMENTATION_MATRIX.json to partial with accurate current evidence; counts now 4 verified, 161 partial, 88 unverified, 91 not audited. Traceability verifier passes all 344 IDs. Focused SQLite tests: 2 passed, 2 PostgreSQL adapter variants skipped. A fresh disposable PostgreSQL rerun could not start because Docker Desktop reports 'Docker Desktop is unable to start'; no persistent containers or databases were modified. Browser/mobile/accessibility and localization remain open.


## 2026-11-10 — ECO-009 accessible production chart

Added an expandable production comparison to the resource header. Three server-derived rates are shown with accessible progress labels and exact base, additive bonuses, terrain percentage, stock/capacity, time-to-cap and paused/full status. Dynamic terrain labels are escaped. Mobile layout wraps the disclosure to its own row. No forecast for future rules/events is implied. Frontend regression verifies rendering, integration, escaping, pause/full states, cap estimate and accessible labels. Full frontend suite 59 passed; ESLint, JavaScript syntax and 344-ID traceability pass. ECO-009 stays partial pending browser/mobile/screenreader acceptance.

## 2026-11-10 — ECO-014 bounded economy simulation

Added authenticated `POST /api/v1/economy/simulate` for up to 20 build/research/train/trade/goods_trade/quest actions. The simulator invokes the real `Game.command` rules in a DB savepoint, reports active immutable rule and neutral-market catalog digests with each step's resource/goods/reserve balances, and rolls back every write on both success and failure. It uses normal CSRF/session checks and rejects unsupported actions/oversized scenarios. Focused API tests: 3 passed, including successful non-mutation, rollback after a later command fails, CSRF, limits and action restrictions. Full SQLite suite: 350 passed, 179 PostgreSQL adapter tests skipped, one existing Starlette/httpx deprecation warning (1118.38s). Ruff, Black check and strict mypy passed; traceability confirms 344 unique IDs and no status drift. PostgreSQL rerun could not be performed because Docker Desktop's engine is unavailable. Main/Staging databases and persistent Docker volumes were not changed. ECO-014 remains partial: complete cross-feature/event flow inventory, balance report and UI/device/localization/browser acceptance remain open.

## 2026-11-10 — ECO-011 concurrent alliance-supply retry

Audited existing alliance supply behavior: dispatch validates same-world alliance membership and home-colony targets, route and carrier/logistics capacity; arrival rechecks membership and returns cargo if invalid; cancellation returns cargo/carriers with overflow preserved in reserve. Added a parallel same-token retry regression; only one shipment is escrowed and persisted. Focused adapter tests: 4 passed, 4 PostgreSQL variants skipped because Docker Desktop cannot start. Ruff, Black check and strict mypy pass; the full SQLite suite from immediately before this test-only addition passed 350 tests, 179 PostgreSQL skips, one existing warning. ECO-011 remains partial pending browser lifecycle, mobile/accessibility and abuse acceptance. No persistent DB or player state changed.

## 2026-11-10 — ECO-012 scheduled-route source audit

Corrected a stale feature assessment: recurring Terra trade routes already exist in the root app. The current source enforces three routes per source colony, one route per source-target pair, 1–168 hour intervals, per-dispatch cargo/carrier escrow, non-overlapping trips, pause with reason on shortage or paused colony, and owner resume/stop. Already-dispatched supply completes after route stop. Expanded the route regression for out-of-range intervals, duplicate targets and the 168-hour maximum; the full pause/resume/stop lifecycle remains covered. Focused run: SQLite passed, PostgreSQL variant skipped (Docker Desktop unavailable). Ruff, Black check, strict mypy and 344-ID traceability pass. ECO-012 remains partial pending browser/mobile/accessibility/localization and broader abuse acceptance; no pre-dispatch resource escrow contract exists. No persistent DB/player data changed.

## 2026-11-10 — ECO-013 production-template ownership regression

Extended the authenticated production-template API regression: a second account cannot queue another player's template. The test verifies the rejected attempt creates neither a command nor a production job. An initial assertion compared resource balances across ordinary API reads and failed because real production ticks can add resources while requests run; the test now checks command/job invariants instead. ECO-013 focused API tests: 2 passed. Ruff, Black check and strict mypy pass. ECO-013 remains partial pending browser/mobile/screen-reader acceptance and a production migration/restore rehearsal. No persistent player data changed.

## 2026-11-10 — ECO-015 FUR-2 research-path audit

Verified the three existing colony-scoped research effects against the immutable FUR-2 catalog and current code: tactics adds 15 percentage points of combat power per level, logistics adds 10 carrying capacity per unit per level, engineering adds 15 percentage points of production per level. Focused prerequisites/queue/cost/colony-scope/combat/logistics tests: 3 passed, 2 PostgreSQL variants skipped because Docker Desktop cannot start. Evidence and implementation matrix now reflect those exact effects. ECO-015 stays partial: there is no branching specialization tree, comparative balance simulation, or owner-approved FUR-3 research catalog, so no dominant-path or FUR-3-balance claim is made. No game rules or persistent data changed.

## 2026-11-10 — ECO-016 current faction-content reconciliation

Audited the live faction code and the available master design. The code contains nine faction research keys (three per faction), six faction units (two per faction), Pioneer survey/settlement discount, Warden alliance fortification, and Syndicate protected convoy. Added parameterized regression coverage for all nine research owner/idempotency/completion paths and all six unit unlock gates. Focused run: 15 passed, 15 PostgreSQL variants skipped; Ruff, Black check and strict mypy passed. Updated the evidence to reflect existing behavior while retaining ECO-016 as unverified: additions use provisional values, and approved coefficients/costs/caps plus the requested narrative campaign are not defined. No persistent game data changed.

## 2026-11-10 — WAR-020 FUR-2 per-unit outcome boundaries

The existing FUR-2 resolver grid executes 14,400 scenarios (not the stale 24,336 recorded in earlier documentation). Added a regression for all nine currently trainable types: ten units win against an empty tier-1 post and one unit loses against an empty tier-8 post. Focused combat grid plus the new unit-class test: 2 passed. Ruff, Black check, strict mypy pass. Updated feature evidence and implementation matrix. WAR-020 remains partial because these broad FUR-2 boundaries do not demonstrate role-specific counters or any proposed FUR-3 balance. K01 remains unverified: the available FUR-3 rules file defines Orbit rules only and must not be used as Terra combat coefficients. No persistent game data changed.

## 2026-11-10 — WAR-007 concurrent recall coverage

Expanded the mission-recall regression to issue two simultaneous same-token recall requests for each of the seven currently recallable outbound kinds (raid, PvP attack, scout, transport, own-colony supply, garrison station, expedition). Assertions verify one return job, one audit record and exactly one eventual force/cargo return. Focused SQLite matrix: 7 passed; PostgreSQL adapter variants skipped because Docker Desktop engine is unavailable. Ruff, Black check and strict mypy passed. Updated WAR-007 notes across the feature inventory, traceability, index and implementation matrix: an earlier six-kind count was stale. WAR-007 remains partial; post-arrival/battle recall and browser/device/accessibility acceptance remain open. Separately, ACC-004's 24-hour commander-name cooldown is owner-confirmed and already implemented with case-insensitive uniqueness, reauthentication, colony display projection, preserved colony names and audit coverage. No persistent database or player data changed.

## 2026-11-10 — K12 battle report timestamp and participant parity

Strengthened the PvP report regression: attacker and defender receive the same immutable server timestamp and participant identities, alongside the existing per-round powers, exact unit sent/lost/survived counts, loot, and third-party privacy assertion. The targeted package covering PvP/neutral reports, all seven concurrent recall cases, and the owner-confirmed commander-name cooldown completed with 10 passed and 10 PostgreSQL adapter variants skipped because Docker Desktop is unavailable. Ruff, Black check (44 files), strict mypy (29 files), and the 344-ID traceability check passed. The 24-hour commander-name cooldown test itself passed on SQLite; its PostgreSQL variant was skipped. K12 remains partial because FUR-2 is one round and browser/device/replay acceptance remain open. No persistent database or player data changed.

## 2026-11-10 — WAR-009 third-party report privacy

Extended the tiered scouting regression to verify that neither the target account nor an uninvolved third player receives the observer's intel report, and that the report payload does not include target resources. Existing checks still cover level-2 military/building intel, expiry, one-time return of scouts and private report access. Focused SQLite regression: 1 passed; PostgreSQL adapter variant skipped because Docker Desktop engine is unavailable. Ruff, Black check (44 files), strict mypy (29 files), and traceability (344 IDs) passed. Updated the feature inventory, implementation matrix, feature index and traceability evidence. WAR-009 remains partial: no spy skill/technology beyond Ranger count; browser/device/accessibility acceptance remains open. No persistent database or player data changed.

## 2026-11-11 — Full local SQLite suite after WAR-007/K12/WAR-009 regressions

Ran the required complete Python suite after the latest test changes: 364 passed, 192 skipped, one existing Starlette/httpx deprecation warning; 1447.18 seconds. Current skips include PostgreSQL adapter tests because `docker version` still returns `Docker Desktop is unable to start`. The new WAR-009 privacy regression also passed in its focused SQLite run (1 passed, PostgreSQL variant skipped). Ruff, Black check (44 files), strict mypy (29 source files), and `scripts/check_traceability.py` passed for all 344 IDs. Persistent databases, Docker volumes, and player data were not modified. Current feature counts remain 4 verified, 162 partial, 87 unverified, 91 not audited; that is 1.2% fully verified, and partial features cannot be represented as a defensible completion percentage.

## 2026-11-11 — K13 mission template load behavior

Added a frontend regression that executes the actual mission-template load handler. It verifies the saved army is clamped to current unit availability, capture is enabled only for a valid neutral target, the mode change updates the form, and an incompatible target mode produces actionable status text without applying the template. The complete frontend suite passes: 60 tests. ESLint and JavaScript syntax checks pass. Updated K13 evidence in the feature inventory, implementation matrix, traceability and feature index. K13 stays partial pending batch dispatch/target scheduling and browser/device/accessibility acceptance. Full Python suite just completed: 364 passed, 192 PostgreSQL/unavailable variants skipped, one existing Starlette/httpx warning. Docker daemon remains unavailable; persistent databases and player data untouched.


## 2026-11-11 — K05 Terra Allianzangriffe (FUR-3-TERRA-ACS-2)

Implemented schema 73 for Terra ACS operations and wings, an immutable versioned rule catalog, server-side escrow and cancellation/withdrawal, common world-worker resolution, neutral-outpost and PvP-home combat, arrival-time protection/alliance checks, per-member FUR-2 casualties, leader-attributed neutral capture, deterministic capacity-weighted loot, individual return jobs, audit/combat reports, and member-only operation UI. Focused SQLite matrix: 7 passed; 6 PostgreSQL adapter variants skipped because Docker Desktop cannot start. Frontend suite: 61 passed; ESLint and JavaScript syntax pass. Ruff, Black check (45 files), strict mypy (30 source files) and 344-ID traceability pass. Full Python suite is running. K05 is recorded partial pending PostgreSQL migration/runtime, browser/mobile/accessibility/localization, help and broader race/retry acceptance. Migration/state tests use temporary databases; persistent player databases and data/ were not touched.

## 2026-11-11 — K05 ACS Abschluss der lokalen Abnahme

Die vollständige lokale Python-Suite nach K05 und den Schema-73-Rehearsal-Korrekturen ist grün: 371 passed, 198 skipped, eine bestehende Starlette/httpx-Deprecation-Warnung (531.03s). Die übersprungenen Fälle benötigen überwiegend die aktuell nicht startende Docker-Desktop-Engine für PostgreSQL-Adapter. Frontend: 61 passed; ESLint und JavaScript-Syntax bestanden. Ruff, Black-Check (45 Dateien), strict mypy (30 Quelldateien) und Traceability (344 IDs) bestanden. K05 bleibt partial, weil PostgreSQL-Migration/Laufzeit, Browser-/Mobil-/Screenreader-Abnahme, Übersetzungs-/Hilfetextabdeckung und zusätzliche Race-/Retry-Akzeptanz nicht nachgewiesen sind. Persistente Spielerdaten und Datenbanken wurden nicht verändert.

## 2026-11-11 — PostgreSQL Engine verfügbar, K05 Vollsuite

Docker Desktop Linux Engine ist wieder erreichbar. Die vollständige Python-Suite lief gegen die lokale SQLite-Konfiguration und einen eigens gestarteten PostgreSQL-18-Container ohne Volume: 568 passed, 1 skipped, eine bestehende Starlette/httpx-Deprecation-Warnung; 3668.76 Sekunden, Exitcode 0. Der eine Skip ist ein separater Restore-Test, nicht ein PostgreSQL-Adapterfall. Der temporäre Container `fur-empire-pg-test-20261111` wurde danach entfernt. K05-Schema 73 und Lifecycle-Adapter liefen damit auch auf PostgreSQL. Frontend 61 Tests sowie Ruff, Black-Check, strict mypy, ESLint, JavaScript-Syntax und Traceability 344/344 bestanden. Persistent Main-/Staging-Datenbanken und `data/` wurden nicht verändert. K05 bleibt partial wegen fehlender echter Browser-/Mobil-/Screenreader-/Übersetzungs-/Hilfetextabnahme und zusätzlicher Lifecycle-Akzeptanz.


## 2026-11-11 — K05 Browser-Fix und vollständige SQLite/PostgreSQL-Abnahme

Die Live-Browserprüfung des Allianzangriffs deckte einen Fehler auf: Das Missionsformular sendet gesperrte Einheitentypen mit Anzahl 0; der Server lehnte diese fälschlich als unbekannten Truppentyp ab. `terra_alliance_attack_command` ignoriert solche Null-Einträge jetzt und speichert nur positive Truppenzahlen. Der neue Regressionstest lief auf SQLite und PostgreSQL. Im lokalen Browser wurden danach der Angriff erstellt und ein zweiter Allianzspieler erfolgreich aufgenommen; die Oberfläche bestätigte die Reservierung der Truppen. Vollständige Python-Suite gegen SQLite und einen temporären PostgreSQL-18-Container: 570 passed, 1 skipped, eine bestehende Starlette/httpx-Deprecation-Warnung (4744.45s, Exit 0). Frontend 61 passed; Ruff, Black-Check (45 Dateien), strict mypy (30 Dateien), ESLint, JavaScript-Syntax und Traceability (344 IDs) bestanden. Temporärer Container sowie Demo-DB/Server entfernt; persistente Spielerdaten und Datenbanken unverändert. K05 bleibt partial; Mobil-, Tastatur-/Screenreader-, Übersetzungs-/Hilfetext-, weitere Retry/Race- und Produktionsabnahme stehen aus.


## 2026-11-11 — K06 Schema 74 vorbereitet

K06-Contract FUR-3-TERRA-ALLIED-GARRISON-1 mit Host-Zustimmung, 1–300 Einheiten Kapazität, Ankunfts-Revalidierung, intaktem Rücktransport, eigentümergebundenen Kampfverlusten und Löschschutz ist festgehalten. Additive SQLite-/PostgreSQL-Migration 074 legt Allianzfreigabe und separat besessene Garnisonen an; Kolonie-FKs nutzen RESTRICT. Migration-Recreation/Data-Preservation besteht fokussiert auf SQLite; PostgreSQL-Variante mangels Test-URL übersprungen. Vollständige SQLite-Suite: 373 passed, 200 PostgreSQL skips, eine bestehende Deprecation-Warnung (592.66s). Ruff, Black (45 Dateien), strict mypy (30 Dateien) und Traceability 344/344 bestanden. K06 bleibt unverifiziert; Dispatch, Worker-Lifecycle, Kampf, Recall, UI und PostgreSQL-Runtime müssen noch implementiert werden.


## 2026-11-11 — K06 Allianz-Garnisonen implementiert

FUR-3-TERRA-ALLIED-GARRISON-1 ist als aktiver Regelstand eingebunden. K06 bietet schema-74-gestützte Host-Zustimmung je Heimatkolonie/Allianz, 1–300 Einheiten Kapazität mit transaktionaler Reservierung auch während des Flugs, Troop-Escrow, Welt-/Allianz-/Besitz-/Kapazitätsprüfung bei Versand und Ankunft, intakte Rückkehr bei ungültiger Zustimmung, Host- und Entsender-Rückruf, Rückkehr aktiver Garnisonen bei Allianz-Austritt/Kick, Defense-Kraft mit Contributor-Taktik und deterministische Verluste pro Eigentümerarmee samt Audit und privatem Bericht. Responsive Allianzansicht erhält Freigabe-, Entsendungs- und Rückrufsteuerung. Vollsuite mit SQLite + disposable PostgreSQL 18: 575 passed, 1 skipped, eine vorhandene Deprecation-Warnung (3288.31s). Frontend 62 passed; Ruff, Black (46 Dateien), strict mypy (31 Quelldateien), ESLint, JS-Syntax und Traceability 344/344 bestanden. K06 bleibt partial: Browser-/Geräte-/Screenreader-/Lokalisierungs-/Hilfetextabnahme, Capacity-Race-/Failure-Replay und produktive Rollout-Prüfung ausstehend. Persistent Main/Staging und Spielerdaten nicht verändert.


## 2026-11-11 — K06 Rückruf-Snapshotfehler behoben und Vollabnahme

Die Browsernachprüfung zeigte, dass ein Entsender-Rückruf den Rückreisejob in die geladene Kolonie schrieb, danach aber `Game.command` denselben älteren Snapshot speicherte und den Job damit löschte. `Systems._return_allied_garrison` übernimmt beim vom Entsender gestarteten Rückruf jetzt denselben Befehlszustand; der Host-Rückruf liest weiterhin den aktuellen Absenderzustand. Neue Regression `test_allied_garrison_recall_survives_contributor_command_save` deckt den Überschreibefall ab. Focused SQLite: 2 passed, 2 PostgreSQL-Varianten mit der alten lokalen Setup-Konfiguration übersprungen; danach komplette Suite gegen SQLite plus disposable PostgreSQL 18: 577 passed, 1 skipped, eine bestehende Starlette/httpx-Deprecation-Warnung (2958.87s). Ruff, Black check (46 Dateien), strict mypy (31 Quelldateien), Frontend 62, ESLint, JS-Syntax, Traceability 344/344, beide Compose-Konfigurationen und `pip-audit` (keine bekannten Schwachstellen) bestanden. Temporäre Browserreise: fünf Ranger aus zwölf entsandt, angekommen, über den UI-Rückruf zurückgerufen und nach Ablauf wieder verfügbar (sieben). Testcontainer und temporärer Demo-Server entfernt. Main/Staging-Datenbanken, Volumes und `data/` unverändert. K06 bleibt partial: Kapazitäts-Race/Crash-Retry, Tastatur/Mobil/Screenreader, Übersetzungs-/Hilfetext und produktiver Rollout offen. Der nächste Abhängigkeitsschritt ist E07-Kampf (K01/K02/WAR-001); die FUR-3-Sechs-Runden-Skizze hat keine numerischen Schadens-/Panzerungs-/Schild-/Initiativewerte, daher bleibt ein versionierter FUR-3-Regelvertrag nötig und FUR-2 bleibt unverändert.

## 2026-11-11 — K01 versionierter FUR-3-Kampfprototyp

Der aktive E07-Arbeitsschritt ergänzt einen separaten FUR-3-Terra-Kampfresolver mit versioniertem Regelkatalog. Er bildet sechs Runden, neun Kampfprofile, Trefferwahrscheinlichkeit, Zufallsvariation aus 256-Bit-Seed, Panzerung, Schilde, Initiative, Zielpriorität/Konter, Taktik, Doktrin-, Gelände- und Fraktionsfaktoren sowie einen Rückzugsschwellenwert ab. FUR-2-Auflösung und Weltregeln bleiben unverändert. Fünf fokussierte Resolvertests bestanden. Die vollständige lokale SQLite-Suite bestand mit 381 passed und 202 übersprungenen PostgreSQL-Adapterfällen (FUR_TEST_POSTGRES nicht konfiguriert), einer bestehenden Starlette/httpx-Deprecation-Warnung, 667,70 Sekunden. Ruff, Black-Check (48 Dateien), strict mypy (32 Quelldateien) und Traceability 344/344 bestanden. Sechs Feature-IDs (K01, K02, WAR-001, WAR-002, WAR-004, WAR-008) wurden von unverified auf partial gesetzt. Der Resolver ist ein isolierter Prototyp und noch nicht im Live-Missionspfad; Seed-Persistenz/-Enthüllung, Weltumschaltung, PvE/PvP-Auflösung, Berichte, Simulator/UI, PostgreSQL-Adapter, Lokalisierung und vollständige Akzeptanz bleiben offen. Kein persistenter Datenbank- oder Spielerdatenbestand wurde verändert.

## 2026-11-11 — FUR-3-/Bergungs-Nachweis aktualisiert

- Berichtete Live-FUR-3-PvE/PvP- und Simulatorintegration in Traceability und Integrationsgraph; hielt FUR-2-Standard sowie die offene ACS-Fortifikations-/Attributionsentscheidung fest.
- Reauditiert K09, WAR-011, ORB-021 und ORB-029: Orbit-Bergung/Reparatur sind implementiert und in einer integrierten Multiplayerregression enthalten; Terra-Materialtrümmer/Reparatur und breite UI-Akzeptanz bleiben offen. Frühere „kein Orbit-System“-Aussagen in Traceability waren überholt.
- K12-Berichtspfad bestätigt: FUR-3-Runden-/Einheitenreport samt Replay, PvE/PvP und expandierbarer UI-Details.
- Inventarstatus korrekt auf `partial` für K09/WAR-011/ORB-021/ORB-029 gesetzt; 344 IDs: 4 verified, 176 partial, 73 unverified, 91 not audited. Validator bestanden. Keine Produktcodeänderung und keine neuen Tests in diesem Dokumentationsslice.
- Fortsetzung: unabhängige offene IDs weiter prüfen; keine erfundenen Terra-Wirtschafts- oder Fortifikationswerte. K01 ACS und K09 Terra brauchen versionierte Eigentümerregeln, bevor sie umgesetzt werden können.

## 2026-11-11 — K10/K11 Orbit-Abdeckung nachauditiert

- K10: Orbit-Sternlanzen, Reichweitenlimit, Munitions-Escrow und Abfangen durch Schleier-Abfänger sind implementiert/testbelegt; Terra-Artillerie bleibt mangels freigegebener Regeln offen.
- K11: Orbit-Flotten nutzen langsamstes Schiff und aggregierte Fracht/Treibstoff; Terra-Marschzeit bleibt unabhängig von der Armee. Zahlen und Kompatibilität für Terra-Einheiten benötigen ein Regel-Owner-Contract.
- K10/K11 Status aktualisiert auf `partial`; Traceability-Validator besteht. Keine Codeänderung und keine neuen Tests in diesem Source-Audit.

## 2026-11-11 — K14 Verteidigung nachauditiert

- K14 als `partial` aktualisiert: belegte Terra-Schildwall-/Fraktionsboni und Orbit-Verteidigungsplattform/Station mit Garnison und Wartung; Terra-Türme/Fallen/Strukturschaden/Reparatur bleiben regeloffen.
- Traceability 344/344 bestanden. Keine Codeänderung, keine neuen Tests.

## 2026-11-11 — K14 Orbit-Stations-UI-Regressionsfall

- Neuer Frontendtest prüft Raumstationskapazität, Ausbau, Wartung, aktiven/inaktiven Garnisonsstatus, Rückholung, Escaping und Command-Bindings.
- Frontend 63/63; JS-Syntaxcheck und ESLint bestanden; Traceability aktualisiert.
- Keine Produktcode- oder Bestandsdatenänderung; Terra-Strukturregeln bleiben offen.

## 2026-11-11 — K13 Orbit-Vorlagenoberfläche

- Neue Frontendregression für typgefilterte Orbit-Vorlagen mit Escaping und Save/Load/Delete-Bindungen.
- Frontend 64/64, ESLint, JS-Syntax und 344-ID-Traceability bestanden.
- K13 genauer dokumentiert: Auftragsvorlagen speichern/laden, aber keine Batch- oder Terminplanung.

## 2026-11-11 — K14 Stationsausbau-UI an Serverregeln gebunden

- Fehlende Vorbedingungsanzeige korrigiert: Stationsausbau ist bei fehlender/laufender Forschung, unzureichenden Orbit-Ressourcen und laufendem Bau gesperrt; Grund wird angezeigt.
- Frontendtest prüft alle Sperrfälle und den aktiven Ausbaupfad. Frontend 64/64; ESLint und JS-Syntaxcheck bestanden.
- Keine Änderungen an Domainregeln oder Bestandsdaten.

## 2026-11-11 — K14 Stationskapazität und Vollsuite

- Serverregression: 100/100 belegte Stationsplätze; zusätzlicher Einsatz wird ohne Abzug beim Absender abgelehnt. Testbestand bleibt konsistent.
- Vollständiges `python -m pytest`: 400 bestanden, 218 übersprungen, eine bestehende Warnung, 1189.82 s. Ruff, Black (48 Dateien), strict mypy (32 Dateien) grün.
- Vorheriger direkter `pytest.exe`-Aufruf hatte Importfehler durch Windows-Stub-Kontext; korrekt über die Projekt-Python-Umgebung wiederholt und bestanden.


## 2026-11-12 — K11/WAR-006 FUR-3-Bewegungsentwurf

- Terraingewichtete Bewegungsquote in `FUR-3-TERRA-COMBAT-3` umgesetzt: langsamste Einheit bestimmt Reisezeit, alle Einheiten müssen Reichweite einhalten, Hin-/Rücktreibstoff wird beim Start aus Erz reserviert. FUR-2 nutzt unverändert die Legacy-Reisezeit.
- PvE/PvP/Spionage/Transport/Versorgung/Allianzversorgung/Garnison/Expedition/Allianzangriff nutzen die versionierte Quote; laufende Rückreisen behalten ihre gespeicherte Dauer. Migration 079 ergänzt FUR-3-COMBAT-3-Welten und persistente alliierte Garnisonsreisezeit.
- Missionsdialog zeigt debouncte Zeit-/Treibstoffvorschau. API liest nur aktuelle Kolonie-/Ziel-/Kartendaten, begrenzt Ziel auf bekannte Sektoren und Armee auf verfügbaren Bestand.
- Gezielt: 16 passed, 11 übersprungen (PostgreSQL nicht verfügbar), 1 bestehende Starlette/httpx-Warnung. Ruff, Black check, strict mypy, JS-Syntax, ESLint, Frontendtests und Traceability bestanden. Vollsuite mit isoliertem PostgreSQL 18: 646 bestanden, 1 übersprungen, eine bestehende Starlette/httpx-Warnung (2899.36s). Main lokal nach Backup (387209 Bytes), `pg_restore --list` und echtem Restore in isoliertes PostgreSQL auf Schema 79 aktualisiert; 3 Nutzer/3 Kolonien/1 Welt/104 Außenposten/4096 Terrain unverändert; App, Worker, Health und Readiness gesund. Testcontainer entfernt. Private Staging und öffentliches Profil unverändert.
- Featurestatus bleibt partiell: Werte sind ein eigener Startentwurf ohne Balancefreigabe; neue Profile nicht ausbildbar; Browser/Device/Accessibility/Localization und Produktionsabnahme offen. Inventar: 4 verified, 185 partial, 70 unverified, 85 nicht auditiert.


## 2026-11-12 — WAR-003/K14 Verteidigung und Replay

FUR-3-TERRA-DEFENSE-1 bleibt ein opt-in, vorläufiger COMBAT-4-Regelvertrag. Geschütz, Aegis-Emitter und Gefechtsbunker wirken in normalen PvP- und ACS-Runden als separate Profile; seeded Minen können einmal pro Mission auslösen und werden dabei verbraucht. Schäden, Restintegrität, Mine, Digest und Replay werden mit dem Kolonie-Zustand atomar gespeichert. Die ACS-Teilnehmerberichte enthalten denselben Verteidigungsblock; das UI übersetzt interne Profil-IDs, zeigt Minenereignis und Integrität. Die ausführliche Spielregel steht in `docs/game-design/FUR_EMPIRE_SPEC.md`, die Kurz-Anleitung in `docs/SPIELANLEITUNG.md`.

Gezielte Verteidigungsregressionen: 19 bestanden, 4 PostgreSQL-Adapterfälle übersprungen; zusätzlicher ACS COMBAT-4-Angriff einschließlich Bericht/Replay SQLite 1 bestanden, PostgreSQL 1 übersprungen. Anschließende Simulatorintegration: 6 gezielte SQLite-Fälle bestanden, 5 PostgreSQL-Fälle übersprungen; vollständige SQLite-Suite nach allen Python-Änderungen: **453 bestanden, 231 übersprungen**, eine bestehende Starlette/httpx-Warnung (538,69 s). Frontend 69/69; Ruff, Black (53 Dateien), strict mypy (35 Quelldateien), ESLint, JS-Syntax und Traceability 344/344 bestanden. Main- und Staging-Compose-Konfiguration ist gültig. Docker Desktop selbst meldet `Docker Desktop is unable to start`, daher keine PostgreSQL-, Laufzeit- oder Restore-Probe in diesem Lauf. Keine persistenten DBs/Spielerdaten verändert. K14/WAR-003 und WAR-005 bleiben `partial`; Balance, PostgreSQL, manuelle Browser-/Geräte-/Barrierefreiheits-/Lokalisierungs- und breite Multiplayerabnahme stehen aus. WAR-004-Replay/RNG wurde auditiert; nächster Implementierungsschritt ist der noch nicht integrierte Einheiten-Lifecycle für WAR-001/002.


## 2026-11-12 — WAR-001/002 COMBAT-4 roster guard

- Auditierte den 21-Profil-COMBAT-3/4-Katalog und den realen Bewegungs-, Treibstoff-, Reichweiten-, Transport-, Dispatch-, Rückkehr-, Garnisons- und Kampfkatalogpfad. Zwölf Zusatzrollen sind nicht durch `UNITS` abgedeckt und Training ist weiterhin ausdrücklich gesperrt, bis Balance und End-to-End-Lifecycle abgenommen sind. Keine Freigabe dieser Entwurfswerte vorgenommen.
- Neue Regression über alle zwölf Rollen: API-Trainingsversuche werden abgelehnt; Ressourcen, Einheitenbestand und Auftragsqueue bleiben exakt unverändert. 12 SQLite pass, 12 PostgreSQL Adapterfälle mangels Docker übersprungen.
- Vollständiges Python: 465 passed, 243 skipped, eine bestehende Starlette/httpx-Warnung (734.92s). Ruff, Black-Check, strict mypy bestanden. Traceability: 344 eindeutige IDs, keine Statusabweichung. Vorheriger Frontendlauf: 69/69, ESLint und JS-Syntax bestanden; UI wurde in diesem Paket nicht geändert.
- FUR-3 bleibt opt-in/vorläufig; FUR-2 und persistente Spieler-/Datenbankbestände unverändert. Docker Desktop kann nicht starten; keine PostgreSQL-Laufzeitabnahme.


## 2026-11-12 — WAR-013 coordinated attacks

- Current-source audit disproved the old unverified inventory note: persistent shared attack/wing tables, per-member escrow/refunds, synchronized max-travel arrival, 12-member cap, pinned FUR-3 ACS combat, owner-attributed losses/loot and origin returns are implemented. Status corrected to partial across feature registry and traceability.
- Extracted the alliance attack panel renderer for direct acceptance tests. Leadership cancellation, member withdrawal, open join, empty state and escaping of untrusted target/leader labels pass. Frontend 70/70; ESLint and JS syntax pass. Python suite remains 465 passed/243 skipped/one warning; no Python code changed in this UI step.
- Actual browser journeys, PostgreSQL runtime, device/accessibility/localization and multi-account load acceptance remain pending; no persistent database or player data touched.

## 2026-11-12 — SOC-002 granulare Allianzrechte

Granulare, serverseitig erzwungene Allianzrechte für Offizier/Mitglied ergänzt. Migration 83 übernimmt bestehende Offiziersstandardrechte; neue Allianzen erhalten dieselben Defaults. Leitung verwaltet sieben allowlistete Rechte über die Allianzoberfläche. Führungsübertrag und Servermoderation bleiben unveränderbar geschützt. SQLite-Domänen- und Frontendregressionen sowie Python-/Frontend-Qualitätsprüfungen laufen; PostgreSQL- und manuelle Browser-/Accessibility-Abnahme sind noch offen. Quelle-only; Main/Staging/player data unverändert.

SOC-002 abschließend lokal abgenommen: Full pytest 467 bestanden, 244 PostgreSQL-Adapterfälle übersprungen, 1 vorhandene Starlette/httpx-Warnung (1951,74 s). Frontend 71/71, Ruff/Black/strict mypy/ESLint/JS-Syntax/344-ID-Traceability bestanden. Keine persistenten Daten verändert. PostgreSQL- und manuelle Browser-/Accessibility-Abnahme bleiben offen.

## 2026-11-12 — SOC-003 Führungsübergabe mit Zustimmung

Sofortigen Führungswechsel durch nominierungsbasierte Übergabe ersetzt: nur Nachfolger akzeptiert, kann ablehnen; aktuelle Leitung kann zurücknehmen. Schema 84 persistiert genau eine offene Anfrage je Allianz. Rollen- und Leitungstabelle ändern sich gemeinsam in einer Transaktion. Fokusregressionen für Annahme/Ablehnung/Rücknahme, Idempotenz und UI laufen; voller pytest-Lauf nach Schema 84 erforderlich. Main/Staging unverändert.

SOC-003 Abschluss — Full pytest 468 bestanden/245 PostgreSQL-Fälle übersprungen, eine bestehende Starlette/httpx-Warnung (1136,20 s). Frontend 72/72, Ruff/Black/strict mypy/ESLint/JS-Syntax/344-ID-Traceability bestehen. Übertragung bleibt bis zur Nachfolgerannahme offen, Rücknahme/Ablehnung und atomarer Wechsel getestet. Keine persistenten Daten geändert.


## 2026-11-12 — SOC-006 Allianzkasse implementiert und lokal verifiziert

Schema 87 ergänzt weltgebundene Kassenbestände, Auszahlungsanträge, Freigaben und unveränderliche Ledger-/Approval-Belege für SQLite und PostgreSQL. Der vom Eigentümer ausgewählte versionierte FUR-3-Entwurf setzt gebührenfreie Spenden, 1 % je Ressource (Abrundung), zwei unabhängige Freigeber ab 5.000 Bruttoressourcen, sieben Tage Ablauf und vollständige Rückbuchung bei Storno/Ablehnung/Ablauf/Austritt/Entfernung um. Leitung und granulare treasury-Berechtigung verwalten Freigaben; Auszahlungen gehen an die eigene aktive Kolonie. UI, Worker-Ablauf und Idempotenz sind integriert.

Fokusregression inkl. Mitgliederrechte, Gebühr, Vier-Augen-Prüfung, Weltisolation, Storno, Ablauf, Leave-/Kick-Rückbuchung und Ledger-Unveränderlichkeit: SQLite + PostgreSQL 18, 2 bestanden. SQLite-Migrations-Rehearsal bewahrt Bestand. Vollständige Python-Suite nach SOC-006: 473 bestanden, 249 PostgreSQL-Adapterfälle übersprungen, 0 Fehler, eine vorhandene Starlette/httpx-Deprecation-Warnung (1252,16 s). Ruff, Black (50 Dateien), strict mypy (38), Frontend-Tests, ESLint, JavaScript-Syntax, Traceability 344/344 sowie Main und zusammengeführte Staging-Compose-Konfiguration bestanden. Der kurzlebige PostgreSQL-Container wurde entfernt; persistente Spielerdatenbanken und Docker-Volumes blieben unverändert.

Status bleibt partial: Der Eigentümer hat die Gebühren- und Freigaberegeln ausdrücklich festgelegt (1 %, zwei unabhängige Freigeber ab 5.000 Bruttoressourcen, vollständige Rückbuchung nach sieben Tagen); diese Werte sind daher keine offene Eigentümerentscheidung mehr. Balanceprüfung, manuelle Browser-/Mobil-/Tastatur-/Screenreader-Abnahme und persistenter Deployment-/Runtime-Nachweis fehlen. Nächster Eintrag SOC-007 Allianzprojekte.


## 2026-11-12 — SOC-007 Allianzprojekte abgeschlossen

Schema 88 ergänzt einen versionierten, vorläufigen FUR-3-Katalog mit drei befristeten Allianzprojekten, weltgebundener Ein-Projekt-Grenze, begrenzten Beiträgen aus gleichweltigen Kolonien, Berechtigungsprüfung, Abschlussprotokoll ohne Wirtschaftsbonus sowie vollständigen, idempotenten Rückbuchungen bei Abbruch/Ablauf. Unveränderliches Beitrags-/Rückbuchungsledger, Worker und Allianzansicht integriert; FUR-2 unverändert.

Fokusregression (SQLite + PostgreSQL 18) und SQLite-Migrations-Rehearsal bestanden. Vollständige Python-Suite nach Schema 88: 474 bestanden, 250 optionale/nicht konfigurierte PostgreSQL-Adapterfälle übersprungen, 0 Fehler, eine FastAPI/Starlette-TestClient-Deprecation-Warnung (1275,67 s). Ruff, Black-Check (51 Dateien), strict mypy (39 Dateien), npm test, ESLint, JS-Syntax, Traceability 344/344 sowie Main- und Staging-Compose-Konfiguration bestanden. Persistente Datenbank nicht migriert.

SOC-007 bleibt partial: Ziele und Fristen sind vorläufig; Eigentümer-/Balance-, manuelle Browser-/Mobil-/Tastatur-/Screenreader- und persistente Staging-Abnahme offen. Nächster Prüfschritt: SOC-008 Allianzforum gegen aktuellen Quellcode und Akzeptanzkatalog auditieren.


## 2026-11-12 — SOC-008/009 forum and bulletin current-source acceptance

SOC-008 Forum audit verified current membership scoping, author/moderator controls, mute restrictions, report privacy, duplicate-pending guard, scoped keyset cursor validation, XSS-safe UI and SQLite/PostgreSQL persistence. Focused suite: 7 passed across SQLite + disposable PostgreSQL 18. SOC-009 bulletin audit verified current member visibility, granular permission enforcement, archive visibility, CSRF/API boundary, audit privacy and 100-entry keyset pages. Focused suite: 5 passed across SQLite + disposable PostgreSQL 18. Both remain partial pending manual browser, mobile, screen-reader and full localization acceptance.

Frontend acceptance now passes 76/76; one test harness was corrected to inject the app's global number formatter for the public diplomacy view. ESLint, JS syntax, Ruff, Black (51), strict mypy (39), traceability 344/344 and Compose checks pass.

Private Docker Staging was updated to the current source and schema 88, without reseeding its five existing users. Before rollout, `backups/fur-staging-pre-schema88-20261112.dump` was created, archive-validated and fully restored into a disposable PostgreSQL 18 probe (schema 77, five users, zero alliances); probe removed. Staging now reports schema 88, HTTPS health/readiness HTTP 200, worker lag 0, no quarantined jobs, and healthy app/worker/db/proxy. Main database/volumes were not changed. This stack remains bound to loopback; it is not public production.


## 2026-11-12 — SOC-010 friend lifecycle and SOC-011 block audit

SOC-010 audit confirmed owner-private contact lists, participant-bound request/accept/decline/cancel/remove, pagination, and simultaneous opposite-request protection. Added regression for decline, cancel, removal and wrong actors. It passes on SQLite and disposable PostgreSQL 18 (2 adapter cases); the broader targeted SOC-010 group passed 7 cases. SOC-011 block path also checked for contact termination, both-direction private-message rejection, request rejection, owner-only visibility and independent moderation. Both remain partial pending manual account/browser, device/accessibility and localization acceptance.

Complete Python suite after the new regression: 475 passed, 251 optional/unconfigured PostgreSQL adapter variants skipped, 0 failures, one existing Starlette/httpx deprecation warning (1388.52s). Frontend 76/76, Ruff, Black (51), strict mypy (39), ESLint, JS syntax, Traceability 344/344 and Compose checks pass. Private staging schema 88 remains healthy; Main and player data unchanged.


## 2026-11-12 — SOC-012 Spielerprofile; SOC-006 Regelwerte bestätigt

SOC-012 ergänzt Schema 89 mit privater Standardeinstellung für alle bestehenden Konten, weltgebundener Opt-in-Profilkarte, strikter Feld-Allowlist, Widerruf, kosmetischem Titel und bis zu drei frei gewählten Abzeichen. Vertrauliche Konto-/Sicherheits-/Kolonie-/Armee-/Allianz-/Kommunikationsdaten werden nicht ausgegeben. Die bestehende Rangliste zeigt Name und Punktzahl weiterhin unabhängig von der Profileinstellung. Profilhistorie und verdiente Abzeichen sind noch nicht umgesetzt; SOC-012 und A07 bleiben deshalb partial.

Fokussierte API-/Privacy-/Migrationssuite auf SQLite und disposable PostgreSQL 18: 6 passed. Vollständige Python-Suite nach Schema 89: **478 passed, 253 optionale Adapterfälle übersprungen, 0 Fehler**, eine bestehende Starlette/httpx-Deprecation-Warnung (1573,34 s). Frontend 77/77, Ruff, Black (52 Dateien), strict mypy (40 Quelldateien), ESLint, JS-Syntax, Traceability 344/344 und Staging-Compose-Konfiguration bestehen.

Private Staging-Datenbank vor dem Rollout als `backups/fur-staging-pre-schema89-20261112.dump` gesichert. `pg_restore --list` und vollständiger Restore in isoliertes PostgreSQL 18 bestanden; vor Rollout Schema 88, fünf Konten, null Allianzen. Nur privates Loopback-Staging auf Schema 89 migriert; danach fünf Konten, fünf privat voreingestellte Profile, null Allianzen, App/Worker/DB/Mailpit/Proxy gesund, HTTPS-Health 200, Readiness true, keine Quarantäne und Scheduler-Verzug 0. Restore-Probe entfernt; Main unverändert und nicht öffentlich bereitgestellt.

Der Eigentümer hat die SOC-006-Kassenregeln ausdrücklich bestätigt: 1 % Gebühr je Ressource, ab 5.000 Bruttoressourcen zwei unabhängige Freigeber und vollständige Rückbuchung nach sieben Tagen. Diese Werte werden im vorhandenen Regelkatalog bereits exakt umgesetzt; die Eigentümerentscheidung ist geschlossen. SOC-006 bleibt wegen offener Balance- und manueller Betriebs-/Accessibility-Abnahme partial. Aktuelle Inventarzähler: 4 verified, 196 partial, 59 unverified, 85 not audited. Nächster Schritt: SOC-013 Notizen.


## 2026-11-13 — SOC-014 Berichtsfreigabe Vollsuite

Nach schema-90-Einbau bestand die vollständige lokale SQLite-Python-Suite mit 484 passed, 256 optionalen/nicht konfigurierten PostgreSQL-Adapter-Skips und 0 Fehlern (2141,16 s); eine bestehende Starlette/httpx-Deprecation-Warnung bleibt. Der korrigierte Allianz-Rückkehrtest prüft jetzt, dass Rückkehrarmeen zuerst unterwegs und nach Fälligkeit intakt zu Hause sind. Ruff, Black-Check (53 Dateien), strict mypy (41 Quelldateien) bestanden. Frontend 78/78, ESLint, JS-Syntax und Traceability 344/344 bestanden.

Fokussierte SOC-014 SQLite-/PostgreSQL-18-Tests sowie Restore der Schema-89-Staging-Sicherung in eine disposable PostgreSQL-18-Instanz und Schema-90-Migration bestanden; fünf Konten, null Allianzen und fünf private Profileinstellungen blieben erhalten. Docker Desktop war beim Rollout-Check pausiert, daher blieb persistent Staging auf Schema 89; Main und Spielerdaten wurden nicht verändert. SOC-014 bleibt partial bis privater Staging-Rollout und manuelle Zwei-Konten-/Browser-/Geräte-/Accessibility-/Locale-Abnahme abgeschlossen sind. Inventarzähler: 4 verified, 197 partial, 58 unverified, 85 not audited. Nächster Schritt: SOC-015 Moderation gegen aktuellen Quellcode auditieren.

## 2026-11-13 — SOC-014 privates Staging-Rollout

Docker Desktop ist wieder verfügbar. Vor dem Rollout wurde `backups/fur-staging-pre-schema90-20261113.dump` mit 431851 Bytes erstellt, per `pg_restore --list` validiert und vollständig in eine kurzlebige PostgreSQL-18-Wegwerfkopie restauriert. Das aktuelle Root-Appimage migrierte ausschließlich diese Probe von Schema 89 auf 90; fünf Benutzer, null Allianzen und fünf Profileinstellungen blieben erhalten, die Tabelle `alliance_shared_reports` wurde angelegt. Der alte Staging-Image-Build endete noch bei Migration 89; nach aktuellem Root-Build wurde das private Loopback-Staging aktualisiert.

Nach Rollout: Datenbank Schema 90, fünf Benutzer, null Allianzen, fünf Profileinstellungen und null geteilte Berichte. App, Worker, Datenbank, Mailpit und Staging-Proxy gesund; HTTPS-Health 200, Readiness true, keine quarantänisierten Aufträge und Scheduler-Verzug 0. Main/öffentliche Caddy-Freigabe nicht verändert. Der Probecontainer wurde entfernt. SOC-014 bleibt partial bis manuelle Zwei-Konten-/Browser-/Geräte-/Accessibility-/Locale-Abnahme abgeschlossen sind.

## 2026-11-13 — SOC-015 Chatmeldungen und Mute-Einsprüche

Schema 91 ergänzt Chatmeldungen und Einsprüche gegen aktive temporäre Mutes. Meldungen prüfen die aktuelle Sichtbarkeit derselben Welt, Allianz oder Privatunterhaltung und schließen eigene, ausgeblendete, doppelte oder nicht sichtbare Nachrichten aus. Spieler sehen nur ihre eigenen Fallstände; Moderation erhält eine begrenzte Warteschlange mit fallbezogenen Entscheidungen. Schließen/Ausblenden und Ablehnen/Aufheben eines Mutes werden auditiert. Kontosperrungs-Einsprüche sind nicht implementiert. Fokusprüfung SQLite + disposable PostgreSQL 18: 5 bestanden; vollständige Python-Suite: 485 bestanden, 257 optionale PostgreSQL-Adapterfälle übersprungen, kein Fehler, eine bestehende Starlette/httpx-Deprecation-Warnung. Frontend 80/80, ESLint, JS-Syntax, Ruff, Black, strict mypy und Traceability 344/344 bestanden.

Vor Staging wurde `backups/fur-staging-pre-schema91-20261113.dump` (435374 Bytes) erstellt und als Archiv validiert. Der vollständige Restore in die Wegwerf-PostgreSQL-18-Datenbank und Schema-91-Migrationslauf bewahrten fünf Benutzer, null Allianzen und fünf Profileinstellungen. Privates Loopback-Staging läuft auf Schema 91; App, Worker, PostgreSQL, Mailpit und Proxy sind gesund, HTTPS-Health 200, Readiness true, null quarantänisierte Aufträge und Scheduler-Verzug 0. Main blieb unberührt. SOC-015 bleibt partial bis manuelle Zwei-Konten-/Browser-/Geräte-/Accessibility-/Locale-Abnahme. Gesamtinventar unverändert: 4 verified, 197 partial, 58 unverified, 85 not audited; nächster Schritt: SOC-016 aus dem aktuellen Produktquellcode prüfen.


## 2026-11-14 — SOC-016 Rollout und ITEM-010 Notification-Grundlage

SOC-016 Schema 92 ist nach frischer Staging-Sicherung `backups/fur-staging-pre-schema92-20261114.dump`, Archivprüfung und vollständigem Restore-/Migrationslauf in disposable PostgreSQL 18 auf privates Loopback-Staging ausgerollt. Die Probe bewahrte fünf Konten, null Allianzen und fünf private Profileinstellungen. Alle fünf Services sind gesund; HTTPS Health/Readiness erfolgreich, kein quarantänisierter Auftrag, Scheduler-Lag 0. Main blieb unverändert. Vollsuite: **491 passed, 259 optionale PostgreSQL-Adapterfälle übersprungen, 0 Fehler**, eine bestehende Starlette/httpx-Warnung (3024,08 s). Fokus SOC-016 SQLite + PostgreSQL 18: 21 bestanden; Frontend 83/83; Ruff, Black (59 Dateien), strict mypy (41), ESLint, JS-Syntax und Traceability 344/344 bestanden.

ITEM-010 ergänzt Schema 93 (additiv zu SOC-016/schema92) mit kontengebundenen Kategorienpräferenzen und privaten Zustellfehlern. Ereignisse werden Wirtschaft/Forschung/Militär/Soziales/System zugeordnet; Mutes wirken beim Publish, Zustellfehler werden mit Versuchszahl bis zum fünften Versuch erneut probiert und dann privat angezeigt. Schema-92-Stagingbackup `backups/fur-staging-pre-item010-20261114.dump` (445547 Bytes) wurde archivgeprüft und in Wegwerf-PostgreSQL 18 restauriert; Schema-93-Delta erfolgreich angewandt, fünf Konten und null Allianzen erhalten, Probe gelöscht. Persistentes Staging bleibt schema92; Main unverändert. Fokustests 14 bestanden/2 optionale PostgreSQL-Skips; Migrationsgruppe 23 bestanden/19 optionale PostgreSQL-Skips; vollständige Python-Suite nach Delta **493 passed, 260 übersprungen, 0 Fehler**, eine bestehende Starlette/httpx-Warnung (812,54 s). Frontend 83/83; Ruff, Black (59 Dateien), strict mypy (41), ESLint, JS-Syntax und Traceability 344/344 bestanden. ITEM-010/UX-017 bleiben partial; Push (ITEM-011), vollständige Ereigniszuordnung/Filter/Verlauf, manuelle Geräte-/Screenreader-/Locale- und Runtime-Abnahme offen. Gesamtstatus: 4 verified, 198 partial, 57 unverified, 85 not audited; Gesamtabnahme unvollständig.


## 2026-11-14 — ITEM-010 Feedfilter und Verlauf

Der private Ereignisfeed unterstützt nun Kategorienfilter und begrenzte ältere Seiten per Sequenzcursor; API prüft aktive Welt und Eigentümer. Ereignisse werden in jeder Seite chronologisch dargestellt, ältere Treffer bei Kategorieauswahl über chunkweises Rückwärtsscannen gefunden. Unbekannte Typen werden als System eingeordnet. Regressionen: 16 fokussierte Python-Tests bestanden, 3 optionale PostgreSQL-Skips; Frontend 83/83; Ruff, Black-Check, strict mypy, ESLint und JavaScript-Syntax bestanden. Vollsuite nach Änderung läuft noch. Dokumentation und Featurestatus aktualisiert; ITEM-010/UX-017 bleiben partial bis Ereignisabdeckung und manuelle Accessibility-/Device-/Locale-Abnahme.


2026-11-14 Follow-up: AST-Audit aller in `game.py`/`systems.py` erkennbaren Player-Commandtypen; Kategoriezuordnung für Allianzprojekt-Erstellung/-Abbruch, Terra-Verteidigung und Kolonisierung korrigiert. Bisheriger vollständiger Python-Lauf (vor letzter kleinen Kategoriefeinheit) 495 passed/261 skipped/0 failed; erneuter Lauf auf aktuellem Stand läuft. Mapping-Regressions decken alle Hauptbereiche und sicheren System-Fallback ab.


## 2026-11-14 — ITEM-010 Abschluss der Implementierung und Vollregression

Event-Feed: aktive-Welt-API filtert Kategorien und lädt begrenzte ältere Cursor-Seiten; beobachtete Game-/Command-Eventfamilien sind kategorisiert und unbekannte Typen werden auf System abgebildet. Kategorieabdeckung, Privatsphäre, Filter und Reihenfolge sind regressionsgeprüft. Vollständige Python-Suite: **496 passed, 261 optionale PostgreSQL-Adapterfälle übersprungen, 0 Fehler**, eine bestehende Starlette/httpx-Deprecation-Warnung (1880,35 s). Aktuelle Kategoriezuordnung: 2 passed/1 PostgreSQL-Skip; Frontend 83/83; Ruff, Black-Check (53 Dateien), strict mypy (41), ESLint, JavaScript-Syntax, JSON-Metadaten und Traceability 344/344 bestanden. Schema-93-Restore-/Delta-Rehearsal in Wegwerf-PostgreSQL zuvor bestanden; persistentes Staging bleibt Schema 92, Main unangetastet. Allianzkasse: Eigentümerregeln bereits umgesetzt und bestätigt: Spenden gebührenfrei, 1 % je Ressource von Auszahlungen, 2 unabhängige Freigaben ab 5.000 Bruttoressourcen, volle Rückbuchung nach 7 Tagen. ITEM-010/UX-017 bleiben partial bis manuelle Browser-/Geräte-/Keyboard-/Screenreader-/Locale-Abnahme; Gesamtprojekt weiter offen.


## 2026-11-14 - ITEM-002 crafting and ITEM-003 recycling

ITEM-002 provides two explicitly provisional recipes in the per-world FUR-CRAFTING-1 opt-in; FUR-2 remains the default. ITEM-003 adds FUR-ITEM-RECYCLING-1: one field repair kit returns two crafting components and three textiles, below the three components and six textiles used to make it. Catalog loading rejects salvage output vectors above any producing recipe input vector. Both actions are in the strict API contract, transactional, idempotent, audited and available in the trade UI; overflow goes to existing reserves.

Combined ITEM-002/003 package regression: 48 passed. Authenticated API/crafting/recycling follow-up: 30 passed with one existing Starlette/httpx deprecation warning. Frontend 88/88. Ruff, Black, strict mypy (44 source files), ESLint for static/app.js, JavaScript syntax, JSON and Traceability 344/344 passed. The full Python suite is still running. FUR-3 values remain drafts; owner balance, PostgreSQL, browser, device, accessibility and localization acceptance remain open. Main and Staging were not changed.


## 2026-11-14 - ITEM-002/003 completed local regression checkpoint

Full Python suite: **533 passed, 261 optional/unconfigured PostgreSQL adapter cases skipped, zero failures**, with one existing Starlette/httpx deprecation warning (1635.46s). After the added item-stack and market-goods reserve-overflow assertion, the focused crafting/items/market/authenticated API package passed **50 tests**. Frontend 88/88. A disposable PostgreSQL 18 colony-supply/recall adapter run passed 16 tests; its container and anonymous volume were removed. Ruff, Black (64 files), strict mypy (44 source files), npm lint/check, JS syntax, JSON and Traceability 344/344 passed. Main and Staging were unchanged; no migration or deployment occurred. ITEM-002/003 remain partial because FUR-3 values are drafts and manual browser/device/accessibility/localization acceptance remains open. Next feature: ITEM-004.

## 2026-11-15 — SEAS-013 geplante weltgebundene Regelupdates

SEAS-013 ergänzt Schema 104 sowie Admin-Planung/Abbruch, world-spezifische Rollouthistorie, zeitlich geordnete Worker-Anwendung und erneute Kompatibilitätsprüfungen zum Aktivierungszeitpunkt. FUR-2 bleibt Standard; bereits gestartete Missionen behalten ihren gepinnten Kampfvertrag. Ein verspätet ungültiger Rollout wird atomar als fehlgeschlagen mit Auditgrund abgeschlossen. Regressionen: vollständige Python-Suite **570 passed, 280 optionale/unbereitgestellte PostgreSQL-Fälle übersprungen, 0 failed**, eine bestehende Starlette/httpx-Warnung (1028,48 s); `test_multiplayer.py` **272 passed, 260 optionale PostgreSQL-Skips, 0 failed**. Frontend **95/95**, Ruff, Black (75 Dateien), strict mypy (54 Module), ESLint, JavaScript-Syntax, Traceability **344/344** sowie Main- und Staging-Compose-Konfigurationsprüfungen bestanden. Docker Engine ist erreichbar. Keine persistente Datenbank migriert oder bereitgestellt.

SEAS-013 bleibt **partial**: PostgreSQL-18-Migrations-/Worker-Akzeptanz wurde hier mangels `FUR_TEST_POSTGRES` nicht ausgeführt; manuelle Browser-, Mobil-, Tastatur-/Screenreader- und Lokalisierungsabnahme sowie sicherer persistenter Rollout stehen offen. Inventar nach Status: **4 verified, 223 partial, 57 unverified, 60 not audited**. Nächster Arbeitsschritt: E15/Inventar paketweise fortsetzen.

## 2026-11-16 — SOC-006 Allianzkasse: Gebührensemantik präzisiert

Die freigegebene FUR-3-Regelversion 3 interpretiert den eingegebenen Antrag jetzt als gewünschte Nettoauszahlung. Die Allianz reserviert Auszahlung plus 1 % je Ressource, aufgerundet, sodass der Empfänger exakt den angefragten Betrag erhält. Die 5.000-Schwelle prüft den gesamten reservierten Bruttobetrag; unabhängige Freigaben, sieben Tage und volle Rückbuchung bleiben unverändert. Alte Anträge behalten ihre gespeicherte Regelversion/Prüfsumme. Gezielte SQLite-Kassenregression bestanden (1); vollständige Python-Suite 571 passed/280 optionale PostgreSQL-Skips/0 failed; Frontend95/95; Ruff, Black75, strict mypy54, ESLint, JS-Syntax und Traceability344 bestanden. PostgreSQL-Variante mangels `FUR_TEST_POSTGRES` übersprungen. Keine persistente Datenbank migriert. Manuelle Browser-/Mobil-/Keyboard-/Screenreader-/Lokalisierungsabnahme und persistenter Rollout bleiben offen. Inventar: 4 verified, 223 partial, 57 unverified, 60 not audited.


## 2026-11-16 — SOC-014 Berichtsfreigabe: Perspektivschutz und Schema 105

Quellenaudit fand einen Privacy-Fehler: alte Allianzprojektionen zeigten für Verteidiger die Angreiferperspektive und konnten bei ACS weitere Angreiferflotten zusammenfassen. Neue Reports speichern die private Eigentümerperspektive getrennt vom Combat-Payload; Verteidigergebnisse werden korrekt gespiegelt, ACS teilt nur den jeweiligen Flügel. Verteidigerberichte mit nicht trennbaren verbündeten Garnisonen sind nicht teilbar. Schema 105 widerruft gespeicherte Altprojektionen, deren Perspektive nicht rekonstruierbar ist; Spielerkonten und Kolonien bleiben erhalten.

Gezielte Privacy/API/Migrationsregression: **8 bestanden, 5 optionale PostgreSQL-Skips**; Frontend **95/95**. Erste Vollsuite: **548 bestanden, 281 übersprungen, 25 fehlgeschlagen**, sämtliche Fehler waren veraltete `max(schema_versions)=104`-Erwartungen. Nach Aktualisierung der Versionsprüfungen: betroffene breite Gruppen **381 bestanden, 281 übersprungen**; zwei versehentlich veränderte Outpost-Zählwerte wurden auf 104 korrigiert und einzeln bestanden (**2 passed, 2 PostgreSQL-Skips**). Weitere Schema-Migrationsstichprobe **5 passed, 4 PostgreSQL-Skips**. Keine zweite Vollsuite nach diesen Testkorrekturen; vollständige Regression bleibt daher offen. Vorher liefen Ruff, Black75, strict mypy54, ESLint, JavaScript-Syntax und Frontend95 erfolgreich; Abschlussnachprüfung der Quality Checks nach Testdateiänderung offen. PostgreSQL Engine nicht verfügbar. Keine persistente Datenbank migriert. SOC-014 bleibt partial bis PostgreSQL/Backup- und manuelle Browser-, Geräte-, Accessibility- und Localization-Abnahme.

Aktualisierung SOC-014-Abschlusscheck: Nach Korrektur der Schemaobergrenzen bestand die finale Regression der vier betroffenen Python-Dateien **383 passed, 281 optionale PostgreSQL-Skips, 0 failed**, eine vorhandene Starlette/httpx-Warnung (773,81 s).

## 2026-11-16 — SOC-015 gesperrte Konten können Einspruch einreichen

Schema 106 ergänzt eine begrenzte, auditierbare Appeal-Tabelle mit höchstens einem offenen Ban-Einspruch je Konto. Der Login bietet nach bestätigter Kontosperre ein Formular an. Der Einspruch-Endpunkt verlangt das Kontopasswort sowie TOTP oder einen einmaligen Recovery-Code, wenn MFA eingeschaltet ist. Er erstellt keine Sitzung und entsperrt das Konto nicht selbst. Moderatoren/Admins sehen den Begründungstext im begrenzten Moderationskorb und können ablehnen oder entsperren; Freigabe löscht keine Daten und erzeugt keine Sitzung, der Spieler muss sich danach normal anmelden.

Gezielte API/MFA/Migration/Moderationssuite: **5 passed, 3 optionale PostgreSQL-Skips**, eine bestehende Starlette/httpx-Warnung; Frontend **97/97**. Ruff, Black, strict mypy (drei Quelldateien), JavaScript-Syntax und Traceability344 bestanden. Keine persistente Datenbank migriert. PostgreSQL18-/Backup-Restore-, manuelle Browser-/Geräte-/Accessibility-/Locale-Abnahme offen; SOC-015 bleibt partial.

Abschlussregression: Vollständige Python-Suite **576 passed, 282 optionale PostgreSQL-Skips, 0 failed** in 1016,15 s; eine bestehende Starlette/httpx-Deprecation-Warnung. Frontend **97/97**; Ruff, Black (75 Dateien), strict mypy (54 Module), ESLint, JavaScript-Syntax und Traceability 344/344 bestanden. Ein frisches Backup des privaten Staging-Schemas 92 wurde in PostgreSQL 18 restauriert und dort mit Migration 105/106 bis Schema 106 migriert: fünf Benutzer erhalten, Appeal-Tabelle leer, keine alten Allianzprojektionen vorhanden. Die PostgreSQL-API-Tests konnten wegen fehlendem pytest im App-Image nicht ausgeführt werden. Beim anschließenden Test-Runner-Einrichten wurden Migration 105/106 versehentlich zusätzlich auf das persistente private Staging angewendet (Schema 92→106); die 0 vorhandenen Allianz-Berichtsfreigaben wurden durch Migration 105 widerrufen. Nachkontrolle: fünf Nutzer, fünf Kolonien, fünf Profileinstellungen und sechs Sitzungen erhalten; null Appeals; Staging health/readiness 200. Ein frisches Recovery-Dump `/tmp/fur-staging-schema106-recovery.dump` wurde erstellt und mit `pg_restore --list` geprüft. Main blieb Schema79 mit drei Nutzern unverändert. Staging-App/Worker-Images sind noch alt; kein Rollout erfolgte. Browser-, Geräte-, Accessibility- und Locale-Abnahme bleibt offen.

Nachtrag Session-Sicherheit SOC-015: Beim ersten angenommenen Ban-Einspruch werden alle noch vorhandenen Sitzungen des gesperrten Kontos transaktional widerrufen; Wiederholungen legen weder zusätzliche Appeals noch doppelte Audit-Einträge an. Ein erweiterter API-Test fand zunächst die bestehende Sitzung und bestätigte nach der Korrektur deren Widerruf. API/MFA-Tests gegen PostgreSQL liefen danach 2/2 durch. Ruff, Black75, strict mypy54 und Frontend97 pass. Der PostgreSQL-Schemaadapter-Test hing bei seiner lang laufenden Testvorbereitung; die SQLite-Schemaregression war bereits in der Vollsuite enthalten.

Betriebsnachtrag: Während eines fehlgeleiteten Test-Runner-Aufrufs wurden Schema 105 und 106 zusätzlich auf das private Staging angewandt (92→106). Der 105-Schritt widerrief null vorhandene Allianzprojektionen; 106 legte eine leere Appeal-Tabelle an. Nachkontrolle und frisches, archive-validiertes Recovery-Dump: fünf Nutzer, fünf Kolonien, fünf Profileinstellungen und sechs Sitzungen intakt; health/readiness 200; Main unverändert (Schema79, drei Nutzer). Das Staging-App-/Worker-Image ist noch alt, daher ist SOC-015 nicht ausgerollt.




## 2026-11-16 — SOC-016 source audit and focused regression

Current source confirms schema92 public/world-scoped announcements and recipient-only private system mail; schema103 schedules public publication and marks emergencies without changing private mailbox semantics. Admin/moderator scope, due-time filtering, recipient-bound reads/cursors and body-free audit are covered by current source and tests. Focused Python/API/schema suite: 4 passed, 3 optional PostgreSQL skips, one existing Starlette/httpx warning; frontend escaping/separation 1 passed. Historical disposable PostgreSQL18 scope run: 21 passed. Current Staging runs root images on schema106; five accounts/colonies preserved; health/readiness200. Strict readiness still has admin_mfa_ready=false. SOC-016 remains partial pending manual two-account/browser/device/accessibility/localization acceptance.


## 2026-11-16 — Staging-Rollout und SOC-016/A06/PVE-001-Abgleich

Aktuelles Staging-Backup ackups/fur-staging-schema106-pre-soc015-20261116-073341.dump (SHA256 9CC35010EA7A68DDE71B43D1ECF978E5C00A054F260336B43242DDDD829F5DE2) bestand pg_restore --list und vollständigen PostgreSQL-18-Wegwerfrestore: Schema106, fünf Nutzer/Kolonien/Profileinstellungen, sechs Sitzungen, null Appeals/Allianzfreigaben. Restorebericht liegt daneben; Wegwerf-DB entfernt. Nur private Staging-App und Worker wurden aus aktuellem Root-Code rebuilt/recreated. Beide healthy; HTTPS health/readiness 200, Home mit Ban-Appeal-Panel, unbekannter Testnutzer-Endpunkt erwartungsgemäß 400, Workercheck bestanden. Datenwerte unverändert; Main blieb Schema79/3 Nutzer. Strikte Staging-Readiness meldet weiter dmin_mfa_ready=false; keine öffentliche Freigabe.

SOC-016 Quellabgleich: schema92 trennt öffentliche Welt-/Globalankündigung und empfängergebundene Systempost; schema103 ergänzt Fälligkeit/Notfallmarkierung ohne Mail-Scope zu verändern. Fokustests4 passed/3 optionale PG-Skips, UI1 passed; Status partial wegen manueller Browser-/Geräte-/Barrierefreiheits-/Lokalisierungsabnahme.

A06 wurde im aktuellen Quellstand auf SOC-008-Allianzforum gemappt und von 
ot_audited auf partial gesetzt. Threads/Beiträge, Mitgliederscope, Rollen, Archiv, private Reports, Pagination und XSS-Schutz belegt; Fokus4 passed/3 optionale PG-Skips, UI1 passed. Manuelle Abnahme bleibt offen. Inventar jetzt 4 verified/224 partial/57 unverified/59 not audited.

PVE-001-Audit bestätigt einen echten Scope-Unterschied: aktuelles FUR-2 enthält drei seedstabile Neutralposten-Fraktionen und bounded resupply, keine fünf eigenständigen NPC-Lager/Profile/Actions. PVE-001 bleibt partial; das bestehende FUR-2-Verhalten muss erhalten bleiben, Erweiterung versioniert/opt-in. Nächster Paket-Schritt PVE-001/002.



## 2026-11-16 — PVE-001/002 NPC-Camp-Katalog und Persistenz

FUR-2-Neutralpostenlogik bleibt unverändert. `FUR-3-NPC-CAMPS-1` ergänzt fünf unterschiedliche Profile mit startenden Ressourcen/Einheiten und erlaubten Policy-IDs. Schema107 speichert weltgebundene Lager, Bestände, Truppen und Tageskontingente sowie eine eindeutige Ereignistabelle. Schema108 erweitert die Rollout-Constraint rückwärtskompatibel; ein SQLite-106→108-Drill erhielt eine existierende Rolloutzeile und nahm den neuen Schlüssel an. Admin-Rollout und Opt-in bei Weltgründung sowie active-world Status/UI sind angebunden.

Fokussierte SQLite-Tests: 6 passed/4 optionale PostgreSQL-Skips; ausgewählte Frontend-Escapingtests 2 passed; Ruff, Black, strict mypy, npm lint/check bestanden. Regeln sind als vorläufige Balance gekennzeichnet. Noch offen: Effekte der Aktionen, NPC-Bewegung/Bereitstellung, Tagesreset, PostgreSQL-Adapterausführung, manuelle Mobil-/Accessibility-/Locale-/Balanceabnahme. Daher PVE-001/002 `partial`, keine Verallgemeinerung auf vollständig fertig. Persistent Main und Staging unverändert; keine Bereitstellung dieser Migrationen. Aktuelles Inventar: 4 verified/224 partial/57 unverified/59 not audited.


## 2026-11-16 — PVE-001/002 Camp-Aktionen und Tageskontingente

FUR-3-NPC-CAMPS-1 enthält nun den versionierten Kosten-/Ertragsvertrag: Versorgung füllt begrenzt Vorräte, Verstärkung rekrutiert zwei Ranger und einen Wächter, Befestigung wächst bis Stufe 10. Aufklärung und Manöver verbrauchen Bewegungskontingent und protokollieren Zähler, bewegen noch keine Einheiten und decken keine Sektoren auf. Eindeutige Event-IDs verhindern bei Wiederholung doppelten Verbrauch. `Game.advance` setzt Bewegungs- und Bereitstellungslimits idempotent an UTC-Tagesgrenzen zurück. Schema109 speichert Befestigung, Aufklärungs- und Manöverzähler. UI erklärt vorläufige Werte und Grenzen.

Fokussierte SQLite-NPC-Gruppe 8 passed/6 optionale PostgreSQL-Skips; Frontend2/2; Ruff, Black, strict mypy, npm lint/check, JS-Syntax und 344-ID-Traceability bestanden. FUR-2-Frontierregression bleibt grün. Weiter offen sind automatische NPC-Entscheidungen, reale Bewegung/Spähwirkung, PostgreSQL-Ausführung und manuelle Balance-/Browser-/Geräte-/Accessibility-/Locale-Abnahme. Daher weiterhin `partial`. Main und private Staging nicht geändert oder migriert; Main Schema79/Staging Schema106, Staging `admin_mfa_ready=false`. Inventar: 4 verified/224 partial/57 unverified/59 not audited.


## 2026-11-16 — PVE-001/002 tägliche NPC-Policy

`Game.advance` führt in ausdrücklich aktivierten FUR-3-Welten je Lager höchstens eine bezahlbare Profilaktion pro UTC-Tag aus. Die erste bezahlbare Aktion der festen Profilreihenfolge gewinnt; Event-IDs binden Welt, Lager und Tag und blockieren Worker-Duplikate. Es werden ausschließlich Lagerbestand, Truppen und begrenzte Zähler geändert. Keine Angriffe, Kartenbewegung, Aufdeckung oder Spielerbeute. UI, versionierter Regelkatalog, Spec, JSON-Matrix und Traceability aktualisiert. Die vom Nutzer bestätigten Allianzkassenwerte sind in Regelversion 3 bereits umgesetzt; persistente Datenbanken wurden nicht geändert.

Neue SQLite-Regression prüft fünf tägliche Events, Retry ohne Duplikat, Folgetag und FUR-2-Weltisolation. NPC-Fokuslauf: 5 passed/5 optionale PostgreSQL-Skips. Vollständige Ruff/Black/mypy/pytest- und Frontendläufe nach dem letzten Patch folgen. Inventar bleibt 4 verified/224 partial/57 unverified/59 not audited; PVE-001/002 bleiben `partial`, da Scout/Manöver noch keine Bewegung/Sichtwirkung haben und PostgreSQL-/Browser-/Accessibility-/Locale-/Balanceabnahme offen sind. Persistente Main-/Staging-Datenbanken, Daten und Deployments unverändert.


Final regression after updating migration rehearsal: full Python suite 581 passed / 287 optional PostgreSQL skips / 0 failed / one pre-existing Starlette-httpx warning (1046.90s). Frontend 98/98. Ruff, Black check (57 files), strict mypy (55 modules), ESLint, JavaScript syntax and Traceability344 pass. Schema rehearsal goes from a disposable schema71 source through109 and confirms the original copy remains71. PostgreSQL is unavailable; no persistent Main/Staging migration, deployment or player-data write was performed. SOC-006 treasury values match the owner-approved v3 already in source. Inventory remains 4 verified/224 partial/57 unverified/59 not audited; PVE-001/002 partial pending actual scout/maneuver effects and manual/adapter acceptance.

## E11 cross-database verification follow-up (2026-11-16)

A full mixed SQLite + disposable PostgreSQL 18 regression run completed in 6103.18s with **864 passed, 1 skipped, 3 failed**. All three failures were PostgreSQL-only test portability/rehearsal defects: psycopg `dict_row` was asserted as a positional row; an expected immutable-trigger exception left the surrounding PostgreSQL transaction aborted; and the schema-10 replay rehearsal dropped `world_settings` while a later commander table still referenced it. The tests now read named columns, isolate the expected trigger error with a savepoint, and temporarily remove/recreate only the dependent FK around the simulated migration. The corrected tests pass on SQLite (**3 passed**) and disposable PostgreSQL 18 (**3 passed**). Ruff and Black checks for `tests/test_multiplayer.py` pass. The complete suite has not yet been rerun after these test-only fixes, so full regression is not yet green. The temporary PostgreSQL containers were removed; Main and Staging remained healthy and untouched. Current feature counts remain 344 total: 4 verified, 224 partial, 57 unverified, 59 not audited. PVE-001/002 movement/scouting effects and manual browser/accessibility/localization/balance acceptance remain open.


## 2026-11-18 — E11 continuation through PVE-008

The numbered master package validated. The root and master inventories match on all 344 IDs and epic assignments. Current canonical counts are 4 verified, 229 partial, 52 unverified and 59 unaudited.

- PVE-004 and PVE-005. The strict HTTP contract now accepts COMBAT-5 and supported world opt-ins, scheduled ruin rollouts, Ranger surveys and scoped movement quotes. Ruin resolution uses portable conditional upserts, retains the newest private observation, and records the actual bounded cargo. The map projects visible targets and private observations. Dispatch, recall, cross-world rejection, two-worker resolution and single return have focused coverage.
- PVE-006. Frontier expedition probabilities, loss ranges and resource ranges come from the server's pinned public rules catalog. A renderer regression verifies that the dialog follows the supplied values.
- PVE-007. Schema 118 adds the optional world boss with preparation, two phases, twelve slots and an account-bound contribution. The owner selected one damage-weighted share per contributing account from a capped pool. Mixed-adapter tests cover overkill, return after victory, overflow conservation and two concurrent claims.
- PVE-008. Schema 119 adds the CAMPS-3 invasion window with a 30-minute warning, 48-hour active period, six-attack budget, existing target protections and bounded aggregate history. Mixed-adapter regressions exercise the warning gate, duplicate admin requests, a real private attack, the spent budget and ended history.
- Adjacent audit. The existing Orbit gateway honors citadel ownership. The worker already supports inactivity warning and preserved-colony reactivation. The protected market convoy is a delivery system. The separate contested NPC event awaits the PvE/PvP participation policy.

The focused pre-boss E11 group passed 29 mixed-adapter cases. The schema 118 group passed 21 cases. The focused schema 119 boss/invasion/command/restore group passed 26 cases, with the existing Starlette/httpx deprecation warning. Frontend passed 103/103, plus ESLint, JS syntax, Ruff, Black (79 files), strict mypy (58 modules), master package and traceability. Chromium exercised ruin dispatch and observed the worker result at desktop and mobile widths. A separate 390px Chromium run exercised authenticated boss booking and slot refresh. Physical mobile, keyboard/screen-reader and full localization acceptance remain open. The 903-case SQLite regression is running. The first fresh container check hit a startup timeout despite a successful app health response. A retry is running on disposable Compose services.

Read-only online backup backups/local-sqlite-preservation/empire-pre-roadmap-20261118T195645150641Z.sqlite3 passed integrity and foreign-key checks and rehearsed schema 110→119. The restore exposed and then verified a fix for the known early CAMPS-2 snapshot. backups/fur-main-pre-roadmap-20261118T200429Z.dump restored with three users/colonies and migrated 79→119. backups/fur-staging-pre-roadmap-20261118T200429Z.dump restored with five users/colonies and migrated 106→119. Both dumps passed archive validation before restore. Main, Staging and the reference archives stayed outside all migration and test paths. See the incident entry below for the unintended local SQLite migration.

The dependency audit remains open for certifi PYSEC-2026-4320 and urllib3 PYSEC-2026-4175/4176/4177. The Node audit reported zero findings. PVE-004 to PVE-008 remain partial. PVE-009 is next. RESUME_STATE.json tracks the decision and verification status.


### Disposable container retry

Fresh PostgreSQL 18, app and worker started on an isolated Compose project. App health, readiness with zero quarantined jobs, worker check and schema 119 passed. The probe used host readiness polling with a longer startup window after health-check timeouts under concurrent test load. The disposable services and volume were removed.

 
### Local SQLite test-isolation incident

An unguarded full-run shard executed the existing multiplayer login-rate test. It imported FastAPI before configuring its temporary database, triggering initialization and migrating the live default data/empire.sqlite3 from 110 to 119. The affected run was stopped. The live local file and the fresh backup at backups/local-sqlite-preservation/empire-post-verification-incident-20261118T210225153381Z.sqlite3 passed integrity and foreign-key checks.

The read-only comparison against the pre-work schema-110 archive found every pre-existing row unchanged in all shared columns. Shared-table differences were nine added schema rows and five added rule-catalog rows. Eight new gameplay tables were empty. Main (79, three users/colonies) and private Staging (106, five users/colonies) retained their live schemas and counts.

tests/conftest.py now redirects implicit API imports to a temporary SQLite database before collection and clears Docker/production database overrides. The login-rate test sets its actual disposable fixture path before import. Its SQLite replay passed with the live file SHA-256 unchanged. Ruff, Black (80 files) and strict mypy (58 modules) passed. The 903-case suite was restarted with the guard, independent temp paths and a live-file hash check.

### Guarded verification completed

The full eight-shard suite collected 903 cases. It finished with 604 passed, 299 optional PostgreSQL parametrizations skipped, zero failures and the existing Starlette/httpx deprecation warning in each affected shard. Wall time was 614.5 seconds. The persistent SQLite SHA-256 matched before and after the run. A separate guarded mixed-adapter check of login-rate limiting, Orbit access, inactivity/reactivation and quest rewards passed eight cases, with the same live-file hash before and after. The temporary PostgreSQL probe was removed.

ESLint, JavaScript syntax and all 103 frontend tests passed on the final UI. Ruff, Black (80 files) and strict mypy (58 modules) passed. The traceability validator now checks the implementation matrix alongside the canonical inventory and the Markdown evidence. The master and canonical epic assignments match for all 344 IDs. Four entries are verified, 229 partial, 52 unverified and 59 unaudited.

The next dependent implementation is PVE-009. The convoy's PvE-only or player-contested participation policy is awaiting the owner decision. The older SQLite file is retained in its verified schema-110 backup and the current schema-119 file has a second verified backup. The code-level pytest isolation guard is active.
# Production deployment progress — 2026-11-20

- [x] Confirm SSH key authentication and vendor host fingerprint.
- [x] Inventory VPS. Debian 13, 8 CPUs, 16 GB RAM, approximately 300 GB free.
- [x] Install Debian docker.io and docker-compose packages. Docker enabled at boot.
- [x] Create furdeploy, install public key, test SSH and passwordless sudo.
- [x] Enable UFW for TCP 22, 80, 443, including IPv6.
- [x] Disable SSH password and keyboard-interactive authentication after alternative admin login succeeded. Root key authentication retained.
- [x] Preserve local SQLite backup with integrity check.
- [ ] Complete source transfer and production build.
- [ ] Rehearse SQLite to PostgreSQL migration without modifying original data.
- [ ] Configure real SMTP, operator settings, DNS and HTTPS.
- [ ] Restore drill, monitoring, release scripts and end-to-end tests.

Public DNS currently returns NXDOMAIN. Existing local SMTP settings are localhost placeholders. Production code requires PostgreSQL and TLS SMTP. No public go-live has been verified.

## VPS installation continuation — 2026-11-20
- Production source transferred and image built on VPS.
- PostgreSQL 18 started on private Compose network with persistent volume and fresh server-generated secrets.
- Application schema migrations completed in PostgreSQL.
- SQLite migration rehearsal on backup copy passed, schema 119 to 121.
- Full player-data transfer to PostgreSQL remains pending.
- Initial PostgreSQL backup and isolated restore drill initiated, result pending.
- Domain activation and real SMTP configuration remain external dependencies.

## Installed runtime and remaining gates
The production image is built. PostgreSQL contains 4,848 imported rows, one player and one colony from the migration rehearsal copy. Sessions, rate limits and runtime status were omitted. No additional writes from the original local database are synchronized automatically.
A post-import backup was restored successfully into fur_player_restore_drill. Daily backup-scheduler is running. No external backup destination or retention policy is installed yet.
App and worker now run with FUR_ENV=production behind a loopback-only app port. Public proxy and TLS remain pending.
Selected mail design is authenticated TLS SMTP on mail.fur-empire.de. This is currently configuration only. Mail daemon, credentials, certificate, DKIM, SPF and DMARC still require implementation and verification.
Operator name and contact were taken from the existing netcup account context.

## Reverse proxy and restart validation
Caddy configuration validates and the public proxy is started. WWW redirects to the canonical domain. App and worker restarted successfully, readiness true afterward, and the player/colony counts remain one each.
Domain still has pending status in netcup CCP, with no DNS editing controls exposed. Public DNS activation is therefore still required. TLS issuance is not verified.
Required initial DNS records after activation: @ A 62.83.116.160, www A 62.83.116.160, mail A 62.83.116.160. Mail authentication records must follow the actual mail installation.
Health inspection script added at deploy/healthcheck.sh. Strict readiness currently reports admin_mfa_ready false.

## Runtime monitoring and update process
A systemd timer runs deploy/monitor.sh every five minutes. Checks cover HTTP readiness, worker heartbeat, PostgreSQL availability, backup age, disk threshold, container state and resource usage. Results go to the system journal. External alerts are not configured.
deploy/release.sh provides an exclusive deployment lock, configuration validation, previous-image tag, database backup, image build, stopped-worker migration, health-gated service update and runtime inspection. It intentionally leaves failed migrations stopped for operator diagnosis. The release script has syntax validation only and has not yet passed a full deployment rehearsal.

## Off-host backup
A post-import PostgreSQL dump was downloaded over verified SSH to backups/fur-vps-offsite-initial.dump on the development computer. This is a manual second copy, not automated external backup.
Rollback procedure is described in deploy/ROLLBACK.md. Database rollback requires a new restored database and compatibility validation. Automatic schema rollback is disabled.

## Deployment and host restart verification
deploy/release.sh completed successfully on the VPS with pre-release backup, cached image build, schema migration, service restart and runtime checks.
A controlled host reboot was performed after another backup. Docker, app, worker, PostgreSQL, Caddy and backup-scheduler started automatically. HTTP readiness returned true after reboot. Before reboot the player/colony inventory was one each and the orphan-colony count was zero.
Ruff and Black checks passed. Strict mypy passed for 60 source files. Full pytest execution is in progress.

## Resource limits and audit
Compose now limits app and worker to 1 GiB RAM, 2 CPUs and 256 processes each. PostgreSQL is limited to 2 GiB, 2 CPUs and 256 processes. Caddy is limited to 256 MiB, 1 CPU and 128 processes. Applied after a fresh backup.
Frontend ESLint and syntax checks passed. All 105 frontend tests passed.
pip-audit failed with reported vulnerabilities in certifi 2026.7.22 and urllib3 2.7.0. Reported correction versions are certifi 2026.10.18 and urllib3 2.8.0. Verification and targeted remediation remain pending. Full Python tests remain running.

## Dependency security remediation
Targeted required security updates applied in requirements.lock: certifi 2026.7.22 to 2026.10.23 and urllib3 2.7.0 to 2.8.0. Package versions confirmed against PyPI. Re-running pip-audit against the updated lock completed successfully with no known vulnerabilities. VPS image rebuild and deployment initiated with the existing release script and fresh pre-release backup. Full Python suite still running against the previous local environment.

## Domain activation detected
Public DNS now resolves fur-empire.de to 46.38.243.234, the current provider default. It must be changed to 62.83.116.160.
The previously authenticated netcup CCP session has expired. User reauthentication was requested before DNS editing can proceed.
The updated running app confirms certifi 2026.10.23 and urllib3 2.8.0; readiness remains true.

## DNS and mail preparation
netcup accepted the submitted A records for @, www and mail pointing to 62.83.116.160. Its UI currently reports deployment in progress. Authoritative DNS still returns the provider default for apex and no www record.
Earlier automatic ACME attempts failed against the old DNS and reached a temporary Let's Encrypt authorization failure limit. Valid production TLS remains unverified.
Postfix and OpenDKIM installation started, configured for loopback-only SMTP and local recipients while TLS/authenticated submission is pending. No public SMTP firewall port opened. DKIM key generation is on the VPS only.
All single-column foreign-key references in the imported PostgreSQL database were checked with no orphan references detected. Outbox is empty.

## SMTP authenticated transport
Postfix submission is bound to the Docker bridge and loopback. UFW allows port 587 only from the backend subnet 172.18.0.0/16 to 172.18.0.1. SMTP authentication requires TLS, uses a random server-only secret and SASL identity furmailer@fur-empire.de.
The application connects using fur-empire.de mapped internally to the bridge and verifies the valid public certificate. STARTTLS and SMTP authentication were tested successfully from the running app container.
External delivery, DKIM signing configuration, SPF/DMARC records, reverse DNS and certificate refresh integration remain pending. OpenDKIM keys exist but signing is not yet active.
Production Compose currently assumes backend gateway 172.18.0.1, which must be made explicit or configurable before deployment portability is claimed.

## HTTPS registration test
Created GoLiveTest20261120 through the production registration endpoint using go-live-test@fur-empire.de. Secure session cookie and authenticated state loading passed. TLS certificate validation remained enabled. The test explicitly resolved the domain to 62.83.116.160 because ordinary local DNS still used the old provider IP.
Test password is in .secrets/go-live-test.json only. This is an explicitly identified production test account. Email confirmation and game commands are still untested.
OpenDKIM signing configuration is active and both Postfix and OpenDKIM services are running. Public DKIM/SPF/DMARC publication and external delivery verification remain pending.

## Authentication and local email tests
GoLiveTest20261120 successfully logged in over valid HTTPS, loaded its authenticated state, logged out through the CSRF-protected endpoint and then received HTTP 401 for protected state access.
The queued confirmation mail was delivered to a dedicated go-live-test alias in the server's local root mailbox. Postfix queue is empty. This proves internal SMTP acceptance and local delivery only. External provider delivery remains unverified.

## Email verification and build test
Consumed the actual single-use verification code from the test account's delivered local mailbox through /api/v1/account/public. Verification succeeded, followed by a normal login.
Submitted a wood-building command twice with the same idempotency token through /api/v1/command. Both requests succeeded. Database command-count verification follows separately. This test uses only GoLiveTest20261120 and preserves imported player data.

## Mail authentication DNS submission
Submitted TXT records at netcup for SPF (v=spf1 ip4:62.83.116.160 -all), DMARC (quarantine with strict alignment), and the server-generated fur._domainkey DKIM public key. netcup reports deployment in progress. DNS publication and key validation remain pending.
A TCP connectivity probe to Gmail's inbound SMTP port 25 was started. External delivery is not yet demonstrated.

## Worker completion and mail DNS validation
The test account's wood building reached level 2 and its jobs queue is empty, confirming completion of the submitted build by the worker.
OpenDKIM public-key lookup validates successfully (key OK). The lookup reports DNSSEC is not secured. Google public DNS resolves the game domain to 62.83.116.160. No AAAA record is published.
The normal development-computer HTTPS request still timed out before DNS cache clearing, while certificate-validated direct-IP resolution succeeds.

## UI deployment and mail certificate renewal
The revised generic online/local-compatible landing labels were deployed successfully through release.sh. Frontend lint, syntax and 105 tests passed before deployment.
Installed hourly fur-mail-tls.timer running deploy/refresh-mail-tls.sh. It checks certificate validity, detects certificate hash changes and reloads Postfix only when the Caddy certificate changes. Initial service run succeeded.
Public /api/v1/ready returns true without DNS override. Strict production readiness still fails because admin_mfa_ready is false.
Provider firewall inspection confirms netcup Mail block drops outbound TCP 25, 465 and 587. Action-time user confirmation to remove this policy is pending. No policy change performed.

## Additional public game commands
The verified GoLiveTest20261120 account submitted barracks and laboratory build requests through the normally resolved public HTTPS domain. Both were accepted and two jobs were queued. Completion, research and training tests follow after server-side timers finish.
Compose backend subnet and SMTP gateway are now parameterized locally to make the selected SMTP route reproducible. This network configuration change is validated syntactically but has not been applied to running production or staging.

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

## Priority update — four-language open beta
Original production goal retained. Added initial centralized four-language catalogs and browser language detection, persistent manual selector, interpolation and Intl formatting helpers. Landing/navigation integration started. Full UI/server message extraction, account preference persistence, beta consent/password confirmation and four-language end-to-end tests remain pending. Changes are local and have not been deployed.

Four-language authentication mode labels, resource labels and number formatter integrated locally. Language changes rerender the existing in-memory game state, preserving the account and world. Catalog loading tolerates unavailable non-default translations and retains source labels when no translation exists. Full UI coverage and backend message keys remain outstanding.

## Immediate live delivery preference
Owner requested immediate live delivery of working changes. Current language package deployment started after 110 frontend tests, five server i18n tests, account-language persistence/security test and isolated account-security regression passed. Original full suite had one account-security failure that did not reproduce in isolation, requiring broader follow-up.
The package includes partial four-language coverage, persistent account preference migration 122 and opt-in localized API error keys. It is not full four-language acceptance. Beta password confirmation/consent and full translation remain pending.

Base FUR-2 buildings, research and units have translated catalog names and available descriptions in all four languages, deployed through release.sh. Public catalog checks and six i18n tests passed. Language-switch regression verifies numeric costs and prerequisites remain unchanged. Broader advanced-feature and system-text translation remains pending.

Translated base construction/research queue actions, level labels, requirements label, troop readiness/recruitment controls and related headings in all four catalogs. Rendered translation attributes are applied after content insertion. Frontend suite passed and deployment completed with public readiness true. Full advanced UI coverage remains open.

Public beta registration accepted the new password-confirmation and versioned acceptance payload in de/en/es/fr. Four explicitly named test accounts initialized successfully with their requested language and normal three-resource state. These are API-level tests; full browser lifecycle validation is still pending.

Owner supplied responsible operator as Talent Link Ltd & Co. KG, currently in formation. Production operator name updated to Talent Link Ltd & Co. KG (in Gründung). Public company address and designated company contact remain unspecified.

Security-email subjects and bodies now use the saved account language and shared four-language message keys. Single-use code lifetime remains 30 minutes. Focused localized-mail, outbox and reset regression checks started. Not yet deployed pending those results.

Kommando overview hero, greeting, main statistics and headings now use four-language catalog keys. Safe JSON placeholder parameters are applied through textContent. Seven i18n tests including hostile player-name text passed, frontend checks passed, release deployed and public readiness verified. Queue details and further overview subpanels still need full localization.

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
