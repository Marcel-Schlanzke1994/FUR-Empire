"""Versioned, deterministic Terra alliance-attack rules and allocation helpers."""

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from .terrain import defense_with_terrain


def _load_rules(filename: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((Path(__file__).parent / "rules" / filename).read_text(encoding="utf-8")),
    )


RULESETS = {
    "FUR-3-TERRA-ACS-2": _load_rules("fur-3-terra-alliance-attacks-1.json"),
    "FUR-3-TERRA-ACS-3": _load_rules("fur-3-terra-alliance-attacks-3.json"),
}
SNAPSHOTS = {
    version: json.dumps(rules, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for version, rules in RULESETS.items()
}
DIGESTS = {
    version: "sha256:" + hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
    for version, snapshot in SNAPSHOTS.items()
}
RULES: dict[str, Any] = RULESETS["FUR-3-TERRA-ACS-2"]
VERSION = "FUR-3-TERRA-ACS-2"
SNAPSHOT = SNAPSHOTS[VERSION]
DIGEST = DIGESTS[VERSION]
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()
MINIMUM_MEMBERS = int(RULES["operation"]["minimum_members"])
MAXIMUM_MEMBERS = int(RULES["operation"]["maximum_members"])
ASSEMBLY_SECONDS = int(RULES["operation"]["assembly_seconds"])


def resolve(
    wings: list[dict[str, Any]],
    defenders: dict[str, int],
    *,
    neutral_tier: int | None = None,
    terrain: str = "plain",
    player_defense: int | None = None,
) -> dict[str, Any]:
    """Resolve one simultaneous allied volley with each member's own tactics."""
    from .game import UNITS

    if not MINIMUM_MEMBERS <= len(wings) <= MAXIMUM_MEMBERS:
        raise ValueError("invalid alliance attack participant count")
    if (neutral_tier is None) == (player_defense is None):
        raise ValueError("exactly one target defense mode is required")
    initial_armies = [dict(wing["army"]) for wing in wings]
    if any(
        unit not in UNITS or type(count) is not int or count < 0
        for army in initial_armies
        for unit, count in army.items()
    ):
        raise ValueError("invalid alliance attack army")
    army: dict[str, int] = {}
    for wing in wings:
        for unit, count in wing["army"].items():
            army[unit] = army.get(unit, 0) + count
    power = sum(
        sum(UNITS[unit]["power"] * count for unit, count in wing["army"].items())
        * (100 + 15 * int(wing["tactics"]))
        // 100
        for wing in wings
    )
    defender_power = sum(UNITS[unit]["power"] * count for unit, count in defenders.items())
    if neutral_tier is not None:
        defense = defense_with_terrain(55 * neutral_tier**2 + defender_power, terrain)
    else:
        defense = int(player_defense or 0)
    if defense < 1:
        raise ValueError("invalid alliance attack defense")
    victory = power > defense
    attacker_loss_percent = min(100, 10 + defense * 60 // max(1, power)) if victory else 100
    defender_loss_percent = 100 if victory else min(100, power * 70 // max(1, defense))
    survivors = [
        {
            unit: max(0, count - (count * attacker_loss_percent + 99) // 100)
            for unit, count in wing["army"].items()
        }
        for wing in wings
    ]
    defender_survivors = {
        unit: max(0, count - (count * defender_loss_percent + 99) // 100)
        for unit, count in defenders.items()
    }
    return {
        "power": power,
        "defense": defense,
        "victory": victory,
        "attacker_loss_percent": attacker_loss_percent,
        "defender_loss_percent": defender_loss_percent,
        "wing_survivors": survivors,
        "attacker_survivors": {
            unit: sum(wing.get(unit, 0) for wing in survivors) for unit in UNITS
        },
        "defender_survivors": defender_survivors,
    }


def allocate_amount(total: int, weights: list[int], tie_breakers: list[str]) -> list[int]:
    """Allocate an integer amount proportionally with deterministic largest remainders."""
    if (
        type(total) is not int
        or total < 0
        or len(weights) != len(tie_breakers)
        or any(type(weight) is not int or weight < 0 for weight in weights)
    ):
        raise ValueError("invalid alliance allocation")
    denominator = sum(weights)
    if not denominator:
        return [0] * len(weights)
    shares = [divmod(total * weight, denominator) for weight in weights]
    result = [whole for whole, _ in shares]
    order = sorted(range(len(weights)), key=lambda index: (-shares[index][1], tie_breakers[index]))
    for index in order[: total - sum(result)]:
        result[index] += 1
    return result
