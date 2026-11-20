"""World-scoped cooperative Terra boss raid with finite resource rewards."""

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-terra-boss-1.json").read_text(encoding="utf-8")
)
VERSION = str(RULES["version"])
SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
DIGEST = hashlib.sha256(SNAPSHOT.encode()).hexdigest()


class BossRaidError(ValueError):
    """A raid action is unavailable to this player."""


def _raid(db: Connection, world_id: int, raid_id: str) -> dict[str, Any]:
    row = db.execute(
        "SELECT * FROM terra_boss_raids WHERE id=? AND world_id=?", (raid_id, world_id)
    ).fetchone()
    if row is None:
        raise BossRaidError("Dieser Weltboss ist in deiner aktiven Welt nicht verfügbar.")
    if row["rules_version"] != VERSION or row["rules_digest"] != DIGEST:
        raise RuntimeError("Unsupported Terra boss raid rule snapshot")
    return dict(row)


def _phase(remaining: int, health: int) -> str:
    return (
        "phase_two"
        if 100 * remaining <= health * int(RULES["phase_two_health_percent"])
        else "phase_one"
    )


def schedule(db: Connection, world_id: int, raid_id: str, name: str, now: int) -> None:
    if db.execute(
        "SELECT 1 FROM terra_boss_raids WHERE world_id=? AND ends>? LIMIT 1", (world_id, now)
    ).fetchone():
        raise BossRaidError("In dieser Welt läuft bereits ein Boss-Zeitfenster.")
    starts = now + int(RULES["warning_seconds"])
    ends = starts + int(RULES["active_seconds"])
    health = int(RULES["health"])
    db.execute(
        "INSERT INTO terra_boss_raids "
        "(id,world_id,name,rules_version,rules_digest,health,remaining_health,starts,ends) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (raid_id, world_id, name, VERSION, DIGEST, health, health, starts, ends),
    )


def join(
    db: Connection,
    world_id: int,
    raid_id: str,
    user: str,
    mission_id: str,
    rangers: int,
    now: int,
) -> dict[str, Any]:
    raid = _raid(db, world_id, raid_id)
    due = now + int(RULES["attack_seconds"])
    if not raid["starts"] <= now or due >= raid["ends"] or raid["defeated_at"] is not None:
        raise BossRaidError("Der Angriff kann nicht im aktiven Boss-Zeitfenster ankommen.")
    if db.execute(
        "SELECT 1 FROM terra_boss_contributions WHERE raid_id=? AND user_id=?", (raid_id, user)
    ).fetchone():
        raise BossRaidError("Du hast deinen Angriff für diesen Weltboss bereits gebucht.")
    booked = db.execute(
        "SELECT COUNT(*) AS booked FROM terra_boss_contributions WHERE raid_id=?", (raid_id,)
    ).fetchone()["booked"]
    if booked >= int(RULES["attack_slots"]):
        raise BossRaidError("Alle Angriffsplätze sind belegt.")
    db.execute(
        "INSERT INTO terra_boss_contributions (raid_id,user_id,mission_id,rangers,due) "
        "VALUES (?,?,?,?,?)",
        (raid_id, user, mission_id, rangers, due),
    )
    return {
        "id": mission_id,
        "kind": "terra_boss_attack",
        "key": raid_id,
        "label": f"Weltboss: {raid['name']}",
        "due": due,
    }


