# FUR Empire – vollständige Spielanleitung

Diese Anleitung beschreibt die Funktionen, die im aktuellen FUR-Empire-Spiel vorhanden sind. Sie gilt für die Browseroberfläche „Genesis“, den Regelkatalog FUR-2 und einen separat gekennzeichneten FUR-3-Vorschlag zur Außenpostenumwandlung. Die Spielleitung kann einzelne Funktionen wie Registrierung, PvP oder Wartung serverseitig ein- und ausschalten.

## Schnellstart

1. Öffne die Adresse, die dir der Betreiber gegeben hat. Auf dem Entwicklungsrechner ist das lokal `http://127.0.0.1:8080`; der Docker-Testbetrieb verwendet `http://127.0.0.1:8081`. Eine lokale Adresse ist nur auf demselben PC erreichbar.
2. Wähle **Neu hier? Imperium gründen**, gib einen Kommandantennamen und ein Passwort ein und melde dich an. Namen sind 3–24 Zeichen lang. Im lokalen Modus gilt eine Mindestpasswortlänge von 8 Zeichen; im Produktionsmodus sind mindestens 12 Zeichen und eine gültige E-Mail erforderlich.
3. Baue deine Wirtschaft aus, hole fertige Direktivenbelohnungen ab und stelle Truppen auf.
4. Wähle auf der Weltkarte einen Außenposten, prüfe die Verteidigung und entsende eine Mission. Die Weltaufträge laufen serverseitig weiter, auch wenn du den Browser schließt.

In einer Welt, in der die Spielleitung das FUR-3-Gegenstandssystem aktiviert hat, können Expeditionen höchstens ein Bergungsmaterial finden: bei Fundort, Vorratsfund oder Grenzpatrouille jeweils mit 10 % Chance, entsprechend 8 % je Expedition insgesamt. Gegenstände werden erst nach der Ressourcenbeute in freie Trägerkapazität geladen. FUR-2 und nicht optierte Welten erhalten keine Expeditionsgegenstände. Die Werte sind ein vorläufiger Balanceentwurf.

Ist die Ruinenerkundung für deine Welt aktiviert, findest du aktive Kolonieruinen unter **Weltkarte → Ruinenerkundung**. Wähle eine Ruine und die Zahl der Ranger. In der Missionsliste kannst du den Trupp vor Ankunft zurückrufen. Nach der Erkundung stehen das Ergebnis unter **Berichte** und die private Beobachtung für 24 Stunden auf der Karte. Geborgene Rohstoffe kommen mit den überlebenden Rangern in der Ausgangskolonie an.

Sobald die Spielleitung in deiner Welt einen **kooperativen Weltboss** ansetzt, erscheint er unter **Streitkräfte**. Nach der Warnzeit kannst du einen freien Angriffsplatz mit Rangern belegen. Der gemeinschaftliche Fortschritt steht neben deinem eigenen Beitrag. Bei einem Sieg kannst du dort einmal den durch deinen Schaden verdienten Erzanteil abholen.

Unter **Weltkarte → NPC-Weltinvasion** siehst du angesetzte Invasionen und das verbleibende Angriffsbudget. Persönliche Warnungen erscheinen auf der Karte. Sie nennen deinen betroffenen Außenposten und die Ankunftszeit, damit du die Garnison vorbereiten kannst.

Dein Konto und die gemeinsame Welt bleiben auf dem jeweiligen Server gespeichert. SQLite im lokalen Modus und PostgreSQL im Docker-/Produktionsbetrieb sind getrennte Spielwelten; ein lokaler Spielstand wird nicht automatisch auf den Server übertragen.

Zum Start erhältst du 1.200 Holz, 1.000 Stein und 800 Erz sowie je ein Produktionsgebäude auf Stufe 1. Damit kannst du die erste Stufe jedes Gebäudetyps bezahlen und alle drei Ressourcen ohne eroberte Außenposten weiter erzeugen. Der Neulingsschutz gilt eine Stunde nach Kontoerstellung; deine Grundproduktion läuft währenddessen weiter.

## Oberfläche und Bereiche

| Bereich | Was du dort tun kannst |
|---|---|
| **Kommando** | Produktion, Imperiumsmacht, Garnison, Außenposten, Auftragswarteschlange und Direktiven sehen. Erfüllte Direktivenbelohnungen hier abholen. |
| **Außenposten** | Gebäude ansehen und Ausbauaufträge starten. |
| **Forschung** | Logistik, Taktik und Ingenieurswesen erforschen. Ein Forschungslabor ist erforderlich. |
| **Streitkräfte** | Ranger, Wächter und Sturmmechs ausbilden. |
| **Weltkarte** | In der 64 × 64-Welt navigieren, neutrale Posten und Kommandanten auswählen und Missionen starten. Das Raster zeigt jeweils bis zu 20 × 20 Sektoren. |
| **Handel** | Holz, Stein und Erz an der neutralen Rohstoffbörse sofort tauschen. |
| **Handel / Gegenstände** | Sieben Materialgüter handeln, FUR-3-Gegenstände same-world zwischen eigenen Kolonien versorgen, Gegenstandsreserven abholen und in optierten FUR-3-Welten bis zu zwei Entwurfsrezepte in Auftrag geben. |
| **Berichte** | Kampf-, Missions-, Transport- und Kolonieereignisse nachlesen. |
| **Rangliste** | Imperiumsmacht aller Kommandanten vergleichen. |
| **Spielanleitung** | Kurze Einstiegshilfe im Spiel. Diese Datei enthält die ausführlichere Fassung. |
| **Allianz** | Allianzen gründen oder Einladungen annehmen, Mitglieder verwalten und Diplomatie betreiben. |
| **Nachrichten** | Weltkanal, Allianzkanal und private Nachrichten verwenden. |
| **Spielermarkt** | Waren gegen andere Rohstoffe anbieten, Angebote annehmen oder zurückziehen. |
| **Weltbetrieb** | Eine Fraktion wählen, Live-Ereignisse und Saisons ansehen und den Urlaubsmodus steuern. |
| **Kontosicherheit** | E-Mail, Authenticator und angemeldete Geräte verwalten, Sitzungen einzeln oder vollständig abmelden. |
| **Spielleitung** | Moderation und Weltbetrieb verwalten. Der Bereich wird nur Moderatoren und Administratoren angezeigt. |

Die Oberfläche aktualisiert den Spielstand regelmäßig. Sie ist nur die Bedienoberfläche: Ressourcen, Kämpfe, Berechtigungen, Aufträge und Buchungen werden auf dem Server geprüft und verarbeitet.

