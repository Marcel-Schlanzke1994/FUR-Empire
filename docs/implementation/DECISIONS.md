# Entscheidungen — Phase A

## 2026-11-18 — PVE-007 Boss-Belohnung

Der Eigentümer wählte die Aufteilung des begrenzten Pools nach verbuchtem Schaden mit einer Auszahlung je beitragendem Konto. Der Entwurf teilt nach erfolgreichem Sieg den Pool ganzzahlig abgerundet im Verhältnis zum Schaden. Aufgerundete Truppenverluste, Boss-Integrität und Schadensobergrenze, Warnzeit und Herkunft der Ranger stehen im optionalen Regelkatalog `FUR-3-TERRA-BOSS-1` als vorläufige Werte.

## 2026-11-12 — Vorläufiger Terra-Wrack-/Reparaturvertrag

Für den opt-in FUR-3-Regelsatz COMBAT-4 gilt `FUR-3-TERRA-RECOVERY-1`; FUR-2 und frühere Kampf-Snapshots bleiben unverändert. Pro Einheitentyp und Verlustereignis werden 25 Prozent der Verluste abgerundet als Wrack gespeichert, mindestens null, für 48 Stunden. Eine Reparatur kostet je Einheit die Hälfte der Katalogkosten, je Ressource aufgerundet, und dauert `training_time × Anzahl`. Pro Kolonie ist ein Auftrag gleichzeitig erlaubt. Das Reservieren von Wrack und Rohstoffen ist atomar; ein Abbruch vor Abschluss stellt Wrackbestand und vollständige Kosten wieder her, Überschüsse gehen ins Reservelager. Ein rechtzeitig gestarteter Auftrag darf nach Ende des Wrackfensters fertig werden. Der Vertrag ist ein vorläufiger Startentwurf; Kampf-/Bewegungs-/Wirtschaftsbalance ist nicht abgenommen und schaltet COMBAT-3/4-Training nicht frei.

## 2026-11-09 — Reihenfolge und Nachweise

Der aktuelle Eigentümerauftrag und `FUR_CODEX_UEBERGABE/CODEX_MASTERPROMPT.md`
ordnen Implementierung vor sämtlichen Prüfungen an. Ältere Epic-/AGENTS-Gates
werden deshalb erst in Phase B ausgeführt. Vorher nur Source-/Schema-Inspektion,
Dateisicherung, Implementierung und Vorbereitung von Tests. Keine neue
`verified`-Markierung. Historische Nachweise bleiben unverändert archiviert.

## D01 — Originalkatalog zusätzlich zum rekonstruierten Tracker

Originale IDs, Verträge und Abhängigkeiten werden vollständig in der neuen
Implementierungsmatrix geführt. Das bestehende `spec/FEATURES.json` und
`TRACEABILITY.md` werden nicht blind ersetzt; frühere Nachweise bleiben lesbar.
Ein noch nicht überprüfter Eintrag ist als Audit in Arbeit gekennzeichnet,
nicht als vorhandene fertige Funktion.

## D02 — Additive Materialien statt Verlängerung aller FUR-2-Rohstoffarrays

Die geforderten zehn Neutralmarktgüter werden durch drei Bestandsrohstoffe
plus sieben eigenständige Materialwaren erfüllt. Die Bestandswirtschaft behält
ihre drei Einträge, Formeln, Transporte, Kosten und Regelhashes. Materialien
haben ein eigenes persistentes Kolonieinventar und einen eigenständigen
versionierten Katalog. Neue Materialwerte sind Designentscheidungen, keine
historischen FUR-2-Werte; Preisbalance bleibt ungetestet.

Bestands-Rohstofftausch und seine API bleiben verfügbar. Neue Warenbefehle
reservieren keine Ressourcen außerhalb der existierenden Spieltransaktion.
Die additive Belegtabelle 030 verhindert Änderung und Löschung der Buchungen.
`colony_id` ist absichtlich eine stabile Archiv-Referenz ohne löschenden
Kolonie-Fremdschlüssel, damit spätere erlaubte Kolonieaufgabe Belege bewahrt.

## D03 — Heimatwechsel pro Konto und Welt

Für die neue Funktion gilt eine 24-Stunden-Sperrfrist pro Welt, Version
`FUR-COLONY-HOME-1`. Diese neue Entscheidung ist unabhängig vom bestehenden
24-Stunden-Kommandantennamen-Cooldown. Kein Ressourcenpreis, keine Verlegung,
keine Übertragung von Einheiten. Die Sperrfrist wird mit Regelversion/Hash
gespeichert; spätere Regeln verändern laufende Fristen nicht rückwirkend.
Die bestehende eindeutige Heimatkennzeichnung wird unter der Spieltransaktion
von alter zu neuer Basis gesetzt. Weltwahl und künftige Allianzlieferungen
nutzen die neue Heimat. Aktuelle Verwaltungsauswahl bleibt bestehen.

