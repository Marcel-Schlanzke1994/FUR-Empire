"""Persistent Orbit attack flights and participant-only combat snapshots."""

import json
import secrets
from collections.abc import Callable
from typing import Any

from . import orbit_battle, orbit_economy, orbit_intel, orbit_rules, orbit_station
from .database import Connection

MOON_PROTECTION_SECONDS = 86400
MOON_SIEGE_MIN = 3
REPORT_PAGE_SIZE = 10
REPORT_SCOPE = (
    "WITH accessible(id) AS (SELECT id FROM orbit_battle_reports WHERE origin=? "
    "UNION SELECT id FROM orbit_battle_reports WHERE target=? "
    "UNION SELECT attack_id FROM orbit_attack_wings WHERE colony_id=? AND participated=TRUE) "
)


def report_page(db: Connection, colony: str, before: str | None = None) -> dict[str, Any]:
    parameters: tuple[Any, ...] = (colony,) * 3
    boundary = ""
    if before is not None:
        cursor = db.execute(
            REPORT_SCOPE + "SELECT b.resolved_at FROM accessible a "
            "JOIN orbit_battle_reports b ON b.id=a.id WHERE b.id=?",
            (*parameters, before),
        ).fetchone()
        if not cursor:
            raise ValueError("Dieser Orbit-Berichtscursor ist nicht verfügbar.")
        boundary = " WHERE (b.resolved_at<? OR (b.resolved_at=? AND b.id<?))"
        parameters += (cursor["resolved_at"], cursor["resolved_at"], before)
    rows = db.execute(
        REPORT_SCOPE
        + "SELECT b.id,b.resolved_at,b.report,d.ore,d.ether,d.expires,m.colony_id AS moon_id "
        "FROM accessible a JOIN orbit_battle_reports b ON b.id=a.id "
        "LEFT JOIN orbit_debris d ON d.battle_id=b.id "
        "LEFT JOIN orbit_moons m ON m.battle_id=b.id"
        + boundary
        + " ORDER BY b.resolved_at DESC,b.id DESC LIMIT ?",
        (*parameters, REPORT_PAGE_SIZE + 1),
    ).fetchall()
    reports = [
        {
            **json.loads(row["report"]),
            "id": row["id"],
            "resolved_at": row["resolved_at"],
            "debris_expires": row["expires"],
            "debris_ore": row["ore"],
            "debris_ether": row["ether"],
            "moon_formed": row["moon_id"] is not None,
        }
        for row in rows[:REPORT_PAGE_SIZE]
    ]
    return {
        "reports": reports,
        "before": reports[-1]["id"] if len(rows) > REPORT_PAGE_SIZE else None,
    }


def record_debris(
    db: Connection, battle_id: str, target: str, due: int, ore: int, ether: int
) -> None:
    if (
        ore >= orbit_rules.MOON_FORMATION_ORE
        and ether >= orbit_rules.MOON_FORMATION_ETHER
        and db.execute(
            "INSERT INTO orbit_moons(colony_id,battle_id,formed_at) VALUES (?,?,?) "
            "ON CONFLICT(colony_id) DO NOTHING RETURNING colony_id",
            (target, battle_id, due),
        ).fetchone()
    ):
        ore -= orbit_rules.MOON_FORMATION_ORE
        ether -= orbit_rules.MOON_FORMATION_ETHER
    if ore or ether:
        db.execute(
            "INSERT INTO orbit_debris(battle_id,ore,ether,expires) VALUES (?,?,?,?)",
            (battle_id, ore, ether, due + orbit_rules.DEBRIS_SECONDS),
        )


