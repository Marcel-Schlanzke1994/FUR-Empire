import pytest

from fur_empire.contracts import Command
from fur_empire.crafting import RECIPES, RULES
from fur_empire.game import Game, RuleError, identity
from fur_empire.recycling import RULES as RECYCLING_RULES


@pytest.fixture
def crafting_world(tmp_path, monkeypatch):
    now = 1_800_000_000
    monkeypatch.setattr("fur_empire.game.time.time", lambda: now)
    game = Game(tmp_path / "crafting.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Crafter', 'unused')", (user,))
        game.create(db, user, "Crafter")
        state = game.read(db, user)
        state["resources"] = [5000, 5000, 5000]
        state["buildings"]["hq"] = 2
        state["goods_inventory"] = {
            "alloy": 500,
            "circuits": 500,
            "textiles": 500,
            "rations": 500,
        }
        state["item_inventory"] = {"crafting_component": 100}
        state["last"] = now
        game.save(db, state)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            ('{"crafting_ruleset":"FUR-CRAFTING-1"}',),
        )
    return game, user, [now]


def craft(game, user, payload, token=None):
    with game.transaction() as db:
        return game.command(db, user, "craft_start", payload, token or identity())


def update_world(game, user, **settings):
    with game.transaction() as db:
        game.command(db, user, "world_update", {"world_id": 1, **settings}, identity())
        return game.view(db, user)


def test_recipe_catalog_is_versioned_and_outputs_registered_items():
    assert RULES.version == "FUR-CRAFTING-1"
    assert set(RECIPES) == {"component_press", "field_repair_kit"}
    assert all(
        set(recipe.output) <= {"crafting_component", "repair_kit"} for recipe in RECIPES.values()
    )


def test_crafting_requires_admin_world_opt_in_and_cannot_disable_with_active_jobs(crafting_world):
    game, user, clock = crafting_world
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (user,))
        db.execute("UPDATE world_settings SET settings='{}' WHERE world_id=1")
        assert game.view(db, user)["crafting"]["enabled"] is False
        with pytest.raises(RuleError, match="nicht aktiviert"):
            game.command(
                db,
                user,
                "craft_start",
                {"recipe_id": "component_press", "batches": 1},
                identity(),
            )
    enabled = update_world(game, user, crafting_ruleset=RULES.version)
    assert enabled["active_world"]["crafting_ruleset"] == RULES.version
    started = craft(game, user, {"recipe_id": "component_press", "batches": 1})
    job = next(job for job in started["jobs"] if job["kind"] == "craft")
    with pytest.raises(RuleError, match="laufenden Fertigungsaufträge"):
        update_world(game, user, crafting_ruleset="FUR-2")
    clock[0] = job["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
    disabled = update_world(game, user, crafting_ruleset="FUR-2")
    assert disabled["active_world"]["crafting_ruleset"] == "FUR-2"
    assert (
        next(world for world in disabled["worlds"] if world["id"] == 1)["crafting_ruleset"]
        == "FUR-2"
    )


def test_recycling_is_versioned_loss_making_and_opted_in():
    assert RECYCLING_RULES.version == "FUR-ITEM-RECYCLING-1"
    recipe = RECYCLING_RULES.recipes[0]
    # A repair kit recipe consumes 3 components and 6 textiles; recycling returns
    # only 2 components and 3 textiles, so neither input can produce a net gain.
    assert recipe.item_id == "repair_kit"
    assert recipe.output_items == {"crafting_component": 2}
    assert recipe.output_goods == {"textiles": 3}
    kit_recipe = RECIPES["field_repair_kit"]
    assert recipe.output_items["crafting_component"] < kit_recipe.items["crafting_component"]
    assert recipe.output_goods["textiles"] < kit_recipe.goods["textiles"]


def test_recycling_is_atomic_audited_and_idempotent_with_reserve_overflow(crafting_world):
    game, user, _ = crafting_world
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (user,))
        state = game.read(db, user)
        state["buildings"]["storage"] = 0
        state["item_inventory"] = {"repair_kit": 3, "crafting_component": 999}
        state["goods_inventory"]["textiles"] = 1999
        game.save(db, state)
    payload = {"item_id": "repair_kit", "item_amount": 2}
    token = identity()
    with game.transaction() as db:
        recycled = game.command(db, user, "item_recycle", payload, token)
        assert recycled["item_inventory"] == {"repair_kit": 1, "crafting_component": 1000}
        assert recycled["item_reserve"]["crafting_component"] == 3
        assert recycled["goods_inventory"]["textiles"] == 2000
        assert recycled["goods_reserve"]["textiles"] == 5
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='item_recycle'", (user,)
            ).fetchone()[0]
            == 1
        )
    with game.transaction() as db:
        replayed = game.command(db, user, "item_recycle", payload, token)
        assert replayed["item_inventory"] == {"repair_kit": 1, "crafting_component": 1000}
        assert replayed["item_reserve"]["crafting_component"] == 3
        assert replayed["goods_reserve"]["textiles"] == 5
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='item_recycle'", (user,)
            ).fetchone()[0]
            == 1
        )


