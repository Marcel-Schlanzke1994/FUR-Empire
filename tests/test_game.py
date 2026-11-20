import hashlib
import json
import math
import random
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from fur_empire import live_events, npc_camps, ranking_categories
from fur_empire.database import Connection, migrate
from fur_empire.game import (
    BUILDINGS,
    NPC_FACTIONS,
    REGISTRY,
    RULES_DIGEST,
    TECH,
    UNITS,
    Game,
    RuleError,
    identity,
)
from fur_empire.terrain import terrain_at, travel_costs
from fur_empire.territory import (
    MAX_REGION_PRODUCTION_BONUS,
    REGION_PRODUCTION_BONUS,
    summarize_regions,
)


def test_existing_npc_movement_snapshot_reopens_and_keeps_its_original_digest(tmp_path):
    target = str(tmp_path / "original-npc-movement.sqlite3")
    version = npc_camps.MOVEMENT_RULES_VERSION
    snapshot = npc_camps.LEGACY_MOVEMENT_SNAPSHOT
    digest = npc_camps.LEGACY_MOVEMENT_DIGEST
    assert digest == "94407cd1ce05d69be62add37a2010c61ff79ab0b0d45f45e7ecc88b3034f3b5f"
    with Connection(target) as db:
        migrate(db)
        db.execute("INSERT INTO rule_catalogs VALUES (?,?,?)", (version, snapshot, digest))
    game = Game(target)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "OriginalMover", "unused"))
        game.create(db, user, "OriginalMover")
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({npc_camps.RULESET_KEY: version}),),
        )
        assert game.view(db, user)["active_world"]["npc_camps_rules_digest"] == digest
        assert dict(
            db.execute(
                "SELECT snapshot,digest FROM rule_catalogs WHERE version=?", (version,)
            ).fetchone()
        ) == {"snapshot": snapshot, "digest": digest}


def test_season_goal_schema_defaults_legacy_seasons_and_checks_new_targets(tmp_path):
    game = Game(tmp_path / "season-goal.sqlite3")
    with game.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123
        user = identity()
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "SeasonAward", "unused"))
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id) "
            "VALUES ('legacy-season','Legacy',1,2,1,'[]',1)"
        )
        assert (
            db.execute("SELECT goal_score FROM seasons WHERE id='legacy-season'").fetchone()[0]
            == 10000
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id,goal_score) "
                "VALUES ('invalid-season','Invalid',1,2,0,'[]',1,0)"
            )
        award = ("legacy-season", user, "season_champion", 12000, 3)
        db.execute(
            "INSERT INTO season_awards(season_id,user_id,award,score,created) "
            "VALUES (?,?,?,?,?) ON CONFLICT(season_id,user_id,award) DO NOTHING",
            award,
        )
        db.execute(
            "INSERT INTO season_awards(season_id,user_id,award,score,created) "
            "VALUES (?,?,?,?,?) ON CONFLICT(season_id,user_id,award) DO NOTHING",
            award,
        )
        assert db.execute("SELECT count(*) FROM season_awards").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError, match="season awards are immutable"):
            db.execute("UPDATE season_awards SET score=0 WHERE season_id='legacy-season'")
        with pytest.raises(sqlite3.IntegrityError, match="season awards are immutable"):
            db.execute("DELETE FROM season_awards WHERE season_id='legacy-season'")


def test_hall_of_fame_is_world_scoped_and_exposes_only_historical_records(world):
    game, user = world
    with game.transaction() as db:
        other_world = game.create_world(db, "Second Hall", 91234, 8)
        hall = game.systems.hall_of_fame(db, {"id": user, "world_id": 1})
        assert hall == {"seasons": [], "alliances": [], "bosses": [], "wars": []}
        season_id = identity()
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id) "
            "VALUES (?,?,1,2,1,'[]',1)",
            (season_id, "Pilotensaison"),
        )
        db.execute(
            "INSERT INTO season_awards(season_id,user_id,award,score,created) VALUES (?,?,?,?,?)",
            (season_id, user, "season_champion", 123, 3),
        )
        other_season_id = identity()
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id) "
            "VALUES (?,?,1,2,1,'[]',?)",
            (other_season_id, "Andere Welt", other_world),
        )
        db.execute(
            "INSERT INTO season_awards(season_id,user_id,award,score,created) VALUES (?,?,?,?,?)",
            (other_season_id, user, "goal_achieved", 999, 4),
        )
        hall = game.systems.hall_of_fame(db, {"id": user, "world_id": 1})
        assert [(row["season_name"], row["score"]) for row in hall["seasons"]] == [
            ("Pilotensaison", 123)
        ]
        assert all(hall[key] == [] for key in ("alliances", "bosses", "wars"))
        assert game.systems.player_hall_of_fame(db, user)["level"] == 0


def test_prestige_milestones_are_idempotent_immutable_and_have_no_game_effect(world):
    game, user = world
    from fur_empire import prestige

    with game.transaction() as db:
        colony = game.read(db, user)
        before = (game.colony_score(colony), dict(colony["units"]), list(colony["resources"]))
        assert (
            prestige.award(
                db, user, "campaign:victory", "campaign_victory", 1, "citadel-victory", 10
            )
            == 1
        )
        assert (
            prestige.award(
                db, user, "campaign:victory", "campaign_victory", 1, "citadel-victory", 11
            )
            == 1
        )
        assert prestige.view(db, user)["badge"] == "Grenzveteran"
        after = game.read(db, user)
        assert (game.colony_score(after), dict(after["units"]), list(after["resources"])) == before
        assert (
            db.execute("SELECT COUNT(*) FROM prestige_records WHERE user_id=?", (user,)).fetchone()[
                0
            ]
            == 1
        )
        with pytest.raises(Exception, match="immutable"):
            db.execute("UPDATE prestige_records SET prestige_level=3 WHERE user_id=?", (user,))
        with pytest.raises(Exception, match="immutable"):
            db.execute("DELETE FROM prestige_records WHERE user_id=?", (user,))


@pytest.fixture
def world(tmp_path, monkeypatch):
    import time

    now = int(time.time())
    monkeypatch.setattr("fur_empire.game.time.time", lambda: now)
    game = Game(tmp_path / "test.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Tester', 'unused')", (user,))
        game.create(db, user, "Tester")
    return game, user


def test_fur2_catalog_declares_existing_unlock_requirements():
    assert all(
        item["requirements"] == {"buildings": {}, "tech": {}}
        for item in REGISTRY["buildings"].values()
    )
    assert all(
        item["requirements"] == {"buildings": {"lab": 1}, "tech": {}}
        for item in REGISTRY["tech"].values()
    )
    assert all(
        item["requirements"] == {"buildings": {"barracks": item["require"]}, "tech": {}}
        for item in REGISTRY["units"].values()
    )


def issue(world, action, payload, token=None):
    game, user = world
    with game.transaction() as db:
        return game.command(db, user, action, payload, token or identity())


def test_ranking_uses_building_research_and_capture_weights_with_stable_ties(world):
    game, user = world
    rival = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Rival', 'unused')", (rival,))
        game.create(db, rival, "Rival")
        player = game.read(db, user)
        player["buildings"]["hq"] = 2
        player["tech"]["tactics"] = 1
        player["captures"] = 1
        game.save(db, player)
        rival_state = game.read(db, rival)
        rival_state["buildings"]["hq"] = 13
        game.save(db, rival_state)

        scores = game.ranking(db)
        assert [(row["id"], row["score"]) for row in scores] == [(user, 180), (rival, 170)]

        rival_state["buildings"]["hq"] = 14
        game.save(db, rival_state)
        tied = game.ranking(db)
        expected = sorted((user, rival))
        assert [row["id"] for row in tied] == expected
        assert [row["score"] for row in tied] == [180, 180]


def test_war_score_ledger_is_opt_in_idempotent_and_auditable(world):
    game, user = world
    rival = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Rival', 'unused')", (rival,))
        game.create(db, rival, "Rival")
        mission = identity()
        game.record_war_score(
            db,
            mission_id=mission,
            world_id=1,
            user_id=user,
            category="attack",
            points=5,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=100,
        )
        game.record_war_score(
            db,
            mission_id=mission,
            world_id=1,
            user_id=user,
            category="attack",
            points=99,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=101,
        )
        game.record_war_score(
            db,
            mission_id=identity(),
            world_id=1,
            user_id=user,
            category="defense",
            points=3,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=102,
        )
        game.record_war_score(
            db,
            mission_id=identity(),
            world_id=1,
            user_id=rival,
            category="attack",
            points=100,
            rules_version="FUR-2",
            at=103,
        )
        game.record_war_score(
            db,
            mission_id=identity(),
            world_id=1,
            user_id=user,
            category="support",
            points=4,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=200,
        )
        game.record_war_score(
            db,
            mission_id=identity(),
            world_id=1,
            user_id=user,
            category="support",
            points=10,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=300,
        )
        game.record_war_score(
            db,
            mission_id=identity(),
            world_id=1,
            user_id=user,
            category="support",
            points=10,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=86600,
        )
        assert game.player_ranking_score(db, user, 1) == 50
        standing = {row["id"]: row for row in game.military_ranking_for_world(db, 1)}
        assert standing[user]["attack"] == 5
        assert standing[user]["defense"] == 3
        assert standing[user]["support"] == 14
        assert standing[user]["score"] == 22
        assert standing[rival]["score"] == 0
        with pytest.raises(Exception, match="immutable"):
            db.execute(
                "UPDATE war_score_ledger SET points=0 WHERE user_id=? AND category='attack'",
                (user,),
            )


def test_alliance_war_score_is_world_scoped_and_uses_current_members(world):
    game, user = world
    member = identity()
    outside = identity()
    alliance = identity()
    with game.transaction() as db:
        game.create_world(db, "Military Score World", 713_420, 8, True)
        for account, name in ((member, "Member"), (outside, "Outside")):
            db.execute("INSERT INTO users VALUES (?,?,?)", (account, name, "unused"))
            game.create(db, account, name)
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (alliance, "SCORE", "Score Keepers", "", user, 1),
        )
        db.execute("INSERT INTO members VALUES (?,?,?)", (user, alliance, "leader"))
        db.execute("INSERT INTO members VALUES (?,?,?)", (member, alliance, "member"))
        for account, category, points, world_id in (
            (user, "attack", 4, 1),
            (member, "support", 7, 1),
            (outside, "defense", 99, 1),
            (member, "defense", 50, 2),
        ):
            game.record_war_score(
                db,
                mission_id=identity(),
                world_id=world_id,
                user_id=account,
                category=category,
                points=points,
                rules_version="FUR-3-TERRA-COMBAT-4",
                at=2,
            )
        rows = game.alliance_military_ranking_for_world(db, 1)
        alliance_row = next(row for row in rows if row["id"] == alliance)
        assert (alliance_row["attack"], alliance_row["support"], alliance_row["score"]) == (
            4,
            7,
            11,
        )