## Kolonie, Rohstoffe und Produktion

Neue Genesis-Heimatbasen und Weltbeitritte entstehen auf freien Landsektoren mit mindestens sechs Sektoren Abstand zu jeder bestehenden Kolonie der Welt. Weitere Kolonien können nur auf freien, aufgeklärten Landsektoren entstehen, die über begehbares Gelände von mindestens einer deiner Kolonien derselben Welt erreichbar sind und ebenfalls mindestens sechs Sektoren Abstand zu allen bereits belegten Kolonien haben. Die Belegung wird zusammen mit dem Kolonieeintrag atomar gespeichert; derselbe Sektor kann nicht doppelt belegt werden.

Eigene, vollständig eroberte Außenposten unterhalb Stufe 8 lassen sich über die Außenpostenliste zu Kolonien ausbauen. Dieser aktive Spielbefehl folgt derzeit einem separat versionierten FUR-3-Vorschlag, der noch auf Eigentümerabnahme wartet: Kommandozentrale 3, freier Kolonieslot, sechs Sektoren Abstand zu allen eigenen Kolonien, aufgeklärtes und begehbares Ziel, exakte Namensbestätigung sowie 6.000 Holz, 4.500 Stein und 3.000 Erz. Vorräte und Garnison wechseln in die neue Kolonie; das übliche Startpaket entfällt. Der Außenposten wird entfernt, sein Eroberungswert und Regionsbeitrag enden, und gespeicherte Kartenfavoriten auf dieses Ziel werden gelöscht. Die Zitadelle kann nicht umgewandelt werden.

Auf der Weltkarte kannst du aufgeklärte Außenposten suchen, Koordinaten anspringen und bis zu 20 Ziele je Welt als private Favoriten markieren. Favoriten, Sternmarker und der Filter „Nur gemerkte Ziele“ wechseln mit deiner aktiven Welt. Für ein gemerktes Ziel kannst du einen bekannten Weg von der aktiven Kolonie anzeigen lassen. Die Routenplanung nutzt nur aufgeklärte, begehbare Felder; unbekannte Sektoren und Wasser werden nicht als Abkürzung verwendet. Die Route wird nicht dauerhaft gespeichert.


Öffne **Imperium / Kolonien** und ändere den Namen direkt auf der Karte der gewünschten Kolonie. Namen müssen 3–32 Zeichen lang und weltweit eindeutig sein; der Kommandantenname des Kontos ändert sich dadurch nicht.

Eine Außenkolonie kannst du erst aufgeben, wenn alle Bau-, Forschungs-, Trainings- und Missionsaufträge abgeschlossen und eingehende Versorgungen angekommen oder zurückgenommen sind. Nimm offene Marktangebote vorher zurück. Zum Schutz vor Fehlklicks musst du den aktuellen Kolonienamen exakt bestätigen. Die Heimatkolonie kann erst nach einem Heimatwechsel aufgegeben werden. Dabei werden Rohstoffe, Reserve, Gebäude, Forschung und Truppen dieser Nebenbasis endgültig entfernt.

Jede Kolonie besitzt **Holz**, **Stein** und **Erz**. Neue Konten beginnen mit 1.200 Holz, 1.000 Stein und 800 Erz. Die Produktion läuft serverseitig, auch wenn der Browser geschlossen ist. Fertige Aufträge werden durch den Welt-Worker verarbeitet.

Die Produktion je Ressource und Sekunde richtet sich nach:

```text
(2 + 2 × Stufe des zugehörigen Rohstoffgebäudes)
× (100 + 15 × Ingenieurswesen + Ereignisboni + 5 × eroberte Außenposten + Fraktionsbonus)
/ 100
```

Bruchteile werden als Rest gespeichert, damit häufiges Aktualisieren keine Produktion verliert. Während des Urlaubsmodus ist die eigene Produktion ausgesetzt.

Das Depot fasst `2.000 + 2.000 × Depotstufe` je Rohstoff. Lieferungen und Rückerstattungen, die nicht mehr in das Depot passen, gehen ins **Reserve-Lager**. Von dort kannst du sie später mit **Ins Depot übernehmen** abholen; es wird nur so viel übernommen, wie noch in die Lager passt.

### Gebäude

Alle Gebäude können bis Stufe 10 ausgebaut werden. Die Kosten eines Ausbaus betragen die Basiskosten multipliziert mit der Zielstufe. Je Kolonie können bis zu fünf Bauaufträge gleichzeitig in der Warteschlange stehen; nur der erste läuft gerade. Beim Einreihen werden Kosten reserviert und bleiben an die für den Auftrag gespeicherte Regelversion gebunden. Die Reihenfolge wartender Bauaufträge kann geändert werden; dabei plant der Server Zielstufen, Kosten und Startzeiten neu. Ein Bauauftrag kann storniert werden; die Erstattung richtet sich nach dem noch nicht verbrauchten Zeitanteil.

| Gebäude | Funktion | Basiskosten (Holz / Stein / Erz) |
|---|---|---:|
| Kommandozentrale | Beschleunigt Bauaufträge, erhöht Imperiumsmacht; ab Stufe 3 sind Eroberungen möglich. | 150 / 120 / 80 |
| Bioforst | Produziert Holz. | 75 / 50 / 20 |
| Steinbruch | Produziert Stein. | 90 / 65 / 30 |
| Erzraffinerie | Produziert Erz. | 100 / 90 / 45 |
| Depot | Erhöht das Lagerlimit um 2.000 je Stufe. | 120 / 100 / 50 |
| Kaserne | Schaltet Truppen abhängig von ihrer Stufe frei. | 130 / 110 / 90 |
| Forschungslabor | Voraussetzung für alle Technologien. | 120 / 150 / 130 |
| Schildwall | Erhöht die Verteidigung der Kolonie. | 80 / 160 / 70 |

Ein Bauauftrag dauert mindestens 3 Sekunden; die genaue Bauzeit sinkt mit der Stufe der Kommandozentrale. Das Spiel zeigt den laufenden Auftrag in der Operationszentrale.

### Forschung

Je Kolonie können bis zu fünf Forschungsaufträge gleichzeitig in der Warteschlange stehen; nur der erste läuft gerade. Eine Technologie kostet ihre Basiskosten multipliziert mit der Zielstufe und benötigt `12 × Zielstufe` Sekunden. Beim Einreihen werden Kosten reserviert und an die Regelversion des Auftrags gebunden. Wartende Forschungsaufträge lassen sich umordnen und stornieren; die verbleibende Zeit bestimmt die anteilige Rückerstattung.

