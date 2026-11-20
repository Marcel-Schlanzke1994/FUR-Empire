"""Scheduled, world-scoped ruleset publication with mission-version pinning."""

from __future__ import annotations

import json
from typing import Any

from . import (
    crafting,
    hero_doctrines,
    hero_respec,
    heroes,
    npc_camps,
    ruin_exploration,
    terra_combat,
)
from .database import Connection

RULES: dict[str, tuple[str, ...]] = {
    "terra_combat_ruleset": ("FUR-2", *terra_combat.RULESETS),
    "crafting_ruleset": ("FUR-2", crafting.RULES.version),
    "hero_ruleset": ("FUR-2", heroes.RULES.version),
    "hero_doctrine_ruleset": ("FUR-2", hero_doctrines.RULES.version),
    "hero_respec_ruleset": ("FUR-2", hero_respec.RULES.version),
    "npc_camps_ruleset": ("FUR-2", *npc_camps.RULESET_VERSIONS),
    "terra_ruin_exploration_ruleset": ("FUR-2", ruin_exploration.VERSION),
}
SETTING_KEYS = {
    "crafting_ruleset": "crafting_ruleset",
    "hero_ruleset": heroes.RULES.enabled_key,
    "hero_doctrine_ruleset": hero_doctrines.RULES.enabled_key,
    "hero_respec_ruleset": hero_respec.RULES.enabled_key,
    "npc_camps_ruleset": npc_camps.RULESET_KEY,
    "terra_ruin_exploration_ruleset": "terra_ruin_exploration_ruleset",
}


def page(db: Connection, world_id: int) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            "SELECT id,rule_key,target_version,active_at,status,failure_code,created "
            "FROM world_rule_rollouts WHERE world_id=? ORDER BY created DESC,id DESC LIMIT 20",
            (world_id,),
        )
    ]


def validate_target(db: Connection, world_id: int, rule_key: str, target: str) -> str | None:
    if rule_key not in RULES or target not in RULES[rule_key]:
        return "unsupported_ruleset"
    world = db.execute(
        "SELECT terra_combat_ruleset,settings FROM world_settings WHERE world_id=?",
        (world_id,),
    ).fetchone()
    if world is None:
        return "world_missing"
    settings = json.loads(world["settings"] or "{}")
    if not isinstance(settings, dict):
        return "settings_invalid"
    current = (
        str(world["terra_combat_ruleset"])
        if rule_key == "terra_combat_ruleset"
        else str(settings.get(SETTING_KEYS[rule_key], "FUR-2"))
    )
    if (
        rule_key == "terra_combat_ruleset"
        and (
            target in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            or current in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
        )
        and db.execute("SELECT 1 FROM colonies WHERE world_id=? LIMIT 1", (world_id,)).fetchone()
    ):
        return "roster_ruleset_requires_empty_world"
    if (
        rule_key in ("hero_doctrine_ruleset", "hero_respec_ruleset")
        and target != "FUR-2"
        and settings.get(heroes.RULES.enabled_key, "FUR-2") != heroes.RULES.version
    ):
        return "commander_ruleset_required"
    if rule_key == "terra_ruin_exploration_ruleset" and target == ruin_exploration.VERSION:
        for colony in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,)):
            if any(
                job.get("kind") == "ruin_exploration"
                for job in json.loads(colony["state"]).get("jobs", [])
            ):
                return "ruin_exploration_jobs_in_flight"
    if rule_key == "hero_ruleset" and target == "FUR-2":
        if settings.get(hero_doctrines.RULES.enabled_key, "FUR-2") != "FUR-2":
            return "commander_doctrines_still_enabled"
        if settings.get(hero_respec.RULES.enabled_key, "FUR-2") != "FUR-2":
            return "commander_respec_still_enabled"
    if rule_key == "crafting_ruleset" and (
        (target == "FUR-2" and current != "FUR-2") or (target != "FUR-2" and current == "FUR-2")
    ):
        for colony in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,)):
            colony_state = json.loads(colony["state"])
            if any(job.get("kind") == "craft" for job in colony_state.get("jobs", [])):
                return "crafting_jobs_in_flight"
    return None


