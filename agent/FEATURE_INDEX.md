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

- [~] **W01** [P0] Mehrere vollständig ausbaubare Kolonien — Zweite Basis gründen, separat entwickeln und zentral verwalten
- [~] **W02** [P0] Kolonisation leerer Sektoren — Gründung statt nur Eroberung; Kolonisationskosten und Distanzen
- [~] **W03** [P0] Eigene Kolonien untereinander versorgen — Transfer zwischen eigenen Basen; übergreifende Missionsplanung
- [~] **W04** [P0] Fog of War und Aufklärungsstufen — Nicht jedes gegnerische Militärdetail ohne Spionage sichtbar machen
- [~] **W05** [P1] Strategische Geländearten (Wald, Wasser, Berge, Pass) — Terrain beeinflusst autoritativ Reisewege, Produktion und Verteidigung; Browser-/Accessibility-/Mehrspielerabnahme offen
- [~] **W06** [P1] Karten-Generator und weitere Welten — Seeds, Gelände, Welten mit eigenen Einstellungen und Weltenliste
- [ ] **W07** [P0] Dynamischer NPC-/Außenposten-Nachschub — Neutrale Ziele respawnen oder Bestände erneuern; Schutz vor leerer Welt
- [~] **W08** [P2] Territoriumsgrenzen / Regionen / Kontrollzonen — Strategische Regionsziele und Gebietsboni (teilweise implementiert; siehe spec/FEATURES.json)
- [~] **W09** [P1] Karten-Suche, Marker, Favoriten — Koordinaten-/Außenpostensuche, Sprungfunktion, private weltgebundene Favoriten (20 je Welt), Marker und Wegvorschau über bekannte begehbare Sektoren sind implementiert. Interaktive Browser-/Mobil-/Screenreader-Abnahme offen; Details und Tests in `spec/FEATURES.json` (W09/TERRA-012).
- [~] **W10** [P1] Erweiterte NPC-Fraktionen und KI-Gegner — Drei seed-stabile Fraktionen verstärken neutrale Posten weltisoliert und liefern gedeckelten Nachschub; sichtbare Grenzdruck-/Bedrohungsanzeige. SQLite/PostgreSQL 18, Fog- und UI-Escapingtests bestanden. Diplomatie, Gegenstrategien, NPC-Armeen/Kämpfe und tiefere Eskalation offen.

## Original-55: Kampf & Missionen

- [~] **K01** [P0] Mehrstufiger, rundenbasierter Kampf — Sechs-Runden-Resolver ist in FUR-3-PvE/PvP, Simulator und ACS-3 integriert; FUR-2 bleibt kompatibel. COMBAT-2-Neutralfortifikation ist ein optionaler, unbalancierter Entwurf; Schildwall-Struktur und manuelle UI-/Accessibility-Abnahme offen.
- [~] **K02** [P0] Einheiten mit spezifischen Rollen und Gegen-Effekten — COMBAT-3/4 versionieren je 21 Profile. Dynamische Weltkataloge laufen durch Dispatch, Bewegung/Treibstoff, Transport/Fracht, Versorgung, Garnison, Expedition, Kampf/ACS-Berichte, Rückkehr und Außenposten-Umwandlung. Schema 81 ergänzt einen COMBAT-4-only Wrack-/Reparaturentwurf mit 25%-Verlustquote, 48-Stunden-Fenster, Rohstoffreservierung und voller Rückerstattung bei Abbruch. Training bleibt bis Balance- und UI-/Geräteabnahme gesperrt; Migration ist source-only. Vollständige SQLite-/PostgreSQL-18-Suite nach Korrekturen: 655 bestanden, 1 übersprungen; Ruff/Black/mypy und 344-ID-Traceability bestanden.
- [~] **K03** [P0] Spionage / Gegenaufklärung — Zusätzlich FUR-3-only: versionierte Interception-/Detection-Regel mit auf Versand gepinnten Chancen und Seed, 50/60%-Caps, generischem Verteidigerbericht, Verlust genau eines Rangers beim Abfang und unterdrückter Intel. FUR-2 unverändert. SQLite-/PostgreSQL-18- und Gesamtsuite bestanden. Private Staging läuft auf Schema 77; Balance- und Browser-/Geräteabnahme offen.
- [~] **K04** [P1] Kampfsimulator — Lesende PvE-/PvP-Projektion: FUR-2 exakt, FUR-3 über 16 reproduzierbare Szenarien. COMBAT-4 nutzt Intel-gepinnte Verteidigungsanlagen und schätzt Minenauslösung/Integrität. PvP verlangt frische Stufe-2-Intel; Browser-/Geräte-/Accessibility-Abnahme offen.
- [~] **K05** [P0] Gemeinsame Allianzangriffe (ACS) — FUR-2-Welten behalten ACS-2; FUR-3-Welten pinnen ACS-3 und den Weltkampfregelsatz, Digest, Seed und Rückzug. Teilnehmer-/Einheitenstacks und Taktik bleiben über Mehr-Rundenkampf getrennt, Verluste und Rückkehr je Ursprung. SQLite 13 und PostgreSQL 18 26 gezielte Tests bestanden; Balance und manuelle Browser-/Mobil-/Screenreader-/Lokalisierungsabnahme offen.
- [~] **K06** [P0] Unterstützung fremder Allianzbasen — versionierte Zustimmung, Kapazität, Stationierung, Verteidigungsverluste und Rückruf implementiert; vollständige SQLite/PostgreSQL-Suite 577/1 sowie temporärer Browserpfad bis zur intakten Rückkehr bestanden. Kapazitäts-Race/Worker-Retry, Geräte-/Screenreader-/Lokalisierungs-/Hilfetextabnahme offen
- [~] **K07** [P1] Taktischer Rückzug und laufende Mission abbrechen — Ausgehende Überfälle/Angriffe/Aufklärung/Transporte/Versorgungen/Garnisonsmärsche und Expeditionen kehren zeitbasiert um; Armee/Fracht gebunden bis Rückkehr, idempotent und auditiert. Rückzugsschwellen/Mid-Battle-Abbruch offen; hängt vom noch zu definierenden FUR-3-Kampfvertrag (E07) ab.
- [~] **K08** [P1] Expeditionen und Ereignis-Missionen — versionierte FUR-3-Expedition mit deterministischen Ereignissen, Ressourcenverlust, Rückkehr und Schema-014-Vorlagen; Browser/Mobil/Lastabnahme offen
- [!] **K09** [P2] Trümmerfelder, Bergung und Reparatur — FUR-2 definiert keine Trümmer-/Bergungsökonomie; FUR-3 benötigt Regeln für Ertrag, Verfall, Konkurrenz, Besitz und Reparatur
- [!] **K10** [P2] Fernkampfangriffe / Artillerie / Raketen — Waffen, Munition, Reichweite, Gegenmaßnahmen und Effekte brauchen einen versionierten FUR-3-Kampfvertrag
- [!] **K11** [P1] Unterschiedliche Truppen-Geschwindigkeit und Reichweite — FUR-2 catalog has no unit speed/range values; requires owner-approved versioned rules before implementation
- [~] **K12** [P1] Kampfbericht pro Runde und Einheit — strukturierter FUR-2-Einrundenbericht mit Beteiligten, Kampfkraft, Verlusten/Überlebenden je Truppentyp und Beute; Mehrfachrunden und UI-Abnahme offen
- [~] **K13** [P2] Schlachtvorlagen / Angriffsprofile — Bis zu zehn accountgebundene Truppen-/Eroberungsprofile mit serverseitiger Validierung; Laden begrenzt auf verfügbaren Bestand. Batch-Dispatch, Ziel-/Ankunftsplanung sowie Browser-/Geräte-/Accessibility-Abnahme offen; echter Formular-Load ist frontendgetestet.
- [~] **K14** [P1] Weitere Verteidigungsobjekte — Vorläufiger digest-gepinnter FUR-3-Vertrag mit Bau/Reparatur-UI; COMBAT-4-PvP und ACS lösen Türme/Schild/Bunker rundenweise auf, Minen wirken einmalig seeded, Restintegrität/Replay werden atomar gespeichert und in Player-/ACS-Reports lesbar gerendert; COMBAT-4-Gefechtsproben nutzen zusätzlich frische, gepinnte Verteidigungs-Intel. Balance, Browser-/Accessibility-/Mobil-/Lokalisierungsabnahme offen; FUR-2 unverändert.

