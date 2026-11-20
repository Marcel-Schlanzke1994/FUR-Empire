"""Orbit-1 starter infrastructure, independent of Terra balances."""

from typing import Any

from . import orbit_rules
from .database import Connection

STORAGE_CAP = 10_000
MAX_LEVEL = 10
ORE_PER_HOUR = 60
STARTER_SUPPLY_SECONDS = 7 * 86400
SUPPLY_SECONDS = 86400
SUPPLY_ETHER = 12
BUILDINGS = {"solar": (80, 60), "refinery": (120, 90)}


def initialize(db: Connection) -> None:
    db.execute(
        "INSERT INTO orbit_economy(mission_id,ore,ether,solar,refinery,updated_at,remainder,supplied_until) "
        "SELECT p.mission_id,500,0,1,0,p.founded_at,0,p.founded_at+? FROM orbit_planet_claims p "
        "WHERE p.founded_at IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM orbit_economy e WHERE e.mission_id=p.mission_id) "
        "ON CONFLICT(mission_id) DO NOTHING",
        (STARTER_SUPPLY_SECONDS,),
    )


def require_supply(colony: dict[str, Any], now: int) -> None:
    if colony["supplied_until"] <= now:
        raise ValueError("Die Flottenversorgung dieser Orbit-Kolonie ist abgelaufen.")


def renew_supply(db: Connection, colony: dict[str, Any], now: int) -> None:
    until = colony["supplied_until"]
    if until >= now + SUPPLY_SECONDS:
        raise ValueError("Die Flotte ist bereits für mindestens 24 Stunden versorgt.")
    refresh(db, colony, now)
    if colony["ether"] < SUPPLY_ETHER:
        raise ValueError("Für die Flottenversorgung fehlt Äther.")
    db.execute(
        "UPDATE orbit_economy SET ether=ether-?,supplied_until=? WHERE mission_id=?",
        (SUPPLY_ETHER, max(now, until) + SUPPLY_SECONDS, colony["mission_id"]),
    )


def produce(row: dict[str, Any], until: int) -> None:
    seconds = max(0, until - row["updated_at"])
    ore, ore_remainder = divmod(row["ore_remainder"] + seconds * ORE_PER_HOUR, 3600)
    row["ore"] = min(STORAGE_CAP, row["ore"] + ore)
    row["ore_remainder"] = ore_remainder if row["ore"] < STORAGE_CAP else 0
    powered = min(row["solar"], row["refinery"])
    amount, remainder = divmod(row["remainder"] + seconds * powered * 12, 3600)
    row["ether"] = min(STORAGE_CAP, row["ether"] + amount)
    row["remainder"] = remainder if row["ether"] < STORAGE_CAP else 0
    row["updated_at"] += seconds


def refresh(
    db: Connection, row: dict[str, Any], now: int, *, complete_building: bool = False
) -> None:
    job = row["job"]
    if job is not None and row["due"] <= now:
        produce(row, row["due"])
        if complete_building:
            row[job] += 1
            row["job"] = row["due"] = None
            produce(row, now)
    else:
        produce(row, now)
    db.execute(
        "UPDATE orbit_economy SET ore=?,ore_remainder=?,ether=?,solar=?,refinery=?,"
        "updated_at=?,remainder=?,job=?,due=? "
        "WHERE mission_id=?",
        tuple(
            row[key]
            for key in (
                "ore",
                "ore_remainder",
                "ether",
                "solar",
                "refinery",
                "updated_at",
                "remainder",
                "job",
                "due",
                "mission_id",
            )
        ),
    )


def build(db: Connection, row: dict[str, Any], building: str, now: int) -> None:
    refresh(db, row, now)
    if building not in BUILDINGS or row["job"] is not None or row[building] >= MAX_LEVEL:
        raise ValueError("Dieser Orbit-Ausbau ist derzeit nicht verfügbar.")
    base_cost, base_duration = BUILDINGS[building]
    level = row[building] + 1
    cost = base_cost * level
    if row["ore"] < cost:
        raise ValueError("Für diesen Orbit-Ausbau fehlt Erz.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,job=?,due=? WHERE mission_id=?",
        (cost, building, now + base_duration * level, row["mission_id"]),
    )


def research_shipbuilding(db: Connection, row: dict[str, Any], now: int) -> None:
    refresh(db, row, now)
    if row["refinery"] < 1 or row["shipbuilding_ready_at"] is not None:
        raise ValueError("Schiffbauforschung benötigt eine Raffinerie und ist einmalig.")
    if row["ore"] < orbit_rules.SHIPBUILDING_ORE:
        raise ValueError("Für die Schiffbauforschung fehlt Orbit-Erz.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,shipbuilding_ready_at=? WHERE mission_id=?",
        (orbit_rules.SHIPBUILDING_ORE, now + orbit_rules.SHIPBUILDING_SECONDS, row["mission_id"]),
    )