## D04 — Feste Missionsziele und historische Kompatibilität

Spielerangriffe und Transporte speicherten bisher nur die Zielkonto-ID und
lasen bei Ankunft dessen aktive Kolonie. Das konnte nach einem Weltwechsel
Effekte in die falsche Welt lenken. Neue Jobs pinnen zusätzlich die Zielkolonie;
bestehende Jobs ohne Pin bekommen eine auf die Ursprungswelt begrenzte
Heimat-Fallbackregel. Die genaue frühere Zielkolonie lässt sich aus solchen
Altjobs nicht zuverlässig rekonstruieren; es wird keine erfunden.
Fehlt das berechtigte Ziel, kehren Einheiten und vorhandene Fracht zurück.
Allianzversorgung prüft bei Empfang weiterhin Konto, Welt und Mitgliedschaft,
aber verlangt keine fortbestehende Heimatmarkierung am fixen Ziel.

## D05 — Keine Laufzeitaktivierung ungetesteter Migrationen

Die neuen Migrationen heißen 030/031, da 029 bereits vorgefunden wurde.
Keine laufenden Prozesse werden neu gestartet, keine Images gebaut oder
Datenbanken geöffnet. Für spätere Phase B sind temporäre Datenbanken sowie
separate PostgreSQL-Tests vorgesehen. Ein unverändert laufender alter Prozess
ist kein Nachweis der geänderten Source-Version.


## D06 — Weltmitgliedschaft und Fraktionswahl

Schema 032 führt eine Mitgliedschaft je Konto und Welt ein. Die Migration übernimmt die bisherige globale Fraktion in eine Welt, wenn mindestens eine dortige Kolonie bereits eine Wahl vermerkt. Die Wahl gilt anschließend für alle Kolonien dieser Welt. Koloniedaten werden für die Übernahme gelesen. Neue Welten beginnen mit freier Fraktionswahl. Produktion, Neutraltausch und Schildwallbonus lesen die Wahl der betroffenen Welt. Die alten Profilfelder bleiben für historische Daten erhalten. Der weltgebundene Fraktionstest ist vorbereitet.


### ENG-002 — Folgesaison in einer neuen Welt

Eine Saisonwelt trägt einen Wettbewerb. Ab dessen Endzeit bleiben Neubeitritte gesperrt. Bestehende Kolonien und das Archiv bleiben erhalten. Dauerwelten können weiterhin aufeinanderfolgende Wettbewerbe austragen.


### ENG-002 — Sandbox-Regel

Der Mastervertrag schreibt einen expliziten Weltmodus vor und lässt die konkrete Sandbox-Regel offen. Sandbox ist eine persistente PvE-Übungswelt ohne Saisonwettbewerbe. Der globale PvP-Schalter bleibt für Dauer- und Saisonwelten maßgeblich.


### ENG-003 — Bestandswelten und Regelbindung

Die erste Bindung einer Bestandswelt verwendet den zu diesem Zeitpunkt ausgelieferten FUR-2-Katalog. Daraus lässt sich kein historischer Regelstand ableiten. Bestehende Kampfberichte werden nicht nachträglich gestempelt.


### ENG-003 — Orbit-Reiseformeln v1

Das Originalpaket legt Formelkennungen und Mindestdauer fest. Für v1 gilt pro Wegabschnitt: Dauer mindestens 60 Sekunden, sonst Distanz durch langsamstes Schiff aufgerundet. Treibstoff ist Distanz mal Summe der Schiffsraten, Frachtkapazität die Summe der Schiffskapazitäten. Distanz und Missionsbuchung müssen beim späteren Flottenbefehl serverseitig ermittelt werden.


### ORB-001 — Terra-Zugang

HQ 8 und aktueller Besitz der Kernzitadelle in derselben Welt erlauben die Freischaltung zu Gateway-Kosten. Die dauerhaft verfügbare Alternative verlangt HQ 8, Ingenieurswesen 8 und Logistik 8 sowie Gateway- und Navigationskosten. Die beiden Pfade verwenden die ursprünglichen Materialwerte. Freischaltung ist eine einmalige Zertifizierung, kein separat gebautes oder wartendes Modul.


ORB-002: Drei Galaxien je Welt als erste feste Kartengrenze, je 100 Systeme mit je 16 Slots aus dem Masterkatalog. Der Server leitet die Geografie aus Katalogdigest, Weltseed, Welt-ID und Koordinaten ab. Dynamische Belegung braucht eine getrennte Sichtprüfung.


ORB-004: Die Terra-Freischaltung stellt einmal je Welt ein Pionierschiff mit Treibstoff für den einfachen Flug bereit. Es startet am Terra-Gateway vor dem ersten System. Der Flug nutzt die Orbit-1-Reiseformel und endet mit der Koloniegründung. Kosten späterer Flüge kommen aus dem Orbit-Inventar.


