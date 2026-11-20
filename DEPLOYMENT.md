# FUR Empire deployment

Production host is 62.83.116.160, application directory /opt/fur-empire. Connect as furdeploy using the dedicated local ED25519 key and verified fur-empire-known-hosts file.

The root application is FastAPI with directly served Vanilla JavaScript assets. Docker Compose runs PostgreSQL 18, app, separate worker, Caddy and a daily backup scheduler. Persistent PostgreSQL and Caddy volumes survive deployments.

## Update
Transfer a complete reviewed source tree over SSH, preserving .env, .secrets, backups and named volumes. Exclude reference repositories, local databases, node_modules and virtual environments.
Run on the VPS:
```sh
sudo sh /opt/fur-empire/deploy/release.sh
```
The script locks deployments, validates Compose, tags the previous app image, backs up PostgreSQL, builds, stops application writers, migrates and starts healthy services. Failed migrations require inspection before resuming. See deploy/ROLLBACK.md.

## Current gates
Authoritative DNS now resolves apex and www to the VPS. Cached public resolvers may still hold the previous A record.
Public TLS, SMTP delivery, admin MFA and public game lifecycle testing remain pending.

## SMTP authenticated transport
Postfix submission is bound to the Docker bridge and loopback. UFW allows port 587 only from the backend subnet 172.18.0.0/16 to 172.18.0.1. SMTP authentication requires TLS, uses a random server-only secret and SASL identity furmailer@fur-empire.de.
The application connects using fur-empire.de mapped internally to the bridge and verifies the valid public certificate. STARTTLS and SMTP authentication were tested successfully from the running app container.
External delivery, DKIM signing configuration, SPF/DMARC records, reverse DNS and certificate refresh integration remain pending. OpenDKIM keys exist but signing is not yet active.
Production Compose currently assumes backend gateway 172.18.0.1, which must be made explicit or configurable before deployment portability is claimed.

## HTTPS registration test
Created GoLiveTest20261120 through the production registration endpoint using go-live-test@fur-empire.de. Secure session cookie and authenticated state loading passed. TLS certificate validation remained enabled. The test explicitly resolved the domain to 62.83.116.160 because ordinary local DNS still used the old provider IP.
Test password is in .secrets/go-live-test.json only. This is an explicitly identified production test account. Email confirmation and game commands are still untested.
OpenDKIM signing configuration is active and both Postfix and OpenDKIM services are running. Public DKIM/SPF/DMARC publication and external delivery verification remain pending.

## Authentication and local email tests
GoLiveTest20261120 successfully logged in over valid HTTPS, loaded its authenticated state, logged out through the CSRF-protected endpoint and then received HTTP 401 for protected state access.
The queued confirmation mail was delivered to a dedicated go-live-test alias in the server's local root mailbox. Postfix queue is empty. This proves internal SMTP acceptance and local delivery only. External provider delivery remains unverified.

## Mail authentication DNS submission
Submitted TXT records at netcup for SPF (v=spf1 ip4:62.83.116.160 -all), DMARC (quarantine with strict alignment), and the server-generated fur._domainkey DKIM public key. netcup reports deployment in progress. DNS publication and key validation remain pending.
A TCP connectivity probe to Gmail's inbound SMTP port 25 was started. External delivery is not yet demonstrated.

## UI deployment and mail certificate renewal
The revised generic online/local-compatible landing labels were deployed successfully through release.sh. Frontend lint, syntax and 105 tests passed before deployment.
Installed hourly fur-mail-tls.timer running deploy/refresh-mail-tls.sh. It checks certificate validity, detects certificate hash changes and reloads Postfix only when the Caddy certificate changes. Initial service run succeeded.
Public /api/v1/ready returns true without DNS override. Strict production readiness still fails because admin_mfa_ready is false.
Provider firewall inspection confirms netcup Mail block drops outbound TCP 25, 465 and 587. Action-time user confirmation to remove this policy is pending. No policy change performed.

## Application rollback rehearsal
With database schema unchanged, stopped app/worker, switched to the pre-UI-change image, started both and confirmed readiness true. An EXIT handler restored the current image and both services passed healthchecks. A backup preceded the drill. No database downgrade was attempted.
Added Deploy-FUR-Empire.ps1 as the local source packaging/SSH transfer entry point. It preserves server source in releases before extraction and invokes release.sh. PowerShell syntax validation passed; a full invocation remains pending.

## Local-to-production deployment and retention
Deploy-FUR-Empire.ps1 completed successfully, including SSH transfer, pre-update source archive, database backup, build, migration and healthy services.
Backup retention now keeps every dump from the last 30 days and at least ten additional older archives. Only regular files matching the FUR timestamp naming pattern are candidates, and pg_restore --list must validate each candidate before removal. Current archives are recent, so none were removed during the initial successful run. Scheduler was recreated to bind the updated script.
Testkommando was promoted to administrator after explicit owner selection. Email verification and MFA remain pending.
