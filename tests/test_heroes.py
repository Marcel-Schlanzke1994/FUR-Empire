"""Regression coverage for opt-in, world-scoped Commander progression."""

import copy
import json
import os
from urllib.parse import quote

import pytest

from fur_empire import hero_doctrines, hero_respec, heroes
from fur_empire.contracts import Command
from fur_empire.game import Game, RuleError, identity


@pytest.fixture(params=["sqlite", "postgres"])
def hero_world(request, tmp_path, monkeypatch):
    clock = [1_800_000_000]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    postgres_admin = None
    schema = "hero_test_" + identity().replace("-", "")
    if request.param == "postgres":
        base = os.getenv("FUR_TEST_POSTGRES")
        if not base:
            pytest.skip("FUR_TEST_POSTGRES not configured")
        import psycopg
        from psycopg import sql

        postgres_admin = psycopg.connect(base, autocommit=True)
        postgres_admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        target = (
            base + ("?" if "?" not in base else "&") + "options=" + quote("-csearch_path=" + schema)
        )
    else:
        target = tmp_path / "heroes.sqlite3"
    game = Game(target)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Commander', 'unused')", (user,))
        game.create(db, user, "Commander")
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (user,))
        db.execute("UPDATE world_settings SET settings='{}' WHERE world_id=1")
    with game.transaction() as db:
        game.command(
            db,
            user,
            "world_update",
            {"world_id": 1, "hero_ruleset": heroes.RULES.version},
            identity(),
        )
    yield game, user, clock
    if postgres_admin:
        from psycopg import sql

        postgres_admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        postgres_admin.close()


def test_hero_rules_and_level_curve_are_bounded():
    assert heroes.RULES.version == "FUR-3-HERO-1"
    assert heroes.level_for_experience(0) == 1
    assert heroes.level_for_experience(99) == 1
    assert heroes.level_for_experience(100) == 2
    assert heroes.level_for_experience(299) == 2
    assert heroes.level_for_experience(300) == 3
    assert heroes.level_for_experience(heroes._xp_before(heroes.RULES.level_cap)) == 20
    assert heroes._xp_before(heroes.RULES.level_cap) == 19000


def test_hero_action_contract_is_strict():
    parsed = Command.model_validate(
        {
            "action": "hero_allocate",
            "payload": {"hero_stat": "economy"},
            "token": "hero-token-1",
        }
    )
    assert parsed.action == "hero_allocate"
    assert (
        Command.model_validate(
            {"action": "hero_respec", "payload": {}, "token": "hero-respec-token"}
        ).action
        == "hero_respec"
    )
    with pytest.raises(ValueError):
        Command.model_validate(
            {
                "action": "hero_respec",
                "payload": {"unexpected": "field"},
                "token": "hero-respec-extra",
            }
        )
    with pytest.raises(ValueError):
        Command.model_validate(
            {
                "action": "hero_allocate",
                "payload": {"hero_stat": "admin"},
                "token": "hero-token-2",
            }
        )


def test_commander_xp_is_pinned_world_scoped_and_exactly_once(hero_world):
    game, user, clock = hero_world
    with game.transaction() as db:
        assert heroes.view(db, user, 1)["enabled"] is True
        assert heroes.view(db, user, 2)["enabled"] is False
        job = {"id": "expedition-a", "kind": "expedition"}
        heroes.pin_job(db, 1, job)
        assert job["hero_rules_version"] == heroes.RULES.version
        assert job["hero_rules_hash"] == heroes.RULE_HASH
        assert heroes.award_job(db, user, 1, job, clock[0]) == 8
        assert heroes.award_job(db, user, 1, job, clock[0]) == 0
        assert heroes.award_job(db, user, 2, {"id": "legacy", "kind": "expedition"}, clock[0]) == 0
        assert heroes.view(db, user, 1)["experience"] == 8
        assert heroes.view(db, user, 2)["experience"] == 0
        event = db.execute(
            "SELECT source_kind,experience,rules_version,rules_hash "
            "FROM commander_hero_xp_events WHERE user_id=?",
            (user,),
        ).fetchone()
        assert (event["source_kind"], event["experience"]) == ("expedition", 8)
        assert event["rules_version"] == heroes.RULES.version
        assert event["rules_hash"] == heroes.RULE_HASH
        assert (
            db.execute(
                "SELECT count(*) FROM commander_hero_xp_events WHERE user_id=?", (user,)
            ).fetchone()[0]
            == 1
        )


