"""Terrain is persisted by the server and affects travel, production and defense."""

import json
import math
import os
import time
from urllib.parse import quote

import pytest

from fur_empire.fog import visible_sectors
from fur_empire.game import Game, RuleError, identity
from fur_empire.registry import load_rules
from fur_empire.terrain import (
    DEFENSE_PERCENT,
    GENERATION_WEIGHT,
    MOVEMENT_COST,
    PRODUCTION_PERCENT,
    TERRAIN_LABELS,
    defense_with_terrain,
    travel_seconds,
)


@pytest.fixture(params=["sqlite", "postgres"])
def terrain_universe(request, tmp_path, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    pg = None
    schema = "fur_terrain_test_" + identity().replace("-", "")
    if request.param == "postgres":
        base = os.getenv("FUR_TEST_POSTGRES")
        if not base:
            pytest.skip("FUR_TEST_POSTGRES not configured")
        import psycopg
        from psycopg import sql

        pg = psycopg.connect(base, autocommit=True)
        pg.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        target = (
            base + ("?" if "?" not in base else "&") + "options=" + quote("-csearch_path=" + schema)
        )
    else:
        target = str(tmp_path / "terrain.sqlite3")
    game = Game(target)
    users = []
    with game.transaction() as db:
        for name in ("TerrainAlpha", "TerrainBravo"):
            user = identity()
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, name, "unused"))
            game.create(db, user, name)
            db.execute("UPDATE profiles SET joined=? WHERE user_id=?", (clock[0] - 7200, user))
            users.append(user)
    yield game, users, clock
    if pg:
        from psycopg import sql

        pg.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        pg.close()


def test_world_terrain_seed_is_complete_stable_and_preserves_existing_world(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        start = game.read(db, users[0])
        before = db.execute("SELECT state FROM world WHERE id=1").fetchone()[0]
        count = db.execute("SELECT count(*) FROM world_terrain WHERE world_id=1").fetchone()[0]
        assert count == 4096
        assert start["terrain"] != "water"
        view = game.view(db, users[0])
        assert len(view["terrain_map"]) < 4096
        assert view["sector_intel"][f"{start['x']}:{start['y']}"]["status"] == "current"
        assert view["sector_intel"]["63:63"]["status"] == "unknown"
        assert "63:63" not in view["terrain_map"]
        assert all(not region["surveyed"] for region in view["regions"])
        assert all(region["outpost_count"] is None for region in view["regions"])
        assert db.execute(
            "SELECT count(*) FROM map_sector_intel WHERE observer_id=? AND world_id=1",
            (users[0],),
        ).fetchone()[0] == len(view["terrain_map"])
        other_view = game.view(db, users[1])
        unknown_key = next(
            key
            for key, status in other_view["sector_intel"].items()
            if status["status"] == "unknown" and view["sector_intel"][key]["status"] == "unknown"
        )
        stale_x, stale_y = (int(part) for part in unknown_key.split(":"))
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, stale_x, stale_y, 1),
        )
        stale_view = game.view(db, users[0])
        assert stale_view["sector_intel"][unknown_key] == {"status": "stale", "observed_at": 1}
        assert unknown_key in stale_view["terrain_map"]
        other_view = game.view(db, users[1])
        assert other_view["sector_intel"][unknown_key]["status"] == "unknown"
        db.execute(
            "UPDATE world_terrain SET terrain='mountain' WHERE world_id=1 AND x=? AND y=?",
            (start["x"], start["y"]),
        )
    Game(game.path)
    with game.transaction() as db:
        assert db.execute("SELECT state FROM world WHERE id=1").fetchone()[0] == before
        assert (
            db.execute(
                "SELECT terrain FROM world_terrain WHERE world_id=1 AND x=? AND y=?",
                (start["x"], start["y"]),
            ).fetchone()[0]
            == "mountain"
        )
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124


def test_terrain_modifiers_are_loaded_from_validated_fur2_catalog(terrain_universe):
    game, users, _clock = terrain_universe
    catalog = load_rules()["terrain"]

    assert tuple(catalog) == ("plain", "forest", "water", "mountain", "pass")
    assert sum(GENERATION_WEIGHT.values()) == 100
    assert {kind: rule["name"] for kind, rule in catalog.items()} == TERRAIN_LABELS
    assert {
        kind: float("inf") if rule["movement_cost"] is None else rule["movement_cost"]
        for kind, rule in catalog.items()
    } == MOVEMENT_COST
    assert {
        kind: tuple(rule["production_percent"]) for kind, rule in catalog.items()
    } == PRODUCTION_PERCENT
    assert {kind: rule["defense_percent"] for kind, rule in catalog.items()} == DEFENSE_PERCENT
    assert catalog["water"]["movement_cost"] is None
    with game.transaction() as db:
        exposed = game.view(db, users[0])["catalog"]["terrain"]
    for kind, rule in catalog.items():
        assert exposed[kind] == {
            "name": rule["name"],
            "movement_cost": rule["movement_cost"],
            "production_percent": rule["production_percent"],
            "defense_percent": rule["defense_percent"],
        }


