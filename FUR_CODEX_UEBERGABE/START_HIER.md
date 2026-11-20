# FUR EMPIRE — CODEX-ÜBERGABE (IMPLEMENTIEREN VOR TESTEN)

## Ziel
Das vorhandene FUR-2-Projekt wird ohne Datenverlust zu **einem** vollständigen FUR-3-Terra/Orbit-Spiel ausgebaut. Alle 344 bekannten Feature-IDs, Bestandsfeatures und später dokumentierte Erweiterungen müssen erhalten, implementiert und über echte Server-/Datenbank-/UI-/Worker-Schnittstellen verbunden werden. Zuerst alle Funktionen implementieren und ihre Verbindungen dokumentieren; **keine Testläufe vor vollständiger Implementierung**. Erst danach die Gesamtabnahme starten. Grafikbedarf und Motive in `GRAFIK.md` führen; rechtmäßig selbst erzeugbare Assets sofort integrieren.

## Dateistruktur dieser ZIP

- `CODEX_MASTERPROMPT.md` — **Hauptprompt. Direkt in Codex einfügen oder als Datei lesen lassen.**
- `GRAFIK.md` — startfertiges Asset-Briefing mit Größen, Formaten, Varianten, Rechten und Datensatzschema. Im **echten Spielrepo** pflegen/ergänzen, aber vorhandene gleichnamige Datei nicht überschreiben.
- `ASSET_MANIFEST_TEMPLATE.json` — Maschinenlesbare Vorlage für ein vollständiges Assetinventar, das Codex im Projekt unter `assets/ASSET_MANIFEST.json` pflegt.
- `MASTER_SPEC/` — gesamtes ursprüngliches 344-Feature-Masterpaket inklusive `spec/FEATURES.json`, Epics, Docs, Regeldateien, Quellenregister und originaler Agent-Anweisungen. Bei widersprüchlicher Testreihenfolge hat **CODEX_MASTERPROMPT.md** die vom Eigentümer neu angeordnete Reihenfolge (erst integrieren, dann testen). Sicherheit, Datenschutz und Datenbewahrung bleiben jederzeit verbindlich.
- `AKTUELLER_STAND/` — die acht aktuellen, vom Eigentümer am 08.11.2026 gelieferten Berichte. Sie ergänzen/aktualisieren ältere Soll- und Ist-Aussagen.

## Ausführung

1. Das ZIP in einen **eigenen Ordner neben oder im FUR-Projekt** entpacken, z. B. `FUR_CODEX_UEBERGABE/`. Auf keinen Fall das eigentliche Projekt mit den fremden neun Referenz-Repositories ersetzen. Keine `AGENTS.md`, Datenbanken, `.env`, Secrets, vorhandene Regelsätze oder Spielerstände überschreiben.
2. Das echte FUR-Repository in Codex als Arbeitsverzeichnis öffnen; ZIP-Ordner als lesbares Begleitmaterial verfügbar machen.
3. Den folgenden Startauftrag in Codex eingeben:

   **„Arbeite den kompletten `FUR_CODEX_UEBERGABE/CODEX_MASTERPROMPT.md` eigenständig und fortlaufend ab. Nutze `FUR_CODEX_UEBERGABE/MASTER_SPEC/spec/FEATURES.json` als 344-ID-Pflichtkatalog, alle aktuellen Berichte unter `AKTUELLER_STAND/` als neuere Ist-Hinweise, erstelle und pflege `GRAFIK.md` im echten Root. Führe keinerlei Testlauf vor 100 % fertig implementierter und verbundener Features aus; schreibe Tests nur vorbereitend. Schütze alle bestehenden Daten. Implementiere bis zur abschließenden Gesamtabnahme, dokumentiere Restblocker ehrlich, und nutze RESUME_STATE.json bei erzwungenen Unterbrechungen.“**

4. Codex darf nicht erwarten, dass dieses ZIP die eigentliche FUR-Anwendung enthält. Der **aktuelle Quellcode und seine echten Datenbanken** müssen im Codex-Workspace vorhanden sein. Die acht Markdown-Berichte allein genügen nicht, um das Spiel technisch fertigzustellen.
5. Am Ende: `implementation_complete_unverified` erst bei 344/344 vollständig verbundenen Implementierungen; danach gesammelte QA; echte Releasebereitschaft erst nach erfolgreicher QA und Eigentümerfreigabe.

## Externe Voraussetzungen
Domain, Root-/VPS-Vertrag, produktives SMTP, echte Secrets, rechtliche Betreiberangaben und öffentliche Livefreigabe werden später vom Eigentümer erledigt. Keine externen Kosten oder öffentliche Bereitstellung ohne Zustimmung.

**Hinweis:** Ein Coding-Agent ist an Laufzeit-/Kontextlimits gebunden; kein Prompt kann unbegrenztes, zeitlich ununterbrochenes Arbeiten garantieren. Der Prompt fordert deshalb lückenlose Statusdateien und eindeutige Wiederaufnahme.
