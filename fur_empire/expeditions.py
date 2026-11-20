"""Versioned deterministic FUR-3 frontier expedition outcomes."""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-expedition-v1.json").read_text(encoding="utf-8")
)
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
_OUTCOMES = tuple(RULES["outcomes"])
assert sum(int(item["weight"]) for item in _OUTCOMES) == int(RULES["outcome_rolls"])


def validate_ruleset(version: str, digest: str) -> None:
    """Reject an in-flight expedition if its exact immutable rules snapshot is unavailable."""
    if version != RULES["version"] or not hmac.compare_digest(digest, RULES_DIGEST):
        raise ValueError("Unsupported expedition rule snapshot")


def _draw(seed: str, label: str, upper: int) -> int:
    digest = hashlib.sha256(f"{RULES['version']}\0{seed}\0{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % upper


def resolve_expedition(seed: str, army: dict[str, int]) -> dict[str, Any]:
    """Resolve a single expedition repeatably; caller commits result transactionally."""
    if not seed or not army or any(type(count) is not int or count < 0 for count in army.values()):
        raise ValueError("Invalid expedition seed or army")
    roll = _draw(seed, "outcome", int(RULES["outcome_rolls"]))
    selected: dict[str, Any] | None = None
    edge = 0
    for outcome in _OUTCOMES:
        edge += int(outcome["weight"])
        if roll < edge:
            selected = outcome
            break
    assert selected is not None
    low_loss, high_loss = int(selected["loss_min_percent"]), int(selected["loss_max_percent"])
    loss_percent = low_loss + _draw(seed, "loss", high_loss - low_loss + 1)
    survivors = {
        unit: max(0, count - (count * loss_percent + 99) // 100) for unit, count in army.items()
    }
    minimum, maximum = int(selected["resource_min"]), int(selected["resource_max"])
    loot = [0, 0, 0]
    if maximum:
        resource = _draw(seed, "resource", 3)
        loot[resource] = minimum + _draw(seed, "amount", maximum - minimum + 1)
    return {
        "rules_version": str(RULES["version"]),
        "rules_digest": RULES_DIGEST,
        "outcome": str(selected["id"]),
        "roll": roll,
        "loss_percent": loss_percent,
        "survivors": survivors,
        "loot": loot,
    }
