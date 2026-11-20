"""Phase-B regressions prepared in Phase A; do not execute before the global gate."""

import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from fur_empire.game import Game, RuleError, identity
from fur_empire.neutral_market import (
    GOODS,
    RULE_HASH,
    RULES,
    balances,
    exchange,
    market_view,
)


@pytest.fixture
def market_world(tmp_path, monkeypatch):
    now = int(time.time())
    monkeypatch.setattr("fur_empire.game.time.time", lambda: now)
    game = Game(tmp_path / "neutral-market.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Merchant', 'unused')", (user,))
        game.create(db, user, "Merchant")
    return game, user


def dispatch(game, user, source, destination, amount=100, token=None):
    with game.transaction() as db:
        return game.command(
            db,
            user,
            "goods_trade",
            {"goods_source": source, "goods_destination": destination, "amount": amount},
            token or identity(),
        )


def test_ten_goods_share_stock_and_value_losing_round_trip(market_world):
    game, user = market_world
    for key in list(GOODS)[3:]:
        bought = dispatch(game, user, "wood", key, 40)
        assert bought["goods_inventory"][key] == 20 // GOODS[key].value
    state = dispatch(game, user, "wood", "textiles", 100)
    before = state["resources"][0]
    sold = dispatch(game, user, "textiles", "wood", 10)
    assert sold["resources"][0] == before + 20
    assert len(sold["neutral_market"]["goods"]) == 10
    assert sold["neutral_market"]["rule_hash"] == RULE_HASH


def test_syndicate_rate_requires_committed_faction_choice(market_world):
    game, user = market_world
    with game.transaction() as db:
        state = game.read(db, user)
        unchosen = market_view(state, "syndicate")
        assert unchosen["payout_percent"] == 50
        state["faction_chosen"] = True
        game.save(db, state)
        db.execute(
            "UPDATE world_players SET faction='syndicate' WHERE user_id=? AND world_id=1", (user,)
        )
    result = dispatch(game, user, "wood", "stone", 100)
    assert result["resources"][:2] == [1100, 1060]


@pytest.mark.parametrize(
    "source,destination,amount",
    [
        ("wood", "wood", 10),
        ("fake", "ore", 10),
        ("wood", "ore", True),
        ("wood", "ore", -10),
        ("wood", "ore", 9),
        ("wood", "ore", 100001),
        ("wood", "circuits", 10),
        ("alloy", "wood", 10),
    ],
)
def test_invalid_exchange_has_no_effect(market_world, source, destination, amount):
    game, user = market_world
    with game.transaction() as db:
        before = game.read(db, user)
    with pytest.raises(RuleError):
        dispatch(game, user, source, destination, amount)
    with game.transaction() as db:
        assert game.read(db, user) == before
        assert db.execute("SELECT count(*) FROM neutral_goods_trades").fetchone()[0] == 0


def test_capacity_rejection_is_before_any_debit(market_world):
    game, user = market_world
    with game.transaction() as db:
        state = game.read(db, user)
        state["goods_inventory"] = {"textiles": 4000}
        game.save(db, state)
    with pytest.raises(RuleError, match="Depot"):
        dispatch(game, user, "wood", "textiles", 100)
    with game.transaction() as db:
        assert game.read(db, user)["resources"][0] == 1200


def test_reserved_inbound_goods_preserve_depot_room_and_can_be_claimed(market_world):
    game, user = market_world
    with game.transaction() as db:
        state = game.read(db, user)
        state["goods_inbound"] = {"alloy": 3998}
        game.save(db, state)
    with pytest.raises(RuleError, match="Depot"):
        dispatch(game, user, "wood", "alloy", 100)
    with game.transaction() as db:
        state = game.read(db, user)
        assert state["resources"][0] == 1200
        state["goods_inbound"] = {}
        state["goods_reserve"] = {"alloy": 12}
        game.save(db, state)
    with game.transaction() as db:
        claimed = game.command(
            db,
            user,
            "goods_reserve_claim",
            {"good_id": "alloy", "amount": 8},
            identity(),
        )
    assert claimed["goods_inventory"]["alloy"] == 8
    assert claimed["neutral_market"]["goods"][3]["reserve_amount"] == 4


