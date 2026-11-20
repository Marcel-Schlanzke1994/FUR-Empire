"""Versioned home designation; never moves resources, units or mission targets."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .database import Connection


class HomeRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    cooldown_seconds: int = Field(ge=1, le=30 * 86400)


RULES = HomeRules.model_validate(
    json.loads((Path(__file__).parent / "rules" / "colony-home-1.json").read_text(encoding="utf-8"))
)
RULE_HASH = hashlib.sha256(
    json.dumps(RULES.model_dump(), sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def home_status(db: Connection, user: str, world_id: int, now: int) -> dict[str, Any]:
    row = db.execute(
        "SELECT next_change FROM colony_home_changes WHERE owner=? AND world_id=?",
        (user, world_id),
    ).fetchone()
    next_change = int(row["next_change"]) if row else 0
    return {
        "version": RULES.version,
        "rule_hash": RULE_HASH,
        "cooldown_seconds": RULES.cooldown_seconds,
        "next_change": next_change,
        "available": now >= next_change,
    }


def designate_home(
    db: Connection, user: str, world_id: int, colony_id: str, now: int
) -> dict[str, Any]:
    from .game import RuleError

    target = db.execute(
        "SELECT is_home FROM colonies WHERE colony_id=? AND user_id=? AND world_id=?",
        (colony_id, user, world_id),
    ).fetchone()
    if not target:
        raise RuleError("Wähle eine eigene Kolonie in der aktiven Welt.")
    if target["is_home"]:
        raise RuleError("Diese Kolonie ist bereits deine Heimatkolonie.")
    status = home_status(db, user, world_id, now)
    if not status["available"]:
        raise RuleError("Die Heimatkolonie kann nur alle 24 Stunden gewechselt werden.")
    old = db.execute(
        "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
        (user, world_id),
    ).fetchone()
    if not old:
        raise RuleError("Die bestehende Heimatkolonie konnte nicht gefunden werden.")
    db.execute(
        "UPDATE colonies SET is_home=FALSE WHERE user_id=? AND world_id=? AND is_home=TRUE",
        (user, world_id),
    )
    db.execute(
        "UPDATE colonies SET is_home=TRUE WHERE colony_id=? AND user_id=? AND world_id=?",
        (colony_id, user, world_id),
    )
    next_change = now + RULES.cooldown_seconds
    db.execute(
        "INSERT INTO colony_home_changes(owner,world_id,changed,next_change,rule_version,rule_hash) "
        "VALUES (?,?,?,?,?,?) ON CONFLICT(owner,world_id) DO UPDATE SET "
        "changed=excluded.changed,next_change=excluded.next_change,"
        "rule_version=excluded.rule_version,rule_hash=excluded.rule_hash",
        (user, world_id, now, next_change, RULES.version, RULE_HASH),
    )
    return {
        "previous_colony_id": str(old["colony_id"]),
        "colony_id": colony_id,
        "world_id": world_id,
        "next_change": next_change,
        "rule_version": RULES.version,
        "rule_hash": RULE_HASH,
    }
