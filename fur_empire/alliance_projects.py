"""Versioned cooperative alliance projects with bounded contributions and refunds."""

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .database import Connection

RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-alliance-projects-1.json").read_text(encoding="utf-8")
)
RULES_VERSION = str(RULES["version"])
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = "sha256:" + hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
PROJECTS = {str(project["id"]): project for project in RULES["projects"]}


def identity() -> str:
    return str(uuid4())


def resource_vector(value: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(type(amount) is not int or not 0 <= amount <= 100_000 for amount in value)
        or not any(value)
    ):
        raise ValueError("Gib für Holz, Stein und Erz gültige Beiträge bis jeweils 100.000 an.")
    return list(value)


def append_ledger(
    db: Connection,
    *,
    entry_key: str,
    project: dict[str, Any],
    actor_id: str,
    source_colony_id: str | None,
    event_type: str,
    resources: list[int],
    created: int,
) -> None:
    for index, amount in enumerate(resources):
        if amount <= 0:
            continue
        db.execute(
            "INSERT INTO alliance_project_ledger"
            "(id,entry_key,project_id,alliance_id,world_id,actor_id,source_colony_id,"
            "resource_index,event_type,amount,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                identity(),
                entry_key,
                project["id"],
                project["alliance_id"],
                project["world_id"],
                actor_id,
                source_colony_id,
                index,
                event_type,
                amount,
                created,
            ),
        )


def refund(
    systems: Any,
    db: Connection,
    project: dict[str, Any],
    *,
    actor_id: str,
    status: str,
    at: int,
    active_state: dict[str, Any] | None = None,
) -> None:
    changed = db.execute(
        "UPDATE alliance_projects SET status=?,completed=? WHERE id=? AND status='active' "
        "RETURNING id",
        (status, at, project["id"]),
    ).fetchone()
    if not changed:
        return
    for contribution in db.execute(
        "SELECT * FROM alliance_project_contributions WHERE project_id=? AND refunded=FALSE "
        "ORDER BY created,id",
        (project["id"],),
    ).fetchall():
        amounts = [int(amount) for amount in json.loads(str(contribution["resources_json"]))]
        source = db.execute(
            "SELECT colony_id FROM colonies WHERE colony_id=? AND user_id=? AND world_id=?",
            (
                contribution["source_colony_id"],
                contribution["user_id"],
                contribution["world_id"],
            ),
        ).fetchone()
        destination = (
            source
            or db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                (contribution["user_id"], contribution["world_id"]),
            ).fetchone()
        )
        if not destination:
            raise RuntimeError("Alliance project contributor has no refund colony in its world")
        destination_id = str(destination["colony_id"])
        if active_state is not None and str(active_state["colony_id"]) == destination_id:
            systems.credit_state(db, active_state, amounts, "Rückzahlung eines Allianzprojekts", at)
        else:
            systems.credit_colony(
                db,
                destination_id,
                amounts,
                "Rückzahlung eines Allianzprojekts",
                at,
            )
        append_ledger(
            db,
            entry_key=str(contribution["id"]) + ":refund",
            project=project,
            actor_id=actor_id,
            source_colony_id=str(destination["colony_id"]),
            event_type="refund",
            resources=amounts,
            created=at,
        )
        db.execute(
            "UPDATE alliance_project_contributions SET refunded=TRUE "
            "WHERE id=? AND refunded=FALSE",
            (contribution["id"],),
        )


def expire(
    systems: Any,
    db: Connection,
    now: int,
    active_state: dict[str, Any] | None = None,
) -> None:
    for row in db.execute(
        "SELECT * FROM alliance_projects WHERE status='active' AND deadline<=? "
        "ORDER BY deadline,id",
        (now,),
    ).fetchall():
        refund(
            systems,
            db,
            dict(row),
            actor_id="worker",
            status="expired",
            at=now,
            active_state=active_state,
        )
