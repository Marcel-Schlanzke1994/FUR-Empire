# Terra real-time engine proposal — ADR draft

**Status:** Design, not enabled. **Scope:** Terra only. Preserve the existing FastAPI modular monolith, world/colony IDs, accounts, economy and mission records. New rules require an explicit per-world version and default-off flag.

## Authoritative flow

1. Client submits a typed command with world, group, target/order, expected revision and idempotency key. It never submits damage, resource totals or ownership.
2. API authenticates session and CSRF, checks active world, group ownership, fog, bounds, unit capabilities, capacity and rule version. It writes command plus resource/fuel reservation in one transaction. Repeated identical keys return the original result; conflicting payloads fail.
3. A single worker per world advances fixed-duration ticks in database order. It reads only committed commands, derives movement and combat from versioned rules, and commits positions, HP, ownership, ledger entries and sequenced events atomically. Tick ID and command ID make retries safe after a crash.
4. HTTP snapshot and an authenticated event stream return only sectors visible to that observer. Deltas carry a monotonic world sequence and snapshot revision. A reconnect with an old sequence receives a fresh scoped snapshot.

## Proposed additive model

`terra_groups` (world, owner, sector, sub-sector position, revision, rules digest), `terra_group_units` (type, count, HP pool), `terra_orders` (idempotency key, order, path, reserved fuel, state), `terra_ticks` (world, tick, rule version, committed time), `terra_events` (sequence, tick, observer scope, payload), and `terra_capture_attempts` (target, attacker, progress, state). Foreign keys must bind world and owner; uniqueness must protect tick and command replay. No migration is written until a disposable PostgreSQL restore and compatibility test pass.

## Deterministic rules and boundaries

- Weighted four-way pathfinding uses the current terrain catalog; unknown sectors may be ordered by a policy still to be decided, but unknown terrain/targets must not leak through previews or deltas.
- Persist the selected path and rule digest when an order starts. Define blocked-path and retarget behavior explicitly. Fuel must be reserved once and settled once; no negative balances.
- Fixed tick order: accepted commands, movement, visibility, acquisition/targeting, damage, deaths, capture, economy/ledger, observer events. Resolve simultaneous damage before capture so transaction order cannot award two owners.
- Capture is a state machine with a unique active winner and compare-and-swap ownership update in the same transaction as a permanent event. Preserve existing arrival-based missions until opt-in migration and coexistence behavior is tested.
- Event payloads are projections, not the source of authority. Never send enemy hidden position, strength or private reports. Public rendering uses interpolation between committed snapshots only.

## Capacity and rollout

Start with one worker and the existing serialized world transaction. Measure 2, 10 and increasing concurrent clients, command latency, tick duration, lock wait, event fanout, database growth and recovery after worker restart on a disposable world. Set actual SLOs from measured capacity; do not add workers before contention and conflict behavior are proven. Roll out behind a Terra-only world flag, first to disposable staging, then a small cohort after backup/restore, CI and explicit production approval. Rollback turns off new orders and drains/reconciles existing groups; it must never delete player state.

## Open rule decisions

Tick interval, unit footprint/collision, fog behavior for unexplored movement, grouping limits, fuel units, target priorities, retreat, capture time and old-mission coexistence need FUR-specific balance decisions and tests. The supplied Delta Wars tables do not settle them.
