"""FUR-3-only versioned recipes using escrowed colony goods and generic items."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .items import (
    ITEMS,
    inventory,
    release_incoming,
    reserve_incoming,
    return_cargo,
)
from .items import (
    RULES as ITEM_RULES,
)
from .neutral_market import (
    GOODS,
    RESOURCE_IDS,
    _goods_inventory,
    depot_capacity,
)


class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    min_hq: int = Field(ge=1, le=10)
    duration_seconds: int = Field(ge=1, le=604800)
    resources: dict[str, int]
    goods: dict[str, int]
    items: dict[str, int]
    output: dict[str, int]


class CraftingRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    max_batches_per_job: int = Field(ge=1, le=100)
    max_active_jobs: int = Field(ge=1, le=20)
    recipes: list[Recipe] = Field(min_length=1, max_length=100)


RULES = CraftingRules.model_validate(
    json.loads((Path(__file__).parent / "rules" / "crafting-1.json").read_text(encoding="utf-8"))
)
RECIPES = {recipe.id: recipe for recipe in RULES.recipes}
if len(RECIPES) != len(RULES.recipes):
    raise ValueError("Duplicate crafting recipe identifier")
for recipe in RULES.recipes:
    invalid_resource = any(
        key not in RESOURCE_IDS or type(amount) is not int or amount <= 0
        for key, amount in recipe.resources.items()
    )
    invalid_good = any(
        key not in GOODS or key in RESOURCE_IDS or type(amount) is not int or amount <= 0
        for key, amount in recipe.goods.items()
    )
    invalid_input = any(
        key not in ITEMS or type(amount) is not int or amount <= 0
        for key, amount in recipe.items.items()
    )
    invalid_output = not recipe.output or any(
        key not in ITEMS or type(amount) is not int or amount <= 0
        for key, amount in recipe.output.items()
    )
    if invalid_resource or invalid_good or invalid_input or invalid_output:
        raise ValueError(f"Invalid crafting recipe: {recipe.id}")
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def enabled_in_world(db: Any, world_id: int) -> bool:
    from .game import RuleError

    row = db.execute("SELECT settings FROM world_settings WHERE world_id=?", (world_id,)).fetchone()
    if not row:
        return False
    try:
        settings = json.loads(row["settings"] or "{}")
    except (TypeError, ValueError) as exc:
        raise RuleError("Die FUR-3-Welteinstellungen sind ungültig.") from exc
    if not isinstance(settings, dict):
        raise RuleError("Die FUR-3-Welteinstellungen sind ungültig.")
    ruleset = settings.get("crafting_ruleset", "FUR-2")
    if ruleset not in ("FUR-2", RULES.version):
        raise RuleError("Der gespeicherte Fertigungsregelstand ist ungültig.")
    return bool(ruleset == RULES.version)


def _scaled(inputs: dict[str, int], batches: int) -> dict[str, int]:
    return {key: amount * batches for key, amount in inputs.items()}


def _exact_amounts(value: object, expected: dict[str, int]) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == set(expected)
        and all(
            type(value[key]) is int and value[key] == amount for key, amount in expected.items()
        )
    )


def _recipe(recipe_id: object) -> Recipe:
    from .game import RuleError

    if not isinstance(recipe_id, str) or recipe_id not in RECIPES:
        raise RuleError("Dieses Rezept ist nicht verfügbar.")
    return RECIPES[recipe_id]


def start(state: dict[str, Any], payload: dict[str, Any], now: int) -> dict[str, Any]:
    from .game import RuleError, identity

    recipe = _recipe(payload.get("recipe_id"))
    batches = payload.get("batches", 1)
    if type(batches) is not int or not 1 <= batches <= RULES.max_batches_per_job:
        raise RuleError(f"Wähle 1 bis {RULES.max_batches_per_job} Fertigungsdurchläufe.")
    active = sum(job.get("kind") == "craft" for job in state.get("jobs", []))
    if active >= RULES.max_active_jobs:
        raise RuleError("Die Fertigungsschlange ist voll.")
    if int(state.get("buildings", {}).get("hq", 0)) < recipe.min_hq:
        raise RuleError(f"Dieses Rezept benötigt Hauptquartier-Stufe {recipe.min_hq}.")
    resources = _scaled(recipe.resources, batches)
    goods = _scaled(recipe.goods, batches)
    item_inputs = _scaled(recipe.items, batches)
    output = _scaled(recipe.output, batches)
    balances = _goods_inventory(state)
    item_balances = inventory(state)
    for resource_id, amount in resources.items():
        if state["resources"][RESOURCE_IDS.index(resource_id)] < amount:
            raise RuleError("Nicht genügend Rohstoffe für dieses Rezept.")
    if any(balances.get(good_id, 0) < amount for good_id, amount in goods.items()):
        raise RuleError("Nicht genügend Marktgüter für dieses Rezept.")
    if any(item_balances.get(item_id, 0) < amount for item_id, amount in item_inputs.items()):
        raise RuleError("Nicht genügend Gegenstände für dieses Rezept.")
    reserve_incoming(state, output)
    for resource_id, amount in resources.items():
        state["resources"][RESOURCE_IDS.index(resource_id)] -= amount
    goods_inventory = dict(_goods_inventory(state))
    for good_id, amount in goods.items():
        goods_inventory[good_id] = int(goods_inventory.get(good_id, 0)) - amount
    state["goods_inventory"] = goods_inventory
    item_inventory = dict(item_balances)
    for item_id, amount in item_inputs.items():
        item_inventory[item_id] = int(item_inventory.get(item_id, 0)) - amount
    state["item_inventory"] = item_inventory
    job = {
        "id": identity(),
        "kind": "craft",
        "recipe_id": recipe.id,
        "rules_version": RULES.version,
        "rules_hash": RULE_HASH,
        "item_rules_version": ITEM_RULES.version,
        "batches": batches,
        "duration": recipe.duration_seconds * batches,
        "due": now + recipe.duration_seconds * batches,
        "inputs": {"resources": resources, "goods": goods, "items": item_inputs},
        "output": output,
        "label": recipe.name,
    }
    state.setdefault("jobs", []).append(job)
    return job


def _job_contract(job: dict[str, Any]) -> tuple[Recipe, int]:
    from .game import RuleError

    recipe = _recipe(job.get("recipe_id"))
    batches = job.get("batches")
    expected_inputs = {
        "resources": _scaled(recipe.resources, batches) if type(batches) is int else {},
        "goods": _scaled(recipe.goods, batches) if type(batches) is int else {},
        "items": _scaled(recipe.items, batches) if type(batches) is int else {},
    }
    actual_inputs = job.get("inputs")
    inputs_valid = bool(
        isinstance(actual_inputs, dict)
        and set(actual_inputs) == {"resources", "goods", "items"}
        and all(_exact_amounts(actual_inputs[key], expected_inputs[key]) for key in expected_inputs)
    )
    if (
        job.get("rules_version") != RULES.version
        or job.get("rules_hash") != RULE_HASH
        or job.get("item_rules_version") != ITEM_RULES.version
        or type(batches) is not int
        or not 1 <= batches <= RULES.max_batches_per_job
        or job.get("duration") != recipe.duration_seconds * batches
        or type(job.get("due")) is not int
        or not inputs_valid
        or not _exact_amounts(
            job.get("output"), _scaled(recipe.output, batches) if type(batches) is int else {}
        )
    ):
        raise RuleError("Der gespeicherte Fertigungsauftrag besitzt ungültige Regeln oder Fracht.")
    return recipe, batches


def complete(state: dict[str, Any], job: dict[str, Any], now: int) -> dict[str, int]:
    from .game import RuleError

    _job_contract(job)
    if int(job["due"]) > now:
        raise RuleError("Der Fertigungsauftrag ist noch nicht fällig.")
    output = dict(job["output"])
    release_incoming(state, output)
    inventory_now = dict(inventory(state))
    for item_id, amount in output.items():
        inventory_now[item_id] = int(inventory_now.get(item_id, 0)) + amount
    state["item_inventory"] = inventory_now
    inventory(state)
    return output


def cancel(state: dict[str, Any], job_id: object, now: int) -> dict[str, Any]:
    from .game import RuleError

    if not isinstance(job_id, str):
        raise RuleError("Fertigungsauftrag nicht gefunden.")
    job = next(
        (
            item
            for item in state.get("jobs", [])
            if item.get("id") == job_id and item.get("kind") == "craft"
        ),
        None,
    )
    if not job:
        raise RuleError("Dieser Fertigungsauftrag kann nicht sicher abgebrochen werden.")
    recipe, _ = _job_contract(job)
    if int(job["due"]) <= now:
        raise RuleError("Ein fälliger Fertigungsauftrag kann nicht mehr abgebrochen werden.")
    inputs = job["inputs"]
    refund_resources = inputs.get("resources", {})
    refund_goods = inputs.get("goods", {})
    refund_items = inputs.get("items", {})
    output = job.get("output", {})
    if not all(
        isinstance(value, dict) for value in (refund_resources, refund_goods, refund_items, output)
    ):
        raise RuleError("Der Fertigungsauftrag enthält ungültige Rückbuchungsdaten.")
    release_incoming(state, output)
    cap = depot_capacity(state)
    resource_reserve = state.setdefault("reserve", [0, 0, 0])
    for resource_id, amount in refund_resources.items():
        if resource_id not in RESOURCE_IDS or type(amount) is not int or amount < 0:
            raise RuleError("Die Rohstofferstattung des Fertigungsauftrags ist ungültig.")
        index = RESOURCE_IDS.index(resource_id)
        room = max(0, cap - state["resources"][index])
        restored = min(room, amount)
        state["resources"][index] += restored
        resource_reserve[index] += amount - restored
    goods_inventory = dict(_goods_inventory(state))
    goods_reserve = dict(state.get("goods_reserve", {}))
    goods_inbound = dict(state.get("goods_inbound", {}))
    for good_id, amount in refund_goods.items():
        if good_id not in GOODS or good_id in RESOURCE_IDS or type(amount) is not int or amount < 0:
            raise RuleError("Die Warenrückerstattung des Fertigungsauftrags ist ungültig.")
        room = max(
            0,
            cap - int(goods_inventory.get(good_id, 0)) - int(goods_inbound.get(good_id, 0)),
        )
        restored = min(room, amount)
        goods_inventory[good_id] = int(goods_inventory.get(good_id, 0)) + restored
        overflow = amount - restored
        if overflow:
            goods_reserve[good_id] = int(goods_reserve.get(good_id, 0)) + overflow
    state["goods_inventory"] = goods_inventory
    state["goods_reserve"] = goods_reserve
    return_cargo(state, refund_items)
    state["jobs"] = [item for item in state["jobs"] if item.get("id") != job_id]
    return {
        "resources": dict(refund_resources),
        "goods": dict(refund_goods),
        "items": dict(refund_items),
        "recipe_id": recipe.id,
        "job_id": job_id,
    }


def view(state: dict[str, Any], enabled: bool = False) -> dict[str, Any]:
    balances = _goods_inventory(state)
    item_balances = inventory(state)
    active_jobs = sum(job.get("kind") == "craft" for job in state.get("jobs", []))
    return {
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "enabled": enabled,
        "max_active_jobs": RULES.max_active_jobs,
        "active_jobs": active_jobs,
        "recipes": [
            {
                **recipe.model_dump(),
                "available": (
                    enabled
                    and int(state.get("buildings", {}).get("hq", 0)) >= recipe.min_hq
                    and all(
                        state["resources"][RESOURCE_IDS.index(key)] >= amount
                        for key, amount in recipe.resources.items()
                    )
                    and all(balances.get(key, 0) >= amount for key, amount in recipe.goods.items())
                    and all(
                        item_balances.get(key, 0) >= amount for key, amount in recipe.items.items()
                    )
                    and active_jobs < RULES.max_active_jobs
                ),
            }
            for recipe in RULES.recipes
        ],
    }
