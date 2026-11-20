# Release-Prüfung vom 6. November 2026

## K02 / WAR-001 COMBAT-4-Rosterpfade — 12. November 2026

- Vollständige Python-Suite SQLite: 427 bestanden, 225 übersprungen, eine vorhandene Starlette/httpx-Deprecation-Warnung (546,76 s). Die PostgreSQL-Adaptertests wurden übersprungen, da `FUR_TEST_POSTGRES` in diesem Lauf nicht gesetzt war.
- Ruff und Black für `fur_empire`/`tests`, strict mypy für 33 Module bestanden. Neuer COMBAT-4-Test prüft Profile und Logistikkonvoi in der neutralen Gefechtsprobe. ACS-2/ACS-3, passive Festung, Rückkehr, Garnison, Transport und Expedition geprüft.
- Repositoryweiter Ruff-/Black-Aufruf findet weiterhin fünf Format-/Importverstöße in den fremden Übergabepaket-Skripten `FUR_CODEX_UEBERGABE/MASTER_SPEC/scripts/prepare_traceability.py` und `validate_package.py`; Produktcode und Tests sind sauber.
- FUR-2 und frühere Kampfregel-Snapshots unverändert. Keine persistenten Datenbanken oder Live-Stacks geändert. K02 bleibt `partial`: Reparatur-/Wrackregeln, Balanceabnahme und Browser-/Geräte-/Lokalisierungs-/Barrierefreiheitsabnahme fehlen; COMBAT-4 bleibt source-only.

## K03 / WAR-010 FUR-3-Gegenaufklärung — 12. November 2026

- Regelkatalog `FUR-3-TERRA-INTELLIGENCE-1`: Abfang `min(50%, 2% × Taktik + 3% × Wall)`, Entdeckung `min(60%, 10% + 3% × Taktik + 2% × Wall)`. Versand pinnt Version, Prüfsumme, Wahrscheinlichkeiten und Seed-Commitment; der Seed bleibt serverseitig.
- Fokustests SQLite + PostgreSQL 18: 8 bestanden. Vollständige Python-Suite SQLite + PostgreSQL 18: 634 bestanden, 1 übersprungen, eine bestehende Starlette/httpx-Deprecation-Warnung (2.348,98 s).
- Ruff, Black-Check (44 Dateien), strict mypy (33 Dateien), ESLint, JavaScript-Check und Traceability für alle 344 IDs bestanden.
- Das Missionsfenster warnt vor FUR-3-Entdeckung/Abfang; FUR-2-Text bleibt erhalten. Frontend 65/65, ESLint und JavaScript-Syntax bestanden. Neues App-Image auf privatem Staging deployed; Health/Readiness bleiben 200/ready.
- Ergänzend OPS-011: 1.000 Kampfreplay-Seeds sind stabil, erhalten Eingabearmeen und bilanzieren Verluste/Überlebende; fokussierte Terra-Combat-Suite 7/7. Live-Dry-run/API/UI-Abnahme bleibt offen.
- Frische Dumps `backups/fur-20261111T235409Z.dump` (Staging) und `backups/fur-20261112T000712Z.dump` (Main) wiederhergestellt und von Schema 76 auf 77 migriert. Kopien behielten Staging 5 Konten/5 Kolonien und Main 3/3 sowie jeweils 1 Welt/104 Außenposten/4.096 Geländefelder; temporäre PostgreSQL-Container entfernt.
- Main und privates Staging sind auf Schema 77 ausgerollt. Beide App-/Worker-Paare healthy; Health/Readiness HTTP 200, `ready=true`, `quarantined=0`, Worker-Lag 0. Main bleibt auf `127.0.0.1:8081`; Staging auf `https://localhost:8443`.
- K03/WAR-010 bleiben `partial`, bis Balance- und Browser-/Geräte-/Barrierefreiheitsabnahme erfolgt. Öffentlicher Betrieb ist nicht eingerichtet; Railway-Zugang ist nicht authentifiziert.

## Nachtrag: Sitzungsschutz im Browser

- Ursache des wiederkehrenden Fehlers „Ungültiger Sitzungsschutz“: Die Browser-API ergänzte den CSRF-Header nur bei ausdrücklich markierten Anfragen; Spielbefehle und Abmeldung waren nicht markiert. Authentifizierte POSTs tragen den Sitzungsschutz jetzt automatisch, öffentliche Anmeldung und Wiederherstellung bleiben ausgenommen.
- Startseite und ausführende Browser-Skripte erzwingen Cache-Revalidierung, damit ein Client nach einem Reload nicht die alte fehlerhafte Version weiterverwendet.
- Regressionen: 47 Python-Tests bestanden, 19 PostgreSQL-Varianten lokal übersprungen; 6 Frontend-Tests bestanden. Ruff, Black-Check und striktes mypy bestanden.
- Der App-Container wurde neu gebaut. HTTP-Smoke-Test mit dem echten DEV-Rabbit-Login bestätigte Startseite und `app.js` mit `no-cache`, Anmeldung, CSRF-geschützten Spielbefehl und Abmeldung erfolgreich. Der absichtlich ungültige Spielauftrag wurde regulär abgewiesen, nicht vom Sitzungsschutz.

