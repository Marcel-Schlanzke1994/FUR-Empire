# FUR Empire – vollständige Spielanleitung

Diese Anleitung beschreibt die Funktionen, die im aktuellen FUR-Empire-Spiel vorhanden sind. Sie gilt für die Browseroberfläche „Genesis“ und die Spielregeln FUR-2. Die Spielleitung kann einzelne Funktionen wie Registrierung, PvP oder Wartung serverseitig ein- und ausschalten.

## Schnellstart

1. Öffne die Adresse, die dir der Betreiber gegeben hat. Auf dem Entwicklungsrechner ist das lokal `http://127.0.0.1:8080`; der Docker-Testbetrieb verwendet `http://127.0.0.1:8081`. Eine lokale Adresse ist nur auf demselben PC erreichbar.
2. Wähle **Neu hier? Imperium gründen**, gib einen Kommandantennamen und ein Passwort ein und melde dich an. Namen sind 3–24 Zeichen lang. Im lokalen Modus gilt eine Mindestpasswortlänge von 8 Zeichen; im Produktionsmodus sind mindestens 12 Zeichen und eine gültige E-Mail erforderlich.
3. Baue deine Wirtschaft aus, hole fertige Direktivenbelohnungen ab und stelle Truppen auf.
4. Wähle auf der Weltkarte einen Außenposten, prüfe die Verteidigung und entsende eine Mission. Die Weltaufträge laufen serverseitig weiter, auch wenn du den Browser schließt.

Dein Konto und die gemeinsame Welt bleiben auf dem jeweiligen Server gespeichert. SQLite im lokalen Modus und PostgreSQL im Docker-/Produktionsbetrieb sind getrennte Spielwelten; ein lokaler Spielstand wird nicht automatisch auf den Server übertragen.

## Oberfläche und Bereiche

| Bereich | Was du dort tun kannst |
|---|---|
| **Kommando** | Produktion, Imperiumsmacht, Garnison, Außenposten, Auftragswarteschlange und Direktiven sehen. Erfüllte Direktivenbelohnungen hier abholen. |
| **Außenposten** | Gebäude ansehen und Ausbauaufträge starten. |
| **Forschung** | Logistik, Taktik und Ingenieurswesen erforschen. Ein Forschungslabor ist erforderlich. |
| **Streitkräfte** | Ranger, Wächter und Sturmmechs ausbilden. |
| **Weltkarte** | In der 64 × 64-Welt navigieren, neutrale Posten und Kommandanten auswählen und Missionen starten. Das Raster zeigt jeweils bis zu 20 × 20 Sektoren. |
| **Handel** | Holz, Stein und Erz an der neutralen Rohstoffbörse sofort tauschen. |
| **Berichte** | Kampf-, Missions-, Transport- und Kolonieereignisse nachlesen. |
| **Rangliste** | Imperiumsmacht aller Kommandanten vergleichen. |
| **Spielanleitung** | Kurze Einstiegshilfe im Spiel. Diese Datei enthält die ausführlichere Fassung. |
| **Allianz** | Allianzen gründen oder Einladungen annehmen, Mitglieder verwalten und Diplomatie betreiben. |
| **Nachrichten** | Weltkanal, Allianzkanal und private Nachrichten verwenden. |
| **Spielermarkt** | Waren gegen andere Rohstoffe anbieten, Angebote annehmen oder zurückziehen. |
| **Weltbetrieb** | Eine Fraktion wählen, Live-Ereignisse und Saisons ansehen und den Urlaubsmodus steuern. |
| **Kontosicherheit** | E-Mail bestätigen oder ändern, Wiederherstellung und Authenticator verwalten, lokale Testmails ansehen (nur lokale Betriebsart). |
| **Spielleitung** | Moderation und Weltbetrieb verwalten. Der Bereich wird nur Moderatoren und Administratoren angezeigt. |

Die Oberfläche aktualisiert den Spielstand regelmäßig. Sie ist nur die Bedienoberfläche: Ressourcen, Kämpfe, Berechtigungen, Aufträge und Buchungen werden auf dem Server geprüft und verarbeitet.

## Kolonie, Rohstoffe und Produktion

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

Alle Gebäude können bis Stufe 10 ausgebaut werden. Die Kosten eines Ausbaus betragen die Basiskosten multipliziert mit der Zielstufe. Pro Kolonie läuft jeweils höchstens ein Bauauftrag gleichzeitig.

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

Pro Kolonie läuft höchstens eine Forschung gleichzeitig. Eine Technologie kostet ihre Basiskosten multipliziert mit der Zielstufe und benötigt `12 × Zielstufe` Sekunden.

