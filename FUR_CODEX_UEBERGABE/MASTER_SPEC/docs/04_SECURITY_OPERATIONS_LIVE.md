# FUR EMPIRE — SICHERHEIT, DATENSCHUTZ, BETRIEB UND LAUNCH-VORBEREITUNG

**Ziel:** Betreiber kauft die Domain und VPS/Root später. Alles bis zum öffentlichen Go-Live muss offline/lokal oder auf privatem Staging vorbereitet, getestet und dokumentiert sein. Dieses Dokument ist technische Checkliste, keine individuelle Rechtsberatung.

## 1. Vertrauensgrenzen und Security-by-default
- Untrusted: Webclient, Chat, uploads, URL, Query/Body, WebSocket, OAuth, DNS, andere Welten, externe Webhooks, Mod-Plugins, AI-Texte. Trusted: validierte Domänenbefehle unter authentisierter Session und DB-Transaktion.
- `session_id`/TOTP-/Reset-Token nie protokollieren. Argon2id/aktuell sichere Passwort-Hasher, Rotation + Einmal-Reset-Codes, Rate-limit IP+Account+Device heuristisch, kein Account-Enumeration.
- CSRF-Tokens (Cookie-Session), `Secure/HttpOnly/SameSite`, Login-Session-Rotation, Origin-Prüfung, HTTPS in Produktion, CSP/HSTS nur nach TLS-Test, zentraler Fehlerhandler ohne Stacktrace.
- Objekt- und Weltberechtigungen je Anfrage, nicht nur in UI; Role-Based Access + Policy-Based Access für Allianzrolle, Besitz, Fog, Chatgruppe, Gamemaster.
- SQL-Parameter, Pydantic-Validierung, HTML-Escaping und sanitizer für BBCode/Markdown; Template-Autoescaping, Image-/File-Upload Typ, Größe, Pfadprüfung; keine unsicheren Deserialisierungen.
- Verbot: Debug-Endpoints, `uvicorn --reload` in Produktion, unveränderte Testaccounts, bekannte Demo-Passwörter, localhost als öffentliches Callback-Ziel, Admin ohne 2FA, Default-Credentials.

## 2. Spielintegrität / Anti-Cheat
- Alle wirtschaftlichen Werte aus serverseitiger DB, integer/fixed-point, origin/owner-Policy, DB-FK-Checks, Ledger, idempotente Requests, Repeat-At-Least-Once Worker mit exactly-once Wirkung.
- World/Season/Account-Trennung, keine Cross-World-Schreiboperationen oder missbräuchliche saisonale Belohnungstransfers.
- Lock-Order für mehrere Konten deterministisch; `SELECT FOR UPDATE` unter PostgreSQL; idempotency key / payload checksum / conflict.
- Keine verbotenen Angriffe bei NAP, Newbie-Schutz, Urlaub, eigenen Zielen, Kriegssperre; Start und Ankunft validieren. Anti-Raid-Limits und Attack-Cooldowns.
- Anti-Bot: serverseitiges Rate Limiting, verdachtsbasierte Moderation, auditierter Einspruch. Keine automatischen permanenten IP-only-Sperren. Privacy by design.

## 3. Secret-Management und bereits offengelegte Schlüssel
- Keine früher in Chats oder lokalen Beispielen geposteten Tokens übernehmen. Alle zuvor offengelegten Schlüssel gelten als potenziell kompromittiert und sollen vor Livebetrieb bei den Diensten rotiert werden.
- Neue `.env.example` enthält nur Platzhalter wie `CHANGE_ME`, ohne echte Zugangsdaten. `.env`, SSH-Keys, DB-Dumps, Mailer-Credentials, Bot-Token und Backup-Schlüssel in `.gitignore` und getrenntem Secret Store.
- `pip-audit`, Lockfile, SAST, Secretscanner vor jedem Release, Abhängigkeiten pinnen. Fremdprojekte nicht ungeprüft als produktive Bibliotheken installieren.
- Minimum Privilege: DB-Gameuser nicht Superuser; Backup-Account ohne Spiel-Schreibrechte; Runtime Container ohne Root, read-only files, klar beschränkte Volumes, keine Docker-Socket-Freigabe an Webapp.

## 4. Deployment-Sollstruktur
```text
Internet [erst nach Go-Live-Freigabe]
  ↓ DNS + HTTPS (Caddy/Traefik/Nginx)
  ↓ rate-limit + security headers + TLS
Web API + statisches FUR UI
  ↕ private Docker network
PostgreSQL + Redis/Event Queue
  ↕ dedicated world_worker + scheduler
  ↕ Object/backup volume, alerting + metrics
SMTP-Provider [später; lokale Mailcatcher-Alternative]
Discord/External-Webhooks [optional; disabled-by-default]
```
- `compose.local.yaml`: binds auf 127.0.0.1, keine echten Maildienste, seedbare Testwelt, test-DB.
- `compose.staging.yaml`: realistische Prod-Profile aber private/Test-Secrets, Migrations-Preflight, Healthchecks, Backup/Restore.
- `compose.prod.yaml`: Proxy 80/443 erst nach expliziter Freigabe, bindet DB/Redis nicht öffentlich, Volumes persistent, Backup-Cron, Service-User, CPU/RAM/Disk-Limits, Restart-Policy.
- Pipeline: CI → Testimage → SBOM/Scan → signierter Release-Tag → manuelle `deploy-approved` Aktion → preflight → Backup → Migration → Rolling Restart → Smoke → Monitoring → Rollback-Plan.

