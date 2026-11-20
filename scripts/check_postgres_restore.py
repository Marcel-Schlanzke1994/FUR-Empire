"""Restore drill against two disposable databases on the configured TEST cluster."""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse
from uuid import uuid4

import psycopg
from psycopg import sql

from fur_empire.database import Connection
from fur_empire.game import Game, identity


def mission_digest(jobs: list[dict[str, object]]) -> str:
    payload = json.dumps(jobs, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def database_digest(db: Connection) -> str:
    digest = hashlib.sha256()
    tables = db.raw.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname=current_schema() ORDER BY tablename"
    ).fetchall()
    for table_row in tables:
        table = str(table_row["tablename"])
        columns = db.raw.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=current_schema() AND table_name=%s ORDER BY ordinal_position",
            (table,),
        ).fetchall()
        column_names = [str(column["column_name"]) for column in columns]
        selection = sql.SQL("SELECT * FROM {} ORDER BY {}").format(
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in column_names),
        )
        rows = db.raw.execute(selection).fetchall()
        payload = json.dumps(
            [[row[column] for column in column_names] for row in rows],
            default=str,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        digest.update(table.encode())
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    base = os.environ["FUR_TEST_POSTGRES"]
    parsed = urlparse(base)
    names = ["fur_drill_" + uuid4().hex for _ in range(2)]
    admin = psycopg.connect(base, autocommit=True)
    try:
        for name in names:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        source_url = urlunparse(parsed._replace(path="/" + names[0]))
        target_url = urlunparse(parsed._replace(path="/" + names[1]))
        game = Game(source_url)
        user = identity()
        with game.transaction() as db:
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, "RestoreTest", "unused"))
            game.create(db, user, "RestoreTest")
            game.command(
                db, user, "alliance_create", {"tag": "RST", "name": "Restore Alliance"}, identity()
            )
            colony = game.read(db, user)
            colony["resources"] = [1234, 2345, 3456]
            colony["buildings"]["wood"] = 4
            colony["tech"]["engineering"] = 2
            colony["units"]["ranger"] = 5
            game.save(db, colony)
            initial_view = game.view(db, user)
            targets = [target for target in initial_view["world"] if target["owner"] is None]
            if not targets:
                raise RuntimeError("Restore drill has no visible neutral mission target")
            target = max(targets, key=lambda item: int(item["travel_seconds"] or 0))
            game.command(db, user, "raid", {"key": target["id"], "army": {"ranger": 1}}, identity())
            colony = game.read(db, user)
            # Keep the real mission pending while the dump is restored and checked.
            colony["jobs"][0]["due"] += 86400
            colony["vacation_until"] = colony["last"] + 86400
            game.save(db, colony)
            original = game.view(db, user)
            expected_missions = mission_digest(original["jobs"])
            expected_database = database_digest(db)
        env = dict(os.environ)
        env.update(
            PGHOST=parsed.hostname or "127.0.0.1",
            PGPORT=str(parsed.port or 5432),
            PGUSER=unquote(parsed.username or ""),
            PGPASSWORD=unquote(parsed.password or ""),
        )
        with tempfile.TemporaryDirectory() as directory:
            dump = Path(directory) / "restore.dump"
            env["PGDATABASE"] = names[0]
            subprocess.run(
                ["pg_dump", "--format=custom", "--file", str(dump)],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["pg_restore", "--exit-on-error", "--dbname", names[1], str(dump)],
                env=env,
                check=True,
                capture_output=True,
            )
            restored = Game(target_url)
            with restored.transaction() as db:
                current = restored.read(db, user)
                membership = db.execute(
                    "SELECT alliance_id,role FROM members WHERE user_id=?", (user,)
                ).fetchone()
                assert membership["alliance_id"] == original["membership"]["alliance_id"]
                assert membership["role"] == original["membership"]["role"]
                assert current["buildings"] == original["buildings"]
                assert current["resources"] == original["resources"]
                assert mission_digest(current["jobs"]) == expected_missions
                world_posts = db.execute(
                    "SELECT count(*) FROM world_outposts WHERE world_id=1"
                ).fetchone()[0]
                assert world_posts == 104
                assert db.execute("SELECT count(*) FROM world_terrain").fetchone()[0] == 4096
                assert db.execute("SELECT count(*) FROM map_sector_intel").fetchone()[0] > 0
                assert db.execute("SELECT count(*) FROM audit").fetchone()[0] == 1
                restored_database = database_digest(db)
                assert restored_database == expected_database
            print(
                json.dumps(
                    {
                        "postgres_backup_restore": "passed",
                        "world_posts": world_posts,
                        "terrain_cells": 4096,
                        "pending_missions": len(current["jobs"]),
                        "mission_sha256": expected_missions,
                        "database_sha256": restored_database,
                        "resources_preserved": True,
                        "restored_alliance": True,
                    }
                )
            )
    finally:
        for name in names:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )
        admin.close()


if __name__ == "__main__":
    main()
