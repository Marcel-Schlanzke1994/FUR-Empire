"""Versioned NPC camp catalogue and state initialization helpers."""

from __future__ import annotations

import hashlib
import importlib.resources
import json
import secrets
import time
from collections import deque
from typing import Any, cast

from . import npc_invasions
from .database import Connection

RULES_VERSION = "FUR-3-NPC-CAMPS-1"
MOVEMENT_RULES_VERSION = "FUR-3-NPC-CAMPS-2"
ATTACK_RULES_VERSION = "FUR-3-NPC-CAMPS-3"
RULESET_VERSIONS = (RULES_VERSION, MOVEMENT_RULES_VERSION, ATTACK_RULES_VERSION)
RULESET_KEY = "npc_camps_ruleset"
RULES_FILE = "fur-3-npc-camps-1.json"
MOVEMENT_RULES_FILE = "fur-3-npc-camps-2.json"
ATTACK_RULES_FILE = "fur-3-npc-camps-3.json"
RULES: dict[str, Any] = {
    "version": RULES_VERSION,
    "game": "terra",
    "kind": "world_scoped_npc_camps",
    "legacy_fur2_preserved": True,
    "status": "provisional_balance",
    "starting_resources": {"wood": 1200, "stone": 1000, "ore": 800},
    "units": ["ranger", "scout", "guardian"],
    "movement_quota_per_day": 4,
    "deployment_quota_per_day": 8,
    "autonomous_policy": {
        "actions_per_camp_per_utc_day": 1,
        "selection": "first affordable action in the profile allowlist",
        "retry_key": "world, camp and UTC day",
        "effects": "camp inventory, units and counters only",
        "attacks_or_player_loot": False,
    },
    "action_rules": {
        "resupply": {"cost": [100, 50, 50], "yield": [240, 180, 160], "quota": "none"},
        "scout": {"cost": [40, 0, 30], "yield": [1, 0, 0], "quota": "movement"},
        "reinforce": {
            "cost": [100, 80, 120],
            "yield": {"ranger": 2, "guardian": 1},
            "quota": "deployment",
        },
        "fortify": {"cost": [80, 160, 100], "yield": [1, 0, 0], "quota": "none"},
        "maneuver": {"cost": [50, 50, 100], "yield": [1, 0, 0], "quota": "movement"},
    },
    "profiles": [
        {
            "id": "ash_covenant",
            "name": "Aschebund",
            "doctrine": "logistics",
            "actions": ["resupply", "scout", "reinforce"],
            "initial_units": {"ranger": 18, "scout": 8, "guardian": 4},
        },
        {
            "id": "iron_compact",
            "name": "Eisenpakt",
            "doctrine": "fortification",
            "actions": ["fortify", "reinforce", "scout"],
            "initial_units": {"ranger": 10, "scout": 5, "guardian": 16},
        },
        {
            "id": "thorn_conclave",
            "name": "Dornenkonklave",
            "doctrine": "reconnaissance",
            "actions": ["scout", "maneuver", "resupply"],
            "initial_units": {"ranger": 12, "scout": 18, "guardian": 3},
        },
        {
            "id": "dawn_accord",
            "name": "Morgenbund",
            "doctrine": "balanced_defense",
            "actions": ["fortify", "resupply", "maneuver"],
            "initial_units": {"ranger": 14, "scout": 8, "guardian": 10},
        },
        {
            "id": "tide_syndicate",
            "name": "Gezeitenbund",
            "doctrine": "rapid_deployment",
            "actions": ["maneuver", "reinforce", "resupply"],
            "initial_units": {"ranger": 16, "scout": 12, "guardian": 5},
        },
    ],
}
RULES_DIGEST = hashlib.sha256(
    json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
_rules_path = importlib.resources.files("fur_empire").joinpath("rules", RULES_FILE)
if json.loads(_rules_path.read_text(encoding="utf-8")) != {
    **RULES,
    "design_source": "FUR-2 frontier factions; independent provisional extension",
    "unimplemented_actions": ["npc_attack", "player_loot", "autonomous_war"],
}:
    raise RuntimeError("NPC camp code catalog differs from its versioned rules file")
PROFILES: dict[str, dict[str, Any]] = {
    str(profile["id"]): cast(dict[str, Any], profile) for profile in RULES["profiles"]
}
ACTION_TYPES = frozenset(
    str(action) for profile in RULES["profiles"] for action in profile["actions"]
)
ACTION_RULES = cast(dict[str, dict[str, Any]], RULES["action_rules"])
MOVEMENT_RULES: dict[str, Any] = {
    **RULES,
    "version": MOVEMENT_RULES_VERSION,
    "kind": "world_scoped_npc_camps_with_movement",
    "autonomous_policy": {
        **RULES["autonomous_policy"],
        "selection": "rotate the profile allowlist by UTC day, then choose the first affordable legal action",
        "effects": "camp state and camp-only intelligence; player colonies and outposts are never modified",
    },
    "movement": {
        "scout_radius": 3,
        "scout_distance": "Manhattan",
        "intel_expiry_days": 7,
        "maneuver_steps_per_action": 1,
        "path": "shortest four-direction route over non-water terrain",
        "target": "nearest scouted, neutral, unowned outpost; tie-break by target ID",
        "camp_standoff_from_player_colonies": 6,
        "player_colony_standoff_from_camps": 6,
        "camp_never_occupies": [
            "water",
            "outpost sectors",
            "colony sectors",
            "active ruins",
            "protected colony radius",
            "reserved spawn sectors",
        ],
        "no_target": "action is unavailable and consumes no resources or quota",
    },
    "attack_planning": {
        "enabled": True,
        "cadence_seconds": 300,
        "world_event_budget": 1,
        "max_target_candidates": 300,
        "catchup": "no backlog; at most the current cycle is planned",
        "selection": "least recently targeted player, then least used camp; stable id tie-break",
        "knowledge": "target ownership must match camp-local owner intel observed within seven days",
        "effects": "immutable private warning plan only; no dispatch, combat, loot, or player-state mutation",
        "idempotency": "world and five-minute UTC cycle",
        "visibility": "only the player owning the targeted outpost",
        "rules_version": MOVEMENT_RULES_VERSION,
    },
}
_movement_rules_path = importlib.resources.files("fur_empire").joinpath(
    "rules", MOVEMENT_RULES_FILE
)
if json.loads(_movement_rules_path.read_text(encoding="utf-8")) != {
    **MOVEMENT_RULES,
    "design_source": "FUR-2 frontier factions; independent provisional extension",
    "unimplemented_actions": ["npc_attack", "player_loot", "autonomous_war"],
}:
    raise RuntimeError("NPC movement code catalog differs from its versioned rules file")
ATTACK_RULES: dict[str, Any] = {
    **MOVEMENT_RULES,
    "version": ATTACK_RULES_VERSION,
    "kind": "world_scoped_npc_camps_with_attacks",
    "attack_planning": {
        **MOVEMENT_RULES["attack_planning"],
        "effects": "five-minute warning; deterministic combat; garrison losses; capped resource raid; survivors return to camp",
        "warning_seconds": 300,
        "max_attacks_per_player_seconds": 86400,
        "maximum_overdue_seconds": 3600,
        "combat_rules_version": "FUR-3-TERRA-COMBAT-1",
        "combat_rules_version_policy": "use world's active FUR-3 ruleset; use COMBAT-1 in FUR-2 worlds",
        "unit_mapping": {
            "ranger": "ranger",
            "scout": "covert_courier",
            "guardian": "sentinel",
        },
        "loot_percent_per_resource": 10,
        "loot_cap_per_resource": 200,
        "camp_storage_cap_per_resource": 4000,
        "idempotency": "plan id; one resolving mission per world per worker invocation",
        "rules_version": ATTACK_RULES_VERSION,
    },
    "autonomous_policy": {
        **MOVEMENT_RULES["autonomous_policy"],
        "effects": "camp state, camp-only intelligence and combat; no outpost capture",
        "attacks_or_player_loot": True,
    },
}
_attack_rules_path = importlib.resources.files("fur_empire").joinpath("rules", ATTACK_RULES_FILE)
if json.loads(_attack_rules_path.read_text(encoding="utf-8")) != {
    **ATTACK_RULES,
    "design_source": "FUR-2 frontier factions; independent provisional extension",
    "unimplemented_actions": ["autonomous_war"],
}:
    raise RuntimeError("NPC attack code catalog differs from its versioned rules file")
RULESET_CATALOGS = {
    RULES_VERSION: RULES,
    MOVEMENT_RULES_VERSION: MOVEMENT_RULES,
    ATTACK_RULES_VERSION: ATTACK_RULES,
}
RULESET_DIGESTS = {
    version: hashlib.sha256(
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    for version, snapshot in RULESET_CATALOGS.items()
}
RULESET_SNAPSHOTS = {
    version: json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for version, snapshot in RULESET_CATALOGS.items()
}
# Early CAMPS-2 worlds pinned movement before private attack planning was added.
LEGACY_MOVEMENT_SNAPSHOT = json.dumps(
    {key: value for key, value in MOVEMENT_RULES.items() if key != "attack_planning"},
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)
LEGACY_MOVEMENT_DIGEST = hashlib.sha256(LEGACY_MOVEMENT_SNAPSHOT.encode()).hexdigest()


def stored_rules_digest(db: Connection, version: str) -> str | None:
    if version not in RULESET_VERSIONS:
        return None
    row = db.execute("SELECT digest FROM rule_catalogs WHERE version=?", (version,)).fetchone()
    return str(row["digest"]) if row else None


def enabled(world_settings: dict[str, Any]) -> bool:
    return world_settings.get(RULESET_KEY, "FUR-2") in RULESET_VERSIONS


def movement_enabled(world_settings: dict[str, Any]) -> bool:
    return bool(
        world_settings.get(RULESET_KEY, "FUR-2") in (MOVEMENT_RULES_VERSION, ATTACK_RULES_VERSION)
    )


def initialize_world(
    db: Connection,
    world_id: int,
    seed: int,
    now: int,
    version: str = RULES_VERSION,
) -> int:
    """Create five deterministic independent camps exactly once per world."""
    from .game import RuleError

    if version not in RULESET_VERSIONS:
        raise RuleError("Ungültiger NPC-Lager-Regelstand.")
    if db.execute("SELECT 1 FROM npc_camps WHERE world_id=? LIMIT 1", (world_id,)).fetchone():
        return (
            _initialize_positions(db, world_id, seed)
            if version in (MOVEMENT_RULES_VERSION, ATTACK_RULES_VERSION)
            else 0
        )
    profiles = cast(list[dict[str, Any]], RULES["profiles"])
    for position, profile in enumerate(profiles):
        camp_id = hashlib.sha256(f"{RULES_VERSION}:{seed}:{profile['id']}".encode()).hexdigest()[
            :32
        ]
        db.execute(
            "INSERT INTO npc_camps(world_id,camp_id,profile_id,position,resources,units,"
            "movement_quota,deployment_quota,quota_checked_at,created) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                world_id,
                camp_id,
                profile["id"],
                position,
                json.dumps([1200, 1000, 800], separators=(",", ":")),
                json.dumps(profile["initial_units"], sort_keys=True, separators=(",", ":")),
                int(RULES["movement_quota_per_day"]),
                int(RULES["deployment_quota_per_day"]),
                now // 86400 * 86400,
                now,
            ),
        )
    if version in (MOVEMENT_RULES_VERSION, ATTACK_RULES_VERSION):
        _initialize_positions(db, world_id, seed)
    return len(RULES["profiles"])


def _initialize_positions(db: Connection, world_id: int, seed: int) -> int:
    """Assign stable safe camp coordinates without claiming or changing map tiles."""
    from .game import RuleError

    camps = db.execute(
        "SELECT camp_id,x,y FROM npc_camps WHERE world_id=? ORDER BY position,camp_id",
        (world_id,),
    ).fetchall()
    missing = [camp for camp in camps if camp["x"] is None or camp["y"] is None]
    if not missing:
        return 0
    land = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'",
            (world_id,),
        )
    }
    occupied = {
        (int(colony["x"]), int(colony["y"]))
        for row in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,))
        for colony in [json.loads(row["state"])]
    }
    occupied.update((int(post["x"]), int(post["y"])) for post in _world_outposts(db, world_id))
    occupied.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM terra_ruins WHERE world_id=? AND expires>?",
            (world_id, int(time.time())),
        )
    )
    protected = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM terra_sector_rules WHERE world_id=? "
            "AND kind IN ('protected','spawn_reserved')",
            (world_id,),
        )
    }
    occupied.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM terra_sector_rules WHERE world_id=? "
            "AND kind IN ('protected','spawn_reserved')",
            (world_id,),
        )
    )
    occupied.update(
        (int(camp["x"]), int(camp["y"]))
        for camp in camps
        if camp["x"] is not None and camp["y"] is not None
    )
    colonies = [
        (int(colony["x"]), int(colony["y"]))
        for row in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,))
        for colony in [json.loads(row["state"])]
    ]
    positions: list[tuple[int, int]] = []
    for camp in missing:
        camp_id = str(camp["camp_id"])
        candidates = [
            point
            for point in land - occupied - protected
            if all((point[0] - x) ** 2 + (point[1] - y) ** 2 >= 36 for x, y in colonies)
            and all((point[0] - x) ** 2 + (point[1] - y) ** 2 >= 16 for x, y in positions)
        ]
        candidates.sort(
            key=lambda point: hashlib.sha256(
                f"{MOVEMENT_RULES_VERSION}:{seed}:{camp_id}:{point[0]}:{point[1]}".encode()
            ).digest()
        )
        if not candidates:
            raise RuleError("Für alle NPC-Lager gibt es keinen sicheren Landsektor.")
        x, y = candidates[0]
        db.execute(
            "UPDATE npc_camps SET x=?,y=? WHERE world_id=? AND camp_id=?",
            (x, y, world_id, camp_id),
        )
        occupied.add((x, y))
        positions.append((x, y))
    return len(positions)


