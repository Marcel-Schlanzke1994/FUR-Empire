# FUR EMPIRE — VOLLSTÄNDIGE TEST- UND RELEASESTRATEGIE

## 1. Testpyramide (automatisiert + nachvollziehbar)
- **Unit:** Ressourcenarithmetik, Fraktionsboni, Research prerequisites, Defensivwerte, Kosten/Zeit, Speed/Distance, Kampf-RNG, loot/fuel, XP/skills, NC/NAP/Urlaub/Noobschutz, Regelnversions-Serialisierung.
- **Property-based:** `balances>=0`, `units>=0`, keine duplizierten Items/Claims, gleichbleibende Inventarsummen bei Transfers, deterministischer Kampf, keine Mission ohne Eigentümer, Kampf-/Markt-Caps.
- **Integration DB:** Postgres auf derselben Version wie Staging, Transaktionen, Retry/Deadlock, FK/CHECK/unique, Worker-Leases, Outbox, Sitzungen, Audit, Multiworld-Permissions, Migration alter FUR-2-Fixtures.
- **API/contract:** FastAPI OpenAPI + Schemas, 401/403/404/409/422/429, Rate-limit, CSRF, Content-Type, Origin, Session expiration, SSE auth, später OAuth/Discord optional.
- **E2E Browser:** Playwright Desktop Chrome/Firefox/WebKit und Mobile, Registration→Verification→World join→Build→Research→Train→Raid→Return→Market→Alliance→ACS→Espionage→Orbit→Season→Privacy request; Admin-Betrieb getrennt.
- **Accessibility:** WCAG 2.2 AA als Ziel, Tastatur, kontrastreiche UI, Screenreader-Semantik, responsive 320/360/768/1440/1920, Reduced Motion, Fokusfallen/Modale.
- **Security:** SAST/Dependency-/Secret-/Container-Scan, XSS, SQLi, CSRF, IDOR/world leakage, TOTP replay, reset links, brute-force, forged mission, websocket channel leakage.
- **Load/Soak:** realistische Mischung aus Lese- und Schreibvorgängen mit 200 aktiven/1.000 Accounts als initialem Richtwert. Dokumentiere Hardware/Testdaten/Laufzeit. 30 Minuten ohne verlorene Events/Ressourcen; p95 und Fehlerrate real messen.

## 2. Historische FUR-2-Akzeptanz (darf nicht still brechen)
- 64×64 Karte, 104 neutrale Posten, 20×20 Ansicht; Start 1200/1000/800; 8 Gebäude bis Level 10; Produktion exakt nach FUR-2; Depot 2000+2000×level je Rohstoff; 3 Techs (+15% Taktik, +10 Loot/Logistik, +15pp Engineer); 3 Basisunits; 5 Direktiven; 10 Angebote für 24h; Börse 50/60%; Fraktionen; Neulingsschutz 1h für **bestehende** Welt; PvP/NAP/Urlaub; Zitadellenziel, Ranking 10/20/100; Saisons und 0–100pp Live-Boni; Session/TOTP/E-Mail.
- Regression auf anonymisiertem Snapshot, einschließlich aktiver Missions-/Bau-/Forschungs-/Trainings-Queues. Migration legt bei laufender Alt-Mission gepinnte FUR-2-Version fest.
- Neue Regeln nur explizit je neuer Welt (z.B. FUR-3); Migration von bestehenden Welten erfordert bewusstes, dokumentiertes Umschaltdatum und Vergleich der Daten.

## 3. Race-, Crash- und Replay-Matrix
| Fall | Parallelität/Fehler | Sollzustand |
|---|---|---|
| Doppelte Mission | 20 gleichzeitig gleiche `command_id` | 1 Mission, 1 Ressourcen-/Unit-Debit |
| Doppelter Marktkauf | 20 Käufer gleichzeitig | exakt 1 Zuschlag, Ware nur einmal |
| Koloniegründen | 100 Spieler gleiche Kachel | maximal 1 Eigentümer |
| Quote/Claim | 10 Direktiven-Claims parallel | Belohnung einmal |
| Worker stirbt | nach DB-Commit vor Ack | Wiederholung keine Doppelwirkung |
| Gleichzeitige Kämpfe | 10 Angriffe auf gleiche Basis | deterministische Ankunftsreihenfolge |
| Saison-Finalisierung | Worker doppelt | 1 Archiv, kein permanent world reset |
| Research bei Ausgaben | gleichzeitiger Bau+Research | keine negative Resource, klarer Gewinner |
| Chat/WSS | Unbefugter errät Channel | kein Zugriff/kein Event |
| Backup/Restore | 1000 Accounts + events | konsistente Missionen, unveränderte Geldsumme |
| Orbit-Kolonisation | gleiche Planetenposition | einmalige Reservierung |
| Terra↔Orbit-Transport | Retry/Return/Overflow | Ledger vollständig, kein Warendupe |

## 4. Balance und langfristige Spielbarkeit
- Simulation 1/7/30/90/180 Tage mit Anfänger/Gelegenheitsspieler/Vielspieler, 10–1000 simulierten Spielern; gleiche Welten-Seed-Fälle, Reproduzierbarkeit.
- Fairnessziele vorläufig: Startpositionen erreichbar, keine garantiert unbesiegbaren Eröffnungen, PvP-Verlustregeln begrenzen Griefing, KI-Spawn-Budget nicht unendlich, Ressourcen/Power-Inflation auditierbar, niemals Pay-to-win.
- Spionage hat echten Informationswert ohne komplette Gratis-Enthüllung; Kampf soll unterschiedliche optimale Aufstellungen haben. Jede Einheit benötigt eine Rolle, Konter und Nutzbarkeit in wenigstens einem Szenario.
- Weltwirtschaft: Marktbilanz, NPC-Sinks, Ressourcenfaucets, maximal mögliche Gewinne, Depotgrenzen, Betrugs-/Botszenarien, Preisextreme. Simulationsbericht mit konkreten Defaults und Änderungsgründen.

## 5. Release-Gate und Artefakte
- Keine Blocker hoher Kritikalität. `FEATURES.json` zu 100% mit Code/UI/Policy/Test/Dokumentation nachgewiesen. Alle Tests erfolgreich (echte Kommandos und Logs, keine Dummy-Häkchen). Reproduzierbares Image, SBOM, Lizenz-/Asset-Freigaben.
- `RELEASE_CANDIDATE_REPORT.md`: Build/Commit/OS, exakte Kommandos, Testzahlen, Load-Resultate, bekannte Bugs, Real-World-Grenzen, Smoke-Screenshots, Screens-Liste, Dependency- und Lizenzreport, Restore, Integritätsprüfungen.
- `PERFORMANCE_REPORT.md`: Hardware, Version, DB-Größe, Szenarien, p50/p95/p99, Queue-Lag, Error Rate, Lastprofile, Bottlenecks, kapazitive Empfehlung vor Serverkauf.
- `SECURITY_REPORT.md`: Threat Model, Scans, Fix-Verweise, offene akzeptierte Risiken + Owner-Freigaben.
- `TRACEABILITY.md`: per Feature-ID implementierter Codepfad + Tests/Screen. `OWNER_HANDOFF.md` nur externe Voraussetzungen.
- `RESUME_STATE.json`: letztes abgeschlossenes Epic, nächste nicht verifizierte Feature-IDs, lokale Branch/Commit, Fehler/fehlende Rechte und reproduzierbare Testkommandos. Ein neuer Agent muss ohne erneutes Ratespiel fortsetzen können.