## Nachtrag: Saison-Regelregister

- Ergänzt wurde eine additive Datenbankmigration für Saison-Regelsnapshots. Neue Saisons speichern den kanonischen FUR-2-Katalog samt SHA-256-Prüfsumme atomar mit dem Saisonstart; Datenbanktrigger schützen Snapshots vor Änderung und Löschung. Bestehende Saisons erhalten bei der Migration eine sichtbar als nachträgliche Referenz markierte Zuordnung. Das Register belegt nicht rückwirkend den früheren Regelstand und umfasst keine hartcodierten Simulationsformeln.
- Aktueller lokaler Lauf nach dieser Änderung: **47 bestanden, 19 PostgreSQL-Varianten übersprungen**. Separater vollständiger Multiplayer-Lauf gegen eine neu gestartete, isolierte PostgreSQL-18-Testdatenbank: **37 bestanden, 1 SQLite-spezifischer Test übersprungen**. Die Testdatenbank wurde entfernt.
- Ruff, Black-Check, striktes mypy, ESLint, JavaScript-Syntaxcheck und **5 Frontend-Tests** bestanden.
- App und Worker wurden neu gebaut und gestartet. App, Worker und PostgreSQL sind **healthy**; `/api/v1/health` ist OK, `/api/v1/ready` meldet `ready=true, quarantined=0`, `check-worker` endet erfolgreich. Die aktive PostgreSQL-Datenbank meldet Schema-Version 3 und enthält aktuell keine Saisons.

## Automatisierte Prüfungen

- SQLite-Standardlauf `python -m pytest -q`: **46 bestanden**, **18 PostgreSQL-Varianten übersprungen**, weil `FUR_TEST_POSTGRES` nicht gesetzt war.
- Vollständiger Lauf in einem isolierten Docker-Testcontainer mit eigener temporärer PostgreSQL-Datenbank: **63 bestanden, 1 übersprungen**. Der übersprungene PostgreSQL-Fall ist der SQLite-spezifische Backup-Test; der PostgreSQL-Backup-/Restore-Pfad wurde separat geprüft.
- `ruff check fur_empire tests scripts`, `black --check fur_empire tests scripts`, `mypy fur_empire`: bestanden.
- `npm run lint`, `npm run check`, `npm test`: bestanden; **5 Frontend-Tests** bestanden. Die ESLint-Globals sind dateispezifisch konfiguriert, damit lokale Variablen nicht als doppelte oder schreibgeschützte Browser-Globals fehlinterpretiert werden.
- `pip-audit -r requirements.lock --no-deps --disable-pip`: keine bekannten Schwachstellen. Pip-Audit empfiehlt weiterhin Paket-Hashes.

Die PostgreSQL-Suite und das Python-Testset decken unter anderem Registrierung, Anmeldung, CSRF und Ursprungsprüfung, Idempotenz, Ressourcenbuchungen, PvP-Neulingsschutz, Allianzen, Privatnachrichten, Markt-Escrow, Worker-Fortschritt, Saisonabschluss, Moderationsrechte, MFA-Token sowie parallele Transaktionen ab. Die Tests änderten ausschließlich temporäre SQLite-Dateien und temporäre PostgreSQL-Testschemas/-datenbanken.

## Docker-Laufzeit und Spielablauf

