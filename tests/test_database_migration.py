"""Fresh PostgreSQL startup must remain serialized across migration commits."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.parse import quote

import pytest

from fur_empire.database import Connection, migrate
from fur_empire.game import Game, identity


def test_parallel_postgres_bootstrap_and_failed_migration_release_lock(monkeypatch):
    base = os.getenv("FUR_TEST_POSTGRES")
    if not base:
        pytest.skip("FUR_TEST_POSTGRES not configured")
    import psycopg
    from psycopg import sql

    schema = "fur_startup_" + identity().replace("-", "")
    target = base + ("&" if "?" in base else "?") + "options=" + quote("-csearch_path=" + schema)
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            barrier = Barrier(2)

            def bootstrap():
                barrier.wait(timeout=30)
                return Game(target)

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(bootstrap) for _ in range(2)]
                games = [future.result(timeout=240) for future in futures]
            with games[0].transaction() as db:
                assert db.execute("SELECT COUNT(*) FROM world WHERE id=1").fetchone()[0] == 1
                assert (
                    db.execute("SELECT COUNT(*) FROM world_outposts WHERE world_id=1").fetchone()[0]
                    == 104
                )
                assert (
                    db.execute("SELECT COUNT(*) FROM world_terrain WHERE world_id=1").fetchone()[0]
                    == 4096
                )
                assert db.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 123

            # Exercise the failure path without relying on closing the connection
            # to release the session lock. PostgreSQL is left in an aborted SQL
            # transaction until migrate rolls it back and explicitly unlocks.
            def fail(db):
                db.execute("SELECT 1 / 0")

            with Connection(target) as broken:
                with monkeypatch.context() as patch:
                    patch.setattr("fur_empire.database._migrate", fail)
                    with pytest.raises(psycopg.errors.DivisionByZero):
                        migrate(broken)
                with Connection(target) as other:
                    assert other.execute("SELECT pg_try_advisory_lock(714190725)").fetchone()[0]
                    assert other.execute("SELECT pg_advisory_unlock(714190725)").fetchone()[0]
        finally:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
