"""Private, time-limited observations by Orbit probes."""

import json
from typing import Any

from . import orbit_economy, orbit_rules, orbit_station
from .database import Connection

INTEL_SECONDS = 24 * 3600
SCANNER_ORE = 750
SCANNER_ETHER = 180
SCANNER_SECONDS = 600
PHALANX_COST = 12
PHALANX_SECONDS = 300
PHALANX_RANGE = 5


def phalanx_scan(
    db: Connection,
    origin: dict[str, Any],
    owner: str,
    world: int,
    coordinates: tuple[int, int, int],
    now: int,
) -> None:
    if any(type(value) is not int for value in coordinates):
        raise ValueError("Ungültige Orbit-Koordinaten.")
    orbit_rules.planet_index(*coordinates)
    galaxy, system, _ = coordinates
    if galaxy != origin["galaxy"] or abs(system - origin["system_no"]) > PHALANX_RANGE:
        raise ValueError("Das Ziel liegt außerhalb der Sensorreichweite.")
    colony_id = origin["mission_id"]
    if not db.execute(
        "SELECT 1 FROM orbit_moons WHERE colony_id=? AND destroyed_at IS NULL AND scanner_ready_at<=?",
        (colony_id, now),
    ).fetchone():
        raise ValueError("Die Sensorphalanx benötigt einen fertigen Mondscanner.")
    if db.execute(
        "SELECT 1 FROM orbit_phalanx_scans WHERE colony_id=? AND observed_at>?",
        (colony_id, now - PHALANX_SECONDS),
    ).fetchone():
        raise ValueError("Die Sensorphalanx befindet sich in der Abklingzeit.")
    orbit_economy.refresh(db, origin, now)
    if origin["ether"] < PHALANX_COST:
        raise ValueError("Für die Sensorphalanx fehlt Äther.")

    result: dict[str, Any] = {"coordinates": list(coordinates), "missions": [], "jammed": False}
    target = db.execute(
        "SELECT mission_id,owner FROM orbit_planet_claims WHERE world_id=? AND galaxy=? "
        "AND system_no=? AND slot=? AND founded_at IS NOT NULL",
        (world, *coordinates),
    ).fetchone()
    if target:
        station = orbit_station.view(db, target["mission_id"], now)
        result["jammed"] = bool(
            target["owner"] != owner
            and station.get("active")
            and station["ships"].get("shield_carrier", 0)
        )
        if not result["jammed"]:
            result["missions"] = [
                dict(row)
                for row in db.execute(
                    "SELECT kind,due FROM ("
                    "SELECT 'attack' AS kind,due,id FROM orbit_attacks "
                    "WHERE target=? AND is_returning=FALSE AND due>? "
                    "UNION ALL SELECT 'freight' AS kind,due,id FROM orbit_transports "
                    "WHERE target=? AND is_returning=FALSE AND due>? AND salvage_report IS NULL"
                    ") incoming ORDER BY due,id LIMIT 10",
                    (target["mission_id"], now, target["mission_id"], now),
                )
            ]
    db.execute(
        "UPDATE orbit_economy SET ether=ether-? WHERE mission_id=?", (PHALANX_COST, colony_id)
    )
    db.execute(
        "INSERT INTO orbit_phalanx_scans(colony_id,observed_at,result) VALUES (?,?,?) "
        "ON CONFLICT(colony_id) DO UPDATE SET observed_at=excluded.observed_at,result=excluded.result",
        (colony_id, now, json.dumps(result)),
    )


def build_scanner(db: Connection, origin: dict[str, Any], now: int) -> None:
    moon = db.execute(
        "SELECT scanner_ready_at FROM orbit_moons WHERE colony_id=? AND destroyed_at IS NULL",
        (origin["mission_id"],),
    ).fetchone()
    if not moon or moon["scanner_ready_at"] is not None:
        raise ValueError("Ein Mond ohne Scanner wird benötigt.")
    orbit_economy.refresh(db, origin, now)
    if origin["ore"] < SCANNER_ORE or origin["ether"] < SCANNER_ETHER:
        raise ValueError("Für den Mondscanner fehlen Orbit-Ressourcen.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,ether=ether-? WHERE mission_id=?",
        (SCANNER_ORE, SCANNER_ETHER, origin["mission_id"]),
    )
    db.execute(
        "UPDATE orbit_moons SET scanner_ready_at=? WHERE colony_id=?",
        (now + SCANNER_SECONDS, origin["mission_id"]),
    )