| Technologie | Effekt je Stufe | Basiskosten (Holz / Stein / Erz) |
|---|---|---:|
| Militärtaktik | +15 % Angriffskraft und Truppenverteidigung. | 70 / 90 / 150 |
| Logistik | +10 Beutekapazität je Einheit und Stufe. | 130 / 70 / 100 |
| Ingenieurswesen | +15 Prozentpunkte Rohstoffproduktion. | 100 / 140 / 90 |

### Truppen

Ausbildung erfordert die angegebene Kaserne-Stufe. Eine Einheit kostet die aufgeführten Rohstoffe; ein Ausbildungsauftrag darf 1–100 Einheiten enthalten. Die Ausbildungszeit je Einheit ist ebenfalls angegeben. Pro Kolonie läuft jeweils ein Ausbildungsauftrag gleichzeitig.

| Einheit | Kaserne ab | Kampfkraft | Ausbildungszeit | Kosten je Einheit (Holz / Stein / Erz) |
|---|---:|---:|---:|---:|
| Ranger | 1 | 12 | 2 Sekunden | 35 / 15 / 25 |
| Wächter | 2 | 28 | 4 Sekunden | 50 / 40 / 60 |
| Sturmmech | 3 | 70 | 7 Sekunden | 100 / 90 / 140 |

## Aufträge und Direktiven

Es gibt fünf serverseitige Direktiven in dieser Reihenfolge: alle drei Rohstoffgebäude auf Stufe 2 (400 je Rohstoff), Kaserne bauen (300), erste Technologie erforschen (500), ersten Außenposten erobern (900), Zitadelle erobern (2.000). Ein Ziel kann schon vorher erfüllt sein; seine Belohnung wird aber erst freigeschaltet, wenn du die vorherige Direktive abgeholt hast. Jede Belohnung gibt es einmal. Über dem Depotlimit liegende Rohstoffe landen im Reserve-Lager.

Neue Missions- und Garnisonsaufträge werden ab 30 bereits gespeicherten laufenden Aufträgen blockiert. Bau, Forschung und Ausbildung besitzen je eine separate Einzelwarteschlange und können parallel laufen. Die Oberfläche zeigt verbleibende Zeit und Auftragstyp.

In den Bereichen **Außenposten**, **Forschung** und **Streitkräfte** kannst du Produktionsvorlagen speichern. Jede Vorlage enthält einen Bau-, Forschungs- oder Rekrutierungsauftrag; Rekrutierung speichert zusätzlich 1–100 Einheiten. Bis zu zehn Vorlagen mit unterschiedlichen Namen lassen sich pro Konto speichern. **Einreihen** wendet das Profil auf die aktuell gewählte Kolonie an. Der Server prüft dabei erneut Voraussetzungen, Rohstoffe, Stufen- und Warteschlangenlimits. Eine Vorlage reserviert nichts und wiederholt sich nicht automatisch; erneutes Einreihen erzeugt einen neuen, idempotenten Befehl.

## Weltkarte, Überfälle und Eroberungen

Die gemeinsame Welt umfasst **64 × 64 = 4.096 Sektoren** und **104 neutrale Außenposten**. Die Sektoren werden in Ausschnitten angezeigt; mit den Richtungsbuttons kannst du die Karte verschieben. In der Übersicht rechts kannst du jeden Außenposten direkt auswählen. Andere Kommandanten erscheinen in einer separaten Liste.

Neutrale Außenposten haben Stufen 1–8. Die Verteidigung beträgt `55 × Stufe²` plus die Kampfkraft einer vorhandenen Garnison. Die Zitadelle des Kerns ist das Stufe-8-Kampagnenziel.

Im Missionsfenster kannst du Truppen auswählen und die angezeigte Kampfkraft mit der Verteidigung vergleichen. Die Kampfkraft deiner Armee ist die Summe aus Kampfkraft je Einheit, multipliziert mit `100 + 15 × Taktikstufe` Prozent. Zum Sieg muss der Angriff **höher** als die Verteidigung sein.

Für einen bekannten neutralen Außenposten kannst du im Missionsfenster **Gefechtsprobe** aufrufen. Bei einem Spielerziel erscheint die Probe nur mit einem aktuellen Spionagebericht der Stufe 2 und wenn der Angriff nach den geltenden PvP-Schutzregeln möglich ist. Beide Varianten verwenden serverseitig dieselbe deterministische FUR-2-Berechnung wie die spätere Kampfauflösung und zeigen Ausgang, eigene Verluste und Überlebende. Die neutrale Probe zeigt mögliche Beute; beim Spielerziel bleiben nicht aufgeklärte Ressourcen unbekannt. Die Probe startet keine Mission und verändert weder Truppen noch Ziel. In FUR-2 ist die Projektion exakt für den gespeicherten Intel-Stand; in FUR-3 zeigt sie Schätzwerte aus 16 reproduzierbaren Szenarien. In COMBAT-4 verwendet sie zusätzlich die im aktuellen Stufe-2-Bericht gespeicherten Verteidigungsanlagen und zeigt die geschätzte Minen-Auslösequote. Keine Vorschau garantiert, dass sich ein Ziel bis zu einer späteren Ankunft nicht verändert.

Für die **Aufklärung eines Spielers** schickst du ausschließlich Ranger an dessen Heimatkolonie in derselben Welt. Ein oder zwei Ranger liefern Stufe 1 mit HQ und Gebäuden; ab drei Rangern gibt es Stufe 2 mit zusätzlich Verteidigung und Truppenbestand. Der Bericht bleibt eine Stunde aktuell. PvP muss erlaubt sein und Schutzzeiten gelten auch bei der Ankunft. In Welten mit FUR-3-Gegenaufklärung kann der Verteidiger die Mission entdecken und erhält dann nur einen allgemeinen Alarm ohne deinen Namen oder deine Truppenzahl. Bei einem Abfang verlierst du genau einen Ranger und erhältst keine neuen Zieldaten; übrige Ranger kehren zurück. FUR-2-Welten behalten das bisherige Aufklärungssystem ohne diese Gegenaufklärung.

