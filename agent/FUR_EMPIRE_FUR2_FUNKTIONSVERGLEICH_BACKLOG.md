# FUR Empire – Funktionslücken gegenüber neun Open-Source-Strategiespielen

Stand: 06.11.2026. **Grundlage ist ausschließlich die hochgeladene `SPIELANLEITUNG.md` als dokumentierter Ist-Stand FUR-2.** Die aktuelle laufende FUR-2-Codebasis wurde nicht bereitgestellt und nicht getestet. „Nicht dokumentiert“ bedeutet daher nicht zwingend „technisch nicht vorhanden“.

## Legende
- **P0:** fundamental für strategische Spieltiefe oder sicheren Dauerbetrieb.
- **P1:** wichtiger Ausbau; **P2:** spätere oder optionale Erweiterung.
- **Teilweise:** Der Ist-Stand beschreibt verwandte Bausteine, aber nicht die referenzierte Erweiterung.
- Quellen: D = Devana, T = Tribal-Wars-Open-Source, U = ugml/php-client, O = OGameX, X4 = XGProyect 4, X3 = XGProyect 3, L = Sprachpakete, A = historische Archive, X2 = XGProyect 2.10.

**Bereits dokumentiert:** gemeinsame 64×64-Karte, 104 neutrale Posten, 8 Gebäude, 3 Technologien, 3 Truppentypen, Rohstoffproduktion, Reserve-Lager, Direktiven, PvP, Transporte, Garnisonen, Eroberung, Rohstoffbörse, Spieler-Markt, Allianzen, Diplomatie, Nachrichten/Chat, Rangliste, Fraktionen, Produktionsereignisse, Saisons, Urlaub, Moderation, TOTP/E-Mail, Worker, PostgreSQL/SQLite. Diese Fähigkeiten dürfen im Backlog nicht pauschal als fehlend bewertet werden.


## Detaillierter Gap-Backlog


### Welt & Expansion

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| W01 | Mehrere vollständig ausbaubare Kolonien | Nicht dokumentiert | **P0** | O,X4,X3,U | Zweite Basis gründen, separat entwickeln und zentral verwalten |
| W02 | Kolonisation leerer Sektoren | Nicht dokumentiert | **P0** | O,X3,U | Gründung statt nur Eroberung; Kolonisationskosten und Distanzen |
| W03 | Eigene Kolonien untereinander versorgen | Teilweise | **P0** | O,X3,U | Transfer zwischen eigenen Basen; übergreifende Missionsplanung |
| W04 | Fog of War und Aufklärungsstufen | Nicht dokumentiert | **P0** | O,X3 | Nicht jedes gegnerische Militärdetail ohne Spionage sichtbar machen |
| W05 | Strategische Geländearten (Wald, Wasser, Berge, Pass) | Nicht dokumentiert | **P1** | D | Einfluss auf Bewegungswege, Produktion und Verteidigung |
| W06 | Karten-Generator und weitere Welten | Nicht dokumentiert | **P1** | D,O,X4 | Seeds, Gelände, Welten mit eigenen Einstellungen und Weltenliste |
| W07 | Dynamischer NPC-/Außenposten-Nachschub | Nicht dokumentiert | **P0** | O | Neutrale Ziele respawnen oder Bestände erneuern; Schutz vor leerer Welt |
| W08 | Territoriumsgrenzen / Regionen / Kontrollzonen | Nicht dokumentiert | **P2** | D,T | Strategische Regionsziele und Gebietsboni |
| W09 | Karten-Suche, Marker, Favoriten | Nicht dokumentiert | **P1** | O,X3 | Koordinatensuche, Ziel-Bookmarks, Sprungfunktionen |
| W10 | Erweiterte NPC-Fraktionen und KI-Gegner | Nicht dokumentiert | **P1** | O | Gegenbewegungen und eskalierende Herausforderungen |

