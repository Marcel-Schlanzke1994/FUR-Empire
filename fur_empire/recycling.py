"""Versioned, deliberately loss-making salvage for eligible FUR-3 items."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .crafting import RECIPES as CRAFTING_RECIPES
from .items import ITEMS, return_cargo
from .items import inventory as item_inventory
from .neutral_market import GOODS, RESOURCE_IDS, _goods_inventory, depot_capacity


class RecyclingRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    item_id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    output_items: dict[str, int]
    output_goods: dict[str, int]


class RecyclingRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    max_units_per_command: int = Field(ge=1, le=1000)
    recipes: list[RecyclingRecipe] = Field(min_length=1, max_length=100)


RULES = RecyclingRules.model_validate(
    json.loads(
        (Path(__file__).parent / "rules" / "item-recycling-1.json").read_text(encoding="utf-8")
    )
)
RECIPES = {recipe.item_id: recipe for recipe in RULES.recipes}
if len(RECIPES) != len(RULES.recipes):
    raise ValueError("Duplicate recycling recipe item identifier")
for recipe in RULES.recipes:
    if (
        recipe.item_id not in ITEMS
        or not recipe.output_items
        or any(
            item_id not in ITEMS or type(amount) is not int or amount <= 0
            for item_id, amount in recipe.output_items.items()
        )
        or any(
            good_id not in GOODS
            or good_id in RESOURCE_IDS
            or type(amount) is not int
            or amount <= 0
            for good_id, amount in recipe.output_goods.items()
        )
        or (not recipe.output_goods and not recipe.output_items)
    ):
        raise ValueError(f"Invalid recycling recipe: {recipe.item_id}")
    producing_recipes = [
        craft for craft in CRAFTING_RECIPES.values() if craft.output.get(recipe.item_id, 0) > 0
    ]
    if not producing_recipes or not all(
        set(recipe.output_items) <= set(craft.items)
        and set(recipe.output_goods) <= set(craft.goods)
        and all(amount <= craft.items[item_id] for item_id, amount in recipe.output_items.items())
        and all(amount <= craft.goods[good_id] for good_id, amount in recipe.output_goods.items())
        and (
            any(amount < craft.items[item_id] for item_id, amount in recipe.output_items.items())
            or any(amount < craft.goods[good_id] for good_id, amount in recipe.output_goods.items())
        )
        for craft in producing_recipes
    ):
        raise ValueError(f"Recycling can create a profitable crafting loop: {recipe.item_id}")
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def recycle(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    from .game import RuleError

    item_id = payload.get("item_id")
    amount = payload.get("item_amount", 1)
    recipe = RECIPES.get(item_id) if isinstance(item_id, str) else None
    if recipe is None:
        raise RuleError("Dieser Gegenstand kann derzeit nicht zerlegt werden.")
    recycle_item_id = recipe.item_id
    if type(amount) is not int or not 1 <= amount <= RULES.max_units_per_command:
        raise RuleError(f"Wähle 1 bis {RULES.max_units_per_command} Gegenstände zum Zerlegen.")

    owned = item_inventory(state)
    if owned.get(recycle_item_id, 0) < amount:
        raise RuleError("Nicht genügend Gegenstände zum Zerlegen.")
    item_outputs = {key: value * amount for key, value in recipe.output_items.items()}
    goods_outputs = {key: value * amount for key, value in recipe.output_goods.items()}

    # All changes are performed on copies and assigned only after every catalog and
    # capacity check passes. The enclosing game command persists them atomically.
    next_items = dict(owned)
    next_items[recycle_item_id] -= amount
    next_items = {key: value for key, value in next_items.items() if value > 0}
    item_state = dict(state)
    item_state["item_inventory"] = next_items
    return_cargo(item_state, item_outputs)

    goods = dict(_goods_inventory(state))
    inbound = state.get("goods_inbound", {})
    reserve = dict(state.get("goods_reserve", {}))
    if not isinstance(inbound, dict):
        raise RuleError("Die reservierte Warenfracht ist ungültig.")
    capacity = depot_capacity(state)
    for good_id, output in goods_outputs.items():
        room = max(0, capacity - int(goods.get(good_id, 0)) - int(inbound.get(good_id, 0)))
        stored = min(room, output)
        goods[good_id] = int(goods.get(good_id, 0)) + stored
        overflow = output - stored
        if overflow:
            reserve[good_id] = int(reserve.get(good_id, 0)) + overflow

    state["item_inventory"] = item_state["item_inventory"]
    state["item_reserve"] = item_state.get("item_reserve", {})
    state["goods_inventory"] = goods
    state["goods_reserve"] = reserve
    item_inventory(state)
    _goods_inventory(state)
    return {
        "item_id": recycle_item_id,
        "amount": amount,
        "output_items": item_outputs,
        "output_goods": goods_outputs,
        "rules_version": RULES.version,
        "rules_hash": RULE_HASH,
    }


def view(state: dict[str, Any], enabled: bool) -> dict[str, Any]:
    inventory = item_inventory(state)
    return {
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "enabled": enabled,
        "recipes": [
            {
                **recipe.model_dump(),
                "available": enabled and inventory.get(recipe.item_id, 0) > 0,
            }
            for recipe in RULES.recipes
        ],
    }