def launch(
    db: Connection,
    mission: str,
    origin: dict[str, Any],
    owner: str,
    world: int,
    coordinates: tuple[int, int, int],
    ship: str,
    count: int,
    now: int,
    authorize: Callable[[str, str, int, int], None],
    destroy_moon: bool = False,
    alliance_id: str | None = None,
    retreat_pct: int | None = None,
    lances: int = 0,
) -> None:
    orbit_economy.require_supply(origin, now)
    if (
        any(type(value) is not int for value in coordinates)
        or type(count) is not int
        or not 1 <= count <= 100
    ):
        raise ValueError("Ungültige Orbit-Flotte oder Koordinaten.")
    if retreat_pct is not None and (type(retreat_pct) is not int or not 10 <= retreat_pct <= 100):
        raise ValueError("Ungültige Rückzugsschwelle.")
    destination = orbit_rules.planet_index(*coordinates)
    start = orbit_rules.planet_index(origin["galaxy"], origin["system_no"], origin["slot"])
    if type(lances) is not int or not 0 <= lances <= orbit_rules.AMMUNITION_CAP:
        raise ValueError("Ungültige Anzahl Orbit-Raketen.")
    if lances and (
        coordinates[0] != origin["galaxy"] or abs(destination - start) > orbit_rules.LANCE_RANGE
    ):
        raise ValueError("Das Ziel liegt außerhalb der Raketenreichweite.")
    intel = db.execute(
        "SELECT moon FROM orbit_intel WHERE observer=? AND world_id=? AND galaxy=? "
        "AND system_no=? AND slot=? AND occupied=TRUE AND observed_at>?",
        (owner, world, *coordinates, now - orbit_intel.INTEL_SECONDS),
    ).fetchone()
    if not intel:
        raise ValueError("Der Angriff benötigt eine aktuelle Belegungsbeobachtung.")
    target = db.execute(
        "SELECT mission_id,owner FROM orbit_planet_claims WHERE world_id=? AND galaxy=? "
        "AND system_no=? AND slot=? AND founded_at IS NOT NULL",
        (world, *coordinates),
    ).fetchone()
    if not target or target["owner"] == owner:
        raise ValueError("Dieses Orbit-Ziel ist nicht angreifbar.")
    authorize(owner, target["owner"], now, world)
    moon_target = None
    if destroy_moon:
        if not intel["moon"] or ship != "siege_ship" or count < MOON_SIEGE_MIN:
            raise ValueError(
                "Die Mondbelagerung benötigt Mondaufklärung und mindestens drei Belagerungsschiffe."
            )
        moon = db.execute(
            "SELECT battle_id FROM orbit_moons WHERE colony_id=? AND destroyed_at IS NULL "
            "AND formed_at<=?",
            (target["mission_id"], now - MOON_PROTECTION_SECONDS),
        ).fetchone()
        if (
            not moon
            or db.execute(
                "SELECT 1 FROM orbit_attacks WHERE moon_target=? AND is_returning=FALSE",
                (moon["battle_id"],),
            ).fetchone()
        ):
            raise ValueError("Dieser Mond ist derzeit kein verfügbares Belagerungsziel.")
        moon_target = moon["battle_id"]
    seconds, fuel, _ = orbit_rules.quote_travel({ship: count}, abs(destination - start))
    orbit_economy.refresh(db, origin, now)
    if origin["lances"] < lances:
        raise ValueError("Für die Eröffnungssalve fehlen Sternlanzen.")
    if origin["ether"] < 2 * fuel:
        raise ValueError("Für den Orbit-Angriff fehlt Äther.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship=? AND amount>=? "
        "RETURNING amount",
        (count, origin["mission_id"], ship, count),
    ).fetchone():
        raise ValueError("Die Angriffsflotte steht nicht bereit.")
    db.execute(
        "UPDATE orbit_economy SET ether=ether-?,lances=lances-? WHERE mission_id=?",
        (2 * fuel, lances, origin["mission_id"]),
    )
    db.execute(
        "INSERT INTO orbit_attacks(id,origin,target,ship,amount,due,duration,seed,rule_version,"
        "moon_target,alliance_id,retreat_pct,fuel_spent,lances) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            mission,
            origin["mission_id"],
            target["mission_id"],
            ship,
            count,
            now + seconds + (300 if alliance_id else 0),
            seconds,
            secrets.token_hex(32),
            orbit_rules.VERSION,
            moon_target,
            alliance_id,
            retreat_pct,
            2 * fuel,
            lances,
        ),
    )


