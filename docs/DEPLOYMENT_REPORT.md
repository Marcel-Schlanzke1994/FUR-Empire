# Produktionsbereitstellungsbericht

## Bereitstellung vom 20. November 2026

Die Erweiterungen für öffentliche Beta, sofort spielbare Registrierung, Datenbankschema 124 und
permanenten Echtzeit-Chat wurden über den vorhandenen, abgesicherten Release-Ablauf auf
`https://fur-empire.de` bereitgestellt.

Vor dem Austausch der Container wurde die produktive PostgreSQL-Datenbank nach
`/backups/fur-20261120T221341Z.dump` gesichert. Das erzeugte Image trägt den SHA-256-Bezug
`26e9ad…`. App und Worker wurden neu erstellt, die Migrationen meldeten ein aktuelles Schema und
beide Dienste erreichten anschließend ihren Health-Status. Die Releasekennung lautet
`20261120T221340Z`.

## Nachweise nach der Bereitstellung

- `/api/v1/public-config` meldet Produktionsbetrieb, aktiven Beta-Modus und deaktivierte
  E-Mail-Verifikationspflicht.
- Der Readiness-Endpunkt meldet `ready: true`.
- `/static/live-chat.js` wird mit HTTP 200 ausgeliefert und verwendet `/api/v1/chat/live`.
- Die Produktionsdaten blieben erhalten: bei der Kontrolle waren 11 Benutzer und 11 Kolonien
  vorhanden.
- Datenbankschema 124 ist vorhanden.
- Die Betriebsüberwachung zeigte keine Quarantäne und keine Neustartschleife.

Es wurden keine produktiven Testkonten und keine Fake-Spielerdaten angelegt. Ein authentifizierter
Mehrspieler-End-to-End-Test auf der öffentlichen Instanz wurde daher nicht mit künstlichen Konten
durchgeführt; diese Funktion wurde mit isolierten lokalen Testdaten geprüft.

## Rollback und Betrieb

Der bestehende Release-Ablauf behält ein Datenbank-Backup und eine Releasekennung. Ein Rollback
muss die Abwärtskompatibilität der Migration berücksichtigen; das produktive Schema darf nicht
destruktiv zurückgesetzt werden. WebSocket-Verbindungen werden durch den vorhandenen Reverse Proxy
weitergereicht. Geheimnisse und Produktionsdaten wurden weder in das Repository noch in diesen
Bericht aufgenommen.
