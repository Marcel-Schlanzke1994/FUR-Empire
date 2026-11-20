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
- [ ] **K03** [P0] Spionage / Gegenaufklärung — Späher, verdeckte Informationen, Abfangchancen
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
- [ ] **WAR-010** [P0] Gegenaufklärung — Abfangchance nach Tech/RNG, bei Entdeckung Report/optional Gegenkampf ohne private Daten.
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

- [ ] **SOC-001** [P1] Allianzaufnahmeverfahren — Bewerbung, Einladung, Rücknahme, Annahme und Ablehnung sind einheitliche Zustände.
- [ ] **SOC-002** [P1] Granulare Allianzrechte — Rollen können spezifische Permissions erhalten, ohne Moderator/Server-Owner zu werden.
- [ ] **SOC-003** [P1] Führungsübertrag — Letzte Leitung darf nicht gehen, bevor neuer Leiter bestätigt ist.
- [ ] **SOC-004** [P1] Allianzkrieg-Objektive — Krieg hat Start, Ziele, Kriegswertung, Friedensverhandlung, Ende und öffentliches Protokoll.
- [ ] **SOC-005** [P1] Allianz-Rangliste — Aggregierte Score-Werte mit Anti-Multiaccount-Regeln und saisonaler Archivierung.
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