def test_alliance_season_archive_freezes_verified_event_time_membership(world):
    game, leader = world
    member = identity()
    rival = identity()
    alliance_a = identity()
    alliance_b = identity()
    with game.transaction() as db:
        for account, name in ((member, "Verified Member"), (rival, "Rival")):
            db.execute("INSERT INTO users VALUES (?,?,?)", (account, name, "unused"))
            game.create(db, account, name)
            db.execute(
                "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
                (f"{name.lower().replace(' ', '.')}@example.test", account),
            )
        db.execute("UPDATE profiles SET verified=0 WHERE user_id=?", (member,))
        db.execute(
            "UPDATE profiles SET email='leader@example.test',verified=1 WHERE user_id=?",
            (leader,),
        )
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (alliance_a, "A", "Alpha", "", leader, 1),
        )
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (alliance_b, "B", "Beta", "", rival, 1),
        )
        db.execute("INSERT INTO members VALUES (?,?,?)", (leader, alliance_a, "leader"))
        db.execute("INSERT INTO members VALUES (?,?,?)", (member, alliance_a, "member"))
        db.execute("INSERT INTO members VALUES (?,?,?)", (rival, alliance_b, "leader"))
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id) "
            "VALUES (?,?,?,?,0,'[]',1)",
            ("season-alliance-test", "Archive", 100, 200),
        )
        game.record_war_score(
            db,
            mission_id="mission-at-end",
            world_id=1,
            user_id=leader,
            category="attack",
            points=100,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=200,
        )
        game.record_war_score(
            db,
            mission_id="mission-unverified",
            world_id=1,
            user_id=member,
            category="attack",
            points=500,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=150,
        )
        game.record_war_score(
            db,
            mission_id="mission-rival",
            world_id=1,
            user_id=rival,
            category="attack",
            points=100,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=150,
        )
        # Historical score stays with Alpha when the player later changes alliance.
        db.execute("UPDATE members SET alliance_id=? WHERE user_id=?", (alliance_b, leader))
        game.record_war_score(
            db,
            mission_id="mission-at-end",
            world_id=1,
            user_id=leader,
            category="attack",
            points=999,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=201,
        )
        game.expire(db, 201)
        rows = db.execute(
            "SELECT alliance_id,alliance_name,score,rank,eligible_accounts "
            "FROM season_alliance_standings WHERE season_id=? ORDER BY rank",
            ("season-alliance-test",),
        ).fetchall()
        assert [(row["alliance_id"], row["score"]) for row in rows] == sorted(
            [(alliance_a, 100), (alliance_b, 100)], key=lambda item: item[0]
        )
        assert [row["rank"] for row in rows] == [1, 2]
        assert all(row["eligible_accounts"] == 1 for row in rows)
        assert (
            db.execute(
                "SELECT rules_version,rules_digest FROM season_alliance_snapshots "
                "WHERE season_id=?",
                ("season-alliance-test",),
            ).fetchone()["rules_version"]
            == "FUR-3-ALLIANCE-RANKING-1"
        )
        with pytest.raises(Exception, match="immutable"):
            db.execute(
                "UPDATE season_alliance_standings SET score=0 WHERE season_id=?",
                ("season-alliance-test",),
            )


def test_ranking_categories_preserve_the_total_fur2_score_and_world_scope(world):
    game, user = world
    with game.transaction() as db:
        colony = game.read(db, user)
        colony["buildings"]["wood"] = 3
        colony["tech"]["engineering"] = 2
        colony["captures"] = 1
        game.save(db, colony)
        regions = game.world_regions(db, 1)
        controlled_region = next(region for region in regions if region["owner_id"] is None)
        regions[0] = {**controlled_region, "owner_id": user}
        game.record_war_score(
            db,
            mission_id="ranking-category-war",
            world_id=1,
            user_id=user,
            category="attack",
            points=7,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=3,
        )
        rankings = ranking_categories.live_rankings(
            db, 1, regions, game.alliance_military_ranking_for_world(db, 1)
        )
        scores = {
            category: next(row["score"] for row in entries if row["id"] == user)
            for category, entries in rankings.items()
            if category != "alliance"
        }
        assert scores["overall"] == scores["economy"] + scores["research"] + scores["pve"]
        assert scores["research"] == 40
        assert scores["pve"] == 100
        assert scores["war"] == 7
        assert scores["regions"] == 2


def test_season_ranking_categories_freeze_once_and_reject_mutation(tmp_path, monkeypatch):
    now = int(time.time())
    monkeypatch.setattr("fur_empire.game.time.time", lambda: now)
    game = Game(tmp_path / "ranking-season.sqlite3")
    users = [identity()]
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (users[0], "Season Pilot", "unused"))
        game.create(db, users[0], "Season Pilot")
    clock = [now]
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"]["wood"] = 3
        colony["tech"]["engineering"] = 2
        colony["captures"] = 1
        game.save(db, colony)
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,goal_score,world_id) "
            "VALUES (?,?,?, ?,0,?,100000,1)",
            (
                "ranking-category-season",
                "Category season",
                clock[0] - 100,
                clock[0],
                json.dumps([{"id": users[0], "name": "Season Pilot", "score": 777}]),
            ),
        )
        game.record_war_score(
            db,
            mission_id="ranking-season-war",
            world_id=1,
            user_id=users[0],
            category="attack",
            points=7,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0],
        )
        game.record_war_score(
            db,
            mission_id="ranking-after-season-war",
            world_id=1,
            user_id=users[0],
            category="attack",
            points=100,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0] + 1,
        )
        game.expire(db, clock[0])
        snapshot = db.execute(
            "SELECT rules_version,rules_digest FROM season_ranking_snapshots WHERE season_id=?",
            ("ranking-category-season",),
        ).fetchone()
        assert snapshot["rules_version"] == ranking_categories.RULES_VERSION
        assert len(snapshot["rules_digest"]) == 71
        rows = db.execute(
            "SELECT category,score FROM season_ranking_standings "
            "WHERE season_id=? AND user_id=?",
            ("ranking-category-season", users[0]),
        ).fetchall()
        scores = {row["category"]: row["score"] for row in rows}
        assert set(scores) == set(ranking_categories.CATEGORY_KEYS)
        assert scores["research"] == 40
        assert scores["pve"] == 100
        assert scores["war"] == 7
        assert scores["overall"] == 777
        with pytest.raises(Exception, match="immutable"):
            db.execute(
                "UPDATE season_ranking_standings SET score=0 "
                "WHERE season_id=? AND category='overall' AND user_id=?",
                ("ranking-category-season", users[0]),
            )
        with pytest.raises(Exception, match="immutable"):
            db.execute(
                "DELETE FROM season_ranking_snapshots WHERE season_id=?",
                ("ranking-category-season",),
            )
        game.expire(db, clock[0])
        assert db.execute(
            "SELECT COUNT(*) FROM season_ranking_standings WHERE season_id=?",
            ("ranking-category-season",),
        ).fetchone()[0] == len(ranking_categories.CATEGORY_KEYS)


def test_genesis_new_spawns_keep_a_six_sector_protection_radius(world):
    game, user = world
    with game.transaction() as db:
        home = game.read(db, user)
        before = [
            json.loads(row["state"])
            for row in db.execute("SELECT state FROM colonies WHERE world_id=1")
        ]
        newcomer = identity()
        db.execute("INSERT INTO users VALUES (?,?,?)", (newcomer, "Newcomer", "unused"))
        game.create(db, newcomer, "Newcomer")
        added = game.read(db, newcomer)
        assert all(
            math.hypot(added["x"] - colony["x"], added["y"] - colony["y"]) >= 6 for colony in before
        )
        posts = game.world_outposts(db, 1)
        occupied = {(post["x"], post["y"]) for post in posts}
        occupied.update((colony["x"], colony["y"]) for colony in before)
        protected_sector = next(
            (x, y)
            for y in range(max(0, home["y"] - 5), min(64, home["y"] + 6))
            for x in range(max(0, home["x"] - 5), min(64, home["x"] + 6))
            if math.hypot(x - home["x"], y - home["y"]) < 6
            and (x, y) not in occupied
            and db.execute(
                "SELECT 1 FROM world_terrain WHERE world_id=1 AND x=? AND y=? AND terrain<>'water'",
                (x, y),
            ).fetchone()
        )
        blocked_user = identity()
        db.execute("INSERT INTO users VALUES (?,?,?)", (blocked_user, "Blocked", "unused"))
        with pytest.raises(RuleError, match="Kolonieschutzabstand"):
            game.create(db, blocked_user, "Blocked", sector=protected_sector)
        assert (
            db.execute("SELECT 1 FROM colonies WHERE user_id=?", (blocked_user,)).fetchone() is None
        )


def test_new_colony_has_all_resources_and_production_during_protection(world):
    game, user = world
    with game.transaction() as db:
        colony = game.read(db, user)
        joined = db.execute("SELECT joined FROM profiles WHERE user_id=?", (user,)).fetchone()[0]

        assert colony["terrain"] != "water"
        assert all(colony["buildings"][key] >= 1 for key in ("wood", "stone", "ore"))
        for index, key in enumerate(("wood", "stone", "ore")):
            assert colony["resources"][index] >= max(
                BUILDINGS[building]["cost"][index] for building in BUILDINGS
            )
        assert joined + 3600 >= int(time.time())