def build_defense(db: Connection, row: dict[str, Any], now: int) -> None:
    refresh(db, row, now)
    rule = orbit_rules.DEFENSE
    if row["shipbuilding_ready_at"] is None or row["shipbuilding_ready_at"] > now:
        raise ValueError("Die Verteidigungsplattform benötigt abgeschlossene Schiffbauforschung.")
    if row["defense_ready_at"] is not None:
        raise ValueError("Für diese Kolonie gibt es bereits eine Verteidigungsplattform.")
    if row["ore"] < rule.ore_cost or row["ether"] < rule.ether_cost:
        raise ValueError("Für die Verteidigungsplattform fehlen Orbit-Ressourcen.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,ether=ether-?,defense_ready_at=? WHERE mission_id=?",
        (
            rule.ore_cost,
            rule.ether_cost,
            now + orbit_rules.DEFENSE_BUILD_SECONDS,
            row["mission_id"],
        ),
    )


def build_ammunition(db: Connection, row: dict[str, Any], kind: str, count: int, now: int) -> None:
    if (
        kind not in orbit_rules.AMMUNITION_COSTS
        or type(count) is not int
        or not 1 <= count <= orbit_rules.AMMUNITION_CAP
    ):
        raise ValueError("Ungültige Orbit-Munition oder Stückzahl.")
    ready = row["shipbuilding_ready_at"]
    if ready is None or ready > now:
        raise ValueError("Die Orbit-Munition benötigt abgeschlossene Schiffbauforschung.")
    refresh(db, row, now)
    if row[kind] + count > orbit_rules.AMMUNITION_CAP:
        raise ValueError("Das Munitionslager ist voll.")
    ore, ether = orbit_rules.AMMUNITION_COSTS[kind]
    if row["ore"] < ore * count or row["ether"] < ether * count:
        raise ValueError("Für die Orbit-Munition fehlen Ressourcen.")
    db.execute(
        f"UPDATE orbit_economy SET {kind}={kind}+?,ore=ore-?,ether=ether-? WHERE mission_id=?",
        (count, ore * count, ether * count, row["mission_id"]),
    )


def order_ships(
    db: Connection,
    row: dict[str, Any],
    ship: str,
    amount: int,
    now: int,
    *,
    repair: bool = False,
) -> None:
    rule = orbit_rules.ship_catalog().get(ship)
    if rule is None or type(amount) is not int or not 1 <= amount <= 100:
        raise ValueError("Ungültige Schiffsklasse oder Stückzahl.")
    if row["shipbuilding_ready_at"] is None or row["shipbuilding_ready_at"] > now:
        raise ValueError("Schließe zuerst die Schiffbauforschung ab.")
    refresh(db, row, now)
    ore_cost = (rule.ore_cost + 1) // 2 if repair else rule.ore_cost
    ether_cost = (rule.ether_cost + 1) // 2 if repair else rule.ether_cost
    ore, ether = ore_cost * amount, ether_cost * amount
    if row["ore"] < ore or row["ether"] < ether:
        raise ValueError("Für den Schiffsbau fehlen Orbit-Ressourcen.")
    if not db.execute(
        "INSERT INTO orbit_ship_orders(mission_id,ship,amount,due) VALUES (?,?,?,?) "
        "ON CONFLICT(mission_id) DO NOTHING RETURNING mission_id",
        (row["mission_id"], ship, amount, now + amount * orbit_rules.SHIP_BUILD_SECONDS),
    ).fetchone():
        raise ValueError("Die Werft bearbeitet bereits einen Auftrag.")
    if repair:
        remaining = amount
        for wreck in db.execute(
            "SELECT battle_id,amount FROM orbit_wrecks WHERE colony_id=? AND ship=? "
            "AND expires>? AND amount>0 ORDER BY expires,battle_id",
            (row["mission_id"], ship, now),
        ).fetchall():
            used = min(remaining, wreck["amount"])
            db.execute(
                "UPDATE orbit_wrecks SET amount=amount-? WHERE battle_id=? AND colony_id=? AND ship=?",
                (used, wreck["battle_id"], row["mission_id"], ship),
            )
            remaining -= used
            if not remaining:
                break
        if remaining:
            raise ValueError("Es stehen nicht genügend reparierbare Wracks bereit.")
    db.execute(
        "UPDATE orbit_economy SET ore=ore-?,ether=ether-? WHERE mission_id=?",
        (ore, ether, row["mission_id"]),
    )


def finish_ship_orders(db: Connection, now: int, colony_id: str) -> None:
    for order in db.execute(
        "SELECT * FROM orbit_ship_orders WHERE due<=? AND mission_id=?", (now, colony_id)
    ).fetchall():
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,?,?) "
            "ON CONFLICT(mission_id,ship) DO UPDATE SET amount=orbit_ships.amount+excluded.amount",
            (order["mission_id"], order["ship"], order["amount"]),
        )
        db.execute("DELETE FROM orbit_ship_orders WHERE mission_id=?", (order["mission_id"],))
