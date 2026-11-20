"""Versioned provisional FUR-3 Terra defense catalog and pure calculations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

VERSION = "FUR-3-TERRA-DEFENSE-1"
RULES: dict[str, Any] = cast(
    dict[str, Any],
    json.loads(
        (Path(__file__).parent / "rules" / "fur-3-terra-defense-1.json").read_text(encoding="utf-8")
    ),
)
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()


def validate_rules(rules: dict[str, Any] = RULES) -> None:
    if (
        rules.get("version") != VERSION
        or rules.get("status") != "provisional_balance"
        or rules.get("activation") != "FUR-3-TERRA-COMBAT-4-only"
        or rules.get("legacy_fur2_preserved") is not True
        or rules.get("provisional") is not True
    ):
        raise ValueError("unsupported Terra defense contract")
    slots = rules.get("slots")
    if not isinstance(slots, dict) or (
        slots.get("base"),
        slots.get("per_hq_levels"),
        slots.get("maximum"),
    ) != (1, 3, 4):
        raise ValueError("invalid Terra defense slots")
    objects = rules.get("objects")
    if not isinstance(objects, dict) or set(objects) != {
        "kinetic_turret",
        "aegis_emitter",
        "proximity_mines",
        "command_bunker",
    }:
        raise ValueError("invalid Terra defense roster")
    for key, item in objects.items():
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("cost"), list)
            or len(item["cost"]) != 3
            or any(type(value) is not int or value <= 0 for value in item["cost"])
            or type(item.get("slot_cost")) is not int
            or item["slot_cost"] != 1
            or type(item.get("defense_power")) is not int
            or item["defense_power"] <= 0
            or type(item.get("structure_points")) is not int
            or item["structure_points"] <= 0
            or type(item.get("repair_cost_percent")) is not int
            or not 1 <= item["repair_cost_percent"] <= 100
            or type(item.get("maximum_count")) is not int
            or item["maximum_count"] < 1
            or not isinstance(item.get("prerequisites"), dict)
            or set(item["prerequisites"]) != {"buildings", "tech"}
            or (
                item.get("combat_profile") is not None
                and (
                    not isinstance(item["combat_profile"], dict)
                    or set(item["combat_profile"])
                    != {"attack", "armor", "accuracy", "evasion", "initiative", "target_priority"}
                    or any(
                        type(value) is not int or value < 0
                        for value in item["combat_profile"].values()
                    )
                    or item["combat_profile"]["accuracy"] > 100
                    or item["combat_profile"]["evasion"] > 100
                )
            )
            or (key == "proximity_mines") != (item.get("combat_profile") is None)
        ):
            raise ValueError(f"invalid Terra defense object: {key}")
    damage = rules.get("damage")
    minefield = rules.get("minefield")
    reports = rules.get("reports")
    if (
        not isinstance(damage, dict)
        or damage.get("repair_requires_safe_colony") is not True
        or damage.get("minimum_integrity") != 0
        or damage.get("minefield_consumed_on_successful_trigger") is not True
        or not isinstance(reports, dict)
        or reports.get("include_minefield_trigger_in_participant_combat_report") is not True
        or not isinstance(minefield, dict)
        or minefield.get("scope") != ["player_attack", "alliance_player_attack"]
        or type(minefield.get("trigger_chance_base_percent")) is not int
        or type(minefield.get("trigger_chance_per_defender_tactics_level")) is not int
        or type(minefield.get("trigger_chance_max_percent")) is not int
        or not 0
        <= minefield["trigger_chance_base_percent"]
        <= minefield["trigger_chance_max_percent"]
        or not 1 <= minefield["trigger_chance_max_percent"] <= 100
        or not 0 <= minefield["trigger_chance_per_defender_tactics_level"] <= 100
        or type(minefield.get("attacker_damage_percent_when_triggered")) is not int
        or not 1 <= minefield["attacker_damage_percent_when_triggered"] <= 100
        or minefield.get("maximum_triggers_per_mission") != 1
    ):
        raise ValueError("invalid Terra defense behavior")


def slot_limit(hq_level: int) -> int:
    if type(hq_level) is not int or hq_level < 0:
        raise ValueError("invalid headquarters level")
    return min(
        int(RULES["slots"]["maximum"]),
        int(RULES["slots"]["base"]) + hq_level // int(RULES["slots"]["per_hq_levels"]),
    )


def validate_stacks(stacks: dict[str, list[int]]) -> None:
    if not isinstance(stacks, dict) or set(stacks) - set(RULES["objects"]):
        raise ValueError("unknown Terra defense stack")
    slots = 0
    for key, stack in stacks.items():
        rule = RULES["objects"][key]
        if (
            not isinstance(stack, list)
            or len(stack) > int(rule["maximum_count"])
            or any(type(integrity) is not int or not 0 <= integrity <= 100 for integrity in stack)
        ):
            raise ValueError("invalid Terra defense stack")
        slots += len(stack) * int(rule["slot_cost"])
    if slots > int(RULES["slots"]["maximum"]):
        raise ValueError("Terra defense stacks exceed the slot cap")


def defense_power(stacks: dict[str, list[int]]) -> int:
    validate_stacks(stacks)
    total = 0
    for key, stack in stacks.items():
        total += int(RULES["objects"][key]["defense_power"]) * sum(stack) // 100
    return total


def combat_profiles(
    stacks: dict[str, list[int]],
) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, tuple[str, int]]]:
    """Expand intact combat structures into private resolver-only unit profiles."""
    validate_stacks(stacks)
    profiles: dict[str, dict[str, Any]] = {}
    army: dict[str, int] = {}
    instances: dict[str, tuple[str, int]] = {}
    for key in sorted(stacks):
        item = RULES["objects"][key]
        combat_profile = item.get("combat_profile")
        if combat_profile is None:
            continue
        for index, integrity in enumerate(stacks[key]):
            if integrity <= 0:
                continue
            unit_id = f"furdef_{key}_{index}"
            profiles[unit_id] = {
                **combat_profile,
                "shield": 0,
                "hull": max(1, int(item["structure_points"]) * integrity // 100),
                "counters": [],
            }
            army[unit_id] = 1
            instances[unit_id] = (key, index)
    return profiles, army, instances


def trigger_minefield(
    seed: bytes, stacks: dict[str, list[int]], defender_tactics: int
) -> tuple[dict[str, list[int]], bool, int]:
    """Apply the one-per-mission seeded minefield trigger and consume one field."""
    validate_stacks(stacks)
    if type(defender_tactics) is not int or not 0 <= defender_tactics <= 10:
        raise ValueError("invalid minefield defender tactics")
    updated = {key: list(values) for key, values in stacks.items()}
    active = [index for index, value in enumerate(updated.get("proximity_mines", [])) if value > 0]
    if not active:
        return updated, False, 0
    rule = RULES["minefield"]
    chance = min(
        int(rule["trigger_chance_max_percent"]),
        int(rule["trigger_chance_base_percent"])
        + defender_tactics * int(rule["trigger_chance_per_defender_tactics_level"]),
    )
    roll = (
        int.from_bytes(
            hashlib.sha256(seed + b"\x00FUR-3-TERRA-DEFENSE-1\x00minefield").digest()[:8], "big"
        )
        % 100
    )
    triggered = roll < chance
    if triggered:
        updated["proximity_mines"][active[0]] = 0
    return updated, triggered, chance


def apply_combat_integrity(
    initial: dict[str, list[int]],
    instances: dict[str, tuple[str, int]],
    survivors: dict[str, dict[str, int]],
) -> dict[str, list[int]]:
    """Return per-structure remaining integrity based on its final resolver hull."""
    updated = {key: list(values) for key, values in initial.items()}
    for unit_id, (key, index) in instances.items():
        hull = int(survivors.get(unit_id, {}).get("hull", 0))
        maximum = int(RULES["objects"][key]["structure_points"])
        updated[key][index] = max(0, min(100, hull * 100 // maximum))
    return updated


validate_rules()