| Technologie | Effekt je Stufe | Basiskosten (Holz / Stein / Erz) |
|---|---|---:|
| Militärtaktik | +15 % Angriffskraft und Truppenverteidigung. | 70 / 90 / 150 |
| Logistik | +10 Beutekapazität je Einheit und Stufe. | 130 / 70 / 100 |
| Ingenieurswesen | +15 Prozentpunkte Rohstoffproduktion. | 100 / 140 / 90 |

### Truppen

Ausbildung erfordert die angegebene Kaserne-Stufe. Eine Einheit kostet die aufgeführten Rohstoffe; ein Ausbildungsauftrag darf 1–100 Einheiten enthalten. Die Ausbildungszeit je Einheit ist ebenfalls angegeben. Pro Kolonie ist jeweils nur ein Ausbildungsauftrag gleichzeitig aktiv.

| Einheit | Kaserne ab | Kampfkraft | Ausbildungszeit | Kosten je Einheit (Holz / Stein / Erz) |
|---|---:|---:|---:|---:|
| Ranger | 1 | 12 | 2 Sekunden | 35 / 15 / 25 |
| Wächter | 2 | 28 | 4 Sekunden | 50 / 40 / 60 |
| Sturmmech | 3 | 70 | 7 Sekunden | 100 / 90 / 140 |

## Aufträge und Direktiven

Es gibt fünf serverseitige Direktiven. Sie belohnen den Ausbau der drei Rohstoffgebäude auf Stufe 2 (400 je Rohstoff), den Bau einer Kaserne (300 je Rohstoff), die erste erforschte Technologie (500 je Rohstoff), die erste Eroberung (900 je Rohstoff) und die Eroberung der Zitadelle (2.000 je Rohstoff). Jede Direktive kann nur einmal abgeholt werden. Über dem Depotlimit liegende Belohnungen landen im Reserve-Lager.

Neue Missions- und Garnisonsaufträge werden ab 30 bereits gespeicherten laufenden Aufträgen blockiert. Bau, Forschung und Ausbildung besitzen je eine separate Einzelwarteschlange und können parallel laufen. Die Oberfläche zeigt verbleibende Zeit und Auftragstyp.

## Weltkarte, Überfälle und Eroberungen

Die gemeinsame Welt umfasst **64 × 64 = 4.096 Sektoren** und **104 neutrale Außenposten**. Die Sektoren werden in Ausschnitten angezeigt; mit den Richtungsbuttons kannst du die Karte verschieben. In der Übersicht rechts kannst du jeden Außenposten direkt auswählen. Andere Kommandanten erscheinen in einer separaten Liste.

Neutrale Außenposten haben Stufen 1–8. Die Verteidigung beträgt `55 × Stufe²` plus die Kampfkraft einer vorhandenen Garnison. Die Zitadelle des Kerns ist das Stufe-8-Kampagnenziel.

Im Missionsfenster kannst du Truppen auswählen und die angezeigte Kampfkraft mit der Verteidigung vergleichen. Die Kampfkraft deiner Armee ist die Summe aus Kampfkraft je Einheit, multipliziert mit `100 + 15 × Taktikstufe` Prozent. Zum Sieg muss der Angriff **höher** als die Verteidigung sein.

- Bei einer Niederlage gehen die entsandten Einheiten verloren.
- Auch ein Sieg kostet mindestens 10 % der angreifenden Truppen; bei starker Verteidigung können die Verluste höher ausfallen.
- Die Verluste der Einheitentypen werden auf ganze Einheiten aufgerundet.
- Überlebende können Beute tragen. Die Kapazität beträgt `überlebende Einheiten × (40 + 10 × Logistikstufe)`. Bei neutralen Posten wird die Beute auf Holz, Stein und Erz verteilt und durch vorhandene Bestände sowie Kapazität begrenzt.
- Eine Reise dauert mindestens 5 Sekunden und hängt von der Entfernung ab. Nach dem Angriff startet ein Rückmarsch; Überlebende und Beute werden bei der Rückkehr gutgeschrieben.
- Die Bestände neutraler Außenposten regenerieren sich nicht.
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

Spielerangriffe sind nur möglich, wenn die Spielleitung PvP aktiviert hat. Beide beteiligten Konten müssen mindestens eine Stunde bestehen. Allianzmitglieder können einander nicht angreifen. Ein angenommener Nichtangriffspakt schützt die Mitglieder der beteiligten Allianzen. Spieler im Urlaubsmodus sind geschützt. Die Stärke der gegnerischen Verteidigung wird im Missionsfenster angezeigt.