Im Missionsfenster kannst du eine Truppenzusammenstellung als **Missionsvorlage** speichern und später bei einem passenden Ziel laden. Vorlagen enthalten Missionsart, Einheitenzahlen und optional die Eroberungswahl; beim Laden werden Truppenzahlen auf deine aktuell verfügbaren Einheiten begrenzt. Bis zu zehn Vorlagen gehören zu deinem Konto und lassen sich wieder löschen. Sie reservieren keine Truppen und starten keine Mission.

Mit **Expedition** entsendest du Truppen zu einem bekannten freien Außenpostensektor. Die FUR-3-Regelversion `FUR-3-EXPEDITIONS-1` würfelt bei Ankunft reproduzierbar: Fundort (35 %), Vorräte (25 %), Grenzpatrouille (20 %), Geländegefahr (10 %) oder kein besonderes Ereignis (10 %). Fundort/Vorräte bringen 120–420 Einheiten einer zufälligen Ressource; Patrouillen bringen 80–180 und kosten 10–25 % der Truppen, Geländegefahr kostet 20–40 %. Die Beute ist durch die Kapazität der Überlebenden begrenzt. Überlebende und Funde kehren automatisch zurück. Du kannst die Expedition vor der Ankunft zurückrufen; dann wird kein Ereignis ausgelöst.

- Bei einer Niederlage gehen die entsandten Einheiten verloren.
- Auch ein Sieg kostet mindestens 10 % der angreifenden Truppen; bei starker Verteidigung können die Verluste höher ausfallen.
- Die Verluste der Einheitentypen werden auf ganze Einheiten aufgerundet.
- Überlebende können Beute tragen. Die Kapazität beträgt `überlebende Einheiten × (40 + 10 × Logistikstufe)`. Bei neutralen Posten wird die Beute auf Holz, Stein und Erz verteilt und durch vorhandene Bestände sowie Kapazität begrenzt.
- Eine Reise dauert mindestens 5 Sekunden und hängt von der Entfernung ab. Nach dem Angriff startet ein Rückmarsch; Überlebende und Beute werden bei der Rückkehr gutgeschrieben.
- Neutrale Außenposten füllen ihre Vorräte automatisch wieder auf: je Ressource um 1 Einheit pro Minute bis zum bisherigen Stufenbestand von `400 × Stufe`. Das gilt nicht für eroberte Außenposten. Bei alten Spielständen wird der Regenerationszeitpunkt beim ersten Weltlauf gesetzt; bestehende Vorräte werden dabei nicht verändert.
- Besetzt ein anderer Kommandant den angegriffenen Außenposten vor Missionsankunft, wird die Mission abgebrochen und die Truppen kehren unverletzt zurück.

Aktiviere im Missionsfenster **Erobern**, um einen Außenposten dauerhaft zu übernehmen. Das erfordert Kommandozentrale Stufe 3 und einen gewonnenen Kampf. Jeder eroberte Posten erhöht die Rohstoffproduktion um 5 Prozentpunkte und die Imperiumsmacht um 100 Punkte. Eine gegnerische Übernahme zieht dem bisherigen Besitzer einen Eroberungspunkt für den Posten ab. Die Eroberung der Zitadelle schaltet den Kampagnensieg frei; danach kann weitergespielt werden.

## Rohstoffbörse und Spielermarkt

### Neutraler Soforttausch

Im Bereich **Handel** gibst du mindestens 10 Einheiten eines Rohstoffs ab und wählst einen anderen Rohstoff als Ziel. Der Tausch wird sofort ausgeführt. Normalerweise erhältst du 50 % der abgegebenen Menge. Das Depot muss den Zielrohstoff aufnehmen können. Die Syndikat-Fraktion erhöht den Ertrag auf 60 %.

### Markt zwischen Spielern

Im **Spielermarkt** kannst du bis zu zehn Angebote gleichzeitig offen haben. Ein Angebot hinterlegt bei Erstellung 10–100.000 Einheiten des angebotenen Rohstoffs und fordert 10–100.000 Einheiten eines anderen Rohstoffs. Die angegebene Menge wird beim Annehmen vollständig bezahlt; es gibt keine automatische Preisempfehlung.

- Jedes Angebot läuft nach 24 Stunden ab.
- Der angebotene Rohstoff wird während der Laufzeit sicher verwahrt und nicht mehr als Kolonievorrat gezählt.
- Ein Angebot kann nur einmal angenommen werden. Du kannst dein eigenes Angebot nicht selbst annehmen.
- Bei Annahme wird die Ware dem Käufer ins Reserve-Lager gelegt; die Zahlung wird dem Anbieter gutgeschrieben, bei vollem Depot ebenfalls über das Reserve-Lager.
- Du kannst eigene offene Angebote zurücknehmen. Die hinterlegte Ware geht dann ins Reserve-Lager.
- Abgelaufene Angebote werden geschlossen und die hinterlegte Ware zurückerstattet.

## Spielerangriffe, Transporte und Garnisonen

### PvP-Angriffe

Spielerangriffe sind nur möglich, wenn die Spielleitung PvP aktiviert hat. Beide beteiligten Konten müssen mindestens eine Stunde bestehen. Allianzmitglieder können einander nicht angreifen. Ein angenommener Nichtangriffspakt schützt die Mitglieder der beteiligten Allianzen. Spieler im Urlaubsmodus sind geschützt. Diese Regeln werden bei Ankunft erneut geprüft: Wird ein Schutz aktiv oder ein NAP angenommen, kehrt die Armee unverletzt zurück. Eine Kriegserklärung ist derzeit keine Angriffsvoraussetzung. Die Stärke der gegnerischen Verteidigung wird im Missionsfenster angezeigt.

Der Schildwall zählt zur Spielerverteidigung; beim Wächterbund ist er im PvP 40 % stärker. Kämpfe können Truppenverluste, Ressourcendiebstahl und Berichte verursachen. Kampf, Ressourcenbuchung und Bericht werden serverseitig gemeinsam verarbeitet.

In Welten mit dem ausdrücklich vorläufigen Regelstand **FUR-3-TERRA-COMBAT-4** kannst du unter **Gebäude → Kolonieverteidigung** zusätzlich Kinetikgeschütze, Aegis-Emitter, Annäherungsminen und einen Gefechtsbunker errichten und beschädigte Anlagen reparieren. Die Anlagen benötigen Voraussetzungen und freie Verteidigungsslots; Reparatur ist während eines eingehenden Angriffs gesperrt. Geschütze, Schilde und Bunker kämpfen in Spieler- und Allianzgefechten mit. Ein Minenfeld kann einmal pro Angriff auslösen, wird dann verbraucht und schwächt den Angreifer. Restintegrität und Minenereignis stehen im Gefechtsbericht. Diese Werte sind noch nicht balanceabgenommen. In FUR-2-Welten ändert sich die Verteidigung dadurch nicht.

