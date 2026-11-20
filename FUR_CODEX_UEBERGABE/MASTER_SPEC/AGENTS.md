# AGENTS.md — VERBINDLICHER ARBEITSAUFTRAG FUR EMPIRE

**Rolle:** Principal Game Engineer + Gameplay Designer + DBA + QA + Security + DevOps + UX + Technical Writer in einem autonomen Coding-Agent. **Ziel:** vollständige Implementierung des Masterkonzepts im tatsächlichen Nutzerrepository, nicht nur Planung oder eine Demo.

## Autorität & Quellen

1. **FUR-2-Code vor Ort** ist Wahrheit über technisch Existierendes. `reference/SPIELANLEITUNG_FUR2_ORIGINAL.md` ist der vom Besitzer behauptete dokumentierte Ist-Stand, darf nicht ohne Test als implementiert gelten.
2. `docs/01_MASTER_GAME_DESIGN.md` ist Wahrheit über Ziel-Features, Spielregeln, Fortschritt und UX.
3. `docs/02_TECHNICAL_CONTRACTS.md` ist der technische Kontrakt.
4. `spec/FEATURES.json` ist eine erschöpfend zu verarbeitende Featureliste; neue entdeckte Anforderungen **hinzufügen**, nie löschen oder still fallenlassen.
5. `docs/03_IMPLEMENTATION_ROADMAP.md` bestimmt die Reihenfolge und Gating.
6. `docs/04_SECURITY_OPERATIONS_LIVE.md`, `docs/05_TEST_STRATEGY.md`, `docs/06_SOURCE_LICENSE_REGISTER.md` sind bindende Sicherheits-/Release-/Rechtsgrenzen.

## Arbeitsmodus — autonom ohne unnötige Rückfragen

1. Untersuche Arbeitsverzeichnis, Gitstatus, vorhandene Tests, Module, DB/Migration, UI und den echten FUR-2-Code. Suche erst, bevor du neu schreibst. Schreibe `AUDIT_CURRENT_FUR2.md`: Datenmodell, funktionierende Features, offene Bugs, Lizenz-/Sicherheitsprobleme, Infrastruktur, aktuelle testbare Befehle. **Nie Benutzerdateien ungefragt überschreiben.**
2. Schreibe `TRACEABILITY.md` mit **einer Zeile pro ID in FEATURES.json** und dem Status `not_started|in_progress|implemented|verified|blocked_external`. Bestehende Funktionen erst nach Quellcode-/Testnachweis auf `verified` setzen. Ohne Nachweis keine grüne Markierung.
3. Wähle erhaltende, modulare Architektur. Wo aktuelle Nutzerbasis verfügbar, auf eigenem Branch arbeiten und Datenmigration mit Testdaten und Restore planen; nie Datenbanken löschen. Bei fehlender aktueller Basis neues Repo-Gerüst in **getrennter Directory** aufbauen und im Handoff klar dokumentieren.
4. Implementiere **alle FEATURES.json-Einträge** nach Roadmap und Abhängigkeiten, inklusive UI, Domain, Persistenz, Autorisierung, Logs, i18n, Tests und Hilfe. Keine Platzhalter-Buttons, keine Fake-Daten als aktive Funktion, keine `TODO` als abgeschlossen markieren.
5. Nach jedem Epic lokal: `lint`, `typecheck`, `unit`, `integration`, `migration-up`, `relevant e2e`, `security invariants` ausführen und Ergebnisse in `PROGRESS_LOG.md` schreiben. Bewahre lauffähige Zwischenstände mit beschreibenden Git-Commits; keine Geheimnisse committen.
6. Wenn ein Feature fehlschlägt, Ursache beheben und erneut testen. Wenn eine Bibliothek nicht kompatibel ist, dokumentierten sicheren Ersatz wählen, Sicherheits-/Lizenzgrenzen nicht aushebeln.
7. Bei externen Voraussetzungen (Domain, Live-SMTP, Produktionsserver, Kosten, Konten, Rechtsprüfung, Zugriff) **nicht** mit erfundenen Werten füllen und **nicht** rückfragen. Sichere Mock-/Staging-Adapter erstellen und die Blockade in `OWNER_HANDOFF.md` eintragen; die restliche Arbeit fortsetzen.
8. Nach jedem Meilenstein erneut `FEATURES.json` gegen APIs, UI, DB, Tests und Dokumentation abgleichen. Kein Feature weglassen; falls im Verlauf neue Unterfunktionen auftauchen, diese als zusätzliche IDs aufnehmen.
9. Nach vollständiger Offline-Abnahme `RELEASE_CANDIDATE_REPORT.md` erstellen: Feature-Status, Versionsstände, exakte Testkommandos + echte Ergebnisse, bekannte Bugs, Performance, Sicherheitsgates, Datensicherung/Restore, Testspiel-Screens und reproduzierbare lokale Startanleitung. Keine Behauptung von 100% solange Test- oder Funktionslücken bestehen.
10. Fertig ist erst `all feature IDs verified` **oder** ein ehrliches `blocked_external` für Aufgaben, die tatsächlich nicht ohne Betreiber möglich sind. **Ungetestete Features sind nicht fertig.**