### Kampf & Missionen

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| K01 | Mehrstufiger, rundenbasierter Kampf | Teilweise | **P0** | O,X4,X3,X2 | Eigene Schadens-, Rüstungs-, Schild- und Rundenlogik |
| K02 | Einheiten mit spezifischen Rollen und Gegen-Effekten | Teilweise | **P0** | D,O,X4 | Mindestens 8–12 zunächst klar unterscheidbare Einheiten |
| K03 | Spionage / Gegenaufklärung | Nicht dokumentiert | **P0** | O,X3 | Späher, verdeckte Informationen, Abfangchancen |
| K04 | Kampfsimulator vor Missionsstart | Nicht dokumentiert | **P1** | D,O | Eigene Simulation, Anzeige von Verlustspannen |
| K05 | Gemeinsame Allianzangriffe (ACS) | Nicht dokumentiert | **P0** | O,X4,X3,X2 | Kombinierter Verband mehrerer Spieler mit gemeinsamer Ankunft |
| K06 | Unterstützung fremder Allianzbasen | Teilweise | **P0** | O,X3 | Defensive Garnison auch bei Verbündeten stationieren |
| K07 | Taktischer Rückzug und laufende Mission abbrechen | Nicht dokumentiert | **P1** | O,X3 | Rückruf, Rückzugsschwellen, definierte Rückmarschfolgen |
| K08 | Expeditionen und Ereignis-Missionen | Nicht dokumentiert | **P1** | O,X4,X3 | PvE-Expedition mit zufälligen Chancen und Belohnungen |
| K09 | Trümmerfelder, Bergung und Reparatur | Nicht dokumentiert | **P2** | O,X3 | Nach Schlachten zerstörte Materialien bergen |
| K10 | Fernkampfangriffe / Artillerie / Raketen | Nicht dokumentiert | **P2** | O,X3 | Spezielle Fernmissionen mit Gegenmaßnahmen |
| K11 | Unterschiedliche Truppen-Geschwindigkeit und Reichweite | Nicht dokumentiert | **P1** | O,X3 | Armeezusammenstellung bestimmt Marschzeit und Kosten |
| K12 | Kampfbericht pro Runde und Einheit | Teilweise | **P1** | O,X3,X2 | Schaden, Einheitenverluste, Loot, Zeit, beteiligte Spieler |
| K13 | Schlachtvorlagen / Angriffsprofile | Nicht dokumentiert | **P2** | O,X3 | Schnelles wiederholbares Entsenden üblicher Truppentypen |
| K14 | Weitere Verteidigungsobjekte | Teilweise | **P1** | O,X4,X3,U | Türme, Geschütze, Fallen, Reparatur und Anlagenslots |

### Wirtschaft & Technik

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| E01 | Abhängiger Forschungs- und Freischaltbaum | Teilweise | **P0** | D,O,X4,X3,U | Tech-Voraussetzungen, neue Einheiten und Gebäudetypen |
| E02 | Erweiterbare Gebäudekategorien / Spezialausbauten | Teilweise | **P1** | D,O,X4 | Werkstatt, Versorgung, Spionagezentrum, Festung |
| E03 | Energie-, Betriebs- oder Unterhaltsmechanik | Nicht dokumentiert | **P2** | O,X4,X3 | Optionaler vierter Wirtschaftskreislauf statt trivialer Produktion |
| E04 | Bau-/Forschungswarteschlangen umordnen & stornieren | Nicht dokumentiert | **P1** | O,X3 | Stornieren, Rückerstattung und planbare Folgestufen |
| E05 | Ausbau jenseits von Stufe 10 / Prestige | Nicht dokumentiert | **P1** | D,O,X4 | Späte Spielphase mit Kostenkurve und Meisterungsstufen |
| E06 | Marktpreis-Statistiken und Handelsverlauf | Nicht dokumentiert | **P2** | X3,O | Transparente Preisentwicklung und Transaktionshistorie |
| E07 | Datengetriebene Konfig für Gebäude, Einheiten, Formeln | Teilweise | **P0** | D,O,X4 | Versionierte Regeldefinitionen statt hartcodierter Spielwerte |
| E08 | Fraktionsspezifische Einheiten/Technologien | Teilweise | **P1** | D,O | Fraktionswahl wirkt stärker auf Spielstil als nur passive Boni |

### Allianz & Spieler

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| A01 | Allianzkrieg mit Zielen, Wertung und Frieden | Teilweise | **P1** | D,X3 | Krieg nicht bloß als Diplomatiestatus: Ziele, Zeit, Ergebnis |
| A02 | Allianz-Rangliste und gemeinsame Siege | Nicht dokumentiert | **P1** | O,X3 | Allianzstatistik, Saisonplatzierung, Kriegsfortschritt |
| A03 | Allianzkasse / Gemeinschaftsprojekte | Nicht dokumentiert | **P2** | O | Allianzdepot, gemeinsame Festungen, Beiträge |
| A04 | Flexible Allianz-Rollen und Einzelberechtigungen | Teilweise | **P2** | X4,X3 | Rollen jenseits Leitung/Offizier/Mitglied |
| A05 | Freundesliste und Blockliste | Nicht dokumentiert | **P2** | O,X3 | Kontakte, Anfragen, private Kommunikation |
| A06 | Interne Foren / Pinnwand | Nicht dokumentiert | **P2** | X3,T | Längerfristige Strategiedokumente der Allianz |
| A07 | Spielerprofile, Badges, Leistungsdaten | Nicht dokumentiert | **P2** | O,X3 | Öffentliche Profilansicht und Historie |
| A08 | Notizen, Berichtsfreigaben, Zielmarkierungen | Nicht dokumentiert | **P2** | O,X3 | Persönliche Kartenhinweise und gemeinsame Einsatzplanung |

