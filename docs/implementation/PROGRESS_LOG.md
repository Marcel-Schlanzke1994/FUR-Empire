
## K02 / WAR-001 COMBAT-4-Rosterpfade — 2026-11-12

Die aktiven Weltkataloge werden jetzt in Aufklärungs-/Gefechtsproben, Außenpostenangriffen, Spielerangriffen, Kolonie- und Allianzversorgung, Expeditionen, Garnisonen, Allianz-ACS-Berichten und Außenposten-zu-Kolonie-Umwandlung verwendet. FUR-3-Kapazität berücksichtigt Profilfracht; der Logistikkonvoi bringt seine definierte Frachtkapazität ein. Kolonie-Rückkehr speichert bereits beliebige Einheiten-IDs und wurde gegen die versionierten Missionspfade geprüft. Die passive COMBAT-3/4-Außenpostenfestung wird als temporäres Resolver-Profil eingebracht, ohne den unveränderlichen Regelkatalog zu verändern. FUR-2 und COMBAT-2/ACS-2 behalten ihre bisherigen Pfade.

Regressionen ergänzt für COMBAT-4-Roster plus Logistikkonvoi in der neutralen Gefechtsprobe und für die Frachtkapazität in der Gefechtsprojektion. Vollständige Python-Suite auf SQLite: 427 bestanden, 225 übersprungen, eine vorhandene Starlette/httpx-Deprecation-Warnung (546,76 s). Ruff und Black für `fur_empire`/`tests` sowie strict mypy bestanden. Ein vorheriger Gesamtlauf deckte vier Integrationsfehler auf; nach Korrektur bestanden alle betreffenden Regressionen und der anschließende vollständige Lauf. Keine persistenten Datenbanken, Migrationen oder Live-Dienste wurden in diesem Schritt verändert.

K02 bleibt `partial`: COMBAT-3/4-Ausbildung bleibt gesperrt. Ein vorläufiger COMBAT-4-Wrack-/Reparatur-Lifecycle ist inzwischen ergänzt; Schema 81 und der Regelsatz sind source-only. Balanceabnahme sowie vollständige UI-/Geräte-/Lokalisierungs-/Barrierefreiheitsabnahme bleiben offen.

Der Recoveryentwurf `FUR-3-TERRA-RECOVERY-1` setzt 25 Prozent Verlustwiederherstellung je Typ (abgerundet), 48 Stunden Wrackfrist, halbe Einheitskosten (je Ressource aufgerundet), `training_time × Anzahl`, eine laufende Reparatur pro Kolonie und volle Erstattung/Wrackrückgabe bei Abbruch um. Auch Null-Wrackverluste werden idempotent gespeichert. Schema 81 und die UI sind nur source-only; kein persistenter Stack wurde migriert.

Abnahme nach Korrekturen: vollständige pytest-Suite mit SQLite und disposable PostgreSQL 18 **655 bestanden, 1 übersprungen**, eine bestehende Starlette/httpx-Warnung (1640,06 s). Der volumenlose PostgreSQL-Container wurde danach entfernt. Ruff, Black (51 Dateien), strict mypy (34), ESLint, JS-Syntax, Frontendtests 67/67, pip-audit und Traceability 344/344 bestehen.

## K03 / WAR-010 Gegenaufklärung — 2026-11-12

Ergänzt `FUR-3-TERRA-INTELLIGENCE-1`: Versand pinnt Regelversion, Prüfsumme, seed-basierte Zufallswerte und die aus Taktik/Wall berechneten Wahrscheinlichkeiten. Abfangchance `min(50%, 2% × Taktik + 3% × Wall)`, Entdeckung `min(60%, 10% + 3% × Taktik + 2% × Wall)`. Entdeckung meldet dem Verteidiger ausschließlich einen generischen Alert. Abfang verliert genau einen Ranger und unterdrückt neue Intel; es gibt keinen Gegenkampf. FUR-2 bleibt unverändert. Migration 77 erstellt die missionsgebundene, transaktionale Ergebnisablage.

Neue Tests decken Regelgrenzen, ungültige Eingaben, Wiederholbarkeit über 1.000 Seeds, FUR-2-Kompatibilität, FUR-3-Entdeckung und FUR-3-Abfang/Rückkehr ab. Fokussierter Scout-Lauf SQLite + PostgreSQL 18: 8 bestanden. Gesamtsuite: 634 bestanden, 1 übersprungen, eine vorhandene Starlette/httpx-Warnung. Frische Main-/Staging-Dumps (`backups/fur-20261112T000712Z.dump`, `backups/fur-20261111T235409Z.dump`) wurden auf separaten PostgreSQL-18-Kopien restored und 76→77 ohne Bestandsverlust migriert. Beide persistenten Stacks laufen jetzt auf 77; Main 3/3/1/104/4096 und Staging 5/5/1/104/4096. Das Missionsfenster erklärt jetzt FUR-3-Entdeckung/Abfang vor dem Abflug; FUR-2 behält den alten Text. Frontend 65/65, ESLint und JS-Syntax bestehen. App/Worker sind auf Main und privatem Staging gesund; Readiness jeweils `ready=true`, Quarantäne 0, Lag 0. K03/WAR-010 bleiben `partial`, bis Balance sowie Browser-/Geräte-/Barrierefreiheitsakzeptanz abgenommen sind.

### K03 Eigentümerentscheidung und erneute Regression — 2026-11-12

Der Eigentümer delegierte die fehlenden Startwerte ausdrücklich zur eigenen Festlegung. Der bestehende Vertrag `FUR-3-TERRA-INTELLIGENCE-1` wird bestätigt: Abfang `min(50%, 2% × Verteidiger-Taktik + 3% × Schildwall)`; Entdeckung `min(60%, 10% + 3% × Taktik + 2% × Schildwall)`. Erkennung sendet einen generischen Alert; Abfang kostet genau einen Ranger, unterdrückt neues Intel und lässt Überlebende zurückkehren; kein Gegenkampf. FUR-2 bleibt unverändert. Fokussierter Lauf: 10 bestanden, 3 PostgreSQL-Adaptervarianten mangels `FUR_TEST_POSTGRES` übersprungen. Das bestätigt den implementierten Startvertrag, ersetzt keine Balanceabnahme.

### WAR-005 Kampf-Dry-run — erneuter API-/Datenmutationsabgleich — 2026-11-12

Die bestehenden Domain-, PvP-Intel-, COMBAT-4-Struktur-/Minen- und API-CSRF-Regressionsfälle wurden gezielt erneut ausgeführt: 9 bestanden, 6 PostgreSQL-Adaptervarianten mangels `FUR_TEST_POSTGRES` übersprungen; eine vorhandene Starlette/httpx-Deprecation-Warnung. FUR-2-Vorschau bleibt deterministisch, FUR-3 nutzt 16 reproduzierbare Resolver-Szenarien. PvP verwendet ausschließlich frisches beobachterspezifisches Stufe-2-Intel; Simulation schreibt weder Kolonie-/Außenpostenzustand noch Audit-/Ledgerbuchungen und gibt weder Seeds noch unbekannte Ressourcen/Beute preis. COMBAT-4-Verteidigung stammt aus dem gepinnten Intel-Snapshot. Kein Regelwert wurde dabei geändert. WAR-005 bleibt `partial` bis PostgreSQL-, Browser-/Geräte-/Lokalisierungs-/Accessibility- und Balanceabnahme.

OPS-011 erhielt ergänzend einen 1.000-Seed-Kampfreplay-Test: gleiche Seeds erzeugen dasselbe Sechs-Runden-Ergebnis, Eingabearmeen bleiben unverändert und Verlust-/Überlebendenzahlen stimmen. `tests/test_terra_combat.py`: 7 bestanden. Das deckt Resolver-Wiederholbarkeit ab; API-/Dry-run-/Betriebsabnahme bleibt offen.

## T01 Backup-Nachweis — 2026-11-11

Quellcode-Audit und isolierte PostgreSQL-18-Probe: Der einmalige Docker-Backupjob validiert das Archiv vor Veröffentlichung und schreibt nach erfolgreichem Dump den Betriebszeitstempel; CI prüft diesen Zeitstempel und enthält einen Restore-Drill. Das isolierte Dump war 1705 Bytes groß, `pg_restore --list` war erfolgreich, der Zeitstempel 12 Sekunden alt. Das laufende Schema-14-System hat die Tabelle `backup_status` noch nicht; zwei Live-Dumps wurden dennoch erfolgreich erstellt und gelistet. Keine Datenbankmigration. T01 ist teilweise umgesetzt. Periodischer Zeitplan, Rotation/Aufbewahrung und vollständige Recovery-Freigabe sind offen.

## P02 / P04 source audit — 2026-11-11

P02: The one-time citadel capture/victory quest exists (`game.py`, `test_citadel_victory`). The audited current paths do not provide later boss tiers, rotating campaigns, or global goals; P02 is partial.

P04: PvP checks both account creation ages against a one-hour floor and rechecks attack eligibility at arrival. Six-sector spawn spacing and vacation mode have regression coverage. The proposed FUR-3 rule JSON contains 72-hour newbie and 12-hour defeat-recovery values but explicitly labels the defaults unvalidated; defeat recovery and snowball mitigation have no current implementation evidence. These draft values were not activated. P04 remains partial pending a versioned, balance-tested contract.

Only feature evidence and traceability documents changed for these two audits. `scripts/check_traceability.py`: 344 IDs, statuses synchronized.

T01 scheduler implementation — 2026-11-11

A separate opt-in `backup-scheduler` service now runs the verified one-shot backup immediately and then on a validated configurable interval (default 24 hours; 1–30 days). Compose restarts the scheduler after a backup failure. README documents operations. Compose config (default and example env), PostgreSQL-container shell parse, interval-bound rejection, and traceability passed. The service was not enabled against the live schema-14 database because `backup_status` is missing there. No automatic retention deletion was configured without an approved policy.

## P03 saisonale Welten — Source-Audit und Regression — 2026-11-11

Die Implementierung erzeugt pro Saisonwelt einen getrennten Seed-/Weltzustand. Spieler treten der Saisonwelt separat bei; Saisonstart schreibt FUR-2-Katalogsnapshot und Prüfsumme unveränderlich. Der Worker archiviert die Rangliste und sperrt eine abgelaufene Saisonwelt für neue Beitritte. Die alte Runde wird nicht gelöscht oder zurückgesetzt; für den nächsten Wettbewerb wird eine neue Saisonwelt angelegt, die Dauerwelt bleibt separat. Das ist ein manueller Weltwechsel, kein In-place-Reset oder geführter Saison-Rollover. Übergreifende Weltisolation und persistente Mehrwelt-Rehearsals bleiben offen, daher P03 `partial`.

Fokussierte Regressionen (`test_world_events_and_season_archive_are_isolated`, `test_sandbox_blocks_pvp_and_seasons_without_changing_genesis`, `test_events_integrate_actual_interval_and_season_archives`, `test_season_closes_before_later_build`): 4 bestanden, 3 PostgreSQL-Varianten übersprungen, da `FUR_TEST_POSTGRES` für diesen Lauf nicht gesetzt war. Traceability: 344 IDs synchron.

## K01 Live-Integration-Nachweis — 2026-11-11

Quellabgleich fand veraltete K01-Evidenz in `spec/FEATURES.json`: dort stand noch „nicht in Live-PvE/PvP integriert“, während Code, Testfälle und TRACEABILITY bereits die Integration dokumentieren. Der kanonische Eintrag und die Matrix sind berichtigt; K01 bleibt `partial`. Fokussierter Lauf mit Pure Resolver, live PvE-/PvP-Auflösung, read-only Simulation, Spionage-Snapshot und Recall: 17 passed, 10 PostgreSQL-Adaptervarianten übersprungen, weil `FUR_TEST_POSTGRES` nicht gesetzt war. Keine Spielcode- oder Datenbankänderung.

Gesamtinventar nach Auditabgleich: 4 verified, 181 partial, 72 unverified, 87 not audited. Traceability: 344 IDs synchron. Nächste offene Schritte: K02-/WAR-003-Kontrakt und E07-Abdeckung, danach die übrigen Abhängigkeiten; vollständige globale Tests und Release-Gates sind offen.

## K02 Einheitensystem — aktueller Code-/Testabgleich — 2026-11-11

Die neun Combat-Profile (drei Basis- und sechs Fraktionseinheiten) liegen im gehashten FUR-3-Terra-Kampfkatalog und speisen nach Weltregelwahl den Live-PvE-/PvP-Resolver. Alle sechs Fraktionseinheiten sind über weltgebundene Fraktions-/Forschungsregeln rekrutierbar. FUR-2-Einheiten und Kampf bleiben unverändert. Fokussierte Tests für Katalog, Modifier, Rekrutierung, PvE/PvP und Replay: 14 passed, 7 PostgreSQL-Adapterfälle übersprungen (kein `FUR_TEST_POSTGRES`). Die alte kanonische Notiz „nicht live integriert“ ist ersetzt. K02 bleibt `partial`: vollständiger allgemeiner Einheitenkatalog, Reise-/Kosten-/Reparaturwerte, Balanceabnahme und Browser-/Geräte-/i18n-/Accessibility-Abnahme fehlen.

## K04 / K07 Bestandsabgleich — 2026-11-11

K04: Ein veralteter kanonischer Hinweis, der Simulator sei ausschließlich FUR-2/ohne Verlustspannen, wurde an den aktuellen Stand angepasst. Aktuelle Regeln: FUR-2 deterministisch; FUR-3 optional, 16 reproduzierbare Projektionen mit Siegchance und Verlust-/Überlebendenbereichen, ohne Datenmutation oder Seed-Leak. FUR-3-Balance und Browser-/Geräte-/i18n-/Accessibility-Abnahme bleiben offen.

