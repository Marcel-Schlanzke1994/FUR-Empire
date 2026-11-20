# Development-system release history

## 0.1.0 — 2026-11-20

- Added persistent task, dependency, approval, session, attempt, test and commit storage.
- Added transactional single-worker claiming with leases, retry limits and exponential delay.
- Added task timeouts, durable logs, stop-file control and systemd resource/sandbox limits.
- Added focused regression tests for dependency ordering, retry state and approval gates.
