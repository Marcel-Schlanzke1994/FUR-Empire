# FUR EMPIRE — DURCHGÄNGIGE IMPLEMENTIERUNGSROADMAP

**Verbindlicher Ausführungsmodus:** Der Coding-Agent bearbeitet sämtliche Epics bis alle lokal möglichen Feature-IDs implementiert und nachgewiesen sind. Nach jedem Epic automatisch nächstes Epic starten; kein Abbruch, nur weil eine Demo läuft. Keine Erfolgsmeldung ohne reproduzierbare Tests. Externe Käufe, Livefreigaben oder fehlender Zugriff bleiben Owner-Handoff, sie dürfen nicht vorgetäuscht werden.

## 0. Orchestrierung und Beweisführung

1. Scanne Repository, `git status`, Sprache/Version, Server, DB, Migrationsstand, bisherige Tests und CI. Öffne die vorhandene FUR-2-Anwendung lokal. Dokumentiere tatsächliche Features in `AUDIT_CURRENT_FUR2.md`; die Spielanleitung ist Dokumentation, kein Funktionsbeweis.
2. Prüfe jedes Item in `spec/FEATURES.json`. Erzeuge `TRACEABILITY.md`, `PROGRESS_LOG.md`, `RELEASE_CANDIDATE_REPORT.md`, `OWNER_HANDOFF.md` und `docs/ADR/`. Für jedes Feature: `id | code | migration | endpoint | screen | policy | tests | manual QA | docs | status`.
3. Erhalte bestehende Funktion und Daten; keine Löschung/Überschreibung der Originaldaten. Backup und Restore nachweisen **vor** Schemaänderungen; migrationsgetriebener, testbarer Umstieg auf Multiworld.
4. Technischer Standard: bestehender FastAPI/Python-Stack, soweit Audit bestätigt; PostgreSQL im gemeinsamen Betrieb; deterministischer Eventworker, migrationsgeschützte Weltentitäten, originale FUR-Assets. Keine 1:1-Übernahme von Fremdcode oder lizenzierten Grafiken.
5. Alle `spec/FEATURES.json`-IDs sind die Arbeitsqueue. P0/P1/P2 sind **Reihenfolge**, keine Erlaubnis zur Auslassung von P2. Jeder Epic wird `implemented` → `verified`; ein Teilbereich mit unerledigter UI gilt nicht als fertig.

## Epic-Plan (E00–E21): Alle Epics ausführen

### E00 — Ist-Audit, Assets und Lizenz-Manifest
**Depends:** —. **Implementierung:** laufenden Code aufstöbern, Git-Branch/Backup, Datenbestand anonymisiert inspizieren, Schnittstellen inventarisieren, neun Referenz-Repositories mit Quellenregister und Lizenzprüfung erfassen, Bestand der FUR-2-Anleitung absichern. **Ergebnisse:** `AUDIT_CURRENT_FUR2.md`, Dependency-Lock, originaler Stand als Git-Tag, Secret-Scan, Datenmigration-Plan. **Gate:** Backup lässt sich isoliert wiederherstellen; kein geheimer Token committed; jeder dokumentierte Ist-Teil mit Testbefund oder `unverified` gekennzeichnet.

### E01 — Reproduzierbare Infrastruktur und CI
**Depends:** E00. **Implementierung:** modularer Service, PostgreSQL/Redis optional, isolierte Worker, Alembic, Docker Compose dev/staging, Konfiguration aus Env, Health/Ready, strukturierte Logs, CI, Lint, Format, Types, Test, Dependency Scan, SAST, E2E-Skelett. **Gate:** Clone→Compose→Migration→Seed→Login→Health in neuem Verzeichnis; wiederholte Starts ohne Datenverlust; kein Produktionsservice ungeschützt nach außen.

### E02 — Identity, Sitzungen, Welten und Datenschutz
**Depends:** E01. **Implementierung:** Registrierung, E-Mail-Verifikation, Passwort-Reset, Argon2id, TOTP mit Replay-Schutz, Recovery Codes, Rate Limits, Session Revocation, globales Konto vs `world_player`, Sprachauswahl, Nutzerdatenexport/Lösch-Workflow, Admin-RBAC. **Gate:** fremde Welt kann nicht gelesen/geschrieben werden; 401/403/404 kontrolliert; Admin benötigt 2FA in Prod-Konfiguration.