K07: Der kanonische Hinweis auf fehlende konfigurierbare Schwellen war überholt. Pro-Welt-Schwelle (1–100 %, Standard 60 %) wird in Schema 76 gespeichert und an jede FUR-3-Mission gepinnt; idempotenter Rückruf im Flug bucht Rückkehr einmal. FUR-2-Rückzug, Abbruch nach Ankunft/Kampfbeginn und breite UX-Abnahme bleiben offen. Fokuslauf: 15 passed, 9 PostgreSQL-Varianten ohne `FUR_TEST_POSTGRES` übersprungen. Traceability: 344 IDs synchron.

## P01 Fortschritts-Direktiven — 2026-11-11

Die fünf bestehenden Direktiven sind jetzt eine serverautoritativ erzwungene Claim-Kette: Wirtschaft → Kaserne → Forschung → Expansion → Zitadelle. Ziele können vorher erfüllt werden, Belohnungen bleiben aber bis zur Reihenfolge gesperrt. Bereits gespeicherte ältere Claims werden nicht entfernt; Belohnungen sind weiterhin einmalig, Depotüberlauf landet im Reservelager. Die UI nennt Status und Sperrgrund. Dokumentiert in `docs/Spielanleitung.md` und `docs/game-design/FUR_EMPIRE_SPEC.md`.

Regressionen: Fokus 3/3 bestanden (inklusive vorzeitiger unberechtigter Claim, Fortschritt, Alt-Claims, einmalige Belohnung und Überlauf); vollständige SQLite-Suite **401 passed, 218 skipped**, eine bestehende Starlette/httpx-Deprecation-Warnung, 522.74 s. Übersprungene Fälle sind die konfigurationsabhängigen PostgreSQL-Adapter. Frontend **65/65**, ESLint, JavaScript-Syntax, Ruff, Black-Check (48 Dateien), strict mypy (32 Quelldateien), Compose-Konfiguration und `scripts/check_traceability.py` (344 IDs) bestanden. Status P01: `partial`; tägliche/wöchentliche Quests, Achievement-Katalog, vollständige Übersetzungen und Browser-/Device-/Accessibility-Abnahme bleiben offen.

### P01 Nachtrag: Weltisolation auf PostgreSQL — 2026-11-11

Die Regression `test_directive_claims_are_scoped_to_the_active_world` wurde erneut gegen beide Adapter ausgeführt: SQLite und eine kurzlebige PostgreSQL-18-Datenbank, **2 passed**. Der Testcontainer wurde entfernt; die laufenden Main-/Staging-Datenbanken und Spielerdaten blieben unberührt. Aktuellster vollständiger lokaler Lauf nach den P01-Regressionen: **403 passed, 219 skipped**, eine vorhandene Starlette/httpx-Deprecation-Warnung; die übersprungenen Fälle benötigen einen separat konfigurierten PostgreSQL-Testadapter. P01 bleibt `partial`.

### K03 nächster Abhängigkeitsschritt

Der Eigentümer hat die Festlegung der fehlenden K03-Werte an den Agenten delegiert. `FUR-3-TERRA-INTELLIGENCE-1` setzt für FUR-3 einen Startvertrag um: Abfangchance `min(50%, 2% × Verteidigertaktik + 3% × Schildwall)`; Entdeckung `min(60%, 10% + 3% × Taktik + 2% × Schildwall)`. Die Formel und der Seed werden beim Versand gepinnt. Bei Abfang geht ein Ranger verloren, neue Intel wird unterdrückt und die übrigen Ranger kehren zurück; der Verteidiger wird ohne Offenlegung des Angreifers informiert. Ein gewöhnlicher Entdeckungsalarm ist ebenfalls generisch und löst keinen Gegenkampf aus. FUR-2 bleibt unverändert. K03 bleibt `partial`, bis die Startwerte ausbalanciert und Browser-/Geräte-/Barrierefreiheit abgenommen sind.

## Docker-Migration und lokaler Rollout — 2026-11-11

Vor Rollout wurden getrennte Main- und Staging-Dumps erstellt und per `pg_restore --list` validiert. Main wurde auf einer isolierten Kopie von Schema 14, Staging von Schema 28 jeweils bis Schema 76 migriert; die geprüften Konto-, Kolonie-, Welt-, Außenposten-, Terrain- und Saisonzeilen blieben erhalten. Danach liefen beide lokalen Stacks mit aktuellem Quellstand auf Schema 76. Main: 3 Konten/3 Kolonien/1 Welt/104 Außenposten/4.096 Geländefelder; Staging: 5/5/1/104/4.096. Beide App-/Worker-Paare sind healthy; Health und Readiness liefern HTTP 200, keine quarantänisierten Aufträge, Scheduler-Lag 0.

Der Kaltstart machte den Worker-Healthcheck zu langsam: `manage.py check-worker` importierte unnötig das komplette Game. CLI-Imports sind jetzt verzögert; Ruff, Black-Check, strict mypy und vollständiges `pytest -q` bestanden (**403 passed, 219 skipped**, eine vorhandene Starlette/httpx-Deprecation-Warnung; 2.223,14 s). Nach Neubau sind Worker auf Main und Staging healthy.

Aktuelle Dumps: `backups/fur-20261111T221914Z.dump` und `backups/fur-20261111T221831Z.dump`. Beide wurden in einer separaten PostgreSQL-18-Instanz wiederhergestellt und verifiziert: Schema 76 sowie unveränderte Bestände 3/3/1/104/4.096 und 5/5/1/104/4.096. Die temporäre Instanz wurde entfernt. Der Staging-Backupjob überschreibt nun `PGDATABASE=fur_staging`; manueller Job und Statuszeitstempel wurden validiert. Periodischer Scheduler bleibt opt-in, weil es keine abgestimmte Aufbewahrungs-/Löschregel gibt.

Main bleibt ausschließlich auf `127.0.0.1:8081`, Staging auf `https://localhost:8443`; es wurde kein öffentlicher Internetzugang eingerichtet. Die 344-ID-Gesamtabnahme ist weiterhin offen.
## K01 neutraler FUR-3-Außenposten COMBAT-2 — 2026-11-12

Der Bestandsaudit fand einen K01-Fehler: FUR-3 übersprang bei neutralen Außenposten deren Tierstufenverteidigung sowohl in echten Kämpfen als auch in Gefechtsproben. COMBAT-2 ergänzt deshalb einen separaten, optionalen Regelkatalog mit passiven Strukturpunkten in Höhe von 55 × Tier², ohne Gegenangriff. Die Struktur wird pro Kampf aus der kanonischen Tierstufe abgeleitet und nicht als Spieler-Garnison gespeichert. COMBAT-1/FUR-2 bleiben unverändert; neue Welten bleiben FUR-2. COMBAT-2 ist im Adminbereich als Entwurf gekennzeichnet und bis zur Balanceabnahme nicht produktionsfreigegeben.

Migration 078 erweitert die Combat-Regelauswahl; SQLite erhält eine Datenerhaltungs-Rebuild-Migration inklusive Weltmodus und Prestige-Feld, PostgreSQL eine Constraint-Erweiterung. Tests: `tests/test_terra_combat.py` 8 bestanden; COMBAT-2 echte Außenpostenmission mit pinned Digest, Tier-8-Struktur und nicht persistierter Befestigung bestanden; `tests/test_game.py` 69 bestanden. K01 bleibt `partial`: ACS-Teilnehmerattribution/persistente Befestigung, Balance, Browser-/Geräte- und Accessibility-Abnahme sind noch offen. Die laufenden Main-/Staging-Instanzen wurden in diesem Arbeitsschritt nicht migriert.

K01 COMBAT-2 PostgreSQL-Freigabeprüfung — 2026-11-12: Temporärer PostgreSQL-18-Container `fur-k01-pg` lief isoliert auf Port 55432 und wurde nach dem Lauf entfernt. `tests/test_game.py`, `tests/test_multiplayer.py`, `tests/test_terrain.py` und `tests/test_world_snapshot.py` mit SQLite und PostgreSQL: 524 bestanden, 1 übersprungen, eine bestehende Starlette/httpx-Warnung (2566.64 s). Damit sind Schema-78-Migration, Kampf-/Missionspfade und Restore-Rehearsals auf beiden Adaptern abgedeckt. Main und Staging blieben auf Schema 77; beide Readiness-Endpunkte lieferten weiterhin `ready=true`. Vollständiger SQLite-Lauf: 416 bestanden, 222 PostgreSQL-adapterabhängige Fälle übersprungen. Paketweite Ruff, Black, strict mypy, ESLint, JavaScript-Syntax, Frontend 65/65 und Traceability 344/344 bestehen. COMBAT-2 wurde nicht in Main/Staging aktiviert.


## K05 FUR-3-TERRA-ACS-3 — 2026-11-12

FUR-2-Welten behalten den eingefrorenen ACS-2-Vertrag. FUR-3-Welten pinnen beim Start Combat-Regelsatz, Digest, Seed und Rückzugsschwelle in `terra_combat_missions`, referenziert über die Allianzangriffs-ID. Jeder Teilnehmer und Einheitentyp bleibt ein separater deterministischer Mehr-Runden-Stack; Taktik wirkt pro Teilnehmer. Verluste und Überlebende werden an die Ursprungsarmeen zurückgeführt. COMBAT-2-Neutralfortifikation bleibt virtuell und optional. Abbruch löscht unverbrauchte Seeds; Abschluss speichert Replay und veröffentlicht Seed/Commitment im Teilnehmerbericht. Nachweise: 13 SQLite-ACS/Kampfregressionen; 26 PostgreSQL-18-ACS/Kampfregressionen; vollständige SQLite-Suite 419 bestanden/224 adapterabhängig übersprungen. K05 bleibt `partial` bis Browser-, Geräte-, Tastatur/Screenreader-, Lokalisierungs- und Balanceabnahme. Main/Staging bleiben unverändert auf Schema 77.

## K02 Einheitensystem — COMBAT-3-Roster — 2026-11-12

`FUR-3-TERRA-COMBAT-3` versioniert 21 Kampfprofile: die neun vorhandenen plus die zwölf Rollen aus der Master-Roadmap (Feldspäher, Saboteur, Sanitäter, Schilddrohne, Scharfschütze, Belagerungsroboter, Artillerieplattform, Logistikkonvoi, Ingenieurtrupp, Interceptor-Drohne, Kommandantenwache, Titan-Koloss). Für jedes Profil enthält der Snapshot Rolle, Kampfwerte/Konter, Kosten, Zeit, Gebäude-/Forschungsvoraussetzungen, Geschwindigkeit, Fracht, Treibstoff, Reichweite und Reparaturquote. Regelvalidierung prüft Vollständigkeit, Grenzen und Voraussetzungen. Produktions-/Bewegungszahlen sind eigene Vorschlagswerte, `provisional_balance`; Training ist gesperrt. Grund: Die zwölf IDs haben noch keinen persistenten Besitz-/Reservebestand und sind nicht in allen Transport-, Garnison-, Reparatur-, Wertungs- und Rückkehrpfaden abgebildet. Keine Migration, Aktivierung oder Änderung persistenter Main-/Staging-Daten. `tests/test_terra_combat.py`: 10 bestanden. K02 bleibt `partial`; als nächstes vollständigen persistenten Einheiten-Lifecycle einschließlich Bewegung/Treibstoff, Reparatur und idempotenter Rückkehr modellieren, dann UI und Balancetest.

K02/WAR-001/002/004 Audit-Fortsetzung: Die erste Multiplayer-Gesamtrunde deckte einen COMBAT-2-Datei-/Katalogdigestfehler auf. Die COMBAT-2-Quelldatei wurde aus dem read-only geöffneten lokalen Main-Regelkatalog exakt wiederhergestellt; danach stimmen die COMBAT-1/2-Digests zwischen Datei und Datenbank wieder überein. Die finale Multiplayerregression lief gegen eine automatisch entfernte temporäre `FUR_DB`: 221 bestanden, 213 PostgreSQL-Varianten übersprungen, eine vorhandene Starlette/httpx-Warnung. Ein zusätzlicher Game-Test bestätigt die COMBAT-3-Registrierung als unveränderlichen Entwurf und dass keine Welt COMBAT-3 ausgewählt hat; zusammen mit Katalog- und FUR-2-Kompatibilitätstest: 3 bestanden. Ruff, Black, strict mypy, Traceability 344/344 bestehen. Persistente lokale SQLite geprüft: Schema 78, ein Konto/eine Welt, keine COMBAT-3-Katalogzeile; keine Daten geändert. Docker Main/Staging blieben unangetastet.


## K02 / WAR-001 Fortsetzung: isolierter COMBAT-4-Lebenszyklusentwurf — 2026-11-12

COMBAT-3 bleibt byte-/digeststabil und weiterhin nicht trainierbar. Als neue Version wurde `FUR-3-TERRA-COMBAT-4` mit denselben 21 Profilen, ausdrücklich vorläufigem Balance-Status und Schema-80-Migration für SQLite/PostgreSQL ergänzt. Der Admin kann COMBAT-4 nur vor dem ersten Weltbeitritt wählen; bestehende Welten sind gegen Wechsel in oder aus dieser Version geschützt. Das Frontend markiert die Auswahl als Entwurf. Training ist serverseitig und sichtbar weiterhin gesperrt, weil Dispatch, Transport, Garnison, Reparatur, Wertung, Rückkehr und alle Kampfpfade noch nicht gemeinsam auf den zusätzlichen Roster migriert sind.

Nachweise in diesem Lauf: combat/game Regressionen 84 bestanden; vollständige SQLite-Suite 425 bestanden, 224 PostgreSQL-Adapterfälle übersprungen, eine vorhandene Warnung; fokussierte PostgreSQL-18-Migrationsabdeckung 8 bestanden. Frontend 66/66; ESLint, JavaScript-Syntax, Ruff, Black-Check (50 Dateien), strict mypy (33 Dateien), pip-audit und Traceability (344 eindeutige IDs) bestanden. Main- und Staging-Compose-Konfiguration bestanden. Keine dauerhaften SQLite-/Docker-/Staging-Datenbank wurde geändert oder migriert. Schema 80 bleibt source-only; die PostgreSQL-Probe lief in einem kurzlebigen Container ohne Volume, der danach entfernt wurde. K02/WAR-001 bleibt `partial`; als nächstes den vollständigen Einheitenbesitz- und Einsatz-Lifecycle implementieren, bevor Training aktiviert wird.
## K02 / WAR-018 vorläufige Militärwertung — 2026-11-12

