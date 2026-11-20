"""Versioned FUR-3 Terra scouting interception and detection; FUR-2 is unchanged."""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-terra-intelligence-1.json").read_text(
        encoding="utf-8"
    )
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()


def validate_rules(rules: dict[str, Any]) -> None:
    if rules.get("version") != VERSION or rules.get("kind") != "terra_scout_counterintelligence":
        raise ValueError("unsupported Terra intelligence rules")
    if rules.get("legacy_fur2_preserved") is not True:
        raise ValueError("Terra intelligence rules must preserve FUR-2")
    formula = rules.get("formula")
    outcomes = rules.get("outcomes")
    if not isinstance(formula, dict) or not isinstance(outcomes, dict):
        raise TypeError("invalid Terra intelligence rule types")
    for key, expected_max in (("interception", 50), ("detection", 60)):
        values = formula.get(key)
        if not isinstance(values, dict) or any(
            type(values.get(field)) is not int
            for field in (
                "base_percent",
                "tactics_percent_per_level",
                "wall_percent_per_level",
                "maximum_percent",
            )
        ):
            raise ValueError(f"invalid Terra {key} formula")
        if not 0 <= values["base_percent"] <= values["maximum_percent"] <= expected_max:
            raise ValueError(f"out-of-range Terra {key} formula")
        if values["tactics_percent_per_level"] < 0 or values["wall_percent_per_level"] < 0:
            raise ValueError(f"negative Terra {key} modifier")
    if (
        outcomes.get("intercepted_rangers_lost") != 1
        or outcomes.get("interception_suppresses_intel") is not True
        or outcomes.get("interception_always_detected") is not True
        or outcomes.get("detection_report_exposes_attacker") is not False
        or outcomes.get("counter_battle") is not False
        or rules.get("probability_scale") != 10000
    ):
        raise ValueError("unsupported Terra intelligence outcome contract")


validate_rules(RULES)


def chances(tactics_level: int, wall_level: int) -> tuple[int, int]:
    """Return pinned (interception, detection) percentages for valid FUR-2 levels."""
    bounds = RULES["level_bounds"]
    if (
        type(tactics_level) is not int
        or type(wall_level) is not int
        or not bounds["tactics"][0] <= tactics_level <= bounds["tactics"][1]
        or not bounds["wall"][0] <= wall_level <= bounds["wall"][1]
    ):
        raise ValueError("invalid Terra intelligence levels")
    formula = RULES["formula"]
    interception = formula["interception"]
    detection = formula["detection"]
    return (
        min(
            interception["maximum_percent"],
            interception["base_percent"]
            + tactics_level * interception["tactics_percent_per_level"]
            + wall_level * interception["wall_percent_per_level"],
        ),
        min(
            detection["maximum_percent"],
            detection["base_percent"]
            + tactics_level * detection["tactics_percent_per_level"]
            + wall_level * detection["wall_percent_per_level"],
        ),
    )


def _roll(seed: bytes, label: bytes) -> int:
    return int.from_bytes(hashlib.sha256(seed + b"\x00" + label).digest()[:8], "big") % int(
        RULES["probability_scale"]
    )


def resolve(
    seed: str,
    ranger_count: int,
    *,
    interception_percent: int,
    detection_percent: int,
) -> dict[str, Any]:
    """Resolve a pinned scouting attempt reproducibly without mutating its army."""
    if (
        not isinstance(seed, str)
        or len(seed) != 64
        or any(char not in "0123456789abcdef" for char in seed)
    ):
        raise ValueError("invalid Terra intelligence seed")
    if type(ranger_count) is not int or not 1 <= ranger_count <= 10000:
        raise ValueError("invalid Terra intelligence ranger count")
    if (
        type(interception_percent) is not int
        or not 0 <= interception_percent <= int(RULES["formula"]["interception"]["maximum_percent"])
        or type(detection_percent) is not int
        or not 0 <= detection_percent <= int(RULES["formula"]["detection"]["maximum_percent"])
    ):
        raise ValueError("invalid Terra intelligence probability")
    seed_bytes = bytes.fromhex(seed)
    interception_roll = _roll(seed_bytes, b"interception")
    detection_roll = _roll(seed_bytes, b"detection")
    intercepted = interception_roll < interception_percent * 100
    detected = intercepted or detection_roll < detection_percent * 100
    lost = (
        min(ranger_count, int(RULES["outcomes"]["intercepted_rangers_lost"])) if intercepted else 0
    )
    return {
        "rules_version": VERSION,
        "rules_digest": DIGEST,
        "seed_commitment": hashlib.sha256(seed_bytes).hexdigest(),
        "interception_percent": interception_percent,
        "detection_percent": detection_percent,
        "interception_roll": interception_roll,
        "detection_roll": detection_roll,
        "intercepted": intercepted,
        "detected": detected,
        "rangers_lost": lost,
        "rangers_returned": ranger_count - lost,
    }


def pin_mission(
    db: Connection,
    mission_id: str,
    world_id: int,
    attacker_id: str,
    defender_id: str,
    defender_tactics: int,
    defender_wall: int,
    created: int,
) -> dict[str, str]:
    interception, detection = chances(defender_tactics, defender_wall)
    seed = secrets.token_hex(32)
    commitment = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    db.execute(
        "INSERT INTO terra_intel_missions"
        "(mission_id,world_id,attacker_id,defender_id,rules_version,rules_digest,seed,"
        "seed_commitment,interception_percent,detection_percent,created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            mission_id,
            world_id,
            attacker_id,
            defender_id,
            VERSION,
            DIGEST,
            seed,
            commitment,
            interception,
            detection,
            created,
        ),
    )
    return {
        "intel_rules_version": VERSION,
        "intel_rules_digest": DIGEST,
        "intel_seed_commitment": commitment,
    }


def mission_seed(
    db: Connection,
    mission_id: str,
    world_id: int,
    attacker_id: str,
    defender_id: str,
    expected_commitment: str,
) -> tuple[str, int, int, bool]:
    """Load and verify pinned mission inputs; the seed remains server-private."""
    row = db.execute(
        "SELECT * FROM terra_intel_missions WHERE mission_id=? AND world_id=? "
        "AND attacker_id=? AND defender_id=?",
        (mission_id, world_id, attacker_id, defender_id),
    ).fetchone()
    if not row:
        raise ValueError("missing Terra intelligence mission record")
    seed = str(row["seed"])
    if (
        str(row["rules_version"]) != VERSION
        or str(row["rules_digest"]) != DIGEST
        or str(row["seed_commitment"]) != hashlib.sha256(bytes.fromhex(seed)).hexdigest()
        or str(row["seed_commitment"]) != expected_commitment
    ):
        raise ValueError("invalid Terra intelligence mission record")
    return (
        seed,
        int(row["interception_percent"]),
        int(row["detection_percent"]),
        row["resolved"] is not None,
    )


def store_outcome(db: Connection, mission_id: str, outcome: dict[str, Any], resolved: int) -> None:
    changed = db.execute(
        "UPDATE terra_intel_missions SET resolved=?,outcome=? "
        "WHERE mission_id=? AND resolved IS NULL RETURNING mission_id",
        (resolved, json.dumps(outcome, sort_keys=True, separators=(",", ":")), mission_id),
    ).fetchone()
    if changed is None:
        raise ValueError("Terra intelligence mission was already resolved")


def discard_mission(db: Connection, mission_id: str) -> None:
    db.execute(
        "DELETE FROM terra_intel_missions WHERE mission_id=? AND resolved IS NULL", (mission_id,)
    )