Im Berichtsarchiv lassen sich Gefechtsdetails aufklappen: Regelversion, Angreifer/Verteidiger, Kampfkraft, eingesetzte, verlorene und überlebende Einheiten je Typ sowie Beute. Die aktuelle FUR-2-Regel löst eine Runde auf; Mehrphasenberichte gehören nicht zum aktiven Regelstand.

### Transporte

Wähle auf der Karte einen anderen Kommandanten, dann im Missionsfenster **Rohstofftransport**. Wähle mindestens eine Einheit und mindestens eine Ressource. Die Fracht darf deine Vorräte und die Truppenkapazität nicht überschreiten. Sie beträgt `Anzahl Einheiten × (40 + 10 × Logistikstufe)`. Bei Ankunft wird die Fracht dem Zieldepot oder dessen Reserve-Lager gutgeschrieben; die Truppen treten den Rückweg an.

### Garnisonen

Eigene eroberte Außenposten können über die Karte verstärkt werden. Wähle im Missionsfenster **Garnison verstärken** und entsende Einheiten. Mit **Garnison zurückrufen** kannst du stationierte Einheiten zurückbeordern. Die Truppen sind während Marsch und Stationierung nicht für andere Missionen verfügbar. Ist ein Ziel beim Eintreffen nicht mehr dein Außenposten, kehren die Truppen stattdessen zurück.

## Fraktionen, Ereignisse, Saisons und Urlaubsmodus

### Fraktion

Im Weltbetrieb wählst du einmalig eine Fraktion. Die Auswahl kann danach nicht geändert werden:

- **Pioniere:** +10 Prozentpunkte Rohstoffproduktion.
- **Wächterbund:** Schildwall im PvP 40 % stärker.
- **Syndikat:** neutraler Rohstofftausch liefert 60 statt 50 Prozent.

Der Vorteil wird nach der verbindlichen Wahl aktiv.

### Live-Ereignisse und Saisons

Live-Ereignisse gewähren einen zeitlich begrenzten Produktionsbonus von 0–100 Prozentpunkten für 1–168 Stunden. Sie werden von der Spielleitung gestartet und im Weltbetrieb angezeigt.

Die Spielleitung kann in einer Saisonwelt einen Wettbewerb von 1–365 Tagen starten; pro Welt läuft höchstens eine Saison. Zum Abschluss speichert das Spiel die Rangliste, archiviert den Wettbewerb und schließt diese Welt für neue Beitritte. Die Kolonien werden nicht zurückgesetzt. Für die nächste Runde legt die Spielleitung eine neue Saisonwelt an; die Dauerwelt bleibt davon getrennt. Jede neu gestartete Saison speichert den FUR-2-Regeldatenkatalog samt Prüfsumme. Bei älteren Saisons ist ein später hinzugefügter Regelstand ausdrücklich als Referenz gekennzeichnet.

### Urlaubsmodus

Du kannst den Urlaubsmodus für mindestens 24 Stunden starten. Dafür dürfen in deiner Kolonie keine eigenen Aufträge und keine feindlichen Angriffe auf deine Kolonie laufen. Während des Urlaubs pausieren deine Produktion und eigene Spielaktionen; Nachrichten bleiben möglich und neue Spielerangriffe auf dich sind blockiert. Der Modus lässt sich nicht vor Ablauf der Mindestzeit beenden.

## Allianzen und Diplomatie

Du kannst eine Allianz gründen, wenn du noch keiner angehörst. Ein Tag besteht aus 3–8 Buchstaben oder Zahlen; der Allianzname ist 3–30 Zeichen lang. Die gründende Person wird Allianzleitung.

Mitgliederrollen:

- **Leitung:** Kann Offiziere ernennen oder zurückstufen, die Führung übertragen und Mitglieder verwalten.
- **Offizier:** Kann Kommandanten einladen, die Allianzbeschreibung ändern und einfache Mitglieder entfernen.
- **Mitglied:** Kann den Allianzchat verwenden und die Allianz verlassen.

Der Bereich **Allianz** in der Navigation zeigt deine Mitgliedschaft, Mitglieder und Einladungen. Du kannst eine Einladung annehmen oder ablehnen; Leitung und Offiziere können offene Einladungen zurücknehmen. Ohne Allianzmitgliedschaft kannst du dich bei einer bestehenden Allianz bewerben und eine offene Bewerbung zurücknehmen. Leitung und Offiziere sehen eingegangene Bewerbungen und können sie annehmen oder ablehnen. Einladung und Bewerbung für dieselbe Allianz können nicht gleichzeitig offen sein; nach Aufnahme werden weitere offene Einladungen und Bewerbungen des Spielers geschlossen. Leitung oder Offizier wählt außerdem ein Konto ohne Allianzmitgliedschaft aus und sendet eine Einladung. Die letzte Allianzleitung kann die Allianz nicht verlassen, bevor sie die Führung mit der Schaltfläche **Führung übertragen** an ein bestehendes Mitglied übergibt. Nach Bestätigung wirst du zum Offizier. Konfigurierbare Einzelrechte gibt es noch nicht. Pro Spieler kann nur eine Mitgliedschaft bestehen.

Offiziere und Leitung können bei anderen Allianzen einen **Nichtangriffspakt** anbieten, **Krieg** erklären oder den Status auf **Neutral** setzen. Ein angebotener Nichtangriffspakt wird erst wirksam, wenn die Gegenseite ihn annimmt. Der angenommene Pakt schützt Mitglieder vor Spielerangriffen beider Allianzen.

In der **Allianz-Pinnwand** können Leitung und Offiziere Ankündigungen mit Titel und Text veröffentlichen, bearbeiten oder archivieren. Aktuelle Mitglieder sehen Beiträge seitenweise in zeitlicher Reihenfolge; über **Ältere Beiträge laden** werden weitere Einträge nachgeholt. Archivierte Beiträge bleiben lesbar und sind in der Pinnwand gekennzeichnet. Ohne aktuelle Mitgliedschaft gibt die Spielschnittstelle keine Pinnwandbeiträge zurück.

## Nachrichten und Moderation

- **Weltkanal:** Nachrichten an alle Spieler der gemeinsamen Welt.
- **Allianzkanal:** Nur für Mitglieder der eigenen Allianz.
- **Postfach:** Private Nachrichten an einen ausgewählten Kommandanten. Empfänger werden aus der Spielerliste gewählt.

