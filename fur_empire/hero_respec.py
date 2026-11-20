"""Opt-in, versioned Commander respec rules for FUR-3-HERO-3."""

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import heroes
from .database import Connection


class RespecRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    balance_status: Literal["draft"]
    enabled_key: str
    cooldown_seconds: int = Field(ge=86400, le=90 * 86400)
    cost: dict[str, int]


RULES = RespecRules.model_validate(
    json.loads((Path(__file__).parent / "rules" / "hero-respec-1.json").read_text(encoding="utf-8"))
)
RESOURCES = ("wood", "stone", "ore")
if set(RULES.cost) != set(RESOURCES) or any(
    type(value) is not int or value < 1 or value > 100_000 for value in RULES.cost.values()
):
    raise ValueError("Invalid FUR Commander respec cost")


def enabled_in_world(db: Connection, world_id: int) -> bool:
    row = db.execute("SELECT settings FROM world_settings WHERE world_id=?", (world_id,)).fetchone()
    if not row:
        return False
    try:
        settings = json.loads(row["settings"] or "{}")
    except (TypeError, ValueError):
        return False
    return (
        isinstance(settings, dict)
        and settings.get(heroes.RULES.enabled_key) == heroes.RULES.version
        and settings.get(RULES.enabled_key) == RULES.version
    )


def view(db: Connection, user_id: str, world_id: int) -> dict[str, Any]:
    row = db.execute(
        "SELECT last_respec_at,military,economy,recon,command FROM commander_heroes "
        "WHERE user_id=? AND world_id=?",
        (user_id, world_id),
    ).fetchone()
    last_respec_at = (
        int(row["last_respec_at"]) if row and row["last_respec_at"] is not None else None
    )
    return {
        "enabled": enabled_in_world(db, world_id),
        "rules_version": RULES.version,
        "balance_status": RULES.balance_status,
        "cooldown_seconds": RULES.cooldown_seconds,
        "last_respec_at": last_respec_at,
        "available_at": last_respec_at + RULES.cooldown_seconds if last_respec_at else 0,
        "cost": dict(RULES.cost),
        "has_allocated_stats": bool(row and any(int(row[key]) for key in heroes.RULES.stats)),
    }


def reset(db: Connection, state: dict[str, Any], now: int) -> None:
    """Charge the active colony and return spent points without changing XP history."""
    from .game import RuleError

    user_id, world_id = str(state["id"]), int(state["world_id"])
    if not enabled_in_world(db, world_id):
        raise RuleError("Der Commander-Reset ist in dieser Welt nicht aktiviert.")
    row = db.execute(
        "SELECT last_respec_at,military,economy,recon,command FROM commander_heroes "
        "WHERE user_id=? AND world_id=?",
        (user_id, world_id),
    ).fetchone()
    if not row:
        raise RuleError("Es gibt noch keine Commander-Attribute zum Zurücksetzen.")
    if not any(int(row[key]) for key in heroes.RULES.stats):
        raise RuleError("Es sind keine Commander-Attribute verteilt.")
    last_respec_at = row["last_respec_at"]
    if last_respec_at is not None and now < int(last_respec_at) + RULES.cooldown_seconds:
        raise RuleError("Der Commander-Reset ist noch in der Abklingzeit.")
    cost = [RULES.cost[key] for key in RESOURCES]
    resources = state.get("resources")
    if (
        not isinstance(resources, list)
        or len(resources) != len(cost)
        or any(type(value) is not int for value in resources)
        or any(have < price for have, price in zip(resources, cost))
    ):
        raise RuleError("Für den Commander-Reset fehlen Rohstoffe.")
    updated = db.execute(
        "UPDATE commander_heroes SET military=0,economy=0,recon=0,command=0,"
        "last_respec_at=?,updated=? WHERE user_id=? AND world_id=? "
        "AND (last_respec_at IS NULL OR last_respec_at<=?)",
        (now, now, user_id, world_id, now - RULES.cooldown_seconds),
    ).cursor.rowcount
    if updated != 1:
        raise RuleError("Der Commander-Reset konnte nicht sicher ausgeführt werden.")
    state["resources"] = [have - price for have, price in zip(resources, cost)]
