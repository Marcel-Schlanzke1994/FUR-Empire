# FUR EMPIRE — GESAMTKONZEPT, FEATUREPLAN UND AUTONOME AGENTEN-ROADMAP

**06.11.2026 — Verbindliche Spezifikation, noch kein fertig implementiertes Spiel.**

Dieses Einzeldokument bündelt das Gesamtkonzept. Die maschinenlesbaren Feature- und Regeldateien sowie die Arbeitswerkzeuge liegen separat im ZIP-Paket.



---

<!-- QUELLDOKUMENT: 00_START_HIER.md -->

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



---

<!-- QUELLDOKUMENT: docs/01_MASTER_GAME_DESIGN.md -->

# FUR EMPIRE — KANONISCHES GAME-DESIGN-DOKUMENT

**Version:** Master-Blueprint 1.0 · **Stand:** 06.11.2026 · **Genre:** asynchrones Multiplayer-Strategie-Browsergame · **Ziel:** dauerhaft spielbare Multiworld-Plattform mit PvP, PvE und zwei Theater-Ebenen.

## 0. Projektziel, Quellen und Verbindlichkeit

FUR Empire ist kein OGame- oder Tribal-Wars-Nachbau, sondern eine neue Cyber-Fantasy-/Sci-Fi-Strategiewelt. Es kombiniert eigene Landkolonien, frei belegbare Territorien, technologische Entwicklung, taktische Armeen, orbitale Expansion, Diplomatie, Expeditionen und Welt-Events. Die Grafik ist **eigenständig** (Onyx, Gold, Cyan, holografische Karten, originelles FUR-Branding). Originalgrafiken, exakte Texte, geschützte Logos und Charaktere anderer Spiele sind ausgeschlossen.

**Basis-Fakten aus der vom Nutzer gelieferten FUR-2-Anleitung, noch code-ungeprüft:** Genesis-Oberfläche, FUR-2-Regelkatalog, 64×64-Karte und 104 neutrale Außenposten, die drei Ressourcen Holz/Stein/Erz, 8 Gebäude (max Stufe 10), drei Technologien, drei Einheiten, Direktiven, PvP/PvE, Eroberung, Garnison, Rohstofftransport, Spielermarkt und neutraler Tausch, Allianzen, Diplomatie, drei Fraktionen, Chat/Postfach, Ranglisten, Saison, zeitgesteuerte Events, Urlaub, Admin, E-Mail/TOTP, SQLite lokal/PostgreSQL Docker, gesonderter Worker. **Diese Systeme nicht verwerfen, sondern gegen den echten Quellcode auditieren und migrieren.**

**Neue Produktentscheidung für den Neubau (nicht aus FUR-2 belegt):** Zwei ineinander greifende Theater: 1. **Terra**: 2D-Regionskarte, Außenposten, Landkolonien, Armeemärsche. 2. **Orbit**: freischaltbare Sternensektoren, orbitaler Bau, Flotten, Monde/Stationen, interstellare Missionen. Beide teilen Account, Allianz, Inventar, globale Fortschrittsdaten und marktbasierte Wirtschaft, besitzen aber unterschiedliche Regeln und Einheiten. Nicht die Benutzeroberfläche eines anderen Spiels kopieren.

## 1. Leitidee / Spielspaß / unverwechselbares Profil

- **Spielerfantasie:** Vom kleinen Kommandoposten zum vernetzten Cyber-Imperium; Territorien verteidigen, mit Verbündeten planen, Technologiepfade meistern, das Orbitalnetz kontrollieren und in Saisons sichtbar Geschichte schreiben.
- **Strategie statt Klickmasse:** Jede Einheit hat eine erkennbare Rolle, Reisezeiten sind taktisch relevant, Aufklärung hat Wert, Koordination verändert Ergebnisse, Schutzmechaniken verhindern Hoffnungslosigkeit.
- **Fairness:** Keine kaufbare Kampf- oder Produktionsmacht. Kosmetik-/Unterstützerfunktionen bleiben ohne aktiven Echtgeld-Zahlungsverkehr; Live-Payment ist vor Betreiberentscheidung nicht Teil der Freischaltung.
- **Immer etwas zu tun, ohne Zwang:** Offline-Fortschritt, Eskalation von NPCs, Forschungs-/Bauplanung, Expeditionen, optionale Clan-Ziele. Kein künstliches Bestrafungssystem für Abwesenheit.
- **Technischer Kern:** Server autoritativ; Browser darf nie Ressourcen, Schaden, Position, Zeit, Rechte, Missionsstatus oder zufälliges Ergebnis bestimmen.

## 2. Setting, Fraktionen, Weltgeschichte

**Ausgangslage:** Nach dem Zusammenbruch der alten Netzwerke existieren isolierte Städte in einem globalen Gitter von Geo-Sektoren. Die namensgebende FUR-Architektur verbindet Ruinen, Rohstoffknoten, Orbitaleinheiten und verschlüsselte Kommunikationsnetze. Die Zitadelle des Kerns bewacht den Zugang zum Orbit. Spieler sind Kommandanten mit eigenem Kommandosiegel.

**Bestehende FUR-2-Fraktionen unverändert bei Migration:** Pioniere (+10 Prozentpunkte Produktion), Wächterbund (+40% Schildwallverteidigung im PvP), Syndikat (60 statt 50% neutraler Rohstofftausch). Wahl einmalig je Welt; Einmalwahl nur über explizite Respec-Regel in neuen Weltmodi ändern. **Neu:** Jede Fraktion bekommt drei eigene Spezialtechnologien, zwei optisch einzigartige (mechanisch balancierte) Spezialeinheiten, eine einzigartige Diplomatie-/Wirtschaftsaktion und eine öffentliche Hintergrundkampagne. Keiner darf durch einen unendlichen skalierenden Bonus einen sicheren Sieg haben.

**NPC-Lager:** Kernwächter (defensiv), Plünderer (mobil), Archive (Forschung/Expeditionen), Schattenhändler (Handel), Orbitale Abtrünnige (spätes PvE). Verhalten deterministisch im Hintergrund simuliert, keine unkontrollierten Sprachmodelle für die Spielmechanik. Narrative Texte können kuratiert und lokalisiert werden.

## 3. Spielerlebenszyklus und Spiellandschaft

1. Landing: Informationen, Sprache, Datenschutzhinweise; Konto mit bestätigter E-Mail für öffentlichen Betrieb, sicherer Session und optional TOTP; Einwilligungen differenzieren.
2. Start: vorhandene FUR-2-Ressourcen **1.200 Holz, 1.000 Stein, 800 Erz**; erste Landkolonie; Einführung mit fünf existierenden Direktiven; Fraktionswahl bewusst, mit Vorschau.
3. Frühspiel: Produktion, Kommandobasis, Kaserne, Labor, drei Grundtruppen, erste PvE-Raids, Handel, Allianzsuche; visuelle Hilfen und PvP-Schutz.
4. Mittelspiel: zweite und weitere Kolonien, Aufklärungsinformationen, zusätzliche Einheiten und Forschungszweige, taktische Verteidigung, gemeinsam koordinierte Angriffe und Handelsrouten.
5. Endspiel Terra: Regionen sichern, Kernzitadelle überwinden, Allianzkrieg mit objektiven Zielen, NPC-Bedrohungen, Weltbosse und Sektorfronten.
6. Endspiel Orbit: Sprungfeld-/Orbittechnik freischalten, Raumstationen, Flotten, Expeditionen, Mond-/Orbit-Ressourcen, Flottenverbände und Weltraumkrieg. Hohe Voraussetzungen, aber keine exklusiv käufliche Macht.
7. Langzeitspiel: Dauerwelten mit bleibenden Erfolgen; getrennte optionale Saisonwelten mit regelkonformem Neustart; Saisonarchive, Hall of Fame, neue NPC-Konflikte und kosmetische Prestigeobjekte.

**Multiserver-Struktur:** `accounts` global; pro Welt ein `world_player` mit fraktionsspezifischem Fortschritt, Kolonien und Missionen. Spieler darf mehrere Welten nutzen, aber pro Welt nur einen regelkonformen Account. Saison- und Dauerwelt niemals versehentlich zusammenführen. Regionen-/Karteneinstellungen sind pro Welt versioniert.

## 4. Weltkarten, Kolonisation und Gebietskontrolle

### Terra-Karte

- Bestehender Welt-Standard für migrierte FUR-2-Welten: `64×64=4.096` Sektoren, Startbestand 104 neutraler Außenposten, Ansichtsfenster max 20×20; Koordinaten `(x,y)` 0-basiert im Backend, Benutzeranzeige einheitlich dokumentieren. Index `(world_id,x,y)` eindeutig.
- Terrain: Ebene, Wald, Sumpf, Gebirge, Fluss/Wasser, Ruinen, Pässe, Industriezone, Ödland. Begehbarkeit, Migrationsregel, Produktionsmodifikator und Sichtreichweite aus `terrain_rules` statt aus UI-Text; kein Speichern von Bild-Farben als Autorität.
- Welt-Seed reproduzierbar; Spawnpunkte mit Mindestabstand, erreichbaren Ressourcen und Anfängerzonen; keine unlösbar isolierten Startbasen. Ein seed-basierter Generator kann mehrere Welten erzeugen. Admin kann Previews sehen, ohne Live-Welt zu überschreiben.
- Nebel des Krieges: `unexplored / observed_stale / currently_visible`; eigene und Allianzaufklärung nur im Rahmen permissions; keine gegnerischen Militärstärken offenlegen ohne Informationsquelle. Regelbasierte Aufklärung mit Zeitstempel, gefälschten oder veralteten Informationen als im UI erkennbare Unsicherheit.
- Kartenwerkzeuge: Filter (NPC/Spieler/Allianz/Gefahr/Rohstoffe/Missionen), Kachel-Inspektor, Kartenmarker, Spielerfavoriten, Koordinatensuche, Wegvorschau, Zugänglichkeits-Listenansicht, mobile Touch-Steuerung.
- Regionen und Sektorkontrolle: Grenzen/Frontlinien aus Besitz abgeleitet; regionale Ziele, Sektor-Festungen, Kontrollpunkte, begrenzte Boni, Siegpunkte, Konvoi-Routen; keine unbegrenzte exponentielle Aufsummierung von Außenpostenboni.
- Neutraler Nachschub: Neutrale unbesetzte Posten generieren Bestand/NPC-Verteidigung bis definierte Höchstwerte und neue PvE-Posten entstehen nur auf erlaubten freien Sektoren; **niemals** eroberte Spielerposten heimlich überschreiben. Spawn- und Ressourcenbudgets pro Region/Welt. Test: Eine voll besetzte Karte führt zu transparenter Sättigung und neuen Weltstarts, nicht zu Datenverlust.

### Mehrkolonien-System (neu)

- Erste existierende Kolonie bleibt bestehen. Spieler können in freien geeigneten Sektoren weitere **eigene voll ausbaubare Kolonien** gründen; separate Lager, Produktion, Bauten, Garnisonen, Queue-/Missionsslots und lokale Verteidigung; gemeinsamer Account, Allianz und Imperiumspunkte.
- Default-Grenzen für neue Welten: maximal 5 Terra-Kolonien ohne Tech; Forschungen erweitern auf 12. Admin kann pro Welt andere Grenzen einstellen. Kolonisation nur über definierte Erkundung, Kosten, freien Zielsektor und Sperrfrist; Zielreservierung transaktional, `unique(world_id,x,y)` verhindert Doppelgründung.
- Kolonien umbenennen, als Hauptkolonie setzen, verlassen/umsiedeln mit Warnung; aktive Angriffe/Missionen und abhängige Garnisonen werden korrekt bearbeitet. Eine letzte Kolonie kann nicht irrtümlich aufgegeben werden.
- Interkolonialer Ressourcen- und Truppentransport, Transferlog, Kapazität, Reisezeit, Versorgungskosten, optional Handelsrouten mit täglichen Limits. Beihilfe an Allianzen möglich, aber keine Generierung durch Hin-und-her-Transfers.
- Außenposten (erobertes Gebiet) sind **nicht** automatisch voll ausbaubare Kolonien; Umwandlung nur über eine eigenständige teure Aktion und mit freiem Kolonieslot.

## 5. Wirtschaft, Ressourcen, Lager, Markt

### Historischer FUR-2-Vertrag – migrationsfest

- Ressourcen `wood`, `stone`, `ore` mit Startbeständen 1200/1000/800.
- **Bestehende Formel pro Ressource und Sekunde:** `(2 + 2 × zugehörige Rohstoffgebäudestufe) × (100 + 15 × Ingenieurswesen + Eventpunkte + 5 × eroberte Außenposten + Fraktionspunkte) / 100`. Bruchteile als Rest speichern, keine Rundungsverluste durch oftmalige API-Aufrufe.
- Depotkapazität je Rohstoff: `2000 + 2000 × Depotstufe`; Überlauf von Belohnung/Retouren ins **Reserve-Lager**, keine Warenvernichtung.
- Neutralbörse: min. 10 Einheiten, Standardrückgabe 50%, Syndikat 60%; Lager muss Ware aufnehmen können.
- Spielermarkt: maximal 10 offene Angebote; Menge je Seite 10–100.000, Gültigkeit 24h; Ware beim Einstellen in Escrow, nur einmal annehmbar, keine Selbstannahme; auslaufende/zurückgezogene Ware ins Reserve-Lager.
- Ohne aktive neue Weltregel die Werte einer migrierten Welt nicht still ändern. Neue Regeln für `ruleset=FUR-3` und höher gesondert versionieren.

### Neue Wirtschaft (FUR-3 und Orbit)

- Vier bestandsfähige Ressourcenarten: Holz, Stein, Erz, **Ätherkristall** (Orbit/Lategame; keine Echtgeldwährung); Energie ist ein **Kapazitäts-/Leistungswert**, kein handelbarer Lagerrohstoff. Versorgung und Treibstoff werden aus expliziten Rezepten/Äther abgeleitet, keine versteckte kostenlose Generierung.
- Produktion aus Zeitdifferenz `delta=max(0,min(now-last_produced_at,offline_limit))`, exakten Integer-/Decimal-Resten und zugehöriger Regelnversion; keine Client-Uhren. `offline_limit` default 30 Tage, aber Admin konfigurierbar.
- Produktionsverbrauch und Wartung nur bei ausdrücklich gekennzeichneten Spezialgebäuden; fehlende Energie deaktiviert priorisiert definierte Verbraucher statt negative Lager zu verursachen.
- Dauerhafte Außenpostenboni für neue Welten: **abnehmender Grenznutzen** statt linearer unbeschränkter Steigerung, z. B. `outpost_pct=min(40, 5*min(n,4)+2*max(0,n-4))`; diese **neue** Balance ist versionsgebunden. Gegenseitige Kartenkonkurrenz darf nicht Wirtschaftskollaps verursachen.
- Lager getrennt nach Kolonie; Reserve-Lager erhält Provenienz und hat klare Transfers; Transfer- und Kaufaktionen im Ledger mit `cause_id`, `actor_id`, idempotenter Buchung.
- Marktmodi: neutraler Soforttausch, direkte Spielerangebote, befristete Kauf-/Verkaufsorders, Allianzd epot (Name im Code ohne Leerzeichen), Handelsrouten, Markt-Transaktionshistorie, durchschnittlicher Kurs, globale Besteuerung pro Welt via Ruleset; alles auf Ressourcen mit Reservierungen und Transaktionen gestützt.
- Missbrauchsabwehr: Limits für Handel, Trades zwischen Konten, Marktpreisabweichungen und Multiaccount-Signale; Transparenz und manuelle Anfechtung, keine automatische Enteignung durch rein heuristische Signale.
- Händler-NPC, Auktions-/Vertragssystem und planbare Frachtrouten mit Stornierungs-/Rückgaberegeln. Keine Echtgeld-/Premium-Ressourcen als spielentscheidende Abkürzung.

## 6. Gebäude, Bauwarteschlangen und Infrastruktur

**Acht bestehende Gebäude beibehalten:** Kommandozentrale (Basis 150/120/80), Bioforst (75/50/20), Steinbruch (90/65/30), Erzraffinerie (100/90/45), Depot (120/100/50), Kaserne (130/110/90), Forschungslabor (120/150/130), Schildwall (80/160/70). In FUR-2 Zielstufe ≤10, Kosten `Basis × Zielstufe`, ein aktiver Bau je Kolonie, Mindestbauzeit 3s; Kommandozentrale reduziert Bauzeit.

**Zusätzliche Terra-Gebäude und Zweck** (Daten in `rulesets/` als echte `building_defs`, Preise beim Balancing verbindlich festlegen und versionieren):

| Neues Gebäude | Zweck / Freischaltung |
|---|---|
| Werkstatt | schwere Einheiten, Reparatur und Herstellung |
| Radarstation | aktive Sichtweite, Aufklärung, Gegenaufklärung |
| Militärakademie | Doktrinen, taktische Kommandos, Ausbilder |
| Logistikzentrum | Marschtempo, Handelsrouten und Fracht |
| Kraftwerk | Energieproduktion für spätere Infrastruktur |
| Forschungskomplex | fortgeschrittene globale Forschung |
| Verteidigungstürme | stationäre Abwehrslots |
| Artilleriebatterie | begrenzte Fernkampfabwehr und Missionen |
| Schildgenerator | temporäre/energieabhängige Befestigung |
| Reparaturdock | geborgene Einheiten und Gebäude reparieren |
| Handelskontor | erweiterte Markt- und Vertragsfunktionen |
| Allianz-Terminal | Allianz-Operationen und Depot |
| Raumhafen | Freischaltung der Orbit-Progression |
| Kolonieverwaltung | höhere Kolonielimits, Prestige/Fernverwaltung |
| Späherzentrale | Spezialaufklärung, Tarnung und Konter |
| Archivkern | mehrstufige Quests, PvE-Weltforschung |

**Neue Orbit-Infrastruktur:** Orbitalkommando, Ätherreaktor, Sternenwerft, Sensorphalanx, Sprungtor, Flottenhangar, Schildarray, Wrack-/Bergungsdock, Kolonisierungsmodul, Mondlabor, Orbitaldepot und Allianzanker.

Bauten haben definierte Anforderungen, Kostenkurven, Slots, Energiebedarf, Stufenlimits, Dauer, Rückbau-/Stornokosten, Reparatur und individuelle Grafik. FUR-3-Standard für neu eingeführte Gebäude: `cost(level)=ceil(base_cost × 1.35^(level-1))`, Levelcap standardmäßig 20, höhere Prestige-Stufen mit kosmetischem Status und moderaten abnehmenden Boni. **Alte acht Gebäude migrieren ohne sofortige neue Preise.** Bauqueues: eine aktive + bis zu 4 geplante Positionen je Kolonie (FUR-2-Live-Regel: eine aktive); geplante Aufträge reservieren Ressourcen erst beim tatsächlichen Start oder verbindlicher Reservierungsregel aus Snapshot, niemals doppelt. Umordnen, Stornieren, Teilrefund, Pause/Resume, Upgrade-Preview, Anforderungen und ETA.

## 7. Forschung, Technologiebaum, Fraktionen, Doktrinen

**FUR-2-Basistechnologien:** Militärtaktik (+15% Angriff/Verteidigung je Stufe, Basis 70/90/150), Logistik (+10 Beutekapazität je Einheit und Stufe, Basis 130/70/100), Ingenieurswesen (+15 Prozentpunkte Produktion je Stufe, Basis 100/140/90). Pro Kolonie eine lokale Forschung, `12 × Zielstufe` Sekunden, `Basis × Zielstufe`. FUR-2-Werte bleiben über Regelversion erhalten.

**FUR-3-Metaforschung:** Technologiegraph mit `prerequisites`, `max_level`, `scope=colony|world_player`, `unlocks`, Kosten, Zeit, Produktionswirkung, Erklärtext und Live-Regelversionsschlüssel. Zusätzliche Knoten: Erkundung I–V; Kartografie I–V; Bauautomation I–V; Rekrutierung I–V; Ballistik I–V; Defensive Systeme I–V; Sensorik I–V; Tarntechnik I–V; Gegenaufklärung I–V; Feldmedizin I–V; Reparatur I–V; Allianzkoordination I–V; Kolonisation I–V; Energiemanagement I–V; Ätherverarbeitung I–V; Raumfahrt I–V; Flottenantrieb I–V; Orbitalwaffen I–V; Mondtechnik I–V; Sprungtechnik I–V; Diplomatische Netzwerke I–V; Spezialdoktrin je Fraktion I–V.

Globale Forschungen haben eine eigene Account/Welt-Queue und lassen vorhandene koloniebezogene FUR-2-Forschung unangetastet. Jede UI zeigt Baum, Voraussetzungen, Effekte, Veränderung zur nächsten Stufe, Abbruchfolgen. Zyklen im Graph werden durch automatische Regelnvalidierung verhindert. Keine Forschung über Limits/ohne Kosten.

## 8. Streitkräfte, Einheitenrollen und Fertigung

**Bestehende Truppen:** Ranger (12 Kampfkraft, 2s, Kaserne 1, Kosten 35/15/25), Wächter (28, 4s, Kaserne 2, 50/40/60), Sturmmech (70, 7s, Kaserne 3, 100/90/140); pro Auftrag 1–100, eine aktive Trainingsqueue je Kolonie.

**Neue Terra-Einheitendefinitionen:** Späher (Aufklärung), Saboteur (Gegenmodule), Sanitäter (Heilung/Nachbereitung), Schilddrohne (Gruppenschutz), Scharfschütze (Konter leichter Einheiten), Belagerungsroboter (Festungszerstörung), Artillerieplattform (Reichweite), Logistikkonvoi (Fracht ohne Kampfbonus), Ingenieurtrupp (Reparatur/Bergen), Interceptor-Drohne (Schnelligkeit/Flugabwehr), Kommandantenwache (Garnison), Titan-Koloss (späte schwere Einheit). Zusätzliche fraktionsspezifische Einheiten (je zwei) und zeitgebundene Event-NPC-Truppen. **Ziel: mindestens 15 allgemein unterschiedliche Terra-Einheiten inklusive bestehender drei**, plus 6 fraktionsspezifische.

Jede Unit-Definition benötigt `id`, `role`, `attack`, `armor`, `shield`, `hull`, `accuracy`, `evasion`, `initiative`, `speed`, `cargo`, `fuel`, `range`, `target_priority`, `counter_tags`, `training_time`, `cost`, `prerequisites`, `repair_ratio`, `visual_asset`, `rule_version`. Keine rein kosmetisch andere Variante bei identischer Rolle. Einheiten existieren in `at_home`, `in_mission`, `garrison`, `repair_queue`, `destroyed`. Wiederverwendung derselben Einheit in zwei Missionen technisch unmöglich.

**Doktrinen:** aggressiv, defensiv, ausweichend, Belagerung, Aufklärung; sichtbare Stärken/Schwächen, keine Geheimkosten. Unabhängige Transport-/Späher-/Kampfmischungen dürfen nach klaren Missionstypregeln gebaut werden. Trainingsvorlagen, Batchproduktion, Kosten-/ETA-Vorschau.

## 9. Kriegssystem, Kampfrunden, Spionage und Berichte

### FUR-2-Vertrag

Im dokumentierten FUR-2 gewinnt Angriffskraft über gegnerische Verteidigung; Überfall verliert nach Sieg mindestens 10% Angreifer, bei Niederlage alle, Loot-Cap `(überlebende Einheiten × (40+10×Logistik))`, Mindestmarsch 5s, anschließender Rückmarsch. Schildwall zählt zur Spielerabwehr; Wächterbund verstärkt den Wall im PvP um 40%. Geheimhaltung dieser alten Regeln und bestehende Ereignisse bei Migration prüfen. Neue Regeln beginnen mit einem **expliziten Kampfregel-Versionswechsel**.

### FUR-3-Mehr-Runden-Motor

