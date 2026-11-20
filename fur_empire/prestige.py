"""Account-scoped, non-gameplay prestige milestones."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-cosmetic-rewards-1.json").read_text(encoding="utf-8")
)["prestige"]
VERSION = str(RULES["version"])
MAX_LEVEL = int(RULES["max_level"])
MILESTONE_SOURCES = {str(key) for key in RULES["milestone_sources"]}
if (
    VERSION != "FUR-3-PRESTIGE-1"
    or MAX_LEVEL != 3
    or set(RULES["milestone_sources"].values()) != {1}
    or RULES["thresholds"] != [1, 2, 3]
    or set(RULES["profile_badges"]) != {"1", "2", "3"}
    or RULES["gameplay_effects"] is not False
    or RULES["account_scope"] is not True
):
    raise ValueError("Invalid or unsafe prestige ruleset")


def award(
    db: Connection,
    user_id: str,
    source_key: str,
    source_type: str,
    world_id: int,
    source_id: str,
    now: int,
) -> int:
    """Record one qualifying milestone exactly once and return the resulting level."""
    if (
        source_type not in MILESTONE_SOURCES
        or not source_key
        or len(source_key) > 160
        or not source_id
        or len(source_id) > 160
        or not 1 <= world_id <= 2_147_483_647
        or now < 0
    ):
        raise ValueError("Invalid prestige milestone")
    existing = db.execute(
        "SELECT prestige_level FROM prestige_records WHERE user_id=? AND source_key=?",
        (user_id, source_key),
    ).fetchone()
    if existing is not None:
        return int(
            db.execute(
                "SELECT COUNT(*) FROM prestige_records WHERE user_id=?", (user_id,)
            ).fetchone()[0]
        )
    current = int(
        db.execute("SELECT COUNT(*) FROM prestige_records WHERE user_id=?", (user_id,)).fetchone()[
            0
        ]
    )
    target = min(MAX_LEVEL, current + 1)
    if current >= MAX_LEVEL:
        return MAX_LEVEL
    db.execute(
        "INSERT INTO prestige_records(user_id,source_key,source_type,world_id,prestige_level,"
        "rules_version,source_id,created) VALUES (?,?,?,?,?,?,?,?) "
        "ON CONFLICT(user_id,source_key) DO NOTHING",
        (user_id, source_key, source_type, world_id, target, VERSION, source_id, now),
    )
    return int(
        db.execute("SELECT COUNT(*) FROM prestige_records WHERE user_id=?", (user_id,)).fetchone()[
            0
        ]
    )


def view(db: Connection, user_id: str) -> dict[str, Any]:
    rows = [
        dict(row)
        for row in db.execute(
            "SELECT source_key,source_type,world_id,prestige_level,source_id,created "
            "FROM prestige_records WHERE user_id=? ORDER BY created DESC,source_key LIMIT 50",
            (user_id,),
        )
    ]
    level = int(
        db.execute("SELECT COUNT(*) FROM prestige_records WHERE user_id=?", (user_id,)).fetchone()[
            0
        ]
    )
    return {
        "version": VERSION,
        "level": min(MAX_LEVEL, level),
        "max_level": MAX_LEVEL,
        "badge": RULES["profile_badges"].get(str(min(MAX_LEVEL, level))),
        "milestones": rows,
    }