Nachrichten dürfen bis zu 2.000 Zeichen lang sein. Das Spiel zeigt bis zu 100 passende Nachrichten je Ansicht. Private Nachrichten sehen Absender und Empfänger; Moderation kann sie nicht beliebig als öffentliche Nachrichten darstellen.

Im Bereich **Nachrichten** findest du außerdem Kontakte und Blockliste. Sende einem Mitspieler aus der aktuellen Welt eine Kontaktanfrage; die andere Person muss sie annehmen. Offene Anfragen lassen sich zurücknehmen oder ablehnen. Kontakte kannst du entfernen. Zwischen blockierten Konten sind private Nachrichten gesperrt; du kannst Konten jederzeit entsperren. Beim Blockieren wird eine bestehende Freundschaft beendet. Deine Kontakte und Blockliste sind nur für dein Konto sichtbar. Moderation und das Ausblenden älterer Nachrichten bleiben davon unabhängig.

Im selben Bereich kannst du private **Notizen** zu Kartenkoordinaten und eigenen Berichten speichern. Notizen sind nur für dein Konto und die ausgewählte Welt sichtbar. Pro Koordinate oder Bericht gibt es eine bearbeitbare Notiz mit höchstens 500 Zeichen; nicht mehr angezeigte Berichte behalten ihre Notiz, bis du sie löschst.

Im Bereich **Freunde & Blockliste** kannst du einen eigenen Gefechtsbericht ausdrücklich mit deiner aktuellen Allianz teilen oder die Freigabe widerrufen. Mitglieder derselben Allianz mit einer Kolonie in der aktiven Welt sehen nur das Ergebnis jeder Runde sowie die Summen deiner Verluste und Überlebenden. Ziel- und Kontokennungen, Namen, Koordinaten, gegnerische Truppen, Beute, genauer Zeitpunkt und der Rohbericht werden nicht geteilt. Verlässt du die Allianz oder wirst entfernt, werden deine Freigaben widerrufen; austretende Mitglieder verlieren den Zugriff sofort.

Moderatoren und Administratoren können Spieler für eine begrenzte Zeit stummschalten oder eine Sperre aufheben. Administratoren können Spieler sperren und wieder entsperren, Wartung, Registrierung und PvP ein- oder ausschalten, Ereignisse und Saisons starten sowie fehlerhafte Weltaufträge erneut anstoßen. Moderatoren haben eingeschränkte Rechte und können Nachrichten ausblenden. Administrationsaktionen werden protokolliert. Moderierte Konten mit höheren Rollen sind über die Spieloberfläche vor normalen Spielersperren geschützt.

## Imperiumsmacht, Rangliste und Kampagnensieg

Die Imperiumsmacht ergibt sich aus:

```text
10 Punkte je Gebäudestufe
+ 20 Punkte je Technologiestufe
+ 100 Punkte je erobertem Außenposten
```

Truppen und Rohstoffvorräte geben keine direkten Ranglistenpunkte. Die Rangliste wird aus den gespeicherten Kolonie-, Forschungs- und Eroberungsständen erstellt.

Das Kampagnenziel ist die **Zitadelle des Kerns**. Baue deine Kommandozentrale auf Stufe 3, entwickle eine starke Armee und Taktik und erobere den Stufe-8-Posten. Der Sieg wird im Kommando angezeigt. Du kannst danach weiterbauen und zusätzliche Posten sichern.

## Kontosicherheit

- Anmeldung verwendet einen sicheren Passwort-Hash. Das Passwort wird nicht als Klartext gespeichert.
- Anmeldungen sind pro Netzwerk begrenzt; zusätzlich gelten höchstens fünf Versuche pro Konto und Netzwerk innerhalb einer Minute. Unbekannte Konten und falsche Passwörter erhalten dieselbe Fehlermeldung. Passwort-Wiederherstellungsanfragen verraten nicht, ob eine E-Mail-Adresse registriert ist.
- Sitzungen sind auf dem Server gespeichert und laufen nach sieben Tagen ab. Unter **Kontosicherheit → Angemeldete Geräte und Sitzungen** kannst du andere Sitzungen einzeln abmelden, alle anderen Sitzungen beenden oder dich auf allen Geräten abmelden. Eine Sitzung zeigt Startzeit und Browserkennung; Token und Netzwerkadressen werden nicht angezeigt. Bestehende Sitzungen ohne gespeicherte Gerätekennung erscheinen als „Gerät nicht angegeben“.
- In der Produktionsumgebung sind für die Registrierung mindestens 12 Passwortzeichen und eine gültige E-Mail notwendig. Die E-Mail muss bestätigt werden, bevor Spielaktionen möglich sind.
- Ein Passwortwechsel verlangt das aktuelle Passwort und bei aktivem Authenticator einen gültigen TOTP-Code. Danach wirst du auf allen Geräten abgemeldet und meldest dich mit dem neuen Passwort erneut an.
- Unter **Kontosicherheit** kannst du deine E-Mail nach erneuter Passwortprüfung ändern und einen Authenticator (TOTP) einrichten. Administratoren müssen den Authenticator im Livebetrieb aktiviert haben.
- Deinen Kommandantennamen kannst du unter **Kontosicherheit → Kommandantenname** ändern. Er muss 3–24 Buchstaben, Zahlen, Leerzeichen oder Bindestriche enthalten, muss global eindeutig sein und kann nur einmal innerhalb von 24 Stunden geändert werden. Die Änderung verlangt dein aktuelles Passwort und bei aktivem Authenticator einen frischen TOTP-Code. Deine Kolonien behalten ihre eigenen Namen; historische Berichte und Ereignisse bleiben unverändert.
- Über **Datenexport erstellen** lädst du nach erneuter Passwortprüfung und gegebenenfalls TOTP-Bestätigung ein JSON mit deinen Kontodaten, eigenen Kolonien, aktiven Sitzungsmetadaten, Missions- und Produktionsvorlagen sowie Kartenmarkierungen herunter. Sitzungstoken, Geheimnisse und fremde Kommunikation werden nicht exportiert.
- Bei aktivem Authenticator ist beim Anmelden ein zeitbasierter 6-stelliger Code erforderlich. Bereits verwendete Codes werden nicht erneut akzeptiert. Alternativ kannst du einen deiner einmaligen Recovery-Codes verwenden.
- Beim Aktivieren des Authenticators erhältst du zehn Recovery-Codes genau einmal angezeigt. Speichere sie an einem sicheren Ort außerhalb des Spiels. Der Server speichert nur Hashes; ein verbrauchter Code wird gelöscht und kann kein zweites Mal verwendet werden.
- Unter **Kontosicherheit → Recovery-Codes** kannst du mit aktuellem Passwort und gültigem Authenticator-Code einen neuen Satz ausstellen. Dadurch werden alle bisherigen Recovery-Codes sofort ungültig. Der neue Satz wird nur einmal angezeigt. Ohne Authenticator-Zugriff kannst du keine neuen Codes ausstellen.
- Über **Passwort vergessen / E-Mail bestätigen** kannst du einen Wiederherstellungs- oder Bestätigungscode verwenden. Codes sind einmalig und 30 Minuten gültig. Im Produktionsbetrieb müssen sie per E-Mail zugestellt werden; in der lokalen Betriebsart gibt es eine lokale Mailvorschau.
- Der Browser sendet den Sitzungsschutz automatisch bei geschützten Spielaktionen mit. Wenn ein anderes offenes Browserfenster eine neue Sitzung gestartet hat und ein Tab deshalb noch ein veraltetes Token hält, synchronisiert die Oberfläche den aktuellen Sitzungswert einmalig und wiederholt den abgewiesenen Befehl mit derselben Befehls-ID. Läuft die Anmeldung selbst ab, melde dich erneut an.

