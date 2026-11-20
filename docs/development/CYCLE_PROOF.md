# Controlled development-cycle proof

- UTC time `2026-11-20T17:03:29Z`
- Checked-out branch `agent/task-1`
- Checked-out commit `a946b7f569a9e840159ece8cf5106e19595766d4`

## Validations

- Read `AGENTS.md`, the documentation under `docs/development/`, and the runner
  service and example configuration under `deploy/development/`.
- `git worktree list --porcelain` and `git rev-parse` confirmed a linked task
  worktree at `/var/lib/fur-development-runner/worktrees/task-1` with its own Git
  directory. `git status` was clean before adding this file.
- Running as `furdev`, checked local production paths without opening their
  contents. `/opt/fur-empire` and `/var/lib/fur-empire` denied read, write, and
  traversal access. `namei` reported permission denied for production environment
  configuration, secrets, data, backups, and mail certificate state. The local
  Docker socket denied read and write access.
- `/opt/fur-empire-development/venv/bin/python -m pytest -q tests/test_development_runner.py`
  passed all 3 tests using temporary runner databases.

This evidence file is the only repository change. No gameplay code, deployment
secrets, production configuration, player data, or production state changed.
