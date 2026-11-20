"""Timed public NPC routes with separate PvE encounters and a bounded reward budget."""

import hashlib
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

from .database import Connection
from .terrain import MOVEMENT_COST, travel_times

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-npc-convoy-1.json").read_text(encoding="utf-8")
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = hashlib.sha256(SNAPSHOT.encode()).hexdigest()


class ConvoyError(ValueError):
    """An unavailable convoy action, suitable for displaying to its caller."""


def _route(db: Connection, world: int) -> list[tuple[int, int]]:
    """Choose a connected neutral trade route using only the world's real terrain."""
    posts = [
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y,state FROM world_outposts WHERE world_id=? ORDER BY sort_order,target_id",
            (world,),
        )
        if not json.loads(row["state"]).get("owner")
        and not json.loads(row["state"]).get("alliance_owner_id")
    ]
    passable = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute("SELECT x,y,terrain FROM world_terrain WHERE world_id=?", (world,))
        if not math.isinf(MOVEMENT_COST[str(row["terrain"])])
    }
    for origin in posts:
        if origin not in passable:
            continue
        parents: dict[tuple[int, int], tuple[int, int] | None] = {origin: None}
        distance = {origin: 0}
        queue = deque([origin])
        while queue:
            x, y = point = queue.popleft()
            for neighbor in ((x - 1, y), (x, y - 1), (x, y + 1), (x + 1, y)):
                if neighbor in passable and neighbor not in parents:
                    parents[neighbor] = point
                    distance[neighbor] = distance[point] + 1
                    queue.append(neighbor)
        destination = max(posts, key=lambda point: distance.get(point, -1))
        if distance.get(destination, 0) < 2:
            continue
        route = [destination]
        while (previous := parents[route[-1]]) is not None:
            route.append(previous)
        return route[::-1]
    raise ConvoyError("Es gibt keine begehbare Handelsroute zwischen neutralen Außenposten.")


def schedule(db: Connection, world: int, convoy_id: str, name: str, now: int) -> None:
    if db.execute(
        "SELECT 1 FROM npc_convoys WHERE world_id=? AND ends>? LIMIT 1", (world, now)
    ).fetchone():
        raise ConvoyError("In dieser Welt ist bereits ein Konvoi angesetzt.")
    route = _route(db, world)
    starts = now + int(RULES["warning_seconds"])
    db.execute(
        "INSERT INTO npc_convoys(id,world_id,name,rules_version,rules_digest,route,starts,ends) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            convoy_id,
            world,
            name,
            VERSION,
            DIGEST,
            json.dumps(route),
            starts,
            starts + int(RULES["stages"]) * int(RULES["stage_seconds"]),
        ),
    )


def _convoy(db: Connection, world: int, convoy_id: str) -> dict[str, Any]:
    row = db.execute(
        "SELECT * FROM npc_convoys WHERE id=? AND world_id=?", (convoy_id, world)
    ).fetchone()
    if row is None:
        raise ConvoyError("Dieser Konvoi ist in deiner aktiven Welt nicht verfügbar.")
    if row["rules_version"] != VERSION or row["rules_digest"] != DIGEST:
        raise RuntimeError("Unsupported NPC convoy rule snapshot")
    return dict(row)


