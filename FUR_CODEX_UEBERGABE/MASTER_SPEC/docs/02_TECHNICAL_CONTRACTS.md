# FUR EMPIRE — VERBINDLICHE TECHNISCHE KONTRAKTE

**Zweck:** Engineering-Spezifikation für Coding-Agent, basierend auf dokumentiertem FUR-2-Spiel und dem neuen Master-GDD. Kein Ersatz für die Prüfung des echten aktuellen Repositorys.

## 1. Architekturentscheidung

**Default:** Den aktuell eingesetzten Python/FastAPI- und Worker-Stack beibehalten, sofern ein Repository-Audit ihn bestätigt. Nicht blind einen PHP-Laravel-Fork in FUR einbauen. Empfohlener Ausbau: FastAPI + Python 3.12/3.13 (vom vorhandenen Projekt unterstützte Version zuerst), SQLAlchemy/SQLModel bzw. bestehende DB-Abstraktion, Alembic-Migrationen, PostgreSQL als gemeinsame Server-Datenbank, Redis als Queue-/Cache-Option, klar getrennte Worker, WebSocket/SSE, moderne Templates/TypeScript oder bestehendes FUR-Frontend inkrementell. **Frontend-Technik durch Codeprüfung entscheiden**, nicht wegen eines Trends neu schreiben.

**Deployment:** Ein modularer Monolith mit getrennten Prozessen `web`, `world_worker`, `scheduler`, optional `realtime`, `database`, `redis`, `reverse_proxy`. Erst bei dokumentiertem Skalierungsbedarf Services auskoppeln. Klares Domain-/API-Modell und keine zyklischen Importe.

**Schnittstellenebenen:**

```text
Browser/PWA (untrusted)
   | HTTPS + CSRF + Session / WS auth
API & Controllers (validation, authorization, rate limits)
   | command/query buses, application services
Domain Core (world, economy, colony, research, units, combat, missions,
             orbit, alliances, politics, NPC, season, market, moderation)
   | transactions, deterministic ruleset, event/outbox
PostgreSQL  <->  World Worker/Scheduler  <->  Real-time event bus
   | audit, backup, metrics, snapshots, notifications
External adapters (SMTP, optional Discord OAuth/webhook, future payments disabled)
```

**Grenzen:** keine Spielelogik im Template, keine DB-Schreiboperation ohne Domain-Service, kein globales unsicheres Mutable-Objekt, keine Geheimnisse im Code, keine generischen Admin-Endpunkte ohne RBAC. Nutzer- und Weltidentität in *jeder* Anfrage und Query.

## 2. Basisstruktur (bei vorhandenen Ordnern anpassen)

```text
fur_empire/
  api/                       routers, schemas, policies, csrf, pagination
  domain/
    accounts/ worlds/ colonies/ economy/ buildings/ research/
    units/ missions/ battle/ espionage/ alliances/ diplomacy/
    markets/ npcs/ orbit/ events/ quests/ season/ leaderboard/
  application/               command handlers, query services, UoW
  infra/                     postgres repositories, redis, messaging, smtp
  rulesets/                  immutable, validated FUR-2, FUR-3, ORBIT-1
  worker/                    idempotent event processors, schedule jobs
  web/                       templates/static/i18n/assets, accessibility
  admin/                     RBAC, moderation, world ops, compliance
  telemetry/                 tracing/logging/audit
migrations/                   forwards+safe rollback or restore recipes
scripts/                      bootstrap, seed, backups, sanity tests
ops/                          compose, reverse proxy, runbooks
spec/                         feature definitions, ruleset JSON schemas
fixtures/                     combat replays, world seeds, scenarios
tests/                        unit, integration, e2e, perf, security
```

## 3. Multiworld und Datengrenzen

- Globale Account-ID (UUIDv7 oder UUID4), `world_id`, `world_player_id`, `colony_id`, `mission_id`, `command_id`/`idempotency_key`, `rule_version`, `event_id` nie als Benutzerinput vertrauen.
- Tabellen besitzen `world_id` wo Daten weltbezogen sind, und Fremdschlüssel/unique constraints verhindern weltübergreifenden Besitztransfer.
- `world_player` referenziert genau eine Fraktion pro Welt. `accounts` kann Mitglied mehrerer Welten sein, aber nur ein `world_player` je `(account_id, world_id)`.
- `world_type = permanent|seasonal|sandbox`; saisonales Ende darf nur Ressourcen der betroffenen Welt archivieren/resetten.
- Migration bestehender FUR-2-Spielstände **ohne irreversible Löschung**; Backup + Restore zuerst, Dual-Read/Dual-Write nur bei begründetem Bedarf, beim Feature-Switch replays und Datenintegrität vergleichen.