- `docker compose config -q` und der Neuaufbau von App und Worker waren erfolgreich. PostgreSQL, App und Worker stehen auf **healthy**; PostgreSQL verwendet ein benanntes persistentes Volume.
- Die Docker-Portbindung ist nun per `APP_BIND_ADDRESS` konfigurierbar. Compose-Auflösung wurde mit beiden Werten geprüft: Standard `127.0.0.1:8081`, opt-in `0.0.0.0:8081`. Die laufende Instanz bleibt nach `docker inspect` ausschließlich an `127.0.0.1:8081` gebunden.
- Nach dieser Änderung bestehen sowohl `docker compose config -q` als auch `docker compose --env-file .env.example config -q`; die sieben PowerShell-Blöcke der README wurden mit dem PowerShell-Parser geprüft.
- Die App ist absichtlich nur an `127.0.0.1:8081` veröffentlicht. Startseite, `/api/v1/health`, `/api/v1/ready`, Favicon und die neu gebaute Frontend-Datei lieferten HTTP 200. `check-worker` endete mit Exitcode 0.
- Ein lokaler Read-only-Smoke-Test sendete 120 parallele GET-Anfragen auf Startseite, `/api/v1/health` und `/api/v1/ready` mit 12 gleichzeitigen Clients; alle Antworten waren HTTP 200. Das ist kein öffentlicher Last- oder Dauerlastnachweis.
- Ein separater, kurzlebiger Docker-Appcontainer mit eigener temporärer PostgreSQL-Datenbank absolvierte einen HTTP-Spielablauf: Registrierung, CSRF-geschützter Bauauftrag, Fertigstellung durch Worker, Holzgebäude Stufe 1 → 2, keine offenen Aufträge, Welt mit 104 Posten. Testcontainer und Testdatenbank wurden anschließend entfernt.
- Ein zusätzlicher isolierter Lauf prüfte Registrierung, App-Neustart, erneute Anmeldung und unveränderte Kolonie-Stammdaten über PostgreSQL; Readiness war danach `ready=true`, `quarantined=0`. Der Prüfcontainer und die temporäre Datenbank wurden entfernt.
- Die Spieloberfläche wurde im Browser für Kommando, Außenposten, Forschung, Streitkräfte, Weltkarte, Handel, Berichte, Rangliste, Allianz, Nachrichten, Spielermarkt, Weltbetrieb, Kontosicherheit und Spielanleitung geprüft. Eine erneute read-only Navigation durch alle 14 Bereiche der laufenden Docker-App änderte jeweils den Seitentitel; dabei wurden keine JavaScript-Konsolenfehler gemeldet.
- Ein frisches PostgreSQL-Backup wurde über das `ops`-Profil erstellt und in eine separate Testdatenbank zurückgespielt; das wiederhergestellte Schema enthielt 24 Tabellen. Die Restore-Datenbank wurde danach entfernt.
- Für den aktuellen Stand wurden erneut beide aktiven Datenbestände gesichert: der lokale SQLite-Spielstand nach `backups/local-sqlite-preservation/` (SQLite-Integritätsprüfung bestanden) und PostgreSQL nach `backups/fur-20261105T231759Z.dump`. Das frische PostgreSQL-Dump wurde in einer temporären Datenbank wiederhergestellt; 24 Tabellen und die Weltzeile waren vorhanden. Die Prüf-Datenbank wurde entfernt.
- Der lokale SQLite-Spielstand und die Docker-PostgreSQL-Welt sind getrennte Datenbestände; Compose migriert SQLite nicht automatisch nach PostgreSQL. Beide Sicherungen bleiben erhalten und wurden nicht überschrieben.

Der lokale Compose-Modus nutzt `FUR_ENV=local`. Der direkte Readiness-CLI-Aufruf im App-Container meldet `postgresql=true`, `worker_recent=true`, `quarantined=0` und `operator_configured=true`, aber `production=false` und `admin_mfa_ready=false`; er endet erwartungsgemäß mit Exitcode 1. Für DEV Rabbit wurde auf ausdrücklichen Betreiberauftrag ein vorhandenes Konto zur Adminrolle umgestellt, umbenannt und mit einem neu erzeugten Passwort versehen; alle vorherigen Sitzungen wurden widerrufen. Das Konto ist noch nicht verifiziert und hat noch kein TOTP. Die öffentliche Domain und echte SMTP-Zustellung sind nicht konfiguriert. Das ist **keine Produktionsfreigabe**. `/api/v1/ready` prüft nur Worker-Heartbeat und Quarantäne und liefert im lokalen Docker-Modus HTTP 200.

## Offene Freigabepunkte

- Remote-Spieler können den aktuellen Dienst noch nicht erreichen: Port 8081 ist weiterhin nur loopback-gebunden. Eine zeitlich begrenzte private LAN-Bindung samt privater Windows-Firewallregel ist in README beschrieben, aber nicht aktiviert oder von einem zweiten Gerät getestet. Für denselben Rechner ist `http://127.0.0.1:8081` verfügbar.
- Vor einem moderierten Spielertest muss DEV Rabbit das initiale Passwort ändern, die E-Mail bestätigen und TOTP einrichten. Die E-Mail-Bestätigung erfordert im Produktionsbetrieb eine funktionierende SMTP-Zustellung. Das initiale Passwort wird nicht in dieser Prüfdokumentation gespeichert.
- Ein Test aus dem lokalen Netzwerk benötigt eine bewusst festgelegte LAN-Bindung und Firewallregel. Ein Test über das Internet benötigt Domain/DNS, gültiges HTTPS über Caddy, SMTP-Zugang, Betreiberangaben, einen verifizierten Administrationsaccount mit TOTP sowie `FUR_ENV=production`. Diese externe Konfiguration wurde nicht erfunden oder aktiviert.
- Last-, Kapazitäts- und öffentliche Sicherheitstests wurden nicht ausgeführt. Die 100 parallelen Ressourcenübertragungen sind ein Funktionstest, kein öffentlicher Lastnachweis.
- Starlette meldet eine Deprecation-Warnung für `httpx` im Testadapter; der read-only Testcontainer meldet zusätzlich, dass pytest seinen Cache nicht in den gemounteten Quellbaum schreiben kann. Beide Testläufe waren erfolgreich.

Eine absolute Fehlerfreiheit lässt sich nicht beweisen. Der lokale Stack und die geprüften Spielpfade sind funktionsfähig; die Freigabe für Spieler außerhalb dieses PCs hängt davon ab, ob sie im LAN oder über das Internet zugreifen sollen und welche passende Netzkonfiguration bereitgestellt wird.

## E19 OPS-004/OPS-015 vollständiger Schema-12-PostgreSQL-Restore — 2026-11-07

