"""Small DB-API adapter: SQLite locally, PostgreSQL for deployment.

All game transactions acquire one world lock. This deliberately favors deterministic
simulation and correctness over write throughput; scale is measured, never inferred.
"""

import json
import secrets
import sqlite3
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, Self

SQLITE_BUSY_TIMEOUT_SECONDS = 120


class Row(dict[str, Any]):
    def __getitem__(self, key: str | int) -> Any:
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Cursor:
    def __init__(self, cursor: Any):
        self.cursor = cursor

    def fetchone(self) -> Any:
        row = self.cursor.fetchone()
        return Row(row) if isinstance(row, dict) else row

    def fetchall(self) -> list[Any]:
        return list(self)

    def __iter__(self) -> Iterator[Any]:
        for row in self.cursor:
            yield Row(row) if isinstance(row, dict) else row


class Connection:
    def __init__(self, target: str):
        self.postgres = target.startswith(("postgresql://", "postgres://"))
        self.raw: Any
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row

            self.raw = psycopg.connect(target, row_factory=dict_row, connect_timeout=10)
        else:
            self.raw = sqlite3.connect(target, timeout=SQLITE_BUSY_TIMEOUT_SECONDS)
            self.raw.row_factory = sqlite3.Row
            self.raw.execute("PRAGMA foreign_keys=ON")

    def execute(self, sql: str, params: Sequence[Any] = ()) -> Cursor:
        if sql == "BEGIN IMMEDIATE" and self.postgres:
            self.raw.execute("SELECT pg_advisory_xact_lock(714190725)")
            return Cursor(self.raw.execute("SELECT 1"))
        return Cursor(self.raw.execute(sql.replace("?", "%s") if self.postgres else sql, params))

    def executescript(self, sql: str) -> None:
        if self.postgres:
            self.raw.execute(sql)
        else:
            self.raw.executescript(sql)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        try:
            if args[0] is None:
                self.raw.commit()
            else:
                self.raw.rollback()
        finally:
            self.raw.close()


def migrate(db: Connection) -> None:
    if not db.postgres:
        _migrate(db)
        return
    # Migration scripts commit individually. A transaction-level lock would be
    # released by the first COMMIT, exposing later DDL to concurrent bootstraps.
    # Use the live-world lock key so neither another migrator nor a worker enters.
    db.execute("SELECT pg_advisory_lock(714190725)")
    try:
        _migrate(db)
        db.raw.commit()
    finally:
        # Roll back any failed script before executing the unlock. Session locks
        # survive rollback; the connection context also closes on any exception.
        db.raw.rollback()
        db.execute("SELECT pg_advisory_unlock(714190725)")


