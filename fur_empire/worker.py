"""Persistent world clock and retryable mail outbox."""

import logging
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage

from . import game_events, web_push
from .config import Settings
from .game import Game, JobProcessingError, identity

log = logging.getLogger("fur.worker")


def cycle(game: Game) -> None:
    now = int(time.time())
    try:
        with game.transaction() as db:
            lag = game.advance(db, now)
            game_events.publish(db)
            if now % 3600 == 0:
                web_push.cleanup(db, now)
            db.execute(
                "INSERT INTO scheduler_status(id,sampled_at,lag_seconds) VALUES (1,?,?) "
                "ON CONFLICT(id) DO UPDATE SET sampled_at=excluded.sampled_at,lag_seconds=excluded.lag_seconds",
                (now, lag),
            )
            db.execute(
                "INSERT INTO worker_status VALUES (1,?,'') ON CONFLICT(id) DO UPDATE SET heartbeat=excluded.heartbeat,error=''",
                (now,),
            )
    except JobProcessingError as exc:
        with game.transaction() as db:
            db.execute(
                "INSERT INTO job_failures VALUES (?,?,?,1,?,?) ON CONFLICT(user_id,job_id) DO UPDATE SET attempts=job_failures.attempts+1,error=excluded.error",
                (identity(), exc.user, exc.job, type(exc.__cause__).__name__, now),
            )
            db.execute(
                "INSERT INTO worker_status VALUES (1,?,?) ON CONFLICT(id) DO UPDATE SET heartbeat=excluded.heartbeat,error=excluded.error",
                (now, "Auftrag fehlgeschlagen; automatische Wiederholung bis Quarantäne."),
            )
        log.error("world_job_failed job=%s", exc.job)


def deliver(game: Game, settings: Settings) -> None:
    if not settings.smtp_host:
        return
    # World lock also prevents concurrent outbox senders. A crash after SMTP acceptance
    # can resend the same single-use token; consuming it remains idempotent.
    with game.transaction() as db:
        row = db.execute(
            "SELECT * FROM outbox WHERE status='pending' AND attempts<5 ORDER BY created LIMIT 1"
        ).fetchone()
        if not row:
            return
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = row["recipient"]
        message["Subject"] = row["subject"]
        message["Message-ID"] = f"<{row['id']}@fur-empire>"
        message.set_content(row["body"])
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                if settings.smtp_tls:
                    smtp.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            db.execute(
                "UPDATE outbox SET attempts=attempts+1,status=CASE WHEN attempts>=4 THEN 'failed' ELSE 'pending' END WHERE id=?",
                (row["id"],),
            )
            log.warning("mail_delivery_failed message=%s", row["id"])
        else:
            db.execute(
                "UPDATE outbox SET status='sent',body='',attempts=attempts+1 WHERE id=?",
                (row["id"],),
            )


def run(game: Game, settings: Settings, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            cycle(game)
            deliver(game, settings)
            web_push.deliver_batch(game, int(time.time()), settings)
        except Exception as exc:  # noqa: BLE001 - daemon boundary; report, never swallow.
            # Service stays observable and retries; credentials/SQL parameters never logged.
            log.error("worker_cycle_failed type=%s", type(exc).__name__)
        stop.wait(1)


def main() -> None:
    from pathlib import Path

    from .observability import configure

    configure()
    settings = Settings.load(str(Path("data/empire.sqlite3")))
    run(Game(settings.database), settings, threading.Event())


if __name__ == "__main__":
    main()
