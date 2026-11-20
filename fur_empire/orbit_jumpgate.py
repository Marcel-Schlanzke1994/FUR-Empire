"""Station gates transfer ships atomically between two owned Orbit colonies."""

from typing import Any

from . import orbit_economy, orbit_rules, orbit_station
from .database import Connection


def build(db: Connection, colony: dict[str, Any], hq: int, now: int) -> None:
    colony_id = colony["mission_id"]
    station = orbit_station.view(db, colony_id, now)
    if hq < orbit_rules.JUMPGATE_HQ or station.get("level", 0) < 2:
        raise ValueError(
            "Ein Sprungtor benötigt eine Stationsstufe 2 und eine Terra-Kommandozentrale Stufe 10."
        )
    orbit_economy.refresh(db, colony, now)
    if colony["ore"] < orbit_rules.JUMPGATE_ORE:
        raise ValueError("Für das Sprungtor fehlt Orbit-Erz.")
    if not db.execute(
        "INSERT INTO orbit_jumpgates(colony_id,ready_at) VALUES (?,?) "
        "ON CONFLICT(colony_id) DO NOTHING RETURNING colony_id",
        (colony_id, now + orbit_rules.JUMPGATE_SECONDS),
    ).fetchone():
        raise ValueError("Für diese Kolonie gibt es bereits ein Sprungtor.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-? WHERE mission_id=?",
        (orbit_rules.JUMPGATE_ORE, colony_id),
    )


def jump(db: Connection, origin: str, target: str, ship: str, count: int, now: int) -> None:
    if (
        origin == target
        or ship not in orbit_rules.ship_catalog()
        or type(count) is not int
        or not 1 <= count <= 100
    ):
        raise ValueError("Ungültiges Sprungziel, Schiff oder Stückzahl.")
    for colony in (origin, target):
        if (
            not orbit_station.view(db, colony, now).get("active")
            or not db.execute(
                "UPDATE orbit_jumpgates SET cooldown_until=? "
                "WHERE colony_id=? AND ready_at<=? AND cooldown_until<=? RETURNING colony_id",
                (now + orbit_rules.JUMPGATE_COOLDOWN, colony, now, now),
            ).fetchone()
        ):
            raise ValueError("Beide Sprungtore müssen einsatzbereit sein.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship=? "
        "AND amount>=? RETURNING amount",
        (count, origin, ship, count),
    ).fetchone():
        raise ValueError("Es stehen nicht genügend Schiffe für den Sprung bereit.")
    db.execute(
        "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,?,?) "
        "ON CONFLICT(mission_id,ship) DO UPDATE SET amount=orbit_ships.amount+excluded.amount",
        (target, ship, count),
    )