## Original-55: Wirtschaft & Technik

- [~] **E01** [P0] Abhängiger Forschungs- und Freischaltbaum — FUR-2-Labor-/Kasernen-Freischaltungen sind datengetrieben, validiert und im UI angezeigt; neue FUR-3-Einheiten/Gebäude benötigen freigegebenen Regelkatalog.
- [!] **E02** [P1] Erweiterbare Gebäudekategorien / Spezialausbauten — Masterplan nennt Zweck, aber keine freigegebenen Basispreise/Freischaltungen/Slots/Energieeffekte. FUR-2-Bestand bleibt bei acht Gebäuden; keine neuen Werte erfinden.
- [ ] **E03** [P2] Energie-, Betriebs- oder Unterhaltsmechanik — Optionaler vierter Wirtschaftskreislauf statt trivialer Produktion
- [~] **E04** [P1] Bau-/Forschungswarteschlangen umordnen & stornieren — Bis zu fünf Aufträge je Queue; Kosten-Regelsnapshot schützt Reservierungen beim Replanning. Vollständige Browser-/Barrierefreiheits- und Lebenszyklusabnahme offen.
- [ ] **E05** [P1] Ausbau jenseits von Stufe 10 / Prestige — Späte Spielphase mit Kostenkurve und Meisterungsstufen
- [x] **E06** [P2] Marktpreis-Statistiken und Handelsverlauf — Anonyme, weltbezogene Stundenaggregate mit gewichteter Rate, 30-Tage-Fenster und 60-Zeilen-Limit; SQLite/PostgreSQL- und Desktop-/Mobil-/Barrierefreiheitsabnahme bestanden.
- [~] **E07** [P0] Datengetriebene Konfig für Gebäude, Einheiten, Formeln — FUR-2-Katalog validiert/versioniert; Voraussetzungen und Expeditionshashes werden geprüft. Einige Formeln bleiben hartcodiert; FUR-3/Orbit-Katalog fehlt.
- [!] **E08** [P1] Fraktionsspezifische Einheiten/Technologien — FUR-2 hat nur die dokumentierten passiven Fraktionsboni; Masterkonzept fordert drei Technologien und zwei Einheiten je Fraktion, aber ohne IDs, Werte, Kosten oder Freischaltungen. Kein Balancing erfunden.

## Original-55: Allianz & Spieler

- [ ] **A01** [P1] Allianzkrieg mit Zielen, Wertung und Frieden — Krieg nicht bloß als Diplomatiestatus: Ziele, Zeit, Ergebnis
- [ ] **A02** [P1] Allianz-Rangliste und gemeinsame Siege — Allianzstatistik, Saisonplatzierung, Kriegsfortschritt
- [ ] **A03** [P2] Allianzkasse / Gemeinschaftsprojekte — Allianzdepot, gemeinsame Festungen, Beiträge
- [ ] **A04** [P2] Flexible Allianz-Rollen und Einzelberechtigungen — Rollen jenseits Leitung/Offizier/Mitglied
- [~] **A05** [P2] Freundesliste und Blockliste — Kontakte, Anfragen, private Kommunikation
- [ ] **A06** [P2] Interne Foren / Pinnwand — Längerfristige Strategiedokumente der Allianz
- [~] **A07** [P2] Spielerprofile, Badges, Leistungsdaten — Opt-in-Profilkarte mit kosmetischen Titeln/Abzeichen und Welt-Rang/Punktzahl, private Voreinstellung; Historienfeed und meilensteinverdiente Abzeichen bleiben offen.
- [~] **A08** [P2] Notizen, Berichtsfreigaben, Zielmarkierungen — Private Karten-/Berichtsnotizen umgesetzt; gemeinsame Einsatzplanung und Berichtsfreigabe offen.

## Original-55: Progression & Livebetrieb

- [ ] **P01** [P1] Fortlaufende Quest-/Erfolgsysteme — Fünf Direktiven zu einer Progressionskette ausbauen
- [ ] **P02** [P0] Langfristiges Endgame nach Zitadellen-Sieg — Neue Boss-Stufen, wechselnde Kampagnen, globale Ziele
- [ ] **P03** [P1] Saisonmechaniken / faire Neustartwelten — Optional Saisonwelt mit Reset und separatem Dauerwelt-Spielstand
- [ ] **P04** [P0] Spieler-Balance und Comeback-Schutz — Schutz nach Niederlage, Noobschutz, Abschwächung des Snowballs
- [ ] **P05** [P1] Ereignisse mit Missions- und Kampfvarianten — Nicht nur Produktion, sondern spezifische PvE-Events
- [ ] **P06** [P2] Vernünftige Automatisierung für Rückkehrer — Benachrichtigungen, Aufgabenstatus, Kommandoübersichten

## Original-55: Technik & Betrieb

- [ ] **T01** [P0] Automatische Backups + Restore-Probe — Backups, Wiederherstellungstest, Rotation und Zugriffsschutz
- [~] **T02** [P0] Race-Condition-/Lasttests und Missions-Idempotenztests — Replay, parallele Buchung, Worker-Crash und acht gleichzeitige Worker sind auf SQLite/PostgreSQL getestet; Dauerlastprofil offen.
- [ ] **T03** [P0] Anti-Bot/Anti-Multiaccount/Rate Limits — Abuse-Detektion ohne personenbezogene Überwachungsexzesse
- [ ] **T04** [P1] Umfassende Welt- und Balancing-Adminwerkzeuge — Weltregeln, Missions-Suche, Korrekturwerkzeuge und Telemetrie
- [ ] **T05** [P2] Mehrsprachigkeit / Lokalisierung — String-Katalog für DE/EN, anschließend weitere Sprachen
- [ ] **T06** [P1] Responsive Mobile-/Accessibility-Prüfung — Bedienung und Tastaturzugänglichkeit für Karte und Kampf
- [ ] **T07** [P2] Echtzeit-Updates statt ausschließlich Polling — Websocket/SSE für Missionen und Allianzkoordination
- [ ] **T08** [P1] Spielregel-Migrationen und Balancing-Simulation — Regelversions-Snapshots gegen echte Formellogik validieren
- [ ] **T09** [P1] Sicherer Test-/Produktions-Release-Prozess — CI/CD mit Tests, Rollback, Spiel-DB-Migration, Monitoring

