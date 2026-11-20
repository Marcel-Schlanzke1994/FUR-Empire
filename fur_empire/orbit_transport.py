"""Transactional freight between owned Orbit colonies."""

from typing import Any

from . import orbit_economy, orbit_rules
from .database import Connection


def require_fleet_slot(db: Connection, owner: str, world: int) -> None:
    active = db.execute(
        "SELECT (SELECT COUNT(*) FROM orbit_transports t JOIN orbit_planet_claims p "
        "ON p.mission_id=t.origin WHERE p.owner=? AND p.world_id=?) + "
        "(SELECT COUNT(*) FROM orbit_planet_claims WHERE owner=? AND world_id=? "
        "AND founded_at IS NULL) + "
        "(SELECT COUNT(*) FROM orbit_scouts s JOIN orbit_planet_claims p "
        "ON p.mission_id=s.origin WHERE p.owner=? AND p.world_id=?) + "
        "(SELECT COUNT(*) FROM orbit_attacks a JOIN orbit_planet_claims p "
        "ON p.mission_id=a.origin WHERE p.owner=? AND p.world_id=?) + "
        "(SELECT COUNT(*) FROM orbit_expeditions e JOIN orbit_planet_claims p "
        "ON p.mission_id=e.origin WHERE p.owner=? AND p.world_id=? AND e.finished_at IS NULL) + "
        "(SELECT COUNT(*) FROM orbit_attack_wings w JOIN orbit_attacks a ON a.id=w.attack_id "
        "JOIN orbit_planet_claims p ON p.mission_id=w.colony_id WHERE p.owner=? AND p.world_id=?)",
        (owner, world, owner, world, owner, world, owner, world, owner, world, owner, world),
    ).fetchone()[0]
    if active >= orbit_rules.BASE_FLEET_LIMIT:
        raise ValueError("Das Orbit-Flottenlimit ist erreicht.")


def recall(db: Connection, origin: str, mission: str, now: int) -> None:
    if not db.execute(
        "UPDATE orbit_transports SET is_returning=TRUE,recalled=TRUE, "
        "due=CASE WHEN due-duration>=? THEN ?+1 ELSE ?+(?-due+duration) END "
        "WHERE id=? AND origin=? AND is_returning=FALSE AND due>? AND rule_version=? "
        "RETURNING id",
        (now, now, now, now, mission, origin, now, orbit_rules.VERSION),
    ).fetchone():
        raise ValueError("Dieser Orbit-Transport kann nicht zurückgerufen werden.")


def owned_colony(db: Connection, owner: str, world: int, colony: str) -> dict[str, Any]:
    row = db.execute(
        "SELECT e.*,p.galaxy,p.system_no,p.slot FROM orbit_economy e "
        "JOIN orbit_planet_claims p ON p.mission_id=e.mission_id "
        "WHERE p.owner=? AND p.world_id=? AND p.mission_id=? AND p.rule_version=?",
        (owner, world, colony, orbit_rules.VERSION),
    ).fetchone()
    if row is None:
        raise ValueError("Diese Orbit-Kolonie ist nicht verfügbar.")
    return dict(row)


def launch(
    db: Connection,
    mission: str,
    origin: dict[str, Any],
    target: dict[str, Any],
    ships: int,
    ore: int,
    ether: int,
    now: int,
    salvage_report: str | None = None,
) -> None:
    orbit_economy.require_supply(origin, now)
    if (
        (salvage_report is None and origin["mission_id"] == target["mission_id"])
        or type(ships) is not int
        or not 1 <= ships <= 100
        or type(ore) is not int
        or not 0 <= ore <= orbit_economy.STORAGE_CAP
        or type(ether) is not int
        or not 0 <= ether <= orbit_economy.STORAGE_CAP
        or (salvage_report is None and ore + ether == 0)
    ):
        raise ValueError("Ungültige Orbit-Fracht, Schiffsanzahl oder Zielkolonie.")
    start = orbit_rules.planet_index(origin["galaxy"], origin["system_no"], origin["slot"])
    end = orbit_rules.planet_index(target["galaxy"], target["system_no"], target["slot"])
    ship = "salvager" if salvage_report is not None else "freighter"
    seconds, fuel, capacity = orbit_rules.quote_travel({ship: ships}, max(1, abs(end - start)))
    orbit_economy.refresh(db, origin, now)
    if ore + ether > capacity:
        raise ValueError("Die Orbit-Fracht überschreitet die Ladekapazität.")
    if origin["ore"] < ore or origin["ether"] < ether + 2 * fuel:
        raise ValueError("Für Fracht oder Hin- und Rückflug fehlen Orbit-Ressourcen.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship=? "
        "AND amount>=? RETURNING amount",
        (ships, origin["mission_id"], ship, ships),
    ).fetchone():
        raise ValueError("Es stehen nicht genügend Schiffe bereit.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,ether=ether-? WHERE mission_id=?",
        (ore, ether + 2 * fuel, origin["mission_id"]),
    )
    db.execute(
        "INSERT INTO orbit_transports(id,origin,target,ore,ether,ships,due,duration,rule_version,salvage_report) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            mission,
            origin["mission_id"],
            target["mission_id"],
            ore,
            ether,
            ships,
            now + seconds,
            seconds,
            orbit_rules.VERSION,
            salvage_report,
        ),
    )