def test_map_bookmark_migration_preserves_existing_player_data(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    game = Game(path)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Legacy', 'password-hash')", (user,))
        game.create(db, user, "Legacy")
        before = json.loads(
            db.execute("SELECT state FROM colonies WHERE user_id=?", (user,)).fetchone()[0]
        )
        for table in (
            "terra_orbit_cargo",
            "orbit_transports",
            "orbit_attacks",
            "orbit_attack_wings",
        ):
            for operation in ("insert", "update"):
                db.execute(f"DROP TRIGGER {table}_scope_{operation}")
        db.execute("DELETE FROM schema_versions WHERE version=68")
        db.execute("ALTER TABLE colonies RENAME TO colonies_v5")
        db.execute(
            "CREATE TABLE colonies(user_id TEXT PRIMARY KEY REFERENCES users(id), state TEXT NOT NULL)"
        )
        db.execute(
            "INSERT INTO colonies(user_id,state) SELECT user_id,state FROM colonies_v5 WHERE is_home=1"
        )
        db.execute("DROP TABLE colonies_v5")
        db.execute("ALTER TABLE profiles DROP COLUMN active_colony_id")
        db.execute("DROP TABLE map_bookmarks")
        db.execute("DELETE FROM schema_versions WHERE version IN (4,5)")

    upgraded = Game(path)
    with upgraded.transaction() as db:
        row = db.execute("SELECT name FROM users WHERE id=?", (user,)).fetchone()
        colony = json.loads(
            db.execute("SELECT state FROM colonies WHERE user_id=?", (user,)).fetchone()[0]
        )
        assert row[0] == "Legacy"
        assert colony == before
        assert db.execute("SELECT count(*) FROM map_bookmarks").fetchone()[0] == 0
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=4").fetchone()
        migrated = db.execute(
            "SELECT colony_id,world_id,is_home FROM colonies WHERE user_id=?", (user,)
        ).fetchone()
        assert migrated["colony_id"] == user
        assert migrated["world_id"] == 1 and migrated["is_home"] == 1
        assert (
            db.execute("SELECT active_colony_id FROM profiles WHERE user_id=?", (user,)).fetchone()[
                0
            ]
            == user
        )


def test_world_outpost_normalization_backfills_without_changing_legacy_data(tmp_path):
    path = tmp_path / "outposts.sqlite3"
    game = Game(path)
    player = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Legacy', 'unused')", (player,))
        game.create(db, player, "Legacy")
        world_row = db.execute("SELECT state FROM world WHERE id=1").fetchone()
        legacy_outposts = json.loads(world_row[0])
        legacy_outposts[0]["stock"] = [123, 456, 789]
        legacy_outposts[0]["owner"] = "legacy-owner"
        legacy_text = json.dumps(legacy_outposts)
        db.execute("UPDATE world SET state=? WHERE id=1", (legacy_text,))
        db.execute("DELETE FROM schema_versions WHERE version=9")
        db.execute("DROP TABLE world_outposts")

    migrated = Game(path)
    with migrated.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123
        assert (
            db.execute("SELECT count(*) FROM world_outposts WHERE world_id=1").fetchone()[0] == 104
        )
        assert db.execute("SELECT state FROM world WHERE id=1").fetchone()[0] == legacy_text
        normalized = migrated.world_outposts(db, 1)
        assert normalized == legacy_outposts
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1
        assert (
            db.execute("SELECT count(*) FROM colonies WHERE user_id=?", (player,)).fetchone()[0]
            == 1
        )


def test_world_context_migration_removes_single_world_limit_without_data_loss(tmp_path):
    path = tmp_path / "world-context.sqlite3"
    game = Game(path)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'World owner', 'unused')", (user,))
        game.create(db, user, "World owner")
    with game.connect() as db:
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("BEGIN IMMEDIATE")
        legacy_world = db.execute("SELECT state FROM world WHERE id=1").fetchone()[0]
        db.execute(
            "CREATE TABLE world_new(id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL)"
        )
        db.execute("INSERT INTO world_new SELECT * FROM world")
        db.execute("DROP TABLE world")
        db.execute("ALTER TABLE world_new RENAME TO world")
        db.execute("DROP TABLE world_settings")
        db.execute("ALTER TABLE profiles DROP COLUMN active_world_id")
        db.execute("DELETE FROM schema_versions WHERE version=10")
        db.execute("COMMIT")
        db.execute("PRAGMA foreign_keys=ON")

    upgraded = Game(path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123
        assert db.execute("SELECT state FROM world WHERE id=1").fetchone()[0] == legacy_world
        assert (
            db.execute("SELECT active_world_id FROM profiles WHERE user_id=?", (user,)).fetchone()[
                0
            ]
            == 1
        )
        assert (
            db.execute("SELECT name FROM world_settings WHERE world_id=1").fetchone()[0]
            == "Genesis"
        )


def test_schema_16_session_upgrade_preserves_sessions_and_backfills_opaque_ids(tmp_path):
    path = tmp_path / "session-upgrade.sqlite3"
    game = Game(path)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Session owner', 'unused')", (user,))
        game.create(db, user, "Session owner")
        db.execute(
            "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                "hashed-session-token",
                user,
                "csrf-secret",
                2_000_000_000,
                "opaque-device-id",
                1_900_000_000,
                "Old browser",
            ),
        )
        db.execute("DROP INDEX sessions_owner_feed")
        db.execute("DROP INDEX sessions_session_id_unique")
        db.execute("ALTER TABLE sessions DROP COLUMN user_agent")
        db.execute("ALTER TABLE sessions DROP COLUMN created")
        db.execute("ALTER TABLE sessions DROP COLUMN session_id")
        db.execute("DELETE FROM schema_versions WHERE version=16")
        db.execute("DELETE FROM schema_versions WHERE version=27")

    upgraded = Game(path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123
        session = db.execute(
            "SELECT token,user_id,csrf,expires,session_id,created,user_agent FROM sessions"
        ).fetchone()
        assert tuple(session[key] for key in ("token", "user_id", "csrf", "expires")) == (
            "hashed-session-token",
            user,
            "csrf-secret",
            2_000_000_000,
        )
        assert session["session_id"]
        assert session["session_id"] != "hashed-session-token"
        assert session["created"] == 0
        assert session["user_agent"] == ""
        db.execute("INSERT INTO world(id,state) VALUES (2,'[]')")
        db.execute(
            "INSERT INTO world_settings(world_id,name,seed,outpost_count,created,settings) "
            "VALUES (2,'Second Dawn',7001,0,1,'{}')"
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def edit(world, **changes):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state.update(changes)
        game.save(db, state)


def test_build_completes_once_and_production_changes(world):
    game, user = world
    result = issue(world, "build", {"key": "wood"})
    assert result["resources"][0] == 1050
    with game.transaction() as db:
        state = game.read(db, user)
        due = state["jobs"][0]["due"]
        game.tick(db, state, due + 10)
        assert state["buildings"]["wood"] == 2
        assert not state["jobs"]
        expected = list(state["resources"])
        game.tick(db, state, due + 10)
        assert state["resources"] == expected


def test_idempotency_and_conflict(world):
    token = identity()
    one = issue(world, "build", {"key": "wood"}, token)
    two = issue(world, "build", {"key": "wood"}, token)
    assert one["resources"] == two["resources"]
    with pytest.raises(RuleError):
        issue(world, "build", {"key": "stone"}, token)


def test_concurrent_queue_cannot_double_spend(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [5000, 5000, 5000]
        state["buildings"]["storage"] = 10
        game.save(db, state)

    def build(_):
        try:
            issue(world, "build", {"key": "wood"})
            return True
        except RuleError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(build, range(8))) == 5
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        queue = sorted(state["jobs"], key=lambda job: job["queue_order"])
        assert len(queue) == 5
        assert [job["target_level"] for job in queue] == [2, 3, 4, 5, 6]
        assert state["resources"] == [3500, 4000, 4600]


def test_seeded_command_sequences_preserve_resource_unit_invariants_and_are_deterministic(
    tmp_path, monkeypatch
):
    clock = [1_790_000_000]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    user = "00000000-0000-4000-8000-00000000f010"

    def run_sequence(database: str) -> dict[str, object]:
        game = Game(database)
        with game.transaction() as db:
            db.execute("INSERT INTO users VALUES (?, 'Property Pilot', 'unused')", (user,))
            game.create(db, user, "Property Pilot")
            state = game.read(db, user)
            state["resources"] = [500_000, 500_000, 500_000]
            state["buildings"]["lab"] = 1
            state["buildings"]["barracks"] = 3
            state["buildings"]["storage"] = 10
            game.save(db, state)

        rng = random.Random(0xF0E)
        actions = ("build", "research", "train", "trade", "cancel_job")
        building_keys = tuple(BUILDINGS)
        research_keys = tuple(TECH)
        unit_keys = tuple(UNITS)
        for index in range(120):
            with game.transaction() as db:
                before = game.read(db, user)
            action = rng.choice(actions)
            if action == "build":
                payload = {"key": rng.choice(building_keys)}
            elif action == "research":
                payload = {"key": rng.choice(research_keys)}
            elif action == "train":
                payload = {"key": rng.choice(unit_keys), "count": rng.randint(1, 100)}
            elif action == "trade":
                source, destination = rng.sample(range(3), 2)
                payload = {"source": source, "dest": destination, "amount": rng.randint(1, 50_000)}
            else:
                payload = (
                    {"key": rng.choice(before["jobs"])["id"]}
                    if before["jobs"]
                    else {"key": "missing"}
                )

            token = f"property-{index}"
            try:
                with game.transaction() as db:
                    game.command(db, user, action, payload, token)
                with game.transaction() as db:
                    game.command(db, user, action, payload, token)
            except RuleError:
                pass

            with game.transaction() as db:
                current = game.read(db, user)
            assert all(type(value) is int and value >= 0 for value in current["resources"])
            assert all(type(value) is int and value >= 0 for value in current["reserve"])
            assert all(type(value) is int and value >= 0 for value in current["units"].values())
            assert len(current["jobs"]) <= 30
            for job in current["jobs"]:
                for field in ("army", "loot"):
                    assert all(
                        type(value) is int and value >= 0 for value in job.get(field, {}).values()
                    )

        clock[0] += 1_000_000
        with game.transaction() as db:
            game.advance(db, clock[0])
            final = game.read(db, user)
        assert all(type(value) is int and value >= 0 for value in final["resources"])
        assert all(type(value) is int and value >= 0 for value in final["units"].values())
        return {
            "resources": final["resources"],
            "reserve": final["reserve"],
            "units": final["units"],
            "buildings": final["buildings"],
            "tech": final["tech"],
            "jobs": [
                {key: value for key, value in job.items() if key != "id"} for job in final["jobs"]
            ],
        }

    assert run_sequence(str(tmp_path / "property-first.sqlite3")) == run_sequence(
        str(tmp_path / "property-second.sqlite3")
    )


@pytest.mark.parametrize(
    "key,base_cost",
    [
        ("hq", [150, 120, 80]),
        ("wood", [75, 50, 20]),
        ("stone", [90, 65, 30]),
        ("ore", [100, 90, 45]),
        ("storage", [120, 100, 50]),
        ("barracks", [130, 110, 90]),
        ("lab", [120, 150, 130]),
        ("wall", [80, 160, 70]),
    ],
)
def test_each_building_cost_scales_by_target_level_and_uses_hq_speed(world, key, base_cost):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        funding = 4000
        if key != "storage":
            state["buildings"]["storage"] = 10
            funding = 20000
        state["resources"] = [funding, funding, funding]
        game.save(db, state)
        start = state["last"]
        level = state["buildings"][key]
        result = game.command(db, user, "build", {"key": key}, identity())
        expected_cost = [value * (level + 1) for value in base_cost]
        assert result["resources"] == [funding - value for value in expected_cost]
        expected_duration = max(3, 8 * (level + 1) - state["buildings"]["hq"])
        assert result["jobs"][0]["due"] == start + expected_duration
        assert BUILDINGS[key]["cost"] == base_cost


def test_build_queue_has_five_planned_levels_and_building_level_is_capped_at_ten(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [20000, 20000, 20000]
        state["buildings"]["storage"] = 10
        game.save(db, state)
        first = game.command(db, user, "build", {"key": "wood"}, identity())
        for _ in range(4):
            result = game.command(db, user, "build", {"key": "wood"}, identity())
        queue = sorted(result["jobs"], key=lambda job: job["queue_order"])
        assert [job["target_level"] for job in queue] == [2, 3, 4, 5, 6]
        assert queue[0]["id"] == first["jobs"][0]["id"]
        remaining = list(result["resources"])
    with pytest.raises(RuleError, match="fünf Aufträge"):
        issue(world, "build", {"key": "stone"})
    with game.transaction() as db:
        state = game.read(db, user)
        assert state["resources"] == remaining
        state["jobs"] = []
        state["buildings"]["wood"] = 10
        game.save(db, state)
    with pytest.raises(RuleError, match="Maximalstufe 10"):
        issue(world, "build", {"key": "wood"})


def test_research_requires_lab_and_plans_multiple_levels_in_one_queue(world, monkeypatch):
    game, user = world
    with game.transaction() as db:
        initial_time = game.read(db, user)["last"]
    clock = [initial_time]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    with pytest.raises(RuleError, match="Forschungslabor"):
        issue(world, "research", {"key": "tactics"})
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["lab"] = 1
        state["buildings"]["storage"] = 10
        state["resources"] = [20000, 20000, 20000]
        game.save(db, state)
        start = state["last"]
        first = game.command(db, user, "research", {"key": "tactics"}, identity())
        assert first["jobs"][0]["due"] == start + 12
        assert first["resources"] == [19930, 19910, 19850]
    queued = issue(world, "research", {"key": "logistics"})
    logistics = next(job for job in queued["jobs"] if job["key"] == "logistics")
    tactics = next(job for job in queued["jobs"] if job["key"] == "tactics")
    assert logistics["queued"] is True
    assert logistics["started_at"] == tactics["due"]
    assert logistics["due"] == tactics["due"] + 12
    with game.transaction() as db:
        state = game.read(db, user)
        clock[0] = tactics["due"]
        game.tick(db, state, clock[0])
        assert state["tech"]["tactics"] == 1
        promoted = next(job for job in state["jobs"] if job["key"] == "logistics")
        assert promoted["queued"] is False
        assert promoted["started_at"] == tactics["due"]
        clock[0] = promoted["due"]
        game.tick(db, state, clock[0])
        assert state["tech"]["logistics"] == 1
        assert state["jobs"] == []
        state["resources"] = [20000, 20000, 20000]
        game.save(db, state)
        next_start = state["last"]
        second = game.command(db, user, "research", {"key": "tactics"}, identity())
        assert second["jobs"][0]["due"] == next_start + 24
        assert second["resources"] == [19860, 19820, 19700]
    assert TECH["tactics"]["cost"] == [70, 90, 150]
    assert TECH["logistics"]["cost"] == [130, 70, 100]
    assert TECH["engineering"]["cost"] == [100, 140, 90]


def test_queued_build_costs_keep_their_catalog_snapshot_when_replanned(world, monkeypatch):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [20000, 20000, 20000]
        state["buildings"]["storage"] = 10
        game.save(db, state)
    first = issue(world, "build", {"key": "wall"})
    second = issue(world, "build", {"key": "wall"})
    with game.transaction() as db:
        state = game.read(db, user)
        original_resources = list(state["resources"])
        jobs = sorted(
            (job for job in state["jobs"] if job["kind"] == "build"),
            key=lambda job: job["queue_order"],
        )
        assert [job["costs"] for job in jobs] == [[80, 160, 70], [160, 320, 140]]
        assert all(job["rule_snapshot"]["digest"] == RULES_DIGEST for job in jobs)
        assert all(job["rule_snapshot"]["base_cost"] == [80, 160, 70] for job in jobs)

        # Existing persisted queues from earlier releases have costs but no pinned snapshot.
        jobs[0].pop("rule_snapshot")
        monkeypatch.setitem(BUILDINGS["wall"], "cost", [800, 900, 1000])
        game.replan_upgrade_queue(state, "build", int(jobs[0]["started_at"]))

        assert [job["costs"] for job in jobs] == [[80, 160, 70], [160, 320, 140]]
        assert jobs[0]["rule_snapshot"]["source"] == "legacy_cost_inference"
        assert jobs[0]["rule_snapshot"]["base_cost"] == [80, 160, 70]
        assert state["resources"] == original_resources
        assert jobs[0]["id"] == first["jobs"][0]["id"]
        assert jobs[1]["id"] == second["jobs"][1]["id"]


def test_queued_research_costs_keep_their_catalog_snapshot_when_replanned(world, monkeypatch):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [20000, 20000, 20000]
        state["buildings"]["storage"] = 10
        state["buildings"]["lab"] = 1
        game.save(db, state)
    first = issue(world, "research", {"key": "tactics"})
    second = issue(world, "research", {"key": "tactics"})
    with game.transaction() as db:
        state = game.read(db, user)
        original_resources = list(state["resources"])
        jobs = sorted(
            (job for job in state["jobs"] if job["kind"] == "research"),
            key=lambda job: job["queue_order"],
        )
        assert [job["costs"] for job in jobs] == [[70, 90, 150], [140, 180, 300]]
        assert all(job["rule_snapshot"]["digest"] == RULES_DIGEST for job in jobs)
        assert all(job["rule_snapshot"]["base_cost"] == [70, 90, 150] for job in jobs)

        jobs[0].pop("rule_snapshot")
        monkeypatch.setitem(TECH["tactics"], "cost", [700, 900, 1500])
        game.replan_upgrade_queue(state, "research", int(jobs[0]["started_at"]))

        assert [job["costs"] for job in jobs] == [[70, 90, 150], [140, 180, 300]]
        assert jobs[0]["rule_snapshot"]["source"] == "legacy_cost_inference"
        assert jobs[0]["rule_snapshot"]["base_cost"] == [70, 90, 150]
        assert state["resources"] == original_resources
        assert jobs[0]["id"] == first["jobs"][0]["id"]
        assert jobs[1]["id"] == second["jobs"][1]["id"]


def test_fur2_unit_catalog_has_original_cost_power_time_and_barracks_gate(world):
    game, user = world
    expected = {
        "ranger": ([35, 15, 25], 12, 2, 1),
        "sentinel": ([50, 40, 60], 28, 4, 2),
        "mech": ([100, 90, 140], 70, 7, 3),
    }
    for key, (cost, power, duration, barracks) in expected.items():
        assert UNITS[key]["cost"] == cost
        assert (UNITS[key]["power"], UNITS[key]["time"], UNITS[key]["require"]) == (
            power,
            duration,
            barracks,
        )
    with pytest.raises(RuleError, match="Kaserne Stufe 2"):
        issue(world, "train", {"key": "sentinel", "count": 1})
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["barracks"] = 2
        state["buildings"]["storage"] = 10
        state["resources"] = [20000, 20000, 20000]
        game.save(db, state)
        start = state["last"]
        trained = game.command(db, user, "train", {"key": "sentinel", "count": 5}, identity())
        assert trained["resources"] == [19750, 19800, 19700]
        assert trained["jobs"][0]["due"] == start + 20
    with pytest.raises(RuleError, match="Warteschlange"):
        issue(world, "train", {"key": "ranger", "count": 1})
    with game.transaction() as db:
        state = game.read(db, user)
        state["jobs"] = []
        state["buildings"]["barracks"] = 2
        game.save(db, state)
    with pytest.raises(RuleError, match="Kaserne Stufe 3"):
        issue(world, "train", {"key": "mech", "count": 1})


def test_combat3_unit_roster_is_registered_as_an_immutable_draft(world):
    from fur_empire import terra_combat

    game, _user = world
    version = "FUR-3-TERRA-COMBAT-3"
    with game.transaction() as db:
        stored = db.execute(
            "SELECT snapshot,digest FROM rule_catalogs WHERE version=?", (version,)
        ).fetchone()
        assert stored["digest"] == terra_combat.RULESET_DIGESTS[version]
        assert stored["snapshot"] == terra_combat.RULESET_SNAPSHOTS[version]
        rules = terra_combat.rules_for(version)
        assert len(rules["units"]) == 21
        assert rules["unit_economy"]["enabled_for_training"] is False
        assert not db.execute(
            "SELECT 1 FROM world_settings WHERE terra_combat_ruleset=?", (version,)
        ).fetchone()


def test_combat4_catalog_is_visible_but_training_stays_locked(world):
    game, user = world
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-4' "
            "WHERE world_id=1"
        )
        state = game.view(db, user)
        assert state["active_world"]["unit_training_enabled"] is False
        assert len(state["catalog"]["units"]) == 21
        assert state["units"]["ranger"] > 0
    with pytest.raises(RuleError, match="nicht zur Ausbildung freigegeben"):
        issue((game, user), "train", {"key": "scout", "count": 1})


def test_combat4_repair_wreck_is_transactional_cancellable_and_completes(world):
    game, user = world
    token = identity()
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-4' "
            "WHERE world_id=1"
        )
        state = game.read(db, user)
        state["buildings"]["barracks"] = 1
        game.save(db, state)
        starting_rangers = int(state["units"]["ranger"])
        wreck = game.record_terra_unit_wrecks(
            db,
            mission_id="repair-test-battle",
            owner_id=user,
            colony_id=state["colony_id"],
            world_id=1,
            losses={"ranger": 4},
            combat_version="FUR-3-TERRA-COMBAT-4",
            at=int(time.time()),
        )[0]
        replay = game.record_terra_unit_wrecks(
            db,
            mission_id="repair-test-battle",
            owner_id=user,
            colony_id=state["colony_id"],
            world_id=1,
            losses={"ranger": 4},
            combat_version="FUR-3-TERRA-COMBAT-4",
            at=int(time.time()),
        )
        assert replay == [wreck]
        assert (
            game.record_terra_unit_wrecks(
                db,
                mission_id="small-loss-battle",
                owner_id=user,
                colony_id=state["colony_id"],
                world_id=1,
                losses={"ranger": 3},
                combat_version="FUR-3-TERRA-COMBAT-4",
                at=int(time.time()),
            )
            == []
        )
        with pytest.raises(RuleError, match="Wrackdaten sind ungültig"):
            game.record_terra_unit_wrecks(
                db,
                mission_id="small-loss-battle",
                owner_id=user,
                colony_id=state["colony_id"],
                world_id=1,
                losses={"ranger": 4},
                combat_version="FUR-3-TERRA-COMBAT-4",
                at=int(time.time()),
            )
        before = list(state["resources"])
        payload = {
            "wreck_id": wreck["id"],
            "count": 1,
            "world_id": 1,
            "colony_id": state["colony_id"],
        }

    queued = issue((game, user), "terra_repair_units", payload, token)
    retried = issue((game, user), "terra_repair_units", payload, token)
    job = next(job for job in queued["jobs"] if job["kind"] == "terra_repair")
    assert next(job for job in retried["jobs"] if job["kind"] == "terra_repair")["id"] == job["id"]
    assert job["costs"] == [18, 8, 13]

    with game.transaction() as db:
        state = game.read(db, user)
        assert state["resources"] == [a - b for a, b in zip(before, job["costs"])]
        assert game.view(db, user)["terra_unit_wrecks"] == []

    cancelled = issue((game, user), "cancel_job", {"key": job["id"]})
    assert not any(job["kind"] == "terra_repair" for job in cancelled["jobs"])
    with game.transaction() as db:
        state = game.read(db, user)
        assert state["resources"] == before
        amount = db.execute(
            "SELECT amount FROM terra_unit_wrecks WHERE id=?", (wreck["id"],)
        ).fetchone()[0]
        assert amount == 1

    with game.transaction() as db:
        now = int(time.time())
        expired_wreck = game.record_terra_unit_wrecks(
            db,
            mission_id="repair-cancel-after-expiry",
            owner_id=user,
            colony_id=state["colony_id"],
            world_id=1,
            losses={"ranger": 4},
            combat_version="FUR-3-TERRA-COMBAT-4",
            at=now,
        )[0]
    expired_order = issue(
        (game, user),
        "terra_repair_units",
        {**payload, "wreck_id": expired_wreck["id"]},
    )
    expired_job = next(job for job in expired_order["jobs"] if job["kind"] == "terra_repair")
    with game.transaction() as db:
        db.execute("UPDATE terra_unit_wrecks SET expires=0 WHERE id=?", (expired_wreck["id"],))
    refunded = issue((game, user), "cancel_job", {"key": expired_job["id"]})
    assert not any(job["kind"] == "terra_repair" for job in refunded["jobs"])

    next_order = issue((game, user), "terra_repair_units", payload)
    repair = next(job for job in next_order["jobs"] if job["kind"] == "terra_repair")
    with game.transaction() as db:
        game.advance(db, repair["due"])
        state = game.read(db, user)
        assert state["units"]["ranger"] == starting_rangers + 1
        assert not any(job["kind"] == "terra_repair" for job in state["jobs"])


def test_schema_81_wreck_migration_preserves_existing_player_state(tmp_path):
    path = tmp_path / "schema-82-preservation.sqlite3"
    game = Game(path)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Schema owner', 'unused')", (user,))
        game.create(db, user, "Schema owner")
        state = game.read(db, user)
        state["resources"] = [123, 456, 789]
        game.save(db, state)
        original = db.execute(
            "SELECT state FROM colonies WHERE colony_id=?", (state["colony_id"],)
        ).fetchone()[0]
        db.execute("DROP TABLE terra_unit_wrecks")
        db.execute("DELETE FROM schema_versions WHERE version=81")

    upgraded = Game(path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123
        assert (
            db.execute("SELECT state FROM colonies WHERE colony_id=?", (user,)).fetchone()[0]
            == original
        )
        assert db.execute("SELECT count(*) FROM terra_unit_wrecks").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1


def test_combat3_movement_uses_slowest_unit_range_and_round_trip_fuel(world):
    from fur_empire import terra_combat

    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        origin = (state["x"], state["y"])
        target = next(
            point
            for point in ((state["x"] + 1, state["y"]), (state["x"], state["y"] + 1))
            if 0 <= point[0] < 64
            and 0 <= point[1] < 64
            and terrain_at(db, point[0], point[1], state["world_id"]) != "water"
        )
        legacy = game.movement_quote(db, origin, target, state["world_id"], {"ranger": 1})
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-3' WHERE world_id=?",
            (state["world_id"],),
        )
        fast = game.movement_quote(db, origin, target, state["world_id"], {"ranger": 1})
        mixed = game.movement_quote(
            db, origin, target, state["world_id"], {"ranger": 1, "mech": 10}
        )
        assert legacy["rules_version"] == "FUR-2"
        assert legacy["fuel_ore"] == 0
        assert fast["rules_version"] == "FUR-3-TERRA-COMBAT-3"
        assert fast["rules_digest"] == terra_combat.RULESET_DIGESTS[fast["rules_version"]]
        assert mixed["travel_seconds"] > fast["travel_seconds"]
        assert mixed["fuel_ore"] > fast["fuel_ore"]
        assert fast["travel_seconds"] >= 60
        assert fast["route_cost"] > 0

        route_costs = travel_costs(db, origin, state["world_id"])
        distant = max(route_costs, key=route_costs.__getitem__)
        with pytest.raises(RuleError, match="Reichweite"):
            game.movement_quote(db, origin, distant, state["world_id"], {"ranger": 1})


def test_unlock_prerequisites_use_completed_not_planned_buildings(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [20000, 20000, 20000]
        state["buildings"]["storage"] = 10
        game.save(db, state)
    with pytest.raises(RuleError, match="Forschungslabor"):
        issue(world, "research", {"key": "tactics"})
    with pytest.raises(RuleError, match="Kaserne Stufe 2"):
        issue(world, "train", {"key": "sentinel", "count": 1})

    # Planning the prerequisite building does not unlock research or training
    # until that building actually completes.
    issue(world, "build", {"key": "lab"})
    with pytest.raises(RuleError, match="Forschungslabor"):
        issue(world, "research", {"key": "tactics"})
    issue(world, "build", {"key": "barracks"})
    with pytest.raises(RuleError, match="Kaserne Stufe 2"):
        issue(world, "train", {"key": "sentinel", "count": 1})

    with game.transaction() as db:
        state = game.read(db, user)
        state["jobs"] = []
        state["buildings"]["lab"] = 1
        state["buildings"]["barracks"] = 1
        game.save(db, state)
    issue(world, "research", {"key": "tactics"})
    with pytest.raises(RuleError, match="Kaserne Stufe 2"):
        issue(world, "train", {"key": "sentinel", "count": 1})


def test_headquarters_reduces_build_time_and_capture_requires_level_three(world):
    game, user = world
    with game.transaction() as db:
        initial_power = next(
            row["score"] for row in game.view(db, user)["ranking"] if row["name"] == "Tester"
        )
        state = game.read(db, user)
        state["resources"] = [20000, 20000, 20000]
        game.save(db, state)
        start = state["last"]
        first = game.command(db, user, "build", {"key": "wall"}, identity())
        base_duration = first["jobs"][0]["due"] - start
        state = game.read(db, user)
        state["jobs"] = []
        state["buildings"]["hq"] = 3
        state["resources"] = [20000, 20000, 20000]
        game.save(db, state)
        faster = game.command(db, user, "build", {"key": "wall"}, identity())
        fast_duration = faster["jobs"][0]["due"] - start
        assert base_duration == 7 and fast_duration == 5
        state = game.read(db, user)
        state["jobs"] = []
        state["buildings"]["hq"] = 2
        state["units"]["mech"] = 100
        game.save(db, state)
        town = game.view(db, user)["world"][0]
        assert (
            next(row["score"] for row in game.view(db, user)["ranking"] if row["name"] == "Tester")
            == initial_power + 10
        )
        before_units = dict(game.read(db, user)["units"])
    with pytest.raises(RuleError, match="Stufe 3"):
        issue(world, "raid", {"key": town["id"], "army": {"mech": 50}, "capture": True})
    with game.transaction() as db:
        assert game.read(db, user)["units"] == before_units


@pytest.mark.parametrize("count", [0, 101])
def test_training_count_must_be_between_one_and_one_hundred(world, count):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["barracks"] = 3
        state["buildings"]["storage"] = 10
        state["resources"] = [22000, 22000, 22000]
        game.save(db, state)
    with pytest.raises(RuleError, match="1 bis 100"):
        issue(world, "train", {"key": "mech", "count": count})


def test_thirty_operation_limit_rejects_an_additional_raid(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        future = state["last"] + 1000
        state["jobs"] = [
            {"id": identity(), "kind": "transport", "key": "target", "due": future}
            for _ in range(30)
        ]
        state["units"]["ranger"] = 15
        game.save(db, state)
        target = game.view(db, user)["world"][0]
    with pytest.raises(RuleError, match="Maximal 30"):
        issue(world, "raid", {"key": target["id"], "army": {"ranger": 1}})


@pytest.mark.parametrize(
    "action,payload",
    [
        ("build", {"key": "bad"}),
        ("train", {"key": "ranger", "count": -1}),
        ("research", {"key": "tactics"}),
        ("trade", {"source": 0, "dest": 1, "amount": -100}),
        ("trade", {"source": 0, "dest": 0, "amount": 100}),
        ("quest", {"key": "victory"}),
        ("raid", {"key": "invalid", "army": {"ranger": 5}}),
    ],
)
def test_invalid_commands_rollback(world, action, payload):
    game, user = world
    with game.transaction() as db:
        before = game.read(db, user)
    with pytest.raises(RuleError):
        issue(world, action, payload)
    with game.transaction() as db:
        after = game.read(db, user)
    assert before == after


def test_raid_returns_and_captures_offline(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["hq"] = 3
        game.save(db, state)
        town = game.view(db, user)["world"][0]
    result = issue(world, "raid", {"key": town["id"], "army": {"ranger": 15}, "capture": True})
    assert result["units"]["ranger"] == 0
    game = Game(game.path)  # simulate restart
    with game.transaction() as db:
        state = game.read(db, user)
        game.tick(db, state, state["last"] + 300)
        assert state["captures"] == 1
        assert state["units"]["ranger"] > 0
        assert not state["jobs"]
        assert len(state["reports"]) == 2
        game.tick(db, state, state["last"])
        assert state["captures"] == 1


def test_fur3_outpost_mission_pins_secret_seed_and_reveals_replay_after_arrival(world):
    from fur_empire import terra_combat

    game, user = world
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        state = game.read(db, user)
        state["units"]["ranger"] = 60
        game.save(db, state)
        target = game.view(db, user)["world"][0]

    dispatched = issue(world, "raid", {"key": target["id"], "army": {"ranger": 60}})
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "raid")
    assert mission["rules_version"] == terra_combat.VERSION
    assert mission["rules_digest"] == terra_combat.DIGEST
    assert mission["seed_commitment"]
    assert "seed" not in mission
    with game.transaction() as db:
        stored = db.execute(
            "SELECT seed,seed_commitment,resolved FROM terra_combat_missions WHERE mission_id=?",
            (mission["id"],),
        ).fetchone()
        assert stored["seed_commitment"] == mission["seed_commitment"]
        assert stored["resolved"] is None
        public_state = db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=1", (user,)
        ).fetchone()[0]
        assert stored["seed"] not in public_state
        db.execute("UPDATE world_settings SET terra_combat_ruleset='FUR-2' WHERE world_id=1")
        game.advance(db, mission["due"])
        result_state = game.read(db, user)
        report = next(item for item in result_state["reports"] if item.get("combat"))
        assert report["combat"]["rules_version"] == terra_combat.VERSION
        assert report["combat"]["seed"] == stored["seed"]
        replay = db.execute(
            "SELECT resolved,replay FROM terra_combat_missions WHERE mission_id=?",
            (mission["id"],),
        ).fetchone()
        assert replay["resolved"] == mission["due"]
        assert json.loads(replay["replay"])["seed"] == stored["seed"]


def test_fur3_tactical_retreat_returns_only_replay_survivors(world):
    from fur_empire import terra_combat
    from fur_empire.game import DEFENSE_PERCENT

    game, user = world
    version = "FUR-3-TERRA-COMBAT-1"
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=?,"
            "terra_retreat_threshold_percent=1 WHERE world_id=1",
            (version,),
        )
        state = game.read(db, user)
        state["units"]["ranger"] = 12
        game.save(db, state)
        target_id = game.view(db, user)["world"][0]["id"]
        posts = game.world_outposts(db, 1)
        target = next(post for post in posts if post["id"] == target_id)
        target.update(owner=None, tier=1, units={"sentinel": 12}, stock=[0, 0, 0])
        game.save_world_outposts(db, 1, posts)

    dispatched = issue(world, "raid", {"key": target_id, "army": {"ranger": 12}})
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "raid")
    with game.transaction() as db:
        state = game.read(db, user)
        mission = next(job for job in state["jobs"] if job["id"] == mission["id"])
        posts = game.world_outposts(db, 1)
        target = next(post for post in posts if post["id"] == target_id)
        terrain = terrain_at(db, int(target["x"]), int(target["y"]), 1)
        modifiers = {"terrain": int(DEFENSE_PERCENT[terrain])}
        seed = next(
            candidate
            for value in range(1000)
            if (candidate := f"{value:064x}")
            and terra_combat.resolve(
                candidate,
                dict(mission["army"]),
                dict(target["units"]),
                attacker_tactics=int(mission["tactics"]),
                defender_modifiers=modifiers,
                retreat_threshold_percent=1,
                rules_version=version,
            )["retreated"]
        )
        commitment = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
        db.execute(
            "UPDATE terra_combat_missions SET seed=?,seed_commitment=? WHERE mission_id=?",
            (seed, commitment, mission["id"]),
        )
        mission["seed_commitment"] = commitment
        game.save(db, state)
        expected = terra_combat.resolve(
            seed,
            dict(mission["army"]),
            dict(target["units"]),
            attacker_tactics=int(mission["tactics"]),
            defender_modifiers=modifiers,
            retreat_threshold_percent=1,
            rules_version=version,
        )
        assert expected["retreated"] is True
        assert sum(expected["attacker_survivors"].values()) > 0

        game.advance(db, int(mission["due"]))
        after = game.read(db, user)
        report = next(item for item in after["reports"] if item.get("combat"))
        returning = next(job for job in after["jobs"] if job["kind"] == "return")

        assert report["combat"]["outcome"] == "attacker_retreat"
        assert report["combat"]["retreated"] is True
        assert returning["army"] == expected["attacker_survivors"]
        assert returning["due"] == mission["due"] + mission["travel"]
        assert after["units"]["ranger"] == 0


