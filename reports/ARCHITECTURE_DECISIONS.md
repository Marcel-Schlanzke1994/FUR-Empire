# Architecture decisions

## ADR-TERRA-001 — Extend the current modular monolith

**Status:** Proposed, 2026-11-22. Current source already centralizes world transactions, rule snapshots and worker advancement in Python. A Terra tick engine should initially be another domain module behind a world flag, retaining FastAPI, SQLite local mode and PostgreSQL production mode. A new service or parallel worker would add ordering and recovery risks before throughput is measured.

## ADR-TERRA-002 — Preserve arrival missions during transition

**Status:** Proposed. Existing player and neutral missions are due-time records with server-side arrival resolution. New directly controlled groups should use additive tables and rules. Existing missions continue under their pinned rules; no silent conversion or destructive migration of active jobs. Any coexistence change needs disposable PostgreSQL migration/restore evidence.

## ADR-TERRA-003 — Do not import reference game code or balance

**Status:** Accepted for this branch. The logged-in Delta Wars view confirms a large visual map, resource HUD and minimap conceptually, but the page and supplied tables do not establish FUR mechanics. FUR map, symbols, text, assets and simulation will be original. No reference JavaScript or artwork was copied.