def _world_outposts(db: Connection, world_id: int) -> list[dict[str, Any]]:
    return [
        cast(dict[str, Any], json.loads(row["state"]))
        for row in db.execute(
            "SELECT state FROM world_outposts WHERE world_id=? ORDER BY sort_order,target_id",
            (world_id,),
        )
    ]


def page(
    db: Connection,
    world_id: int,
    world_settings: dict[str, Any],
    now: int | None = None,
) -> list[dict[str, Any]]:
    """Return public profile and bounded readiness state for an opted-in world."""
    if not enabled(world_settings):
        return []
    return [
        {
            "id": str(row["camp_id"]),
            "profile_id": str(row["profile_id"]),
            "name": str(PROFILES[str(row["profile_id"])]["name"]),
            "doctrine": str(PROFILES[str(row["profile_id"])]["doctrine"]),
            "actions": list(PROFILES[str(row["profile_id"])]["actions"]),
            "resources": json.loads(row["resources"]),
            "units": json.loads(row["units"]),
            "movement_quota": int(row["movement_quota"]),
            "deployment_quota": int(row["deployment_quota"]),
            "fortification_level": int(row["fortification_level"]),
            "scout_actions": int(row["scout_actions"]),
            "maneuver_actions": int(row["maneuver_actions"]),
            "x": int(row["x"]) if row["x"] is not None else None,
            "y": int(row["y"]) if row["y"] is not None else None,
            "target_outpost_id": (
                str(row["target_outpost_id"]) if row["target_outpost_id"] is not None else None
            ),
            "scouted_outposts": int(row["scouted_outposts"]),
        }
        for row in db.execute(
            "SELECT camp_id,profile_id,resources,units,movement_quota,deployment_quota,"
            "fortification_level,scout_actions,maneuver_actions,x,y,target_outpost_id,"
            "(SELECT count(*) FROM npc_camp_intel i WHERE i.world_id=npc_camps.world_id "
            "AND i.camp_id=npc_camps.camp_id AND i.observed_at>=?) AS scouted_outposts "
            "FROM npc_camps WHERE world_id=? ORDER BY position,camp_id LIMIT 5",
            (
                (int(time.time()) if now is None else now)
                - int(MOVEMENT_RULES["movement"]["intel_expiry_days"]) * 86400,
                world_id,
            ),
        )
    ]