Orbit-1-Ausbaustart: Gründung stellt 500 Orbit-Erz und Solarstufe 1 bereit. Solaranlage und Raffinerie kosten je Zielstufe 80 bzw. 120 Erz und dauern 60 bzw. 90 Sekunden je Zielstufe. Eine Solarstufe versorgt eine Raffineriestufe mit 12 Äther pro Stunde. Lagergrenze 10.000 Äther, Stufengrenze 10. Diese Erstwerte ergänzen die offenen Produktionswerte des Masterpakets.


Orbit-Werft v1: Jede gegründete Kolonie gewinnt 60 Erz pro Stunde bis zur Lagergrenze. Die Forschung verwendet den Orbit-Erzanteil und die Dauer aus dem Masterkatalog (2600 Erz, 590 Sekunden) und setzt eine Raffinerie voraus. Holz und Stein bleiben Terra-Ressourcen. Schiffskosten kommen aus dem Katalog. Ein Schiff benötigt 60 Sekunden, je Werft läuft ein Auftrag.


ORB-004: Reguläre Flüge verbrauchen ein Kolonieschiff und Äther für den Hinflug. Distanz ist die absolute Differenz der linearen Orbit-Slotindizes. Das Grundlimit von drei aus dem Katalog umfasst aktive Reservierungen und gegründete Kolonien.


ORB-011/014: Frachter transportieren Erz und Äther zwischen eigenen Kolonien der aktiven Welt. Beide Strecken werden vorausbezahlt. Die gesamte Fracht geht zunächst in die Zielreserve. Abholung füllt das begrenzte Lager und lässt Übermengen in der Reserve.


Orbit-Frachtrückruf: vor der Ankunft. Die Rückreise dauert so lange wie der zurückgelegte Hinweg, mindestens eine Sekunde. Bereits gebuchter Treibstoff bleibt verbraucht. Zurückkehrende Fracht geht in die Ursprungsreserve.


Orbit-Aufklärung v1: Eine Sonde erfasst bei Ankunft die Belegung eines Planetenslots. Beobachtungen sind privat und 24 Stunden gültig. Sonden kehren nach dem Scan zurück. Abfangen und weitergehende Daten folgen mit der Orbit-Verteidigung.


Orbit-Kampf v1: Gleichzeitige Salven mit 72 Prozent Basisgenauigkeit und deterministischer Variation von 90 bis 110 Prozent. Schildpunkte erneuern sich je Runde, Hüllenschaden bleibt innerhalb des Gefechts erhalten. Restschaden trifft Klassen in ID-Reihenfolge. Bei nicht überwundener Verteidigung bleibt die Position verteidigt. Ein einzelner Angriff startet mit einer Schiffsklasse.


ORB-021: Ein Viertel der Erz- und Ätherbaukosten zerstörter Schiffe bildet pro Kampf ein Trümmerfeld für 48 Stunden. Beteiligte bergen in Ankunftsreihenfolge bis zum Frachtraum, zuerst Erz, danach Äther. Rückkehr liefert in die Startreserve.


Orbit-Verteidigungsplattform v1: Eine Plattform je Orbit-Kolonie nach Schiffbauforschung. Sie kostet 900 Erz und 240 Äther, dauert 600 Sekunden und wirkt mit 65 Angriff, 110 Schild und 220 Hülle. Die Plattform ist stationär und zerstörbar. Die Werte ergänzen den Masterkatalog.


ORB-005: Ab 1.000 Erz und 250 Äther im neu entstandenen Trümmerfeld bildet sich an der Zielkolonie ein Mond, sofern dort noch keiner existiert. Die Bildung verbraucht genau diese Menge. Der Mond verweist auf das verursachende Gefecht.


Orbit-Station v1: Eine Station pro Kolonie, bis Stufe 3 und 100 Garnisonsschiffe je Stufe. Je Zielstufe kostet der Ausbau 600 Erz und 120 Äther und dauert 300 Sekunden. Der Erstbau umfasst einen Wartungstag, weitere 24 Stunden kosten 24 Äther je Stufe. Inaktive Garnisonen bleiben erhalten und können abgezogen werden. Bei gleichartigen Kampfverlusten werden zuerst Garnisonsschiffe abgezogen.


Mondscanner v1: 750 Erz, 180 Äther und 600 Sekunden Bauzeit. Sonden einer Kolonie mit fertigem Scanner liefern zusätzlich die beobachtete Schiffsanzahl. Ein gegnerischer Schildträger in einer aktiven Stationsgarnison fängt die Sonde ab. Das Ergebnis meldet den Verlust ohne Belegung oder Flottenzahl.


ORB-023: Sprungtore setzen Stationsstufe 2 und Terra-HQ 10 voraus. Bau verwendet 4.200 Orbit-Erz und 890 Sekunden aus dem Forschungsvorschlag. Zwei aktive Stationen sind nötig. Jeder Sprung versetzt eine Schiffsklasse ohne Fracht und belegt beide Tore für sechs Stunden.


