# FUR EMPIRE — GAMEPLAY-REGELDETAILS UND ZUSTANDSAUTOMATEN

Dieses Dokument ergänzt das GDD mit Zuständen, Abbruchpfaden und Default-Regeln für eine robuste Agentenimplementierung. Ursprungsdaten FUR-2 sind in `rulesets/FUR_2_REFERENCE_RULES.json` getrennt von **neuen, vorgeschlagenen** Defaults in `FUR_3_ORBIT_1_PROPOSED_RULES.json`. Die neuen Balancewerte sind keine bezeugten Altweltwerte; vor Release simulieren und per Ruleset-Version fixieren.

## 1. Welt und Kolonie — Objektlebensläufe

`World`: `planned → generating → verified → online ↔ maintenance → frozen → archived`. Für permanente Welten ist kein automatisches Reset erlaubt. Ein neues Weltobjekt besitzt `seed, width,height, generation_version, ruleset_hash, server_timezone_display, world_type` und einen streng isolierten Datenraum.

`WorldPlayer`: `invited/registered → onboarding → active ↔ vacation → suspended → anonymized`. Weltjoin erstellt **genau eine** Startkolonie über atomare Reservierung. Fraktionswahl ist einmalig; Respec existiert nur in neuem Regelmodus, mit sichtbarem Preis und Cooldown.

`TerraSector`: `unexplored | free | neutral_outpost | player_colony | player_outpost | ruins | protected | impassable`. Besitzwechsel benötigt Sperre und gleichzeitig gültige Besitz-/Mission-/Diplomatie-Policies. Unbekannte Kacheln zeigen keine geheimen Einheitendaten.

`Colony`: `establishing → active → relocation_pending | abandon_pending → abandoned`; letzte Kolonie niemals aufgebbar, offene Bau-/Trainings-/Forschungs-/Missionsevents sicher kompensieren. Outposts sind keine Vollkolonien; Upgrade zu Kolonie kostet selbstständigen Kolonieslot.

## 2. Ressourcentransaktionen

`wallet/resource`: `available`, `reserved`, `in_transit`, `reserve`, `spent` als **separate Buchungsstatus**, nicht willkürliche Feldänderung. Für jede Aktion ist Ledger-Summe korrekt: Ein Kauf verschiebt Wert aus Spieler-Guthaben in Anbieter-Escrow, später nur einmal zum berechtigten Empfänger. NPC-Belohnungen sind explizite Faucet und Bau/Truppen sind explizite Sink.

Produktionsintegration: `elapsed = monotonic server time derived from UTC corrected transitions`; berechne exakte Segmente für Urlaub, Buffstart und Ende. Nutze feste Bruchzahlen statt Float-Rundung, belohne nicht bei häufigem Browser-Polling.

`MarketOffer`: `open → accepted | expired | cancelled | administratively_frozen`. Kauf und Cancel parallel: genau ein Endzustand. TTL 24h aus FUR-2; Mengen/Caps nach Welt-Regeln. Duplikate und Marktmanipulationen prüfen.

`CraftOrder`: `queued → running → completed | cancelled | failed`; Inputs atomar escrowed, Output bei Completion einmal credited; Recycler darf keine Materialschleife mit Netto-Gewinn erlauben.

## 3. Gebäude, Forschung, Produktion

`QueueItem`: `pending → running → completed`; von `pending/running` kann je Regeln `cancelled` entstehen; `failed` nur intern mit Wiederaufnahme-/Refundpfad. Zeitfortschritt aus Worker. Gleicher Command mehrfach hat immer dieselbe Wirkung. Forschungsvoraussetzungen gegen Serverkatalog; abgebrochener Erzeuger darf bereits laufende Forschung nicht in unbestimmten Zustand bringen (Policy je Regelversion).

Energie: in FUR-3 pro Kolonie Energieproduktion und Verbrauch, unter Energiemangel ordentliche priorisierte Drosselung bis auf konfigurierten Mindestwert; im FUR-2-Bestand keine rückwirkende Energiedrosselung. Unterhalt darf nie zu negativem Kontostand führen; stattdessen `depleted`/begrenzte Performance/Safe-return.

Technologieeffekt-Caps und die genauen Bau-/Forschungskosten stehen im versionierten Regelkatalog; Einheiten- und Bauobjekte tragen stabile IDs, keine UI-Positions-IDs.

## 4. Transport und Missionen

`Mission`: `draft → dispatched → travelling_out → arrival_pending → resolving → returning → completed`; Alternativzustände `cancel_requested → returning | cancelled`, `failed_retryable`, `failed_terminal` mit kompensierter Waren-/Truppenbilanz. Jeder Übergang als atomarer Domain-Event mit Unique-Key und Outbox.

Bei Dispatch: aktive Missionscap, Herkunfts- und Zielbesitz, freie Units, Fuel/Cargo, Pakt/PvP/Urlaub/Neulingsschutz, Rate Limit, vollständige Ressourcenreservierung, due_at, ruleset-hash. Bei Ankunft dynamische Policy nochmals prüfen; illegale Attacken werden sicher zurückgerufen. Bei Rückkehr ins volle Depot überschüssige **Lieferungen** in Reserve, während passive Produktion am Cap stoppt.

`AllianceOperation`: `assembling → locked → travelling → resolving → returning → completed | cancelled`. Join nur während Assembling, Membership/Owner und Startzeit validieren; Ankunft synchronisieren; Teilnehmeranteil und eventuelles Loot pro Besitzer deterministisch und rechtmäßig zuweisen.

## 5. Kampfsystem FUR-3

