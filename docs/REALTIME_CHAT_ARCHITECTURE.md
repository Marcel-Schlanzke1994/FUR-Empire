# Architektur des Echtzeit-Chats

## Ergebnis

Der angemeldete Spielbereich besitzt ein dauerhaft eingebundenes Chat-Dock mit Global-, Allianz-,
System- und Privatkanal. Es bleibt beim Wechsel zwischen Terra, Orbit und Community-Ansichten
erhalten. Desktopnutzer können es skalieren oder minimieren; mobil wird es platzsparend angedockt.

Der Browser verbindet sich über `/api/v1/chat/live` mit der bestehenden HttpOnly-Sitzung. In
Produktion muss die Origin der konfigurierten öffentlichen Adresse entsprechen. Der Server prüft bei
jedem Snapshot Sitzung, Sperrstatus, aktive Welt und aktuelle Allianz neu. Beitritt oder Austritt
ändert damit die Berechtigung ohne Vertrauen in Clientdaten.

## Datenfluss

```text
Chat-Eingabe
  -> bestehender CSRF-geschützter /api/v1/command
  -> transaktionale Rechte-, Rate-, Mute- und Blockprüfung
  -> persistente messages-Tabelle
  -> begrenzter WebSocket-Snapshot
  -> angemeldetes Chat-Dock
```

Der WebSocket liest die gemeinsame Datenbank einmal je Sekunde und sendet nur bei einer Änderung.
Damit funktionieren lokale SQLite-Entwicklung und mehrere PostgreSQL-App-Instanzen ohne neuen Broker:
Schreibt Instanz A, sieht ein Socket auf Instanz B die Änderung über PostgreSQL. Die maximale
Near-Realtime-Latenz beträgt eine Sekunde.

Schreibvorgänge bleiben im etablierten idempotenten Befehlspfad. Der Socket ist ausschließlich
empfangend und kann CSRF, Kanalrechte, Allianzmitgliedschaft, private Blocklisten, Mutes,
Eingabegrenzen oder Audit nicht umgehen. Betreiberankündigungen erscheinen schreibgeschützt im
Systemkanal und können von Spielern nicht gefälscht werden.

## Speicherung und begrenzter Verlauf

- Globalnachrichten sind an die aktive Welt gebunden.
- Allianznachrichten speichern die Allianz-ID und sind nur für aktuelle Mitglieder sichtbar.
- Privatnachrichten sind ausschließlich für Absender und Empfänger sichtbar.
- Systemmeldungen stammen aus der getrennten Ankündigungstabelle.
- Das Dock erhält höchstens 50 sichtbare Einträge je Kanal. Die Nachrichtenansicht lädt ältere
  Einträge weiterhin per Cursor; der Browser lädt nie den gesamten Verlauf.
- Stabile Server-IDs und Zeitstempel bestimmen die Reihenfolge; ausgeblendete Nachrichten fehlen.

## Clientverhalten

- Automatische Wiederverbindung mit begrenztem exponentiellem Backoff
- Ungelesenzähler für inaktive Kanäle und Deduplizierung nach Server-ID
- Automatisches Scrollen nur am bisherigen Verlaufsende
- Enter sendet, Shift+Enter erzeugt einen Zeilenumbruch
- Emoji-Auswahl und tastaturbedienbare native Steuerelemente
- Namen und Inhalte werden mit `textContent`, niemals als HTML, eingesetzt
- Eigene Zustände für Verbinden, verbunden, Wiederholungsversuch und abgemeldet

## Missbrauchsschutz und Moderation

Der vorhandene Serverpfad erzwingt Authentifizierung, maximal 2.000 Zeichen, API-Ratelimits,
temporäre Mutes, Sperren, private Blocklisten, Kanalrechte, Meldungen, Moderator-Ausblendung und
auditierte Entscheidungen. Clientdaten können keine Moderator- oder Administratorrechte verleihen.

## Betrieb und Prüfungen

Caddys `reverse_proxy app:8080` unterstützt WebSocket-Upgrades automatisch. Das Deployment benötigt
weiterhin HTTPS, `PUBLIC_ORIGIN`, vertrauenswürdige Hosts sowie Health-/Readiness-Prüfungen.

Automatisiert geprüft sind authentifizierte Zustellung zwischen zwei getrennten Konten ohne Reload,
anonyme Abweisung, Persistenz/Pagination, Allianzisolierung, Privatsichtbarkeit, Blockierung,
XSS-sichere Darstellung, Meldungen, Ausblendung, Mutes und Kataloggleichheit der vier Sprachen. Eine
vollständige manuelle Mehrbrowser-, Mobil- und Screenreader-Abnahme bleibt ein eigener Releasecheck.