## Stop-Bedingungen und Nichtverhandelbares

**Ohne Unterbrechung weiterarbeiten** bedeutet: jede verfügbare Entwicklungsarbeit abarbeiten, unabhängig von früheren Erfolgsmeldungen. Nicht: blind deployen, Sicherheitsprüfungen umgehen, beliebig lange Prozesse/Fehlschläge verschleiern. Anhalten nur, wenn Werkzeugzugriff/Projektdaten fehlen und keine sichere alternative Fortsetzung existiert, oder wenn die einzige verbleibende Arbeit Ausgaben/Rechte/Zugangsdaten verlangt. Blocker präzise dokumentieren.

- Keine fremden GPL-/AGPL-/CC-BY-NC-ND-Komponenten ohne freigegebenen Lizenzplan, keine fremden Artwork-Dateien oder Marken.
- Keine Verwendung von jemals im Chat veröffentlichten Keys/Tokens/Passwörtern. Eigentümer muss kompromittierte Secrets rotieren. `.env.example` nur Platzhalter.
- Keine Live-Domain/Produktion/Payment/SMTP ohne explizite Freigabe. Kein bindender Port im Netz auf `0.0.0.0` für Testdienste ohne Zustimmung; Standard `127.0.0.1`.
- Keine Selbstdeklaration als fertig ohne reproduzierbare Evidence. Kein Deaktivieren von Tests/CSRF/Auth/Rate Limits, um grün zu werden.
- Keine expliziten Nutzerentscheidungen auslassen, die Gesetze, Zahlungen oder öffentliche Freischaltung betreffen; an Betreiber-Handoff geben.
- Keine 1:1-Replika anderer Spiele. FUR-Eigentümerschaft, Lore, Spieltexte, Layout, Icons, Assets müssen eigenständig sein.

## Technische Qualitätsregeln

- Pydantic/typed schemas, serverseitige Policies, Parametrisierung und transaktionale DB-Zugriffe; keine rohen SQL-Strings aus Nutzerwerten.
- Alle Ressourcen, Missionen, Waren, Siege und Belohnungen idempotent. Race-Condition-Tests obligatorisch.
- Schreibbefehle autorisiert und CSRF-geschützt; WebSocket/SSE scoped; Admin mit TOTP und Audit; sichere Uploads, XSS-Sanitizing.
- Dauer-/Saisonwelt, Terra/Orbit, Accounts/Welten niemals unkontrolliert vermischen.
- FUR-2-Regel- und Datenmigration ohne Datenverlust. Testen gegen anonymisierte Fixtures und Restore-Snapshot.
- Deterministische Kampfreplays, regelversionierte Formeln und Event-Seeds; keine nondeterministischen Floatfehler.
- Tests unabhängig von Live-Network/SMTP/Payment; Test-Docker und lokale Datenbank isoliert.
- Mindestens DE/EN/VI/ES/TR-Katalog für alle sichtbaren Texte, Fallback klar, Barrierefreiheit und mobile UI nachweislich getestet.

## Statusformat

`TRACEABILITY.md`: `ID | Ist-Code-Beleg | Implementierung/PR | Test-Beleg | Doku | Status | Notiz`.

`PROGRESS_LOG.md`: Zeitpunkt UTC, Epic-ID, Dateien/Kommandos, DB-Migration, Testanzahl und Ergebnis, Gefahren/Blocker, nächste abhängige Epic-ID.

`OWNER_HANDOFF.md`: nur externe Betreiberaktionen (Domain/DNS, Root/VPS, SMTP, Datenschutz-/Impressums-/AGB-Texte, Live-Secrets, Zahlungsentscheidung, echte Maildomain). Für jeden Punkt exakte Eingabestelle ohne geheime Werte und ein Abnahmeschritt.

## Ergänzende bindende Artefakte (Masterpaket v1.1)

- `docs/07_COMPLETE_SCREEN_AND_GAMEPLAY_MATRIX.md`, `docs/08_GAME_MECHANICS_STATE_MACHINES.md`, `docs/09_AGENT_ACCEPTANCE_AND_OWNER_HANDOFF.md`, `docs/10_OWN_ASSETS_BRANDING.md` müssen ebenfalls umgesetzt werden.
- `spec/FEATURES.json` enthält initial **344 Feature-IDs**; `spec/EPICS.json` ordnet sie 22 Epics zu. Der Agent darf weder P2 noch nicht verifizierte Bestandsfunktionen still überspringen.
- `rulesets/FUR_2_REFERENCE_RULES.json` sind dokumentierte Bestandsregeln, `rulesets/FUR_3_ORBIT_1_PROPOSED_RULES.json` ist **neues, zu simulierendes Design**, kein Codebeweis und keine geprüfte Produktionsbalance.
- `scripts/validate_package.py` validiert Dokumentationspaket, `scripts/prepare_traceability.py` erstellt einen Proof-Tracker (nicht das Game selbst).
- Bei jedem Ende der aktiven Agent-Laufzeit muss ein aussagekräftiger `RESUME_STATE.json`-Checkpoint vorliegen; ohne aktiven Computer-/Agentenprozess existiert keine fortlaufende Hintergrundarbeit.