### Progression & Livebetrieb

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| P01 | Fortlaufende Quest-/Erfolgsysteme | Teilweise | **P1** | O | Fünf Direktiven zu einer Progressionskette ausbauen |
| P02 | Langfristiges Endgame nach Zitadellen-Sieg | Nicht dokumentiert | **P0** | D,O | Neue Boss-Stufen, wechselnde Kampagnen, globale Ziele |
| P03 | Saisonmechaniken / faire Neustartwelten | Teilweise | **P1** | O,X4 | Optional Saisonwelt mit Reset und separatem Dauerwelt-Spielstand |
| P04 | Spieler-Balance und Comeback-Schutz | Teilweise | **P0** | O,X4 | Schutz nach Niederlage, Noobschutz, Abschwächung des Snowballs |
| P05 | Ereignisse mit Missions- und Kampfvarianten | Teilweise | **P1** | O | Nicht nur Produktion, sondern spezifische PvE-Events |
| P06 | Vernünftige Automatisierung für Rückkehrer | Nicht dokumentiert | **P2** | O,X3 | Benachrichtigungen, Aufgabenstatus, Kommandoübersichten |

### Technik & Betrieb

| ID | Funktion | Dokumentierter Stand | Priorität | Quellen | Konkrete Ergänzung |
|---|---|---|---|---|---|
| T01 | Automatische Backups + Restore-Probe | Nicht dokumentiert | **P0** | X4 | Backups, Wiederherstellungstest, Rotation und Zugriffsschutz |
| T02 | Race-Condition-/Lasttests und Missions-Idempotenztests | Nicht dokumentiert | **P0** | O | Parallelstart, doppelte Buchung, Worker-Absturz, Replay testen |
| T03 | Anti-Bot/Anti-Multiaccount/Rate Limits | Nicht dokumentiert | **P0** | O,X4 | Abuse-Detektion ohne personenbezogene Überwachungsexzesse |
| T04 | Umfassende Welt- und Balancing-Adminwerkzeuge | Teilweise | **P1** | X4,O | Weltregeln, Missions-Suche, Korrekturwerkzeuge und Telemetrie |
| T05 | Mehrsprachigkeit / Lokalisierung | Nicht dokumentiert | **P2** | O,X4,L | String-Katalog für DE/EN, anschließend weitere Sprachen |
| T06 | Responsive Mobile-/Accessibility-Prüfung | Nicht dokumentiert | **P1** | O | Bedienung und Tastaturzugänglichkeit für Karte und Kampf |
| T07 | Echtzeit-Updates statt ausschließlich Polling | Teilweise | **P2** | O | Websocket/SSE für Missionen und Allianzkoordination |
| T08 | Spielregel-Migrationen und Balancing-Simulation | Teilweise | **P1** | X4,O | Regelversions-Snapshots gegen echte Formellogik validieren |
| T09 | Sicherer Test-/Produktions-Release-Prozess | Teilweise | **P1** | O,X4 | CI/CD mit Tests, Rollback, Spiel-DB-Migration, Monitoring |

## Abgleich der 9 Quellen