def test_fur3_v2_outpost_mission_pins_rules_and_keeps_fortification_virtual(world):
    from fur_empire import terra_combat

    game, user = world
    version = "FUR-3-TERRA-COMBAT-2"
    with game.transaction() as db:
        db.execute("UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1", (version,))
        state = game.read(db, user)
        state["units"]["ranger"] = 100
        game.save(db, state)
        target = game.view(db, user)["world"][0]
        posts = game.world_outposts(db, 1)
        next(post for post in posts if post["id"] == target["id"])["tier"] = 8
        game.save_world_outposts(db, 1, posts)

    dispatched = issue(world, "raid", {"key": target["id"], "army": {"ranger": 100}})
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "raid")
    assert mission["rules_version"] == version
    assert mission["rules_digest"] == terra_combat.RULESET_DIGESTS[version]
    with game.transaction() as db:
        db.execute("UPDATE world_settings SET terra_combat_ruleset='FUR-2' WHERE world_id=1")
        game.advance(db, mission["due"])
        state = game.read(db, user)
        report = next(item for item in state["reports"] if item.get("combat"))
        assert report["combat"]["rules_version"] == version
        assert "outpost_fortification" not in report["combat"]["defender_survivors"]
        post = next(post for post in game.world_outposts(db, 1) if post["id"] == target["id"])
        assert "outpost_fortification" not in post["units"]


