# FUR EMPIRE — AUTONOMER BUILD-LOOP FÜR EINEN CODING-AGENT

## Pflicht-Start

1. `python scripts/validate_package.py` im extrahierten Masterpaket.
2. In das echte FUR-Projekt wechseln. Git-Zustand dokumentieren, sichere Arbeitsbranch/Worktree erstellen. Bei uncommitted Benutzerdaten **nicht** zurücksetzen/überschreiben; vom Agenten kontrollierte Änderungen davon trennen.
3. Tatsächlichen FUR-2-Bestand anhand `reference/SPIELANLEITUNG_FUR2_ORIGINAL.md`, `AUDIT_CURRENT_FUR2.md` und realen Tests vergleichen. Nicht den Demo-Prototyp für den aktuellen produktiven FUR-2-Code ausgeben.
4. `spec/FEATURES.json`, `spec/FEATURE_INDEX.md`, `docs/03_IMPLEMENTATION_ROADMAP.md` abarbeiten; `TRACEABILITY.md` wird per Feature-ID gepflegt.

## Endloser Arbeitsalgorithmus innerhalb der verfügbaren Agent-Laufzeit

```text
while feature_status exists in {not_verified,in_progress,implemented}:
  pick first unfinished dependency-ready epic from E00..E21
  inspect existing source and exact requirements
  write tests for changed behavior (positive, negative, race, world boundary)
  implement domain + persistence + API + UI + i18n + docs
  run formatter, types, unit, integration, browser smoke, security checks
  if fail: inspect error, repair, re-test; do not hide it
  if external-only blocker: write owner handoff; continue other independent work
  commit only code controlled by agent with truthful message
  store evidence in TRACEABILITY and PROGRESS_LOG
  update RESUME_STATE after each verified feature / epic
  repeat

when all implementation IDs verified:
  run global E20/E21 gates
  generate RELEASE_CANDIDATE_REPORT and OWNER_HANDOFF
  do NOT buy domain/server or publicly expose service
```

## Immer denselben Qualitätsbegriff benutzen

- `not_verified`: noch nicht durch aktuellen Code belegte Bestandsfunktion oder ungebaute Sollfunktion.
- `in_progress`: in Bearbeitung, noch nicht vollständige Tests.
- `implemented`: Code/UI/Schema vorhanden, Tests/Manual QA noch nicht voll bestanden.
- `verified`: alle vom Feature geforderten Gates belegbar bestanden.
- `blocked_external`: tatsächliche Bereitstellung/Bestätigung durch Eigentümer erforderlich (z.B. Domain, Provider, Produktionssecrets, Lizenzfreigabe). **Nicht** für gewöhnliche Bugs/Fehler verwenden.

## Wenn eine neue Agentensitzung nötig wird

- Kein Versprechen einer unbeaufsichtigten Ausführung nach Ende der aktuellen Sitzung. Vor Kontext-/Quota-Ende `RESUME_STATE.json` mit Branch/Commit/Dateien/Tests/Fehler/nächster Feature-ID speichern, einen knappen Zwischenbericht schreiben.
- Neuer Agent erhält `agent/RESUME_PROMPT.md` und nutzt `RESUME_STATE.json` statt ungeprüft wieder von Null zu beginnen.
- Bleibt ein Tool wirklich unzugänglich, implementiere prüfbare alternative lokale Schritte und dokumentiere die exakte unvermeidbare Grenze.

## Red flags, die sofort zum Fix führen

- Unautorisierter cross-world Zugriff, doppelte Ressourcengutschrift, negatif Betrag, Duplicate Claim, nicht deterministischer Kampf oder Seed, kaputte Datenmigration, fehlender Backuppfad, Kopieren von fremden Grafiken, ungeprüfter Lizenzcode, Fake UI, Secret im Git, öffentlich offener DB-Port, Admin ohne TOTP.