def validate_action(profile_id: str, action: str) -> bool:
    profile = PROFILES.get(profile_id)
    return profile is not None and action in profile["actions"]


def _scout_outposts(db: Connection, world_id: int, camp_id: str, x: int, y: int, now: int) -> int:
    radius = int(MOVEMENT_RULES["movement"]["scout_radius"])
    observed = 0
    for post in _world_outposts(db, world_id):
        post_x, post_y = int(post["x"]), int(post["y"])
        if abs(post_x - x) + abs(post_y - y) > radius:
            continue
        defense = post.get("defense", 0)
        if type(defense) is not int or defense < 0:
            defense = 0
        owner_id = post.get("owner")
        observed_owner_id = owner_id if isinstance(owner_id, str) and owner_id else None
        db.execute(
            "INSERT INTO npc_camp_intel(world_id,camp_id,target_id,x,y,observed_owner,tier,"
            "defense,observed_at,observed_owner_id) VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(world_id,camp_id,target_id) DO UPDATE SET x=excluded.x,y=excluded.y,"
            "observed_owner=excluded.observed_owner,tier=excluded.tier,defense=excluded.defense,"
            "observed_at=excluded.observed_at,observed_owner_id=excluded.observed_owner_id",
            (
                world_id,
                camp_id,
                str(post["id"]),
                post_x,
                post_y,
                bool(post.get("owner") is not None or post.get("alliance_owner_id") is not None),
                max(0, min(8, int(post.get("tier", 0)))),
                defense,
                now,
                observed_owner_id,
            ),
        )
        observed += 1
    return observed


def _maneuver_plan(
    db: Connection, world_id: int, camp_id: str, now: int, *, exclude_target: str | None = None
) -> dict[str, Any] | None:
    camp = db.execute(
        "SELECT x,y,target_outpost_id FROM npc_camps WHERE world_id=? AND camp_id=?",
        (world_id, camp_id),
    ).fetchone()
    if camp is None or camp["x"] is None or camp["y"] is None:
        return None
    start = int(camp["x"]), int(camp["y"])
    expiry = now - int(MOVEMENT_RULES["movement"]["intel_expiry_days"]) * 86400
    known = {
        str(row["target_id"]): (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT target_id,x,y FROM npc_camp_intel WHERE world_id=? AND camp_id=? "
            "AND observed_owner=FALSE AND observed_at>=? ORDER BY target_id LIMIT 300",
            (world_id, camp_id, expiry),
        )
    }
    if not known:
        return None
    posts = {str(post["id"]): post for post in _world_outposts(db, world_id)}
    colony_points = [
        (int(state["x"]), int(state["y"]))
        for row in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,))
        for state in [json.loads(row["state"])]
    ]
    if any((start[0] - x) ** 2 + (start[1] - y) ** 2 < 36 for x, y in colony_points):
        return None
    terrain = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'",
            (world_id,),
        )
    }
    blockers = {(int(post["x"]), int(post["y"])) for post in posts.values()}
    blockers.update(colony_points)
    blockers.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM terra_sector_rules WHERE world_id=? "
            "AND kind IN ('protected','spawn_reserved')",
            (world_id,),
        )
    )
    blockers.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM terra_ruins WHERE world_id=? AND expires>?",
            (world_id, now),
        )
    )
    blockers.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute(
            "SELECT x,y FROM npc_camps WHERE world_id=? AND camp_id<>? AND x IS NOT NULL",
            (world_id, camp_id),
        )
    )
    safe = {
        point
        for point in terrain - blockers
        if all((point[0] - x) ** 2 + (point[1] - y) ** 2 >= 36 for x, y in colony_points)
    }
    safe.add(start)
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue: deque[tuple[int, int]] = deque([start])
    while queue:
        point = queue.popleft()
        for neighbor in (
            (point[0] - 1, point[1]),
            (point[0], point[1] - 1),
            (point[0], point[1] + 1),
            (point[0] + 1, point[1]),
        ):
            if neighbor in safe and neighbor not in parents:
                parents[neighbor] = point
                queue.append(neighbor)
    goals: list[tuple[int, str, tuple[int, int]]] = []
    for target_id, (x, y) in known.items():
        post = posts.get(target_id)
        if (
            post is None
            or post.get("owner") is not None
            or post.get("alliance_owner_id") is not None
            or target_id == exclude_target
        ):
            continue
        adjacent = [
            point for point in ((x - 1, y), (x, y - 1), (x, y + 1), (x + 1, y)) if point in parents
        ]
        if adjacent:
            goal = min(adjacent, key=lambda point: (len(_path_from_parents(parents, point)), point))
            goals.append((len(_path_from_parents(parents, goal)), target_id, goal))
    if not goals:
        return None
    _, target_id, goal = min(goals, key=lambda item: (item[0], item[1]))
    path = _path_from_parents(parents, goal)
    next_point = path[1] if len(path) > 1 else start
    return {
        "target_outpost_id": target_id,
        "destination": [next_point[0], next_point[1]],
        "remaining_steps": max(0, len(path) - 2),
        "arrived": len(path) <= 2,
    }