FUR-2-Punktelogik bleibt unverändert. Versionierter FUR-3-COMBAT-Wertungsvorschlag implementiert: je tatsächlicher verlorener Einheit ein Angriffs- oder Verteidigungspunkt; ACS-Angreifer werden je Wing verbucht; Verluste verbündeter Verteidiger-Garnisonen gehen an den Entsender. Bestätigte Garnisonsankunft gibt dem Entsender einen Unterstützungspunkt je stationierter Einheit, höchstens einmal je rollierendem 24-Stunden-Fenster pro Spieler/Welt, und nur wenn die Welt einen unterstützten FUR-3-Combatregelsatz nutzt. Allianzsumme aggregiert aktuelle Mitglieder weltgebunden. Tabelle `war_score_ledger` hat SQLite-/PostgreSQL-Migration 082, Unique-Key je Mission/Spieler/Kategorie sowie Datenbank-Trigger gegen UPDATE/DELETE. Werte sind transaktional am Auflösungsereignis gebucht; eine private Auditansicht begrenzt Einträge auf 50. Ranking-UI und paginierte API liefern persönliche und Allianz-Militärwertung.

Vertrag ist ausdrücklich nur Entwurf, keine Balance-/Eigentümerabnahme und ändert die traditionelle FUR-2-Rangliste nicht. Vollständige SQLite-Suite nach Schema-82-Snapshotkorrektur: 432 bestanden, 226 PostgreSQL-Adapterfälle übersprungen und eine bestehende Starlette/httpx-Warnung. Danach wurde die Wertung noch mit 24-Stunden-Supportlimit und Unveränderlichkeitstrigger gehärtet; gezielte Tests bestanden: Wertung/Rangliste 4, Garnisonsankunft 2; Ruff, Black (51 Dateien), strict mypy, ESLint, JS-Syntax, Frontend 68/68 und Traceability 344/344 bestehen. PostgreSQL-Migration 082, Balance-/Eigentümerentscheidung und manuelle Browser-/Geräte-/Barrierefreiheits-/Lokalisierungsabnahme bleiben offen.


## WAR-014 source-truth audit and FUR-3 casualty attribution — 2026-11-12

Current source contradicted the old inventory note: versioned allied home garrisons are already present in schema 74 with explicit host consent/capacity, contributor escrow, world/member rechecks, recall, colony deletion guards, and separate-owner combat loss allocation. FUR-2 uses deterministic proportional losses; FUR-3 COMBAT-3/4 applies resolver losses across host units and each named garrison owner. Updated WAR-014 to `partial` across the reconstructed inventory, feature index, traceability, and implementation matrix; retained manual/balance/PostgreSQL gates.

Added `test_fur3_garrison_casualties_are_allocated_to_each_owner_exactly`, which stations a COMBAT-4 garrison and verifies a four-unit loss splits two/two between host and contributor, mutates the garrison balance to its exact remainder and notifies the contributor. SQLite passed; PostgreSQL adapter variant skipped because no test URL was configured. This is a focused regression, not a full-suite rerun.


## WAR-003 / K14 Fortschritt — COMBAT-4-Verteidigung

Die zuvor dokumentierte Lücke in der Gefechtsintegration ist geschlossen: Kinetikgeschütz, Aegis-Emitter und Gefechtsbunker werden mit eigener Integrität als synthetische Einheiten in normale und ACS-COMBAT-4-Runden aufgenommen. Ein auf den Missionsseed gestütztes Minenfeld kann einmalig verbraucht werden und senkt den Angreifer-Schadensmodifikator gemäß dem ausdrücklich vorläufigen FUR-3-Vertrag. Verbleibende Strukturintegrität, verbrauchte Minen, Digest und Replay werden in derselben Transaktion wie der Verteidigerkolonie-Zustand gespeichert. Bau-/Reparaturaktionen sind bereits in der Gebäudeoberfläche angebunden.

Gezielte Verifikation: `tests/test_terra_defense.py` und die zugehörigen Multiplayer-Regressionen: 19 bestanden, 4 PostgreSQL-Adapterfälle mangels `FUR_TEST_POSTGRES` übersprungen. Ein zusätzlicher echter ACS-COMBAT-4-Spielerangriff speichert Verteidigungszustand in Kolonie, Replay und Teilnehmerbericht: SQLite 1 bestanden, PostgreSQL-Adapter 1 mangels `FUR_TEST_POSTGRES` übersprungen. Frontend 69/69; ESLint und JS-Syntax bestehen. Der Lauf deckt Regeln, Slots, deterministische Strukturauflösung, Minenauslösung, ACS-Wings, idempotenten Bau/Reparatur, Reparatursperre bei eingehendem Angriff sowie normalen PvP- und ACS-Spielerangriff mit persistiertem Replay/Strukturschaden und Berichtsweitergabe ab. Das ist noch keine Gesamt- oder Browserabnahme. Werte bleiben bis zur Balanceabnahme vorläufig; FUR-2 blieb unverändert; keine persistente Docker-Datenbank wurde verändert.

Vollständiger SQLite-Lauf nach K14/ACS-Berichtsfeld: 452 bestanden, 231 übersprungen (PostgreSQL nicht verfügbar), eine bestehende Starlette/httpx-Warnung in 548.04 s. Frontend 69/69, Ruff/Black/strict mypy, ESLint/JS-Syntax und Traceability 344/344 bestanden. Main-/Staging-Compose-Konfiguration ist gültig; Docker Desktop meldet `Docker Desktop is unable to start`. Keine persistente DB verändert.

## WAR-004 Audit — reproduzierbare Gefechtswürfe

Der vorhandene Pfad erfüllt die Domain- und Replay-Verträge: Der Dispatch speichert ein zufälliges 256-Bit-Seed geheim und bindet es an Seed-Commitment, Welt, Combat-Regelversion/-Digest und Rückzugsschwelle. Bei der Ankunft prüft der Worker Commitment und Digest, löst dieselbe deterministische FUR-3-Funktion auf und speichert Replay plus Seed-Reveal genau einmal innerhalb der Kampftransaktion. Unaufgelöste, abgebrochene Missionen löschen das geheime Seedmaterial. ACS hält den Seed bis zum Replay privat und ordnet Überlebende je Flügel zu. FUR-2 bleibt getrennt.

Nachweise: 1.000-Seed-Domänenregression, identische Wiederauflösung, Einheitenbilanz, Modifikator-Pinning, privates Seed bis zum Replay, PvP- und ACS-Report sowie Retry/Abbruch sind in der 452-bestandenen SQLite-Vollsuite enthalten. 231 PostgreSQL-Adapterfälle übersprungen, da Docker Desktop nicht startet und `FUR_TEST_POSTGRES` fehlt; eine vorhandene Starlette/httpx-Warnung. WAR-004 bleibt `partial` bis PostgreSQL-, Browser-/Geräte-/Accessibility- und breitere Releaseabnahme. Nächster E07-Abgleich: WAR-005 Kampfsimulator.


## K14 / WAR-005 Nachlauf — COMBAT-4-Verteidigung im Gefechtssimulator

Stufe-2-Aufklärung in COMBAT-4-Welten pinnt jetzt zusätzlich die Verteidigungsstacks und `FUR-3-TERRA-DEFENSE-1`-Digest im privaten, beobachterspezifischen Intel-Snapshot. Die FUR-3-Projektion führt dieselben Verteidigungsprofile und seed-basierten Minenregeln über alle 16 Szenarien aus. Ihr Ergebnis enthält die aggregierte Minen-Auslösequote und Integritätsspannen. FUR-2- und ältere COMBAT-Regeln bleiben unverändert. Die UI zeigt die geschätzte Minen-Auslösequote.

Gezielte Verifikation von COMBAT-4-Simulation, frischem Intel, PvP-Preview-Read-only und alten Simulatorfällen: 6 SQLite-Fälle bestanden, 5 PostgreSQL-Adapterfälle mangels `FUR_TEST_POSTGRES` übersprungen. Frontend 69/69. Ruff, Black und strict mypy (35 Quelldateien) bestehen. Die anschließende vollständige Python-Suite nach allen Änderungen besteht: 465 passed, 243 skipped (PostgreSQL-Adapter ohne laufenden Docker-Endpunkt), eine bestehende Starlette/httpx-Deprecation-Warnung, 734,92 s. COMBAT-4-Simulator bleibt `partial` bis PostgreSQL-Adapter-, Browser-/Geräte-/Accessibility-, Lokalisierungs- und Balanceabnahme.


## WAR-001/002 Lifecycle-Audit — 2026-11-12

Der COMBAT-3/4-Katalog enthält insgesamt 21 Profile: neun bereits bekannte FUR-3-Rollen und zwölf zusätzliche Rollen. Quellenprüfung: Die zusätzlichen Rollen fließen über den aktiven Weltkatalog in Bewegungs-/Reichweiten-/Treibstoffberechnung, Transportkapazität, serverseitige Missionsvalidierung, Rückkehr, Garnison und Resolver ein; die Freigabe zur Ausbildung ist im COMBAT-4-Katalog absichtlich `false`, solange Werte und gesamter Lebenszyklus nicht abgenommen sind. Diese Sperre bleibt bestehen, damit keine unbalancierten Profile in Spielerbestände gelangen.

Neue Regression `test_combat4_unapproved_roster_training_stays_locked_without_side_effects` wird über alle zwölf zusätzlichen Profile parametrisiert. Jeder Trainingsversuch wird serverseitig abgelehnt und bestätigt unveränderte Ressourcen, Einheiten und Auftragswarteschlange. Ergebnis: 12 SQLite-Fälle bestanden, 12 PostgreSQL-Adapterfälle mangels Docker übersprungen. Ruff, Black-Check (Testdatei) und strict mypy bestanden. Vollständige Suite nach Testergänzung: **465 bestanden, 243 übersprungen**, eine vorhandene Starlette/httpx-Deprecation-Warnung, 734,92 s. WAR-001/002 bleiben partiell bis Balance-/Eigentümer-, PostgreSQL- und vollständige Browser-/Geräte-/Barrierefreiheitsabnahme.


## WAR-013 coordinated attack source and UI audit — 2026-11-12

The reconstructed inventory incorrectly marked coordinated attack as unverified. Current source includes schema-73 world/alliance-scoped operations and contributor wings; server-side leader/contributor escrow/refunds, synchronized arrival by maximum travel, target/protection gates, 12-member cap, pinned ACS-3 replay and per-owner return/loot attribution. Existing multiplayer regressions cover successful two-wing resolution, cap, cancel/refund, parallel create and retry. The alliance attack panel was extracted into a directly testable renderer and now verifies leader cancel, member withdrawal, open join, empty state and hostile-label escaping. Python full suite: 465 passed/243 skipped/one existing warning (734.92s); frontend 70/70; ESLint, JS syntax and traceability pass. WAR-013 corrected from unverified to partial; PostgreSQL, actual browser/device/accessibility/localization and broad 2–10 player acceptance remain open.

### WAR-006 Bewegungs-/Rueckreise-Regressionsabgleich -- 2026-11-12

Gezielte Tests fuer Terraingewichtung, langsamste Einheit, Reichweite, atomaren Rundreise-Treibstoff, bekannte Ziele in der read-only Bewegungsprobe sowie Rueckruf ausgefuehrt: 9 bestanden, 7 PostgreSQL-Adaptervarianten mangels `FUR_TEST_POSTGRES` uebersprungen; eine vorhandene Starlette/httpx-Warnung. FUR-2 bleibt unveraendert; FUR-3-COMBAT-3/4 pinnt die Route und nutzt UTC-Faelligkeiten. Kein Codeverhalten geaendert. WAR-006 bleibt `partial`, weil PostgreSQL-/Compose-Runtime, Browser-/Geraete-/Accessibility-/Lastabnahme und Balancefreigabe noch fehlen. Naechster Eintrag: WAR-007 Rueckruf.

### WAR-008 Rueckzug bis zur Rueckkehr regressionsgeprueft -- 2026-11-12

Quell-/Testaudit fand Resolver und normalen Rueckkehrpfad, aber keine zusammenhaengende Missionstestabdeckung fuer einen ausgelosten Rueckzug. `tests/test_game.py::test_fur3_tactical_retreat_returns_only_replay_survivors` nutzt einen reproduzierbaren Seed bei Schwelle 1 Prozent und prueft `attacker_retreat`, Replay sowie exakt dieselben ueberlebenden Truppen in der Rueckkehrmission. Der gezielte Test besteht (1 passed). Vollstaendige Python-Suite nach der Regression: 466 passed, 243 PostgreSQL-Adapterfaelle mangels Docker-Testserver uebersprungen, eine bestehende Starlette/httpx-Warnung (3200,85 s). Ruff und strict mypy bestehen; Black besteht nach Formatierung auf 53 Dateien. WAR-008 bleibt `partial`, bis ACS-Integration, Balance sowie PostgreSQL-/Browser-/Gerate-/Accessibility-/Lokalisierungsabnahme abgeschlossen sind.

### WAR-009 Aufklaerungs-/Intel-Scope erneut geprueft -- 2026-11-12

Gezielter Lauf fuer private, gestufte Berichte, Ein-Ranger-Minimalbericht, Ranger-/PvP-Schutz, Ankunftsneupruefung, FUR-3-Entdeckung/Abfang und FUR-2-Kompatibilitaet: 8 bestanden, 8 PostgreSQL-Adaptervarianten mangels `FUR_TEST_POSTGRES` uebersprungen. Die gesamte Suite mit der Rueckzugsregression besteht mit 466 passed/243 skipped. Status WAR-009 bleibt `partial`: neue Spionagetechnologie ist nicht definiert; Browser-/Mobil-/Accessibility-/Lokalisierungs- und Runtimeabnahme offen.

