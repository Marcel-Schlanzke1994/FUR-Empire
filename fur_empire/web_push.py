"""Owner-bound Web Push subscriptions and generic event delivery."""

import hashlib
import ipaddress
import json
import logging
import socket
from typing import Any, Self
from urllib.parse import urlsplit
from uuid import uuid4

from .database import Connection
from .game import Game

log = logging.getLogger("fur.web_push")
MAX_SUBSCRIPTIONS = 5
MAX_GLOBAL_QUEUE = 10_000
MAX_ENDPOINT_LENGTH = 2048
MAX_KEY_LENGTH = 128
BATCH_SIZE = 50
MAX_ATTEMPTS = 5
MAX_AGE_SECONDS = 7 * 24 * 60 * 60
BACKOFF_SECONDS = (30, 120, 600, 1800)
PUSH_HOST_SUFFIXES = (
    ".push.services.mozilla.com",
    ".notify.windows.com",
    ".push.apple.com",
    ".googleapis.com",
    ".google.com",
    ".push.services.mozilla.org",
)
GENERIC_PAYLOAD = json.dumps(
    {
        "title": "FUR Empire",
        "body": "Es gibt neue Informationen in deinem Imperium.",
        "url": "/",
        "tag": "fur-empire-update",
    },
    separators=(",", ":"),
)


