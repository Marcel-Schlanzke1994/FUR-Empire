"""Server authoritative game rules; all commands execute in one transaction."""

import hashlib
import json
import math
import random
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from . import (
    alliance_projects,
    alliance_season,
    alliance_treasury,
    alliance_war,
    boss_raids,
    cosmetic_rewards,
    crafting,
    expeditions,
    game_events,
    hero_doctrines,
    hero_respec,
    heroes,
    item_drops,
    live_events,
    npc_camps,
    npc_convoys,
    npc_invasions,
    orbit_attack,
    orbit_battle,
    orbit_economy,
    orbit_expedition,
    orbit_intel,
    orbit_jumpgate,
    orbit_rules,
    orbit_station,
    orbit_transport,
    prestige,
    ranking_categories,
    recurring_quests,
    recycling,
    ruin_exploration,
    rule_rollouts,
    terra_alliance,
    terra_combat,
    terra_garrison,
    terra_intelligence,
    terra_recovery,
)
from .colony_management import home_status
from .contracts import CommandOrigin
from .database import Connection, migrate
from .fog import record_observations, sector_is_known, sector_status
from .items import claim_reserve as claim_item_reserve
from .items import view as generic_item_view
from .neutral_market import claim_reserve, exchange, market_view
from .registry import load_colony_conversion_rules, load_rules
from .systems import Systems
from .terrain import (
    DEFENSE_PERCENT,
    PRODUCTION_PERCENT,
    TERRAIN_RULES,
    defense_with_terrain,
    seed_world,
    terrain_at,
    travel_cost,
    travel_seconds,
    travel_times,
)
from .territory import (
    MAX_REGION_PRODUCTION_BONUS,
    REGION_PRODUCTION_BONUS,
    summarize_regions,
)

