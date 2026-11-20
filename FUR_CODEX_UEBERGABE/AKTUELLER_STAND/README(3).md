# FUR EMPIRE · Genesis

Eigenständiges Browser-Strategiespiel mit persistenter Welt, Koloniewirtschaft, Außenposten, PvE-Kampagne und Multiplayer-Systemen. Die abgeschlossenen Referenzprojekte in `Neuer Ordner/` dienen als Architektur- und Konzeptmaterial; ihre Fremdgrafiken und lizenzgebundenen Spielimplementierungen werden nicht ins FUR-Spiel kopiert.

## Spielen unter Windows

**`Start-FUR-Empire.cmd` doppelklicken.** Das Fenster offen lassen und im Browser **http://127.0.0.1:8080** öffnen. Beim ersten Start „Neu hier? Imperium gründen“ wählen, einen Namen und ein Passwort mit mindestens acht Zeichen eingeben.

Python 3.11 oder neuer ist erforderlich. Beim ersten Start werden fehlende Python-Pakete installiert; dafür wird Internet benötigt. Danach benötigt das Spiel keine Internetverbindung. Die vorbereitete `.venv` auf diesem Rechner enthält die Abhängigkeiten bereits.

Stoppen: im Serverfenster Strg+C. Erneut starten: dieselbe CMD-Datei doppelklicken. Fortschritt und Konten bleiben erhalten. Standardadresse ausschließlich `127.0.0.1`, kein öffentlicher Server.

Der während der Einrichtung gestartete Hintergrundserver lässt sich mit `Stop-FUR-Empire.cmd` stoppen. Das Skript prüft den tatsächlichen Listener an Port 8080 und beendet ihn nur, wenn Interpreterpfad und FUR-Startbefehl passen.

Für einen isolierten lokalen Mehrspieler-Test kann eine separate Demowelt in einer neuen SQLite-Datei erzeugt werden. Der Befehl verweigert vorhandene Datenbanken und den Standard-Spielstand; die zufälligen Demo-Passwörter werden nur beim Erstellen im Terminal angezeigt:

```powershell
New-Item -ItemType Directory -Force data | Out-Null
.\.venv\Scripts\python.exe -m fur_empire.manage seed-demo --database data/demo-world.sqlite3 --accounts 3
$env:FUR_DB = (Resolve-Path data/demo-world.sqlite3).Path
.\.venv\Scripts\python.exe -m uvicorn fur_empire.api:app --host 127.0.0.1 --port 8082
```

Das Demo-Spiel läuft unter **http://127.0.0.1:8082** und nutzt ausschließlich diese separate SQLite-Datei. Für spätere Starts dieselbe Datenbank mit `FUR_DB` auswählen; den Seed-Befehl nicht erneut ausführen.

## Privates Docker-Staging

Für einen produktionsnahen Test mit PostgreSQL, getrenntem Worker, HTTPS über ein lokales Caddy-Zertifikat und Mailpit als SMTP-Fänger PowerShell im Projektordner öffnen und einmal starten:

```powershell
.\Start-FUR-Empire-Staging.ps1
```

Beim ersten Start erzeugt das Skript drei Testkonten mit zufälligen Passwörtern und zeigt sie einmalig im Terminal. Staging-Spiel: **https://localhost:8443**; aufgefangene Bestätigungsmails: **http://127.0.0.1:8025**. Nur Caddy veröffentlicht Testports, ausschließlich auf Loopback; App, Worker, PostgreSQL, SMTP und Mailpit sind intern. Staging verwendet ein separates Compose-Projekt, interne Netze, PostgreSQL-Volume und Secret-Dateien. Es sendet keine E-Mails nach außen. Browser können beim ersten Aufruf dem lokalen Caddy-Zertifikat noch nicht vertrauen.

Stoppen ohne Löschen der Staging-Daten:

```powershell
.\Stop-FUR-Empire-Staging.ps1
```

## Spielumfang