## 4. Normiertes Schema (Tabellen/Namen als Zielentwurf)

**Identity:** `accounts`, `account_emails`, `account_credentials`, `totp_secrets`, `recovery_codes`, `sessions`, `session_revocations`, `account_preferences`, `privacy_requests`, `notifications`, `notification_preferences`, `auth_audit`.

**Welten:** `worlds`, `world_rulesets`, `world_seeds`, `world_settings`, `world_players`, `world_regions`, `world_sectors`, `terrain_tiles`, `fog_observations`, `world_spawn_points`, `map_bookmarks`, `regional_control`, `world_event_instances`.

**Kolonien/Ökonomie:** `colonies`, `outposts`, `colony_buildings`, `colony_research`, `world_player_research`, `research_queue`, `building_queue`, `training_queue`, `resources_balances`, `resource_fraction_remainders`, `reserve_balances`, `resource_ledger`, `resource_reservations`, `energy_state`, `inventory_stacks`, `items`, `item_recipes`, `colony_transfers`.

**Krieg:** `unit_stacks`, `garrisons`, `defense_installations`, `missions`, `mission_participants`, `mission_cargo`, `mission_events`, `combat_instances`, `combat_rounds`, `combat_losses`, `combat_reports`, `combat_replays`, `espionage_reports`, `fog_snapshots`, `wreck_fields`, `repair_orders`, `supply_routes`.

**Orbit:** `star_systems`, `orbital_positions`, `orbital_bodies`, `orbital_colonies`, `orbital_buildings`, `starships`, `fleets`, `fleet_composition`, `fleet_missions`, `fleet_unions`, `orbital_sensors`, `jumpgates`, `jumpgate_cooldowns`, `orbital_debris`, `orbital_expeditions`, `orbital_reports`, `moons`.

**Allianz/Sozial:** `alliances`, `alliance_members`, `alliance_roles`, `alliance_permissions`, `alliance_invitations`, `alliance_applications`, `alliance_treaties`, `alliance_wars`, `war_objectives`, `war_scores`, `alliance_projects`, `alliance_treasury`, `alliance_treasury_ledger`, `friendships`, `blocked_players`, `personal_notes`, `alliance_forums`, `forum_threads`, `forum_posts`, `chat_channels`, `chat_memberships`, `messages`, `message_reads`, `message_reports`.

**Progression/Service:** `quest_defs`, `quest_progress`, `achievement_defs`, `achievements`, `seasons`, `season_participants`, `season_snapshots`, `season_results`, `hall_of_fame`, `npc_factions`, `npc_bases`, `npc_strategies`, `npc_orders`, `event_templates`, `player_rewards`, `highscore_snapshots`, `event_outbox`, `world_jobs`, `idempotency_records`, `operator_audit`, `moderation_cases`, `bans`, `appeals`, `feature_flags`, `job_failures`, `world_snapshots`, `backup_restore_checks`.

**Migrationsregeln:** Money/Resources sind Integer in kleinstmöglicher Ressourceneinheit, Restproduktion DECIMAL/Integer-Bruchnumerator (keine Float-Rundungsfehler), UTC-Timestamps mit Zeitzone, explizite `CHECK amount >= 0`, `CHECK capacity >= 0`, FK-Integrität, DB-Unique für Standorte und Einmalclaims. Tabellen zum Archivieren je `world_id` indexieren; `ON DELETE CASCADE` nie bei Kostenbuchungen ohne archiviertes Ledger nutzen. Spielerbezogene PII getrennt von dauerhaften Spielstatistiken und mit Löschplan.

## 5. Spiel-Befehle und Read-Modell

**Command Envelope:**

```json
{
  "command_id": "uuid",
  "world_id": "uuid",
  "actor": "server_session_identity",
  "action": "mission.dispatch",
  "resource_version": 17,
  "payload": { "origin_colony_id": "uuid", "target_sector": [20, 7], "units": { "ranger": 15 } }
}
```