def test_outpost_capture_adds_exact_ranking_power_and_five_percent_production(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["hq"] = 3
        state["units"]["ranger"] = 15
        game.save(db, state)
        target = game.view(db, user)["world"][0]
        before_score = next(row["score"] for row in game.ranking(db) if row["id"] == user)
        baseline = game.read(db, user)
        captured = json.loads(json.dumps(baseline))
        captured["captures"] = 1
        game.produce(baseline, baseline["last"] + 100)
        game.produce(captured, captured["last"] + 100)
    issue(world, "raid", {"key": target["id"], "army": {"ranger": 15}, "capture": True})
    with game.transaction() as db:
        due = game.read(db, user)["jobs"][0]["due"]
        game.advance(db, due)
        state = game.read(db, user)
        assert state["captures"] == 1
        assert "citadel" not in state or state["citadel"] is False
        assert (
            next(row["score"] for row in game.ranking(db) if row["id"] == user)
            == before_score + 100
        )
        assert [a - b for a, b in zip(captured["resources"], baseline["resources"])] == [
            20,
            20,
            20,
        ]


def test_neutral_raid_defeat_loses_army_and_returns_without_loot(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["units"]["ranger"] = 5
        game.save(db, state)
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        target = towns[1]
        target["stock"] = [300, 300, 300]
        game.save_world_outposts(db, 1, towns)
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (user, 1, target["x"], target["y"], state["last"]),
        )
    issue(world, "raid", {"key": target["id"], "army": {"ranger": 5}})
    with game.transaction() as db:
        due = game.read(db, user)["jobs"][0]["due"]
        game.advance(db, due)
        state = game.read(db, user)
        assert state["units"]["ranger"] == 0
        assert len(state["jobs"]) == 1
        assert state["jobs"][0]["kind"] == "return"
        assert state["jobs"][0]["army"] == {"ranger": 0}
        assert state["jobs"][0]["loot"] == [0, 0, 0]
        assert json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])[1][
            "stock"
        ] == [300, 300, 300]


