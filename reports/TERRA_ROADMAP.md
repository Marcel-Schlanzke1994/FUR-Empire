# Terra-only execution roadmap

This order narrows the supplied P0–P12 roadmap to the user's current Terra scope. Orbit and Mars source modules remain untouched; their expansion is deferred until Terra is accepted.

| Phase | Status on 2026-11-22 | Acceptance evidence |
| --- | --- | --- |
| P0 local inventory and restore | TESTED locally; live BLOCKED | Source inventory and disposable SQLite restore recorded in `AUDIT_LOCAL_SYSTEM.md`; live/PG evidence outstanding |
| P1 reproducible baseline | IN_PROGRESS | Full Python and frontend checks, smoke on disposable world, dependency contract |
| P2 world/ownership compatibility | TODO | Source-to-live mapping, migration rehearsal, cross-world isolation tests |
| P3 Terra map and synchronization | IN_PROGRESS | Fog-filtered minimap added and frontend-tested; camera, zoom, direct selection, deltas and two-client review remain |
| P4 economy and production integration | TODO | Ledger invariants, offline/restart behavior under group orders |
| P5 direct unit movement | TODO | Owned groups, typed orders, persisted path, fuel, collision/retry tests |
| P6 continuous combat and capture | TODO | Deterministic ticks, simultaneous damage, capture race/replay |
| P7 alliances and multiplayer | TODO | Capability and diplomacy checks, reconnection and visibility |
| P8 Terra regional transit | TODO | Atomic region crossing and logistics, no orbital dependencies |
| P11 hardening and load | TODO | Measured 2/10-player and larger disposable-world profiles, accessibility, security, recovery |
| P12 staged beta release | BLOCKED | CI, human review, verified production restore, explicit release approval |

The first implementation slice after P1 should be small and end-to-end: one owned Terra group can receive a move order in a disposable world, advance server-side, and recover idempotently after a worker restart. This requires approved FUR-specific rules for speed, fuel, path visibility and coexistence with current arrival missions. Migration and flag remain off in live environments.