def test_commander_mission_progress_skill_allocation_and_economy_stat(hero_world):
    game, user, clock = hero_world
    with game.transaction() as db:
        player = game.read(db, user)
        player["units"]["ranger"] = 5
        player["last"] = clock[0]
        game.save(db, player)
        target = next(post for post in game.world_outposts(db, 1) if post["owner"] is None)
    with game.transaction() as db:
        dispatched = game.command(
            db,
            user,
            "expedition",
            {"key": target["id"], "army": {"ranger": 5}},
            identity(),
        )
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "expedition")
    assert mission["hero_rules_version"] == heroes.RULES.version
    clock[0] = mission["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        commander = game.view(db, user)["commander"]
        assert commander["experience"] == 8
        assert commander["level"] == 1
        assert commander["experience_to_next"] == 92
        colony_json = db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=1", (user,)
        ).fetchone()["state"]
        assert "commander" not in json.loads(colony_json)

    with game.transaction() as db:
        db.execute(
            "UPDATE commander_heroes SET experience=100 WHERE user_id=? AND world_id=1", (user,)
        )
        before_allocation = game.read(db, user)
        allocated = game.command(
            db,
            user,
            "hero_allocate",
            {"hero_stat": "economy"},
            identity(),
        )
        assert allocated["commander"]["skill_points"] == 0
        assert allocated["commander"]["stats"]["economy"] == 1
        colony = game.read(db, user)
        no_bonus, with_bonus = copy.deepcopy(before_allocation), copy.deepcopy(colony)
        for sample in (no_bonus, with_bonus):
            sample["resources"] = [0, 0, 0]
            sample["last"] = clock[0]
            sample["carry"] = [0, 0, 0]
            sample["carry_sub"] = [0, 0, 0]
        game.produce(no_bonus, clock[0] + 100)
        game.produce(with_bonus, clock[0] + 100)
        assert with_bonus["resources"][0] > no_bonus["resources"][0]

    with game.transaction() as db, pytest.raises(RuleError, match="Skillpunkt"):
        game.command(
            db,
            user,
            "hero_allocate",
            {"hero_stat": "economy"},
            identity(),
        )


def test_unimplemented_commander_stats_cannot_consume_skill_points(hero_world):
    game, user, _ = hero_world
    with game.transaction() as db:
        db.execute(
            "INSERT INTO commander_heroes(user_id,world_id,experience,created,updated) "
            "VALUES (?,1,100,0,0)",
            (user,),
        )
        before = heroes.view(db, user, 1)
        with pytest.raises(RuleError, match="FUR-3-Doktrinen"):
            game.command(
                db,
                user,
                "hero_allocate",
                {"hero_stat": "military"},
                identity(),
            )
        after = heroes.view(db, user, 1)
        assert after["skill_points"] == before["skill_points"] == 1
        assert after["stats"] == before["stats"]


def test_doctrine_rules_are_capped_and_opt_in_world_scoped(hero_world):
    game, user, _ = hero_world
    with game.transaction() as db:
        db.execute(
            "INSERT INTO commander_heroes(user_id,world_id,experience,military,economy,recon,command,created,updated) "
            "VALUES (?,1,19000,10,10,10,10,0,0)",
            (user,),
        )
        commander = {"stats": {"economy": 10, "military": 10, "recon": 10, "command": 10}}
        assert hero_doctrines.bonuses(commander["stats"], enabled=False) == {
            "production_percent": 0,
            "combat_damage_percent": 0,
            "intel_lifetime_percent": 0,
            "mission_slots": 0,
        }
        enabled = game.command(
            db,
            user,
            "world_update",
            {"world_id": 1, "hero_doctrine_ruleset": hero_doctrines.RULES.version},
            identity(),
        )
        doctrine = enabled["commander_doctrines"]
        assert doctrine["enabled"] is True
        assert doctrine["bonuses"] == {
            "production_percent": 20,
            "combat_damage_percent": 20,
            "intel_lifetime_percent": 100,
            "mission_slots": 5,
        }
        assert game.read(db, user)["commander"]["available_stats"] == list(heroes.RULES.stats)
        pinned = {"id": "hero-doctrine-job", "kind": "attack"}
        hero_doctrines.pin_job(db, 1, commander, pinned)
        assert hero_doctrines.pinned_bonuses(pinned) == doctrine["bonuses"]
        assert hero_doctrines.combat_modifier(pinned) == 120
        assert hero_doctrines.intel_lifetime_seconds(pinned) == 7200
        assert hero_doctrines.pinned_bonuses({"kind": "attack"})["combat_damage_percent"] == 0
        with pytest.raises(ValueError, match="unsupported pinned"):
            hero_doctrines.pinned_bonuses({**pinned, "hero_doctrine_rules_hash": "0" * 64})


def test_commander_doctrine_stat_allocation_requires_both_world_opt_ins(hero_world):
    game, user, _ = hero_world
    with game.transaction() as db, pytest.raises(RuleError, match="FUR-3-Doktrinen"):
        db.execute(
            "INSERT INTO commander_heroes(user_id,world_id,experience,created,updated) "
            "VALUES (?,1,100,0,0)",
            (user,),
        )
        game.command(db, user, "hero_allocate", {"hero_stat": "military"}, identity())
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({heroes.RULES.enabled_key: heroes.RULES.version}),),
        )
        with pytest.raises(RuleError, match="Doktrinen"):
            game.command(db, user, "hero_allocate", {"hero_stat": "military"}, identity())
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (
                json.dumps(
                    {
                        heroes.RULES.enabled_key: heroes.RULES.version,
                        hero_doctrines.RULES.enabled_key: hero_doctrines.RULES.version,
                    }
                ),
            ),
        )
        result = game.command(db, user, "hero_allocate", {"hero_stat": "military"}, identity())
        assert result["commander"]["stats"]["military"] == 1


