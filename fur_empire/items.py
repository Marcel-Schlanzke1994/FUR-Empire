"""Versioned generic colony item stacks, separate from the ten-goods market."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ItemDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    item_class: str = Field(alias="class", pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)


class ItemInventoryRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    max_stack_types: int = Field(ge=1, le=100)
    stack_limit: int = Field(ge=1, le=1000000)
    reserve_limit: int = Field(ge=1, le=1000000000)
    transport_weight: int = Field(ge=1, le=1000)
    items: list[ItemDefinition] = Field(min_length=1, max_length=100)


RULES = ItemInventoryRules.model_validate(
    json.loads(
        (Path(__file__).parent / "rules" / "item-inventory-1.json").read_text(encoding="utf-8")
    )
)
ITEMS = {item.id: item for item in RULES.items}
if len(ITEMS) != len(RULES.items):
    raise ValueError("Duplicate generic item identifier")


def inventory(state: dict[str, Any]) -> dict[str, int]:
    """Validate owned stacks and all pending incoming reservations for this colony."""
    from .game import RuleError

    stacks = state.get("item_inventory", {})
    inbound = state.get("item_inbound", {})
    if not isinstance(stacks, dict) or not isinstance(inbound, dict):
        raise RuleError("Das Gegenstandsinventar dieser Kolonie ist ungültig.")
    reserve = state.get("item_reserve", {})
    if not isinstance(reserve, dict):
        raise RuleError("Das Gegenstandsreservelager ist ungültig.")
    for item_id, amount in reserve.items():
        if (
            not isinstance(item_id, str)
            or item_id not in ITEMS
            or type(amount) is not int
            or amount < 0
            or amount > RULES.reserve_limit
        ):
            raise RuleError("Das Gegenstandsreservelager ist ungültig.")
    for label, collection in (("Inventar", stacks), ("Reservierung", inbound)):
        for item_id, amount in collection.items():
            if (
                not isinstance(item_id, str)
                or item_id not in ITEMS
                or type(amount) is not int
                or amount < 0
                or amount > RULES.stack_limit
            ):
                raise RuleError(f"{label} enthält einen ungültigen Gegenstandsstapel.")
    for item_id, amount in inbound.items():
        if int(stacks.get(item_id, 0)) + amount > RULES.stack_limit:
            raise RuleError("Eine Eingangsreservierung überschreitet das Stapellimit.")
    occupied = _occupied_types(stacks, inbound)
    if len(occupied) > RULES.max_stack_types:
        raise RuleError("Die Eingangsreservierung überschreitet die Inventarplätze.")
    return stacks


def reserve_incoming(target: dict[str, Any], items: dict[str, int]) -> dict[str, int]:
    stacks = inventory(target)
    inbound = dict(target.get("item_inbound", {}))
    if any(
        not isinstance(item_id, str)
        or item_id not in ITEMS
        or type(amount) is not int
        or amount <= 0
        for item_id, amount in items.items()
    ):
        from .game import RuleError

        raise RuleError("Die Gegenstandsfracht ist ungültig.")
    for item_id, amount in items.items():
        if int(stacks.get(item_id, 0)) + int(inbound.get(item_id, 0)) + amount > RULES.stack_limit:
            from .game import RuleError

            raise RuleError("Das Stapellimit des Zielinventars reicht nicht aus.")
        inbound[item_id] = int(inbound.get(item_id, 0)) + amount
    occupied = _occupied_types(stacks, inbound)
    if len(occupied) > RULES.max_stack_types:
        from .game import RuleError

        raise RuleError("Im Zielinventar sind nicht genug Stapelplätze frei.")
    target["item_inbound"] = inbound
    return dict(items)


def _occupied_types(stacks: dict[str, int], inbound: dict[str, int]) -> set[str]:
    return {
        item_id
        for item_id in ITEMS
        if int(stacks.get(item_id, 0)) > 0 or int(inbound.get(item_id, 0)) > 0
    }


def release_incoming(state: dict[str, Any], items: dict[str, int]) -> None:
    inventory(state)
    inbound = dict(state.get("item_inbound", {}))
    for item_id, amount in items.items():
        if type(amount) is not int or amount < 0 or int(inbound.get(item_id, 0)) < amount:
            from .game import RuleError

            raise RuleError("Die Gegenstandsreservierung fehlt oder ist ungültig.")
        remaining = int(inbound.get(item_id, 0)) - amount
        if remaining:
            inbound[item_id] = remaining
        else:
            inbound.pop(item_id, None)
    state["item_inbound"] = inbound
    # Validate the resulting occupied-slot count after releasing reservation.
    inventory(state)


def receive_reserved(state: dict[str, Any], items: dict[str, int]) -> None:
    release_incoming(state, items)
    stacks = dict(state.get("item_inventory", {}))
    for item_id, amount in items.items():
        stacks[item_id] = int(stacks.get(item_id, 0)) + amount
    state["item_inventory"] = stacks
    inventory(state)


def return_cargo(state: dict[str, Any], items: dict[str, int]) -> None:
    from .game import RuleError

    stacks = dict(inventory(state))
    reserve = dict(state.get("item_reserve", {}))
    if not isinstance(state.get("item_reserve", {}), dict):
        raise RuleError("Das Gegenstandsreservelager ist ungültig.")
    for item_id, amount in items.items():
        if item_id not in ITEMS or type(amount) is not int or amount < 0:
            raise RuleError("Die zurückkehrende Gegenstandsfracht ist ungültig.")
        occupied = sum(value > 0 for value in stacks.values())
        room = max(0, RULES.stack_limit - int(stacks.get(item_id, 0)))
        if int(stacks.get(item_id, 0)) == 0 and occupied >= RULES.max_stack_types:
            room = 0
        stored = min(room, amount)
        if stored:
            stacks[item_id] = int(stacks.get(item_id, 0)) + stored
        overflow = amount - stored
        if overflow:
            total_reserve = int(reserve.get(item_id, 0)) + overflow
            if total_reserve > RULES.reserve_limit:
                raise RuleError("Das Gegenstandsreservelager ist voll.")
            reserve[item_id] = total_reserve
    state["item_inventory"] = stacks
    state["item_reserve"] = reserve


def claim_reserve(state: dict[str, Any], item_id: object, amount: object) -> None:
    from .game import RuleError

    if (
        not isinstance(item_id, str)
        or item_id not in ITEMS
        or type(amount) is not int
        or amount < 1
    ):
        raise RuleError("Wähle einen gültigen Gegenstand und eine Menge.")
    reserve = state.get("item_reserve", {})
    inventory(state)
    available = reserve.get(item_id, 0)
    if type(available) is not int or amount > available:
        raise RuleError("Nicht genügend Gegenstände im Reserve-Lager.")
    stacks = dict(inventory(state))
    if int(stacks.get(item_id, 0)) + amount > RULES.stack_limit:
        raise RuleError("Das Stapellimit reicht für diese Reserveabholung nicht aus.")
    if (
        int(stacks.get(item_id, 0)) == 0
        and sum(value > 0 for value in stacks.values()) >= RULES.max_stack_types
    ):
        raise RuleError("Im Inventar ist kein Stapelplatz frei.")
    stacks[item_id] = int(stacks.get(item_id, 0)) + amount
    reserve[item_id] = available - amount
    if reserve[item_id] == 0:
        reserve.pop(item_id)
    state["item_inventory"] = stacks
    state["item_reserve"] = reserve


def view(state: dict[str, Any]) -> dict[str, Any]:
    stacks = inventory(state)
    reserve = state.get("item_reserve", {})
    inbound = state.get("item_inbound", {})
    if not isinstance(reserve, dict):
        from .game import RuleError

        raise RuleError("Das Gegenstandsreservelager ist ungültig.")
    return {
        "version": RULES.version,
        "max_stack_types": RULES.max_stack_types,
        "stack_limit": RULES.stack_limit,
        "used_stack_types": len(_occupied_types(stacks, inbound)),
        "items": [
            {
                **item.model_dump(by_alias=True),
                "amount": int(stacks.get(item.id, 0)),
                "incoming_amount": int(inbound.get(item.id, 0)),
                "reserve_amount": int(reserve.get(item.id, 0)),
            }
            for item in RULES.items
        ],
    }