### E03 — Bestehende FUR-2-Regeln, Ledger und Migration
**Depends:** E02. **Implementierung:** Regelkatalog `FUR-2` als unveränderliche Baseline, Startbestände, 8 Gebäude, 3 Forschungen, 3 Einheiten, 5 Direktiven, Produktion, Restbruchteile, Lager, Reserve, Kosten, Limits, Trade, Score; Ressourcen-Ledger und Einmal-Claims. **Gate:** FUR-2 Fixtures exakt wie dokumentiert; Zeitsegmentierung über Event-/Urlaubsgrenzen; kein negativer Bestand, keine Doppelprämien.

### E04 — Game-Clock, Eventworker, Missionen und Zeitverwaltung
**Depends:** E03. **Implementierung:** Scheduler, Event-Outbox, idempotente Commands, Leases/Retry/Dead Letter, UTC, Bau/Forschung/Truppen, 30 Missionslimit als FUR-2-Kontingent, Anmarsch/Rückmarsch, Queue-Umsortierung/Kündigung mit Rückerstattungsregel. **Gate:** künstlich 100-fach denselben Auftrag wiederholen und einen Worker abstürzen lassen: genau eine Wirkung; FIFO bei gleicher Zeit mit Event-ID-Tiebreak.

### E05 — Terra-2D-Welt, Karten, Gelände und Kolonien
**Depends:** E04. **Implementierung:** vorhandene 64×64/104 Posten schützen; Welt-Seed und Karten-Generator für neue Welten, Regionen, Terrain, Fog-of-War, Karte 20×20/Zoom/Pan/Filter, Spieler-/Allianzmarker, eigene vollständig ausbaubare Mehrkolonien, Kachelreservierung, Standortsuche, Relocation/Abandon unter Schutzregeln, interkolonialer Transport. **Gate:** 100 parallele Kolonisten auf gleiche Kachel→eine Reservierung; Seed reproduzierbar; alte Kolonien unverändert.

### E06 — Terra-Ökonomie, Energie, Bau- und Techgraph
**Depends:** E05. **Implementierung:** alte Gebäude erhalten, neue Gebäudetypen/Spezialgebäude, defensives Upgrade, Techgraph mit Abhängigkeiten, Forschung je Kolonie/imperiumsweit, Warteschlangensteuerung, Energiemodell, Kosten-/Zeit-Editor, Migration Max-Level von 10 in versionierte neue Regeln, market history. **Gate:** Voraussetzungen auch bei parallelen Requests geprüft; Kosten, Energie, Slots und Cap über Regeln konfigurierbar.

### E07 — Terra-Einheiten, Verteidigung und Kampf-Engine
**Depends:** E06. **Implementierung:** mindestens 12 Rollen-Einheiten plus 3 FUR-2-Grundeinheiten als migrationserhaltende Identitäten, Unit-Definitionen, konkrete Schilde/Panzerung/Kontra/Tempo, 6-Runden-Determinismus, Gelände und Gegenklassen, Rückzug, Belagerung, Spezialabwehr, Reparatur, Gefechtsberichte, Replay, Schlachtsimulator. **Gate:** identischer Seed→identisches Ergebnis, Replay rekonstruierbar, dry-run ohne Ledger-Effekt, keine aus dem Nichts entstandenen Einheiten.

### E08 — Spionage, Terra-Missionen, Konvois und Fernwaffen
**Depends:** E07. **Implementierung:** Sicht-/Intel-Levels, Spionage und Gegenaufklärung, Abfangmechanik, Angriffe/PvE/PvP/Erobern/Garnison/Transport/Kolonisieren, koordinierte Operationen, Expedition, Handelsschutz, Artillerie/Fernwaffen, Bergung/Wrack, Truppen-Speeds/Fracht/Fuel, Vorlagen, Reisen/Recall. **Gate:** Revalidierung bei Ankunft, geschützte Gegner nicht angreifbar; keine verborgenen Daten in API; Rückkehrende Güter korrekt verbucht.

### E09 — Diplomatie und vollständige Allianzen
**Depends:** E08. **Implementierung:** bestehende Allianzen migrieren; Rollen/Policies, Einladungen/Anträge/Kicks/Führung, NAP, Frieden, Krieg, Kriegsziele, Allianz-Ranking, Depots, Hilfeaktionen, gemeinsame Angriffe (ACS), gemeinsames Verteidigen, Forum, Pinnwand, Treasury/Spenden/Projekte. **Gate:** keine Selbstgenehmigung kritischer Rollen; Allianz-/Weltgrenzen und Pakte korrekt in laufenden Missionen; keine Doppelentnahme aus Kasse.