def recall(db: Connection, colony: str, attack: str, now: int) -> None:
    if not db.execute(
        "UPDATE orbit_attacks SET is_returning=TRUE,recalled=TRUE,due=?+duration "
        "WHERE id=? AND origin=? AND is_returning=FALSE AND due>? AND rule_version=? RETURNING id",
        (now, attack, colony, now, orbit_rules.VERSION),
    ).fetchone():
        raise ValueError("Dieser Orbit-Angriff kann nicht zurückgerufen werden.")


def join(
    db: Connection,
    attack_id: str,
    origin: dict[str, Any],
    owner: str,
    world: int,
    alliance_id: str,
    ship: str,
    count: int,
    now: int,
    authorize: Callable[[str, str, int, int], None],
) -> None:
    orbit_economy.require_supply(origin, now)
    attack = db.execute(
        "SELECT a.*,t.owner AS defender,t.galaxy,t.system_no,t.slot,o.owner AS leader "
        "FROM orbit_attacks a JOIN orbit_planet_claims t ON t.mission_id=a.target "
        "JOIN orbit_planet_claims o ON o.mission_id=a.origin "
        "JOIN members m ON m.user_id=o.owner AND m.alliance_id=a.alliance_id "
        "WHERE a.id=? AND t.world_id=? AND a.alliance_id=? AND a.is_returning=FALSE "
        "AND a.due>? AND a.rule_version=?",
        (attack_id, world, alliance_id, now, orbit_rules.VERSION),
    ).fetchone()
    if not attack or attack["leader"] == owner:
        raise ValueError("Dieser Orbit-Verband ist nicht verfügbar.")
    authorize(owner, attack["defender"], now, world)
    wings = db.execute(
        "SELECT p.owner FROM orbit_attack_wings w JOIN orbit_planet_claims p "
        "ON p.mission_id=w.colony_id WHERE w.attack_id=?",
        (attack_id,),
    ).fetchall()
    if len(wings) + 1 >= orbit_rules.ALLIED_FLEET_LIMIT or any(
        row["owner"] == owner for row in wings
    ):
        raise ValueError("Der Verband ist voll oder du bist bereits beteiligt.")
    if type(count) is not int or not 1 <= count <= 100:
        raise ValueError("Ungültige Verbandsschiffsanzahl.")
    start = orbit_rules.planet_index(origin["galaxy"], origin["system_no"], origin["slot"])
    target = orbit_rules.planet_index(attack["galaxy"], attack["system_no"], attack["slot"])
    seconds, fuel, _ = orbit_rules.quote_travel({ship: count}, abs(target - start))
    if now + seconds > attack["due"]:
        raise ValueError("Diese Flotte erreicht den Verband nicht rechtzeitig.")
    orbit_economy.refresh(db, origin, now)
    if origin["ether"] < 2 * fuel:
        raise ValueError("Für den Verbandsflug fehlt Äther.")
    if not db.execute(
        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship=? AND amount>=? "
        "RETURNING amount",
        (count, origin["mission_id"], ship, count),
    ).fetchone():
        raise ValueError("Die Verbandsflotte steht nicht bereit.")
    db.execute(
        "UPDATE orbit_economy SET ether=ether-? WHERE mission_id=?",
        (2 * fuel, origin["mission_id"]),
    )
    db.execute(
        "INSERT INTO orbit_attack_wings(attack_id,colony_id,ship,amount) VALUES (?,?,?,?)",
        (attack_id, origin["mission_id"], ship, count),
    )
    if seconds > attack["duration"]:
        db.execute("UPDATE orbit_attacks SET duration=? WHERE id=?", (seconds, attack_id))


def allocate_survivors(counts: list[int], survivors: int) -> list[int]:
    total = sum(counts)
    shares = [divmod(count * survivors, total) for count in counts]
    result = [whole for whole, _ in shares]
    order = sorted(range(len(counts)), key=lambda i: (-shares[i][1], i))
    for index in order[: survivors - sum(result)]:
        result[index] += 1
    return result


