"""Deterministic Orbit-1 combat. The caller owns persistence and authorization."""

import hashlib
from collections.abc import Mapping
from typing import Any

from . import orbit_rules

FORMULA = "orbit_battle_v1"


def seed_commitment(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


def _damage(power: int, seed: bytes, round_no: int, side: str) -> int:
    sample = hashlib.sha256(seed + f":{round_no}:{side}".encode("ascii")).digest()
    variance = 900 + int.from_bytes(sample[:4], "big") % 201
    return max(1, power * orbit_rules.ACCURACY_PERMILLE * variance // 1_000_000) if power else 0


def resolve(
    attackers: Mapping[str, int],
    defenders: Mapping[str, int],
    seed: bytes,
    retreat_pct: int | None = None,
    opening_lances: int = 0,
) -> dict[str, Any]:
    """Resolve simultaneous volleys with round shields and cumulative hull damage."""
    catalog = orbit_rules.combat_catalog()
    if type(opening_lances) is not int or not 0 <= opening_lances <= orbit_rules.AMMUNITION_CAP:
        raise ValueError("Ungültige Orbit-Eröffnungssalve.")
    if (
        (retreat_pct is not None and (type(retreat_pct) is not int or not 10 <= retreat_pct <= 100))
        or len(seed) != 32
        or any(
            ship not in catalog or type(count) is not int or count < 0
            for fleet in (attackers, defenders)
            for ship, count in fleet.items()
        )
    ):
        raise ValueError("Ungültiger Orbit-Kampfsnapshot.")

    fleets = [
        {ship: count for ship, count in fleet.items() if count} for fleet in (attackers, defenders)
    ]
    initial = [dict(fleet) for fleet in fleets]
    hull_damage = [{ship: 0 for ship in fleet} for fleet in fleets]
    rounds = []
    starting_count = sum(initial[0].values())
    retreated = False
    for round_no in range(1, orbit_rules.COMBAT_ROUNDS + 1):
        if not all(any(fleet.values()) for fleet in fleets):
            break
        power = [
            sum(catalog[ship].attack * count for ship, count in fleet.items()) for fleet in fleets
        ]
        volleys = [
            _damage(power[0], seed, round_no, "attack"),
            _damage(power[1], seed, round_no, "defense"),
        ]
        if round_no == 1:
            volleys[0] += opening_lances * orbit_rules.LANCE_POWER
        losses = []
        for side, fleet in enumerate(fleets):
            incoming = volleys[1 - side]
            shields = sum(catalog[ship].shield * count for ship, count in fleet.items())
            incoming = max(0, incoming - shields)
            lost = {}
            for ship in sorted(fleet):
                if not fleet[ship] or not incoming:
                    continue
                hull = catalog[ship].hull
                absorbed = min(incoming, fleet[ship] * hull - hull_damage[side][ship])
                destroyed, hull_damage[side][ship] = divmod(
                    hull_damage[side][ship] + absorbed, hull
                )
                fleet[ship] -= destroyed
                incoming -= absorbed
                if destroyed:
                    lost[ship] = destroyed
            losses.append(lost)
        rounds.append({"round": round_no, "volleys": volleys, "losses": losses})
        remaining = sum(fleets[0].values())
        if (
            retreat_pct is not None
            and remaining
            and any(fleets[1].values())
            and (starting_count - remaining) * 100 >= starting_count * retreat_pct
        ):
            retreated = True
            break
    surviving = [{ship: count for ship, count in fleet.items() if count} for fleet in fleets]
    return {
        "formula": FORMULA,
        "rule_version": orbit_rules.VERSION,
        "rules_digest": orbit_rules.DIGEST,
        "seed": seed.hex(),
        "seed_commitment": seed_commitment(seed),
        "initial": initial,
        "rounds": rounds,
        "survivors": surviving,
        "attacker_won": bool(surviving[0] and not surviving[1]),
        "retreat_pct": retreat_pct,
        "retreated": retreated,
        "opening_lances": opening_lances,
    }