- **Regionskontrolle:** Die 64 × 64 Karte ist in 16 Regionen A1–D4 mit je 16 × 16 Sektoren geteilt. Kontrolle verlangt mindestens zwei und mehr als die Hälfte der Außenposten einer Region; pro kontrollierter Region erhalten alle eigenen Kolonien dieser Welt +2 Prozentpunkte Produktion, höchstens +32 Prozentpunkte insgesamt.

- Konten mit Argon2-Anmeldung, Sitzungsschutz, Wiederherstellung, optionalem Authenticator und Verwaltung angemeldeter Geräte/Sitzungen
- Kontosicherheit mit 24-Stunden-Cooldown für eindeutig vergebene Kommandantennamen und reauthentifiziertem, CSRF-geschütztem Export freigegebener eigener Kontodaten
- Persistente 64 × 64 Welten mit eigenem Seed, Gelände und Außenpostenbestand; die Karte führt pro Spieler unbekannte, veraltete und aktuelle Sektoren. Eigene Kolonien sehen 8, eigene eroberte Außenposten 2 Sektoren weit. Unbekanntes Gelände und versteckte Ziele bleiben serverseitig verborgen. Genesis startet mit 104 Zielen. Neutrale Außenposten erneuern ihre Vorräte automatisch bis zur Stufengrenze; eroberte Ziele regenerieren sich nicht. Die Spielleitung kann Welten mit 8–300 Außenposten anlegen, umbenennen und den Beitritt öffnen oder schließen. Spieler können beitreten und zwischen ihren Welten wechseln; Kolonien, Karten, Reisen, Aufträge, Markt und Weltchat sind weltgebunden.
- Acht Gebäude, drei Technologien, drei Truppentypen, Produktion, Depot und Reservelager; Terrainwerte für Bewegung, Erzeugung, Produktion und Verteidigung stehen im validierten FUR-2-Regelkatalog
- Getrennte Bau-, Forschungs- und Ausbildungsqueues je Kolonie; bis zu fünf Bau-/Forschungsstufen lassen sich planen und umsortieren, Abbruch erstattet die ungenutzte Zeit anteilig. Main und privates Loopback-Staging laufen aktuell auf Schema 14. Dazu Überfälle, Rückmärsche, Beute, Eroberungen und Ressourcenversorgung zwischen eigenen Basen
- PvP-Angriffe, Truppentransporte, stationierte Garnisonen und Ranger-Aufklärung gegen Spieler (Gebäudebericht mit 1–2 Rangern, Militärbericht ab 3; nur für den Späher sichtbar und eine Stunde aktuell)
- Deterministische, serverseitige Gefechtsprobe für bekannte neutrale Außenposten und Spielerziele mit aktuellem Stufe-2-Aufklärungsbericht; sie ändert keinen Spielstand und zeigt keine nicht aufgeklärten Ressourcen
- Kontogebundene Missionsvorlagen und Bau-/Forschungs-/Rekrutierungspresets; Produktionsvorlagen werden beim Einreihen erneut gegen die aktiven Serverregeln, Rohstoffe und Warteschlangen geprüft; neutrale, bekannte Sektoren können außerdem mit deterministischen FUR-3-Expeditionen erkundet werden
- Allianzen mit Einladungen, Rollen, Allianzchat, ausgehandelten Nichtangriffspakten, öffentlichem Diplomatieprotokoll und Trägerlieferungen an die Heimatkolonie verbündeter Mitglieder derselben Welt; Lieferungen können vor Ankunft storniert werden
- Moderierte Allianz-Pinnwand: Leitung und Offiziere veröffentlichen, bearbeiten und archivieren Ankündigungen; aktuelle Mitglieder sehen den chronologisch sortierten Verlauf
- Allianzforum mit Themen und Antworten, eigener Bearbeitung, Archivierung durch Leitung/Offiziere und begründeten vertraulichen Meldungen; ältere Themen lassen sich nachladen. Inhalte werden escaped, Nichtmitglieder erhalten keine Forumsdaten.
- Weltchat, geschützte Privatnachrichten und Spielermarkt mit hinterlegten Waren
- Zustimmungsbasierte Kontaktanfragen, private Kontaktlisten und beidseitig wirksame Blocklisten; bestehende Moderation und alte Nachrichten bleiben separat geregelt
- Weltgebundene private Notizen zu Koordinaten und eigenen Berichten; pro Ziel eine bearbeitbare Notiz mit bis zu 500 Zeichen
- Anonymisierter 30-Tage-Preisverlauf abgeschlossener Weltmarktgeschäfte, stündlich aggregiert; keine rückwirkende Historie
- Fünf Direktiven, Sieg durch Zitadelleneroberung, Fraktionen, Live-Ereignisse und Saisons
- Verwaltende Moderation, Betreiberkonfiguration, Datenbank-Worker und Betriebswerkzeuge