def cancel(db: Connection, rollout_id: str, now: int) -> bool:
    row = db.execute(
        "SELECT world_id FROM world_rule_rollouts WHERE id=? AND status='pending'",
        (rollout_id,),
    ).fetchone()
    if row is None:
        return False
    db.execute(
        "UPDATE world_rule_rollouts SET status='cancelled',completed=? "
        "WHERE id=? AND status='pending'",
        (now, rollout_id),
    )
    return (
        db.execute(
            "SELECT 1 FROM world_rule_rollouts WHERE id=? AND status='cancelled'", (rollout_id,)
        ).fetchone()
        is not None
    )


def _apply_one(db: Connection, row: Any, now: int) -> str | None:
    world_id = int(row["world_id"])
    rule_key = str(row["rule_key"])
    target = str(row["target_version"])
    if rule_key not in RULES or target not in RULES[rule_key]:
        return "unsupported_ruleset"
    world = db.execute(
        "SELECT terra_combat_ruleset,settings FROM world_settings WHERE world_id=?",
        (world_id,),
    ).fetchone()
    if world is None:
        return "world_missing"
    try:
        settings = json.loads(world["settings"] or "{}")
    except (TypeError, ValueError):
        return "settings_invalid"
    if not isinstance(settings, dict):
        return "settings_invalid"

    current = (
        str(world["terra_combat_ruleset"])
        if rule_key == "terra_combat_ruleset"
        else str(settings.get(SETTING_KEYS[rule_key], "FUR-2"))
    )
    if current == target:
        return "already_active"
    if rule_key == "terra_ruin_exploration_ruleset" and target == ruin_exploration.VERSION:
        try:
            colonies = db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,))
            if any(
                job.get("kind") == "ruin_exploration"
                for colony in colonies
                for job in json.loads(colony["state"]).get("jobs", [])
            ):
                return "ruin_exploration_jobs_in_flight"
        except (TypeError, ValueError, json.JSONDecodeError):
            return "colony_state_invalid"
    if rule_key == "npc_camps_ruleset" and target in npc_camps.RULESET_VERSIONS:
        world_seed = db.execute(
            "SELECT seed FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        if world_seed is None:
            return "world_missing"
        npc_camps.initialize_world(
            db, world_id, int(world_seed["seed"]), int(row["created"]), target
        )
    if rule_key == "terra_combat_ruleset":
        if (
            target in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            or current in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
        ) and db.execute("SELECT 1 FROM colonies WHERE world_id=? LIMIT 1", (world_id,)).fetchone():
            return "roster_ruleset_requires_empty_world"
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=?",
            (target, world_id),
        )
    else:
        if rule_key in ("hero_doctrine_ruleset", "hero_respec_ruleset"):
            hero_version = settings.get(heroes.RULES.enabled_key, "FUR-2")
            if target != "FUR-2" and hero_version != heroes.RULES.version:
                return "commander_ruleset_required"
        if rule_key == "hero_ruleset" and target == "FUR-2":
            if settings.get(hero_doctrines.RULES.enabled_key, "FUR-2") != "FUR-2":
                return "commander_doctrines_still_enabled"
            if settings.get(hero_respec.RULES.enabled_key, "FUR-2") != "FUR-2":
                return "commander_respec_still_enabled"
        if rule_key == "crafting_ruleset" and (
            (target == "FUR-2" and current != "FUR-2") or (target != "FUR-2" and current == "FUR-2")
        ):
            for colony in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,)):
                state = json.loads(colony["state"])
                if any(job.get("kind") == "craft" for job in state.get("jobs", [])):
                    return "crafting_jobs_in_flight"
        settings[SETTING_KEYS[rule_key]] = target
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=?",
            (json.dumps(settings, separators=(",", ":")), world_id),
        )
    return None


def apply_due(db: Connection, now: int, audit: Any) -> int:
    applied = 0
    for row in db.execute(
        "SELECT * FROM world_rule_rollouts WHERE status='pending' AND active_at<=? "
        "ORDER BY active_at,id",
        (now,),
    ).fetchall():
        reason = _apply_one(db, row, now)
        status = "failed" if reason and reason != "already_active" else "applied"
        db.execute(
            "UPDATE world_rule_rollouts SET status=?,failure_code=?,completed=? "
            "WHERE id=? AND status='pending'",
            (status, None if reason == "already_active" else reason, now, row["id"]),
        )
        audit(
            db,
            "worker",
            "world_rule_rollout_" + status,
            str(row["id"]),
            world_id=int(row["world_id"]),
            rule_key=str(row["rule_key"]),
            target_version=str(row["target_version"]),
            scheduled_at=int(row["active_at"]),
            failure_code=reason,
        )
        applied += int(status == "applied")
    return applied
