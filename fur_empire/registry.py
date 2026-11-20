"""Validated original FUR rule registry; immutable for the deployed rule version."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def empty_requirements() -> dict[str, dict[str, int]]:
    return {"buildings": {}, "tech": {}}


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1, max_length=80)
    cost: list[int] = Field(min_length=3, max_length=3)
    description: str = ""
    icon: str = ""
    power: int = Field(default=0, ge=0)
    time: int = Field(default=1, ge=1)
    require: int = Field(default=0, ge=0, le=10)
    requirements: dict[str, dict[str, int]] = Field(default_factory=empty_requirements)


class TerrainRule(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1, max_length=40)
    movement_cost: int | None
    generation_weight: int = Field(ge=0)
    production_percent: list[int] = Field(min_length=3, max_length=3)
    defense_percent: int = Field(ge=0, le=1000)


class Rules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    buildings: dict[str, Item]
    tech: dict[str, Item]
    units: dict[str, Item]
    terrain: dict[str, TerrainRule]


class ColonyConversionRules(BaseModel):
    """New, explicitly proposed FUR-3 conversion rules; not part of FUR-2 snapshots."""

    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    status: str
    cost: list[int] = Field(min_length=3, max_length=3)
    headquarters_level: int = Field(ge=1, le=10)
    minimum_colony_distance: int = Field(ge=1, le=63)
    excluded_outpost_tier: int = Field(ge=1, le=10)
    retain_stock: bool
    retain_garrison: bool
    require_exact_name_confirmation: bool


def load_rule_model() -> Rules:
    rules = Rules.model_validate(
        json.loads((Path(__file__).parent / "rules" / "fur-2.json").read_text(encoding="utf-8"))
    )
    if rules.version != "FUR-2":
        raise ValueError("Unerwartete Spielregelversion.")
    for group in (rules.buildings, rules.tech, rules.units):
        for item in group.values():
            if any(c <= 0 for c in item.cost):
                raise ValueError("Basiskosten müssen positiv sein.")
            if set(item.requirements) != {"buildings", "tech"}:
                raise ValueError("Voraussetzungen benötigen Gebäude- und Forschungsgruppen.")
            if any(level < 1 for values in item.requirements.values() for level in values.values()):
                raise ValueError("Voraussetzungsstufen müssen positiv sein.")
            if not set(item.requirements["buildings"]).issubset(rules.buildings):
                raise ValueError("Unbekanntes Gebäude in einer Voraussetzung.")
            if not set(item.requirements["tech"]).issubset(rules.tech):
                raise ValueError("Unbekannte Forschung in einer Voraussetzung.")
    if any(
        item.require != item.requirements["buildings"].get("barracks", 0)
        for item in rules.units.values()
    ):
        raise ValueError("Legacy-Kasernenfreischaltung und deklarierte Voraussetzungen weichen ab.")
    expected_terrain = ("plain", "forest", "water", "mountain", "pass")
    if tuple(rules.terrain) != expected_terrain:
        raise ValueError(
            "Das Geländeregister muss die fünf FUR-2-Typen in stabiler Reihenfolge führen."
        )
    if sum(rule.generation_weight for rule in rules.terrain.values()) != 100:
        raise ValueError("Die Gewichte des FUR-2-Geländegenerators müssen 100 ergeben.")
    if any(any(value < 0 for value in rule.production_percent) for rule in rules.terrain.values()):
        raise ValueError("Gelände-Produktionsmodifier dürfen nicht negativ sein.")
    if rules.terrain["water"].movement_cost is not None:
        raise ValueError("Wasser muss für den Wegfinder unpassierbar sein.")
    if any(
        rule.movement_cost is None or rule.movement_cost < 1
        for key, rule in rules.terrain.items()
        if key != "water"
    ):
        raise ValueError("Begehbares Gelände benötigt positive Bewegungskosten.")
    return rules


def load_rules() -> dict[str, Any]:
    return load_rule_model().model_dump()


def load_colony_conversion_rules() -> dict[str, Any]:
    rules = ColonyConversionRules.model_validate(
        json.loads(
            (Path(__file__).parent / "rules" / "fur-3-colony-conversion-proposal.json").read_text(
                encoding="utf-8"
            )
        )
    )
    if rules.version != "FUR-3-proposal" or rules.status != "owner_review_pending":
        raise ValueError("Die Umwandlungsregeln müssen als FUR-3-Vorschlag gekennzeichnet bleiben.")
    if any(cost <= 0 for cost in rules.cost):
        raise ValueError("Umwandlungskosten müssen positiv sein.")
    if not all((rules.retain_stock, rules.retain_garrison, rules.require_exact_name_confirmation)):
        raise ValueError("Der Vorschlag muss Vorräte, Garnison und Namensbestätigung erhalten.")
    return rules.model_dump()