Ein lokal gestarteter Server ist ausschließlich unter `127.0.0.1` erreichbar und nutzt SQLite. Docker verwendet getrennt davon PostgreSQL; der lokale SQLite-Spielstand wird nicht automatisch importiert. Docker-Geheimnisse liegen in `.secrets/` und dürfen nicht ins Repository gelangen.

## Docker-Testbetrieb auf diesem Rechner

Docker Desktop muss laufen. Beim allerersten Start aus PowerShell im Projektordner zuerst die drei Datenbank-/SMTP-Secrets erzeugen; diesen Schritt **nicht** erneut ausführen, sobald ein PostgreSQL-Datenbankvolume initialisiert wurde:

```powershell
New-Item -ItemType Directory -Force .secrets | Out-Null
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
  foreach ($name in @('db_password', 'db_admin_password', 'smtp_password')) {
    $bytes = New-Object byte[] 32
    $rng.GetBytes($bytes)
    $value = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path '.secrets' $name), $value)
  }
} finally {
  $rng.Dispose()
}
```

Danach App, PostgreSQL und Worker starten:

```powershell
docker compose up --build -d app worker db
docker compose ps
Invoke-RestMethod http://127.0.0.1:8081/api/v1/ready
```

Das Spiel ist lokal unter **http://127.0.0.1:8081** erreichbar. Standardmäßig bindet Docker ausschließlich an Loopback. Für einen ausdrücklich gewünschten, zeitlich begrenzten Test im privaten LAN kann in `.env` die Bindung auf `APP_BIND_ADDRESS=0.0.0.0` und `PUBLIC_ORIGIN=http://<LAN-IP-dieses-PCs>:8081` gesetzt werden; danach den App-Dienst mit `docker compose up -d app` neu erstellen. Die App akzeptiert dann nur den in `PUBLIC_ORIGIN` festgelegten Host. Falls Windows die Verbindung blockiert, muss ein Betreiber als Administrator eine auf das private Profil und das lokale Subnetz begrenzte Firewallregel einrichten:

```powershell
New-NetFirewallRule -DisplayName "FUR Empire LAN-Test" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow -Profile Private -RemoteAddress LocalSubnet
```

Diese HTTP-LAN-Option ist nur für ein kontrolliertes privates Testnetz bestimmt, nicht für Internetzugriff. `docker compose stop` hält die Dienste an; `docker compose start` fährt sie mit denselben Daten wieder hoch. Das benannte PostgreSQL-Volume enthält den Docker-Spielstand. `docker compose down -v` löscht dieses Volume und damit die PostgreSQL-Datenbank; vor Wartungsarbeiten ein Backup anlegen:

```powershell
docker compose --profile ops run --rm backup
```

Für ein öffentliches Produktionsdeployment müssen vor dem Start über das `public`-Compose-Profil `FUR_ENV=production`, eine echte `PUBLIC_ORIGIN`-HTTPS-Domain, SMTP- und Betreiberangaben gesetzt werden; die Domain muss auf diesen Rechner zeigen, Ports 80/443 müssen frei und aus dem Internet erreichbar sein, und `ACME_EMAIL` muss eine gültige Adresse enthalten. Ein lokaler Docker-Start ist nicht für externe Spieler freigegeben.