- **[Devana](https://github.com/ioying/devana)** (D): Siedlungen/nodes, modulares Bauen und Produzieren, fraktionsabhängige Regeln, Kampf-Simulator, Terrain-Karte und Krieg/Frieden. Eigene permissive Lizenz (Bedingungen beachten).
- **[Tribal Wars Open Source](https://github.com/laserswald/Tribal-Wars-Open-Source)** (T): Überwiegend historische Startseite, JavaScript, CSS und Grafiken; keine vollständige spielbare Server-Engine. Keine direkte Übernahme lizenzrechtlich ungeprüfter Grafiken.
- **[Ugamela](https://github.com/ugml/php-client)** (U): Frühere Flotten-, Bauen-, Forschungs- und Galaxieansätze, MVC-Aufteilung. Alpha, nicht produktionsreif; AGPL-3.0.
- **[OGameX](https://github.com/lanedirt/OGameX)** (O): Beste moderne Referenz: Kampfengine, Expeditionen, Spionage, ACS, Missionen, Kolonisation, Worker-/Race-Test-Strategien. MIT für eigenen Backendcode; ausdrücklich keine blanket-Freigabe für Artwork.
- **[XG Proyect 4](https://github.com/XGProyect/XGProyect)** (X4): Modulares GameObjectRegistry, Forschungsformeln, Administration, Backups, Nutzerverwaltung. GPL-3.0.
- **[XG Proyect 3](https://github.com/XGProyect/XG-Proyect-v3.x.x)** (X3): Historische vollständige Modulauswahl: Flottenaufträge, Allianzen, Forum, Phalanx, Freunde, Notizen und Kampfsystem. GPL-3.0; archiviert.
- **[XG Sprachpakete](https://github.com/XGProyect/XG-Proyect-v3.x.x-Languages)** (L): Übersetzungsstruktur für Englisch/Spanisch/Türkisch, kein eigenständiges Gameplay. GPL-3.0.
- **[XG Legacy-Archiv](https://github.com/XGProyect/legacy-versions)** (A): Versionsarchive ohne neue unabhängige Engine; als Forschungs-/Regression-Referenz, Lizenz innerhalb der Archive prüfen.
- **[XG Proyect 2.10](https://github.com/XGProyect/XG-Proyect-v2.10.x)** (X2): Historische Rundenkampf-Engine, Ressourcensystem, Flotten- und Gebäudefunktionen; nicht als moderne Produktionsbasis verwenden.

## Kritische Balance-Risiken der aktuellen dokumentierten FUR-2-Regeln

1. **104 endliche neutrale Außenposten mit nicht regenerierenden Beständen:** Nach dem Farmen sind neue Spieler im Nachteil, auch wenn die Welt noch freie Felder hat. Empfehlung: kontrollierte Neuspawns, periodische Ressourcen und PvE-Progression.
2. **Jeder eroberte Posten +5 Prozentpunkte Produktion:** Wer früh Posten sammelt, beschleunigt dauernd weiter (Snowball). Empfehlung: skalierende Abnahme, Kosten, Obergrenzen oder Versorgungs-/Kontrollkosten.
3. **Neulingsschutz nach nur einer Stunde vorbei:** Für asynchrone Browser-Strategiespiele zu kurz, besonders gegen ältere Accounts. Empfehlung: Schutz nach Machtverhältnis/Spielerentwicklung und Rückkehrschutz.
4. **Gegnerische Verteidigung wird bei Angriff angezeigt:** Spionage und Täuschung sind so nur eingeschränkt sinnvoll. Empfehlung: Informationsstufen durch Aufklärung sowie genaue Daten nur mit entsprechenden Fähigkeiten.
5. **Saisons archivieren Ranglisten, setzen die Welt nicht zurück:** Ohne Dauerendgame beziehungsweise getrennte Neustartwelten fehlt ein langfristiger Wiedereinstieg.
6. **3 Truppentypen, 3 Forschungen, 8 Gebäude mit Maximalstufe 10:** Balancing kann zwar gut sein, langfristig aber zu begrenzt. Erst Spiele-Systeme vertiefen, dann auf 8–12 Einheiten und verknüpfte Technologien erhöhen.
7. **FUR-2-Regelsnapshot enthält nicht jede im Code stehende Formel:** Für reproduzierbare Kampfauswertung und saisonale Fairness muss Simulationsversion samt exakten Formeln, Konfiguration und Migrationsregeln versioniert werden.

## Nächste Ausbaustufen

- **Sofort (Sicherheit und Fairness):** T01, T02, T03, P04, W07 und E07.
- **Strategie-Kern V3:** W01, W02, K01, K02, K03, K05, E01.
- **Mehrspieler-Tiefe V4:** K06, K07, K08, A01, A02, W05, W09.
- **Langfristiger Betrieb V5:** P02, P03, T04, T05, T06, T08, T09 und optionale P2-Features.

## Lizenzgrenze

Quellcode aus GPL-/AGPL-Quellen nicht stillschweigend in eine proprietäre MIT/geschlossene Codebasis kopieren. Devana-Lizenzauflagen beachten. Tribal-Wars-Grafiken nicht einfach verwenden. OGameX-Grafiken/Frontend fallen laut Projekt-Disclaimer nicht automatisch unter die MIT-Freigabe der Backendimplementierung. Eigene Spielregeln/Mechaniken dürfen als eigenständige Ideenquelle dienen; für konkrete Code-/Artwork-Übernahmen braucht es einen separaten Asset- und Lizenzcheck.

