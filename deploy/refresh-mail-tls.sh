#!/bin/sh
set -eu
cert=/var/lib/docker/volumes/fur-empire_caddy_data/_data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/fur-empire.de/fur-empire.de.crt
state=/var/lib/fur-empire/mail-cert.sha256
test -s "$cert"
openssl x509 -in "$cert" -checkend 86400 -noout
install -d -m 700 /var/lib/fur-empire
current=$(sha256sum "$cert" | cut -d ' ' -f 1)
previous=$(cat "$state" 2>/dev/null || true)
if [ "$current" != "$previous" ]; then
    postfix check
    systemctl reload postfix
    printf '%s
' "$current" > "$state"
fi