- Maximal **6 simultan deterministisch ausgewertete Runden** mit pro Stack/Einheit: Schild, Hülle, Panzerung, Genauigkeit, Ausweichen, Schadenstyp, Reichweite und Initiative.
- Serverseitiger Zufallsstrom aus gesichertem Kampf-Seed. Jede Schlacht speichert Ruleset-Hash, Kampf-Seed-Commitment, finalen Seed/Replay (erst nach Abschluss offenlegen), Eingangszustand, Aktionenkette, Bilanzen und Rundendetails. Eindeutig reproduzierbares Replay unabhängig von Spielclient und Workeranzahl.
- Ausgang: Angreifer gewinnt, wenn alle verteidigenden kampffähigen Stapel ausgeschaltet und Belagerungsziel erfüllt sind; Verteidiger gewinnt bei Angreifervernichtung; nach Runde 6 gilt **verteidigte Stellung / unentschieden** statt automatischer Besetzung. Kein gleichzeitiger Sieg beider Parteien.
- Timing und Reihenfolge: Ankunftsereignisse `(due_at,event_id)` in DB-Reihenfolge unter Ziel-Lock; diplomatische Immunität, Urlaub, Noobschutz **zum Missionsstart und bei Ankunft** erneut prüfen. Bei geändertem Besitz und unzulässiger Mission sichere Rückkehr nach festgelegter Rückrufregel.
- Schäden, Verteidigung und Gegenklassen: `effective_attack = base_attack × (1+tactics_bonus) × doctrine × counter × terrain × faction`; Wahrscheinlichkeit Treffer `clamp(0.35, 0.95, 0.72 + 0.02×(accuracy-evasion))`; Variationsfaktor 0.90–1.10 nur aus Seed; Schaden `max(1,floor(effective_attack×variation - armor))`, erst Schilde, dann Hülle. Die **genauen** Gewichte und Zielwahl-Algorithmen im Regelkatalog versionieren und per Fixture-Tests einfrieren; die Formeln dienen als implementierbarer FUR-3-Default und sind keine bereits bestehende FUR-2-Tatsache.
- Verteidigungsbauwerke als Spezialstapel, Schildwall-Buff, Reparaturquoten, Festungsintegrität, Belagerungsschaden; gegnerische Einheitentypen mit klaren Counter-Tags. Kein unendlicher Kampf und keine negativen Mengen.
- Verlierer erhalten angemessene rekonstruierbare Berichte, keine Offenlegung versteckter Gegnerinformationen vor erlaubter Spionage. Runde, Schaden, Tote, Sieger, Beute, Trümmer, Rückzug, Allianzbeiträge, Timestamp, Spielregelversion auswertbar.
- Taktischer Rückzug nach Regel, Rückruf vor Ankunft, Sperre bei festem Kampf-Lock, defensive Allianzunterstützung, koordinierte Attacken mit Teilnehmer-Cap, Betrugsschutz.
- Geschützte Spielzustände: Besatzung, Garnison, flüchtende Truppen, Reserve, Behandlung, Reparatur; Loot aus tatsächlich verfügbarem Depot, niemals aus fremden Reservebeständen ohne gesonderte Regel.
- **Kampfsimulator:** gleiche Battle Engine im reinen `dry_run` ohne Ressourcenänderung; bei nicht aufgeklärten Gegnern Ergebnisse als Spannen/Unsicherheit; UI und JSON-Ausgabe; Bot nutzt keinen anderen Algorithmus.

### Spionage / Gegenaufklärung

Spähermissionen enthüllen abhängig von Aufklärung/Forschung und Abwehr: Standort, Gebäudelevel, Lagerband, Garnisonsband, konkrete Truppen erst auf höherer Stufe; Bericht mit Verfallszeit. Gegenaufklärung erlaubt Entdeckung, verschleierte Gegenmeldung und eventuell Abfanggefecht, niemals Zugriff auf Admin- oder private Daten. `fog_snapshot` statt unberechtigter direkter DB-Sicht.

## 10. Missionskatalog und Zeitmaschine

**Terra:** Überfall, Erobern, Spionage, Gegenaufklärung, Garnison verstärken/abziehen, Transport, Allianzunterstützung, gemeinsamer Angriff, Belagerung, Artillerieschlag, Kolonisation, Erkundung, Expedition, Bergen, Rückzug/Rückruf, Konvoi, Relocation (unter Cooldown), NPC-Event-Mission.

**Orbit:** Flottenangriff, Transport, Stationierung, Kolonisierung, Expedition, Bergung, Sensor-Sweep, Abfangen, koordiniertes Flottengefecht, Verteidigungsvereinigung, Raketenangriff, Sprungtortransfer, Mond-/Stationszerstörungsversuch nur unter sehr engen Voraussetzungen, orbitale Evakuierung.

**State machine:** `created → reserved → outbound → arrived → resolving → returning → completed`. Alternative terminale Zustände `cancelled`, `failed`, `expired`, `intercepted`; `recovering`/`stationed` erlaubt wo passend. Jede Änderung ist Event mit idempotentem `command_id`; Missions- und Ressourcenreserve in derselben DB-Transaktion. Bei Worker-Absturz Wiederaufnahme ohne zweite Beute oder zweite Zieleroberung. Aufträge nach `world_id` separieren; Zeitserver UTC; Benutzerzeiten lokalisiert.

**FUR-2:** Limit 30 laufende Missionen/Operationen je Kolonie, jeweils eine aktive Bau-/Forschung-/Ausbildungsqueue. Neue Welt kann eigene Limits je Klasse konfigurieren. Dauer/Ziel/Flottenart aus serverseitig gültigen Daten, keine manipulierte Client-ETA. Support für Reisezeit-, Speed- und Belastungsberechnung sowie Rückruf-/Nichtankunfts-Varianten.

## 11. Allianz-, Diplomatie- und Sozial-System

**Bestehende Grundlage:** Allianzname 3–30 Zeichen, Tag 3–8 alphanumerisch, Gründer Leitung; Rollen Leitung, Offizier, Mitglied; Einladung annehmen, eine Mitgliedschaft pro Spieler, Leiter muss bei Ausstieg Nachfolge sichern; Nichtangriffspakt erst nach beidseitiger Annahme, Krieg/Neutral; Welt-/Allianzchat und private Nachricht bis 2.000 Zeichen. **Bei Upgrade bewahren.**

**Neu:** Bearbeitbare Allianzrollen und explizite Berechtigungen (Einladungen, Krieg, Diplomatie, Depot, Forum, Operationsplanung, Territorien); kein Recht durch nur vom Client gesetzte Rolle. Führungswahl/-übergabe, Mitgliedsanträge, Kicks und Austritte mit Journal; Allianzprofil, Emblem (lizenz- und moderationsgeprüft), Mitglieder-/Austrittsverlauf, Vereins-/Militär-Statistiken, gemeinsame Kriegsübersicht.

**Kriegsrecht:** Kriegserklärung mit Startschwelle, Kriegszielen, Kriegspunkten, Fronten, Raids, Armeen- und Gebietswertungen, Frieden/Verhandlung, formellem Endstatus und Cooldown. Keine automatische Aufhebung eines angenommenen Pakts ohne explizite Regel; Diplomatieänderung in Flugzeit wird bei Start/Ankunft respektiert. Allianz vs. Allianz und NPC-Allianzkrieg. 

**Koordination:** Allianzkalender mit Kriegszeitfenstern, Operation-/Sammelangriff, Verteidigungskoordination, militärischer Planungstafel, geteilten Berichten nach Zustimmung, Kartenmarkierungen, internen Foren und Thread-Rechten. Gemeinschaftslager, Spendenledger, gemeinsame Allianzgebäude/Projekte und Nicht-Missbrauchsgrenzen. Spielerprofile, Freundes-/Blockliste, Buddy-Anfragen, personalisierte Notizen.

**Kommunikation:** Moderierte Kanäle, Direct Messages, Zustellstatus, Lese-/Stummschaltoptionen, Nachrichtensuche, Templates, BBCode/Markdown-Sanitizing, Spam-Limits, Mute/Block/Report; privater Inhalt nur berechtigten Teilnehmern und eng begrenzten gesetzlichen/moderativen Verfahren zugänglich. Kein Moderationszugriff als öffentliche Anzeige.

## 12. NPC-Kampagnen, Missionen, Quests, Erfolge, Endgame

- **Fünf FUR-2-Direktiven** unverändert migrieren: Rohstoffgebäude Stufe 2, Kaserne, erste Forschung, erste Eroberung, Kernzitadelle (ursprüngliche Belohnungen jeweils 400, 300, 500, 900, 2000 je Ressource).
- Weitere Questreihen: Tutorial 20 Schritte, Terra-Kampagne 30 Missionen, Allianz 15, Wirtschaft 15, PvE 20, Orbit 30, Saison-Challenges 20; wiederholbare Wochenaufträge und Erfolge. Zahlen sind Mindest-Content-Ziele, Regeln/Belohnungen in JSON, nicht im UI hart verdrahten.
- Weltboss- und Raidketten, regionale Krisen, NPC-Fraktionen, NPC-Nachschub, veränderliche Intensität und klar definierte Verlust-/Loot-Caps; NPC-Planer benutzt den gleichen Missionsservice und darf keine unlimitierte Ware erzeugen.
- Fortlaufendes Endgame nach Zitadellensieg: Sternentor-Schlüssel, Orbit-Zugang, neun Kernprotokolle, Sektordominanz, Allianz-Weltkampagnen, neue Weltbosse; kein leerer Bildschirm nach dem ersten Sieg.
- Erfolge, saisonale und dauerhafte Rangliste, Hall of Fame, Medaillen, Avatarrahmen, Skins/Embleme und rein kosmetische Belohnungen; keine Echtgeld-Power.

## 13. Orbit und Weltraum-Layer (vollständige neue Erweiterung)

**Freischaltung:** Kernzitadelle oder alternative vergleichbar schwere FUR-Kampagnenroute, Raumhafen/Forschung für Orbit-I, universelle Gate-Ressourcen; kein einzelner Sieg anderer Spieler blockiert alle Neulinge (mehrere Zugangswege, NPC-Instanzprotokoll).

**Orbital-Karte:** Welt→System→Orbitalposition: `galaxy`, `system`, `slot` als eindeutiges Objekt je Welt; pro Welt mehrere Galaxien; navigierbar, filtrierbar, Nebel/Sensorik. Planet/Satellit/Trümmerfeld/Station/Mond separate Typen und Lebenszyklen. Orbitaler Besetzungsplatz und Hauptbasis können nicht von zwei Spielern gleichzeitig reserviert werden.

**Orbitalkolonie:** max. 3 ohne Erweiterungen, bis 8 mit Forschung per neue-Welt-Default; eigener Bau-/Forschungs-/Werftslot, Energieversorgung, Flottenlager, Ätherförderung, Frachtrouten zum Terra-Kommando. Kein magischer Soforttransfer zwischen Ebenen ohne Cargo-Mission.

**Schiffsklassen:** Aufklärungssonde, Kurierdrohne, Leichter Jäger, Schwerer Jäger, Fregatte, Kreuzer, Schlachtschiff, Schildträger, Träger, Kolonieschiff, Frachter, Bergungsschiff, Belagerungsschiff, Flaggschiff. Jedes besitzt Angriff/Schild/Hülle/Speed/Fracht/Treibstoff, Voraussetzungen, Angriffsklasse, Unterhalt; Befehle mit Raumfahrttechnik und Hangar-Anzahl limitiert.

**Orbital-Missionen:** Transporte, stationieren, kolonisieren, auskundschaften, angreifen, abfangen, Verbandsangriff, Expedition in Anomalien, Abbau und Bergung, Mond-/Stationserkundung, Fernwaffen- und Verteidigungsmissile, Sprungtor, Evakuierung. Aufklärung kann abgefangen werden; Flottenverbände mit Besitzeranteilen und Ergebnisverteilung; Rückflüge müssen im Server weiterlaufen.

**Mond-/Station-Systeme:** Entstehung über klar definierte PvE/PvP-Ereignisse oder Bau, Mond-/Spezialgebäude, Sensorphalanx, Sprungtor mit Cooldown, Wrack-/Trümmerfeld mit Material-Limits, Reparatur/Recycling, Mond-/Stationsübernahme unter strikten Matchmaking-/Schutzregeln. Keine 1:1-Übernahme der OGame-Marken oder Assettexte.

**Technik:** Eigene Orbitalregeln, aber derselbe `GameEvent`-Scheduler, Ledger, Auth, Allianz, Bericht, Regelnversion, Gegnerprofil, Worker und Verwaltungs-/Testinfrastruktur wie auf Terra.

## 14. Handel, Gegenstände, Helden und Komfort

- Ein überschaubares Item-System mit Bau-/Kampf-/Kosmetikmaterial, Inventar, verbrauchbaren PvE-Boostern **ohne Pay-to-win**, Herstellung und Recycling; Items sind per `item_defs` versioniert, niemals unbeschränkter unkontrollierter RNG-Wert.
- Kommandanten-/Heldenrollen (Wirtschaft, Verteidigung, Aufklärung, Flotten) mit passiven begrenzten Fähigkeiten, klarer Cooldown- und Respec-Mechanik, fairer Erreichbarkeit; kein exklusiver Kaufvorteil. Bei Bedarf reine Abzeichen in frühen Welten aktivieren.
- Private Vorlagen: Baupläne, Forschungsvorlagen, Trainingsstapel, Flotten-/Konvoiaufstellungen; Benachrichtigungsregeln; Schnellaktionen mit serverseitiger Vorprüfung.
- Keine Echtgeldkäufe im Initial-Livebetrieb. Freiwilliger Unterstützershop ist **architektonisch nur als deaktivierbare spätere Erweiterung** vorgesehen; vor Nutzung braucht es Betreiberentscheidung, Zahlungsanbieter, Steuern, Widerruf und gesonderte juristische Prüfung. Der Rest des Spiels ist ohne Shop vollständig spielbar.

## 15. Saison-/Multiwelt-/Progressionssystem

- Dauerwelt: keine automatischen Resets; Fraktion und Grundstücke bleiben erhalten, Weltregeln können ab bestimmtem Stichtag migriert werden.
- Saisonwelt: separate DB-/World-ID-Daten, separate Ranglisten; Start/Ende optional konfigurierbar 1–365 Tage, Status `scheduled/active/finalizing/archived`; Ende archiviert Scores, Belohnungen und replays; Neustart nur nach ausdrücklichem saisonalem Weltmodus, **nicht** automatisch in bestehender Dauerwelt.
- Live-Ereignisse aus FUR-2 (Produktionsbonus 0–100 Prozentpunkte, 1–168 Stunden) erhalten; ergänzen PvE-Invasion, Konvoi-Event, Ressourcensturm, Allianzvorherrschaft, Forschungsschub, Orbit-Anomalien, Bossphase. Overlap-Regeln für Boni und Events, harte Caps, Audits, Zeitpunkt in UTC.
- Saisons speichern kompletten **wirksamen** RuleSet-Hash inklusive externer Formeln/Version; aktuelle FUR-2-Dokumentation speichert nur JSON-Katalog, weshalb beim Upgrade auch ausführbare Formelversionen einzufrieren sind.
- Power-Wertung FUR-2 `10×Gebäudestufen + 20×Technologiestufen + 100×eroberte Außenposten` bleibt als `legacy_power`; für FUR-3 getrennte Scores (Wirtschaft, Forschung, Militärleistung, territoriale Kontrolle, Allianzbeitrag) und transparente Hauptwertung mit Score-Migration.

## 16. Schutz, Anti-Griefing, soziale Verantwortung und Betriebsregeln

- FUR-2: PvP nach mindestens einer Stunde Accountalter, Allianz/NAP-/Urlaubs-Immunität. **Neue Welten:** Anfänger-Grundschutz 72 Stunden ODER bis definierter Machtgrenze, mit transparenter Ablaufzeit und spätestens nach 7 Tagen Ende; keine Angriffe aus aktiver Schutzstellung; 12 Stunden Defeat-Recovery-Option, die aggressive Aktionen beendet. Werte versioniert und Admin-konfigurierbar.
- Power-Differenz-Limits, Angriffscooldowns, Plünderungs- und Verlustratenlimits, Escape-/Rückzugmechanik, faire Respawn-Positionen; Schutz vor dauerhafter Vernichtung eines Accounts.
- Multiaccount-/Bot-Detektion nur verhältnismäßig: Rate Limits, Telemetrie-Minimierung, Verdachts-Score, nachvollziehbarer Review, keine willkürliche automatische Sperre allein auf IP-Basis, Einspruchs- und Löschprozesse.
- Login: keine öffentliche Offenlegung, ob eine Adresse existiert; Mindestpasswort, Argon2id, bestätigte E-Mail, sichere Sessions, CSRF und TOTP, später optional WebAuthn; Recovery-Codes einmalig, Rate-Limit und Audit.
- Ingame-Verhaltenskodex, Melde-/Blockfunktion, abgestufte Moderation und Protokollierung mit rollenabhängiger Sicht. Datenschutz-/Auskunfts-/Löschprozesse und Aufbewahrungsplan.

## 17. UX, Design, Mobile, Barrierefreiheit und Internationalisierung

**Styleguide:** Onyx `#0C1018`, Gold `#C99A43`, Cyan `#37B6C6`, helle Schrift, klar lesbare Tabellen, Statusfarben mit Text/Symbol. Neue FUR-Grafiken und SVG-Icons; WCAG 2.2 AA als Ziel, Tastaturbedienung, Fokus, ausreichend Kontrast, nicht allein Farbe als Information.

**Navigation Desktop:** Kommandozentrale → Weltkarte → Imperium/Kolonien → Wirtschaft → Gebäude → Forschung → Streitkräfte → Missionen → Orbit → Diplomatie/Allianzen → Markt → Ranglisten → Berichte → Quests → Nachrichten → Inventar → Einstellungen → Admin (rollenbasiert). **Mobile:** Bottom-Nav mit Kernaktionen, erreichbare Touch-Bereiche, Kartenliste als Alternative, editierbare Formulare ohne unnötiges horizontales Scrollen.

**Screens:** Landing, Auth, Onboarding, Dashboard, Kolonieübersicht, Gebäudebaum, Forschungsbaum, Rekrutierung, Defense, Terra-Karte, Orbit-Karte, Missionsplaner, Flottenauswahl, Timeline, Kampfbericht/Replay, NPC-Raid, Expedition, Markt, Händler, Inventar, Quests, Allianz, Krieg, Forum, Chat, Postfach, Profil, Statistik, Rangliste, Hall of Fame, Moderation, Admin/Welten, Einstellungen, Konto/Sicherheit, Systemstatus/Fehler, Hilfe/Spielanleitung. Jede Aktion mit Fehler-, Lade-, Leer-, Erfolgs-, Offline-Zustand; keine Fake-Buttons.

**Realtime:** WebSocket oder SSE für Events/Chats/Operationsstatus, Polling-Fallback und idempotente State-Reconciliation. Server bleibt Autorität. Browser-Push/E-Mail optional opt-in, Abwesenheit nicht bestrafend. Optional PWA als lesbarer Offline-Cache, aber **kein** Offline-Schreiben an Wirtschafts-/Kampfdaten.

**Sprachen:** Deutsch und Englisch vollständig; Vietnamesisch, Spanisch, Türkisch ebenfalls als produktfähige Sprachkataloge samt QA. Locale-Schlüssel statt Hartkodierung, Fallback DE oder EN, Zeit/Datum/Zahlen/Plural-Übersetzung, keine GPL-Sprachdateien kopieren. Neue Spielerprofile speichern Locale und Timezone getrennt.

## 18. Admin-Konsole, LiveOps, Compliance

- Rollen `owner/superadmin/admin/gamemaster/moderator/support/player` mit granularen Rechten, TOTP-Pflicht für Admin, Vier-Augen-Workflow für kritische Datenänderungen. Kein Admin-Zugriff über öffentlich ungeschützte Dev-Endpoints.
- Administrative Spieler-/Allianz-/Kolonieverwaltung; Weltenverwaltung, Regeln-/Feature-Flags, Nutzer-/PvP-Schutz, Neuregistrierung, Balancing-Editor, Karten-Seed-Preview, NPC-Spawn, Welt-Reset **nur Saison/Test**, Wartung, Mutes/Bans, Appeals, Reportqueue, Marktaufsicht, E-Mail-Status und Absenderkonfiguration.
- Zeitgesteuerte Events, Saisons, Boss-Raids, Ankündigungen, Nachrichten, Spiel-Historie, Moderation, Logs, Audits, Mitarbeiterrechte, automatisierte Integritätsprüfungen. Backups/Restore-Probe und Betriebshandbuch.
- Sicherheits-/Datenschutzansichten: Datenexport, Lösch-/Anonymisierungsworkflow, Datenaufbewahrungsfristen, Systemzugriffe ohne PII-Leak, Sitzungen widerrufen, Debug-Daten minimieren. SEO/Impressum/Datenschutz/AGB mit Platzhalter-Hinweis **nicht live schalten, bis rechtlich geprüft**.

## 19. Definitiver Qualitätsmaßstab für alle Funktionen

Jede Funktion erhält: ID in `FEATURES.json`, UI-Route, API-Service, Domain-Verhalten, DB-/Eventmodell (wo sinnvoll), Rechte- und Eingabeprüfung, positive/negative/race Tests, Telemetrie ohne PII, DE/EN/VI/ES/TR-Strings, Hilfeartikel, `implemented`-Nachweis. Gilt insbesondere für Legacy-Funktionen, die nur in der Anleitung beschrieben sind. Keine Statusbehauptung ohne Codeprüfung und nachvollziehbaren Test.

## 20. Grenzen und betriebliche Entscheidungen

- **Nicht als frei wiederverwendbar ansehen:** fremde Grafiken/Marken; alte GPL-/AGPL-/CC-Quellen ungeprüft kopieren. Exakte OGame-/Tribal-Wars-Formeln und Lore nicht als unverändert nötige Funktion behandeln. Die **Spielmechanikklasse** wird als eigenständiges FUR-System realisiert.
- **Nicht ohne Eigentümerfreigabe:** echte Zahlung, Domain, Root-Server, produktives SMTP, Discord-Token, öffentliche DNS-Änderungen, Geheimschlüssel oder Veröffentlichung personenbezogener Daten. Adapter, Mock-Integrationen, `.env.example` und Staging-Probe sind Bestandteil.
- **Wenn Agent Hindernisse findet:** Implementierung fortsetzen, alternative sichere Technologie wählen, Entscheidungen in ADR dokumentieren; nur echte externe Voraussetzungen an den Besitzer übergeben. Nie Authentifizierungs-/Test-/Lizenzprüfungen aus Zeitdruck deaktivieren.



---

<!-- QUELLDOKUMENT: docs/02_TECHNICAL_CONTRACTS.md -->

# FUR EMPIRE — VERBINDLICHE TECHNISCHE KONTRAKTE

**Zweck:** Engineering-Spezifikation für Coding-Agent, basierend auf dokumentiertem FUR-2-Spiel und dem neuen Master-GDD. Kein Ersatz für die Prüfung des echten aktuellen Repositorys.

## 1. Architekturentscheidung

**Default:** Den aktuell eingesetzten Python/FastAPI- und Worker-Stack beibehalten, sofern ein Repository-Audit ihn bestätigt. Nicht blind einen PHP-Laravel-Fork in FUR einbauen. Empfohlener Ausbau: FastAPI + Python 3.12/3.13 (vom vorhandenen Projekt unterstützte Version zuerst), SQLAlchemy/SQLModel bzw. bestehende DB-Abstraktion, Alembic-Migrationen, PostgreSQL als gemeinsame Server-Datenbank, Redis als Queue-/Cache-Option, klar getrennte Worker, WebSocket/SSE, moderne Templates/TypeScript oder bestehendes FUR-Frontend inkrementell. **Frontend-Technik durch Codeprüfung entscheiden**, nicht wegen eines Trends neu schreiben.

**Deployment:** Ein modularer Monolith mit getrennten Prozessen `web`, `world_worker`, `scheduler`, optional `realtime`, `database`, `redis`, `reverse_proxy`. Erst bei dokumentiertem Skalierungsbedarf Services auskoppeln. Klares Domain-/API-Modell und keine zyklischen Importe.

**Schnittstellenebenen:**

```text
Browser/PWA (untrusted)
   | HTTPS + CSRF + Session / WS auth
API & Controllers (validation, authorization, rate limits)
   | command/query buses, application services
Domain Core (world, economy, colony, research, units, combat, missions,
             orbit, alliances, politics, NPC, season, market, moderation)
   | transactions, deterministic ruleset, event/outbox
PostgreSQL  <->  World Worker/Scheduler  <->  Real-time event bus
   | audit, backup, metrics, snapshots, notifications
External adapters (SMTP, optional Discord OAuth/webhook, future payments disabled)
```