## Identität und Konto

- [~] **ACC-001** [P0] Passwortänderung — Altes Passwort und TOTP prüfen, alle Sitzungen widerrufen; Browser-/Accessibility-Abnahme offen.
- [~] **ACC-002** [P0] Recovery-Codes — Zehn Einmalcodes werden gehasht gespeichert, beim Login einmalig verbraucht und nur nach Passwort plus aktuellem TOTP-Code regeneriert; Browser-/Accessibility-Abnahme offen.
- [~] **ACC-003** [P0] Sitzungsverwaltung — Geräte/Sessions anzeigen und einzeln, selektiv oder vollständig widerrufen; Browser-/Accessibility-Abnahme offen.
- [~] **ACC-004** [P0] Accountname ändern — 24h-Cooldown, case-insensitive Uniqueness, Passwort/TOTP-Reauth, Account-Projektion und unveränderte historische Einträge. Browser-/Accessibility-Abnahme offen.
- [!] **ACC-005** [P0] Avatare und Profildetails — Kein Upload-/Asset-/Moderationspfad im Produkt. Erlaubte Formate, Größen-/Dimensionsgrenzen, Retention und Moderationsprozess sind nicht spezifiziert; keine Regeln erfinden.
- [~] **ACC-006** [P0] Privacy Export — Reauthentifizierter, CSRF-geschützter JSON-Export freigegebener eigener Kontodaten; Browser-/Accessibility- und Rechtsprüfung offen.
- [!] **ACC-007** [P0] Privacy Delete — Lösch-/Anonymisierungsworkflow fehlt; Aufbewahrung und Behandlung geteilter Inhalte benötigen eine explizite Rechts-/Produktregel vor Umsetzung.
- [!] **ACC-008** [P0] Benachrichtigungseinstellungen — Nur Verifizierungs-/Recovery-E-Mails vorhanden; Kategorien, Kanäle, Einwilligung und Zustellsemantik sind nicht spezifiziert.
- [~] **ACC-009** [P0] Login-Schutz — Globales IP-Limit plus fünf Loginversuche pro Konto/Netz und Minute; Login-/Resetfehler enumerieren keine Konten. Verteilte Abuse-Erkennung und Betriebsabnahme offen.
- [ ] **ACC-010** [P0] WebAuthn optional — Passkey Enrollment und Recovery werden hinter sicherem Featureflag verfügbar und getestbar.

## Game-Engine und Infrastruktur

- [ ] **ENG-001** [P0] Globale Accounts und WorldPlayer — Ein Account kann mehreren Welten angehören; Progress ist pro Welt getrennt.
- [ ] **ENG-002** [P0] Dauer- Saison- Sandboxwelten — Weltmodus erlaubt explizite Regeln; Data Leakage und saisonaler Reset sind unmöglich.
- [~] **ENG-003** [P0] Regelversionierter Katalog — FUR-2 Saison-Hash und FUR-3-Expeditionsversion+SHA-256 werden eingefroren und geprüft; Orbit-Katalog und mehrere archivierte aktive Regelversionen fehlen.
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

- [~] **TERRA-001** [P0] Kartengenerator — Konfigurierter Seed reproduziert 4096 Geländefelder und Außenposten; getesteter Beitritt erreicht einen neutralen Ressourcenposten per Weg innerhalb 3600s. Breite Seedmatrix und Startparität offen.
- [~] **TERRA-002** [P0] Sektorbesitztransaktionen — Barrier-synchronisierter Zweispieler-Race erzeugt genau eine Kolonie und belastet nur den Gewinner; SQLite/PostgreSQL 18 bestanden. UI-/Load-Abnahme offen.
- [~] **TERRA-003** [P0] Ausgeglichene Startpositionen — Startbestand und Stufe-1-Produktion liefern Holz/Stein/Erz ohne Außenposten während des einstündigen Schutzes; Terrain-/Neutralziel-Parität und Clientabnahme offen.
- [~] **TERRA-004** [P0] Fog-Koordinatenliste — Per Spieler/Welt gespeichert; neue Adapterregression belegt, dass Beobachtungen beim Weltwechsel privat bleiben und beim Zurückwechseln stale sichtbar sind. UI-/Accessibility-/Allianzfreigabe offen.
- [~] **TERRA-005** [P0] Regionen-Score — 32-Prozentpunkte-Gesamtdeckel und unveränderter persönlicher Ranglistenscore sind jetzt auf SQLite/PostgreSQL 18 geprüft; Browser-/Mobile-/Accessibility-Abnahme offen.
- [~] **TERRA-006** [P0] Geländemodifikatoren — Terrain beeinflusst zulässige Wege, Reisezeit und Defense aus Regelkatalog.
- [~] **TERRA-007** [P0] Kolonie umbenennen — Neue Namen mit validierter Länge und Sperre gegen fremden Zugriff.
- [ ] **TERRA-008** [P0] Hauptkolonie wechseln — Player kann die Hauptkolonie nach Cooldown ändern ohne Einheitentransfer. (Cooldown-Dauer/-Scope vom Owner festzulegen.)
- [~] **TERRA-009** [P0] Kolonie aufgeben — Letzte Heimatkolonie nicht aufgebbar; Missionen/Items/Waren werden vorher geregelt.
- [ ] **TERRA-010** [P0] Kolonie versetzen — Targetreserving/Cooldown/Kosten und sichere Abwicklung aller offenen Missionen.
- [~] **TERRA-011** [P0] Außenposten zu Kolonie ausbauen — Implementierter, noch nicht owner-abgenommener FUR-3-Vorschlag; serverseitige Besitz-/Slot-/Kostenprüfung und transaktionaler Transfer. Regeln/Balance und Browser-/Mobil-/Accessibility-Abnahme offen.
- [~] **TERRA-012** [P0] Kartenfavoriten — Private Marker/Filter, bis 20 Ziele je Welt, Routen- und Koordinatensuche.
- [~] **TERRA-013** [P0] Territorialkontrolle — Allianzgebiete werden aus Mitgliederbesitz und bestehender Zweiposten-/Mehrheitsschwelle aggregiert; individuelle Kontrolle/Produktion unverändert. Browser/PostgreSQL/Accessibility-Abnahme offen.
- [~] **TERRA-014** [P0] Schutzgebiete und Spawnregeln — Genesis-Spawn/Weltbeitritt/Expansion mit 6-Sektoren-Schutzabstand; nur bekannte, freie und erreichbare Felder; atomare Unique-Belegung. Browser-/Mobile-/Accessibility-Abnahme offen.
- [~] **TERRA-015** [P0] Verlassene Kolonien und Ruinen — Owner-approved 30-day inactivity warning, seven-day notice, safe dormancy/retention and owner reactivation; PostgreSQL/browser/mobile/accessibility and localization acceptance remain.