def test_recycling_rejects_disabled_rules_and_insufficient_items(crafting_world):
    game, user, _ = crafting_world
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (user,))
        state = game.read(db, user)
        state["item_inventory"] = {"repair_kit": 1}
        game.save(db, state)
    update_world(game, user, crafting_ruleset="FUR-2")
    with game.transaction() as db, pytest.raises(RuleError, match="nicht aktiviert"):
        game.command(
            db,
            user,
            "item_recycle",
            {"item_id": "repair_kit", "item_amount": 1},
            identity(),
        )
    update_world(game, user, crafting_ruleset=RULES.version)
    with game.transaction() as db, pytest.raises(RuleError, match="Nicht genügend Gegenstände"):
        game.command(
            db,
            user,
            "item_recycle",
            {"item_id": "repair_kit", "item_amount": 2},
            identity(),
        )


def test_crafting_and_recycling_are_reachable_through_strict_api_contract():
    craft_command = Command.model_validate(
        {
            "action": "craft_start",
            "payload": {"recipe_id": "component_press", "batches": 1},
            "token": identity(),
        }
    )
    recycle_command = Command.model_validate(
        {
            "action": "item_recycle",
            "payload": {"item_id": "repair_kit", "item_amount": 1},
            "token": identity(),
        }
    )
    assert craft_command.action == "craft_start"
    assert recycle_command.action == "item_recycle"


def test_crafting_escrows_inputs_reserves_output_and_completes_once(crafting_world):
    game, user, clock = crafting_world
    token = identity()
    payload = {"recipe_id": "component_press", "batches": 2}
    started = craft(game, user, payload, token)
    job = next(job for job in started["jobs"] if job["kind"] == "craft")
    assert job["duration"] == 600
    assert started["resources"][2] == 4800
    assert started["goods_inventory"]["alloy"] == 460
    assert started["goods_inventory"]["circuits"] == 484
    assert started["item_inventory"]["crafting_component"] == 100
    assert started["item_inbound"]["crafting_component"] == 8
    replay = craft(game, user, payload, token)
    assert sum(job["kind"] == "craft" for job in replay["jobs"]) == 1
    clock[0] = job["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        completed = game.read(db, user)
        assert completed["item_inventory"]["crafting_component"] == 108
        assert completed["item_inbound"] == {}
        assert completed["jobs"] == []
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='craft_completed'", (user,)
            ).fetchone()[0]
            == 1
        )
        assert game.view(db, user)["crafting"]["enabled"]
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='craft_started'", (user,)
            ).fetchone()[0]
            == 1
        )
        game.advance(db, clock[0])
        assert game.read(db, user)["item_inventory"]["crafting_component"] == 108


def test_craft_cancel_refunds_all_escrow_and_releases_output_reservation(crafting_world):
    game, user, clock = crafting_world
    payload = {"recipe_id": "field_repair_kit", "batches": 2}
    started = craft(game, user, payload)
    job = next(job for job in started["jobs"] if job["kind"] == "craft")
    assert started["item_inventory"]["crafting_component"] == 94
    assert started["item_inbound"]["repair_kit"] == 2
    with game.transaction() as db:
        canceled = game.command(db, user, "cancel_job", {"key": job["id"]}, identity())
    assert canceled["item_inventory"]["crafting_component"] == 100
    assert canceled["item_inbound"] == {}
    assert canceled["goods_inventory"]["textiles"] == 500
    assert canceled["goods_inventory"]["rations"] == 500
    assert canceled["jobs"] == []
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='craft_cancelled'", (user,)
            ).fetchone()[0]
            == 1
        )
        clock[0] = job["due"]
        with pytest.raises(RuleError, match="Bau- oder Forschungsauftrag"):
            game.command(db, user, "cancel_job", {"key": job["id"]}, identity())