**Grenzen:** keine Spielelogik im Template, keine DB-Schreiboperation ohne Domain-Service, kein globales unsicheres Mutable-Objekt, keine Geheimnisse im Code, keine generischen Admin-Endpunkte ohne RBAC. Nutzer- und Weltidentität in *jeder* Anfrage und Query.

## 2. Basisstruktur (bei vorhandenen Ordnern anpassen)

```text
fur_empire/
  api/                       routers, schemas, policies, csrf, pagination
  domain/
    accounts/ worlds/ colonies/ economy/ buildings/ research/
    units/ missions/ battle/ espionage/ alliances/ diplomacy/
    markets/ npcs/ orbit/ events/ quests/ season/ leaderboard/
  application/               command handlers, query services, UoW
  infra/                     postgres repositories, redis, messaging, smtp
  rulesets/                  immutable, validated FUR-2, FUR-3, ORBIT-1
  worker/                    idempotent event processors, schedule jobs
  web/                       templates/static/i18n/assets, accessibility
  admin/                     RBAC, moderation, world ops, compliance
  telemetry/                 tracing/logging/audit
migrations/                   forwards+safe rollback or restore recipes
scripts/                      bootstrap, seed, backups, sanity tests
ops/                          compose, reverse proxy, runbooks
spec/                         feature definitions, ruleset JSON schemas
fixtures/                     combat replays, world seeds, scenarios
tests/                        unit, integration, e2e, perf, security
```

## 3. Multiworld und Datengrenzen

- Globale Account-ID (UUIDv7 oder UUID4), `world_id`, `world_player_id`, `colony_id`, `mission_id`, `command_id`/`idempotency_key`, `rule_version`, `event_id` nie als Benutzerinput vertrauen.
- Tabellen besitzen `world_id` wo Daten weltbezogen sind, und Fremdschlüssel/unique constraints verhindern weltübergreifenden Besitztransfer.
- `world_player` referenziert genau eine Fraktion pro Welt. `accounts` kann Mitglied mehrerer Welten sein, aber nur ein `world_player` je `(account_id, world_id)`.
- `world_type = permanent|seasonal|sandbox`; saisonales Ende darf nur Ressourcen der betroffenen Welt archivieren/resetten.
- Migration bestehender FUR-2-Spielstände **ohne irreversible Löschung**; Backup + Restore zuerst, Dual-Read/Dual-Write nur bei begründetem Bedarf, beim Feature-Switch replays und Datenintegrität vergleichen.

## 4. Normiertes Schema (Tabellen/Namen als Zielentwurf)

**Identity:** `accounts`, `account_emails`, `account_credentials`, `totp_secrets`, `recovery_codes`, `sessions`, `session_revocations`, `account_preferences`, `privacy_requests`, `notifications`, `notification_preferences`, `auth_audit`.

**Welten:** `worlds`, `world_rulesets`, `world_seeds`, `world_settings`, `world_players`, `world_regions`, `world_sectors`, `terrain_tiles`, `fog_observations`, `world_spawn_points`, `map_bookmarks`, `regional_control`, `world_event_instances`.

**Kolonien/Ökonomie:** `colonies`, `outposts`, `colony_buildings`, `colony_research`, `world_player_research`, `research_queue`, `building_queue`, `training_queue`, `resources_balances`, `resource_fraction_remainders`, `reserve_balances`, `resource_ledger`, `resource_reservations`, `energy_state`, `inventory_stacks`, `items`, `item_recipes`, `colony_transfers`.

**Krieg:** `unit_stacks`, `garrisons`, `defense_installations`, `missions`, `mission_participants`, `mission_cargo`, `mission_events`, `combat_instances`, `combat_rounds`, `combat_losses`, `combat_reports`, `combat_replays`, `espionage_reports`, `fog_snapshots`, `wreck_fields`, `repair_orders`, `supply_routes`.

**Orbit:** `star_systems`, `orbital_positions`, `orbital_bodies`, `orbital_colonies`, `orbital_buildings`, `starships`, `fleets`, `fleet_composition`, `fleet_missions`, `fleet_unions`, `orbital_sensors`, `jumpgates`, `jumpgate_cooldowns`, `orbital_debris`, `orbital_expeditions`, `orbital_reports`, `moons`.

**Allianz/Sozial:** `alliances`, `alliance_members`, `alliance_roles`, `alliance_permissions`, `alliance_invitations`, `alliance_applications`, `alliance_treaties`, `alliance_wars`, `war_objectives`, `war_scores`, `alliance_projects`, `alliance_treasury`, `alliance_treasury_ledger`, `friendships`, `blocked_players`, `personal_notes`, `alliance_forums`, `forum_threads`, `forum_posts`, `chat_channels`, `chat_memberships`, `messages`, `message_reads`, `message_reports`.

**Progression/Service:** `quest_defs`, `quest_progress`, `achievement_defs`, `achievements`, `seasons`, `season_participants`, `season_snapshots`, `season_results`, `hall_of_fame`, `npc_factions`, `npc_bases`, `npc_strategies`, `npc_orders`, `event_templates`, `player_rewards`, `highscore_snapshots`, `event_outbox`, `world_jobs`, `idempotency_records`, `operator_audit`, `moderation_cases`, `bans`, `appeals`, `feature_flags`, `job_failures`, `world_snapshots`, `backup_restore_checks`.

**Migrationsregeln:** Money/Resources sind Integer in kleinstmöglicher Ressourceneinheit, Restproduktion DECIMAL/Integer-Bruchnumerator (keine Float-Rundungsfehler), UTC-Timestamps mit Zeitzone, explizite `CHECK amount >= 0`, `CHECK capacity >= 0`, FK-Integrität, DB-Unique für Standorte und Einmalclaims. Tabellen zum Archivieren je `world_id` indexieren; `ON DELETE CASCADE` nie bei Kostenbuchungen ohne archiviertes Ledger nutzen. Spielerbezogene PII getrennt von dauerhaften Spielstatistiken und mit Löschplan.

## 5. Spiel-Befehle und Read-Modell

**Command Envelope:**

```json
{
  "command_id": "uuid",
  "world_id": "uuid",
  "actor": "server_session_identity",
  "action": "mission.dispatch",
  "resource_version": 17,
  "payload": { "origin_colony_id": "uuid", "target_sector": [20, 7], "units": { "ranger": 15 } }
}
```

`actor` wird serverseitig aus Session/Token ermittelt und niemals aus Body vertraut. Alle schreibenden Browser-Requests erfordern CSRF-/SameSite-Schutz, Origin- und Berechtigungsprüfung. `command_id` und eindeutige DB-Constraints garantieren Replayschutz; identische Wiederholung gibt denselben gespeicherten Erfolg zurück; gleiche ID mit verändertem Payload führt zu `409 Conflict`.

**Event Envelope:**

```json
{
  "event_id":"uuid", "schema_version":1, "event_type":"mission.arrived",
  "world_id":"uuid", "aggregate_type":"mission", "aggregate_id":"uuid",
  "occurred_at":"2026-11-06T09:00:00Z", "due_at":"2026-11-06T09:00:00Z",
  "causation_id":"uuid", "correlation_id":"uuid", "ruleset_sha256":"hex",
  "payload": { "mission_id":"uuid", "state":"arrived" }
}
```

Alle fälligen Aufgaben durch Worker-Poll/Queue `FOR UPDATE SKIP LOCKED`/Lease übernehmen, DB-transaktional abschließen, `outbox` erst nach Commit publishen. Bei Lease-Ablauf retry; Dead-letter nach begrenzten Fehlversuchen, Admin-Replay nur mit Validierungs-/Idempotenzgarantie. Kein clientseitiger `setTimeout` als einzige Zustandsänderung.

## 6. Ressourcen-Ledger und Produktionskontrakte

- Jede Änderung hat `tx_id`, `world_id`, `owner_id`, `colony_id`, `resource`, `delta`, `source`, `cause_id`, `balance_after`, `created_at`, `ruleset_version`. Nicht negativ, vollständiger Audit.
- Reservierung und Verbrauch atomar: `SELECT ... FOR UPDATE`, Rate/Cost serverseitig, `available_balance` prüfen, Reservation erstellen, keine Doppelbuchung; Fehler führt zu vollständigem Rollback.
- Transfer: Sender-Debit sofort, Cargo-Escrow während Marsch, Empfänger-Credit erst nach legitimer Ankunft; Return-Event/Cancellation idempotent, Empfang bei vollem Depot ins Reserve-Lager; nie beide aufgelösten Routen gleichzeitig.
- Produktion: `produced = floor((elapsed_ms * per_second_numerator + remainder) / rate_denominator)`; Zeitverschiebung der Uhr verhindern; Wert nur bis Lagercap gutschreiben, Rest nicht still ins Reserve-Lager, wenn Produktionslimit erreicht (im Gegensatz zu Lieferrückständen); Pausen im Urlaub ausklammern. `effective_at` für Regeln/Ereignisse, die zwischen zwei Besuchen starten/enden, in Segmenten integrieren.
- Warenmarkt: `open -> reserved/accepted/cancelled/expired`, Verkaufspreis und Ressourcenreserve atomar, Käufer und Verkäufer gelockt in stabiler ID-Reihenfolge, `unique(trade_execution.offer_id)`.
- FUR-2-Direktive: `unique(world_player_id, directive_id)`; Versand einer Belohnung ins Reserve-Lager nur einmal.

## 7. Bau-, Forschungs-, Ausbildungs- und Warteschlangen

- Queue-Item: `queued -> active -> completed` / `cancelled|failed`; bei Start die Regelversion mit Kosten, prerequisites und Dauer pinnen. `active`-Uniqueness pro erlaubtem Slot/Scope. Nach Abschluss einzigen Levelzuwachs; Outbox-Event `building.completed`, `research.completed`, `training.completed`.
- Je Kolonie der FUR-2-Default für aktive Bau-/Forschungs-/Ausbildungsqueue, neue Planungs-Slots als konfigurierter FUR-3-Wert. Skill-Voraussetzungen und Inventar-Verbrauch beim Start erneut prüfen.
- Stornierung: falls vor Start keine Kosten oder eindeutige Release-Funktion; während Produktion nur definierte Teilkosten zurück, nie mehr als verbraucht. Umordnung nur pending und atomar.
- Worker darf Abschluss für gelöschte/umgezogene Kolonie nicht blind durchführen. Referenzen/Tombstones und Kompensationsereignisse anwenden.

## 8. Missionen und Kampfvertrag

**Mission dispatch:** Session -> world/player/ownership -> treaty/protection -> origin/speed -> target/visibility -> available troops -> cargo/energy -> active mission limit -> transaction reserve troops/resources -> mission entry -> outbox. Alle Prüfungen beim Start und bei Ankunft, die auf zwischenzeitlichen Weltstatus angewiesen sind.

**Kampfreplay:** `battle_version`, `participants`, `initial_state`, `commitment`, `rng_seed`, `rounds`, `final_state`, `loot`, `wreck`, `owner_changes`, `rule_hash`. Dieselbe Simulation muss mit identischem Seed bitgenau identisches Resultat liefern. `dry_run` erzeugt keinerlei Ledger- oder Besitz-Änderung. Sieger-/Besatzungseffekt erst nach Commit und nur, wenn Eroberungsbedingungen gültig sind.

**Schlachtatomizität:** Truppenverluste, Gebäude-/Schildstatus, Loot, Besatzung, Wrecks, Berichte und veranlasste Rückkehr in **einem** konsistenten Verarbeitungsablauf, idealerweise DB-Transaktion plus outbox. Keine Teilbuchungen bei Exceptions. Gleicher Zielzustand wird in festen Sperren verarbeitet; Transaktions-Deadlocks unter Retry mit Jitter behandeln.

**Anti-Abuse:** Besitzer darf keine fremden Einheiten senden; Truppenanzahl kann nicht negativ/NaN/unendlich sein; Mission nicht doppelt starten/abbrechen; undefinierte Zieltypen werden abgewiesen; Gegner im Urlaub, NAP und Neulingsschutz sind geschützt; keine Forschung/Spielzeug-Ids per client trusted.

## 9. API-Kontrakt v1 – Hauptendpunkte

Alle Endpunkte unter `/api/v1` mit paginierter, typisierter Antwort, stabilem Fehlercode und `request_id`. Spezifikation als OpenAPI generieren, Schemas in Tests snapshotten. In Klammern: HTTP-Methode.

**System/Account:** `/health/live` (GET), `/health/ready` (GET), `/system/version` (GET), `/auth/register` (POST), `/auth/login` (POST), `/auth/logout` (POST), `/auth/me` (GET), `/auth/email/verify` (POST), `/auth/recover/start` (POST), `/auth/recover/complete` (POST), `/auth/totp/enroll` (POST), `/auth/totp/confirm` (POST), `/auth/sessions` (GET/DELETE), `/account/preferences` (GET/PATCH), `/account/privacy/export` (POST), `/account/privacy/delete-request` (POST).

**Welten/Karten:** `/worlds` (GET), `/worlds/{world_id}/join` (POST), `/worlds/{id}/rules` (GET), `/worlds/{id}/map/tiles` (GET), `/worlds/{id}/map/sector/{x}/{y}` (GET), `/worlds/{id}/map/bookmarks` (GET/POST/DELETE), `/worlds/{id}/regions` (GET), `/worlds/{id}/orbit/systems` (GET), `/worlds/{id}/status` (GET).

**Imperium/Economy:** `/w/{world_id}/dashboard` (GET), `/w/{id}/colonies` (GET/POST), `/w/{id}/colonies/{cid}` (GET/PATCH), `/w/{id}/colonies/{cid}/relocate` (POST), `/w/{id}/colonies/{cid}/abandon` (POST), `/w/{id}/colonies/{cid}/resources` (GET), `/w/{id}/colonies/{cid}/storage/claim` (POST), `/w/{id}/colonies/{cid}/buildings` (GET), `/w/{id}/colonies/{cid}/build-queue` (GET/POST/PATCH/DELETE), `/w/{id}/colonies/{cid}/research` (GET), `/w/{id}/research/tree` (GET), `/w/{id}/research/queue` (GET/POST/DELETE), `/w/{id}/colonies/{cid}/training` (GET/POST/DELETE), `/w/{id}/trade/instant` (POST), `/w/{id}/market/offers` (GET/POST), `/w/{id}/market/offers/{offer_id}/accept` (POST), `/w/{id}/market/offers/{offer_id}` (DELETE), `/w/{id}/market/history` (GET), `/w/{id}/inventory` (GET), `/w/{id}/crafting` (POST).

**Militär/Missionen:** `/w/{id}/units/catalog` (GET), `/w/{id}/missions/catalog` (GET), `/w/{id}/missions` (GET/POST), `/w/{id}/missions/{mid}` (GET), `/w/{id}/missions/{mid}/recall` (POST), `/w/{id}/missions/{mid}/intercept` (POST), `/w/{id}/garrisons` (GET/POST/DELETE), `/w/{id}/espionage/reports` (GET), `/w/{id}/combat/simulate` (POST), `/w/{id}/combat/reports` (GET), `/w/{id}/combat/reports/{rid}` (GET), `/w/{id}/combat/reports/{rid}/replay` (GET), `/w/{id}/alliance/operations` (GET/POST), `/w/{id}/alliance/operations/{oid}/join` (POST).

**Allianz/Social:** `/w/{id}/alliances` (GET/POST), `/w/{id}/alliances/{aid}` (GET/PATCH), `/w/{id}/alliances/{aid}/members` (GET), `/w/{id}/alliances/{aid}/invites` (POST), `/w/{id}/alliance/invites/{iid}/accept` (POST), `/w/{id}/alliances/{aid}/roles` (GET/POST/PATCH), `/w/{id}/alliances/{aid}/treaties` (GET/POST), `/w/{id}/alliances/{aid}/wars` (GET/POST), `/w/{id}/alliances/{aid}/depot` (GET/POST), `/w/{id}/alliance/forums` (GET/POST), `/w/{id}/chat/channels` (GET), `/w/{id}/chat/{channel}/messages` (GET/POST), `/w/{id}/messages` (GET/POST), `/w/{id}/messages/{msg_id}` (GET/DELETE), `/w/{id}/friends` (GET/POST/DELETE), `/w/{id}/notes` (GET/POST/PATCH/DELETE).

**Progression/Orbit:** `/w/{id}/quests` (GET), `/w/{id}/quests/{qid}/claim` (POST), `/w/{id}/achievements` (GET), `/w/{id}/leaderboard` (GET), `/w/{id}/hall-of-fame` (GET), `/w/{id}/seasons` (GET), `/w/{id}/events` (GET), `/w/{id}/orbit/colonies` (GET/POST), `/w/{id}/orbit/fleets` (GET/POST), `/w/{id}/orbit/missions` (GET/POST), `/w/{id}/orbit/wrecks` (GET), `/w/{id}/orbit/sensors` (POST), `/w/{id}/orbit/jumpgate` (POST).

**Admin:** `/admin/whoami` (GET), `/admin/worlds` (GET/POST/PATCH), `/admin/worlds/{id}/ruleset` (POST dry-run, POST publish), `/admin/worlds/{id}/seasons` (POST), `/admin/events` (POST/PATCH), `/admin/players` (GET), `/admin/players/{id}/sanctions` (POST), `/admin/audit` (GET), `/admin/moderation/reports` (GET/PATCH), `/admin/jobs` (GET), `/admin/jobs/{id}/retry` (POST), `/admin/worlds/{id}/integrity-check` (POST), `/admin/backups` (GET/POST), `/admin/backups/restore-test` (POST), `/admin/announcements` (POST), `/admin/feature-flags` (GET/PATCH).

**Errorformat:** `{ "error": { "code":"INSUFFICIENT_RESOURCES", "message":"...", "details":{}, "request_id":"..." } }` — kein Stacktrace; `401` unauthenticated, `403` owner/role/treaty, `404` conceal private resource, `409` conflict/idempotency, `422` validation, `429` rate-limit. Alle GETs read-only, alle mutierenden Aktionen POST/PATCH/DELETE mit CSRF und Rollenprüfung. Für einen externen API-Client gesonderter OAuth2-/Token-Scope.

## 10. Websocket/SSE

`/api/v1/events/stream` authentifiziert per Session/kurzlebigem Eventtoken, pro `world_id`, autorisiertem Kanal und Last-Event-ID. Typen: `mission.updated`, `resource.updated`, `queue.completed`, `battle.reported`, `alliance.operation`, `chat.message`, `world.event`, `season.updated`, `announcement`, `security.session`. Payload immer minimiert; private Infos nicht in globalen Broadcast; Sequenznummer+Replay/Delta-Fetch bei Verbindungsabbruch. Rate/Message Caps und Polling-Fallback.

## 11. Spielregeln als Daten

`ruleset` enthält alle aktiven Formeln (Formel-ID + Version + überprüfbare Parameter), Definitionen für Gebäude, Forschung, Units, Terrain, Kampf, NPC, Quests, Markt, Kolonien, Orbit; deterministischer Serializer, SHA-256 signiert/gespeichert mit Veröffentlichung, Fixtures und Migration. **Ein Regelwechsel darf nicht rückwirkend laufende Missionen im alten RuleSet ändern**, außer es existiert ein auditierter expliziter Migrationspfad.

Beispiel: `FUR-2` reproduziert historische Rohstoffe/Events; `FUR-3` ergänzt abnehmende Außenpostenboni, Kampf-Engine v3, Erweiterungsgraph und PvP-Schutz. Agent darf nicht pauschal durch `max_level=20` alte Spielerobjekte ohne Policy ändern. `rulesets/` enthält JSON-Schema und Unit-/Invariant-Tests.

## 12. End-to-end Fehler- und Integritätsmodelle

- Doppelklick Marktkauf: nur eine Annahme, keine doppelte Auszahlung; Auftragsstatus stabil.
- Zwei Spieler kolonisieren dieselbe Kachel gleichzeitig: exakt einer gewinnt, beide erhalten deterministisches Ergebnis.
- Zwei Angriffe bei gleicher Ankunftssekunde: feste Event-ID-Tiebreak-Reihenfolge, kein doppelt abgezogener Verteidiger.
- Worker stirbt beim Kampf: wiederholtes Abarbeiten erzeugt exakt **eine** Schlacht, Berichte und Rückweg.
- Spielregel während Reise geändert: gepinnte Regelversion oder explizite Migrationsentscheidung, kein heimlicher Replay-Bruch.
- Urlaub aktiviert während Angriff: Aktivierung blockiert, solange gültige feindliche Angriffsmissionslage vorhanden.
- Allianzpakt während Marsch aufgelöst: Start-/Ankunftspolitik definieren und Replay-Test.
- Rückkehrende Ressourcen überfüllen Lager: überschüssige Lieferrückstände ins Reserve-Lager, produzierte Rohstoffe laufen bis Cap und gehen nicht unendlich ins Reserve-Lager.
- Regeltext ohne echte UI, nicht erreichbare Buttons, tote Links, unübersetzte Strings: E2E-/UI-Test muss fehlschlagen.
- Löschen/Anonymisieren: keine referenzierten Kampfberichte zerstören oder personenbezogene Inhalte unzulässig weiter speichern.
- Saisonende: Dauerwelt **unverändert**, archivierte Rangliste vollständig, neue Saison ohne alte Waren.

## 13. Verfügbarkeits- und Performance-Ziele

**Vorläufige messbare Abnahmeziele für eine einzelne VPS-/Root-Deploymentklasse**, erst nach realem Lasttest als Zusage verwendbar: 200 gleichzeitig aktive Benutzer mit 1.000 bereits registrierten Testspielern; P95 für standardmäßige Dashboard-Reads <500 ms auf definierter Testhardware, Map-Fenster P95 <800 ms, Action-API P95 <800 ms ohne lange Schlacht, kritische Queue-Abwicklung binnen 5 Sekunden bei gewöhnlicher Last, keine verlorenen Missions-/Ledger-Einträge in 30-minütigem Lastlauf. Definierte Testhardware, Seeds und Lastprofil in `PERFORMANCE_REPORT.md` angeben; Werte nicht einfach als bestanden markieren. Backups täglich + Point-in-Time-Wiederherstellung soweit vom gewählten DB-Setup unterstützt, Restore-Test in isolierter Instanz, Alert bei ausbleibendem Worker, Fehler-Rate-Schwellen als Monitoring Rules.

## 14. Quell-/Rechtskontrakt

Keine Assetübernahme aus fremden Browsergames, kein XG GPL/AGPL-Code in den privaten FUR-Kern ohne Lizenzstrategie, kein devana-Code ohne Bedingungen, kein CC BY-NC-ND-Code. Neu implementierte Spielkonzepte dokumentieren; eventuelle MIT-Snippets nur mit Copyright, Lizenz und Datei-/Commit-Provenienz. `docs/06_SOURCE_LICENSE_REGISTER.md` ist bindend.



---

<!-- QUELLDOKUMENT: docs/03_IMPLEMENTATION_ROADMAP.md -->

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



---

<!-- QUELLDOKUMENT: docs/04_SECURITY_OPERATIONS_LIVE.md -->

# FUR EMPIRE — SICHERHEIT, DATENSCHUTZ, BETRIEB UND LAUNCH-VORBEREITUNG

**Ziel:** Betreiber kauft die Domain und VPS/Root später. Alles bis zum öffentlichen Go-Live muss offline/lokal oder auf privatem Staging vorbereitet, getestet und dokumentiert sein. Dieses Dokument ist technische Checkliste, keine individuelle Rechtsberatung.