### E10 — Sozial, Berichte, Komfort, Moderation
**Depends:** E02,E09. **Implementierung:** Chat Welt/Allianz/Privat, Postfach, Suche, Freund/Blocklisten, Notizen, Berichtsfreigaben, Statusfilter, Meldungen, Moderations-Warteschlange, Mutes/Bans/Appeals, Profil/Statistik, sicherer BBCode, Hilfeseiten. **Gate:** XSS-Suite, Berechtigung für jede Nachricht, Nachrichtensicht nur für Berechtigte, Rate Limits, Audit.

### E11 — NPC-Lebenswelt, Questlinien und Expeditionen
**Depends:** E07,E08,E09. **Implementierung:** begrenzte NPC-Spawns, Verteidigungsbudgets, KI-Fraktionszustand, PVE-Raids, Bossphasen, Zitadellenfortsetzung, tägliche/wöchentliche Quests, Erfolge, Questketten, Drop-Tabellen, Reward-Escrow, Comeback-System. **Gate:** NPCs überschreiben nie Spielerkolonien, Belohnungen nur einmal, Spawns verlieren bei Weltvollstand keine Daten, keine endlose Bonusinflation.

### E12 — Orbit-Karte, Freischaltung und Kolonien
**Depends:** E06,E11. **Implementierung:** eigenen FUR-Orbit statt OGame-Kopie, Sternensystem-Generator, reservierte Slots, Orbitalzugang über Forschung/Kampagne, Planet/Satellit/Mond/Station, Energie, Äther/Fuel, orbitaler Bau/Tech/Slots und intertheatralische Frachtrouten, Orbitkolonien. **Gate:** kein doppelter Slot, kein kostenloser Terra↔Orbit-Waren-Teleport, kein Welt-Leak.

### E13 — Flotten, Orbitschlachten, Mondsystem und Exploration
**Depends:** E12,E07,E08. **Implementierung:** mindestens 14 eigene Schiffstypen, Schiffswerft, Flottendesigner, Bewegung/Treibstoff/Fracht, Missionen Attack/Transport/Deploy/Colonize/Espionage/Intercept/Expedition/Salvage, Verbandsflotten, Trümmer/Mond-/Stationserzeugung, Sensorphalanx/Sprungtor/Repair, Belagerung und Orbital-PvE. **Gate:** Flotten-Race und Missions-Idempotenz, dieselbe reproduzierbare Kampf-Engine, keine negative Fuel/Cargo-Menge.

### E14 — Handel, Inventar, Handwerk, Helden/Doktrinen
**Depends:** E06,E09,E13. **Implementierung:** bestehende Börse/Markt, Marktchronik, limitierte Händler, Produktionsrezepte, Items/Inventar und Lager, Crafting, Bergung, Commander-Talente und Fraktionsdoktrinen, kosmetische Abzeichen, fairer Respec, Marktmanipulationskontrollen. **Gate:** alle Waren- und Itemtransfers im Ledger, kein Pay-to-win, kein Duping durch Cancel/Accept.

### E15 — Events, Welt-Simulation, Seasons und Ranglisten
**Depends:** E11,E13,E14. **Implementierung:** bereits vorhandene Live-Boni/Saisons beibehalten; separate Saisonwelten und Archiv, Event-Vorlagen (NPC-Invasion, Konvoi, Weltenboss, Orbit-Anomalie, Allianzziele), Regelversions-Snapshots inklusive Formel-Hash, Bestenlisten, Hall of Fame, neue Endgame-Ziele, Benachrichtigungen. **Gate:** Reset ausschließlich in ausdrücklich saisonaler Test-/Saisonwelt; permanente Welt unverändert; Score auditierbar.

### E16 — Admin, GameMaster, Welteditor, Anti-Abuse
**Depends:** E01–E15. **Implementierung:** Owner/Superadmin/Admin/GM/Moderator/Support-RBAC, vier-Augen-Adminaktionen, Regel-Preview/Publish, Karten-/NPC-Editor, Nutzer-/Kolonie-/Markt-/Missions-Support, Event/Saisonmanager, Ban/Appeal, Audit/Errors, automatische Integrity Checks, Anti-Bot, Multiaccount-Review ohne IP-only Sperre. **Gate:** Rollen-Matrix negativ testen, manipulative Admin-Events auditieren, keine destruktive Live-Aktion ohne Freigabe.

