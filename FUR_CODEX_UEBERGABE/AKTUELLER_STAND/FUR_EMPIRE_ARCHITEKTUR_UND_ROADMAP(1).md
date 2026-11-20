# FUR Empire — Architektur- und Entwicklungsplan

> **Fortschrittsabgleich vom 5. November 2026:** Dieser Plan entstand für Genesis 0.1 und beschreibt nicht mehr den aktuellen Bestand. Die spätere Umsetzung umfasst inzwischen PostgreSQL-Migrationen, getrennte App- und Worker-Dienste, Mehrspielerangriffe, Transporte, Allianzen, Diplomatie, Nachrichten, Spielermarkt, Spielleitung, Saisonverwaltung und Kontosicherheit. Die lokale Anwendung nutzt weiterhin SQLite. Maßgebliche aktuelle Spezifikation: `docs/game-design/FUR_EMPIRE_SPEC.md`; Architektur: `docs/architecture/ARCHITECTURE.md`. Roadmap-Punkte sind geplante Ziele, keine Betriebsnachweise. Das Prüfarchiv liegt unter `Neuer Ordner/`; fremde Implementierungen oder Assets werden nicht ungeprüft in FUR übernommen.

## Zielbild

Ein dauerhaft laufendes Online-Strategiespiel mit Territorien, Außenposten, Wirtschaft, Aufträgen, Forschungsbäumen, Allianzen, Fraktionen und asynchronen Konflikten. Das Spiel bekommt **eigene** Spielwelt, UI, Einheiten, Zahlenwerte und Assets; es ist kein Re-Skin eines anderen Spiels.

## Domänenstruktur (Zielarchitektur)

```
Browser / Mobile UI
  ↓ HTTPS / Session / CSRF / Rate limit
Game API ── Auth/RBAC ── Audit log
  ├─ Worlds / Map / Territories
  ├─ Economy / Production / Inventory
  ├─ Construction / Recruitment / Research
  ├─ Command / Missions / Battle / Reports
  ├─ Alliances / Diplomacy / Trade / Chat
  ├─ Events / Seasons / Rewards
  └─ Administration / Moderation / Configuration
       ↓               ↓                ↓
  PostgreSQL       Job Queue        Redis Cache
       ↓               ↓
  Transactional   Dedicated Worker
  persistence     + Idempotent jobs
```

### Warum aktuell FastAPI statt eines Forks von OGameX?

Der neue Prototyp ist bewusst **eigener Code**, weil mehrere angegebene Projekte unter GPL/AGPL/unklaren Lizenzen stehen und andere historische Fremdgrafiken enthalten. FastAPI erlaubt einen kleinen, überprüfbaren ersten vertikalen Schnitt. Für eine direkte OGameX-Forkstrategie wäre Laravel 13 / PHP 8.5 notwendig und die Artwork-Rechte wären vollständig zu trennen. **Das Framework ist keine irreversible Entscheidung**: Eine Domain API mit versioniertem Eventmodell lässt sich später auf Laravel oder einen Dienstverbund portieren.

## Produktkonzept — Eigenständigkeit

- **Name / Setting:** FUR EMPIRE: Grenzgebiete einer zusammenbrechenden Cyber-Welt, befestigte Außenposten, Fraktionskämpfe, Kommandozentralen.
- **Wirtschaft:** Holz (Baustoff), Stein (Befestigung), Erz (Rüstung und Technik), später Energie und Daten.
- **Territorien:** koordinatenbasierte Karte mit Bodentypen, Wasser, Relaisnetzen, Rohstoffanomalien und strategischen Engstellen.
- **Kampf:** Sektorüberfall, Sektorbesetzung, Verteidigung, Versorgung und Allianzangriffe; v0.1 enthält nur einen einfachen Raid.
- **Forschung:** Militärtaktik, Logistik, Ingenieurswesen, Aufklärung, Netzwerke.
- **Community:** Allianzen mit Rollen, gemeinsamem Inventar, Eventleitstand, Discord-Bot und Saison-Ligen.
- **Live-Events:** Adminregeln steuern begrenzte Ereignisse, Wetter-/Umweltfaktoren, Ressourcenboni und Fraktionsziele.

## Transaktionale Invarianten

1. Kein Rohstoff- oder Truppenbestand wird negativ.
2. Jeder Spielbefehl wird serverseitig validiert und einem Eigentümer zugeordnet.
3. Gleichzeitige Befehle dürfen Ressourcen/Einheiten nicht doppelt ausgeben (in v0.1 `BEGIN IMMEDIATE`; später PostgreSQL-Zeilenlocks plus Tests).
4. Derselbe Auftrag darf nur einmal abgeschlossen werden; Jobstatus wird mit seinem Effekt atomar gespeichert.
5. Zeitgeber beziehen sich auf die Serverzeit und nicht auf Browserwerte.
6. Reproduzierbare Schlachten brauchen festgelegte Regelversion, Seed und vollständige Eingabedaten.
7. Buchungen, Missionsänderungen und Adminaktionen werden langfristig durch ein unveränderliches Auditlog nachvollziehbar.
8. Berechnung und Darstellung bleiben getrennt, damit die UI austauschbar ist.