- Kampf startet nur aus gültiger Mission, nach Sperrung auf Ziel/Teilnehmer, mit gepinnter Regelversion.
- Bis zu sechs Runden mit gemeinsamen Frontstapeln; konkrete Reihenfolge: Initiative und target policy; Treffer mit versioniertem RNG, dann Schild, Panzerung, Hülle; nach jeder Runde Tote und Spezialeffekte; Rückzug entsprechend Policy.
- Kein Sieger bei Gleichstand nach Rundenlimit: Verteidigungsposition bleibt erhalten. Eroberung erst mit eigenem Belagerungsziel und gültiger Einheit nach dem Kampf.
- Jede Runde erzeugt Replaydaten, State-Hash und Verlustliste. Renderer bekommt nur autorisierten Bericht; Spionage bestimmt Datenfreigaben.
- `simulate` läuft in reinem Modul ohne Speichern, Zahlentransfer oder Loot-Abzug.
- Übermacht darf nicht automatisch Endlosdominanz erzeugen: Combat-Log-Balance, Attrition und Recovery-Caps werden in Simulationsberichten beobachtet.

## 6. Orbit und Flotten

`OrbitalBody`: `unknown → discovered → claimable → colonization_reserved → occupied | abandoned | destroyed`. Uniqueness `(world_id,galaxy,system,slot)`; Mond/Stationen referenzieren parent-orbital-body. Ein Flug nimmt Fuel und Einheiten nur einmal ab; Cargo wird als Escrow bewegt.

`FleetMission` übernimmt die Basiszustände der Terra-Mission. `Jumpgate`: `ready → transfer_resolving → cooldown → ready` mit Atomic Lock über beide Tore; no two concurrent jumps of same fleet. Trümmerfeld hat Masse, Claim-/Salvage-Transaktionen und Ablauf. Alle Operationen in Orbit teilen dieselbe Konto-/World-Policy und Auditlogs.

## 7. Allianz, Krieg und Diplomatie

`Invitation`: `pending→accepted | rejected | expired | revoked`. `Treaty`: `proposed→accepted→terminated | rejected | expired`, unilateral `war_declared` mit War-Notice und regelkonformen Schutzperioden. `War`: `declared→active→ceasefire→settled→archived`; Punkteregel, Siegziele und Beitrag nachvollziehbar.

Allianzkasse: jeder Beitrag/Sink im eigenen Ledger; große Entnahmen per Vier-Augen-Genehmigung, Anfragen haben Ablauf und können nicht doppelt freigegeben werden. Führungstransfer erfordert Zielbestätigung und schließt die letzte-Leitung-Lücke.

## 8. Welt-Events, NPC und Quests

`WorldEvent`: `draft→scheduled→announced→active→resolving→finished→archived | cancelled`. Boni zeitsegmentiert und gedeckelt. `NPCOrder`: Spawn-/Move-/Raid durch begrenzte Worker-Budgets, reproduzierbare Seeds, keine Kolonieüberschreibung.

`Quest`: `locked→active→completed_unclaimed→claimed`; Belohnung darf nur einmal vergeben werden; tägliche/wöchentliche Versionen haben UTC-Reset und idempotente Claim-ID. `Season`: `scheduled→active→finalizing→archived`, Abschluss nur genau einmal mit eingefrorener Rangliste.

## 9. Game Balance und Fairness

- Spieler bleiben nach Niederlage spielbar. Neue Welten: Anfänger-Schonfrist, Powerband, Recovery-Cooldown. Bestehende FUR-2-Welten bekommen nicht still eine geänderte 1h-Regel.
- Outposts generieren im FUR-2-Modus keine Bestände neu; neue Welten verwenden nachwachsende neutrale unbesetzte Ziele, ROI-Budgets und Outpost-Bonus-Sättigung. Für Migrationswelten kann der Admin eine neue Regelversion bewusst aktivieren.
- Jede Rolle muss einen Gegen-/Nutzeneffekt besitzen. Kein globaler Kampfverstärker ohne Limit. Kein Echtgeld-Pay-to-win.
- Balancing ist ein laufender Entwicklungsprozess mit Simulation, aber vor Release wird ein getesteter Regelstand eingefroren.

## 10. Minimale, testbare Spiel-Journeys

1. Nutzer A/B registrieren, Email verifizieren, 2FA, Weltjoin, Startressourcen, Fraktion, Direktive, Holz/Wirtschaft und Forschung; Browser schließen, Queue durch Worker schließen.
2. A gründet zweite Kolonie und transportiert Rohstoffe; B versucht dieselbe Kachel (scheitert); A baut Aufklärung und sieht nur erlaubte Infos.
3. A spioniert B, B entdeckt (optional) und erhält Bericht; A berechnet Kampf, sendet Raid, Rückkehr mit Verluste/Beute; keine doppelte Auszahlung.
4. A/B schließen Freundschaft/Allianz, gründen Allianzkrieg/Verteidigung/ACS auf NPC, splitten Verluste/Beute und dokumentieren Siege.
5. A entsperrt Orbit, kolonisiert Slot, baut Mine und Werft, sendet Flotte auf Expedition/Attack, nutzt Trümmerbergung und Tor.
6. Saison startet, Events wirken, Hall of Fame archiviert, Dauerwelt unverändert; Admin behebt steckengebliebene Mission auditierbar; Datenschutzexport ohne fremde Daten.
7. Komplett neuer Compose-Stack reproduziert Migration, Seeds, Testaccounts; Backup→isolierter Restore→identische Statusdaten, kein öffentliches Deployment.