def test_commander_respec_costs_points_cooldown_and_xp_replay_protection(hero_world):
    game, user, clock = hero_world
    with game.transaction() as db:
        db.execute(
            "UPDATE commander_heroes SET experience=300,military=1,economy=1 "
            "WHERE user_id=? AND world_id=1",
            (user,),
        )
        game.command(
            db,
            user,
            "world_update",
            {
                "world_id": 1,
                "hero_doctrine_ruleset": hero_doctrines.RULES.version,
                "hero_respec_ruleset": hero_respec.RULES.version,
            },
            identity(),
        )
        xp_job = {"id": "respec-xp-source", "kind": "attack"}
        heroes.pin_job(db, 1, xp_job)
        assert heroes.award_job(db, user, 1, xp_job, clock[0]) == 12
        db.execute(
            "UPDATE commander_heroes SET experience=300,military=1,economy=1 "
            "WHERE user_id=? AND world_id=1",
            (user,),
        )

    with game.transaction() as db:
        before = game.view(db, user)
        assert before["commander_respec"]["enabled"] is True
        assert before["commander_respec"]["cost"] == {"wood": 250, "stone": 250, "ore": 250}
        result = game.command(db, user, "hero_respec", {}, "hero-respec-first")
        assert result["resources"] == [950, 750, 550]
        assert result["commander"]["experience"] == 300
        assert result["commander"]["skill_points"] == 2
        assert result["commander"]["stats"] == {
            "military": 0,
            "economy": 0,
            "recon": 0,
            "command": 0,
        }
        assert result["commander_respec"]["available_at"] == clock[0] + 7 * 86400
        assert heroes.award_job(db, user, 1, xp_job, clock[0]) == 0
        assert (
            db.execute(
                "SELECT count(*) FROM commander_hero_xp_events WHERE user_id=?", (user,)
            ).fetchone()[0]
            == 1
        )
        replay = game.command(db, user, "hero_respec", {}, "hero-respec-first")
        assert replay["resources"] == result["resources"]
        assert replay["commander"]["skill_points"] == 2

    with game.transaction() as db:
        game.command(db, user, "hero_allocate", {"hero_stat": "economy"}, "hero-after-reset")
    with game.transaction() as db, pytest.raises(RuleError, match="Abklingzeit"):
        game.command(db, user, "hero_respec", {}, "hero-respec-too-soon")
    clock[0] += 7 * 86400
    with game.transaction() as db:
        second = game.command(db, user, "hero_respec", {}, "hero-respec-after-cooldown")
        assert second["commander"]["stats"]["economy"] == 0
        assert second["commander"]["skill_points"] == 2
        assert second["commander"]["experience"] == 300


def test_commander_respec_rejects_disabled_world_and_insufficient_funds_without_mutation(
    hero_world,
):
    game, user, _ = hero_world
    with game.transaction() as db:
        heroes._ensure(db, user, 1, 1_800_000_000)
        db.execute(
            "UPDATE commander_heroes SET experience=100,economy=1 WHERE user_id=? AND world_id=1",
            (user,),
        )
        state = game.read(db, user)
        state["resources"] = [0, 0, 0]
        game.save(db, state)
        with pytest.raises(RuleError, match="nicht aktiviert"):
            game.command(db, user, "hero_respec", {}, "hero-respec-disabled")
        game.command(
            db,
            user,
            "world_update",
            {"world_id": 1, "hero_respec_ruleset": hero_respec.RULES.version},
            "hero-respec-enable",
        )
        before = game.view(db, user)
        with pytest.raises(RuleError, match="fehlen Rohstoffe"):
            game.command(db, user, "hero_respec", {}, "hero-respec-poor")
        after = game.view(db, user)
        assert after["resources"] == before["resources"] == [0, 0, 0]
        assert after["commander"]["stats"] == before["commander"]["stats"]
        assert after["commander_respec"]["last_respec_at"] is None


def test_commander_respec_schema_migrates_existing_hero_without_data_loss(hero_world):
    game, user, _ = hero_world
    with game.transaction() as db:
        heroes._ensure(db, user, 1, 1_800_000_000)
        db.execute(
            "UPDATE commander_heroes SET experience=300,economy=2 WHERE user_id=? AND world_id=1",
            (user,),
        )
        db.execute("ALTER TABLE commander_heroes DROP COLUMN last_respec_at")
        db.execute("DELETE FROM schema_versions WHERE version=95")

    migrated = Game(game.path)
    with migrated.transaction() as db:
        row = db.execute(
            "SELECT experience,economy,last_respec_at FROM commander_heroes "
            "WHERE user_id=? AND world_id=1",
            (user,),
        ).fetchone()
        assert row["experience"] == 300
        assert row["economy"] == 2
        assert row["last_respec_at"] is None
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 123


def test_commander_allocation_is_rejected_without_opt_in(hero_world):
    game, user, _ = hero_world
    with game.transaction() as db:
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps({}),))
        with pytest.raises(RuleError, match="nicht aktiviert"):
            game.command(
                db,
                user,
                "hero_allocate",
                {"hero_stat": "economy"},
                identity(),
            )
