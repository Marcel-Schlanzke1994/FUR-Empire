import pytest

from fur_empire.game import Game, RuleError, identity
from fur_empire.items import (
    ITEMS,
    RULES,
    claim_reserve,
    inventory,
    receive_reserved,
    reserve_incoming,
    return_cargo,
)


def test_generic_item_catalog_is_versioned_and_matches_fur3_item_classes():
    assert RULES.version == "FUR-ITEM-INVENTORY-1"
    assert {item.item_class for item in ITEMS.values()} == {
        "crafting_component",
        "repair_kit",
        "cosmetic_skin",
        "commander_badge",
        "loot_material",
        "research_artifact",
        "mission_consumable_pve",
        "prestige_token_non_purchasable",
    }


@pytest.mark.parametrize(
    "state",
    [
        {"item_inventory": {"unknown": 1}},
        {"item_inventory": {"repair_kit": -1}},
        {"item_inventory": {"repair_kit": 1.5}},
        {"item_inventory": {"repair_kit": True}},
        {"item_inventory": {"repair_kit": RULES.stack_limit + 1}},
        {
            "item_inventory": {"repair_kit": 1},
            "item_inbound": {"repair_kit": RULES.stack_limit + 1},
        },
        {"item_reserve": {"unknown": 1}},
    ],
)
def test_malformed_item_state_is_rejected(state):
    with pytest.raises(RuleError):
        inventory(state)


def test_incoming_item_reservation_converts_once_and_uses_bounded_stacks():
    target = {"item_inventory": {"repair_kit": 10}, "item_inbound": {}}
    reserve_incoming(target, {"repair_kit": 15, "loot_material": 5})
    assert target["item_inbound"] == {"repair_kit": 15, "loot_material": 5}
    receive_reserved(target, {"repair_kit": 15, "loot_material": 5})
    assert target["item_inventory"] == {
        "repair_kit": 25,
        "loot_material": 5,
    }
    assert target["item_inbound"] == {}
    with pytest.raises(RuleError):
        receive_reserved(target, {"repair_kit": 15})


def test_return_overflow_is_claimable_and_slot_limits_are_enforced():
    state = {
        "item_inventory": {"repair_kit": RULES.stack_limit - 5},
        "item_inbound": {},
        "item_reserve": {},
    }
    return_cargo(state, {"repair_kit": 12})
    assert state["item_inventory"]["repair_kit"] == RULES.stack_limit
    assert state["item_reserve"] == {"repair_kit": 7}
    state["item_inventory"]["repair_kit"] -= 4
    claim_reserve(state, "repair_kit", 4)
    assert state["item_inventory"]["repair_kit"] == RULES.stack_limit
    assert state["item_reserve"] == {"repair_kit": 3}


def test_new_item_stack_cannot_exceed_slot_capacity():
    state = {
        "item_inventory": {item_id: 1 for item_id in list(ITEMS)[: RULES.max_stack_types]},
        "item_inbound": {},
    }
    unheld_item = next(item_id for item_id in ITEMS if item_id not in state["item_inventory"])
    with pytest.raises(RuleError, match="Stapelplätze"):
        reserve_incoming(state, {unheld_item: 1})


def test_item_reserve_claim_command_is_idempotent_and_audited(tmp_path):
    game = Game(tmp_path / "items.sqlite3")
    user = identity()
    token = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'ItemOwner', 'unused')", (user,))
        game.create(db, user, "ItemOwner")
        state = game.read(db, user)
        state["item_reserve"] = {"repair_kit": 8}
        game.save(db, state)
    payload = {"item_id": "repair_kit", "amount": 3}
    with game.transaction() as db:
        claimed = game.command(db, user, "item_reserve_claim", payload, token)
    with game.transaction() as db:
        replayed = game.command(db, user, "item_reserve_claim", payload, token)
        assert replayed["item_inventory"]["repair_kit"] == 3
        assert replayed["item_reserve"]["repair_kit"] == 5
        assert claimed["item_inventory"]["repair_kit"] == 3
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='item_reserve_claim'", (user,)
            ).fetchone()[0]
            == 1
        )
