"""Portable world topology snapshots and restore into a new SQLite database."""

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .database import Connection
from .game import REGISTRY, RULES_DIGEST, RULES_SNAPSHOT, Game, identity

MAX_BYTES = 2 * 1024 * 1024


def _clone_sqlite(source: sqlite3.Connection, database: Path) -> None:
    with database.open("xb"):
        pass
    with closing(sqlite3.connect(database)) as target:
        source.backup(target)


def _sqlite_health(db: sqlite3.Connection) -> None:
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("Die SQLite-Sicherung ist beschädigt.")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("Die SQLite-Sicherung enthält ungültige Fremdschlüssel.")


def restore_sqlite_world_backup(snapshot: Path, database: Path, world_id: int) -> None:
    """Validate and clone a full SQLite backup, retaining shared world dependencies."""
    source_uri = snapshot.resolve(strict=True).as_uri() + "?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as source:
        source.execute("BEGIN")
        _sqlite_health(source)
        rules = source.execute(
            "SELECT c.version,c.digest,c.snapshot FROM world_rulesets w "
            "JOIN rule_catalogs c ON c.version=w.version "
            "JOIN world_settings s ON s.world_id=w.world_id WHERE w.world_id=?",
            (world_id,),
        ).fetchone()
        if rules != (REGISTRY["version"], RULES_DIGEST, RULES_SNAPSHOT):
            raise ValueError("Die Welt oder ihr Regelstand passt nicht zu diesem Build.")
        _clone_sqlite(source, database)


def _migration_inventory(db: sqlite3.Connection) -> dict[str, object]:
    columns = {row[1] for row in db.execute("PRAGMA table_info(colonies)")}
    colony_key = "colony_id" if "colony_id" in columns else "user_id"
    colonies = {}
    for key, owner, raw in db.execute(f"SELECT {colony_key},user_id,state FROM colonies"):
        state = json.loads(raw)
        jobs = sorted(
            json.dumps([job.get("id"), job.get("kind"), job.get("due")])
            for job in state.get("jobs", [])
        )
        colonies[key] = (owner, state["x"], state["y"], state["resources"], jobs)
    return {
        "users": sorted(row[0] for row in db.execute("SELECT id FROM users")),
        "worlds": sorted(row[0] for row in db.execute("SELECT id FROM world")),
        "colonies": colonies,
    }


def rehearse_sqlite_migration(snapshot: Path, database: Path) -> dict[str, int]:
    """Run production migrations on a fresh copy without advancing the game clock."""
    source_uri = snapshot.resolve(strict=True).as_uri() + "?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as source:
        source.execute("BEGIN")
        _sqlite_health(source)
        before = _migration_inventory(source)
        has_versions = source.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_versions'"
        ).fetchone()
        old_version = (
            source.execute("SELECT COALESCE(MAX(version),0) FROM schema_versions").fetchone()[0]
            if has_versions
            else 0
        )
        _clone_sqlite(source, database)
    Game(database)
    with closing(sqlite3.connect(database)) as target:
        _sqlite_health(target)
        after = _migration_inventory(target)
        if before != after:
            changed = ", ".join(key for key in before if before[key] != after[key])
            raise ValueError(f"Migration verändert geschützte Bestandsdaten: {changed}.")
        new_version = target.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0]
    return {"schema_before": old_version, "schema_after": new_version}


class Tile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    x: int = Field(ge=0, le=63)
    y: int = Field(ge=0, le=63)


class Terrain(Tile):
    terrain: Literal["plain", "forest", "water", "mountain", "pass"]


class SectorRule(Tile):
    kind: Literal["protected", "spawn_reserved"]


class Outpost(Tile):
    name: str = Field(min_length=1, max_length=100)
    tier: int = Field(ge=1, le=8)