Orbit-Expedition v1: Kurierschiffe zahlen Äther für Hin- und Rückflug. Seed entscheidet zu 25 Prozent Sturm (aufgerundetes Viertel Schiffsverlust), 35 Prozent keinen Fund, 25 Prozent Ruinen (30 Erz je Schiff) oder 15 Prozent Anomalie (16 Äther je Schiff). Funde sind durch Frachtraum begrenzt und landen in der Ursprungsreserve.


ORB-022: Ein Mondscanner erfasst für 12 Äther bis zu zehn anfliegende Fracht- und Angriffsmissionen im Umkreis von fünf Systemen derselben Galaxie. Die private Momentaufnahme und die Abklingzeit dauern fünf Minuten. Aktive gegnerische Schildträger-Garnisonen stören den Scan. Angezeigt werden nur Missionstyp und Ankunft.


ORB-024: Mondbelagerung erfordert frische Stufe-2-Mondaufklärung, einen mindestens 24 Stunden alten Mond und drei Belagerungsschiffe. Höchstens ein Hinflug pro Mond. Sieg mit mindestens drei überlebenden Belagerungsschiffen zerstört den Mond und verbraucht eines der Schiffe. Der historische Mond bleibt als Datensatz erhalten, der Scanner wird deaktiviert.


ORB-025: Der Anführer eröffnet einen Allianzverband mit 300 Sekunden zusätzlicher Sammelzeit. Jedes Konto steuert höchstens ein Kontingent einer Schiffsklasse bei und zahlt seinen Hin-/Rückflug. Die längste Reisezeit bestimmt die gemeinsame Rückkehr. Nach Rechteprüfung werden Überlebende je Klasse proportional mit ganzzahligem Rest verteilt.


ORB-026: Der Angriff oder Gesamtverband kann vor Ankunft zurückgerufen werden. Rückflug dauert die angesetzte Reisestrecke, Treibstoff bleibt gebucht. Eine optionale Verlustschwelle zwischen 10 und 100 Prozent wird nach jeder gleichzeitigen Salve ausgewertet, solange beide Seiten noch Schiffe haben.


ORB-027: Höchstens 20 persönliche Vorlagen je Welt, eindeutige Namen je Typ ohne Beachtung der Groß-/Kleinschreibung. Flottenvorlagen speichern eine Klasse, Anzahl und optionale Rückzugsschwelle. Beim Laden wird ein verfügbares Startkontingent ausgewählt. Der eigentliche Auftrag prüft Bestände und Rechte erneut.


ORB-028: Kolonien erhalten sieben Tage Startversorgung. Verlängerung um 24 Stunden kostet 12 Äther und ist möglich, wenn weniger als ein Tag bleibt. Ablauf sperrt neue Abflüge und Sprünge. Bestände, Verteidigung, Werft, Rückruf und laufende Missionen bleiben funktionsfähig. Terra-Pionierflüge nutzen ihre eigene Startausstattung.


ORB-029: Je Klasse und beteiligter Kolonie ist das abgerundete Viertel der Kampfverluste 48 Stunden reparierbar. Wrackmaterial wird vor Trümmerbildung aus dem Materialwert abgezogen. Reparatur kostet die aufgerundete Hälfte der Baukosten und nutzt den regulären Werftplatz und dessen Dauer.


ORB-030: Nur Erz ist auf dieser Gateway-Route zugelassen. Jede Lieferung bewegt 1 bis 500 Einheiten unverändert, zusätzlich kostet der Start 20 Erz am Ursprung. Dauer: 600 Sekunden plus Orbitalreise nach Frachtergeschwindigkeit. Ein Flug je Koloniepaar. Orbit-Ziel bucht in die Reserve, Terra-Ziel nutzt den vorhandenen Lager-/Reservepfad.


ORB-031: Sternlanzen kosten 90 Erz/30 Äther, Schleier-Abfänger 60/20. Je Typ passen 20 Einheiten ins Lager. Sternlanzen werden beim Start gebucht, auch bei Rückruf. Reichweite: 48 Plätze derselben Galaxie. Je nicht abgefangener Lanze erhält die erste Salve 40 Zusatzschaden. Eine verteidigte Kolonie verbraucht je abgefangener Lanze einen Schleier-Abfänger.


ORB-032: Je Welt ein aktives Spezialereignis. Sonnensturm dauert 24 Stunden, Anomalie 36 und Wächter 48. Nur Expeditionen mit Ankunft vor Ende können teilnehmen. Je Konto ist eine Auszahlung möglich, je Ereignis maximal 20. Das Zeitfenster gilt für die Begegnung, die Auszahlung folgt erst bei Rückkehr.


