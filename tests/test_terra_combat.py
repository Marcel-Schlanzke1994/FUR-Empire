"""Pure FUR-3 combat tests; legacy FUR-2 battles stay in their existing suites."""

from __future__ import annotations

import copy
import hashlib

import pytest

from fur_empire import terra_combat


def test_terra_combat_rules_are_versioned_and_leave_fur2_separate() -> None:
    assert terra_combat.VERSION == "FUR-3-TERRA-COMBAT-1"
    assert terra_combat.RULES["legacy_fur2_preserved"] is True
    assert terra_combat.RULES["rounds"]["maximum"] == 6
    assert terra_combat.DIGEST.startswith("sha256:")
    terra_combat.validate_rules(terra_combat.RULES)


def test_v2_fortification_is_opt_in_and_does_not_change_v1() -> None:
    v1 = terra_combat.resolve("00" * 32, {"ranger": 1}, {})
    v2 = terra_combat.resolve(
        "00" * 32,
        {"ranger": 1},
        {"outpost_fortification": 64},
        rules_version="FUR-3-TERRA-COMBAT-2",
    )
    assert v1["outcome"] == "attacker_win"
    assert v1["rules_digest"] == terra_combat.DIGEST
    assert v2["rules_version"] == "FUR-3-TERRA-COMBAT-2"
    assert v2["outcome"] != "attacker_win"
    assert (
        terra_combat.RULESETS["FUR-3-TERRA-COMBAT-2"]["neutral_outpost_fortification"]["status"]
        == "provisional_balance"
    )


def test_combat_3_contains_versioned_full_unit_economy_roster_but_is_locked() -> None:
    rules = terra_combat.rules_for("FUR-3-TERRA-COMBAT-3")
    terra_combat.validate_rules(rules)
    assert len(rules["units"]) == 21
    assert rules["unit_economy"]["status"] == "provisional_balance"
    assert rules["unit_economy"]["enabled_for_training"] is False
    for unit in rules["units"].values():
        assert unit["role"]
        assert unit["speed"] > 0
        assert unit["range"] > 0
        assert len(unit["cost"]) == 3
        assert set(unit["prerequisites"]) == {"buildings", "tech"}
        assert unit["repair_ratio"] <= 100
    assert rules["units"]["logistics_convoy"]["cargo"] == 240
    assert rules["units"]["titan_colossus"]["speed"] < rules["units"]["ranger"]["speed"]


def test_combat_4_is_separate_lifecycle_draft_and_does_not_change_combat_3() -> None:
    previous_digest = terra_combat.RULESET_DIGESTS["FUR-3-TERRA-COMBAT-3"]
    assert previous_digest == (
        "sha256:4e8cfbd5d9fe12dadb614521e9589d830c46f35a0d326ace517a8f2208b09b7a"
    )
    v3 = terra_combat.rules_for("FUR-3-TERRA-COMBAT-3")
    v4 = terra_combat.rules_for("FUR-3-TERRA-COMBAT-4")
    terra_combat.validate_rules(v4)
    assert len(v4["units"]) == 21
    assert v4["units"] == v3["units"]
    assert v4["unit_economy"]["enabled_for_training"] is False
    assert terra_combat.RULESET_DIGESTS["FUR-3-TERRA-COMBAT-3"] == previous_digest
    assert v4["version"] != v3["version"]


def test_terra_alliance_wings_keep_distinct_stacks_and_personal_tactics() -> None:
    wings = [
        {"army": {"ranger": 12, "mech": 2}, "tactics": 0},
        {"army": {"ranger": 9}, "tactics": 4},
    ]
    first = terra_combat.resolve_wings(
        "41" * 32,
        wings,
        {"sentinel": 8},
        rules_version="FUR-3-TERRA-COMBAT-1",
        defender_tactics=1,
    )
    second = terra_combat.resolve_wings(
        "41" * 32,
        wings,
        {"sentinel": 8},
        rules_version="FUR-3-TERRA-COMBAT-1",
        defender_tactics=1,
    )
    assert first == second
    assert len(first["wing_survivors"]) == 2
    for index, wing in enumerate(wings):
        assert sum(first["wing_survivors"][index].values()) <= sum(wing["army"].values())
        assert first["rounds"][0]["attacker_wings_before"][index] == wing["army"]
    assert all(not key.startswith("wing_") for key in first["attacker_survivors"])