Der aktualisierte Restore-Probe bestand in einem eigens erzeugten, kurzlebigen PostgreSQL-18-Container/Netzwerk. Custom-Format-Dump wurde in eine zweite Datenbank restauriert. Der Probe verglich SHA-256 über alle Tabellenzeilen, separaten Missions-SHA-256, Ressourcen, Allianz, Karte/Intel, 104 Außenposten und 4096 Terrainzellen; ein echter ausstehender Raid blieb erhalten. 136 Intelzeilen; Schema 12. Ausgabe meldete `postgres_backup_restore=passed`. Beide Datenbanken, Container und Netzwerk entfernt. SQLite/PostgreSQL-18-Migrationsfälle: 6 passed. Gesamtsuite: 166 passed / 80 skipped / eine vorhandene Warnung (146.43s). Ruff, Black, strict mypy für App und alle vier Skripte, Traceability 344/344 bestanden. OPS-004 und OPS-015 mit diesem Lauf auf `verified` gesetzt.

## ACC-004 / ACC-006 verification — 2026-11-07

Full Python suite: 221 passed, 118 skipped, one existing Starlette/httpx deprecation warning (575.65s). Focused disposable PostgreSQL 18 account-name and personal-data export tests: 4 passed across SQLite and PostgreSQL. Frontend: 36 passed; Ruff, Black check (21 files), strict mypy (16 files), ESLint, JavaScript syntax and 344-ID traceability passed. The temporary PostgreSQL container was removed. Source migration 018 was not applied to persistent Main or Staging. Browser/mobile/accessibility and full privacy/legal data-inventory review are not covered by this run.

## FUR-3 Live-Mission und Schema-75-Rehearsal — 2026-11-11

Schema 75 fügt die weltbezogene Combat-Regelwahl sowie private, pro Mission gebundene Seed-/Replay-Datensätze hinzu. FUR-3 kann für PvE-Außenpostenraids und PvP-Angriffe aktiviert werden; FUR-2 bleibt Standard. Angekommene Missionen lösen die gepinnte Regel transaktional auf, legen Replay samt Seed-Reveal im Kampfbericht ab und teilen den Bericht mit den betroffenen Parteien. Der Missionsrückruf löscht den noch unverbrauchten Seed. Die neue Admin-Auswahl in der Weltverwaltung ist als Beta markiert. Allianzangriffe (ACS), Gefechtsproben, Wall-only-Verteidiger, vollständige Mehrsprachen-/Barrierefreiheits- und Balanceabnahme sind weiterhin offen.

Die vollständige SQLite-/PostgreSQL-18-Suite lief 6655.17 Sekunden: 588 bestanden, 1 übersprungen, 1 fehlgeschlagen. Der einzige Fehler war der Schema-Rehearsal-Test, der den alten Höchststand 74 erwartete und Schema 75 beim Zurücksetzen nicht entfernte. Der Test wurde auf 75 aktualisiert und beim Rehearsal um den Drop der Schema-75-Artefakte ergänzt. Danach bestanden die fokussierten Rehearsal-/Rückruftests mit SQLite 8/8 und mit dem kurzlebigen PostgreSQL-18-Container 15/15. Beide Testcontainer wurden entfernt; persistente Datenbanken blieben unangetastet.

Ruff auf `fur_empire`, `scripts` und `tests`, Black-Check derselben Pfade, strict mypy (32 Quelldateien), ESLint, JavaScript-Syntaxprüfung, Frontendtests (62/62) und 344-ID-Traceability bestanden. Ein pauschaler Ruff-Lauf über `.` findet weiterhin fünf bestehende Probleme in den unveränderten `FUR_CODEX_UEBERGABE/MASTER_SPEC/scripts/`-Referenzdateien; das Referenzarchiv wurde nicht verändert. Die Windows-`npm`-Stubdatei ist leer, daher wurden ESLint und Node-Tests direkt mit lokal installierten Node-Binärdateien ausgeführt.

Das ist kein vollständiger Suite-Re-Run nach der Testkorrektur. FUR-3 bleibt Teilimplementierung; die Gesamtfreigabe, vollständige 344-ID-Akzeptanz und externe Produktions-/Browser-/Last-/Betriebsprüfung sind offen.

Supply-chain scan (2026-11-11): `pip-audit` initially found four advisories for environment-only `pip 26.1.1`. The isolated workspace virtualenv tool was upgraded to the reported patched `pip 26.2.0`; no application dependency or lockfile changed. A repeat `pip-audit` reported no known vulnerabilities.
`docker compose config --quiet` passed. No app, worker or production database containers were started by this verification. Current 344-row traceability counts: 4 verified, 170 partial, 79 unverified, 91 not audited. These are acceptance statuses, not a percentage-complete estimate; most entries are intentionally not verified until their full positive/negative/idempotency/UI acceptance contract passes.


## K07 / WAR-008 Schema 76: FUR-3-Rückzugsschwelle — 2026-11-11

