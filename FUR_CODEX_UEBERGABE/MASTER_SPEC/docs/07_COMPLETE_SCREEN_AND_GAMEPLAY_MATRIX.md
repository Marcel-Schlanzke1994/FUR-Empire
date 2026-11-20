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