`actor` wird serverseitig aus Session/Token ermittelt und niemals aus Body vertraut. Alle schreibenden Browser-Requests erfordern CSRF-/SameSite-Schutz, Origin- und Berechtigungsprüfung. `command_id` und eindeutige DB-Constraints garantieren Replayschutz; identische Wiederholung gibt denselben gespeicherten Erfolg zurück; gleiche ID mit verändertem Payload führt zu `409 Conflict`.

**Event Envelope:**

```json
{
  "event_id":"uuid", "schema_version":1, "event_type":"mission.arrived",
  "world_id":"uuid", "aggregate_type":"mission", "aggregate_id":"uuid",
  "occurred_at":"2026-11-06T09:00:00Z", "due_at":"2026-11-06T09:00:00Z",
  "causation_id":"uuid", "correlation_id":"uuid", "ruleset_sha256":"hex",
  "payload": { "mission_id":"uuid", "state":"arrived" }
}
```

Alle fälligen Aufgaben durch Worker-Poll/Queue `FOR UPDATE SKIP LOCKED`/Lease übernehmen, DB-transaktional abschließen, `outbox` erst nach Commit publishen. Bei Lease-Ablauf retry; Dead-letter nach begrenzten Fehlversuchen, Admin-Replay nur mit Validierungs-/Idempotenzgarantie. Kein clientseitiger `setTimeout` als einzige Zustandsänderung.

## 6. Ressourcen-Ledger und Produktionskontrakte

- Jede Änderung hat `tx_id`, `world_id`, `owner_id`, `colony_id`, `resource`, `delta`, `source`, `cause_id`, `balance_after`, `created_at`, `ruleset_version`. Nicht negativ, vollständiger Audit.
- Reservierung und Verbrauch atomar: `SELECT ... FOR UPDATE`, Rate/Cost serverseitig, `available_balance` prüfen, Reservation erstellen, keine Doppelbuchung; Fehler führt zu vollständigem Rollback.
- Transfer: Sender-Debit sofort, Cargo-Escrow während Marsch, Empfänger-Credit erst nach legitimer Ankunft; Return-Event/Cancellation idempotent, Empfang bei vollem Depot ins Reserve-Lager; nie beide aufgelösten Routen gleichzeitig.
- Produktion: `produced = floor((elapsed_ms * per_second_numerator + remainder) / rate_denominator)`; Zeitverschiebung der Uhr verhindern; Wert nur bis Lagercap gutschreiben, Rest nicht still ins Reserve-Lager, wenn Produktionslimit erreicht (im Gegensatz zu Lieferrückständen); Pausen im Urlaub ausklammern. `effective_at` für Regeln/Ereignisse, die zwischen zwei Besuchen starten/enden, in Segmenten integrieren.
- Warenmarkt: `open -> reserved/accepted/cancelled/expired`, Verkaufspreis und Ressourcenreserve atomar, Käufer und Verkäufer gelockt in stabiler ID-Reihenfolge, `unique(trade_execution.offer_id)`.
- FUR-2-Direktive: `unique(world_player_id, directive_id)`; Versand einer Belohnung ins Reserve-Lager nur einmal.

## 7. Bau-, Forschungs-, Ausbildungs- und Warteschlangen

- Queue-Item: `queued -> active -> completed` / `cancelled|failed`; bei Start die Regelversion mit Kosten, prerequisites und Dauer pinnen. `active`-Uniqueness pro erlaubtem Slot/Scope. Nach Abschluss einzigen Levelzuwachs; Outbox-Event `building.completed`, `research.completed`, `training.completed`.
- Je Kolonie der FUR-2-Default für aktive Bau-/Forschungs-/Ausbildungsqueue, neue Planungs-Slots als konfigurierter FUR-3-Wert. Skill-Voraussetzungen und Inventar-Verbrauch beim Start erneut prüfen.
- Stornierung: falls vor Start keine Kosten oder eindeutige Release-Funktion; während Produktion nur definierte Teilkosten zurück, nie mehr als verbraucht. Umordnung nur pending und atomar.
- Worker darf Abschluss für gelöschte/umgezogene Kolonie nicht blind durchführen. Referenzen/Tombstones und Kompensationsereignisse anwenden.

## 8. Missionen und Kampfvertrag

