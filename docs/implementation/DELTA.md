# Source-Delta — 2026-11-09, Phase A

Kein Testlauf, kein Runtime-Start, kein Deployment und keine Datenmigration in
diesem Arbeitsstand. Das Produkt ist weiterhin unvollständig.

## Bestandsbefunde

- Das Root ist die FastAPI-Anwendung; die Referenzarchive bleiben unverändert.
- `.git` fehlt. Ausgangskopie mit SHA-256-Inventar:
  `backups/implementation-20261109/SOURCE_SHA256.txt`. Enthält Produktcode,
  Tests, Dokumentation und bisherige Trackingdateien, keine `.env` oder Secrets.
- Die jüngsten Übergabeberichte nennen Schema 28. Der aktuelle Source enthält
  bereits Migration 029 und eine persistierte Ranglistenprojektion. Diese
  vorgefundenen Änderungen wurden erhalten. Live-Schema/Container wurden nicht
  abgefragt; keine aktuelle Betriebsbereitschaft wird daraus abgeleitet.
- Das originale 344-ID-Inventar liegt jetzt unter
  `FUR_CODEX_UEBERGABE/MASTER_SPEC/spec/FEATURES.json`. Das rekonstruierte
  Root-Inventar samt historischen Nachweisen bleibt erhalten. Aktuelle
  Phase-A-Matrix: `IMPLEMENTATION_MATRIX.json` / `.md`.
- Mehrwelten, Kolonien, Terrain/Fog, NPC-Grenzdruck, Expeditionen,
  Produktionsvorlagen, Freunde/Blocks, Notizen, Allianzforum/Pinnwand und
  zahlreiche Cursor-Listen sind tatsächlich im Source vorhanden. Ein erneuter
  flächiger Neubau dieser Systeme wäre falsch.

## Implementierte Änderungen, noch nicht verifiziert

1. **F2-048:** Zehn-Güter-Börse mit lokalem persistentem Wareninventar,
   serverseitigem Werttausch, 50/60-Prozent-Regel, Cap/Stock-Prüfung,
   unveränderlichem Beleg, Export, Abandon-Schutz und zehn Original-SVGs.
2. **TERRA-008:** Weltgebundener Heimatwechsel, 24-Stunden-Sperrfrist mit
   gespeichertem Ablauf/Regelhash, Besitzerprüfung, Audit und UI. Aktive
   Kolonie, Armeen, Ressourcen und Reiseziele werden nicht umgebucht.
3. **ENG-004/E04/ECO-003/ECO-004/K08/ECO-011:** Vorhandene Domainaktionen
   `cancel_job`, `queue_move`, `expedition`, `alliance_send_supply` und
   `alliance_supply_cancel` sowie `direction` waren im strikten API-Vertrag
   nicht zugelassen. Der Vertrag ist jetzt mit den vorhandenen UI-/Domainpfaden
   verbunden; sämtliche serverseitigen Regeln bleiben zuständig.
4. **ENG-001/W06/W03/WAR-006:** Neue Spielerangriffe/Transporte pinnen
   `target_colony_id`. Auflösung liest diese Kolonie mit Besitzer- und Weltprüfung,
   statt die aktuelle Auswahl des Empfängers zu verwenden. Historische Jobs ohne
   Pin verwenden ausschließlich die Heimat der Ursprungswelt. Fehlende Ziele
   führen zur sicheren Rückkehr; Aufklärung eines inzwischen entfernten Ziels
   läuft über den bestehenden Abbruch/Rückkehrpfad. Bereits entsandte
   Allianzversorgungen bleiben nach Heimatwechsel an ihre ursprüngliche
   berechtigte Zielkolonie gebunden.

## Nicht erledigt