def test_terra_combat_replay_is_deterministic_and_conserves_each_army() -> None:
    attackers = {"ranger": 8, "mech": 2}
    defenders = {"sentinel": 4, "bastion_walker": 1}
    before = (copy.deepcopy(attackers), copy.deepcopy(defenders))
    seed = "4d" * 32

    first = terra_combat.resolve(seed, attackers, defenders, attacker_tactics=2, defender_tactics=1)
    second = terra_combat.resolve(
        seed, attackers, defenders, attacker_tactics=2, defender_tactics=1
    )

    assert first == second
    assert first["rules_version"] == terra_combat.VERSION
    assert first["seed_commitment"] == hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    assert 1 <= len(first["rounds"]) <= 6
    assert sum(first["attacker_initial"].values()) == sum(
        first["attacker_survivors"].values()
    ) + sum(first["attacker_losses"].values())
    assert sum(first["defender_initial"].values()) == sum(
        first["defender_survivors"].values()
    ) + sum(first["defender_losses"].values())
    assert (attackers, defenders) == before


def test_terra_combat_one_thousand_seed_replays_are_stable_and_read_only() -> None:
    attackers = {"ranger": 8, "mech": 2}
    defenders = {"sentinel": 4, "bastion_walker": 1}
    before = (copy.deepcopy(attackers), copy.deepcopy(defenders))
    for value in range(1000):
        seed = f"{value:064x}"
        first = terra_combat.resolve(
            seed, attackers, defenders, attacker_tactics=2, defender_tactics=1
        )
        second = terra_combat.resolve(
            seed, attackers, defenders, attacker_tactics=2, defender_tactics=1
        )
        assert first == second
        assert sum(first["attacker_initial"].values()) == sum(
            first["attacker_survivors"].values()
        ) + sum(first["attacker_losses"].values())
        assert sum(first["defender_initial"].values()) == sum(
            first["defender_survivors"].values()
        ) + sum(first["defender_losses"].values())
        assert "seed" not in first or first["seed"] == seed
    assert (attackers, defenders) == before


def test_terra_combat_rejects_invalid_armies_seeds_and_retreat_thresholds() -> None:
    with pytest.raises(ValueError, match="army"):
        terra_combat.resolve("00" * 32, {"unknown": 1}, {"ranger": 1})
    with pytest.raises(ValueError, match="hexadecimal"):
        terra_combat.resolve("not-a-seed", {"ranger": 1}, {"sentinel": 1})
    with pytest.raises(ValueError, match="retreat threshold"):
        terra_combat.resolve("00" * 32, {"ranger": 1}, {"sentinel": 1}, retreat_threshold_percent=0)


def test_terra_combat_bounds_army_size_before_simulation() -> None:
    limit = int(terra_combat.RULES["limits"]["maximum_army_units_per_side"])
    with pytest.raises(ValueError, match="unit limit"):
        terra_combat.resolve("00" * 32, {"ranger": limit + 1}, {"sentinel": 1})


def test_terra_combat_replay_pins_all_combat_modifiers() -> None:
    seed = "17" * 32
    attackers = {"mech": 4}
    defenders = {"sentinel": 5}
    baseline = terra_combat.resolve(seed, attackers, defenders)
    modified = terra_combat.resolve(
        seed,
        attackers,
        defenders,
        attacker_modifiers={"doctrine": 125, "terrain": 110, "faction": 115},
    )

    assert modified["attacker_modifiers"] == {
        "doctrine": 125,
        "terrain": 110,
        "faction": 115,
    }
    assert baseline["attacker_modifiers"] == {
        "doctrine": 100,
        "terrain": 100,
        "faction": 100,
    }
    assert modified["rounds"] != baseline["rounds"]
    with pytest.raises(ValueError, match="modifiers"):
        terra_combat.resolve(seed, attackers, defenders, defender_modifiers={"terrain": 201})


