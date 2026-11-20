# FUR EMPIRE — DAS VOLLSTÄNDIGE SPIELKONZEPT & AGENTEN-MASTERPAKET

**Stand:** 06.11.2026 · **Status:** vollständige Spezifikation zur **Umsetzung**; ausdrücklich **kein** bereits fertig programmiertes neues Spiel.

## Was du bekommst

Ein ausführliches, eigenständiges FUR-Strategiespiel-Konzept mit **344 einzeln prüfbaren Funktionsanforderungen**, 22 Entwicklungs-Epics (E00–E21), Regeln für Terra und Orbit, neu entworfenen Gebäuden/Technologien/Einheiten/Schiffen, Betriebs-, Sicherheits-, Test- und Lizenzkonzept, einen direkt einsetzbaren Coding-Agent-Prompt, eine maschinenlesbare Featureliste, automatischen Paketvalidator und ein Resume-System für längere Agentenläufe.

**Ausgangslage:** Die vom Besitzer übergebene Datei `SPIELANLEITUNG.md` beschreibt FUR-2. Sie belegt Features dokumentarisch, aber ohne den aktuellen FUR-2-Quellcode **nicht**, dass sämtliche Funktionen in der aktuellen App zuverlässig laufen. Der Agent muss zuerst den echten Code auditieren und die Migration sicher planen. Solange der Code fehlt, kann der Agent ein eigenes System in getrenntem Verzeichnis entwickeln, aber keine erfolgreiche Migration behaupten.

## So setzt du den Coding-Agenten direkt ein

1. Entpacke das ZIP-Paket und lege die Dokumente im echten aktuellen FUR-2-Projekt ab (oder öffne das Paket und das Projekt gemeinsam im Agent-Workspace). Achte darauf, vorhandene `AGENTS.md`, Configs und Nutzerdateien nicht ungeprüft zu überschreiben — bei vorhandener Datei Inhalte sorgfältig zusammenführen.
2. Gib dem Coding-Agenten den **kompletten Inhalt** von **`agent/AGENT_START_PROMPT.md`**. Alternativ reiche das gesamte Paket plus den Auftrag „Lies AGENT_START_PROMPT“ ein.
3. Der Agent prüft Paket/Code, erstellt einen sicheren Entwicklungsbranch, initialisiert Beweismatrix und erledigt E00–E21. Er arbeitet alle Feature-IDs ab, nicht nur P0 oder eine Demo.
4. Nach jedem Epic prüft der Agent Code, Datenbank, UI, Tests, Sicherheit und Lizenz. Der Status `verified` wird nur mit realem Nachweis vergeben. Falls Agentenlaufzeit/Toolbudget endet, muss er `RESUME_STATE.json` speichern; anschließend kann ein neuer Agent mit `agent/RESUME_PROMPT.md` fortsetzen.
5. Nach vollständigem Offline-/Staging-Abnahmelauf erhältst du `RELEASE_CANDIDATE_REPORT.md` und `OWNER_HANDOFF.md`. **Nur** Domain, VPS/Root, echte SMTP-Zugangsdaten, Betreiberrechtliches, neue Produktionssecrets und ausdrückliche Livefreigabe liegen dann noch bei dir — sofern der Agent die Implementation tatsächlich abgeschlossen hat.

## Was jetzt als verbindliche Arbeitsunterlagen enthalten ist