Das vollständige Layer-Audit aller 344 IDs ist offen. Insbesondere Orbit,
FUR-3-Rundenkampf/erweiterte Einheiten, Energie/Unterhalt, ACS,
Allianz-Saisonwertung, Allianzkasse/-projekte, umfangreiche Questkampagnen, Crafting/Helden,
weltisolierte Saisonarchitektur und vollständige Lokalisierung sind nicht
als vollständig implementiert nachgewiesen. Die Matrix nennt unbekannte
Layer ausdrücklich offen. Historische grüne Tests sind keine aktuelle Abnahme.

Die Migrationen 030/031 sind ausschließlich vorbereitet. Sie wurden weder auf
temporäre noch auf persistente Datenbanken angewandt. Vor jeglichem späteren
Start beachten: `Game` migriert beim Initialisieren; daher in Phase A keine
App/Worker/CLI mit einer persistenten Datenbank starten.


### ENG-002 — Abschlussgrenze der Saisonwelt

Beitritt vor Worker-Archivierung ab Endzeit, administratives Wiederöffnen und ein zweiter Wettbewerb sind serverseitig gesperrt. Regression vorbereitet. Sandboxwelten sind serverseitig PvE-Übungswelten ohne Saisonwettbewerbe.


### ENG-003 — FUR-2-Katalogbindung

Schema 034 vorbereitet. Versionskonflikte verhindern den Runtime-Start. FUR-3/Orbit und die parallele Katalogausführung bleiben offen.


### ORB-001 — Terra-Zugang

Schema 035, Weltzugang, Materialbuchung und Imperiumsaktion vorbereitet. Orbit-Karte, Flotten und Kolonien bleiben offen.


ORB-002/003: Navigierbare öffentliche Orbit-Geografie innerhalb freigeschalteter Welten. Private Beobachtungen und dynamische Kartenobjekte sind offen.


ORB-004: Exklusive Zielreservierung und persistente Ankunftsgründung für das Pionierschiff vorbereitet. Werft, Folgekolonien und Ausbau stehen aus.


ORB-007/009/010: Startwirtschaft mit Ausbau, Solarversorgung und Ätherförderung implementiert. Orbit-Erzförderung und weitere Module offen.


ORB-008/012/013: Erzförderung, Schiffbauforschung, Werft und Bestand aller 14 Schiffsklassen. Flotteneinsatz und weitere Forschung bleiben offen.


ORB-011/014: Frachtermission mit Hin- und Rückflug, Frachtlimit und verlustfreier Zielreserve. Weitere Missionen und Rückruf sind offen.


ORB-003/016: Private Sondenbeobachtungen und Sichtgrenzen integriert. Abgestufte Sensorik und Abfangen offen.


ORB-015: Orbit-Angriff, deterministischer Rundenkampf, Berichte und Rückkehr. Gemischte Flotten, Trümmer, Mond und Station stehen offen.


ORB-021: Trümmer und begrenzte Bergung durch Beteiligte integriert. Weitergehende Sicht- und Zugangsregeln bleiben offen.


ORB-006/015: Stationäre Verteidigungsplattform und Kampfbeteiligung integriert. Eigenständige Raumstationen, Monde und Wartung bleiben offen. ORB-017 ist durch Orbit-Fracht bereits teilweise abgedeckt.


ORB-005: Mondentstehung und Anzeige angeschlossen. Mondgebäude, Nutzung und Eroberung offen.


ORB-006/018: Stationsausbau, Wartung und lokale Garnison mit Kampfeinsatz umgesetzt. Interkoloniale/allierte Stationierung und Stationsressourcen offen.


ORB-003/016: Mondscanner, gestufte Beobachtung und Abfangen durch Stationsgarnison integriert. Weitere Sensor- und Flottenbeobachtung offen.


ORB-023: Eigene Sprungtore und atomare Transfers integriert. Weitergehende Freigaben und Abnahme offen.


ORB-020: Orbit-Expeditionen mit Verlust, Fund, Hinflug und Rückkehr integriert. Persistente Anomalien und umfangreiche PvE-Ketten offen.