### WAR-011 Wrack/Reparatur-Bestand korrigiert -- 2026-11-12

Quellabgleich korrigiert die ueberholte Aussage, Terra habe keinen Reparatur-/Wrackpfad: COMBAT-4 speichert idempotente 25%-Wrackanteile je Einheitentyp fuer 48 Stunden. Reparatur kostet 50% der Profilkosten (aufgerundet), dauert `training_time x count`, reserviert Bestand atomar und erstattet bei Abbruch Kosten und Wrack vollstaendig. Die Orbit-Bergungsmission ist weiterhin nicht auf Terra-Wracks uebertragbar. Fokussierte Lifecycle-/Schema-81-Regressionspruefung: 3 passed, 1 PostgreSQL-Variante mangels `FUR_TEST_POSTGRES` uebersprungen. Schema 81 ist source-only, COMBAT-3/4-Ausbildung gesperrt, Werte unbalanciert. WAR-011 bleibt partial. Naechster E07-Schritt: WAR-012 Fernwaffenvertrag-Audit.

### WAR-012 Fernwaffenprofil in COMBAT-3/4 inventarisch belegt -- 2026-11-12

Quellabgleich fand ein versioniertes `artillery_platform`-Profil mit Attacke, Reichweite, Geschwindigkeit, Treibstoff und Konterbeziehungen im COMBAT-3/4-Roster. Die zusaetzlichen Rollen bleiben serverseitig von der Ausbildung gesperrt. Ein eigener Munitions-/Fernangriffs-/Gegenmassnahmen-/Eventlebenszyklus fehlt; dazu wurden keine Werte erfunden. FUR-2 bleibt unveraendert. Gezielter Roster-/Sperrtest: 13 passed, 12 PostgreSQL-Varianten mangels Testserver uebersprungen. WAR-012 von `unverified` auf `partial` korrigiert. Gesamtinventar: 4 verified / 190 partial / 65 unverified / 85 not audited.

### WAR-014 Verteidiger-Verband fokussiert verifiziert -- 2026-11-12

Source-/Testaudit bestaetigt explizite Heimatbasis-Zustimmung und konfigurierbare Kapazitaet, Einheiten-Escrow, Welt-/Allianzpruefung bei Versand und Ankunft, Rueckruf, idempotente Ankunft sowie exakte COMBAT-3/4-Verlustzuordnung je Eigentuemerkonto. Fokuslauf: 4 passed, 4 PostgreSQL-Varianten mangels Testserver uebersprungen. Status bleibt partial, bis Balance-/Eigentuemerabnahme, breite Browser-/Geraete-/Screenreader-/Lokalisierungs-/Last- und PostgreSQL-Abnahme erfolgen. Naechster E07-Eintrag: WAR-015 Belagerung.

### WAR-015 Belagerungsinventar korrigiert -- 2026-11-12

Source audit fand ein `siege_robot`-Profil in den versionierten COMBAT-3/4-Rostern (Ausbildung gesperrt); Orbit-Mondzerstoerung ist eine andere Mechanik. Ein Terra-Belagerungszustand mit Timer, graduellem Schaden, Ablaufentscheidung, Reparatur oder Kapitulation ist nicht implementiert. Dauer, Effekte und Kosten erfordern einen bestaetigten Regelvertrag und wurden nicht erfunden. WAR-015 wird von `unverified` auf `partial` korrigiert. Counts: 4 verified / 191 partial / 64 unverified / 85 not audited.

### WAR-016 PvP-Schutz bei Versand und Ankunft erneut verifiziert -- 2026-11-12

Fokustests fuer Allianz-/NAP-Sperre und Neubeurteilung waehrend des Anflugs: 5 passed, 5 PostgreSQL-Adaptervarianten mangels Testserver uebersprungen. Der Server prueft PvP, Neulingsschutz, Verteidigerurlaub, eigene Allianz und angenommene NAPs bei Versand und Ankunft; eine blockierte Mission gibt die Armee einmal intakt zurueck. Keine formale Kriegserklaerung wird derzeit verlangt. WAR-016 bleibt partial bis UI-/Geraete-/Accessibility-/Lokalisierungsabnahme.

### WAR-017 Raid-Limit-Sourceaudit -- 2026-11-12

Current API-/Mission-/PvP-Pfade und Vorkommen von target-spezifischen Farmzaehlern geprueft. Vorhanden sind generische clientadressbasierte Anfrageratenlimits und maximal 30 parallele Jobs pro Kolonie. Keine Begrenzung wiederholter Angriffe/Verluste/Beute je Spielerziel, keine abnehmenden Ertraege und kein Zielcooldown. Zeitfenster, Caps, Ausnahmen und Resetregeln sind nicht definiert; kein Regelwert wurde erfunden. WAR-017 bleibt `unverified`. Naechster Schritt: WAR-018 Ranking-Vertragsabgleich.

### WAR-018 Welt-/Allianz-Militaerwertung geprueft -- 2026-11-12

Fokussierte Tests fuer idempotenten, auditierbaren FUR-3-Verlust-/Supportledger, aktuelle Weltmitglieder in Allianzsumme und aktiven Welt-Ranking-Scope: 3 passed, eine bestehende Starlette/httpx-Warnung. FUR-2-Ranking bleibt unveraendert. Support ist auf einmal je Spieler/Welt in 24 Stunden begrenzt. Schema 82 und Werte bleiben FUR-3-Entwurf; PostgreSQL-Schema-82, Owner-/Balance-, Browser-/Geraete-/Accessibility-/Lokalisierungsabnahme offen. WAR-018 bleibt partial. Naechster Schritt WAR-019 Replay-/Freigabeaudit.

### WAR-019 Replay-/Berichtsscope korrigiert -- 2026-11-12

Aktualisiert veraltete Behauptung, Replay-Commitment fehle insgesamt: FUR-3 pinnt Regel-Digest und Seed-Commitment, haelt den Seed bis zur atomaren Kampfaufloesung serverprivat und gibt danach das Replay an beide Parteien aus; ACS-Stacks bleiben Teilnehmern zugeordnet. FUR-2 bleibt ein deterministischer Einrundenbericht. Fokuslauf fuer Teilnehmerberichte/Seed-Privatheit: 3 passed, 3 PostgreSQL-Adaptervarianten uebersprungen. Anonymisierte oeffentliche Freigabe fehlt weiterhin; dafuer wird ohne Datenschutz-/Regelvertrag keine Funktion freigeschaltet. WAR-019 bleibt partial. Naechster Schritt: WAR-020 Balance-Gegenbeispiele.

### WAR-020 Kampf-Balance-Gegenbeispiele erneut ausgefuehrt -- 2026-11-12

Fokustests bestehen: 2 passed. Der Resolvergrid umfasst 14.400 deterministische FUR-2-Mischungen; ein zweiter Test beweist je eine begrenzte Sieg- und Niederlagenzusammenstellung fuer alle neun trainierbaren Typen. Das beweist weder Rollenvielfalt noch Balance der gesperrten FUR-3-Profile. WAR-020 bleibt partial; Balance-/Eigentuemerabnahme sowie PostgreSQL- und breite Browser-/Accessibilityabnahme offen. E07-Audit abgeschlossen, naechster Roadmap-Eintrag SOC-001.

### SOC-001 Einladungs-/Bewerbungsfluss auditiert -- 2026-11-12

Getrennte Bewerbungs-/Einladungstabellen decken Bewerbung, Rueckzug, Annahme/Ablehnung, Einladung, Empfaenger-Ablehnung und Leitungs-/Offiziers-Ruecknahme ab. Rechtegepruefte, begrenzte Ansichten und Bereinigung konkurrierender Anfragen bei Aufnahme sind vorhanden. Fokuslauf: 5 passed, 4 PostgreSQL-Varianten uebersprungen, eine vorhandene Warnung. Kein gemeinsames Status-/Historienmodell; manuelle Browser-/Mobil-/Accessibility-/Lokalisierungsabnahme offen. SOC-001 bleibt partial; naechster Schritt SOC-002 granulare Rechte.

## SOC-002 Granulare Allianzrechte — 2026-11-12

Schema 83 ergänzt SQLite- und PostgreSQL-Tabellen für Allianzrechte und übernimmt die bisherigen Offiziersrechte. Für neue Allianzen werden dieselben Standardrechte angelegt. Leitung kann sieben begrenzte Berechtigungen für Offizier und Mitglied setzen. Serverprüfungen schützen Bewerbungsentscheidungen, Einladungen, Beschreibung, Mitgliederentfernung, Diplomatie, Pinnwand und Forum-Moderation; Rollen- und Führungswechsel bleiben leitungsgebunden. Die Allianzoberfläche erhält eine nur für die Leitung sichtbare, zugängliche Checkbox-Matrix. Regression prüft Standardrechte, Ablehnung fehlender Rechte, Freigabe und Widerruf, geschützte Rollen sowie unbekannte Permissions. Qualitäts-/Vollsuite laufen noch; PostgreSQL-Testadapter und manuelle Browser-/Geräte-/Barrierefreiheitsabnahme bleiben offen. Keine persistenten Spielerdatenbanken geändert.

## SOC-003 Führungsübertrag mit Zustimmung — 2026-11-12

Schema 84 ergänzt einen offenen Führungsübergabevorschlag pro Allianz. Der amtierende Leiter bleibt bis zur Annahme im Amt. Nur das benannte aktuelle Allianzmitglied kann akzeptieren/ablehnen; die Leitung kann den Antrag zurücknehmen. Annahme prüft Rechte und Mitgliedschaft neu und aktualisiert Nachfolge, Rolle, Allianzleitung und Antrag atomar. Anträge sind auf die beiden Beteiligten beschränkt; Verlassen/Entfernen löscht einen Vorschlag. Fokus: SQLite Zustimmungslifecycle bestanden; Migrationssuite und volle Python-Suite folgen. Frontend 72/72 sowie Ruff/Black/mypy/ESLint/JS-Syntax bestanden. PostgreSQL-, manuelle Browser-/Accessibility- und Deploymentabnahme offen.

## SOC-004 Formeller Allianzkrieg — 2026-11-12

Schema 85 ergänzt formelle FUR-3-Kriegsdatensätze mit gespeichertem Regelstand/Prüfsumme, Punktziel, Kriegsparteien, idempotenten Kampfbelegen, unveränderlichem Punkteledger und öffentlichem Ereignisfeed. Der versionierte Katalog `FUR-3-ALLIANCE-WAR-1` ist ausdrücklich ein vorläufiger Balanceentwurf: ein Punkt je verlorener gegnerischer Einheit, Ziel 1.000, erste Allianz am Ziel gewinnt; Punkte werden gleichmäßig mit stabilem Konto-ID-Rest verteilt. FUR-2-Statuskriege erzeugen weiterhin keinen formellen Datensatz. Frieden erfordert Angebot und Gegenzustimmung; Ablehnung oder Rücknahme lässt denselben Krieg weiterlaufen. Kampfwertung berücksichtigt nur beteiligte Mitglieder der beiden tatsächlich kriegsführenden Allianzen. Ereignisse mit derselben Sekunde werden chronologisch stabilisiert. Fokusregression nach diesen Regeln: 3 SQLite-Fälle bestanden, 3 PostgreSQL-Adapterfälle mangels `FUR_TEST_POSTGRES` übersprungen. Volle Python-Suite läuft. Balancefreigabe, PostgreSQL, manuelle Browser-/Mobil-/Barrierefreiheits-/Lokalisierungs- und Runtimeabnahme sind offen.

## SOC-005 Allianz-Rangliste — Sourceaudit 2026-11-12

Korrektur der alten Bestandsbehauptung: Ranglistenscreen und `/api/v1/ranking` enthalten bereits eine weltbezogene Aggregation der FUR-3-Militärledgerpunkte nach aktueller Allianzmitgliedschaft; `test_alliance_war_score_is_world_scoped_and_uses_current_members` deckt Kategorie, Weltgrenze und Mitgliedssemantik ab. Saisonabschluss archiviert bislang ausschließlich Spielerränge. Die globale E-Mail-Eindeutigkeit verhindert identische Adressen bei mehreren Konten, identifiziert aber keine Mehrkonten mit getrennten Adressen. Eine Allianz-Saisonarchivierung sowie belastbare Mehrkonto-, E-Mail-Eignungs- und Mitgliederwechselregeln fehlen. Status von `unverified` auf `partial` korrigiert; Feature-Katalog, Matrix und Traceability aktualisiert. Keine Konten oder persistente Datenbanken geändert.

## SOC-005 Allianz-Saisonarchiv — Implementierung 2026-11-12

Schema 86 speichert FUR-3-Militärwertung unveränderlich bei der Allianz, der der Spieler zum Wertungsereignis angehörte. Saisonabschluss schließt den Zeitraum an beiden Grenzen ein, berücksichtigt bestätigte Profile mit nichtleerer E-Mail, friert Namen, Tag, Rang, Punkte und Zahl qualifizierter Konten inklusive Regelversion/-Digest ein und zeigt die Top-Spielerränge plus Allianzarchiv in der Saisonansicht. Gleichstände ordnen sich deterministisch nach Allianz-ID; wiederholte Wertungen/Archivaufrufe verändern keine vorhandenen Belege. `FUR-3-ALLIANCE-RANKING-1` ist ein ausdrücklich vorläufiger Regelentwurf; FUR-2 bleibt unverändert. Frische volle Python-Suite nach SOC-005: 472 passed, 248 skipped (PostgreSQL nicht im Gesamtlauf konfiguriert), 0 failures, 1 vorhandene Starlette/httpx-Deprecation-Warnung. Separat: Migrations-Rehearsal 3 passed; fokussierte SOC-004/005 SQLite+PostgreSQL-Regressions 8 passed im volumenlosen PostgreSQL 18-Testcontainer. Ruff, Black, strict mypy, Frontend tests/lint/syntax, Traceability/JSON und Compose-Konfiguration bestehen. Getrennte E-Mail-Adressen erlauben keine verlässliche Mehrkontoerkennung; Owner-/Balancefreigabe und manuelle UI-/Accessibility-Abnahme fehlen; SOC-005 bleibt partial.

