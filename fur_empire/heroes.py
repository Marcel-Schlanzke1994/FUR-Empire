"""Opt-in, account-owned Commander progression scoped to a game world."""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .database import Connection


class HeroRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    enabled_key: str
    eligible_jobs: dict[str, int] = Field(min_length=1, max_length=20)
    level_cap: int = Field(ge=2, le=100)
    xp_per_level: int = Field(ge=1, le=100000)
    stat_cap: int = Field(ge=1, le=100)
    stats: list[str] = Field(min_length=1, max_length=20)


RULES = HeroRules.model_validate(
    json.loads((Path(__file__).parent / "rules" / "hero-1.json").read_text(encoding="utf-8"))
)
if len(RULES.stats) != len(set(RULES.stats)) or any(
    amount < 1 or amount > 100 for amount in RULES.eligible_jobs.values()
):
    raise ValueError("Invalid FUR hero rules")
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
AVAILABLE_STATS = ("economy",)


def enabled_in_world(db: Connection, world_id: int) -> bool:
    row = db.execute("SELECT settings FROM world_settings WHERE world_id=?", (world_id,)).fetchone()
    if not row:
        return False
    try:
        settings = json.loads(row["settings"] or "{}")
    except (TypeError, ValueError):
        return False
    if not isinstance(settings, dict):
        return False
    configured = settings.get(RULES.enabled_key, "FUR-2")
    return isinstance(configured, str) and configured == RULES.version


def pin_job(db: Connection, world_id: int, job: dict[str, Any]) -> None:
    if enabled_in_world(db, world_id) and str(job.get("kind", "")) in RULES.eligible_jobs:
        job["hero_rules_version"] = RULES.version
        job["hero_rules_hash"] = RULE_HASH


def level_for_experience(experience: int) -> int:
    level = 1
    remaining = max(0, experience)
    while level < RULES.level_cap:
        required = level * RULES.xp_per_level
        if remaining < required:
            break
        remaining -= required
        level += 1
    return level


def _ensure(db: Connection, user_id: str, world_id: int, now: int) -> None:
    db.execute(
        "INSERT INTO commander_heroes(user_id,world_id,created,updated) VALUES (?,?,?,?) "
        "ON CONFLICT(user_id,world_id) DO NOTHING",
        (user_id, world_id, now, now),
    )


def view(db: Connection, user_id: str, world_id: int) -> dict[str, Any]:
    enabled = enabled_in_world(db, world_id)
    from . import hero_doctrines

    doctrine_enabled = hero_doctrines.enabled_in_world(db, world_id)
    row = db.execute(
        "SELECT experience,military,economy,recon,command FROM commander_heroes "
        "WHERE user_id=? AND world_id=?",
        (user_id, world_id),
    ).fetchone()
    stats = {key: int(row[key]) if row else 0 for key in RULES.stats}
    experience = int(row["experience"]) if row else 0
    level = level_for_experience(experience)
    spent = sum(stats.values())
    return {
        "enabled": enabled,
        "rules_version": RULES.version,
        "rules_hash": RULE_HASH,
        "experience": experience,
        "level": level,
        "level_cap": RULES.level_cap,
        "experience_to_next": (
            0 if level >= RULES.level_cap else _xp_before(level + 1) - experience
        ),
        "skill_points": max(0, level - 1 - spent),
        "stats": stats,
        "available_stats": list(RULES.stats if doctrine_enabled else AVAILABLE_STATS),
        "stat_cap": RULES.stat_cap,
        "eligible_rewards": dict(RULES.eligible_jobs),
    }


def _xp_before(level: int) -> int:
    return RULES.xp_per_level * (level - 1) * level // 2


def allocate(db: Connection, user_id: str, world_id: int, stat: object, now: int) -> None:
    from .game import RuleError

    if not enabled_in_world(db, world_id):
        raise RuleError("Die Heldenverwaltung ist in dieser Welt nicht aktiviert.")
    if not isinstance(stat, str) or stat not in RULES.stats:
        raise RuleError("Wähle ein gültiges Commander-Attribut.")
    if stat not in AVAILABLE_STATS:
        from . import hero_doctrines

        if stat not in hero_doctrines.DOCTRINE_STATS or not hero_doctrines.enabled_in_world(
            db, world_id
        ):
            raise RuleError("Dieses Attribut ist erst mit den FUR-3-Doktrinen verfügbar.")
    _ensure(db, user_id, world_id, now)
    current = view(db, user_id, world_id)
    if current["skill_points"] < 1:
        raise RuleError("Es ist kein Skillpunkt zur Vergabe verfügbar.")
    if current["stats"][stat] >= RULES.stat_cap:
        raise RuleError("Dieses Attribut hat bereits seine Höchststufe erreicht.")
    db.execute(
        f"UPDATE commander_heroes SET {stat}={stat}+1,updated=? WHERE user_id=? AND world_id=?",
        (now, user_id, world_id),
    )


def award_job(db: Connection, user_id: str, world_id: int, job: dict[str, Any], now: int) -> int:
    """Award completion XP once, only under the world rules pinned at dispatch."""
    kind = str(job.get("kind", ""))
    amount = RULES.eligible_jobs.get(kind, 0)
    version, digest = job.get("hero_rules_version"), job.get("hero_rules_hash")
    if not amount or version is None and digest is None:
        return 0
    if (
        version != RULES.version
        or not isinstance(digest, str)
        or not hmac.compare_digest(digest, RULE_HASH)
    ):
        raise RuntimeError("Unsupported Commander experience rules")
    _ensure(db, user_id, world_id, now)
    current_experience = int(
        db.execute(
            "SELECT experience FROM commander_heroes WHERE user_id=? AND world_id=?",
            (user_id, world_id),
        ).fetchone()["experience"]
    )
    amount = min(amount, max(0, _xp_before(RULES.level_cap) - current_experience))
    if amount == 0:
        return 0
    inserted = db.execute(
        "INSERT INTO commander_hero_xp_events(id,user_id,world_id,source_job_id,source_kind,"
        "experience,rules_version,rules_hash,created) "
        "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id,world_id,source_job_id) DO NOTHING",
        (job["id"], user_id, world_id, str(job["id"]), kind, amount, RULES.version, RULE_HASH, now),
    ).cursor.rowcount
    if inserted != 1:
        return 0
    db.execute(
        "UPDATE commander_heroes SET experience=experience+?,updated=? WHERE user_id=? AND world_id=?",
        (amount, now, user_id, world_id),
    )
    return amount