## Ökonomie und Forschung erweitert

- [ ] **ECO-001** [P1] Energieversorgung — Unverified: Root-App und FUR-2-Katalog enthalten weder Energiekoeffizienten noch Unterdeckungsregel; Owner-Balanceentscheidung nötig.
- [!] - [ ] **ECO-002** [P1] Unterhaltskosten — Unterhaltskosten — FUR-2 enthält keine periodischen Kosten; FUR-3-Sätze, Taktung und Erschöpfungsschutz sind nicht festgelegt.
- [ ] **ECO-003** [P1] Bauqueue umordnen — Erlaubte Reorder-Kontrolle respektiert Slots, Ressourcen und bereits gestartete Aufträge.
- [ ] **ECO-004** [P1] Bauqueue abbrechen — Stornierungsregel definiert Credit, bereits verbrauchte Zeit und Upgrade-Invariante.
- [ ] **ECO-005** [P1] Forschung global vs lokal — Forschungs- und Kolonieeffekte sind sauber getrennt, kein doppelt gerechneter Bonus. *(Teilweise belegt; siehe TRACEABILITY.md.)*
- [ ] **ECO-006** [P1] Technologieabhängigkeiten — Server prüft Bau/Forschung/Einheit-Freischaltungen auch bei parallelen Aufträgen. *(FUR-2-Grundgates teilweise belegt; erweiterter Techgraph offen.)*
- [!] - [ ] **ECO-007** [P1] Spezialgebäude — Spezialgebäude — FUR-2 hat acht Gebäudeklassen; neue Spezialgebäude benötigen Preise, Freischaltungen und Effekte.
- [!] - [ ] **ECO-008** [P1] Prestigeausbau — Prestigeausbau — Level 10 ist FUR-2-Maximum; Prestige-Slots/-Kosten und Regelmigration sind undefiniert.
- [~] **ECO-009** [P1] Ressourcenproduktionsgrafik — Aktuelle Rate, Boni, Gelände, Depotstand, Vollzeit und Pausenstatus als zugängliche Grafik; Browser-/Mobile-/Screenreader-Abnahme offen.
- [x] **ECO-010** [P1] Markt-Preisverlauf — Abgeschlossene Trades werden anonym und weltbezogen aggregiert; Gewichtung, Zeitraum, Limit, Privatsphäre und Desktop-/Mobilansicht sind abgenommen.
- [~] **ECO-011** [P1] Allianzversorgungsrouten — Weg/Kapazität, Ankunftsprüfung, Abbruch/Rückgabe und parallele idempotente Wiederholung sind getestet; Browser-Lebenszyklus, Mobil-/Barrierefreiheit und Abuse-Abnahme offen.
- [~] **ECO-012** [P1] Dauerhafte Handelsrouten — Periodische Terra-Routen: max. 3 je Ausgangskolonie, einzigartige Ziele, 1–168 h, Fracht-/Trägerescrow beim Start, Pausieren bei Mangel, Fortsetzen/Beenden und nicht überlappende Zustellung; UI-/Browser-/Mobil-/Barrierefreiheit und Abuse-Abnahme offen.
- [~] **ECO-013** [P1] Produktionsvorlagen — Accountgebundene Bau-/Forschungs-/Rekrutierungspresets mit normaler Serverautorisierung, CSRF, Idempotenz und Limits; Browser-/Mobile-/Screenreaderabnahme offen.
- [~] **ECO-014** [P1] Ressourcen-Faucets/Sinks — CSRF-geschützte Simulation bis 20 Bau-/Forschungs-/Trainings-/Handels-/Questaktionen nutzt Live-Regeln und versionierte Digests; schreibt per Savepoint-Rollback auch bei Erfolg oder Fehler nichts dauerhaft. Vollständige Flussinventur, Balancebericht, UI- und Geräteabnahme offen.
- [~] **ECO-015** [P1] Forschungsspezialisierung — Drei colony-gebundene FUR-2-Effekte (Taktik, Logistik, Produktion) mit Kosten/Voraussetzungen und fokussierten Tests; verzweigte Pfade, vergleichende Balanceprüfung und freigegebener FUR-3-Katalog offen.
- [!] **ECO-016** [P1] Fraktions-Spezialaktionen — Code enthält neun Spezialforschungen, sechs gesperrte Einheiten sowie Pioniervermessung, Wächterbefestigung und Syndikatkonvoi; Werte sind vorläufig, der freigegebene Balance-/Kampagnenkatalog fehlt, daher unverified.

## Kampf, Missionen und Schutz