def _path_from_parents(
    parents: dict[tuple[int, int], tuple[int, int] | None], point: tuple[int, int]
) -> list[tuple[int, int]]:
    path = [point]
    while parents[path[-1]] is not None:
        path.append(cast(tuple[int, int], parents[path[-1]]))
    path.reverse()
    return path


def perform_action(
    db: Connection,
    world_id: int,
    camp_id: str,
    action: str,
    event_id: str,
    now: int,
    world_settings: dict[str, Any],
) -> dict[str, Any]:
    """Apply one allowlisted NPC action once; caller owns the transaction."""
    from .game import RuleError

    if not enabled(world_settings):
        raise RuleError("NPC-Lager sind in dieser Welt nicht aktiviert.")
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 100:
        raise RuleError("Ungültige NPC-Ereigniskennung.")
    previous = db.execute(
        "SELECT world_id,camp_id,action,payload FROM npc_camp_events WHERE event_id=?",
        (event_id,),
    ).fetchone()
    if previous:
        if (
            int(previous["world_id"]) != world_id
            or str(previous["camp_id"]) != camp_id
            or str(previous["action"]) != action
        ):
            raise RuleError("NPC-Ereigniskennung wurde bereits anders verwendet.")
        try:
            result = json.loads(previous["payload"])
        except (TypeError, ValueError) as exc:
            raise RuleError("NPC-Ereignisprotokoll ist ungültig.") from exc
        if not isinstance(result, dict):
            raise RuleError("NPC-Ereignisprotokoll ist ungültig.")
        result = cast(dict[str, Any], result)
        result["replayed"] = True
        return result
    row = db.execute(
        "SELECT profile_id,resources,units,movement_quota,deployment_quota,fortification_level,"
        "scout_actions,maneuver_actions,quota_checked_at,x,y,target_outpost_id "
        "FROM npc_camps WHERE world_id=? AND camp_id=?",
        (world_id, camp_id),
    ).fetchone()
    if row is None:
        raise RuleError("NPC-Lager in dieser Welt nicht gefunden.")
    profile_id = str(row["profile_id"])
    if not validate_action(profile_id, action) or action not in ACTION_RULES:
        raise RuleError("Dieses Lager darf die angeforderte Aktion nicht ausführen.")
    try:
        resources = json.loads(row["resources"])
        units = json.loads(row["units"])
    except (TypeError, ValueError) as exc:
        raise RuleError("NPC-Lagerbestand ist ungültig.") from exc
    if (
        not isinstance(resources, list)
        or len(resources) != 3
        or any(type(value) is not int or value < 0 for value in resources)
        or not isinstance(units, dict)
        or any(
            key not in RULES["units"] or type(value) is not int or value < 0
            for key, value in units.items()
        )
    ):
        raise RuleError("NPC-Lagerbestand ist ungültig.")
    action_rule = ACTION_RULES[action]
    cost = cast(list[int], action_rule["cost"])
    if any(have < price for have, price in zip(resources, cost)):
        raise RuleError("NPC-Lager hat nicht genügend Vorräte für diese Aktion.")
    x = int(row["x"]) if row["x"] is not None else None
    y = int(row["y"]) if row["y"] is not None else None
    target_outpost_id = (
        str(row["target_outpost_id"]) if row["target_outpost_id"] is not None else None
    )
    movement_quota = int(row["movement_quota"])
    deployment_quota = int(row["deployment_quota"])
    fortification_level = int(row["fortification_level"])
    scout_actions = int(row["scout_actions"])
    maneuver_actions = int(row["maneuver_actions"])
    quota = str(action_rule["quota"])
    if quota == "movement" and movement_quota < 1:
        raise RuleError("Das Bewegungskontingent dieses NPC-Lagers ist erschöpft.")
    if quota == "deployment" and deployment_quota < 1:
        raise RuleError("Das Bereitstellungskontingent dieses NPC-Lagers ist erschöpft.")
    movement_enabled_here = movement_enabled(world_settings)
    if movement_enabled_here and (row["x"] is None or row["y"] is None):
        world = db.execute(
            "SELECT seed FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        if world is None:
            raise RuleError("Die NPC-Welt wurde nicht gefunden.")
        _initialize_positions(db, world_id, int(world["seed"]))
        row = db.execute(
            "SELECT profile_id,resources,units,movement_quota,deployment_quota,fortification_level,"
            "scout_actions,maneuver_actions,quota_checked_at,x,y,target_outpost_id "
            "FROM npc_camps WHERE world_id=? AND camp_id=?",
            (world_id, camp_id),
        ).fetchone()
        x = int(row["x"]) if row["x"] is not None else None
        y = int(row["y"]) if row["y"] is not None else None
        target_outpost_id = (
            str(row["target_outpost_id"]) if row["target_outpost_id"] is not None else None
        )
    movement_plan = None
    if action == "maneuver" and movement_enabled_here:
        current_target = (
            str(row["target_outpost_id"]) if row["target_outpost_id"] is not None else None
        )
        movement_plan = _maneuver_plan(db, world_id, camp_id, now)
        if (
            current_target is not None
            and movement_plan is not None
            and bool(movement_plan["arrived"])
            and str(movement_plan["target_outpost_id"]) == current_target
        ):
            movement_plan = None
        if movement_plan is None and current_target is not None:
            movement_plan = _maneuver_plan(
                db, world_id, camp_id, now, exclude_target=current_target
            )
        if movement_plan is None:
            raise RuleError("Das Lager kennt kein sicheres, erreichbares neutrales Ziel.")
    resources = [value - price for value, price in zip(resources, cost)]
    yield_value = action_rule["yield"]
    if action == "resupply":
        resources = [
            min(4000, value + int(amount)) for value, amount in zip(resources, yield_value)
        ]
    elif action == "reinforce":
        for unit, amount in cast(dict[str, int], yield_value).items():
            units[unit] = int(units.get(unit, 0)) + amount
        deployment_quota -= 1
    elif action == "scout":
        movement_quota -= 1
        scout_actions += 1
        if movement_enabled_here:
            if row["x"] is None or row["y"] is None:
                raise RuleError("Der NPC-Standort ist nicht initialisiert.")
            result_scouted = _scout_outposts(
                db, world_id, camp_id, int(row["x"]), int(row["y"]), now
            )
        else:
            result_scouted = None
    elif action == "maneuver":
        movement_quota -= 1
        maneuver_actions += 1
        if movement_enabled_here and movement_plan is not None:
            x, y = cast(list[int], movement_plan["destination"])
            target_outpost_id = str(movement_plan["target_outpost_id"])
        else:
            x = int(row["x"]) if row["x"] is not None else None
            y = int(row["y"]) if row["y"] is not None else None
            target_outpost_id = (
                str(row["target_outpost_id"]) if row["target_outpost_id"] is not None else None
            )
    elif action == "fortify":
        if fortification_level >= 10:
            raise RuleError("Die maximale Befestigungsstufe dieses NPC-Lagers ist erreicht.")
        fortification_level += int(yield_value[0])
    result = {
        "world_id": world_id,
        "camp_id": camp_id,
        "profile_id": profile_id,
        "action": action,
        "cost": cost,
        "resources": resources,
        "units": units,
        "movement_quota": movement_quota,
        "deployment_quota": deployment_quota,
        "fortification_level": fortification_level,
        "scout_actions": scout_actions,
        "maneuver_actions": maneuver_actions,
        "created": now,
        "replayed": False,
    }
    if movement_enabled_here:
        result.update(
            {
                "x": x if action == "maneuver" else int(row["x"]),
                "y": y if action == "maneuver" else int(row["y"]),
                "target_outpost_id": target_outpost_id,
            }
        )
        if action == "scout":
            result["scouted_outposts"] = result_scouted
        if action == "maneuver" and movement_plan is not None:
            result["remaining_steps"] = movement_plan["remaining_steps"]
            result["arrived"] = movement_plan["arrived"]
    db.execute(
        "UPDATE npc_camps SET resources=?,units=?,movement_quota=?,deployment_quota=?"
        ",fortification_level=?,scout_actions=?,maneuver_actions=?,x=?,y=?,target_outpost_id=? "
        "WHERE world_id=? AND camp_id=?",
        (
            json.dumps(resources, separators=(",", ":")),
            json.dumps(units, sort_keys=True, separators=(",", ":")),
            movement_quota,
            deployment_quota,
            fortification_level,
            scout_actions,
            maneuver_actions,
            x,
            y,
            target_outpost_id,
            world_id,
            camp_id,
        ),
    )
    db.execute(
        "INSERT INTO npc_camp_events(event_id,world_id,camp_id,action,payload,created) "
        "VALUES (?,?,?,?,?,?)",
        (event_id, world_id, camp_id, action, json.dumps(result, sort_keys=True), now),
    )
    return result


def reset_daily_quotas(db: Connection, now: int) -> int:
    """Restore movement/deployment quotas once for each elapsed UTC day."""
    changed = 0
    day = now // 86400
    for row in db.execute(
        "SELECT world_id,camp_id,quota_checked_at,movement_quota,deployment_quota "
        "FROM npc_camps WHERE quota_checked_at<?",
        (day * 86400,),
    ).fetchall():
        previous_day = int(row["quota_checked_at"]) // 86400
        elapsed_days = max(0, day - previous_day)
        if elapsed_days < 1:
            continue
        db.execute(
            "UPDATE npc_camps SET movement_quota=?,deployment_quota=?,quota_checked_at=? "
            "WHERE world_id=? AND camp_id=?",
            (
                int(RULES["movement_quota_per_day"]),
                int(RULES["deployment_quota_per_day"]),
                day * 86400,
                int(row["world_id"]),
                str(row["camp_id"]),
            ),
        )
        changed += 1
    return changed


def run_daily_policy(db: Connection, now: int) -> int:
    """Let each opted-in camp perform at most one affordable policy action per UTC day.

    The event ID is derived from world, camp, and UTC day, so a worker retry cannot
    perform a second action. This deliberately does not dispatch attacks, move units,
    reveal map sectors, or affect player-owned state.
    """
    day = now // 86400
    completed = 0
    for world in db.execute("SELECT world_id,settings,seed FROM world_settings").fetchall():
        try:
            settings = json.loads(world["settings"])
        except (TypeError, ValueError):
            continue
        if not isinstance(settings, dict) or not enabled(settings):
            continue
        world_id = int(world["world_id"])
        if movement_enabled(settings):
            _initialize_positions(db, world_id, int(world["seed"]))
        for camp in db.execute(
            "SELECT camp_id,profile_id,resources,units,movement_quota,deployment_quota,"
            "fortification_level,position,x,y,target_outpost_id "
            "FROM npc_camps WHERE world_id=? ORDER BY position,camp_id",
            (world_id,),
        ).fetchall():
            camp_id = str(camp["camp_id"])
            event_id = f"npc-ai:{world_id}:{camp_id}:{day}"
            prior = db.execute(
                "SELECT action FROM npc_camp_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if prior:
                perform_action(
                    db,
                    world_id,
                    camp_id,
                    str(prior["action"]),
                    event_id,
                    now,
                    settings,
                )
                continue
            profile = PROFILES.get(str(camp["profile_id"]))
            try:
                resources = json.loads(camp["resources"])
                units = json.loads(camp["units"])
            except (TypeError, ValueError):
                continue
            if (
                profile is None
                or not isinstance(resources, list)
                or len(resources) != 3
                or any(type(value) is not int or value < 0 for value in resources)
                or not isinstance(units, dict)
            ):
                continue
            actions = list(profile["actions"])
            if movement_enabled(settings):
                offset = (day + int(camp["position"])) % len(actions)
                actions = actions[offset:] + actions[:offset]
            action = None
            for candidate in actions:
                if not _policy_action_ready(candidate, camp, resources):
                    continue
                if candidate == "maneuver" and movement_enabled(settings):
                    plan = _maneuver_plan(db, world_id, camp_id, now)
                    current_target = (
                        str(camp["target_outpost_id"])
                        if camp["target_outpost_id"] is not None
                        else None
                    )
                    if (
                        plan is not None
                        and current_target is not None
                        and bool(plan["arrived"])
                        and str(plan["target_outpost_id"]) == current_target
                    ):
                        plan = None
                    if plan is None:
                        if current_target is None:
                            continue
                        plan = _maneuver_plan(
                            db, world_id, camp_id, now, exclude_target=current_target
                        )
                    if plan is None:
                        continue
                action = candidate
                break
            if action is None:
                continue
            perform_action(db, world_id, camp_id, str(action), event_id, now, settings)
            completed += 1
    return completed


def run_attack_planner(db: Connection, now: int) -> int:
    """Write at most one private, immutable NPC attack plan per world per 5m cycle.

    The later version 2 snapshot creates warning plans only. Version 3 pins a private combat
    seed and schedules an idempotent attack after its warning window.
    """
    cycle = now // 300
    planned = 0
    movement_digest = stored_rules_digest(db, MOVEMENT_RULES_VERSION)
    for world in db.execute(
        "SELECT world_id,settings,terra_combat_ruleset FROM world_settings"
    ).fetchall():
        try:
            settings = json.loads(world["settings"])
        except (TypeError, ValueError):
            continue
        if not isinstance(settings, dict) or not movement_enabled(settings):
            continue
        if (
            settings.get(RULESET_KEY) == MOVEMENT_RULES_VERSION
            and movement_digest != RULESET_DIGESTS[MOVEMENT_RULES_VERSION]
        ):
            continue
        world_id = int(world["world_id"])
        attack_enabled = settings.get(RULESET_KEY) == ATTACK_RULES_VERSION
        invasion_id = None
        if attack_enabled:
            arrival = now + int(ATTACK_RULES["attack_planning"]["warning_seconds"])
            invasion_id, may_plan = npc_invasions.planning_window(db, world_id, now, arrival)
            if not may_plan:
                continue
        if db.execute(
            "SELECT 1 FROM npc_attack_plans WHERE world_id=? AND cycle=?",
            (world_id, cycle),
        ).fetchone():
            continue
        posts = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=? "
            "ORDER BY sort_order,target_id LIMIT 300",
            (world_id,),
        ).fetchall()
        intel_by_target: dict[str, list[tuple[str, str]]] = {}
        for intel in db.execute(
            "SELECT target_id,camp_id,observed_owner_id FROM npc_camp_intel "
            "WHERE world_id=? AND observed_owner_id IS NOT NULL AND observed_at>=? "
            "ORDER BY observed_at DESC,target_id,camp_id LIMIT 1500",
            (world_id, now - int(MOVEMENT_RULES["movement"]["intel_expiry_days"]) * 86400),
        ):
            intel_by_target.setdefault(str(intel["target_id"]), []).append(
                (str(intel["camp_id"]), str(intel["observed_owner_id"]))
            )
        if not intel_by_target:
            continue
        candidates: list[dict[str, Any]] = []
        for row in posts:
            try:
                post = json.loads(row["state"])
            except (TypeError, ValueError):
                continue
            owner = post.get("owner") if isinstance(post, dict) else None
            if owner is None:
                continue
            target_id = str(row["target_id"])
            observed_by = [
                camp_id
                for camp_id, observed_owner in intel_by_target.get(target_id, [])
                if observed_owner == str(owner)
            ]
            if not observed_by:
                continue
            try:
                x, y = int(post["x"]), int(post["y"])
                if not (0 <= x <= 63 and 0 <= y <= 63):
                    continue
                candidates.append(
                    {
                        "target_id": target_id,
                        "target_owner": str(owner),
                        "target_name": str(post.get("name", "Außenposten"))[:80],
                        "target_x": x,
                        "target_y": y,
                        "observed_by": observed_by,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        if not candidates:
            continue
        active_owners = {
            str(row["user_id"])
            for row in db.execute(
                "SELECT DISTINCT user_id FROM colonies WHERE world_id=?", (world_id,)
            )
        }
        candidates = [item for item in candidates if item["target_owner"] in active_owners]
        if attack_enabled:
            warning_seconds = int(ATTACK_RULES["attack_planning"]["warning_seconds"])
            protected_owners: set[str] = set()
            for row in db.execute(
                "SELECT p.user_id,p.joined,p.banned,c.state,i.dormant_at FROM profiles p "
                "JOIN colonies c ON c.user_id=p.user_id AND c.world_id=? AND c.is_home=TRUE "
                "LEFT JOIN terra_inactivity i ON i.user_id=p.user_id",
                (world_id,),
            ):
                try:
                    vacation_until = int(json.loads(row["state"]).get("vacation_until", 0))
                except (TypeError, ValueError, AttributeError):
                    vacation_until = now + warning_seconds + 1
                if (
                    bool(row["banned"])
                    or int(row["joined"]) + 3600 > now + warning_seconds
                    or row["dormant_at"] is not None
                    or vacation_until > now + warning_seconds
                ):
                    protected_owners.add(str(row["user_id"]))
            protected_sectors = {
                (int(row["x"]), int(row["y"]))
                for row in db.execute(
                    "SELECT x,y FROM terra_sector_rules WHERE world_id=? "
                    "AND kind IN ('protected','spawn_reserved')",
                    (world_id,),
                )
            }
            candidates = [
                item
                for item in candidates
                if item["target_owner"] not in protected_owners
                and (item["target_x"], item["target_y"]) not in protected_sectors
            ]
            cooling_down = {
                str(row["target_owner"])
                for row in db.execute(
                    "SELECT DISTINCT target_owner FROM npc_attack_missions "
                    "WHERE world_id=? AND status IN ('warning','resolving','resolved') AND created>=?",
                    (
                        world_id,
                        now
                        - int(ATTACK_RULES["attack_planning"]["max_attacks_per_player_seconds"]),
                    ),
                )
            }
            candidates = [item for item in candidates if item["target_owner"] not in cooling_down]
        if not candidates:
            continue
        owner_stats = db.execute(
            "SELECT target_owner,count(*) AS hits,max(created) AS last_hit "
            "FROM npc_attack_plans WHERE world_id=? AND created>=? GROUP BY target_owner",
            (world_id, now - 7 * 86400),
        ).fetchall()
        owner_rank = {
            str(row["target_owner"]): (int(row["hits"]), int(row["last_hit"] or 0))
            for row in owner_stats
        }
        candidates.sort(
            key=lambda item: (
                (
                    owner_rank.get(item["target_owner"], (0, 0))[1],
                    owner_rank.get(item["target_owner"], (0, 0))[0],
                ),
                item["target_id"],
            )
        )
        target = candidates[0]
        eligible_camp_ids = set(target["observed_by"])
        busy_camps = (
            {
                str(row["camp_id"])
                for row in db.execute(
                    "SELECT camp_id FROM npc_attack_missions WHERE world_id=? AND status IN "
                    "('warning','resolving')",
                    (world_id,),
                )
            }
            if attack_enabled
            else set()
        )
        camps = [
            row
            for row in db.execute(
                "SELECT camp_id,units FROM npc_camps WHERE world_id=? ORDER BY camp_id",
                (world_id,),
            )
            if str(row["camp_id"]) in eligible_camp_ids and str(row["camp_id"]) not in busy_camps
        ]
        if not camps:
            continue
        camp_stats = db.execute(
            "SELECT camp_id,count(*) AS hits,max(created) AS last_hit "
            "FROM npc_attack_plans WHERE world_id=? AND created>=? GROUP BY camp_id",
            (world_id, now - 7 * 86400),
        ).fetchall()
        camp_rank = {
            str(row["camp_id"]): (int(row["hits"]), int(row["last_hit"] or 0)) for row in camp_stats
        }
        camp = min(
            camps,
            key=lambda row: (
                camp_rank.get(str(row["camp_id"]), (0, 0)),
                str(row["camp_id"]),
            ),
        )
        try:
            units = json.loads(camp["units"])
        except (TypeError, ValueError):
            continue
        if not isinstance(units, dict) or any(
            not isinstance(unit, str) or type(count) is not int or count < 0
            for unit, count in units.items()
        ):
            continue
        plan_rules_version = ATTACK_RULES_VERSION if attack_enabled else MOVEMENT_RULES_VERSION
        digest = RULESET_DIGESTS[plan_rules_version]
        plan_id = hashlib.sha256(f"npc-plan:{world_id}:{cycle}".encode()).hexdigest()
        inserted = db.execute(
            "INSERT INTO npc_attack_plans"
            "(id,world_id,cycle,camp_id,target_id,target_owner,target_name,target_x,target_y,"
            "units,rules_version,rules_digest,created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(world_id,cycle) DO NOTHING RETURNING id",
            (
                plan_id,
                world_id,
                cycle,
                str(camp["camp_id"]),
                target["target_id"],
                target["target_owner"],
                target["target_name"],
                target["target_x"],
                target["target_y"],
                json.dumps(units, sort_keys=True),
                plan_rules_version,
                digest,
                now,
            ),
        ).fetchone()
        planned += int(inserted is not None)
        if inserted is not None and attack_enabled:
            from . import terra_combat

            mapping = cast(dict[str, str], ATTACK_RULES["attack_planning"]["unit_mapping"])
            combat_units = {
                mapping[unit]: amount
                for unit, amount in units.items()
                if unit in mapping and amount > 0
            }
            if not combat_units:
                raise ValueError("NPC attack plan has no compatible combat units")
            seed = secrets.token_hex(32)
            configured_combat = str(world["terra_combat_ruleset"])
            combat_version = (
                configured_combat
                if terra_combat.is_supported_version(configured_combat)
                else str(ATTACK_RULES["attack_planning"]["combat_rules_version"])
            )
            db.execute(
                "INSERT INTO npc_attack_missions"
                "(id,world_id,plan_id,camp_id,target_owner,arrival,status,attacker_units,seed,"
                "seed_commitment,combat_version,combat_digest,created) "
                "VALUES (?,?,?,?,?,?,'warning',?,?,?,?,?,?)",
                (
                    plan_id,
                    world_id,
                    plan_id,
                    str(camp["camp_id"]),
                    str(target["target_owner"]),
                    now + int(ATTACK_RULES["attack_planning"]["warning_seconds"]),
                    json.dumps(combat_units, sort_keys=True, separators=(",", ":")),
                    seed,
                    hashlib.sha256(bytes.fromhex(seed)).hexdigest(),
                    combat_version,
                    terra_combat.RULESET_DIGESTS[combat_version],
                    now,
                ),
            )
            if invasion_id is not None:
                db.execute(
                    "INSERT INTO npc_invasion_attacks(mission_id,invasion_id) VALUES (?,?)",
                    (plan_id, invasion_id),
                )
    return planned


def attack_plan_page(db: Connection, world_id: int, owner_id: str) -> list[dict[str, Any]]:
    """Return only the current player's own plans; never expose other targets."""
    return [
        dict(row)
        for row in db.execute(
            "SELECT p.id,p.camp_id,p.target_id,p.target_name,p.target_x,p.target_y,p.units,p.created,"
            "m.arrival AS attack_arrival,m.status AS attack_status,m.outcome AS attack_outcome "
            "FROM npc_attack_plans p LEFT JOIN npc_attack_missions m ON m.plan_id=p.id "
            "WHERE p.world_id=? AND p.target_owner=? ORDER BY p.created DESC,p.id DESC LIMIT 20",
            (world_id, owner_id),
        )
    ]


def _cancel_npc_attack(db: Connection, mission_id: str, reason: str, now: int) -> None:
    db.execute(
        "UPDATE npc_attack_missions SET status='cancelled',resolved=?,cancel_reason=? "
        "WHERE id=? AND status='resolving'",
        (now, reason, mission_id),
    )


def resolve_due_attacks(db: Connection, game: Any, now: int) -> int:
    """Resolve no more than one due NPC attack per world in this worker pass."""
    from . import terra_combat

    resolved_count = 0
    worlds = db.execute("SELECT world_id,settings FROM world_settings ORDER BY world_id").fetchall()
    for world in worlds:
        world_id = int(world["world_id"])
        try:
            settings = json.loads(world["settings"])
        except (TypeError, ValueError):
            settings = {}
        if not isinstance(settings, dict) or settings.get(RULESET_KEY) != ATTACK_RULES_VERSION:
            db.execute(
                "UPDATE npc_attack_missions SET status='cancelled',resolved=?,"
                "cancel_reason='rules_disabled' WHERE world_id=? AND status='warning'",
                (now, world_id),
            )
            continue
        mission = db.execute(
            "SELECT m.*,p.target_id FROM npc_attack_missions m "
            "JOIN npc_attack_plans p ON p.id=m.plan_id "
            "WHERE m.world_id=? AND m.status='warning' "
            "AND m.arrival<=? ORDER BY m.arrival,m.id LIMIT 1",
            (world_id, now),
        ).fetchone()
        if mission is None:
            continue
        claimed = db.execute(
            "UPDATE npc_attack_missions SET status='resolving' WHERE id=? AND status='warning' "
            "RETURNING id",
            (mission["id"],),
        ).fetchone()
        if claimed is None:
            continue

        mission_id = str(mission["id"])

        arrival = int(mission["arrival"])
        if now - arrival > int(ATTACK_RULES["attack_planning"]["maximum_overdue_seconds"]):
            _cancel_npc_attack(db, mission_id, "too_late", now)
            resolved_count += 1
            continue
        post_row = db.execute(
            "SELECT state FROM world_outposts WHERE world_id=? AND target_id=?",
            (world_id, mission["target_id"]),
        ).fetchone()
        camp = db.execute(
            "SELECT profile_id,units,resources FROM npc_camps WHERE world_id=? AND camp_id=?",
            (world_id, mission["camp_id"]),
        ).fetchone()
        owner = db.execute(
            "SELECT colony_id FROM colonies WHERE world_id=? AND user_id=? "
            "ORDER BY is_home DESC,colony_id LIMIT 1",
            (world_id, mission["target_owner"]),
        ).fetchone()
        if post_row is None or camp is None or owner is None:
            _cancel_npc_attack(db, mission_id, "target_or_owner_missing", now)
            resolved_count += 1
            continue
        profile = db.execute(
            "SELECT joined,banned FROM profiles WHERE user_id=?",
            (mission["target_owner"],),
        ).fetchone()
        defender_state = game.read_colony(db, str(owner["colony_id"]))
        dormant = db.execute(
            "SELECT 1 FROM terra_inactivity WHERE user_id=? AND dormant_at IS NOT NULL",
            (mission["target_owner"],),
        ).fetchone()
        if (
            profile is None
            or bool(profile["banned"])
            or arrival < int(profile["joined"]) + 3600
            or dormant is not None
            or int(defender_state.get("vacation_until", 0)) > arrival
        ):
            _cancel_npc_attack(db, mission_id, "defender_protected", now)
            resolved_count += 1
            continue
        try:
            target = json.loads(post_row["state"])
            camp_units = json.loads(camp["units"])
            camp_resources = json.loads(camp["resources"])
            attacker_units = json.loads(mission["attacker_units"])
        except (TypeError, ValueError):
            _cancel_npc_attack(db, mission_id, "snapshot_invalid", now)
            resolved_count += 1
            continue
        if (
            not isinstance(target, dict)
            or str(target.get("owner")) != str(mission["target_owner"])
            or not isinstance(camp_units, dict)
            or not isinstance(camp_resources, list)
            or len(camp_resources) != 3
            or not isinstance(attacker_units, dict)
            or not isinstance(target.get("units", {}), dict)
        ):
            _cancel_npc_attack(db, mission_id, "target_changed", now)
            resolved_count += 1
            continue
        combat_version = str(mission["combat_version"])
        try:
            combat_rules = terra_combat.rules_for(combat_version)
            seed_commitment = hashlib.sha256(bytes.fromhex(str(mission["seed"]))).hexdigest()
        except (KeyError, TypeError, ValueError):
            _cancel_npc_attack(db, mission_id, "combat_snapshot_invalid", now)
            resolved_count += 1
            continue
        if (
            str(mission["combat_digest"]) != terra_combat.RULESET_DIGESTS[combat_version]
            or seed_commitment != str(mission["seed_commitment"])
            or not attacker_units
            or any(type(value) is not int or value < 0 for value in attacker_units.values())
            or any(
                type(value) is not int or value < 0 for value in target.get("units", {}).values()
            )
            or set(attacker_units) - set(combat_rules["units"])
            or set(target.get("units", {})) - set(combat_rules["units"])
        ):
            _cancel_npc_attack(db, mission_id, "combat_snapshot_invalid", now)
            resolved_count += 1
            continue
        try:
            from .terrain import DEFENSE_PERCENT, terrain_at

            terrain = terrain_at(db, int(target["x"]), int(target["y"]), world_id)
            result = terra_combat.resolve(
                str(mission["seed"]),
                attacker_units,
                dict(target.get("units", {})),
                defender_modifiers={"terrain": int(DEFENSE_PERCENT[terrain])},
                rules_version=combat_version,
            )
        except (TypeError, ValueError):
            _cancel_npc_attack(db, mission_id, "combat_snapshot_invalid", now)
            resolved_count += 1
            continue
        victory = result["outcome"] == "attacker_win"
        mapping = cast(dict[str, str], ATTACK_RULES["attack_planning"]["unit_mapping"])
        inverse_mapping = {combat_unit: camp_unit for camp_unit, combat_unit in mapping.items()}
        survivors = dict(camp_units)
        for combat_unit, camp_unit in inverse_mapping.items():
            lost = int(result["attacker_losses"].get(combat_unit, 0))
            survivors[camp_unit] = max(0, int(camp_units.get(camp_unit, 0)) - lost)
        camp_resources = [int(value) for value in camp_resources]
        loot = [0, 0, 0]
        if victory:
            stock = target.get("stock", [0, 0, 0])
            if (
                not isinstance(stock, list)
                or len(stock) != 3
                or any(type(value) is not int or value < 0 for value in stock)
            ):
                _cancel_npc_attack(db, mission_id, "target_stock_invalid", now)
                resolved_count += 1
                continue
            for index, amount in enumerate(stock):
                loot[index] = min(
                    amount
                    * int(ATTACK_RULES["attack_planning"]["loot_percent_per_resource"])
                    // 100,
                    int(ATTACK_RULES["attack_planning"]["loot_cap_per_resource"]),
                    max(
                        0,
                        int(ATTACK_RULES["attack_planning"]["camp_storage_cap_per_resource"])
                        - camp_resources[index],
                    ),
                )
                camp_resources[index] += loot[index]
                stock[index] -= loot[index]
            target["stock"] = stock
        target["units"] = dict(result["defender_survivors"])
        combat = {
            **result,
            "participants": {
                "attacker": str(PROFILES.get(str(camp["profile_id"]), {}).get("name", "NPC-Lager")),
                "defender": str(target.get("name", "Außenposten")),
            },
            "loot": loot,
            "mission_id": str(mission["id"]),
            "attack_rules_version": ATTACK_RULES_VERSION,
            "attack_rules_digest": RULESET_DIGESTS[ATTACK_RULES_VERSION],
        }
        posts = game.world_outposts(db, world_id)
        for item in posts:
            if str(item.get("id")) == str(mission["target_id"]):
                item.update(target)
                break
        game.save_world_outposts(db, world_id, posts)
        db.execute(
            "UPDATE npc_camps SET units=?,resources=? WHERE world_id=? AND camp_id=?",
            (
                json.dumps(survivors, sort_keys=True, separators=(",", ":")),
                json.dumps(camp_resources, separators=(",", ":")),
                world_id,
                mission["camp_id"],
            ),
        )
        defender = defender_state
        title = "NPC-Angriff abgewehrt" if not victory else "NPC-Überfall auf Außenposten"
        game.report(
            defender,
            title,
            f"Ein NPC-Lager griff {target.get('name', 'deinen Außenposten')} an. "
            f"Ergebnis: {'Angreifer siegt' if victory else 'Verteidigung hält'}. "
            f"Verlorene Vorräte: {sum(loot)}.",
            combat,
            report_side="defender",
        )
        defender["reports"][0]["time"] = arrival
        game.save(db, defender)
        db.execute(
            "UPDATE npc_attack_missions SET status='resolved',resolved=?,outcome=?,replay=?,loot=? "
            "WHERE id=? AND status='resolving'",
            (
                now,
                str(result["outcome"]),
                json.dumps(combat, sort_keys=True, separators=(",", ":")),
                json.dumps(loot, separators=(",", ":")),
                mission["id"],
            ),
        )
        resolved_count += 1
    return resolved_count


def _policy_action_ready(action: str, camp: Any, resources: list[int]) -> bool:
    rule = ACTION_RULES[action]
    cost = cast(list[int], rule["cost"])
    if any(have < price for have, price in zip(resources, cost)):
        return False
    quota = str(rule["quota"])
    if quota == "movement" and int(camp["movement_quota"]) < 1:
        return False
    if quota == "deployment" and int(camp["deployment_quota"]) < 1:
        return False
    if action == "fortify" and int(camp["fortification_level"]) >= 10:
        return False
    if action == "resupply":
        yield_values = cast(list[int], rule["yield"])
        if all(
            min(4000, have - price + amount) == have
            for have, price, amount in zip(resources, cost, yield_values)
        ):
            return False
    return True
