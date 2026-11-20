"""Owned Orbit stations with paid upkeep and a separate defense garrison."""

from typing import Any

from . import orbit_economy, orbit_rules
from .database import Connection

MAX_LEVEL = 3
UPKEEP_SECONDS = 86400


def view(db: Connection, colony: str, now: int) -> dict[str, Any]:
    row = db.execute("SELECT * FROM orbit_stations WHERE colony_id=?", (colony,)).fetchone()
    if not row:
        return {}
    station = dict(row)
    station["active"] = station["level"] > 0 and station["maintained_until"] > now
    station["ships"] = {
        ship["ship"]: ship["amount"]
        for ship in db.execute(
            "SELECT ship,amount FROM orbit_station_ships WHERE colony_id=? AND amount>0 ORDER BY ship",
            (colony,),
        )
    }
    return station


def command(
    db: Connection, colony: dict[str, Any], action: str, ship: str, count: int, now: int
) -> None:
    key = colony["mission_id"]
    station = view(db, key, now)
    level = station.get("level", 0)
    if action in ("orbit_station_build", "orbit_station_upkeep"):
        if action == "orbit_station_build":
            if (
                station.get("ready_at") is not None
                or level >= MAX_LEVEL
                or colony["shipbuilding_ready_at"] is None
                or colony["shipbuilding_ready_at"] > now
            ):
                raise ValueError(
                    "Stationsbau benötigt Schiffbauforschung und einen freien Ausbauplatz."
                )
            ore, ether = 600 * (level + 1), 120 * (level + 1)
        else:
            if level == 0 or station["maintained_until"] > now + UPKEEP_SECONDS:
                raise ValueError("Stationswartung ist derzeit nicht verfügbar.")
            ore, ether = 0, 24 * level
        orbit_economy.refresh(db, colony, now)
        if colony["ore"] < ore or colony["ether"] < ether:
            raise ValueError("Für die Station fehlen Orbit-Ressourcen.")
        db.execute(
            "UPDATE orbit_economy SET ore=ore-?,ether=ether-? WHERE mission_id=?", (ore, ether, key)
        )
        if action == "orbit_station_build":
            due = now + 300 * (level + 1)
            db.execute(
                "INSERT INTO orbit_stations(colony_id,level,ready_at,maintained_until) VALUES (?,0,?,?) "
                "ON CONFLICT(colony_id) DO UPDATE SET ready_at=excluded.ready_at",
                (key, due, due + UPKEEP_SECONDS),
            )
        else:
            db.execute(
                "UPDATE orbit_stations SET maintained_until=? WHERE colony_id=?",
                (max(now, station["maintained_until"]) + UPKEEP_SECONDS, key),
            )
        return

    if (
        level == 0
        or ship not in orbit_rules.ship_catalog()
        or type(count) is not int
        or not 1 <= count <= 100
    ):
        raise ValueError("Ungültige Station, Schiffsklasse oder Stückzahl.")
    if action == "orbit_station_deploy":
        if not station["active"] or sum(station["ships"].values()) + count > level * 100:
            raise ValueError("Die Stationsgarnison ist voll oder außer Betrieb.")
        source, source_key = "orbit_ships", "mission_id"
        target, target_key = "orbit_station_ships", "colony_id"
    else:
        source, source_key = "orbit_station_ships", "colony_id"
        target, target_key = "orbit_ships", "mission_id"
    if not db.execute(
        f"UPDATE {source} SET amount=amount-? WHERE {source_key}=? AND ship=? "
        "AND amount>=? RETURNING amount",
        (count, key, ship, count),
    ).fetchone():
        raise ValueError("Es stehen nicht genügend Schiffe bereit.")
    db.execute(
        f"INSERT INTO {target}({target_key},ship,amount) VALUES (?,?,?) "
        f"ON CONFLICT({target_key},ship) DO UPDATE SET amount={target}.amount+excluded.amount",
        (key, ship, count),
    )
