# Infrastructure audit — 2026-11-20

## Verified production state

- Host: netcup VPS `62.83.116.160`, Debian 13, 8 vCPU, 16 GiB RAM, 314 GiB root disk.
- Product directory: `/opt/fur-empire`; it is not a Git checkout.
- Runtime: Docker Compose with healthy FastAPI app, separate game worker and PostgreSQL 18;
  Caddy and the backup scheduler were running during each audit check.
- Public health and readiness returned success. Strict operational readiness still reports
  `admin_mfa_ready=false`; this is not hidden by the development system.
- Existing monitoring timer runs every five minutes. Production containers retain their existing
  CPU, memory, PID, read-only filesystem and capability limits.
- Deployment uses the unprivileged `furdeploy` account and reviewed release script. Production
  source deployment remains separate from Git branch publication.

## Verified development state

- Dedicated system account: `furdev` (no login shell and no sudo grant).
- Workspace: `/opt/fur-empire-development`; persistent state:
  `/var/lib/fur-development-runner`.
- `furdev` cannot write `/opt/fur-empire`.
- Node.js 20 and Codex CLI 0.171.0 are installed from the supported npm package.
- GitHub access uses a repository-scoped ED25519 deploy key. The GitHub host key is pinned to the
  fingerprint published by GitHub.
- The authorized public repository is `Marcel-Schlanzke1994/FUR-Empire`. `main` requires the
  `test` CI check, linear history, conversation resolution and one approving review; force pushes
  and deletion are disabled.
- `fur-development-runner.service` is enabled with a 3 GiB hard memory limit, 200% CPU quota,
  256-task limit and systemd filesystem/device/kernel hardening.

## Separation and remaining gates

The development runner has no production database credential, Docker socket access or production
write permission. Production deployment is not an automated runner action. Codex authentication is
the remaining external authorization gate for the first live AI task. CI must complete successfully
and PR review must be supplied by an eligible reviewer before merging.
