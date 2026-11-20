from fur_empire import orbit_attack, orbit_battle, orbit_rules


def test_orbit_battle_replays_same_seed_and_snapshot():
    seed = bytes(range(32))
    fleet = {"flagship": 4, "probe": 3}
    defense = {"probe": 5}
    result = orbit_battle.resolve(fleet, defense, seed)
    assert result == orbit_battle.resolve(dict(reversed(list(fleet.items()))), defense, seed)
    assert result["rules_digest"] == orbit_rules.DIGEST
    assert result["seed_commitment"] == orbit_battle.seed_commitment(seed)
    assert result["attacker_won"]
    assert result["survivors"][1] == {}
    assert fleet == {"flagship": 4, "probe": 3}
    assert defense == {"probe": 5}


def test_orbit_battle_shields_preserve_defended_position_at_round_limit():
    result = orbit_battle.resolve({"probe": 1}, {"probe": 1}, bytes(32))
    assert len(result["rounds"]) == orbit_rules.COMBAT_ROUNDS
    assert result["survivors"] == [{"probe": 1}, {"probe": 1}]
    assert not result["attacker_won"]


def test_platform_defends_without_becoming_a_buildable_ship():
    station = orbit_rules.DEFENSE.id
    result = orbit_battle.resolve({"probe": 1}, {station: 1}, bytes(32))
    assert result["survivors"] == [{}, {station: 1}]
    assert not result["attacker_won"]
    assert station not in orbit_rules.ship_catalog()


def test_allied_survivors_are_allocated_without_loss_or_duplication():
    assert orbit_attack.allocate_survivors([6, 3, 1], 5) == [3, 2, 0]
    assert orbit_attack.allocate_survivors([1, 1], 1) == [1, 0]
    assert orbit_attack.allocate_survivors([1, 2], 0) == [0, 0]
    assert orbit_attack.allocate_survivors([1, 2], 3) == [1, 2]


def test_retreat_stops_after_first_partial_loss():
    result = orbit_battle.resolve({"probe": 10}, {"flagship": 1}, bytes(32), retreat_pct=10)
    assert result["retreated"]
    assert not result["attacker_won"]
    assert len(result["rounds"]) == 1
    assert 0 < result["survivors"][0]["probe"] < 10


def test_lances_add_damage_only_to_first_volley():
    seed = bytes(32)
    baseline = orbit_battle.resolve({"probe": 1}, {"flagship": 1}, seed)
    armed = orbit_battle.resolve({"probe": 1}, {"flagship": 1}, seed, opening_lances=1)
    assert armed["rounds"][0]["volleys"][0] == baseline["rounds"][0]["volleys"][0] + 40
    assert armed["rounds"][0]["volleys"][1] == baseline["rounds"][0]["volleys"][1]