## Regionen und Gebietskontrolle

Die Weltkarte ist in 16 Regionen aufgeteilt: A1 bis D4, jeweils 16 × 16 Sektoren. Die Regionsübersicht befindet sich unter der Karte. Ein Spieler kontrolliert eine Region mit mindestens zwei und mehr als der Hälfte aller Außenposten darin. Eine Allianz kontrolliert sie nach derselben Schwelle, wenn die Außenposten ihren Mitgliedern zusammen gehören. Gleichstände und fehlende Mehrheiten ergeben keine Kontrolle. Die Allianzgrenze ist eine Gebietsanzeige und ändert nicht die individuelle Kontrolle oder deren Produktionsbonus. Jede individuell kontrollierte Region steigert die Rohstoffproduktion aller deiner Kolonien in dieser Welt um zwei Prozentpunkte, insgesamt höchstens 32 Prozentpunkte. Der Regionsbonus verändert den persönlichen Ranglistenscore nicht. Nicht vollständig erkundete Regionen zeigen keine globalen Besitzstände.

## Betriebsarten und Hinweise

### Lokal auf dem eigenen PC

Der lokale Start verwendet standardmäßig `127.0.0.1:8080` und SQLite in `data/empire.sqlite3`. Nur Programme auf demselben Rechner können zugreifen. Docker-Testbetrieb ist standardmäßig unter `127.0.0.1:8081` erreichbar und verwendet PostgreSQL. Browseradresse und Spielstand hängen daher vom verwendeten Startmodus ab.

### Gemeinsamer Server

Auf einem Server teilen sich registrierte Konten dieselbe Welt. Der Browser kann geschlossen bleiben; der separate Worker verarbeitet fällige Aufträge und E-Mails weiter. Für einen öffentlichen Betrieb sind eine gültige HTTPS-Adresse, erreichbare Domain, SMTP, Betreiberangaben, bestätigtes Admin-Konto, eingerichtetes TOTP und der erfolgreiche Betriebscheck erforderlich. Eine lokale Adresse ist nicht von anderen Geräten erreichbar.

### Grenzen und Daten

- Eine Kolonie kann höchstens 30 gleichzeitig laufende Missionen/Operationen, zehn offene Marktangebote und je eine Bau-, Forschungs- und Ausbildungswarteschlange haben.
- Weltkarte und Spielerliste zeigen die aktuell geladenen Welt- und Spieleransichten; in der API sind Listen auf 400 Spieler, 100 Angebote, 100 Einladungen, 100 Nachrichten je Ansicht und 100 Audit-/Berichtszeilen je relevanter Ansicht begrenzt.
- Das Spiel enthält keine Echtgeldkäufe, externen Chatdienste, plattformübergreifenden Konten oder automatische Synchronisierung zwischen SQLite und PostgreSQL.
- Serverbetreiber können Weltregeln, Registrierung, PvP und Wartung steuern. Bei einem Testserver können einzelne Funktionen daher zeitweise deaktiviert sein.

## Begriffe

| Begriff | Bedeutung |
|---|---|
| **Auftrag / Warteschlange** | Ein serverseitig laufender Bau-, Forschungs-, Ausbildungs- oder Missionsschritt. |
| **Anmarsch / Rückmarsch** | Hinweg zum Missionsziel beziehungsweise Rückkehr überlebender Truppen samt Beute. |
| **Garnison** | Auf einem eigenen eroberten Außenposten stationierte Truppen. |
| **Neulingsschutz** | PvP-Schutz während der ersten Stunde nach der Kontoerstellung. Beide Seiten eines Angriffs müssen die Stunde überschritten haben. |
| **Reserve-Lager** | Sicherer Vorrat für Lieferungen oder Erstattungen, die nicht ins Depot passen. |
| **TOTP** | Einmalcode aus einer Authenticator-App, der sich zeitbasiert ändert. |
| **FUR-2** | Aktueller Regeldatenkatalog und Kampfregelversion. Saison-Snapshots erfassen den JSON-Katalog, nicht jede fest im Simulationscode enthaltene Formel. |



## Öffentliches Kommandantenprofil

## Commander-Fortschritt und Doktrinen (FUR-3-Entwurf)

In einer Welt mit ausdrücklich aktivierter Heldenverwaltung findest du **Deinen Commander** in der Übersicht. Ein neuer Commander beginnt auf Stufe 1 und erhält Erfahrung erst, wenn ein nach der Aktivierung gestarteter Auftrag abgeschlossen ist: Überfall/Angriff 12 XP, Expedition 8 XP, Aufklärung 4 XP. Die Stufenkosten steigen: 100 XP für Stufe 2, danach je Stufe 100 XP mehr. Bei Stufe 20 (19.000 XP) ist Schluss. Jeder Levelaufstieg gibt einen Skillpunkt; ein Attribut kann höchstens Stufe 10 erreichen.

