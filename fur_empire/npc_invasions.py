"""Optional, finite world invasion windows for existing CAMPS-3 missions."""

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-npc-invasion-1.json").read_text(encoding="utf-8")
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = hashlib.sha256(SNAPSHOT.encode()).hexdigest()


def schedule(db: Connection, world_id: int, invasion_id: str, name: str, now: int) -> bool:
    if db.execute(
        "SELECT 1 FROM npc_invasions WHERE world_id=? AND ends>? LIMIT 1", (world_id, now)
    ).fetchone():
        return False
    starts = now + int(RULES["warning_seconds"])
    db.execute(
        "INSERT INTO npc_invasions "
        "(id,world_id,name,rules_version,rules_digest,budget,created,starts,ends) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            invasion_id,
            world_id,
            name,
            VERSION,
            DIGEST,
            int(RULES["mission_budget"]),
            now,
            starts,
            starts + int(RULES["active_seconds"]),
        ),
    )
    return True


def planning_window(
    db: Connection, world_id: int, now: int, attack_arrival: int
) -> tuple[str | None, bool]:
    invasion = db.execute(
        "SELECT i.id,i.rules_version,i.rules_digest,i.starts,i.ends,i.budget,"
        "(SELECT COUNT(*) FROM npc_invasion_attacks a WHERE a.invasion_id=i.id) AS planned "
        "FROM npc_invasions i WHERE i.world_id=? AND i.ends>? ORDER BY i.starts DESC,i.id LIMIT 1",
        (world_id, now),
    ).fetchone()
    if invasion is None:
        return None, True
    if invasion["rules_version"] != VERSION or invasion["rules_digest"] != DIGEST:
        return str(invasion["id"]), False
    permitted = (
        invasion["starts"] <= now
        and attack_arrival < invasion["ends"]
        and invasion["planned"] < invasion["budget"]
    )
    return str(invasion["id"]), permitted


def view(db: Connection, world_id: int, now: int, enabled: bool) -> dict[str, Any]:
    items = []
    for row in db.execute(
        "SELECT i.name,i.starts,i.ends,i.budget,COUNT(m.id) AS planned,"
        "SUM(CASE WHEN m.status='resolved' THEN 1 ELSE 0 END) AS resolved,"
        "SUM(CASE WHEN m.status='cancelled' THEN 1 ELSE 0 END) AS cancelled "
        "FROM (SELECT id,name,starts,ends,budget,created FROM npc_invasions WHERE world_id=? "
        "ORDER BY created DESC,id LIMIT 10) i "
        "LEFT JOIN npc_invasion_attacks a ON a.invasion_id=i.id "
        "LEFT JOIN npc_attack_missions m ON m.id=a.mission_id "
        "GROUP BY i.id,i.name,i.starts,i.ends,i.budget,i.created ORDER BY i.created DESC,i.id",
        (world_id,),
    ):
        status = "ended" if now >= row["ends"] else "warning" if now < row["starts"] else "active"
        items.append({**dict(row), "status": status})
    return {"enabled": enabled, "items": items, "version": VERSION}