TERRA-010: Ein sofortiger atomarer Umzug reserviert den neuen Platz über den eindeutigen Weltsektorschlüssel. HQ 3, 2.000 Holz, 1.500 Stein, 1.000 Erz und sieben Tage Cooldown. Laufende eigene und eingehende Missionen sowie Terra-Orbit-Fracht müssen abgeschlossen sein.


TERRA-014: Schutzfelder sind für alle Neubelegungen gesperrt. Reservierte Landfelder haben beim Neuspawn Vorrang und sperren Erweiterungen sowie Umzüge. Normale Belegungs-, Gelände- und Abstandsprüfungen gelten weiter. Regeländerungen wirken auf zukünftige Belegungen.


TERRA-015: Freiwillige Aufgabe erzeugt eine 24 Stunden blockierende Ruine ohne öffentliche Besitzer- oder Inventardaten. Danach wird der Sektor automatisch wieder frei, die historische Zeile bleibt erhalten. Automatische Inaktivitätsmaßnahmen brauchen eine eigene Vorwarn- und Wiederherstellungsregel.


TERRA-015 Inaktivität: Authentifizierte Nutzung erneuert den Zeitstempel höchstens stündlich, nach einer Warnung sofort. Nach 30 Tagen gibt es einen privaten Spielbericht und sieben Tage Vorlauf. Offene Missionen, Fracht und Angebote verschieben den Ruhemodus. Dieser pausiert Terra-Produktion und PvP, hält den Standort belegt und bewahrt die Bestände. Reaktivierung lässt keine rückwirkende Produktion entstehen.


ENG-005: Der erste Consumer ist ein privates, sequenziertes Weltprotokoll. Es enthält Ereignistyp und Zeitpunkt ohne Befehlspayload. Ein Weltwechsel wird in der Ausgangswelt protokolliert. Der Worker überträgt bis zu 200 Ereignisse je Zyklus und quittiert die Outbox innerhalb derselben Transaktion.


ENG-006: Der Idempotenzschlüssel bleibt je Konto eindeutig, damit ein alter Retry nach Weltwechsel nie als neuer Auftrag gelten kann. Der Browser sendet Welt, Kolonie und Regelversion. Exakte Wiederholung liefert die aktuelle Ansicht. Historische Signaturen und kontextlose Aufrufer bleiben kompatibel; neue Signaturen speichern SHA-256 statt des Payloads.


ENG-007: Fällige Orbit-Kolonisationen, Bau, Werft, Station, Fracht, Sonden, Expeditionen und Angriffe konkurrieren einzeln nach Fälligkeit und ID mit Terra-Aufträgen. Bestehende Saison- und Gateway-Prioritäten bei gleichen Zeitstempeln bleiben erhalten. Stationsabfragen lösen keine Fertigstellungen mehr aus.


ENG-008: Orbit-Fehler werden mit Besitzer und Typ-ID isoliert. Drei Fehlversuche sperren diesen Auftragsdatensatz. Ein erfolgreicher Retry entfernt seinen Fehlerzähler. Produktion wartet bei einem festhängenden Orbit-Bau am Fälligkeitszeitpunkt, damit der Retry die Rate rückwirkend korrekt weiterführen kann. Der Rückstandswert misst den ältesten verarbeiteten Auftrag relativ zum Beginn des letzten erfolgreichen Zyklus.


ENG-009: Datenbanktrigger erfassen Orbit-Lager und -Reserve bei Anlage und tatsächlicher Änderung. Historische Bestände erhalten einen Startsnapshot. Die Sequenz ordnet Buchungen, der Zeitstempel stammt aus der Datenbank. Fehlgeschlagene Transaktionen hinterlassen keine Buchung. Terra-Ledger und Gateway-Audit bleiben erhalten.


ENG-010: Terra-Produktion rechnet in Zehntausendsteln. Alte Hundertstel bleiben in carry, der feinere Rest liegt additiv in carry_sub. An der Lagergrenze verfallen Überschüsse und Rest. Urlaub und Ruhemodus schreiben den Zeitanker weiter, ohne Produktion gutzuschreiben.


ENG-011: Additive Datenbankwächter prüfen Missionsreferenzen beim Einfügen und Aktualisieren. Bergung darf ein fremdes Ziel nur über einen Kampfbericht mit Beteiligung des Startkontos referenzieren. Kontingente behalten nach Rückkehr ihre historischen Verweise. Bestehende Zeilen werden durch diese Migration nicht umgeschrieben.


ENG-012: Das erste portable Format enthält Topologie und Regeln. Es wird ausschließlich in eine neu angelegte SQLite-Datei als geschlossene Sandbox importiert. Außenposten werden neu neutralisiert. Vollständige Spielstände bleiben Aufgabe der Datenbanksicherung, bis ein separater Welt-Spielstandimport implementiert und abgenommen ist.


