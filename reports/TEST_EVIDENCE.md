# Test evidence — 2026-11-22

The local overlay was examined in `agent/task-terra-audit`; the reviewable change is on clean branch `agent/task-terra-minimap`. Tests created temporary SQLite databases; no test used `data/empire.sqlite3` as a write target.

| Check | Result |
| --- | --- |
| Local SQLite read-only `quick_check` | `ok` |
| SQLite online backup and isolated restore | `integrity_check=ok` on both, schema/counts match |
| Focused `pytest -q tests/test_terrain.py tests/test_world_snapshot.py` on clean branch | 14 passed, 11 skipped (PostgreSQL URL unavailable), 31.47 s |
| `python -m ruff check fur_empire tests scripts` | Passed |
| `python -m black --check fur_empire tests scripts` on clean branch | Passed; 88 files unchanged |
| `python -m mypy fur_empire` | Passed; 61 source files |
| `npm.cmd run lint` | Passed |
| `npm.cmd run check` | Passed |
| `npm.cmd test` on clean branch after minimap edit | 117 passed, 0 failed |
| `python scripts/check_traceability.py` | Passed; 344 unique feature IDs |
| `docker compose config --quiet` | Passed; syntax/config only, daemon unavailable |
| `pip-audit -r requirements.lock --no-deps --disable-pip` | No known vulnerabilities reported; no hash verification |
| Full `pytest -q` | Started in isolated environment; stopped before completion after the targeted Terra/restore suite and static gates passed. Full-suite gate remains open. |
| `python -m pip check` in isolated environment | No broken requirements found |
| Disposable browser smoke | A fresh local SQLite world on `127.0.0.1:8095` was created, a disposable test account logged in, and the Terra map rendered the minimap with observed sectors and a 20×20 viewport. Clicking the minimap changed the displayed window from `0:0` to `20:17`; the viewport rectangle moved correspondingly. The local server was then stopped. This is one desktop browser smoke, not mobile or screen-reader acceptance. |

The copied uncommitted local source overlay also passed 119 frontend tests after the same minimap edit. Initial use of the global Python install failed during collection because Starlette 1.10 requires `httpx2` for `TestClient`. The isolated environment installed it. `requirements-dev.txt` now declares this test dependency; no production lockfile was changed.
