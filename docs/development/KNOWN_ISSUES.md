# Known development-system issues

- The authorized GitHub repository existed but was empty at audit start; the local source had no
  `.git` directory.
- Codex and Node.js were not installed on the VPS at audit time.
- Codex authentication on the VPS is not yet established. Tokens will not be copied from the
  Windows workstation.
- The production host has no swap. Development receives strict memory/CPU limits and must not run
  heavy suites concurrently with releases.
- Automated off-host production backups and external alert delivery remain operational gaps in the
  existing product documentation.
- Public production readiness must not be inferred from local or staging tests.