- [~] **WAR-001** [P0] FUR-3 Gefecht mit 6 Runden — versionierte Treffer-, Schaden-, Rüstungs-, Schild-, Initiative- und Rückzugsregeln sind implementiert und in deterministischem Replay getestet; Werte sind noch nicht balanceabgenommen und keine vollständige Geräte-/Accessibility-Abnahme.
- [~] **WAR-002** [P0] Unit Counter Matrix — neun Profile live in FUR-3-PvE/PvP und ACS-3; COMBAT-3 versioniert zwölf weitere Master-Rollen samt Produktions-/Bewegungsmetadaten. Deren Besitz-, Missions-, Transport-, Reparatur- und Rückkehr-Lifecycle bleibt gesperrt; Werte sind Entwurf und unbalanciert.
- [~] **WAR-003** [P0] Verteidigungsobjekte — Vorläufiger versionierter Vertrag, serverseitiger Bau/Reparatur-Lifecycle und Gebäude-UI; Türme/Schild/Bunker sowie seeded Minen integrieren in normale und ACS-COMBAT-4-Replays mit atomarer Integrität; Teilnehmerreports enthalten Mine und Restintegrität lesbar; COMBAT-4-Dry-run nimmt dieselben gepinnten Strukturen in alle Szenarien auf. Balance-, Browser-/Accessibility-/Mobil-/Lokalisierungs- und breite Adapterabnahme offen; FUR-2 unverändert.
- [~] **WAR-004** [P0] Gefechts-RNG — FUR-3-PvE/PvP und ACS-3 pinnen serverseitig 256-Bit-Seed, Digest und Commitment, prüfen sie beim Resolve, speichern Replay/Seed-Reveal einmal atomar und verhindern doppelte Reports/Rückkehr. 1.000-Seed-Regressionsfall in SQLite-Vollsuite bestanden; FUR-2 bleibt getrennt. PostgreSQL und manuelle Browser-/Geräte-/Accessibility-Abnahme offen.
- [~] **WAR-005** [P0] Kampf Dry-run — Gleicher Resolver in lesender FUR-2-Projektion bzw. 16 FUR-3-Szenarien; PvP nutzt nur frische Stufe-2-Intel, COMBAT-4 inkludiert gepinnte Abwehrstrukturen/Minenquote, unbekannte Beute bleibt verborgen. Gezielte API-/Domainregression 9 bestanden, 6 PostgreSQL-Adaptervarianten übersprungen; Browser-/Geräte-/Balanceabnahme offen.
- [!] **WAR-006** [P0] Zeitgestaffelte Bewegungen — Terrainpfad und UTC vorhanden, aber keine Unit-Speed-/Fuel-Werte oder Transitphasen im FUR-2-Katalog.
- [~] **WAR-007** [P0] Mission Recall — idempotenter, paralleler Rückruf für sieben ausgehende Missionstypen erzeugt eine Rückkehr; Einheiten/Fracht bleiben gebunden. Rückruf nach Ankunft und UI-/Geräteabnahme offen.
- [!] **WAR-008** [P0] Taktischer Rückzug — FUR-2 hat nur eine atomare Kampfrunde; Retreat-Schwellen, Abbruchzustand und Rückflugregeln fehlen im FUR-3-Vertrag.
- [~] **WAR-009** [P0] Spionage-Mission — Level 1/2 Ranger-Intel; Regression bestätigt Beobachter-/Welt-Scope, kein Ressourcen-Payload und keine Berichte für Ziel oder unbeteiligte Dritte; browser/device-Abnahme offen.
- [~] **WAR-010** [P0] Gegenaufklärung — FUR-3-TERRA-INTELLIGENCE-1 implementiert Abfang/Entdeckung mit privaten Seed-Daten, generischem Alert, ohne Gegenkampf; FUR-2 bleibt unverändert. SQLite-/PostgreSQL-18- und Gesamtsuite bestanden; private Staging-Migration 77 läuft. Balance- und Browserabnahme offen.
- [!] **WAR-011** [P0] Reparatur und Wrackbergung — K09-Audit: FUR-2 kennt weder Wrackfelder/Bergungsökonomie noch Reparaturkosten oder Lebenszyklus.
- [~] **WAR-012** [P0] Artillerie und Fernwaffen — COMBAT-3/4 hat ein versioniertes, untrainierbares Artillerieprofil mit Reichweite und Kontern; Munitions-/Angriffs-/Schutz-/Eventlebenszyklus und Regelabnahme fehlen. Regression 13 passed, 12 PostgreSQL skipped.
- [~] **WAR-013** [P0] Koordinierte Attacke — Quellabgleich bestätigt persistierte welt-/allianzgebundene Operationen, bis zu 12 Wings, escrow/refund, synchronisierte Ankunft, FUR-3-ACS-3 Replay, anteilige Verluste/Beute und Rückkehr je Ausgangskolonie; SQLite-Regressionssuite besteht. PostgreSQL, Browser-/Device-/Accessibility-/Lokalisierungs- und breite Multiplayerabnahme offen.
- [~] **WAR-014** [P0] Verteidiger-Verband — versionierte Allianz-Garnison mit ausdrücklicher Heimatbasis-Zustimmung, reserviertem Besitzerbestand, weltgebundener Ankunft, Rückruf, Kapazitäts- und Mitgliedschaftsprüfung sowie COMBAT-3/4-Verlustzurechnung je Entsender vorhanden. Balance-, Live-Browser-/Mobil-/Screenreader-, Lokalisierungs- und Lastabnahme offen.
- [~] **WAR-015** [P0] Taktische Belagerung — COMBAT-3/4 enthält `siege_robot`, aber das Roster ist gesperrt. Zeitbelagerung, Ablauf, Reparatur und Kapitulationsregeln fehlen; Owner-Regelabnahme nötig.
- [~] **WAR-016** [P0] Kriegseinfluss auf Angriff — PvP/Neulingsschutz/Urlaub/Allianz/NAP werden bei Start und Ankunft geprüft; SQLite/PostgreSQL-18-Abbruch bei Schutz-/NAP-Änderung mit einmaliger Rückkehr belegt. Formale Kriegserklärung und UI-Abnahme offen.
- [!] **WAR-017** [P0] Raid-Limit — keine zielbezogenen Angriffs-/Verlust-Caps oder Diminishing Returns; Caps, Zeitfenster, Ausnahmen und Reset brauchen einen FUR-3-Regelvertrag.
- [~] **WAR-018** [P0] Welt- und Allianz-Rankings — FUR-2-Wertung bleibt unverändert. FUR-3-Entwurf v1 vergibt pro verlorener Einheit Angriffs-/Verteidigungspunkte, ACS je Teilnehmerwing; bestätigte Garnisonen geben höchstens einmal je 24 Stunden Supportpunkte. Allianzsumme je Welt folgt aktuellen Mitgliedern. Eindeutiger unveränderlicher Transaktionsledger und private 50-Zeilenprüfung; Eigentümer-/Balance-, PostgreSQL- und manuelle UI-Abnahme offen.
- [~] **WAR-019** [P0] Bericht Replay und Freigabe — vollständige strukturierte FUR-2-Rundendaten nur für die zwei Beteiligten; Replay-Commitment und anonymisierte öffentliche Freigabe fehlen.
- [~] **WAR-020** [P0] Kampf-Balance-Test — 14.400 deterministische FUR-2-Fälle plus Win-/Loss-Gegenbeleg für alle neun trainierbaren Unit-Typen; Rollen-/FUR-3-Balance bleibt offen.

## Allianz und soziale Plattform