## 1. Vertrauensgrenzen und Security-by-default
- Untrusted: Webclient, Chat, uploads, URL, Query/Body, WebSocket, OAuth, DNS, andere Welten, externe Webhooks, Mod-Plugins, AI-Texte. Trusted: validierte Domänenbefehle unter authentisierter Session und DB-Transaktion.
- `session_id`/TOTP-/Reset-Token nie protokollieren. Argon2id/aktuell sichere Passwort-Hasher, Rotation + Einmal-Reset-Codes, Rate-limit IP+Account+Device heuristisch, kein Account-Enumeration.
- CSRF-Tokens (Cookie-Session), `Secure/HttpOnly/SameSite`, Login-Session-Rotation, Origin-Prüfung, HTTPS in Produktion, CSP/HSTS nur nach TLS-Test, zentraler Fehlerhandler ohne Stacktrace.
- Objekt- und Weltberechtigungen je Anfrage, nicht nur in UI; Role-Based Access + Policy-Based Access für Allianzrolle, Besitz, Fog, Chatgruppe, Gamemaster.
- SQL-Parameter, Pydantic-Validierung, HTML-Escaping und sanitizer für BBCode/Markdown; Template-Autoescaping, Image-/File-Upload Typ, Größe, Pfadprüfung; keine unsicheren Deserialisierungen.
- Verbot: Debug-Endpoints, `uvicorn --reload` in Produktion, unveränderte Testaccounts, bekannte Demo-Passwörter, localhost als öffentliches Callback-Ziel, Admin ohne 2FA, Default-Credentials.

## 2. Spielintegrität / Anti-Cheat
- Alle wirtschaftlichen Werte aus serverseitiger DB, integer/fixed-point, origin/owner-Policy, DB-FK-Checks, Ledger, idempotente Requests, Repeat-At-Least-Once Worker mit exactly-once Wirkung.
- World/Season/Account-Trennung, keine Cross-World-Schreiboperationen oder missbräuchliche saisonale Belohnungstransfers.
- Lock-Order für mehrere Konten deterministisch; `SELECT FOR UPDATE` unter PostgreSQL; idempotency key / payload checksum / conflict.
- Keine verbotenen Angriffe bei NAP, Newbie-Schutz, Urlaub, eigenen Zielen, Kriegssperre; Start und Ankunft validieren. Anti-Raid-Limits und Attack-Cooldowns.
- Anti-Bot: serverseitiges Rate Limiting, verdachtsbasierte Moderation, auditierter Einspruch. Keine automatischen permanenten IP-only-Sperren. Privacy by design.

## 3. Secret-Management und bereits offengelegte Schlüssel
- Keine früher in Chats oder lokalen Beispielen geposteten Tokens übernehmen. Alle zuvor offengelegten Schlüssel gelten als potenziell kompromittiert und sollen vor Livebetrieb bei den Diensten rotiert werden.
- Neue `.env.example` enthält nur Platzhalter wie `CHANGE_ME`, ohne echte Zugangsdaten. `.env`, SSH-Keys, DB-Dumps, Mailer-Credentials, Bot-Token und Backup-Schlüssel in `.gitignore` und getrenntem Secret Store.
- `pip-audit`, Lockfile, SAST, Secretscanner vor jedem Release, Abhängigkeiten pinnen. Fremdprojekte nicht ungeprüft als produktive Bibliotheken installieren.
- Minimum Privilege: DB-Gameuser nicht Superuser; Backup-Account ohne Spiel-Schreibrechte; Runtime Container ohne Root, read-only files, klar beschränkte Volumes, keine Docker-Socket-Freigabe an Webapp.

## 4. Deployment-Sollstruktur
```text
Internet [erst nach Go-Live-Freigabe]
  ↓ DNS + HTTPS (Caddy/Traefik/Nginx)
  ↓ rate-limit + security headers + TLS
Web API + statisches FUR UI
  ↕ private Docker network
PostgreSQL + Redis/Event Queue
  ↕ dedicated world_worker + scheduler
  ↕ Object/backup volume, alerting + metrics
SMTP-Provider [später; lokale Mailcatcher-Alternative]
Discord/External-Webhooks [optional; disabled-by-default]
```
- `compose.local.yaml`: binds auf 127.0.0.1, keine echten Maildienste, seedbare Testwelt, test-DB.
- `compose.staging.yaml`: realistische Prod-Profile aber private/Test-Secrets, Migrations-Preflight, Healthchecks, Backup/Restore.
- `compose.prod.yaml`: Proxy 80/443 erst nach expliziter Freigabe, bindet DB/Redis nicht öffentlich, Volumes persistent, Backup-Cron, Service-User, CPU/RAM/Disk-Limits, Restart-Policy.
- Pipeline: CI → Testimage → SBOM/Scan → signierter Release-Tag → manuelle `deploy-approved` Aktion → preflight → Backup → Migration → Rolling Restart → Smoke → Monitoring → Rollback-Plan.

## 5. Backup und Wiederherstellung
- Tägliche verschlüsselte PostgreSQL-Backups, Aufbewahrung mindestens 7 tägliche/4 wöchentliche/3 monatliche Kopien als anpassbares Ziel. Mindestens eine verschlüsselte Offsite-Kopie und periodischer Restore in isolierter DB.
- RPO/RTO als vorläufige Ziele: RPO 24h ohne WAL bzw. deutlich kleiner mit verifiziertem WAL/PITR; RTO ≤2h auf getesteter Hardware. Keine Zielzusage, bevor gemessen.
- Backup enthält DB, Ruleset-Versionen, Asset-Manifest, Uploads, Env-Schema und Deploy-Version — **keine Klartext-Secrets in Backup-Reports**.
- Wiederherstellung: Wartung→Snapshot→neuen isolierten Stack→Restore→Integrity-Replay→Vergleich Spieler/Ressourcen/Orders/Missionen→DNS/Traffic erst nach Owner-Freigabe.
- Spätestens monatlich Restore-Drill + Nachweis: UTC-Zeit, Snapshot-ID, Checksummen, Recovery-Dauer, DB-integrity und UI-Smoke.

## 6. Datenschutz / Spieler und Community
- Personenbezogene Daten minimieren. getrennte Account-Identität und Weltstatistik, Lösch-/Auskunfts-/Portabilitätsanfragen, konsistente Anonymisierung historischer Battles/Chatlogs soweit zulässig.
- Rechtstexte: Impressum/Datenschutzerklärung/Nutzungsbedingungen/Community-Regeln/ggf. Cookie-Einwilligung und Alters-/Jugendschutzprüfung vor öffentlichem Launch von Betreiber/Rechtsprüfung finalisieren.
- Kontaktformular, Abuse-Meldungen, Community-Meldesystem, Rechtsmittel/Appeal und klare Moderations-Zuständigkeiten.
- Telemetrie anonym/aggregiert wo möglich; Audit-Aufbewahrung regelbasiert, kein unnötiges dauerndes Tracking. DSGVO-Prozesse mit realen Fristen von Fachperson prüfen.
- Keine ChatGPT/API-/Discord-/Google-Keys aus früheren Chats verwenden; Integrationen opt-in und mit minimalen scopes.

## 7. Monitoring und Betriebsrunbooks
- Health: HTTP/Web-DB-Redis-Liveness/Readiness/Worker-heartbeat/Scheduler-lag; Metrics: p50/p95, Fehlerquote, Anzahl Missionen/Queue-Backlog, DB-Locks, Late Events, Login-Fehler, Ressourcenkonsistenz, Datenträger, Backup-Alter.
- Alerts: Worker-Ausfall, Backup >26h alt, DB volllaufend, ungeplant hohe 5xx, überlanger Queue-Lag, verdächtige Ressourcenverdoppelung, HTTPS-/Zertifikat-Fehler.
- Runbooks: Start/Stop, DB-Migration, Worker-Retry/DLQ, Security Incident, Key-Rotation, Backup/Restore, Welt-Freeze, Event-Stop, gehärtetes Admin-Onboarding, Spieler-Import/Export, Rollback, Notfallkontakt.
- Logs sind strukturiert mit request_id/world_id/event_id (keine Klardaten); Tracing wird an wenigen kontrollierten Orten aktiviert.

## 8. Betreiberschritte nach vollständiger lokaler Abnahme
1. Domain besitzen, gewünschten DNS-Anbieter festlegen; DNS-A/AAAA/CNAME korrekt auf VPS zeigen lassen.
2. VPS/Root bereitstellen (Linux LTS mit Security-Updates, mindestens passend zum gemessenen Lastprofil), separates unprivilegiertes Deploymentkonto, SSH-Keys + Firewall, SSH Passwortlogin deaktivieren, automatisierte Sicherheitsupdates prüfen.
3. Gültige HTTPS-Zertifikate über Reverse Proxy, TLS-Checks, HSTS erst nach Bestätigung.
4. SMTP-Domain/Provider und SPF/DKIM/DMARC konfigurieren; E-Mail-Absender/Retouren testen.
5. Alle Secrets neu und einzigartig generieren, Produktions-TOTP für Admin aktivieren, Testaccounts sperren, Staging-Flags deaktivieren.
6. Rechtliche Dokumente prüfen/veröffentlichen, DSGVO-Löschanfragen und Meldekanal testen, Datenverarbeitung mit Host/Provider prüfen.
7. Release-Candidate-Bericht und Restore-Test abzeichnen, Betreiber setzt `LAUNCH_APPROVED=true` erst nach explizitem Go-Live-Entscheid.
8. Erst dann Domain live, Smoke-Test, Last-/Betriebsüberwachung, anfängliches Spielerlimit und Rollback-Bereitschaft.

## 9. Klare Owner-Handoff-Formatvorgabe
`OWNER_HANDOFF.md`: `ID | externer Beschluss | was benötigt | sichere Eingabestelle | letzter Test ohne Zugang | Inbetriebnahmeschritt | Abnahme`. Alle realen Preise/Providerentscheidungen bleiben offen; Agent soll diese **nicht erfinden oder buchen**.



---

<!-- QUELLDOKUMENT: docs/05_TEST_STRATEGY.md -->

# FUR EMPIRE — VOLLSTÄNDIGE TEST- UND RELEASESTRATEGIE

## 1. Testpyramide (automatisiert + nachvollziehbar)
- **Unit:** Ressourcenarithmetik, Fraktionsboni, Research prerequisites, Defensivwerte, Kosten/Zeit, Speed/Distance, Kampf-RNG, loot/fuel, XP/skills, NC/NAP/Urlaub/Noobschutz, Regelnversions-Serialisierung.
- **Property-based:** `balances>=0`, `units>=0`, keine duplizierten Items/Claims, gleichbleibende Inventarsummen bei Transfers, deterministischer Kampf, keine Mission ohne Eigentümer, Kampf-/Markt-Caps.
- **Integration DB:** Postgres auf derselben Version wie Staging, Transaktionen, Retry/Deadlock, FK/CHECK/unique, Worker-Leases, Outbox, Sitzungen, Audit, Multiworld-Permissions, Migration alter FUR-2-Fixtures.
- **API/contract:** FastAPI OpenAPI + Schemas, 401/403/404/409/422/429, Rate-limit, CSRF, Content-Type, Origin, Session expiration, SSE auth, später OAuth/Discord optional.
- **E2E Browser:** Playwright Desktop Chrome/Firefox/WebKit und Mobile, Registration→Verification→World join→Build→Research→Train→Raid→Return→Market→Alliance→ACS→Espionage→Orbit→Season→Privacy request; Admin-Betrieb getrennt.
- **Accessibility:** WCAG 2.2 AA als Ziel, Tastatur, kontrastreiche UI, Screenreader-Semantik, responsive 320/360/768/1440/1920, Reduced Motion, Fokusfallen/Modale.
- **Security:** SAST/Dependency-/Secret-/Container-Scan, XSS, SQLi, CSRF, IDOR/world leakage, TOTP replay, reset links, brute-force, forged mission, websocket channel leakage.
- **Load/Soak:** realistische Mischung aus Lese- und Schreibvorgängen mit 200 aktiven/1.000 Accounts als initialem Richtwert. Dokumentiere Hardware/Testdaten/Laufzeit. 30 Minuten ohne verlorene Events/Ressourcen; p95 und Fehlerrate real messen.

## 2. Historische FUR-2-Akzeptanz (darf nicht still brechen)
- 64×64 Karte, 104 neutrale Posten, 20×20 Ansicht; Start 1200/1000/800; 8 Gebäude bis Level 10; Produktion exakt nach FUR-2; Depot 2000+2000×level je Rohstoff; 3 Techs (+15% Taktik, +10 Loot/Logistik, +15pp Engineer); 3 Basisunits; 5 Direktiven; 10 Angebote für 24h; Börse 50/60%; Fraktionen; Neulingsschutz 1h für **bestehende** Welt; PvP/NAP/Urlaub; Zitadellenziel, Ranking 10/20/100; Saisons und 0–100pp Live-Boni; Session/TOTP/E-Mail.
- Regression auf anonymisiertem Snapshot, einschließlich aktiver Missions-/Bau-/Forschungs-/Trainings-Queues. Migration legt bei laufender Alt-Mission gepinnte FUR-2-Version fest.
- Neue Regeln nur explizit je neuer Welt (z.B. FUR-3); Migration von bestehenden Welten erfordert bewusstes, dokumentiertes Umschaltdatum und Vergleich der Daten.

## 3. Race-, Crash- und Replay-Matrix
| Fall | Parallelität/Fehler | Sollzustand |
|---|---|---|
| Doppelte Mission | 20 gleichzeitig gleiche `command_id` | 1 Mission, 1 Ressourcen-/Unit-Debit |
| Doppelter Marktkauf | 20 Käufer gleichzeitig | exakt 1 Zuschlag, Ware nur einmal |
| Koloniegründen | 100 Spieler gleiche Kachel | maximal 1 Eigentümer |
| Quote/Claim | 10 Direktiven-Claims parallel | Belohnung einmal |
| Worker stirbt | nach DB-Commit vor Ack | Wiederholung keine Doppelwirkung |
| Gleichzeitige Kämpfe | 10 Angriffe auf gleiche Basis | deterministische Ankunftsreihenfolge |
| Saison-Finalisierung | Worker doppelt | 1 Archiv, kein permanent world reset |
| Research bei Ausgaben | gleichzeitiger Bau+Research | keine negative Resource, klarer Gewinner |
| Chat/WSS | Unbefugter errät Channel | kein Zugriff/kein Event |
| Backup/Restore | 1000 Accounts + events | konsistente Missionen, unveränderte Geldsumme |
| Orbit-Kolonisation | gleiche Planetenposition | einmalige Reservierung |
| Terra↔Orbit-Transport | Retry/Return/Overflow | Ledger vollständig, kein Warendupe |

## 4. Balance und langfristige Spielbarkeit
- Simulation 1/7/30/90/180 Tage mit Anfänger/Gelegenheitsspieler/Vielspieler, 10–1000 simulierten Spielern; gleiche Welten-Seed-Fälle, Reproduzierbarkeit.
- Fairnessziele vorläufig: Startpositionen erreichbar, keine garantiert unbesiegbaren Eröffnungen, PvP-Verlustregeln begrenzen Griefing, KI-Spawn-Budget nicht unendlich, Ressourcen/Power-Inflation auditierbar, niemals Pay-to-win.
- Spionage hat echten Informationswert ohne komplette Gratis-Enthüllung; Kampf soll unterschiedliche optimale Aufstellungen haben. Jede Einheit benötigt eine Rolle, Konter und Nutzbarkeit in wenigstens einem Szenario.
- Weltwirtschaft: Marktbilanz, NPC-Sinks, Ressourcenfaucets, maximal mögliche Gewinne, Depotgrenzen, Betrugs-/Botszenarien, Preisextreme. Simulationsbericht mit konkreten Defaults und Änderungsgründen.

## 5. Release-Gate und Artefakte
- Keine Blocker hoher Kritikalität. `FEATURES.json` zu 100% mit Code/UI/Policy/Test/Dokumentation nachgewiesen. Alle Tests erfolgreich (echte Kommandos und Logs, keine Dummy-Häkchen). Reproduzierbares Image, SBOM, Lizenz-/Asset-Freigaben.
- `RELEASE_CANDIDATE_REPORT.md`: Build/Commit/OS, exakte Kommandos, Testzahlen, Load-Resultate, bekannte Bugs, Real-World-Grenzen, Smoke-Screenshots, Screens-Liste, Dependency- und Lizenzreport, Restore, Integritätsprüfungen.
- `PERFORMANCE_REPORT.md`: Hardware, Version, DB-Größe, Szenarien, p50/p95/p99, Queue-Lag, Error Rate, Lastprofile, Bottlenecks, kapazitive Empfehlung vor Serverkauf.
- `SECURITY_REPORT.md`: Threat Model, Scans, Fix-Verweise, offene akzeptierte Risiken + Owner-Freigaben.
- `TRACEABILITY.md`: per Feature-ID implementierter Codepfad + Tests/Screen. `OWNER_HANDOFF.md` nur externe Voraussetzungen.
- `RESUME_STATE.json`: letztes abgeschlossenes Epic, nächste nicht verifizierte Feature-IDs, lokale Branch/Commit, Fehler/fehlende Rechte und reproduzierbare Testkommandos. Ein neuer Agent muss ohne erneutes Ratespiel fortsetzen können.



---

<!-- QUELLDOKUMENT: docs/06_SOURCE_LICENSE_REGISTER.md -->

# FUR EMPIRE — NEUN REFERENZQUELLEN, CODEPROVENIENZ UND LIZENZGRENZEN

**Stand:** 06.11.2026. GitHub-Repositories im vorigen Architektur-Review anhand von API-Metadaten, Dateibäumen und repräsentativen zentralen Dateien ausgewertet. Nicht jede fremde Zeile und jedes einzelne Asset wurde juristisch auditiert. Das Quellenverzeichnis ist **Design-Recherche**, keine pauschale Codefreigabe.

