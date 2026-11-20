"""Deterministic, replayable FUR-3 Terra combat rules; FUR-2 remains separate."""

from __future__ import annotations

import hashlib
import heapq
import json
import secrets
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from .database import Connection


def _load_rules(filename: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((Path(__file__).parent / "rules" / filename).read_text(encoding="utf-8")),
    )


RULESETS: dict[str, dict[str, Any]] = {
    "FUR-3-TERRA-COMBAT-1": _load_rules("fur-3-terra-combat-1.json"),
    "FUR-3-TERRA-COMBAT-2": _load_rules("fur-3-terra-combat-2.json"),
    "FUR-3-TERRA-COMBAT-3": _load_rules("fur-3-terra-combat-3.json"),
    "FUR-3-TERRA-COMBAT-4": _load_rules("fur-3-terra-combat-4.json"),
    "FUR-3-TERRA-COMBAT-5": _load_rules("fur-3-terra-combat-5.json"),
}
RULESET_SNAPSHOTS = {
    version: json.dumps(rules, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for version, rules in RULESETS.items()
}
RULESET_DIGESTS = {
    version: "sha256:" + hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
    for version, snapshot in RULESET_SNAPSHOTS.items()
}
RULES: dict[str, Any] = RULESETS["FUR-3-TERRA-COMBAT-1"]
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = "sha256:" + hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest()
UNITS: dict[str, dict[str, Any]] = RULES["units"]
SIMULATION_VERSION = "FUR-3-TERRA-SIM-1"
SIMULATION_SAMPLES = 16


def validate_rules(rules: dict[str, Any]) -> None:
    if (
        rules.get("version") not in RULESETS
        or rules.get("kind") != "deterministic_six_round_combat"
    ):
        raise ValueError("unsupported Terra combat rules")
    if rules.get("legacy_fur2_preserved") is not True:
        raise ValueError("FUR-3 combat rules must preserve legacy FUR-2")
    rounds = rules.get("rounds")
    if (
        not isinstance(rounds, dict)
        or type(rounds.get("maximum")) is not int
        or rounds["maximum"] != 6
    ):
        raise ValueError("invalid Terra combat round limit")
    formula = rules.get("formula")
    if (
        not isinstance(formula, dict)
        or type(formula.get("wall_armor_bonus_per_level")) is not int
        or formula["wall_armor_bonus_per_level"] < 0
        or not isinstance(formula.get("retreat"), dict)
        or not 1 <= formula["retreat"].get("default_threshold_percent", 0) <= 100
    ):
        raise ValueError("invalid Terra combat formula")
    units = rules.get("units")
    required = {
        "attack",
        "armor",
        "shield",
        "hull",
        "accuracy",
        "evasion",
        "initiative",
        "target_priority",
        "counters",
    }
    if not isinstance(units, dict) or not units:
        raise ValueError("Terra combat roster is empty")
    for unit_id, profile in units.items():
        if not isinstance(profile, dict) or not required <= profile.keys():
            raise ValueError(f"incomplete Terra combat profile: {unit_id}")
        if any(type(profile[field]) is not int for field in required - {"counters"}):
            raise ValueError(f"non-integer Terra combat profile: {unit_id}")
        if any(profile[field] < 0 for field in required - {"counters"}):
            raise ValueError(f"negative Terra combat profile: {unit_id}")
        if profile["hull"] < 1 or profile["accuracy"] > 100 or profile["evasion"] > 100:
            raise ValueError(f"out-of-range Terra combat profile: {unit_id}")
        if not isinstance(profile["counters"], list) or any(
            counter not in units for counter in profile["counters"]
        ):
            raise ValueError(f"unknown Terra combat counter: {unit_id}")
        if rules["version"] in (
            "FUR-3-TERRA-COMBAT-3",
            "FUR-3-TERRA-COMBAT-4",
            "FUR-3-TERRA-COMBAT-5",
        ):
            economy_fields = {
                "role",
                "speed",
                "cargo",
                "fuel",
                "range",
                "training_time",
                "cost",
                "prerequisites",
                "repair_ratio",
            }
            if not economy_fields <= profile.keys():
                raise ValueError(f"incomplete Terra unit economy profile: {unit_id}")
            if (
                any(
                    type(profile[field]) is not int or profile[field] < 0
                    for field in (
                        "speed",
                        "cargo",
                        "fuel",
                        "range",
                        "training_time",
                        "repair_ratio",
                    )
                )
                or profile["speed"] < 1
                or profile["range"] < 1
                or profile["training_time"] < 1
            ):
                raise ValueError(f"invalid Terra unit economy values: {unit_id}")
            if (
                not isinstance(profile["cost"], list)
                or len(profile["cost"]) != 3
                or any(type(value) is not int or value <= 0 for value in profile["cost"])
                or not isinstance(profile["prerequisites"], dict)
                or set(profile["prerequisites"]) != {"buildings", "tech"}
            ):
                raise ValueError(f"invalid Terra unit production profile: {unit_id}")
            if not isinstance(profile["role"], str) or not profile["role"].strip():
                raise ValueError(f"invalid Terra unit role: {unit_id}")
            if profile["repair_ratio"] > 100:
                raise ValueError(f"invalid Terra unit repair ratio: {unit_id}")
            if any(
                not isinstance(group, dict)
                or any(
                    not isinstance(key, str) or type(level) is not int or level < 1
                    for key, level in group.items()
                )
                for group in profile["prerequisites"].values()
            ):
                raise ValueError(f"invalid Terra unit prerequisites: {unit_id}")
    if rules["version"] in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
        economy = rules.get("unit_economy")
        if (
            not isinstance(economy, dict)
            or type(economy.get("enabled_for_training")) is not bool
            or type(economy.get("maximum_units_per_colony")) is not int
            or not 1 <= economy["maximum_units_per_colony"] <= 2000
        ):
            raise ValueError("invalid FUR-3 unit lifecycle gate")


def rules_for(version: str) -> dict[str, Any]:
    try:
        return RULESETS[version]
    except KeyError as exc:
        raise ValueError("unsupported world combat ruleset") from exc


def is_supported_version(version: str) -> bool:
    return version in RULESETS


def _army(source: dict[str, int], rules: dict[str, Any]) -> dict[str, list[dict[str, int]]]:
    units = rules["units"]
    if not isinstance(source, dict):
        raise TypeError("invalid army")
    if any(
        key not in units or type(amount) is not int or amount < 0 for key, amount in source.items()
    ):
        raise ValueError("invalid army")
    if sum(source.values()) > int(rules["limits"]["maximum_army_units_per_side"]):
        raise ValueError("army exceeds the FUR-3 combat unit limit")
    return {
        key: [
            {"shield": int(units[key]["shield"]), "hull": int(units[key]["hull"])}
            for _ in range(amount)
        ]
        for key, amount in source.items()
        if amount > 0
    }


def _alive(army: dict[str, list[dict[str, int]]]) -> bool:
    return any(unit["hull"] > 0 for units in army.values() for unit in units)


def _counts(army: dict[str, list[dict[str, int]]]) -> dict[str, int]:
    return {
        key: count
        for key, units in sorted(army.items())
        if (count := sum(1 for unit in units if unit["hull"] > 0))
    }


def _roll(seed: bytes, *parts: object) -> int:
    payload = b"\x1f".join(str(part).encode("utf-8") for part in parts)
    return int.from_bytes(hashlib.sha256(seed + b"\x00" + payload).digest()[:8], "big")


def pin_mission(
    db: Connection,
    mission_id: str,
    world_id: int,
    created: int,
    *,
    rules_version: str | None = None,
    retreat_threshold_percent: int | None = None,
) -> dict[str, Any] | None:
    """Pin FUR-3 replay material outside public player state, or return None for FUR-2."""
    world = db.execute(
        "SELECT terra_combat_ruleset,terra_retreat_threshold_percent "
        "FROM world_settings WHERE world_id=?",
        (world_id,),
    ).fetchone()
    if not world or str(world["terra_combat_ruleset"]) == "FUR-2":
        return None
    selected_version = str(world["terra_combat_ruleset"])
    if rules_version is not None and rules_version != selected_version:
        raise ValueError("world combat rules changed before mission dispatch")
    if not is_supported_version(selected_version):
        raise ValueError("unsupported world combat ruleset")
    rules = rules_for(selected_version)
    digest = RULESET_DIGESTS[selected_version]
    threshold = (
        int(world["terra_retreat_threshold_percent"])
        if retreat_threshold_percent is None
        else retreat_threshold_percent
    )
    if type(threshold) is not int or not int(
        rules["formula"]["retreat"]["threshold_min_percent"]
    ) <= threshold <= int(rules["formula"]["retreat"]["threshold_max_percent"]):
        raise ValueError("invalid retreat threshold")
    seed = secrets.token_hex(32)
    commitment = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    db.execute(
        "INSERT INTO terra_combat_missions"
        "(mission_id,world_id,rules_version,rules_digest,seed,seed_commitment,"
        "retreat_threshold_percent,created) VALUES (?,?,?,?,?,?,?,?)",
        (mission_id, world_id, selected_version, digest, seed, commitment, threshold, created),
    )
    return {
        "rules_version": selected_version,
        "rules_digest": digest,
        "seed_commitment": commitment,
    }


def mission_seed(
    db: Connection,
    mission_id: str,
    world_id: int,
    expected_commitment: str | None = None,
) -> tuple[str, int]:
    """Read private, unresolved mission material and verify all pinned commitments."""
    row = db.execute(
        "SELECT rules_version,rules_digest,seed,seed_commitment,retreat_threshold_percent,resolved "
        "FROM terra_combat_missions WHERE mission_id=? AND world_id=?",
        (mission_id, world_id),
    ).fetchone()
    if not row:
        raise ValueError("missing FUR-3 mission replay record")
    seed = str(row["seed"])
    version = str(row["rules_version"])
    if (
        not is_supported_version(version)
        or str(row["rules_digest"]) != RULESET_DIGESTS.get(version)
        or str(row["seed_commitment"]) != hashlib.sha256(bytes.fromhex(seed)).hexdigest()
        or (expected_commitment is not None and str(row["seed_commitment"]) != expected_commitment)
        or row["resolved"] is not None
    ):
        raise ValueError("invalid or already resolved FUR-3 mission replay record")
    return seed, int(row["retreat_threshold_percent"])


def store_replay(db: Connection, mission_id: str, replay: dict[str, Any], resolved: int) -> None:
    """Persist the post-resolution replay and revealed seed in the same world transaction."""
    changed = db.execute(
        "UPDATE terra_combat_missions SET resolved=?,replay=? "
        "WHERE mission_id=? AND resolved IS NULL RETURNING mission_id",
        (resolved, json.dumps(replay, sort_keys=True, separators=(",", ":")), mission_id),
    ).fetchone()
    if changed is None:
        raise ValueError("FUR-3 mission replay was already resolved")


def discard_mission(db: Connection, mission_id: str) -> None:
    """Erase an unused secret seed when arrival protection cancels combat."""
    db.execute(
        "DELETE FROM terra_combat_missions WHERE mission_id=? AND resolved IS NULL",
        (mission_id,),
    )


def _fire(
    source: dict[str, list[dict[str, int]]],
    target: dict[str, list[dict[str, int]]],
    *,
    source_side: str,
    round_no: int,
    seed: bytes,
    tactics: int,
    target_armor_bonus: int,
    doctrine_percent: int,
    terrain_percent: int,
    faction_percent: int,
    rules: dict[str, Any],
    tactics_by_unit: dict[str, int] | None = None,
) -> dict[str, Any]:
    units_catalog = rules["units"]
    formula = rules["formula"]
    hits = misses = damage_total = casualties = shots = 0
    focus: list[tuple[int, int, str, int]] = []
    for target_key, units in target.items():
        target_profile = units_catalog[target_key]
        total = int(target_profile["shield"]) + int(target_profile["hull"])
        for target_index, unit in enumerate(units):
            if unit["hull"] <= 0:
                continue
            remaining = unit["shield"] + unit["hull"]
            heapq.heappush(
                focus,
                (
                    remaining * 10000 // max(total, 1),
                    -int(target_profile["target_priority"]),
                    target_key,
                    target_index,
                ),
            )
    for source_key in sorted(source, key=lambda key: (-int(units_catalog[key]["initiative"]), key)):
        profile = units_catalog[source_key]
        if int(profile["attack"]) == 0:
            continue
        for ordinal, _ in enumerate(list(source.get(source_key, []))):
            if source[source_key][ordinal]["hull"] <= 0:
                continue
            if not focus:
                break
            _, _, target_key, target_index = heapq.heappop(focus)
            target_profile = units_catalog[target_key]
            raw_accuracy = int(profile["accuracy"]) - int(target_profile["evasion"])
            accuracy = max(
                int(formula["accuracy_min_percent"]),
                min(
                    int(formula["accuracy_max_percent"]),
                    int(formula["accuracy_base_percent"])
                    + int(formula["accuracy_per_difference_percent"]) * raw_accuracy,
                ),
            )
            shot_index = shots
            shots += 1
            if (
                _roll(seed, round_no, source_side, source_key, ordinal, shot_index, "hit") % 100
                >= accuracy
            ):
                misses += 1
                target_unit = target[target_key][target_index]
                remaining = target_unit["shield"] + target_unit["hull"]
                total = int(target_profile["shield"]) + int(target_profile["hull"])
                heapq.heappush(
                    focus,
                    (
                        remaining * 10000 // max(total, 1),
                        -int(target_profile["target_priority"]),
                        target_key,
                        target_index,
                    ),
                )
                continue
            hits += 1
            variance_min = int(formula["damage_variance_min_percent"])
            variance_max = int(formula["damage_variance_max_percent"])
            variance = variance_min + _roll(
                seed, round_no, source_side, source_key, ordinal, shot_index, "damage"
            ) % (variance_max - variance_min + 1)
            unit_tactics = tactics_by_unit.get(source_key, tactics) if tactics_by_unit else tactics
            tactic_factor = 100 + int(formula["tactics_damage_percent_per_level"]) * unit_tactics
            counter_factor = (
                int(formula["counter_multiplier_percent"])
                if target_key in profile["counters"]
                else int(formula["base_multiplier_percent"])
            )
            effective = (
                int(profile["attack"])
                * tactic_factor
                * counter_factor
                * variance
                * doctrine_percent
                * terrain_percent
                * faction_percent
            )
            armor = int(target_profile["armor"]) + target_armor_bonus
            amount = max(
                int(formula["damage_floor"]),
                effective // 1_000_000_000_000 - armor,
            )
            target_unit = target[target_key][target_index]
            shield_damage = min(target_unit["shield"], amount)
            target_unit["shield"] -= shield_damage
            hull_damage = min(target_unit["hull"], amount - shield_damage)
            target_unit["hull"] -= hull_damage
            damage_total += shield_damage + hull_damage
            if target_unit["hull"] <= 0:
                casualties += 1
            else:
                remaining = target_unit["shield"] + target_unit["hull"]
                total = int(target_profile["shield"]) + int(target_profile["hull"])
                heapq.heappush(
                    focus,
                    (
                        remaining * 10000 // max(total, 1),
                        -int(target_profile["target_priority"]),
                        target_key,
                        target_index,
                    ),
                )
    return {
        "shots": shots,
        "hits": hits,
        "misses": misses,
        "damage": damage_total,
        "casualties": casualties,
    }


def _recharge(army: dict[str, list[dict[str, int]]], rules: dict[str, Any]) -> None:
    percent = int(rules["rounds"]["shield_recharge_percent_after_round"])
    for key, units in army.items():
        maximum = int(rules["units"][key]["shield"])
        if maximum:
            for unit in units:
                if unit["hull"] > 0:
                    unit["shield"] = min(maximum, unit["shield"] + maximum * percent // 100)


def resolve(
    seed: str,
    attackers: dict[str, int],
    defenders: dict[str, int],
    *,
    attacker_tactics: int = 0,
    defender_tactics: int = 0,
    attacker_armor_bonus: int = 0,
    defender_armor_bonus: int = 0,
    attacker_modifiers: dict[str, int] | None = None,
    defender_modifiers: dict[str, int] | None = None,
    retreat_threshold_percent: int | None = None,
    rules_version: str = "FUR-3-TERRA-COMBAT-1",
    attacker_tactics_by_unit: dict[str, int] | None = None,
    defender_structures: dict[str, list[int]] | None = None,
    defense_rules_digest: str | None = None,
    outpost_fortification_integrity: int | None = None,
    _rules_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve a bounded FUR-3 battle from a 256-bit seed and return replay data."""
    try:
        if not isinstance(seed, str):
            raise TypeError("combat seed must be text")
        seed_bytes = bytes.fromhex(seed)
    except ValueError as exc:
        raise ValueError("combat seed must be hexadecimal") from exc
    if len(seed_bytes) != 32:
        raise ValueError("combat seed must contain 256 bits")
    if any(
        type(value) is not int or value < 0 or value > 10
        for value in (attacker_tactics, defender_tactics)
    ):
        raise ValueError("invalid tactics level")
    if any(
        type(value) is not int or value < 0 or value > 100
        for value in (attacker_armor_bonus, defender_armor_bonus)
    ):
        raise ValueError("invalid combat fortification")
    default_modifiers = {"doctrine": 100, "terrain": 100, "faction": 100}
    modifiers: dict[str, dict[str, int]] = {}
    for side, supplied in (
        ("attacker", attacker_modifiers),
        ("defender", defender_modifiers),
    ):
        selected = dict(default_modifiers)
        if supplied is not None:
            if not isinstance(supplied, dict) or set(supplied) - set(default_modifiers):
                raise ValueError(f"invalid {side} combat modifiers")
            selected.update(supplied)
        if any(type(value) is not int or not 50 <= value <= 200 for value in selected.values()):
            raise ValueError(f"invalid {side} combat modifiers")
        modifiers[side] = selected
    catalog_rules = rules_for(rules_version)
    rules = _rules_override if _rules_override is not None else catalog_rules
    fortification_rules = rules.get("neutral_outpost_fortification")
    if outpost_fortification_integrity is not None:
        maximum_integrity = (
            int(fortification_rules["structure_per_tier_squared"])
            * int(fortification_rules["maximum_tier"]) ** 2
            if isinstance(fortification_rules, dict)
            else 0
        )
        if (
            rules_version != "FUR-3-TERRA-COMBAT-5"
            or not isinstance(defenders, dict)
            or defenders.get("outpost_fortification") != 1
            or type(outpost_fortification_integrity) is not int
            or not 1 <= outpost_fortification_integrity <= maximum_integrity
        ):
            raise ValueError("invalid neutral outpost fortification integrity")
    if (
        isinstance(defenders, dict)
        and defenders.get("outpost_fortification", 0) > 0
        and "outpost_fortification" not in rules["units"]
        and fortification_rules
    ):
        rules = deepcopy(rules)
        rules["units"]["outpost_fortification"] = {
            "attack": 0,
            "armor": 0,
            "shield": 0,
            "hull": (
                outpost_fortification_integrity
                if outpost_fortification_integrity is not None
                else int(fortification_rules["structure_per_tier_squared"])
            ),
            "accuracy": 0,
            "evasion": 0,
            "initiative": 0,
            "target_priority": 100,
            "counters": [],
        }
    structure_army: dict[str, int] = {}
    structure_instances: dict[str, tuple[str, int]] = {}
    defense_initial: dict[str, list[int]] | None = None
    minefield_triggered = False
    minefield_chance = 0
    if defender_structures is not None:
        from . import terra_defense

        if defense_rules_digest != terra_defense.DIGEST or rules_version not in (
            "FUR-3-TERRA-COMBAT-4",
            "FUR-3-TERRA-COMBAT-5",
        ):
            raise ValueError("unsupported or unpinned Terra defense rules")
        terra_defense.validate_stacks(defender_structures)
        defense_initial = {key: list(values) for key, values in defender_structures.items()}
        mine_result, minefield_triggered, minefield_chance = terra_defense.trigger_minefield(
            seed_bytes, defender_structures, defender_tactics
        )
        defense_initial = mine_result
        structure_profiles, structure_army, structure_instances = terra_defense.combat_profiles(
            mine_result
        )
        rules = deepcopy(rules)
        for unit_id, profile in structure_profiles.items():
            if unit_id in rules["units"]:
                raise ValueError("Terra defense profile collides with a combat unit")
            rules["units"][unit_id] = profile
        if "command_bunker" in mine_result and any(mine_result["command_bunker"]):
            bonus = int(
                terra_defense.RULES["objects"]["command_bunker"]["garrison_defense_percent"]
            )
            modifiers["defender"]["doctrine"] = min(200, modifiers["defender"]["doctrine"] + bonus)
        if minefield_triggered:
            damage_percent = int(
                terra_defense.RULES["minefield"]["attacker_damage_percent_when_triggered"]
            )
            modifiers["attacker"]["doctrine"] = max(
                50, modifiers["attacker"]["doctrine"] * damage_percent // 100
            )
    elif defense_rules_digest is not None:
        raise ValueError("defense digest supplied without a defense snapshot")
    units_catalog = rules["units"]
    formula = rules["formula"]
    digest = RULESET_DIGESTS[rules_version]
    retreat_threshold = (
        int(formula["retreat"]["default_threshold_percent"])
        if retreat_threshold_percent is None
        else retreat_threshold_percent
    )
    if type(retreat_threshold) is not int or not int(
        formula["retreat"]["threshold_min_percent"]
    ) <= retreat_threshold <= int(formula["retreat"]["threshold_max_percent"]):
        raise ValueError("invalid retreat threshold")
    if (
        not isinstance(attackers, dict)
        or not isinstance(defenders, dict)
        or any(
            type(count) is not int or count < 0
            for army in (attackers, defenders)
            for count in army.values()
        )
        or not any(attackers.values())
    ):
        raise ValueError("attacker needs a valid combat army")
    if attacker_tactics_by_unit is not None and (
        not isinstance(attacker_tactics_by_unit, dict)
        or set(attacker_tactics_by_unit) - set(attackers)
        or any(
            type(level) is not int or not 0 <= level <= 10
            for level in attacker_tactics_by_unit.values()
        )
    ):
        raise ValueError("invalid per-unit attacker tactics")
    initial_attack_count = sum(attackers.values())
    defender_counts = dict(defenders)
    for unit, count in structure_army.items():
        if unit in defender_counts:
            raise ValueError("Terra defense unit collides with a defender stack")
        defender_counts[unit] = count
    attacker, defender = _army(attackers, rules), _army(defender_counts, rules)
    rounds: list[dict[str, Any]] = []
    outcome = "attacker_win" if not _alive(defender) else "draw"
    retreated = False
    for round_no in range(1, int(rules["rounds"]["maximum"]) + 1 if _alive(defender) else 1):
        before_attack, before_defend = _counts(attacker), _counts(defender)
        initiative_attack = max(
            int(units_catalog[key]["initiative"])
            for key, count in before_attack.items()
            if count > 0
        )
        initiative_defend = max(
            int(units_catalog[key]["initiative"])
            for key, count in before_defend.items()
            if count > 0
        )
        sides = (
            (
                ("attacker", attacker, defender, attacker_tactics),
                ("defender", defender, attacker, defender_tactics),
            )
            if initiative_attack >= initiative_defend
            else (
                ("defender", defender, attacker, defender_tactics),
                ("attacker", attacker, defender, attacker_tactics),
            )
        )
        action_log = []
        for side, source, target, tactics in sides:
            if not _alive(source) or not _alive(target):
                continue
            action_log.append(
                {
                    "side": side,
                    **_fire(
                        source,
                        target,
                        source_side=side,
                        round_no=round_no,
                        seed=seed_bytes,
                        tactics=tactics,
                        target_armor_bonus=(
                            defender_armor_bonus if side == "attacker" else attacker_armor_bonus
                        ),
                        **{f"{name}_percent": value for name, value in modifiers[side].items()},
                        rules=rules,
                        tactics_by_unit=(attacker_tactics_by_unit if side == "attacker" else None),
                    ),
                }
            )
        _recharge(attacker, rules)
        rechargeable_defender = {
            unit: stack for unit, stack in defender.items() if unit not in structure_instances
        }
        _recharge(rechargeable_defender, rules)
        attack_counts, defend_counts = _counts(attacker), _counts(defender)
        casualties = initial_attack_count - sum(attack_counts.values())
        rounds.append(
            {
                "round": round_no,
                "attacker_before": before_attack,
                "defender_before": before_defend,
                "actions": action_log,
                "attacker_after": attack_counts,
                "defender_after": defend_counts,
            }
        )
        if not _alive(attacker):
            outcome = "defender_win"
            break
        if not _alive(defender):
            outcome = "attacker_win"
            break
        if casualties * 100 >= initial_attack_count * retreat_threshold:
            outcome, retreated = "attacker_retreat", True
            break
    full_defender_survivors = _counts(defender)
    ordinary_defender_survivors = {
        key: count
        for key, count in full_defender_survivors.items()
        if key not in structure_instances
    }
    ordinary_defender_losses = {
        key: int(amount) - ordinary_defender_survivors.get(key, 0)
        for key, amount in defenders.items()
    }
    output: dict[str, Any] = {
        "rules_version": rules_version,
        "rules_digest": digest,
        "seed_commitment": hashlib.sha256(seed_bytes).hexdigest(),
        "seed": seed,
        "outcome": outcome,
        "retreated": retreated,
        "rounds": rounds,
        "attacker_initial": dict(sorted(attackers.items())),
        "defender_initial": dict(sorted(defenders.items())),
        "attacker_modifiers": modifiers["attacker"],
        "defender_modifiers": modifiers["defender"],
        "attacker_armor_bonus": attacker_armor_bonus,
        "defender_armor_bonus": defender_armor_bonus,
        "attacker_survivors": _counts(attacker),
        "defender_survivors": ordinary_defender_survivors,
        "attacker_losses": {
            key: int(amount) - _counts(attacker).get(key, 0)
            for key, amount in sorted(attackers.items())
        },
        "defender_losses": ordinary_defender_losses,
    }
    if outpost_fortification_integrity is not None:
        fortification_stack = defender.get("outpost_fortification", [])
        output["outpost_fortification_integrity"] = (
            max(0, int(fortification_stack[0]["hull"])) if fortification_stack else 0
        )
    if defender_structures is not None and defense_initial is not None:
        from . import terra_defense

        structure_states = {
            unit_id: stacks[0]
            for unit_id, stacks in defender.items()
            if unit_id in structure_instances and stacks
        }
        remaining_structures = terra_defense.apply_combat_integrity(
            defense_initial, structure_instances, structure_states
        )
        output["terra_defense"] = {
            "version": terra_defense.VERSION,
            "digest": terra_defense.DIGEST,
            "initial_stacks": {key: list(values) for key, values in defender_structures.items()},
            "remaining_stacks": remaining_structures,
            "structure_initial": {
                unit: {"unit_id": unit, "integrity": defense_initial[key][index]}
                for unit, (key, index) in structure_instances.items()
            },
            "structure_remaining": {
                unit: remaining_structures[key][index]
                for unit, (key, index) in structure_instances.items()
            },
            "minefield": {
                "chance_percent": minefield_chance,
                "triggered": minefield_triggered,
                "consumed": minefield_triggered,
            },
        }
    return output


def resolve_wings(
    seed: str,
    wings: list[dict[str, Any]],
    defenders: dict[str, int],
    *,
    rules_version: str,
    defender_tactics: int = 0,
    attacker_armor_bonus: int = 0,
    defender_armor_bonus: int = 0,
    attacker_modifiers: dict[str, int] | None = None,
    defender_modifiers: dict[str, int] | None = None,
    retreat_threshold_percent: int | None = None,
    defender_structures: dict[str, list[int]] | None = None,
    defense_rules_digest: str | None = None,
) -> dict[str, Any]:
    """Resolve an alliance force as distinct stacks and return each wing's survivors."""
    base_rules = rules_for(rules_version)
    rules = deepcopy(base_rules)
    base_units = base_rules["units"]
    alias_maps: list[dict[str, str]] = []
    attackers: dict[str, int] = {}
    tactics: dict[str, int] = {}
    alias_owner: dict[str, str] = {}
    for index, wing in enumerate(wings):
        army, level = wing.get("army"), wing.get("tactics")
        if (
            not isinstance(army, dict)
            or type(level) is not int
            or not 0 <= level <= 10
            or not army
            or any(
                unit not in base_units or type(count) is not int or count <= 0
                for unit, count in army.items()
            )
        ):
            raise ValueError("invalid alliance attack wing")
        aliases: dict[str, str] = {}
        for unit, count in sorted(army.items()):
            alias = f"wing_{index:02d}_{unit}"
            aliases[unit] = alias
            alias_owner[alias] = unit
            attackers[alias] = count
            tactics[alias] = level
        alias_maps.append(aliases)

    for alias, unit in alias_owner.items():
        profile = deepcopy(base_units[unit])
        rules["units"][alias] = profile
    for defender_profile in rules["units"].values():
        if defender_profile is base_units.get("outpost_fortification"):
            continue
        counters = set(defender_profile["counters"])
        defender_profile["counters"] = sorted(
            counters | {alias for alias, unit in alias_owner.items() if unit in counters}
        )

    result = resolve(
        seed,
        attackers,
        defenders,
        attacker_tactics_by_unit=tactics,
        defender_tactics=defender_tactics,
        attacker_armor_bonus=attacker_armor_bonus,
        defender_armor_bonus=defender_armor_bonus,
        attacker_modifiers=attacker_modifiers,
        defender_modifiers=defender_modifiers,
        retreat_threshold_percent=retreat_threshold_percent,
        rules_version=rules_version,
        defender_structures=defender_structures,
        defense_rules_digest=defense_rules_digest,
        _rules_override=rules,
    )

    def aggregate(snapshot: dict[str, int]) -> dict[str, int]:
        return {
            unit: total
            for unit in sorted(base_units)
            if (
                total := sum(
                    snapshot.get(aliases[unit], 0) for aliases in alias_maps if unit in aliases
                )
            )
            > 0
        }

    def split(snapshot: dict[str, int]) -> list[dict[str, int]]:
        return [
            {unit: snapshot.get(alias, 0) for unit, alias in aliases.items()}
            for aliases in alias_maps
        ]

    wing_survivors = split(result["attacker_survivors"])
    result["attacker_initial"] = aggregate(result["attacker_initial"])
    result["attacker_survivors"] = aggregate(result["attacker_survivors"])
    result["attacker_losses"] = {
        unit: count - result["attacker_survivors"].get(unit, 0)
        for unit, count in result["attacker_initial"].items()
    }
    result["wing_survivors"] = wing_survivors
    for battle_round in result["rounds"]:
        before, after = battle_round["attacker_before"], battle_round["attacker_after"]
        battle_round["attacker_wings_before"] = split(before)
        battle_round["attacker_wings_after"] = split(after)
        battle_round["attacker_before"] = aggregate(before)
        battle_round["attacker_after"] = aggregate(after)
    return result


def simulate(
    attackers: dict[str, int],
    defenders: dict[str, int],
    *,
    simulation_key: str,
    attacker_tactics: int = 0,
    defender_tactics: int = 0,
    attacker_armor_bonus: int = 0,
    defender_armor_bonus: int = 0,
    attacker_modifiers: dict[str, int] | None = None,
    defender_modifiers: dict[str, int] | None = None,
    retreat_threshold_percent: int | None = None,
    loot_stock: list[int] | None = None,
    logistics_level: int = 0,
    unit_transport_capacity: dict[str, int] | None = None,
    rules_version: str = "FUR-3-TERRA-COMBAT-1",
    defender_structures: dict[str, list[int]] | None = None,
    defense_rules_digest: str | None = None,
    outpost_fortification_integrity: int | None = None,
) -> dict[str, Any]:
    """Return a deterministic Monte Carlo projection without persisting combat state."""
    if not isinstance(simulation_key, str) or not simulation_key:
        raise ValueError("simulation key is required")
    if type(logistics_level) is not int or not 0 <= logistics_level <= 10:
        raise ValueError("invalid logistics level")
    if loot_stock is not None and (
        not isinstance(loot_stock, list)
        or len(loot_stock) != 3
        or any(type(amount) is not int or amount < 0 for amount in loot_stock)
    ):
        raise ValueError("invalid simulation loot stock")
    rules_for(rules_version)
    if defender_structures is not None:
        from . import terra_defense

        if (
            rules_version not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            or defense_rules_digest != terra_defense.DIGEST
        ):
            raise ValueError("unsupported or unpinned Terra defense simulation rules")
        terra_defense.validate_stacks(defender_structures)
    elif defense_rules_digest is not None:
        raise ValueError("defense digest supplied without a defense simulation snapshot")
    if unit_transport_capacity is not None and (
        not isinstance(unit_transport_capacity, dict)
        or set(unit_transport_capacity) - set(rules_for(rules_version)["units"])
        or any(
            type(capacity) is not int or not 0 <= capacity <= 1_000_000
            for capacity in unit_transport_capacity.values()
        )
    ):
        raise ValueError("invalid per-unit transport capacity")
    inputs = {
        "simulation_key": simulation_key,
        "rules_digest": RULESET_DIGESTS[rules_version],
        "attackers": dict(sorted(attackers.items())) if isinstance(attackers, dict) else attackers,
        "defenders": dict(sorted(defenders.items())) if isinstance(defenders, dict) else defenders,
        "attacker_tactics": attacker_tactics,
        "defender_tactics": defender_tactics,
        "attacker_armor_bonus": attacker_armor_bonus,
        "defender_armor_bonus": defender_armor_bonus,
        "attacker_modifiers": attacker_modifiers,
        "defender_modifiers": defender_modifiers,
        "retreat_threshold_percent": retreat_threshold_percent,
        "loot_stock": loot_stock,
        "logistics_level": logistics_level,
        "unit_transport_capacity": unit_transport_capacity,
        "defender_structures": defender_structures,
        "defense_rules_digest": defense_rules_digest,
        "outpost_fortification_integrity": outpost_fortification_integrity,
    }
    fingerprint = hashlib.sha256(
        json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).digest()
    results: list[dict[str, Any]] = []
    outcome_counts = {"attacker_win": 0, "defender_win": 0, "attacker_retreat": 0, "draw": 0}
    loot_scenarios: list[list[int]] = []
    for sample in range(SIMULATION_SAMPLES):
        seed = hashlib.sha256(fingerprint + sample.to_bytes(2, "big")).hexdigest()
        result = resolve(
            seed,
            attackers,
            defenders,
            attacker_tactics=attacker_tactics,
            defender_tactics=defender_tactics,
            attacker_armor_bonus=attacker_armor_bonus,
            defender_armor_bonus=defender_armor_bonus,
            attacker_modifiers=attacker_modifiers,
            defender_modifiers=defender_modifiers,
            retreat_threshold_percent=retreat_threshold_percent,
            rules_version=rules_version,
            defender_structures=defender_structures,
            defense_rules_digest=defense_rules_digest,
            outpost_fortification_integrity=outpost_fortification_integrity,
        )
        result.pop("seed", None)
        result.pop("seed_commitment", None)
        result["victory"] = result["outcome"] == "attacker_win"
        outcome_counts[result["outcome"]] += 1
        if loot_stock is not None:
            capacity = (
                sum(result["attacker_survivors"].values()) * (40 + 10 * logistics_level)
                if unit_transport_capacity is None
                else sum(
                    count * unit_transport_capacity.get(unit, 0)
                    for unit, count in result["attacker_survivors"].items()
                )
            )
            result["loot"] = (
                [min(amount, capacity // 3) for amount in loot_stock]
                if result["victory"]
                else [0, 0, 0]
            )
            loot_scenarios.append(result["loot"])
        results.append(result)

    results.sort(
        key=lambda result: (
            sum(result["attacker_losses"].values()),
            result["outcome"],
            tuple(sorted(result["attacker_survivors"].items())),
        )
    )
    representative = dict(results[len(results) // 2])

    def ranges(field: str, initial: dict[str, int]) -> dict[str, list[int]]:
        return {
            unit: [
                min(result[field].get(unit, 0) for result in results),
                max(result[field].get(unit, 0) for result in results),
            ]
            for unit in sorted(initial)
        }

    representative["deterministic"] = False
    representative["simulation"] = {
        "version": SIMULATION_VERSION,
        "samples": SIMULATION_SAMPLES,
        "attacker_victory_percent": round(
            outcome_counts["attacker_win"] * 100 / SIMULATION_SAMPLES, 1
        ),
        "outcomes_percent": {
            name: round(count * 100 / SIMULATION_SAMPLES, 1)
            for name, count in outcome_counts.items()
        },
        "attacker_losses_total": [
            min(sum(result["attacker_losses"].values()) for result in results),
            max(sum(result["attacker_losses"].values()) for result in results),
        ],
        "attacker_survivors_total": [
            min(sum(result["attacker_survivors"].values()) for result in results),
            max(sum(result["attacker_survivors"].values()) for result in results),
        ],
        "defender_losses_total": [
            min(sum(result["defender_losses"].values()) for result in results),
            max(sum(result["defender_losses"].values()) for result in results),
        ],
        "attacker_losses": ranges("attacker_losses", attackers),
        "attacker_survivors": ranges("attacker_survivors", attackers),
        "defender_losses": ranges("defender_losses", defenders),
        "defender_survivors": ranges("defender_survivors", defenders),
        "loot": (
            [
                [
                    min(sample[index] for sample in loot_scenarios),
                    max(sample[index] for sample in loot_scenarios),
                ]
                for index in range(3)
            ]
            if loot_scenarios
            else None
        ),
    }
    if defender_structures is not None:
        defense_results = [result["terra_defense"] for result in results]
        first_defense = defense_results[0]
        structure_ids = sorted(first_defense["structure_remaining"])
        representative["simulation"]["terra_defense"] = {
            "version": first_defense["version"],
            "digest": first_defense["digest"],
            "minefield_trigger_percent": round(
                sum(bool(result["minefield"]["triggered"]) for result in defense_results)
                * 100
                / SIMULATION_SAMPLES,
                1,
            ),
            "structure_integrity_ranges": {
                unit_id: [
                    min(result["structure_remaining"][unit_id] for result in defense_results),
                    max(result["structure_remaining"][unit_id] for result in defense_results),
                ]
                for unit_id in structure_ids
            },
        }
    return representative


for _rules in RULESETS.values():
    validate_rules(_rules)
