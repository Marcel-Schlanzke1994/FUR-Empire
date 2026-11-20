"""Deterministic, lootbox-free item salvage from FUR-3 PvE expeditions."""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .expeditions import RULES as EXPEDITION_RULES
from .items import ITEMS
from .items import RULES as ITEM_RULES


class ItemDrop(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    item_id: str = Field(pattern=r"^[a-z0-9_]+$")
    eligible_outcomes: list[str] = Field(min_length=1, max_length=20)
    chance_basis_points: int = Field(ge=0, le=10000)
    max_per_mission: int = Field(ge=1, le=100)


class ItemDropRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    roll_space: int = Field(ge=1, le=1000000)
    drops: list[ItemDrop] = Field(min_length=1, max_length=100)


RULES = ItemDropRules.model_validate(
    json.loads((Path(__file__).parent / "rules" / "item-drops-1.json").read_text(encoding="utf-8"))
)
if RULES.roll_space != 10000:
    raise ValueError("FUR item-drop chance basis must use 10,000 rolls")
if len({drop.item_id for drop in RULES.drops}) != len(RULES.drops):
    raise ValueError("Duplicate expedition item-drop identifier")
OUTCOMES = {str(item["id"]) for item in EXPEDITION_RULES["outcomes"]}
if any(
    drop.item_id not in ITEMS
    or len(set(drop.eligible_outcomes)) != len(drop.eligible_outcomes)
    or not set(drop.eligible_outcomes) <= OUTCOMES
    or drop.chance_basis_points > RULES.roll_space
    for drop in RULES.drops
):
    raise ValueError("Invalid expedition item-drop rules")
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def _roll(seed: str, item_id: str) -> int:
    digest = hashlib.sha256(f"{RULES.version}\0{seed}\0item-drop:{item_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % RULES.roll_space


def validate_ruleset(version: str, rule_hash: str) -> None:
    if version != RULES.version or not hmac.compare_digest(rule_hash, RULE_HASH):
        raise ValueError("Unsupported expedition item-drop rules")


def resolve(seed: str, outcome: str, version: str, rule_hash: str) -> dict[str, Any]:
    """Repeatably roll each item once for a mission and enforce its per-mission cap."""
    if not seed or outcome not in OUTCOMES:
        raise ValueError("Invalid item-drop seed or expedition outcome")
    validate_ruleset(version, rule_hash)
    rolls: list[dict[str, Any]] = []
    for drop in RULES.drops:
        roll = _roll(seed, drop.item_id)
        eligible = outcome in drop.eligible_outcomes
        succeeded = eligible and roll < drop.chance_basis_points
        rolls.append(
            {
                "item_id": drop.item_id,
                "roll": roll,
                "eligible": eligible,
                "success": succeeded,
                "amount": drop.max_per_mission if succeeded else 0,
                "max_per_mission": drop.max_per_mission,
            }
        )
    return {
        "rules_version": RULES.version,
        "rules_hash": RULE_HASH,
        "outcome": outcome,
        "rolls": rolls,
    }


def view(enabled: bool = False) -> dict[str, Any]:
    total_weight = sum(int(outcome["weight"]) for outcome in EXPEDITION_RULES["outcomes"])
    outcome_weights = {
        str(outcome["id"]): int(outcome["weight"]) for outcome in EXPEDITION_RULES["outcomes"]
    }
    return {
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "enabled": enabled,
        "transport_weight": ITEM_RULES.transport_weight,
        "drops": [
            {
                **drop.model_dump(),
                "item_name": ITEMS[drop.item_id].name,
                "overall_chance_basis_points": (
                    sum(outcome_weights[outcome] for outcome in drop.eligible_outcomes)
                    * drop.chance_basis_points
                    // total_weight
                ),
            }
            for drop in RULES.drops
        ],
        "resource_loot_has_priority": True,
    }