def validate_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    if (
        len(endpoint) > MAX_ENDPOINT_LENGTH
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise ValueError("Der Push-Endpunkt muss eine gültige HTTPS-Adresse sein.")
    hostname = parsed.hostname.lower().rstrip(".")
    if not any(hostname.endswith(suffix) for suffix in PUSH_HOST_SUFFIXES):
        raise ValueError("Dieser Push-Anbieter wird nicht unterstützt.")
    try:
        addresses = [ipaddress.ip_address(parsed.hostname)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(result[4][0])
                for result in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
            ]
        except OSError as exc:
            raise ValueError("Der Push-Endpunkt ist nicht erreichbar.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private und lokale Push-Endpunkte sind nicht zulässig.")


def subscribe(
    db: Connection, user: str, endpoint: str, p256dh: str, auth: str, now: int
) -> dict[str, Any]:
    validate_endpoint(endpoint)
    if not p256dh or len(p256dh) > MAX_KEY_LENGTH or not auth or len(auth) > MAX_KEY_LENGTH:
        raise ValueError("Der Push-Schlüssel ist ungültig.")
    _validate_subscription_keys(p256dh, auth)
    existing = db.execute(
        "SELECT id,user_id FROM web_push_subscriptions WHERE endpoint=?", (endpoint,)
    ).fetchone()
    if existing and existing["user_id"] != user:
        raise ValueError("Dieser Push-Endpunkt ist bereits einem anderen Konto zugeordnet.")
    count = db.execute(
        "SELECT count(*) FROM web_push_subscriptions WHERE user_id=?", (user,)
    ).fetchone()[0]
    if not existing and count >= MAX_SUBSCRIPTIONS:
        raise ValueError("Es sind höchstens fünf Push-Geräte pro Konto erlaubt.")
    identifier = str(existing["id"]) if existing else str(uuid4())
    last_sequence = int(
        db.execute(
            "SELECT COALESCE(MAX(sequence),0) FROM game_events WHERE recipient=?", (user,)
        ).fetchone()[0]
    )
    db.execute(
        "INSERT INTO web_push_subscriptions(id,user_id,endpoint,p256dh,auth,created,updated,failures,last_sequence) "
        "VALUES (?,?,?,?,?,?,?,0,?) ON CONFLICT(endpoint) DO UPDATE SET "
        "p256dh=excluded.p256dh,auth=excluded.auth,updated=excluded.updated,failures=0",
        (identifier, user, endpoint, p256dh, auth, now, now, last_sequence),
    )
    return {"id": identifier, "created": not bool(existing)}


def unsubscribe(db: Connection, user: str, endpoint: str) -> bool:
    removed = db.execute(
        "DELETE FROM web_push_subscriptions WHERE endpoint=? AND user_id=? RETURNING id",
        (endpoint, user),
    ).fetchone()
    return bool(removed)


def enqueue_pending_events(db: Connection, batch_size: int = BATCH_SIZE) -> None:
    subscriptions = db.execute(
        "SELECT id,user_id,created,last_sequence FROM web_push_subscriptions ORDER BY id"
    ).fetchall()
    queued = int(db.execute("SELECT count(*) FROM web_push_outbox").fetchone()[0])
    for subscription in subscriptions:
        events = db.execute(
            "SELECT sequence,id,kind,created FROM game_events WHERE recipient=? AND sequence>? "
            "AND created>=? ORDER BY sequence LIMIT ?",
            (
                subscription["user_id"],
                subscription["last_sequence"],
                subscription["created"],
                batch_size,
            ),
        ).fetchall()
        for event in events:
            if not enqueue_event(
                db,
                subscription,
                str(event["id"]),
                str(event["kind"]),
                int(event["created"]),
                queued,
            ):
                break
            queued += 1
            db.execute(
                "UPDATE web_push_subscriptions SET last_sequence=? WHERE id=?",
                (event["sequence"], subscription["id"]),
            )


def enqueue_event(
    db: Connection, subscription: Any, event_id: str, kind: str, now: int, queued: int
) -> bool:
    if queued >= MAX_GLOBAL_QUEUE:
        return False
    if kind == "notification_preference":
        return True
    preference = db.execute(
        "SELECT muted FROM game_event_preferences WHERE user_id=? AND category=?",
        (subscription["user_id"], _category_for(kind)),
    ).fetchone()
    if preference and preference["muted"]:
        return True
    identifier = hashlib.sha256(f"{subscription['id']}:{event_id}".encode()).hexdigest()
    db.execute(
        "INSERT INTO web_push_outbox(id,subscription_id,event_id,available_at,created) "
        "VALUES (?,?,?,?,?) ON CONFLICT(subscription_id,event_id) DO NOTHING",
        (identifier, subscription["id"], event_id, now, now),
    )
    return True


def _category_for(kind: str) -> str:
    from .game_events import category_for

    return category_for(kind)


def deliver_batch(game: Game, now: int, settings: Any) -> None:
    if (
        not settings.webpush_public_key
        or not settings.webpush_private_key_file
        or not settings.webpush_subject
    ):
        return
    try:
        from pywebpush import WebPushException, webpush  # type: ignore[import-untyped]
        from requests import Session
        from requests.exceptions import RequestException
    except ImportError as exc:
        log.error("web_push_dependency_unavailable type=%s", type(exc).__name__)
        return

    for _ in range(5):
        with game.transaction() as db:
            row = db.execute(
                "SELECT q.id,q.attempts,s.id AS subscription_id,s.endpoint,s.p256dh,s.auth "
                "FROM web_push_outbox q JOIN web_push_subscriptions s ON s.id=q.subscription_id "
                "WHERE q.available_at<=? AND q.created>? AND q.lease_until<=? "
                "ORDER BY q.created,q.id LIMIT 1",
                (now, now - MAX_AGE_SECONDS, now),
            ).fetchone()
            if not row:
                return
            db.execute(
                "UPDATE web_push_outbox SET lease_until=? WHERE id=?",
                (now + 30, row["id"]),
            )
        try:
            validate_endpoint(str(row["endpoint"]))
            _validate_subscription_keys(str(row["p256dh"]), str(row["auth"]))
            request_session = Session()
            request_session.trust_env = False

            webpush(
                {
                    "endpoint": row["endpoint"],
                    "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
                },
                GENERIC_PAYLOAD,
                vapid_private_key=settings.webpush_private_key_file,
                vapid_claims={"sub": settings.webpush_subject},
                ttl=60,
                timeout=5,
                requests_session=_NoRedirectSession(request_session),
            )
        except ImportError as exc:
            with game.transaction() as db:
                _retry(db, row, now)
            log.error("web_push_dependency_unavailable type=%s", type(exc).__name__)
            return
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                with game.transaction() as db:
                    db.execute(
                        "DELETE FROM web_push_subscriptions WHERE id=?", (row["subscription_id"],)
                    )
                continue
            with game.transaction() as db:
                _retry(db, row, now)
            log.warning("web_push_delivery_failed status=%s", status or "network")
        except (OSError, ValueError, RuntimeError, TypeError, RequestException) as exc:
            with game.transaction() as db:
                _retry(db, row, now)
            log.warning("web_push_delivery_failed type=%s", type(exc).__name__)
        else:
            with game.transaction() as db:
                db.execute("DELETE FROM web_push_outbox WHERE id=?", (row["id"],))
                db.execute(
                    "UPDATE web_push_subscriptions SET failures=0 WHERE id=?",
                    (row["subscription_id"],),
                )


def _retry(db: Connection, row: Any, now: int) -> None:
    attempts = int(row["attempts"]) + 1
    if attempts >= MAX_ATTEMPTS:
        db.execute("DELETE FROM web_push_subscriptions WHERE id=?", (row["subscription_id"],))
        return
    delay = BACKOFF_SECONDS[min(attempts - 1, len(BACKOFF_SECONDS) - 1)]
    db.execute(
        "UPDATE web_push_outbox SET attempts=?,available_at=? WHERE id=?",
        (attempts, now + delay, row["id"]),
    )
    db.execute(
        "UPDATE web_push_subscriptions SET failures=failures+1 WHERE id=?",
        (row["subscription_id"],),
    )


def cleanup(db: Connection, now: int) -> None:
    db.execute("DELETE FROM web_push_outbox WHERE created<=?", (now - MAX_AGE_SECONDS,))


def _validate_subscription_keys(p256dh: str, auth: str) -> None:
    import base64

    try:
        key = base64.b64decode(p256dh + "=" * (-len(p256dh) % 4), altchars=b"-_", validate=True)
        secret = base64.b64decode(auth + "=" * (-len(auth) % 4), altchars=b"-_", validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Der Push-Schlüssel ist ungültig.") from exc
    if len(key) != 65 or key[0] != 4 or len(secret) != 16:
        raise ValueError("Der Push-Schlüssel ist ungültig.")
    from cryptography.hazmat.primitives.asymmetric import ec

    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), key)
    except ValueError as exc:
        raise ValueError("Der Push-Schlüssel ist ungültig.") from exc


class _NoRedirectSession:
    """Requests adapter forbidding redirect following to secondary endpoints."""

    def __init__(self, session: Any):
        self._session = session

    def post(self, *args: Any, **kwargs: Any) -> Any:
        kwargs["allow_redirects"] = False
        return self._session.post(*args, **kwargs)

    def __enter__(self) -> Self:
        self._session.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        self._session.__exit__(*args)
