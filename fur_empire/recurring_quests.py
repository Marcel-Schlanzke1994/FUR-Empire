"""Versioned daily and weekly objectives for completed Terra orders."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .database import Connection

DAY = 86_400
WEEK = 7 * DAY


class Quest(BaseModel):
    id: str
    period: Literal["daily", "weekly"]
    event: Literal["build", "research", "train"]
    title: str
    target: int = Field(gt=0)
    reward: tuple[int, int, int]


_RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-recurring-quests-1.json").read_text(encoding="utf-8")
)
VERSION = str(_RULES["version"])
SNAPSHOT = json.dumps(_RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = hashlib.sha256(SNAPSHOT.encode()).hexdigest()
QUESTS = tuple(Quest.model_validate(entry) for entry in _RULES["quests"])


def set_enabled(db: Connection, world_id: int, window_id: str, now: int, enabled: bool) -> bool:
    if enabled:
        changed = db.execute(
            "INSERT INTO recurring_quest_windows(id,world_id,rules_version,starts) VALUES (?,?,?,?) "
            "ON CONFLICT(world_id) WHERE ends IS NULL DO NOTHING RETURNING id",
            (window_id, world_id, VERSION, now),
        ).fetchone()
    else:
        changed = db.execute(
            "UPDATE recurring_quest_windows SET ends=? WHERE world_id=? AND ends IS NULL RETURNING id",
            (now, world_id),
        ).fetchone()
    return changed is not None


def periods(now: int) -> dict[str, tuple[int, int]]:
    daily = now // DAY * DAY
    # The Unix epoch was a Thursday, three days after the start of its UTC week.
    weekly = (now + 3 * DAY) // WEEK * WEEK - 3 * DAY
    return {"daily": (daily, daily + DAY), "weekly": (weekly, weekly + WEEK)}


def record_completed_order(
    db: Connection, world_id: int, user: str, kind: str, completed_at: int, amount: int
) -> None:
    """Run only in the transaction that completes and removes the queued order."""
    if not db.execute(
        "SELECT 1 FROM recurring_quest_windows WHERE world_id=? AND rules_version=? "
        "AND starts<=? AND (ends IS NULL OR ends>?) LIMIT 1",
        (world_id, VERSION, completed_at, completed_at),
    ).fetchone():
        return
    windows = periods(completed_at)
    for quest in QUESTS:
        if quest.event != kind:
            continue
        start = windows[quest.period][0]
        db.execute(
            "INSERT INTO recurring_quest_progress "
            "(world_id,user_id,rules_version,period_start,quest_id,progress) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(world_id,user_id,rules_version,period_start,quest_id) DO UPDATE SET "
            "progress=CASE WHEN recurring_quest_progress.progress+excluded.progress>=? THEN ? "
            "ELSE recurring_quest_progress.progress+excluded.progress END "
            "WHERE recurring_quest_progress.progress<?",
            (
                world_id,
                user,
                VERSION,
                start,
                quest.id,
                min(amount, quest.target),
                quest.target,
                quest.target,
                quest.target,
            ),
        )


def claim_key(world_id: int, start: int, quest_id: str) -> str:
    return f"{world_id}:{VERSION}:{start}:{quest_id}"


def claim(db: Connection, world_id: int, user: str, key: str, now: int) -> Quest | None:
    windows = periods(now)
    for quest in QUESTS:
        start = windows[quest.period][0]
        if key != claim_key(world_id, start, quest.id):
            continue
        claimed = db.execute(
            "UPDATE recurring_quest_progress SET claimed_at=? "
            "WHERE world_id=? AND user_id=? AND rules_version=? AND period_start=? AND quest_id=? "
            "AND progress>=? AND claimed_at IS NULL RETURNING quest_id",
            (now, world_id, user, VERSION, start, quest.id, quest.target),
        ).fetchone()
        return quest if claimed else None
    return None


def view(db: Connection, world_id: int, user: str, now: int) -> dict[str, Any]:
    windows = periods(now)
    enabled = (
        db.execute(
            "SELECT 1 FROM recurring_quest_windows WHERE world_id=? AND rules_version=? AND ends IS NULL",
            (world_id, VERSION),
        ).fetchone()
        is not None
    )
    progress = {
        (row["period_start"], row["quest_id"]): row
        for row in db.execute(
            "SELECT period_start,quest_id,progress,claimed_at FROM recurring_quest_progress "
            "WHERE world_id=? AND user_id=? AND rules_version=? AND period_start IN (?,?)",
            (world_id, user, VERSION, windows["daily"][0], windows["weekly"][0]),
        )
    }
    quests = []
    for quest in QUESTS:
        start, end = windows[quest.period]
        row = progress.get((start, quest.id))
        if not enabled and row is None:
            continue
        quests.append(
            {
                "id": quest.id,
                "key": claim_key(world_id, start, quest.id),
                "period": quest.period,
                "ends": end,
                "title": quest.title,
                "target": quest.target,
                "progress": row["progress"] if row is not None else 0,
                "claimed": row is not None and row["claimed_at"] is not None,
                "reward": quest.reward,
            }
        )
    return {"enabled": enabled, "version": VERSION, "quests": quests}