## SOC-006 Allianzkasse — Sourceaudit 2026-11-12

Produktquellen in `fur_empire/`, `static/`, Migrationen und `tests/` geprüft: kein Allianzkassen-Ledger, Spenden-/Auszahlungs-/Antragsfluss, Gebühr, Vier-Augen-Freigabe oder zugehörige UI/Regression vorhanden. Die bestehende Allianzrechte-Matrix hat keine Kassenrechte. Gebühren, Ausgaberechte, Schwelle für zweite Freigabe, zulässige Freigeber, Ablauf/Ablehnung/Storno sind nicht spezifiziert. Keine Ressourcenbewegung oder Gebührenregel erfunden; Status bleibt `unverified`, Umsetzung erfordert einen versionierten Regelentwurf und anschließende Regression.

## SOC-007 Allianzprojekte — Sourceaudit 2026-11-12

Produkt- und Testquellen geprüft: kein Projektkatalog, Beitrag, Abschluss-/Belohnungsweg, Erstattung, Worker, Persistenz oder UI vorhanden. Kosten, Zielmengen, Fristen, Belohnungen, Überzahlung, Rückzahlung, Berechtigung, Abbruch, Welt-/Mitgliederwechsel und Neustart sind nicht spezifiziert. Keine Ressourcenwirkungen erfunden; Feature bleibt `unverified` bis ein versionierter Regelentwurf vorliegt.


### ITEM-010 / UX-017 UI-Nachpruefung -- 2026-11-14

Responsive CSS fuer die Benachrichtigungskategorien ergaenzt, damit Checkboxen und Beschriftungen in einem klaren Raster statt als breite Einzelzeilen erscheinen. Isolierte SQLite-Browserwelt: DemoAstra eingeloggt; Kategorie Wirtschaft ausgewaehlt und nach „Protokoll laden“ wurden 30 Eintraege angezeigt, alle mit der Kategorie Wirtschaft. Die All-Kategorien-/aeltere-Verlauf-Browserpruefung konnte wegen nicht bedienbarer nativer Auswahl in der aktuellen CUA-Sitzung nicht abgeschlossen werden; keine vollstaendige Historien- oder Accessibility-Abnahme behauptet. Frontend 83/83, ESLint, JS-Syntax und 344-ID-Traceability bestanden. Temporärer Server gestoppt; disposable DB liegt unter `data/item010-ui-smoke.sqlite3`, aber die Shell-Sicherheitsrichtlinie blockierte die Loeschung. Persistente Main-/Staging-Daten unveraendert.


### ITEM-010 Filterseiten-Regression und ITEM-011 Sourceaudit -- 2026-11-14

ITEM-010: Kategorieumschaltung fordert eine neue serverseitig gefilterte Seite an und setzt den Kategorien-Cursor zurück; ältere Cursorabfragen verwenden denselben Kategorieparameter. Frontend-Verhaltenstest prüft URL, Filter und Cursorwechsel. Frontend 85/85; ESLint, JavaScript-Syntax und Traceability 344/344 bestanden. Fokussierter SQLite-Domänentest für Kategorie/Paginierung bestanden; PostgreSQL-Adapter mangels `FUR_TEST_POSTGRES` übersprungen. Fokussierter API-Test war in dieser Windows-Umgebung nach langsamen Argon2-/SQLite-Anfragen nicht verlässlich terminal; daher kein Erfolgsanspruch. Kein aktueller Voll-Pythonlauf.

ITEM-011: Root-Quellen `fur_empire/`, `static/`, Tests, Konfiguration und Lockfile auditiert. Es existieren weder Service Worker/Push API noch Subscription-Persistenz/CRUD, Sender/Worker, VAPID-Konfiguration oder Preview-Policy. Für eine sichere Umsetzung sind eine autorisierte Web-Push-Laufzeitabhängigkeit samt Lockfile, persistente VAPID-Schlüsselverwaltung und Rotation, owner-gebundene Subscription-/Widerrufspfade, generische Payloads, Endpoint-SSRF-/Missbrauchsregeln, Retry/Expiry, CSP-/Scope-/Cache-Deployment und Browser-Opt-in-/Abmeldeabnahme nötig. Keine Abhängigkeit oder Datei-Lock aktualisiert; Push bleibt optional und nicht implementiert. Main und Staging unverändert.


### ITEM-001 Inventar-Sourceaudit -- 2026-11-14

Statusabgleich korrigiert: `spec/FEATURES.json` und `TRACEABILITY.md` hatten ITEM-001 als ungeprüft geführt, obwohl die aktuelle Matrix bereits einen Teilumfang kannte. Quellprüfung bestätigt FUR-NEUTRAL-MARKET-1 mit sieben zusätzlichen Materialstapeln plus Holz/Stein/Erz je Kolonie; serverseitigem Depotlimit, aktiver Kolonie-/Weltbindung, idempotenter atomarer Transaktion, unveränderlichem Tauschbeleg, Audit/Bericht, Kontoexport und Abbruchschutz vor Inventarverlust. Kein allgemeiner Itemkatalog, keine Slot-Policy, Itemtransfers/Reserve, Crafting-/Dropbindung oder vollständige Lokalisierung. ITEM-001 bleibt `partial`; kein neues Inventarverhalten oder Balancewert erfunden.


### ITEM-009 Vorlagen-Sourceaudit -- 2026-11-14

Feature-Inventar korrigiert: `spec/FEATURES.json`, Matrix und Traceability hatten den bereits implementierten Vorlagenfluss als ungeprüft/in Arbeit geführt. Missionsvorlagen sind owner-gebunden, prüfen Modus/Einheiten/Counts/Eroberungsoption, begrenzen 10 Einträge und erlauben case-insensitive eindeutige Namen. Bau-/Forschungs-/Trainingsvorlagen prüfen Katalogschlüssel und Anzahl, speichern owner-gebunden und begrenzen ebenfalls zehn. Einreihen ruft die gewöhnliche idempotente `Game.command`-Logik auf und validiert Ressourcen, Voraussetzungen und Queue erneut. UI kann erstellen, laden und löschen; Missionsvorlage wird auf verfügbare Einheiten gekappt. Fokussierte API-Regressionen für Missionvorlagen, Produktionsscope/Idempotenz und CSRF: 3 passed, eine bestehende Starlette/httpx-Deprecation-Warnung. Browser-, Mobil-, Tastatur-/Screenreader- und fünfsprachige Abnahme offen; ITEM-009 bleibt partial.


### ITEM-002 Crafting-Sourceaudit -- 2026-11-14

In `fur_empire/`, `static/`, Tests und Ruleset geprüft: kein Crafting-Katalog, Rezept-/Craft-Endpunkt oder Befehl, Produktionsjob, Input-Escrow, idempotenter Output-Beleg, UI oder Regression vorhanden. `crafting_component` und `crafts_support_drones` stehen nur als unverbundene Textwerte im Orbit-Regelkatalog. ITEM-002 ist `unverified`; Voraussetzung ist das generische ITEM-001-Inventarmodell plus ein versionierter FUR-3-Rezept-/Zeitkatalog und atomare Worker-Retry-/Abbruchsemantik. Für diesen Audit wurden keine Kosten oder Dauern erfunden, keine Produktionsdateien geändert.


### Feature-status vocabulary reconciliation -- 2026-11-14

Validator exposed a repository inconsistency: `spec/FEATURES.json` retained legacy values (`existing_partial`, `in_progress`, `implemented_unverified`) that violate the canonical validator and no longer matched the 344 evidence rows in TRACEABILITY.md. Normalized canonical feature and implementation-matrix JSON plus compact Markdown statuses to current Traceability statuses (202 partial, 80 not audited, 58 unverified, 4 verified); retained every prior nonmatching value as `historical_inventory_status`. Updated the inventory status note to clarify that `in_progress` alone is not evidence. `scripts/check_traceability.py` now passes all 344 IDs. No gameplay data or persistent database changed.


### ITEM-001 Warenlager: Cap-Validierung und Stapelanzeige -- 2026-11-14

Das vorhandene `goods_inventory` validiert nun nur katalogisierte Nicht-Rohstoffgüter, nur nichtnegative Ganzzahlen und keinen Bestand oberhalb des aktuellen Depotlimits. Ungültige JSON-Warenbestände lösen vor Anzeige/Tausch eine Regelablehnung aus, statt still als gültige Ware behandelt zu werden. `market_view` meldet belegte Materialstapel gegenüber den sieben katalogisierten Materialarten; die neutrale Börse zeigt diese Zahl mit dem aktiven Depotlimit. Keine FUR-2-Kosten-/Produktionswerte verändert, keine Migration nötig. `tests/test_neutral_market.py`: 21 passed. Frontend 85/85, ESLint, JS-Syntax, Ruff, Black (59 Dateien unverändert), strict mypy (41 Dateien) und 344-ID-Traceability bestanden. Generische ITEM-001-Gegenstände, Transfers und Crafting bleiben offen; FUR-2 unverändert.


ITEM-001 API-Nachweis ergänzt: `tests/test_api.py::test_neutral_goods_command_requires_csrf_and_records_only_one_exchange` besteht (1 passed, bestehende Starlette/httpx-Warnung). Der authentifizierte Börsenbefehl gibt `material_stacks={used:1,available_types:7}` aus; idempotenter Replay lässt den Wert unverändert. API-Test ist in der Feature-Traceability referenziert.


### ITEM-001 Materialwaren zwischen eigenen Kolonien -- 2026-11-14

Kolonieversorgung transportiert zusätzlich zu Holz/Stein/Erz die sieben katalogisierten Materialwaren. Jede Einheit zählt als eine Träger-Kapazitätseinheit. Bei Abflug werden Zielbestände plus bestehende Eingangsreservierungen gegen das Depotlimit geprüft und reserviert; Markttausch kann diesen Platz nicht verbrauchen. Die Ankunft löst die Reservierung im selben Worker-Vorgang in Bestand auf. Rückruf entfernt die Zielreservierung und liefert die Materialfracht mit der Truppe zurück. Rückkehrende Ware nutzt freien Depotraum und legt einen Überschuss in `goods_reserve`; die Warenbörse zeigt den Bestand und bietet eine Claim-Aktion mit erneutem Cap-Check. Idempotenz bleibt am vorhandenen Befehls- und Jobablauf gebunden. Geplante Handelsrouten transportieren weiter nur Rohstoffe. Keine FUR-2-Regeln geändert, keine Migration oder persistente Spielerdaten verändert. `tests/test_neutral_market.py` plus Kolonieversorgungsregression: 23 passed, 1 optionale PostgreSQL-Adaptervariante skipped; gezielter SQLite-Rückruftest: 1 passed. Frontend 85/85, ESLint, JS-Syntax, Ruff, Black (53 Dateien), strict mypy (41 Dateien), JSON und 344-ID-Traceability bestanden. Generische Items, freie Spielertransfers, Crafting/Drops, Gesamt-Python-Suite, PostgreSQL-Integration und manuelle UI-Abnahme bleiben offen.


### ITEM-001 Generisches FUR-3-Inventar -- 2026-11-14

Neues versioniertes `FUR-ITEM-INVENTORY-1` definiert acht Gegenstands-IDs und Klassen aus dem vorhandenen FUR-3-Regelkatalog. Pro Kolonie gelten sechs belegte Stapelarten und maximal 1.000 Stück je Art; JSON-Bestände, Eingangsreservierungen, Stapelplätze und Reserven werden strikt validiert. Die bestehende eigene Kolonieversorgung kann diese Gegenstände mit Gewicht 1 transportieren. Empfang reserviert Stapel und Cap, Ankunft wandelt die Reservierung atomar um, Rückruf gibt sie frei, Rückfracht wird ins Inventar oder in die anteilig claimbare Reserve zurückgebucht. Die UI zeigt Bestand/Unterwegs/Reserve und unterstützt Transfer/Claim. Kontodatenexport umfasst Gegenstandsdaten; Kolonieaufgabe ist bei Bestand, Reserve oder reservierter Fracht gesperrt. `tests/test_items.py`, Warenlager-/Versorgungs-/Recall-/Export-/Abandonment-Regressionen: 38 passed, 2 optionale PostgreSQL-Fälle skipped. Frontend 86/86, ESLint, JS-Syntax, Ruff, Black (55 Dateien), strict mypy (42 Source-Dateien), JSON und Traceability bestanden. Keine Migration oder persistente Datenänderung. Gegenstände haben absichtlich noch keine Crafting-/Drop-Erwerbsquelle oder Spielwirkung; ITEM-002/004, vollständige Suite, PostgreSQL und manuelle Geräte-/Mehrsprachenabnahme bleiben offen.


## 2026-11-14 - ITEM-002 crafting and ITEM-003 recycling

ITEM-002 provides two explicitly provisional recipes in the per-world FUR-CRAFTING-1 opt-in; FUR-2 remains the default. ITEM-003 adds FUR-ITEM-RECYCLING-1: one field repair kit returns two crafting components and three textiles, below the three components and six textiles used to make it. Catalog loading rejects salvage output vectors above any producing recipe input vector. Both actions are in the strict API contract, transactional, idempotent, audited and available in the trade UI; overflow goes to existing reserves.

Combined ITEM-002/003 package regression: 48 passed. Authenticated API/crafting/recycling follow-up: 30 passed with one existing Starlette/httpx deprecation warning. Frontend 88/88. Ruff, Black, strict mypy (44 source files), ESLint for static/app.js, JavaScript syntax, JSON and Traceability 344/344 passed. The full Python suite is still running. FUR-3 values remain drafts; owner balance, PostgreSQL, browser, device, accessibility and localization acceptance remain open. Main and Staging were not changed.


## 2026-11-14 - ITEM-002/003 completed local regression checkpoint

