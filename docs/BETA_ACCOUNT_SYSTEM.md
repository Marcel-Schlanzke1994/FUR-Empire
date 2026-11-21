# Beta-Kontosystem

## Aktive Richtlinie

```dotenv
BETA_MODE=true
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=false
```

Die Werte wirken serverseitig. Ungültige Boolesche Werte sowie aktiver Beta-Modus mit gleichzeitig
erzwungener E-Mail-Bestätigung stoppen den Start. Der Server prüft Name, Passwort, optionale
eindeutige E-Mail, Sprache, Passwortbestätigung und die aktuelle AGB-/Datenschutzannahme. Konto,
Startwelt und Startressourcen entstehen transaktional; anschließend ist die Spielersitzung sofort
nutzbar. Eine E-Mail erzeugt im Beta-Modus keinen Aktivierungscode und blockiert keine Spielaktion.
Neue Konten erhalten ausschließlich die Rolle `player`.

Argon2, eindeutige Identitäten, HttpOnly-/SameSite-Sitzungen, Secure Cookies in Produktion, CSRF-,
Origin- und Hostprüfung, Netzwerk- und Kontoratelimits, serverseitige Validierung, neutrale
Reset-Antworten, optionales TOTP, Recovery-Codes, Sperren und auditierte Moderation bleiben aktiv.

## Übergang nach der Beta

```dotenv
BETA_MODE=false
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=true
```

Neue Registrierungen erhalten dann einen Bestätigungscode und noch keine Spielsitzung. Migration 124
vermerkt ausschließlich diese neuen Konten in `email_verification_pending`; nur dort vermerkte,
unbestätigte Konten werden bei Login oder Spielbefehl abgewiesen. Bestehende Beta- und Altkonten
werden nicht ausgesperrt. Vor der Umstellung müssen SMTP, lokalisierte Mails, Bestätigungsroute und
öffentliche Origin-Konfiguration im Staging geprüft werden.

## Migrationen

- Schema 122: Kontosprache `de`, `en`, `es` oder `fr`
- Schema 123: angenommene AGB-/Datenschutzversion und Registrierungssprache
- Schema 124: explizite Menge neu zu bestätigender Konten

Alle Migrationen sind additiv und erhalten Konten, Sitzungen, Kolonien, Welten und Fortschritt.