def salvage_target(db: Connection, report: str, user: str, world: int, now: int) -> dict[str, Any]:
    row = db.execute(
        "SELECT t.mission_id,t.galaxy,t.system_no,t.slot FROM orbit_debris d "
        "JOIN orbit_battle_reports b ON b.id=d.battle_id "
        "JOIN orbit_planet_claims o ON o.mission_id=b.origin "
        "JOIN orbit_planet_claims t ON t.mission_id=b.target "
        "WHERE d.battle_id=? AND t.world_id=? AND (o.owner=? OR t.owner=?) "
        "AND d.expires>? AND (d.ore>0 OR d.ether>0)",
        (report, world, user, user, now),
    ).fetchone()
    if not row:
        raise ValueError("Dieses Trümmerfeld ist nicht verfügbar.")
    return dict(row)


def advance(db: Connection, now: int, event_id: str) -> None:
    while trip := db.execute(
        "SELECT * FROM orbit_transports WHERE due<=? AND rule_version=? AND id=?",
        (now, orbit_rules.VERSION, event_id),
    ).fetchone():
        salvage = trip["salvage_report"]
        if trip["is_returning"]:
            if trip["recalled"] or salvage:
                db.execute(
                    "UPDATE orbit_economy SET ore_reserve=ore_reserve+?,"
                    "ether_reserve=ether_reserve+? WHERE mission_id=?",
                    (trip["ore"], trip["ether"], trip["origin"]),
                )
            db.execute(
                "UPDATE orbit_ships SET amount=amount+? WHERE mission_id=? AND ship=?",
                (trip["ships"], trip["origin"], "salvager" if salvage else "freighter"),
            )
            db.execute("DELETE FROM orbit_transports WHERE id=?", (trip["id"],))
        elif salvage:
            debris = db.execute(
                "SELECT ore,ether FROM orbit_debris WHERE battle_id=? AND expires>?",
                (salvage, trip["due"]),
            ).fetchone()
            ore = ether = 0
            if debris:
                capacity = orbit_rules.ship_catalog()["salvager"].cargo * trip["ships"]
                ore = min(capacity, debris["ore"])
                ether = min(capacity - ore, debris["ether"])
                db.execute(
                    "UPDATE orbit_debris SET ore=ore-?,ether=ether-? WHERE battle_id=?",
                    (ore, ether, salvage),
                )
            db.execute(
                "UPDATE orbit_transports SET is_returning=TRUE,due=due+duration,ore=?,ether=? WHERE id=?",
                (ore, ether, trip["id"]),
            )
        else:
            db.execute(
                "UPDATE orbit_economy SET ore_reserve=ore_reserve+?,ether_reserve=ether_reserve+? "
                "WHERE mission_id=?",
                (trip["ore"], trip["ether"], trip["target"]),
            )
            db.execute(
                "UPDATE orbit_transports SET is_returning=TRUE,due=due+duration,ore=0,ether=0 "
                "WHERE id=?",
                (trip["id"],),
            )


def collect(db: Connection, colony: dict[str, Any], now: int) -> None:
    orbit_economy.refresh(db, colony, now)
    ore = min(colony["ore_reserve"], orbit_economy.STORAGE_CAP - colony["ore"])
    ether = min(colony["ether_reserve"], orbit_economy.STORAGE_CAP - colony["ether"])
    if not ore and not ether:
        raise ValueError("Es ist keine Fracht abholbar oder das Lager ist voll.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore+?,ether=ether+?,ore_reserve=ore_reserve-?,"
        "ether_reserve=ether_reserve-? WHERE mission_id=?",
        (ore, ether, ore, ether, colony["mission_id"]),
    )