- [~] **SOC-001** [P1] Allianzaufnahmeverfahren — Einladen, Bewerben, Annehmen, Ablehnen und Zurückziehen sind rollen- und kontogebunden; Ablauf, Geräteabnahme und einheitliche Statushistorie offen.
- [~] **SOC-002** [P1] Granulare Allianzrechte — Schema 83–88 erlauben der Leitung, neun serverseitig erzwungene Rechte für Offiziere und Mitglieder getrennt zu vergeben. PostgreSQL-, Browser-, Geräte- und Barrierefreiheitsabnahme offen.
- [~] **SOC-003** [P1] Führungsübertrag — Schema 84 hält die aktuelle Führung bis zur Zustimmung des vorgeschlagenen Nachfolgers; Ablehnung, Rücknahme und atomare Rollenänderung sind implementiert. PostgreSQL-, Browser-, Geräte- und Barrierefreiheitsabnahme offen.
- [~] **SOC-004** [P1] Allianzkrieg-Objektive — Schema 85 ergänzt FUR-3-Kriegsstart, versionierte Zielwertung, append-only Kampfbelege, idempotente Wertung, Friedensvorschlag mit Gegenzustimmung und öffentliches Kriegsprotokoll. FUR-2 bleibt unverändert. Die Punkt-/Zielwerte sind ein Balanceentwurf; Eigentümer-, PostgreSQL-, UI-/Geräte- und Betriebsabnahme offen.
- [~] **SOC-005** [P1] Allianz-Rangliste — Live-Aggregation bleibt nach aktueller Mitgliedschaft; Schema 86 friert FUR-3-Saisonpunkte nach Allianz zum Wertungszeitpunkt ein und zeigt das unveränderliche Saisonarchiv. `FUR-3-ALLIANCE-RANKING-1` ist ein vorläufiger Entwurf für bestätigte Konten mit E-Mail. FUR-2 bleibt unverändert. Getrennte E-Mail-Adressen werden nicht als Mehrkonten erkannt; Balance-/Owner-, PostgreSQL- und UI-/Accessibility-Abnahme offen.
- [~] **SOC-006** [P1] Allianzkasse — Schema 87, weltgebundene Kasse, unveränderliches Ledger, Spenden/Auszahlungen, 1-%-Gebühr, Zwei-Freigaben-Schwelle ab 5.000 und Sieben-Tage-Rückbuchung implementiert. FUR-3-Regelsatz ist vorläufig; Balance-, Browser-/Accessibility- und Produktionsabnahme offen.
- [~] **SOC-007** [P1] Allianzprojekte — Schema 88 und versionierter FUR-3-Projektkatalog, Einzahlungen bis zum Ziel, Fristen, Rechte, Abschlussrekord sowie vollständige Rückbuchung bei Abbruch/Ablauf implementiert. Werte bleiben vorläufig; Balance-, Browser-/Accessibility- und Produktionsabnahme offen.
- [~] **SOC-008** [P1] Allianzforum — Threads, Rechte, Archiv und Edit-/Report-Funktionen, XSS-Schutz. Thread/Antworten, Autorenbearbeitung, Moderatorarchiv, Meldungsqueue und Escaping sind serverseitig implementiert; SQLite- und PostgreSQL-18-Regressionen bestehen. Browser-, Mobil- und Screenreader-Abnahme offen; Migration 023 nicht auf persistente Stacks angewandt.
- [~] **SOC-009** [P1] Pinnwand — Rollenprüfungen, Archiv und 100er-Keyset-Paginierung; nur aktuelle Mitglieder.
- [~] **SOC-010** [P1] Freundeslisten — private, keyset-paginierte Kontakte; request/accept/decline/cancel/remove, Blockschutz und Gegenanfragen-Race abgedeckt. Vollständiger Ablauf samt Akteursprüfung SQLite + PostgreSQL 18 bestanden; Browser-/Mobil-/Accessibility-/Lokalisierungsabnahme offen.
- [~] **SOC-011** [P1] Blocklisten — Owner-only Blockliste; Sperre beendet Freundschaft und verhindert Nachrichten/Gegenanfragen, Moderation bleibt unabhängig. SQLite + PostgreSQL 18 geprüft; manuelle Geräte-/Accessibility-/Lokalisierungsabnahme offen.
- [~] **SOC-012** [P1] Spielerprofil — Schema 89, private Voreinstellung, weltgebundene Opt-in-Profilkarte, allowlistete Rang-/Punktestände und kosmetische Titel/Abzeichen; volle Suite und privates Staging erfolgreich. Manuelle Mehrkonto-/Mobil-/Screenreader-/Locale-Abnahme offen. Bestehende Rangliste zeigt Name/Punktzahl unabhängig davon.
- [~] **SOC-013** [P1] Notizen — Private weltgebundene Notizen zu Koordinaten/eigenen Berichten, je Ziel 500 Zeichen; interaktive Browser-/Barrierefreiheitsabnahme offen.
- [~] **SOC-014** [P1] Berichtsfreigabe — Schema 90, explizite Allianzfreigabe pro Kampfbericht, streng redigierte Runden-/Eigenverluste-/Überlebenden-Summen, Eigentümerwiderruf und sofortige Welt-/Mitgliedschaftsgrenzen. Full Python nach Schema 92: 491 passed/259 optionale PostgreSQL-Skips; fokussiertes PostgreSQL-/Restore-/Migrationsdrill bestanden. Privates Loopback-Staging auf Schema 92 gesund; Browser-/Mobil-/Screenreader-/Locale-Abnahme offen.
- [~] **SOC-015** [P1] Chatmoderation — Schema 91 ergänzt reporter-private Meldungen sichtbarer Welt-/Allianz-/Privatnachrichten, Einsprüche gegen aktive temporäre Mutes sowie eine begrenzte, auditierte Moderatorwarteschlange mit fallbezogenen Entscheidungen. Vollsuite nach Schema 92: 491 passed/259 optionale PostgreSQL-Skips; fokussierte SQLite-/PostgreSQL-18-Prüfung bestanden. Privates Staging auf Schema 92 gesund; manuelle Browser-/Accessibility-/Locale-Abnahme offen; Einsprüche gegen Kontosperren sind nicht enthalten.
- [~] **SOC-016** [P1] Ankündigung und Briefkasten — Schema 92 trennt globale und aktive-Welt-Ankündigungen vom privaten Systempostfach. Moderatoren kündigen nur in der aktiven Welt an; globale Beiträge und Einzelpost sind Admin-only. Empfänger sehen nur eigene Post und können idempotent als gelesen markieren; Audits enthalten keinen Nachrichtentext. SQLite + PostgreSQL 18 fokussiert 21 bestanden; Vollsuite 491/259 und privates Schema-92-Staging gesund. Manuelle UI-/Accessibility-/Locale-Abnahme offen.

## NPC, Quests, Endgame

- [~] **PVE-001** [P1] NPC-Fraktionen — Mindestens fünf eigene NPC-Lager mit unterschiedlichen Profilen und erlaubten Aktionen.
- [~] **PVE-002** [P1] NPC-Lagerzustand — NPC-Basen besitzen Ressourcen, Einheiten, Bewegungen und Bereitstellungskontingent.
- [ ] **PVE-003** [P1] NPC Angriffskette — Strategie-KI erzeugt geplante Missionen innerhalb CPU-/Event-Budget, fair und auditierbar.
- [~] **PVE-004** [P1] NPC Außenposten Regeneration — Neutralvorräte regenerieren begrenzt und weltgebunden; defensive Regeneration fehlt.
- [~] **PVE-005** [P1] Ruinenerkundung — Opt-in für Ranger-Missionen mit privater Sektor- und Ruinenbeobachtung; Balance und vollständige Abnahme offen.
- [~] **PVE-006** [P1] Expeditionskatalog — Regelgebundene Grenzlandexpedition mit deterministischer Auflösung und Rückmarsch; der Dialog liest den Serverkatalog. Katalogausbau und vollständige Abnahme offen.
- [~] **PVE-007** [P1] Boss-Raid — Optionaler Terra-Boss mit zwei Phasen, begrenzten Angriffsplätzen und einmaliger nach Schaden anteiliger Auszahlung; vollständige Abnahme offen.
- [ ] **PVE-008** [P1] Weltinvasion — Spawnwelle hat Budget, Warnphase, Angriff, Verlauf und Ende.
- [~] **PVE-009** [P1] Konvoi-Ereignis — Zeitgestaffelte NPC-Handelsroute wird verteidigt/überfallen mit klarer Belohnung.
- [~] **PVE-010** [P1] Questlinien — Fünf einfache feste Aufträge mit Claim existieren; Questlinien, Fortschrittshistorie und Story-/Handels-/Allianz-/Orbit-Tracks offen.
- [~] **PVE-011** [P1] Tagesquests — Täglich resetbare Quests haben UTC-Grenze und Claim-Einmaligkeit.
- [~] **PVE-012** [P1] Wochenquests — Wöchentliche Ziele werden sicher bei Wochenwechsel versioniert.
- [ ] **PVE-013** [P1] Erfolge — Persistente Achievements mit einmaliger Vergabe und öffentlicher/privater Anzeige.
- [~] **PVE-014** [P1] Questreward-Reserve — Questclaims legen Überlauf ins Reserve-Lager; alle Rewardquellen und UI-Abnahme offen.
- [ ] **PVE-015** [P1] Zitadellen-Endgame — Nach Historischem Kern-Sieg weitere regionale/Orbit- und Allianzkampagnen.
- [~] **PVE-016** [P1] Comeback-Hilfe — Abwesende Spieler erhalten kein unfairen PvP-Startnachteil und transparente Schutzfenster.
- [~] **PVE-017** [P1] NPC Simulation — Weltbot hat deterministische Seeds, kann nicht moderieren und verteilt keine willkürlichen Lootbeträge.
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