Full Python suite: **533 passed, 261 optional/unconfigured PostgreSQL adapter cases skipped, zero failures**, with one existing Starlette/httpx deprecation warning (1635.46s). After the added item-stack and market-goods reserve-overflow assertion, the focused crafting/items/market/authenticated API package passed **50 tests**. Frontend 88/88. A disposable PostgreSQL 18 colony-supply/recall adapter run passed 16 tests; its container and anonymous volume were removed. Ruff, Black (64 files), strict mypy (44 source files), npm lint/check, JS syntax, JSON and Traceability 344/344 passed. Main and Staging were unchanged; no migration or deployment occurred. ITEM-002/003 remain partial because FUR-3 values are drafts and manual browser/device/accessibility/localization acceptance remains open. Next feature: ITEM-004.

## 2026-11-14 — ITEM-005 Commander progression checkpoint

Added opt-in `FUR-3-HERO-1` with world/account-scoped Commander records, immutable exact-once XP events pinned to new eligible jobs, completion XP, bounded level/skill progression, one available economy stat (+2 percentage points production per point, max +20%), server/admin world opt-in, overview UI and player report/audit. Military/recon/command allocation remains blocked until ITEM-006; FUR-2 and legacy missions are unchanged. Schema 94 is included for SQLite/PostgreSQL and is deliberately not deployed to persistent databases. Added six SQLite regressions and one frontend test. Focused SQLite: 6 passed; frontend 89/89, lint/check passed. Full Python run, final disposable PostgreSQL adapter run and aggregate quality/traceability checks are in progress. Balance and manual browser/device/accessibility/localization acceptance remain open; ITEM-005 is partial, not complete.

Full Python suite after ITEM-005: **540 passed, 266 optional/unconfigured PostgreSQL adapter cases skipped, zero failures**, with the existing Starlette/httpx deprecation warning (2222.72s). The six new Commander regressions are included in the SQLite count; its full adapter matrix separately passed 10/10 on SQLite and disposable PostgreSQL 18. Frontend 89/89; Ruff, Black (67 files), strict mypy (46 sources), ESLint, JavaScript syntax, JSON validation and Traceability 344/344 passed. The short-lived PostgreSQL container was removed. Persistent Main/Staging databases and player data were not touched; schema 94 was not deployed. ITEM-005 remains partial pending balance and manual browser/device/accessibility/localization acceptance; military/recon/command remain gated for ITEM-006.

Post-checkpoint stabilization note: An exploratory ITEM-006 edit introduced temporary references to an unfinished bonus helper and was not retained. Those references were removed immediately. The post-correction regression subset passed **17 passed, 4 optional PostgreSQL skips, 0 failures**; Commander SQLite focused tests passed 6/6. Repeated final Frontend 89/89, Ruff, Black (67 unchanged), strict mypy (46 source files), ESLint, JavaScript syntax and Traceability 344/344 all pass. No ITEM-006 gameplay effects have been activated; its balance contract remains the next work item.


## 2026-11-14 — ITEM-006 Commander-Doktrinen (vorläufig)

Separates weltweises `FUR-3-HERO-2` setzt voraus, dass `FUR-3-HERO-1` aktiv ist. Der versionierte Regelkatalog deckelt Wirtschaft bei +2 Prozentpunkten Produktion je Punkt (max. 20 %), Militär bei +2 % Schaden je Punkt ausschließlich in Terra-FUR-3-Kämpfen (max. 20 %), Aufklärung bei +10 % PvP-Berichtsdauer je Punkt (max. 100 %) und Kommando bei +1 gleichzeitigem Terra-Auftragsplatz je Punkt (max. 5). Angriffs-, Raub- und Spähaufträge pinnen Version, Prüfsumme, Stats und berechnete Effekte; Worker prüfen den Snapshot. FUR-2-Kampfgleichungen bleiben unverändert. Nichtwirtschaftliche Attribute sind erst mit beiden Weltopt-ins verteilbar. Werte sind ein vorläufiger Balanceentwurf.

Fokussierte SQLite-Commander-/Doktrinenregressionen: 19 bestanden, 6 optionale PostgreSQL-Fälle übersprungen. Frontend 89/89; Ruff, Black (68 Dateien), strict mypy (47 Quellen), ESLint, JavaScript-Syntax und Traceability 344/344 bestanden. Der fokussierte Commander-/Doktrinenlauf bestand mit 14/14 über SQLite und einen isolierten PostgreSQL-18-Container; die zusätzliche SQLite-Regressionsgruppe bestand mit 19 Tests, sechs optionale PG-Fälle wurden übersprungen. Der Container wurde entfernt. Die vollständige Python-Suite bestand mit 542 passed, 268 skipped, 0 failed und einer vorhandenen Starlette/httpx-Deprecation-Warnung (2510,01 s). Keine persistenten Main-/Staging-Daten oder Schemas geändert. Browser-/Mobil-/Tastatur-/Screenreader-/Übersetzungsabnahme sowie Eigentümer-Balance bleiben offen; ITEM-006 ist teilweise umgesetzt.


## 2026-11-14 — ITEM-007 Commander-Attribut-Reset (vorläufig)

Neues weltweises `FUR-3-HERO-3`-Opt-in verlangt HERO-1. Der Reset kostet auf der aktiven Kolonie je 250 Holz, Stein und Erz; Cooldown je Konto/Welt: sieben Tage. Er setzt nur alle Attributstufen zurück, belässt XP und das unveränderliche Exact-once-XP-Ledger und berechnet Skillpunkte aus Level minus erneutem Stat-Stand. Schema 95 ergänzt `last_respec_at` für SQLite und PostgreSQL. API-Befehl mit normalem Idempotenzschlüssel und derselben Spieltransaktion bucht Ressourcen, Reset, Audit und Befehlseintrag gemeinsam. Commander-Übersicht und Admin-Weltregel enthalten Kosten, Cooldown und Sperrgrund. Werte sind ein unbewilligter Balanceentwurf.

Fokussierte Hero-/Respec-Suite: 20/20 über SQLite und disposable PostgreSQL 18. Migrations-/Restore-Gruppe: 11 bestanden, 7 optionale PG-Skips. Frontend 89/89; ESLint, JS-Syntax, Ruff, Black (69 Dateien), strict mypy (48 Quellen), Python-Syntax und Traceability 344/344 bestanden. Gesamte Python-Suite läuft. Temporärer PostgreSQL-Container entfernt; persistente Main-/Staging-Daten unverändert; Schema 95 nicht ausgerollt. Eigentümer-Balance, manuelle Browser-/Geräte-/Tastatur-/Screenreader- und Mehrsprachenabnahme offen.

## ITEM-008 — kosmetische Kampagnenbelohnungen

FUR-3-COSMETIC-REWARDS-1 versieht vorhandene einmalige Kampagnenaufträge mit rein kosmetischen Konto-Freischaltungen. Der serverautoritative Auftragsabschluss und `player_cosmetic_unlocks` teilen eine Transaktion; der Primärschlüssel `(user_id, cosmetic_id)` verhindert Doppelfreigaben. Spieler wählen nur tatsächlich besessene Belohnungstitel, Skins und Banner. Profilkarten enthalten die Auswahl ausschließlich beim bestehenden öffentlichen Opt-in. FUR-2-Regeln bleiben unverändert.

Die Belohnungen verwenden absichtlich beschriftete Textdarstellungen statt nicht vorhandener Asset-Dateien. Balance-/Kunstfreigabe, weitere Belohnungsquellen, Mobil-/Screenreader-Abnahme und Lokalisierung bleiben offen; ITEM-008 bleibt daher teilweise umgesetzt.

## ITEM-008 — Abschlussprüfung

2026-11-15: Schema-96-Suite vollständig grün: 546 bestanden, 272 optionale/unconfigured PostgreSQL-Skips, 0 Fehler; fokussierte Migration/Profile 31 bestanden/27 Skips. Frontend 89/89; Ruff, Black64, strict mypy49, ESLint, JS-Syntax und Traceability344/344 grün. FUR-2 sowie persistente Main-/Staging-Daten unverändert.

## ITEM-009 — Baupläne

2026-11-15 Audit der vorhandenen Funktion: Konto-eigene Missionsvorlagen (Migration013) und Produktionsvorlagen für Bau, Forschung, Rekrutierung (Migration019) sind bereits vorhanden. API erzwingt Besitzerfilter, Namens-/Katalog-/Anzahllimits; beim Einreihen wird die gleiche serverautoritative aktive Kolonie, Welt, Kosten-, Voraussetzung- und Queue-Logik verwendet. Frontend hat Panels in Bau, Forschung und Streitkräfte sowie Missionsvorlagen im Missionsdialog. Regression erweitert: Produktionstest deckt Einreihung/Replay für Bau, Rekrutierung und Forschung sowie Eigentümer- und Mengenlimits ab; Frontendtest prüft alle drei Panels und escaping. Fokussiert: API 1 passed; Frontend90/90. Manuelle Mobil-/Tastatur-/Screenreader-Abnahme und vollständiger Lauf nach der Testergänzung ausstehend, daher partial.


## 2026-11-15 — ITEM-011 regression checkpoint and SEAS-001 world directory

ITEM-011 now has owner-bound Web Push subscriptions and generic event delivery with provider/endpoint restrictions, validated VAPID configuration, worker retry/expiry, and explicit browser opt-in. After installing the exact existing `requirements.lock` in the local `.venv`, focused push-domain/API and VAPID key-generation regressions passed 7/7. Ruff, Black check (65 files), strict mypy (50 sources), frontend 92/92, ESLint, JS syntax and 344-ID traceability passed. Full Python suite, PostgreSQL 97 migration, real browser/provider delivery and device/accessibility/localization acceptance remain open; no persistent DB or player data was changed.

SEAS-001 source audit found world join/switch, world-scoped ranking, safe ruleset metadata and bounded cursor pages already implemented. Added an aggregated public distinct-player count to the existing world page plus an accessible rule summary and a direct link to the active world ranking. API cursor/count regression passed 1/1; frontend 92/92. Mobile, keyboard/screen-reader, localization, multi-user browser and PostgreSQL acceptance remain open; no schema migration was needed.


## 2026-11-15 — SEAS-002 atomare Weltgründung mit Startregeln

Die Admin-Weltgründung erlaubt jetzt im selben Befehl Seed, 8–300 Außenposten, Dauer-/Saison-/Sandbox-Modus, Joinstatus und einen vollständigen Regelprofil-Snapshot. FUR-2 bleibt Standard; Kampf, Fertigung, Commander, Doktrinen und Respec lassen sich als FUR-3-Entwurf nur explizit aktivieren. Serverseitige Wert- und Abhängigkeitsprüfung erfolgt vor dem deterministischen Aufbau; ungültige Regeln hinterlassen keine Teilwelt. Startprofil, Weltkarte, Außenposten, Audit und Idempotenzdatensatz teilen die bestehende Transaktion. API-Regression prüft 8 Außenposten, null Startkolonien, gewählte Regeln, Replay ohne Doppelanlage und Rollback einer inkompatiblen Regelkombination. API 1/1, Frontend 93/93, Ruff/Black/strict mypy/ESLint/JS-Syntax bestehen. Vollsuite nach diesem Code-Update, PostgreSQL Seed-/Restore-Drill und manuelle Admin-/Mobil-/Barrierefreiheits-/Lokalisierungsabnahme offen; keine Schemaänderung oder persistente Datenänderung.


## 2026-11-15 — SEAS-003 saisonale Wettbewerbe mit Punkteziel

`admin_season` ist nun strikt auf Admins in `mode=season` begrenzt; Dauer- und Sandboxwelten können keine Saison starten. Die Administration setzt Titel, 1–365 Tage und ein FUR-2-Ranglisten-Punkteziel (1 bis 1.000.000.000). Schema 98 speichert das Ziel; bestehende Saisonzeilen erhalten den Startwert 10.000. Der Worker ergänzt bei Abschluss in der weltgebundenen Ranglistenarchivzeile `goal_reached` und schließt den Beitritt zur beendeten Saisonwelt. Admins erhalten das Startformular nur in einer neuen Saisonwelt; alle Spieler können Ziel, Ende, Status und Archiv einsehen. SQLite-Saisonregressionen: 3 passed, 3 optionale PostgreSQL-Parameter übersprungen; Schema-98-Default/Constraint: 1 passed. Frontend94/94; Ruff, Black65, strict mypy50, ESLint, JS-Syntax und Traceability344/344 bestanden. PostgreSQL-98/Worker, vollständige Python-Suite nach den neueren Änderungen, echte Browser-/Mobil-/Screenreader-/Lokalisierungsabnahme und Prüfung des Standardziels 10.000 offen. Keine persistente Datenbank migriert.


## SEAS-004 Saisonabschluss und Awards — Implementierung 2026-11-15

Schema 99 ergänzt `season_awards` mit stabiler Eindeutigkeit pro Saison/Konto/Award und Datenbankregeln gegen nachträgliche Änderung oder Löschung. Der Ablauf-Worker friert Einzelrangliste, Zielerreichung, Saisonmeister, Allianzrangliste und Archivstatus in einer Transaktion ein; Konfliktbehandlung macht Wiederholungen idempotent. Die Saisonansicht zeigt Einzel-/Allianzstände und Awards escaped an. Fokustests SQLite + temporäres PostgreSQL 18: 6 bestanden; Schema-/Unveränderlichkeitstest: 1 bestanden; Frontend94/94. Ruff und Black bestehen. PostgreSQL-18 Migration/Worker, Award-Trigger und Retry sind mit 6/6 fokussierten Fällen abgenommen; strict mypy, Ruff/Black, ESLint/JS und Frontend94/94 bestehen. Vollständige Python-Suite läuft; manuelle UI-/Accessibility-/Lokalisierungsabnahme ist offen. Keine persistente Datenbank migriert.


## SEAS-005 Dauerweltschutz — Quellaudit und Regressionserweiterung 2026-11-15