def test_sector_fog_observations_are_isolated_by_world_when_switching(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        world_id = game.create_world(db, "Fog Scope", 981_273, 16, True)
        game.join_world(db, users[0], "TerrainAlpha", world_id)
        visible_genesis = visible_sectors(db, users[0], 1)
        visible_new_world = visible_sectors(db, users[0], world_id)
        x, y = next(
            (x, y)
            for y in range(64)
            for x in range(64)
            if (x, y) not in visible_genesis and (x, y) not in visible_new_world
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, x, y, 1),
        )

        new_world_view = game.view(db, users[0])
        key = f"{x}:{y}"
        assert new_world_view["sector_intel"][key] == {
            "status": "unknown",
            "observed_at": None,
        }
        assert key not in new_world_view["terrain_map"]

        game.join_world(db, users[0], "TerrainAlpha", 1)
        genesis_view = game.view(db, users[0])
        assert genesis_view["sector_intel"][key] == {"status": "stale", "observed_at": 1}
        assert key in genesis_view["terrain_map"]


def test_colonization_rejects_unknown_sector(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db, pytest.raises(RuleError, match="noch nicht aufgeklärt"):
        game.command(db, users[0], "colonize", {"x": 63, "y": 63}, "fog-colonize")
    with game.transaction() as db:
        home = game.read(db, users[0])
        post = next(
            town
            for town in game.world_outposts(db, 1)
            if math.hypot(town["x"] - home["x"], town["y"] - home["y"]) > 8
        )
        with pytest.raises(RuleError, match="noch nicht aufgeklärt"):
            game.command(
                db,
                users[0],
                "raid",
                {"key": post["id"], "army": {"ranger": 1}},
                "fog-raid",
            )


def test_colonization_rejects_isolated_land_without_a_walkable_route(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["hq"] = 3
        home["resources"] = [10000, 10000, 10000]
        game.save(db, home)
        game.view(db, users[0])
        colonies = [
            json.loads(row["state"])
            for row in db.execute("SELECT state FROM colonies WHERE world_id=1")
        ]
        posts = {(post["x"], post["y"]) for post in game.world_outposts(db, 1)}
        target = next(
            (x, y)
            for y in range(64)
            for x in range(64)
            if (x, y) not in posts
            and all(math.hypot(x - colony["x"], y - colony["y"]) >= 6 for colony in colonies)
            and 6 <= math.hypot(x - home["x"], y - home["y"]) < 8
        )
        db.execute("UPDATE world_terrain SET terrain='water' WHERE world_id=1")
        db.execute(
            "UPDATE world_terrain SET terrain='plain' WHERE world_id=1 AND x=? AND y=?",
            (home["x"], home["y"]),
        )
        db.execute(
            "UPDATE world_terrain SET terrain='plain' WHERE world_id=1 AND x=? AND y=?",
            target,
        )
        before_resources = game.read(db, users[0])["resources"]
        before_count = db.execute(
            "SELECT count(*) FROM colonies WHERE user_id=?", (users[0],)
        ).fetchone()[0]
        with pytest.raises(RuleError, match="keiner deiner Kolonien erreichbar"):
            game.command(
                db, users[0], "colonize", {"x": target[0], "y": target[1]}, "isolated-colony"
            )
        assert game.read(db, users[0])["resources"] == before_resources
        assert (
            db.execute("SELECT count(*) FROM colonies WHERE user_id=?", (users[0],)).fetchone()[0]
            == before_count
        )


def test_owned_outpost_expands_sight_by_two_sectors(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        own_colonies = [
            json.loads(row["state"])
            for row in db.execute("SELECT state FROM colonies WHERE user_id=?", (users[0],))
        ]
        post = next(
            town
            for town in game.world_outposts(db, 1)
            if town["x"] <= 60
            and town["y"] <= 60
            and min(math.hypot(town["x"] - c["x"], town["y"] - c["y"]) for c in own_colonies) > 12
        )
        initial = game.view(db, users[0])
        outer_key = f"{post['x'] + 3}:{post['y']}"
        inner_key = f"{post['x'] + 2}:{post['y']}"
        assert initial["sector_intel"][inner_key]["status"] == "unknown"
        assert initial["sector_intel"][outer_key]["status"] == "unknown"
        post["owner"] = users[0]
        towns = game.world_outposts(db, 1)
        target = next(town for town in towns if town["id"] == post["id"])
        target["owner"] = users[0]
        game.save_world_outposts(db, 1, towns)

        expanded = game.view(db, users[0])
        assert expanded["sector_intel"][inner_key]["status"] == "current"
        assert expanded["sector_intel"][outer_key]["status"] == "unknown"
        assert post["id"] in {town["id"] for town in expanded["world"]}


def test_sector_intel_migration_from_schema_11_preserves_existing_world(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        game.view(db, users[0])
        assert (
            db.execute(
                "SELECT count(*) FROM map_sector_intel WHERE observer_id=?", (users[0],)
            ).fetchone()[0]
            > 0
        )
        db.execute("DROP TABLE map_sector_intel")
        db.execute("DELETE FROM schema_versions WHERE version=12")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM colonies").fetchone()[0] == 2
        assert (
            db.execute("SELECT count(*) FROM world_outposts WHERE world_id=1").fetchone()[0] == 104
        )
        assert (
            db.execute("SELECT count(*) FROM world_terrain WHERE world_id=1").fetchone()[0] == 4096
        )
        assert db.execute("SELECT count(*) FROM map_sector_intel").fetchone()[0] == 0


def test_weighted_pathfinding_avoids_water_and_uses_terrain_costs(terrain_universe):
    game, _users, _clock = terrain_universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_terrain SET terrain='water' WHERE world_id=1 "
            "AND x BETWEEN 9 AND 21 AND y BETWEEN 8 AND 14"
        )
        db.execute(
            "UPDATE world_terrain SET terrain='plain' WHERE world_id=1 "
            "AND x BETWEEN 10 AND 20 AND y IN (10,12)"
        )
        db.execute(
            "UPDATE world_terrain SET terrain='plain' WHERE world_id=1 " "AND x IN (10,20) AND y=11"
        )
        start, finish = (10, 10), (20, 10)
        db.execute("UPDATE world_terrain SET terrain='forest' WHERE world_id=1 AND x=15 AND y=10")
        assert travel_seconds(db, start, finish) == 21

        db.execute("UPDATE world_terrain SET terrain='water' WHERE world_id=1 AND x=15 AND y=10")
        assert travel_seconds(db, start, finish) == 28

        db.execute(
            "UPDATE world_terrain SET terrain='water' WHERE world_id=1 AND x=15 "
            "AND y BETWEEN 9 AND 13"
        )
        with pytest.raises(ValueError, match="keinen begehbaren Weg"):
            travel_seconds(db, start, finish)


def test_terrain_changes_fixed_point_production_and_defense(terrain_universe):
    game, users, clock = terrain_universe
    with game.transaction() as db:
        state = game.read(db, users[0])
        state["resources"] = [0, 0, 0]
        state["carry"] = [0, 0, 0]
        state["last"] = clock[0]
        state["terrain"] = "forest"
        game.produce(state, clock[0] + 100)
        assert state["resources"] == [480, 360, 360]

    assert defense_with_terrain(400, "plain") == 400
    assert defense_with_terrain(400, "forest") == 440
    assert defense_with_terrain(400, "mountain") == 500
    assert defense_with_terrain(400, "pass") == 360


def test_state_explains_terrain_production_bonus_storage_and_vacation_pause(terrain_universe):
    game, users, clock = terrain_universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        db.execute(
            "UPDATE world_terrain SET terrain='forest' WHERE world_id=1 AND x=? AND y=?",
            (colony["x"], colony["y"]),
        )
        details = game.view(db, users[0])["production_details"]
        wood = details[0]
        assert wood == {
            "resource": "wood",
            "base_per_second": 4,
            "bonus_percent": 0,
            "terrain_percent": 120,
            "terrain": "Wald",
            "per_second_hundredths": 480,
            "per_second_ten_thousandths": 48000,
            "storage": colony["resources"][0],
            "storage_cap": 4000,
            "seconds_to_cap": (max(0, 4000 - colony["resources"][0]) * 100 + 479) // 480,
            "paused": False,
        }
        colony["vacation_until"] = clock[0] + 600
        game.save(db, colony)
        paused_wood = game.view(db, users[0])["production_details"][0]
        assert paused_wood["paused"] is True
        assert paused_wood["per_second_hundredths"] == 0
        assert paused_wood["seconds_to_cap"] is None


def test_colonization_rejects_water_and_preserves_valid_coordinates(terrain_universe):
    game, users, _clock = terrain_universe
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["hq"] = 3
        home["resources"] = [10000, 10000, 10000]
        game.save(db, home)
        occupied = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=1")
        }
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        occupied.update((town["x"], town["y"]) for town in towns)
        water = next(
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM world_terrain WHERE world_id=1 AND terrain='water' ORDER BY y,x"
            )
            if (int(row["x"]), int(row["y"])) not in occupied
            and all(math.hypot(int(row["x"]) - x, int(row["y"]) - y) >= 6 for x, y in occupied)
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, water[0], water[1], _clock[0]),
        )
        before = db.execute("SELECT x,y FROM colonies WHERE colony_id=?", (users[0],)).fetchone()
    with pytest.raises(RuleError, match="Wasserfelder"), game.transaction() as db:
        game.command(db, users[0], "colonize", {"x": water[0], "y": water[1]}, "water-colony")
    with game.transaction() as db:
        after = db.execute("SELECT x,y FROM colonies WHERE colony_id=?", (users[0],)).fetchone()
        assert (after["x"], after["y"]) == (before["x"], before["y"])
