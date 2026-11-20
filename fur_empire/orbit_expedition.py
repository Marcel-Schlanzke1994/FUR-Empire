"""Private Orbit expeditions with persistent outbound and return stages."""

import hashlib
import json
import secrets
from typing import Any

from . import orbit_economy, orbit_rules
from .database import Connection

SPECIAL_EVENTS = {"solar": 24, "anomaly": 36, "boss": 48}
EVENT_REWARD_LIMIT = 20


def start_event(db: Connection, event: str, world: int, kind: str, now: int) -> None:
    if kind not in SPECIAL_EVENTS:
        raise ValueError("Unbekanntes Orbit-Ereignis.")
    if db.execute(
        "SELECT 1 FROM orbit_special_events WHERE world_id=? AND ends>?", (world, now)
    ).fetchone():
        raise ValueError("In dieser Welt läuft bereits ein Orbit-Ereignis.")
    db.execute(
        "INSERT INTO orbit_special_events(id,world_id,kind,starts,ends,rule_version) VALUES (?,?,?,?,?,?)",
        (event, world, kind, now, now + SPECIAL_EVENTS[kind] * 3600, orbit_rules.VERSION),
    )


def resolve_special(seed: str, count: int, kind: str) -> dict[str, int | str]:
    roll = int.from_bytes(hashlib.sha256(bytes.fromhex(seed)).digest()[:4], "big") % 100
    capacity = orbit_rules.ship_catalog()["courier"].cargo * count
    if kind == "boss":
        if count < 8 or roll < 30:
            return {"event": "boss_retreat", "lost": (count + 3) // 4, "ore": 0, "ether": 0}
        return {"event": "boss_salvage", "lost": 1, "ore": min(capacity, 240), "ether": 0}
    if kind == "solar":
        if roll < 45:
            return {"event": "ion_storm", "lost": (count + 3) // 4, "ore": 0, "ether": 0}
        return {"event": "solar_samples", "lost": 0, "ore": 0, "ether": min(capacity, 120)}
    if roll < 25:
        return {"event": "quiet", "lost": 0, "ore": 0, "ether": 0}
    return {"event": "anomaly", "lost": 0, "ore": 0, "ether": min(capacity, 160)}


def resolve(seed: str, count: int) -> dict[str, int | str]:
    roll = int.from_bytes(hashlib.sha256(bytes.fromhex(seed)).digest()[:4], "big") % 100
    if roll < 25:
        return {"event": "ion_storm", "lost": (count + 3) // 4, "ore": 0, "ether": 0}
    if roll < 60:
        return {"event": "quiet", "lost": 0, "ore": 0, "ether": 0}
    capacity = orbit_rules.ship_catalog()["courier"].cargo * count
    if roll < 85:
        return {"event": "ruins", "lost": 0, "ore": min(capacity, 30 * count), "ether": 0}
    return {"event": "anomaly", "lost": 0, "ore": 0, "ether": min(capacity, 16 * count)}


def launch(
    db: Connection,
    mission: str,
    origin: dict[str, Any],
    coordinates: tuple[int, int, int],
    count: int,
    now: int,
    *,
    world: int,
    special_event: str | None = None,
) -> None:
    orbit_economy.require_supply(origin, now)
    if (
        any(type(value) is not int for value in coordinates)
        or type(count) is not int
        or not 1 <= count <= 100
    ):
        raise ValueError("Ungültige Orbit-Expedition.")
    end = orbit_rules.planet_index(*coordinates)
    start = orbit_rules.planet_index(origin["galaxy"], origin["system_no"], origin["slot"])
    seconds, fuel, _ = orbit_rules.quote_travel({"courier": count}, abs(end - start))
    if (
        special_event is not None
        and not db.execute(
            "SELECT 1 FROM orbit_special_events WHERE id=? AND world_id=? AND starts<=? "
            "AND ends>? AND rule_version=?",
            (special_event, world, now, now + seconds, orbit_rules.VERSION),
        ).fetchone()
    ):
        raise ValueError("Das Orbit-Ereignis ist nicht erreichbar oder endet vor der Ankunft.")
    orbit_economy.refresh(db, origin, now)
    if origin["ether"] < 2 * fuel:
        raise ValueError("Für die Expedition fehlt Äther.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship='courier' "
        "AND amount>=? RETURNING amount",
        (count, origin["mission_id"], count),
    ).fetchone():
        raise ValueError("Für die Expedition stehen nicht genügend Kurierschiffe bereit.")
    db.execute(
        "UPDATE orbit_economy SET ether=ether-? WHERE mission_id=?",
        (2 * fuel, origin["mission_id"]),
    )
    db.execute(
        "INSERT INTO orbit_expeditions(id,origin,galaxy,system_no,slot,ships,due,duration,seed,rule_version,special_event) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            mission,
            origin["mission_id"],
            *coordinates,
            count,
            now + seconds,
            seconds,
            secrets.token_hex(32),
            orbit_rules.VERSION,
            special_event,
        ),
    )


def advance(db: Connection, now: int, event_id: str) -> None:
    while trip := db.execute(
        "SELECT * FROM orbit_expeditions WHERE finished_at IS NULL AND due<=? AND rule_version=? "
        "AND id=?",
        (now, orbit_rules.VERSION, event_id),
    ).fetchone():
        if trip["result"] is None:
            if trip["special_event"] is None:
                result = resolve(trip["seed"], trip["ships"])
            else:
                event = db.execute(
                    "SELECT e.kind,p.owner FROM orbit_special_events e "
                    "JOIN orbit_planet_claims p ON p.world_id=e.world_id "
                    "WHERE e.id=? AND p.mission_id=? AND e.rule_version=?",
                    (trip["special_event"], trip["origin"], trip["rule_version"]),
                ).fetchone()
                result = resolve_special(trip["seed"], trip["ships"], event["kind"])
                if (result["ore"] or result["ether"]) and not db.execute(
                    "INSERT INTO orbit_event_rewards(event_id,user_id,mission_id) "
                    "SELECT ?,?,? WHERE (SELECT COUNT(*) FROM orbit_event_rewards WHERE event_id=?)<? "
                    "ON CONFLICT DO NOTHING RETURNING mission_id",
                    (
                        trip["special_event"],
                        event["owner"],
                        trip["id"],
                        trip["special_event"],
                        EVENT_REWARD_LIMIT,
                    ),
                ).fetchone():
                    result["ore"] = result["ether"] = 0
                    result["event"] = "reward_limit"
            db.execute(
                "UPDATE orbit_expeditions SET result=?,due=due+duration WHERE id=?",
                (json.dumps(result), trip["id"]),
            )
        else:
            result = json.loads(trip["result"])
            db.execute(
                "UPDATE orbit_ships SET amount=amount+? WHERE mission_id=? AND ship='courier'",
                (trip["ships"] - result["lost"], trip["origin"]),
            )
            db.execute(
                "UPDATE orbit_economy SET ore_reserve=ore_reserve+?,ether_reserve=ether_reserve+? "
                "WHERE mission_id=?",
                (result["ore"], result["ether"], trip["origin"]),
            )
            db.execute("UPDATE orbit_expeditions SET finished_at=due WHERE id=?", (trip["id"],))