Pro Welt ist die Rückzugsschwelle jetzt vom Admin zwischen 1 und 100 Prozent konfigurierbar; Standard 60 Prozent. Sie wird zusammen mit FUR-3-Regelstand, Digest und Seed-Commitment beim Missionsstart gepinnt, spätere Änderungen betreffen nur neue Aufträge. Admin-UI, Bereichsvalidierung, aktive Weltanzeige und Migrationserhalt sind abgedeckt.

Vollständige SQLite-Suite: 387 bestanden, 207 übersprungen (PostgreSQL-Adaptervarianten ohne aktiven Adapter), eine vorhandene Starlette/httpx-Deprecation-Warnung; 528.45 Sekunden. Fokussierte SQLite-Prüfungen: 6 bestanden; fokussierte PostgreSQL 18-Migration-/Admin-/Pinning-Prüfungen: 11 bestanden. Frontend: 62 bestanden; ESLint, JavaScript-Syntax, Ruff, Black, strict mypy (32 Dateien) und Traceability 344/344 bestanden. Docker-Compose-Konfiguration validiert; kein App-/Worker-/Produktionscontainer gestartet. FUR-3 bleibt Beta und Gesamtprojektabnahme offen.

The FUR-3 implementation and dependency audit were followed by local validation; the previous full-suite results are recorded above. pip 26.2.0 is the only environment package changed.


## FUR-3-Gefechtsprobe (2026-11-11)

Fokus: SQLite 6 bestanden; temporäre PostgreSQL 18: 10 bestanden (Container anschließend entfernt); Frontend 62/62. Vollständige Python-Suite: 391 bestanden, 209 bedingte PostgreSQL-Überspringungen, eine vorhandene Starlette/httpx-Deprecation-Warnung, 512.40 s. Black-Check, Ruff, strict mypy, ESLint, Node-Syntax, JSON-Matrix-Parse und Traceability 344/344 bestanden. Kein Voll-PostgreSQL-Lauf und keine Live-Browser-/Geräte-/Balance- oder öffentliche Release-Abnahme in diesem Slice; keine 100-%-Freigabe.

## K05 / ACS-Lebenszyklusregressionen (2026-11-11)

SQLite: 3 neue Fälle bestanden, 3 PG-Varianten standardmäßig übersprungen. Disposable PostgreSQL 18: 6 Tests bestanden, Container ohne persistentes Volume danach entfernt. Fälle: nichtleitender Austritt während Anreise, zwischenzeitlich eroberter Zielaußenposten und Beitrittsgrenze an `join_until`. Black/Ruff/strict mypy und 344-ID-Traceability bestehen. Kein vollständiger Projekttestlauf nach ausschließlich test-/nachweisbezogener Ergänzung ausgeführt.

## K05 / ACS-Teilnehmerlimit und Wiederholungsprüfung (2026-11-11)

SQLite: 5 fokussierte Fälle bestanden, PostgreSQL-Varianten standardmäßig übersprungen. Wegwerf-PostgreSQL 18: 10 adapterparametrisierte Ausführungen bestanden. Genau 12 aktive Flügel funktionieren; ein dreizehnter Beitritt ändert weder Escrow noch Wing-Zahl. Doppelte Auflösung gleicher Fälligkeit erzeugt je Teilnehmer genau einen Rückflug, Bericht und Audit. Container danach entfernt. Kein Volltestlauf nach den neuen Tests; statische Python-Regeln und Traceability danach erneut ausgeführt.

## K06 / Garnisonskonkurrenz und Wiederholung (2026-11-11)

SQLite: 3 fokussierte Tests bestanden, 3 PostgreSQL-Varianten im Standardlauf übersprungen. Disposable PostgreSQL 18: alle 6 adapterparametrisierten Fälle bestanden; Container danach entfernt. Geprüft wurden Kapazitätsrennen, paralleler Replay desselben Tokens und wiederholte Ankunftsverarbeitung. Kein Vollsuite-Lauf nach den neuen Regressionen. Crash-Injection/Fehlerrollback, Browser, Geräte und Lokalisierung bleiben offen.

## K06 / Ankunftsfehler und atomarer Retry (2026-11-11)

Neue Fehler-Injektion im Ankunftspfad: Fehler zwischen Statusänderung und Gastgeber-Persistenz rollt alle Datenbankänderungen zurück; erneuter Lauf ergibt eine aktive Garnison mit genau einer Meldung und einem Audit. SQLite: 1 bestanden; PostgreSQL-18-Lauf zusammen mit den übrigen K06-Fokusfällen: 8 bestanden. Temporärer Container entfernt. Weitere Fehlerpunkte bei Kampf-/Rückruftransaktionen und vollständige K06-Akzeptanz bleiben offen.


## Gesamtprüfung nach K05/K06-Fortsetzung (2026-11-11)