| Kürzel | Repo / geprüfter Hauptstand | Lizenz laut Repository bzw. Dateien | Verwendbarer Erkenntnisbereich | Direkter Copy-Paste-Status |
|---|---|---|---|---|
| D | [ioying/devana](https://github.com/ioying/devana) · `4e64e5a72c5ed00e94e1464992808d9e75f9cef1` | `docs/license.txt`: eigener permissiver Lizenztext, inklusive Attribution, Markierung von Änderungen und Copyright-Hinweis | 2D-Raster, Fraktionen, modularer Basenausbau, Krieg/Frieden, Ressourcen, Kampfsimulator | Nur nach Einzeldatei-/Provenienzprüfung und Einhaltung der Lizenzauflagen |
| TW | [laserswald/Tribal-Wars-Open-Source](https://github.com/laserswald/Tribal-Wars-Open-Source) · `2bd72a062ea1ffa235e50e7d723f37df5b5c6eee` | Kein Repo-Lizenzfeld; eigene PHP-Header nennen CC BY-NC-ND 3.0; Assets zudem unklar | Historische UI-Referenz, Karten-/Allianzbildschirm als Analyseobjekt | **Nicht kopieren** |
| U | [ugml/php-client](https://github.com/ugml/php-client) · `acb7ae51c04cbebdd65d321633f4f71c910e4ba1` | AGPL-3.0 | MVC-Struktur, Datenobjekte, Fleet/Building/Research, Tests | Nicht in proprietären/anders lizenzierten Kern übernehmen; Anforderungen der AGPL gesondert prüfen |
| OGX | [lanedirt/OGameX](https://github.com/lanedirt/OGameX) · `f61cbede42fe4a91cd7d25f8bac963f2804f3af5` | MIT für eigenes Backend; README erklärt Gameforge-Rechte an Artwork und Frontend | Missionsklassen, Eventserver, PHP/Rust-Kampf, Race-Tests, Planet/Forschung/Flotte | MIT-Code ggf. mit Notices; **Artwork und Drittinhalte nicht kopieren** |
| X4 | [XGProyect/XGProyect](https://github.com/XGProyect/XGProyect) · `b3971d873f7512c62b4c981f285deb4d109349f4` | GPL-3.0 | GameObjectRegistry, Entwicklung, Shop/Administration, Backup, Settings | Kein Import ohne explizite GPL-Veröffentlichungsstrategie |
| X3 | [XGProyect/XG-Proyect-v3.x.x](https://github.com/XGProyect/XG-Proyect-v3.x.x) · `612fe05945417552d2eee750761ff8c0ade454f5` | GPL-3.0, archiviert | Missionen, Forum, Diplomatie, Flotten/Allianzen | Kein Import ohne GPL-Plan |
| X3L | [XGProyect/XG-Proyect-v3.x.x-Languages](https://github.com/XGProyect/XG-Proyect-v3.x.x-Languages) · `945d1ec6ef2523327ea15208a080e6f5e90b1e53` | GPL-3.0 | Übersetzungsstruktur, Locale-Trennung | Texte selbst neu schreiben/übersetzen |
| XL | [XGProyect/legacy-versions](https://github.com/XGProyect/legacy-versions) · `44cb0f0b2ba7de13d9ec670b31931c8842b431db` | Kein konsistentes Repository-Lizenzfeld; enthält historische Archive | historische Architekturvergleiche, keine moderne Laufzeitbasis | Einzelarchiv nicht ohne Prüfung nutzen |
| X2 | [XGProyect/XG-Proyect-v2.10.x](https://github.com/XGProyect/XG-Proyect-v2.10.x) · `e9a088a36cb135ab2986c47aaad877838e7f2fdc` | GitHub 'Other'; `LICENSE.md` im geprüften Checkout leer | historische Kampf- und Flottenrechenmodelle | **Nicht kopieren**, Rechte unklar |

## Grundlegende Lizenzentscheidung

**FUR-Grundcode = eigenständige Implementierung.** Mechanikgattungen (Bauwarteschlange, Fleet-Mission, Forschung, strategische Karte) können konzeptionell untersucht werden; Quelltext, spezifische Assets, Logos, originalsprachliche Texte und rechtlich geschützte Eigenheiten dürfen nicht gedankenlos kopiert werden. MIT-Code kann im Einzelfall übernommen werden, wenn alle Urheber-/Lizenzhinweise und Dritt-Abhängigkeiten erhalten bleiben. GPL/AGPL-Lizenzen können Copyleft- bzw. Quellcodebereitstellungspflichten auslösen; das ist vor einer echten Übernahme mit einer geeigneten Rechts- und Projektstrategie zu entscheiden. CC BY-NC-ND und fremde geschützte Grafiken werden nicht verwendet.

## Agentenpflichten bei jedem importierten Fremdasset/-paket

1. Erzeuge/aktualisiere `third_party/PROVENANCE.json` mit `repo`, `commit`, `file`, `author`, `license`, `modifications`, `notice_required`, `copyright_claims`, `risk`, `reviewed_by`.
2. Automatischer License-/Dependency-Scanner; Notices in `THIRD_PARTY_NOTICES.md` und ggf. `/legal/licenses` verfügbar.
3. Fehlende Lizenzfreigabe → eigenständig implementieren oder eigenes Asset erzeugen; niemals fremde Bilder als vorläufige Produktionsplatzhalter einbauen.
4. Originelles FUR-Branding, neue Kommandanten-/Fraktions-/Planeten- und Schiffsbezeichnungen, eigener UI-Stil und eigene Lore.
5. Rechte auf User-FUR-Assets und mögliche Community-Beiträge vor der Veröffentlichung prüfen; Upload-Lizenzen und Entfernen-/Report-Prozess dokumentieren.

**Hinweis:** Dies ist eine technische Lizenzinventarisierung und keine anwaltliche Entscheidung darüber, welche konkrete Mischung rechtlich zulässig wäre.



---

<!-- QUELLDOKUMENT: docs/07_COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX.md -->

# FUR EMPIRE — SCREEN-, INTERAKTIONS- UND GAMEPLAY-KATALOG

**Verbindliche Regel:** Jeder Screen funktioniert mit Tastatur, Mobile und Maus; alle Buttons/Filter/Modale senden echte autorisierte Commands; Empty/Loading/Error/Success/Offline sind implementiert. Keine Links auf nicht existente Seiten. Bei jedem Screen Hilfetext, Spielregeln und aktuelle Daten statt Hardcoding.

## A. Öffentlicher Bereich & Identität
- Landing: eigenes FUR-Logo, Überblick, Screenshots **nur aus der FUR-Anwendung**, Weltliste, Features, News, Sprache, Registrieren/Anmelden, Betreibertexte.
- Register: Nutzername/Email/Passwort, Passwortstärke, Zustimmung nur zu notwendigen Regeln, Double submit vermeiden, Email-Verifikation, Captcha/Rate-Abuse-Schutz datensparsam.
- Login: 2FA-Schritt, Sessionliste, andere Sitzungen widerrufen, Logout, Failed-login-Telemetrie, E-Mail Recovery, Backupcodes.
- Konto: Sprache, Zone, Datenschutzexport/Löschanfrage, Newsletter-Einwilligung getrennt, Sicherheitsschlüssel/TOTP, Benachrichtigungseinstellungen.

## B. Onboarding & Kommando
- Startwelt wählen, Fraktionsvergleich, Startkolonie, Missions-/Karten-Tutorial, erste Direktiven mit Claim, Anzeige Anfänger-Schutz, Hilfe.
- Dashboard: Produktion/s, Lager/Reserve, Premiumstatus **nicht als Echtgeldzwang**, Imperiumspower, aktuelle Bau/Forschung/Rekrutierung, Missionszeitstrahl, Globalwarnungen, Inbox, Allianz, aktive Ereignisse, Quests.
- Kolonien: Gesamtübersicht, Detailtab, Wechsel, Umbenennen, Hauptkolonie, Gründung, Versetzen/Verlassen mit geschützter Bestätigung, Transferkonvoi und Versorgung.

## C. Produktion, Bau, Forschung
- Wirtschaft: Live-Deltas, Ressourcenverlauf, Fertigungs- und Depotlimits, Eenergie/Unterhalt, Reserveclaim, geplante Kosten, Fraktions-/Eventboni mit Formel-Breakdown.
- Bau: Kacheln/Buildings, Preconditions, Kosten, Zeiten, Slots, Start/Cancel/Sort, Vergleich Level N→N+1, Spezial-Upgrade/Prestige.
- Forschung: Voraussetzungen als interaktiver Graph, Techinfo, Lock-Gründe, Level/Zeiten/Kosten, Forschungswarteschlange, globale und koloniale Techs, Doktrin-/Fraktionspfade.
- Rekrutierung/Verteidigung: Detailvergleich Units, Counter und Terrain, Produktionsaufträge, Slots, dauerhafte Verteidigungsinstallationen, Garnisonen, Reparatur.

## D. Terra-Karte und Missionen
- 2D-Karte: Map-Pan/Zoom, freie/aktive Sektoren, NPC/Spieler, eigene/allierte Positionen, Fog, Gebietskontrolle, Suche, Favoriten, Terrain-Legende, Hilfe, Listenalternative.
- Sektor-Overlay: Besitzer/Verteidigung abhängig von Intel, verfügbare Missionen, Schutzstatus, Angriffsvorprüfung, mögliche Reisezeit, Truppenauswahl/Cargo.
- Missionszentrum: Hin/Rückflug, Status, Front, Abbrechen/Rückruf, Ankunfts-Timeline, Dispatch-Presets, Versorgungsaufträge, Expeditionsauswahl.
- Kampf: Simulator und Unsicherheitsbereiche, Battle-Report, Damage/Armor, Runde-für-Runde-Replay, nachweisbare Regelversion/Seed, Attribution bei Allianzoperation.
- Spionage: Intel-Fog, Spähbericht, Gegenaufklärung, Warnungen, Intel-Ablauf.

## E. Sozial/Allianz
- Allianzsuche, erstellen/joinen, Rollen/Einladungen, Diplomatie und Verträge, Allianz-Forum, Pinnwand, Kasse und Projekte, Kriegsmobilisierung, ACS und Bündnis-Verteidigung.
- Chat Welt/Allianz/Privat, Postfach, Berechtigungen, Block-/Freundesliste, Profil, Erfolge, Notizen, Berichtsfreigabe, Nachrichten melden, Moderationsfeedback.
- Handel: Sofortbörse, Spieler-Orderbuch, angenommene/abgelaufene Angebote, Preisstatistik, interne Lieferungen, Escrow-/Reserveanzeigen; keine zwischen Welten handelbare Ware.

## F. PvE/Quests/Endgame
- NPC-Fraktionen, Regionen- und Raidkarte, Eskalationsstufen, Boss-Screen/Teilnahme, Expeditionsevents, Belohnungsansprüche, Questkatalog (Einführung/Täglich/Wöchentlich/Story), Achievementvitrine, Hall-of-Fame, saisonale Objectives.

## G. Orbit
- Navigationskarte Galaxie→Sonnensystem→Orbitalslot, Erkundungsnebel, Kolonisation, Orbit-Kolonieansicht, Planeten/Gebäude/Energie, Forschung, Werft/Flottendesigner, Sprungtor/Mond/Sensorik, Trümmer/Repair, Flottenbewegungen, Weltraumschlachten, Expeditionen und Replays.

## H. Spielleitung
- Owner/Gamemaster-Konsole: Spieler/Allianz/Region/Welt/Saison/Events, Featureflags, Regelpreview, Audits, Integrität, Backups und Restore-Drill, Workerstau und DLQ, Mutes/Bans/Einsprüche, E-Mailstatus, Moderationsmeldungen, zentrales Ankündigungscenter, Spielstatistiken; Vier-Augen-Gate bei kritischen Vorgängen.

## I. Navigation und Performance
- Desktop: linkes Menü + obere Statusleiste + Quick Switch, keine Vollseitenreloads nötig, aber progressive enhancement.
- Mobile: Bottom Nav, Drawer und Kartenliste, 44px Touch-Ziele, horizontal scrollende Tabellen mit Alternative, Karte als Canvas/WebGL oder optimierte Tile-Ansicht, progressive Pagination.
- Realtime: chronologische Events, Badges, Connection-/Reconnect-Indikator, Polling-Fallback, optimistische UI nur für harmlose Aktionen, Server bleibt Wahrheit.

## J. Durchgehende Akzeptanz pro UI-Aktion
1. Actor/World/Owner/Rolle validiert, Idempotency und Conflict sauber.
2. Im UI ist sichtbar, was passiert, wie viel es kostet, wie lange es dauert und warum es ggf. nicht geht.
3. Gewählte Aktion ändert den richtigen Datensatz; andere Welten/Spieler bleiben unberührt.
4. Fehler und Abbruch ändern nichts oder erstatten genau einmal; Handhabung bei vollem Depot und Worker-Timeout.
5. Jede Sprache liefert korrekte Pluralisierung, Formate, Hilfe und barrierearme Interaktion.
6. Automatisierter API- und Browsernachweis nach Ergänzung eines neuen Screens; `TRACEABILITY.md` aktualisieren.



---

<!-- QUELLDOKUMENT: docs/08_GAME_MECHANICS_STATE_MACHINES.md -->

# FUR EMPIRE — GAMEPLAY-REGELDETAILS UND ZUSTANDSAUTOMATEN

Dieses Dokument ergänzt das GDD mit Zuständen, Abbruchpfaden und Default-Regeln für eine robuste Agentenimplementierung. Ursprungsdaten FUR-2 sind in `rulesets/FUR_2_REFERENCE_RULES.json` getrennt von **neuen, vorgeschlagenen** Defaults in `FUR_3_ORBIT_1_PROPOSED_RULES.json`. Die neuen Balancewerte sind keine bezeugten Altweltwerte; vor Release simulieren und per Ruleset-Version fixieren.

## 1. Welt und Kolonie — Objektlebensläufe

`World`: `planned → generating → verified → online ↔ maintenance → frozen → archived`. Für permanente Welten ist kein automatisches Reset erlaubt. Ein neues Weltobjekt besitzt `seed, width,height, generation_version, ruleset_hash, server_timezone_display, world_type` und einen streng isolierten Datenraum.

`WorldPlayer`: `invited/registered → onboarding → active ↔ vacation → suspended → anonymized`. Weltjoin erstellt **genau eine** Startkolonie über atomare Reservierung. Fraktionswahl ist einmalig; Respec existiert nur in neuem Regelmodus, mit sichtbarem Preis und Cooldown.

`TerraSector`: `unexplored | free | neutral_outpost | player_colony | player_outpost | ruins | protected | impassable`. Besitzwechsel benötigt Sperre und gleichzeitig gültige Besitz-/Mission-/Diplomatie-Policies. Unbekannte Kacheln zeigen keine geheimen Einheitendaten.

`Colony`: `establishing → active → relocation_pending | abandon_pending → abandoned`; letzte Kolonie niemals aufgebbar, offene Bau-/Trainings-/Forschungs-/Missionsevents sicher kompensieren. Outposts sind keine Vollkolonien; Upgrade zu Kolonie kostet selbstständigen Kolonieslot.

## 2. Ressourcentransaktionen

`wallet/resource`: `available`, `reserved`, `in_transit`, `reserve`, `spent` als **separate Buchungsstatus**, nicht willkürliche Feldänderung. Für jede Aktion ist Ledger-Summe korrekt: Ein Kauf verschiebt Wert aus Spieler-Guthaben in Anbieter-Escrow, später nur einmal zum berechtigten Empfänger. NPC-Belohnungen sind explizite Faucet und Bau/Truppen sind explizite Sink.

Produktionsintegration: `elapsed = monotonic server time derived from UTC corrected transitions`; berechne exakte Segmente für Urlaub, Buffstart und Ende. Nutze feste Bruchzahlen statt Float-Rundung, belohne nicht bei häufigem Browser-Polling.

`MarketOffer`: `open → accepted | expired | cancelled | administratively_frozen`. Kauf und Cancel parallel: genau ein Endzustand. TTL 24h aus FUR-2; Mengen/Caps nach Welt-Regeln. Duplikate und Marktmanipulationen prüfen.

`CraftOrder`: `queued → running → completed | cancelled | failed`; Inputs atomar escrowed, Output bei Completion einmal credited; Recycler darf keine Materialschleife mit Netto-Gewinn erlauben.

## 3. Gebäude, Forschung, Produktion

`QueueItem`: `pending → running → completed`; von `pending/running` kann je Regeln `cancelled` entstehen; `failed` nur intern mit Wiederaufnahme-/Refundpfad. Zeitfortschritt aus Worker. Gleicher Command mehrfach hat immer dieselbe Wirkung. Forschungsvoraussetzungen gegen Serverkatalog; abgebrochener Erzeuger darf bereits laufende Forschung nicht in unbestimmten Zustand bringen (Policy je Regelversion).

Energie: in FUR-3 pro Kolonie Energieproduktion und Verbrauch, unter Energiemangel ordentliche priorisierte Drosselung bis auf konfigurierten Mindestwert; im FUR-2-Bestand keine rückwirkende Energiedrosselung. Unterhalt darf nie zu negativem Kontostand führen; stattdessen `depleted`/begrenzte Performance/Safe-return.

Technologieeffekt-Caps und die genauen Bau-/Forschungskosten stehen im versionierten Regelkatalog; Einheiten- und Bauobjekte tragen stabile IDs, keine UI-Positions-IDs.

## 4. Transport und Missionen

`Mission`: `draft → dispatched → travelling_out → arrival_pending → resolving → returning → completed`; Alternativzustände `cancel_requested → returning | cancelled`, `failed_retryable`, `failed_terminal` mit kompensierter Waren-/Truppenbilanz. Jeder Übergang als atomarer Domain-Event mit Unique-Key und Outbox.

Bei Dispatch: aktive Missionscap, Herkunfts- und Zielbesitz, freie Units, Fuel/Cargo, Pakt/PvP/Urlaub/Neulingsschutz, Rate Limit, vollständige Ressourcenreservierung, due_at, ruleset-hash. Bei Ankunft dynamische Policy nochmals prüfen; illegale Attacken werden sicher zurückgerufen. Bei Rückkehr ins volle Depot überschüssige **Lieferungen** in Reserve, während passive Produktion am Cap stoppt.

`AllianceOperation`: `assembling → locked → travelling → resolving → returning → completed | cancelled`. Join nur während Assembling, Membership/Owner und Startzeit validieren; Ankunft synchronisieren; Teilnehmeranteil und eventuelles Loot pro Besitzer deterministisch und rechtmäßig zuweisen.

## 5. Kampfsystem FUR-3

- Kampf startet nur aus gültiger Mission, nach Sperrung auf Ziel/Teilnehmer, mit gepinnter Regelversion.
- Bis zu sechs Runden mit gemeinsamen Frontstapeln; konkrete Reihenfolge: Initiative und target policy; Treffer mit versioniertem RNG, dann Schild, Panzerung, Hülle; nach jeder Runde Tote und Spezialeffekte; Rückzug entsprechend Policy.
- Kein Sieger bei Gleichstand nach Rundenlimit: Verteidigungsposition bleibt erhalten. Eroberung erst mit eigenem Belagerungsziel und gültiger Einheit nach dem Kampf.
- Jede Runde erzeugt Replaydaten, State-Hash und Verlustliste. Renderer bekommt nur autorisierten Bericht; Spionage bestimmt Datenfreigaben.
- `simulate` läuft in reinem Modul ohne Speichern, Zahlentransfer oder Loot-Abzug.
- Übermacht darf nicht automatisch Endlosdominanz erzeugen: Combat-Log-Balance, Attrition und Recovery-Caps werden in Simulationsberichten beobachtet.

## 6. Orbit und Flotten

`OrbitalBody`: `unknown → discovered → claimable → colonization_reserved → occupied | abandoned | destroyed`. Uniqueness `(world_id,galaxy,system,slot)`; Mond/Stationen referenzieren parent-orbital-body. Ein Flug nimmt Fuel und Einheiten nur einmal ab; Cargo wird als Escrow bewegt.

`FleetMission` übernimmt die Basiszustände der Terra-Mission. `Jumpgate`: `ready → transfer_resolving → cooldown → ready` mit Atomic Lock über beide Tore; no two concurrent jumps of same fleet. Trümmerfeld hat Masse, Claim-/Salvage-Transaktionen und Ablauf. Alle Operationen in Orbit teilen dieselbe Konto-/World-Policy und Auditlogs.

## 7. Allianz, Krieg und Diplomatie

`Invitation`: `pending→accepted | rejected | expired | revoked`. `Treaty`: `proposed→accepted→terminated | rejected | expired`, unilateral `war_declared` mit War-Notice und regelkonformen Schutzperioden. `War`: `declared→active→ceasefire→settled→archived`; Punkteregel, Siegziele und Beitrag nachvollziehbar.

Allianzkasse: jeder Beitrag/Sink im eigenen Ledger; große Entnahmen per Vier-Augen-Genehmigung, Anfragen haben Ablauf und können nicht doppelt freigegeben werden. Führungstransfer erfordert Zielbestätigung und schließt die letzte-Leitung-Lücke.

## 8. Welt-Events, NPC und Quests

`WorldEvent`: `draft→scheduled→announced→active→resolving→finished→archived | cancelled`. Boni zeitsegmentiert und gedeckelt. `NPCOrder`: Spawn-/Move-/Raid durch begrenzte Worker-Budgets, reproduzierbare Seeds, keine Kolonieüberschreibung.

`Quest`: `locked→active→completed_unclaimed→claimed`; Belohnung darf nur einmal vergeben werden; tägliche/wöchentliche Versionen haben UTC-Reset und idempotente Claim-ID. `Season`: `scheduled→active→finalizing→archived`, Abschluss nur genau einmal mit eingefrorener Rangliste.

## 9. Game Balance und Fairness

- Spieler bleiben nach Niederlage spielbar. Neue Welten: Anfänger-Schonfrist, Powerband, Recovery-Cooldown. Bestehende FUR-2-Welten bekommen nicht still eine geänderte 1h-Regel.
- Outposts generieren im FUR-2-Modus keine Bestände neu; neue Welten verwenden nachwachsende neutrale unbesetzte Ziele, ROI-Budgets und Outpost-Bonus-Sättigung. Für Migrationswelten kann der Admin eine neue Regelversion bewusst aktivieren.
- Jede Rolle muss einen Gegen-/Nutzeneffekt besitzen. Kein globaler Kampfverstärker ohne Limit. Kein Echtgeld-Pay-to-win.
- Balancing ist ein laufender Entwicklungsprozess mit Simulation, aber vor Release wird ein getesteter Regelstand eingefroren.

## 10. Minimale, testbare Spiel-Journeys

1. Nutzer A/B registrieren, Email verifizieren, 2FA, Weltjoin, Startressourcen, Fraktion, Direktive, Holz/Wirtschaft und Forschung; Browser schließen, Queue durch Worker schließen.
2. A gründet zweite Kolonie und transportiert Rohstoffe; B versucht dieselbe Kachel (scheitert); A baut Aufklärung und sieht nur erlaubte Infos.
3. A spioniert B, B entdeckt (optional) und erhält Bericht; A berechnet Kampf, sendet Raid, Rückkehr mit Verluste/Beute; keine doppelte Auszahlung.
4. A/B schließen Freundschaft/Allianz, gründen Allianzkrieg/Verteidigung/ACS auf NPC, splitten Verluste/Beute und dokumentieren Siege.
5. A entsperrt Orbit, kolonisiert Slot, baut Mine und Werft, sendet Flotte auf Expedition/Attack, nutzt Trümmerbergung und Tor.
6. Saison startet, Events wirken, Hall of Fame archiviert, Dauerwelt unverändert; Admin behebt steckengebliebene Mission auditierbar; Datenschutzexport ohne fremde Daten.
7. Komplett neuer Compose-Stack reproduziert Migration, Seeds, Testaccounts; Backup→isolierter Restore→identische Statusdaten, kein öffentliches Deployment.



---

<!-- QUELLDOKUMENT: docs/09_AGENT_ACCEPTANCE_AND_OWNER_HANDOFF.md -->

# FUR EMPIRE — EIGENTÜMERÜBERGABE UND ABNAHME NACH DER IMPLEMENTIERUNG

## Was als vollständig lokal fertig gilt
- Jede Feature-ID aus `spec/FEATURES.json`: fachliche Umsetzung, UI, Datenhaltung, Sicherheitsprüfung, übersetzte Texte/Hilfe, automatisierter Test, Ergebnisbeleg und `verified`.
- Frischer Checkout startet ohne manuelle Programmierung via dokumentierten Compose-/CLI-Befehlen; ohne Live-SMTP laufen Test-Mails sicher in einem Mailcatcher.
- Testdaten/QA-Accounts können isoliert gelöscht werden, ohne eine echte Nutzerwelt zu gefährden. Kein Fake-Gameplay.
- Zwei Spieler und zwei Welten lassen sich live gegeneinander testen; sämtliche Wirtschaftsketten, Events, War/Alliance, Terra/Orbit, Saisons und Admin-Prozesse funktionieren unter wiederholter Last.
- Release umfasst dokumentierten Restore-Test, Sicherheitsreport, Lasttest, Lizenz-/Assetregister und einen neuen Release-Tag.

## Was erst nach deiner Rückkehr benötigt wird
| Externe Aktion | Agent kann vorher erledigen | Betreiber macht später |
|---|---|---|
| Domain | DNS-Vorlage, Reverse-Proxy, TLS-ACME-Config und Test-Domain-Konfig | Domain kaufen, Registrar/DNS-Zugang bereitstellen |
| VPS/Root | Serveranforderungen aus gemessenem Lastprofil, Compose-/IaC-Deploy, Hardening-Runbook | Host auswählen, Vertrag/Server bestellen, SSH-Zugang sicher einrichten |
| HTTPS | TLS-Config und interne Stagingtests | DNS auf Host zeigen lassen und Live-Zertifikat prüfen |
| SMTP | Mailcatcher, E-Mail-Templates, SMTP-Adapter | Provider, Domain-Sender, SPF/DKIM/DMARC konfigurieren |
| Rechtliches | Mustervorlagen/Platzhalter und Datenfluss-Dokumentation | Rechtskonforme Impressum/Datenschutz/AGB/Jugendschutz prüfen/freigeben |
| Secrets | Variablenschema, Generierungsskripte, `.env.example` | Produktive Secrets generieren, sicher einspielen und alte veröffentlichte Tokens rotieren |
| Admin-Freigabe | Rollen/TOTP/Account-Onboarding testen | Eigene Adminidentität final bestätigen, TOTP einrichten |
| Live-Freigabe | Gates, Restore-, Performance-, Security-Reports | Belastbaren Go-Live-Beschluss treffen und Deployment genehmigen |

## Eigentümer-Abnahmetest (real, nicht nur Screenshots)
1. Neue Welt erstellen, Account A/B registrieren, Regeln-/Beginnerschutz-/Fraktionen prüfen.
2. Wirtschafts- und Bauaktionen ausführen, schließen/neu öffnen, Serverworker stellt Queues fertig.
3. Karte mit NPC-PvE, Spionage, Allianz-PvP und Gemeinsamem Angriff testen, echte Logs und Verluste nachvollziehen.
4. Mehrkolonien und Transport einschließlich vollen Depots/Ressourcenreserve testen.
5. Orbit freischalten, Flotte senden, Mond/Station/Bergung/Expedition gegen echte DB-Events prüfen.
6. Saison-Event/Weltboss starten, Saisonabschluss, Dauerwelt bleibt intakt.
7. Security: falscher Nutzer kann keine fremde Kolonie lesen/manipulieren, doppelte Marktannahme erfolgt nur einmal, TOTP kann nicht repliziert werden.
8. Backup in separater Testinstallation wiederherstellen und Ergebnisse vergleichen.
9. Erst nach allen Schritten öffentliche Domain und Echtgeld-/Live-Integrationen gesondert freigeben.

**Wichtig:** Auch wenn der Agent alles implementiert, ist ein öffentlicher Start nie nur ein Domainkauf. Host-Sicherheit, Supportkapazität, Moderation, Lastprofil, Betreiberpflichten und laufende Updates bleiben dauerhafte Aufgaben.



---

<!-- QUELLDOKUMENT: docs/10_OWN_ASSETS_BRANDING.md -->

# FUR EMPIRE — VOLLSTÄNDIGES EIGENSTÄNDIGES GRAFIK-/UI-DESIGNSYSTEM

## 1. Identität
- Titel: **FUR EMPIRE**; optionaler Untertitel **Genesis of the Network**; originelle Cyber-Fantasy/Strategie statt Kopie von Die Stämme oder OGame.
- Kerntöne: Onyx `#0C1018`, dunkles Panel `#152635`, Gold `#C99A43`, Holografie-Cyan `#37B6C6`, Warnung `#E8B65B`, kritische Warnung `#D45F64`, helle Schrift `#F0F2F5`.
- Keine fremden Logos, OGame-Schiffsgrafiken, Tribal-Wars-Screenshots, geschützte UI-Skins oder als frei verfügbare Bilder behaupteten Assets. Eigene Herkunftsdaten als `assets/MANIFEST.json`.

## 2. Assetfamilien (alle erforderlich, eigene Erstellung)
- Corporate: Wordmark/Signet/Storymark, Favicon/Social-Square/OG Cover, Loading, Error, PWA-Icons.
- Terra: neun Terrain-Tile-Typen × Tag/Nacht × minimap/Map/large, Siedlungen in mind. fünf Entwicklungsstufen, Region-/Fog-/Frontlinien-Overlays, Fraktionsfarben, NPC-/Quest-/Eventmarker.
- Gebäude: FUR-2 acht Bestandsgebäude als eigene Illustrationen; neue 20 Gebäudetypen mit Icons und Isometrie/Detailansicht; Sperrstatus/Upgrade-Layer.
- Truppen: FUR-2 drei Basiseinheiten sowie zwölf neue Einheitentypen, zusätzlich sechs Fraktions-Spezialeinheiten; Icon, Portrait, Silhouette, animierbare Varianten optional.
- Krieg: Waffen-/Panzer-/Schild-/Status-Icons, Marschpfeile, Replay-Timeline, Erfolgs-/Verlust-Badges, Garnisonen, Artillerie, Spionage/Counterintel.
- Orbit: Galaxiekarten/Planeten, Monde/Stationen, Nebel-/Trümmer-/Warp-Effekte, 14 eigene Raumschiffklassen, Planeten-/Flottenstatus, UI-Badges.
- Sozial: drei Fraktionsembleme, Allianzbanner/Rank-Badges, Arena-, Saison-, Boss- und Achievement-Medaillen.
- Avatar/Community: eigene spielbare FUR-Rollen, Accountprofil, Hall of Fame; keine fotorealistischen fremden Charaktere oder markenrechtlich problematischen Vorlagen.

## 3. UI-Komponentenbibliothek
`GameShell`, `MainNav`, `MobileBottomNav`, `WorldSwitcher`, `ResourceBar`, `MissionTimeline`, `QueueList`, `UnitCard`, `BuildingCard`, `ResearchTreeNode`, `MapTile`, `SectorDetails`, `IntelReport`, `BattleReplay`, `MarketOrder`, `AllianceMember`, `ChatChannel`, `NotificationCenter`, `ConfirmDialog`, `ErrorPanel`, `AdminAuditRow`.

Jede Komponente braucht Loading/Empty/Error/Disabled/Success, Keyboard-Focus, Tooltip-Alternativen, DE/EN/VI/ES/TR und visuelle Regressionsscreenshot-Tests. Kontrast und Textgröße werden getestet, Icons zusätzlich mit Labels.

## 4. Typografie und Performance
- Zugelassene Open-Source-Schrift mit Lizenznotice oder System-Font-Stack, keine proprietären Fontdateien ins Nutzerpaket kopieren.
- PNG/WebP/AVIF responsive Größen, SVG für Symbole, verlustarme komprimierte Tiles, Sprite-Atlanten nur wenn eigener Assetnachweis.
- Keine komplett gerenderte 64×64-Karte für jedes Polling; Tiles/Viewport cachen. Reduced-motion-Option, keine blinken­den Zwangsanimationen.

## 5. QA / Recht
- `assets/MANIFEST.json`: `id,file,creator,license,source,created_at,reviewed,usage` für jedes Asset.
- Ein asset darf erst produktiv eingebunden werden, wenn Ursprung/Berechtigung klar und es auf Desktop/Mobile lesbar ist.
- Kein temporäres fremdes Grafikmaterial in Release-Bundles einschließen. Eigene Platzhalter nur als deutlich markierte **Asset-Arbeit**, nicht als spielmechanisch Fake-Funktion.



---

<!-- QUELLDOKUMENT: spec/FEATURE_INDEX.md -->

# FUR EMPIRE — ALLE FEATURE-IDs / CHECKLISTE

**344 einzeln prüfbare Feature-IDs**; 60 dokumentierte FUR-2-Bestandsfunktionen und 55 ursprüngliche Lückenpunkte. Nicht automatisch als implementiert betrachten.


## FUR-2 Bestandswahrung

- [ ] **F2-001** [P0] Genesis-Login und Registrierung — Neue Benutzer werden sicher angelegt und können sich authentifiziert anmelden; lokale und Produktionsregeln sind getrennt.
- [ ] **F2-002** [P0] Registrierungsmodus — Die Spielleitung kann Registrierung deaktivieren; neue Accounts sind dann gesperrt und alte bleiben nutzbar.
- [ ] **F2-003** [P0] E-Mail-Bestätigung — Produktionsaccounts dürfen vor bestätigter Adresse keine Spielaktionen ausführen.
- [ ] **F2-004** [P0] 7-Tage-Session — Sitzungen haben serverseitige Ablaufzeit; Logout widerruft sie.
- [ ] **F2-005** [P0] 2FA-TOTP — Anmeldung unterstützt gültigen sechsstelligen TOTP-Code und verhindert Wiederverwendung.
- [ ] **F2-006** [P0] Wiederherstellung — Einmalcode verfällt nach 30 Minuten und kann kein zweites Mal genutzt werden.
- [ ] **F2-007** [P0] Kontosicherheit — E-Mailwechsel erfordert erneute Passwortprüfung; Admin benötigt in Produktion 2FA.
- [ ] **F2-008** [P0] Welt mit 64×64 Feldern — 4096 eindeutige Sektorkoordinaten und ein Kartenfenster bis 20×20 sind vorhanden.
- [ ] **F2-009** [P0] 104 neutrale Außenposten — Historische Welt enthält 104 neutrale Außenposten einschließlich Stufe-8-Zitadelle.
- [ ] **F2-010** [P0] Startkolonie und Ressourcen — Neue Spieler starten mit Holz=1200 Stein=1000 Erz=800.
- [ ] **F2-011** [P0] Holzproduktion — Bioforst nach FUR-2-Formel mit Nachkomma-Rest und Offlinestatus.
- [ ] **F2-012** [P0] Steinproduktion — Steinbruch nach FUR-2-Formel mit Nachkomma-Rest und Offlinestatus.
- [ ] **F2-013** [P0] Erzproduktion — Erzraffinerie nach FUR-2-Formel mit Nachkomma-Rest und Offlinestatus.
- [ ] **F2-014** [P0] Depotlimit — Je Ressource 2000+2000×Depotstufe; Überlauf von Lieferungen/Claims ins Reserve-Lager.
- [ ] **F2-015** [P0] Reserve-Lager — Reserve wird nur bis zur Depotkapazität aufgenommen; kein Verlust bei Rückgaben.
- [ ] **F2-016** [P0] Kommandozentrale — Bestandsgebäude beschleunigt Bau, erhöht Macht und schaltet ab Stufe 3 Eroberung frei.
- [ ] **F2-017** [P0] Bioforst — Bestandsgebäude produziert Holz und kostet 75/50/20 je Zielstufe.
- [ ] **F2-018** [P0] Steinbruch — Bestandsgebäude produziert Stein und kostet 90/65/30 je Zielstufe.
- [ ] **F2-019** [P0] Erzraffinerie — Bestandsgebäude produziert Erz und kostet 100/90/45 je Zielstufe.
- [ ] **F2-020** [P0] Depot — Bestandsgebäude vergrößert Lager; Grundkosten 120/100/50 je Zielstufe.
- [ ] **F2-021** [P0] Kaserne — Bestandsgebäude schaltet Ranger ab 1, Wächter ab 2 und Sturmmechs ab 3 frei.
- [ ] **F2-022** [P0] Forschungslabor — Bestandsgebäude Voraussetzung für die drei FUR-2-Forschungen.
- [ ] **F2-023** [P0] Schildwall — Bestandsgebäude erhöht Koloniedefensive inklusive Wächterbund-Bonus im PvP.
- [ ] **F2-024** [P0] FUR-2-Gebäudelimit — Historische Welten erlauben höchstens Stufe 10.
- [ ] **F2-025** [P0] Einzelne Bauqueue — Eine aktive Bauqueue pro Bestandskolonie; Kosten und Zeit serverseitig.
- [ ] **F2-026** [P0] Taktikforschung — +15 Prozent Angriff und Truppenverteidigung je Level nach FUR-2.
- [ ] **F2-027** [P0] Logistikforschung — +10 Tragekapazität je Einheit und Level nach FUR-2.
- [ ] **F2-028** [P0] Ingenieurforschung — +15 Prozentpunkte Produktion je Level nach FUR-2.
- [ ] **F2-029** [P0] Einzelne Forschungsqueue — Eine aktive Researchqueue pro Bestandskolonie mit 12×Zielstufe Sekunden Dauer.
- [ ] **F2-030** [P0] Ranger — Bestandseinheit Basisstärke 12, Kaserne 1, 2s Ausbildungszeit, 35/15/25 Kosten.
- [ ] **F2-031** [P0] Wächter — Bestandseinheit Basisstärke 28, Kaserne 2, 4s Ausbildungszeit, 50/40/60 Kosten.
- [ ] **F2-032** [P0] Sturmmech — Bestandseinheit Basisstärke 70, Kaserne 3, 7s Ausbildungszeit, 100/90/140 Kosten.
- [ ] **F2-033** [P0] Einzelne Trainingsqueue — Eine Trainingqueue pro Bestandskolonie, 1–100 Einheiten pro Auftrag.
- [ ] **F2-034** [P0] Fünf Direktiven — Wirtschaft-2, Kaserne, erste Forschung, erster Außenposten, Zitadelle jeweils einmal belohnen.
- [ ] **F2-035** [P0] Überfall auf Neutrale — Kampfvergleich Angriff größer Verteidigung; Retourtruppen/Beute nach Rückmarsch.
- [ ] **F2-036** [P0] FUR-2-Verlustregel — Niederlage alle entsandten Units verloren, Sieg mind. 10 Prozent Verlust pro Type aufgerundet.
- [ ] **F2-037** [P0] FUR-2-Loot — Nach Sieg Lootlimit SurvivingUnits×(40+10×Logistik) und tatsächlicher Postenbestand.
- [ ] **F2-038** [P0] Rohstoff-Transport — Anderen Spieler mit ausreichend Trägern/Beständen beliefern; Retourtruppen laufen serverseitig.
- [ ] **F2-039** [P0] Außenposten erobern — Commandcenter3 und Sieg besitzen Posten dauerhaft; +100 Power und +5pp Produktion nach Bestandsregel.
- [ ] **F2-040** [P0] Garnison verstärken — Eigene Außenposten bekommen entsandte Truppen mit Reisezeit; kein Dupe.
- [ ] **F2-041** [P0] Garnison zurückrufen — Stationierte Truppen kehren zum Ursprung zurück und sind unterwegs nicht verfügbar.
- [ ] **F2-042** [P0] PvP mit aktivierbarer Weltregel — PvP nur unter aktiver Adminregel; Angreifer und Verteidiger historisch mind. 1h alt.
- [ ] **F2-043** [P0] Allianz-NAP-Schutz — Aktive Allianzmitglieder und akzeptierte Nichtangriffspakte verhindern PvP.
- [ ] **F2-044** [P0] Urlaubsmodus — Start mind. 24h bei fehlenden laufenden feindlichen Angriffsaufträgen; Produktion/Actions pausieren.
- [ ] **F2-045** [P0] Pioniere — Einmalige FUR-2-Fraktionswahl bewirkt +10pp Produktion.
- [ ] **F2-046** [P0] Wächterbund — Einmalige FUR-2-Fraktionswahl bewirkt 40 Prozent Schildwallbonus gegen PvP.
- [ ] **F2-047** [P0] Syndikat — Einmalige FUR-2-Fraktionswahl bewirkt 60 statt 50 Prozent Soforttausch.
- [ ] **F2-048** [P0] Neutralmarkt — Mindestens 10 Waren, Ressourcenwechsel 50 Prozent oder 60 Prozent beim Syndikat.
- [ ] **F2-049** [P0] Spielermarkt — Bis 10 Angebote/Spieler von 10–100000 je Seite; 24h Ablauf; Escrow und Reserve.
- [ ] **F2-050** [P0] Allianzgründung — Tag 3–8, Name 3–30 Zeichen; Besitzer wird Leiter.
- [ ] **F2-051** [P0] Allianzrollen und Einladungen — Leitung/Offizier/Mitglied mit beschriebenen Befugnissen; Einladung muss akzeptiert werden.
- [ ] **F2-052** [P0] Diplomatie — Nichtangriffspakt wird beidseitig angenommen; Krieg/Neutralstatus verfügbar.
- [ ] **F2-053** [P0] Chat und Postfach — Welt, Allianz und privat; Nachricht maximal 2000 Zeichen, rollen- und empfängerbegrenzt.
- [ ] **F2-054** [P0] Meldungen und Sanktionen — Mute, Ban, Wartung, Registrierungs- und PvP-Sperre mit Audit durch Spielleitung.
- [ ] **F2-055** [P0] Ranking Machtwert — FUR-2-Score = 10×Gebäudestufen +20×Forschungsstufen +100×Posten.
- [ ] **F2-056** [P0] Saisonarchiv — Eine aktive Saison, 1–365 Tage, Einfrieren der Rangliste, keine Kolonie-Resets der Bestandswelt.
- [ ] **F2-057** [P0] Produktionsereignisse — Admin startet Bonus 0–100 Prozentpunkte für 1–168h; zeitkorrekt berücksichtigt.
- [ ] **F2-058** [P0] Zitadellenkampagne — Stufe-8-Zitadelle ist eroberbares Ziel und belohnt einmal; Weiterspielen möglich.
- [ ] **F2-059** [P0] Spielauftrag-Limit — Maximal 30 eigene gleichzeitige relevante Missionen/Operationen nach Bestandsregeln.
- [ ] **F2-060** [P0] SQLite und Postgres Betriebsmodi — Lokaler Speicher und Dockerwelt getrennt, kein behaupteter automatischer Synchronisierungsprozess.

## Original-55: Welt & Expansion

- [ ] **W01** [P0] Mehrere vollständig ausbaubare Kolonien — Zweite Basis gründen, separat entwickeln und zentral verwalten
- [ ] **W02** [P0] Kolonisation leerer Sektoren — Gründung statt nur Eroberung; Kolonisationskosten und Distanzen
- [ ] **W03** [P0] Eigene Kolonien untereinander versorgen — Transfer zwischen eigenen Basen; übergreifende Missionsplanung
- [ ] **W04** [P0] Fog of War und Aufklärungsstufen — Nicht jedes gegnerische Militärdetail ohne Spionage sichtbar machen
- [ ] **W05** [P1] Strategische Geländearten (Wald, Wasser, Berge, Pass) — Einfluss auf Bewegungswege, Produktion und Verteidigung
- [ ] **W06** [P1] Karten-Generator und weitere Welten — Seeds, Gelände, Welten mit eigenen Einstellungen und Weltenliste
- [ ] **W07** [P0] Dynamischer NPC-/Außenposten-Nachschub — Neutrale Ziele respawnen oder Bestände erneuern; Schutz vor leerer Welt
- [ ] **W08** [P2] Territoriumsgrenzen / Regionen / Kontrollzonen — Strategische Regionsziele und Gebietsboni
- [ ] **W09** [P1] Karten-Suche, Marker, Favoriten — Koordinatensuche, Ziel-Bookmarks, Sprungfunktionen
- [ ] **W10** [P1] Erweiterte NPC-Fraktionen und KI-Gegner — Gegenbewegungen und eskalierende Herausforderungen

## Original-55: Kampf & Missionen

- [ ] **K01** [P0] Mehrstufiger, rundenbasierter Kampf — Eigene Schadens-, Rüstungs-, Schild- und Rundenlogik
- [ ] **K02** [P0] Einheiten mit spezifischen Rollen und Gegen-Effekten — Mindestens 8–12 zunächst klar unterscheidbare Einheiten
- [ ] **K03** [P0] Spionage / Gegenaufklärung — Ranger-Spähberichte; FUR-3-only Abfang `min(50%, 2% × Taktik + 3% × Wall)` und Entdeckung `min(60%, 10% + 3% × Taktik + 2% × Wall)`, generischer Verteidigeralarm, ein Ranger Verlust, kein Gegenkampf; FUR-2 unverändert. Balance- und Clientabnahme offen.
- [ ] **K04** [P1] Kampfsimulator vor Missionsstart — Eigene Simulation, Anzeige von Verlustspannen
- [ ] **K05** [P0] Gemeinsame Allianzangriffe (ACS) — Kombinierter Verband mehrerer Spieler mit gemeinsamer Ankunft
- [ ] **K06** [P0] Unterstützung fremder Allianzbasen — Defensive Garnison auch bei Verbündeten stationieren
- [ ] **K07** [P1] Taktischer Rückzug und laufende Mission abbrechen — Rückruf, Rückzugsschwellen, definierte Rückmarschfolgen
- [ ] **K08** [P1] Expeditionen und Ereignis-Missionen — PvE-Expedition mit zufälligen Chancen und Belohnungen
- [ ] **K09** [P2] Trümmerfelder, Bergung und Reparatur — Nach Schlachten zerstörte Materialien bergen
- [ ] **K10** [P2] Fernkampfangriffe / Artillerie / Raketen — Spezielle Fernmissionen mit Gegenmaßnahmen
- [ ] **K11** [P1] Unterschiedliche Truppen-Geschwindigkeit und Reichweite — Armeezusammenstellung bestimmt Marschzeit und Kosten
- [ ] **K12** [P1] Kampfbericht pro Runde und Einheit — Schaden, Einheitenverluste, Loot, Zeit, beteiligte Spieler
- [ ] **K13** [P2] Schlachtvorlagen / Angriffsprofile — Schnelles wiederholbares Entsenden üblicher Truppentypen
- [ ] **K14** [P1] Weitere Verteidigungsobjekte — Türme, Geschütze, Fallen, Reparatur und Anlagenslots

## Original-55: Wirtschaft & Technik

- [ ] **E01** [P0] Abhängiger Forschungs- und Freischaltbaum — Tech-Voraussetzungen, neue Einheiten und Gebäudetypen
- [ ] **E02** [P1] Erweiterbare Gebäudekategorien / Spezialausbauten — Werkstatt, Versorgung, Spionagezentrum, Festung
- [ ] **E03** [P2] Energie-, Betriebs- oder Unterhaltsmechanik — Optionaler vierter Wirtschaftskreislauf statt trivialer Produktion
- [ ] **E04** [P1] Bau-/Forschungswarteschlangen umordnen & stornieren — Stornieren, Rückerstattung und planbare Folgestufen
- [ ] **E05** [P1] Ausbau jenseits von Stufe 10 / Prestige — Späte Spielphase mit Kostenkurve und Meisterungsstufen
- [ ] **E06** [P2] Marktpreis-Statistiken und Handelsverlauf — Transparente Preisentwicklung und Transaktionshistorie
- [ ] **E07** [P0] Datengetriebene Konfig für Gebäude, Einheiten, Formeln — Versionierte Regeldefinitionen statt hartcodierter Spielwerte
- [ ] **E08** [P1] Fraktionsspezifische Einheiten/Technologien — Fraktionswahl wirkt stärker auf Spielstil als nur passive Boni

## Original-55: Allianz & Spieler

- [ ] **A01** [P1] Allianzkrieg mit Zielen, Wertung und Frieden — Krieg nicht bloß als Diplomatiestatus: Ziele, Zeit, Ergebnis
- [ ] **A02** [P1] Allianz-Rangliste und gemeinsame Siege — Allianzstatistik, Saisonplatzierung, Kriegsfortschritt
- [ ] **A03** [P2] Allianzkasse / Gemeinschaftsprojekte — Allianzdepot, gemeinsame Festungen, Beiträge
- [ ] **A04** [P2] Flexible Allianz-Rollen und Einzelberechtigungen — Rollen jenseits Leitung/Offizier/Mitglied
- [ ] **A05** [P2] Freundesliste und Blockliste — Kontakte, Anfragen, private Kommunikation
- [ ] **A06** [P2] Interne Foren / Pinnwand — Längerfristige Strategiedokumente der Allianz
- [ ] **A07** [P2] Spielerprofile, Badges, Leistungsdaten — Öffentliche Profilansicht und Historie
- [ ] **A08** [P2] Notizen, Berichtsfreigaben, Zielmarkierungen — Persönliche Kartenhinweise und gemeinsame Einsatzplanung

## Original-55: Progression & Livebetrieb

- [ ] **P01** [P1] Fortlaufende Quest-/Erfolgsysteme — Fünf Direktiven zu einer Progressionskette ausbauen
- [ ] **P02** [P0] Langfristiges Endgame nach Zitadellen-Sieg — Neue Boss-Stufen, wechselnde Kampagnen, globale Ziele
- [ ] **P03** [P1] Saisonmechaniken / faire Neustartwelten — Optional Saisonwelt mit Reset und separatem Dauerwelt-Spielstand
- [ ] **P04** [P0] Spieler-Balance und Comeback-Schutz — Schutz nach Niederlage, Noobschutz, Abschwächung des Snowballs
- [ ] **P05** [P1] Ereignisse mit Missions- und Kampfvarianten — Nicht nur Produktion, sondern spezifische PvE-Events
- [ ] **P06** [P2] Vernünftige Automatisierung für Rückkehrer — Benachrichtigungen, Aufgabenstatus, Kommandoübersichten

## Original-55: Technik & Betrieb

- [ ] **T01** [P0] Automatische Backups + Restore-Probe — Backups, Wiederherstellungstest, Rotation und Zugriffsschutz
- [ ] **T02** [P0] Race-Condition-/Lasttests und Missions-Idempotenztests — Parallelstart, doppelte Buchung, Worker-Absturz, Replay testen
- [ ] **T03** [P0] Anti-Bot/Anti-Multiaccount/Rate Limits — Abuse-Detektion ohne personenbezogene Überwachungsexzesse
- [ ] **T04** [P1] Umfassende Welt- und Balancing-Adminwerkzeuge — Weltregeln, Missions-Suche, Korrekturwerkzeuge und Telemetrie
- [ ] **T05** [P2] Mehrsprachigkeit / Lokalisierung — String-Katalog für DE/EN, anschließend weitere Sprachen
- [ ] **T06** [P1] Responsive Mobile-/Accessibility-Prüfung — Bedienung und Tastaturzugänglichkeit für Karte und Kampf
- [ ] **T07** [P2] Echtzeit-Updates statt ausschließlich Polling — Websocket/SSE für Missionen und Allianzkoordination
- [ ] **T08** [P1] Spielregel-Migrationen und Balancing-Simulation — Regelversions-Snapshots gegen echte Formellogik validieren
- [ ] **T09** [P1] Sicherer Test-/Produktions-Release-Prozess — CI/CD mit Tests, Rollback, Spiel-DB-Migration, Monitoring

## Identität und Konto

- [ ] **ACC-001** [P0] Passwortänderung — Altes Passwort und TOTP prüfen, danach aktive Sessions nach Policy widerrufen.
- [ ] **ACC-002** [P0] Recovery-Codes — TOTP-Recovery Codes einmalig, gehasht, regenerierbar nach starker Authentifizierung.
- [ ] **ACC-003** [P0] Sitzungsverwaltung — Geräte/Sessions auflisten, einzeln/weltweit widerrufen und Audit anlegen.
- [ ] **ACC-004** [P0] Accountname ändern — Umbenennen mit Cooldown, Uniqueness und historischer Referenzpflege.
- [ ] **ACC-005** [P0] Avatare und Profildetails — Nur eigene oder freigegebene Assets, Größen-/Typprüfung und Moderationsweg.
- [ ] **ACC-006** [P0] Privacy Export — Spieler erhält strukturierten Export eigener personenbezogener Daten ohne fremde Inhalte.
- [ ] **ACC-007** [P0] Privacy Delete — Datenschutzanfrage wird auditiert und anonymisiert/löscht nach rechtlicher Aufbewahrungsregel.
- [ ] **ACC-008** [P0] Benachrichtigungseinstellungen — E-Mail/Browser/Ingame je Ereigniskategorie opt-in steuerbar.
- [ ] **ACC-009** [P0] Login-Schutz — Rate limit pro Account/Netz plus sichere Fehlermeldung ohne Email-Enumeration.
- [ ] **ACC-010** [P0] WebAuthn optional — Passkey Enrollment und Recovery werden hinter sicherem Featureflag verfügbar und getestbar.

## Game-Engine und Infrastruktur

- [ ] **ENG-001** [P0] Globale Accounts und WorldPlayer — Ein Account kann mehreren Welten angehören; Progress ist pro Welt getrennt.
- [ ] **ENG-002** [P0] Dauer- Saison- Sandboxwelten — Weltmodus erlaubt explizite Regeln; Data Leakage und saisonaler Reset sind unmöglich.
- [ ] **ENG-003** [P0] Regelversionierter Katalog — FUR-2 und FUR-3/ORBIT-1 haben immutable Hash und eingefrorene Rechenformeln.
- [ ] **ENG-004** [P0] Domain Commands — Alle Spielbefehle laufen über autorisierte Commands statt Client-Datenmanipulation.
- [ ] **ENG-005** [P0] Event-Outbox — DB Commit und publish reproduzieren Events ohne Nachrichtenverlust.
- [ ] **ENG-006** [P0] Idempotenz — Gleicher Command kann mehrfach zugestellt werden, hat aber nur eine Wirkung.
- [ ] **ENG-007** [P0] Persistenter Worker — Fällige Aufträge laufen ohne Browser und sind nach Neustart verarbeitbar.
- [ ] **ENG-008** [P0] Scheduler-Lag und Deadletter — Gestörte Worker und fehlgeschlagene Tasks sind sichtbar und sicher erneut anstoßbar.
- [ ] **ENG-009** [P0] Transaktionales Ressourcenledger — Jede Resource-Buchung hat Ursache, Besitzer, Welt und nachvollziehbaren Saldo.
- [ ] **ENG-010** [P0] Deterministische Zeitintegration — Produktion berechnet UTC-Intervalle mit Eventbeginn/-ende und Urlaubsmodi korrekt.
- [ ] **ENG-011** [P0] Stabile IDs und FK — Jeder Welt-/Kolonie-/Missionsdatensatz ist eindeutig und besitzt gesicherte referenzielle Integrität.
- [ ] **ENG-012** [P0] Welt-Snapshot — Snapshot/Restore pro Welt und Regeln mit dokumentierter Gültigkeit, keine Live-Destruktion.
- [ ] **ENG-013** [P0] Regeländerungs-Simulation — Admin sieht Auswirkungen auf Economy/Power/aktive Missionen vor Publikation.
- [ ] **ENG-014** [P0] Datenbankmigration FUR-2 — Alte Welt und laufende Queues bleiben nach Migration konsistent und im Notfall wiederherstellbar.
- [ ] **ENG-015** [P0] Produktions-Fehlerformat — API verwendet definierte Fehlercodes, Request-ID und keine Stacktraces.
- [ ] **ENG-016** [P0] Read Model + Pagination — Große Listen sind gefiltert/paginiert und leaken keine versteckten Gegnerdaten.
- [ ] **ENG-017** [P0] Monitoring und Warnschwellen — p95, event lag, Ressourcenintegrität, DB, Backupalter erzeugen Metriken/Alarme.

## Terra-Welt detailliert

- [ ] **TERRA-001** [P0] Kartengenerator — Welt ist aus einem Seed reproduzierbar, mit begehbaren Startbereichen und Ressourcen.
- [ ] **TERRA-002** [P0] Sektorbesitztransaktionen — Kachelbesitz ist je Welt eindeutig; Race mit zwei Gründern erzeugt einen Gewinner.
- [ ] **TERRA-003** [P0] Ausgeglichene Startpositionen — Neue Spieler können innerhalb Schutzzeit für Fortschritt notwendige Ressourcen erreichen.
- [ ] **TERRA-004** [P0] Fog-Koordinatenliste — Sichtzustand je Spieler ist unbekannt/alt/aktuell, mit Zeitstempel und Berechtigung.
- [ ] **TERRA-005** [P0] Regionen-Score — Gebietskontrolle ist separat von persönlichen Basenwerten und hat gedeckelte Boni.
- [ ] **TERRA-006** [P0] Geländemodifikatoren — Terrain beeinflusst zulässige Wege, Reisezeit und Defense aus Regelkatalog.
- [ ] **TERRA-007** [P0] Kolonie umbenennen — Neue Namen mit validierter Länge und Sperre gegen fremden Zugriff.
- [ ] **TERRA-008** [P0] Hauptkolonie wechseln — Player kann die Hauptkolonie nach Cooldown ändern ohne Einheitentransfer.
- [ ] **TERRA-009** [P0] Kolonie aufgeben — Letzte Heimatkolonie nicht aufgebbar; Missionen/Items/Waren werden vorher geregelt.
- [ ] **TERRA-010** [P0] Kolonie versetzen — Targetreserving/Cooldown/Kosten und sichere Abwicklung aller offenen Missionen.
- [ ] **TERRA-011** [P0] Außenposten zu Kolonie ausbauen — Nur zulässiger Posten und verfügbarer Kolonieslot; eindeutige Besitz- und Kostenbuchung.
- [ ] **TERRA-012** [P0] Kartenfavoriten — Pro Welt private Marker/Filter/Routen- und Koordinatensuche.
- [ ] **TERRA-013** [P0] Territorialkontrolle — Allianzgrenzen und Regionen werden aus tatsächlichem Sektorbesitz berechnet.
- [ ] **TERRA-014** [P0] Schutzgebiete und Spawnregeln — Neue Kolonien dürfen keine reservierten/geschützten/unerreichbaren Kacheln belegen.
- [ ] **TERRA-015** [P0] Verlassene Kolonien und Ruinen — Inaktive Basen werden nach Regeln gesichert in Ruinen umgewandelt; keine überraschende Löschung.

## Ökonomie und Forschung erweitert

- [ ] **ECO-001** [P1] Energieversorgung — Gebäude haben Erzeugung, Verbrauch und bei Unterdeckung definierte Produktionsdrosselung.
- [ ] **ECO-002** [P1] Unterhaltskosten — Spezielle Units/Orbitflotten belasten regelkonforme Ressourcen ohne negative Bestände.
- [ ] **ECO-003** [P1] Bauqueue umordnen — Erlaubte Reorder-Kontrolle respektiert Slots, Ressourcen und bereits gestartete Aufträge.
- [ ] **ECO-004** [P1] Bauqueue abbrechen — Stornierungsregel definiert Credit, bereits verbrauchte Zeit und Upgrade-Invariante.
- [ ] **ECO-005** [P1] Forschung global vs lokal — Forschungs- und Kolonieeffekte sind sauber getrennt, kein doppelt gerechneter Bonus.
- [ ] **ECO-006** [P1] Technologieabhängigkeiten — Server prüft Bau/Forschung/Einheit-Freischaltungen auch bei parallelen Aufträgen.
- [ ] **ECO-007** [P1] Spezialgebäude — Militär/Spionage/Energie/Logistik/Fertigung/Orbit und Support haben eigene Bauklassen.
- [ ] **ECO-008** [P1] Prestigeausbau — Nach Level-10 Altweltregel neue Prestigeslots nur bei neuer Regelversion mit Kosten.
- [ ] **ECO-009** [P1] Ressourcenproduktionsgrafik — Backend liefert genaue Produktionskomponenten mit Cap/Pause und Forecast.
- [ ] **ECO-010** [P1] Markt-Preisverlauf — Trades erzeugen nachvollziehbare Statistik je Welt ohne Account-Leak.
- [ ] **ECO-011** [P1] Allianzversorgungsrouten — Cargo-Transfers brauchen Weg, Kapazität, Empfang und Abbruchregeln.
- [ ] **ECO-012** [P1] Dauerhafte Handelsrouten — Periodischer Transport hat Limit, Reservierung und Stop bei ungenügenden Rohstoffen.
- [ ] **ECO-013** [P1] Produktionsvorlagen — Bau/Forschung/Rekrutierung unterstützen wiederholbare autorisierte Presets.
- [ ] **ECO-014** [P1] Ressourcen-Faucets/Sinks — Neutrale Belohnungen und Wirtschaftssinks sind versioniert und simuliert.
- [ ] **ECO-015** [P1] Forschungsspezialisierung — Mindestens drei strategisch unterschiedliche Pfade, kein dominanter Autowin.
- [ ] **ECO-016** [P1] Fraktions-Spezialaktionen — Jede Faktion hat die laut Master-GDD freigeschalteten fairen Spezialeinheiten/Technologien.

## Kampf, Missionen und Schutz

- [ ] **WAR-001** [P0] FUR-3 Gefecht mit 6 Runden — Angriff/Verteidigung, Rüstung, Schild, Schaden und Flucht werden deterministisch aufgelöst.
- [ ] **WAR-002** [P0] Unit Counter Matrix — Jede neue Kampfeinheit hat Rolle, Stärken, Schwächen, Kosten, Tempo und konfigurierbare Zielwahl.
- [ ] **WAR-003** [P0] Verteidigungsobjekte — Kanonen, Schilde, Minen und Unterstützungsbauwerke haben eigene Defense-Stacks und Reparatur.
- [ ] **WAR-004** [P0] Gefechts-RNG — Server seedet Kampf, speichert Commitment/Replay und liefert bei Wiederholung exaktes Ergebnis.
- [ ] **WAR-005** [P0] Kampf Dry-run — Simulator nutzt denselben Resolver ohne Datenbankmutation oder Intel-Leak.
- [ ] **WAR-006** [P0] Zeitgestaffelte Bewegungen — Anmarsch, Transit und Rückmarsch berücksichtigen Terrain, Unit-Speed, Fuel und UTC.
- [ ] **WAR-007** [P0] Mission Recall — Rückruf an erlaubtem Punkt erzeugt genau eine gültige Retourmission, kein Verlust/Dupe.
- [ ] **WAR-008** [P0] Taktischer Rückzug — Server prüft Retreat-Bedingungen und rechnet Überlebende/Rückflug eindeutig ab.
- [ ] **WAR-009** [P0] Spionage-Mission — Report enthüllt nur Informationen, die erlaubte Intel-Levels tatsächlich gewähren.
- [ ] **WAR-010** [P0] Gegenaufklärung — FUR-3-only versionierte Abfang-/Entdeckungswürfe mit privatem gepinntem Seed, generischem Alert ohne Angreiferdaten, genau einem Ranger Verlust, unterdrückter Intel und ohne Gegenkampf; FUR-2 unverändert. Balance- und Clientabnahme offen.
- [ ] **WAR-011** [P0] Reparatur und Wrackbergung — Verluste erzeugen begrenzte Trümmer, Bergung benötigt Mission und Cargo.
- [ ] **WAR-012** [P0] Artillerie und Fernwaffen — Kosten, Reichweite, Schutzregeln, Gegenwehr und Eventwirkung serverseitig.
- [ ] **WAR-013** [P0] Koordinierte Attacke — Mehrere Mitglieder senden Einheiten zu gemeinsamem Arrival, Anteile und Rechte geprüft.
- [ ] **WAR-014** [P0] Verteidiger-Verband — Unterstützung allierter Kolonien mit Besitzerrechten/Abzug und verlusttreuer Auszahlung.
- [ ] **WAR-015** [P0] Taktische Belagerung — Belagerung braucht spezifische Units/Zeit; Defense gewinnt bei Ablauf ungebrochen.
- [ ] **WAR-016** [P0] Kriegseinfluss auf Angriff — NAP/War/Vacation/Beginner-Schutz Start und Ankunft relevant und transparent.
- [ ] **WAR-017** [P0] Raid-Limit — Beschränkung auf Ziele/Angriffe/Verluste reduziert unendliches Farmen desselben Spielers.
- [ ] **WAR-018** [P0] Welt- und Allianz-Rankings — Militärwertungen unterscheiden Angriff/Defense/Support und sind auditierbar.
- [ ] **WAR-019** [P0] Bericht Replay und Freigabe — Nur Rechteinhaber sieht vollständiges Replay, öffentliche Freigabe anonymisiert Geheimdaten.
- [ ] **WAR-020** [P0] Kampf-Balance-Test — Mindestens ein Gegenbeispiel für jede Unit-Klasse verhindert nutzlose Einheit oder Autowin.

## Allianz und soziale Plattform

- [~] **SOC-001** [P1] Allianzaufnahmeverfahren — Bewerbung, Einladung, Rücknahme, Annahme und Ablehnung sind getrennte rollen- und kontogebundene Abläufe; gemeinsame Historie und Geräteabnahme offen.
- [~] **SOC-002** [P1] Granulare Allianzrechte — Schema 83 ergänzt sieben Leitungskonfigurationen, die serverseitig für Offizier/Mitglied durchgesetzt werden; Betriebsabnahme offen.
- [~] **SOC-003** [P1] Führungsübertrag — Schema 84 verlangt Zustimmung des Nachfolgers, bevor die Rollen atomar wechseln; PostgreSQL-/UI-/Geräteabnahme offen.
- [~] **SOC-004** [P1] Allianzkrieg-Objektive — Schema 85 ergänzt formelle FUR-3-Kriege, Ziele, Wertung, Gegenzustimmung für Frieden und öffentliches Protokoll. Punktwerte bleiben vorläufig; FUR-2 unverändert.
- [~] **SOC-005** [P1] Allianz-Rangliste — Live-FUR-3-Militäraggregation besteht; Schema 86 archiviert bestätigte Konten mit Eventzeit-Allianzzuordnung und unveränderlicher Rangfolge. Vorläufiger Regelentwurf; getrennte E-Mail-Adressen sind nicht dedupliziert. Freigaben und PostgreSQL/UI-/Accessibility-Abnahme offen.
- [ ] **SOC-006** [P1] Allianzkasse — Spende, Ausgabe, Anforderung, Gebühren, Ledger und Vier-Augen-Gate für große Buchungen.
- [ ] **SOC-007** [P1] Allianzprojekte — Mitglieder leisten Ressourcenbeiträge zu endlich getimten Bau-/Eventzielen.
- [ ] **SOC-008** [P1] Allianzforum — Threads, Rechte, Archiv und Edit-/Report-Funktionen, XSS-Schutz.
- [ ] **SOC-009** [P1] Pinnwand — Moderierte Allianzankündigungen mit Sichtbarkeit und zeitlicher Reihenfolge.
- [ ] **SOC-010** [P1] Freundeslisten — Anfragen, Zustimmungen, Entfernen und private Sichtbarkeit.
- [ ] **SOC-011** [P1] Blocklisten — Blockierte Nutzer können keine privaten Nachrichten senden; Moderation bleibt möglich.
- [ ] **SOC-012** [P1] Spielerprofil — Titel, Abzeichen, Stats, Account-Privacy ohne preisgeben sensibler Daten.
- [ ] **SOC-013** [P1] Notizen — Private Notizen zu Koordinaten/Reports mit Textbegrenzung und Weltbindung.
- [ ] **SOC-014** [P1] Berichtsfreigabe — Kampfberichte teilbar in Allianz, ohne verborgene IDs/Informationen preiszugeben.
- [ ] **SOC-015** [P1] Chatmoderation — Melden, Ausblenden, Mute, Appeal und auditierte Rechte.
- [ ] **SOC-016** [P1] Ankündigung und Briefkasten — Private und öffentliche Ankündigungen getrennt; Leser erhält nur erlaubte Inhalte.

## NPC, Quests, Endgame

- [ ] **PVE-001** [P1] NPC-Fraktionen — Mindestens fünf eigene NPC-Lager mit unterschiedlichen Profilen und erlaubten Aktionen.
- [ ] **PVE-002** [P1] NPC-Lagerzustand — NPC-Basen besitzen Ressourcen, Einheiten, Bewegungen und Bereitstellungskontingent.
- [ ] **PVE-003** [P1] NPC Angriffskette — Strategie-KI erzeugt geplante Missionen innerhalb CPU-/Event-Budget, fair und auditierbar.
- [ ] **PVE-004** [P1] NPC Außenposten Regeneration — Nicht besetzte Außenposten erzeugen regelbegrenzt Ressourcen und Verteidigung.
- [ ] **PVE-005** [P1] Ruinenerkundung — Erkundungs-Mission mit Danger/Reward, Fog- und Intel-Updates.
- [ ] **PVE-006** [P1] Expeditionskatalog — PvE-Expeditionen mit deterministischer Reward-Distribution und Rückmarsch.
- [ ] **PVE-007** [P1] Boss-Raid — Kooperative Boss-Lebenspunkte, Angriffsslots, Contribution und endliche Belohnung.
- [ ] **PVE-008** [P1] Weltinvasion — Spawnwelle hat Budget, Warnphase, Angriff, Verlauf und Ende.
- [ ] **PVE-009** [P1] Konvoi-Ereignis — Zeitgestaffelte NPC-Handelsroute wird verteidigt/überfallen mit klarer Belohnung.
- [ ] **PVE-010** [P1] Questlinien — Tutorial/Story/Forschung/Militär/Handel/Allianz/Orbit Quests mit Progress.
- [ ] **PVE-011** [P1] Tagesquests — Täglich resetbare Quests haben UTC-Grenze und Claim-Einmaligkeit.
- [ ] **PVE-012** [P1] Wochenquests — Wöchentliche Ziele werden sicher bei Wochenwechsel versioniert.
- [ ] **PVE-013** [P1] Erfolge — Persistente Achievements mit einmaliger Vergabe und öffentlicher/privater Anzeige.
- [ ] **PVE-014** [P1] Questreward-Reserve — Belohnungen bei vollem Depot vollständig in Reserve oder Inventar.
- [ ] **PVE-015** [P1] Zitadellen-Endgame — Nach Historischem Kern-Sieg weitere regionale/Orbit- und Allianzkampagnen.
- [ ] **PVE-016** [P1] Comeback-Hilfe — Abwesende Spieler erhalten kein unfairen PvP-Startnachteil und transparente Schutzfenster.
- [ ] **PVE-017** [P1] NPC Simulation — Weltbot hat deterministische Seeds, kann nicht moderieren und verteilt keine willkürlichen Lootbeträge.
- [ ] **PVE-018** [P1] Abgeschlossene Kampagne — Story-Fortschritt wird pro Welt gespeichert; Replay/Neue-Welt-Entscheidung klar.

## Orbit und Raumsysteme

- [ ] **ORB-001** [P1] Orbitfreischaltung — Terra-Zitadelle oder Forschung und erforderliche Materialien schalten Orbit sicher frei.
- [ ] **ORB-002** [P1] System- und Galaxiekarte — Generierte Galaxie/Sektoren/Slots sind pro Welt eindeutig und navigierbar.
- [ ] **ORB-003** [P1] Orbitale Sicht — Sensorik und Fog schützen gegnerische Systemdaten nach Intel-Regel.
- [ ] **ORB-004** [P1] Planeten-Kolonisierung — Kolonieschiff reserviert leeren Slot und gründet nach Ankunft Orbitalbasis.
- [ ] **ORB-005** [P1] Mondentstehung — Monde entstehen nach geregelten Missionen/Ereignissen, nicht zufällig ohne Ereignislog.
- [ ] **ORB-006** [P1] Raumstationen — Stationen besitzen Ausbau, Wartung, Garrison, Inventar und Owner-Berechtigungen.
- [ ] **ORB-007** [P1] Orbitbau — Orbitkolonien haben eigene Bauqueue, Gebäudekosten, Zeit und Kapazität.
- [ ] **ORB-008** [P1] Orbitforschung — Orbitaltechbaum mit Voraussetzungskette und Forschungslimits.
- [ ] **ORB-009** [P1] Energiehaushalt — Orbitaler Energie-Input/Verbrauch drosselt Module, nie negativer Bestand.
- [ ] **ORB-010** [P1] Ätherförderung — Orbitressource hat Fördergebäude, Obergrenze und persistente Fraktionalreste.
- [ ] **ORB-011** [P1] Orbitaler Frachtraum — Frachtlimit und Frachtressourcen sind serverseitig beim Abflug gebucht.
- [ ] **ORB-012** [P1] Flottenaufbau — 14 Schifftypen mit Speed, Fracht, Treibstoff, Angriff, Schild, Hülle und Freischaltung.
- [ ] **ORB-013** [P1] Schiffswerft — Auftragsqueue mit Einheitenausbau und Anti-Duplikation.
- [ ] **ORB-014** [P1] Flottenentsendung — Validierte Flottenbefehle nutzen dieselben Missionsstandards wie Terra.
- [ ] **ORB-015** [P1] Orbitaler Angriff — Flottenkampf verwendet versionierte Kampfschilde und Verteidiger inklusive Mond/Station.
- [ ] **ORB-016** [P1] Orbitale Spionage — Sensor- und Spähsonden liefern abgestufte Intel-Reports und können abgefangen werden.
- [ ] **ORB-017** [P1] Orbitaler Transport — Fracht und Fuel werden beim Dispatch abgezogen und am Ende einmal verbucht.
- [ ] **ORB-018** [P1] Flottenstationierung — Eigene oder allierte Stationierung mit Berechtigung, Rückruf und Versorgung.
- [ ] **ORB-019** [P1] Orbitkolonisation — Neue Kolonie bekommt eigenen Welt-/Account-/Slotbezug und saubere Reservierung.
- [ ] **ORB-020** [P1] Orbitale Expedition — Anomalien und Raumruinen mit Risiko, Ereignis, Belohnung und Missionabschluss.
- [ ] **ORB-021** [P1] Bergungsmission — Begrenzte Trümmerfelder, Cargo-Berechtigung, Raid-/Recycle-Competition.
- [ ] **ORB-022** [P1] Sensorphalanx — Scan zeigt nur Missionsdaten je Reichweite, Kosten und Gegenabwehr.
- [ ] **ORB-023** [P1] Sprungtor — Zwei kompatible Tore und Cooldown; atomare Transferbilanz, kein Teleportdupe.
- [ ] **ORB-024** [P1] Mondzerstörung — Spezialmission mit Sicherheits-/Balancegrenzen und korrekter Schadensbilanz.
- [ ] **ORB-025** [P1] Verbandflotte — Gemeinsame Flotte mit Teilnehmerrechten, Ankunft und Ergebnisaufteilung.
- [ ] **ORB-026** [P1] Orbitaler Rückzug — Taktischer Flottenrückzug, Fuel und Losses transparent, kein Out-of-Combat Dupe.
- [ ] **ORB-027** [P1] Schiffswerft-vorlagen — Spieler speichert Flotten- und Fertigungsvorlagen pro Welt.
- [ ] **ORB-028** [P1] Unterhalt und Versorgung — Flotten benötigen begrenzte Unterhaltsressourcen, aber keine irreversible Offline-Extinktion.
- [ ] **ORB-029** [P1] Wrackfeld-Reparatur — Reparaturcenter heilt nur vorhandene Wracks gegen regelbasierte Kosten.
- [ ] **ORB-030** [P1] Terra-Orbit Cargo — Routen zwischen Ebenen verbuchen Cargo und Reisezeit ohne magisches Material.
- [ ] **ORB-031** [P1] Orbitale Verteidigungsraketen — Missile/Missile-Abwehr mit eigenen FUR-Namen, Reichweite und Gegenwehr.
- [ ] **ORB-032** [P1] Orbit-Spezialereignisse — Sternevents, Anomalien und Bosse nutzen dieselbe Regelversionierung und Reward-Caps.

## Inventar, Craft, Charakter

- [ ] **ITEM-001** [P1] Inventar — Besitz von Stack-Items mit Slot-/Cap-Policy, Weltbindung und Audit.
- [ ] **ITEM-002** [P1] Crafting — Rezepte kosten definierte Ressourcen/Items, dauern ggf. und erzeugen exakt einmal Output.
- [ ] **ITEM-003** [P1] Item-Recycling — Zerlegen von Items gibt bestimmte Teilmengen und erzeugt keinen positiven Endloskreislauf.
- [ ] **ITEM-004** [P1] Lootbox-freies Itemdrop-System — Deterministisch seedbare PvE-Itemdrops mit dokumentierten Wahrscheinlichkeiten und Caps.
- [ ] **ITEM-005** [P1] Heldenverwaltung — Eigener Commander mit XP/Stats/Skillpunkten aus Spielaktionen statt Kauf.
- [ ] **ITEM-006** [P1] Helden-Doktrinen — Wirtschaft/Militär/Spionage/Flotte haben definierte passive Boni mit Power-Caps.
- [ ] **ITEM-007** [P1] Talent-Reset — Respec hat Cooldown und Kosten, kein zusätzlicher Skillpunkt durch Replay.
- [ ] **ITEM-008** [P1] Kosmetische Belohnungen — Skins, Titel, Banner ohne Kampfkraft oder Produktivitätsvorteil.
- [ ] **ITEM-009** [P1] Baupläne — Vorlagen für Bau/Rekrutierung/Forschung mit Servervalidierung und Ownership.
- [ ] **ITEM-010** [P1] Ingame Benachrichtigungen — Spieler kann Kategorien lesen, stummschalten und Zustellfehler nachvollziehen.
- [ ] **ITEM-011** [P1] Brower Push optional — Opt-in Push nach Freigabe, Unsubscribe funktioniert, keine sensitiven Details in Vorschau.

## Welten, Saisons, Rankings, LiveOps

- [ ] **SEAS-001** [P1] Multiworld Browser — Spieler sieht Welten, Regeln, Status, Ranglisten, ohne sich mehrfach registrieren zu müssen.
- [ ] **SEAS-002** [P1] Neue Welt gründen — Admin nutzt seed/Ruleset/Type und schafft leere, getestete Welt ohne alte Daten.
- [ ] **SEAS-003** [P1] Neue Saison — Nur in Saisonwelt, Laufzeit und Ziele gesetzt, separate Ranglisten und Archiv.
- [ ] **SEAS-004** [P1] Saisonabschluss — Scores und Awards archivieren exakt einmal, anschließend Status archived.
- [ ] **SEAS-005** [P1] Dauerwelt schützen — Saisonabschluss darf niemals fremde Welt oder Dauerwelt zurücksetzen.
- [ ] **SEAS-006** [P1] LiveEvent-Editor — Admin kann Produktionsboni, Ziele, Warn- und Endphase versioniert konfigurieren.
- [ ] **SEAS-007** [P1] Mehrfach-Event Regeln — Überlappende Boni werden gedeckelt und in Zeitsegmenten korrekt integriert.
- [ ] **SEAS-008** [P1] Allianzrangliste — Rangliste aggregiert Beiträge auf Allianz-/Weltbasis mit historischen Snapshots.
- [ ] **SEAS-009** [P1] Ranglistenarten — Gesamt, Wirtschaft, Forschung, Krieg, PvE, Allianz/Regionen saisonal und permanent.
- [ ] **SEAS-010** [P1] Hall of Fame — Historische Gewinner, Seasons, Boss- und Kriegserfolge bleiben sichtbar.
- [ ] **SEAS-011** [P1] Imperium-Prestige — Endgame erhöht kosmetische Prestigelevel ohne unbegrenzte PvP-Macht.
- [ ] **SEAS-012** [P1] Server-Ankündigungen — Geplante Texte und Notfallankündigungen erreichen betroffene Welten mit Audit.
- [ ] **SEAS-013** [P1] Regelupdate Rollout — Ruleset-Publish per Welt/Aktivzeit, laufende Missionen behalten gültigen Vertrag.

## Administration, Sicherheit, Betrieb

- [ ] **ADM-001** [P0] RBAC Owner/Admin/GM/Mod — Rollen und Einzelpermissions verhindern unberechtigten Zugriff.
- [ ] **ADM-002** [P0] Admin-TOTP-Pflicht — Live Admin muss TOTP vor privilegierter Aktion bestätigen.
- [ ] **ADM-003** [P0] Admin Vier-Augen Gate — Kritische Welt-/Ressourcen-/Accountänderung verlangt zweiten berechtigten Zustimmer.
- [ ] **ADM-004** [P0] Auditlog — Jede privilegierte Aktion mit Actor/World/Grund/Zeit/Result ohne Secrets.
- [ ] **ADM-005** [P0] Spielerverwaltung — Admin kann Spieler nach berechtigtem Scope suchen, ansehen, sperren und entsperren.
- [ ] **ADM-006** [P0] Allianzverwaltung — Admin kann Allianzkonflikte bearbeiten, Rollen prüfen, gezielt reparieren.
- [ ] **ADM-007** [P0] Weltsteuerung — Admin verwaltet Wartung/Registrierung/PvP/Events/Saison ohne manuelle SQL-Eingriffe.
- [ ] **ADM-008** [P0] Regelvorschau — Neue Definitionen laufen erst in Dry-run/Simulation, Veröffentlichung wird auditierbar.
- [ ] **ADM-009** [P0] Map/NPC Editor — Region/Spawn-Preview, Invasion/Event-Verwaltung unter Schutz vor Kolonieüberschreibung.
- [ ] **ADM-010** [P0] Missions-Support — Stuck Missions, Worker-DLQ und Rückruf haben wiederholbare Korrekturwege.
- [ ] **ADM-011** [P0] Integritätskontrolle — Admin sieht negative Bestände, ungültige FK, Doppelmissionen/Claims/Inventar-Auffälligkeiten.
- [ ] **ADM-012** [P0] GameMaster-Maßnahmen — Eventstart, NPC/Quest-Steuerung ohne Kontozugriff oder Ownersecrets.
- [ ] **ADM-013** [P0] Melde- und Appealverwaltung — Moderationsfälle sind einsehbar, bearbeitbar und begründet.
- [ ] **ADM-014** [P0] AutoBot Monitoring — Raten-/Abuse-Anomalien führen zu Review statt blindem IP-Bann.
- [ ] **ADM-015** [P0] Stats und Servermonitor — Worker, DB, Last, Error rate und Backupalter werden dargestellt.
- [ ] **ADM-016** [P0] Admin Backups — DB-Backup initiiert, zeigt Checksum/Alter und getrennten Restore-Drill.
- [ ] **ADM-017** [P0] Data retention Controls — Datenschutz-Anfragen und Aufbewahrungsregeln mit Audit und Freigabe.
- [ ] **ADM-018** [P0] Admin Rollenprüfung — Negativtest aller Admin-Endpoints gegen Player, Mod, GM, Admin und Owner.
- [ ] **ADM-019** [P0] Notfall-Flag — Kill Switch für Handel/PvP/Missionen erhalten laufende Abwicklung ohne Dupe.

## Frontend, Internationalisierung, Usability

- [ ] **UX-001** [P1] Eigenes Cyber-Gold-Design — Dark Onyx, Gold und Cyan, keine geschützten Fremdassets; konsistente Komponenten.
- [ ] **UX-002** [P1] Globale Navigation — Alle Screens aus 07_COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX sind erreichbar und nutzbar.
- [ ] **UX-003** [P1] Responsiv 320-1920 — Alle Eingaben/Tabellen/Karten auf Mobile und Desktop ohne Funktionsverlust.
- [ ] **UX-004** [P1] Tastatur und ARIA — Fokussteuerung, Modale, Statusmeldungen und Kontrast barrierearm gemäß WCAG 2.2 AA.
- [ ] **UX-005** [P1] Internationalisierung Deutsch — Alle Spielelemente samt Hilfetext und Validierung in Deutsch.
- [ ] **UX-006** [P1] Internationalisierung Englisch — Gleiche Featureabdeckung und gleiche Bedeutungen auf Englisch.
- [ ] **UX-007** [P1] Internationalisierung Vietnamesisch — Locale Vi vollständig und überprüfbare Fallback-Strategie.
- [ ] **UX-008** [P1] Internationalisierung Spanisch — Locale Es vollständig und überprüfbare Fallback-Strategie.
- [ ] **UX-009** [P1] Internationalisierung Türkisch — Locale Tr vollständig und überprüfbare Fallback-Strategie.
- [ ] **UX-010** [P1] Zeit, Zahlen, Plural — Datums-, Reisezeit-, Ressourcenzahlen und Plural korrekt nach Sprachgebiet.
- [ ] **UX-011** [P1] Echtzeit SSE/Websocket — Privat-/Allianz-/Weltkanäle sind autorisiert mit Reconnect und EventIDs.
- [ ] **UX-012** [P1] Polling-Fallback — Nach Verbindungsfehler bleiben Queue-/Kampf-/Chatinformationen aktuell.
- [ ] **UX-013** [P1] Hilfetexte — In jedem Funktionsbereich steht eine vollständige benutzbare Erklärung.
- [ ] **UX-014** [P1] Systemstatus/Fehlerzustände — Loading/Empty/Fail/Offline für alle Screens und Aktionen abgedeckt.
- [ ] **UX-015** [P1] Interaktive Bau-/Research-Graphen — Preconditions und freigeschaltete Knoten können per Screenreader gelesen werden.
- [ ] **UX-016** [P1] Map-Leistungsoptimierung — Karten und Bewegungen paginiert/Tile-optimiert, ohne gigantische Ganzweltpayload.
- [ ] **UX-017** [P1] Notification Center — Missionen/Forschung/Kampf/Adminevents erscheinen sichtbar und filterbar.
- [ ] **UX-018** [P1] PWA offline read-only — Optional Offline-Navigation von Hilfetexten; offline keine mutierenden Commands.

## Automatisierung, Tests und Deployment

- [ ] **OPS-001** [P0] One command dev — Sauberer Checkout startet lokale DB/Worker/API und seedbare Demowelt.
- [ ] **OPS-002** [P0] One command staging — Private Stagingumgebung startet mit produktionsnahen Services und Testdaten.
- [ ] **OPS-003** [P0] Docker production bundle — Container starten ohne dev reload; DB und Redis privat; Persistenz und Proxy.
- [ ] **OPS-004** [P0] Migration-Upgrade — Migrationen ohne Datenverlust und Restoreplan nachweisbar.
- [ ] **OPS-005** [P0] Automatische CI — Lint, Format, Types, Unit/Integration/Browser und Scans laufen auf Pull Request.
- [ ] **OPS-006** [P0] Secretscanner — Vor Kommit/Release werden Token und Private Keys entdeckt und blockiert.
- [ ] **OPS-007** [P0] SBOM und Drittanbieter-Notices — Abhängigkeiten und Herkunft dokumentiert; Lizenzgates vor Imagebau.
- [ ] **OPS-008** [P0] Rate-Limit/CSRF/XSS/IDOR Tests — Häufige Webrisiken und fremde Objekte mit negativen Tests abgedeckt.
- [ ] **OPS-009** [P0] Race Condition Tests — Dispatch/Market/Claim/Colonize/Worker parallel und nach Crash genau einmal.
- [ ] **OPS-010** [P0] Property tests — Ressourcen und Einheiten bleiben innerhalb Invarianten und deterministisch.
- [ ] **OPS-011** [P0] Kampfreplay-Testruns — 1000 Seed-Fälle liefern stable Output und no mutation bei dry_run.
- [ ] **OPS-012** [P0] Loadtest 30min — 200 aktive/1000 Accounts Szenario mit dokumentierten p95/error/queue lag.
- [ ] **OPS-013** [P0] Multiworld-Isolationstest — Cross-World Spieler können kein Geheimdaten/Items/Ressourcen bewegen.
- [ ] **OPS-014** [P0] Backup-Retention — Tag/Woche/Monat Plan, Verschlüsselung und Offsite-Adapter dokumentiert.
- [ ] **OPS-015** [P0] Restore-Probe — Isolierter Restore plus DB/Resource/Missionschecksum ist erfolgreich.
- [ ] **OPS-016** [P0] Health/Ready Endpoint — Web und Worker signalisieren getrennte Lebens-/Bereitschaftsdaten.
- [ ] **OPS-017** [P0] Alerts und Observability — Backupalter, Eventlag, Errorrate und DB/Service-Ausfall erzeugen Alarm.
- [ ] **OPS-018** [P0] Systemhärtung — Nicht-root Container, Firewall, Dienstkonto, restrictive secrets und TLS-Ready.
- [ ] **OPS-019** [P0] Operator Runbook — Start/Stop/Migration/Incident/Backup/Restore/KeyRotation sind Schritt-für-Schritt dokumentiert.
- [ ] **OPS-020** [P0] Live Launch Gate — Externe Domain/VPS/SMTP/Rechtstexte bleiben bis Ownergenehmigung offline vorbereitet.
- [ ] **OPS-021** [P0] Fail/Resume Agent — Agent schreibt validen Checkpoint und kann auf neuer Sitzung ohne Ratefragen fortsetzen.
- [ ] **OPS-022** [P0] Ausführlicher QA Report — Jedes Feature hat echten Test-/UI-/Codebeleg statt bloßem Checkboxstatus.
- [ ] **OPS-023** [P0] License Gate — MIT/Devana nur mit Notice/Rechten; GPL/AGPL/CC unterbleiben ohne bewussten Lizenzentscheid.
- [ ] **OPS-024** [P0] Dependencies Upgrade — Veraltete/unmaintained Komponenten werden bewertet und Tests bei Updates durchgeführt.



---

<!-- QUELLDOKUMENT: spec/IMPLEMENTATION_ORDER.md -->

# FUR EMPIRE — AGENT BUILD ORDER

Epics werden nach Abhängigkeit abgearbeitet; alle Feature-IDs sind verpflichtend, auch P2.

## E00 — Audit & Lizenz

Abhängigkeiten: keine; 0 primär zugeordnete Feature-IDs.



## E01 — Infrastruktur / CI

Abhängigkeiten: E00; 6 primär zugeordnete Feature-IDs.

OPS-001, OPS-002, OPS-003, OPS-005, OPS-006, OPS-007

## E02 — Identität / Welten / Datenschutz

Abhängigkeiten: E01; 20 primär zugeordnete Feature-IDs.

F2-001, F2-002, F2-003, F2-004, F2-005, F2-006, F2-007, ACC-001, ACC-002, ACC-003, ACC-004, ACC-005, ACC-006, ACC-007, ACC-008, ACC-009, ACC-010, ENG-001, ENG-002, ENG-003

## E03 — FUR-2-Migration / Ledger

Abhängigkeiten: E02; 53 primär zugeordnete Feature-IDs.

F2-008, F2-009, F2-010, F2-011, F2-012, F2-013, F2-014, F2-015, F2-016, F2-017, F2-018, F2-019, F2-020, F2-021, F2-022, F2-023, F2-024, F2-025, F2-026, F2-027, F2-028, F2-029, F2-030, F2-031, F2-032, F2-033, F2-034, F2-035, F2-036, F2-037, F2-038, F2-039, F2-040, F2-041, F2-042, F2-043, F2-044, F2-045, F2-046, F2-047, F2-048, F2-049, F2-050, F2-051, F2-052, F2-053, F2-054, F2-055, F2-056, F2-057, F2-058, F2-059, F2-060

## E04 — Zeit-Engine / Queues

Abhängigkeiten: E03; 14 primär zugeordnete Feature-IDs.

ENG-004, ENG-005, ENG-006, ENG-007, ENG-008, ENG-009, ENG-010, ENG-011, ENG-012, ENG-013, ENG-014, ENG-015, ENG-016, ENG-017

## E05 — Terra-Karte / Mehrkolonien

Abhängigkeiten: E04; 25 primär zugeordnete Feature-IDs.

W01, W02, W03, W04, W05, W06, W07, W08, W09, W10, TERRA-001, TERRA-002, TERRA-003, TERRA-004, TERRA-005, TERRA-006, TERRA-007, TERRA-008, TERRA-009, TERRA-010, TERRA-011, TERRA-012, TERRA-013, TERRA-014, TERRA-015

## E06 — Wirtschaft / Gebäude / Forschung

Abhängigkeiten: E05; 24 primär zugeordnete Feature-IDs.

E01, E02, E03, E04, E05, E06, E07, E08, ECO-001, ECO-002, ECO-003, ECO-004, ECO-005, ECO-006, ECO-007, ECO-008, ECO-009, ECO-010, ECO-011, ECO-012, ECO-013, ECO-014, ECO-015, ECO-016

## E07 — Kampf-Engine / Units

Abhängigkeiten: E06; 25 primär zugeordnete Feature-IDs.

K01, K02, K04, K12, K14, WAR-001, WAR-002, WAR-003, WAR-004, WAR-005, WAR-006, WAR-007, WAR-008, WAR-009, WAR-010, WAR-011, WAR-012, WAR-013, WAR-014, WAR-015, WAR-016, WAR-017, WAR-018, WAR-019, WAR-020

## E08 — Missionen / Spionage / Fernkampf

Abhängigkeiten: E07; 9 primär zugeordnete Feature-IDs.

K03, K05, K06, K07, K08, K09, K10, K11, K13

## E09 — Allianz / Diplomatie

Abhängigkeiten: E08; 20 primär zugeordnete Feature-IDs.

A01, A02, A03, A04, SOC-001, SOC-002, SOC-003, SOC-004, SOC-005, SOC-006, SOC-007, SOC-008, SOC-009, SOC-010, SOC-011, SOC-012, SOC-013, SOC-014, SOC-015, SOC-016

## E10 — Sozial / Berichte / Moderation

Abhängigkeiten: E09; 4 primär zugeordnete Feature-IDs.

A05, A06, A07, A08

## E11 — NPC / Quests / Endgame

Abhängigkeiten: E08; 20 primär zugeordnete Feature-IDs.

P01, P02, P04, PVE-001, PVE-002, PVE-003, PVE-004, PVE-005, PVE-006, PVE-007, PVE-008, PVE-009, PVE-010, PVE-011, PVE-012, PVE-013, PVE-014, PVE-015, PVE-016, PVE-017

## E12 — Orbit Welten / Kolonien

Abhängigkeiten: E11; 10 primär zugeordnete Feature-IDs.

ORB-001, ORB-002, ORB-003, ORB-004, ORB-005, ORB-006, ORB-007, ORB-008, ORB-009, ORB-010

## E13 — Orbit Flotten / Kampf

Abhängigkeiten: E12; 22 primär zugeordnete Feature-IDs.

ORB-011, ORB-012, ORB-013, ORB-014, ORB-015, ORB-016, ORB-017, ORB-018, ORB-019, ORB-020, ORB-021, ORB-022, ORB-023, ORB-024, ORB-025, ORB-026, ORB-027, ORB-028, ORB-029, ORB-030, ORB-031, ORB-032

## E14 — Inventar / Handel / Helden

Abhängigkeiten: E13; 12 primär zugeordnete Feature-IDs.

P06, ITEM-001, ITEM-002, ITEM-003, ITEM-004, ITEM-005, ITEM-006, ITEM-007, ITEM-008, ITEM-009, ITEM-010, ITEM-011

## E15 — Saisons / LiveEvents / Ranking

Abhängigkeiten: E14; 16 primär zugeordnete Feature-IDs.

P03, P05, PVE-018, SEAS-001, SEAS-002, SEAS-003, SEAS-004, SEAS-005, SEAS-006, SEAS-007, SEAS-008, SEAS-009, SEAS-010, SEAS-011, SEAS-012, SEAS-013

## E16 — Administration / Anti-Abuse

Abhängigkeiten: E15; 21 primär zugeordnete Feature-IDs.

T04, T08, ADM-001, ADM-002, ADM-003, ADM-004, ADM-005, ADM-006, ADM-007, ADM-008, ADM-009, ADM-010, ADM-011, ADM-012, ADM-013, ADM-014, ADM-015, ADM-016, ADM-017, ADM-018, ADM-019

## E17 — Design / Mobile / i18n

Abhängigkeiten: E16; 12 primär zugeordnete Feature-IDs.

T05, T06, UX-001, UX-002, UX-003, UX-004, UX-005, UX-006, UX-007, UX-008, UX-009, UX-010

## E18 — Realtime / Integrationen

Abhängigkeiten: E17; 9 primär zugeordnete Feature-IDs.

T07, UX-011, UX-012, UX-013, UX-014, UX-015, UX-016, UX-017, UX-018

## E19 — Sicherheit / Datenschutz / Betrieb

Abhängigkeiten: E18; 13 primär zugeordnete Feature-IDs.

T01, T02, T03, OPS-004, OPS-008, OPS-009, OPS-014, OPS-015, OPS-016, OPS-017, OPS-018, OPS-023, OPS-024

## E20 — Vollständige QA & Performance

Abhängigkeiten: E19; 5 primär zugeordnete Feature-IDs.

OPS-010, OPS-011, OPS-012, OPS-013, OPS-022

## E21 — Betriebsbereites Handoff

Abhängigkeiten: E20; 4 primär zugeordnete Feature-IDs.

T09, OPS-019, OPS-020, OPS-021




---

<!-- QUELLDOKUMENT: agent/AGENT_START_PROMPT.md -->

# DIREKT AN DEN CODING-AGENTEN SENDEN — FUR EMPIRE KOMPLETTBAU

Du bist der **autonom arbeitende Principal Game Engineer und QA-/Security-/DevOps-Agent** für das Projekt **FUR EMPIRE**. Dein Auftrag ist die **vollständige, echte Implementierung aller Spielsysteme**, nicht nur eine Demo, eine UI oder eine Roadmap. Arbeite im **bereits vorhandenen aktuellen FUR-Repository**, erhalte dessen Bestandsdaten und baue darauf auf. Arbeite ohne unnötige Nachfragen und fahre nach jedem erfolgreichen Arbeitspaket mit dem nächsten fort, solange deine Toolausführung läuft. Keine künstlichen Meilensteinstopps oder 'fertig'-Meldungen, bevor alle Aufgaben tatsächlich abgenommen sind.

**Lies in dieser Reihenfolge:** `00_START_HIER.md`, `agent/AGENTS.md`, `agent/BUILD_LOOP.md`, `docs/01_MASTER_GAME_DESIGN.md`, `docs/02_TECHNICAL_CONTRACTS.md`, `docs/03_IMPLEMENTATION_ROADMAP.md`, `docs/04_SECURITY_OPERATIONS_LIVE.md`, `docs/05_TEST_STRATEGY.md`, `docs/06_SOURCE_LICENSE_REGISTER.md`, `docs/07_COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX.md`, `docs/08_GAME_MECHANICS_STATE_MACHINES.md`, `docs/09_AGENT_ACCEPTANCE_AND_OWNER_HANDOFF.md`, `docs/10_OWN_ASSETS_BRANDING.md`, `spec/FEATURES.json`, `spec/FEATURE_INDEX.md`, `rulesets/*`, `reference/SPIELANLEITUNG_FUR2_ORIGINAL.md`, `reference/FUR2_55_GAPS_ORIGINAL.json`.

**MUSS-UMFANG:** Alle **344 Initial-Feature-IDs** aus `spec/FEATURES.json` inklusive sämtlicher dokumentierter FUR-2-Systeme, aller 55 ursprünglichen Lücken und aller weiteren Funktionsdetails: Welt/Mehrkolonien/Terrain/Nebel/Regionskontrolle, Wirtschaft/Handel/Inventar/Fertigung, komplett datengetriebenes Gebäudesystem und Forschungsbäume, 3+12 Terra-Units, neue Kampfrunden, Spionage, Simulator, PvP/PvE, Rückzug, Artillerie, Expeditionen, NPCs, Worldbosses, Diplomatie, Allianzen, gemeinsame Angriffe, Wars/Forums/Chats/Reports, Fraktionsdoktrinen, Quests, Erfolge, Events, Multiworld, Saisons, Hall of Fame, **Orbit mit 14 Schiffsklassen, Planeten/Monden/Stationen/Flotten/Wracks/Sensorik/Sprungtor**, Administration, Moderation, Sicherheit, Rechtstexte-Platzhalter, vollständige Übersetzungen, Mobile-UI, Realtime, AI-/Discord-Adapter nur freiwillig und sicher, CI/CD, Backups und getestetes Restore.

**Sofort beginnen:** Prüfe aktuellen Git-Stand und Quellcode, führe vorhandene Tests aus, ziehe ein Backup der vorhandenen Daten, dokumentiere `AUDIT_CURRENT_FUR2.md`, lege einen sicheren Feature-Branch an und starte Roadmap E00 → E21. Alle bestehenden FUR-2-Werte nur nach geprüftem Code übernehmen; bei abweichendem Ist-Stand Migration und Datenkompatibilität dokumentieren. Wenn der tatsächliche aktuelle FUR-2-Code nicht verfügbar ist, baue ein klar getrenntes neues System und kennzeichne den fehlenden Integrationsnachweis als Blocker; behaupte keine erfolgreiche FUR-2-Migration.

**Pro Feature:** Domain-Logik, DB-Migration, API, UI-Screen inkl. Mobil/Barrierefreiheit, lokalisierte Texte DE/EN/VI/ES/TR, Rollen-/World-Prüfung, positive/negative/Concurrency-Tests, Hilfetexte, `TRACEABILITY.md` mit exakten Code- und Testergebnissen. Ein Testfehler bedeutet reparieren und erneut testen. Kein Button darf wirkungslos sein. Kein Feature ohne reale Nachweise `verified` nennen.

**Sicherheit & Recht:** Keine fremden GPL-/AGPL-/CC-BY-NC-ND-Codes in den neuen FUR-Kern kopieren; keine fremden Grafiken/Marken/UI kopieren. Eigenständige Implementierung oder spezifisch rechtlich freigegebene MIT-/andere permissive Komponenten unter korrekten Notices. Niemals in Chats offengelegte Schlüssel verwenden. Keine geheimen Werte in Git. Keine Domain/Root/VPS bestellen, Kosten auslösen, Produktionsdaten öffentlich machen, Echtgeldzahlungen aktivieren oder Produktivserver ohne explizite Eigentümerfreigabe deployen.

**Abnahmeregel:** Alle 344 Feature-IDs müssen belegbar `verified` sein. Schreibe `PROGRESS_LOG.md`, `RESUME_STATE.json`, `RELEASE_CANDIDATE_REPORT.md`, `SECURITY_REPORT.md`, `PERFORMANCE_REPORT.md`, `OWNER_HANDOFF.md`. Teste den vollständigen Spielerlebenszyklus mit 2–10 Testaccounts und mindestens zwei Welten, deterministische Gefechtsreplays, Anti-Duping, Browser-E2E, 30-minütige Last und isolierten Backup-Restore. Echte Messungen statt erfundener Zahlen. Nächsten Abhängigkeitsschritt selbst beginnen, auch wenn eine Demo schon läuft. Bei Quota-/Sitzungsende den exakten Resume-Zustand sichern und für den nächsten Agenten `agent/RESUME_PROMPT.md` nutzen. Die gewünschte Eigenständigkeit berechtigt nicht zum Umgehen von Sicherheitsgates.

**Endzustand:** Komplett installiertes, lokal bzw. in privatem Staging spielbares, reproduzierbar testbares FUR Empire — danach muss der Eigentümer nur noch externe Domain/VPS/SMTP, Produktionssecrets, Betreiberrechtliches und ausdrückliche Go-Live-Freigabe erledigen. Alles andere gehört zur Agentenimplementierung, nicht auf die Handoff-Liste.

