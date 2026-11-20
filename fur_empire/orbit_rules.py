"""Versioned Orbit-1 rules and integer fleet travel calculations."""

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field


class ShipRule(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    id: str = Field(pattern=r"^[a-z][a-z_]+$")
    role: str = Field(min_length=1)
    speed_units: int = Field(gt=0)
    attack: int = Field(ge=0)
    shield: int = Field(ge=0)
    hull: int = Field(gt=0)
    cargo: int = Field(ge=0)
    ore_cost: int = Field(gt=0)
    ether_cost: int = Field(gt=0)
    fuel_per_distance: int = Field(gt=0)


class TerraBuildRule(TypedDict):
    hq: int
    cost: list[int]
    seconds: int
    max_level: int


_proposal = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-orbit-1.json").read_text(encoding="utf-8")
)
VERSION = _proposal["id"]
if VERSION != "FUR-3 / ORBIT-1" or _proposal["legacy_fur2_preserved"] is not True:
    raise ValueError("Ungültige Version des Orbit-Regelkatalogs.")

_orbit = _proposal["orbit"]
SYSTEMS_PER_GALAXY = int(_orbit["star_systems_per_galaxy"])
PLANETS_PER_SYSTEM = int(_orbit["planets_per_system"])
BASE_COLONY_LIMIT = int(_orbit["colonies_without_tech"])
BASE_FLEET_LIMIT = int(_orbit["default_max_fleet_slots"])
ALLIED_FLEET_LIMIT = int(_orbit["max_allied_fleets"])
DEBRIS_SECONDS = int(_orbit["debris_expiry_hours"]) * 3600
MOON_FORMATION_ORE = 1000
MOON_FORMATION_ETHER = 250
GATEWAY_CARGO_LIMIT = 500
GATEWAY_CARGO_FEE = 20
GATEWAY_TRANSFER_SECONDS = 600
AMMUNITION_CAP = 20
LANCE_RANGE = 48
LANCE_POWER = 40
AMMUNITION_COSTS = {"lances": (90, 30), "screens": (60, 20)}
COMBAT_ROUNDS = int(_proposal["battle"]["turns_max"])
ACCURACY_PERMILLE = round(_proposal["battle"]["accuracy_base"] * 1000)
GALAXY_COUNT = 3
if (
    _orbit["travel_speed_formula_id"] != "orbit_distance_speed_v1"
    or _orbit["fuel_formula_id"] != "orbit_fuel_v1"
):
    raise ValueError("Unbekannte Orbit-Reiseformel.")

_ships = {
    rule.id: rule for rule in (ShipRule.model_validate(entry) for entry in _orbit["new_ships"])
}
if len(_ships) != 14 or len(_orbit["new_ships"]) != 14:
    raise ValueError("Orbit-1 benötigt 14 eindeutige Schiffsklassen.")

_minimum_seconds = _proposal["gameplay_default_timing"]["orbit_min_travel_seconds"]
if type(_minimum_seconds) is not int or _minimum_seconds <= 0:
    raise ValueError("Die minimale Orbit-Reisezeit muss positiv sein.")