ENG-017: Admin-Warnschwellen sind API-p95 über 500 ms bei mindestens 20 Stichproben, Worker-Heartbeat ab 30 s, Scheduler-Lag über 30 s, CLI-Sicherung älter als 24 Stunden oder fehlend und jede Orbit-Bestandsabweichung. Die Latenzprobe gilt pro API-Prozess, höchstens 2.048 Einträge in fünf Minuten.


Terra-Energie v1: Je Kernstufe vier Versorgung, je Fusionsstufe sechs Bedarf. Jede gedeckte Einheit gibt zwei Prozentpunkte Erzproduktion. Gebäudegrenzen, Zeit und Kosten stammen aus dem Masterkatalog. Grundproduktion bleibt ohne Ausbau erhalten.


ECO-002: Die erste Fusionsstufe enthält 24 Stunden Brennstoff. Je weitere 24 Stunden kosten 120 Erz pro aktueller Stufe. Der Bonus endet exakt am Ablaufzeitpunkt. Grundproduktion und Module bleiben erhalten.


ECO-007: Scannertürme vergrößern die Sicht je Stufe um einen Sektor bis maximal vier zusätzliche Sektoren. Uplinks geben zwei Auftragsplätze je Stufe, gedeckelt bei 40. Baukosten, HQ und Bauzeit kommen aus dem Masterkatalog.


ECO-008: Die Spielleitung bindet den Prestige-Regelstand explizit je Welt. Stufen 1–20 laufen separat von HQ und kosten je Auftrag die Grundkosten aus dem Masterkatalog. Je fünf Prestigestufen erweitern die Uplink-Obergrenze um zwei Plätze, sofern ausreichend Uplink-Stufen vorhanden sind.


ECO-012: Bis zu drei Routen pro Terra-Startkolonie, jeweils zu einer eigenen Kolonie der Welt. Intervalle 1–168 Stunden. Kein Nachholstapel bei Ausfall. Pro Route ist eine Trägergruppe zugleich unterwegs. Bei Mangel pausiert sie bis zur manuellen Fortsetzung. Beenden lässt gestartete Transporte regulär enden.


ECO-016: Erste Fraktionsforschungen ab HQ 4, mit 180 Sekunden Laufzeit und Koloniebindung. Adaptive Forstwirtschaft gibt fünf Holz-Prozentpunkte, Kinetischer Schild fünf Prozent Garnisonsstärke bei vorhandenem Wall und Verdeckte Navigation zehn Prozent kürzere eigene Versorgungsflüge. Weitere Katalogeinträge bleiben offen.


ECO-016 Pioniervermessung: Nach Adaptiver Forstwirtschaft kann die aktive Kolonie alle 24 Stunden einen begehbar erreichbaren Sektor im Radius 12 vermessen. Der private Kartenbeobachtung folgt ein einmaliger Gründungsrabatt von acht Prozent am vermessenen Ziel, gültig eine Stunde. Die normale Sektorprüfung bleibt bindend.


ECO-016 Wächterbefestigung: 200 Erz, eine Stunde Wirkung, 24 Stunden Abklingzeit je Startkolonie. Zehn Prozent Verteidigungsbonus an einer fremden Allianzkolonie derselben Welt. Beim Gefecht oder Scan wird die Allianzbindung erneut geprüft. Mehrere Befestigungen stapeln sich nicht.


ECO-016 Syndikatkonvoi: Verdeckte Navigation erlaubt einmal je 24 Stunden einen geschützten Marktkauf an eine andere eigene Kolonie. Der Verkäufer erhält die reguläre Zahlung. Die Escrow-Ware bleibt bis Ankunft gebunden. Dauer: fünf Minuten plus Weg zwischen den beiden eigenen Kolonien. Verkäuferkoordinaten werden nicht verwendet oder offengelegt.


K06 / FUR-3-TERRA-ALLIED-GARRISON-1: Ein Basiseigentümer aktiviert Garnisonen je Heimatkolonie und aktueller Allianz; die Kapazität liegt zwischen 1 und 300 Einheiten. Nur Mitglieder derselben Allianz und Welt dürfen von einer eigenen Kolonie entsenden. Zustimmung, Mitgliedschaft, Zielbesitz und Kapazität werden beim Eintreffen erneut geprüft. Eigentümer und Entsender dürfen zurückrufen; bei ungültiger Mitgliedschaft oder Zielbesitz kehren Truppen intakt zur Ursprungskolonie zurück. Verteidigerverluste werden nach demselben deterministischen Anteil auf jedes separat besessene Heer angewandt. Kolonien und Welten mit noch stationierten oder zurückkehrenden Einheiten dürfen nicht entfernt werden. Dies ist ein neuer FUR-3-Vertrag und ändert keine FUR-2-Kampfkoeffizienten.

