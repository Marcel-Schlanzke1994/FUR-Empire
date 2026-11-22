# Progress log

## 2026-11-22 — P0 local audit

- **TESTED:** Isolated worktree created on `agent/task-terra-audit` and populated with the local uncommitted source state; original working tree untouched.
- **TESTED:** Local SQLite online backup and separate restore drill passed integrity, schema and count comparisons. This does not cover VPS/PostgreSQL.
- **TESTED:** Isolated dependency setup, focused Terra/restore tests, 118 frontend tests, Ruff, Black, mypy, ESLint, syntax, traceability, Compose config and dependency audit. The complete Python suite remains **IN_PROGRESS** as a release gate.
- **TESTED:** A Terra minimap now uses only already observed terrain and visible target coordinates, shows the 20×20 viewport, and supports mouse/keyboard recentering. The clean branch passed 117 frontend tests and 14 focused Python tests; the local source overlay passed 119 frontend tests. Manual browser and accessibility acceptance remain open.
- **TESTED:** Disposable desktop browser smoke opened a new local world, displayed the minimap and moved the viewport from `0:0` to `20:17` by clicking it. Mobile, keyboard and screen-reader browser checks remain open.
- **BLOCKED:** VPS host-key verification; production inventory and restore pending trusted host-key verification and access.
- **TODO:** Select a narrow Terra vertical slice after baseline and safety gates. First candidate: server-owned group order/path with a disposable-world migration and race tests; no production flag enablement.

No Terra real-time unit control or combat has been implemented or released in this phase.