- [~] **ITEM-001** [P1] Inventar — Teilumfang: acht versionierte FUR-3-Gegenstands-IDs, sechs Stapelarten je Kolonie, Cap 1.000/Stapel, same-world Kolonieversorgung mit reserviertem Eingang, Rückruf und claimbarer Reserve; Export/Abandonment geschützt. Generische Gegenstandsklassen haben noch keine Rezept-/Drop-Erwerbsquelle und keinen Effekt. Gezielte Tests: 38 passed, zwei optionale PostgreSQL-Fälle skipped; Frontend 86/86. Full Python/PostgreSQL/Browser noch offen.
- [~] **ITEM-002** [P1] Crafting — `FUR-CRAFTING-1` enthält zwei als Entwurf markierte, weltweise Opt-in-Rezepte. Eingaben werden transaktional verbraucht und Ausgaben reserviert; Worker-Abschluss ist einmalig, vorzeitiger Abbruch erstattet einschließlich Reservelager; Audit und UI sind angebunden. FUR-2 bleibt aus. ITEM-002/003 und API-Regressions: 50 bestanden; Gesamtsuite 533 bestanden/261 optionale PostgreSQL-Skips; Frontend 88/88. Traceability 344/344, Ruff, Black, strict mypy, ESLint und JavaScript-Syntax bestanden. Eigentümer-Balance, breitere PostgreSQL-, Browser-, Geräte-, Accessibility- und Übersetzungsabnahme bleiben offen.
- [~] **ITEM-003** [P1] Item-Recycling — `FUR-ITEM-RECYCLING-1` lässt in optierten FUR-3-Welten Feldreparaturkits in zwei Komponenten und drei Textilien zerlegen. Herstellungsinputs sind jeweils höher als Recyclingausgaben; der Katalog weist positive Herstellung-/Recycling-Schleifen beim Laden zurück. Transaktion, Befehlsschlüssel-Idempotenz, API-Vertrag, Audit, Gegenstands- und Waren-Reservelagerüberlauf und Handel-UI sind angebunden. 50 Paket-/API-Regressionen bestanden; 533 bestanden/261 optionale PostgreSQL-Skips im Gesamtlauf; separate PostgreSQL-18-Versorgung/Rückrufgruppe 16/16. Werte sind vorläufig; nur ein Gegenstand ist recycelbar. Balance-, Browser-, Geräte-, Accessibility- und Übersetzungsabnahme offen.
- [~] **ITEM-004** [P1] Lootbox-freies Itemdrop-System — `FUR-3-ITEM-DROPS-1` pinnt reproduzierbare, lootbox-freie Expeditionswürfe an Opt-in-Welten: 10 % bei Fund/Vorratsfund/Patrouille, 8 % je Expedition, höchstens ein Bergungsmaterial. Rohstoffe erhalten Trägerpriorität; FUR-2 und Altmissionen bleiben unverändert. SQLite-Expeditionsregressionen 7/7 bestanden; disposable PostgreSQL 18, Vollsuite und Qualitätsläufe folgen. Balance-, Browser-, Mobil-, Accessibility- und Übersetzungsabnahme offen.
- [~] **ITEM-005** [P1] Heldenverwaltung — Opt-in `FUR-3-HERO-1`: raid/attack 12 XP, Expedition 8, Aufklärung 4; Levelkurve 100 × Vorlevel bis Stufe 20; ein Punkt je Level, Attributcap 10. Wirtschaftsattribut gibt +2 Prozentpunkte Produktion je Punkt (max. +20 %). Auftragregel wird gepinnt; unveränderliches Exact-once-XP-Ledger; Welt- und Accountscope; SQLite/PostgreSQL Schema 94. Militär/Aufklärung/Kommando sind zusätzlich über HERO-2 freischaltbar. HERO-1-Fokustests SQLite/PostgreSQL 10/10; Vollsuite 540 bestanden/266 optionale PostgreSQL-Skips/0 Fehler; Frontend 89/89; Ruff, Black, strict mypy, ESLint, JS syntax und Traceability 344/344 bestanden. HERO-2-Effekte haben weiterhin vorläufige Balancewerte; manuelle Browser-/Accessibility-/Übersetzungsabnahme offen.
- [~] **ITEM-006** [P1] Helden-Doktrinen — separates opt-in `FUR-3-HERO-2` definiert Wirtschaft +2 Prozentpunkte Produktion/Punkt (Cap 20 %), Militär +2 % Terra-FUR-3-Kampfschaden/Punkt (Cap 20 %), Aufklärung +10 % PvP-Berichtsdauer/Punkt (Cap 100 %) und Flotte/Kommando +1 Terra-Auftragsplatz/Punkt (Cap 5). Angriff/Spähauftrag pinnt Version, Prüfsumme, Stats und Effekte. FUR-2-Kampfgleichungen bleiben gleich. Fokussierte SQLite-Regressionsgruppe 19 bestanden/6 optionale Adapter-Skips; Doctrine-Suite 14/14 über SQLite und disposable PostgreSQL 18. Vollsuite 542 bestanden/268 übersprungen/0 Fehler; Frontend 89/89 und statische Checks bestanden; Balance und manuelle Browser-/Geräte-/Accessibility-/Locale-Abnahme offen.
- [~] **ITEM-007** [P1] Talent-Reset — `FUR-3-HERO-3` weltweises Opt-in erfordert HERO-1; 250 Holz/Stein/Erz, sieben Tage Konto-/Weltcooldown; setzt nur Attribute zurück, XP-Ledger unverändert und Skillpunkte exakt aus XP neu berechnet. Schema 95 SQLite/PostgreSQL, idempotenter transaktionaler Befehl und Commander-/Admin-UI. Hero-/Reset suite 20/20 across SQLite and disposable PostgreSQL18; full suite 545/271/0; migrations 11 passed/7 skipped; frontend 89/89. Disposable desktop browser walkthrough passed. Owner balance and mobile/keyboard/screen-reader/localization acceptance remain open.
- [ ] **ITEM-008** [P1] Kosmetische Belohnungen — Skins, Titel, Banner ohne Kampfkraft oder Produktivitätsvorteil.
- [~] **ITEM-009** [P1] Baupläne — Owner-gebundene Missions- und Bau-/Forschungs-/Rekrutierungsvorlagen, serverseitig validiert; Produktionsvorlagen reihen über den normalen idempotenten Befehl ein. Drei fokussierte API-Regressionsfälle bestanden; Browser-/Accessibility-/Locale-Abnahme offen.
- [~] **ITEM-010** [P1] Ingame-Benachrichtigungen — Schema 93 ergänzt fünf Kategorien mit persönlichen Mutes und private Zustellfehler bis fünf Versuchen; Kategorien stehen im Weltprotokoll. SQLite-Fokus 14 bestanden/2 optionale PostgreSQL-Skips; Frontend 85/85 aktuell; Schema-92-PostgreSQL-Restore plus Delta-Drill bestanden. Vollsuite nach Migration 93: 496 bestanden/261 optionale Adapter-Skips/0 Fehler (1880,35 s); Filter und begrenzter Cursor-Verlauf ergänzt; aktuelle Command-Eventfamilien sind kategorisiert, unbekannte Typen fallen sicher auf System zurück. Manuelle UI-/Accessibility-/Locale-Abnahme offen.
- [ ] **ITEM-011** [P1] Browser Push optional — Opt-in Push, Abmeldung und datensparsame Vorschau fehlen noch.

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
- [~] **UX-017** [P1] Notification Center — Weltgebundener Ereignisfeed zeigt Kategorien, persönliche Mute-Steuerung und private Zustellfehler. Filter und älterer Cursor-Verlauf implementiert; aktuelle Command-Eventfamilien sind kategorisiert, unbekannte Typen fallen auf System zurück. Manuelle Accessibility-/Device-/Locale-Abnahme offen.
- [ ] **UX-018** [P1] PWA offline read-only — Optional Offline-Navigation von Hilfetexten; offline keine mutierenden Commands.