Vollständige SQLite-basierte Python-Suite mit allen aktuellen Regressionstests: 400 passed, 218 skipped, eine vorhandene Starlette/httpx-Deprecation-Warnung, 523.10 s. Neue K05-Fokusfälle: SQLite 5 bestanden, PostgreSQL 18 10 adapterparametrisierte Ausführungen bestanden. Neue K06-Fokusfälle: SQLite 4 bestanden, PostgreSQL 18 8 adapterparametrisierte Ausführungen bestanden. Temporäre Datenbankcontainer wurden nach den jeweiligen Läufen entfernt. Keine vollständige PostgreSQL-Gesamtsuite in diesem Schritt.

## K14 Orbit-Stationsoberfläche — 2026-11-11

Neue Frontendregression für Raumstationskontrollen: Kapazitätsanzeige, Ausbau-/Wartungsaktionen, escaped Kolonie-ID, Garnisonsentsendung nur bei aktiver Station, Rückholung und Command-Bindings. `node --test tests/frontend.test.cjs`: 63/63; `node --check static/app.js`: bestanden; ESLint auf `static/app.js`, `static/community.js`, `static/legal.js`: bestanden. Keine Spielstands- oder Datenbankänderung.

## K13 Orbit-Vorlagenoberfläche — 2026-11-11

Neue UI-Regressionsprüfung für Orbit-Flotten-/Werftvorlagen: Typfilter, Escaping untrusted ID/Name, Benennung und Aktionsbindungen. `node --test tests/frontend.test.cjs`: 64/64; `node --check static/app.js` und ESLint (drei produktive JS-Dateien): bestanden. Terra-Vorlagen-API, Scope und Migrationen sind durch bestehende API-/SQLite-/PostgreSQL-Tests belegt. Keine Produktcode- oder Spielstandänderung.

K14-Nachlauf: Ausbauvoraussetzungen stimmen jetzt mit `orbit_station.command` überein. Fehlende oder laufende Schiffbauforschung, zu wenig Erz/Äther und bereits laufender Stationsbau sperren den Button; ein erklärender Text bleibt sichtbar. Der Frontendtest prüft diese Zustände. Gesamtes Frontend weiterhin 64/64; ESLint und `node --check static/app.js` bestanden.

## K14 Orbit-Stationskapazität und vollständige Python-Suite — 2026-11-11

Die Mehrspielerregression setzt eine Stationsgarnison auf exakt 100/100 Plätze und versucht eine weitere Einheit zu entsenden. Der Server lehnt dies ab; sowohl Koloniebestand als auch Garnisonsbestand bleiben unverändert. Danach wird die Testvorrichtung zurückgesetzt und der bestehende Station-/Wartungsablauf fortgesetzt. Vollständige Suite mit `.venv\Scripts\python.exe -m pytest`: 400 bestanden, 218 bedingt übersprungen (PostgreSQL-Adapter ohne `FUR_TEST_POSTGRES`), eine bestehende Starlette/httpx-Deprecationwarnung, 1189.82 Sekunden. Ruff, Black (48 Dateien) und strict mypy (32 Quelldateien) bestanden.

## T01 isolierter Backup-Lauf — 2026-11-11

- Disposable PostgreSQL 18: `deploy/backup.sh` erzeugte ein Dump mit 1705 Bytes; `pg_restore --list` erfolgreich; `backup_status` Zeitstempel 12 Sekunden alt.
- `docker compose config --quiet`: erfolgreich.
- Live-Schema 14: zwei zusätzliche Archive liegen unter `backups/` und bestanden jeweils die Archivlistenprüfung. Statusschreiben scheiterte wegen fehlender Tabelle `backup_status`; persistenten Datenbestand nicht migriert.
- Laufzeit-/Berechtigungsgrenzen bleiben dokumentiert. Das isolierte Testverzeichnis konnte wegen lokaler Befehlsfreigabe nach Entfernen von Container und Netzwerk nicht automatisch gelöscht werden und liegt noch unter `%TEMP%\fur-backup-check-94f3d22c`.

## P02 / P04 Audit — 2026-11-11

- P02: one-time citadel victory confirmed in source and regression; no post-victory boss/campaign/global-goal paths found. Partial.
- P04: one-hour account-age PvP gate, arrival recheck, newbie spawn spacing and vacation protection confirmed. Proposed 72-hour/12-hour values are explicitly unvalidated in FUR-3 rules; defeat recovery and snowball mitigation absent. Partial; no draft balance rules activated.
- Traceability: 344 unique feature IDs and statuses synchronized.

## T01 scheduler follow-up — 2026-11-11

- Added opt-in `backup-scheduler` under the `ops` profile. It runs immediately, then defaults to 24-hour intervals (`BACKUP_INTERVAL_SECONDS`, accepted 3600–2592000 seconds); failure exits and Compose restart policy retries.
- README includes start/log/stop instructions and states no old archives are automatically deleted.
- `docker compose config --quiet` and `docker compose --env-file .env.example config --quiet`: passed. PostgreSQL 18 container `sh -n`: passed. Interval 3599 rejected with exit 2.
- Scheduler deliberately not started on the persistent schema-14 deployment, which lacks `backup_status`; no migration or player-data mutation occurred.

## P03 Saisonwelten — 2026-11-11

