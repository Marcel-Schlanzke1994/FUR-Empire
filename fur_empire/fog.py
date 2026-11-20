"""Sector visibility and persistent player-scoped map observations."""

import json
import math
from typing import Any

from .database import Connection

COLONY_SIGHT_RADIUS = 8
OUTPOST_SIGHT_RADIUS = 2


def visible_sectors(db: Connection, user: str, world_id: int) -> set[tuple[int, int]]:
    sources: list[tuple[int, int, int]] = []
    for row in db.execute(
        "SELECT x,y,state FROM colonies WHERE user_id=? AND world_id=?", (user, world_id)
    ):
        levels = json.loads(row["state"]).get("terra_energy_levels", {})
        radius = COLONY_SIGHT_RADIUS + min(4, levels.get("scanner_tower", 0))
        sources.append((int(row["x"]), int(row["y"]), radius))
    for row in db.execute("SELECT x,y,state FROM world_outposts WHERE world_id=?", (world_id,)):
        if json.loads(row["state"]).get("owner") == user:
            sources.append((int(row["x"]), int(row["y"]), OUTPOST_SIGHT_RADIUS))
    visible: set[tuple[int, int]] = set()
    for sx, sy, radius in sources:
        for y in range(max(0, sy - radius), min(63, sy + radius) + 1):
            for x in range(max(0, sx - radius), min(63, sx + radius) + 1):
                if math.hypot(x - sx, y - sy) <= radius:
                    visible.add((x, y))
    return visible


def record_observations(
    db: Connection, user: str, world_id: int, now: int
) -> tuple[set[tuple[int, int]], dict[tuple[int, int], int]]:
    visible = visible_sectors(db, user, world_id)
    for x, y in visible:
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET observed_at=excluded.observed_at",
            (user, world_id, x, y, now),
        )
    last_seen = {
        (int(row["x"]), int(row["y"])): int(row["observed_at"])
        for row in db.execute(
            "SELECT x,y,observed_at FROM map_sector_intel WHERE observer_id=? AND world_id=?",
            (user, world_id),
        )
    }
    return visible, last_seen


def sector_is_known(db: Connection, user: str, world_id: int, x: int, y: int) -> bool:
    if (x, y) in visible_sectors(db, user, world_id):
        return True
    return bool(
        db.execute(
            "SELECT 1 FROM map_sector_intel WHERE observer_id=? AND world_id=? AND x=? AND y=?",
            (user, world_id, x, y),
        ).fetchone()
    )


def sector_status(
    x: int,
    y: int,
    visible: set[tuple[int, int]],
    seen: dict[tuple[int, int], int],
) -> dict[str, Any]:
    observed_at = seen.get((x, y))
    status = "current" if (x, y) in visible else "stale" if observed_at is not None else "unknown"
    return {"status": status, "observed_at": observed_at}