def test_neutral_raid_rounds_losses_up_per_type_and_caps_loot_by_capacity_and_stock(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["units"].update(ranger=9, mech=5)
        state["tech"]["logistics"] = 1
        game.save(db, state)
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        target = towns[0]
        target["stock"] = [1, 1000, 2]
        game.save_world_outposts(db, 1, towns)
    issue(world, "raid", {"key": target["id"], "army": {"ranger": 9, "mech": 5}})
    with game.transaction() as db:
        due = game.read(db, user)["jobs"][0]["due"]
        game.advance(db, due)
        state = game.read(db, user)
        ret = next(job for job in state["jobs"] if job["kind"] == "return")
        # Attack 9*12+5*70=458 beats the tier-one defense of 55.
        # The 17% losses round up separately: ranger 2 and mech 1 lost.
        assert ret["army"] == {"ranger": 7, "mech": 4}
        # Capacity is 11 survivors * (40 + 10 logistics) = 550; each of
        # three resource types is limited to one third, then to actual stock.
        assert ret["loot"] == [1, 183, 2]
        remaining = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])[0][
            "stock"
        ]
        assert remaining == [0, 817, 0]


def test_neutral_outpost_stock_replenishes_once_per_minute_to_tier_cap(world):
    game, _ = world
    now = int(time.time())
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)
        target = towns[0]
        target["stock"] = [0, 398, 400]
        game.save_world_outposts(db, 1, towns)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"outpost_stock_checked_at": now - 125}),),
        )
        game.advance(db, now)
        remaining = next(t for t in game.world_outposts(db, 1) if t["id"] == target["id"])
        assert remaining["stock"] == [2, 400, 400]
        game.advance(db, now)
        unchanged = next(t for t in game.world_outposts(db, 1) if t["id"] == target["id"])
        assert unchanged["stock"] == [2, 400, 400]
        game.advance(db, now + 60)
        replenished = next(t for t in game.world_outposts(db, 1) if t["id"] == target["id"])
        assert replenished["stock"] == [3, 400, 400]
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        assert settings["outpost_stock_checked_at"] == now + 55


def test_neutral_outpost_replenishment_is_world_scoped_and_never_changes_owned_stores(world):
    game, user = world
    now = int(time.time())
    with game.transaction() as db:
        game.create_world(db, "Resupply World", 9127, 8, True)
        genesis = game.world_outposts(db, 1)
        genesis[0].update(owner=user, stock=[0, 0, 0])
        game.save_world_outposts(db, 1, genesis)
        second = game.world_outposts(db, 2)
        target = second[1]  # The index-zero outpost is the tier-eight citadel.
        target["stock"] = [0, 399, 400]
        citadel = second[0]
        citadel["stock"] = [3199, 3200, 4000]
        game.save_world_outposts(db, 2, second)
        for world_id in (1, 2):
            db.execute(
                "UPDATE world_settings SET settings=? WHERE world_id=?",
                (json.dumps({"outpost_stock_checked_at": now - 60}), world_id),
            )

        game.advance(db, now)

        owned = next(t for t in game.world_outposts(db, 1) if t["id"] == genesis[0]["id"])
        neutral = next(t for t in game.world_outposts(db, 2) if t["id"] == target["id"])
        assert owned["stock"] == [0, 0, 0]
        assert neutral["stock"] == [1, 400, 400]
        updated_citadel = next(t for t in game.world_outposts(db, 2) if t["id"] == citadel["id"])
        assert updated_citadel["stock"] == [3200, 3200, 4000]


def test_legacy_neutral_outpost_gets_regeneration_baseline_without_stock_change(world):
    game, _ = world
    now = int(time.time())
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)
        target = towns[0]
        target["stock"] = [17, 23, 31]
        game.save_world_outposts(db, 1, towns)
        db.execute("UPDATE world_settings SET settings='{}' WHERE world_id=1")

        game.advance(db, now)

        legacy = next(t for t in game.world_outposts(db, 1) if t["id"] == target["id"])
        assert legacy["stock"] == [17, 23, 31]
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        assert settings["outpost_stock_checked_at"] == now


def test_combat5_neutral_fortifications_regenerate_bounded_and_skip_owned_posts(world):
    game, user = world
    now = int(time.time())
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=?,settings=? WHERE world_id=1",
            (
                "FUR-3-TERRA-COMBAT-5",
                json.dumps({"outpost_stock_checked_at": now}),
            ),
        )
        posts = game.world_outposts(db, 1)
        neutral = posts[0]
        neutral["tier"] = 1
        neutral["fortification_integrity"] = 1
        neutral["fortification_checked_at"] = now - 120
        owned = posts[1]
        owned.update(owner=user, fortification_integrity=1, fortification_checked_at=now - 120)
        game.save_world_outposts(db, 1, posts)

        game.advance(db, now)
        result = game.world_outposts(db, 1)
        healed = next(post for post in result if post["id"] == neutral["id"])
        untouched = next(post for post in result if post["id"] == owned["id"])
        assert healed["fortification_integrity"] == 5
        assert healed["fortification_checked_at"] == now
        assert untouched["fortification_integrity"] == 1
        assert untouched["fortification_checked_at"] == now - 120

        game.advance(db, now)
        repeated = next(post for post in game.world_outposts(db, 1) if post["id"] == neutral["id"])
        assert repeated["fortification_integrity"] == 5


def test_combat5_outpost_fortification_damage_is_deterministic_and_persistable():
    from fur_empire import terra_combat

    ruleset = "FUR-3-TERRA-COMBAT-5"
    result = terra_combat.resolve(
        "00" * 32,
        {"titan_colossus": 10},
        {"outpost_fortification": 1},
        rules_version=ruleset,
        outpost_fortification_integrity=20,
    )
    assert result["outpost_fortification_integrity"] == 0
    assert result["rules_digest"] == terra_combat.RULESET_DIGESTS[ruleset]
    assert result["defender_survivors"] == {}


def test_combat5_raid_persists_fortification_damage_in_target_state(world):
    game, user = world
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-5",),
        )
        state = game.read(db, user)
        state["units"]["titan_colossus"] = 10
        state["resources"][2] = 100_000
        state["buildings"]["hq"] = 3
        game.save(db, state)
        target = game.view(db, user)["world"][0]
        posts = game.world_outposts(db, 1)
        neutral = next(post for post in posts if post["id"] == target["id"])
        neutral.update(owner=None, tier=1, stock=[0, 0, 0])
        game.save_world_outposts(db, 1, posts)

    dispatched = issue(world, "raid", {"key": target["id"], "army": {"titan_colossus": 10}})
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "raid")
    with game.transaction() as db:
        game.advance(db, int(mission["due"]))
        changed = next(post for post in game.world_outposts(db, 1) if post["id"] == target["id"])
        assert changed["fortification_integrity"] == 0
        assert changed["fortification_checked_at"] == mission["due"]
        replay = db.execute(
            "SELECT replay FROM terra_combat_missions WHERE mission_id=?", (mission["id"],)
        ).fetchone()
        assert json.loads(replay["replay"])["outpost_fortification_integrity"] == 0
        game.advance(db, int(mission["due"]) + 60)
        healed = next(post for post in game.world_outposts(db, 1) if post["id"] == target["id"])
        assert healed["fortification_integrity"] == 2
        assert healed["fortification_checked_at"] == int(mission["due"]) + 60