K01/K05 FUR-3 ACS-Integration: Seed-Pinning allein reicht nicht als Einbindung des Mehr-Runden-Motors. Die vorhandene ACS-Regel legt für K05 ausdrücklich einen deterministischen Ein-Runden-FUR-2-Kampf fest und verteilt Verluste pro Teilnehmer; die neue Combat-Engine benötigt Teilnehmerattribution bei identischen Einheitentypen über Runden. Außerdem tragen neutrale Außenposten aktuell weder Einheiten noch Strukturintegrität im Zustand, sondern erhalten ihre Verteidigung aus dem FUR-2-Tierstufenwert. Vor FUR-3-ACS müssen deshalb ein versionierter, reproduzierbarer Teilnehmer-Stack-/Taktikvertrag und ein persistentes Fortifikationsmodell (Außenposten und Schildwall) implementiert werden. Keine Seed-Zeile unter ACS-IDs anlegen, solange die vollständige FUR-3-Auflösung nicht integriert ist.


K07 / FUR-3-Rückzug: Der Schwellenwert wird pro Welt durch Admins im Bereich 1–100 Prozent gesetzt (Katalogstandard 60). Der Worker pinnt ihn zusammen mit Kampfregelhash und Seed-Commitment beim Missionsstart; spätere Weltänderungen wirken nur auf neue Missionen. FUR-2 erhält keine Rückzugsregel.

K02 / WAR-018 — FUR-3 militärische Wertung v1 (Entwurf, nicht balanceabgenommen): Bestehende FUR-2-Gebäude-/Forschungs-/Eroberungspunkte bleiben unverändert. Für unterstützte FUR-3-COMBAT-Missionen erhält ein persönlicher Angreifer je tatsächlich verlorener Einheit einen Angriffspunkt; der Heimatverteidiger je tatsächlich verlorener eigener Einheit einen Verteidigungspunkt. Verluste verbündeter Verteidiger-Garnisonen werden dem jeweiligen Entsender als Verteidigungspunkte zugerechnet. Neutrale NPC-Verluste erzeugen keine Spielerscores. Bei ACS wird jeder Verlust der jeweiligen Angriffswing zugerechnet; Allianzwerte sind die Summe der Werte aktueller Allianzmitglieder derselben Welt. Eine bestätigte Ankunft einer alliierten Garnison vergibt einmalig einen Unterstützungspunkt pro stationierter Einheit an den Entsender, höchstens einmal je rollierendem 24-Stunden-Fenster pro Spieler und Welt; Ablehnung, Abbruch und Rückruf geben keine Punkte. Der Ledger ist nach Mission, Spieler und Kategorie eindeutig, transaktional, weltgebunden und mit Regelversion/Zeitpunkt auditierbar; die eigene Ansicht gibt höchstens 50 Zeilen aus. Neue Versionen dürfen den Wert nicht neu interpretieren. Der FUR-3-Ledger ist additiv und wirkt nicht auf das bestehende FUR-2-Ranking. Zahlen und Zurechnung bleiben bis zur Eigentümer-/Balanceabnahme ein opt-in Entwurf; Ranking-UI zeigt diesen Status an.
## 2026-11-11 — FUR-3-Gefechtsprobe

Die FUR-3-Gefechtsprobe verwendet 16 reproduzierbare Auflösungen des versionierten Live-Resolvers. FUR-2 bleibt deterministisch. PvP-Projektionen basieren ausschließlich auf frischer Level-2-Aufklärung; die API gibt weder Szenario-Seeds aus noch persistiert sie Kampfzustand. Fokus- und Frontend-Regressionen bestehen. Die FUR-3-Balance ist nicht abgenommen; ACS, Fortifikationen und breite Browser-/Geräte-/Barrierefreiheitsabnahme bleiben offen.

## 2026-11-12 — FUR-3-Gegenaufklärung

Auf Nutzerwunsch wurden die fehlenden K03-Werte als eigener, opt-in FUR-3-Vertrag festgelegt; FUR-2 bleibt unverändert. `FUR-3-TERRA-INTELLIGENCE-1` setzt Abfang auf `min(50%, 2% × Verteidiger-Taktik + 3% × Schildwall)` und Entdeckung auf `min(60%, 10% + 3% × Taktik + 2% × Schildwall)`. Werte und Seed werden beim Aufklärungsversand gepinnt. Ein Abfang entdeckt die Mission, verliert genau einen Ranger, unterdrückt neue Intel und löst keinen Gegenkampf aus; Entdeckung gibt dem Verteidiger nur einen generischen Alert. Die Zahlen sind ein implementierter Startvertrag und bleiben bis zur Balanceabnahme ausdrücklich unbalanciert.