## Versioniertes Regel-/Objektregister

Die aktuelle `game.py` enthält ein kleines Objektregister. Ziel: unabhängige JSON/YAML-Daten für `BUILDINGS`, `UNITS`, `TECH`, `TERRAIN`, `RULESETS` mit Schemaprüfung. Eine Welt wird mit einer Regelversion gestartet und bleibt während einer Saison reproduzierbar. Konfigurationen werden nicht ungeprüft live auf laufende Events angewendet.

## Datenmigration

- **Alpha:** SQLite und einfache Tabellen, weil lokal sehr leicht zu installieren.
- **Beta:** PostgreSQL, Alembic-Migrationen, Foreign Keys, Unique Constraints, partieller Index pro Queue und Outbox-Pattern.
- **Produktion:** getrennte Worker, persistente Jobwarteschlange, Monitoring, Backups mit Restore-Proben, separate Datenbankrollen, Redis nur als Cache – nicht als alleinige Quelle der Wahrheit.

## Security- und Operations-Checkliste

- [x] Argon2-Passworthashing, Session-Token nur als Hash in DB gespeichert
- [x] HttpOnly + SameSite-Cookie, `COOKIE_SECURE=1` für HTTPS-Deployment vorgesehen
- [x] CSRF-Schutz für authentifizierte Mutation-Endpunkte
- [x] Besitzprüfung für Kolonien, serverautoritatives Regelwerk
- [x] Parameterisierte SQL-Abfragen; dynamische Feldnamen stammen nur aus der eigenen geprüften Whitelist
- [x] Idempotenzschlüssel mit Befehlssignatur gegen unerwünschte Wiederholungen
- [x] Security-Header, CSP, keine fremden Script-CDNs
- [x] Automatisierte Tests für grundlegende Rechte, Jobs, Ressourcen und Kämpfe
- [ ] Login-/Registrierungs-Rate-Limits; CAPTCHA/Abuse-Protection wo notwendig
- [ ] E-Mail-Verifizierung, Passwort-Reset, MFA für Administratoren
- [ ] Schließung von Anmelde-/Session-CSRF- und Origin-Randfällen im Proxybetrieb
- [ ] Auditlog für alle spielrelevanten Buchungen, Adminaktionen, Moderationsereignisse
- [ ] Logging/Tracing, Dead-Letter/Retry-Strategie, Alarmierung, Backups
- [ ] PostgreSQL-Parallelitätstests, Property-based Tests und Lasttests
- [ ] Vollständige Altersfreigabe-/Datenschutz-/Community-Rechtsprüfung

**Niemals:** reale Passwörter, Discord-Token, GitHub-PATs oder andere Secrets in Git speichern. Vor dem Deployment über Secret-Store injizieren. Sämtliche vormals veröffentlichten oder unkontrolliert weitergegebenen Tokens rotieren.

## Ausbaustufen

| Stufe | Inhalt | Abnahmekriterium |
|---|---|---|
| 0.1 — Genesis | Login, Kolonie, 3 Rohstoffe, Bau-/Forschungs-/Truppenqueue, Raid, Weltkarte | 8+ automatische Tests; zwei Spieler können interagieren |
| 0.2 — Core | PostgreSQL, Migrations, Background Worker, Config-/Testdaten, Bau- und Forschungsverzweigungen | 100+ parallele Aktionen ohne Doppelbuchungen |
| 0.3 — Warfare | versionierte Kampfengine, Truppenstats, Rückwege, Garnisonen, Verteidigungsboni, Reports | deterministische Roundtrip-Tests |
| 0.4 — World | prozedurale Welt, Terrain, Handel, Gebietseroberung, Transport-/Versorgungswege | 1.000+ Zonen mit verlässlicher Verarbeitung |
| 0.5 — Clans | Allianzen, Rollen, Diplomatie, Nachrichten, Moderation, Discord-OAuth | authentifizierte Community-Rollen und Auditlogs |
| 0.6 — LiveOps | saisonale Events, Admin-Dashboard, Feature Flags, Weltregeln, Mehrsprachigkeit | Events deterministisch und ohne manuelle Datenbankeingriffe steuerbar |
| 1.0 — Launch | Belastung, Sicherheit, Restore, Betrieb, Lizenz-/Markenprüfung, Monitoring | dokumentierte Freigabekriterien erfüllt |

Zeilen wie "100+ parallele Aktionen" sind **zukünftige Abnahmeziele**, keine bereits gemessenen Leistungswerte.