def test_npc_frontier_pressure_is_deterministic_world_scoped_and_never_reinforces_owned_posts(
    world,
):
    game, user = world
    now = int(time.time())
    with game.transaction() as db:
        genesis_posts = game.world_outposts(db, 1)
        world_id = game.create_world(db, "NPC Frontier", 819221, 24, True)
        posts = game.world_outposts(db, world_id)
        target = posts[1]
        target["tier"] = 2
        target["stock"] = [0, 0, 0]
        owned = posts[2]
        owned["owner"] = user
        owned["stock"] = [0, 0, 0]
        game.save_world_outposts(db, world_id, posts)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=?",
            (json.dumps({"npc_frontier_checked_at": now - 300}), world_id),
        )
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"npc_frontier_checked_at": now}),),
        )

        game.update_npc_frontiers(db, now)
        updated = {post["id"]: post for post in game.world_outposts(db, world_id)}
        frontier = updated[target["id"]]
        assert frontier["npc_faction"] in {item[0] for item in NPC_FACTIONS}
        assert frontier["npc_faction_name"] in {item[1] for item in NPC_FACTIONS}
        assert frontier["npc_pressure"] == 2
        assert frontier["stock"] == [0, 0, 0]
        assert "npc_pressure" not in updated[owned["id"]]
        assert updated[owned["id"]]["stock"] == [0, 0, 0]
        assert game.world_outposts(db, 1) == genesis_posts

        game.update_npc_frontiers(db, now + 148 * 300)
        escalated = next(
            post for post in game.world_outposts(db, world_id) if post["id"] == target["id"]
        )
        assert escalated["npc_pressure"] == 98
        assert escalated["stock"] == [4, 4, 4]


def test_npc_faction_summary_reports_derived_world_threat_level(world):
    game, user = world
    now = int(time.time())
    with game.transaction() as db:
        posts = game.world_outposts(db, 1)
        for post in posts:
            post["owner"] = "npc-test-hidden-owner"
        hidden = next(
            post for post in reversed(posts[3:]) if math.hypot(post["x"] - 8, post["y"] - 4) > 8
        )
        hidden["owner"] = None
        hidden["npc_pressure"] = 9999
        pressure_by_faction = {faction: 0 for faction, _name in NPC_FACTIONS}
        seed = 504921
        for index, (faction, _name) in enumerate(NPC_FACTIONS):
            posts[index]["owner"] = None
            posts[index]["npc_pressure"] = (index + 1) * 120
            faction_index = int.from_bytes(
                hashlib.sha256(f"{seed}:{posts[index]['id']}".encode()).digest()[:4], "big"
            ) % len(NPC_FACTIONS)
            pressure_by_faction[NPC_FACTIONS[faction_index][0]] += posts[index]["npc_pressure"]
        for post in posts[3:]:
            post.pop("npc_pressure", None)
        hidden["npc_pressure"] = 9999
        game.save_world_outposts(db, 1, posts)
        colony = game.read(db, user)
        colony["x"], colony["y"] = 8, 4
        game.save(db, colony)
        db.execute("UPDATE colonies SET x=8,y=4 WHERE colony_id=?", (colony["colony_id"],))
        for post in posts[:3]:
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                "VALUES (?,?,?,?,?)",
                (user, 1, post["x"], post["y"], now),
            )
        view = game.view(db, user)
        assert hidden["id"] not in {post["id"] for post in view["world"]}
        factions = {entry["id"]: entry for entry in view["npc_factions"]}
        for faction, pressure in pressure_by_faction.items():
            if pressure:
                assert factions[faction]["pressure"] == pressure
                assert factions[faction]["threat_level"] == min(5, pressure // 100)
            else:
                assert faction not in factions


def test_overdue_raid_uses_outpost_stock_at_its_due_time(world):
    game, user = world
    now = int(time.time())
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)
        target = towns[0]
        target["stock"] = [0, 0, 0]
        game.save_world_outposts(db, 1, towns)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"outpost_stock_checked_at": now - 120}),),
        )
        state = game.read(db, user)
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "raid",
                "key": target["id"],
                "due": now - 60,
                "travel": 0,
                "army": {"mech": 100},
                "tactics": 0,
                "capture": False,
            }
        )
        game.save(db, state)

        game.advance(db, now)

        completed = game.read(db, user)
        report = next(item for item in completed["reports"] if item["title"].startswith("Sieg bei"))
        assert "Beute: 3." in report["body"]
        replenished = next(t for t in game.world_outposts(db, 1) if t["id"] == target["id"])
        assert replenished["stock"] == [1, 1, 1]


def test_region_partition_and_control_require_two_posts_and_strict_majority():
    posts = [
        {"x": 0, "y": 0, "owner": "alpha"},
        {"x": 15, "y": 15, "owner": "alpha"},
        {"x": 16, "y": 0, "owner": "alpha"},
        {"x": 16, "y": 16, "owner": "bravo"},
        {"x": 16, "y": 17, "owner": "charlie"},
        {"x": 16, "y": 18, "owner": None},
    ]

    regions = summarize_regions(posts)
    northwest = next(region for region in regions if region["id"] == "A1")
    northeast = next(region for region in regions if region["id"] == "B1")
    southeast = next(region for region in regions if region["id"] == "B2")
    empty = next(region for region in regions if region["id"] == "D4")

    assert len(regions) == 16
    assert (northwest["x_min"], northwest["x_max"], northwest["y_min"], northwest["y_max"]) == (
        0,
        15,
        0,
        15,
    )
    assert northwest["owner_id"] == "alpha"
    assert northwest["production_bonus_percent"] == REGION_PRODUCTION_BONUS
    assert northeast["outpost_count"] == 1
    assert northeast["required_posts"] == 2
    assert northeast["owner_id"] is None
    assert southeast["leader_tied"]
    assert southeast["owner_id"] is None
    assert empty["outpost_count"] == 0
    assert empty["owner_id"] is None


def test_alliance_region_control_aggregates_actual_member_outpost_ownership():
    posts = [
        {"x": 1, "y": 1, "owner": "alpha"},
        {"x": 2, "y": 2, "owner": "bravo"},
        {"x": 3, "y": 3, "owner": "charlie"},
    ]

    region = next(
        row
        for row in summarize_regions(
            posts,
            {"alpha": "alliance-a", "bravo": "alliance-a", "charlie": "alliance-b"},
        )
        if row["id"] == "A1"
    )

    assert region["owner_id"] is None
    assert region["alliance_owner_id"] == "alliance-a"
    assert region["alliance_leader_tied"] is False


def test_alliance_region_control_tie_has_no_controller():
    posts = [
        {"x": 1, "y": 1, "owner": "alpha"},
        {"x": 2, "y": 2, "owner": "bravo"},
        {"x": 3, "y": 3, "owner": "charlie"},
        {"x": 4, "y": 4, "owner": "delta"},
    ]

    region = next(
        row
        for row in summarize_regions(
            posts,
            {
                "alpha": "alliance-a",
                "bravo": "alliance-a",
                "charlie": "alliance-b",
                "delta": "alliance-b",
            },
        )
        if row["id"] == "A1"
    )

    assert region["alliance_owner_id"] is None
    assert region["alliance_leader_tied"] is True


def test_world_region_cache_tracks_membership_changes(world):
    game, alpha = world
    bravo, charlie = identity(), identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Bravo', 'unused')", (bravo,))
        db.execute("INSERT INTO users VALUES (?, 'Charlie', 'unused')", (charlie,))
        game.create(db, bravo, "Bravo")
        game.create(db, charlie, "Charlie")
        db.execute(
            "INSERT INTO alliances VALUES ('guild','GUILD','Guild','',?,?)",
            (alpha, int(time.time())),
        )
        db.execute("INSERT INTO members VALUES (?, 'guild', 'leader')", (alpha,))
        db.execute("INSERT INTO members VALUES (?, 'guild', 'member')", (bravo,))
        posts = game.world_outposts(db, 1)[:3]
        for index, owner in enumerate((alpha, bravo, charlie)):
            posts[index].update(x=index, y=0, owner=owner)
        game.save_world_outposts(db, 1, posts)
        regions = game.world_regions(db, 1)
        assert (
            next(region for region in regions if region["id"] == "A1")["alliance_owner_id"]
            == "guild"
        )
        db.execute("DELETE FROM members WHERE user_id=?", (bravo,))
        regions = game.world_regions(db, 1)
        assert (
            next(region for region in regions if region["id"] == "A1")["alliance_owner_id"] is None
        )