def launch(
    db: Connection,
    mission: str,
    origin: dict[str, Any],
    galaxy: int,
    system: int,
    slot: int,
    now: int,
) -> None:
    orbit_economy.require_supply(origin, now)
    if any(type(value) is not int for value in (galaxy, system, slot)):
        raise ValueError("Ungültige Orbit-Koordinaten.")
    destination = orbit_rules.planet_index(galaxy, system, slot)
    start = orbit_rules.planet_index(origin["galaxy"], origin["system_no"], origin["slot"])
    seconds, fuel, _ = orbit_rules.quote_travel({"probe": 1}, abs(destination - start))
    orbit_economy.refresh(db, origin, now)
    if origin["ether"] < 2 * fuel:
        raise ValueError("Für den Sondenflug fehlt Äther.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-1 WHERE mission_id=? AND ship='probe' "
        "AND amount>0 RETURNING amount",
        (origin["mission_id"],),
    ).fetchone():
        raise ValueError("In dieser Kolonie ist keine Spähsonde verfügbar.")
    db.execute(
        "UPDATE orbit_economy SET ether=ether-? WHERE mission_id=?",
        (2 * fuel, origin["mission_id"]),
    )
    scanner = db.execute(
        "SELECT 1 FROM orbit_moons WHERE colony_id=? AND destroyed_at IS NULL AND scanner_ready_at<=?",
        (origin["mission_id"], now),
    ).fetchone()
    db.execute(
        "INSERT INTO orbit_scouts(id,origin,galaxy,system_no,slot,due,duration,rule_version,intel_level) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            mission,
            origin["mission_id"],
            galaxy,
            system,
            slot,
            now + seconds,
            seconds,
            orbit_rules.VERSION,
            2 if scanner else 1,
        ),
    )


def advance(db: Connection, now: int, event_id: str) -> None:
    while scout := db.execute(
        "SELECT s.*,p.owner,p.world_id FROM orbit_scouts s JOIN orbit_planet_claims p "
        "ON p.mission_id=s.origin WHERE s.due<=? AND s.rule_version=? AND s.id=?",
        (now, orbit_rules.VERSION, event_id),
    ).fetchone():
        if scout["is_returning"]:
            db.execute(
                "UPDATE orbit_ships SET amount=amount+1 WHERE mission_id=? AND ship='probe'",
                (scout["origin"],),
            )
            db.execute("DELETE FROM orbit_scouts WHERE id=?", (scout["id"],))
            continue
        target = (scout["world_id"], scout["galaxy"], scout["system_no"], scout["slot"])
        colony = db.execute(
            "SELECT mission_id,owner FROM orbit_planet_claims WHERE world_id=? AND galaxy=? "
            "AND system_no=? AND slot=? AND founded_at<=?",
            (*target, scout["due"]),
        ).fetchone()
        level = scout["intel_level"]
        ships = None
        moon = None
        if colony:
            station = orbit_station.view(db, colony["mission_id"], scout["due"])
            garrison = station["ships"] if station.get("active") else {}
            if colony["owner"] != scout["owner"] and garrison.get("shield_carrier", 0):
                level = 0
            elif level == 2:
                ships = db.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM orbit_ships WHERE mission_id=?",
                    (colony["mission_id"],),
                ).fetchone()[0] + sum(garrison.values())
                moon = (
                    db.execute(
                        "SELECT 1 FROM orbit_moons WHERE colony_id=? AND formed_at<=? "
                        "AND (destroyed_at IS NULL OR destroyed_at>?)",
                        (colony["mission_id"], scout["due"], scout["due"]),
                    ).fetchone()
                    is not None
                )
        db.execute(
            "INSERT INTO orbit_intel(observer,world_id,galaxy,system_no,slot,occupied,observed_at,intel_level,ships,moon) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(observer,world_id,galaxy,system_no,slot) "
            "DO UPDATE SET occupied=excluded.occupied,observed_at=excluded.observed_at,"
            "intel_level=excluded.intel_level,ships=excluded.ships,moon=excluded.moon "
            "WHERE orbit_intel.observed_at<=excluded.observed_at",
            (scout["owner"], *target, bool(colony) and level > 0, scout["due"], level, ships, moon),
        )
        if level == 0:
            db.execute("DELETE FROM orbit_scouts WHERE id=?", (scout["id"],))
        else:
            db.execute(
                "UPDATE orbit_scouts SET is_returning=TRUE,due=due+duration WHERE id=?",
                (scout["id"],),
            )
