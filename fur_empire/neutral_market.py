"""Original ten-good exchange, separate from the immutable FUR-2 catalog."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Good(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[a-z_]+$")
    name: str = Field(min_length=1, max_length=60)
    value: int = Field(ge=1, le=1000)
    description: str = Field(min_length=1, max_length=500)


class MarketRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    minimum_amount: int = Field(ge=1)
    maximum_amount: int = Field(ge=1)
    payout_percent: int = Field(ge=1, lt=100)
    syndicate_payout_percent: int = Field(ge=1, lt=100)
    goods: list[Good] = Field(min_length=10, max_length=10)


RULES = MarketRules.model_validate(
    json.loads(
        (Path(__file__).parent / "rules" / "neutral-market-1.json").read_text(encoding="utf-8")
    )
)
if (
    len({good.id for good in RULES.goods}) != 10
    or [good.id for good in RULES.goods[:3]] != ["wood", "stone", "ore"]
    or any(good.value != 1 for good in RULES.goods[:3])
    or RULES.minimum_amount > RULES.maximum_amount
):
    raise ValueError("Invalid neutral market catalog")
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
GOODS = {good.id: good for good in RULES.goods}
RESOURCE_IDS = ("wood", "stone", "ore")


def depot_capacity(state: dict[str, Any]) -> int:
    from .game import RuleError

    buildings = state.get("buildings")
    storage = buildings.get("storage") if isinstance(buildings, dict) else None
    if type(storage) is not int or not 0 <= storage <= 10:
        raise RuleError("Die Depotstufe dieser Kolonie ist ungültig.")
    return 2000 + 2000 * storage


def _goods_inventory(state: dict[str, Any]) -> dict[str, int]:
    """Validate the legacy colony-scoped material stacks before using them."""
    from .game import RuleError

    inventory = state.get("goods_inventory", {})
    if not isinstance(inventory, dict):
        raise RuleError("Das Warenlager dieser Kolonie ist ungültig.")
    capacity = depot_capacity(state)
    for item_id, amount in inventory.items():
        if not isinstance(item_id, str) or item_id not in GOODS or item_id in RESOURCE_IDS:
            raise RuleError("Das Warenlager enthält eine unbekannte Warenart.")
        if type(amount) is not int or amount < 0:
            raise RuleError("Der Warenbestand muss eine nichtnegative ganze Zahl sein.")
        if amount > capacity:
            raise RuleError("Der Warenbestand überschreitet das Depotlimit.")
    inbound = state.get("goods_inbound", {})
    if not isinstance(inbound, dict):
        raise RuleError("Die reservierte Warenfracht ist ungültig.")
    for item_id, amount in inbound.items():
        if (
            not isinstance(item_id, str)
            or item_id not in GOODS
            or item_id in RESOURCE_IDS
            or type(amount) is not int
            or amount < 0
            or int(inventory.get(item_id, 0)) + amount > capacity
        ):
            raise RuleError("Die reservierte Warenfracht überschreitet das Depotlimit.")
    reserve = state.get("goods_reserve", {})
    if not isinstance(reserve, dict):
        raise RuleError("Das Warenreserve-Lager ist ungültig.")
    for item_id, amount in reserve.items():
        if (
            not isinstance(item_id, str)
            or item_id not in GOODS
            or item_id in RESOURCE_IDS
            or type(amount) is not int
            or amount < 0
        ):
            raise RuleError("Das Warenreserve-Lager ist ungültig.")
    return inventory


def balances(state: dict[str, Any]) -> dict[str, int]:
    inventory = _goods_inventory(state)
    return {
        good.id: (
            int(state["resources"][RESOURCE_IDS.index(good.id)])
            if good.id in RESOURCE_IDS
            else int(inventory.get(good.id, 0))
        )
        for good in RULES.goods
    }


def payout_percent(state: dict[str, Any], faction: str) -> int:
    return (
        RULES.syndicate_payout_percent
        if state.get("faction_chosen") and faction == "syndicate"
        else RULES.payout_percent
    )


def market_view(state: dict[str, Any], faction: str) -> dict[str, Any]:
    stock = balances(state)
    material_ids = tuple(good_id for good_id in GOODS if good_id not in RESOURCE_IDS)
    stored_material_stacks = sum(stock[good_id] > 0 for good_id in material_ids)
    return {
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "payout_percent": payout_percent(state, faction),
        "minimum_amount": RULES.minimum_amount,
        "maximum_amount": RULES.maximum_amount,
        "capacity": depot_capacity(state),
        "material_stacks": {
            "used": stored_material_stacks,
            "available_types": len(material_ids),
        },
        "goods": [
            {
                **good.model_dump(),
                "amount": stock[good.id],
                "reserve_amount": int(state.get("goods_reserve", {}).get(good.id, 0)),
                "incoming_amount": int(state.get("goods_inbound", {}).get(good.id, 0)),
                "asset": f"/static/assets/goods/{good.id}.svg",
            }
            for good in RULES.goods
        ],
    }


def claim_reserve(state: dict[str, Any], item_id: object, amount: object) -> None:
    from .game import RuleError

    if (
        not isinstance(item_id, str)
        or item_id not in GOODS
        or item_id in RESOURCE_IDS
        or type(amount) is not int
        or amount < 1
    ):
        raise RuleError("Wähle eine gültige Materialware und Menge.")
    reserve = state.get("goods_reserve", {})
    if not isinstance(reserve, dict) or type(reserve.get(item_id, 0)) is not int:
        raise RuleError("Das Warenreserve-Lager ist ungültig.")
    available = int(reserve.get(item_id, 0))
    inventory = dict(_goods_inventory(state))
    if amount > available:
        raise RuleError("Nicht genügend Ware im Reserve-Lager.")
    if int(inventory.get(item_id, 0)) + int(
        state.get("goods_inbound", {}).get(item_id, 0)
    ) + amount > depot_capacity(state):
        raise RuleError("Im Depot ist nicht genug Platz für diese Ware.")
    inventory[item_id] = int(inventory.get(item_id, 0)) + amount
    reserve[item_id] = available - amount
    if reserve[item_id] == 0:
        reserve.pop(item_id)
    state["goods_inventory"] = inventory
    state["goods_reserve"] = reserve


def exchange(
    state: dict[str, Any], faction: str, source: object, destination: object, amount: object
) -> dict[str, Any]:
    """Validate before mutation. Caller commits inventory, ledger and command atomically."""
    from .game import RuleError

    if (
        not isinstance(source, str)
        or not isinstance(destination, str)
        or source not in GOODS
        or destination not in GOODS
        or source == destination
        or type(amount) is not int
        or not RULES.minimum_amount <= amount <= RULES.maximum_amount
    ):
        raise RuleError("Wähle zwei verschiedene Marktgüter und eine Menge von 10 bis 100.000.")
    before = balances(state)
    if before[source] < amount:
        raise RuleError("Nicht genügend Vorrat dieses Marktguts.")
    percent = payout_percent(state, faction)
    received = amount * GOODS[source].value * percent // (100 * GOODS[destination].value)
    if received < 1:
        raise RuleError("Diese Menge reicht nicht für eine Einheit des Zielguts.")
    cap = depot_capacity(state)
    reserved = int(state.get("goods_inbound", {}).get(destination, 0))
    remaining_destination = (
        before[source] - amount if source == destination else before[destination]
    )
    if remaining_destination + received + reserved > cap:
        raise RuleError("Das Depot ist für diesen Tausch zu klein.")
    after = dict(before)
    after[source] -= amount
    after[destination] += received
    inventory = dict(state.get("goods_inventory", {}))
    for key in (source, destination):
        if key in RESOURCE_IDS:
            state["resources"][RESOURCE_IDS.index(key)] = after[key]
        else:
            inventory[key] = after[key]
    state["goods_inventory"] = inventory
    return {
        "source": source,
        "destination": destination,
        "given": amount,
        "received": received,
        "payout_percent": percent,
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "before": before,
        "after": after,
    }