@pytest.mark.parametrize(
    "payload",
    [
        {"recipe_id": "missing_recipe", "batches": 1},
        {"recipe_id": "component_press", "batches": True},
        {"recipe_id": "component_press", "batches": 0},
        {"recipe_id": "component_press", "batches": 11},
        {"recipe_id": "field_repair_kit", "batches": 1},
    ],
)
def test_invalid_or_locked_recipe_has_no_debit(crafting_world, payload):
    game, user, _ = crafting_world
    if payload["recipe_id"] == "field_repair_kit":
        with game.transaction() as db:
            state = game.read(db, user)
            state["buildings"]["hq"] = 1
            game.save(db, state)
    with game.transaction() as db:
        before = game.read(db, user)
    with pytest.raises(RuleError):
        craft(game, user, payload)
    with game.transaction() as db:
        after = game.read(db, user)
        assert after["resources"] == before["resources"]
        assert after.get("goods_inventory", {}) == before.get("goods_inventory", {})
        assert after.get("item_inventory", {}) == before.get("item_inventory", {})
        assert after["jobs"] == before["jobs"]


def test_insufficient_input_and_output_stack_capacity_reject_without_mutation(crafting_world):
    game, user, _ = crafting_world
    with game.transaction() as db:
        state = game.read(db, user)
        state["goods_inventory"]["alloy"] = 0
        game.save(db, state)
    with pytest.raises(RuleError, match="Nicht genügend Marktgüter"):
        craft(game, user, {"recipe_id": "component_press", "batches": 1})
    with game.transaction() as db:
        state = game.read(db, user)
        state["goods_inventory"]["alloy"] = 500
        state["item_inventory"] = {"repair_kit": 1000}
        state["item_inbound"] = {"repair_kit": 0}
        state["jobs"] = []
        game.save(db, state)
        before = game.read(db, user)
        with pytest.raises(RuleError):
            game.command(
                db,
                user,
                "craft_start",
                {"recipe_id": "field_repair_kit", "batches": 1},
                identity(),
            )
    with game.transaction() as db:
        after = game.read(db, user)
        assert after["item_inventory"] == before["item_inventory"]
        assert after["jobs"] == before["jobs"]


def test_craft_cancel_refunds_overflow_without_losing_any_inputs(crafting_world):
    game, user, _ = crafting_world
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"][2] = 2000
        state["goods_inventory"]["alloy"] = 4000
        state["goods_inventory"]["circuits"] = 4000
        state["item_inventory"] = {"cosmetic_skin": 1000}
        state["item_reserve"] = {"research_artifact": 5}
        game.save(db, state)
    started = craft(game, user, {"recipe_id": "component_press", "batches": 1})
    job = next(job for job in started["jobs"] if job["kind"] == "craft")
    assert started["item_reserve"] == {"research_artifact": 5}
    with game.transaction() as db:
        state = game.read(db, user)
        state["resources"][2] = 4000
        state["goods_inventory"]["alloy"] = 4000
        state["goods_inventory"]["circuits"] = 4000
        game.save(db, state)
    canceled = None
    with game.transaction() as db:
        canceled = game.command(db, user, "cancel_job", {"key": job["id"]}, identity())
    assert canceled["resources"][2] == 4000
    assert canceled["reserve"][2] >= 100
    assert canceled["goods_inventory"]["alloy"] == 4000
    assert canceled["goods_reserve"]["alloy"] >= 20
    assert canceled["goods_reserve"]["circuits"] >= 8
    assert canceled["item_inventory"] == {"cosmetic_skin": 1000}
    assert canceled["item_reserve"]["research_artifact"] == 5