ORB-022: Kostenpflichtiger Phalanxscan mit privater Momentaufnahme und Stationsstörung integriert.


ORB-024: Mondbelagerung und Schadensbilanz integriert. Neubildung und Gesamtabnahme offen.


ORB-025: Allianzverbände, Ankunft, Rechte und Verteilung integriert. Detailberichte je Kontingent und Abnahme offen.


ORB-026: Rückruf und taktischer Rückzug für Orbit-Angriffe integriert. Einzelkontingent und weitere Missionsarten offen.


ORB-027: Persönliche Werft- und Flottenvorlagen in der aktiven Welt integriert. Mehrklassenprofile bleiben offen.


ORB-028: Zeitgebundener Flottenunterhalt ohne Offline-Verluste integriert.


ORB-029: Kampfwracks, Verbrauch und Werftreparatur integriert. Gesamtabnahme offen.


ORB-030: Erzfrachten in beide Richtungen mit Startabbuchung und fälliger Ankunft integriert. Weitere Materialverträge bleiben offen.


ORB-031: Munition, Reichweite und Abwehr in Orbit-Gefechten integriert. Weitere Einsätze und Abnahme offen.


ORB-032: Regelgebundene Orbit-Ereignisse mit Risiken und Belohnungsgrenzen. Mehrstufige Bosse und eigene Ereigniskartenobjekte offen.


TERRA-010: Kartenaktion und serverseitige Versetzung mit stabiler Kolonie-ID integriert. Erweiterte Schutzsektoren folgen unter TERRA-014.


TERRA-014: Weltgebundene Schutz- und Reservierungssektoren mit Admin-Aktion, Karte und allen regulären Gründungspfaden verbunden.


TERRA-015: Freiwillige Ruinen mit Sicht und Ablauf integriert. Inaktivitäts- und Wiederherstellungspfad offen.


TERRA-015: Vorwarnung, reversible Inaktivität und Pause ohne Entfernung umgesetzt. Wiederbesiedlung inaktiver Standorte bleibt separat offen.


ENG-005: Spiel-Outbox und Weltprotokoll integriert. Weitere Domain-Ereignisse, Retention und Betriebsmetriken stehen offen.


ENG-006: Herkunftsbindung und Hash-Signatur für neue Befehle. Kontext bleibt für ältere API-Aufrufer optional.


ENG-007: Chronologischer Terra-/Orbit-Scheduler integriert. Orbit-Quarantäne bleibt offen.


ENG-008: Orbit-Quarantäne, Admin-Wiederanlauf und Rückstandsprobe integriert. Zeitreihen und Abnahme offen.


ENG-009: Transaktionales Orbit-Ledger ergänzt. Ein gemeinsamer Buchungsschlüssel und Reconciliation über beide Ebenen bleiben offen.


ENG-010: Zwischenrundung bei Gelände- und Eventeffekten entfernt. Gemeinsame Phase-B-Abnahme bleibt offen.


ENG-011: Welt-/Besitzgrenzen für persistente Orbit-Missionspfade verstärkt. Terra-JSON und Migrationsabnahme bleiben offen.


ENG-012: Welt-Blueprint und isolierter Restore vorbereitet. Spielerdaten, Aufträge und Orbitzustand werden vom Blueprint nicht erfasst.

## Nächste Abhängigkeit: FUR-3-ACS / Fortifikationen

Der nächste Live-Kampfpfad darf nicht durch bloßes Seed-Pinning als FUR-3 markiert werden. Der aktuelle Allianzresolver verwendet die separat versionierte Ein-Runden-Auflösung; neutrale Außenposten haben in ihrem Zustand keinen Heer- oder Integritätswert und erhalten ihre Verteidigung ausschließlich aus dem historischen Tier-Faktor. Vor ACS müssen ein versionierter, replaybarer Quellen-Stack mit Teilnehmer-Taktiken und persistente Fortifikationsintegrität für Außenposten/Schildwall feststehen. Entscheidung und Begründung stehen in `docs/implementation/DECISIONS.md`. Danach erst combat resolver, Migration, ACS-Escrow/Verlustaufteilung, Replayberichte und Regressionen integrieren.