- Vier fokussierte Saison-/Mehrweltregressionen: 4 bestanden; 3 PostgreSQL-Varianten mangels `FUR_TEST_POSTGRES` übersprungen; bestehende Starlette/httpx-Warnung.
- Traceability: 344 IDs synchron.
- Bestätigter Ist-Umfang: isolierte seeded Saisonwelt, unveränderlicher FUR-2-Regelsnapshot, Ranglistenarchiv und Beitrittssperre nach Ablauf. Nächste Runde wird auf neuer Welt angelegt; kein Reset der alten Saison oder Dauerwelt.
- UI-/Betriebsdokumentation erläutert diesen Lifecycle. Gesamtintegration mit zwei Welten, globale Systemisolation, PostgreSQL-Rehearsal und vollständige Mobil-/Accessibility-Abnahme bleiben offen.

## K01 Livekampf-Abgleich — 2026-11-11

Der kanonische K01-Eintrag enthielt eine überholte Aussage, der FUR-3-Resolver sei nicht mit Live-Missionen verbunden. Focused current-source run: 17 passed / 10 PostgreSQL-Adaptervarianten übersprungen (kein `FUR_TEST_POSTGRES`). Belegt sind deterministische FUR-3-PvE-Außenposten- und PvP-Missionen mit gepinnter privater Seed-/Regelversion, Teilnehmerreports/Replays und read-only Simulator; FUR-2 bleibt Standard. K01 wurde korrekt `partial` belassen wegen offener ACS/Verteidigungsregel-, Balance- und UI-Abnahme.

## K02 Einheitensystem — 2026-11-11

FUR-3 hat neun versionierte Kampfprofile; sechs zusätzliche Fraktionseinheiten sind tatsächlich welt-/forschungsgebunden rekrutierbar und in den Live-PvE-/PvP-Pfad integriert. Fokussierte SQLite-Katalog-/Produktion-/Live-Kampf-Probe: 14 passed, 7 PostgreSQL-Adaptervarianten übersprungen. Das ist keine Vollroster- oder Balanceabnahme. K02 bleibt partial; Statusmatrix berichtigt und `scripts/check_traceability.py` für 344 IDs bestanden.

## E07/E08-Nachweiskorrektur K04/K07 — 2026-11-11

Aktuelle Quellen zeigten bereits FUR-3-Simulation mit 16 Fällen/Unsicherheitsbereichen und per Welt konfigurierbaren, mission-gepinnten Rückzugsschwellen; alte canonical notes wurden berichtigt. Rückruftest + private Replay/Seed + Schwellen-Pinning: 15 passed, 9 PostgreSQL adapter cases skipped (FUR_TEST_POSTGRES unset). Compose-Konfiguration und 344-ID Traceability weiterhin grün. Teilstatus bleibt wegen offener FUR-2-Rückzugslogik, Balance und vollständiger Browser-/Device-/i18n-/Accessibility-Abnahme.

## P01 Direktivenkette — 2026-11-11

- Backend: die fünf vorhandenen Direktiven sind der Reihe nach serverseitig claimbar; spätere erfüllte Ziele bleiben bis zum Vorgängerclaim gesperrt. Vorhandene Claims bleiben kompatibel. Einmalbelohnungen und Ressourcenreserve-Überlauf bleiben transaktional.
- UI: Status „Offen“, „Bereit zur Abholung“, „Gesperrt“ mit Grund oder „Erfüllt“; gesperrte Aktionen deaktiviert und mit zugänglichem Label.
- Tests: fokussiert 3 passed; vollständiges Python `pytest -q`: 401 passed / 218 PostgreSQL-Fälle übersprungen mangels `FUR_TEST_POSTGRES`, eine vorhandene Deprecation-Warnung (522.74s). Frontend `npm test`: 65 passed.
- Qualität: Ruff, Black-Check, strict mypy, ESLint, JS-Syntax, Compose config und 344-ID Traceability bestanden.
- P01 bleibt partial: wiederholbare Tages-/Wochenquests, Erfolge, volle Locale-/Help- und Browser-/Geräte-/Barrierefreiheitsabnahme offen.

## P01 Weltisolation auf SQLite und PostgreSQL — 2026-11-11

- `test_directive_claims_are_scoped_to_the_active_world`: **2 passed** (SQLite plus disposable PostgreSQL 18).
- Der PostgreSQL-Container nutzte einen temporären Port und wurde nach dem Lauf entfernt. Main/Staging und vorhandene Spielerdaten wurden nicht verändert.
- Aktueller vollständiger lokaler Python-Lauf nach den P01-Regressionen: **403 passed, 219 skipped**, eine vorhandene Starlette/httpx-Deprecation-Warnung. Der vollständige Lauf war SQLite-only; PostgreSQL-Adapterschritte wurden mit der gezielten Weltisolationsregression separat geprüft.
- K03 bleibt partial: Die zugrundeliegende Aufklärung ist getestet, aber eine freigegebene und balancierte Abfangformel fehlt. Nicht validierte Orbit-Entwurfswerte werden nicht als Terra-Regeln aktiviert.

## Main- und Staging-Rollout — 2026-11-11

