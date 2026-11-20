"""Conservative projections for explicitly shared alliance combat summaries."""

import hashlib
import json
from pathlib import Path
from typing import Any, cast

RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-report-sharing-1.json").read_text(encoding="utf-8")
)
RULES_DIGEST = hashlib.sha256(
    json.dumps(RULES, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
VERSION = str(RULES["version"])
MAX_ROUNDS = 6
MAX_UNIT_COUNT = 1_000_000


def _total(mapping: Any) -> int:
    if not isinstance(mapping, dict):
        raise TypeError("Combat report side is invalid")
    total = 0
    for count in mapping.values():
        if type(count) is not int:
            raise TypeError("Combat report count is invalid")
        if count < 0 or count > MAX_UNIT_COUNT:
            raise ValueError("Combat report count is invalid")
        total += count
    return total


def project_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return only owner-side totals; never copy identifiers or raw report text."""
    combat = report.get("combat")
    owner = report.get("share_owner")
    if not isinstance(owner, dict) or owner.get("allowed") is not True:
        raise ValueError("Combat report has no safe owner-specific sharing perspective")
    side = owner.get("side")
    wing_index = owner.get("wing_index")
    if side not in ("attacker", "defender", "attacker_wing"):
        raise ValueError("Combat report owner side is invalid")
    if side == "attacker_wing" and (type(wing_index) is not int or wing_index < 0):
        raise ValueError("Combat report owner wing is invalid")
    owner_wing_index = cast(int, wing_index) if side == "attacker_wing" else None
    rounds = combat.get("rounds") if isinstance(combat, dict) else None
    if not isinstance(rounds, list):
        raise TypeError("Combat report rounds are invalid")
    if not 1 <= len(rounds) <= MAX_ROUNDS:
        raise ValueError("Only bounded combat reports can be shared")
    projection: list[dict[str, int | str]] = []
    for index, battle_round in enumerate(rounds, start=1):
        if not isinstance(battle_round, dict):
            raise TypeError("Combat report round is invalid")
        if type(battle_round.get("victory")) is not bool:
            raise ValueError("Combat report round is invalid")
        if side == "attacker_wing":
            wings = battle_round.get("attacker_wings")
            if (
                not isinstance(wings, list)
                or owner_wing_index is None
                or owner_wing_index >= len(wings)
            ):
                raise TypeError("Combat report owner wing is unavailable")
            owner_stacks = wings[owner_wing_index]
            is_victory = battle_round.get("victory")
        else:
            owner_stacks = battle_round.get(side)
            is_victory = battle_round.get("victory")
            if side == "defender" and type(is_victory) is bool:
                is_victory = not is_victory
        if not isinstance(owner_stacks, dict):
            raise TypeError("Combat report owner side is invalid")
        round_number = battle_round.get("round", index)
        if type(round_number) is not int:
            raise TypeError("Combat report round number is invalid")
        if not 1 <= round_number <= MAX_ROUNDS:
            raise ValueError("Combat report round number is invalid")
        if type(is_victory) is not bool:
            raise ValueError("Combat report outcome is invalid")
        projection.append(
            {
                "number": round_number,
                "outcome": "victory" if is_victory else "defeat",
                "own_losses": _total(owner_stacks.get("losses", {})),
                "own_survivors": _total(owner_stacks.get("survivors", {})),
            }
        )
    return {"outcome": projection[-1]["outcome"], "rounds": projection}