## K07 / WAR-008: konfigurierbarer FUR-3-Rückzug

Schema 76 ergänzt `terra_retreat_threshold_percent` pro Welt (1–100, Standard 60). Admin-Welteinstellungen bieten ein Zahlenfeld; API validiert Bereich und Ganzzahligkeit. Neue FUR-3-Missionen pinnen die Schwelle beim Dispatch in ihren privaten Combat-Datensatz. Laufende Missionen bleiben unverändert. Getestet mit SQLite-Gesamtsuite und fokussierten SQLite/PostgreSQL-18-Migration-, Admin- und Pinningfällen.


## K04 / WAR-005: FUR-3-Gefechtsprobe

Bei aktiviertem FUR-3 erzeugt die Gefechtsprobe 16 deterministisch abgeleitete Szenario-Seeds und löst sie mit demselben versionierten Terra-Resolver auf. UI und API zeigen Siegchance und Verlust-/Überlebendenbereiche; Beute erscheint nur, wenn der neutrale Vorrat bekannt ist. PvP nutzt die beim frischen Level-2-Scan gespeicherte Abwehr, nie aktuelle verborgene Zielwerte. Die Simulation persistiert weder Kampf noch Audit-/Ledgerdaten und gibt keine Szenario-Seeds zurück. FUR-2 bleibt deterministisch. Fokus: 6 SQLite-Tests bestanden; 10 PostgreSQL-18-Varianten bestanden; Frontend 62 bestanden. Vollständige Python-Suite: 391 bestanden, 209 bedingte Überspringungen (PostgreSQL nicht für den Gesamtlauf konfiguriert), eine vorhandene Starlette/httpx-Deprecation-Warnung. Black-Check (48 Dateien), Ruff (fur_empire/tests/scripts), strict mypy (32 Dateien), ESLint, JavaScript-Syntax und Traceability 344/344 bestanden. Diese FUR-3-Balance ist Beta, keine Abnahme.

## K05 / ACS-Lebenszyklusregressionen

Nach dem FUR-3-Simulator-Slice ergänzt: Allianzaustritt eines Nichtleiters vor Eintreffen, zwischenzeitliche Eroberung des festgeschriebenen neutralen Ziels und Beitrittsversuch exakt an der Sammelgrenze. Ungültige Flügel kehren mit ihren vollständigen reservierten Truppen zurück; ein zurückerobertes Ziel bleibt unverändert; verspäteter Beitritt reserviert weder Truppen noch Flügel. SQLite: 3 bestanden; PostgreSQL 18 im temporären Container: 6 bestanden. Der Adapterlauf deckte einen Fehler im Testcode auf und wurde nach Korrektur erneut bestanden. Kein produktiver Code oder bestehender Spielstand wurde verändert.

## K05 / ACS-Grenzen und Wiederholbarkeit

Ergänzt: die Obergrenze von zwölf aktiven Flügeln (dreizehnter Beitritt wird ohne Escrow abgelehnt) sowie erneute Worker-Auflösung derselben Fälligkeit (genau ein Rückflug, Bericht und Audit je Mitglied). Zusammen mit den drei Lebenszyklusfällen bestehen fünf fokussierte SQLite-Fälle; der temporäre PostgreSQL-18-Nachlauf besteht mit 10 adapterparametrisierten Ausführungen. Black, Ruff, strict mypy und 344-ID-Traceability bestehen. Crash-Injection/Transaktionsrollback und konkurrierender Join/Withdraw bleiben offen.

## K06 / alliierte Garnisonsreservierung

