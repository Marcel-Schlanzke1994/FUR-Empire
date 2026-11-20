"""Immutable draft contract for recovering a limited share of Terra combat losses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-terra-recovery-1.json").read_text(encoding="utf-8")
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()


def validate_rules(rules: dict[str, Any]) -> None:
    if (
        rules.get("version") != VERSION
        or rules.get("kind") != "unit_wreck_recovery"
        or rules.get("status") != "provisional_balance"
        or rules.get("legacy_fur2_preserved") is not True
    ):
        raise ValueError("unsupported Terra recovery contract")
    if (
        type(rules.get("loss_recovery_percent")) is not int
        or not 0 <= rules["loss_recovery_percent"] <= 100
        or type(rules.get("wreck_window_seconds")) is not int
        or rules["wreck_window_seconds"] < 1
        or type(rules.get("repair_cost_percent")) is not int
        or not 1 <= rules["repair_cost_percent"] <= 100
        or rules.get("loss_rounding") != "floor_per_unit_type_and_colony"
        or rules.get("repair_cost_rounding") != "ceil_per_resource_per_unit"
        or rules.get("repair_duration_formula") != "unit_training_seconds_times_count"
        or rules.get("repair_queue") != "one_active_order_per_colony"
        or rules.get("cancel_policy") != "full_cost_refund_and_wreck_restore"
        or rules.get("training_activation_gate") != "separate_balance_acceptance"
    ):
        raise ValueError("invalid Terra recovery rules")


validate_rules(RULES)


def record_losses(
    db: Connection,
    *,
    mission_id: str,
    owner_id: str,
    colony_id: str,
    world_id: int,
    losses: dict[str, int],
    unit_profiles: dict[str, dict[str, Any]],
    at: int,
) -> list[dict[str, Any]]:
    """Persist only the rule-defined recoverable portion of a pinned COMBAT-4 loss."""
    recorded: list[dict[str, Any]] = []
    for unit, lost in sorted(losses.items()):
        profile = unit_profiles.get(unit)
        if profile is None or type(lost) is not int or lost <= 0:
            continue
        ratio = int(profile.get("repair_ratio", 0))
        amount = lost * ratio // 100
        wreck_id = hashlib.sha256(
            f"{VERSION}\x1f{mission_id}\x1f{colony_id}\x1f{unit}".encode()
        ).hexdigest()
        expires = at + int(RULES["wreck_window_seconds"])
        db.execute(
            "INSERT INTO terra_unit_wrecks"
            "(id,mission_id,owner_id,colony_id,world_id,unit_id,amount,expires,created,"
            "rule_version,rule_digest) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(mission_id,colony_id,unit_id) DO NOTHING",
            (
                wreck_id,
                mission_id,
                owner_id,
                colony_id,
                world_id,
                unit,
                amount,
                expires,
                at,
                VERSION,
                DIGEST,
            ),
        )
        row = db.execute(
            "SELECT amount,rule_digest FROM terra_unit_wrecks "
            "WHERE mission_id=? AND colony_id=? AND unit_id=?",
            (mission_id, colony_id, unit),
        ).fetchone()
        if not row or int(row["amount"]) != amount or str(row["rule_digest"]) != DIGEST:
            raise ValueError("Terra wreck recovery replay does not match its first result")
        if amount > 0:
            recorded.append({"id": wreck_id, "unit": unit, "amount": amount, "expires": expires})
    return recorded


def repair_costs(unit_profile: dict[str, Any], count: int) -> list[int]:
    if type(count) is not int or count < 1:
        raise ValueError("invalid Terra repair count")
    costs = unit_profile.get("cost")
    if (
        not isinstance(costs, list)
        or len(costs) != 3
        or any(type(value) is not int for value in costs)
    ):
        raise ValueError("invalid Terra unit repair costs")
    percent = int(RULES["repair_cost_percent"])
    return [(int(value) * percent + 99) // 100 * count for value in costs]