**Mission dispatch:** Session -> world/player/ownership -> treaty/protection -> origin/speed -> target/visibility -> available troops -> cargo/energy -> active mission limit -> transaction reserve troops/resources -> mission entry -> outbox. Alle Prüfungen beim Start und bei Ankunft, die auf zwischenzeitlichen Weltstatus angewiesen sind.

**Kampfreplay:** `battle_version`, `participants`, `initial_state`, `commitment`, `rng_seed`, `rounds`, `final_state`, `loot`, `wreck`, `owner_changes`, `rule_hash`. Dieselbe Simulation muss mit identischem Seed bitgenau identisches Resultat liefern. `dry_run` erzeugt keinerlei Ledger- oder Besitz-Änderung. Sieger-/Besatzungseffekt erst nach Commit und nur, wenn Eroberungsbedingungen gültig sind.

**Schlachtatomizität:** Truppenverluste, Gebäude-/Schildstatus, Loot, Besatzung, Wrecks, Berichte und veranlasste Rückkehr in **einem** konsistenten Verarbeitungsablauf, idealerweise DB-Transaktion plus outbox. Keine Teilbuchungen bei Exceptions. Gleicher Zielzustand wird in festen Sperren verarbeitet; Transaktions-Deadlocks unter Retry mit Jitter behandeln.

**Anti-Abuse:** Besitzer darf keine fremden Einheiten senden; Truppenanzahl kann nicht negativ/NaN/unendlich sein; Mission nicht doppelt starten/abbrechen; undefinierte Zieltypen werden abgewiesen; Gegner im Urlaub, NAP und Neulingsschutz sind geschützt; keine Forschung/Spielzeug-Ids per client trusted.

## 9. API-Kontrakt v1 – Hauptendpunkte

Alle Endpunkte unter `/api/v1` mit paginierter, typisierter Antwort, stabilem Fehlercode und `request_id`. Spezifikation als OpenAPI generieren, Schemas in Tests snapshotten. In Klammern: HTTP-Methode.

**System/Account:** `/health/live` (GET), `/health/ready` (GET), `/system/version` (GET), `/auth/register` (POST), `/auth/login` (POST), `/auth/logout` (POST), `/auth/me` (GET), `/auth/email/verify` (POST), `/auth/recover/start` (POST), `/auth/recover/complete` (POST), `/auth/totp/enroll` (POST), `/auth/totp/confirm` (POST), `/auth/sessions` (GET/DELETE), `/account/preferences` (GET/PATCH), `/account/privacy/export` (POST), `/account/privacy/delete-request` (POST).

**Welten/Karten:** `/worlds` (GET), `/worlds/{world_id}/join` (POST), `/worlds/{id}/rules` (GET), `/worlds/{id}/map/tiles` (GET), `/worlds/{id}/map/sector/{x}/{y}` (GET), `/worlds/{id}/map/bookmarks` (GET/POST/DELETE), `/worlds/{id}/regions` (GET), `/worlds/{id}/orbit/systems` (GET), `/worlds/{id}/status` (GET).

**Imperium/Economy:** `/w/{world_id}/dashboard` (GET), `/w/{id}/colonies` (GET/POST), `/w/{id}/colonies/{cid}` (GET/PATCH), `/w/{id}/colonies/{cid}/relocate` (POST), `/w/{id}/colonies/{cid}/abandon` (POST), `/w/{id}/colonies/{cid}/resources` (GET), `/w/{id}/colonies/{cid}/storage/claim` (POST), `/w/{id}/colonies/{cid}/buildings` (GET), `/w/{id}/colonies/{cid}/build-queue` (GET/POST/PATCH/DELETE), `/w/{id}/colonies/{cid}/research` (GET), `/w/{id}/research/tree` (GET), `/w/{id}/research/queue` (GET/POST/DELETE), `/w/{id}/colonies/{cid}/training` (GET/POST/DELETE), `/w/{id}/trade/instant` (POST), `/w/{id}/market/offers` (GET/POST), `/w/{id}/market/offers/{offer_id}/accept` (POST), `/w/{id}/market/offers/{offer_id}` (DELETE), `/w/{id}/market/history` (GET), `/w/{id}/inventory` (GET), `/w/{id}/crafting` (POST).