def _migrate(db: Connection) -> None:
    root = Path(__file__).parent
    if db.postgres:
        # DDL and seed initialization must use the same lock as live transactions.
        db.execute("BEGIN IMMEDIATE")
        db.executescript((root / "migrations" / "001_postgres.sql").read_text())
    else:
        db.executescript((root / "migration.sql").read_text())
    db.executescript((root / "migrations" / "002_multiplayer.sql").read_text())
    db.executescript((root / "migrations" / "003_season_rules.sql").read_text())
    db.executescript((root / "migrations" / "004_map_bookmarks.sql").read_text())
    immutable_rules_migration = (
        "003_season_rules_postgres.sql" if db.postgres else "003_season_rules_sqlite.sql"
    )
    db.executescript((root / "migrations" / immutable_rules_migration).read_text())
    db.execute("INSERT INTO schema_versions(version) VALUES (4) ON CONFLICT(version) DO NOTHING")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=5").fetchone():
        colony_migration = (
            "005_multi_colony_postgres.sql" if db.postgres else "005_multi_colony_sqlite.sql"
        )
        db.executescript((root / "migrations" / colony_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=6").fetchone():
        intel_migration = (
            "006_player_intel_postgres.sql" if db.postgres else "006_player_intel_sqlite.sql"
        )
        db.executescript((root / "migrations" / intel_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=82").fetchone():
        score_migration = (
            "082_war_score_ledger_postgres.sql"
            if db.postgres
            else "082_war_score_ledger_sqlite.sql"
        )
        db.executescript((root / "migrations" / score_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=83").fetchone():
        alliance_permissions_migration = (
            "083_alliance_role_permissions_postgres.sql"
            if db.postgres
            else "083_alliance_role_permissions_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_permissions_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=84").fetchone():
        alliance_transfer_migration = (
            "084_alliance_transfer_requests_postgres.sql"
            if db.postgres
            else "084_alliance_transfer_requests_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_transfer_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=85").fetchone():
        alliance_wars_migration = (
            "085_alliance_wars_postgres.sql" if db.postgres else "085_alliance_wars_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_wars_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=86").fetchone():
        alliance_season_migration = (
            "086_alliance_season_ranking_postgres.sql"
            if db.postgres
            else "086_alliance_season_ranking_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_season_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=87").fetchone():
        alliance_treasury_migration = (
            "087_alliance_treasury_postgres.sql"
            if db.postgres
            else "087_alliance_treasury_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_treasury_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=88").fetchone():
        alliance_projects_migration = (
            "088_alliance_projects_postgres.sql"
            if db.postgres
            else "088_alliance_projects_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_projects_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=89").fetchone():
        player_profiles_migration = (
            "089_player_profiles_postgres.sql" if db.postgres else "089_player_profiles_sqlite.sql"
        )
        db.executescript((root / "migrations" / player_profiles_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=90").fetchone():
        alliance_reports_migration = (
            "090_alliance_shared_reports_postgres.sql"
            if db.postgres
            else "090_alliance_shared_reports_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_reports_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=91").fetchone():
        moderation_cases_migration = (
            "091_moderation_cases_postgres.sql"
            if db.postgres
            else "091_moderation_cases_sqlite.sql"
        )
        db.executescript((root / "migrations" / moderation_cases_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=92").fetchone():
        announcements_mailbox_migration = (
            "092_announcements_mailbox_postgres.sql"
            if db.postgres
            else "092_announcements_mailbox_sqlite.sql"
        )
        db.executescript((root / "migrations" / announcements_mailbox_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=93").fetchone():
        notification_migration = (
            "092_item010_notifications_postgres.sql"
            if db.postgres
            else "092_item010_notifications_sqlite.sql"
        )
        db.executescript((root / "migrations" / notification_migration).read_text())
        db.execute("INSERT INTO schema_versions(version) VALUES (93)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=7").fetchone():
        terrain_migration = (
            "007_world_terrain_postgres.sql" if db.postgres else "007_world_terrain_sqlite.sql"
        )
        db.executescript((root / "migrations" / terrain_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=8").fetchone():
        market_history_migration = (
            "008_market_history_postgres.sql" if db.postgres else "008_market_history_sqlite.sql"
        )
        db.executescript((root / "migrations" / market_history_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=9").fetchone():
        outposts_migration = (
            "009_world_outposts_postgres.sql" if db.postgres else "009_world_outposts_sqlite.sql"
        )
        db.executescript((root / "migrations" / outposts_migration).read_text())
        for world in db.execute("SELECT id,state FROM world"):
            for position, target in enumerate(json.loads(world["state"])):
                db.execute(
                    "INSERT INTO world_outposts(world_id,target_id,sort_order,x,y,state) "
                    "VALUES (?,?,?,?,?,?) ON CONFLICT(world_id,target_id) DO NOTHING",
                    (
                        world["id"],
                        target["id"],
                        position,
                        target["x"],
                        target["y"],
                        json.dumps(target),
                    ),
                )
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (9) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=10").fetchone():
        world_context_migration = (
            "010_world_context_postgres.sql" if db.postgres else "010_world_context_sqlite.sql"
        )
        if not db.postgres:
            # Rebuild the parent table to remove its historical id=1 check while
            # retaining every dependent row and the child tables' world FKs.
            db.raw.commit()
            db.raw.execute("PRAGMA foreign_keys=OFF")
        try:
            db.executescript((root / "migrations" / world_context_migration).read_text())
        finally:
            if not db.postgres:
                db.raw.execute("PRAGMA foreign_keys=ON")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=11").fetchone():
        world_scoped_migration = (
            "011_world_scoped_data_postgres.sql"
            if db.postgres
            else "011_world_scoped_data_sqlite.sql"
        )
        db.executescript((root / "migrations" / world_scoped_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=12").fetchone():
        sector_intel_migration = (
            "012_sector_intel_postgres.sql" if db.postgres else "012_sector_intel_sqlite.sql"
        )
        db.executescript((root / "migrations" / sector_intel_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=13").fetchone():
        mission_templates_migration = (
            "013_mission_templates_postgres.sql"
            if db.postgres
            else "013_mission_templates_sqlite.sql"
        )
        db.executescript((root / "migrations" / mission_templates_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=14").fetchone():
        expedition_templates_migration = (
            "014_expedition_templates_postgres.sql"
            if db.postgres
            else "014_expedition_templates_sqlite.sql"
        )
        db.executescript((root / "migrations" / expedition_templates_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=15").fetchone():
        alliance_applications_migration = (
            "015_alliance_applications_postgres.sql"
            if db.postgres
            else "015_alliance_applications_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_applications_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=16").fetchone():
        session_management_migration = (
            "016_session_management_postgres.sql"
            if db.postgres
            else "016_session_management_sqlite.sql"
        )
        db.executescript((root / "migrations" / session_management_migration).read_text())
        for row in db.execute("SELECT token FROM sessions WHERE session_id IS NULL").fetchall():
            db.execute(
                "UPDATE sessions SET session_id=? WHERE token=?",
                (secrets.token_urlsafe(18), row["token"]),
            )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=17").fetchone():
        recovery_migration = (
            "017_mfa_recovery_codes_postgres.sql"
            if db.postgres
            else "017_mfa_recovery_codes_sqlite.sql"
        )
        db.executescript((root / "migrations" / recovery_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=18").fetchone():
        account_name_migration = (
            "018_account_name_cooldown_postgres.sql"
            if db.postgres
            else "018_account_name_cooldown_sqlite.sql"
        )
        db.executescript((root / "migrations" / account_name_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=19").fetchone():
        production_templates_migration = (
            "019_production_templates_postgres.sql"
            if db.postgres
            else "019_production_templates_sqlite.sql"
        )
        db.executescript((root / "migrations" / production_templates_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=20").fetchone():
        social_lists_migration = (
            "020_social_lists_postgres.sql" if db.postgres else "020_social_lists_sqlite.sql"
        )
        db.executescript((root / "migrations" / social_lists_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=21").fetchone():
        player_notes_migration = (
            "021_player_notes_postgres.sql" if db.postgres else "021_player_notes_sqlite.sql"
        )
        db.executescript((root / "migrations" / player_notes_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=22").fetchone():
        alliance_bulletin_migration = (
            "022_alliance_bulletin_postgres.sql"
            if db.postgres
            else "022_alliance_bulletin_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_bulletin_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=23").fetchone():
        alliance_forum_migration = (
            "023_alliance_forum_postgres.sql" if db.postgres else "023_alliance_forum_sqlite.sql"
        )
        db.executescript((root / "migrations" / alliance_forum_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=24").fetchone():
        diplomacy_chronicle_migration = (
            "024_diplomacy_chronicle_postgres.sql"
            if db.postgres
            else "024_diplomacy_chronicle_sqlite.sql"
        )
        db.executescript((root / "migrations" / diplomacy_chronicle_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=25").fetchone():
        incoming_attacks_migration = (
            "025_incoming_attack_index_postgres.sql"
            if db.postgres
            else "025_incoming_attack_index_sqlite.sql"
        )
        db.executescript((root / "migrations" / incoming_attacks_migration).read_text())
        for row in db.execute("SELECT colony_id,user_id,state FROM colonies"):
            state = json.loads(row["state"])
            for job in state.get("jobs", []):
                if job.get("kind") != "attack" or not job.get("key"):
                    continue
                target = db.execute("SELECT 1 FROM users WHERE id=?", (job["key"],)).fetchone()
                if target:
                    db.execute(
                        "INSERT INTO incoming_attack_index(job_id,target_user,source_colony_id,due) "
                        "VALUES (?,?,?,?) ON CONFLICT(job_id) DO NOTHING",
                        (job["id"], job["key"], row["colony_id"], job["due"]),
                    )
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (25) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=26").fetchone():
        events_feed_migration = (
            "026_events_feed_postgres.sql" if db.postgres else "026_events_feed_sqlite.sql"
        )
        db.executescript((root / "migrations" / events_feed_migration).read_text())
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (26) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=27").fetchone():
        sessions_feed_migration = (
            "027_session_inventory_feed_postgres.sql"
            if db.postgres
            else "027_session_inventory_feed_sqlite.sql"
        )
        db.executescript((root / "migrations" / sessions_feed_migration).read_text())
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (27) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=28").fetchone():
        colony_names_migration = (
            "028_colony_name_index_postgres.sql"
            if db.postgres
            else "028_colony_name_index_sqlite.sql"
        )
        db.executescript((root / "migrations" / colony_names_migration).read_text())
        for row in db.execute("SELECT colony_id,state FROM colonies"):
            state = json.loads(row["state"])
            name = state.get("colony_name", state.get("name", ""))
            if not isinstance(name, str) or not name.strip():
                raise RuntimeError(f"Colony {row['colony_id']} has no valid display name")
            db.execute(
                "UPDATE colonies SET name_key=? WHERE colony_id=?",
                (name.casefold(), row["colony_id"]),
            )
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (28) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=29").fetchone():
        ranking_migration = (
            "029_colony_ranking_score_postgres.sql"
            if db.postgres
            else "029_colony_ranking_score_sqlite.sql"
        )
        db.executescript((root / "migrations" / ranking_migration).read_text())
        for row in db.execute("SELECT colony_id,state FROM colonies"):
            state = json.loads(row["state"])
            buildings = state.get("buildings", {})
            tech = state.get("tech", {})
            score = (
                10 * sum(buildings.values())
                + 20 * sum(tech.values())
                + 100 * int(state.get("captures", 0))
            )
            db.execute(
                "UPDATE colonies SET ranking_score=? WHERE colony_id=?",
                (score, row["colony_id"]),
            )
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (29) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=30").fetchone():
        goods_migration = (
            "030_neutral_goods_postgres.sql" if db.postgres else "030_neutral_goods_sqlite.sql"
        )
        db.executescript((root / "migrations" / goods_migration).read_text())
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (30) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=31").fetchone():
        home_migration = (
            "031_colony_home_postgres.sql" if db.postgres else "031_colony_home_sqlite.sql"
        )
        db.executescript((root / "migrations" / home_migration).read_text())
        db.execute(
            "INSERT INTO schema_versions(version) VALUES (31) ON CONFLICT(version) DO NOTHING"
        )
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=32").fetchone():
        db.execute(
            "CREATE TABLE world_players ("
            "user_id TEXT NOT NULL REFERENCES users(id), "
            "world_id INTEGER NOT NULL REFERENCES world(id), "
            "faction TEXT CHECK(faction IN ('pioneers','wardens','syndicate')), "
            "PRIMARY KEY(user_id,world_id))"
        )
        rows = db.execute(
            "SELECT c.user_id,c.world_id,c.state,p.faction FROM colonies c "
            "LEFT JOIN profiles p ON p.user_id=c.user_id"
        ).fetchall()
        for row in rows:
            chosen = json.loads(row["state"]).get("faction_chosen")
            faction = (row["faction"] or "pioneers") if chosen else None
            db.execute(
                "INSERT INTO world_players(user_id,world_id,faction) VALUES (?,?,?) "
                "ON CONFLICT(user_id,world_id) DO UPDATE SET "
                "faction=COALESCE(world_players.faction,excluded.faction)",
                (row["user_id"], row["world_id"], faction),
            )
        db.execute("INSERT INTO schema_versions(version) VALUES (32)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=33").fetchone():
        db.execute(
            "ALTER TABLE world_settings ADD COLUMN mode TEXT NOT NULL DEFAULT 'permanent' "
            "CHECK(mode IN ('permanent','season','sandbox'))"
        )
        db.execute("ALTER TABLE events ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1")
        db.execute("ALTER TABLE seasons ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1")
        db.execute("CREATE INDEX events_world_page ON events(world_id,starts DESC,id DESC)")
        db.execute("CREATE INDEX seasons_world_page ON seasons(world_id,starts DESC,id DESC)")
        db.execute("INSERT INTO schema_versions(version) VALUES (33)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=34").fetchone():
        db.execute(
            "CREATE TABLE rule_catalogs ("
            "version TEXT PRIMARY KEY, snapshot TEXT NOT NULL, digest TEXT NOT NULL UNIQUE)"
        )
        db.execute(
            "CREATE TABLE world_rulesets ("
            "world_id INTEGER PRIMARY KEY REFERENCES world(id), "
            "version TEXT NOT NULL REFERENCES rule_catalogs(version))"
        )
        if db.postgres:
            for table in ("rule_catalogs", "world_rulesets"):
                db.execute(
                    f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
                    "FOR EACH ROW EXECUTE FUNCTION prevent_season_rules_mutation()"
                )
        else:
            for table in ("rule_catalogs", "world_rulesets"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(
                        f"CREATE TRIGGER {table}_no_{operation.lower()} "
                        f"BEFORE {operation} ON {table} BEGIN "
                        "SELECT RAISE(ABORT, 'immutable rules'); END"
                    )
        db.execute("INSERT INTO schema_versions(version) VALUES (34)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=35").fetchone():
        db.execute(
            "CREATE TABLE orbit_access ("
            "user_id TEXT NOT NULL REFERENCES users(id), "
            "world_id INTEGER NOT NULL REFERENCES world(id), "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version), "
            "unlocked_at BIGINT NOT NULL, "
            "PRIMARY KEY(user_id,world_id))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (35)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=36").fetchone():
        db.execute(
            "ALTER TABLE orbit_access ADD COLUMN pioneer_available BOOLEAN NOT NULL DEFAULT TRUE"
        )
        db.execute(
            "CREATE TABLE orbit_planet_claims ("
            "world_id INTEGER NOT NULL, galaxy INTEGER NOT NULL CHECK(galaxy>0), "
            "system_no INTEGER NOT NULL CHECK(system_no>0), slot INTEGER NOT NULL CHECK(slot>0), "
            "owner TEXT NOT NULL, mission_id TEXT NOT NULL UNIQUE, "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version), "
            "arrival BIGINT NOT NULL, founded_at BIGINT, "
            "PRIMARY KEY(world_id,galaxy,system_no,slot), "
            "FOREIGN KEY(owner,world_id) REFERENCES orbit_access(user_id,world_id))"
        )
        db.execute(
            "CREATE INDEX orbit_claim_arrivals ON orbit_planet_claims(arrival,mission_id) WHERE founded_at IS NULL"
        )
        db.execute("CREATE INDEX orbit_claim_owner ON orbit_planet_claims(owner,world_id)")
        db.execute("INSERT INTO schema_versions(version) VALUES (36)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=37").fetchone():
        db.execute(
            "CREATE TABLE orbit_economy ("
            "mission_id TEXT PRIMARY KEY REFERENCES orbit_planet_claims(mission_id), "
            "ore INTEGER NOT NULL CHECK(ore>=0), ether INTEGER NOT NULL CHECK(ether>=0), "
            "solar INTEGER NOT NULL CHECK(solar>=1), refinery INTEGER NOT NULL CHECK(refinery>=0), "
            "updated_at BIGINT NOT NULL, remainder INTEGER NOT NULL CHECK(remainder>=0 AND remainder<3600), "
            "job TEXT CHECK(job IN ('solar','refinery')), due BIGINT, "
            "CHECK((job IS NULL AND due IS NULL) OR (job IS NOT NULL AND due IS NOT NULL)))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (37)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=38").fetchone():
        db.execute(
            "ALTER TABLE orbit_economy ADD COLUMN ore_remainder INTEGER NOT NULL DEFAULT 0 "
            "CHECK(ore_remainder>=0 AND ore_remainder<3600)"
        )
        db.execute("ALTER TABLE orbit_economy ADD COLUMN shipbuilding_ready_at BIGINT")
        db.execute(
            "CREATE TABLE orbit_ship_orders ("
            "mission_id TEXT PRIMARY KEY REFERENCES orbit_economy(mission_id), "
            "ship TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount BETWEEN 1 AND 100), "
            "due BIGINT NOT NULL)"
        )
        db.execute("CREATE INDEX orbit_ship_orders_due ON orbit_ship_orders(due,mission_id)")
        db.execute(
            "CREATE TABLE orbit_ships (mission_id TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ship TEXT NOT NULL, amount BIGINT NOT NULL CHECK(amount>=0), "
            "PRIMARY KEY(mission_id,ship))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (38)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=39").fetchone():
        for resource in ("ore", "ether"):
            db.execute(
                f"ALTER TABLE orbit_economy ADD COLUMN {resource}_reserve BIGINT NOT NULL "
                f"DEFAULT 0 CHECK({resource}_reserve>=0)"
            )
        db.execute(
            "CREATE TABLE orbit_transports ("
            "id TEXT PRIMARY KEY, origin TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "target TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ore INTEGER NOT NULL CHECK(ore>=0), ether INTEGER NOT NULL CHECK(ether>=0), "
            "ships INTEGER NOT NULL CHECK(ships BETWEEN 1 AND 100), "
            "due BIGINT NOT NULL, duration INTEGER NOT NULL CHECK(duration>0), "
            "is_returning BOOLEAN NOT NULL DEFAULT FALSE, "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version), CHECK(origin<>target))"
        )
        db.execute("CREATE INDEX orbit_transports_due ON orbit_transports(due,id)")
        db.execute("CREATE INDEX orbit_transports_origin ON orbit_transports(origin)")
        db.execute("INSERT INTO schema_versions(version) VALUES (39)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=40").fetchone():
        db.execute(
            "ALTER TABLE orbit_transports ADD COLUMN recalled BOOLEAN NOT NULL DEFAULT FALSE"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (40)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=41").fetchone():
        db.execute(
            "CREATE TABLE orbit_scouts ("
            "id TEXT PRIMARY KEY, origin TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "galaxy INTEGER NOT NULL, system_no INTEGER NOT NULL, slot INTEGER NOT NULL, "
            "due BIGINT NOT NULL, duration INTEGER NOT NULL, is_returning BOOLEAN NOT NULL DEFAULT FALSE, "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version))"
        )
        db.execute("CREATE INDEX orbit_scouts_due ON orbit_scouts(due,id)")
        db.execute(
            "CREATE TABLE orbit_intel ("
            "observer TEXT NOT NULL, world_id INTEGER NOT NULL, galaxy INTEGER NOT NULL, "
            "system_no INTEGER NOT NULL, slot INTEGER NOT NULL, occupied BOOLEAN NOT NULL, "
            "observed_at BIGINT NOT NULL, PRIMARY KEY(observer,world_id,galaxy,system_no,slot), "
            "FOREIGN KEY(observer,world_id) REFERENCES orbit_access(user_id,world_id))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (41)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=42").fetchone():
        db.execute(
            "CREATE TABLE orbit_attacks ("
            "id TEXT PRIMARY KEY, origin TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "target TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ship TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>=0), "
            "due BIGINT NOT NULL, duration INTEGER NOT NULL CHECK(duration>0), "
            "seed TEXT NOT NULL, rule_version TEXT NOT NULL REFERENCES rule_catalogs(version), "
            "is_returning BOOLEAN NOT NULL DEFAULT FALSE)"
        )
        db.execute("CREATE INDEX orbit_attacks_due ON orbit_attacks(due,id)")
        db.execute(
            "CREATE TABLE orbit_battle_reports ("
            "id TEXT PRIMARY KEY, origin TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "target TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "resolved_at BIGINT NOT NULL, report TEXT NOT NULL)"
        )
        db.execute("CREATE INDEX orbit_battle_origin ON orbit_battle_reports(origin,resolved_at)")
        db.execute("CREATE INDEX orbit_battle_target ON orbit_battle_reports(target,resolved_at)")
        db.execute("INSERT INTO schema_versions(version) VALUES (42)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=43").fetchone():
        db.execute(
            "CREATE TABLE orbit_debris ("
            "battle_id TEXT PRIMARY KEY REFERENCES orbit_battle_reports(id), "
            "ore BIGINT NOT NULL CHECK(ore>=0), ether BIGINT NOT NULL CHECK(ether>=0), "
            "expires BIGINT NOT NULL)"
        )
        db.execute(
            "ALTER TABLE orbit_transports ADD COLUMN salvage_report TEXT "
            "REFERENCES orbit_debris(battle_id)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (43)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=44").fetchone():
        db.execute("ALTER TABLE orbit_economy ADD COLUMN defense_ready_at BIGINT")
        db.execute("INSERT INTO schema_versions(version) VALUES (44)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=45").fetchone():
        db.execute(
            "CREATE TABLE orbit_moons ("
            "colony_id TEXT PRIMARY KEY REFERENCES orbit_economy(mission_id), "
            "battle_id TEXT NOT NULL UNIQUE REFERENCES orbit_battle_reports(id), "
            "formed_at BIGINT NOT NULL)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (45)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=46").fetchone():
        db.execute(
            "CREATE TABLE orbit_stations ("
            "colony_id TEXT PRIMARY KEY REFERENCES orbit_economy(mission_id), "
            "level INTEGER NOT NULL CHECK(level BETWEEN 0 AND 3), "
            "ready_at BIGINT, maintained_until BIGINT NOT NULL)"
        )
        db.execute(
            "CREATE TABLE orbit_station_ships ("
            "colony_id TEXT NOT NULL REFERENCES orbit_stations(colony_id), ship TEXT NOT NULL, "
            "amount BIGINT NOT NULL CHECK(amount>=0), PRIMARY KEY(colony_id,ship))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (46)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=47").fetchone():
        db.execute("ALTER TABLE orbit_moons ADD COLUMN scanner_ready_at BIGINT")
        db.execute(
            "ALTER TABLE orbit_scouts ADD COLUMN intel_level INTEGER NOT NULL DEFAULT 1 "
            "CHECK(intel_level IN (1,2))"
        )
        db.execute(
            "ALTER TABLE orbit_intel ADD COLUMN intel_level INTEGER NOT NULL DEFAULT 1 "
            "CHECK(intel_level BETWEEN 0 AND 2)"
        )
        db.execute("ALTER TABLE orbit_intel ADD COLUMN ships BIGINT CHECK(ships>=0)")
        db.execute("INSERT INTO schema_versions(version) VALUES (47)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=48").fetchone():
        db.execute(
            "CREATE TABLE orbit_jumpgates ("
            "colony_id TEXT PRIMARY KEY REFERENCES orbit_stations(colony_id), "
            "ready_at BIGINT NOT NULL, cooldown_until BIGINT NOT NULL DEFAULT 0)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (48)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=49").fetchone():
        db.execute(
            "CREATE TABLE orbit_expeditions ("
            "id TEXT PRIMARY KEY, origin TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "galaxy INTEGER NOT NULL, system_no INTEGER NOT NULL, slot INTEGER NOT NULL, "
            "ships INTEGER NOT NULL CHECK(ships BETWEEN 1 AND 100), "
            "due BIGINT NOT NULL, duration INTEGER NOT NULL CHECK(duration>0), "
            "seed TEXT NOT NULL, result TEXT, finished_at BIGINT, "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version))"
        )
        db.execute(
            "CREATE INDEX orbit_expeditions_due ON orbit_expeditions(due,id) WHERE finished_at IS NULL"
        )
        db.execute("CREATE INDEX orbit_expeditions_origin ON orbit_expeditions(origin,finished_at)")
        db.execute("INSERT INTO schema_versions(version) VALUES (49)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=50").fetchone():
        db.execute(
            "CREATE TABLE orbit_phalanx_scans ("
            "colony_id TEXT PRIMARY KEY REFERENCES orbit_moons(colony_id), "
            "observed_at BIGINT NOT NULL, result TEXT NOT NULL)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (50)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=51").fetchone():
        db.execute("ALTER TABLE orbit_moons ADD COLUMN destroyed_at BIGINT")
        db.execute("ALTER TABLE orbit_intel ADD COLUMN moon BOOLEAN")
        db.execute(
            "ALTER TABLE orbit_attacks ADD COLUMN moon_target TEXT REFERENCES orbit_moons(battle_id)"
        )
        db.execute(
            "CREATE UNIQUE INDEX orbit_moon_attack_pending ON orbit_attacks(moon_target) "
            "WHERE is_returning=FALSE AND moon_target IS NOT NULL"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (51)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=52").fetchone():
        db.execute("ALTER TABLE orbit_attacks ADD COLUMN alliance_id TEXT")
        db.execute(
            "CREATE TABLE orbit_attack_wings ("
            "attack_id TEXT NOT NULL, colony_id TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ship TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount BETWEEN 0 AND 100), "
            "participated BOOLEAN NOT NULL DEFAULT FALSE, "
            "PRIMARY KEY(attack_id,colony_id))"
        )
        db.execute("CREATE INDEX orbit_wings_colony ON orbit_attack_wings(colony_id,attack_id)")
        db.execute("INSERT INTO schema_versions(version) VALUES (52)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=53").fetchone():
        db.execute(
            "ALTER TABLE orbit_attacks ADD COLUMN retreat_pct INTEGER "
            "CHECK(retreat_pct BETWEEN 10 AND 100)"
        )
        db.execute("ALTER TABLE orbit_attacks ADD COLUMN fuel_spent BIGINT")
        db.execute("ALTER TABLE orbit_attacks ADD COLUMN recalled BOOLEAN NOT NULL DEFAULT FALSE")
        db.execute("INSERT INTO schema_versions(version) VALUES (53)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=54").fetchone():
        db.execute(
            "CREATE TABLE orbit_templates ("
            "id TEXT PRIMARY KEY, owner TEXT NOT NULL, world_id INTEGER NOT NULL, "
            "kind TEXT NOT NULL CHECK(kind IN ('fleet','shipyard')), name TEXT NOT NULL, "
            "ship TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount BETWEEN 1 AND 100), "
            "retreat_pct INTEGER CHECK(retreat_pct BETWEEN 10 AND 100), "
            "CHECK(kind='fleet' OR retreat_pct IS NULL), "
            "FOREIGN KEY(owner,world_id) REFERENCES orbit_access(user_id,world_id))"
        )
        db.execute(
            "CREATE UNIQUE INDEX orbit_template_names "
            "ON orbit_templates(owner,world_id,kind,lower(name))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (54)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=55").fetchone():
        db.execute("ALTER TABLE orbit_economy ADD COLUMN supplied_until BIGINT NOT NULL DEFAULT 0")
        db.execute("UPDATE orbit_economy SET supplied_until=updated_at+604800")
        db.execute("INSERT INTO schema_versions(version) VALUES (55)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=56").fetchone():
        db.execute(
            "CREATE TABLE orbit_wrecks ("
            "battle_id TEXT NOT NULL REFERENCES orbit_battle_reports(id), "
            "colony_id TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ship TEXT NOT NULL, amount BIGINT NOT NULL CHECK(amount>=0), expires BIGINT NOT NULL, "
            "PRIMARY KEY(battle_id,colony_id,ship))"
        )
        db.execute("CREATE INDEX orbit_wrecks_colony ON orbit_wrecks(colony_id,ship,expires)")
        db.execute("INSERT INTO schema_versions(version) VALUES (56)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=57").fetchone():
        db.execute(
            "CREATE TABLE terra_orbit_cargo ("
            "id TEXT PRIMARY KEY, terra_colony TEXT NOT NULL REFERENCES colonies(colony_id), "
            "orbit_colony TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "to_orbit BOOLEAN NOT NULL, ore INTEGER NOT NULL CHECK(ore BETWEEN 1 AND 500), "
            "due BIGINT NOT NULL, rule_version TEXT NOT NULL REFERENCES rule_catalogs(version), "
            "UNIQUE(terra_colony,orbit_colony))"
        )
        db.execute("CREATE INDEX terra_orbit_cargo_due ON terra_orbit_cargo(due,id)")
        db.execute("CREATE INDEX terra_orbit_cargo_terra ON terra_orbit_cargo(terra_colony)")
        db.execute("INSERT INTO schema_versions(version) VALUES (57)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=58").fetchone():
        for stock in ("lances", "screens"):
            db.execute(
                f"ALTER TABLE orbit_economy ADD COLUMN {stock} INTEGER NOT NULL DEFAULT 0 "
                f"CHECK({stock} BETWEEN 0 AND 20)"
            )
        db.execute(
            "ALTER TABLE orbit_attacks ADD COLUMN lances INTEGER NOT NULL DEFAULT 0 "
            "CHECK(lances BETWEEN 0 AND 20)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (58)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=59").fetchone():
        db.execute(
            "CREATE TABLE orbit_special_events ("
            "id TEXT PRIMARY KEY, world_id INTEGER NOT NULL REFERENCES world(id), "
            "kind TEXT NOT NULL CHECK(kind IN ('solar','anomaly','boss')), "
            "starts BIGINT NOT NULL, ends BIGINT NOT NULL CHECK(ends>starts), "
            "rule_version TEXT NOT NULL REFERENCES rule_catalogs(version))"
        )
        db.execute("CREATE INDEX orbit_special_events_world ON orbit_special_events(world_id,ends)")
        db.execute(
            "ALTER TABLE orbit_expeditions ADD COLUMN special_event TEXT REFERENCES orbit_special_events(id)"
        )
        db.execute(
            "CREATE TABLE orbit_event_rewards ("
            "event_id TEXT NOT NULL REFERENCES orbit_special_events(id), "
            "user_id TEXT NOT NULL REFERENCES users(id), "
            "mission_id TEXT NOT NULL UNIQUE REFERENCES orbit_expeditions(id), "
            "PRIMARY KEY(event_id,user_id))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (59)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=60").fetchone():
        db.execute(
            "CREATE TABLE terra_sector_rules ("
            "world_id INTEGER NOT NULL REFERENCES world(id), "
            "x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63), "
            "y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63), "
            "kind TEXT NOT NULL CHECK(kind IN ('protected','spawn_reserved')), "
            "PRIMARY KEY(world_id,x,y))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (60)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=61").fetchone():
        db.execute(
            "CREATE TABLE terra_ruins ("
            "id TEXT PRIMARY KEY, world_id INTEGER NOT NULL REFERENCES world(id), "
            "x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63), "
            "y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63), "
            "created BIGINT NOT NULL, expires BIGINT NOT NULL CHECK(expires>created))"
        )
        db.execute("CREATE INDEX terra_ruins_sector ON terra_ruins(world_id,x,y,expires)")
        db.execute("INSERT INTO schema_versions(version) VALUES (61)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=62").fetchone():
        db.execute(
            "CREATE TABLE terra_inactivity ("
            "user_id TEXT PRIMARY KEY REFERENCES users(id), last_seen BIGINT NOT NULL, "
            "warned_at BIGINT, dormant_at BIGINT, review_at BIGINT)"
        )
        db.execute(
            "CREATE INDEX terra_inactivity_due ON terra_inactivity(last_seen) WHERE dormant_at IS NULL"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (62)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=63").fetchone():
        db.execute(
            "CREATE TABLE game_event_outbox ("
            "id TEXT PRIMARY KEY, recipient TEXT NOT NULL REFERENCES users(id), "
            "world_id INTEGER NOT NULL REFERENCES world(id), kind TEXT NOT NULL, "
            "created BIGINT NOT NULL)"
        )
        db.execute("CREATE INDEX game_event_outbox_order ON game_event_outbox(created,id)")
        sequence_type = (
            "BIGSERIAL PRIMARY KEY" if db.postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        db.execute(
            f"CREATE TABLE game_events (sequence {sequence_type}, "
            "id TEXT NOT NULL UNIQUE, recipient TEXT NOT NULL REFERENCES users(id), "
            "world_id INTEGER NOT NULL REFERENCES world(id), kind TEXT NOT NULL, "
            "created BIGINT NOT NULL)"
        )
        db.execute("CREATE INDEX game_events_recipient ON game_events(recipient,world_id,sequence)")
        db.execute("INSERT INTO schema_versions(version) VALUES (63)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=64").fetchone():
        db.execute("ALTER TABLE commands ADD COLUMN origin_world_id INTEGER")
        db.execute("ALTER TABLE commands ADD COLUMN origin_colony_id TEXT")
        db.execute("ALTER TABLE commands ADD COLUMN rule_version TEXT")
        db.execute("INSERT INTO schema_versions(version) VALUES (64)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=65").fetchone():
        db.execute(
            "CREATE INDEX orbit_economy_due ON orbit_economy(due,mission_id) WHERE due IS NOT NULL"
        )
        db.execute(
            "CREATE INDEX orbit_stations_due ON orbit_stations(ready_at,colony_id) "
            "WHERE ready_at IS NOT NULL"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (65)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=66").fetchone():
        db.execute(
            "CREATE TABLE scheduler_status ("
            "id INTEGER PRIMARY KEY CHECK(id=1), sampled_at BIGINT NOT NULL, "
            "lag_seconds BIGINT NOT NULL CHECK(lag_seconds>=0))"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (66)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=67").fetchone():
        sequence = "BIGSERIAL PRIMARY KEY" if db.postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        db.execute(
            f"CREATE TABLE orbit_resource_ledger (sequence {sequence}, "
            "colony_id TEXT NOT NULL REFERENCES orbit_economy(mission_id), "
            "ore BIGINT NOT NULL, ether BIGINT NOT NULL, ore_reserve BIGINT NOT NULL, "
            "ether_reserve BIGINT NOT NULL, recorded_at BIGINT NOT NULL)"
        )
        db.execute(
            "CREATE INDEX orbit_resource_ledger_colony ON orbit_resource_ledger(colony_id,sequence)"
        )
        if db.postgres:
            db.execute(
                "CREATE FUNCTION orbit_log_balances() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN INSERT INTO orbit_resource_ledger(colony_id,ore,ether,ore_reserve,ether_reserve,recorded_at) "
                "VALUES (NEW.mission_id,NEW.ore,NEW.ether,NEW.ore_reserve,NEW.ether_reserve,"
                "CAST(EXTRACT(EPOCH FROM statement_timestamp()) AS BIGINT)); RETURN NEW; END; $$"
            )
            db.execute(
                "CREATE TRIGGER orbit_balance_insert AFTER INSERT ON orbit_economy "
                "FOR EACH ROW EXECUTE FUNCTION orbit_log_balances()"
            )
            db.execute(
                "CREATE TRIGGER orbit_balance_update AFTER UPDATE ON orbit_economy FOR EACH ROW "
                "WHEN ((OLD.ore,OLD.ether,OLD.ore_reserve,OLD.ether_reserve) IS DISTINCT FROM "
                "(NEW.ore,NEW.ether,NEW.ore_reserve,NEW.ether_reserve)) "
                "EXECUTE FUNCTION orbit_log_balances()"
            )
            db.execute(
                "CREATE TRIGGER orbit_ledger_immutable BEFORE UPDATE OR DELETE ON orbit_resource_ledger "
                "FOR EACH ROW EXECUTE FUNCTION prevent_season_rules_mutation()"
            )
        else:
            for operation in ("INSERT", "UPDATE"):
                condition = (
                    "WHEN OLD.ore<>NEW.ore OR OLD.ether<>NEW.ether OR "
                    "OLD.ore_reserve<>NEW.ore_reserve OR OLD.ether_reserve<>NEW.ether_reserve "
                    if operation == "UPDATE"
                    else ""
                )
                db.execute(
                    f"CREATE TRIGGER orbit_balance_{operation.lower()} AFTER {operation} ON orbit_economy "
                    f"{condition} BEGIN INSERT INTO orbit_resource_ledger"
                    "(colony_id,ore,ether,ore_reserve,ether_reserve,recorded_at) "
                    "VALUES (NEW.mission_id,NEW.ore,NEW.ether,NEW.ore_reserve,NEW.ether_reserve,"
                    "CAST(strftime('%s','now') AS INTEGER)); END"
                )
            for operation in ("UPDATE", "DELETE"):
                db.execute(
                    f"CREATE TRIGGER orbit_ledger_no_{operation.lower()} BEFORE {operation} "
                    "ON orbit_resource_ledger BEGIN SELECT RAISE(ABORT,'immutable ledger'); END"
                )
        timestamp = (
            "CAST(EXTRACT(EPOCH FROM statement_timestamp()) AS BIGINT)"
            if db.postgres
            else "CAST(strftime('%s','now') AS INTEGER)"
        )
        db.execute(
            "INSERT INTO orbit_resource_ledger(colony_id,ore,ether,ore_reserve,ether_reserve,recorded_at) "
            f"SELECT mission_id,ore,ether,ore_reserve,ether_reserve,{timestamp} FROM orbit_economy"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (67)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=68").fetchone():
        guards = {
            "terra_orbit_cargo": (
                "SELECT 1 FROM colonies t JOIN orbit_planet_claims o "
                "ON o.world_id=t.world_id AND o.owner=t.user_id "
                "WHERE t.colony_id=NEW.terra_colony AND o.mission_id=NEW.orbit_colony "
                "AND o.rule_version=NEW.rule_version"
            ),
            "orbit_transports": (
                "SELECT 1 FROM orbit_planet_claims o JOIN orbit_planet_claims t "
                "ON t.world_id=o.world_id AND t.rule_version=o.rule_version "
                "WHERE o.mission_id=NEW.origin AND t.mission_id=NEW.target "
                "AND o.rule_version=NEW.rule_version AND ("
                "(NEW.salvage_report IS NULL AND o.owner=t.owner) OR "
                "EXISTS(SELECT 1 FROM orbit_battle_reports b "
                "JOIN orbit_planet_claims a ON a.mission_id=b.origin "
                "WHERE b.id=NEW.salvage_report AND b.target=t.mission_id "
                "AND (a.owner=o.owner OR t.owner=o.owner)))"
            ),
            "orbit_attacks": (
                "SELECT 1 FROM orbit_planet_claims o JOIN orbit_planet_claims t "
                "ON t.world_id=o.world_id AND t.rule_version=o.rule_version "
                "WHERE o.mission_id=NEW.origin AND t.mission_id=NEW.target "
                "AND o.owner<>t.owner AND o.rule_version=NEW.rule_version "
                "AND (NEW.moon_target IS NULL OR EXISTS(SELECT 1 FROM orbit_moons m "
                "WHERE m.battle_id=NEW.moon_target AND m.colony_id=t.mission_id))"
            ),
            "orbit_attack_wings": (
                "SELECT 1 FROM orbit_attacks a JOIN orbit_planet_claims o ON o.mission_id=a.origin "
                "JOIN orbit_planet_claims w ON w.world_id=o.world_id AND w.rule_version=o.rule_version "
                "WHERE a.id=NEW.attack_id AND a.alliance_id IS NOT NULL "
                "AND w.mission_id=NEW.colony_id AND w.owner<>o.owner"
            ),
        }
        for table, valid in guards.items():
            message = "invalid mission world, owner or rule reference"
            if db.postgres:
                db.execute(
                    f"CREATE FUNCTION validate_{table}_scope() RETURNS trigger LANGUAGE plpgsql AS $$ "
                    f"BEGIN IF NOT EXISTS({valid}) THEN RAISE EXCEPTION '{message}'; "
                    "END IF; RETURN NEW; END; $$"
                )
                db.execute(
                    f"CREATE TRIGGER {table}_scope BEFORE INSERT OR UPDATE ON {table} "
                    f"FOR EACH ROW EXECUTE FUNCTION validate_{table}_scope()"
                )
            else:
                for operation in ("INSERT", "UPDATE"):
                    db.execute(
                        f"CREATE TRIGGER {table}_scope_{operation.lower()} BEFORE {operation} ON {table} "
                        f"WHEN NOT EXISTS({valid}) BEGIN SELECT RAISE(ABORT,'{message}'); END"
                    )
        db.execute("INSERT INTO schema_versions(version) VALUES (68)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=69").fetchone():
        db.execute(
            "CREATE TABLE backup_status (id INTEGER PRIMARY KEY CHECK(id=1), completed_at BIGINT NOT NULL)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (69)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=70").fetchone():
        db.execute(
            "ALTER TABLE world_settings ADD COLUMN terra_prestige_ruleset TEXT REFERENCES rule_catalogs(version)"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (70)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=71").fetchone():
        db.execute(
            "CREATE TABLE terra_trade_routes ("
            "id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE CASCADE, "
            "target TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE CASCADE, "
            "army TEXT NOT NULL, cargo TEXT NOT NULL, interval_seconds INTEGER NOT NULL, "
            "due BIGINT NOT NULL, paused BOOLEAN NOT NULL DEFAULT FALSE, reason TEXT NOT NULL DEFAULT '', "
            "CHECK(source<>target), UNIQUE(source,target))"
        )
        db.execute(
            "CREATE INDEX terra_trade_routes_due ON terra_trade_routes(due,id) WHERE paused=FALSE"
        )
        db.execute("INSERT INTO schema_versions(version) VALUES (71)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=72").fetchone():
        db.execute(
            "CREATE TABLE terra_market_convoys ("
            "offer_id TEXT PRIMARY KEY REFERENCES offers(id), "
            "target TEXT NOT NULL REFERENCES colonies(colony_id), "
            "resource INTEGER NOT NULL CHECK(resource BETWEEN 0 AND 2), "
            "amount INTEGER NOT NULL CHECK(amount>0), due BIGINT NOT NULL)"
        )
        db.execute("CREATE INDEX terra_market_convoys_due ON terra_market_convoys(due,offer_id)")
        db.execute("CREATE INDEX terra_market_convoys_target ON terra_market_convoys(target)")
        db.execute("INSERT INTO schema_versions(version) VALUES (72)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=73").fetchone():
        terra_alliance_attacks_migration = (
            "073_terra_alliance_attacks_postgres.sql"
            if db.postgres
            else "073_terra_alliance_attacks_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_alliance_attacks_migration).read_text())
        db.execute("INSERT INTO schema_versions(version) VALUES (73)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=74").fetchone():
        terra_allied_garrisons_migration = (
            "074_terra_allied_garrisons_postgres.sql"
            if db.postgres
            else "074_terra_allied_garrisons_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_allied_garrisons_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=75").fetchone():
        terra_combat_migration = (
            "075_terra_combat_postgres.sql" if db.postgres else "075_terra_combat_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_combat_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=76").fetchone():
        terra_retreat_migration = (
            "076_terra_retreat_threshold_postgres.sql"
            if db.postgres
            else "076_terra_retreat_threshold_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_retreat_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=77").fetchone():
        terra_intelligence_migration = (
            "077_terra_intelligence_postgres.sql"
            if db.postgres
            else "077_terra_intelligence_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_intelligence_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=78").fetchone():
        terra_combat_v2_migration = (
            "078_terra_combat_v2_postgres.sql" if db.postgres else "078_terra_combat_v2_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_combat_v2_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=79").fetchone():
        terra_combat_v3_migration = (
            "079_terra_combat_v3_postgres.sql" if db.postgres else "079_terra_combat_v3_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_combat_v3_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=80").fetchone():
        terra_combat_v4_migration = (
            "080_terra_combat_v4_postgres.sql" if db.postgres else "080_terra_combat_v4_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_combat_v4_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=81").fetchone():
        terra_unit_wrecks_migration = (
            "081_terra_unit_wrecks_postgres.sql"
            if db.postgres
            else "081_terra_unit_wrecks_sqlite.sql"
        )
        db.executescript((root / "migrations" / terra_unit_wrecks_migration).read_text())
    # Run after the legacy SQLite world_settings table-rebuild migrations. Creating this
    # FK table earlier would let SQLite rewrite its reference to a temporary v77 table.
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=94").fetchone():
        commander_hero_migration = (
            "094_commander_hero_postgres.sql" if db.postgres else "094_commander_hero_sqlite.sql"
        )
        db.executescript((root / "migrations" / commander_hero_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=95").fetchone():
        commander_respec_migration = (
            "095_commander_respec_postgres.sql"
            if db.postgres
            else "095_commander_respec_sqlite.sql"
        )
        db.executescript((root / "migrations" / commander_respec_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=96").fetchone():
        cosmetic_migration = (
            "096_cosmetic_rewards_postgres.sql"
            if db.postgres
            else "096_cosmetic_rewards_sqlite.sql"
        )
        db.executescript((root / "migrations" / cosmetic_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=97").fetchone():
        web_push_migration = (
            "097_web_push_postgres.sql" if db.postgres else "097_web_push_sqlite.sql"
        )
        db.executescript((root / "migrations" / web_push_migration).read_text())
        db.execute("INSERT INTO schema_versions(version) VALUES (97)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=98").fetchone():
        season_goal_migration = (
            "098_season_goal_postgres.sql" if db.postgres else "098_season_goal_sqlite.sql"
        )
        db.executescript((root / "migrations" / season_goal_migration).read_text())
        db.execute("INSERT INTO schema_versions(version) VALUES (98)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=99").fetchone():
        season_awards_migration = (
            "099_season_awards_postgres.sql" if db.postgres else "099_season_awards_sqlite.sql"
        )
        db.executescript((root / "migrations" / season_awards_migration).read_text())
        db.execute("INSERT INTO schema_versions(version) VALUES (99)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=100").fetchone():
        live_event_migration = (
            "100_live_event_editor_postgres.sql"
            if db.postgres
            else "100_live_event_editor_sqlite.sql"
        )
        db.executescript((root / "migrations" / live_event_migration).read_text())
        from .live_events import snapshot as live_event_snapshot

        for row in db.execute("SELECT * FROM events").fetchall():
            event = dict(row)
            version, frozen, digest = live_event_snapshot(event)
            db.execute(
                "INSERT INTO live_event_rules(event_id,version,snapshot,digest,source) "
                "VALUES (?,?,?,?,?) ON CONFLICT(event_id) DO NOTHING",
                (event["id"], version, frozen, digest, "legacy_backfill"),
            )
        db.execute("INSERT INTO schema_versions(version) VALUES (100)")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=101").fetchone():
        ranking_categories_migration = (
            "101_ranking_categories_postgres.sql"
            if db.postgres
            else "101_ranking_categories_sqlite.sql"
        )
        db.executescript((root / "migrations" / ranking_categories_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=102").fetchone():
        prestige_migration = (
            "102_prestige_hall_postgres.sql" if db.postgres else "102_prestige_hall_sqlite.sql"
        )
        db.executescript((root / "migrations" / prestige_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=103").fetchone():
        scheduled_announcements_migration = (
            "103_scheduled_announcements_postgres.sql"
            if db.postgres
            else "103_scheduled_announcements_sqlite.sql"
        )
        db.executescript((root / "migrations" / scheduled_announcements_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=104").fetchone():
        rule_rollouts_migration = (
            "104_rule_rollouts_postgres.sql" if db.postgres else "104_rule_rollouts_sqlite.sql"
        )
        db.executescript((root / "migrations" / rule_rollouts_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=105").fetchone():
        report_sharing_migration = (
            "105_report_sharing_perspective_postgres.sql"
            if db.postgres
            else "105_report_sharing_perspective_sqlite.sql"
        )
        db.executescript((root / "migrations" / report_sharing_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=106").fetchone():
        ban_appeal_migration = (
            "106_account_ban_appeals_postgres.sql"
            if db.postgres
            else "106_account_ban_appeals_sqlite.sql"
        )
        db.executescript((root / "migrations" / ban_appeal_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=107").fetchone():
        npc_camps_migration = (
            "107_npc_camps_postgres.sql" if db.postgres else "107_npc_camps_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_camps_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=108").fetchone():
        npc_rollout_migration = (
            "108_npc_camp_rollout_key_postgres.sql"
            if db.postgres
            else "108_npc_camp_rollout_key_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_rollout_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=109").fetchone():
        npc_action_state_migration = (
            "109_npc_camp_action_state_postgres.sql"
            if db.postgres
            else "109_npc_camp_action_state_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_action_state_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=110").fetchone():
        npc_movement_migration = (
            "110_npc_camp_movement_postgres.sql"
            if db.postgres
            else "110_npc_camp_movement_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_movement_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=111").fetchone():
        npc_planning_migration = (
            "111_npc_attack_plans_postgres.sql"
            if db.postgres
            else "111_npc_attack_plans_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_planning_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=112").fetchone():
        planner_indexes_migration = (
            "112_npc_attack_planner_indexes_postgres.sql"
            if db.postgres
            else "112_npc_attack_planner_indexes_sqlite.sql"
        )
        db.executescript((root / "migrations" / planner_indexes_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=113").fetchone():
        camp_intel_owner_migration = (
            "113_npc_camp_observed_owner_postgres.sql"
            if db.postgres
            else "113_npc_camp_observed_owner_sqlite.sql"
        )
        db.executescript((root / "migrations" / camp_intel_owner_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=114").fetchone():
        npc_attack_missions_migration = (
            "114_npc_attack_missions_postgres.sql"
            if db.postgres
            else "114_npc_attack_missions_sqlite.sql"
        )
        db.executescript((root / "migrations" / npc_attack_missions_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=115").fetchone():
        terra_combat_v5_migration = (
            "115_terra_combat_v5_postgres.sql" if db.postgres else "115_terra_combat_v5_sqlite.sql"
        )
        if not db.postgres:
            db.raw.commit()
            db.raw.execute("PRAGMA foreign_keys=OFF")
        try:
            db.executescript((root / "migrations" / terra_combat_v5_migration).read_text())
        finally:
            if not db.postgres:
                db.raw.execute("PRAGMA foreign_keys=ON")
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=116").fetchone():
        ruin_exploration_migration = (
            "116_terra_ruin_exploration_postgres.sql"
            if db.postgres
            else "116_terra_ruin_exploration_sqlite.sql"
        )
        db.executescript((root / "migrations" / ruin_exploration_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=117").fetchone():
        ruin_rollout_key_migration = (
            "117_ruin_rule_rollout_key_postgres.sql"
            if db.postgres
            else "117_ruin_rule_rollout_key_sqlite.sql"
        )
        db.executescript((root / "migrations" / ruin_rollout_key_migration).read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=118").fetchone():
        db.executescript((root / "migrations" / "118_terra_boss_raids.sql").read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=119").fetchone():
        db.executescript((root / "migrations" / "119_npc_invasions.sql").read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=120").fetchone():
        db.executescript((root / "migrations" / "120_recurring_quests.sql").read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=121").fetchone():
        db.executescript((root / "migrations" / "121_npc_convoys.sql").read_text())

    if not db.execute("SELECT 1 FROM schema_versions WHERE version=122").fetchone():
        db.executescript((root / "migrations" / "122_account_language.sql").read_text())
    if not db.execute("SELECT 1 FROM schema_versions WHERE version=123").fetchone():
        db.executescript((root / "migrations" / "123_registration_acceptance.sql").read_text())
