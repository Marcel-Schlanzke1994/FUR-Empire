# Development runner runbook

## State and control

The service reads `/etc/fur-development-runner.json`. Persistent state, logs, task worktrees and the
Codex credential store are under `/var/lib/fur-development-runner` and mode-restricted to `furdev`.

```sh
sudo systemctl status fur-development-runner
sudo journalctl -u fur-development-runner -n 100
sudo -u furdev /opt/fur-empire-development/venv/bin/python -m development_runner.cli \
  --config /etc/fur-development-runner.json list
```

Create a task from a reviewed prompt file with `add-task`. Use `--approval-required` for any risk
class named in `AGENTS.md`. The persistent stop file is controlled with `stop` and `resume`; systemd
provides process restart, while expired leases make interrupted tasks claimable again.

## Recovery

1. Confirm production health before investigating development work.
2. Run SQLite `PRAGMA integrity_check` against `runner.sqlite3` as `furdev`.
3. Inspect task, session and attempt records plus the corresponding log.
4. Verify the task worktree branch and remote branch; never infer completion from a stale process.
5. Restart the service. Do not reset or delete a task worktree until its evidence is retained.

## Release boundary

The runner pushes only `agent/task-*` branches. A GitHub workflow opens a pull request. Full CI,
review and staging evidence are gates. Production release remains the separately approved procedure
in `DEPLOYMENT.md` and `deploy/release.sh`.