class Blueprint(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    format: Literal["fur-world-blueprint-v1"]
    source_world: int = Field(ge=1)
    name: str = Field(min_length=3, max_length=48)
    seed: int = Field(ge=0, le=2**63 - 1)
    outpost_count: int = Field(ge=8, le=300)
    rule_version: str
    rule_digest: str
    rules: str
    terrain: list[Terrain] = Field(min_length=4096, max_length=4096)
    outposts: list[Outpost] = Field(max_length=300)
    sector_rules: list[SectorRule] = Field(max_length=4096)


def _canonical(data: dict[str, object]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def export_world(database: str, world_id: int, output: Path) -> None:
    if not database.startswith(("postgresql://", "postgres://")) and not Path(database).is_file():
        raise ValueError("Die SQLite-Quelldatenbank fehlt.")
    with Connection(database) as db:
        db.execute("BEGIN IMMEDIATE")
        world = db.execute(
            "SELECT s.name,s.seed,s.outpost_count,c.version,c.digest,c.snapshot "
            "FROM world_settings s JOIN world_rulesets w ON w.world_id=s.world_id "
            "JOIN rule_catalogs c ON c.version=w.version WHERE s.world_id=?",
            (world_id,),
        ).fetchone()
        if not world:
            raise ValueError("Welt oder Regelkatalog fehlt.")
        posts = [
            json.loads(row["state"])
            for row in db.execute(
                "SELECT state FROM world_outposts WHERE world_id=? ORDER BY sort_order,target_id",
                (world_id,),
            )
        ]
        blueprint = Blueprint.model_validate(
            {
                "format": "fur-world-blueprint-v1",
                "source_world": world_id,
                "name": world["name"],
                "seed": world["seed"],
                "outpost_count": world["outpost_count"],
                "rule_version": world["version"],
                "rule_digest": world["digest"],
                "rules": world["snapshot"],
                "terrain": [
                    dict(row)
                    for row in db.execute(
                        "SELECT x,y,terrain FROM world_terrain WHERE world_id=? ORDER BY x,y",
                        (world_id,),
                    )
                ],
                "outposts": [
                    {key: post[key] for key in ("x", "y", "name", "tier")} for post in posts
                ],
                "sector_rules": [
                    dict(row)
                    for row in db.execute(
                        "SELECT x,y,kind FROM terra_sector_rules WHERE world_id=? ORDER BY x,y",
                        (world_id,),
                    )
                ],
            }
        ).model_dump()
    digest = hashlib.sha256(_canonical(blueprint)).hexdigest()
    with output.open("xb") as stream:
        stream.write(_canonical({"sha256": digest, "blueprint": blueprint}) + b"\n")


def restore_world(snapshot: Path, database: Path, name: str) -> int:
    with snapshot.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Der Welt-Snapshot ist zu groß.")
    envelope = json.loads(data)
    if not isinstance(envelope, dict) or set(envelope) != {"sha256", "blueprint"}:
        raise ValueError("Ungültiger Welt-Snapshot.")
    blueprint = Blueprint.model_validate(envelope["blueprint"])
    if envelope["sha256"] != hashlib.sha256(_canonical(blueprint.model_dump())).hexdigest():
        raise ValueError("Der Welt-Snapshot hat eine falsche Prüfsumme.")
    if (blueprint.rule_version, blueprint.rule_digest, blueprint.rules) != (
        REGISTRY["version"],
        RULES_DIGEST,
        RULES_SNAPSHOT,
    ):
        raise ValueError("Der Regelkatalog des Welt-Snapshots ist in diesem Build nicht verfügbar.")
    terrain = {(tile.x, tile.y): tile.terrain for tile in blueprint.terrain}
    if len(terrain) != 4096:
        raise ValueError("Der Welt-Snapshot enthält doppelte Geländekoordinaten.")
    for entries in (blueprint.outposts, blueprint.sector_rules):
        points = {(tile.x, tile.y) for tile in entries}
        if len(points) != len(entries) or any(terrain[point] == "water" for point in points):
            raise ValueError("Der Welt-Snapshot enthält doppelte Sektoren oder Einträge im Wasser.")
    with database.open("xb"):
        pass
    game = Game(database)
    with game.transaction() as db:
        world_id = game.create_world(
            db, name, blueprint.seed, blueprint.outpost_count, False, "sandbox"
        )
        for (x, y), tile in terrain.items():
            db.execute(
                "UPDATE world_terrain SET terrain=? WHERE world_id=? AND x=? AND y=?",
                (tile, world_id, x, y),
            )
        game.save_world_outposts(
            db,
            world_id,
            [
                {
                    **post.model_dump(),
                    "id": identity(),
                    "owner": None,
                    "stock": [400 * post.tier] * 3,
                    "cleared": False,
                }
                for post in blueprint.outposts
            ],
        )
        for rule in blueprint.sector_rules:
            db.execute(
                "INSERT INTO terra_sector_rules(world_id,x,y,kind) VALUES (?,?,?,?)",
                (world_id, rule.x, rule.y, rule.kind),
            )
    return world_id