| Datei | Zweck |
|---|---|
| `agent/AGENT_START_PROMPT.md` | **Direkt kopierbarer Komplettauftrag** |
| `AGENTS.md` und `agent/AGENTS.md` | Verbindliche Coding-Agent-Regeln, Sicherheits- und Statuskontrakte |
| `agent/BUILD_LOOP.md`, `agent/RESUME_PROMPT.md` | Kontinuierliche Abarbeitung, Fehlerbehandlung, Session-Fortsetzung |
| `docs/01_MASTER_GAME_DESIGN.md` | Gesamte Lore, alle Module, Spielverlauf, Terra und Orbit |
| `docs/02_TECHNICAL_CONTRACTS.md` | Architektur, Datenmodell, Commands, Eventengine, APIs, Regeln, Integrität |
| `docs/03_IMPLEMENTATION_ROADMAP.md` | 22 abhängige, ausführbare Epics mit konkreten Abnahme-Gates |
| `docs/04_SECURITY_OPERATIONS_LIVE.md` | Auth, Anti-Cheat, Privacy, Monitoring, Backups, Domain/VPS-Liveplan |
| `docs/05_TEST_STRATEGY.md` | Unit, Integration, Browser, Last, Race, FUR-2-Migration, Restore |
| `docs/06_SOURCE_LICENSE_REGISTER.md` | Alle **neun** Quellprojekte, Git-Commit, Lizenzbedingungen und Nutzungsstrategie |
| `docs/07_COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX.md` | Alle notwendigen Screens, Buttons, Zustände und Interaktionsanforderungen |
| `docs/08_GAME_MECHANICS_STATE_MACHINES.md` | Exakte Zustandsautomaten für Kampf, Worker, Markt, Kolonien, Events, Orbit |
| `docs/09_AGENT_ACCEPTANCE_AND_OWNER_HANDOFF.md` | Exakte Abnahme und späterer Eigentümer-Handoff |
| `docs/10_OWN_ASSETS_BRANDING.md` | Originale FUR-Designsprache und vollständiger Assetauftrag |
| `spec/FEATURES.json` | **344 Feature-IDs** mit Anforderungen/Akzeptanz/Evidenzstatus/Quellen/Priorität/Epic |
| `spec/FEATURES.csv` | Tabellenansicht aller Funktionen |
| `spec/FEATURE_INDEX.md` | Menschlich lesbare vollständige Funktions-Checkliste |
| `spec/EPICS.json`, `spec/IMPLEMENTATION_ORDER.md` | Maschinenlesbare Zuordnung zu den 22 Epics |
| `rulesets/FUR_2_REFERENCE_RULES.json` | Gemäß Anleitung festgehaltene historische FUR-2-Baselines |
| `rulesets/FUR_3_ORBIT_1_PROPOSED_RULES.json` | **Neue vorgeschlagene** Gebäude, Techs, Einheiten, Flotten und Gameplay-Caps |
| `scripts/validate_package.py` | Prüft Paketstruktur, 344 IDs, JSON und Secret-Muster |
| `scripts/prepare_traceability.py` | Erstellt initiale 344-Zeilen-Abnahmematrix ohne bestehende Dateien zu überschreiben |
| `reference/*` | Unveränderte FUR-2-Anleitung, 55-Punkte-Vergleich und 9-Repository-Analyse |

## Technische Designvorgabe

Die vorhandene Python/FastAPI-Basis wird **nur falls im echten Repository bestätigt** erhalten. Ziel: modularer Monolith, PostgreSQL in Multiuser-Betrieb, Worker/Scheduler, Redis optional, feste RuleSet-Hash-Versionen, transaktionales Ressourcenledger, deterministische Kampfreplays, REST API + SSE/WebSocket, Original-FUR-Frontend, Compose für offline/dev/staging und produktionsbereites Setup. Kein blindes Mischen von PHP-Engines.

## Recht und Sicherheit

Die neun Repositories sind Inspirations-/Architekturquellen, nicht automatisch lizenzfreier Copy-Paste-Code. Insbesondere CC BY-NC-ND, AGPL, GPL, unklare Legacy-Archive und fremde Spielgrafiken werden ohne ausdrückliche Lizenzstrategie nicht übernommen. Kein Domain-/Serverkauf, kein öffentlicher Upload, keine echten Zahlungen oder Benutzung alter, im Chat exponierter Tokens ohne klare Betreiberfreigabe.

## Echte Fertigstellung

**Nicht:** schöner Startscreen, 80% abgeschlossen, Tests übersprungen, Demo mit Fake-Buttons.

**Sondern:** Alle 344 Initialanforderungen plus notwendige Unterfunktionen haben Code + UI + DB + Autorisierung + DE/EN/VI/ES/TR + Tests + dokumentierten Nachweis; mehrere Spieler und Welten samt Terra/Orbit, Allianzen und Saisons laufen wirklich; Container-Fresh-Install, Anti-Duping, Restore, Lasttest und Security Gate sind grün; ehrlicher Owner-Handoff liegt vor.

> Ein solches Projekt kann nicht durch einen einzelnen Prompt automatisch als bereits gebaut gelten. Das Paket definiert einen prüfbaren Ausführungsprozess. Ob ein Coding-Agent mehrere Stunden/Tage über Sitzungen hinweg arbeiten kann, hängt von seiner konkreten Ausführungsumgebung ab. Benutze `RESUME_STATE.json` für Kontinuität.