Drei neue Mehrspielerregressionen prüfen: Zwei parallele Entsendungen à vier Einheiten gegen Kapazität fünf führen genau zu einer Reservierung; sechs identische Command-Tokens erzeugen nur eine Garnison und ein Audit; doppelte Worker-Auflösung derselben Ankunft erzeugt nur eine aktive Garnison. SQLite: 3 bestanden. PostgreSQL 18 im isolierten, danach entfernten Container: 6 bestanden. Worker-Crash-Injection und Transaktionsrollback bleiben offen.

## K06 / Ankunfts-Fehlerrollback

Eine injizierte Persistenzstörung direkt nach der Datenbankänderung auf `active`, aber vor dem Speichern der Gastgebermeldung, belegt atomaren Rollback: Garnison bleibt `travelling`, Sender-Escrow und Ankunftsauftrag bleiben bestehen, Gastgeber erhält keinen Bericht und Audit bleibt leer. Ein anschließender sauberer Worker-Lauf aktiviert die Garnison genau einmal. Der Test besteht auf SQLite und PostgreSQL 18; im PostgreSQL-18-Lauf bestanden alle vier K06-Fokusfälle insgesamt 8 adapterparametrisierte Ausführungen.


## Gesamtprüfung nach ACS-/Garnisonsregressionen (2026-11-11)

Vollständige Python-Suite: 400 bestanden, 218 übersprungen, eine bestehende Starlette/httpx-Deprecation-Warnung, 523.10 Sekunden. Die PostgreSQL-Varianten der neuen K05-/K06-Fälle liefen separat gegen PostgreSQL 18 und bestanden; der übrige PostgreSQL-Gesamtlauf wurde nach der reinen Testergänzung nicht wiederholt.

## K09 / WAR-011 / ORB-021 / ORB-029: Bergung und Reparatur — Source-Audit

Der vorhandene Orbit-Pfad enthält bereits befristete, begrenzte Trümmer aus Schiffsverlusten, teilnehmergebundene Berichte, Bergungsmissionen mit Cargo-/Salvager-Grenzen und eine Worker-Rückgabe. Orbit-Wracks können gegen Regelkosten über die Werftqueue repariert werden. Die integrierte Multiplayer-Regressionsfunktion `test_pioneer_reserves_exclusive_planet_and_founds_once` deckt Bergung und Reparatur ab; eine separate Browser-/Geräte-/Barrierefreiheitsabnahme fehlt. Die früheren Traceability-Aussagen „kein Orbit-System“ waren falsch und sind mit Code-/Testpfaden berichtigt.

Das eigentliche Terra-K09 bleibt teilweise offen: FUR-3-Kampfeinheiten erzeugen noch keine Materialtrümmer und haben keinen Reparaturablauf. Um keine Wirtschafts- und Konkurrenzregeln zu erfinden, bleiben Ressourcenquote, Eigentum/Teilnehmerkreis, Verfall, konkurrierende Bergung und Reparaturpreis im versionsgebundenen Terra-Regelvertrag offen. K09/WAR-011/ORB-021/ORB-029 sind daher `partial`, nicht `verified`.

K12 Source-Audit bestätigt FUR-3-Einzelrundenreports, Teilnehmer, Einheitenverluste/Überlebende, Replay und expandierbare escapte Details im UI; die relevanten PvE-/PvP-Replaytests bestehen laut letzter Gesamtprüfung. ACS ist weiterhin FUR-2-Einrunde. Dieser Slice änderte nur Inventar-/Nachweisdokumente; keine Tests wurden neu ausgeführt. `scripts/check_traceability.py`: 344 IDs, Status synchron.

## K10 / K11: getrennte Terra- und Orbit-Funktionsabdeckung

K10 Source-Audit: Orbit-1 enthält Sternlanzen für eine Eröffnungssalve sowie Schleier-Abfänger. Die Abflugvalidierung prüft Munition und Reichweite innerhalb derselben Galaxie, bucht Munition atomar ab, und der Worker reduziert abgefangene Lanzen anhand verfügbarer Screens am Ziel. Bestehende Regeln sind in `docs/implementation/DECISIONS.md` ORB-031 festgehalten. Terra-Artillerie/Raketen und ihre Reichweiten-, Munitions-, Ziel- und Gegenmaßnahmeregeln fehlen; diese Werte benötigen einen freigegebenen versionierten Terra-Vertrag.