K01 neutraler FUR-3-Außenposten, COMBAT-2 (2026-11-12): COMBAT-1 bleibt unverändert für laufende Missionen und bestehende Welten. Der optionale COMBAT-2-Katalog ergänzt eine passive Befestigung mit 55 Strukturpunkten je Tierquadrat (Tier 1–8), ohne Gegenangriff; sie wird aus der kanonischen Außenpostenstufe erzeugt und nach dem Kampf nicht als Truppengarnison gespeichert. Diese Zahlen sind ein technischer Entwurf und nicht balanceabgenommen. Neue Welten bleiben FUR-2, und die Auswahl ist im Adminbereich ausdrücklich als Entwurf markiert. PvP und Aufklärung verwenden dieselbe versionierte COMBAT-2-Regelidentität; FUR-3-Gegenaufklärung bleibt aktiv. K01 und K05 bleiben teilweise offen, bis Werte, Teilnehmerattribution für ACS und UI-/Barrierefreiheitsabnahme bestätigt sind.


K05 / FUR-3-TERRA-ACS-3 (2026-11-12): Bestehende FUR-2-Welten behalten den eingefrorenen ACS-2-Vertrag. FUR-3-Welten pinnen beim Start den Weltkampfregelsatz, Digest, Seed und die Rückzugsschwelle in `terra_combat_missions`, referenziert über die Allianzangriffs-ID. Jede Teilnehmertruppe und jeder Einheitentyp ist im deterministischen Mehr-Rundenresolver ein separater Stack; Taktik wirkt pro Teilnehmer. Verluste und Überlebende werden den jeweiligen Ursprungsarmeen zugeordnet. COMBAT-2-Neutralfortifikation bleibt virtuell und optional. Abbruch löscht unverbrauchte Seeds; Abschluss speichert Replay und veröffentlicht Seed/Commitment im Teilnehmerbericht. K05 bleibt `partial` bis Browser-, Geräte-, Tastatur/Screenreader-, Lokalisierungs- und Balanceabnahme.


## 2026-11-12 — FUR-3-Truppenbewegung (K11/WAR-006)

Auf Eigentümerwunsch als opt-in, klar markierter FUR-3-Entwurf umgesetzt; FUR-2 bleibt unverändert. `FUR-3-TERRA-COMBAT-3` erhält Terrainpfadkosten, Einheitengeschwindigkeit, Reichweite und Treibstoff aus seinem unveränderlichen 21-Profil-Katalog. Marschzeit folgt der langsamsten Einheit; Erz für Hin- und Rückweg wird beim Versand atomar reserviert. Die Berechnung wird in den Missionsdaten gespeichert und die Rückreise nutzt die festgelegte Dauer. Schema 79 erweitert den Weltregelsatz und speichert die Reisezeit alliierter Garnisonen. Neue Profile bleiben ohne Ausbildungsweg.

Die Admin-Weltauswahl und Missionsvorschau zeigen den Entwurfsstatus; eine serverseitige Vorschau begrenzt Ziele auf erkundete Sektoren und Trupps auf aktuellen Bestand, ohne Ressourcen oder Aufklärung zu schreiben. Gezielte SQLite-/Migrationsregressionen bestanden (16 passed). Danach bestand die vollständige Suite mit isolierter PostgreSQL 18-Datenbank: 646 passed, 1 skipped und eine bestehende Starlette/httpx-Deprecation-Warnung (2899.36s). Ruff, Black, strict mypy, JavaScript-Check, ESLint, 66 Frontendtests, pip-audit und 344-ID-Traceability bestanden. Der lokale Main-Dockerstand wurde nach Backup und validiertem Restore auf Schema 79 aktualisiert; Browser-/Mobile-/Screenreader- sowie Balanceabnahme bleiben offen.

K07 / PVE-003 — FUR-3-NPC-CAMPS-3 (2026-11-16, vorläufig): 300 Sekunden private Warnzeit; max. ein Angriff je Spieler in 24 Stunden; max. eine Auflösung je Welt/Worker-Durchlauf; deterministischer, beim Start gepinnter Kampf; NPC-Verluste/Überlebende und Ressourcenplünderung max. 10 % je Ressource und höchstens 200, begrenzt auf Lagerbestand; kein Außenpostenbesitzwechsel; Schutz-, Aktivitäts-, Eigentümerwechsel- und Frischeprüfungen; privater Bericht. FUR-2 und CAMPS-1/2 unverändert. Werte bis zur Balanceabnahme als nicht freigegebener opt-in Entwurf behandeln.


K08 / PVE-004 — FUR-3-TERRA-COMBAT-5 (2026-11-16, vorläufig): Neutrale Festungsstruktur max. 55 × Außenpostenstufe² Integrität; bei erstmaliger Opt-in-Aktivierung bestehender Neutralposten volle Integrität; Spielerangriffe speichern verbleibende Strukturintegrität; Regeneration ceil(2 % des Maximums je vergangener Minute), neutral-only, max. bis zur Stufenobergrenze; Worker catch-up anhand je Außenposten gepinntem Zeitstand; bei Eroberung Neutralzustand löschen. FUR-2 und COMBAT-1–4 bleiben unverändert. COMBAT-5 darf wegen des neuen Kampfzustands nur vor dem ersten Weltbeitritt aktiviert werden. Zahlen sind ein technischer Startentwurf und nicht balanceabgenommen.