SNAPSHOT = json.dumps(_proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()

_gateway = next(item for item in _proposal["new_buildings"] if item["id"] == "orbital_gateway")
TERRA_ENERGY_BUILDINGS: dict[str, TerraBuildRule] = {
    item["id"]: {
        "hq": int(item["required_command_level"]),
        "cost": [int(item["base_cost"][resource]) for resource in ("wood", "stone", "ore")],
        "seconds": int(item["base_build_seconds"]),
        "max_level": int(item["max_level"]),
    }
    for item in _proposal["new_buildings"]
    if item["id"] in ("energy_core", "fusion_plant", "scanner_tower", "command_uplink")
}
TERRA_MISSION_BASE = int(_proposal["land"]["max_active_missions_base"])
_prestige = next(item for item in _proposal["new_research"] if item["id"] == "terra_prestige")
TERRA_PRESTIGE: TerraBuildRule = {
    "hq": int(_prestige["unlock_command_level"]),
    "cost": [int(_prestige["base_cost"][resource]) for resource in ("wood", "stone", "ore")],
    "seconds": int(_prestige["base_research_seconds"]),
    "max_level": int(_prestige["max_level"]),
}
_navigation = next(item for item in _proposal["new_research"] if item["id"] == "orbital_navigation")
GATEWAY_HQ = int(_gateway["required_command_level"])
GATEWAY_COST = tuple(int(_gateway["base_cost"][key]) for key in ("wood", "stone", "ore"))
NAVIGATION_COST = tuple(int(_navigation["base_cost"][key]) for key in ("wood", "stone", "ore"))
_shipbuilding = next(
    item for item in _proposal["new_research"] if item["id"] == "orbital_shipbuilding"
)
SHIPBUILDING_ORE = int(_shipbuilding["base_cost"]["ore"])
SHIPBUILDING_SECONDS = int(_shipbuilding["base_research_seconds"])
_jumpgate = next(item for item in _proposal["new_research"] if item["id"] == "jumpgate_network")
JUMPGATE_HQ = int(_jumpgate["unlock_command_level"])
JUMPGATE_ORE = int(_jumpgate["base_cost"]["ore"])
JUMPGATE_SECONDS = int(_jumpgate["base_research_seconds"])
JUMPGATE_COOLDOWN = int(_orbit["jumpgate_cooldown_hours"]) * 3600
SHIP_BUILD_SECONDS = 60
DEFENSE_BUILD_SECONDS = 600
DEFENSE = ShipRule(
    id="defense_platform",
    role="stationary_defense",
    speed_units=1,
    attack=65,
    shield=110,
    hull=220,
    cargo=0,
    ore_cost=900,
    ether_cost=240,
    fuel_per_distance=1,
)


def ship_catalog() -> dict[str, ShipRule]:
    return dict(_ships)


def combat_catalog() -> dict[str, ShipRule]:
    return {**_ships, DEFENSE.id: DEFENSE}


def system_chart(seed: int, world_id: int, galaxy: int, system: int) -> list[dict[str, int | str]]:
    """Chart only public celestial geography. Fleet and colony data have separate visibility."""
    if not 1 <= galaxy <= GALAXY_COUNT or not 1 <= system <= SYSTEMS_PER_GALAXY:
        raise ValueError("Unbekannte Orbit-Koordinaten.")
    climates = ("Gestein", "Eis", "Wüste", "Ozean")
    chart: list[dict[str, int | str]] = []
    for slot in range(1, PLANETS_PER_SYSTEM + 1):
        key = f"{DIGEST}:{seed}:{world_id}:{galaxy}:{system}:{slot}"
        digest = hashlib.sha256(key.encode("ascii")).digest()
        chart.append({"slot": slot, "terrain": climates[digest[0] % len(climates)]})
    return chart


def planet_index(galaxy: int, system: int, slot: int) -> int:
    if not (
        1 <= galaxy <= GALAXY_COUNT
        and 1 <= system <= SYSTEMS_PER_GALAXY
        and 1 <= slot <= PLANETS_PER_SYSTEM
    ):
        raise ValueError("Unbekannte Orbit-Koordinaten.")
    systems = (galaxy - 1) * SYSTEMS_PER_GALAXY + system - 1
    return systems * PLANETS_PER_SYSTEM + slot


def quote_travel(fleet: Mapping[str, int], distance: int) -> tuple[int, int, int]:
    """Return duration, fuel and cargo for one leg at the slowest ship's speed."""
    if type(distance) is not int or distance <= 0 or not fleet:
        raise ValueError("Eine Orbit-Reise benötigt eine Flotte und eine positive Entfernung.")
    if any(
        ship not in _ships or type(count) is not int or count <= 0 for ship, count in fleet.items()
    ):
        raise ValueError("Ungültige Schiffe oder Stückzahlen.")

    slowest_speed = min(_ships[ship].speed_units for ship in fleet)
    seconds = max(_minimum_seconds, (distance + slowest_speed - 1) // slowest_speed)
    fuel = distance * sum(_ships[ship].fuel_per_distance * count for ship, count in fleet.items())
    cargo = sum(_ships[ship].cargo * count for ship, count in fleet.items())
    return seconds, fuel, cargo