**Militär/Missionen:** `/w/{id}/units/catalog` (GET), `/w/{id}/missions/catalog` (GET), `/w/{id}/missions` (GET/POST), `/w/{id}/missions/{mid}` (GET), `/w/{id}/missions/{mid}/recall` (POST), `/w/{id}/missions/{mid}/intercept` (POST), `/w/{id}/garrisons` (GET/POST/DELETE), `/w/{id}/espionage/reports` (GET), `/w/{id}/combat/simulate` (POST), `/w/{id}/combat/reports` (GET), `/w/{id}/combat/reports/{rid}` (GET), `/w/{id}/combat/reports/{rid}/replay` (GET), `/w/{id}/alliance/operations` (GET/POST), `/w/{id}/alliance/operations/{oid}/join` (POST).

**Allianz/Social:** `/w/{id}/alliances` (GET/POST), `/w/{id}/alliances/{aid}` (GET/PATCH), `/w/{id}/alliances/{aid}/members` (GET), `/w/{id}/alliances/{aid}/invites` (POST), `/w/{id}/alliance/invites/{iid}/accept` (POST), `/w/{id}/alliances/{aid}/roles` (GET/POST/PATCH), `/w/{id}/alliances/{aid}/treaties` (GET/POST), `/w/{id}/alliances/{aid}/wars` (GET/POST), `/w/{id}/alliances/{aid}/depot` (GET/POST), `/w/{id}/alliance/forums` (GET/POST), `/w/{id}/chat/channels` (GET), `/w/{id}/chat/{channel}/messages` (GET/POST), `/w/{id}/messages` (GET/POST), `/w/{id}/messages/{msg_id}` (GET/DELETE), `/w/{id}/friends` (GET/POST/DELETE), `/w/{id}/notes` (GET/POST/PATCH/DELETE).

**Progression/Orbit:** `/w/{id}/quests` (GET), `/w/{id}/quests/{qid}/claim` (POST), `/w/{id}/achievements` (GET), `/w/{id}/leaderboard` (GET), `/w/{id}/hall-of-fame` (GET), `/w/{id}/seasons` (GET), `/w/{id}/events` (GET), `/w/{id}/orbit/colonies` (GET/POST), `/w/{id}/orbit/fleets` (GET/POST), `/w/{id}/orbit/missions` (GET/POST), `/w/{id}/orbit/wrecks` (GET), `/w/{id}/orbit/sensors` (POST), `/w/{id}/orbit/jumpgate` (POST).

**Admin:** `/admin/whoami` (GET), `/admin/worlds` (GET/POST/PATCH), `/admin/worlds/{id}/ruleset` (POST dry-run, POST publish), `/admin/worlds/{id}/seasons` (POST), `/admin/events` (POST/PATCH), `/admin/players` (GET), `/admin/players/{id}/sanctions` (POST), `/admin/audit` (GET), `/admin/moderation/reports` (GET/PATCH), `/admin/jobs` (GET), `/admin/jobs/{id}/retry` (POST), `/admin/worlds/{id}/integrity-check` (POST), `/admin/backups` (GET/POST), `/admin/backups/restore-test` (POST), `/admin/announcements` (POST), `/admin/feature-flags` (GET/PATCH).

**Errorformat:** `{ "error": { "code":"INSUFFICIENT_RESOURCES", "message":"...", "details":{}, "request_id":"..." } }` — kein Stacktrace; `401` unauthenticated, `403` owner/role/treaty, `404` conceal private resource, `409` conflict/idempotency, `422` validation, `429` rate-limit. Alle GETs read-only, alle mutierenden Aktionen POST/PATCH/DELETE mit CSRF und Rollenprüfung. Für einen externen API-Client gesonderter OAuth2-/Token-Scope.

## 10. Websocket/SSE

`/api/v1/events/stream` authentifiziert per Session/kurzlebigem Eventtoken, pro `world_id`, autorisiertem Kanal und Last-Event-ID. Typen: `mission.updated`, `resource.updated`, `queue.completed`, `battle.reported`, `alliance.operation`, `chat.message`, `world.event`, `season.updated`, `announcement`, `security.session`. Payload immer minimiert; private Infos nicht in globalen Broadcast; Sequenznummer+Replay/Delta-Fetch bei Verbindungsabbruch. Rate/Message Caps und Polling-Fallback.