K11 Source-Audit: Orbit-Reisezeit verwendet die langsamste Schiffsklasse und summiert Treibstoff/Fracht; `tests/test_orbit_rules.py` deckt dies einschließlich ungültiger Flottenwerte ab. Terra bleibt geländekostenbasierte Wegsuche ohne Einheiten-Geschwindigkeiten. Geschwindigkeiten, Reichweite, Treibstoff und Kompatibilitätsregeln für Terra wurden nicht erfunden. Beide IDs sind `partial`. Traceability bleibt 344/344 synchron.

## K14: Terra-/Orbit-Verteidigung getrennt

K14-Audit bestätigt den Terra-Schildwall und Fraktionsboni sowie auf Orbit-Ebene eine stationäre Verteidigungsplattform und eine separat gewartete Station mit kapazitätsbegrenzter Garnison. Code, UI und integrierte Regression decken Verteidigungsauflösung und Station-Ausbau/Wartung/Einsetzen/Rückholen ab. Terra-Türme, Fallen, Verteidigungsslots, Strukturschaden und Reparatur haben weiterhin keinen freigegebenen Regelvertrag. K14 ist teilweise umgesetzt; keine Werte ergänzt.

K14-UI-Nachlauf: `tests/frontend.test.cjs::orbit station defense renders capacity, upkeep, deployment and withdrawal controls accessibly` prüft Stationsstatus/Kapazität, Bau-/Wartungsaktionen, Escaping, aktive Garnisonsentsendung, Rückholung und Command-Wiring. Frontend: 63/63; ESLint und `node --check static/app.js` bestanden.

## K13 / Schlachtvorlagen — Orbit-UI-Abdeckung

Ein Frontendregressionstest prüft die Orbit-Vorlagenauswahl nach Flotten-/Werfttyp, escaped IDs und Namen, Speichern/Laden/Löschen-Buttons und die zugehörige Command-Bindung. Terra-API- und Orbit-Domainregressionen belegen Speicherung, Scope und Idempotenz bereits. Neu: Frontend 64/64, ESLint und JS-Syntaxcheck bestanden. Vorlagen laden Aufträge; sie planen oder entsenden sie nicht automatisch.

K14-Fehlerkorrektur: Stationsausbau war im UI anklickbar, obwohl die Domain Schiffbauforschung sowie ausreichendes Erz/Äther verlangt. `orbitStationMarkup` deaktiviert den Ausbau nun bei fehlender/laufender Forschung, Ressourcenmangel oder bereits laufendem Stationsbau und zeigt den jeweiligen Grund. Frontendregression deckt alle vier Sperrfälle; Frontend 64/64, ESLint und JS-Syntaxcheck bestanden.

K14-Servergrenze: Der integrierte Orbit-Mehrspielertest füllt eine Stufe-1-Station auf genau 100/100 und bestätigt, dass der nächste Einsatz vor Ressourcenabbuchung abgelehnt wird. Beide Bestände bleiben unverändert. Vollständige Python-Suite: 400 bestanden, 218 bedingt übersprungen, eine vorhandene Warnung (1189.82 s); Ruff, Black-Check (48 Dateien), strict mypy (32 Quelldateien) bestanden.

## T01 Backup-Status und Restore-Probe — 2026-11-11

`deploy/backup.sh` erstellt ein restriktiv berechtigtes PostgreSQL-Custom-Format-Dump, prüft dessen Archivliste mit `pg_restore --list`, benennt erst danach die `.partial`-Datei um und aktualisiert `backup_status`. CI prüft einen aktuellen Zeitstempel und führt einen separaten Restore-Schritt aus. Ein isolierter PostgreSQL-18-Lauf am 2026-11-11 bestätigte Dump-Erstellung, Archivprüfung und Zeitstempel (12 Sekunden alt); die Testdatenbank, das Netzwerk und Testcontainer wurden entfernt.