- Vorherige Schemas: Main 14, Staging 28. Getrennte PostgreSQL-Dumps erstellt, per `pg_restore --list` geprüft und in kurzlebigen PostgreSQL-18-Kopien restored. Die aktuelle Anwendung migrierte beide Kopien bis Schema 76 ohne Änderung der geprüften Bestandszahlen.
- Nach Rollout laufen Main und Staging auf Schema 76. Beide App-/Worker-Paare healthy; `/api/v1/health` und `/api/v1/ready` antworten HTTP 200, `ready=true`, `quarantined=0`, `lag_seconds=0`.
- Main-Bestände: 3 Konten, 3 Kolonien, 1 Welt, 104 Außenposten, 4.096 Terrain-Zeilen. Staging: 5 Konten, 5 Kolonien, 1 Welt, 104 Außenposten, 4.096 Terrain-Zeilen.
- Frische Dumps `backups/fur-20261111T221914Z.dump` (Main) und `backups/fur-20261111T221831Z.dump` (Staging) wurden beide in einem separaten PostgreSQL-18-Container restored; Schema und Bestände stimmten. Container danach entfernt.
- Staging-Backup/Backup-Scheduler erhalten jetzt über `compose.staging.yaml` den Datenbanknamen `fur_staging`. Der manuelle Backupjob aktualisierte `backup_status`; der periodische Scheduler wurde nicht aktiviert, da eine Aufbewahrungs-/Löschrichtlinie fehlt.
- `manage.py check-worker` lädt nun für den Heartbeat-Healthcheck das Spielmodul nicht mehr. Vollständiges `pytest -q`: **403 passed, 219 skipped, 1 vorhandene Deprecation-Warnung** (2.223,14 s). Ruff, Black-Check (48 Dateien), strict mypy (32 Dateien), beide Compose-Konfigurationen und 344-ID Traceability bestanden.
- Bindings bleiben lokal: Main `127.0.0.1:8081`; Staging `127.0.0.1:8443` über Caddy. Kein öffentliches Deployment.


## K01 / K05 Mehr-Runden-ACS-Integration — 2026-11-12

FUR-3-TERRA-ACS-3 verwendet denselben versionierten Mehr-Rundenresolver wie FUR-3-Einzelmissionen und erhält pro Allianzmitglied und Einheitentyp einen getrennten Stack mit der eigenen Taktikstufe. Der Weltkampfregelsatz, Digest, Seed und Rückzugsschwelle werden pro Operation festgehalten. FUR-2-Welten verwenden weiterhin ACS-2/FUR-2-Einrundenkampf. SQLite-ACS/Kampf: 13 bestanden; isolierter PostgreSQL-18-ACS/Kampf: 26 bestanden. Gesamte SQLite-Suite: 419 bestanden, 224 PostgreSQL-adapterabhängig übersprungen, eine bestehende Starlette/httpx-Warnung. COMBAT-2-Außenpostenfortifikation bleibt ein optionaler Entwurf mit unbestätigten Balancewerten. Main und privates Staging wurden nicht migriert oder aktualisiert; beide bleiben Schema 77 und bereit. K01/K05/WAR-001 bleiben partial für Balance- und manuelle Browser-, Geräte-, Lokalisierungs- und Accessibility-Abnahme; Schildwall-Strukturschaden/-reparatur ist noch offen.
## K02 / WAR-001 Terra-Wrack-/Reparaturentwurf — 12. November 2026

- Schema 81 fügt eine eigene, eigentümer-/welt-/koloniegebundene Wracktabelle für SQLite und PostgreSQL hinzu. Regression prüft die Bestandswahrung bei einer Wiederholung der Migration.
- COMBAT-4-only Verluste erzeugen idempotente 25%-Wrackanteile pro Einheitentyp mit 48-Stunden-Frist. Reparatur reserviert Wrack und Rohstoffe atomar, dauert `training_time × Anzahl`, erlaubt eine laufende Reparatur je Kolonie und erstattet bei Abbruch vollständig; Frontend kennzeichnet/zeigt Wracks und Aufträge.
- Vollständige pytest-Suite mit SQLite und einer frischen, volumenlosen PostgreSQL-18-Datenbank nach allen Korrekturen: **655 bestanden, 1 übersprungen**, eine vorhandene Starlette/httpx-Deprecation-Warnung (1640,06 s). Der kurzlebige Testcontainer wurde entfernt.
- Fokussierte SQLite-/PostgreSQL-Nachläufe für Recovery, ACS, Scout-Projektion und Migrations-Rehearsal: **7 bestanden**. Zwei veraltete Assertionen aus einem vorherigen Lauf wurden korrigiert; die vollständige nachfolgende Suite ist nun grün.
- Ruff, Black, strict mypy, ESLint, JavaScript-Syntax, Frontendtests (67/67), pip-audit und Traceability (344/344) bestehen. Keine persistenten Spielstände oder Docker-Stacks migriert. K02 bleibt `partial`; Recoverywerte sind ein unbalancierter Entwurf, COMBAT-3/4-Ausbildung bleibt gesperrt.