## Automatisierung, Tests und Deployment

- [ ] **OPS-001** [P0] One command dev — Sauberer Checkout startet lokale DB/Worker/API und seedbare Demowelt.
- [ ] **OPS-002** [P0] One command staging — Private Stagingumgebung startet mit produktionsnahen Services und Testdaten.
- [ ] **OPS-003** [P0] Docker production bundle — Container starten ohne dev reload; DB und Redis privat; Persistenz und Proxy.
- [x] **OPS-004** [P0] Migration-Upgrade — SQLite/PostgreSQL-Upgrades 1–14 und frischer Schema-14-Restore mit Datenerhalt geprüft.
- [ ] **OPS-005** [P0] Automatische CI — Lint, Format, Types, Unit/Integration/Browser und Scans laufen auf Pull Request.
- [ ] **OPS-006** [P0] Secretscanner — Vor Kommit/Release werden Token und Private Keys entdeckt und blockiert.
- [ ] **OPS-007** [P0] SBOM und Drittanbieter-Notices — Abhängigkeiten und Herkunft dokumentiert; Lizenzgates vor Imagebau.
- [~] **OPS-008** [P0] Rate-Limit/CSRF/XSS/IDOR Tests — Negativtests für Rate-Limit, CSRF, HTML-Escaping und fremde Kolonieobjekte; vollständige Objektmatrix offen.
- [~] **OPS-009** [P0] Race Condition Tests — Dispatch/Marktescrow/Claim/Colonize plus Worker-Fehler-Retry mit Exactly-once-Regression auf SQLite/PostgreSQL 18; Crash-/Lastmatrix offen.
- [~] **OPS-010** [P0] Property tests — deterministische Build/Forschung/Ausbildung/Handel/Abbruch-Sequenzen prüfen Ressourcen-, Reserve-, Einheiten- und Queue-Invarianten; SQLite reproduzierbar, SQLite/PostgreSQL-18-Adapterfall bestanden; breitere Payload-/Worker-Fuzzmatrix offen.
- [~] **OPS-011** [P0] Kampfreplay-Testruns — 1.000 deterministische FUR-3-Seeds liefern identische Resolverausgabe, erhalten Eingabearmeen und bilanzieren Verluste/Überlebende. Domain-Regression bestanden; Live-Dry-run/API/UI und breitere Betriebsabnahme offen.
- [ ] **OPS-012** [P0] Loadtest 30min — 200 aktive/1000 Accounts Szenario mit dokumentierten p95/error/queue lag.
- [~] **OPS-013** [P0] Multiworld-Isolationstest — 8 SQLite/PostgreSQL-18 cases cover world data, chat/offers, Fog and supply; items/object matrix and browser acceptance open.
- [ ] **OPS-014** [P0] Backup-Retention — Tag/Woche/Monat Plan, Verschlüsselung und Offsite-Adapter dokumentiert.
- [x] **OPS-015** [P0] Restore-Probe — Isolierter PostgreSQL-18-Restore mit logischem DB-SHA-256, Ressourcen- und Missions-SHA-256 bestanden.
- [~] **OPS-016** [P0] Health/Ready Endpoint — Getrennte DB-Health-/Worker-Readiness-Prüfung mit Heartbeat-Negativtest; Runtime-Failure-Akzeptanz offen.
- [ ] **OPS-017** [P0] Alerts und Observability — Backupalter, Eventlag, Errorrate und DB/Service-Ausfall erzeugen Alarm.
- [ ] **OPS-018** [P0] Systemhärtung — Nicht-root Container, Firewall, Dienstkonto, restrictive secrets und TLS-Ready.
- [ ] **OPS-019** [P0] Operator Runbook — Start/Stop/Migration/Incident/Backup/Restore/KeyRotation sind Schritt-für-Schritt dokumentiert.
- [ ] **OPS-020** [P0] Live Launch Gate — Externe Domain/VPS/SMTP/Rechtstexte bleiben bis Ownergenehmigung offline vorbereitet.
- [ ] **OPS-021** [P0] Fail/Resume Agent — Agent schreibt validen Checkpoint und kann auf neuer Sitzung ohne Ratefragen fortsetzen.
- [ ] **OPS-022** [P0] Ausführlicher QA Report — Jedes Feature hat echten Test-/UI-/Codebeleg statt bloßem Checkboxstatus.
- [ ] **OPS-023** [P0] License Gate — MIT/Devana nur mit Notice/Rechten; GPL/AGPL/CC unterbleiben ohne bewussten Lizenzentscheid.
- [ ] **OPS-024** [P0] Dependencies Upgrade — Veraltete/unmaintained Komponenten werden bewertet und Tests bei Updates durchgeführt.
















