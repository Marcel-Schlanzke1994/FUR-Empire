"""Versioned deterministic exploration of abandoned Terra colony ruins."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-ruin-exploration-1.json").read_text(encoding="utf-8")
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()
_OUTCOMES = tuple(RULES["outcomes"])
assert sum(int(outcome["weight"]) for outcome in _OUTCOMES) == int(RULES["probability_scale"])


def validate_rules(rules: dict[str, Any]) -> None:
    if (
        rules.get("version") != VERSION
        or rules.get("kind") != "terra_ruin_exploration"
        or rules.get("legacy_fur2_preserved") is not True
    ):
        raise ValueError("unsupported Terra ruin exploration rules")
    scale = rules.get("probability_scale")
    outcomes = rules.get("outcomes")
    survey = rules.get("ruin_survey")
    if type(scale) is not int or scale != 10000 or not isinstance(outcomes, list):
        raise ValueError("invalid Terra ruin exploration rules")
    if (
        not outcomes
        or any(
            not isinstance(outcome, dict)
            or not isinstance(outcome.get("id"), str)
            or any(
                type(outcome.get(field)) is not int
                for field in (
                    "weight",
                    "resource_min",
                    "resource_max",
                    "loss_min_percent",
                    "loss_max_percent",
                )
            )
            or outcome["weight"] < 0
            or not 0 <= outcome["resource_min"] <= outcome["resource_max"] <= 160
            or not 0 <= outcome["loss_min_percent"] <= outcome["loss_max_percent"] <= 100
            for outcome in outcomes
        )
        or sum(outcome["weight"] for outcome in outcomes) != scale
    ):
        raise ValueError("invalid Terra ruin exploration outcome catalog")
    if (
        not isinstance(survey, dict)
        or survey.get("expires_at_dispatch_required") is not True
        or survey.get("update_sector_intel") is not True
        or survey.get("update_private_ruin_intel") is not True
        or type(survey.get("intel_retention_seconds")) is not int
        or survey["intel_retention_seconds"] != 86400
        or type(survey.get("resource_capacity_per_survivor")) is not int
        or survey["resource_capacity_per_survivor"] != 100
        or type(survey.get("maximum_resource_reward")) is not int
        or survey["maximum_resource_reward"] != 160
    ):
        raise ValueError("invalid Terra ruin survey rules")


validate_rules(RULES)


def validate_ruleset(version: str, digest: str) -> None:
    if version != VERSION or not hmac.compare_digest(digest, DIGEST):
        raise ValueError("unsupported Terra ruin exploration snapshot")


def _draw(seed: bytes, label: bytes, upper: int) -> int:
    return int.from_bytes(hashlib.sha256(seed + b"\x00" + label).digest()[:8], "big") % upper


def resolve(seed: str, army: dict[str, int]) -> dict[str, Any]:
    """Resolve an exploration repeatably without mutating its reserved force."""
    if (
        not isinstance(seed, str)
        or len(seed) != 64
        or any(character not in "0123456789abcdef" for character in seed)
        or not isinstance(army, dict)
        or set(army) != {"ranger"}
        or type(army["ranger"]) is not int
        or army["ranger"] < 1
    ):
        raise ValueError("invalid Terra ruin exploration seed or army")
    seed_bytes = bytes.fromhex(seed)
    roll = _draw(seed_bytes, b"outcome", int(RULES["probability_scale"]))
    edge = 0
    selected: dict[str, Any] | None = None
    for outcome in _OUTCOMES:
        edge += int(outcome["weight"])
        if roll < edge:
            selected = outcome
            break
    if selected is None:
        raise ValueError("invalid Terra ruin exploration outcome weights")
    loss_min = int(selected["loss_min_percent"])
    loss_max = int(selected["loss_max_percent"])
    loss_percent = loss_min + _draw(seed_bytes, b"loss", loss_max - loss_min + 1)
    survivors = {
        unit: max(0, count - (count * loss_percent + 99) // 100) for unit, count in army.items()
    }
    resource_max = int(selected["resource_max"])
    resources = [0, 0, 0]
    if resource_max:
        resource_index = _draw(seed_bytes, b"resource", len(resources))
        amount = int(selected["resource_min"]) + _draw(
            seed_bytes, b"amount", resource_max - int(selected["resource_min"]) + 1
        )
        survey = RULES["ruin_survey"]
        resources[resource_index] = min(
            amount,
            survivors["ranger"] * int(survey["resource_capacity_per_survivor"]),
            int(survey["maximum_resource_reward"]),
        )
    return {
        "rules_version": VERSION,
        "rules_digest": DIGEST,
        "seed_commitment": hashlib.sha256(seed_bytes).hexdigest(),
        "outcome": str(selected["id"]),
        "roll": roll,
        "loss_percent": loss_percent,
        "survivors": survivors,
        "loot": resources,
    }


def pin_mission(
    db: Connection,
    mission_id: str,
    world_id: int,
    owner_id: str,
    ruin_id: str,
    x: int,
    y: int,
    created: int,
    expires: int,
) -> dict[str, str]:
    """Persist the private seed and exact in-flight rules before troops are committed."""
    if not mission_id or not ruin_id or expires <= created:
        raise ValueError("invalid Terra ruin exploration mission")
    seed = secrets.token_hex(32)
    commitment = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    db.execute(
        "INSERT INTO terra_ruin_explorations"
        "(mission_id,world_id,owner_id,ruin_id,x,y,rules_version,rules_digest,seed,"
        "seed_commitment,created,expires) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            mission_id,
            world_id,
            owner_id,
            ruin_id,
            x,
            y,
            VERSION,
            DIGEST,
            seed,
            commitment,
            created,
            expires,
        ),
    )
    return {
        "rules_version": VERSION,
        "rules_digest": DIGEST,
        "seed_commitment": commitment,
    }


def mission_seed(
    db: Connection, mission_id: str, world_id: int, owner_id: str
) -> tuple[str, Any, bool]:
    row = db.execute(
        "SELECT * FROM terra_ruin_explorations WHERE mission_id=? AND world_id=? AND owner_id=?",
        (mission_id, world_id, owner_id),
    ).fetchone()
    if row is None:
        raise ValueError("missing Terra ruin exploration record")
    seed = str(row["seed"])
    commitment = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    validate_ruleset(str(row["rules_version"]), str(row["rules_digest"]))
    if commitment != str(row["seed_commitment"]):
        raise ValueError("invalid Terra ruin exploration seed")
    return seed, row, row["resolved"] is not None


def store_outcome(db: Connection, mission_id: str, outcome: dict[str, Any], resolved: int) -> None:
    changed = db.execute(
        "UPDATE terra_ruin_explorations SET resolved=?,outcome=? "
        "WHERE mission_id=? AND resolved IS NULL RETURNING mission_id",
        (resolved, json.dumps(outcome, sort_keys=True, separators=(",", ":")), mission_id),
    ).fetchone()
    if changed is None:
        raise ValueError("Terra ruin exploration was already resolved")


def discard_mission(db: Connection, mission_id: str) -> None:
    db.execute(
        "DELETE FROM terra_ruin_explorations WHERE mission_id=? AND resolved IS NULL",
        (mission_id,),
    )