Der Worker verarbeitet nur fällige, nicht archivierte Saisons, berechnet den Ranglistenstand nach `season.world_id` und sperrt nach Abschluss nur genau diese Saisonwelt. Dauerwelten erhalten keinen Saisonabschluss. `test_world_events_and_season_archive_are_isolated` prüft nun zusätzlich eine Genesis-Heimatkolonie als Sentinel (Kolonie-ID, Gebäude, Einheiten und kein Genesis-Saisoneintrag). Die Vollsuite war beim Einbau des Test-Sentinels bereits gesammelt; gezielter SQLite-/PostgreSQL-Rerun folgt nach dem Voll-Lauf. UI-/Mehrwelt-, Mobil-, Accessibility- und Lokalisierungsabnahme offen.

SEAS-005-Nachtest: Genesis-Bestandskolonie bleibt nach Archivierung der getrennten Saisonwelt erhalten; SQLite + temporäres PostgreSQL 18: 2 passed. Rehearsal-Fix für schema71→99: fokussiert 1 passed. Nach erstem Vollsuite-Lauf (554 passed, 273 skipped, 1 veraltete Fixture-Erwartung fehlgeschlagen) läuft die vollständige Suite mit korrigiertem Fixture erneut.


## SEAS-004/005 Abschlussprüfung — 2026-11-15

Korrigierter kompletter Python-Lauf nach den neuen Schema-99-Awards und dem auf Schema71 zurückgebauten Migrations-Rehearsal: 555 passed, 273 optionale PostgreSQL-Adapterfälle übersprungen, 0 failed, eine vorhandene Starlette/httpx-Deprecation-Warnung (1359.82s). Das alte Datenbankkopie-Rehearsal 71→99 besteht; die SEAS-005-Genesis-Sentinels bestehen auf SQLite und disposable PostgreSQL18 (2/2). Frontend94/94; Ruff, Black65, strict mypy50, ESLint, JS-Syntax und Traceability344/344 bestehen. Kein persistenter Main-/Staging-Store migriert. Manuelle Browser-/Mobil-/Accessibility-/Lokalisierungs- und Produktionsabnahme bleibt offen.

## SEAS-006 versionierte Live-Ereignisse — 2026-11-15

Schema 100 ergänzt geplante Live-Ereignisse mit 0–168 Stunden Warnzeit, optionaler Endphase, separatem Bonus und weltgebundenem FUR-2-Ranglistenziel. Haupt- und Endbonus werden zeitanteilig in der Produktion berücksichtigt. Der Adminbefehl speichert Ereignis, kanonischen Regel-Snapshot, Version und SHA-256-Digest atomar; Legacy-Ereignisse werden mit bisherigem Verhalten rückwärtskompatibel versioniert. Die Oberfläche erklärt Phasen und Ziel und zeigt Fortschritt sowie Regelbeleg. Focused SQLite: 8 bestanden/5 optionale PG-Skips; temporäres PostgreSQL 18: 13 bestanden. Frontend94/94, Ruff, Black72, strict mypy51, ESLint, JS-Syntax und 344-ID-Traceability bestanden. Vollsuite läuft; manuelle Browser-/Mobil-/Tastatur-/Screenreader-/Lokalisierungsabnahme offen. Persistente Main-/Staging-Datenbanken wurden nicht migriert.

## Vollsuite SEAS-006 und Freigabe der Allianzkassenwerte — 2026-11-15

SEAS-006 vollständige Python-Suite: 561 bestanden, 277 optionale/unconfigured PostgreSQL-Fälle übersprungen, 0 fehlgeschlagen, eine bestehende Starlette/httpx-Deprecation-Warnung (938,91 s). Der Eigentümer hat anschließend die schon technisch implementierten Kassenwerte ausdrücklich freigegeben. FUR-3-ALLIANCE-TREASURY-2 pinnt diese Zustimmung als neue Regelversion; Version 1 bleibt erhalten, damit bestehende Anträge ihre bisherige Version/Prüfsumme behalten. Werte: Spenden kostenfrei, 1 % je Ressource (Abrundung), zwei verschiedene Freigeber ab 5.000 Bruttoressourcen, Ablauf nach sieben Tagen mit vollständiger Rückbuchung. Verifikation der neuen Version läuft. Keine persistente Datenbank geändert.

Verifikation der freigegebenen Allianzkassen-Version 2 abgeschlossen: SQLite + temporäres PostgreSQL18 2/2; vollständige Python-Suite 561 passed / 277 optionale PostgreSQL-Skips / 0 failed / eine bestehende Starlette/httpx-Warnung (922,21 s); Frontend94/94, Ruff, Black72, strict mypy51, ESLint, JS-Syntax und Traceability344/344 grün. Bestehende Anträge behalten FUR-3-ALLIANCE-TREASURY-1; keine persistente DB migriert.

## SEAS-007 Live-Ereignis-Überlagerung — 2026-11-15 (Vollsuite läuft)

FUR-2-LIVE-2 berechnet die Summe überlappender Ereignisse an jedem Ereignis-/Endphasenrand neu und begrenzt sie vorläufig auf 100 Prozentpunkte. Ein einzelnes Ereignis bleibt unverändert. Die Grenze ist Teil des unveränderlichen Regel-Snapshots. Produktionssimulation, Statusansicht, Adminvorschau und paginierte Live-Übersicht nutzen dieselbe Obergrenze; die Gesamtanzeige wird unabhängig von der gerade sichtbaren Feed-Seite berechnet. SQLite8 und disposable PostgreSQL18 13 focused bestanden; Frontend94, Ruff/Black72/mypy51, ESLint, JS-Syntax und Traceability344 grün. Vollsuite läuft. Owner-Balancefreigabe, manuelle UI-/Accessibility-/Lokalisierungsabnahme und persistentes Rollout offen; keine persistente DB geändert.

SEAS-007 Gesamtprüfung abgeschlossen: Python562 passed /277 optionale PostgreSQL-Skips/0 failed/eine vorhandene Starlette/httpx-Warnung (967,58 s); SQLite-Overlap8/5 optionale Skips; disposable PostgreSQL18 fokussiert13/13; Frontend94, Ruff, Black72, strict mypy51, ESLint, JS-Syntax und Traceability344 grün. 100-Prozentpunkte-Cap bleibt bis zur Owner-Balancefreigabe vorläufig. Keine persistente Datenbank migriert.

## SEAS-008 Allianzrangliste — Source-Audit 2026-11-15

Vorhandene FUR-3-Allianzwertung wurde gegen Spielcode, API/UI, Migration 086 und Regressionen auditiert: Livewertung ist weltgebunden und nutzt aktuelle Mitgliedschaft; Saisonwertung bleibt den Allianz-IDs zum Zeitpunkt der Punktebuchung zugeordnet. Rangfolge, Allianzname/-tag, qualifizierte Kontenzahl, Regelversion und Prüfsumme werden beim Saisonabschluss als unveränderlicher Snapshot gespeichert. Die Regeln `FUR-3-ALLIANCE-RANKING-1` bleiben vorläufig; Eigentümerfreigabe für Punktattribution und verifizierte Kontoeligibilität sowie manuelle Browser-/Accessibility-/Lokalisierungsabnahme offen. SQLite-Vollsuite562/277 Skips/0 failed; fokussierter PostgreSQL18-Adapterlauf folgt. Keine persistente Datenbank migriert.
SEAS-008 gezielter Datenbanklauf abgeschlossen: Archiv-/Saisonabschlussregression SQLite und disposable PostgreSQL18 2/2. Keine permanente DB verändert.

## SEAS-009 Ranglistenarten — 2026-11-15

Die Lückenprüfung fand zuvor nur die FUR-2-Gesamtwertung sowie separate FUR-3-Militär-/Allianzpunkte. Ergänzt sind nun aktive-Welt-Kategorien Gesamt, Wirtschaft, Forschung, PvE, Krieg, Allianz und Regionen. Die bestehende FUR-2-Gesamtwertung bleibt unverändert; Wirtschaft/Forschung/PvE zerlegen deren vorhandene Gebäudestufen-, Forschungsstufen- und Eroberungspunkte. Krieg zählt unveränderliche FUR-3-Punkte der aktiven Welt; Regionen zählen zwei Punkte je aktueller Kontrolle. Schema 101 archiviert sechs Kontokategorien mit Regelversion/Prüfsumme am Saisonende; Allianzstände bleiben im bestehenden zeitgebundenen Archiv. Alte Saisons werden nicht rückwirkend befüllt.

Gezielte SQLite-API-/Kategorie-/Saison-/Migrationsregressionen 6 bestanden, 1 optionaler PostgreSQL-Parameter übersprungen. Disposable PostgreSQL18 Saison-Snapshot 1 bestanden; Migrations-Rehearsal SQLite 71→101 bestanden. Ruff, Black sieben Dateien, strict mypy52 bestehen. Gesamtsuite sowie Frontend/Traceability-Abschlussprüfung laufen. Regelwerte sind ein Balanceentwurf; Browser-/Mobil-/Tastatur-/Screenreader-/Lokalisierungsabnahme offen. Persistente Main-/Staging-Datenbanken wurden nicht migriert.

SEAS-009 Gesamtprüfung abgeschlossen: Python565 passed/277 optionale PostgreSQL-Skips/0 failed/eine bestehende Starlette/httpx-Warnung (949,56 s). Frontend94/94; Ruff, Black7, strict mypy52, ESLint, JS-Syntax und Traceability344/344 bestehen. Separater PostgreSQL18-Saison-Snapshot1/1 sowie SQLite-Migrations-Rehearsal71→101 bestanden. Regelwerte bleiben Balanceentwurf; manuelle Abnahme und persistente Migration offen. Main/Staging unverändert.

Korrigierter abschließender SEAS-009-Lauf nach Übernahme des historischen FUR-2-Saison-Gesamtwerts: Python565 passed/277 optionale PostgreSQL-Skips/0 failed/eine vorhandene Starlette/httpx-Warnung (957,39 s). PostgreSQL18-Snapshot regression1/1 und SQLite-Rehearsal71→101 bestanden. Frontend94, Ruff/Black/strict mypy, ESLint, JS-Syntax und Traceability344 grün. Keine persistenten Datenbanken migriert.

## SEAS-010 Hall of Fame — 2026-11-15

Bestehende Quellen enthalten unveränderliche Saison-Awards/Zielerreichung, Allianz-Saisonstände, Orbital-Wächterbelohnungen und formelle Allianzkriegschronik samt Beteiligungsledger. Systems.hall_of_fame erzeugt daraus eine nur lesende, aktive-Welt-Sicht je Konto; der Saisonbildschirm zeigt getrennte Bereiche für persönliche Saisonerfolge, Allianzplätze, geborgene Bossfunde und beendete Kriege. Keine neue Awardregel und kein rückwirkender Backfill. Fokus SQLite2 bestanden/1 optionaler PG-Skip; PostgreSQL18 Fokus3/3; Frontend95, ESLint, JS-Syntax, Ruff, Black, strict mypy grün. Vollsuite folgt; manuelle Browser-/Mobil-/Screenreader-/Lokalisierungs- und Historientiefenabnahme offen. Main/Staging unberührt.

SEAS-010 vollständige Python-Suite: 566 passed/277 optionale PostgreSQL-Skips/0 failed/eine vorhandene Starlette/httpx-Warnung (960,99 s). PostgreSQL18 Hall-of-Fame-/Allianzarchiv-Fokus3/3; SQLite-Fokus2/1 Skip; Frontend95/95, Ruff, Black, strict mypy52, ESLint, JS-Syntax und Traceability344 grün. Persistente Dienste unverändert.

## SEAS-011 Imperium-Prestige — 2026-11-15

FUR-3-PRESTIGE-1 implementiert dauerhaft bis zu drei kontoweite Kosmetikstufen für Kampagnensieg, Saisonmeisterschaft und erreichtes Saisonziel. Die bestehende Terra-Orbit-Prestige-Mechanik bleibt separat. Schema 102 speichert den unveränderlichen, source-key-idempotenten Award; Awards werden in der Transaktion bestehender Quest-Claim-/Saisonabschlusslogik verbucht und im Hall-of-Fame-Bildschirm angezeigt. SQLite fokussiert4 bestanden/1 optionaler PG-Skip; disposable PostgreSQL18-Fokus5 bestanden, darin Saisonretry und Schema-Rehearsal 71→102. Vollsuite567 passed/277 optionale PostgreSQL-Skips/0 failed/eine bestehende Starlette/httpx-Warnung (977,92 s). Frontend95/95; Ruff, Black, strict mypy53, ESLint, JS-Syntax und Traceability344 grün. Keine persistente Datenbank migriert. Browser-/Mobil-/Screenreader-/Lokalisierungsabnahme und gesicherter Produktionsrollout bleiben offen.

## SEAS-012 geplante und dringende Ankündigungen — 2026-11-15

Schema 103 ergänzt geplanten Veröffentlichungszeitpunkt (jetzt bis 90 Tage voraus) und Notfallmarkierung. Bestehende Ankündigungen werden auf ihren bisherigen Erstellungszeitpunkt zurückgeführt. Admins/Moderatoren sehen nur Planungen ihrer erlaubten Reichweite und können sie abbrechen; Spieler erhalten fällige Beiträge nach Weltfilterung, sortiert nach Veröffentlichungszeit. Audit erfasst Reichweite, Zeitpunkt, Notfallkennzeichnung und Archivierung; privates Systempostfach bleibt isoliert. SQLite fokussiert4 bestanden/2 optionale PG-Skips; disposable PostgreSQL18 Fokus6 bestanden einschließlich Schema-Rehearsal71→103. Backfill bestehender Beiträge separat SQLite1 + PostgreSQL18 2/2. Frontend95/95; Ruff/Black/strict mypy53/ESLint/JS/Traceability344 grün. Python-Vollsuite nach abschließendem Backfill-Test läuft; persistente Main-/Staging-DB unverändert.

## SEAS-011/012 Abschluss — 2026-11-15

