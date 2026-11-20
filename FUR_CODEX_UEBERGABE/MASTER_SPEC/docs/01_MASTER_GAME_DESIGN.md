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