def test_terra_combat_simulation_is_repeatable_bounded_and_reports_uncertainty() -> None:
    attackers = {"ranger": 8, "mech": 2}
    defenders = {"sentinel": 4, "bastion_walker": 1}
    first = terra_combat.simulate(
        attackers,
        defenders,
        simulation_key="probe:world:1:target:post-7",
        attacker_tactics=2,
        defender_tactics=1,
        retreat_threshold_percent=37,
        loot_stock=[400, 300, 200],
        logistics_level=2,
    )
    second = terra_combat.simulate(
        attackers,
        defenders,
        simulation_key="probe:world:1:target:post-7",
        attacker_tactics=2,
        defender_tactics=1,
        retreat_threshold_percent=37,
        loot_stock=[400, 300, 200],
        logistics_level=2,
    )

    assert first == second
    assert first["deterministic"] is False
    assert first["simulation"]["version"] == terra_combat.SIMULATION_VERSION
    assert first["simulation"]["samples"] == terra_combat.SIMULATION_SAMPLES
    assert 0 <= first["simulation"]["attacker_victory_percent"] <= 100
    assert sum(first["simulation"]["outcomes_percent"].values()) == pytest.approx(100, abs=0.5)
    low_loss, high_loss = first["simulation"]["attacker_losses_total"]
    assert low_loss <= sum(first["attacker_losses"].values()) <= high_loss
    low_survivors, high_survivors = first["simulation"]["attacker_survivors_total"]
    assert low_survivors <= sum(first["attacker_survivors"].values()) <= high_survivors
    assert len(first["simulation"]["loot"]) == 3
    assert "seed" not in first and "seed_commitment" not in first
    assert attackers == {"ranger": 8, "mech": 2}
    assert defenders == {"sentinel": 4, "bastion_walker": 1}


def test_combat4_simulation_uses_structures_and_reports_minefield_probability() -> None:
    from fur_empire import terra_defense

    stacks = {"kinetic_turret": [100], "proximity_mines": [100]}
    kwargs = {
        "rules_version": "FUR-3-TERRA-COMBAT-4",
        "defender_structures": stacks,
        "defense_rules_digest": terra_defense.DIGEST,
        "defender_tactics": 10,
    }
    first = terra_combat.simulate(
        {"ranger": 12}, {"ranger": 2}, simulation_key="defense-probe", **kwargs
    )
    second = terra_combat.simulate(
        {"ranger": 12}, {"ranger": 2}, simulation_key="defense-probe", **kwargs
    )
    assert first == second
    assert first["terra_defense"]["initial_stacks"] == stacks
    defense = first["simulation"]["terra_defense"]
    assert defense["digest"] == terra_defense.DIGEST
    assert 0 <= defense["minefield_trigger_percent"] <= 100
    integrity_range = defense["structure_integrity_ranges"]["furdef_kinetic_turret_0"]
    representative_integrity = first["terra_defense"]["structure_remaining"][
        "furdef_kinetic_turret_0"
    ]
    assert integrity_range[0] <= representative_integrity <= integrity_range[1]
    assert "seed" not in first and "seed_commitment" not in first
    with pytest.raises(ValueError, match="unpinned Terra defense"):
        terra_combat.simulate(
            {"ranger": 1},
            {"ranger": 1},
            simulation_key="wrong-digest",
            rules_version="FUR-3-TERRA-COMBAT-4",
            defender_structures=stacks,
            defense_rules_digest="sha256:wrong",
        )


def test_simulation_uses_explicit_per_unit_cargo_capacity() -> None:
    result = terra_combat.simulate(
        {"logistics_convoy": 1},
        {},
        simulation_key="convoy-cargo",
        loot_stock=[1000, 1000, 1000],
        unit_transport_capacity={"logistics_convoy": 240},
        rules_version="FUR-3-TERRA-COMBAT-4",
    )
    assert result["loot"] == [80, 80, 80]