## 5. Backup und Wiederherstellung
- Tägliche verschlüsselte PostgreSQL-Backups, Aufbewahrung mindestens 7 tägliche/4 wöchentliche/3 monatliche Kopien als anpassbares Ziel. Mindestens eine verschlüsselte Offsite-Kopie und periodischer Restore in isolierter DB.
- RPO/RTO als vorläufige Ziele: RPO 24h ohne WAL bzw. deutlich kleiner mit verifiziertem WAL/PITR; RTO ≤2h auf getesteter Hardware. Keine Zielzusage, bevor gemessen.
- Backup enthält DB, Ruleset-Versionen, Asset-Manifest, Uploads, Env-Schema und Deploy-Version — **keine Klartext-Secrets in Backup-Reports**.
- Wiederherstellung: Wartung→Snapshot→neuen isolierten Stack→Restore→Integrity-Replay→Vergleich Spieler/Ressourcen/Orders/Missionen→DNS/Traffic erst nach Owner-Freigabe.
- Spätestens monatlich Restore-Drill + Nachweis: UTC-Zeit, Snapshot-ID, Checksummen, Recovery-Dauer, DB-integrity und UI-Smoke.

## 6. Datenschutz / Spieler und Community
- Personenbezogene Daten minimieren. getrennte Account-Identität und Weltstatistik, Lösch-/Auskunfts-/Portabilitätsanfragen, konsistente Anonymisierung historischer Battles/Chatlogs soweit zulässig.
- Rechtstexte: Impressum/Datenschutzerklärung/Nutzungsbedingungen/Community-Regeln/ggf. Cookie-Einwilligung und Alters-/Jugendschutzprüfung vor öffentlichem Launch von Betreiber/Rechtsprüfung finalisieren.
- Kontaktformular, Abuse-Meldungen, Community-Meldesystem, Rechtsmittel/Appeal und klare Moderations-Zuständigkeiten.
- Telemetrie anonym/aggregiert wo möglich; Audit-Aufbewahrung regelbasiert, kein unnötiges dauerndes Tracking. DSGVO-Prozesse mit realen Fristen von Fachperson prüfen.
- Keine ChatGPT/API-/Discord-/Google-Keys aus früheren Chats verwenden; Integrationen opt-in und mit minimalen scopes.

## 7. Monitoring und Betriebsrunbooks
- Health: HTTP/Web-DB-Redis-Liveness/Readiness/Worker-heartbeat/Scheduler-lag; Metrics: p50/p95, Fehlerquote, Anzahl Missionen/Queue-Backlog, DB-Locks, Late Events, Login-Fehler, Ressourcenkonsistenz, Datenträger, Backup-Alter.
- Alerts: Worker-Ausfall, Backup >26h alt, DB volllaufend, ungeplant hohe 5xx, überlanger Queue-Lag, verdächtige Ressourcenverdoppelung, HTTPS-/Zertifikat-Fehler.
- Runbooks: Start/Stop, DB-Migration, Worker-Retry/DLQ, Security Incident, Key-Rotation, Backup/Restore, Welt-Freeze, Event-Stop, gehärtetes Admin-Onboarding, Spieler-Import/Export, Rollback, Notfallkontakt.
- Logs sind strukturiert mit request_id/world_id/event_id (keine Klardaten); Tracing wird an wenigen kontrollierten Orten aktiviert.

## 8. Betreiberschritte nach vollständiger lokaler Abnahme
1. Domain besitzen, gewünschten DNS-Anbieter festlegen; DNS-A/AAAA/CNAME korrekt auf VPS zeigen lassen.
2. VPS/Root bereitstellen (Linux LTS mit Security-Updates, mindestens passend zum gemessenen Lastprofil), separates unprivilegiertes Deploymentkonto, SSH-Keys + Firewall, SSH Passwortlogin deaktivieren, automatisierte Sicherheitsupdates prüfen.
3. Gültige HTTPS-Zertifikate über Reverse Proxy, TLS-Checks, HSTS erst nach Bestätigung.
4. SMTP-Domain/Provider und SPF/DKIM/DMARC konfigurieren; E-Mail-Absender/Retouren testen.
5. Alle Secrets neu und einzigartig generieren, Produktions-TOTP für Admin aktivieren, Testaccounts sperren, Staging-Flags deaktivieren.
6. Rechtliche Dokumente prüfen/veröffentlichen, DSGVO-Löschanfragen und Meldekanal testen, Datenverarbeitung mit Host/Provider prüfen.
7. Release-Candidate-Bericht und Restore-Test abzeichnen, Betreiber setzt `LAUNCH_APPROVED=true` erst nach explizitem Go-Live-Entscheid.
8. Erst dann Domain live, Smoke-Test, Last-/Betriebsüberwachung, anfängliches Spielerlimit und Rollback-Bereitschaft.

## 9. Klare Owner-Handoff-Formatvorgabe
`OWNER_HANDOFF.md`: `ID | externer Beschluss | was benötigt | sichere Eingabestelle | letzter Test ohne Zugang | Inbetriebnahmeschritt | Abnahme`. Alle realen Preise/Providerentscheidungen bleiben offen; Agent soll diese **nicht erfinden oder buchen**.