def checkpoints(convoy: dict[str, Any]) -> list[dict[str, int]]:
    route = json.loads(convoy["route"])
    return [
        {
            "x": route[index][0],
            "y": route[index][1],
            "stage": stage,
            "starts": int(convoy["starts"]) + stage * int(RULES["stage_seconds"]),
            "ends": int(convoy["starts"]) + (stage + 1) * int(RULES["stage_seconds"]),
        }
        for stage, index in enumerate((0, len(route) // 2, len(route) - 1))
    ]


def rendezvous(
    db: Connection, convoy: dict[str, Any], origin: tuple[int, int], now: int
) -> dict[str, int] | None:
    times = travel_times(db, origin, int(convoy["world_id"]))
    for point in checkpoints(convoy):
        travel = times.get((point["x"], point["y"]))
        if travel is None:
            continue
        due = max(now + travel, point["starts"])
        if due < point["ends"]:
            return {**point, "due": due, "travel_seconds": travel}
    return None


def join(
    db: Connection,
    world: int,
    convoy_id: str,
    user: str,
    mission_id: str,
    origin: tuple[int, int],
    role: str,
    rangers: int,
    now: int,
) -> dict[str, Any]:
    convoy = _convoy(db, world, convoy_id)
    if not convoy["starts"] <= now < convoy["ends"]:
        raise ConvoyError("Das Konvoi-Zeitfenster ist noch nicht aktiv oder bereits beendet.")
    if role not in ("escort", "raid") or not 1 <= rangers <= int(RULES["maximum_rangers"]):
        raise ConvoyError("Ungültige Konvoi-Truppen oder Rolle.")
    if db.execute(
        "SELECT 1 FROM npc_convoy_participants WHERE convoy_id=? AND user_id=?", (convoy_id, user)
    ).fetchone():
        raise ConvoyError("Dein Teilnahmeplatz für diesen Konvoi wurde bereits genutzt.")
    if db.execute(
        "SELECT COUNT(*) FROM npc_convoy_participants WHERE convoy_id=?", (convoy_id,)
    ).fetchone()[0] >= int(RULES["slots"]):
        raise ConvoyError("Alle Konvoi-Teilnahmeplätze sind belegt.")
    point = rendezvous(db, convoy, origin, now)
    if point is None:
        raise ConvoyError("Deine Ranger erreichen keinen Treffpunkt mehr rechtzeitig.")
    db.execute(
        "INSERT INTO npc_convoy_participants "
        "(convoy_id,user_id,mission_id,role,rangers,stage,started,due,travel_seconds) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            convoy_id,
            user,
            mission_id,
            role,
            rangers,
            point["stage"],
            now,
            point["due"],
            point["travel_seconds"],
        ),
    )
    return {
        "id": mission_id,
        "kind": "npc_convoy",
        "key": convoy_id,
        "label": "Konvoi-Eskorte" if role == "escort" else "NPC-Konvoiüberfall",
        "due": point["due"],
    }


def resolve(
    db: Connection, world: int, convoy_id: str, user: str, mission_id: str, due: int
) -> dict[str, Any]:
    convoy = _convoy(db, world, convoy_id)
    row = db.execute(
        "SELECT * FROM npc_convoy_participants WHERE convoy_id=? AND user_id=? AND mission_id=?",
        (convoy_id, user, mission_id),
    ).fetchone()
    if row is None or row["status"] != "marching" or row["due"] != due:
        raise RuntimeError("Invalid NPC convoy mission record")
    point = checkpoints(convoy)[row["stage"]]
    if not point["starts"] <= due < point["ends"]:
        raise RuntimeError("NPC convoy mission outside its checkpoint window")
    victory = row["rangers"] * int(RULES["power_per_ranger"]) >= int(
        RULES["npc_power"][row["role"]]
    )
    loss_percent = int(RULES["victory_loss_percent"] if victory else RULES["defeat_loss_percent"])
    survivors = row["rangers"] - (row["rangers"] * loss_percent + 99) // 100
    reward = int(RULES["reward_ore"]) if victory else 0
    db.execute(
        "UPDATE npc_convoy_participants SET status='completed',victory=?,survivors=?,reward_ore=? "
        "WHERE convoy_id=? AND user_id=? AND status='marching'",
        (int(victory), survivors, reward, convoy_id, user),
    )
    return {
        "victory": victory,
        "survivors": survivors,
        "reward_ore": reward,
        "return_due": due + row["travel_seconds"],
        "role": row["role"],
    }


def recall(
    db: Connection, world: int, convoy_id: str, user: str, mission_id: str, now: int
) -> dict[str, int]:
    _convoy(db, world, convoy_id)
    row = db.execute(
        "UPDATE npc_convoy_participants SET status='cancelled',survivors=rangers "
        "WHERE convoy_id=? AND user_id=? AND mission_id=? AND status='marching' AND due>? "
        "RETURNING rangers,started,travel_seconds",
        (convoy_id, user, mission_id, now),
    ).fetchone()
    if row is None:
        raise ConvoyError("Dieser Konvoiauftrag kann nicht mehr zurückgerufen werden.")
    return {
        "survivors": int(row["rangers"]),
        "return_due": now + max(5, min(now - row["started"], row["travel_seconds"])),
    }


def claim(db: Connection, world: int, convoy_id: str, user: str, now: int) -> int:
    _convoy(db, world, convoy_id)
    row = db.execute(
        "UPDATE npc_convoy_participants SET claimed_at=? WHERE convoy_id=? AND user_id=? "
        "AND status='completed' AND reward_ore>0 AND claimed_at IS NULL RETURNING reward_ore",
        (now, convoy_id, user),
    ).fetchone()
    if row is None:
        raise ConvoyError("Für diesen Konvoi ist keine Belohnung offen.")
    return int(row["reward_ore"])


def view(
    db: Connection, world: int, user: str, origin: tuple[int, int], now: int
) -> dict[str, Any]:
    row = db.execute(
        "SELECT * FROM npc_convoys WHERE world_id=? AND ends>? ORDER BY starts DESC,id LIMIT 1",
        (world, now),
    ).fetchone()
    convoy = None
    if row is not None:
        raw = dict(row)
        own = db.execute(
            "SELECT mission_id,role,rangers,due,status,victory,survivors FROM npc_convoy_participants "
            "WHERE convoy_id=? AND user_id=?",
            (row["id"], user),
        ).fetchone()
        booked = db.execute(
            "SELECT COUNT(*) FROM npc_convoy_participants WHERE convoy_id=?", (row["id"],)
        ).fetchone()[0]
        point = rendezvous(db, raw, origin, now)
        convoy = {
            "id": row["id"],
            "name": row["name"],
            "starts": row["starts"],
            "ends": row["ends"],
            "checkpoints": checkpoints(raw),
            "rendezvous": point,
            "booked": booked,
            "own": dict(own) if own else None,
            "can_join": own is None
            and row["starts"] <= now
            and point is not None
            and booked < int(RULES["slots"]),
        }
    rewards = [
        dict(row)
        for row in db.execute(
            "SELECT c.id,c.name,p.reward_ore FROM npc_convoy_participants p "
            "JOIN npc_convoys c ON c.id=p.convoy_id WHERE c.world_id=? AND p.user_id=? "
            "AND p.status='completed' AND p.reward_ore>0 AND p.claimed_at IS NULL "
            "ORDER BY c.starts,c.id LIMIT 20",
            (world, user),
        )
    ]
    return {
        "convoy": convoy,
        "rewards": rewards,
        "rules_version": VERSION,
        "slots": RULES["slots"],
        "maximum_rangers": RULES["maximum_rangers"],
        "power_per_ranger": RULES["power_per_ranger"],
        "npc_power": RULES["npc_power"],
        "victory_loss_percent": RULES["victory_loss_percent"],
        "defeat_loss_percent": RULES["defeat_loss_percent"],
        "reward_ore": RULES["reward_ore"],
    }