def test_concurrent_retry_one_trade_and_immutable_receipt(market_world):
    game, user = market_world
    token = identity()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: dispatch(game, user, "wood", "alloy", 100, token), range(4)))
    with game.transaction() as db:
        state = game.read(db, user)
        assert state["resources"][0] == 1100
        assert state["goods_inventory"]["alloy"] == 4
        rows = db.execute("SELECT * FROM neutral_goods_trades WHERE owner=?", (user,)).fetchall()
        assert len(rows) == 1
        receipt = json.loads(rows[0]["details"])
        assert receipt["before"]["alloy"] == 0
        assert receipt["after"]["alloy"] == 4
        assert receipt["rule_hash"] == RULE_HASH
        assert rows[0]["colony_id"] == state["colony_id"]
        assert rows[0]["world_id"] == state["world_id"]
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM neutral_goods_trades WHERE owner=?", (user,))
    with pytest.raises(RuleError, match="Befehlsschlüssel"):
        dispatch(game, user, "wood", "stone", 100, token)
    restarted = Game(game.path)
    with restarted.transaction() as db:
        assert restarted.read(db, user)["goods_inventory"]["alloy"] == 4


def test_new_goods_are_colony_local_and_legacy_balances_stay_three(market_world):
    game, user = market_world
    result = dispatch(game, user, "wood", "alloy", 100)
    with game.transaction() as db:
        rival = identity()
        db.execute("INSERT INTO users VALUES (?, 'OtherMerchant', 'unused')", (rival,))
        game.create(db, rival, "OtherMerchant")
        other = game.view(db, rival)
        assert (
            next(g for g in other["neutral_market"]["goods"] if g["id"] == "alloy")["amount"] == 0
        )
        assert len(other["resources"]) == len(result["resources"]) == 3


def test_material_inventory_reports_occupied_catalog_stacks(market_world):
    game, user = market_world
    with game.transaction() as db:
        initial = game.view(db, user)["neutral_market"]
        assert initial["material_stacks"] == {"used": 0, "available_types": 7}
    dispatch(game, user, "wood", "alloy", 100)
    with game.transaction() as db:
        after_first = game.view(db, user)["neutral_market"]
        assert after_first["material_stacks"] == {"used": 1, "available_types": 7}
    dispatch(game, user, "wood", "circuits", 100)
    with game.transaction() as db:
        after_second = game.view(db, user)["neutral_market"]
        assert after_second["material_stacks"] == {"used": 2, "available_types": 7}


@pytest.mark.parametrize(
    "inventory",
    [
        {"unknown_relic": 1},
        {"alloy": -1},
        {"alloy": 1.5},
        {"alloy": 2001},
        {"wood": 1},
        None,
    ],
)
def test_malformed_goods_inventory_is_rejected_without_mutation(inventory):
    state = {
        "resources": [1200, 1000, 800],
        "buildings": {"storage": 0},
        "goods_inventory": inventory,
    }
    before = json.loads(json.dumps(state))
    with pytest.raises(RuleError):
        balances(state)
    with pytest.raises(RuleError):
        exchange(state, "pioneers", "wood", "alloy", 100)
    assert state == before


def test_every_pair_reduces_value_and_pure_invalid_input_does_not_mutate():
    for source in GOODS:
        for destination in GOODS:
            if source == destination:
                continue
            state = {
                "resources": [2000, 2000, 2000],
                "buildings": {"storage": 10},
                "faction_chosen": True,
                "goods_inventory": {key: 2000 for key in list(GOODS)[3:]},
            }
            result = exchange(state, "syndicate", source, destination, 100)
            assert result["received"] * GOODS[destination].value <= 60 * GOODS[source].value
            assert result["version"] == RULES.version
