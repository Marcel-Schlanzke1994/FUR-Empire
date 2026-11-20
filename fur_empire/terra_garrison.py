"""Versioned rules for separately owned allied defensive garrisons."""

import hashlib
import json
from pathlib import Path
from typing import Any

_raw = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-allied-garrisons-1.json").read_text(encoding="utf-8")
)
RULES: dict[str, Any] = _raw
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()
MAX_CAPACITY = int(RULES["capacity_units_per_home_colony"])


def validate_rules(rules: dict[str, Any]) -> None:
    """Reject incompatible or unsafe rule snapshots during startup and tests."""
    if rules.get("version") != VERSION:
        raise ValueError("unsupported allied garrison rules version")
    if rules.get("kind") != "allied_defensive_garrison":
        raise ValueError("invalid allied garrison rules kind")
    capacity = rules.get("capacity_units_per_home_colony")
    if type(capacity) is not int or not 1 <= capacity <= 300:
        raise ValueError("invalid allied garrison capacity")
    if rules.get("host_consent") != "explicit_per_home_colony_and_current_alliance":
        raise ValueError("allied garrisons require scoped host consent")


validate_rules(RULES)
