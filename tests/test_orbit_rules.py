import pytest

from fur_empire.orbit_rules import quote_travel, system_chart


def test_travel_uses_slowest_ship_and_aggregates_fuel_and_cargo():
    assert quote_travel({"courier": 2, "probe": 1}, 121) == (61, 363, 340)
    assert quote_travel({"courier": 1}, 1) == (60, 1, 160)


def test_travel_rejects_boolean_counts_and_unknown_ships():
    with pytest.raises(ValueError, match="Stückzahlen"):
        quote_travel({"probe": True}, 1)
    with pytest.raises(ValueError, match="Ungültige Schiffe"):
        quote_travel({"unknown": 1}, 1)


def test_system_chart_is_stable_world_scoped_and_has_only_public_geography():
    chart = system_chart(48192, 1, 1, 100)
    assert chart == system_chart(48192, 1, 1, 100)
    assert chart != system_chart(48192, 2, 1, 100)
    assert [entry["slot"] for entry in chart] == list(range(1, 17))
    assert all(set(entry) == {"slot", "terrain"} for entry in chart)
    with pytest.raises(ValueError, match="Orbit-Koordinaten"):
        system_chart(48192, 1, 1, 101)
