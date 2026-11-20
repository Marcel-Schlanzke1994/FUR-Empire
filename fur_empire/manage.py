"""Operator CLI; no public bootstrap/admin credentials."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import secrets
import sqlite3
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .config import Settings
from .database import Connection

if TYPE_CHECKING:
    from .game import Game

DEMO_NAMES = ("DemoAstra", "DemoBoreal", "DemoCinder", "DemoDelta", "DemoEmber")


def _insert_demo_accounts(
    game: Game, account_count: int, marker: str | None = None
) -> list[tuple[str, str, str]]:
    from argon2 import PasswordHasher

    from .game import identity

    if not 2 <= account_count <= 10:
        raise ValueError("Die Demo benötigt zwischen 2 und 10 Konten.")
    credentials: list[tuple[str, str, str]] = []
    hasher = PasswordHasher()
    with game.transaction() as db:
        if marker and db.execute("SELECT 1 FROM flags WHERE name=?", (marker,)).fetchone():
            return []
        if marker and db.execute("SELECT count(*) FROM users").fetchone()[0]:
            raise ValueError(
                "Staging-Demodaten wurden bereits angelegt oder die Welt enthält Konten."
            )
        for index in range(account_count):
            name = DEMO_NAMES[index] if index < len(DEMO_NAMES) else f"DemoPilot{index + 1:02d}"
            user = identity()
            password = secrets.token_urlsafe(18)
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, name, hasher.hash(password)))
            game.create(db, user, name)
            if marker:
                db.execute(
                    "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
                    (f"{name.lower()}@staging.invalid", user),
                )
            credentials.append((name, password, user))
        if marker:
            db.execute("INSERT INTO flags VALUES (?,?)", (marker, "true"))
    return credentials


def seed_demo_database(database: Path, account_count: int = 3) -> list[tuple[str, str, str]]:
    """Create disposable local demo accounts in a brand-new SQLite database."""
    if os.getenv("FUR_ENV", "local") not in ("local", "test"):
        raise ValueError("Demo-Datenbanken sind nur in lokaler oder Testumgebung erlaubt.")
    if os.getenv("DB_HOST") or os.getenv("DATABASE_URL"):
        raise ValueError("Demo-Datenbanken dürfen keine konfigurierte Serverdatenbank verwenden.")
    target = database.expanduser().resolve()
    default_game = Path("data/empire.sqlite3").resolve()
    if target == default_game:
        raise ValueError("Der Standard-Spielstand darf nicht als Demo-Datenbank verwendet werden.")
    if target.suffix.lower() != ".sqlite3":
        raise ValueError("Die Demo-Datenbank muss eine neue .sqlite3-Datei sein.")
    if target.exists() or target.is_symlink():
        raise FileExistsError("Die Demo-Datenbank existiert bereits und wird nicht verändert.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=False)
    try:
        from .game import Game

        game = Game(target)
        return _insert_demo_accounts(game, account_count)
    except BaseException:
        for suffix in ("", "-wal", "-shm"):
            Path(str(target) + suffix).unlink(missing_ok=True)
        raise


def seed_staging_demo(account_count: int = 3) -> list[tuple[str, str, str]]:
    """Seed a fresh private Compose staging database once."""
    if (
        os.getenv("FUR_ENV") != "staging"
        or os.getenv("DB_HOST") != "db"
        or os.getenv("DB_NAME") != "fur_staging"
        or os.getenv("DATABASE_URL")
        or os.getenv("FUR_STAGING_CONFIRM_SEED") != "YES"
    ):
        raise ValueError("Staging-Seed nur über den privaten Compose-Stagingdienst erlaubt.")
    settings = Settings.load("unused.sqlite3")
    from .game import Game

    game = Game(settings.database)
    if not game.path.startswith(("postgresql://", "postgres://")):
        raise ValueError("Staging-Demodaten benötigen die isolierte PostgreSQL-Stagingdatenbank.")
    return _insert_demo_accounts(game, account_count, marker="staging_demo_seeded")


def worker_recent(database: str, now: int | None = None) -> bool:
    """Read the worker heartbeat without running schema migrations on every health probe."""
    current = int(time.time()) if now is None else now
    with Connection(database) as db:
        worker = db.execute("SELECT heartbeat FROM worker_status WHERE id=1").fetchone()
    return bool(worker and worker[0] >= current - 30)


def backup(game: Game, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = (
        directory
        / f'empire-{stamp}{".dump" if game.path.startswith(("postgres:","postgresql:")) else ".sqlite3"}'
    )
    if game.path.startswith(("postgres:", "postgresql:")):
        import os
        from urllib.parse import unquote, urlparse

        parsed = urlparse(game.path)
        environment = dict(os.environ)
        environment["PGPASSWORD"] = unquote(parsed.password or "")
        subprocess.run(
            [
                "pg_dump",
                "--host",
                parsed.hostname or "db",
                "--port",
                str(parsed.port or 5432),
                "--username",
                unquote(parsed.username or "fur"),
                "--dbname",
                parsed.path.lstrip("/"),
                "--format=custom",
                "--file",
                str(destination),
            ],
            env=environment,
            check=True,
            capture_output=True,
        )
    else:
        with sqlite3.connect(game.path) as source, sqlite3.connect(destination) as target:
            source.backup(target)
        with sqlite3.connect(destination) as target:
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Sicherungsprüfung fehlgeschlagen.")
    with game.transaction() as db:
        db.execute(
            "INSERT INTO backup_status(id,completed_at) VALUES (1,?) "
            "ON CONFLICT(id) DO UPDATE SET completed_at=excluded.completed_at",
            (int(time.time()),),
        )
    return destination


def generate_webpush_key_pair(private_key: Path) -> str:
    """Create a new VAPID PEM once; return its browser-safe public key."""
    import base64

    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
    )
    from py_vapid import Vapid  # type: ignore[import-untyped]

    target = private_key.expanduser().resolve()
    if target.exists() and target.stat().st_size:
        raise FileExistsError("Der vorhandene VAPID-Schlüssel bleibt unverändert.")
    target.parent.mkdir(parents=True, exist_ok=True)
    vapid = Vapid()
    vapid.generate_keys()
    encoded = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    public_key = base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")
    created_by_us = False
    replaced_empty_placeholder = False
    try:
        if target.exists():
            with target.open("rb+") as existing:
                if existing.read(1):
                    raise FileExistsError("Der vorhandene VAPID-Schlüssel bleibt unverändert.")
            replaced_empty_placeholder = True
            target.write_bytes(vapid.private_pem())
        else:
            with target.open("xb") as created:
                created_by_us = True
                created.write(vapid.private_pem())
        if os.name != "nt":
            target.chmod(0o600)
    except BaseException:
        if created_by_us:
            target.unlink(missing_ok=True)
        elif replaced_empty_placeholder:
            with target.open("wb") as handle:
                handle.truncate()
        raise
    return public_key


def main() -> None:
    parser = argparse.ArgumentParser(description="FUR Empire Betriebswerkzeuge")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin")
    create.add_argument("--name", required=True)
    create.add_argument("--email", required=True)
    promote = sub.add_parser("promote")
    promote.add_argument("--name", required=True)
    promote.add_argument("--role", choices=["player", "moderator", "admin"], required=True)
    save = sub.add_parser("backup")
    save.add_argument("--directory", default="backups")
    snapshot = sub.add_parser("snapshot-world", help="exportiert Gelände und Regeln einer Welt")
    snapshot.add_argument("--world", type=int, required=True)
    snapshot.add_argument("--output", type=Path, required=True)
    restore = sub.add_parser(
        "restore-world-blueprint",
        help="importiert eine geschlossene Testwelt in eine neue SQLite-Datei",
    )
    restore.add_argument("--snapshot", type=Path, required=True)
    restore.add_argument("--database", type=Path, required=True)
    restore.add_argument("--name", required=True)
    restore_backup = sub.add_parser(
        "restore-world-backup", help="kopiert eine vollständige SQLite-Sicherung in eine neue Datei"
    )
    restore_backup.add_argument("--snapshot", type=Path, required=True)
    restore_backup.add_argument("--database", type=Path, required=True)
    restore_backup.add_argument("--world", type=int, required=True)
    rehearsal = sub.add_parser(
        "rehearse-sqlite-migration", help="migriert eine neue Kopie einer SQLite-Sicherung"
    )
    rehearsal.add_argument("--snapshot", type=Path, required=True)
    rehearsal.add_argument("--database", type=Path, required=True)
    demo = sub.add_parser("seed-demo", help="erzeugt eine isolierte lokale Mehrspieler-Demowelt")
    demo.add_argument("--database", type=Path, required=True)
    demo.add_argument("--accounts", type=int, default=3)
    stage_demo = sub.add_parser("seed-staging-demo", help="füllt einmalig die private Stagingwelt")
    stage_demo.add_argument("--accounts", type=int, default=3)
    webpush_keys = sub.add_parser(
        "generate-webpush-keys", help="erzeugt einmalig ein VAPID-Schlüsselpaar"
    )
    webpush_keys.add_argument(
        "--private-key", type=Path, default=Path(".secrets/webpush_private_key")
    )
    sub.add_parser("check-worker")
    sub.add_parser("migrate")
    sub.add_parser("readiness")
    args = parser.parse_args()
    if args.command == "rehearse-sqlite-migration":
        from .world_snapshot import rehearse_sqlite_migration

        try:
            result = rehearse_sqlite_migration(args.snapshot, args.database)
        except (OSError, ValueError, sqlite3.Error) as error:
            parser.error(str(error))
        print(json.dumps(result))
        return
    if args.command == "restore-world-backup":
        from .world_snapshot import restore_sqlite_world_backup

        try:
            restore_sqlite_world_backup(args.snapshot, args.database, args.world)
        except (OSError, ValueError, sqlite3.Error) as error:
            parser.error(str(error))
        print(f"SQLite-Sicherung mit Welt {args.world} wiederhergestellt: {args.database}")
        return
    if args.command == "restore-world-blueprint":
        from .world_snapshot import restore_world

        try:
            world_id = restore_world(args.snapshot, args.database, args.name)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(f"Geschlossene Sandbox-Welt {world_id}: {args.database}")
        return
    if args.command == "seed-demo":
        try:
            credentials = seed_demo_database(args.database, args.accounts)
        except (FileExistsError, OSError, ValueError) as error:
            parser.error(str(error))
        print("Demo-Zugangsdaten (werden nicht erneut angezeigt):")
        for name, password, _user in credentials:
            print(f"{name}: {password}")
        print(f"Demowelt erstellt: {args.database.expanduser().resolve()}")
        return
    if args.command == "seed-staging-demo":
        try:
            credentials = seed_staging_demo(args.accounts)
        except (OSError, ValueError, RuntimeError) as error:
            parser.error(str(error))
        print("Staging-Zugangsdaten (werden nicht erneut angezeigt):")
        for name, password, _user in credentials:
            print(f"{name}: {password}")
        print("Testdaten wurden einmalig in der separaten Stagingwelt angelegt.")
        return
    if args.command == "generate-webpush-keys":
        try:
            public_key = generate_webpush_key_pair(args.private_key)
        except (FileExistsError, OSError, ValueError) as error:
            parser.error(str(error))
        print(f"WEBPUSH_PUBLIC_KEY={public_key}")
        print(f"WEBPUSH_PRIVATE_KEY_FILE={args.private_key.expanduser().resolve()}")
        print(
            "Den privaten PEM-Dateiinhalt geheim halten; bestehende Schlüssel nicht überschreiben."
        )
        return
    settings = Settings.load(str(Path("data/empire.sqlite3")))
    if args.command == "snapshot-world":
        from .world_snapshot import export_world

        try:
            export_world(settings.database, args.world, args.output)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(args.output)
        return
    if args.command == "check-worker":
        if not worker_recent(settings.database):
            raise SystemExit(1)
        return
    from argon2 import PasswordHasher

    from .game import Game, identity

    game = Game(settings.database)
    if args.command == "backup":
        print(backup(game, Path(args.directory)))
        return
    with game.transaction() as db:
        if args.command == "create-admin":
            from .identity import Accounts, valid_email

            if not valid_email(args.email):
                parser.error("Gültige E-Mail erforderlich.")
            password = getpass.getpass("Neues Administratorpasswort (mind. 12 Zeichen): ")
            if len(password) < 12 or password != getpass.getpass("Passwort wiederholen: "):
                parser.error("Passwörter stimmen nicht überein oder sind zu kurz.")
            if db.execute(
                "SELECT 1 FROM users WHERE lower(name)=lower(?)", (args.name,)
            ).fetchone():
                parser.error("Name ist bereits vergeben; ggf. promote verwenden.")
            if db.execute(
                "SELECT 1 FROM profiles WHERE lower(email)=lower(?)", (args.email,)
            ).fetchone():
                parser.error("E-Mail ist bereits vergeben.")
            user = identity()
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (user, args.name, PasswordHasher().hash(password)),
            )
            game.create(db, user, args.name)
            db.execute(
                "UPDATE profiles SET role='admin',email=? WHERE user_id=?", (args.email, user)
            )
            Accounts(game).send_token(db, user, "verify", args.email)
            game.systems.audit(db, "operator", "create_admin", user)
            print(
                "Administratorkonto angelegt. E-Mail bestätigen und Authenticator im Spiel einrichten."
            )
        elif args.command == "promote":
            row = db.execute(
                "SELECT id FROM users WHERE lower(name)=lower(?)", (args.name,)
            ).fetchone()
            if not row:
                parser.error("Konto unbekannt.")
            db.execute("UPDATE profiles SET role=? WHERE user_id=?", (args.role, row[0]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (row[0],))
            game.systems.audit(db, "operator", "role_change", row[0], role=args.role)
            print("Rolle geändert; alte Sitzungen ungültig gemacht.")
        elif args.command == "readiness":
            readiness_report: dict[str, Any] = {
                "production": settings.production,
                "postgresql": db.postgres,
                "worker_recent": False,
                "quarantined": db.execute(
                    "SELECT count(*) FROM job_failures WHERE attempts>=3"
                ).fetchone()[0],
                "admin_mfa_ready": db.execute(
                    "SELECT count(*) FROM profiles WHERE role='admin' AND totp IS NOT NULL AND verified=1"
                ).fetchone()[0]
                > 0,
                "operator_configured": bool(settings.operator_name and settings.operator_contact),
            }
            worker = db.execute("SELECT heartbeat FROM worker_status WHERE id=1").fetchone()
            readiness_report["worker_recent"] = bool(worker and worker[0] > int(time.time()) - 30)
            print(json.dumps(readiness_report, indent=2))
            if (
                not all(
                    readiness_report[k]
                    for k in (
                        "production",
                        "postgresql",
                        "worker_recent",
                        "admin_mfa_ready",
                        "operator_configured",
                    )
                )
                or readiness_report["quarantined"]
            ):
                raise SystemExit(1)
        else:
            print("Schema aktuell.")


if __name__ == "__main__":
    main()
