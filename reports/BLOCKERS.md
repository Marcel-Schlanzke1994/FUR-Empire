# Blockers and required evidence

| Gate | Status | Evidence needed | Safe work that can continue |
| --- | --- | --- | --- |
| Live host identity | BLOCKED | Independently verified SSH host fingerprint and a read-only account | Local source and disposable-world tests |
| Live inventory | BLOCKED | Actual deployed revision, service topology, DB schema/counts, asset/config paths, resource and worker metrics | Architecture and local compatibility work |
| Production recovery | BLOCKED | Protected PostgreSQL backup, `pg_restore --list`, isolated full restore, app smoke, measured time and space | Local SQLite restore and disposable PostgreSQL rehearsal when available |
| Public release | BLOCKED | Required CI, human review, staging acceptance, explicit owner approval for a specific release | Feature-flagged branch work |

Do not bypass the SSH host-key failure or infer live state from local files. No productive write action is authorized by this report.