Nach SEAS-012-Schedule-, Scope-, Notfall- und Schema-103-Altbestandsregression: vollständige Python-Suite568 passed/278 optionale PostgreSQL-Skips/0 failed/eine bestehende Starlette/httpx-Deprecation-Warnung (1107,66 s). SEAS-011 Fokus SQLite4/1 Skip, disposable PostgreSQL18 5; SEAS-012 Fokus SQLite4/2 Skips, disposable PostgreSQL18 6; Altbestands-Backfill SQLite1/1 Skip und PostgreSQL18 2/2. Frontend95/95, Ruff, Black, strict mypy53, ESLint, JS-Syntax und Traceability344 grün. Main/Staging unverändert. Beide Features bleiben für manuelle Browser-/Geräte-/Accessibility-/Lokalisierungsabnahme und sichere persistente Migration partiell.

## E11 NPC-Lagerbewegung und Kolonieschutz — 2026-11-16

FUR-3-NPC-CAMPS-2 bleibt ein opt-in Balanceentwurf. Der Schutzabstand ist jetzt wechselseitig: FUR-3-Lager bewegen sich nicht in den Sechs-Sektoren-Radius vorhandener Spielerbasen; neue Spielerbasen werden bei Gründung/Weltbeitritt außerhalb der Lagerabstände platziert. Kolonisierung, Verlegung und Außenposten-Umwandlung weisen Ziele im aktiven Lagerabstand ab. FUR-2 und FUR-3-NPC-CAMPS-1 bleiben unverändert. Die Maneuverregression deckt nun auch ab, dass ein fehlendes legales Ziel Ressourcen und Kontingent nicht verbraucht. Schema71→110-Snapshotprobe und gezielte SQLite-/disposable PostgreSQL18-Matrix: 7/7 bestanden; historische SQLite-Versionserwartungen 109→110: 9 bestanden, 4 optionale PostgreSQL-Varianten übersprungen; PostgreSQL-Standabstandstest zusätzlich 2/2. `npm test`, Ruff, Black, strict mypy, ESLint, JS-Syntax und Traceability344 bestanden. Erster vollständiger SQLite-Lauf: 576 passed, 290 optionale PostgreSQL-Skips, 8 fehlgeschlagen; sieben waren überholte Schema-109-Erwartungen, der verbleibende PG-Standoff-Test bestand bei direkter Wiederholung SQLite+PostgreSQL. Die alten Erwartungswerte sind korrigiert; abschließende Wiederholung läuft. Keine persistente Datenbank oder Live-Compose-Dienste verändert. Manuelle Browser-/Mobil-/Screenreader-/Lokalisierungs- und Balanceabnahme bleibt offen.

Abschließende pytest-Wiederholung mit temporärem PostgreSQL18: 873 passed, 1 skipped, 0 failed, eine bestehende Starlette/httpx-Deprecation-Warnung (12,420.12 s). Der zusätzliche Skip ist der absichtliche Backup/Restore-Test. Ruff (76 Dateien), Black check (76 Dateien), strict mypy (55 Module), ESLint, JavaScript-Syntax, Frontend-Tests und Traceability344 bestanden. Die temporäre PostgreSQL-Instanz wurde entfernt. Sieben ursprüngliche Fehler waren veraltete Test-Maxima (Schema 109→110); ein achter PostgreSQL-Standoff-Test bestand bei direkter Wiederholung für SQLite und PostgreSQL. Alle Korrekturen bestehen den Wiederholungslauf. Main und Staging blieben unverändert. PVE-001/002 bleiben partiell wegen noch ausstehender manueller UI-/Geräte-/Accessibility-/Lokalisierungs- und Balanceabnahme.

## PVE-003 NPC-Angriffsplanung — 2026-11-16

FUR-3-NPC-CAMPS-2 erhält eine ausdrücklich nicht angreifende Planungsstufe: höchstens ein privater, unveränderlicher Zielhinweis pro Welt/Fünf-Minuten-UTC-Takt. Auswahl rotiert zuerst nach dem zuletzt betroffenen Spieler und dann nach dem seltensten NPC-Lager; stabile Zyklusschlüssel verhindern Duplikate und Worker-Nachläufe erzeugen keine Bursts. Schema 111 speichert Ziel-, Truppen- und Regelprüfsummen-Snapshot. Nur der Besitzer des betroffenen Außenpostens sieht die Warnung. Es werden keine Einheiten dispatcht, Kämpfe aufgelöst, Ressourcen oder Spielerdaten geändert oder Beute vergeben; FUR-2 bleibt unverändert.

Gezielte NPC-Domainregressionen: 4 bestanden, 3 optionale PostgreSQL-Fälle mangels `FUR_TEST_POSTGRES` übersprungen. Node-Frontend: 99/99 bestanden, einschließlich Escaping und Warnungstext. Vollsuite sowie Ruff/Black/mypy/ESLint/JS-Check/Traceability laufen noch. PVE-003 bleibt partiell: tatsächliche Missionen, Kampf-/Bericht-/Belohnungsweg, PostgreSQL, manuelle Geräte-/Accessibility-/Lokalisierungsabnahme sind offen. Keine persistenten Datenbanken migriert.

PVE-003 Abschluss dieses vertikalen Schritts: vollständige SQLite-Python-Suite 585 passed / 291 optionale PostgreSQL-Fälle übersprungen / 0 failed; eine vorhandene Starlette/httpx-Deprecation-Warnung (2.404,26 s). Die neue Planungs- und Schema-111-Migrationsmatrix bestand auf SQLite und disposable PostgreSQL 18 mit 7/7 Fällen. Frontend 99/99, Ruff, Black (76 Dateien), strict mypy (55 Module), ESLint, JavaScript-Syntax und Traceability344 bestanden. Die Owner-Regel der Allianzkasse bleibt gemäß Freigabe bei 1 % je Ressource, zwei unabhängigen Freigebern ab 5.000 Bruttoressourcen und sieben Tagen Ablauf/Rückbuchung; bestehende Regressionen bestätigen diese Regeln. Keine persistenten Main-/Staging-Datenbanken wurden geöffnet oder migriert. PVE-003 bleibt partiell, bis aus Warnplänen echte versionierte Missionen samt Auflösung, Schutz-/Abbruchregeln, Berichten und Abnahme entstehen.

PVE-003 Planner-Budget-Nachprüfung: Die Kandidatenobergrenze ist auf 300 erhöht, entsprechend dem aktuellen Welt-Erstellungslimit. Zwei Indizes für die Sieben-Tage-Fairnessabfragen vermeiden fortlaufende Vollscans der Audit-Historie. Das neue Schema-Rehearsal und Planner-Set besteht auf SQLite und disposable PostgreSQL 18 mit 5/5 Fällen; der vorherige vollständige Pythonlauf gilt nicht als Endnachweis für Schema112, daher wird die Vollsuite erneut ausgeführt. Main/Staging bleiben unverändert.

PVE-003 Schema112-Gesamtabschluss: Der vollständige Python-Lauf besteht mit 585 passed / 291 optionalen PostgreSQL-Skips / 0 failed und einer bestehenden Starlette/httpx-Deprecation-Warnung (3.512,58 s). Fokussierte Planner-/Migrationstests bestanden auf SQLite und Wegwerf-PostgreSQL18 zusammen 5/5. Frontend 99/99; Ruff, Black76, strict mypy55, ESLint, JS-Syntax, JSON-Validität und Traceability344 bestanden. Das 300-Ziele-Limit entspricht dem aktuellen maximalen Weltumfang; Schema112 indiziert Fairnessabfragen der letzten sieben Tage. Haupt- und Staging-Datenbanken blieben unverändert. PVE-003 bleibt partiell: tatsächliche Missionausführung, Kampf, Berichte/Belohnung, breitere Concurrency-/Load- und manuelle UI-/Accessibility-/Lokalisierungsabnahme fehlen weiterhin.

## PVE-003 Schema 113: faire Zielkenntnis — 2026-11-16

Die Angriffsplanung nutzt nun ausschließlich lagerinterne Besitzerbeobachtungen: Ein Ziel ist nur planbar, wenn genau dieses Lager dessen aktuellen Besitzer innerhalb der letzten sieben Tage beobachtet hat. Fehlende oder veraltete Beobachtungen sowie inzwischen geänderte Besitzer blockieren den Hinweis. Schema 113 speichert die beobachtete Besitzer-ID und indiziert die Frischeabfrage. FUR-2 und die FUR-3-CAMPS-1-Version bleiben unverändert; tatsächliche Angriffe bleiben deaktiviert.

Gezielte SQLite-Planer-/Aufklärungs-/Migrationsfälle: 4 bestanden, 2 optionale PostgreSQL-Skips. Dieselben gezielten PostgreSQL-18-Fälle: 6/6 bestanden. Frontend 99/99, Ruff, Black70, strict mypy55, ESLint, JavaScript-Syntax, JSON-Validität und Traceability344 bestanden. Vollständige Python-Suite gegen Schema 113 läuft noch. Keine persistente Datenbank und keine Main-/Staging-Compose-Dienste verändert. PVE-003 bleibt partiell: Missionsausführung, Kampf, Berichte/Belohnungen sowie manuelle UI-/Geräte-/Accessibility-/Lokalisierungs- und Balanceabnahme sind offen.
## PVE-003 Schema 114 — tatsächliche NPC-Angriffe — 2026-11-16

Der optionale FUR-3-NPC-CAMPS-3-Vertrag führt Warnung (300 Sekunden), höchstens einen Angriff je Spieler/24 Stunden und höchstens eine Auflösung je Welt/Worker-Durchlauf ein. Missionen pinnen Seed/Commitment, Regel-Digest und Kampfversion; sie brechen bei veraltetem Ziel, Eigentümerwechsel, Schutzstatus oder ungültigem Trupp ab. Auflösung verbucht NPC-Verluste und Überlebende sowie begrenzte Ressourcenbeute, erobert keine Außenposten und verändert keine Spielerarmee. Nur der betroffene Besitzer erhält den Gefechtsbericht. FUR-2 und CAMPS-1/2 bleiben unverändert; Werte sind opt-in und nicht balanceabgenommen.

Vollständige Python-Suite: 588 bestanden, 294 optionale PostgreSQL-Skips, 0 fehlgeschlagen (1453,70 s; eine bestehende Starlette-Deprecation-Warnung). Fokussierte SQLite-Fälle: 5 bestanden/4 optionale PG-Skips; Wegwerf-PostgreSQL 18: 12/12. Frontend99, Ruff, Black70, strict mypy55, ESLint, JS-Syntax und Traceability344 bestanden. Breitere PostgreSQL-/Last-/Concurrency- sowie manuelle Browser-/Geräte-/Accessibility-/Lokalisierungs-/Balanceabnahme bleiben offen. Persistente Main-/Staging-Datenbanken blieben unangetastet.

PVE-004-Audit: neutrale Vorräte füllen sich bereits mit einer Ressource je Typ/Minute bis 400 × Außenpostenstufe. Die Verteidigung ist derzeit rein abgeleitet (55 × Stufe² plus Truppen, danach Terrainmodifier), wird bei Kämpfen nicht beschädigt und hat deshalb keinen regenerierbaren Zustand. Eine zusätzliche „Verteidigungsregeneration“ braucht zuerst einen kohärenten, opt-in FUR-3-Durabilitätsvertrag; bestehende FUR-2-Festung bleibt unverändert.


## PVE-004 / COMBAT-5 — Festungsintegrität und Regeneration — 2026-11-16

Der bestehende, nicht beschädigbare Tier-/Terrainbonus bleibt in FUR-2 und COMBAT-1 bis COMBAT-4 unverändert. Neuer opt-in Regelstand `FUR-3-TERRA-COMBAT-5` macht ausschließlich neutrale Außenpostenfestungen dauerhaft beschädigbar: maximal 55 × Stufe² Integrität, bei erstmaliger Aktivierung bestehender Welten volle Festung, 2 % der maximalen Integrität je vergangener Minute (aufgerundet), Worker-Catch-up je Außenposten, keine Regeneration besetzter Außenposten. Beim Erobern wird der Neutralfestungszustand entfernt. Kampfauflösung, Gefechtsprobe und Karte verwenden denselben Integritätswert; Kampf-Replay zeichnet den verbleibenden Wert auf. Schema 115 aktualisiert die SQLite-/PostgreSQL-Regelstand-Whitelist; SQLite-Rebuild erhält abhängige Welt-FKs. Admin-Auswahl, Rollout-Gates, Trainings-/Reparatur-/Verteidigungsintegration und UI-Hilfe berücksichtigen COMBAT-5.

Fokussierte SQLite-Regressionsgruppe: 5 bestanden (Stock-Caps/World Scope, Integritäts-Catch-up/Owned-Post-Skip/Idempotenz, deterministische Zerstörung, echte Spieler-Raid-Persistenz plus anschließende Heilung). Admin-Welterstellung C5 besteht auf SQLite; optionale PostgreSQL-Variante übersprungen. Schema-71→115-Rehearsal inklusive FK-Prüfung besteht. Frontend 99/99, Ruff, Black7 geänderte Pythondateien und strict mypy55 bestanden; volle Suite und abschließende PostgreSQL-18-Prüfung laufen noch. Persistente Main-/Staging-Datenbanken bleiben unberührt. Werte sind nicht balanceabgenommen; manuelle Browser-/Geräte-/Accessibility-/Lokalisierungsabnahme bleibt offen.


## 2026-11-18 — E11 bis PVE-008

Ruinenerkundung ist über den echten HTTP-Befehl und die Karte erreichbar. Der Grenzland-Dialog verwendet die Serverregeln. Schema 118 ergänzt den kooperativen Weltboss mit der vom Eigentümer gewählten einmaligen Schadensaufteilung. Schema 119 ergänzt Invasionsfenster und ein Angriffsbudget über CAMPS-3. Die drei gesicherten Datenbankkopien wurden bis Schema 119 erfolgreich restauriert und geprüft. Die gemischte Fokussuite für Boss und Invasion bestand mit 26 Fällen. Frontend bestand mit 103 Fällen. Vollsuite, Balance, vollständige Übersetzungen und barrierefreie Abnahme bleiben offen. Details und Fortsetzung stehen im Root-Protokoll und in RESUME_STATE.json.
