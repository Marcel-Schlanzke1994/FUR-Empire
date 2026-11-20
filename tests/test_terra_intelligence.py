"""Deterministic tests for the versioned Terra counter-intelligence rules."""

import pytest

from fur_empire import terra_intelligence


def test_versioned_rules_and_probability_caps():
    terra_intelligence.validate_rules(terra_intelligence.RULES)
    assert terra_intelligence.chances(0, 0) == (0, 10)
    assert terra_intelligence.chances(10, 10) == (50, 60)
    assert terra_intelligence.chances(4, 3) == (17, 28)


def test_seeded_outcomes_are_stable_private_inputs_and_do_not_mutate_army():
    seed = "01" * 32
    army = {"ranger": 5}
    first = terra_intelligence.resolve(
        seed, army["ranger"], interception_percent=50, detection_percent=60
    )
    second = terra_intelligence.resolve(
        seed, army["ranger"], interception_percent=50, detection_percent=60
    )
    assert first == second
    assert army == {"ranger": 5}
    assert "seed" not in first
    assert first["detected"] is True
    assert first["intercepted"] is True
    assert first["rangers_lost"] == 1
    assert first["rangers_returned"] == 4


def test_one_thousand_seeded_replays_are_stable_and_do_not_mutate_army():
    for value in range(1000):
        seed = f"{value:064x}"
        army = {"ranger": value % 10 + 1}
        first = terra_intelligence.resolve(
            seed, army["ranger"], interception_percent=23, detection_percent=41
        )
        second = terra_intelligence.resolve(
            seed, army["ranger"], interception_percent=23, detection_percent=41
        )
        assert first == second
        assert army == {"ranger": value % 10 + 1}


def test_detection_without_interception_preserves_rangers():
    seed = ""
    for value in range(1000):
        candidate = f"{value:064x}"
        result = terra_intelligence.resolve(
            candidate,
            1,
            interception_percent=0,
            detection_percent=60,
        )
        if result["detected"] and not result["intercepted"]:
            seed = candidate
            break
    assert seed
    outcome = terra_intelligence.resolve(seed, 1, interception_percent=0, detection_percent=60)
    assert outcome["detected"] is True
    assert outcome["intercepted"] is False
    assert outcome["rangers_lost"] == 0
    assert outcome["rangers_returned"] == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": "not-a-seed", "ranger_count": 1},
        {"seed": "00" * 32, "ranger_count": 0},
        {"seed": "00" * 32, "ranger_count": 1, "interception_percent": 51},
    ],
)
def test_invalid_resolver_inputs_are_rejected(kwargs):
    seed = kwargs.pop("seed")
    ranger_count = kwargs.pop("ranger_count")
    params = {"interception_percent": 0, "detection_percent": 0, **kwargs}
    with pytest.raises(ValueError):
        terra_intelligence.resolve(seed, ranger_count, **params)