Der Schildwall zählt zur Spielerverteidigung; beim Wächterbund ist er im PvP 40 % stärker. Kämpfe können Truppenverluste, Ressourcendiebstahl und Berichte verursachen. Kampf, Ressourcenbuchung und Bericht werden serverseitig gemeinsam verarbeitet.

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

Die Spielleitung kann einen Saisonwettbewerb von 1–365 Tagen starten; gleichzeitig läuft höchstens eine Saison. Zum Abschluss speichert das Spiel die Rangliste und archiviert die Saison. Saisonabschlüsse setzen die Kolonien nicht zurück. Jede neu gestartete Saison speichert den FUR-2-Regeldatenkatalog samt Prüfsumme. Bei älteren Saisons ist ein später hinzugefügter Regelstand ausdrücklich als Referenz gekennzeichnet.

### Urlaubsmodus

Du kannst den Urlaubsmodus für mindestens 24 Stunden starten. Dafür dürfen in deiner Kolonie keine eigenen Aufträge und keine feindlichen Angriffe auf deine Kolonie laufen. Während des Urlaubs pausieren deine Produktion und eigene Spielaktionen; Nachrichten bleiben möglich und neue Spielerangriffe auf dich sind blockiert. Der Modus lässt sich nicht vor Ablauf der Mindestzeit beenden.

## Allianzen und Diplomatie

Du kannst eine Allianz gründen, wenn du noch keiner angehörst. Ein Tag besteht aus 3–8 Buchstaben oder Zahlen; der Allianzname ist 3–30 Zeichen lang. Die gründende Person wird Allianzleitung.

Mitgliederrollen:

- **Leitung:** Kann Offiziere ernennen oder zurückstufen, die Führung übertragen und Mitglieder verwalten.
- **Offizier:** Kann Kommandanten einladen, die Allianzbeschreibung ändern und einfache Mitglieder entfernen.
- **Mitglied:** Kann den Allianzchat verwenden und die Allianz verlassen.

Die letzte Allianzleitung kann die Allianz nicht verlassen, bevor sie die Führung übertragen hat. Einladungen erscheinen im Allianzbereich und müssen angenommen werden. Pro Spieler kann nur eine Mitgliedschaft bestehen.

Offiziere und Leitung können bei anderen Allianzen einen **Nichtangriffspakt** anbieten, **Krieg** erklären oder den Status auf **Neutral** setzen. Ein angebotener Nichtangriffspakt wird erst wirksam, wenn die Gegenseite ihn annimmt. Der angenommene Pakt schützt Mitglieder vor Spielerangriffen beider Allianzen.

## Nachrichten und Moderation

- **Weltkanal:** Nachrichten an alle Spieler der gemeinsamen Welt.
- **Allianzkanal:** Nur für Mitglieder der eigenen Allianz.
- **Postfach:** Private Nachrichten an einen ausgewählten Kommandanten. Empfänger werden aus der Spielerliste gewählt.

Nachrichten dürfen bis zu 2.000 Zeichen lang sein. Das Spiel zeigt bis zu 100 passende Nachrichten je Ansicht. Private Nachrichten sehen Absender und Empfänger; Moderation kann sie nicht beliebig als öffentliche Nachrichten darstellen.

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
- Sitzungen sind auf dem Server gespeichert und laufen nach sieben Tagen ab. Abmelden beendet die Sitzung.
- In der Produktionsumgebung sind für die Registrierung mindestens 12 Passwortzeichen und eine gültige E-Mail notwendig. Die E-Mail muss bestätigt werden, bevor Spielaktionen möglich sind.
- Unter **Kontosicherheit** kannst du deine E-Mail nach erneuter Passwortprüfung ändern und einen Authenticator (TOTP) einrichten. Administratoren müssen den Authenticator im Livebetrieb aktiviert haben.
- Bei aktivem Authenticator ist beim Anmelden ein zeitbasierter 6-stelliger Code erforderlich. Bereits verwendete Codes werden nicht erneut akzeptiert.
- Über **Passwort vergessen / E-Mail bestätigen** kannst du einen Wiederherstellungs- oder Bestätigungscode verwenden. Codes sind einmalig und 30 Minuten gültig. Im Produktionsbetrieb müssen sie per E-Mail zugestellt werden; in der lokalen Betriebsart gibt es eine lokale Mailvorschau.
- Bei Problemen mit Spielbefehlen zuerst die Seite neu laden. Der Browser sendet den Sitzungsschutz automatisch bei geschützten Spielaktionen mit. Wenn die Anmeldung abgelaufen ist, melde dich erneut an.

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