### E17 — Design-System, Screens, Mobile und i18n
**Depends:** E02–E16. **Implementierung:** eigene Cyber-Gold-Assets, originales Logo/Icons, vollständige Screens und Formulare für alle Systeme, Lade-/Leer-/Fehlerzustand, responsive Touch + Tastatur, WCAG 2.2 AA Ziel, vollständige Locale-Kataloge DE/EN/VI/ES/TR; keine inaktiven Demo-Buttons. **Gate:** UI-Screen-Inventory jedes Features durch Playwright, 320px bis 1920px, Tastatur-Navigation und Textkontrast; 100% i18n-Schlüsselabdeckung.

### E18 — Realtime und Integrationen
**Depends:** E09,E10,E17. **Implementierung:** SSE/WebSocket mit Auth, Scope, Replay-Last-ID, Polling-Fallback, systeminterne Notifications, optional deaktivierte Discord-Integration mit opt-in und separatem Bot-Token aus Env; E-Mail via lokalem Mailcatcher und SMTP-Adapter; Webhook-Signatur/Retry. **Gate:** World-/Alliance-/Private-Events nie an Unberechtigte; reconnect keine Datenlücken; kein Live-Webhook beim Test.

### E19 — Security/Privacy/Operability Hardening
**Depends:** E01–E18. **Implementierung:** Threat Model, Input/Output/CORS/CSRF/Auth-Security Suite, Secretscheck, Session-Rotation, Replay-/Rate-/Anti-Duping-Suite, Datenexport/Löschprozess, TLS-Konfiguration, Monitoring, Backup-Rotation, Restore-Drill, Incident-Runbook, Privacy- und Legal-Placeholder. **Gate:** alle kritischen Sicherheitsprüfungen grün, kein unverschlüsselter Secret im Repo, Restore vollständig.

### E20 — Vollständige E2E-, Performance- und Balancing-Abnahme
**Depends:** E19. **Implementierung:** 2–10 Testaccounts/2 Welten/Terra+Orbit, komplette Journey vom Login bis Allianzboss/Saisonarchiv, Regression historische FUR-2-Daten, 30-Minuten-Lastlauf, Worker-Killtests, Fehler-Injektion, Modell-/Balance-Simulation, DB-Integrität, Browser-Matrix, Accessibility, Lizenz-/Asset-BOM. **Gate:** jede Feature-ID `verified`; kein offener P0/P1-Sicherheitsdefekt, keine bekannten Data-Loss-Bugs, reale Testberichte.

### E21 — Deployment-ready Übergabe ohne Serverkauf
**Depends:** E20. **Implementierung:** staging/prod Compose oder IaC, Reverse Proxy TLS, Env-Examples und Secrets-Setup-Dokument, One-Command local/staging, Datenbankupgrade/Rollback, Backup+Restore, Release-Tag, Monitoring-Runbooks, `OWNER_HANDOFF.md` für Domain/VPS/DNS/SMTP/Betreibertexte, produktive Erstkonfiguration, Launch-Gates. **Gate:** frische lokale Staging-Installation nur aus Repo+Dokumentation möglich; öffentlicher Livebetrieb bleibt ausdrücklich deaktiviert.

## Nach jedem Epic: obligatorische Gates

1. `ruff check .` (oder äquivalent), statischer Typecheck (mypy/pyright), Dependency-Lock aktualisiert.
2. Domänentests + komplette Regression + neu angelegte Negativfälle grün; Playwright-Smoke für alle betroffenen Seiten.
3. Migration Upgrade + Datenbestand-Vergleich + falls nötig getestete Restore-Strategie, keine gefährliche automatische Down-Migration.
4. Feature-ID in `TRACEABILITY.md` nur mit realen Belegen aktualisieren. `PROGRESS_LOG.md` um Befehle, Commit, Tests, neue Risiken ergänzen.
5. Neue Architekturentscheidungen als `docs/ADR/NNNN-*.md`; bei offensichtlichem Bug vor Weiterbau reparieren.
6. Nächstes nicht verifiziertes, abhängigkeitsfreies Epic beginnen. Falls ein Werkzeug quota-bedingt beendet, dokumentiere exakten Resume-Checkpoint in `RESUME_STATE.json`, damit ein Folgeagent fortsetzt. Keine Zusage, außerhalb einer aktiven Agent-Session endlos weiterzuarbeiten.

## Abnahme ohne Interpretationsspielraum

`verified = source file exists + callable server behavior + DB consistency + authorization + locale + UI route + automated happy/negative/race test + docs + evidence`. `blocked_external` ausschließlich Domain/VPS/SMTP-Realdaten, rechtliche Texte, Eigentümerrechte und bezahlte Dienste. Keine Dummy-Implementierung zählt als feature complete.