Die laufende Compose-Datenbank ist Schema 14. Dort entstanden zwei neue Dumps (`fur-20261111T202532Z.dump`, `fur-20261111T202609Z.dump`), die `pg_restore --list` bestanden; das Status-UPDATE scheiterte erwartungsgemäß, weil die Tabelle `backup_status` in diesem Altbestand fehlt. Keine Migration wurde ausgeführt. T01 bleibt `partial`: Zeitplanung, genehmigte Rotation/Aufbewahrung und vollständige Betriebsabnahme sind offen.

T01 scheduling follow-up — 2026-11-11: `compose.yaml` now has an opt-in `backup-scheduler` under the `ops` profile. It immediately invokes the same validated backup script and repeats at configurable `BACKUP_INTERVAL_SECONDS` (default 86400; accepted range 3600–2592000). It restarts after failures. `README.md` documents start/log/stop. Compose config with default and `.env.example`, shell syntax, and rejection of interval 3599 (exit 2) passed. No retention deletion was invented; T01 remains partial. The scheduler was not started against the persistent schema-14 database because its missing `backup_status` table would cause repeated failed attempts.

## WAR-003 / K14: Terra-Verteidigung — Fortschritt nach Gefechtsintegration

`FUR-3-TERRA-DEFENSE-1` bleibt ein vorläufiger, digest-addressierter COMBAT-4-Vertrag. Er definiert Geschütz, Schild, Minenfeld und Gefechtsbunker mit eigenen Kosten, Voraussetzungen, Slots, Integrität und Reparatur. Serverseitiger Bau und sichere Reparatur sind an aktive Eigentümerkolonie, Ressourcen, Voraussetzungen und Idempotenz gebunden; laufende Angriffe sperren Reparaturen.

Kinetikgeschütze, Aegis-Emitter und Bunker werden in normalen Spieler- und ACS-COMBAT-4-Runden als getrennte Strukturprofile aufgelöst. Minenfelder würfeln deterministisch mit dem gepinnten Missionsseed, höchstens einmal je Mission, verbrauchen bei Erfolg eine Mine und wenden den festgelegten Angreifer-Modifikator an. Das Replay hält Eingangs-/Restintegrität, Mine und Regel-Digest fest; die Verteidigerkolonie wird innerhalb derselben Transaktion aktualisiert. UI-Karten und Build-/Repair-Buttons befinden sich in der Gebäudeoberfläche.

Gezielte Tests: 19 bestanden, 4 PostgreSQL-Adapterfälle mangels `FUR_TEST_POSTGRES` übersprungen. Der zusätzliche echte ACS-COMBAT-4-Spielerangriff besteht auf SQLite (1); sein PostgreSQL-Adapter wurde mangels `FUR_TEST_POSTGRES` übersprungen. Frontend 69/69, ESLint und JS-Syntax bestehen. ACS-Berichte enthalten jetzt ebenfalls den Mine-/Integritätsblock aus dem gespeicherten Replay, und die UI übersetzt interne Strukturprofile in Anzeigenamen. Abgedeckt sind Resolver, ACS-Wings, deterministische Minen, persistierter normaler PvP-/ACS-Schaden und Replay, Regel-Pins, Idempotenz und Schutz während eines Angriffs. Balance, die lesende COMBAT-4-Gefechtsprobe verwendet jetzt denselben Intel-gepinnten Verteidigungsstack in allen 16 Szenarien; Browser-/Geräte-/Barrierefreiheit, Übersetzungen und breite Multiplayer-/PostgreSQL-Abnahme bleiben offen; der Status bleibt `partial`. FUR-2 und persistente Datenbanken wurden nicht geändert.