REGISTRY = load_rules()
RULES_SNAPSHOT = json.dumps(REGISTRY, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
COLONY_RELOCATION_COST = (2000, 1500, 1000)
COLONY_RELOCATION_COOLDOWN = 7 * 86400
TERRA_RUIN_SECONDS = 86400
FUSION_SUPPLY_SECONDS = 86400
FUSION_SUPPLY_ORE_PER_LEVEL = 120
FACTION_RESEARCH = {
    "adaptive_forestry": ("pioneers", (500, 350, 300)),
    "long_range_colony": ("pioneers", (850, 650, 600)),
    "rapid_construction": ("pioneers", (700, 550, 450)),
    "kinetic_shield": ("wardens", (300, 500, 350)),
    "mobile_fortress": ("wardens", (650, 900, 700)),
    "bastion_protocol": ("wardens", (450, 750, 550)),
    "market_cipher": ("syndicate", (550, 450, 700)),
    "efficient_salvage": ("syndicate", (650, 550, 850)),
    "smuggler_navigation": ("syndicate", (350, 300, 500)),
}
FACTION_RESEARCH_SECONDS = 180
FACTION_RESEARCH_HQ = 4
PIONEER_SURVEY_RANGE = 12
PIONEER_SURVEY_SECONDS = 3600
PIONEER_SURVEY_COOLDOWN = 86400
PIONEER_SETTLEMENT_DISCOUNT = 8
TERRA_INACTIVITY_SECONDS = 30 * 86400
TERRA_INACTIVITY_NOTICE = 7 * 86400
BUILDINGS = REGISTRY["buildings"]
TECH = REGISTRY["tech"]
FACTION_UNITS = {
    "terraformer_drone": (
        "pioneers",
        "adaptive_forestry",
        "Terraformer-Drohne",
        38,
        3,
        26,
        [105, 60, 90],
    ),
    "frontier_vanguard": (
        "pioneers",
        "adaptive_forestry",
        "Grenzvorhut",
        76,
        4,
        44,
        [165, 100, 145],
    ),
    "bastion_walker": ("wardens", "kinetic_shield", "Bastionsläufer", 82, 4, 48, [125, 200, 155]),
    "shield_sentinel": ("wardens", "kinetic_shield", "Schildwache", 43, 3, 28, [75, 125, 100]),
    "covert_courier": (
        "syndicate",
        "smuggler_navigation",
        "Kuriereinheit",
        36,
        3,
        24,
        [80, 65, 105],
    ),
    "salvage_engineer": (
        "syndicate",
        "smuggler_navigation",
        "Bergungstrupp",
        72,
        4,
        40,
        [130, 105, 175],
    ),
}
UNITS = {
    **REGISTRY["units"],
    **{
        key: {
            "name": name,
            "power": power,
            "require": barracks,
            "time": duration,
            "cost": cost,
            "requirements": {"buildings": {"barracks": barracks}, "tech": {}},
        }
        for key, (_, _, name, power, barracks, duration, cost) in FACTION_UNITS.items()
    },
}
COLONY_CONVERSION_RULES = load_colony_conversion_rules()

RESOURCES = ["wood", "stone", "ore"]
COLONY_MIN_DISTANCE = 6
NPC_FACTIONS = (
    ("ash_covenant", "Aschebund"),
    ("iron_compact", "Eisenpakt"),
    ("thorn_conclave", "Dornenkonklave"),
)


class RuleError(ValueError):
    pass


def required_payload_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise RuleError(f"Ungültiger Textwert für {key}.")
    return value


def required_payload_int(
    payload: dict[str, Any],
    key: str,
    *,
    minimum: int = 1,
    maximum: int = 100,
    default: int | None = None,
) -> int:
    value = payload.get(key, default)
    if type(value) is not int or not minimum <= value <= maximum:
        raise RuleError(f"Ungültiger Zahlenwert für {key}.")
    return value


def required_orbit_coordinates(payload: dict[str, Any]) -> tuple[int, int, int]:
    galaxy, system, slot = (payload.get(key) for key in ("galaxy", "system", "slot"))
    if type(galaxy) is not int or type(system) is not int or type(slot) is not int:
        raise RuleError("Ungültige Orbit-Koordinaten.")
    return galaxy, system, slot


class JobProcessingError(RuntimeError):
    def __init__(self, user: str, job: str):
        self.user, self.job = user, job
        super().__init__("Ein Weltauftrag benötigt Wiederholung.")


def identity() -> str:
    return str(uuid4())


def resolve_outpost_battle(
    army: dict[str, int], defenders: dict[str, int], tier: int, tactics: int, terrain: str
) -> dict[str, Any]:
    """Pure FUR-2 neutral-outpost projection shared by simulation and resolution."""
    power = sum(UNITS[k]["power"] * n for k, n in army.items()) * (100 + 15 * tactics) // 100
    defense = defense_with_terrain(
        55 * tier**2 + sum(UNITS[k]["power"] * n for k, n in defenders.items()), terrain
    )
    victory = power > defense
    attacker_loss_percent = min(100, 10 + defense * 60 // max(1, power)) if victory else 100
    attacker_survivors = {
        k: max(0, n - (n * attacker_loss_percent + 99) // 100) for k, n in army.items()
    }
    defender_loss_percent = 100 if victory else min(100, power * 70 // max(1, defense))
    defender_survivors = {
        k: max(0, n - (n * defender_loss_percent + 99) // 100) for k, n in defenders.items()
    }
    return {
        "power": power,
        "defense": defense,
        "victory": victory,
        "attacker_survivors": attacker_survivors,
        "attacker_losses": sum(army.values()) - sum(attacker_survivors.values()),
        "defender_survivors": defender_survivors,
    }


def resolve_player_battle(
    army: dict[str, int],
    defenders: dict[str, int],
    defense: int,
    tactics: int,
    logistics: int,
    resources: list[int] | None = None,
) -> dict[str, Any]:
    """Resolve the deterministic FUR-2 player attrition rule for live and preview battles."""
    power = sum(UNITS[k]["power"] * n for k, n in army.items()) * (100 + 15 * tactics) // 100
    victory = power > defense
    attacker_loss_percent = min(100, 10 + defense * 60 // max(1, power)) if victory else 100
    defender_loss_percent = 100 if victory else min(100, power * 70 // max(1, defense))
    attacker_survivors = {
        k: max(0, n - (n * attacker_loss_percent + 99) // 100) for k, n in army.items()
    }
    defender_survivors = {
        k: max(0, n - (n * defender_loss_percent + 99) // 100) for k, n in defenders.items()
    }
    loot = None
    if resources is not None:
        capacity = sum(attacker_survivors.values()) * (40 + 10 * logistics)
        loot = [min(n // 3, capacity // 3) if victory else 0 for n in resources]
    return {
        "power": power,
        "defense": defense,
        "victory": victory,
        "attacker_survivors": attacker_survivors,
        "attacker_losses": sum(army.values()) - sum(attacker_survivors.values()),
        "defender_survivors": defender_survivors,
        "defender_losses": sum(defenders.values()) - sum(defender_survivors.values()),
        "loot": loot,
    }


class Game:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.settings: Any | None = None
        self.systems = Systems(self)
        self._region_cache: dict[
            int,
            tuple[
                tuple[tuple[tuple[int, int, str | None], ...], tuple[tuple[str, str], ...]],
                list[dict[str, Any]],
            ],
        ] = {}
        with self.connect() as db:
            migrate(db)
        with self.transaction() as db:
            for version, snapshot, digest in (
                (REGISTRY["version"], RULES_SNAPSHOT, RULES_DIGEST),
                (orbit_rules.VERSION, orbit_rules.SNAPSHOT, orbit_rules.DIGEST),
                *[
                    (
                        version,
                        terra_alliance.SNAPSHOTS[version],
                        terra_alliance.DIGESTS[version],
                    )
                    for version in terra_alliance.RULESETS
                ],
                *[
                    (
                        version,
                        terra_combat.RULESET_SNAPSHOTS[version],
                        terra_combat.RULESET_DIGESTS[version],
                    )
                    for version in terra_combat.RULESETS
                ],
                (terra_garrison.VERSION, terra_garrison.SNAPSHOT, terra_garrison.DIGEST),
                (
                    terra_intelligence.VERSION,
                    terra_intelligence.SNAPSHOT,
                    terra_intelligence.DIGEST,
                ),
                (
                    ruin_exploration.VERSION,
                    ruin_exploration.SNAPSHOT,
                    ruin_exploration.DIGEST,
                ),
                (boss_raids.VERSION, boss_raids.SNAPSHOT, boss_raids.DIGEST),
                (npc_invasions.VERSION, npc_invasions.SNAPSHOT, npc_invasions.DIGEST),
                (recurring_quests.VERSION, recurring_quests.SNAPSHOT, recurring_quests.DIGEST),
                (npc_convoys.VERSION, npc_convoys.SNAPSHOT, npc_convoys.DIGEST),
                (terra_recovery.VERSION, terra_recovery.SNAPSHOT, terra_recovery.DIGEST),
                *[
                    (
                        version,
                        npc_camps.RULESET_SNAPSHOTS[version],
                        npc_camps.RULESET_DIGESTS[version],
                    )
                    for version in npc_camps.RULESET_VERSIONS
                ],
            ):
                db.execute(
                    "INSERT INTO rule_catalogs(version,snapshot,digest) VALUES (?,?,?) "
                    "ON CONFLICT(version) DO NOTHING",
                    (version, snapshot, digest),
                )
                catalog = db.execute(
                    "SELECT snapshot,digest FROM rule_catalogs WHERE version=?", (version,)
                ).fetchone()
                if catalog["snapshot"] != snapshot or catalog["digest"] != digest:
                    if (
                        version == npc_camps.MOVEMENT_RULES_VERSION
                        and catalog["snapshot"] == npc_camps.LEGACY_MOVEMENT_SNAPSHOT
                        and catalog["digest"] == npc_camps.LEGACY_MOVEMENT_DIGEST
                    ):
                        continue
                    raise RuleError(
                        "Der geladene Regelkatalog weicht von seiner gespeicherten Version ab."
                    )
            db.execute(
                "INSERT INTO season_rules(season_id,version,snapshot,digest,source) "
                "SELECT id,?,?,?,'legacy_backfill' FROM seasons "
                "WHERE id NOT IN (SELECT season_id FROM season_rules) "
                "ON CONFLICT(season_id) DO NOTHING",
                (REGISTRY["version"], RULES_SNAPSHOT, RULES_DIGEST),
            )
            if db.execute("SELECT 1 FROM world").fetchone() is None:
                towns = []
                for i, (x, y) in enumerate(
                    [(3, 3), (9, 2), (14, 5), (4, 10), (11, 11), (17, 13), (7, 17), (17, 18)]
                ):
                    towns.append(
                        {
                            "id": identity(),
                            "owner": None,
                            "name": [
                                "Aschewacht",
                                "Nebelrelikt",
                                "Eisenhort",
                                "Dornenposten",
                                "Nullsektor",
                                "Schwarzes Relais",
                                "Titanwache",
                                "Zitadelle des Kerns",
                            ][i],
                            "x": x,
                            "y": y,
                            "tier": i + 1,
                            "stock": [400 * (i + 1)] * 3,
                            "cleared": False,
                        }
                    )
                db.execute("INSERT INTO world VALUES (1, ?)", (json.dumps(towns),))
                self.save_world_outposts(db, 1, towns)
            db.execute(
                "INSERT INTO world_settings(world_id,name,seed,outpost_count,joinable,created,settings) "
                "SELECT id,'Genesis',504921,104,TRUE,0,'{}' FROM world WHERE id=1 "
                "ON CONFLICT(world_id) DO NOTHING"
            )
            db.execute(
                "INSERT INTO world_rulesets(world_id,version) SELECT id,? FROM world WHERE TRUE "
                "ON CONFLICT(world_id) DO NOTHING",
                (REGISTRY["version"],),
            )
            if db.execute(
                "SELECT 1 FROM world_rulesets WHERE version<>? LIMIT 1", (REGISTRY["version"],)
            ).fetchone():
                raise RuleError("Mindestens eine Welt benötigt einen anderen Regelkatalog.")
            for row in db.execute("SELECT id FROM users").fetchall():
                self.systems.profile(db, row[0])
            if not db.execute("SELECT 1 FROM flags WHERE name='world_v2'").fetchone():
                towns = self.world_outposts(db, 1)
                occupied = {(t["x"], t["y"]) for t in towns}
                occupied.update(
                    (s["x"], s["y"])
                    for row in db.execute("SELECT state FROM colonies")
                    for s in [json.loads(row[0])]
                )
                rng = random.Random(264205)
                for i in range(96):
                    while True:
                        x, y = rng.randrange(64), rng.randrange(64)
                        if (x, y) not in occupied:
                            break
                    occupied.add((x, y))
                    tier = 1 + i % 6
                    towns.append(
                        {
                            "id": identity(),
                            "owner": None,
                            "name": f"Grenzposten {i+1:03d}",
                            "x": x,
                            "y": y,
                            "tier": tier,
                            "stock": [400 * tier] * 3,
                            "cleared": False,
                        }
                    )
                self.save_world_outposts(db, 1, towns)
                db.execute("INSERT INTO flags VALUES ('world_v2','true')")
            seed_world(db)
            if not db.postgres:
                db.executescript(
                    "CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'immutable'); END; CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'immutable'); END;"
                )
            else:
                db.executescript(
                    "DROP TRIGGER IF EXISTS audit_immutable ON audit; CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit FOR EACH ROW EXECUTE FUNCTION fur_immutable();"
                )

    def connect(self) -> Connection:
        return Connection(self.path)

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    def push_settings(self) -> Any:
        if self.settings is None:
            from .config import Settings

            self.settings = Settings.load(str(Path("data/empire.sqlite3")))
        return self.settings

    def world_outposts(self, db: Connection, world_id: int) -> list[dict[str, Any]]:
        return [
            json.loads(row["state"])
            for row in db.execute(
                "SELECT state FROM world_outposts WHERE world_id=? ORDER BY sort_order,target_id",
                (world_id,),
            )
        ]

    def world_regions(self, db: Connection, world_id: int) -> list[dict[str, Any]]:
        outposts = self.world_outposts(db, world_id)
        alliance_by_owner = {
            str(row["user_id"]): str(row["alliance_id"])
            for row in db.execute("SELECT user_id,alliance_id FROM members")
        }
        snapshot = (
            tuple((int(post["x"]), int(post["y"]), post.get("owner")) for post in outposts),
            tuple(sorted(alliance_by_owner.items())),
        )
        cached = self._region_cache.get(world_id)
        if cached is None or cached[0] != snapshot:
            regions = summarize_regions(outposts, alliance_by_owner)
            self._region_cache[world_id] = (snapshot, regions)
            return regions
        return cached[1]

    def regional_production_bonus(self, db: Connection, user: str, world_id: int) -> int:
        controlled = sum(
            1 for region in self.world_regions(db, world_id) if region["owner_id"] == user
        )
        return min(REGION_PRODUCTION_BONUS * controlled, MAX_REGION_PRODUCTION_BONUS)

    def save_world_outposts(
        self, db: Connection, world_id: int, outposts: list[dict[str, Any]]
    ) -> None:
        db.execute("DELETE FROM world_outposts WHERE world_id=?", (world_id,))
        for position, target in enumerate(outposts):
            db.execute(
                "INSERT INTO world_outposts(world_id,target_id,sort_order,x,y,state) "
                "VALUES (?,?,?,?,?,?)",
                (
                    world_id,
                    target["id"],
                    position,
                    target["x"],
                    target["y"],
                    json.dumps(target),
                ),
            )
        db.execute("UPDATE world SET state=? WHERE id=?", (json.dumps(outposts), world_id))
        self._region_cache.pop(world_id, None)

    def replenish_neutral_outposts(self, db: Connection, now: int) -> None:
        """Refill neutral stores and opted-in FUR-3 fortifications on bounded clocks."""
        worlds = db.execute(
            "SELECT world_id,settings,terra_combat_ruleset FROM world_settings"
        ).fetchall()
        for world in worlds:
            try:
                settings = json.loads(world["settings"])
            except (TypeError, json.JSONDecodeError):
                settings = {}
            if not isinstance(settings, dict):
                settings = {}
            fortification_rules = None
            if str(world["terra_combat_ruleset"]) == "FUR-3-TERRA-COMBAT-5":
                fortification_rules = terra_combat.rules_for("FUR-3-TERRA-COMBAT-5")[
                    "neutral_outpost_fortification"
                ]
            previous_check = settings.get("outpost_stock_checked_at")
            if type(previous_check) is not int:
                previous_check = now
            elapsed_minutes = max(0, now - previous_check) // 60
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts WHERE world_id=?",
                (world["world_id"],),
            ).fetchall():
                target = json.loads(row["state"])
                if target.get("owner") is not None:
                    continue
                post_changed = False
                if fortification_rules:
                    tier = max(1, min(8, int(target.get("tier", 1))))
                    maximum = int(fortification_rules["structure_per_tier_squared"]) * tier**2
                    checked_at = target.get("fortification_checked_at")
                    integrity = target.get("fortification_integrity")
                    if type(integrity) is not int or not 0 <= integrity <= maximum:
                        # Existing worlds begin at full strength when they first opt in.
                        integrity = maximum
                        target["fortification_integrity"] = maximum
                        post_changed = True
                    if type(checked_at) is not int:
                        checked_at = previous_check
                        target["fortification_checked_at"] = checked_at
                        post_changed = True
                    fortification_minutes = max(0, now - checked_at) // 60
                    if fortification_minutes:
                        per_minute = max(
                            1,
                            (
                                maximum
                                * int(fortification_rules["regeneration_percent_per_minute"])
                                + 99
                            )
                            // 100,
                        )
                        restored = min(maximum, integrity + fortification_minutes * per_minute)
                        target["fortification_integrity"] = restored
                        target["fortification_checked_at"] = checked_at + fortification_minutes * 60
                        post_changed = post_changed or restored != integrity
                stock = target.get("stock")
                if (
                    not isinstance(stock, list)
                    or len(stock) != len(RESOURCES)
                    or any(type(value) is not int or value < 0 for value in stock)
                ):
                    replenished = stock
                else:
                    capacity = 400 * max(1, int(target.get("tier", 1)))
                    replenished = [
                        min(capacity, amount + elapsed_minutes) if amount < capacity else amount
                        for amount in stock
                    ]
                    if replenished != stock:
                        target["stock"] = replenished
                        post_changed = True
                if not post_changed:
                    continue
                db.execute(
                    "UPDATE world_outposts SET state=? WHERE world_id=? AND target_id=?",
                    (json.dumps(target), world["world_id"], row["target_id"]),
                )
            settings["outpost_stock_checked_at"] = previous_check + elapsed_minutes * 60
            db.execute(
                "UPDATE world_settings SET settings=? WHERE world_id=?",
                (json.dumps(settings), world["world_id"]),
            )

    def update_npc_frontiers(self, db: Connection, now: int) -> None:
        """Run deterministic, world-local NPC supply pressure on neutral posts."""
        for world in db.execute("SELECT world_id,seed,settings FROM world_settings").fetchall():
            try:
                settings = json.loads(world["settings"])
            except (TypeError, json.JSONDecodeError):
                settings = {}
            if not isinstance(settings, dict):
                settings = {}
            previous = settings.get("npc_frontier_checked_at")
            if type(previous) is not int:
                settings["npc_frontier_checked_at"] = now
                db.execute(
                    "UPDATE world_settings SET settings=? WHERE world_id=?",
                    (json.dumps(settings), world["world_id"]),
                )
                continue
            elapsed = max(0, now - previous) // 300
            if elapsed == 0:
                continue
            outposts = self.world_outposts(db, int(world["world_id"]))
            changed = False
            seed = int(world["seed"])
            for post in outposts:
                if post.get("owner") is not None:
                    continue
                faction_index = int.from_bytes(
                    hashlib.sha256(f"{seed}:{post['id']}".encode()).digest()[:4], "big"
                ) % len(NPC_FACTIONS)
                faction_key, faction_name = NPC_FACTIONS[faction_index]
                post["npc_faction"] = faction_key
                post["npc_faction_name"] = faction_name
                tier = max(1, int(post.get("tier", 1)))
                strength = min(4, 1 + tier // 2)
                total_pressure = int(post.get("npc_pressure", 0)) + elapsed * strength
                supply_cycles, pressure = divmod(total_pressure, 100)
                post["npc_pressure"] = pressure
                stock = post.get("stock", [0, 0, 0])
                if (
                    not isinstance(stock, list)
                    or len(stock) != len(RESOURCES)
                    or any(type(value) is not int or value < 0 for value in stock)
                ):
                    continue
                capacity = 400 * tier
                if supply_cycles and any(value < capacity for value in stock):
                    post["stock"] = [
                        min(capacity, int(value) + supply_cycles * tier) for value in stock
                    ]
                changed = True
            if changed:
                self.save_world_outposts(db, int(world["world_id"]), outposts)
            settings["npc_frontier_checked_at"] = previous + elapsed * 300
            db.execute(
                "UPDATE world_settings SET settings=? WHERE world_id=?",
                (json.dumps(settings), world["world_id"]),
            )

    def terra_sector_rules(self, db: Connection, world_id: int) -> dict[tuple[int, int], str]:
        return {
            (int(row["x"]), int(row["y"])): str(row["kind"])
            for row in db.execute(
                "SELECT x,y,kind FROM terra_sector_rules WHERE world_id=?", (world_id,)
            )
        }

    def require_terra_settlement(self, db: Connection, world_id: int, x: int, y: int) -> None:
        if db.execute(
            "SELECT 1 FROM terra_sector_rules WHERE world_id=? AND x=? AND y=?",
            (world_id, x, y),
        ).fetchone():
            raise RuleError(
                "Dieser Terra-Sektor ist geschützt oder für neue Kontingente reserviert."
            )
        if db.execute(
            "SELECT 1 FROM terra_ruins WHERE world_id=? AND x=? AND y=? AND expires>?",
            (world_id, x, y, int(time.time())),
        ).fetchone():
            raise RuleError("Dieser Terra-Sektor ist vorübergehend durch eine Ruine belegt.")

    def active_terra_ruins(self, db: Connection, world_id: int) -> dict[tuple[int, int], int]:
        return {
            (row["x"], row["y"]): row["expires"]
            for row in db.execute(
                "SELECT x,y,expires FROM terra_ruins WHERE world_id=? AND expires>?",
                (world_id, int(time.time())),
            )
        }

    @staticmethod
    def npc_camp_points(db: Connection, world_id: int) -> set[tuple[int, int]]:
        """Return positioned camps only when movement rules make their sectors relevant."""
        from . import npc_camps

        settings_row = db.execute(
            "SELECT settings FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        if settings_row is None:
            return set()
        try:
            settings = json.loads(settings_row["settings"] or "{}")
        except (TypeError, json.JSONDecodeError):
            return set()
        if not isinstance(settings, dict) or not npc_camps.movement_enabled(settings):
            return set()
        return {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM npc_camps WHERE world_id=? AND x IS NOT NULL AND y IS NOT NULL",
                (world_id,),
            )
        }

    def create(
        self,
        db: Connection,
        user: str,
        name: str,
        world_id: int = 1,
        sector: tuple[int, int] | None = None,
    ) -> None:
        colony_points = {
            (int(colony["x"]), int(colony["y"]))
            for row in db.execute("SELECT state FROM colonies WHERE world_id=?", (world_id,))
            for colony in [json.loads(row["state"])]
        }
        occupied = set(colony_points)
        occupied.update((t["x"], t["y"]) for t in self.world_outposts(db, world_id))
        occupied.update(self.active_terra_ruins(db, world_id))
        camp_points = self.npc_camp_points(db, world_id)
        occupied.update(camp_points)
        sector_rules = self.terra_sector_rules(db, world_id)
        if sector is None:
            land = {
                (int(row["x"]), int(row["y"]))
                for row in db.execute(
                    "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'",
                    (world_id,),
                )
            }
            reserved = sorted(
                point for point, rule in sector_rules.items() if rule == "spawn_reserved"
            )
            candidates = reserved + [(x, y) for y in range(7, 64) for x in range(2, 64)]
            available = [
                (x, y)
                for x, y in candidates
                if (x, y) not in occupied
                and sector_rules.get((x, y)) != "protected"
                and (x, y) in land
                and all(
                    math.hypot(x - colony_x, y - colony_y) >= COLONY_MIN_DISTANCE
                    for colony_x, colony_y in colony_points
                )
                and all(
                    math.hypot(x - camp_x, y - camp_y) >= COLONY_MIN_DISTANCE
                    for camp_x, camp_y in camp_points
                )
            ]
            if not available:
                raise RuleError("Diese Welt ist voll. Bitte wende dich an die Spielleitung.")
            x, y = available[0]
        else:
            x, y = sector
            if not (0 <= x < 64 and 0 <= y < 64):
                raise RuleError("Ungültiger Startsektor.")
            if (
                (x, y) in occupied
                or sector_rules.get((x, y)) == "protected"
                or terrain_at(db, x, y, world_id) == "water"
            ):
                raise RuleError("Der Startsektor ist nicht frei bewohnbar.")
            if any(
                math.hypot(x - colony_x, y - colony_y) < COLONY_MIN_DISTANCE
                for colony_x, colony_y in colony_points
            ):
                raise RuleError(
                    "Der Startsektor liegt im sechs Sektoren großen Kolonieschutzabstand."
                )
            if any(
                math.hypot(x - camp_x, y - camp_y) < COLONY_MIN_DISTANCE
                for camp_x, camp_y in camp_points
            ):
                raise RuleError("Der Startsektor liegt im Schutzabstand eines NPC-Lagers.")
            if any(
                math.hypot(x - camp_x, y - camp_y) < COLONY_MIN_DISTANCE
                for camp_x, camp_y in camp_points
            ):
                raise RuleError("Der Startsektor liegt im Schutzabstand eines NPC-Lagers.")
        colony_id = user if world_id == 1 else identity()
        state = {
            "id": user,
            "colony_id": colony_id,
            "name": name,
            "x": x,
            "y": y,
            "terrain": terrain_at(db, x, y, world_id),
            "resources": [1200, 1000, 800],
            "buildings": {
                key: (1 if key in ("hq", "wood", "stone", "ore", "storage") else 0)
                for key in BUILDINGS
            },
            "tech": {key: 0 for key in TECH},
            "units": {"ranger": 15, "sentinel": 0, "mech": 0},
            "jobs": [],
            "reports": [],
            "claimed": [],
            "captures": 0,
            "last": int(time.time()),
        }
        state["colony_id"] = user
        state["colony_name"] = name
        db.execute(
            "INSERT INTO colonies"
            "(colony_id,user_id,world_id,is_home,x,y,state,name_key,ranking_score) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                colony_id,
                user,
                world_id,
                True,
                x,
                y,
                json.dumps(state),
                name.casefold(),
                self.colony_score(state),
            ),
        )
        self.systems.profile(db, user)
        db.execute(
            "INSERT INTO world_players(user_id,world_id) VALUES (?,?) "
            "ON CONFLICT(user_id,world_id) DO NOTHING",
            (user, world_id),
        )

    def create_world(
        self,
        db: Connection,
        name: str,
        seed: int,
        outpost_count: int = 104,
        joinable: bool = True,
        mode: str = "permanent",
    ) -> int:
        if mode not in ("permanent", "season", "sandbox"):
            raise RuleError("Ungültiger Weltmodus.")
        name = name.strip()
        if not 3 <= len(name) <= 48 or any(ord(char) < 32 for char in name):
            raise RuleError("Der Weltname muss 3 bis 48 Zeichen enthalten.")
        if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
            raise RuleError("Der Weltseed muss eine nichtnegative 64-Bit-Zahl sein.")
        if type(outpost_count) is not int or not 8 <= outpost_count <= 300:
            raise RuleError("Eine Welt benötigt 8 bis 300 Außenposten.")
        if db.execute(
            "SELECT 1 FROM world_settings WHERE lower(name)=lower(?)", (name,)
        ).fetchone():
            raise RuleError("Dieser Weltname ist bereits vergeben.")
        world_id = int(db.execute("SELECT COALESCE(MAX(id),0)+1 FROM world").fetchone()[0])
        db.execute("INSERT INTO world(id,state) VALUES (?, '[]')", (world_id,))
        db.execute(
            "INSERT INTO world_rulesets(world_id,version) VALUES (?,?)",
            (world_id, REGISTRY["version"]),
        )
        db.execute(
            "INSERT INTO world_settings(world_id,name,seed,outpost_count,joinable,created,settings,mode) "
            "VALUES (?,?,?,?,?,?, '{}',?)",
            (world_id, name, seed, outpost_count, bool(joinable), int(time.time()), mode),
        )
        seed_world(db, world_id, seed)
        land = [
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water' ORDER BY y,x",
                (world_id,),
            )
        ]
        rng = random.Random(seed ^ 0x465552)
        rng.shuffle(land)
        if len(land) < outpost_count + 1:
            raise RuleError("Für diese Welt reichen die bewohnbaren Sektoren nicht aus.")
        outposts = []
        for index, (x, y) in enumerate(land[:outpost_count]):
            tier = 8 if index == 0 else 1 + (index - 1) % 6
            outposts.append(
                {
                    "id": identity(),
                    "owner": None,
                    "name": (
                        "Zitadelle des Kerns" if tier == 8 else f"{name} · Außenposten {index:03d}"
                    ),
                    "x": x,
                    "y": y,
                    "tier": tier,
                    "stock": [400 * tier] * 3,
                    "cleared": False,
                }
            )
        self.save_world_outposts(db, world_id, outposts)
        return world_id

    def join_world(self, db: Connection, user: str, name: str, world_id: int) -> None:
        settings = db.execute(
            "SELECT seed,joinable,mode FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        if not settings or not settings["joinable"]:
            raise RuleError("Diese Welt nimmt derzeit keine neuen Spieler auf.")
        if (
            settings["mode"] == "season"
            and db.execute(
                "SELECT 1 FROM seasons WHERE world_id=? AND ends<=?",
                (world_id, int(time.time())),
            ).fetchone()
        ):
            raise RuleError("Eine beendete Saisonwelt bleibt für neue Spieler geschlossen.")
        home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (user, world_id),
        ).fetchone()
        if home:
            db.execute(
                "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
                (home["colony_id"], world_id, user),
            )
            return
        colony_points = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=?", (world_id,))
        }
        occupied = set(colony_points)
        occupied.update(
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM world_outposts WHERE world_id=?", (world_id,))
        )
        occupied.update(self.active_terra_ruins(db, world_id))
        camp_points = self.npc_camp_points(db, world_id)
        occupied.update(camp_points)
        land = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'",
                (world_id,),
            )
        }
        spaces = [
            (x, y)
            for y in range(64)
            for x in range(64)
            if (x, y) not in occupied and (x, y) in land
        ]
        user_seed = int.from_bytes(
            hashlib.sha256(f"{settings['seed']}:{user}".encode()).digest()[:8], "big"
        )
        rng = random.Random(user_seed)
        rng.shuffle(spaces)
        sector_rules = self.terra_sector_rules(db, world_id)
        spaces.sort(key=lambda point: sector_rules.get(point) != "spawn_reserved")
        spawn = next(
            (
                point
                for point in spaces
                if sector_rules.get(point) != "protected"
                and all(
                    math.hypot(point[0] - x, point[1] - y) >= COLONY_MIN_DISTANCE
                    for x, y in colony_points
                )
                and all(
                    math.hypot(point[0] - x, point[1] - y) >= COLONY_MIN_DISTANCE
                    for x, y in camp_points
                )
            ),
            None,
        )
        if spawn is None:
            raise RuleError("In dieser Welt gibt es keinen freien Startsektor mit Schutzabstand.")
        self.create(db, user, name, world_id, spawn)
        home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (user, world_id),
        ).fetchone()
        db.execute(
            "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
            (home["colony_id"], world_id, user),
        )

    def read(self, db: Connection, user: str) -> dict[str, Any]:
        profile = self.systems.profile(db, user)
        row = db.execute(
            "SELECT c.colony_id,c.world_id,c.state FROM colonies c "
            "WHERE c.user_id=? AND c.colony_id=?",
            (user, profile.get("active_colony_id")),
        ).fetchone()
        if row is None:
            raise RuleError("Kolonie nicht gefunden.")
        result: dict[str, Any] = json.loads(row["state"])
        result["colony_id"] = row["colony_id"]
        result["world_id"] = int(row["world_id"])
        result.setdefault("colony_name", result["name"])
        return self._decorate_simulation_state(db, result)

    def read_colony(self, db: Connection, colony_id: str) -> dict[str, Any]:
        row = db.execute(
            "SELECT colony_id,user_id,world_id,state FROM colonies WHERE colony_id=?", (colony_id,)
        ).fetchone()
        if row is None:
            raise RuleError("Kolonie nicht gefunden.")
        result: dict[str, Any] = json.loads(row["state"])
        result["id"] = row["user_id"]
        result["colony_id"] = row["colony_id"]
        result["world_id"] = int(row["world_id"])
        result.setdefault("colony_name", result["name"])
        return self._decorate_simulation_state(db, result)

    def _decorate_simulation_state(self, db: Connection, result: dict[str, Any]) -> dict[str, Any]:
        result["terrain"] = terrain_at(db, result["x"], result["y"], int(result.get("world_id", 1)))
        result["commander"] = heroes.view(db, str(result["id"]), int(result.get("world_id", 1)))
        result["commander_doctrines"] = hero_doctrines.view(
            db, int(result.get("world_id", 1)), result["commander"]
        )
        result["_region_bonus"] = self.regional_production_bonus(
            db, str(result["id"]), int(result.get("world_id", 1))
        )
        result["_events"] = [
            dict(r)
            for r in db.execute(
                "SELECT starts,ends,bonus,end_starts,end_bonus FROM events "
                "WHERE world_id=? AND ends>?",
                (result["world_id"], result["last"]),
            )
        ]
        faction = self.systems.world_faction(db, str(result["id"]), int(result["world_id"]))
        result["faction_chosen"] = faction is not None
        result["_faction_bonus"] = 10 if faction == "pioneers" else 0
        return result

    def travel_time(
        self,
        db: Connection,
        start: tuple[int, int],
        finish: tuple[int, int],
        world_id: int = 1,
        army: dict[str, int] | None = None,
    ) -> int:
        if army is not None:
            return int(self.movement_quote(db, start, finish, world_id, army)["travel_seconds"])
        try:
            return travel_seconds(db, start, finish, world_id)
        except ValueError as exc:
            raise RuleError(str(exc)) from exc

    def movement_quote(
        self,
        db: Connection,
        start: tuple[int, int],
        finish: tuple[int, int],
        world_id: int,
        army: dict[str, int],
        *,
        rules_version: str | None = None,
    ) -> dict[str, Any]:
        """Quote pinned FUR-3 movement; legacy worlds retain terrain-only travel."""
        world = db.execute(
            "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        version = rules_version or (str(world["terra_combat_ruleset"]) if world else "FUR-2")
        if version != "FUR-2" and not terra_combat.is_supported_version(version):
            raise RuleError("Für diese Bewegungsregeln ist keine Terra-Route definiert.")
        if version not in ("FUR-3-TERRA-COMBAT-3", "FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            return {
                "travel_seconds": self.travel_time(db, start, finish, world_id),
                "fuel_ore": 0,
                "route_cost": None,
                "rules_version": version,
                "rules_digest": None,
            }
        rules = terra_combat.rules_for(version)
        profiles = rules["units"]
        if (
            not isinstance(army, dict)
            or not army
            or any(
                unit not in profiles or type(count) is not int or count <= 0
                for unit, count in army.items()
            )
        ):
            raise RuleError("Ungültige Einheiten für die FUR-3-Bewegungsberechnung.")
        try:
            route_cost = travel_cost(db, start, finish, world_id)
        except ValueError as exc:
            raise RuleError(str(exc)) from exc
        limits = rules["unit_economy"]
        if route_cost > int(limits["route_cost_limit"]):
            raise RuleError("Das Ziel liegt außerhalb der Reichweite dieser Truppen.")
        if any(route_cost > int(profiles[unit]["range"]) for unit in army):
            raise RuleError("Mindestens eine Einheit hat nicht genügend Reichweite.")
        slowest_speed = min(int(profiles[unit]["speed"]) for unit in army)
        movement_seconds = (route_cost * 60 + slowest_speed - 1) // slowest_speed
        fuel_rate = sum(count * int(profiles[unit]["fuel"]) for unit, count in army.items())
        one_way_fuel = (route_cost * fuel_rate + 99) // 100
        return {
            "travel_seconds": max(60, movement_seconds),
            "fuel_ore": one_way_fuel * 2,
            "route_cost": route_cost,
            "rules_version": version,
            "rules_digest": terra_combat.RULESET_DIGESTS[version],
        }

    @staticmethod
    def terra_unit_catalog(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Adapt an immutable Terra roster to the common UI/economy unit contract."""
        result: dict[str, dict[str, Any]] = {}
        for key, raw in rules["units"].items():
            profile = dict(raw)
            profile.update(
                name=str(raw.get("role", key.replace("_", " ").title())),
                power=int(raw["attack"]) + int(raw["armor"]) + int(raw["shield"]),
                require=int(raw["prerequisites"]["buildings"].get("barracks", 1)),
                time=int(raw["training_time"]),
                cost=list(raw["cost"]),
                requirements={
                    "buildings": dict(raw["prerequisites"]["buildings"]),
                    "tech": dict(raw["prerequisites"]["tech"]),
                },
                enabled=key != "outpost_fortification",
            )
            result[key] = profile
        return result

    def unit_catalog_for_world(
        self, db: Connection, world_id: int, rules_version: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Return the authoritative unit roster selected by this world's combat version."""
        row = db.execute(
            "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        version = rules_version or (str(row[0]) if row else "FUR-2")
        if version in ("FUR-3-TERRA-COMBAT-3", "FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            return self.terra_unit_catalog(terra_combat.rules_for(version))
        return UNITS

    def army_transport_capacity(
        self, db: Connection, world_id: int, army: dict[str, int], logistics_level: int
    ) -> int:
        """Calculate cargo capacity without changing legacy transport rules."""
        world = db.execute(
            "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        version = str(world[0]) if world else "FUR-2"
        if version not in ("FUR-3-TERRA-COMBAT-3", "FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            return sum(army.values()) * (40 + 10 * logistics_level)
        rules = terra_combat.rules_for(version)
        total = 0
        for unit, count in army.items():
            if unit in UNITS:
                total += count * (40 + 10 * logistics_level)
            elif int(rules["units"][unit].get("cargo", 0)) > 0:
                total += count * int(rules["units"][unit]["cargo"])
        return total

    def record_terra_unit_wrecks(
        self,
        db: Connection,
        *,
        mission_id: str,
        owner_id: str,
        colony_id: str,
        world_id: int,
        losses: dict[str, int],
        combat_version: str,
        at: int,
    ) -> list[dict[str, Any]]:
        """Record rule-limited COMBAT-4 wrecks at the colony that owned each force."""
        if combat_version not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            return []
        owner = db.execute(
            "SELECT user_id,world_id FROM colonies WHERE colony_id=?", (colony_id,)
        ).fetchone()
        if not owner or str(owner["user_id"]) != owner_id or int(owner["world_id"]) != world_id:
            raise RuleError("Der Verlust kann keiner gültigen Ausgangskolonie zugeordnet werden.")
        profiles = terra_combat.rules_for(combat_version)["units"]
        try:
            return terra_recovery.record_losses(
                db,
                mission_id=mission_id,
                owner_id=owner_id,
                colony_id=colony_id,
                world_id=world_id,
                losses=losses,
                unit_profiles=profiles,
                at=at,
            )
        except ValueError as exc:
            raise RuleError("Die versionierten Terra-Wrackdaten sind ungültig.") from exc

    def save(self, db: Connection, state: dict[str, Any]) -> None:
        persisted_state = {
            key: value
            for key, value in state.items()
            if key not in ("commander", "commander_doctrines", "commander_respec")
        }
        db.execute(
            "UPDATE colonies SET state=?,name_key=?,ranking_score=? "
            "WHERE colony_id=? AND user_id=?",
            (
                json.dumps(persisted_state),
                str(state.get("colony_name", state["name"])).casefold(),
                self.colony_score(state),
                state["colony_id"],
                state["id"],
            ),
        )
        db.execute(
            "DELETE FROM incoming_attack_index WHERE source_colony_id=?",
            (state["colony_id"],),
        )
        for job in state.get("jobs", []):
            if job.get("kind") != "attack" or not job.get("key"):
                continue
            target = db.execute("SELECT 1 FROM users WHERE id=?", (job["key"],)).fetchone()
            if target:
                db.execute(
                    "INSERT INTO incoming_attack_index(job_id,target_user,source_colony_id,due) "
                    "VALUES (?,?,?,?) ON CONFLICT(job_id) DO NOTHING",
                    (job["id"], job["key"], state["colony_id"], job["due"]),
                )

    @staticmethod
    def colony_score(state: dict[str, Any]) -> int:
        """Return the unchanged FUR-2 colony ranking formula."""
        return int(
            sum(state["buildings"].values()) * 10
            + sum(state["tech"].values()) * 20
            + int(state["captures"]) * 100
        )

    def report(
        self,
        state: dict[str, Any],
        title: str,
        body: str,
        combat: dict[str, Any] | None = None,
        *,
        report_side: str | None = None,
        report_wing: int | None = None,
        share_allowed: bool = False,
        title_key: str | None = None,
        body_key: str | None = None,
        message_params: dict[str, Any] | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "id": identity(),
            "title": title,
            "body": body,
            "time": int(time.time()),
        }
        if title_key and body_key:
            entry["title_key"] = title_key
            entry["body_key"] = body_key
            entry["message_params"] = message_params or {}
        if combat is not None:
            entry["combat"] = combat
            entry["share_owner"] = {
                "side": report_side,
                "wing_index": report_wing,
                "allowed": share_allowed
                and report_side in ("attacker", "defender", "attacker_wing"),
            }
        state["reports"].insert(0, entry)
        state["reports"] = state["reports"][:100]

    @staticmethod
    def construction_duration(state: dict[str, Any], level: int) -> int:
        duration = 8 * level - state["buildings"]["hq"]
        if "rapid_construction" in state.get("faction_research", []):
            duration = duration * 90 // 100
        return int(max(3, duration))

    def replan_upgrade_queue(self, state: dict[str, Any], kind: str, now: int) -> list[int]:
        """Reprice and reschedule one build/research queue after an edit."""
        catalog = BUILDINGS if kind == "build" else TECH
        section = "buildings" if kind == "build" else "tech"
        queue = sorted(
            (job for job in state["jobs"] if job["kind"] == kind),
            key=lambda job: (int(job.get("queue_order", -1)), int(job["due"])),
        )
        level_counts: dict[str, int] = {}
        updates: list[tuple[dict[str, Any], int, list[int], int]] = []
        net_cost = [0, 0, 0]
        for position, job in enumerate(queue):
            key = job["key"]
            if key not in catalog:
                raise RuleError("Ein Auftrag in der Warteschlange ist ungültig.")
            snapshot = job.get("rule_snapshot")
            base_cost = catalog[key]["cost"]
            if snapshot is None:
                stored_cost = job.get("costs")
                stored_level = job.get("target_level")
                if (
                    isinstance(stored_cost, list)
                    and len(stored_cost) == 3
                    and all(type(value) is int and value > 0 for value in stored_cost)
                    and type(stored_level) is int
                    and stored_level > 0
                    and all(value % stored_level == 0 for value in stored_cost)
                ):
                    base_cost = [value // stored_level for value in stored_cost]
                    snapshot = {
                        "version": "legacy-inferred",
                        "digest": "0" * 64,
                        "base_cost": base_cost,
                        "formula": "linear-target-level-v1",
                        "source": "legacy_cost_inference",
                    }
                    job["rule_snapshot"] = snapshot
            if isinstance(snapshot, dict):
                saved_cost = snapshot.get("base_cost")
                saved_digest = snapshot.get("digest")
                if (
                    snapshot.get("formula") != "linear-target-level-v1"
                    or not isinstance(saved_cost, list)
                    or len(saved_cost) != 3
                    or any(type(value) is not int or value <= 0 for value in saved_cost)
                    or not isinstance(snapshot.get("version"), str)
                    or not isinstance(saved_digest, str)
                    or len(saved_digest) != 64
                    or any(character not in "0123456789abcdef" for character in saved_digest)
                ):
                    raise RuleError("Der Regel-Snapshot eines Bauauftrags ist ungültig.")
                base_cost = saved_cost
            target_level = state[section].get(key, 0) + level_counts.get(key, 0) + 1
            level_counts[key] = level_counts.get(key, 0) + 1
            target_cost = [int(value) * target_level for value in base_cost]
            old_cost = job.get("costs")
            if (
                not isinstance(old_cost, list)
                or len(old_cost) != 3
                or any(type(value) is not int for value in old_cost)
            ):
                old_cost = target_cost
            for index in range(3):
                net_cost[index] += int(old_cost[index]) - target_cost[index]
            duration = job.get("duration")
            if (
                job.get("queued", False)
                or position > 0
                or type(duration) is not int
                or duration < 1
            ):
                duration = (
                    self.construction_duration(state, target_level)
                    if kind == "build"
                    else 12 * target_level
                )
            updates.append((job, target_level, target_cost, duration))

        resources = state["resources"]
        cap = 2000 + state["buildings"]["storage"] * 2000
        reserve = state.setdefault("reserve", [0, 0, 0])
        for index, delta in enumerate(net_cost):
            if delta < 0 and resources[index] < -delta:
                raise RuleError("Nicht genügend Rohstoffe, um die Auftragsfolge neu zu planen.")
        released = [max(0, delta) for delta in net_cost]
        for index, delta in enumerate(net_cost):
            total = resources[index] + delta
            if delta < 0:
                resources[index] = total
            else:
                reserve[index] += max(0, total - cap)
                resources[index] = min(cap, total)

        cursor = now
        for position, (job, target_level, target_cost, duration) in enumerate(updates):
            job["queue_order"] = position
            job["target_level"] = target_level
            job["costs"] = target_cost
            job["duration"] = duration
            if position == 0 and not job.get("queued", False):
                job.setdefault("started_at", int(job["due"]) - duration)
                cursor = int(job["due"])
                continue
            job["queued"] = position > 0
            job["started_at"] = cursor
            job["due"] = cursor + duration
            cursor = int(job["due"])
        if updates and updates[0][0].get("queued", False):
            updates[0][0]["queued"] = False
            updates[0][0]["started_at"] = now
            updates[0][0]["due"] = now + updates[0][3]
        return released

    @staticmethod
    def terra_mission_limit(state: dict[str, Any]) -> int:
        uplink = state.get("terra_energy_levels", {}).get("command_uplink", 0)
        prestige = state.get("terra_prestige_level", 0)
        base = orbit_rules.TERRA_MISSION_BASE + min(10 + 2 * (prestige // 5), 2 * uplink)
        doctrine = state.get("commander_doctrines", {})
        bonus = (
            doctrine.get("bonuses", {}).get("mission_slots", 0) if doctrine.get("enabled") else 0
        )
        return int(base + max(0, int(bonus)))

    @staticmethod
    def terra_energy(state: dict[str, Any], at: int) -> dict[str, int]:
        levels = state.get("terra_energy_levels", {})
        supply = 4 * levels.get("energy_core", 0)
        demand = 6 * levels.get("fusion_plant", 0)
        served = min(supply, demand) if state.get("fusion_supplied_until", 0) > at else 0
        return {"supply": supply, "demand": demand, "served": served, "ore_bonus": 2 * served}

    def produce(self, state: dict[str, Any], until: int) -> None:
        until = max(until, state["last"])
        if state.get("terra_dormant"):
            state["last"] = until
            return
        start = max(state["last"], min(until, state.get("vacation_until", 0)))
        elapsed = until - start
        if not elapsed:
            state["last"] = until
            return
        cap = 2000 + state["buildings"]["storage"] * 2000
        carry = state.setdefault("carry", [0, 0, 0])
        subcarry = state.setdefault("carry_sub", [0, 0, 0])
        event_seconds_pp = live_events.integrated_bonus_seconds(
            state.get("_events", []), start, until
        )
        energy = self.terra_energy(state, start)
        powered_seconds = max(0, min(until, state.get("fusion_supplied_until", 0)) - start)
        for i, key in enumerate(RESOURCES):
            base = 2 + state["buildings"][key] * 2
            terrain_percent = PRODUCTION_PERCENT[state.get("terrain", "plain")][i]
            production_pp = (
                100
                + 15 * state["tech"]["engineering"]
                + state["captures"] * 5
                + state.get("_region_bonus", 0)
                + state.get("_faction_bonus", 0)
                + (
                    2 * int(state.get("commander", {}).get("stats", {}).get("economy", 0))
                    if state.get("commander", {}).get("enabled")
                    else 0
                )
                + (
                    5
                    if key == "wood" and "adaptive_forestry" in state.get("faction_research", [])
                    else 0
                )
            )
            powered_bonus = powered_seconds * energy["ore_bonus"] if key == "ore" else 0
            total = (
                (elapsed * production_pp + event_seconds_pp + powered_bonus)
                * base
                * terrain_percent
                + 100 * carry[i]
                + subcarry[i]
            )
            gained, remainder = divmod(total, 10_000)
            state["resources"][i] = min(cap, state["resources"][i] + gained)
            if state["resources"][i] == cap:
                remainder = 0
            carry[i], subcarry[i] = divmod(remainder, 100)
        state["last"] = until

    def tick(
        self, db: Connection, state: dict[str, Any], now: int, *, event_id: str | None = None
    ) -> None:
        before = list(state["resources"])
        quarantined = {
            r[0] for r in db.execute("SELECT job_id FROM job_failures WHERE attempts>=3")
        }
        while True:
            blocked_queues = {
                job["kind"]
                for job in state["jobs"]
                if job["id"] in quarantined and job["kind"] in ("build", "research")
            }
            due_jobs = [
                job
                for job in state["jobs"]
                if job["due"] <= now
                and (event_id is None or job["id"] == event_id)
                and job["id"] not in quarantined
                and job["kind"] not in blocked_queues
            ]
            if not due_jobs:
                break
            job = min(due_jobs, key=lambda item: (item["due"], item["id"]))
            self.produce(state, job["due"])
            kind, key = job["kind"], job.get("key", "")
            if self.systems.process_job(db, state, job):
                pass
            elif kind in ("build", "research"):
                section = "buildings" if kind == "build" else "tech"
                state[section][key] += 1
                self.report(
                    state,
                    "Auftrag abgeschlossen",
                    f"{job['label']} ist jetzt Stufe {state[section][key]}.",
                    title_key="report.order_title",
                    body_key="report.order_body",
                    message_params={
                        "label": job["label"],
                        "label_key": f"catalog.{section}.{key}.name",
                        "level": state[section][key],
                    },
                )
            elif kind == "terra_energy_build":
                levels = state.setdefault("terra_energy_levels", {})
                levels[key] = job["level"]
                if key == "fusion_plant" and job["level"] == 1:
                    state["fusion_supplied_until"] = job["due"] + FUSION_SUPPLY_SECONDS
                self.report(state, "Terra-Spezialgebäude fertiggestellt", job["label"])
            elif kind == "terra_prestige":
                if job.get("rules_digest") != orbit_rules.DIGEST:
                    raise RuleError("Der Prestige-Regelstand dieses Auftrags ist nicht verfügbar.")
                state["terra_prestige_level"] = job["level"]
                self.report(state, "Terra-Prestige erreicht", job["label"])
            elif kind == "terra_faction_research":
                if job.get("rules_digest") != orbit_rules.DIGEST:
                    raise RuleError("Der Fraktions-Regelstand dieses Auftrags ist nicht verfügbar.")
                state.setdefault("faction_research", []).append(key)
                self.report(state, "Fraktionsforschung abgeschlossen", job["label"])
            elif kind == "train":
                if job.get("rules_digest") is not None:
                    rules = terra_combat.rules_for(str(job.get("rules_version", "")))
                    if (
                        job.get("rules_digest")
                        != terra_combat.RULESET_DIGESTS.get(str(job.get("rules_version", "")))
                        or key not in rules["units"]
                        or int(state["units"].get(key, 0)) + int(job["count"])
                        > int(rules["unit_economy"]["maximum_units_per_colony"])
                    ):
                        raise RuleError(
                            "Der Einheitenauftrag verletzt den gespeicherten Regelstand."
                        )
                state["units"][key] = state["units"].get(key, 0) + job["count"]
                self.report(
                    state,
                    "Truppen einsatzbereit",
                    f"{job['count']} {job['label']} verstärken deine Garnison.",
                    title_key="report.training_title",
                    body_key="report.training_body",
                    message_params={
                        "label": job["label"],
                        "label_key": f"catalog.units.{key}.name",
                        "count": job["count"],
                    },
                )
            elif kind == "terra_repair":
                combat_version = str(job.get("combat_rules_version", ""))
                combat_digest = terra_combat.RULESET_DIGESTS.get(combat_version)
                count = job.get("count")
                if type(job.get("due")) is not int or int(job["due"]) > now:
                    raise RuleError("Der gespeicherte Reparaturauftrag ist noch nicht fällig.")
                wreck = db.execute(
                    "SELECT amount,expires,rule_version,rule_digest FROM terra_unit_wrecks "
                    "WHERE id=? AND owner_id=? AND colony_id=? AND world_id=?",
                    (
                        job.get("wreck_id"),
                        state["id"],
                        state["colony_id"],
                        state["world_id"],
                    ),
                ).fetchone()
                if (
                    job.get("repair_rules_version") != terra_recovery.VERSION
                    or job.get("repair_rules_digest") != terra_recovery.DIGEST
                    or combat_version not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
                    or job.get("combat_rules_digest") != combat_digest
                    or key not in terra_combat.rules_for(combat_version)["units"]
                    or type(count) is not int
                    or count < 1
                    or not wreck
                    or int(wreck["amount"]) < 0
                    or str(wreck["rule_version"]) != terra_recovery.VERSION
                    or str(wreck["rule_digest"]) != terra_recovery.DIGEST
                    or int(state["units"].get(key, 0)) + count
                    > int(
                        terra_combat.rules_for(combat_version)["unit_economy"][
                            "maximum_units_per_colony"
                        ]
                    )
                ):
                    raise RuleError("Der gespeicherte Reparaturauftrag ist ungültig.")
                state["units"][key] = state["units"].get(key, 0) + count
                self.report(
                    state,
                    "Einheiten repariert",
                    f"{count} {job['label']} sind wieder einsatzbereit.",
                )
            elif kind == "raid":
                self.battle(db, state, job)
            elif kind == "return":
                for unit, count in job["army"].items():
                    state["units"][unit] = state["units"].get(unit, 0) + count
                cap = 2000 + 2000 * state["buildings"]["storage"]
                reserve = state.setdefault("reserve", [0, 0, 0])
                for i, (a, b) in enumerate(zip(state["resources"], job["loot"])):
                    reserve[i] += max(0, a + b - cap)
                state["resources"] = [
                    min(cap, a + b) for a, b in zip(state["resources"], job["loot"])
                ]
                goods_cargo = job.get("goods_cargo", {})
                if not isinstance(goods_cargo, dict):
                    raise RuleError("Die gespeicherte Warenfracht im Rückmarsch ist ungültig.")
                if goods_cargo:
                    from .neutral_market import GOODS, RESOURCE_IDS

                    inventory = dict(state.get("goods_inventory", {}))
                    goods_reserve = dict(state.get("goods_reserve", {}))
                    goods_inbound = dict(state.get("goods_inbound", {}))
                    depot_cap = 2000 + state["buildings"]["storage"] * 2000
                    for good_id, amount in goods_cargo.items():
                        if (
                            not isinstance(good_id, str)
                            or good_id not in GOODS
                            or good_id in RESOURCE_IDS
                            or type(amount) is not int
                            or amount < 0
                        ):
                            raise RuleError(
                                "Die gespeicherte Warenfracht im Rückmarsch ist ungültig."
                            )
                        room = max(
                            0,
                            depot_cap
                            - int(inventory.get(good_id, 0))
                            - int(goods_inbound.get(good_id, 0)),
                        )
                        stored = min(room, amount)
                        inventory[good_id] = int(inventory.get(good_id, 0)) + stored
                        overflow = amount - stored
                        if overflow:
                            goods_reserve[good_id] = int(goods_reserve.get(good_id, 0)) + overflow
                    state["goods_inventory"] = inventory
                    state["goods_reserve"] = goods_reserve
                item_cargo = job.get("item_cargo", {})
                if not isinstance(item_cargo, dict):
                    raise RuleError(
                        "Die gespeicherte Gegenstandsfracht im Rückmarsch ist ungültig."
                    )
                if item_cargo:
                    from .items import return_cargo

                    return_cargo(state, item_cargo)
                if job.get("alliance_attack_id"):
                    db.execute(
                        "UPDATE terra_alliance_attack_wings SET status='returned' "
                        "WHERE attack_id=? AND user_id=?",
                        (job["alliance_attack_id"], state["id"]),
                    )
                if job.get("return_reason") == "recalled":
                    self.report(
                        state,
                        "Mission zurückgekehrt",
                        f"Truppen und Fracht sind zurück. Eingelagert: {job['loot'][0]} Holz, "
                        f"{job['loot'][1]} Stein und {job['loot'][2]} Erz (Depotlimit beachten).",
                    )
                else:
                    self.report(
                        state,
                        "Truppen zurückgekehrt",
                        f"Beute eingelagert: {job['loot'][0]} Holz, {job['loot'][1]} Stein, {job['loot'][2]} Erz (Depotlimit beachten).",
                        title_key="report.return_title",
                        body_key="report.return_body",
                        message_params={
                            "wood": job["loot"][0],
                            "stone": job["loot"][1],
                            "ore": job["loot"][2],
                        },
                    )
            if kind in ("build", "research", "train"):
                recurring_quests.record_completed_order(
                    db,
                    int(state["world_id"]),
                    str(state["id"]),
                    kind,
                    int(job["due"]),
                    int(job["count"]) if kind == "train" else 1,
                )
            hero_xp = heroes.award_job(
                db, str(state["id"]), int(state["world_id"]), job, int(job["due"])
            )
            if hero_xp:
                self.report(
                    state,
                    "Commander-Erfahrung erhalten",
                    f"Dein Commander erhält {hero_xp} Erfahrungspunkte für diese abgeschlossene Mission.",
                )
                self.systems.audit(
                    db,
                    str(state["id"]),
                    "hero_xp_awarded",
                    str(job["id"]),
                    world_id=int(state["world_id"]),
                    source_kind=kind,
                    experience=hero_xp,
                    rules_version=heroes.RULES.version,
                    rules_hash=heroes.RULE_HASH,
                )
            state["jobs"].remove(job)
            if kind in ("build", "research"):
                self.replan_upgrade_queue(state, kind, int(job["due"]))
        self.produce(state, now)
        self.save(db, state)
        if before != state["resources"]:
            db.execute(
                "INSERT INTO ledger VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identity(),
                    state["id"],
                    now,
                    "simulation",
                    json.dumps(before),
                    json.dumps(state["resources"]),
                ),
            )

    def simulate_outpost_battle(
        self, db: Connection, state: dict[str, Any], target_id: str, army: dict[str, int]
    ) -> dict[str, Any]:
        """Return a read-only neutral or intel-scoped PvP battle projection."""
        world_id = int(state.get("world_id", 1))
        target = next(
            (post for post in self.world_outposts(db, world_id) if post["id"] == target_id), None
        )
        if target is None:
            return self.systems.simulate_player_battle(db, state, target_id, army)
        if not sector_is_known(db, str(state["id"]), world_id, int(target["x"]), int(target["y"])):
            raise RuleError("Dieses Ziel ist nicht bekannt.")
        if target.get("owner") is not None:
            raise RuleError("Die Gefechtsprobe ist nur für neutrale Außenposten verfügbar.")
        combat_world = db.execute(
            "SELECT terra_combat_ruleset,terra_retreat_threshold_percent "
            "FROM world_settings WHERE world_id=?",
            (world_id,),
        ).fetchone()
        combat_version = str(combat_world["terra_combat_ruleset"]) if combat_world else "FUR-2"
        unit_catalog = self.unit_catalog_for_world(db, world_id, combat_version)
        if (
            not army
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            raise RuleError("Wähle mindestens eine verfügbare Einheit für die Gefechtsprobe.")
        if terra_combat.is_supported_version(combat_version):
            terrain = terrain_at(db, int(target["x"]), int(target["y"]), world_id)
            defenders = dict(target.get("units", {}))
            fortification_integrity = None
            combat_rules = terra_combat.rules_for(combat_version)
            if combat_rules.get("neutral_outpost_fortification"):
                if combat_version == "FUR-3-TERRA-COMBAT-5":
                    fortification = combat_rules["neutral_outpost_fortification"]
                    maximum = (
                        int(fortification["structure_per_tier_squared"]) * int(target["tier"]) ** 2
                    )
                    current = target.get("fortification_integrity", maximum)
                    if type(current) is not int or not 0 <= current <= maximum:
                        current = maximum
                    if current:
                        defenders["outpost_fortification"] = 1
                        fortification_integrity = current
                else:
                    defenders["outpost_fortification"] = int(target["tier"]) ** 2
            projection = terra_combat.simulate(
                dict(army),
                defenders,
                simulation_key=f"neutral:{state['id']}:{world_id}:{target_id}",
                attacker_tactics=int(state["tech"]["tactics"]),
                defender_modifiers={"terrain": int(DEFENSE_PERCENT[terrain])},
                retreat_threshold_percent=int(combat_world["terra_retreat_threshold_percent"]),
                loot_stock=list(target["stock"]),
                logistics_level=int(state["tech"]["logistics"]),
                unit_transport_capacity={
                    unit: self.army_transport_capacity(db, world_id, {unit: 1}, 0) for unit in army
                },
                rules_version=combat_version,
                outpost_fortification_integrity=fortification_integrity,
            )
            projection["defender_survivors"].pop("outpost_fortification", None)
            projection["defender_losses"].pop("outpost_fortification", None)
            projection["simulation"]["defender_survivors"].pop("outpost_fortification", None)
            projection["simulation"]["defender_losses"].pop("outpost_fortification", None)
            return projection
        result = resolve_outpost_battle(
            army,
            dict(target.get("units", {})),
            int(target["tier"]),
            int(state["tech"]["tactics"]),
            terrain_at(db, int(target["x"]), int(target["y"]), world_id),
        )
        capacity = self.army_transport_capacity(
            db, world_id, result["attacker_survivors"], int(state["tech"]["logistics"])
        )
        result["loot"] = (
            [min(count, capacity // 3) for count in target["stock"]]
            if result["victory"]
            else [0, 0, 0]
        )
        return result

    def battle(self, db: Connection, state: dict[str, Any], job: dict[str, Any]) -> None:
        world_id = int(state.get("world_id", 1))
        towns = self.world_outposts(db, world_id)
        target = next(t for t in towns if t["id"] == job["key"])
        blocked = target["owner"] is not None and (
            not job.get("allow_owned") or job.get("expected_owner") != target["owner"]
        )
        if target["owner"] and not blocked:
            try:
                self.systems.can_attack(db, state["id"], target["owner"], job["due"], world_id)
            except RuleError:
                blocked = True
        if blocked:
            if terra_combat.is_supported_version(str(job.get("rules_version", ""))):
                db.execute("DELETE FROM terra_combat_missions WHERE mission_id=?", (job["id"],))
            self.report(
                state,
                "Mission abgebrochen",
                "Der Zielposten wurde bereits besetzt. Alle Truppen kehren unversehrt zurück.",
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": job["key"],
                    "label": "Rückkehr aus " + target["name"],
                    "due": job["due"] + job["travel"],
                    "army": job["army"],
                    "loot": [0, 0, 0],
                }
            )
            return
        defender_id = str(target["owner"]) if target.get("owner") else None
        garrison = dict(target.get("units", {}))
        combat_result: dict[str, Any] | None = None
        rules_version = str(job.get("rules_version", "FUR-2"))
        if terra_combat.is_supported_version(rules_version):
            combat_rules = terra_combat.rules_for(rules_version)
            if job.get("rules_digest") != terra_combat.RULESET_DIGESTS[rules_version]:
                raise RuleError("Der Kampfregelstand dieser Mission ist nicht verfügbar.")
            try:
                seed, retreat_threshold = terra_combat.mission_seed(
                    db, str(job["id"]), world_id, str(job.get("seed_commitment", ""))
                )
            except ValueError as exc:
                raise RuleError("Der gespeicherte Kampfseed ist ungültig.") from exc
            terrain = terrain_at(db, int(target["x"]), int(target["y"]), world_id)
            fortification_integrity = None
            initial_fortification_integrity = None
            if combat_rules.get("neutral_outpost_fortification") and target.get("owner") is None:
                if rules_version == "FUR-3-TERRA-COMBAT-5":
                    fortification_rules = combat_rules["neutral_outpost_fortification"]
                    maximum = (
                        int(fortification_rules["structure_per_tier_squared"])
                        * int(target["tier"]) ** 2
                    )
                    current = target.get("fortification_integrity", maximum)
                    if type(current) is not int or not 0 <= current <= maximum:
                        current = maximum
                    if current:
                        garrison["outpost_fortification"] = 1
                        fortification_integrity = current
                        initial_fortification_integrity = current
                else:
                    garrison["outpost_fortification"] = int(target["tier"]) ** 2
            combat_result = terra_combat.resolve(
                seed,
                dict(job["army"]),
                garrison,
                attacker_tactics=int(job.get("tactics", state["tech"]["tactics"])),
                attacker_modifiers={"doctrine": hero_doctrines.combat_modifier(job)},
                defender_modifiers={"terrain": int(DEFENSE_PERCENT[terrain])},
                retreat_threshold_percent=retreat_threshold,
                rules_version=rules_version,
                outpost_fortification_integrity=fortification_integrity,
            )
            if rules_version == "FUR-3-TERRA-COMBAT-5" and defender_id is None:
                target["fortification_integrity"] = int(
                    combat_result.get("outpost_fortification_integrity", 0)
                )
                target["fortification_checked_at"] = int(job["due"])
            combat_result["defender_survivors"].pop("outpost_fortification", None)
            combat_result["defender_losses"].pop("outpost_fortification", None)
            combat_result["victory"] = combat_result["outcome"] == "attacker_win"
            combat_result["power"] = sum(
                int(combat_rules["units"][unit]["attack"]) * amount
                for unit, amount in job["army"].items()
            )
            combat_result["defense"] = sum(
                (
                    int(combat_rules["units"][unit]["armor"])
                    + int(combat_rules["units"][unit]["shield"])
                    + int(combat_rules["units"][unit]["hull"])
                )
                * amount
                for unit, amount in garrison.items()
                if unit in combat_rules["units"]
            )
            if (
                "outpost_fortification" in garrison
                and "outpost_fortification" not in combat_rules["units"]
            ):
                fortification_defense = (
                    initial_fortification_integrity
                    if rules_version == "FUR-3-TERRA-COMBAT-5"
                    else int(
                        combat_rules["neutral_outpost_fortification"]["structure_per_tier_squared"]
                    )
                    * int(garrison["outpost_fortification"])
                )
                combat_result["defense"] += int(fortification_defense or 0)
            result = combat_result
        elif rules_version == "FUR-2":
            result = resolve_outpost_battle(
                job["army"],
                garrison,
                int(target["tier"]),
                int(job.get("tactics", state["tech"]["tactics"])),
                terrain_at(db, target["x"], target["y"], world_id),
            )
        else:
            raise RuleError("Der Kampfregelstand dieser Mission ist nicht verfügbar.")
        power, defense, win = result["power"], result["defense"], result["victory"]
        army = result["attacker_survivors"]
        unit_catalog = self.unit_catalog_for_world(db, world_id, rules_version)
        target["units"] = result["defender_survivors"]
        attacker_losses = {
            unit: int(job["army"].get(unit, 0)) - int(army.get(unit, 0)) for unit in unit_catalog
        }
        defender_losses = {
            unit: int(garrison.get(unit, 0)) - int(target["units"].get(unit, 0))
            for unit in unit_catalog
        }
        if rules_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            self.record_terra_unit_wrecks(
                db,
                mission_id=str(job["id"]),
                owner_id=str(state["id"]),
                colony_id=str(state["colony_id"]),
                world_id=world_id,
                losses=attacker_losses,
                combat_version=rules_version,
                at=int(job["due"]),
            )
            if target.get("owner"):
                defender_colony = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (target["owner"], world_id),
                ).fetchone()
                if defender_colony:
                    self.record_terra_unit_wrecks(
                        db,
                        mission_id=str(job["id"]),
                        owner_id=str(target["owner"]),
                        colony_id=str(defender_colony["colony_id"]),
                        world_id=world_id,
                        losses=defender_losses,
                        combat_version=rules_version,
                        at=int(job["due"]),
                    )
        capacity = self.army_transport_capacity(db, world_id, army, int(state["tech"]["logistics"]))
        loot = [min(n, capacity // 3) if win else 0 for n in target["stock"]]
        if combat_result is not None:
            combat_result["loot"] = list(loot)
            terra_combat.store_replay(db, str(job["id"]), combat_result, int(job["due"]))
        if win:
            target["stock"] = [n - l for n, l in zip(target["stock"], loot)]
            if job.get("capture") and target["owner"] != state["id"]:
                if target["owner"]:
                    previous = self.read(db, target["owner"])
                    before = list(previous["resources"])
                    self.produce(previous, job["due"])
                    previous["captures"] = max(0, previous["captures"] - 1)
                    if target["tier"] == 8:
                        previous["citadel"] = False
                    self.report(previous, "Außenposten verloren", target["name"])
                    self.systems.ledger(db, previous, "outpost_lost", before)
                target.update(cleared=True, owner=state["id"])
                target.pop("fortification_integrity", None)
                target.pop("fortification_checked_at", None)
                state["captures"] += 1
                if target["tier"] == 8:
                    state["citadel"] = True
        self.save_world_outposts(db, world_id, towns)
        state["_region_bonus"] = self.regional_production_bonus(db, str(state["id"]), world_id)
        self.systems.audit(
            db,
            state["id"],
            "outpost_battle",
            target["id"],
            rule=rules_version,
            power=power,
            defense=defense,
            army_in=job["army"],
            defenders_in=garrison,
            survivors=army,
            loot=loot,
        )
        self.record_war_score(
            db,
            mission_id=str(job["id"]),
            world_id=world_id,
            user_id=str(state["id"]),
            category="attack",
            points=sum(attacker_losses.values()),
            rules_version=rules_version,
            at=int(job["due"]),
        )
        if defender_id and terra_combat.is_supported_version(rules_version):
            alliance_war.record_battle(
                db,
                mission_id=str(job["id"]),
                world_id=world_id,
                attacker_losses={str(state["id"]): attacker_losses},
                defender_losses={defender_id: defender_losses},
                rules_version=rules_version,
                at=int(job["due"]),
            )
        if target.get("owner") and target["owner"] != state["id"]:
            self.record_war_score(
                db,
                mission_id=str(job["id"]),
                world_id=world_id,
                user_id=str(target["owner"]),
                category="defense",
                points=sum(defender_losses.values()),
                rules_version=rules_version,
                at=int(job["due"]),
            )
        combat_report: dict[str, Any]
        if combat_result is not None:
            rounds = []
            for battle_round in combat_result["rounds"]:
                attack_action = next(
                    (item for item in battle_round["actions"] if item["side"] == "attacker"),
                    {"damage": 0},
                )
                defense_action = next(
                    (item for item in battle_round["actions"] if item["side"] == "defender"),
                    {"damage": 0},
                )
                attacker_before = battle_round["attacker_before"]
                defender_before = battle_round["defender_before"]
                attacker_after = battle_round["attacker_after"]
                defender_after = battle_round["defender_after"]
                rounds.append(
                    {
                        "round": battle_round["round"],
                        "attack_power": attack_action["damage"],
                        "defense_power": defense_action["damage"],
                        "victory": win,
                        "attacker": {
                            "sent": attacker_before,
                            "losses": {
                                unit: count - attacker_after.get(unit, 0)
                                for unit, count in attacker_before.items()
                                if count != attacker_after.get(unit, 0)
                            },
                            "survivors": attacker_after,
                        },
                        "defender": {
                            "sent": defender_before,
                            "losses": {
                                unit: count - defender_after.get(unit, 0)
                                for unit, count in defender_before.items()
                                if count != defender_after.get(unit, 0)
                            },
                            "survivors": defender_after,
                        },
                        "loot": list(loot),
                    }
                )
            combat_report = {
                **combat_result,
                "participants": {"attacker": state["name"], "defender": target["name"]},
                "rounds": rounds,
            }
        else:
            combat_report = {
                "rules_version": REGISTRY["version"],
                "rules_digest": RULES_DIGEST,
                "participants": {"attacker": state["name"], "defender": target["name"]},
                "rounds": [
                    {
                        "round": 1,
                        "attack_power": power,
                        "defense_power": defense,
                        "victory": win,
                        "attacker": {
                            "sent": dict(job["army"]),
                            "losses": attacker_losses,
                            "survivors": dict(army),
                        },
                        "defender": {
                            "sent": garrison,
                            "losses": defender_losses,
                            "survivors": dict(target["units"]),
                        },
                        "loot": list(loot),
                    }
                ],
            }
        self.report(
            state,
            "Sieg bei " + target["name"] if win else "Niederlage bei " + target["name"],
            f"Angriff {power} · Verteidigung {defense}. Verluste: {sum(job['army'].values()) - sum(army.values())}. Beute: {sum(loot)}. Überlebende kehren zurück.",
            combat_report,
            report_side="attacker",
            share_allowed=True,
            title_key="report.victory_title" if win else "report.defeat_title",
            body_key="report.combat_body",
            message_params={
                "target": target["name"],
                "attack": power,
                "defense": defense,
                "losses": sum(job["army"].values()) - sum(army.values()),
                "loot": sum(loot),
            },
        )
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "return",
                "key": job["key"],
                "label": "Rückkehr aus " + target["name"],
                "due": job["due"] + job["travel"],
                "army": army,
                "loot": loot,
            }
        )

    @staticmethod
    def record_war_score(
        db: Connection,
        *,
        mission_id: str,
        world_id: int,
        user_id: str,
        category: str,
        points: int,
        rules_version: str,
        at: int,
    ) -> None:
        """Record versioned FUR-3 military score once per participant and mission."""
        if not terra_combat.is_supported_version(rules_version):
            return
        if (
            category == "support"
            and db.execute(
                "SELECT 1 FROM war_score_ledger WHERE world_id=? AND user_id=? "
                "AND category='support' AND created>? LIMIT 1",
                (world_id, user_id, at - 86400),
            ).fetchone()
        ):
            return
        db.execute(
            "INSERT INTO war_score_ledger "
            "(id,mission_id,world_id,user_id,category,points,rules_version,created) "
            "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(mission_id,user_id,category) DO NOTHING",
            (
                identity(),
                mission_id,
                world_id,
                user_id,
                category,
                max(0, int(points)),
                rules_version,
                at,
            ),
        )
        alliance = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (user_id,)
        ).fetchone()
        if alliance and int(points) > 0:
            db.execute(
                "INSERT INTO alliance_military_score_ledger "
                "(mission_id,user_id,world_id,alliance_id,category,points,rules_version,created) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(mission_id,user_id,category) DO NOTHING",
                (
                    mission_id,
                    user_id,
                    world_id,
                    str(alliance["alliance_id"]),
                    category,
                    int(points),
                    rules_version,
                    at,
                ),
            )

    @staticmethod
    def war_score_audit(db: Connection, user_id: str, world_id: int) -> list[dict[str, Any]]:
        """Expose only the caller's own bounded, categorized score ledger."""
        return [
            {
                "mission_id": str(row["mission_id"]),
                "category": str(row["category"]),
                "points": int(row["points"]),
                "rules_version": str(row["rules_version"]),
                "created": int(row["created"]),
            }
            for row in db.execute(
                "SELECT mission_id,category,points,rules_version,created FROM war_score_ledger "
                "WHERE user_id=? AND world_id=? ORDER BY created DESC,mission_id DESC LIMIT 50",
                (user_id, world_id),
            )
        ]

    def military_ranking_for_world(self, db: Connection, world_id: int) -> list[dict[str, Any]]:
        """Return auditable provisional FUR-3 military totals scoped to one world."""
        return [
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "attack": int(row["attack"]),
                "defense": int(row["defense"]),
                "support": int(row["support"]),
                "score": int(row["score"]),
            }
            for row in db.execute(
                "SELECT u.id,u.name,"
                "coalesce(sum(CASE WHEN l.category='attack' THEN l.points ELSE 0 END),0) AS attack,"
                "coalesce(sum(CASE WHEN l.category='defense' THEN l.points ELSE 0 END),0) AS defense,"
                "coalesce(sum(CASE WHEN l.category='support' THEN l.points ELSE 0 END),0) AS support,"
                "coalesce(sum(l.points),0) AS score FROM users u "
                "LEFT JOIN war_score_ledger l ON l.user_id=u.id AND l.world_id=? "
                "GROUP BY u.id,u.name ORDER BY score DESC,u.id",
                (world_id,),
            )
        ]

    def alliance_military_ranking_for_world(
        self, db: Connection, world_id: int
    ) -> list[dict[str, Any]]:
        """Aggregate member military ledger rows, retaining category attribution."""
        return [
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "tag": str(row["tag"]),
                "attack": int(row["attack"]),
                "defense": int(row["defense"]),
                "support": int(row["support"]),
                "score": int(row["score"]),
            }
            for row in db.execute(
                "SELECT a.id,a.name,a.tag,"
                "coalesce(sum(CASE WHEN l.category='attack' THEN l.points ELSE 0 END),0) AS attack,"
                "coalesce(sum(CASE WHEN l.category='defense' THEN l.points ELSE 0 END),0) AS defense,"
                "coalesce(sum(CASE WHEN l.category='support' THEN l.points ELSE 0 END),0) AS support,"
                "coalesce(sum(l.points),0) AS score FROM alliances a "
                "JOIN members m ON m.alliance_id=a.id "
                "LEFT JOIN war_score_ledger l ON l.user_id=m.user_id AND l.world_id=? "
                "GROUP BY a.id,a.name,a.tag ORDER BY score DESC,a.id",
                (world_id,),
            )
        ]

    def advance(self, db: Connection, now: int) -> int:
        """Process the earliest world event, reload, repeat; target writes stay current."""
        orbit_economy.initialize(db)
        scheduler_lag = 0
        quarantined = {
            r[0] for r in db.execute("SELECT job_id FROM job_failures WHERE attempts>=3")
        }
        while True:
            pending: list[tuple[int, str, str]] = []
            for row in db.execute("SELECT colony_id,state FROM colonies"):
                state = json.loads(row["state"])
                blocked_queues = {
                    job["kind"]
                    for job in state["jobs"]
                    if job["id"] in quarantined and job["kind"] in ("build", "research")
                }
                pending.extend(
                    (job["due"], job["id"], row["colony_id"])
                    for job in state["jobs"]
                    if job["due"] <= now
                    and job["id"] not in quarantined
                    and job["kind"] not in blocked_queues
                )
            pending.extend(
                (r["ends"], "!season:" + r["id"], "")
                for r in db.execute(
                    "SELECT id,ends FROM seasons WHERE archived=0 AND ends<=?", (now,)
                )
            )
            pending.extend(
                (r["active_at"], "!rules:" + r["id"], "")
                for r in db.execute(
                    "SELECT id,active_at FROM world_rule_rollouts "
                    "WHERE status='pending' AND active_at<=?",
                    (now,),
                )
            )
            pending.extend(
                (r["due"], "!cargo:" + r["id"], "")
                for r in db.execute(
                    "SELECT id,due FROM terra_orbit_cargo WHERE due<=? AND rule_version=? "
                    "ORDER BY due,id LIMIT 1",
                    (now, orbit_rules.VERSION),
                )
            )
            orbit = self.next_orbit_event(db, now)
            if orbit:
                pending.append((orbit["due"], orbit["id"], "@" + orbit["kind"]))
            route = db.execute(
                "SELECT id,due FROM terra_trade_routes WHERE paused=FALSE AND due<=? ORDER BY due,id LIMIT 1",
                (now,),
            ).fetchone()
            if route:
                pending.append((route["due"], "!route:" + route["id"], ""))
            convoy = db.execute(
                "SELECT offer_id,due FROM terra_market_convoys WHERE due<=? ORDER BY due,offer_id LIMIT 1",
                (now,),
            ).fetchone()
            if convoy:
                pending.append((convoy["due"], "!market:" + convoy["offer_id"], ""))
            if not pending:
                break
            due, job_id, colony_id = min(pending)
            scheduler_lag = max(scheduler_lag, now - due)
            # Catch each world's stock up only to this event's timestamp so overdue
            # raids cannot claim resources that would regenerate later.
            self.replenish_neutral_outposts(db, due)
            self.update_npc_frontiers(db, due)
            if job_id.startswith("!cargo:"):
                self.arrive_orbit_cargo(db, job_id.removeprefix("!cargo:"), due)
                continue
            if job_id.startswith("!route:"):
                self.dispatch_terra_route(db, job_id.removeprefix("!route:"), due, now)
                continue
            if job_id.startswith("!market:"):
                self.arrive_market_convoy(db, job_id.removeprefix("!market:"), due)
                continue
            if colony_id.startswith("@"):
                kind = colony_id[1:]
                failure_key = f"orbit:{kind}:{job_id}"
                try:
                    self.process_orbit_event(db, kind, job_id, due)
                except Exception as exc:
                    raise JobProcessingError(orbit["owner"], failure_key) from exc
                db.execute(
                    "DELETE FROM job_failures WHERE user_id=? AND job_id=?",
                    (orbit["owner"], failure_key),
                )
                continue
            if not colony_id:
                self.expire(db, due)
                continue
            state = self.read_colony(db, colony_id)
            try:
                self.tick(db, state, due, event_id=job_id)
            except Exception as exc:
                raise JobProcessingError(state["id"], job_id) from exc
        self.replenish_neutral_outposts(db, now)
        self.update_npc_frontiers(db, now)
        npc_camps.reset_daily_quotas(db, now)
        npc_camps.run_daily_policy(db, now)
        npc_camps.run_attack_planner(db, now)
        npc_camps.resolve_due_attacks(db, self, now)
        for row in db.execute("SELECT colony_id FROM colonies").fetchall():
            state = self.read_colony(db, row[0])
            if any(j["id"] in quarantined for j in state["jobs"]):
                continue
            self.tick(db, state, now)
        self.expire(db, now)
        self.advance_terra_inactivity(db, now)
        return scheduler_lag

    def arrive_market_convoy(self, db: Connection, offer_id: str, due: int) -> None:
        convoy = db.execute(
            "SELECT target,resource,amount FROM terra_market_convoys WHERE offer_id=?", (offer_id,)
        ).fetchone()
        if convoy:
            cargo = [0, 0, 0]
            cargo[convoy["resource"]] = convoy["amount"]
            self.systems.credit_colony(
                db, convoy["target"], cargo, "Syndikatkonvoi eingetroffen", due
            )
            db.execute("DELETE FROM terra_market_convoys WHERE offer_id=?", (offer_id,))

    def dispatch_terra_route(self, db: Connection, route_id: str, due: int, horizon: int) -> None:
        route = db.execute("SELECT * FROM terra_trade_routes WHERE id=?", (route_id,)).fetchone()
        if not route:
            return
        source = self.read_colony(db, route["source"])
        try:
            if source.get("terra_dormant") or source.get("vacation_until", 0) > due:
                raise RuleError("Die Ausgangskolonie pausiert.")
            if any(job.get("route_id") == route_id for job in source["jobs"]):
                raise RuleError("Die Träger der Route sind noch unterwegs.")
            before = list(source["resources"])
            self.produce(source, due)
            self.systems.dispatch_colony_supply(
                db,
                source,
                {
                    "key": route["target"],
                    "army": json.loads(route["army"]),
                    "resources": json.loads(route["cargo"]),
                },
                at=due,
                route_id=route_id,
            )
        except RuleError as exc:
            db.execute(
                "UPDATE terra_trade_routes SET paused=TRUE,reason=? WHERE id=?",
                (str(exc), route_id),
            )
            return
        self.systems.ledger(db, source, "terra_route_dispatch", before)
        next_due = max(
            horizon + route["interval_seconds"], due + 2 * source["jobs"][-1]["travel"] + 1
        )
        db.execute("UPDATE terra_trade_routes SET due=? WHERE id=?", (next_due, route_id))

    def next_orbit_event(self, db: Connection, now: int) -> Any:
        return db.execute(
            "SELECT e.kind,e.id,e.due,p.owner FROM ("
            "SELECT 'claim' AS kind,mission_id AS id,arrival AS due,mission_id AS colony "
            "FROM orbit_planet_claims "
            "WHERE founded_at IS NULL AND rule_version=? "
            "UNION ALL SELECT 'building',mission_id,due,mission_id FROM orbit_economy WHERE due IS NOT NULL "
            "UNION ALL SELECT 'shipyard',mission_id,due,mission_id FROM orbit_ship_orders "
            "UNION ALL SELECT 'station',colony_id,ready_at,colony_id FROM orbit_stations WHERE ready_at IS NOT NULL "
            "UNION ALL SELECT 'freight',id,due,origin FROM orbit_transports WHERE rule_version=? "
            "UNION ALL SELECT 'scout',id,due,origin FROM orbit_scouts WHERE rule_version=? "
            "UNION ALL SELECT 'expedition',id,due,origin FROM orbit_expeditions "
            "WHERE finished_at IS NULL AND rule_version=? "
            "UNION ALL SELECT 'attack',id,due,origin FROM orbit_attacks WHERE rule_version=?"
            ") e JOIN orbit_planet_claims p ON p.mission_id=e.colony "
            "WHERE e.due<=? AND NOT EXISTS (SELECT 1 FROM job_failures f "
            "WHERE f.user_id=p.owner AND f.job_id='orbit:'||e.kind||':'||e.id AND f.attempts>=3) "
            "ORDER BY e.due,e.id,e.kind LIMIT 1",
            (orbit_rules.VERSION,) * 5 + (now,),
        ).fetchone()

    def process_orbit_event(self, db: Connection, kind: str, event_id: str, due: int) -> None:
        if kind == "claim":
            claim = db.execute(
                "UPDATE orbit_planet_claims SET founded_at=arrival WHERE mission_id=? "
                "AND founded_at IS NULL RETURNING world_id,owner",
                (event_id,),
            ).fetchone()
            if claim:
                orbit_economy.initialize(db)
                self.systems.audit(
                    db,
                    "worker",
                    "orbit_colony_founded",
                    event_id,
                    world_id=claim["world_id"],
                    owner=claim["owner"],
                    arrival=due,
                )
        elif kind == "building":
            row = db.execute(
                "SELECT * FROM orbit_economy WHERE mission_id=?", (event_id,)
            ).fetchone()
            if row:
                orbit_economy.refresh(db, dict(row), due, complete_building=True)
        elif kind == "station":
            db.execute(
                "UPDATE orbit_stations SET level=level+1,ready_at=NULL "
                "WHERE colony_id=? AND ready_at<=?",
                (event_id, due),
            )
        elif kind == "shipyard":
            orbit_economy.finish_ship_orders(db, due, event_id)
        elif kind == "freight":
            orbit_transport.advance(db, due, event_id)
        elif kind == "scout":
            orbit_intel.advance(db, due, event_id)
        elif kind == "expedition":
            orbit_expedition.advance(db, due, event_id)
        elif kind == "attack":
            orbit_attack.advance(
                db,
                due,
                lambda attacker, defender, at, world: self.systems.can_attack(
                    db, attacker, defender, at, world
                ),
                event_id,
            )

    def note_terra_activity(self, db: Connection, user: str, now: int) -> None:
        db.execute(
            "INSERT INTO terra_inactivity(user_id,last_seen) VALUES (?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET last_seen=excluded.last_seen,warned_at=NULL,review_at=NULL "
            "WHERE terra_inactivity.dormant_at IS NULL "
            "AND (terra_inactivity.warned_at IS NOT NULL OR terra_inactivity.last_seen<=?)",
            (user, now, now - 3600),
        )

    def advance_terra_inactivity(self, db: Connection, now: int) -> None:
        db.execute(
            "INSERT INTO terra_inactivity(user_id,last_seen) SELECT id,? FROM users u "
            "WHERE NOT EXISTS(SELECT 1 FROM terra_inactivity i WHERE i.user_id=u.id) "
            "ON CONFLICT(user_id) DO NOTHING",
            (now,),
        )
        for account in db.execute(
            "SELECT * FROM terra_inactivity WHERE dormant_at IS NULL AND last_seen<=? "
            "AND (review_at IS NULL OR review_at<=?) "
            "ORDER BY last_seen,user_id LIMIT 50",
            (now - TERRA_INACTIVITY_SECONDS, now),
        ).fetchall():
            user = account["user_id"]
            db.execute(
                "UPDATE terra_inactivity SET review_at=? WHERE user_id=?", (now + 86400, user)
            )
            colonies = [
                self.read_colony(db, row["colony_id"])
                for row in db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? ORDER BY is_home DESC,colony_id",
                    (user,),
                )
            ]
            if not colonies:
                continue
            if account["warned_at"] is None:
                self.report(
                    colonies[0],
                    "Terra-Ruhemodus angekündigt",
                    "Nach sieben weiteren Tagen ohne Anmeldung ruhen deine Terra-Kolonien. "
                    "Bestände und Standorte bleiben erhalten und können reaktiviert werden.",
                )
                self.save(db, colonies[0])
                db.execute(
                    "UPDATE terra_inactivity SET warned_at=?,review_at=? WHERE user_id=?",
                    (now, now + TERRA_INACTIVITY_NOTICE, user),
                )
                continue
            if account["warned_at"] + TERRA_INACTIVITY_NOTICE > now or any(
                c["jobs"] for c in colonies
            ):
                continue
            if db.execute(
                "SELECT 1 FROM offers WHERE owner=? AND status='open'", (user,)
            ).fetchone():
                continue
            colony_ids = {colony["colony_id"] for colony in colonies}
            incoming = any(
                job.get("target_colony_id") in colony_ids
                or job.get("kind") in ("colony_supply", "alliance_supply", "scout")
                and job.get("key") in colony_ids
                or job.get("kind") in ("attack", "transport")
                and job.get("key") == user
                for row in db.execute("SELECT state FROM colonies WHERE user_id<>?", (user,))
                for job in json.loads(row["state"]).get("jobs", [])
            )
            if (
                incoming
                or db.execute(
                    "SELECT 1 FROM terra_orbit_cargo f JOIN colonies c ON c.colony_id=f.terra_colony "
                    "WHERE c.user_id=?",
                    (user,),
                ).fetchone()
            ):
                continue
            for colony in colonies:
                colony["terra_dormant"] = True
                self.save(db, colony)
            db.execute("UPDATE terra_inactivity SET dormant_at=? WHERE user_id=?", (now, user))
            self.systems.audit(db, "worker", "terra_dormant", user)

    def arrive_orbit_cargo(self, db: Connection, cargo_id: str, due: int) -> None:
        cargo = db.execute(
            "SELECT f.*,c.user_id,c.world_id FROM terra_orbit_cargo f "
            "JOIN colonies c ON c.colony_id=f.terra_colony WHERE f.id=?",
            (cargo_id,),
        ).fetchone()
        if not cargo:
            return
        if cargo["to_orbit"]:
            db.execute(
                "UPDATE orbit_economy SET ore_reserve=ore_reserve+? WHERE mission_id=?",
                (cargo["ore"], cargo["orbit_colony"]),
            )
        else:
            self.systems.credit_colony(
                db, cargo["terra_colony"], [0, 0, cargo["ore"]], "Orbit-Fracht eingetroffen", due
            )
        db.execute("DELETE FROM terra_orbit_cargo WHERE id=?", (cargo_id,))
        game_events.stage(
            db, identity(), cargo["user_id"], cargo["world_id"], "gateway_cargo_arrived", due
        )

    def expire(self, db: Connection, now: int) -> None:
        rule_rollouts.apply_due(db, now, self.systems.audit)
        alliance_treasury.expire(db, now)
        alliance_projects.expire(self.systems, db, now)
        for offer in db.execute(
            "SELECT * FROM offers WHERE status='open' AND expires<=?", (now,)
        ).fetchall():
            refund = [0, 0, 0]
            refund[offer["give_resource"]] = offer["give_amount"]
            colony_id = offer["colony_id"]
            if not colony_id:
                home = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (offer["owner"], offer["world_id"]),
                ).fetchone()
                colony_id = home["colony_id"] if home else None
            if colony_id:
                self.systems.credit_colony(
                    db, colony_id, refund, "Handelsangebot abgelaufen", at=now
                )
            db.execute("UPDATE offers SET status='cancelled' WHERE id=?", (offer["id"],))
        for season in db.execute(
            "SELECT * FROM seasons WHERE archived=0 AND ends<=?", (now,)
        ).fetchall():
            ranking_categories.archive_season_rankings(
                db,
                season_id=str(season["id"]),
                world_id=int(season["world_id"]),
                starts=int(season["starts"]),
                ends=int(season["ends"]),
                closed_at=now,
                regions=self.world_regions(db, int(season["world_id"])),
            )
            alliance_season.archive_season_alliances(
                db,
                season_id=str(season["id"]),
                world_id=int(season["world_id"]),
                starts=int(season["starts"]),
                ends=int(season["ends"]),
                closed_at=now,
            )
            standings = [
                dict(row)
                for row in db.execute(
                    "SELECT c.user_id AS id,u.name,SUM(c.ranking_score) AS score "
                    "FROM colonies c JOIN users u ON u.id=c.user_id WHERE c.world_id=? "
                    "GROUP BY c.user_id,u.name ORDER BY score DESC,c.user_id",
                    (season["world_id"],),
                )
            ]
            for place, standing in enumerate(standings, start=1):
                standing["score"] = int(standing["score"])
                standing["goal_reached"] = standing["score"] >= int(season["goal_score"])
                awards: list[str] = []
                if place == 1:
                    awards.append("season_champion")
                if standing["goal_reached"]:
                    awards.append("goal_achieved")
                standing["awards"] = awards
                for award in awards:
                    db.execute(
                        "INSERT INTO season_awards(season_id,user_id,award,score,created) "
                        "VALUES (?,?,?,?,?) ON CONFLICT(season_id,user_id,award) DO NOTHING",
                        (season["id"], standing["id"], award, standing["score"], now),
                    )
                if "season_champion" in awards:
                    prestige.award(
                        db,
                        str(standing["id"]),
                        f"season:{season['id']}:champion",
                        "season_champion",
                        int(season["world_id"]),
                        str(season["id"]),
                        now,
                    )
                if "goal_achieved" in awards:
                    prestige.award(
                        db,
                        str(standing["id"]),
                        f"season:{season['id']}:goal:{standing['id']}",
                        "season_goal_achieved",
                        int(season["world_id"]),
                        str(season["id"]),
                        now,
                    )
            db.execute(
                "UPDATE seasons SET archived=1,standings=? WHERE id=?",
                (json.dumps(standings), season["id"]),
            )
            db.execute(
                "UPDATE world_settings SET joinable=FALSE WHERE world_id=? AND mode='season'",
                (season["world_id"],),
            )
            self.systems.audit(
                db, "worker", "season_archived", season["id"], world_id=season["world_id"]
            )

    def ranking(self, db: Connection) -> list[dict[str, Any]]:
        return [
            {"id": str(row["id"]), "name": str(row["name"]), "score": int(row["score"])}
            for row in db.execute(
                "SELECT c.user_id AS id,u.name,SUM(c.ranking_score) AS score "
                "FROM colonies c JOIN users u ON u.id=c.user_id "
                "GROUP BY c.user_id,u.name ORDER BY score DESC,c.user_id"
            )
        ]

    def ranking_page(
        self, db: Connection, world_id: int, before_id: str | None = None
    ) -> tuple[list[dict[str, Any]], int, bool]:
        """Return one world-local page using stored scores, without reading colony JSON."""
        score_query = (
            "SELECT c.user_id AS id,u.name AS name,SUM(c.ranking_score) AS score "
            "FROM colonies c JOIN users u ON u.id=c.user_id "
            "WHERE c.world_id=? GROUP BY c.user_id,u.name"
        )
        offset = 0
        where = ""
        query_params: tuple[Any, ...] = (world_id,)
        if before_id is not None:
            cursor = db.execute(
                f"SELECT score FROM ({score_query}) AS ranking WHERE id=?",
                (world_id, before_id),
            ).fetchone()
            if cursor is None:
                raise RuleError("Ranglisteneintrag nicht gefunden.")
            cursor_score = int(cursor["score"])
            offset = (
                int(
                    db.execute(
                        f"SELECT count(*) FROM ({score_query}) AS ranking "
                        "WHERE score>? OR (score=? AND id<?)",
                        (world_id, cursor_score, cursor_score, before_id),
                    ).fetchone()[0]
                )
                + 1
            )
            where = "WHERE score<? OR (score=? AND id>?) "
            query_params = (world_id, cursor_score, cursor_score, before_id)
        rows = list(
            db.execute(
                f"SELECT id,name,score FROM ({score_query}) AS ranking "
                + where
                + "ORDER BY score DESC,id LIMIT 51",
                query_params,
            )
        )
        return [dict(row) for row in rows[:50]], offset, len(rows) > 50

    def ranking_for_world(self, db: Connection, world_id: int) -> list[dict[str, Any]]:
        return [
            {"id": str(row["id"]), "name": str(row["name"]), "score": int(row["score"])}
            for row in db.execute(
                "SELECT c.user_id AS id,u.name,SUM(c.ranking_score) AS score "
                "FROM colonies c JOIN users u ON u.id=c.user_id WHERE c.world_id=? "
                "GROUP BY c.user_id,u.name ORDER BY score DESC,c.user_id",
                (world_id,),
            )
        ]

    def player_ranking_score(self, db: Connection, user: str, world_id: int) -> int:
        row = db.execute(
            "SELECT coalesce(sum(ranking_score),0) FROM colonies WHERE user_id=? AND world_id=?",
            (user, world_id),
        ).fetchone()
        return int(row[0])

    def orbit_access(self, db: Connection, state: dict[str, Any]) -> dict[str, Any]:
        access = db.execute(
            "SELECT rule_version,pioneer_available FROM orbit_access WHERE user_id=? AND world_id=?",
            (state["id"], state["world_id"]),
        ).fetchone()
        citadel = any(
            town["tier"] == 8 and town["owner"] == state["id"]
            for town in self.world_outposts(db, state["world_id"])
        )
        research = all(
            state["tech"][key] >= orbit_rules.GATEWAY_HQ for key in ("engineering", "logistics")
        )
        costs = list(orbit_rules.GATEWAY_COST)
        if not citadel:
            costs = [gate + nav for gate, nav in zip(costs, orbit_rules.NAVIGATION_COST)]
        colonies = []
        if access:
            for record in db.execute(
                "SELECT e.*,p.galaxy,p.system_no AS system,p.slot,m.formed_at AS moon_formed_at,"
                "m.scanner_ready_at "
                "FROM orbit_economy e "
                "JOIN orbit_planet_claims p ON p.mission_id=e.mission_id "
                "LEFT JOIN orbit_moons m ON m.colony_id=e.mission_id AND m.destroyed_at IS NULL "
                "WHERE p.owner=? AND p.world_id=? ORDER BY p.galaxy,p.system_no,p.slot",
                (state["id"], state["world_id"]),
            ).fetchall():
                economy = dict(record)
                orbit_economy.refresh(db, economy, int(time.time()))
                economy["station"] = orbit_station.view(db, economy["mission_id"], int(time.time()))
                economy["resource_ledger"] = [
                    dict(row)
                    for row in db.execute(
                        "SELECT sequence,ore,ether,ore_reserve,ether_reserve,recorded_at "
                        "FROM orbit_resource_ledger WHERE colony_id=? ORDER BY sequence DESC LIMIT 10",
                        (economy["mission_id"],),
                    )
                ]
                gate = db.execute(
                    "SELECT ready_at,cooldown_until FROM orbit_jumpgates WHERE colony_id=?",
                    (economy["mission_id"],),
                ).fetchone()
                economy["jumpgate"] = dict(gate) if gate else None
                scan = db.execute(
                    "SELECT observed_at,result FROM orbit_phalanx_scans WHERE colony_id=? AND observed_at>?",
                    (economy["mission_id"], int(time.time()) - orbit_intel.PHALANX_SECONDS),
                ).fetchone()
                economy["phalanx"] = (
                    {**json.loads(scan["result"]), "observed_at": scan["observed_at"]}
                    if scan and economy["moon_formed_at"] is not None
                    else None
                )
                economy["ship_order"] = next(
                    (
                        dict(row)
                        for row in db.execute(
                            "SELECT ship,amount,due FROM orbit_ship_orders WHERE mission_id=?",
                            (economy["mission_id"],),
                        )
                    ),
                    None,
                )
                economy["ships"] = {
                    row["ship"]: row["amount"]
                    for row in db.execute(
                        "SELECT ship,amount FROM orbit_ships WHERE mission_id=? ORDER BY ship",
                        (economy["mission_id"],),
                    )
                }
                economy["wrecks"] = [
                    dict(row)
                    for row in db.execute(
                        "SELECT ship,SUM(amount) AS amount FROM orbit_wrecks "
                        "WHERE colony_id=? AND expires>? AND amount>0 GROUP BY ship ORDER BY ship",
                        (economy["mission_id"], int(time.time())),
                    )
                ]
                economy["transports"] = [
                    dict(row)
                    for row in db.execute(
                        'SELECT id,target,ore,ether,ships,due,is_returning AS "returning",recalled,salvage_report '
                        "FROM orbit_transports "
                        "WHERE origin=? ORDER BY due,id",
                        (economy["mission_id"],),
                    )
                ]
                economy["gateway_cargo"] = [
                    dict(row)
                    for row in db.execute(
                        "SELECT c.terra_colony,c.to_orbit,c.ore,c.due "
                        "FROM terra_orbit_cargo c WHERE c.orbit_colony=? ORDER BY c.due,c.id",
                        (economy["mission_id"],),
                    )
                ]
                economy["scouts"] = [
                    dict(row)
                    for row in db.execute(
                        'SELECT galaxy,system_no AS system,slot,due,is_returning AS "returning" FROM orbit_scouts '
                        "WHERE origin=? ORDER BY due,id",
                        (economy["mission_id"],),
                    )
                ]
                economy["expeditions"] = [
                    {
                        "galaxy": row["galaxy"],
                        "system": row["system_no"],
                        "slot": row["slot"],
                        "due": row["due"],
                        "returning": row["result"] is not None,
                        "result": (
                            json.loads(row["result"]) if row["finished_at"] is not None else None
                        ),
                    }
                    for row in db.execute(
                        "SELECT galaxy,system_no,slot,due,result,finished_at FROM orbit_expeditions "
                        "WHERE origin=? ORDER BY (finished_at IS NULL) DESC,due DESC,id DESC LIMIT 20",
                        (economy["mission_id"],),
                    )
                ]
                economy["attacks"] = [
                    {
                        "id": row["id"],
                        "ship": row["ship"],
                        "amount": row["amount"],
                        "due": row["due"],
                        "returning": bool(row["returning"]),
                        "recalled": bool(row["recalled"]),
                        "fuel_spent": row["fuel_spent"],
                        "seed_commitment": orbit_battle.seed_commitment(bytes.fromhex(row["seed"])),
                    }
                    for row in db.execute(
                        'SELECT id,ship,amount,due,is_returning AS "returning",recalled,fuel_spent,seed FROM orbit_attacks '
                        "WHERE origin=? ORDER BY due,id",
                        (economy["mission_id"],),
                    )
                ]
                economy["allied_wings"] = [
                    dict(row)
                    for row in db.execute(
                        'SELECT w.ship,w.amount,a.due,a.is_returning AS "returning" FROM orbit_attack_wings w '
                        "JOIN orbit_attacks a ON a.id=w.attack_id WHERE w.colony_id=? ORDER BY a.due,a.id",
                        (economy["mission_id"],),
                    )
                ]
                colonies.append(economy)
        return {
            "unlocked": access is not None,
            "special_events": (
                [
                    dict(row)
                    for row in db.execute(
                        "SELECT id,kind,ends FROM orbit_special_events WHERE world_id=? "
                        "AND starts<=? AND ends>? AND rule_version=? ORDER BY ends,id",
                        (
                            state["world_id"],
                            int(time.time()),
                            int(time.time()),
                            orbit_rules.VERSION,
                        ),
                    )
                ]
                if access
                else []
            ),
            "templates": (
                [
                    dict(row)
                    for row in db.execute(
                        "SELECT id,kind,name,ship,amount,retreat_pct FROM orbit_templates "
                        "WHERE owner=? AND world_id=? ORDER BY kind,lower(name),id LIMIT 20",
                        (state["id"], state["world_id"]),
                    )
                ]
                if access
                else []
            ),
            "alliance_attacks": (
                [
                    dict(row)
                    for row in db.execute(
                        "SELECT a.id,a.due,t.galaxy,t.system_no AS system,t.slot FROM orbit_attacks a "
                        "JOIN orbit_planet_claims t ON t.mission_id=a.target "
                        "JOIN orbit_planet_claims o ON o.mission_id=a.origin "
                        "JOIN members leader ON leader.user_id=o.owner AND leader.alliance_id=a.alliance_id "
                        "JOIN members viewer ON viewer.alliance_id=a.alliance_id AND viewer.user_id=? "
                        "WHERE t.world_id=? AND o.owner<>? AND a.is_returning=FALSE AND a.due>? "
                        "AND NOT EXISTS (SELECT 1 FROM orbit_attack_wings w "
                        "JOIN orbit_planet_claims p ON p.mission_id=w.colony_id "
                        "WHERE w.attack_id=a.id AND p.owner=?) ORDER BY a.due,a.id LIMIT 20",
                        (
                            state["id"],
                            state["world_id"],
                            state["id"],
                            int(time.time()),
                            state["id"],
                        ),
                    )
                ]
                if access
                else []
            ),
            "colonies": colonies,
            "building_costs": {key: value[0] for key, value in orbit_economy.BUILDINGS.items()},
            "building_max_level": orbit_economy.MAX_LEVEL,
            "ore_per_hour": orbit_economy.ORE_PER_HOUR,
            "fleet_supply_ether": orbit_economy.SUPPLY_ETHER,
            "fleet_supply_seconds": orbit_economy.SUPPLY_SECONDS,
            "gateway_cargo_limit": orbit_rules.GATEWAY_CARGO_LIMIT,
            "gateway_cargo_fee": orbit_rules.GATEWAY_CARGO_FEE,
            "colony_limit": orbit_rules.BASE_COLONY_LIMIT,
            "shipbuilding_ore": orbit_rules.SHIPBUILDING_ORE,
            "defense_cost": {
                "ore": orbit_rules.DEFENSE.ore_cost,
                "ether": orbit_rules.DEFENSE.ether_cost,
            },
            "scanner_cost": {"ore": orbit_intel.SCANNER_ORE, "ether": orbit_intel.SCANNER_ETHER},
            "phalanx_cost": orbit_intel.PHALANX_COST,
            "phalanx_range": orbit_intel.PHALANX_RANGE,
            "jumpgate_ore": orbit_rules.JUMPGATE_ORE,
            "jumpgate_hq": orbit_rules.JUMPGATE_HQ,
            "ammunition_costs": orbit_rules.AMMUNITION_COSTS,
            "ammunition_cap": orbit_rules.AMMUNITION_CAP,
            "ship_catalog": (
                {key: rule.model_dump() for key, rule in orbit_rules.ship_catalog().items()}
                if access
                else {}
            ),
            "pioneer_available": bool(access and access["pioneer_available"]),
            "claims": (
                [
                    dict(row)
                    for row in db.execute(
                        "SELECT galaxy,system_no AS system,slot,arrival,founded_at "
                        "FROM orbit_planet_claims WHERE owner=? AND world_id=? "
                        "ORDER BY galaxy,system_no,slot",
                        (state["id"], state["world_id"]),
                    )
                ]
                if access
                else []
            ),
            "rule_version": access["rule_version"] if access else orbit_rules.VERSION,
            "hq_required": orbit_rules.GATEWAY_HQ,
            "galaxies": orbit_rules.GALAXY_COUNT,
            "systems_per_galaxy": orbit_rules.SYSTEMS_PER_GALAXY,
            "citadel": citadel,
            "research_ready": research,
            "eligible": state["buildings"]["hq"] >= orbit_rules.GATEWAY_HQ
            and (citadel or research),
            "costs": costs,
        }

    def view(self, db: Connection, user: str) -> dict[str, Any]:
        self.note_terra_activity(db, user, int(time.time()))
        self.advance(db, int(time.time()))
        state = self.read(db, user)
        world_id = int(state["world_id"])
        state["colonies"] = [
            {
                "colony_id": str(row["colony_id"]),
                "world_id": world_id,
                "is_home": bool(row["is_home"]),
                "name": colony.get("colony_name", colony["name"]),
                "x": int(colony["x"]),
                "y": int(colony["y"]),
                "hq": int(colony["buildings"]["hq"]),
                "selected": row["colony_id"] == state["colony_id"],
            }
            for row in db.execute(
                "SELECT colony_id,is_home,state FROM colonies "
                "WHERE user_id=? AND world_id=? ORDER BY is_home DESC,colony_id LIMIT 5",
                (user, world_id),
            )
            for colony in [json.loads(row["state"])]
        ]
        state["empire_colonies"], state["empire_colonies_has_more"] = (
            self.systems.player_colonies_page(db, user)
        )
        state["colony_count"] = int(
            db.execute(
                "SELECT count(*) FROM colonies WHERE user_id=? AND world_id=?",
                (user, state["world_id"]),
            ).fetchone()[0]
        )
        state["home_designation"] = home_status(db, user, world_id, int(time.time()))
        state["colony_slot_limit"] = min(4, 1 + state["buildings"]["hq"] // 3)
        state["colonization_cost"] = [2000, 1500, 1000]
        state["pioneer_survey_discount"] = PIONEER_SETTLEMENT_DISCOUNT
        state["relocation_cost"] = list(COLONY_RELOCATION_COST)
        state["terra_energy"] = self.terra_energy(state, int(time.time()))
        state["fusion_supply_cost"] = (
            state.get("terra_energy_levels", {}).get("fusion_plant", 0)
            * FUSION_SUPPLY_ORE_PER_LEVEL
        )
        state["terra_energy_catalog"] = orbit_rules.TERRA_ENERGY_BUILDINGS
        state["terra_mission_limit"] = self.terra_mission_limit(state)
        state["warden_fortified"] = self.systems.active_warden_fortification(
            db, state, int(time.time())
        )
        faction = self.systems.world_faction(db, user, world_id)
        state["faction_unit_requirements"] = {
            key: {"research": research, "own_faction": owner == faction}
            for key, (owner, research, *_) in FACTION_UNITS.items()
        }
        combat_version = str(
            db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()[0]
        )
        combat_rules = (
            terra_combat.rules_for(combat_version)
            if terra_combat.is_supported_version(combat_version)
            else None
        )
        state["units"] = {
            key: state["units"].get(key, 0)
            for key in (combat_rules["units"] if combat_rules else UNITS)
        }
        state["terra_unit_wrecks"] = [
            dict(row)
            for row in db.execute(
                "SELECT id,unit_id AS unit,amount,expires,rule_version,rule_digest "
                "FROM terra_unit_wrecks WHERE owner_id=? AND colony_id=? AND world_id=? "
                "AND amount>0 AND expires>? ORDER BY expires,id",
                (user, state["colony_id"], world_id, int(time.time())),
            )
        ]
        state["terra_recovery_rules"] = {
            "version": terra_recovery.VERSION,
            "digest": terra_recovery.DIGEST,
            "window_seconds": int(terra_recovery.RULES["wreck_window_seconds"]),
            "loss_recovery_percent": int(terra_recovery.RULES["loss_recovery_percent"]),
            "repair_cost_percent": int(terra_recovery.RULES["repair_cost_percent"]),
            "provisional": True,
        }
        state["terra_defense"] = None
        if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
            from . import terra_defense

            defense_stacks = state.get("terra_defense_stacks", {})
            state["terra_defense"] = {
                "version": terra_defense.VERSION,
                "digest": terra_defense.DIGEST,
                "stack_rules_version": state.get("terra_defense_rules_version"),
                "stack_rules_digest": state.get("terra_defense_rules_digest"),
                "provisional": True,
                "slot_limit": terra_defense.slot_limit(int(state["buildings"].get("hq", 0))),
                "slot_usage": sum(
                    len(stack) for stack in defense_stacks.values() if isinstance(stack, list)
                ),
                "power": terra_defense.defense_power(defense_stacks),
                "stacks": defense_stacks,
                "catalog": terra_defense.RULES["objects"],
                "minefield": terra_defense.RULES["minefield"],
            }
        state["faction_research_catalog"] = {
            key: {"cost": costs, "hq": FACTION_RESEARCH_HQ, "seconds": FACTION_RESEARCH_SECONDS}
            for key, (owner, costs) in FACTION_RESEARCH.items()
            if owner == faction
        }
        state["terra_trade_routes"] = [
            dict(row)
            for row in db.execute(
                "SELECT r.id,r.target,r.due,r.paused,r.reason,r.interval_seconds,c.name_key "
                "FROM terra_trade_routes r JOIN colonies c ON c.colony_id=r.target "
                "WHERE r.source=? ORDER BY r.due,r.id",
                (state["colony_id"],),
            )
        ]
        state["syndicate_convoys"] = [
            dict(row)
            for row in db.execute(
                "SELECT f.target,f.resource,f.amount,f.due FROM terra_market_convoys f "
                "JOIN colonies c ON c.colony_id=f.target WHERE c.user_id=? AND c.world_id=? "
                "ORDER BY f.due,f.offer_id LIMIT 20",
                (user, world_id),
            )
        ]
        state["terra_prestige"] = {
            **orbit_rules.TERRA_PRESTIGE,
            "level": state.get("terra_prestige_level", 0),
            "version": orbit_rules.VERSION,
            "enabled": db.execute(
                "SELECT 1 FROM world_settings WHERE world_id=? AND terra_prestige_ruleset=?",
                (world_id, orbit_rules.VERSION),
            ).fetchone()
            is not None,
        }
        world = db.execute(
            "SELECT s.name,s.seed,s.outpost_count,s.joinable,s.settings,s.mode,"
            "s.terra_combat_ruleset,s.terra_retreat_threshold_percent,r.version,r.digest "
            "FROM world_settings s LEFT JOIN world_rulesets w ON w.world_id=s.world_id "
            "LEFT JOIN rule_catalogs r ON r.version=w.version WHERE s.world_id=?",
            (world_id,),
        ).fetchone()
        world_settings = json.loads(world["settings"] or "{}") if world else {}
        if not isinstance(world_settings, dict):
            raise RuleError("Die gespeicherten Welteinstellungen sind ungültig.")
        world_configured_crafting = world_settings.get("crafting_ruleset", "FUR-2")
        if world_configured_crafting not in ("FUR-2", crafting.RULES.version):
            raise RuleError("Der gespeicherte Fertigungsregelstand ist ungültig.")
        world_hero_ruleset = world_settings.get(heroes.RULES.enabled_key, "FUR-2")
        if world_hero_ruleset not in ("FUR-2", heroes.RULES.version):
            raise RuleError("Der gespeicherte Commander-Regelstand ist ungültig.")
        world_hero_doctrine_ruleset = world_settings.get(hero_doctrines.RULES.enabled_key, "FUR-2")
        if world_hero_doctrine_ruleset not in ("FUR-2", hero_doctrines.RULES.version):
            raise RuleError("Der gespeicherte Commander-Doktrinstand ist ungültig.")
        world_hero_respec_ruleset = world_settings.get(hero_respec.RULES.enabled_key, "FUR-2")
        if world_hero_respec_ruleset not in ("FUR-2", hero_respec.RULES.version):
            raise RuleError("Der gespeicherte Commander-Resetstand ist ungültig.")
        if (
            world_hero_respec_ruleset == hero_respec.RULES.version
            and world_hero_ruleset != heroes.RULES.version
        ):
            raise RuleError("Commander-Resets benötigen die aktivierte Heldenverwaltung.")
        state["active_world"] = {
            "id": world_id,
            "mode": world["mode"] if world else "permanent",
            "rules_version": world["version"] if world else None,
            "rules_digest": world["digest"] if world else None,
            "name": world["name"] if world else f"Welt {world_id}",
            "seed": world["seed"] if world else 504921,
            "outpost_count": world["outpost_count"] if world else 104,
            "terra_combat_ruleset": world["terra_combat_ruleset"] if world else "FUR-2",
            "crafting_ruleset": str(world_configured_crafting),
            "hero_ruleset": str(world_hero_ruleset),
            "hero_doctrine_ruleset": str(world_hero_doctrine_ruleset),
            "hero_respec_ruleset": str(world_hero_respec_ruleset),
            "npc_camps_ruleset": str(world_settings.get(npc_camps.RULESET_KEY, "FUR-2")),
            "terra_ruin_exploration_ruleset": str(
                world_settings.get("terra_ruin_exploration_ruleset", "FUR-2")
            ),
            "npc_camps_rules_digest": npc_camps.stored_rules_digest(
                db, str(world_settings.get(npc_camps.RULESET_KEY, "FUR-2"))
            ),
            "terra_retreat_threshold_percent": (
                int(world["terra_retreat_threshold_percent"]) if world else 60
            ),
        }
        state["active_world"]["unit_training_enabled"] = bool(
            combat_rules
            and combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            and combat_rules.get("unit_economy", {}).get("enabled_for_training")
        )
        state["worlds"], state["worlds_has_more"] = self.systems.world_directory_page(db, user)
        visible, last_seen = record_observations(db, user, world_id, int(time.time()))
        known = visible | set(last_seen)
        towns = [
            town for town in self.world_outposts(db, world_id) if (town["x"], town["y"]) in visible
        ]
        faction_summary: dict[str, dict[str, Any]] = {}
        for post in towns:
            if post.get("owner") is not None:
                continue
            index = int.from_bytes(
                hashlib.sha256(f"{state['active_world']['seed']}:{post['id']}".encode()).digest()[
                    :4
                ],
                "big",
            ) % len(NPC_FACTIONS)
            faction_key, faction_name = NPC_FACTIONS[index]
            entry = faction_summary.setdefault(
                faction_key,
                {"id": faction_key, "name": faction_name, "outposts": 0, "pressure": 0},
            )
            entry["outposts"] += 1
            entry["pressure"] += int(post.get("npc_pressure", 0))
        for summary_entry in faction_summary.values():
            summary_entry["threat_level"] = min(5, summary_entry["pressure"] // 100)
        state["npc_factions"] = sorted(faction_summary.values(), key=lambda item: item["id"])
        state["npc_camps"] = npc_camps.page(db, world_id, world_settings, int(time.time()))
        state["npc_attack_plans"] = npc_camps.attack_plan_page(db, world_id, user)
        state["npc_invasions"] = npc_invasions.view(
            db,
            world_id,
            int(time.time()),
            world_settings.get(npc_camps.RULESET_KEY) == npc_camps.ATTACK_RULES_VERSION,
        )
        travel = travel_times(db, (state["x"], state["y"]), world_id)
        state["_travel_times"] = travel
        state["terrain_map"] = {
            f"{row['x']}:{row['y']}": row["terrain"]
            for row in db.execute(
                "SELECT x,y,terrain FROM world_terrain WHERE world_id=?", (world_id,)
            )
            if (int(row["x"]), int(row["y"])) in known
        }
        state["terra_sector_rules"] = {
            f"{x}:{y}": kind
            for (x, y), kind in self.terra_sector_rules(db, world_id).items()
            if (x, y) in known
        }
        state["terra_ruins"] = {
            f"{x}:{y}": expires
            for (x, y), expires in self.active_terra_ruins(db, world_id).items()
            if (x, y) in visible
        }
        state["terra_ruin_targets"] = [
            {
                "id": str(row["id"]),
                "x": int(row["x"]),
                "y": int(row["y"]),
                "expires": int(row["expires"]),
                "travel_seconds": travel.get((int(row["x"]), int(row["y"]))),
            }
            for row in db.execute(
                "SELECT id,x,y,expires FROM terra_ruins WHERE world_id=? AND expires>? "
                "ORDER BY expires,id",
                (world_id, int(time.time())),
            )
            if (int(row["x"]), int(row["y"])) in visible and (int(row["x"]), int(row["y"])) in known
        ]
        state["terra_ruin_intel"] = {
            str(row["ruin_id"]): {
                "x": int(row["x"]),
                "y": int(row["y"]),
                "observed_at": int(row["observed_at"]),
                "expires_at": int(row["expires_at"]),
                "outcome": str(row["outcome"]),
            }
            for row in db.execute(
                "SELECT ruin_id,x,y,observed_at,expires_at,outcome FROM terra_ruin_intel "
                "WHERE observer_id=? AND world_id=? AND expires_at>? ORDER BY observed_at DESC,ruin_id",
                (user, world_id, int(time.time())),
            )
        }
        state["terra_dormant_sectors"] = [
            f"{row['x']}:{row['y']}"
            for row in db.execute(
                "SELECT c.x,c.y FROM colonies c JOIN terra_inactivity i ON i.user_id=c.user_id "
                "WHERE c.world_id=? AND i.dormant_at IS NOT NULL",
                (world_id,),
            )
            if (row["x"], row["y"]) in visible
        ]
        state["sector_intel"] = {
            f"{x}:{y}": sector_status(x, y, visible, last_seen)
            for y in range(64)
            for x in range(64)
        }
        for town in towns:
            town["terrain"] = state["terrain_map"][f"{town['x']}:{town['y']}"]
            town["travel_seconds"] = travel.get((town["x"], town["y"]))
            unit_catalog = self.unit_catalog_for_world(db, world_id)
            base_structure = 55 * town["tier"] ** 2
            active_ruleset = str(state["active_world"].get("terra_combat_ruleset", "FUR-2"))
            if active_ruleset == "FUR-3-TERRA-COMBAT-5" and town.get("owner") is None:
                fortification = terra_combat.rules_for(active_ruleset)[
                    "neutral_outpost_fortification"
                ]
                maximum = int(fortification["structure_per_tier_squared"]) * town["tier"] ** 2
                town["fortification_max_integrity"] = maximum
                integrity = town.get("fortification_integrity", maximum)
                base_structure = (
                    integrity if type(integrity) is int and 0 <= integrity <= maximum else maximum
                )
                town["fortification_integrity"] = base_structure
            base_defense = base_structure + sum(
                unit_catalog[k]["power"] * n
                for k, n in town.get("units", {}).items()
                if k in unit_catalog
            )
            town["defense"] = defense_with_terrain(base_defense, town["terrain"])
            if town["owner"] and town["owner"] != user:
                town["intel_level"] = "unknown"
                town.pop("units", None)
                town.pop("defense", None)
                town.pop("garrison", None)
        state["world"] = towns
        state["regions"] = []
        for region in self.world_regions(db, world_id):
            surveyed = all(
                (x, y) in known
                for y in range(region["y_min"], region["y_max"] + 1)
                for x in range(region["x_min"], region["x_max"] + 1)
            )
            visible_region = dict(region)
            visible_region["surveyed"] = surveyed
            if not surveyed:
                visible_region.update(
                    outpost_count=None,
                    leader_id=None,
                    leader_outposts=None,
                    leader_tied=False,
                    required_posts=None,
                    owner_id=None,
                    alliance_owner_id=None,
                    alliance_leader_tied=False,
                    production_bonus_percent=0,
                )
            state["regions"].append(visible_region)
        state["catalog"] = {
            "buildings": BUILDINGS,
            "tech": TECH,
            "units": UNITS,
            "terrain": {
                kind: {
                    "name": rule.name,
                    "movement_cost": rule.movement_cost,
                    "production_percent": rule.production_percent,
                    "defense_percent": rule.defense_percent,
                }
                for kind, rule in TERRAIN_RULES.items()
            },
        }
        if combat_rules and combat_version in (
            "FUR-3-TERRA-COMBAT-3",
            "FUR-3-TERRA-COMBAT-4",
            "FUR-3-TERRA-COMBAT-5",
        ):
            state["catalog"]["units"] = self.terra_unit_catalog(combat_rules)
            state["active_world"]["unit_training_enabled"] = bool(
                combat_rules.get("unit_economy", {}).get("enabled_for_training", False)
            )
        else:
            state["catalog"]["units"] = {**UNITS, **state.get("catalog_units", {})}
        state["server_time"] = int(time.time())
        state["recurring_quests"] = recurring_quests.view(db, world_id, user, state["server_time"])
        ranking, ranking_offset, ranking_has_more = self.ranking_page(db, world_id)
        state["ranking"] = ranking
        state["ranking_offset"] = ranking_offset
        state["ranking_has_more"] = ranking_has_more
        state["ranking_score"] = self.player_ranking_score(db, user, world_id)
        state["military_ranking"] = self.military_ranking_for_world(db, world_id)[:50]
        state["alliance_military_ranking"] = self.alliance_military_ranking_for_world(db, world_id)[
            :50
        ]
        state["ranking_categories"] = ranking_categories.live_rankings(
            db,
            world_id,
            self.world_regions(db, world_id),
            self.alliance_military_ranking_for_world(db, world_id),
        )
        state["military_score_audit"] = self.war_score_audit(db, user, world_id)
        state["orbit_access"] = self.orbit_access(db, state)
        self.systems.decorate(db, state)
        state["neutral_market"] = market_view(state, state["profile"]["faction"])
        state["generic_items"] = generic_item_view(state)
        crafting_enabled = crafting.enabled_in_world(db, world_id)
        state["crafting"] = crafting.view(state, crafting_enabled)
        state["recycling"] = recycling.view(state, crafting_enabled)
        state["expedition_item_drops"] = item_drops.view(crafting_enabled)
        state["expedition_rules"] = {
            "version": expeditions.RULES["version"],
            "digest": expeditions.RULES_DIGEST,
            "outcome_rolls": expeditions.RULES["outcome_rolls"],
            "outcomes": [dict(outcome) for outcome in expeditions.RULES["outcomes"]],
        }
        state["terra_boss"] = boss_raids.view(db, world_id, user, int(time.time()))
        state["npc_convoy"] = npc_convoys.view(
            db, world_id, user, (int(state["x"]), int(state["y"])), state["server_time"]
        )
        state["commander"] = heroes.view(db, user, world_id)
        state["commander_doctrines"] = hero_doctrines.view(db, world_id, state["commander"])
        state["commander_respec"] = hero_respec.view(db, user, world_id)
        state["players"] = [
            player for player in state.get("players", []) if (player["x"], player["y"]) in visible
        ]
        player_names = {player["id"]: player["name"] for player in state.get("players", [])}
        alliance_names = {
            str(alliance["id"]): str(alliance.get("tag", alliance.get("name", "")))
            for alliance in state.get("alliances", [])
        }
        for region in state["regions"]:
            region["owner_name"] = player_names.get(region["owner_id"])
            region["leader_name"] = player_names.get(region["leader_id"])
            region["alliance_owner_name"] = alliance_names.get(region["alliance_owner_id"])
        state["quests"] = self.quests(state)
        for key in ("_events", "_faction_bonus", "_region_bonus", "_travel_times"):
            state.pop(key, None)
        return state

    def command(
        self,
        db: Connection,
        user: str,
        action: str,
        payload: dict[str, Any],
        token: str,
        command_origin: CommandOrigin | None = None,
    ) -> dict[str, Any]:
        command_json = json.dumps(
            [action, payload, command_origin.model_dump() if command_origin else None],
            sort_keys=True,
        )
        signature = "sha256:" + hashlib.sha256(command_json.encode("utf-8")).hexdigest()
        previous = db.execute(
            "SELECT signature FROM commands WHERE user_id=? AND token=?", (user, token)
        ).fetchone()
        if previous:
            legacy_match = command_origin is None and previous[0] == json.dumps(
                [action, payload], sort_keys=True
            )
            if previous[0] != signature and not legacy_match:
                raise RuleError("Befehlsschlüssel bereits anders verwendet.")
            return self.view(db, user)
        self.note_terra_activity(db, user, int(time.time()))
        self.advance(db, int(time.time()))
        state = self.read(db, user)
        world_id = int(state["world_id"])
        if command_origin and (
            command_origin.world_id != state["world_id"]
            or command_origin.colony_id != state["colony_id"]
            or command_origin.rule_version != REGISTRY["version"]
        ):
            raise RuleError("Welt, Kolonie oder Regelstand des Befehls ist nicht mehr aktiv.")
        now = int(time.time())
        profile = self.systems.profile(db, user)
        if profile["banned"]:
            raise RuleError("Dieses Konto ist gesperrt.")
        if self.systems.flag(db, "maintenance") and profile["role"] != "admin":
            raise RuleError("Die Spielwelt befindet sich im Wartungsmodus.")
        if state.get("terra_dormant") and action not in (
            "terra_reactivate",
            "world_select",
            "colony_select",
            "message",
        ):
            raise RuleError("Reaktiviere zuerst deine ruhenden Terra-Kolonien.")
        if state.get("vacation_until", 0) > now and action not in ("message", "terra_reactivate"):
            raise RuleError("Während des Urlaubsmodus sind Spielbefehle gesperrt.")
        quarantined = {
            r[0] for r in db.execute("SELECT job_id FROM job_failures WHERE attempts>=3")
        }
        if any(j["id"] in quarantined for j in state["jobs"]):
            if action not in ("admin_retry", "cancel_job"):
                raise RuleError(
                    "Ein Auftrag dieser Kolonie benötigt eine Korrektur durch die Spielleitung."
                )
        else:
            self.tick(db, state, now)
        before = list(state["resources"])
        existing_job_ids = {str(job["id"]) for job in state["jobs"]}
        key = payload.get("key", "")
        if not isinstance(key, str):
            raise RuleError("Ungültiger Auftragsschlüssel.")
        job: dict[str, Any] = {"id": identity(), "kind": action, "key": key}
        if action == "terra_pioneer_survey":
            world_id = state["world_id"]
            x, y = payload.get("x"), payload.get("y")
            if (
                payload.get("world_id") != world_id
                or self.systems.world_faction(db, user, world_id) != "pioneers"
                or "adaptive_forestry" not in state.get("faction_research", [])
            ):
                raise RuleError("Die Vermessung benötigt Pionierforschung in der aktiven Welt.")
            if state.get("pioneer_survey_ready_at", 0) > now:
                raise RuleError("Die Pioniervermessung ist noch in der Abklingzeit.")
            if type(x) is not int or type(y) is not int or not 0 <= x < 64 or not 0 <= y < 64:
                raise RuleError("Ungültiges Vermessungsziel.")
            if math.hypot(x - state["x"], y - state["y"]) > PIONEER_SURVEY_RANGE + (
                4 if "long_range_colony" in state.get("faction_research", []) else 0
            ) or (x, y) not in travel_times(db, (state["x"], state["y"]), world_id):
                raise RuleError("Das Vermessungsziel liegt außerhalb der begehbaren Reichweite.")
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET observed_at=excluded.observed_at",
                (user, world_id, x, y, now),
            )
            state["pioneer_survey"] = {"x": x, "y": y, "expires": now + PIONEER_SURVEY_SECONDS}
            state["pioneer_survey_ready_at"] = now + PIONEER_SURVEY_COOLDOWN
            self.systems.audit(db, user, action, f"{x}:{y}", world_id=world_id)
        elif action == "terra_faction_research":
            rule = FACTION_RESEARCH.get(key)
            faction = self.systems.world_faction(db, user, state["world_id"])
            if not rule or faction != rule[0] or state["buildings"]["hq"] < FACTION_RESEARCH_HQ:
                raise RuleError(
                    "Diese Forschung gehört nicht zur freigeschalteten Fraktion deiner Kolonie."
                )
            if key in state.get("faction_research", []) or any(
                item["kind"] == action for item in state["jobs"]
            ):
                raise RuleError("Diese Fraktionsforschung ist bereits abgeschlossen oder läuft.")
            research_costs = rule[1]
            if any(stock < cost for stock, cost in zip(state["resources"], research_costs)):
                raise RuleError("Für die Fraktionsforschung fehlen Rohstoffe.")
            state["resources"] = [
                stock - cost for stock, cost in zip(state["resources"], research_costs)
            ]
            job.update(
                due=now + FACTION_RESEARCH_SECONDS, label=key, rules_digest=orbit_rules.DIGEST
            )
            state["jobs"].append(job)
        elif action in ("terra_route_create", "terra_route_resume", "terra_route_stop"):
            colony_id = state["colony_id"]
            if (
                payload.get("colony_id") != colony_id
                or payload.get("world_id") != state["world_id"]
            ):
                raise RuleError("Wähle die aktive Ausgangskolonie.")
            if action == "terra_route_create":
                army, cargo, hours = (
                    payload.get("army"),
                    payload.get("resources"),
                    payload.get("hours"),
                )
                if (
                    not isinstance(army, dict)
                    or not army
                    or any(
                        unit not in self.unit_catalog_for_world(db, int(state["world_id"]))
                        or type(count) is not int
                        or not 0 <= count <= 100
                        for unit, count in army.items()
                    )
                    or not 1 <= sum(army.values()) <= 100
                    or not isinstance(cargo, list)
                    or len(cargo) != 3
                    or any(type(value) is not int or not 0 <= value <= 10000 for value in cargo)
                    or not 1
                    <= sum(cargo)
                    <= self.army_transport_capacity(
                        db, int(state["world_id"]), army, int(state["tech"]["logistics"])
                    )
                    or type(hours) is not int
                    or not 1 <= hours <= 168
                ):
                    raise RuleError("Ungültige Träger, Fracht oder Taktung für die Handelsroute.")
                if (
                    key == colony_id
                    or not db.execute(
                        "SELECT 1 FROM colonies WHERE colony_id=? AND user_id=? AND world_id=?",
                        (key, user, state["world_id"]),
                    ).fetchone()
                ):
                    raise RuleError(
                        "Die Route benötigt eine andere eigene Kolonie in derselben Welt."
                    )
                if (
                    db.execute(
                        "SELECT COUNT(*) FROM terra_trade_routes WHERE source=?", (colony_id,)
                    ).fetchone()[0]
                    >= 3
                ):
                    raise RuleError("Diese Kolonie hat bereits drei Handelsrouten.")
                if not db.execute(
                    "INSERT INTO terra_trade_routes(id,source,target,army,cargo,interval_seconds,due) "
                    "VALUES (?,?,?,?,?,?,?) ON CONFLICT(source,target) DO NOTHING RETURNING id",
                    (
                        job["id"],
                        colony_id,
                        key,
                        json.dumps(army),
                        json.dumps(cargo),
                        hours * 3600,
                        now + hours * 3600,
                    ),
                ).fetchone():
                    raise RuleError("Diese Handelsroute besteht bereits.")
            elif action == "terra_route_resume":
                if not db.execute(
                    "UPDATE terra_trade_routes SET paused=FALSE,reason='',due=?+interval_seconds "
                    "WHERE id=? AND source=? AND paused=TRUE RETURNING id",
                    (now, key, colony_id),
                ).fetchone():
                    raise RuleError("Diese pausierte Route ist nicht verfügbar.")
            elif not db.execute(
                "DELETE FROM terra_trade_routes WHERE id=? AND source=? RETURNING id",
                (key, colony_id),
            ).fetchone():
                raise RuleError("Diese Handelsroute ist nicht verfügbar.")
            self.systems.audit(db, user, action, key, source=colony_id, world_id=state["world_id"])
        elif action == "admin_enable_terra_prestige":
            if profile["role"] != "admin" or payload.get("world_id") != state["world_id"]:
                raise RuleError("Nur die Spielleitung kann Prestige in der aktiven Welt freigeben.")
            if not db.execute(
                "UPDATE world_settings SET terra_prestige_ruleset=? WHERE world_id=? "
                "AND terra_prestige_ruleset IS NULL RETURNING world_id",
                (orbit_rules.VERSION, state["world_id"]),
            ).fetchone():
                raise RuleError("Für diese Welt ist bereits ein Prestige-Regelstand hinterlegt.")
            self.systems.audit(
                db, user, action, str(state["world_id"]), rules_digest=orbit_rules.DIGEST
            )
        elif action == "terra_prestige":
            if not db.execute(
                "SELECT 1 FROM world_settings WHERE world_id=? AND terra_prestige_ruleset=?",
                (state["world_id"], orbit_rules.VERSION),
            ).fetchone():
                raise RuleError("Der Prestige-Regelstand ist für diese Welt nicht freigegeben.")
            prestige_rule = orbit_rules.TERRA_PRESTIGE
            level = state.get("terra_prestige_level", 0) + 1
            if state["buildings"]["hq"] < prestige_rule["hq"] or level > prestige_rule["max_level"]:
                raise RuleError("Für diesen Prestigeausbau fehlen die Voraussetzungen.")
            if any(item["kind"] == action for item in state["jobs"]):
                raise RuleError("Ein Prestigeauftrag läuft bereits.")
            if any(stock < cost for stock, cost in zip(state["resources"], prestige_rule["cost"])):
                raise RuleError("Für den Prestigeausbau fehlen Rohstoffe.")
            state["resources"] = [
                stock - cost for stock, cost in zip(state["resources"], prestige_rule["cost"])
            ]
            job.update(
                level=level,
                due=now + prestige_rule["seconds"],
                label=f"Prestige {level}",
                rules_digest=orbit_rules.DIGEST,
            )
            state["jobs"].append(job)
        elif action == "terra_fusion_supply":
            level = state.get("terra_energy_levels", {}).get("fusion_plant", 0)
            until = state.get("fusion_supplied_until", 0)
            if not level or until >= now + FUSION_SUPPLY_SECONDS:
                raise RuleError("Die Fusionsanlage kann derzeit nicht nachversorgt werden.")
            cost = level * FUSION_SUPPLY_ORE_PER_LEVEL
            if state["resources"][2] < cost:
                raise RuleError("Für den Fusionsunterhalt fehlt Erz.")
            state["resources"][2] -= cost
            state["fusion_supplied_until"] = max(now, until) + FUSION_SUPPLY_SECONDS
        elif action == "terra_energy_build":
            energy_rule = orbit_rules.TERRA_ENERGY_BUILDINGS.get(key)
            if not energy_rule or state["buildings"]["hq"] < energy_rule["hq"]:
                raise RuleError("Dieses Terra-Spezialgebäude ist noch nicht freigeschaltet.")
            if any(item["kind"] == action for item in state["jobs"]):
                raise RuleError("Ein Terra-Spezialgebäude ist bereits im Bau.")
            level = state.get("terra_energy_levels", {}).get(key, 0) + 1
            if level > energy_rule["max_level"]:
                raise RuleError("Dieses Terra-Spezialgebäude hat die Höchststufe erreicht.")
            energy_costs = [value * level for value in energy_rule["cost"]]
            if any(stock < cost for stock, cost in zip(state["resources"], energy_costs)):
                raise RuleError("Für das Terra-Spezialgebäude fehlen Rohstoffe.")
            state["resources"] = [
                stock - cost for stock, cost in zip(state["resources"], energy_costs)
            ]
            job.update(
                level=level,
                due=now + energy_rule["seconds"] * level,
                label=f"{key} · Stufe {level}",
            )
            state["jobs"].append(job)
        elif action == "terra_reactivate":
            if not state.get("terra_dormant"):
                raise RuleError("Deine Terra-Kolonien sind bereits aktiv.")
            for row in db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND colony_id<>?",
                (user, state["colony_id"]),
            ).fetchall():
                colony = self.read_colony(db, row["colony_id"])
                colony.pop("terra_dormant", None)
                colony["last"] = now
                self.save(db, colony)
            state.pop("terra_dormant", None)
            state["last"] = now
            db.execute(
                "UPDATE terra_inactivity SET last_seen=?,warned_at=NULL,dormant_at=NULL,review_at=NULL "
                "WHERE user_id=?",
                (now, user),
            )
            self.systems.audit(db, user, action, user)
        elif action == "orbit_unlock":
            access = self.orbit_access(db, state)
            if access["unlocked"]:
                raise RuleError("Der Orbit-Zugang dieser Welt ist bereits freigeschaltet.")
            if not access["eligible"]:
                raise RuleError(
                    "Der Orbit-Zugang benötigt Kommandozentrale und Zitadelle oder Forschung."
                )
            unlock_costs = access["costs"]
            if any(stock < price for stock, price in zip(state["resources"], unlock_costs)):
                raise RuleError("Die Materialien für den Orbit-Zugang fehlen.")
            state["resources"] = [
                stock - price for stock, price in zip(state["resources"], unlock_costs)
            ]
            db.execute(
                "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) "
                "VALUES (?,?,?,?)",
                (user, state["world_id"], orbit_rules.VERSION, now),
            )
            self.systems.audit(
                db,
                user,
                action,
                str(state["world_id"]),
                world_id=state["world_id"],
                costs=unlock_costs,
                rules_digest=orbit_rules.DIGEST,
            )
        elif action in ("orbit_import_ore", "orbit_export_ore"):
            world_id = state["world_id"]
            ore = payload.get("orbit_ore")
            if (
                payload.get("world_id") != world_id
                or type(ore) is not int
                or not 1 <= ore <= orbit_rules.GATEWAY_CARGO_LIMIT
            ):
                raise RuleError("Ungültige Welt oder Erzmenge für die Gateway-Fracht.")
            try:
                colony = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            to_orbit = action == "orbit_import_ore"
            cost = ore + orbit_rules.GATEWAY_CARGO_FEE
            if to_orbit:
                if state["resources"][2] < cost:
                    raise RuleError("Für Fracht und Startgebühr fehlt Terra-Erz.")
                state["resources"][2] -= cost
            else:
                orbit_economy.refresh(db, colony, now)
                if colony["ore"] < cost:
                    raise RuleError("Für Fracht und Startgebühr fehlt Orbit-Erz.")
                db.execute(
                    "UPDATE orbit_economy SET ore=ore-? WHERE mission_id=?",
                    (cost, colony["mission_id"]),
                )
            distance = orbit_rules.planet_index(
                colony["galaxy"], colony["system_no"], colony["slot"]
            )
            travel, _, _ = orbit_rules.quote_travel({"freighter": 1}, distance)
            due = now + orbit_rules.GATEWAY_TRANSFER_SECONDS + travel
            if not db.execute(
                "INSERT INTO terra_orbit_cargo(id,terra_colony,orbit_colony,to_orbit,ore,due,rule_version) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(terra_colony,orbit_colony) DO NOTHING RETURNING id",
                (
                    job["id"],
                    state["colony_id"],
                    colony["mission_id"],
                    to_orbit,
                    ore,
                    due,
                    orbit_rules.VERSION,
                ),
            ).fetchone():
                raise RuleError("Auf dieser Gateway-Route ist bereits Fracht unterwegs.")
            self.systems.audit(
                db,
                user,
                action,
                job["id"],
                world_id=world_id,
                terra_colony=state["colony_id"],
                orbit_colony=colony["mission_id"],
                ore=ore,
                fee=orbit_rules.GATEWAY_CARGO_FEE,
                due=due,
            )
        elif action in ("orbit_build_jumpgate", "orbit_jump"):
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            try:
                colony = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                if action == "orbit_build_jumpgate":
                    orbit_jumpgate.build(db, colony, state["buildings"]["hq"], now)
                else:
                    orbit_economy.require_supply(colony, now)
                    jump_destination = orbit_transport.owned_colony(
                        db, user, world_id, required_payload_text(payload, "orbit_target")
                    )
                    orbit_jumpgate.jump(
                        db,
                        colony["mission_id"],
                        jump_destination["mission_id"],
                        key,
                        required_payload_int(payload, "count"),
                        now,
                    )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(
                db,
                user,
                action,
                colony["mission_id"],
                world_id=world_id,
                destination=payload.get("orbit_target"),
                ship=key,
                count=payload.get("count"),
            )
        elif action.startswith("orbit_station_"):
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            try:
                colony = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                orbit_station.command(
                    db,
                    colony,
                    action,
                    key,
                    required_payload_int(payload, "count", minimum=0, default=0),
                    now,
                )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(db, user, action, colony["mission_id"], world_id=world_id)
        elif action in (
            "orbit_save_fleet_template",
            "orbit_save_shipyard_template",
            "orbit_delete_template",
        ):
            world_id = state["world_id"]
            if (
                payload.get("world_id") != world_id
                or not db.execute(
                    "SELECT 1 FROM orbit_access WHERE user_id=? AND world_id=? AND rule_version=?",
                    (user, world_id, orbit_rules.VERSION),
                ).fetchone()
            ):
                raise RuleError("Die Orbit-Vorlagen dieser Welt sind nicht verfügbar.")
            if action == "orbit_delete_template":
                if not db.execute(
                    "DELETE FROM orbit_templates WHERE id=? AND owner=? AND world_id=? RETURNING id",
                    (key, user, world_id),
                ).fetchone():
                    raise RuleError("Diese Orbit-Vorlage ist nicht verfügbar.")
            else:
                kind = "fleet" if action == "orbit_save_fleet_template" else "shipyard"
                name = self.systems.text(payload, "name", 2, 32)
                amount = payload.get("count")
                retreat = payload.get("retreat_pct")
                if (
                    key not in orbit_rules.ship_catalog()
                    or type(amount) is not int
                    or not 1 <= amount <= 100
                ):
                    raise RuleError("Ungültige Schiffsklasse oder Stückzahl.")
                if retreat is not None and (
                    kind != "fleet" or type(retreat) is not int or not 10 <= retreat <= 100
                ):
                    raise RuleError("Ungültige Rückzugsschwelle für diese Vorlage.")
                if (
                    db.execute(
                        "SELECT COUNT(*) FROM orbit_templates WHERE owner=? AND world_id=?",
                        (user, world_id),
                    ).fetchone()[0]
                    >= 20
                ):
                    raise RuleError("Das Limit von 20 Orbit-Vorlagen pro Welt ist erreicht.")
                if not db.execute(
                    "INSERT INTO orbit_templates(id,owner,world_id,kind,name,ship,amount,retreat_pct) "
                    "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING RETURNING id",
                    (job["id"], user, world_id, kind, name, key, amount, retreat),
                ).fetchone():
                    raise RuleError("Dieser Vorlagenname ist bereits vergeben.")
        elif action == "admin_orbit_event":
            if profile["role"] != "admin" or payload.get("world_id") != state["world_id"]:
                raise RuleError(
                    "Nur die Spielleitung kann Orbit-Ereignisse in der aktiven Welt starten."
                )
            try:
                orbit_expedition.start_event(db, job["id"], state["world_id"], key, now)
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(
                db,
                user,
                action,
                job["id"],
                world_id=state["world_id"],
                event_kind=key,
                rules_digest=orbit_rules.DIGEST,
            )
        elif action == "orbit_recall_attack":
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            try:
                origin = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                orbit_attack.recall(db, origin["mission_id"], key, now)
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(db, user, action, key, world_id=world_id)
        elif action == "orbit_join_attack":
            world_id = state["world_id"]
            member = self.systems.member(db, user)
            if payload.get("world_id") != world_id or not member:
                raise RuleError("Dieser Orbit-Verband ist nicht verfügbar.")
            try:
                origin = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                orbit_transport.require_fleet_slot(db, user, world_id)
                orbit_attack.join(
                    db,
                    required_payload_text(payload, "orbit_target"),
                    origin,
                    user,
                    world_id,
                    member["alliance_id"],
                    key,
                    required_payload_int(payload, "count"),
                    now,
                    lambda attacker, defender, due, world: self.systems.can_attack(
                        db, attacker, defender, due, world
                    ),
                )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(
                db, user, action, job["id"], world_id=world_id, attack=payload.get("orbit_target")
            )
        elif action in (
            "orbit_scout",
            "orbit_attack",
            "orbit_destroy_moon",
            "orbit_build_scanner",
            "orbit_expedition",
            "orbit_phalanx_scan",
            "orbit_alliance_attack",
        ):
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            try:
                origin = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                coordinates = (
                    required_orbit_coordinates(payload)
                    if action != "orbit_build_scanner"
                    else (0, 0, 0)
                )
                if action not in ("orbit_build_scanner", "orbit_phalanx_scan"):
                    orbit_transport.require_fleet_slot(db, user, world_id)
                if action == "orbit_scout":
                    orbit_intel.launch(db, job["id"], origin, *coordinates, now)
                elif action == "orbit_build_scanner":
                    orbit_intel.build_scanner(db, origin, now)
                elif action == "orbit_phalanx_scan":
                    orbit_intel.phalanx_scan(db, origin, user, world_id, coordinates, now)
                elif action == "orbit_expedition":
                    orbit_expedition.launch(
                        db,
                        job["id"],
                        origin,
                        coordinates,
                        required_payload_int(payload, "count"),
                        now,
                        world=world_id,
                        special_event=payload.get("orbit_target"),
                    )
                else:
                    member = (
                        self.systems.member(db, user) if action == "orbit_alliance_attack" else None
                    )
                    if action == "orbit_alliance_attack" and not member:
                        raise ValueError("Ein Orbit-Verband benötigt eine Allianz.")
                    orbit_attack.launch(
                        db,
                        job["id"],
                        origin,
                        user,
                        world_id,
                        coordinates,
                        key,
                        required_payload_int(payload, "count"),
                        now,
                        lambda attacker, defender, due, world: self.systems.can_attack(
                            db, attacker, defender, due, world
                        ),
                        destroy_moon=action == "orbit_destroy_moon",
                        alliance_id=member["alliance_id"] if member else None,
                        retreat_pct=payload.get("retreat_pct"),
                        lances=payload.get("lances", 0),
                    )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(db, user, action, job["id"], world_id=world_id)
        elif action in (
            "orbit_transport",
            "orbit_collect_reserve",
            "orbit_recall_transport",
            "orbit_salvage",
            "orbit_fleet_supply",
        ):
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            try:
                origin = orbit_transport.owned_colony(
                    db, user, world_id, required_payload_text(payload, "colony_id")
                )
                if action == "orbit_collect_reserve":
                    orbit_transport.collect(db, origin, now)
                elif action == "orbit_fleet_supply":
                    orbit_economy.renew_supply(db, origin, now)
                elif action == "orbit_recall_transport":
                    orbit_transport.recall(db, origin["mission_id"], key, now)
                elif action == "orbit_salvage":
                    target = orbit_transport.salvage_target(db, key, user, world_id, now)
                    orbit_transport.require_fleet_slot(db, user, world_id)
                    orbit_transport.launch(
                        db,
                        job["id"],
                        origin,
                        target,
                        required_payload_int(payload, "count"),
                        0,
                        0,
                        now,
                        salvage_report=key,
                    )
                else:
                    target = orbit_transport.owned_colony(db, user, world_id, key)
                    orbit_transport.require_fleet_slot(db, user, world_id)
                    orbit_transport.launch(
                        db,
                        job["id"],
                        origin,
                        target,
                        required_payload_int(payload, "count"),
                        required_payload_int(payload, "orbit_ore", minimum=0, maximum=200000),
                        required_payload_int(payload, "orbit_ether", minimum=0, maximum=200000),
                        now,
                    )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(
                db,
                user,
                action,
                job["id"],
                world_id=world_id,
                origin=origin["mission_id"],
                orbit_target=key,
                ore=payload.get("orbit_ore", 0),
                ether=payload.get("orbit_ether", 0),
            )
        elif action in (
            "orbit_build",
            "orbit_research_shipbuilding",
            "orbit_build_ships",
            "orbit_build_defense",
            "orbit_repair_wrecks",
            "orbit_build_ammunition",
        ):
            economy = db.execute(
                "SELECT e.* FROM orbit_economy e JOIN orbit_planet_claims p "
                "ON p.mission_id=e.mission_id WHERE p.owner=? AND p.world_id=? "
                "AND p.mission_id=? AND p.rule_version=?",
                (user, state["world_id"], payload.get("colony_id"), orbit_rules.VERSION),
            ).fetchone()
            if not economy or payload.get("world_id") != state["world_id"]:
                raise RuleError("Diese Orbit-Kolonie ist nicht verfügbar.")
            try:
                if action == "orbit_build":
                    orbit_economy.build(db, dict(economy), key, now)
                elif action == "orbit_research_shipbuilding":
                    orbit_economy.research_shipbuilding(db, dict(economy), now)
                elif action == "orbit_build_defense":
                    orbit_economy.build_defense(db, dict(economy), now)
                elif action == "orbit_build_ammunition":
                    orbit_economy.build_ammunition(
                        db,
                        dict(economy),
                        key,
                        required_payload_int(payload, "count", maximum=orbit_rules.AMMUNITION_CAP),
                        now,
                    )
                else:
                    orbit_economy.order_ships(
                        db,
                        dict(economy),
                        key,
                        required_payload_int(payload, "count"),
                        now,
                        repair=action == "orbit_repair_wrecks",
                    )
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            self.systems.audit(
                db, user, action, economy["mission_id"], world_id=state["world_id"], building=key
            )
        elif action == "orbit_colonize":
            world_id = state["world_id"]
            if payload.get("world_id") != world_id:
                raise RuleError("Diese Welt ist nicht aktiv.")
            galaxy, system, slot = (payload.get(key) for key in ("galaxy", "system", "slot"))
            if type(galaxy) is not int or type(system) is not int or type(slot) is not int:
                raise RuleError("Ungültige Orbit-Koordinaten.")
            try:
                orbit_transport.require_fleet_slot(db, user, world_id)
                destination_index = orbit_rules.planet_index(galaxy, system, slot)
            except ValueError as exc:
                raise RuleError(str(exc)) from exc
            claim_count = db.execute(
                "SELECT COUNT(*) FROM orbit_planet_claims WHERE owner=? AND world_id=?",
                (user, world_id),
            ).fetchone()[0]
            if claim_count >= orbit_rules.BASE_COLONY_LIMIT:
                raise RuleError("Das Orbit-Kolonielimit ist erreicht.")
            origin_id = payload.get("colony_id")
            if origin_id is not None:
                origin = db.execute(
                    "SELECT e.*,p.galaxy,p.system_no,p.slot FROM orbit_economy e "
                    "JOIN orbit_planet_claims p ON p.mission_id=e.mission_id "
                    "WHERE p.owner=? AND p.world_id=? AND p.mission_id=? AND p.rule_version=?",
                    (user, world_id, origin_id, orbit_rules.VERSION),
                ).fetchone()
                if not origin:
                    raise RuleError("Diese Orbit-Kolonie ist nicht verfügbar.")
                origin_index = orbit_rules.planet_index(
                    origin["galaxy"], origin["system_no"], origin["slot"]
                )
                if destination_index == origin_index:
                    raise RuleError("Das Ziel muss von der Startkolonie verschieden sein.")
                duration, fuel, _ = orbit_rules.quote_travel(
                    {"colony_ship": 1}, abs(destination_index - origin_index)
                )
                economy = dict(origin)
                try:
                    orbit_economy.require_supply(economy, now)
                except ValueError as exc:
                    raise RuleError(str(exc)) from exc
                orbit_economy.refresh(db, economy, now)
                if economy["ether"] < fuel:
                    raise RuleError("Für diesen Flug fehlt Äther.")
                if not db.execute(
                    "UPDATE orbit_ships SET amount=amount-1 "
                    "WHERE mission_id=? AND ship='colony_ship' AND amount>=1 RETURNING amount",
                    (origin_id,),
                ).fetchone():
                    raise RuleError("In dieser Kolonie ist kein Kolonieschiff verfügbar.")
                db.execute(
                    "UPDATE orbit_economy SET ether=ether-? WHERE mission_id=?", (fuel, origin_id)
                )
            elif not db.execute(
                "UPDATE orbit_access SET pioneer_available=FALSE "
                "WHERE user_id=? AND world_id=? AND rule_version=? AND pioneer_available=TRUE "
                "RETURNING user_id",
                (user, world_id, orbit_rules.VERSION),
            ).fetchone():
                raise RuleError("Für diese Welt ist kein Pionierschiff verfügbar.")
            else:
                duration, _, _ = orbit_rules.quote_travel({"colony_ship": 1}, destination_index)
                fuel = 0
            if not db.execute(
                "INSERT INTO orbit_planet_claims "
                "(world_id,galaxy,system_no,slot,owner,mission_id,rule_version,arrival) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(world_id,galaxy,system_no,slot) DO NOTHING "
                "RETURNING mission_id",
                (
                    world_id,
                    galaxy,
                    system,
                    slot,
                    user,
                    job["id"],
                    orbit_rules.VERSION,
                    now + duration,
                ),
            ).fetchone():
                raise RuleError("Dieser Orbit-Platz ist derzeit nicht verfügbar.")
            self.systems.audit(
                db,
                user,
                action,
                job["id"],
                world_id=world_id,
                coordinates=[galaxy, system, slot],
                arrival=now + duration,
                origin_colony_id=origin_id,
                ether_spent=fuel,
                rules_digest=orbit_rules.DIGEST,
            )
        elif action == "cancel_job":
            queued = next((item for item in state["jobs"] if item["id"] == key), None)
            if queued and queued["kind"] == "terra_repair":
                if (
                    queued.get("repair_rules_version") != terra_recovery.VERSION
                    or queued.get("repair_rules_digest") != terra_recovery.DIGEST
                    or not isinstance(queued.get("costs"), list)
                    or len(queued["costs"]) != 3
                    or any(type(value) is not int or value < 0 for value in queued["costs"])
                ):
                    raise RuleError(
                        "Der Reparaturauftrag besitzt keinen gültigen Erstattungsstand."
                    )
                restored = db.execute(
                    "UPDATE terra_unit_wrecks SET amount=amount+? WHERE id=? AND owner_id=? "
                    "AND colony_id=? AND world_id=? AND rule_version=? "
                    "AND rule_digest=? RETURNING id",
                    (
                        int(queued["count"]),
                        str(queued["wreck_id"]),
                        user,
                        state["colony_id"],
                        int(state["world_id"]),
                        terra_recovery.VERSION,
                        terra_recovery.DIGEST,
                    ),
                ).fetchone()
                if not restored:
                    raise RuleError("Das Wrack ist abgelaufen oder nicht mehr verfügbar.")
                cap = 2000 + state["buildings"]["storage"] * 2000
                reserve = state.setdefault("reserve", [0, 0, 0])
                for index, amount in enumerate(queued["costs"]):
                    total = state["resources"][index] + amount
                    reserve[index] += max(0, total - cap)
                    state["resources"][index] = min(cap, total)
                state["jobs"] = [item for item in state["jobs"] if item["id"] != key]
                self.report(
                    state,
                    "Reparatur abgebrochen",
                    f"{queued['label']}: Wrackbestand und Reparaturkosten wurden vollständig erstattet.",
                )
                self.systems.audit(
                    db,
                    user,
                    "terra_repair_cancelled",
                    key,
                    wreck_id=queued["wreck_id"],
                    unit=queued["unit"],
                    count=queued["count"],
                    refund=queued["costs"],
                    rules_version=terra_recovery.VERSION,
                    rules_digest=terra_recovery.DIGEST,
                )
            elif queued and queued["kind"] == "craft":
                refund = crafting.cancel(state, key, now)
                self.report(
                    state,
                    "Fertigung abgebrochen",
                    f"{refund['recipe_id']}: Eingaben wurden zurückgegeben; Übermengen liegen im Reserve-Lager.",
                )
                self.systems.audit(
                    db,
                    user,
                    "craft_cancelled",
                    key,
                    **refund,
                    rules_version=crafting.RULES.version,
                    rules_hash=crafting.RULE_HASH,
                )
            elif not queued or queued["kind"] not in ("build", "research"):
                raise RuleError("Dieser Bau- oder Forschungsauftrag kann nicht abgebrochen werden.")
            else:
                kind, target = queued["kind"], queued["key"]
                catalog = BUILDINGS if kind == "build" else TECH
                section = "buildings" if kind == "build" else "tech"
                if target not in catalog:
                    raise RuleError(
                        "Der gespeicherte Auftrag ist ungültig und kann nicht abgebrochen werden."
                    )
                duration = queued.get("duration")
                if type(duration) is not int or duration < 1:
                    level = state[section].get(target, 0)
                    duration = (
                        self.construction_duration(state, level + 1)
                        if kind == "build"
                        else 12 * (level + 1)
                    )
                refund_costs = queued.get("costs")
                if (
                    not isinstance(refund_costs, list)
                    or len(refund_costs) != 3
                    or any(type(v) is not int for v in refund_costs)
                ):
                    level = state[section].get(target, 0)
                    refund_costs = [int(value) * (level + 1) for value in catalog[target]["cost"]]
                due = queued.get("due")
                if type(due) is not int:
                    raise RuleError("Der gespeicherte Auftrag hat keine gültige Endzeit.")
                waiting = bool(queued.get("queued", False))
                remaining = duration if waiting else max(0, due - now)
                refund_cost_vector = [cost * remaining // duration for cost in refund_costs]
                cap = 2000 + state["buildings"]["storage"] * 2000
                reserve = state.setdefault("reserve", [0, 0, 0])
                for index, amount in enumerate(refund_cost_vector):
                    total = state["resources"][index] + amount
                    reserve[index] += max(0, total - cap)
                    state["resources"][index] = min(cap, total)
                state["jobs"] = [item for item in state["jobs"] if item["id"] != key]
                repricing_refund = self.replan_upgrade_queue(state, kind, now)
                refund_costs_final = [
                    amount + repricing_refund[index]
                    for index, amount in enumerate(refund_cost_vector)
                ]
                self.report(
                    state,
                    "Auftrag abgebrochen",
                    f"{queued['label']}: Erstattung Holz {refund_costs_final[0]}, Stein {refund_costs_final[1]}, Erz {refund_costs_final[2]}.",
                )
                self.systems.audit(
                    db,
                    user,
                    "job_cancelled",
                    key,
                    job_kind=kind,
                    job_key=target,
                    refund=refund_costs_final,
                    duration=duration,
                    remaining=remaining,
                    was_queued=waiting,
                )
        elif action == "queue_move":
            direction = payload.get("direction")
            if direction not in ("up", "down"):
                raise RuleError("Wähle eine gültige Warteschlangenrichtung.")
            queued = next((item for item in state["jobs"] if item["id"] == key), None)
            if (
                not queued
                or queued["kind"] not in ("build", "research")
                or not queued.get("queued", False)
            ):
                raise RuleError("Nur wartende Bau- und Forschungsaufträge lassen sich verschieben.")
            kind = queued["kind"]
            queue = sorted(
                (item for item in state["jobs"] if item["kind"] == kind),
                key=lambda item: (int(item.get("queue_order", -1)), int(item["due"])),
            )
            position = next(index for index, item in enumerate(queue) if item["id"] == key)
            neighbor = position - 1 if direction == "up" else position + 1
            if neighbor < 1 or neighbor >= len(queue):
                raise RuleError(
                    "Der Auftrag kann in diese Richtung nicht weiter verschoben werden."
                )
            if queue[position]["key"] == queue[neighbor]["key"]:
                raise RuleError(
                    "Gleiche Gebäude- oder Forschungsstufen können nicht vertauscht werden."
                )
            queue[position], queue[neighbor] = queue[neighbor], queue[position]
            for order, item in enumerate(queue):
                item["queue_order"] = order
            self.replan_upgrade_queue(state, kind, now)
            self.systems.audit(
                db,
                user,
                "job_queue_moved",
                key,
                job_kind=kind,
                direction=direction,
                queue_order=neighbor,
            )
            self.report(state, "Warteschlange geändert", f"{queued['label']} wurde verschoben.")
        elif action in ("build", "research", "train"):
            same_kind = [j for j in state["jobs"] if j["kind"] == action]
            if action == "train" and same_kind:
                raise RuleError("Diese Warteschlange ist bereits belegt.")
            if action in ("build", "research") and len(same_kind) >= 5:
                raise RuleError("Diese Warteschlange ist auf fünf Aufträge begrenzt.")
            world_row = db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (state["world_id"],),
            ).fetchone()
            active_combat_version = str(world_row[0]) if world_row else "FUR-2"
            active_combat_rules = (
                terra_combat.rules_for(active_combat_version)
                if terra_combat.is_supported_version(active_combat_version)
                else None
            )
            dynamic_units = (
                self.terra_unit_catalog(active_combat_rules) if active_combat_rules else UNITS
            )
            catalog = (
                BUILDINGS if action == "build" else TECH if action == "research" else dynamic_units
            )
            if key not in catalog:
                raise RuleError("Unbekannter Auftrag.")
            if action == "train" and key not in UNITS:
                if (
                    not active_combat_rules
                    or active_combat_version not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
                    or not active_combat_rules["unit_economy"].get("enabled_for_training")
                    or key not in active_combat_rules["units"]
                    or key == "outpost_fortification"
                ):
                    raise RuleError(
                        "Diese Einheit ist in dieser Welt nicht zur Ausbildung freigegeben."
                    )
                roster = active_combat_rules["units"]
                held = sum(
                    int(state["units"].get(unit, 0))
                    for unit in roster
                    if unit not in UNITS and unit != "outpost_fortification"
                )
                queued_count = sum(
                    int(item.get("count", 0))
                    for item in state["jobs"]
                    if item["kind"] == "train" and item.get("rules_digest") is not None
                )
                if held + queued_count + int(payload.get("count", 1)) > int(
                    active_combat_rules["unit_economy"]["maximum_units_per_colony"]
                ):
                    raise RuleError("Die Einheitenobergrenze dieser Kolonie wäre überschritten.")
            if action == "train" and key in FACTION_UNITS:
                faction, research, *_ = FACTION_UNITS[key]
                if self.systems.world_faction(
                    db, user, state["world_id"]
                ) != faction or research not in state.get("faction_research", []):
                    raise RuleError(
                        "Diese Einheit erfordert ihre Fraktion und deren Spezialforschung."
                    )
            item = catalog[key]
            levels = state["buildings" if action == "build" else "tech"]
            level = levels.get(key, 0) + sum(1 for queued in same_kind if queued["key"] == key)
            if action != "train" and level >= 10:
                raise RuleError("Maximalstufe 10 erreicht.")
            requirements = item["requirements"]
            if (
                action == "train"
                and active_combat_rules is not None
                and key in active_combat_rules["units"]
            ):
                # World faction unlocks are evaluated by the existing faction gate above.
                requirements = {
                    "buildings": dict(requirements["buildings"]),
                    "tech": {
                        technology: required_level
                        for technology, required_level in requirements["tech"].items()
                        if key not in FACTION_UNITS
                    },
                }
            for building, required_level in requirements["buildings"].items():
                if int(state["buildings"].get(building, 0)) < int(required_level):
                    building_name = BUILDINGS[building]["name"]
                    if action == "research" and building == "lab":
                        raise RuleError("Baue zuerst ein Forschungslabor.")
                    raise RuleError(f"Benötigt {building_name} Stufe {required_level}.")
            for technology, required_level in requirements["tech"].items():
                if int(state["tech"].get(technology, 0)) < int(required_level):
                    raise RuleError(
                        f"Benötigt Forschung {TECH[technology]['name']} Stufe {required_level}."
                    )
            count = payload.get("count", 1) if action == "train" else 1
            if type(count) is not int or not 1 <= count <= 100:
                raise RuleError("Wähle 1 bis 100 Einheiten.")
            order_costs = [int(c) * (level + 1) * count for c in item["cost"]]
            if any(a < b for a, b in zip(state["resources"], order_costs)):
                raise RuleError("Nicht genügend Rohstoffe.")
            state["resources"] = [a - b for a, b in zip(state["resources"], order_costs)]
            duration = (
                self.construction_duration(state, level + 1)
                if action == "build"
                else 12 * (level + 1) if action == "research" else count * int(item["time"])
            )
            if action in ("build", "research"):
                queue = sorted(same_kind, key=lambda queued: int(queued.get("queue_order", -1)))
                for queue_position, queued in enumerate(queue):
                    queued["queue_order"] = queue_position
                queue_order = len(queue)
                starts_at = int(queue[-1]["due"]) if queue else now
                job.update(
                    due=starts_at + duration,
                    started_at=starts_at,
                    duration=duration,
                    costs=order_costs,
                    rule_snapshot={
                        "version": str(REGISTRY["version"]),
                        "digest": RULES_DIGEST,
                        "base_cost": [int(value) for value in item["cost"]],
                        "formula": "linear-target-level-v1",
                    },
                    target_level=level + 1,
                    queued=bool(queue),
                    queue_order=queue_order,
                    label=item["name"],
                    count=count,
                )
            else:
                job.update(due=now + duration, label=item["name"], count=count)
                if action == "train" and key not in UNITS and active_combat_rules:
                    job.update(
                        rules_version=active_combat_version,
                        rules_digest=terra_combat.RULESET_DIGESTS[active_combat_version],
                        unit_cost=list(item["cost"]),
                        formula="per-unit-cost-and-time-v1",
                    )
            state["jobs"].append(job)
            if action in ("build", "research"):
                self.replan_upgrade_queue(state, action, now)
        elif action == "terra_repair_units":
            world_id = int(state["world_id"])
            world_rules = db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()
            if (
                payload.get("world_id") != world_id
                or payload.get("colony_id") != state["colony_id"]
                or not world_rules
                or str(world_rules["terra_combat_ruleset"])
                not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            ):
                raise RuleError(
                    "Terra-Reparaturen sind nur in einer aktiven COMBAT-4/5-Kolonie möglich."
                )
            if any(item["kind"] == "terra_repair" for item in state["jobs"]):
                raise RuleError("Die Reparaturwerft bearbeitet bereits einen Auftrag.")
            wreck_id = payload.get("wreck_id")
            if not isinstance(wreck_id, str) or not wreck_id:
                raise RuleError("Wähle ein gültiges Wrack aus.")
            wreck = db.execute(
                "SELECT id,unit_id,amount,expires,rule_version,rule_digest FROM terra_unit_wrecks "
                "WHERE id=? AND owner_id=? AND colony_id=? AND world_id=? AND amount>0 "
                "AND expires>?",
                (wreck_id, user, state["colony_id"], world_id, now),
            ).fetchone()
            if (
                not wreck
                or str(wreck["rule_version"]) != terra_recovery.VERSION
                or str(wreck["rule_digest"]) != terra_recovery.DIGEST
            ):
                raise RuleError("Dieses Wrack ist abgelaufen oder gehört nicht zu dieser Kolonie.")
            count = payload.get("count")
            if type(count) is not int or not 1 <= count <= int(wreck["amount"]):
                raise RuleError("Die Reparaturanzahl überschreitet den verfügbaren Wrackbestand.")
            if (
                db.execute(
                    "SELECT 1 FROM colonies WHERE colony_id=? AND user_id=?",
                    (state["colony_id"], user),
                ).fetchone()
                is None
            ):
                raise RuleError("Diese Kolonie gehört nicht zu deinem Konto.")
            combat_version = str(world_rules["terra_combat_ruleset"])
            combat_rules = terra_combat.rules_for(combat_version)
            unit = str(wreck["unit_id"])
            profile = combat_rules["units"].get(unit)
            if not profile or unit == "outpost_fortification":
                raise RuleError("Für diesen Einheitentyp gibt es keine Reparaturregel.")
            required_barracks = int(profile["prerequisites"]["buildings"].get("barracks", 1))
            if int(state["buildings"].get("barracks", 0)) < required_barracks:
                raise RuleError(
                    f"Für diese Reparatur wird Kaserne Stufe {required_barracks} benötigt."
                )
            if int(state["units"].get(unit, 0)) + count > int(
                combat_rules["unit_economy"]["maximum_units_per_colony"]
            ):
                raise RuleError("Die Reparatur würde die Einheitenobergrenze überschreiten.")
            try:
                repair_cost = terra_recovery.repair_costs(profile, count)
            except ValueError as exc:
                raise RuleError("Die Reparaturkosten dieses Einheitentyps sind ungültig.") from exc
            if any(have < cost for have, cost in zip(state["resources"], repair_cost)):
                raise RuleError("Für die Reparatur fehlen Rohstoffe.")
            changed = db.execute(
                "UPDATE terra_unit_wrecks SET amount=amount-? WHERE id=? AND amount>=? "
                "AND expires>? AND rule_digest=? RETURNING amount",
                (count, wreck_id, count, now, terra_recovery.DIGEST),
            ).fetchone()
            if not changed:
                raise RuleError("Das Wrack wurde bereits repariert oder ist abgelaufen.")
            state["resources"] = [
                have - cost for have, cost in zip(state["resources"], repair_cost)
            ]
            duration = count * int(profile["training_time"])
            job.update(
                kind="terra_repair",
                key=unit,
                unit=unit,
                wreck_id=wreck_id,
                count=count,
                due=now + duration,
                duration=duration,
                costs=repair_cost,
                label=str(profile["role"]),
                repair_rules_version=terra_recovery.VERSION,
                repair_rules_digest=terra_recovery.DIGEST,
                combat_rules_version=combat_version,
                combat_rules_digest=terra_combat.RULESET_DIGESTS[combat_version],
            )
            state["jobs"].append(job)
            self.systems.audit(
                db,
                user,
                action,
                wreck_id,
                world_id=world_id,
                unit=unit,
                count=count,
                costs=repair_cost,
                duration=duration,
                rules_version=terra_recovery.VERSION,
                rules_digest=terra_recovery.DIGEST,
            )
        elif action in ("terra_defense_build", "terra_defense_repair"):
            from . import terra_defense

            world_id = int(state["world_id"])
            world_rules = db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()
            if (
                payload.get("world_id") != world_id
                or payload.get("colony_id") != state["colony_id"]
                or not world_rules
                or str(world_rules["terra_combat_ruleset"])
                not in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
            ):
                raise RuleError(
                    "Terra-Verteidigungsanlagen sind nur in einer aktiven COMBAT-4/5-Kolonie verfügbar."
                )
            object_key = payload.get("key")
            catalog = terra_defense.RULES["objects"]
            if not isinstance(object_key, str) or object_key not in catalog:
                raise RuleError("Wähle eine gültige Terra-Verteidigungsanlage.")
            stacks = state.setdefault("terra_defense_stacks", {})
            if not isinstance(stacks, dict):
                raise RuleError("Der gespeicherte Verteidigungszustand ist ungültig.")
            has_stacks = any(
                isinstance(existing, list) and existing for existing in stacks.values()
            )
            if has_stacks and (
                state.get("terra_defense_rules_version") != terra_defense.VERSION
                or state.get("terra_defense_rules_digest") != terra_defense.DIGEST
            ):
                raise RuleError(
                    "Die installierten Verteidigungsanlagen verwenden unbekannte Regeln."
                )
            stack = stacks.setdefault(object_key, [])
            if not isinstance(stack, list) or any(
                type(integrity) is not int or not 0 <= integrity <= 100 for integrity in stack
            ):
                raise RuleError("Der gespeicherte Verteidigungszustand ist ungültig.")
            rule = catalog[object_key]
            if action == "terra_defense_build":
                prerequisites = rule["prerequisites"]
                for building, level in prerequisites["buildings"].items():
                    if int(state["buildings"].get(building, 0)) < int(level):
                        raise RuleError(f"Benötigt {BUILDINGS[building]['name']} Stufe {level}.")
                for technology, level in prerequisites["tech"].items():
                    if int(state["tech"].get(technology, 0)) < int(level):
                        raise RuleError(
                            f"Benötigt Forschung {TECH[technology]['name']} Stufe {level}."
                        )
                used_slots = sum(
                    len(existing) for existing in stacks.values() if isinstance(existing, list)
                )
                if len(stack) >= int(rule["maximum_count"]):
                    raise RuleError("Die Höchstzahl dieser Verteidigungsanlage ist erreicht.")
                if used_slots + int(rule["slot_cost"]) > terra_defense.slot_limit(
                    int(state["buildings"].get("hq", 0))
                ):
                    raise RuleError("Für diese Anlage ist kein Verteidigungsslot frei.")
                costs = [int(value) for value in rule["cost"]]
                if any(have < cost for have, cost in zip(state["resources"], costs)):
                    raise RuleError("Für diese Verteidigungsanlage fehlen Rohstoffe.")
                state["resources"] = [have - cost for have, cost in zip(state["resources"], costs)]
                stack.append(100)
                state["terra_defense_rules_version"] = terra_defense.VERSION
                state["terra_defense_rules_digest"] = terra_defense.DIGEST
                self.systems.audit(
                    db,
                    user,
                    action,
                    object_key,
                    colony_id=state["colony_id"],
                    world_id=world_id,
                    slots_used=used_slots + 1,
                    costs=costs,
                    rules_version=terra_defense.VERSION,
                    rules_digest=terra_defense.DIGEST,
                )
                self.report(state, "Verteidigung ausgebaut", f"{rule['name']} wurde errichtet.")
            else:
                if db.execute(
                    "SELECT 1 FROM incoming_attack_index WHERE target_user=? LIMIT 1", (user,)
                ).fetchone():
                    raise RuleError("Reparaturen sind während feindlicher Anmärsche gesperrt.")
                damaged = [index for index, integrity in enumerate(stack) if integrity < 100]
                if not damaged:
                    raise RuleError("Diese Anlage ist vollständig intakt.")
                count = payload.get("count", 1)
                if type(count) is not int or not 1 <= count <= len(damaged):
                    raise RuleError("Wähle eine gültige Zahl beschädigter Anlagen.")
                selected = damaged[:count]
                costs = [0, 0, 0]
                for index in selected:
                    missing = 100 - stack[index]
                    for resource, base_cost in enumerate(rule["cost"]):
                        numerator = int(base_cost) * missing * int(rule["repair_cost_percent"])
                        costs[resource] += (numerator + 9999) // 10000
                if any(have < cost for have, cost in zip(state["resources"], costs)):
                    raise RuleError("Für die Reparatur fehlen Rohstoffe.")
                state["resources"] = [have - cost for have, cost in zip(state["resources"], costs)]
                for index in selected:
                    stack[index] = 100
                self.systems.audit(
                    db,
                    user,
                    action,
                    object_key,
                    colony_id=state["colony_id"],
                    world_id=world_id,
                    repaired=count,
                    costs=costs,
                    rules_version=terra_defense.VERSION,
                    rules_digest=terra_defense.DIGEST,
                )
                self.report(state, "Verteidigung repariert", f"{count} Anlage(n) instand gesetzt.")
        elif action == "admin_terra_sector":
            x, y = payload.get("x"), payload.get("y")
            world_id = state["world_id"]
            if profile["role"] != "admin" or payload.get("world_id") != world_id:
                raise RuleError("Nur die Spielleitung kann Sektorregeln der aktiven Welt ändern.")
            if type(x) is not int or type(y) is not int or not 0 <= x < 64 or not 0 <= y < 64:
                raise RuleError("Ungültiger Terra-Sektor.")
            if key == "clear":
                db.execute(
                    "DELETE FROM terra_sector_rules WHERE world_id=? AND x=? AND y=?",
                    (world_id, x, y),
                )
            elif (
                key in ("protected", "spawn_reserved") and terrain_at(db, x, y, world_id) != "water"
            ):
                db.execute(
                    "INSERT INTO terra_sector_rules(world_id,x,y,kind) VALUES (?,?,?,?) "
                    "ON CONFLICT(world_id,x,y) DO UPDATE SET kind=excluded.kind",
                    (world_id, x, y, key),
                )
            else:
                raise RuleError("Ungültige Sektorregel oder Wasserfeld.")
            self.systems.audit(db, user, action, f"{x}:{y}", world_id=world_id, rule=key)
        elif action == "colony_relocate":
            x, y = payload.get("x"), payload.get("y")
            world_id, colony_id = state["world_id"], state["colony_id"]
            if payload.get("world_id") != world_id or payload.get("colony_id") != colony_id:
                raise RuleError("Wähle die aktive Kolonie in dieser Welt.")
            if type(x) is not int or type(y) is not int or not 0 <= x < 64 or not 0 <= y < 64:
                raise RuleError("Wähle gültige Koordinaten zwischen 0 und 63.")
            if state["buildings"]["hq"] < 3 or state.get("relocation_ready_at", 0) > now:
                raise RuleError("Die Kolonie benötigt Kommandozentrale 3 und muss versetzbar sein.")
            if (
                state["jobs"]
                or db.execute(
                    "SELECT 1 FROM terra_orbit_cargo WHERE terra_colony=?", (colony_id,)
                ).fetchone()
                or db.execute(
                    "SELECT 1 FROM terra_market_convoys WHERE target=?", (colony_id,)
                ).fetchone()
            ):
                raise RuleError("Warte auf den Abschluss laufender Aufträge und Lieferungen.")
            if not sector_is_known(db, user, world_id, x, y):
                raise RuleError("Dieser Sektor ist noch nicht aufgeklärt.")
            self.require_terra_settlement(db, world_id, x, y)
            if any(
                math.hypot(x - camp_x, y - camp_y) < COLONY_MIN_DISTANCE
                for camp_x, camp_y in self.npc_camp_points(db, world_id)
            ):
                raise RuleError("Kolonien benötigen sechs Sektoren Abstand zu NPC-Lagern.")
            if (x, y) == (state["x"], state["y"]) or (x, y) not in travel_times(
                db, (state["x"], state["y"]), world_id
            ):
                raise RuleError("Wähle ein anderes Ziel mit begehbarer Route.")
            if any(town["x"] == x and town["y"] == y for town in self.world_outposts(db, world_id)):
                raise RuleError("Dieser Sektor ist nicht verfügbar.")
            for other in db.execute(
                "SELECT x,y,state FROM colonies WHERE world_id=? AND colony_id<>?",
                (world_id, colony_id),
            ):
                if math.hypot(other["x"] - x, other["y"] - y) < COLONY_MIN_DISTANCE:
                    raise RuleError("Kolonien benötigen mindestens sechs Sektoren Abstand.")
                for incoming in json.loads(other["state"]).get("jobs", []):
                    kind, target = incoming.get("kind"), incoming.get("key")
                    pinned = incoming.get("target_colony_id") == colony_id
                    supply_or_scout = (
                        kind in ("colony_supply", "alliance_supply", "scout")
                        and target == colony_id
                    )
                    legacy = (
                        kind in ("attack", "transport")
                        and not incoming.get("target_colony_id")
                        and target == user
                    )
                    if pinned or supply_or_scout or legacy:
                        raise RuleError(
                            "Warte auf den Abschluss laufender Aufträge und Lieferungen."
                        )
            if any(
                math.hypot(camp_x - x, camp_y - y) < COLONY_MIN_DISTANCE
                for camp_x, camp_y in self.npc_camp_points(db, world_id)
            ):
                raise RuleError("Kolonien benötigen sechs Sektoren Abstand zu NPC-Lagern.")
            if any(stock < cost for stock, cost in zip(state["resources"], COLONY_RELOCATION_COST)):
                raise RuleError("Für die Kolonieversetzung fehlen Rohstoffe.")
            old = [state["x"], state["y"]]
            db.execute(
                "UPDATE colonies SET x=?,y=? WHERE colony_id=? AND user_id=? AND world_id=?",
                (x, y, colony_id, user, world_id),
            )
            state.update(x=x, y=y, relocation_ready_at=now + COLONY_RELOCATION_COOLDOWN)
            state["resources"] = [
                stock - cost for stock, cost in zip(state["resources"], COLONY_RELOCATION_COST)
            ]
            self.systems.audit(
                db,
                user,
                action,
                colony_id,
                world_id=world_id,
                origin=old,
                destination=[x, y],
                costs=COLONY_RELOCATION_COST,
            )
        elif action == "colonize":
            x, y = payload.get("x"), payload.get("y")
            if type(x) is not int or type(y) is not int or not 0 <= x < 64 or not 0 <= y < 64:
                raise RuleError("Wähle gültige Koordinaten zwischen 0 und 63.")
            world_id = int(state.get("world_id", 1))
            if not sector_is_known(db, user, world_id, x, y):
                raise RuleError("Dieser Sektor ist noch nicht aufgeklärt.")
            self.require_terra_settlement(db, world_id, x, y)
            if any(
                math.hypot(x - camp_x, y - camp_y) < COLONY_MIN_DISTANCE
                for camp_x, camp_y in self.npc_camp_points(db, world_id)
            ):
                raise RuleError("Kolonien benötigen sechs Sektoren Abstand zu NPC-Lagern.")
            colonies = db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? AND world_id=?",
                (user, world_id),
            ).fetchall()
            world_colonies = db.execute(
                "SELECT state FROM colonies WHERE world_id=?", (world_id,)
            ).fetchall()
            slot_limit = min(4, 1 + state["buildings"]["hq"] // 3)
            if state["buildings"]["hq"] < 3:
                raise RuleError("Kolonisation benötigt Kommandozentrale Stufe 3.")
            if len(colonies) >= slot_limit:
                raise RuleError("Für eine weitere Kolonie ist noch kein Kolonieslot frei.")
            towns = self.world_outposts(db, world_id)
            if any(town["x"] == x and town["y"] == y for town in towns):
                raise RuleError("Dieser Sektor enthält bereits einen Außenposten.")
            if terrain_at(db, x, y, world_id) == "water":
                raise RuleError("Wasserfelder können nicht kolonisiert werden.")
            for colony_row in world_colonies:
                existing = json.loads(colony_row["state"])
                if existing["x"] == x and existing["y"] == y:
                    raise RuleError("Dieser Sektor ist bereits durch eine Kolonie belegt.")
                if math.hypot(existing["x"] - x, existing["y"] - y) < COLONY_MIN_DISTANCE:
                    raise RuleError("Neue Kolonien benötigen mindestens sechs Sektoren Abstand.")
            reachable = False
            for colony_row in colonies:
                owned_colony = json.loads(colony_row["state"])
                destinations = travel_times(
                    db, (int(owned_colony["x"]), int(owned_colony["y"])), world_id
                )
                if (x, y) in destinations:
                    reachable = True
                    break
            if not reachable:
                raise RuleError(
                    "Dieser Sektor ist über begehbares Gelände von keiner deiner Kolonien erreichbar."
                )
            colonization_costs = [2000, 1500, 1000]
            survey = state.get("pioneer_survey", {})
            if survey.get("x") == x and survey.get("y") == y and survey.get("expires", 0) > now:
                colonization_costs = [
                    cost * (100 - PIONEER_SETTLEMENT_DISCOUNT) // 100 for cost in colonization_costs
                ]
                state.pop("pioneer_survey", None)
            if any(have < cost for have, cost in zip(state["resources"], colonization_costs)):
                raise RuleError(
                    f"Die Kolonisationskosten betragen {colonization_costs[0]:,} Holz, {colonization_costs[1]:,} Stein und {colonization_costs[2]:,} Erz.".replace(
                        ",", "."
                    )
                )
            state["resources"] = [
                have - cost for have, cost in zip(state["resources"], colonization_costs)
            ]
            new_id = identity()
            name_index = len(colonies) + 1
            colony_name = f"{state['name']} · Basis {name_index}"
            while db.execute(
                "SELECT 1 FROM colonies WHERE name_key=? LIMIT 1", (colony_name.casefold(),)
            ).fetchone():
                name_index += 1
                colony_name = f"{state['name']} · Basis {name_index}"
            new_state = {
                "id": user,
                "colony_id": new_id,
                "colony_name": colony_name,
                "name": state["name"],
                "x": x,
                "y": y,
                "terrain": terrain_at(db, x, y, world_id),
                "resources": [500, 500, 500],
                "buildings": {
                    key: (1 if key in ("hq", "wood", "stone", "ore", "storage") else 0)
                    for key in BUILDINGS
                },
                "tech": {key: 0 for key in TECH},
                "units": {"ranger": 5, "sentinel": 0, "mech": 0},
                "jobs": [],
                "reports": [],
                "claimed": [],
                "captures": 0,
                "last": now,
                "faction_chosen": bool(state.get("faction_chosen")),
            }
            db.execute(
                "INSERT INTO colonies"
                "(colony_id,user_id,world_id,is_home,x,y,state,name_key,ranking_score) "
                "VALUES (?,?,?,FALSE,?,?,?,?,?)",
                (
                    new_id,
                    user,
                    world_id,
                    x,
                    y,
                    json.dumps(new_state),
                    colony_name.casefold(),
                    self.colony_score(new_state),
                ),
            )
            self.systems.audit(
                db, user, action, new_id, coordinates=[x, y], costs=colonization_costs
            )
        elif action == "raid":
            world_id = int(state.get("world_id", 1))
            towns = self.world_outposts(db, world_id)
            outpost_target = next((t for t in towns if t["id"] == key), None)
            if not outpost_target or outpost_target["owner"] == user:
                raise RuleError("Wähle einen freien oder gegnerischen Außenposten.")
            if not sector_is_known(db, user, world_id, outpost_target["x"], outpost_target["y"]):
                raise RuleError("Dieser Sektor ist noch nicht aufgeklärt.")
            if outpost_target["owner"]:
                self.systems.can_attack(db, user, outpost_target["owner"], now, world_id)
            if len(state["jobs"]) >= self.terra_mission_limit(state):
                raise RuleError(f"Maximal {self.terra_mission_limit(state)} Operationen.")
            army = payload.get("army", {})
            if (
                not isinstance(army, dict)
                or not army
                or any(
                    k not in self.unit_catalog_for_world(db, world_id)
                    or type(n) is not int
                    or n < 0
                    or n > state["units"].get(k, 0)
                    for k, n in army.items()
                )
                or sum(army.values()) < 1
            ):
                raise RuleError("Ungültige Truppenauswahl.")
            if payload.get("capture") and state["buildings"]["hq"] < 3:
                raise RuleError("Eroberungen benötigen Kommandozentrale Stufe 3.")
            for unit, count in army.items():
                state["units"][unit] = state["units"].get(unit, 0) - count
            movement = self.movement_quote(
                db,
                (state["x"], state["y"]),
                (outpost_target["x"], outpost_target["y"]),
                world_id,
                army,
            )
            fuel_ore = int(movement["fuel_ore"])
            if fuel_ore > int(state["resources"][2]):
                raise RuleError(f"Für den Hin- und Rückflug fehlen {fuel_ore} Erz als Treibstoff.")
            state["resources"][2] -= fuel_ore
            travel = int(movement["travel_seconds"])
            job.update(
                due=now + travel,
                travel=travel,
                movement=movement,
                army=army,
                capture=bool(payload.get("capture")),
                label="Angriff auf " + outpost_target["name"],
                tactics=state["tech"]["tactics"],
                allow_owned=outpost_target["owner"] is not None,
                expected_owner=outpost_target["owner"],
            )
            combat_mission = terra_combat.pin_mission(db, job["id"], world_id, now)
            if combat_mission is not None:
                job.update(combat_mission)
            state["jobs"].append(job)
        elif action == "recurring_quest_claim":
            recurring = recurring_quests.claim(db, world_id, user, key, now)
            if recurring is None:
                raise RuleError(
                    "Die Aufgabenbelohnung ist noch nicht verfügbar, abgelaufen oder bereits abgeholt."
                )
            self.systems.credit_state(db, state, list(recurring.reward), "Aufgabenbelohnung", now)
            self.systems.audit(db, user, action, key, world=world_id)
        elif action == "quest":
            quests = self.quests(state)
            quest = next((q for q in quests if q["id"] == key), None)
            if not quest or not quest["unlocked"] or not quest["done"] or key in state["claimed"]:
                raise RuleError("Belohnung noch nicht verfügbar oder bereits abgeholt.")
            state["claimed"].append(key)
            cap = 2000 + state["buildings"]["storage"] * 2000
            reserve = state.setdefault("reserve", [0, 0, 0])
            for index, amount in enumerate(state["resources"]):
                total = amount + quest["reward"]
                reserve[index] += max(0, total - cap)
                state["resources"][index] = min(cap, total)
            awarded = cosmetic_rewards.award_for_directive(db, user, key, now)
            if key == "victory":
                prestige.award(
                    db,
                    user,
                    "campaign:victory",
                    "campaign_victory",
                    world_id,
                    "citadel-victory",
                    now,
                )
            self.report(state, "Auftrag erfüllt", quest["name"])
            for cosmetic_id in awarded:
                self.report(
                    state,
                    "Kosmetik freigeschaltet",
                    cosmetic_rewards.COSMETICS[cosmetic_id][1],
                )
        elif action == "craft_start":
            if not crafting.enabled_in_world(db, int(state["world_id"])):
                raise RuleError("Fertigung ist in dieser Welt nicht aktiviert.")
            job = crafting.start(state, payload, now)
            self.systems.audit(
                db,
                user,
                "craft_started",
                str(job["id"]),
                recipe_id=job["recipe_id"],
                batches=job["batches"],
                inputs=job["inputs"],
                output=job["output"],
                due=job["due"],
                rules_version=crafting.RULES.version,
                rules_hash=crafting.RULE_HASH,
            )
            self.report(
                state,
                "Fertigung eingereiht",
                f"{job['label']} · {job['batches']} Durchlauf/Durchläufe · Abschluss in "
                f"{job['duration']} Sekunden.",
            )
        elif action == "item_recycle":
            if not crafting.enabled_in_world(db, int(state["world_id"])):
                raise RuleError("Gegenstandsrecycling ist in dieser Welt nicht aktiviert.")
            receipt = recycling.recycle(state, payload)
            self.systems.audit(
                db,
                user,
                action,
                str(state["colony_id"]),
                world_id=state["world_id"],
                **receipt,
            )
            self.report(
                state,
                "Gegenstände zerlegt",
                f"{receipt['amount']} × {receipt['item_id']} → "
                f"{receipt['output_items']} und {receipt['output_goods']}",
            )
        elif action == "goods_trade":
            receipt = exchange(
                state,
                self.systems.world_faction(db, user, int(state["world_id"])) or "pioneers",
                payload.get("goods_source"),
                payload.get("goods_destination"),
                payload.get("amount"),
            )
            db.execute(
                "INSERT INTO neutral_goods_trades "
                "(id,owner,world_id,colony_id,command_token,created,details) VALUES (?,?,?,?,?,?,?)",
                (
                    identity(),
                    user,
                    state["world_id"],
                    state["colony_id"],
                    token,
                    now,
                    json.dumps(receipt),
                ),
            )
            if receipt["source"] in RESOURCES and receipt["destination"] in RESOURCES:
                db.execute(
                    "INSERT INTO market_trades VALUES (?,?,?,?,?,?,?,?)",
                    (
                        identity(),
                        state["world_id"],
                        now,
                        RESOURCES.index(receipt["source"]),
                        RESOURCES.index(receipt["destination"]),
                        receipt["given"],
                        receipt["received"],
                        "neutral",
                    ),
                )
            self.systems.audit(
                db,
                user,
                "goods_trade",
                str(state["colony_id"]),
                world_id=state["world_id"],
                **receipt,
            )
            self.report(
                state,
                "Marktgüter getauscht",
                f"{receipt['given']} {receipt['source']} gegen "
                f"{receipt['received']} {receipt['destination']}.",
            )
        elif action == "goods_reserve_claim":
            claim_reserve(state, payload.get("good_id"), payload.get("amount"))
            self.systems.audit(
                db,
                user,
                "goods_reserve_claim",
                str(state["colony_id"]),
                good_id=payload.get("good_id"),
                amount=payload.get("amount"),
            )
        elif action == "item_reserve_claim":
            claim_item_reserve(state, payload.get("item_id"), payload.get("amount"))
            self.systems.audit(
                db,
                user,
                "item_reserve_claim",
                str(state["colony_id"]),
                item_id=payload.get("item_id"),
                amount=payload.get("amount"),
            )
        elif action == "trade":
            source, dest = payload.get("source"), payload.get("dest")
            amount = payload.get("amount")
            if (
                type(source) is not int
                or type(dest) is not int
                or source not in range(3)
                or dest not in range(3)
                or source == dest
                or type(amount) is not int
                or amount < 10
                or amount > state["resources"][source]
            ):
                raise RuleError("Ungültiger Tausch. Mindestmenge: 10.")
            cap = 2000 + state["buildings"]["storage"] * 2000
            received = (
                amount * 3 // 5
                if self.systems.world_faction(db, user, int(state["world_id"])) == "syndicate"
                else amount // 2
            )
            if state["resources"][dest] + received > cap:
                raise RuleError("Das Depot ist für diesen Tausch zu klein.")
            state["resources"][source] -= amount
            state["resources"][dest] += received
            db.execute(
                "INSERT INTO market_trades VALUES (?,?,?,?,?,?,?,?)",
                (
                    identity(),
                    int(state.get("world_id", 1)),
                    now,
                    source,
                    dest,
                    amount,
                    received,
                    "neutral",
                ),
            )
        else:
            self.systems.command(db, state, action, payload)
        for queued_job in state["jobs"]:
            if str(queued_job.get("id", "")) not in existing_job_ids:
                heroes.pin_job(db, int(state["world_id"]), queued_job)
                hero_doctrines.pin_job(db, int(state["world_id"]), state["commander"], queued_job)
        self.save(db, state)
        db.execute(
            "INSERT INTO commands(user_id,token,signature,origin_world_id,origin_colony_id,rule_version) "
            "VALUES (?,?,?,?,?,?)",
            (user, token, signature, state["world_id"], state["colony_id"], REGISTRY["version"]),
        )
        game_events.stage(db, identity(), user, state["world_id"], action, now)
        db.execute(
            "INSERT INTO ledger VALUES (?, ?, ?, ?, ?, ?)",
            (identity(), user, now, action, json.dumps(before), json.dumps(state["resources"])),
        )
        return self.view(db, user)

    def quests(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        claimed = set(state.get("claimed", []))
        previous: list[str] = []
        result: list[dict[str, Any]] = []
        for key, name, done, reward in [
            (
                "economy",
                "Versorgungsnetz: alle Rohstoffgebäude auf Stufe 2",
                all(state["buildings"][k] >= 2 for k in RESOURCES),
                400,
            ),
            (
                "army",
                "Mobilmachung: baue eine Kaserne",
                state["buildings"]["barracks"] >= 1,
                300,
            ),
            (
                "science",
                "Neues Wissen: erforsche eine Technologie",
                sum(state["tech"].values()) >= 1,
                500,
            ),
            ("expansion", "Expansion: erobere einen Außenposten", state["captures"] >= 1, 900),
            (
                "victory",
                "FUR Empire: erobere die Zitadelle des Kerns",
                state.get("citadel", False),
                2000,
            ),
        ]:
            result.append(
                {
                    "id": key,
                    "name": name,
                    "done": done,
                    "reward": reward,
                    "unlocked": all(previous_key in claimed for previous_key in previous),
                }
            )
            previous.append(key)
        return result