def test_regional_production_bonus_is_world_scoped_and_cache_invalidates_on_capture(world):
    game, user = world
    with game.transaction() as db:
        game.create_world(db, "Regional Test", 773311, 24, True)
        posts = game.world_outposts(db, 1)
        groups = {}
        for post in posts:
            groups.setdefault((post["x"] // 16, post["y"] // 16), []).append(post)
        region_posts = max(groups.values(), key=len)
        threshold = max(2, len(region_posts) // 2 + 1)
        for post in region_posts[:threshold]:
            post["owner"] = user
        game.save_world_outposts(db, 1, posts)

        assert game.regional_production_bonus(db, user, 1) == REGION_PRODUCTION_BONUS
        assert game.regional_production_bonus(db, user, 2) == 0

        state = game.read(db, user)
        state.update(resources=[0, 0, 0], last=100, captures=0)
        state["buildings"].update(wood=1, stone=0, ore=0)
        state["_events"] = []
        game.produce(state, 101)
        assert state["resources"] == [4, 2, 2]
        assert state["carry"] == [8, 4, 4]

        revoked = game.world_outposts(db, 1)
        for post in revoked:
            if post["id"] == region_posts[threshold - 1]["id"]:
                post["owner"] = None
        game.save_world_outposts(db, 1, revoked)
        assert game.regional_production_bonus(db, user, 1) == 0


def test_regional_production_bonus_is_explicitly_capped_at_all_world_regions(world):
    game, user = world
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)[:32]
        for region_index in range(16):
            column, row = region_index % 4, region_index // 4
            for slot, post in enumerate(towns[region_index * 2 : region_index * 2 + 2]):
                post.update(x=column * 16 + slot, y=row * 16, owner=user)
        game.save_world_outposts(db, 1, towns)

        assert game.regional_production_bonus(db, user, 1) == MAX_REGION_PRODUCTION_BONUS
        assert MAX_REGION_PRODUCTION_BONUS == 32


def test_view_exposes_public_region_bounds_and_players_production_bonus(world):
    game, user = world
    with game.transaction() as db:
        posts = game.world_outposts(db, 1)
        groups = {}
        for post in posts:
            groups.setdefault((post["x"] // 16, post["y"] // 16), []).append(post)
        region_posts = max(groups.values(), key=len)
        threshold = max(2, len(region_posts) // 2 + 1)
        for post in region_posts[:threshold]:
            post["owner"] = user
        game.save_world_outposts(db, 1, posts)
        region_x, region_y = region_posts[0]["x"] // 16, region_posts[0]["y"] // 16
        for y in range(region_y * 16, region_y * 16 + 16):
            for x in range(region_x * 16, region_x * 16 + 16):
                db.execute(
                    "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO NOTHING",
                    (user, 1, x, y, 1),
                )

        state = game.view(db, user)

        assert len(state["regions"]) == 16
        controlled = [region for region in state["regions"] if region["owner_id"] == user]
        assert len(controlled) == 1
        assert controlled[0]["owner_name"] == "Tester"
        assert state["regional_production_bonus"] == REGION_PRODUCTION_BONUS
        assert all("x_min" in region and "y_max" in region for region in state["regions"])


def test_capture_recalculates_region_bonus_before_the_next_simulation_tick(world):
    game, user = world
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)
        groups = {}
        for post in towns:
            groups.setdefault((post["x"] // 16, post["y"] // 16), []).append(post)
        region_posts = max(groups.values(), key=len)
        threshold = max(2, len(region_posts) // 2 + 1)
        for post in region_posts[: threshold - 1]:
            post["owner"] = user
        game.save_world_outposts(db, 1, towns)
        state = game.read(db, user)
        assert state["_region_bonus"] == 0

        target = region_posts[threshold - 1]
        target.update(tier=1, units={}, stock=[0, 0, 0])
        state.update(units={"mech": 100}, captures=threshold - 1)
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "raid",
                "key": target["id"],
                "army": {"mech": 50},
                "tactics": 0,
                "capture": True,
                "due": state["last"] + 1,
                "travel": 5,
                "loot": [0, 0, 0],
            }
        )
        game.save(db, state)
        game.tick(db, state, state["last"] + 1)
        updated = game.read(db, user)
        assert updated["_region_bonus"] == REGION_PRODUCTION_BONUS


def test_citadel_victory(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["hq"] = 3
        state["units"]["mech"] = 100
        game.save(db, state)
        citadel = next(
            town for town in game.world_outposts(db, 1) if town["name"] == "Zitadelle des Kerns"
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (user, 1, citadel["x"], citadel["y"], state["last"]),
        )
        town = citadel
    issue(world, "raid", {"key": town["id"], "army": {"mech": 100}, "capture": True})
    with game.transaction() as db:
        state = game.read(db, user)
        game.tick(db, state, state["last"] + 300)
        assert state["citadel"]
        assert next(q for q in game.quests(state) if q["id"] == "victory")["done"]


def test_quest_reward_once(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        for key in ("wood", "stone", "ore"):
            state["buildings"][key] = 2
        state["buildings"]["barracks"] = 1
        game.save(db, state)
    issue(world, "quest", {"key": "economy"})
    issue(world, "quest", {"key": "army"})
    with pytest.raises(RuleError):
        issue(world, "quest", {"key": "army"})


def test_directive_rewards_unlock_in_order_and_preserve_existing_claims(world):
    game, user = world
    order = ["economy", "army", "science", "expansion", "victory"]
    with game.transaction() as db:
        state = game.read(db, user)
        for key in ("wood", "stone", "ore"):
            state["buildings"][key] = 2
        state["buildings"]["barracks"] = 1
        state["tech"]["tactics"] = 1
        state["captures"] = 1
        state["citadel"] = True
        game.save(db, state)

        quests = game.quests(state)
        assert [quest["unlocked"] for quest in quests] == [True, False, False, False, False]
        with pytest.raises(RuleError, match="Belohnung noch nicht verfügbar"):
            game.command(db, user, "quest", {"key": "army"}, identity())

    for index, key in enumerate(order):
        result = issue(world, "quest", {"key": key})
        assert key in result["claimed"]
        with game.transaction() as db:
            quests = game.quests(game.read(db, user))
        assert [quest["unlocked"] for quest in quests] == [
            position <= index + 1 for position in range(len(order))
        ]

    with game.transaction() as db:
        state = game.read(db, user)
        state["claimed"] = ["army"]
        game.save(db, state)
        quests = game.quests(state)
        assert quests[0]["unlocked"] is True
        assert quests[1]["unlocked"] is False
    issue(world, "quest", {"key": "economy"})
    with game.transaction() as db:
        quests = game.quests(game.read(db, user))
    assert quests[1]["unlocked"] is True
    assert quests[2]["unlocked"] is True
    assert quests[3]["unlocked"] is False


def test_directive_reward_parallel_replay_is_credited_once(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        for key in ("wood", "stone", "ore"):
            state["buildings"][key] = 2
        game.save(db, state)

    token = identity()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _index: issue(world, "quest", {"key": "economy"}, token),
                range(8),
            )
        )

    assert all(result["claimed"].count("economy") == 1 for result in results)
    assert all(result["resources"] == results[0]["resources"] for result in results)


def test_quest_reward_overflow_is_preserved_in_reserve_and_claimed_once(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        for key in ("wood", "stone", "ore"):
            state["buildings"][key] = 2
        state["buildings"]["barracks"] = 1
        game.save(db, state)
    issue(world, "quest", {"key": "economy"})
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"] = [3900, 4000, 100]
        state["reserve"] = [0, 0, 0]
        game.save(db, state)
        result = game.command(db, user, "quest", {"key": "army"}, identity())
        assert result["resources"] == [4000, 4000, 400]
        assert result["reserve"] == [200, 300, 0]
        assert "army" in result["claimed"]
    with pytest.raises(RuleError, match="bereits abgeholt"):
        issue(world, "quest", {"key": "army"})


def test_resource_cap_and_polling_remainders(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["tech"]["engineering"] = 1
        other = json.loads(json.dumps(state))
        start = state["last"]
        for i in range(1, 31):
            game.produce(state, start + i)
        game.produce(other, start + 30)
        assert state["resources"] == other["resources"]
        game.produce(state, start + 100000)
        assert state["resources"] == [4000] * 3


def test_starting_resources_and_each_resource_production_formula(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        start = state["last"]
        assert state["resources"] == [1200, 1000, 800]
        assert [state["buildings"][key] for key in ("wood", "stone", "ore")] == [1, 1, 1]
        state["tech"]["engineering"] = 1
        game.produce(state, start + 1)
        assert state["resources"] == [1204, 1004, 804]
        assert state["carry"] == [60, 60, 60]
        game.produce(state, start + 2)
        assert state["resources"] == [1209, 1009, 809]
        assert state["carry"] == [20, 20, 20]


def test_delivery_overflow_is_claimable_and_never_exceeds_depot(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["storage"] = 1
        state["resources"] = [3900, 4000, 100]
        state["reserve"] = [0, 0, 0]
        game.save(db, state)
        game.systems.credit(db, user, [500, 50, 500], "Testlieferung", at=state["last"])
        credited = game.read(db, user)
        assert credited["resources"] == [4000, 4000, 600]
        assert credited["reserve"] == [400, 50, 0]
        credited["resources"][0] -= 150
        game.save(db, credited)
        claimed = game.command(db, user, "reserve_claim", {}, identity())
        assert claimed["resources"] == [4000, 4000, 600]
        assert claimed["reserve"] == [250, 50, 0]


def test_trade_has_ledger(world):
    game, _user = world
    result = issue(world, "trade", {"source": 0, "dest": 2, "amount": 100})
    assert result["resources"] == [1100, 1000, 850]
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM ledger").fetchone()[0] == 1


def test_overspend_and_invalid_army(world):
    game, user = world
    with game.transaction() as db:
        state = game.read(db, user)
        state["buildings"]["barracks"] = 1
        game.save(db, state)
        town = game.view(db, user)["world"][0]
    for army in ({"ranger": 16}, {"ranger": -2}, {"mech": True}, {"unknown": 1}, {}):
        with pytest.raises(RuleError):
            issue(world, "raid", {"key": town["id"], "army": army})
    with pytest.raises(RuleError):
        issue(world, "train", {"key": "ranger", "count": 100})


def test_already_captured_target_returns_army(world):
    game, user = world
    with game.transaction() as db:
        target = game.view(db, user)["world"][0]
    issue(world, "raid", {"key": target["id"], "army": {"ranger": 15}})
    with game.transaction() as db:
        towns = json.loads(db.execute("SELECT state FROM world").fetchone()[0])
        towns[0]["owner"] = "another-commander"
        game.save_world_outposts(db, 1, towns)
        state = game.read(db, user)
        game.tick(db, state, state["last"] + 300)
        assert state["units"]["ranger"] == 15
        assert state["captures"] == 0
        assert not state["jobs"]


def test_malformed_key_is_domain_error(world):
    with pytest.raises(RuleError):
        issue(world, "build", {"key": ["wood"]})


def test_production_is_partition_invariant_with_terrain_event_and_vacation(tmp_path):
    from copy import deepcopy

    game = Game(tmp_path / "interval.sqlite3")
    initial = {
        "last": 100,
        "vacation_until": 102,
        "resources": [0, 0, 0],
        "carry": [8, 8, 8],
        "buildings": {"wood": 0, "stone": 0, "ore": 0, "storage": 0},
        "tech": {"engineering": 0},
        "captures": 0,
        "terrain": "forest",
        "_events": [{"starts": 101, "ends": 106, "bonus": 1}],
    }
    combined, sliced = deepcopy(initial), deepcopy(initial)
    game.produce(combined, 107)
    for timestamp in range(101, 108):
        game.produce(sliced, timestamp)
    assert combined == sliced
    assert combined["resources"][1] == 9
    assert combined["carry"][1] == 15
    assert combined["carry_sub"][1] == 20


def test_live_event_migration_backfills_immutable_legacy_rules(tmp_path):
    database = tmp_path / "legacy-events.sqlite3"
    game = Game(database)
    with game.transaction() as db:
        db.execute(
            "INSERT INTO events(id,name,starts,ends,bonus,world_id) VALUES (?,?,?,?,?,?)",
            ("legacy-event", "Legacy event", 100, 1000, 25, 1),
        )
        db.execute("DROP TABLE live_event_rules")
        db.execute("ALTER TABLE events DROP COLUMN goal_score")
        db.execute("ALTER TABLE events DROP COLUMN end_bonus")
        db.execute("ALTER TABLE events DROP COLUMN end_starts")
        db.execute("ALTER TABLE events DROP COLUMN warning_hours")
        db.execute("DELETE FROM schema_versions WHERE version=100")
    upgraded = Game(database)
    with upgraded.transaction() as db:
        event = db.execute(
            "SELECT e.goal_score,e.end_starts,e.end_bonus,r.version,r.digest,r.source,r.snapshot "
            "FROM events e JOIN live_event_rules r ON r.event_id=e.id WHERE e.id=?",
            ("legacy-event",),
        ).fetchone()
        assert event["goal_score"] == 0
        assert event["end_starts"] == 1000
        assert event["end_bonus"] == 25
        assert event["version"] == "FUR-2-LIVE-2"
        assert len(event["digest"]) == 64
        assert event["source"] == "legacy_backfill"
        assert json.loads(event["snapshot"])["bonus"] == 25
        assert json.loads(event["snapshot"])["overlap_bonus_cap"] == 100


def test_overlapping_live_event_bonuses_are_capped_and_integrated_by_phase():
    events = [
        {
            "starts": 100,
            "ends": 200,
            "bonus": 80,
            "end_starts": 150,
            "end_bonus": 40,
        },
        {
            "starts": 120,
            "ends": 200,
            "bonus": 70,
            "end_starts": 180,
            "end_bonus": 100,
        },
    ]
    assert live_events.active_bonus_total(events, 125) == 100
    assert live_events.active_bonus_total(events, 160) == 100
    assert live_events.active_bonus_total(events, 190) == 100
    assert live_events.integrated_bonus_seconds(events, 100, 200) == 9600
    assert live_events.integrated_bonus_seconds(events, 130, 140) == 1000
    assert live_events.integrated_bonus_seconds(events, 200, 300) == 0


def test_live_event_end_phase_bonus_changes_integrated_production(world):
    game, user = world
    with game.transaction() as db:
        base = game.read(db, user)
    base["buildings"]["storage"] = 10000
    starts = int(base["last"])
    event = {
        "starts": starts,
        "ends": starts + 7200,
        "bonus": 20,
        "end_starts": starts + 3600,
        "end_bonus": 40,
    }
    ordinary = deepcopy(base)
    ordinary["_events"] = [{**event, "end_bonus": 20}]
    configured = deepcopy(base)
    configured["_events"] = [event]
    game.produce(ordinary, starts + 7200)
    game.produce(configured, starts + 7200)
    assert all(
        actual >= control for actual, control in zip(configured["resources"], ordinary["resources"])
    )
    assert any(
        actual > control for actual, control in zip(configured["resources"], ordinary["resources"])
    )