**Wirtschaft** ist mit HERO-1 verfügbar: Jeder Punkt gibt +2 Prozentpunkte Rohstoffproduktion, bis höchstens +20 %. Die Weltleitung kann zusätzlich die Regel **FUR-3-HERO-2 Commander-Doktrinen** aktivieren. Dann werden Militär (+2 % Terra-FUR-3-Kampfschaden/Punkt, max. +20 %), Aufklärung (+10 % PvP-Berichtsdauer/Punkt, max. +100 %) und Flotte/Kommando (+1 gleichzeitiger Terra-Auftragsplatz/Punkt, max. +5) freigeschaltet. Kampf- und Aufklärungsboni werden beim Missionsstart festgehalten. FUR-2-Kampfregeln ändern sich nicht. HERO-1 und HERO-2 müssen beide für die Welt eingeschaltet sein. Alle Werte sind vorläufig und noch nicht balanceabgenommen. Die Spielleitung kann außerdem **FUR-3-HERO-3 Attribut-Reset** einschalten. Er kostet 250 Holz, 250 Stein und 250 Erz von deiner aktiven Kolonie und hat sieben Tage Abklingzeit je Konto und Welt. Er setzt die verteilten Attribute zurück, behält aber XP und XP-Buchungen; dadurch werden nur zuvor verdiente Skillpunkte wieder frei. Der Reset ist standardmäßig aus; auch diese Startwerte sind noch nicht balanceabgenommen.

In **Kommunikation → Freunde & Blockliste** kannst du ein Profil freiwillig freigeben, einen Titel wählen und bis zu drei kosmetische Abzeichen markieren. Neue Profile sind privat. In **Rangliste → Profil ansehen** siehst du freigegebene Profile derselben aktiven Welt. Rang und Punktzahl sind schon unabhängig davon in der Rangliste sichtbar. Die Profilkarte zeigt keine E-Mail oder Sicherheitsdaten, Koordinaten, Kolonien, Bestände, Truppen, Allianz, Kontakte, Nachrichten oder Berichte. Abzeichen sind frei gewählte Anzeigeelemente, keine Leistungsnachweise. Du kannst die Profilfreigabe jederzeit wieder auf privat setzen.


### FUR-3-Fertigung (Entwurf)

Die Fertigung läuft nur, wenn die Spielleitung für die aktive Welt ausdrücklich FUR-CRAFTING-1 eingestellt hat; Standard ist FUR-2 ohne Fertigung. Im Bereich **Handel** kannst du Materialien und Gegenstände einsehen sowie verfügbare Rezepte starten. Komponentenpressen benötigt HQ 1 und 300 Sekunden je Durchlauf (100 Erz, 20 Legierungen, 8 Schaltkreise → 4 Fertigungskomponenten). Das Feldreparaturkit benötigt HQ 2 und 600 Sekunden (3 Fertigungskomponenten, 6 Textilien, 10 Rationen → 1 Kit). Ein Auftrag darf bis zu zehn Durchläufe enthalten; maximal fünf Aufträge können in der Kolonie laufen. Vor Abschluss lässt sich der Auftrag vollständig abbrechen. Lagerüberlauf wird ins Reservelager gelegt. Vorläufige Werte und FUR-2 bleiben unverändert.

### FUR-3-Gegenstandsrecycling (Entwurf)

In einer Welt mit aktiviertem FUR-CRAFTING-1 kannst du Feldreparaturkits unter **Handel → Gegenstandsrecycling** zerlegen. Ein Kit gibt zwei Fertigungskomponenten und drei Textilien zurück. Die Herstellung verbraucht drei Komponenten und sechs Textilien; Recycling ersetzt also nur einen Teil der Zutaten und ist kein Gewinnkreislauf. Bis zu 100 Kits lassen sich je Befehl zerlegen. Volle Lager legen Übermengen ins jeweilige Reservelager. Andere Gegenstände können derzeit nicht recycelt werden. Das Kit besitzt noch keine Reparaturaktion. Die Rückgabemengen sind technische Entwurfswerte und noch nicht balanciert; FUR-2 bleibt unverändert.

## FUR-3-Kampagnenkosmetik

Wer im Kontaktbereich das Kommandantenprofil öffnet, kann dort erspielte Titel, Skins und Banner ausrüsten. Mobilmachung schaltet den Skin Aschenwacht frei; die Expansionsdirektive den Titel Grenzgründer und das Banner Morgenrot der Grenze; die Zitadellen-Direktive Titel, Skin und Banner der Zitadellenwacht. Die Auswahl ist kontogebunden und rein kosmetisch. Das öffentliche Spielerprofil bleibt standardmäßig privat; erst nach Freigabe zeigt es die ausgewählte Kosmetik. Die Titel und Banner werden derzeit als Text dargestellt. FUR-3-COSMETIC-REWARDS-1 ist ein vorläufiger Entwurf; FUR-2 bleibt unverändert.

## FUR-3-Kampagnenkosmetik

Wer im Kontaktbereich das Kommandantenprofil öffnet, kann dort erspielte Titel, Skins und Banner ausrüsten. Mobilmachung schaltet den Skin Aschenwacht frei; die Expansionsdirektive den Titel Grenzgründer und das Banner Morgenrot der Grenze; die Zitadellen-Direktive Titel, Skin und Banner der Zitadellenwacht. Die Auswahl ist kontogebunden und rein kosmetisch. Das öffentliche Spielerprofil bleibt standardmäßig privat; erst nach Freigabe zeigt es die ausgewählte Kosmetik. Die Titel und Banner werden derzeit als Text dargestellt. FUR-3-COSMETIC-REWARDS-1 ist ein vorläufiger Entwurf; FUR-2 bleibt unverändert.

### Bau-, Forschungs- und Rekrutierungsvorlagen

Im Bereich Außenposten kannst du Baupläne und in Forschung Laborvorlagen speichern; unter Streitkräfte sind Rekrutierungsvorlagen verfügbar. Sie speichern einen einzelnen Auftrag beziehungsweise Einheitentyp und Anzahl, keine Rohstoffe oder Reservierungen. Beim Einreihen prüft der Server Eigentum an der Vorlage, aktive Welt und Kolonie, Voraussetzungen, Ressourcen, Weltregel und Warteschlange erneut. Bau- und Forschungsaufträge verwenden immer Anzahl 1, Rekrutierung 1 bis 100 je Vorlage. Namen sind je Konto eindeutig; pro Konto gelten zehn Vorlagen je Vorlagefamilie. Wiederholte Einreihung mit demselben Befehlsschlüssel erzeugt keinen doppelten Auftrag. Vorlagen können in eigenen Welten wiederverwendet werden, aber die dortigen Regeln entscheiden, ob der Auftrag aktuell zulässig ist.