def resolve(
    db: Connection, world_id: int, raid_id: str, user: str, mission_id: str, due: int
) -> tuple[int, int]:
    raid = _raid(db, world_id, raid_id)
    row = db.execute(
        "SELECT rangers,due,damage FROM terra_boss_contributions "
        "WHERE raid_id=? AND user_id=? AND mission_id=?",
        (raid_id, user, mission_id),
    ).fetchone()
    if row is None or row["damage"] is not None or row["due"] != due:
        raise RuntimeError("Invalid Terra boss attack record")
    rangers = int(row["rangers"])
    damage = 0
    survivors = rangers
    if raid["starts"] <= due < raid["ends"] and raid["remaining_health"] > 0:
        phase = _phase(raid["remaining_health"], raid["health"])
        damage = min(
            raid["remaining_health"],
            rangers * int(RULES[f"{phase}_damage_per_ranger"]),
            int(RULES["max_damage_per_attack"]),
        )
        survivors -= (rangers * int(RULES[f"{phase}_loss_percent"]) + 99) // 100
        remaining = raid["remaining_health"] - damage
        db.execute(
            "UPDATE terra_boss_raids SET remaining_health=?,defeated_at=? WHERE id=?",
            (remaining, due if remaining == 0 else None, raid_id),
        )
    db.execute(
        "UPDATE terra_boss_contributions SET damage=?,survivors=? "
        "WHERE raid_id=? AND user_id=? AND damage IS NULL",
        (damage, survivors, raid_id, user),
    )
    return damage, survivors


def _reward(damage: int, health: int) -> int:
    return int(RULES["reward_ore_pool"]) * damage // health


def claim(db: Connection, world_id: int, raid_id: str, user: str, now: int) -> int:
    raid = _raid(db, world_id, raid_id)
    if raid["defeated_at"] is None:
        raise BossRaidError("Die Belohnung wird nach dem gemeinsamen Sieg verfügbar.")
    row = db.execute(
        "UPDATE terra_boss_contributions SET claimed_at=? "
        "WHERE raid_id=? AND user_id=? AND damage>0 AND claimed_at IS NULL RETURNING damage",
        (now, raid_id, user),
    ).fetchone()
    if row is None:
        raise BossRaidError("Für diesen Weltboss ist keine Belohnung offen.")
    return _reward(row["damage"], raid["health"])


def view(db: Connection, world_id: int, user: str, now: int) -> dict[str, Any]:
    active = db.execute(
        "SELECT r.id,r.name,r.health,r.remaining_health,r.starts,r.ends,r.defeated_at,"
        "c.damage,c.mission_id,"
        "(SELECT COUNT(*) FROM terra_boss_contributions p WHERE p.raid_id=r.id) AS booked "
        "FROM terra_boss_raids r LEFT JOIN terra_boss_contributions c "
        "ON c.raid_id=r.id AND c.user_id=? "
        "WHERE r.world_id=? AND r.ends>? ORDER BY r.starts DESC,r.id LIMIT 1",
        (user, world_id, now),
    ).fetchone()
    raid = dict(active) if active else None
    if raid:
        raid["joined"] = raid.pop("mission_id") is not None
        raid["phase"] = (
            0
            if raid["defeated_at"] is not None or now < raid["starts"]
            else 2 if _phase(raid["remaining_health"], raid["health"]) == "phase_two" else 1
        )
        raid["can_join"] = (
            not raid["joined"]
            and raid["defeated_at"] is None
            and raid["starts"] <= now
            and now + int(RULES["attack_seconds"]) < raid["ends"]
            and raid["booked"] < int(RULES["attack_slots"])
        )
    rewards = [
        {"id": row["id"], "name": row["name"], "ore": _reward(row["damage"], row["health"])}
        for row in db.execute(
            "SELECT r.id,r.name,r.health,c.damage FROM terra_boss_contributions c "
            "JOIN terra_boss_raids r ON r.id=c.raid_id "
            "WHERE r.world_id=? AND c.user_id=? AND c.claimed_at IS NULL "
            "AND c.damage>0 AND r.defeated_at IS NOT NULL ORDER BY r.defeated_at DESC,r.id LIMIT 20",
            (world_id, user),
        )
    ]
    return {
        "raid": raid,
        "rewards": rewards,
        "attack_slots": RULES["attack_slots"],
        "max_rangers": RULES["max_rangers_per_attack"],
        "reward_ore_pool": RULES["reward_ore_pool"],
        "rules_version": VERSION,
    }