## 11. Spielregeln als Daten

`ruleset` enthält alle aktiven Formeln (Formel-ID + Version + überprüfbare Parameter), Definitionen für Gebäude, Forschung, Units, Terrain, Kampf, NPC, Quests, Markt, Kolonien, Orbit; deterministischer Serializer, SHA-256 signiert/gespeichert mit Veröffentlichung, Fixtures und Migration. **Ein Regelwechsel darf nicht rückwirkend laufende Missionen im alten RuleSet ändern**, außer es existiert ein auditierter expliziter Migrationspfad.

Beispiel: `FUR-2` reproduziert historische Rohstoffe/Events; `FUR-3` ergänzt abnehmende Außenpostenboni, Kampf-Engine v3, Erweiterungsgraph und PvP-Schutz. Agent darf nicht pauschal durch `max_level=20` alte Spielerobjekte ohne Policy ändern. `rulesets/` enthält JSON-Schema und Unit-/Invariant-Tests.

## 12. End-to-end Fehler- und Integritätsmodelle

- Doppelklick Marktkauf: nur eine Annahme, keine doppelte Auszahlung; Auftragsstatus stabil.
- Zwei Spieler kolonisieren dieselbe Kachel gleichzeitig: exakt einer gewinnt, beide erhalten deterministisches Ergebnis.
- Zwei Angriffe bei gleicher Ankunftssekunde: feste Event-ID-Tiebreak-Reihenfolge, kein doppelt abgezogener Verteidiger.
- Worker stirbt beim Kampf: wiederholtes Abarbeiten erzeugt exakt **eine** Schlacht, Berichte und Rückweg.
- Spielregel während Reise geändert: gepinnte Regelversion oder explizite Migrationsentscheidung, kein heimlicher Replay-Bruch.
- Urlaub aktiviert während Angriff: Aktivierung blockiert, solange gültige feindliche Angriffsmissionslage vorhanden.
- Allianzpakt während Marsch aufgelöst: Start-/Ankunftspolitik definieren und Replay-Test.
- Rückkehrende Ressourcen überfüllen Lager: überschüssige Lieferrückstände ins Reserve-Lager, produzierte Rohstoffe laufen bis Cap und gehen nicht unendlich ins Reserve-Lager.
- Regeltext ohne echte UI, nicht erreichbare Buttons, tote Links, unübersetzte Strings: E2E-/UI-Test muss fehlschlagen.
- Löschen/Anonymisieren: keine referenzierten Kampfberichte zerstören oder personenbezogene Inhalte unzulässig weiter speichern.
- Saisonende: Dauerwelt **unverändert**, archivierte Rangliste vollständig, neue Saison ohne alte Waren.

## 13. Verfügbarkeits- und Performance-Ziele

**Vorläufige messbare Abnahmeziele für eine einzelne VPS-/Root-Deploymentklasse**, erst nach realem Lasttest als Zusage verwendbar: 200 gleichzeitig aktive Benutzer mit 1.000 bereits registrierten Testspielern; P95 für standardmäßige Dashboard-Reads <500 ms auf definierter Testhardware, Map-Fenster P95 <800 ms, Action-API P95 <800 ms ohne lange Schlacht, kritische Queue-Abwicklung binnen 5 Sekunden bei gewöhnlicher Last, keine verlorenen Missions-/Ledger-Einträge in 30-minütigem Lastlauf. Definierte Testhardware, Seeds und Lastprofil in `PERFORMANCE_REPORT.md` angeben; Werte nicht einfach als bestanden markieren. Backups täglich + Point-in-Time-Wiederherstellung soweit vom gewählten DB-Setup unterstützt, Restore-Test in isolierter Instanz, Alert bei ausbleibendem Worker, Fehler-Rate-Schwellen als Monitoring Rules.

## 14. Quell-/Rechtskontrakt

Keine Assetübernahme aus fremden Browsergames, kein XG GPL/AGPL-Code in den privaten FUR-Kern ohne Lizenzstrategie, kein devana-Code ohne Bedingungen, kein CC BY-NC-ND-Code. Neu implementierte Spielkonzepte dokumentieren; eventuelle MIT-Snippets nur mit Copyright, Lizenz und Datei-/Commit-Provenienz. `docs/06_SOURCE_LICENSE_REGISTER.md` ist bindend.