def advance(
    db: Connection,
    now: int,
    authorize: Callable[[str, str, int, int], None],
    event_id: str,
) -> None:
    while attack := db.execute(
        "SELECT a.*,o.owner AS attacker,t.owner AS defender,o.world_id "
        "FROM orbit_attacks a JOIN orbit_planet_claims o ON o.mission_id=a.origin "
        "JOIN orbit_planet_claims t ON t.mission_id=a.target "
        "WHERE a.due<=? AND a.rule_version=? AND a.id=?",
        (now, orbit_rules.VERSION, event_id),
    ).fetchone():
        wings = db.execute(
            "SELECT w.*,p.owner,m.alliance_id FROM orbit_attack_wings w "
            "JOIN orbit_planet_claims p ON p.mission_id=w.colony_id "
            "LEFT JOIN members m ON m.user_id=p.owner WHERE w.attack_id=? ORDER BY w.colony_id",
            (attack["id"],),
        ).fetchall()
        if attack["is_returning"]:
            db.execute(
                "UPDATE orbit_ships SET amount=amount+? WHERE mission_id=? AND ship=?",
                (attack["amount"], attack["origin"], attack["ship"]),
            )
            for wing in wings:
                db.execute(
                    "UPDATE orbit_ships SET amount=amount+? WHERE mission_id=? AND ship=?",
                    (wing["amount"], wing["colony_id"], wing["ship"]),
                )
            db.execute("DELETE FROM orbit_attacks WHERE id=?", (attack["id"],))
            continue
        count = attack["amount"]
        try:
            authorize(attack["attacker"], attack["defender"], attack["due"], attack["world_id"])
            if (
                attack["moon_target"]
                and not db.execute(
                    "SELECT 1 FROM orbit_moons WHERE battle_id=? AND colony_id=? AND destroyed_at IS NULL",
                    (attack["moon_target"], attack["target"]),
                ).fetchone()
            ):
                raise ValueError("Das Mondziel ist nicht mehr vorhanden.")
        except ValueError:
            pass  # Protection changed in flight. Return the fleet without a battle.
        else:
            participants = [(attack["origin"], attack["ship"], count)]
            if (
                attack["alliance_id"]
                and db.execute(
                    "SELECT 1 FROM members WHERE user_id=? AND alliance_id=?",
                    (attack["attacker"], attack["alliance_id"]),
                ).fetchone()
            ):
                for wing in wings:
                    if wing["alliance_id"] != attack["alliance_id"]:
                        continue
                    try:
                        authorize(
                            wing["owner"], attack["defender"], attack["due"], attack["world_id"]
                        )
                    except ValueError:
                        continue
                    participants.append((wing["colony_id"], wing["ship"], wing["amount"]))
            fleet: dict[str, int] = {}
            for _, ship, amount in participants:
                fleet[ship] = fleet.get(ship, 0) + amount
            defense = {
                row["ship"]: row["amount"]
                for row in db.execute(
                    "SELECT ship,amount FROM orbit_ships WHERE mission_id=? AND amount>0",
                    (attack["target"],),
                )
            }
            station_garrison = orbit_station.view(db, attack["target"], attack["due"])
            stationed = station_garrison["ships"] if station_garrison.get("active") else {}
            for ship, amount in stationed.items():
                defense[ship] = defense.get(ship, 0) + amount
            station = db.execute(
                "SELECT defense_ready_at,screens FROM orbit_economy WHERE mission_id=?",
                (attack["target"],),
            ).fetchone()
            if (
                station
                and station["defense_ready_at"] is not None
                and station["defense_ready_at"] <= attack["due"]
            ):
                defense[orbit_rules.DEFENSE.id] = 1
            intercepted = min(attack["lances"], station["screens"]) if station and defense else 0
            if intercepted:
                db.execute(
                    "UPDATE orbit_economy SET screens=screens-? WHERE mission_id=?",
                    (intercepted, attack["target"]),
                )
            report = orbit_battle.resolve(
                fleet,
                defense,
                bytes.fromhex(attack["seed"]),
                attack["retreat_pct"],
                attack["lances"] - intercepted,
            )
            report["ammunition"] = {"lances": attack["lances"], "intercepted": intercepted}
            report["leader_fuel_spent"] = attack["fuel_spent"]
            wrecks: list[tuple[str, str, int]] = []
            for ship in fleet:
                squad = [(colony, amount) for colony, kind, amount in participants if kind == ship]
                allocation = allocate_survivors(
                    [amount for _, amount in squad], report["survivors"][0].get(ship, 0)
                )
                for (colony, initial_count), survived in zip(squad, allocation):
                    recoverable = (initial_count - survived) // 4
                    if recoverable:
                        wrecks.append((colony, ship, recoverable))
                    if colony == attack["origin"]:
                        count = survived
                    else:
                        db.execute(
                            "UPDATE orbit_attack_wings SET amount=?,participated=TRUE "
                            "WHERE attack_id=? AND colony_id=?",
                            (survived, attack["id"], colony),
                        )
            if len(participants) > 1:
                report["allied_wings"] = len(participants)
            if attack["moon_target"]:
                destroyed = report["attacker_won"] and count >= MOON_SIEGE_MIN
                report["moon_siege"] = {"destroyed": destroyed, "demolition_ships": int(destroyed)}
                if destroyed:
                    count -= 1
                    db.execute(
                        "UPDATE orbit_moons SET destroyed_at=? WHERE battle_id=?",
                        (attack["due"], attack["moon_target"]),
                    )
            for ship, defense_count in defense.items():
                if ship == orbit_rules.DEFENSE.id:
                    if not report["survivors"][1].get(ship):
                        db.execute(
                            "UPDATE orbit_economy SET defense_ready_at=NULL WHERE mission_id=?",
                            (attack["target"],),
                        )
                    continue
                lost = defense_count - report["survivors"][1].get(ship, 0)
                if lost // 4:
                    wrecks.append((attack["target"], ship, lost // 4))
                station_loss = min(lost, stationed.get(ship, 0))
                if station_loss:
                    db.execute(
                        "UPDATE orbit_station_ships SET amount=amount-? WHERE colony_id=? AND ship=?",
                        (station_loss, attack["target"], ship),
                    )
                if lost > station_loss:
                    db.execute(
                        "UPDATE orbit_ships SET amount=amount-? WHERE mission_id=? AND ship=?",
                        (lost - station_loss, attack["target"], ship),
                    )
            db.execute(
                "INSERT INTO orbit_battle_reports(id,origin,target,resolved_at,report) VALUES (?,?,?,?,?)",
                (
                    attack["id"],
                    attack["origin"],
                    attack["target"],
                    attack["due"],
                    json.dumps(report),
                ),
            )
            catalog = orbit_rules.combat_catalog()
            ore = ether = 0
            for initial, surviving in zip(report["initial"], report["survivors"]):
                for ship, before in initial.items():
                    lost = before - surviving.get(ship, 0)
                    ore += lost * catalog[ship].ore_cost
                    ether += lost * catalog[ship].ether_cost
            for colony, ship, amount in wrecks:
                db.execute(
                    "INSERT INTO orbit_wrecks(battle_id,colony_id,ship,amount,expires) "
                    "VALUES (?,?,?,?,?)",
                    (
                        attack["id"],
                        colony,
                        ship,
                        amount,
                        attack["due"] + orbit_rules.DEBRIS_SECONDS,
                    ),
                )
                ore -= amount * catalog[ship].ore_cost
                ether -= amount * catalog[ship].ether_cost
            record_debris(db, attack["id"], attack["target"], attack["due"], ore // 4, ether // 4)
        db.execute(
            "UPDATE orbit_attacks SET amount=?,is_returning=TRUE,due=due+duration WHERE id=?",
            (count, attack["id"]),
        )
