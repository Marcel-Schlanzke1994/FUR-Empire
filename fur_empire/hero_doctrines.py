"""Versioned, world-opt-in passive Commander doctrines for FUR-3-HERO-2."""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from . import heroes
from .database import Connection


class DoctrineRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    enabled_key: str
    maximum_stat_level: int
    effects: dict[str, dict[str, int]]


RULES = DoctrineRules.model_validate(
    json.loads(
        (Path(__file__).parent / "rules" / "hero-doctrines-1.json").read_text(encoding="utf-8")
    )
)
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
DOCTRINE_STATS = ("military", "recon", "command")


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


def _value(level: int, stat: str, per_point_key: str, cap_key: str) -> int:
    values = RULES.effects[stat]
    return min(
        int(values[cap_key]),
        max(0, min(RULES.maximum_stat_level, level)) * int(values[per_point_key]),
    )


def bonuses(stats: dict[str, Any] | None, *, enabled: bool) -> dict[str, int]:
    selected = stats if enabled and isinstance(stats, dict) else {}
    return {
        "production_percent": _value(
            int(selected.get("economy", 0)) if type(selected.get("economy", 0)) is int else 0,
            "economy",
            "production_percent_per_point",
            "production_percent_cap",
        ),
        "combat_damage_percent": _value(
            int(selected.get("military", 0)) if type(selected.get("military", 0)) is int else 0,
            "military",
            "combat_damage_percent_per_point",
            "combat_damage_percent_cap",
        ),
        "intel_lifetime_percent": _value(
            int(selected.get("recon", 0)) if type(selected.get("recon", 0)) is int else 0,
            "recon",
            "intel_lifetime_percent_per_point",
            "intel_lifetime_percent_cap",
        ),
        "mission_slots": _value(
            int(selected.get("command", 0)) if type(selected.get("command", 0)) is int else 0,
            "command",
            "mission_slots_per_point",
            "mission_slots_cap",
        ),
    }


def view(db: Connection, world_id: int, commander: dict[str, Any]) -> dict[str, Any]:
    enabled = enabled_in_world(db, world_id)
    stats = commander.get("stats", {})
    return {
        "enabled": enabled,
        "rules_version": RULES.version,
        "rules_hash": RULE_HASH,
        "bonuses": bonuses(stats, enabled=enabled),
    }


def pin_job(db: Connection, world_id: int, commander: dict[str, Any], job: dict[str, Any]) -> None:
    if not enabled_in_world(db, world_id) or job.get("kind") not in ("attack", "raid", "scout"):
        return
    stats = commander.get("stats", {})
    if not isinstance(stats, dict):
        return
    active = {key: int(stats.get(key, 0)) for key in RULES.effects}
    job["hero_doctrine_rules_version"] = RULES.version
    job["hero_doctrine_rules_hash"] = RULE_HASH
    job["hero_doctrine_stats"] = active
    job["hero_doctrine_bonuses"] = bonuses(active, enabled=True)


def pinned_bonuses(job: dict[str, Any]) -> dict[str, int]:
    version, digest = job.get("hero_doctrine_rules_version"), job.get("hero_doctrine_rules_hash")
    values = job.get("hero_doctrine_bonuses")
    if version is None and digest is None and values is None:
        return bonuses(None, enabled=False)
    if (
        version != RULES.version
        or not isinstance(digest, str)
        or not hmac.compare_digest(digest, RULE_HASH)
    ):
        raise ValueError("unsupported pinned hero doctrine rules")
    stats = job.get("hero_doctrine_stats")
    if not isinstance(stats, dict) or any(
        type(stats.get(stat)) is not int for stat in RULES.effects
    ):
        raise ValueError("invalid pinned hero doctrine stats")
    expected = bonuses(stats, enabled=True)
    if values != expected:
        raise ValueError("invalid pinned hero doctrine effects")
    return expected


def combat_modifier(job: dict[str, Any]) -> int:
    """FUR-3 attacker doctrine percentage; FUR-2 never consumes this value."""
    return min(200, 100 + pinned_bonuses(job)["combat_damage_percent"])


def intel_lifetime_seconds(job: dict[str, Any]) -> int:
    return 3600 * (100 + pinned_bonuses(job)["intel_lifetime_percent"]) // 100
