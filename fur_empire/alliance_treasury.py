"""Versioned, world-scoped alliance treasury rules and append-only evidence."""

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .database import Connection

RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-alliance-treasury-3.json").read_text(encoding="utf-8")
)
RULES_VERSION = str(RULES["version"])
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = "sha256:" + hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
EXPIRY_SECONDS = int(RULES["withdrawals"]["expiry_seconds"])
APPROVAL_THRESHOLD = int(RULES["withdrawals"]["approval_threshold_gross_resource_units"])


def identity() -> str:
    return str(uuid4())


def resource_vector(value: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(type(amount) is not int or not 0 <= amount <= 100_000 for amount in value)
        or not any(value)
    ):
        raise ValueError("Gib für Holz, Stein und Erz gültige Beträge bis jeweils 100.000 an.")
    return list(value)


def gross_vector(net: list[int]) -> tuple[list[int], list[int]]:
    basis_points = int(RULES["withdrawals"]["recipient_fee_basis_points_per_resource"])
    gross = [
        (amount * 10_000 + (10_000 - basis_points) - 1) // (10_000 - basis_points) for amount in net
    ]
    fee = [amount - payout for amount, payout in zip(gross, net)]
    return gross, fee


def ensure_balances(db: Connection, alliance_id: str, world_id: int) -> None:
    for resource_index in range(3):
        db.execute(
            "INSERT INTO alliance_treasury_balances"
            "(alliance_id,world_id,resource_index) VALUES (?,?,?) "
            "ON CONFLICT(alliance_id,world_id,resource_index) DO NOTHING",
            (alliance_id, world_id, resource_index),
        )


def change_balance(
    db: Connection,
    alliance_id: str,
    world_id: int,
    available: list[int],
    reserved: list[int],
) -> None:
    ensure_balances(db, alliance_id, world_id)
    for resource_index, (available_delta, reserved_delta) in enumerate(zip(available, reserved)):
        changed = db.execute(
            "UPDATE alliance_treasury_balances SET available=available+?,reserved=reserved+? "
            "WHERE alliance_id=? AND world_id=? AND resource_index=? "
            "AND available+?>=0 AND reserved+?>=0 RETURNING resource_index",
            (
                available_delta,
                reserved_delta,
                alliance_id,
                world_id,
                resource_index,
                available_delta,
                reserved_delta,
            ),
        ).fetchone()
        if not changed:
            raise ValueError("Der verfügbare Kassenbestand reicht dafür nicht aus.")


def append_ledger(
    db: Connection,
    *,
    entry_key: str,
    alliance_id: str,
    world_id: int,
    actor_id: str,
    request_id: str | None,
    event_type: str,
    available: list[int],
    reserved: list[int],
    details: dict[str, Any],
    created: int,
) -> None:
    encoded = json.dumps(details, ensure_ascii=False, sort_keys=True)
    for resource_index, (available_delta, reserved_delta) in enumerate(zip(available, reserved)):
        db.execute(
            "INSERT INTO alliance_treasury_ledger"
            "(id,entry_key,alliance_id,world_id,actor_id,request_id,resource_index,event_type,"
            "delta_available,delta_reserved,details,rules_version,created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identity(),
                entry_key,
                alliance_id,
                world_id,
                actor_id,
                request_id,
                resource_index,
                event_type,
                available_delta,
                reserved_delta,
                encoded,
                RULES_VERSION,
                created,
            ),
        )


def release_request(
    db: Connection,
    request: dict[str, Any],
    *,
    actor_id: str,
    status: str,
    at: int,
) -> None:
    gross = json.loads(str(request["gross_json"]))
    change_balance(
        db,
        str(request["alliance_id"]),
        int(request["world_id"]),
        [int(amount) for amount in gross],
        [-int(amount) for amount in gross],
    )
    append_ledger(
        db,
        entry_key=str(request["id"]) + ":refund",
        alliance_id=str(request["alliance_id"]),
        world_id=int(request["world_id"]),
        actor_id=actor_id,
        request_id=str(request["id"]),
        event_type="withdrawal_refund",
        available=[int(amount) for amount in gross],
        reserved=[-int(amount) for amount in gross],
        details={"gross": gross, "status": status},
        created=at,
    )
    db.execute(
        "UPDATE alliance_treasury_requests SET status=?,completed=? WHERE id=? AND status='pending'",
        (status, at, request["id"]),
    )


def expire(db: Connection, now: int) -> None:
    for row in db.execute(
        "SELECT * FROM alliance_treasury_requests WHERE status='pending' AND expires<=? "
        "ORDER BY expires,id",
        (now,),
    ).fetchall():
        release_request(
            db,
            dict(row),
            actor_id="worker",
            status="expired",
            at=now,
        )