### Betreiberkonto

Es wird absichtlich kein voreingestelltes Administratorkonto erzeugt. Für einen moderierten Test legt der Betreiber sein Konto interaktiv an; der Befehl fragt das Passwort zweimal direkt im Terminal ab:

```powershell
docker compose exec app python -m fur_empire.manage create-admin --name "<Name>" --email "<E-Mail>"
```

Danach im Spiel anmelden, unter „Kontosicherheit“ den E-Mail-Code bestätigen und einen Authenticator einrichten. Im lokalen Docker-Modus kann der Betreiber die ausgehende Testmail dort über „Lokale Mailvorschau öffnen“ abrufen. Im Produktionsmodus ist diese Vorschau deaktiviert und eine funktionierende SMTP-Zustellung erforderlich. Der Betreiber sollte vor Spielerbeitritt den strikten Betriebscheck mit `docker compose exec app python -m fur_empire.manage readiness` ausführen; er muss für eine Produktionsfreigabe mit Exitcode 0 enden.

## Einstieg

1. Rohstoffgebäude auf Stufe 2 ausbauen und Belohnung unter „Kommando“ abholen.
2. Kaserne und Labor bauen, Ranger rekrutieren und Taktik erforschen.
3. Auf der Karte einen schwachen Außenposten auswählen, Kampfkraft prüfen und überfallen.
4. Kommandozentrale auf Stufe 3 ausbauen, Posten erobern.
5. Wirtschaft und Armee stärken, dann die Zitadelle des Kerns erobern.

Ein Auftrag dauert Sekunden und wird serverseitig abgearbeitet. Der Browser fragt den Spielstand regelmäßig ab; der Worker verarbeitet Multiplayeraufträge auch bei geschlossenem Browser. Der neutrale Tausch liefert 50 Prozent des Einsatzes als Zielrohstoff; das Syndikat erhält 60 Prozent. Aufträge, Berichte, Beute, Marktware und Auditbuchungen werden dauerhaft gespeichert.

## Spielstand und Sicherung

`data/empire.sqlite3` enthält im lokalen Modus die persistente Welt. Nutze zum Sichern das CLI-Werkzeug `python -m fur_empire.manage backup --directory backups`; SQLite-Sicherungen werden zusätzlich auf Integrität geprüft. Eine Produktionsdatenbank liegt in PostgreSQL und wird mit dem bereitgestellten Backup-/Restore-Ablauf gesichert. Niemals eine fremde Datenbank über einen vorhandenen Spielstand kopieren. Testdatenbanken entstehen in temporären Verzeichnissen oder einem ausdrücklich konfigurierten Prüfserver.

## Entwicklung und Prüfung

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m ruff check fur_empire tests scripts
.\.venv\Scripts\python -m black --check fur_empire tests scripts
.\.venv\Scripts\python -m mypy fur_empire
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip_audit -r requirements.lock --no-deps --disable-pip
npm.cmd run lint
npm.cmd run check
npm.cmd test
```

Start ohne Starter:

```powershell
.\.venv\Scripts\python -m uvicorn fur_empire.api:app --host 127.0.0.1 --port 8080
```

Siehe die vollständige [Spielanleitung](docs/SPIELANLEITUNG.md), [FUR-2-Regeln](docs/game-design/FUR_EMPIRE_SPEC.md), [Architektur](docs/architecture/ARCHITECTURE.md), [Verifikation](docs/VERIFICATION.md) sowie die historische [Quellenanalyse](FUR_EMPIRE_9_REPOSITORIES_ANALYSE.md) und den [Entwicklungsplan](FUR_EMPIRE_ARCHITEKTUR_UND_ROADMAP.md).

