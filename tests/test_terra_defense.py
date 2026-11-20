from copy import deepcopy

import pytest

from fur_empire import terra_combat, terra_defense


def test_provisional_defense_contract_is_versioned_and_fur2_preserving() -> None:
    terra_defense.validate_rules()
    assert terra_defense.VERSION == "FUR-3-TERRA-DEFENSE-1"
    assert terra_defense.RULES["activation"] == "FUR-3-TERRA-COMBAT-4-only"
    assert terra_defense.RULES["damage"]["minefield_consumed_on_successful_trigger"]
    assert terra_defense.RULES["reports"]["include_minefield_trigger_in_participant_combat_report"]
    assert terra_defense.DIGEST.startswith("sha256:")


@pytest.mark.parametrize("hq,expected", [(0, 1), (2, 1), (3, 2), (6, 3), (30, 4)])
def test_defense_slot_limit_is_bounded(hq: int, expected: int) -> None:
    assert terra_defense.slot_limit(hq) == expected


def test_defense_power_respects_per_structure_integrity() -> None:
    stacks = {
        "kinetic_turret": [100, 50],
        "aegis_emitter": [25],
        "proximity_mines": [],
        "command_bunker": [100],
    }
    assert terra_defense.defense_power(stacks) == 180 + 90 + 35 + 80


@pytest.mark.parametrize(
    "stack", [{"unknown": [100]}, {"kinetic_turret": [101]}, {"kinetic_turret": [-1]}]
)
def test_invalid_defense_stack_is_rejected(stack: dict[str, list[int]]) -> None:
    with pytest.raises(ValueError):
        terra_defense.defense_power(stack)


def test_contract_rejects_unapproved_balance_mutation() -> None:
    rules = deepcopy(terra_defense.RULES)
    rules["status"] = "approved"
    with pytest.raises(ValueError):
        terra_defense.validate_rules(rules)


def test_combat4_structures_join_rounds_and_return_deterministic_integrity() -> None:
    stacks = {
        "kinetic_turret": [100],
        "aegis_emitter": [60],
        "proximity_mines": [],
        "command_bunker": [100],
    }
    kwargs = {
        "rules_version": "FUR-3-TERRA-COMBAT-4",
        "defender_tactics": 3,
        "defender_structures": stacks,
        "defense_rules_digest": terra_defense.DIGEST,
    }
    first = terra_combat.resolve("c" * 64, {"mech": 20}, {"ranger": 4}, **kwargs)
    second = terra_combat.resolve("c" * 64, {"mech": 20}, {"ranger": 4}, **kwargs)
    assert first == second
    assert first["terra_defense"]["digest"] == terra_defense.DIGEST
    assert first["terra_defense"]["initial_stacks"] == stacks
    assert first["defender_initial"] == {"ranger": 4}
    assert "furdef_kinetic_turret_0" in first["rounds"][0]["defender_before"]
    remaining = first["terra_defense"]["remaining_stacks"]
    assert 0 <= remaining["kinetic_turret"][0] <= 100
    assert 0 <= remaining["aegis_emitter"][0] <= 60
    assert remaining["command_bunker"][0] <= 100


def test_seeded_minefield_consumes_one_field_and_modifies_attack_damage() -> None:
    mines = {"proximity_mines": [100, 100]}
    seed = bytes.fromhex("c" * 64)
    updated, triggered, chance = terra_defense.trigger_minefield(seed, mines, 6)
    assert chance == 50
    assert triggered
    assert updated["proximity_mines"] == [0, 100]
    result = terra_combat.resolve(
        seed.hex(),
        {"mech": 4},
        {"ranger": 1},
        rules_version="FUR-3-TERRA-COMBAT-4",
        defender_tactics=6,
        defender_structures=mines,
        defense_rules_digest=terra_defense.DIGEST,
    )
    assert result["terra_defense"]["minefield"] == {
        "chance_percent": 50,
        "triggered": True,
        "consumed": True,
    }
    assert result["attacker_modifiers"]["doctrine"] == 80
    assert result["terra_defense"]["remaining_stacks"]["proximity_mines"] == [0, 100]


def test_combat4_defenses_are_shared_by_individual_alliance_wings() -> None:
    result = terra_combat.resolve_wings(
        "c" * 64,
        [{"army": {"mech": 4}, "tactics": 1}, {"army": {"ranger": 5}, "tactics": 2}],
        {"ranger": 3},
        rules_version="FUR-3-TERRA-COMBAT-4",
        defender_tactics=6,
        defender_structures={"kinetic_turret": [100], "proximity_mines": [100]},
        defense_rules_digest=terra_defense.DIGEST,
    )
    assert len(result["wing_survivors"]) == 2
    assert result["terra_defense"]["digest"] == terra_defense.DIGEST
    assert "furdef_kinetic_turret_0" in result["rounds"][0]["defender_before"]
    assert result["terra_defense"]["minefield"]["triggered"]


def test_defense_replay_requires_supported_digest_and_combat4() -> None:
    with pytest.raises(ValueError, match="unpinned Terra defense"):
        terra_combat.resolve(
            "c" * 64,
            {"mech": 1},
            {"ranger": 1},
            rules_version="FUR-3-TERRA-COMBAT-4",
            defender_structures={"kinetic_turret": [100]},
            defense_rules_digest="sha256:wrong",
        )
    with pytest.raises(ValueError, match="unpinned Terra defense"):
        terra_combat.resolve(
            "c" * 64,
            {"mech": 1},
            {"ranger": 1},
            rules_version="FUR-3-TERRA-COMBAT-3",
            defender_structures={"kinetic_turret": [100]},
            defense_rules_digest=terra_defense.DIGEST,
        )
