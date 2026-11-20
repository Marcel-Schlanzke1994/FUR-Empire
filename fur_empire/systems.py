"""Integrated multiplayer services. Never called outside a world transaction."""

import json
import math
import re
import time
from typing import TYPE_CHECKING, Any, NoReturn

from . import (
    alliance_projects,
    alliance_treasury,
    alliance_war,
    boss_raids,
    cosmetic_rewards,
    crafting,
    hero_doctrines,
    hero_respec,
    heroes,
    live_events,
    npc_camps,
    npc_convoys,
    npc_invasions,
    player_profile,
    recurring_quests,
    report_sharing,
    ruin_exploration,
    rule_rollouts,
)
from .colony_management import designate_home
from .database import Connection
from .fog import sector_is_known, visible_sectors
from .terrain import (
    DEFENSE_PERCENT,
    PRODUCTION_PERCENT,
    TERRAIN_LABELS,
    defense_with_terrain,
    terrain_at,
    travel_times,
)

if TYPE_CHECKING:
    from .game import Game


ALLIANCE_PERMISSIONS = (
    "applications",
    "invitations",
    "description",
    "member_removal",
    "diplomacy",
    "bulletin",
    "forum_moderation",
    "treasury",
    "projects",
)
ALLIANCE_PERMISSION_LABELS = {
    "applications": "Bewerbungen bearbeiten",
    "invitations": "Einladungen verwalten",
    "description": "Allianzbeschreibung ändern",
    "member_removal": "Mitglieder entfernen",
    "diplomacy": "Diplomatie verwalten",
    "bulletin": "Pinnwand verwalten",
    "forum_moderation": "Forum moderieren und Meldungen prüfen",
    "treasury": "Allianzkasse verwalten",
    "projects": "Allianzprojekte verwalten",
}


class Systems:
    def __init__(self, game: "Game"):
        self.game = game

    def hall_of_fame(
        self, db: Connection, state: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Return bounded historical records relevant to the current world."""
        user_id = str(state["id"])
        world_id = int(state.get("world_id", 1))
        seasons = [
            dict(row)
            for row in db.execute(
                "SELECT s.id AS season_id,s.name AS season_name,s.starts,s.ends,"
                "a.award,a.score,a.created,u.name FROM season_awards a "
                "JOIN seasons s ON s.id=a.season_id JOIN users u ON u.id=a.user_id "
                "WHERE s.world_id=? AND a.user_id=? ORDER BY a.created DESC,s.id LIMIT 50",
                (world_id, user_id),
            )
        ]
        alliances = [
            dict(row)
            for row in db.execute(
                "SELECT s.season_id,s.alliance_name,s.alliance_tag,s.score,s.rank,s.eligible_accounts,"
                "snap.rules_version,snap.rules_digest FROM season_alliance_standings s "
                "JOIN seasons season ON season.id=s.season_id "
                "JOIN season_alliance_snapshots snap ON snap.season_id=s.season_id "
                "WHERE season.world_id=? AND s.alliance_id IN ("
                "SELECT m.alliance_id FROM members m JOIN colonies c ON c.user_id=m.user_id "
                "WHERE m.user_id=? AND c.world_id=?) "
                "ORDER BY season.ends DESC,s.rank LIMIT 50",
                (world_id, user_id, world_id),
            )
        ]
        boss_records = [
            dict(row)
            for row in db.execute(
                "SELECT e.id AS event_id,e.kind,e.starts,e.ends,r.mission_id "
                "FROM orbit_event_rewards r JOIN orbit_special_events e ON e.id=r.event_id "
                "JOIN orbit_planet_claims p ON p.owner=r.user_id AND p.world_id=e.world_id "
                "WHERE r.user_id=? AND e.world_id=? AND e.kind='boss' "
                "ORDER BY e.ends DESC,r.mission_id LIMIT 50",
                (user_id, world_id),
            )
        ]
        war_records = [
            dict(row)
            for row in db.execute(
                "SELECT e.war_id,e.event_type,e.actor_alliance,e.created,w.winner,w.end_reason,"
                "w.rules_version,w.rules_digest,a.name AS alliance_a_name,a.tag AS alliance_a_tag,"
                "b.name AS alliance_b_name,b.tag AS alliance_b_tag "
                "FROM alliance_war_events e JOIN alliance_wars w ON w.id=e.war_id "
                "JOIN alliances a ON a.id=w.alliance_a JOIN alliances b ON b.id=w.alliance_b "
                "WHERE e.event_type IN ('ended_peace','ended_objective') AND EXISTS ("
                "SELECT 1 FROM alliance_war_score_ledger l WHERE l.war_id=w.id AND l.user_id=?) "
                "ORDER BY e.created DESC,e.id DESC LIMIT 50",
                (user_id,),
            )
        ]
        return {
            "seasons": seasons,
            "alliances": alliances,
            "bosses": boss_records,
            "wars": war_records,
        }

    def player_hall_of_fame(self, db: Connection, user_id: str) -> dict[str, Any]:
        from . import prestige

        return prestige.view(db, user_id)

    def error(self, message: str) -> NoReturn:
        from .game import RuleError

        raise RuleError(message)

    def reserve_movement_fuel(
        self,
        db: Connection,
        state: dict[str, Any],
        start: tuple[int, int],
        finish: tuple[int, int],
        army: dict[str, int],
        *,
        additional_ore_cost: int = 0,
    ) -> dict[str, Any]:
        quote = self.game.movement_quote(db, start, finish, int(state.get("world_id", 1)), army)
        fuel_ore = int(quote["fuel_ore"])
        if fuel_ore + additional_ore_cost > int(state["resources"][2]):
            self.error(f"Für den Hin- und Rückflug fehlen {fuel_ore} Erz als Treibstoff.")
        state["resources"][2] -= fuel_ore
        return quote

    def player_colonies_page(
        self, db: Connection, user: str, before_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (user,)
        if before_id is not None:
            cursor = db.execute(
                "SELECT world_id,is_home,colony_id FROM colonies "
                "WHERE user_id=? AND colony_id=?",
                (user, before_id),
            ).fetchone()
            if not cursor:
                self.error("Kolonie-Cursor ungültig.")
            cursor_clause = (
                "AND (world_id>? OR (world_id=? AND is_home<?) OR "
                "(world_id=? AND is_home=? AND colony_id>?)) "
            )
            params = (
                user,
                int(cursor["world_id"]),
                int(cursor["world_id"]),
                bool(cursor["is_home"]),
                int(cursor["world_id"]),
                bool(cursor["is_home"]),
                before_id,
            )
        rows = list(
            db.execute(
                "SELECT colony_id,world_id,is_home,state FROM colonies WHERE user_id=? "
                + cursor_clause
                + "ORDER BY world_id,is_home DESC,colony_id LIMIT 51",
                params,
            )
        )
        colonies = []
        for row in rows[:50]:
            colony = json.loads(row["state"])
            colonies.append(
                {
                    "colony_id": str(row["colony_id"]),
                    "world_id": int(row["world_id"]),
                    "is_home": bool(row["is_home"]),
                    "name": colony.get("colony_name", colony["name"]),
                    "x": int(colony["x"]),
                    "y": int(colony["y"]),
                    "hq": int(colony["buildings"]["hq"]),
                }
            )
        return colonies, len(rows) > 50

    def world_directory_page(
        self, db: Connection, user: str, before_world_id: int | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (user,)
        if before_world_id is not None:
            cursor = db.execute(
                "SELECT 1 FROM world_settings WHERE world_id=?", (before_world_id,)
            ).fetchone()
            if not cursor:
                self.error("Welt-Cursor ungültig.")
            cursor_clause = "AND s.world_id>? "
            params = (user, before_world_id)
        rows = list(
            db.execute(
                "SELECT s.world_id,s.name,s.joinable,s.mode,s.terra_combat_ruleset,"
                "s.terra_retreat_threshold_percent,s.settings,"
                + "EXISTS(SELECT 1 FROM colonies c WHERE c.world_id=s.world_id AND c.user_id=?) AS has_colony,"
                + "(SELECT COUNT(DISTINCT c.user_id) FROM colonies c WHERE c.world_id=s.world_id) AS player_count "
                "FROM world_settings s WHERE 1=1 " + cursor_clause + "ORDER BY s.world_id LIMIT 51",
                params,
            )
        )
        worlds: list[dict[str, Any]] = []
        profile = self.profile(db, user)
        is_admin = profile["role"] == "admin"
        for row in rows[:50]:
            try:
                settings = json.loads(row["settings"] or "{}")
            except (TypeError, ValueError):
                self.error("Die gespeicherten Welteinstellungen sind ungültig.")
            if not isinstance(settings, dict):
                self.error("Die gespeicherten Welteinstellungen sind ungültig.")
            crafting_ruleset = settings.get("crafting_ruleset", "FUR-2")
            if crafting_ruleset not in ("FUR-2", crafting.RULES.version):
                self.error("Der gespeicherte Fertigungsregelstand ist ungültig.")
            hero_ruleset = settings.get(heroes.RULES.enabled_key, "FUR-2")
            if hero_ruleset not in ("FUR-2", heroes.RULES.version):
                self.error("Der gespeicherte Commander-Regelstand ist ungültig.")
            doctrine_ruleset = settings.get(hero_doctrines.RULES.enabled_key, "FUR-2")
            if doctrine_ruleset not in ("FUR-2", hero_doctrines.RULES.version):
                self.error("Der gespeicherte Commander-Doktrinstand ist ungültig.")
            respec_ruleset = settings.get(hero_respec.RULES.enabled_key, "FUR-2")
            if respec_ruleset not in ("FUR-2", hero_respec.RULES.version):
                self.error("Der gespeicherte Commander-Resetstand ist ungültig.")
            camp_ruleset = settings.get(npc_camps.RULESET_KEY, "FUR-2")
            if camp_ruleset not in ("FUR-2", *npc_camps.RULESET_VERSIONS):
                self.error("Der gespeicherte NPC-Lager-Regelstand ist ungültig.")
            ruin_ruleset = settings.get("terra_ruin_exploration_ruleset", "FUR-2")
            if ruin_ruleset not in ("FUR-2", ruin_exploration.VERSION):
                self.error("Der gespeicherte Ruinenerkundungs-Regelstand ist ungültig.")
            world_entry = {
                "id": int(row["world_id"]),
                "name": str(row["name"]),
                "joinable": bool(row["joinable"]),
                "mode": str(row["mode"]),
                "terra_combat_ruleset": str(row["terra_combat_ruleset"]),
                "crafting_ruleset": str(crafting_ruleset),
                "hero_ruleset": str(hero_ruleset),
                "hero_doctrine_ruleset": str(doctrine_ruleset),
                "hero_respec_ruleset": str(respec_ruleset),
                "npc_camps_ruleset": str(camp_ruleset),
                "terra_ruin_exploration_ruleset": str(ruin_ruleset),
                "terra_retreat_threshold_percent": int(row["terra_retreat_threshold_percent"]),
                "has_colony": bool(row["has_colony"]),
                "player_count": int(row["player_count"]),
            }
            if is_admin:
                world_entry["pending_rule_rollouts"] = rule_rollouts.page(db, int(row["world_id"]))
            worlds.append(world_entry)
        return worlds, len(rows) > 50

    def text(self, payload: dict[str, Any], key: str, minimum: int = 1, maximum: int = 100) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
            self.error(f"{key}: {minimum} bis {maximum} Zeichen erforderlich.")
        return str(value).strip()

    def integer(self, p: dict[str, Any], key: str, low: int, high: int) -> int:
        n = p.get(key)
        if type(n) is not int or not low <= n <= high:
            self.error(f"{key}: ganze Zahl zwischen {low} und {high} erforderlich.")
        return int(n)

    def market_history(self, db: Connection, now: int, world_id: int = 1) -> list[dict[str, Any]]:
        return [
            {
                "source_resource": int(row["source_resource"]),
                "target_resource": int(row["target_resource"]),
                "source_amount": int(row["source_amount"]),
                "target_amount": int(row["target_amount"]),
                "trade_kind": row["trade_kind"],
                "timestamp": int(row["bucket_start"]),
                "trade_count": int(row["trade_count"]),
                "weighted_price_milli": int(row["weighted_price_milli"]),
            }
            for row in db.execute(
                "SELECT source_resource,target_resource,(timestamp/3600)*3600 AS bucket_start,"
                "SUM(source_amount) AS source_amount,SUM(target_amount) AS target_amount,"
                "COUNT(*) AS trade_count,"
                "(SUM(target_amount)*1000)/SUM(source_amount) AS weighted_price_milli,trade_kind "
                "FROM market_trades WHERE world_id=? AND timestamp>=? AND timestamp<=? "
                "GROUP BY source_resource,target_resource,bucket_start,trade_kind "
                "ORDER BY bucket_start DESC,source_resource,target_resource,trade_kind LIMIT 60",
                (world_id, now - 30 * 86400, now),
            )
        ]

    def audit(
        self, db: Connection, actor: str, action: str, target: str = "", **details: Any
    ) -> None:
        from .game import identity

        db.execute(
            "INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?)",
            (identity(), actor, action, target, json.dumps(details), int(time.time())),
        )

    def profile(self, db: Connection, user: str) -> dict[str, Any]:
        db.execute(
            "INSERT INTO profiles(user_id,joined) VALUES (?,?) ON CONFLICT(user_id) DO NOTHING",
            (user, int(time.time())),
        )
        profile = dict(db.execute("SELECT * FROM profiles WHERE user_id=?", (user,)).fetchone())
        if profile.get("active_colony_id") is None:
            home = db.execute(
                "SELECT colony_id,world_id FROM colonies WHERE user_id=? AND is_home=TRUE ORDER BY world_id,colony_id LIMIT 1",
                (user,),
            ).fetchone()
            if home:
                db.execute(
                    "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
                    (home["colony_id"], home["world_id"], user),
                )
                profile["active_colony_id"] = home["colony_id"]
                profile["active_world_id"] = home["world_id"]
        elif profile.get("active_world_id") is None:
            active = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (profile["active_colony_id"], user),
            ).fetchone()
            if active:
                db.execute(
                    "UPDATE profiles SET active_world_id=? WHERE user_id=?",
                    (active["world_id"], user),
                )
                profile["active_world_id"] = active["world_id"]
        return profile

    def player_profile_settings(self, db: Connection, user: str) -> dict[str, Any]:
        db.execute(
            "INSERT INTO player_profile_settings(user_id) VALUES (?) "
            "ON CONFLICT(user_id) DO NOTHING",
            (user,),
        )
        settings = db.execute(
            "SELECT visibility,title_id,reward_title_id,skin_id,banner_id "
            "FROM player_profile_settings WHERE user_id=?",
            (user,),
        ).fetchone()
        badges = [
            str(row["badge_id"])
            for row in db.execute(
                "SELECT badge_id FROM player_profile_badges WHERE user_id=? ORDER BY position",
                (user,),
            )
        ]
        return {
            "visibility": str(settings["visibility"]),
            "title_id": str(settings["title_id"]),
            "reward_title_id": str(settings["reward_title_id"]),
            "skin_id": str(settings["skin_id"]),
            "banner_id": str(settings["banner_id"]),
            "unlocked_cosmetics": cosmetic_rewards.unlocked(db, user),
            "badge_ids": badges,
        }

    def public_player_profile(
        self, db: Connection, viewer: str, target: str, world_id: int
    ) -> dict[str, Any] | None:
        settings = db.execute(
            "SELECT s.visibility,s.title_id,s.reward_title_id,s.skin_id,s.banner_id,p.banned "
            "FROM player_profile_settings s "
            "JOIN profiles p ON p.user_id=s.user_id WHERE s.user_id=?",
            (target,),
        ).fetchone()
        if (
            not settings
            or int(settings["banned"])
            or (viewer != target and settings["visibility"] != "public")
        ):
            return None
        player = db.execute(
            "SELECT u.name,w.name AS world_name,SUM(c.ranking_score) AS score "
            "FROM colonies c JOIN users u ON u.id=c.user_id "
            "JOIN world_settings w ON w.world_id=c.world_id "
            "WHERE c.user_id=? AND c.world_id=? GROUP BY u.id,u.name,w.name",
            (target, world_id),
        ).fetchone()
        if not player:
            return None
        score = int(player["score"])
        ahead = int(
            db.execute(
                "SELECT count(*) FROM (SELECT c.user_id AS id,SUM(c.ranking_score) AS score "
                "FROM colonies c WHERE c.world_id=? GROUP BY c.user_id) standing "
                "WHERE score>? OR (score=? AND id<?)",
                (world_id, score, score, target),
            ).fetchone()[0]
        )
        badge_ids = [
            str(row["badge_id"])
            for row in db.execute(
                "SELECT badge_id FROM player_profile_badges WHERE user_id=? ORDER BY position",
                (target,),
            )
        ]
        title_id = str(settings["title_id"])
        reward_title_id = str(settings["reward_title_id"])
        owned = cosmetic_rewards.unlocked(db, target)
        if reward_title_id != "none" and f"title:{reward_title_id}" in owned:
            title = cosmetic_rewards.RULES.titles[reward_title_id]
        else:
            title = player_profile.TITLES[title_id]
        skin_id = str(settings["skin_id"])
        banner_id = str(settings["banner_id"])
        return {
            "name": str(player["name"]),
            "title": title,
            "skin": cosmetic_rewards.RULES.skins.get(skin_id, ""),
            "skin_id": skin_id,
            "banner": cosmetic_rewards.RULES.banners.get(banner_id, ""),
            "banner_id": banner_id,
            "badges": [player_profile.BADGES[badge_id] for badge_id in badge_ids],
            "world": str(player["world_name"]),
            "rank": ahead + 1,
            "score": score,
            "rules_version": str(player_profile.RULES["version"]),
        }

    def update_player_profile(
        self, db: Connection, state: dict[str, Any], payload: dict[str, Any]
    ) -> None:
        user = str(state["id"])
        visibility = self.text(payload, "profile_visibility", 1, 10)
        title_id = self.text(payload, "profile_title", 1, 40)
        reward_title_id = payload.get("profile_reward_title", "none")
        skin_id = payload.get("profile_skin", "none")
        banner_id = payload.get("profile_banner", "none")
        if any(
            not isinstance(value, str) or len(value) > 40
            for value in (reward_title_id, skin_id, banner_id)
        ):
            self.error("Ungültige Profilkosmetik.")
        raw_badges = payload.get("profile_badges", "")
        if not isinstance(raw_badges, str) or len(raw_badges) > 120:
            self.error("Ungültige Profilabzeichen.")
        badge_ids = raw_badges.split(",") if raw_badges else []
        if visibility not in ("private", "public"):
            self.error("Ungültige Profil-Sichtbarkeit.")
        if title_id not in player_profile.TITLES:
            self.error("Dieser Profil-Titel ist nicht verfügbar.")
        owned = cosmetic_rewards.unlocked(db, user)
        if reward_title_id != "none" and f"title:{reward_title_id}" not in owned:
            self.error("Dieser Belohnungstitel wurde noch nicht freigeschaltet.")
        if skin_id != "none" and f"skin:{skin_id}" not in owned:
            self.error("Dieser Kommandanten-Skin wurde noch nicht freigeschaltet.")
        if banner_id != "none" and f"banner:{banner_id}" not in owned:
            self.error("Dieses Profilbanner wurde noch nicht freigeschaltet.")
        if (
            len(badge_ids) > player_profile.MAX_BADGES
            or len(set(badge_ids)) != len(badge_ids)
            or any(badge_id not in player_profile.BADGES for badge_id in badge_ids)
        ):
            self.error("Wähle höchstens drei verschiedene verfügbare Profilabzeichen.")
        self.player_profile_settings(db, user)
        db.execute(
            "UPDATE player_profile_settings SET visibility=?,title_id=?,reward_title_id=?,"
            "skin_id=?,banner_id=?,updated=? WHERE user_id=?",
            (visibility, title_id, reward_title_id, skin_id, banner_id, int(time.time()), user),
        )
        db.execute("DELETE FROM player_profile_badges WHERE user_id=?", (user,))
        for position, badge_id in enumerate(badge_ids):
            db.execute(
                "INSERT INTO player_profile_badges(user_id,badge_id,position) VALUES (?,?,?)",
                (user, badge_id, position),
            )
        self.audit(
            db,
            user,
            "profile_settings_update",
            user,
            visibility=visibility,
            title_id=title_id,
            reward_title_id=reward_title_id,
            skin_id=skin_id,
            banner_id=banner_id,
            badge_count=len(badge_ids),
            rules_version=player_profile.RULES["version"],
        )

    def world_faction(self, db: Connection, user: str, world_id: int) -> str | None:
        row = db.execute(
            "SELECT faction FROM world_players WHERE user_id=? AND world_id=?",
            (user, world_id),
        ).fetchone()
        return str(row["faction"]) if row and row["faction"] else None

    def flag(self, db: Connection, key: str) -> bool:
        row = db.execute("SELECT value FROM flags WHERE name=?", (key,)).fetchone()
        return bool(row and row[0] == "true")

    def pvp_enabled(self, db: Connection, world_id: int) -> bool:
        world = db.execute(
            "SELECT mode FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        return bool(world and world["mode"] != "sandbox" and self.flag(db, "pvp"))

    def member(self, db: Connection, user: str) -> Any:
        return db.execute("SELECT * FROM members WHERE user_id=?", (user,)).fetchone()

    def officer(self, db: Connection, user: str) -> Any:
        member = self.member(db, user)
        if not member or member["role"] not in ("leader", "officer"):
            self.error("Nur die Allianzleitung kann diese Aktion ausführen.")
        return member

    def alliance_permissions(self, db: Connection, member: Any) -> list[str]:
        if member["role"] == "leader":
            return list(ALLIANCE_PERMISSIONS)
        return [
            str(row["permission"])
            for row in db.execute(
                "SELECT permission FROM alliance_role_permissions "
                "WHERE alliance_id=? AND role=? ORDER BY permission",
                (member["alliance_id"], member["role"]),
            )
        ]

    def require_alliance_permission(self, db: Connection, user: str, permission: str) -> Any:
        member = self.member(db, user)
        if not member:
            self.error(
                "Nur die Allianzleitung oder ausdrücklich berechtigte Allianzrollen können "
                "diese Aktion ausführen."
            )
        if member["role"] == "leader":
            return member
        if permission not in self.alliance_permissions(db, member):
            self.error(
                "Dir fehlt die Berechtigung für diese Allianzaktion; die Allianzleitung kann "
                "sie vergeben."
            )
        return member

    def alliance_bulletin_page(
        self, db: Connection, alliance_id: str, before_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (alliance_id,)
        if before_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM alliance_bulletins WHERE id=? AND alliance_id=?",
                (before_id, alliance_id),
            ).fetchone()
            if not cursor:
                self.error("Älterer Pinnwandeintrag nicht gefunden.")
            cursor_clause = "AND (b.created<? OR (b.created=? AND b.id<?)) "
            params = (
                alliance_id,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT b.id,b.title,b.body,b.author_id,u.name AS author_name,b.created,b.updated,b.archived "
                "FROM alliance_bulletins b JOIN users u ON u.id=b.author_id "
                "WHERE b.alliance_id=? "
                + cursor_clause
                + "ORDER BY b.created DESC,b.id DESC LIMIT 101",
                params,
            )
        ]
        return rows[:100], len(rows) > 100

    def alliance_forum_page(
        self, db: Connection, alliance_id: str, before_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (alliance_id,)
        if before_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM alliance_forum_threads WHERE id=? AND alliance_id=?",
                (before_id, alliance_id),
            ).fetchone()
            if not cursor:
                self.error("Älteres Forumthema nicht gefunden.")
            cursor_clause = "AND (t.created<? OR (t.created=? AND t.id<?)) "
            params = (
                alliance_id,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT t.id,t.author_id,t.title,t.created,t.updated,t.archived,u.name AS author_name "
                "FROM alliance_forum_threads t JOIN users u ON u.id=t.author_id "
                "WHERE t.alliance_id=? "
                + cursor_clause
                + "ORDER BY t.created DESC,t.id DESC LIMIT 51",
                params,
            )
        ]
        has_more = len(rows) > 50
        threads = rows[:50]
        if not threads:
            return threads, has_more
        thread_ids = [str(thread["id"]) for thread in threads]
        placeholders = ",".join("?" for _ in thread_ids)
        posts = db.execute(
            "SELECT id,thread_id,author_id,author_name,body,created,updated FROM ("
            "SELECT p.id,p.thread_id,p.author_id,u.name AS author_name,p.body,p.created,p.updated,"
            "row_number() OVER (PARTITION BY p.thread_id ORDER BY p.created DESC,p.id DESC) AS row_num "
            f"FROM alliance_forum_posts p JOIN users u ON u.id=p.author_id WHERE p.thread_id IN ({placeholders})"
            ") ranked WHERE row_num<=100 ORDER BY thread_id,created,id",
            thread_ids,
        )
        posts_by_thread: dict[str, list[dict[str, Any]]] = {
            thread_id: [] for thread_id in thread_ids
        }
        for post in posts:
            posts_by_thread[str(post["thread_id"])].append(dict(post))
        for thread in threads:
            thread["posts"] = posts_by_thread[str(thread["id"])]
        return threads, has_more

    def alliance_directory_page(
        self, db: Connection, before_id: str | None = None, user_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        membership = (
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (user_id,)).fetchone()
            if user_id
            else None
        )
        own_alliance = str(membership["alliance_id"]) if membership else None
        params: tuple[Any, ...] = (user_id, own_alliance, own_alliance)
        if before_id is not None:
            cursor = db.execute(
                "SELECT lower(tag) AS tag_key,id FROM alliances WHERE id=?", (before_id,)
            ).fetchone()
            if not cursor:
                self.error("Ältere Allianz nicht gefunden.")
            cursor_clause = "WHERE (lower(a.tag)>? OR (lower(a.tag)=? AND a.id>?)) "
            params = (
                user_id,
                own_alliance,
                own_alliance,
                str(cursor["tag_key"]),
                str(cursor["tag_key"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT a.*, (SELECT count(*) FROM members m WHERE m.alliance_id=a.id) AS size, "
                "(SELECT ap.id FROM alliance_applications ap "
                "WHERE ap.alliance_id=a.id AND ap.user_id=?) AS application_id, "
                "d.status AS diplomacy_status,d.accepted AS diplomacy_accepted,"
                "d.proposed_by AS diplomacy_proposed_by "
                "FROM alliances a LEFT JOIN diplomacy d ON "
                "((d.a=? AND d.b=a.id) OR (d.b=? AND d.a=a.id)) "
                + cursor_clause
                + "ORDER BY lower(a.tag),a.id LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def alliance_application_page(
        self,
        db: Connection,
        user_id: str,
        direction: str,
        alliance_id: str | None = None,
        before_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        if direction == "outgoing":
            scope = "ap.user_id=?"
            scope_params: tuple[Any, ...] = (user_id,)
            select = (
                "SELECT ap.id,ap.alliance_id,ap.created,a.name,a.tag "
                "FROM alliance_applications ap JOIN alliances a ON a.id=ap.alliance_id "
            )
        elif direction == "incoming" and alliance_id:
            scope = "ap.alliance_id=?"
            scope_params = (alliance_id,)
            select = (
                "SELECT ap.id,ap.user_id,ap.created,u.name FROM alliance_applications ap "
                "JOIN users u ON u.id=ap.user_id "
            )
        else:
            self.error("Unbekannte Bewerbungsrichtung.")
        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_id is not None:
            cursor = db.execute(
                "SELECT ap.created,ap.id FROM alliance_applications ap WHERE "
                + scope
                + " AND ap.id=?",
                (*scope_params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Bewerbung nicht gefunden.")
            cursor_clause = "AND (ap.created<? OR (ap.created=? AND ap.id<?)) "
            params = (
                *scope_params,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                select
                + "WHERE "
                + scope
                + " "
                + cursor_clause
                + "ORDER BY ap.created DESC,ap.id DESC LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def alliance_invitation_page(
        self,
        db: Connection,
        user_id: str,
        direction: str,
        alliance_id: str | None = None,
        before_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        if direction == "incoming":
            scope = "i.user_id=?"
            scope_params: tuple[Any, ...] = (user_id,)
            select = (
                "SELECT i.id,i.alliance_id,i.user_id,a.name,a.tag "
                "FROM invites i JOIN alliances a ON a.id=i.alliance_id "
            )
            cursor_select = (
                "SELECT lower(a.tag) AS tag_key,a.id AS alliance_key,i.id "
                "FROM invites i JOIN alliances a ON a.id=i.alliance_id "
            )
            order = "lower(a.tag),a.id,i.id"
        elif direction == "outgoing" and alliance_id:
            scope = "i.alliance_id=?"
            scope_params = (alliance_id,)
            select = "SELECT i.id,i.user_id,u.name FROM invites i JOIN users u ON u.id=i.user_id "
            cursor_select = (
                "SELECT lower(u.name) AS name_key,i.id FROM invites i "
                "JOIN users u ON u.id=i.user_id "
            )
            order = "lower(u.name),i.id"
        else:
            self.error("Unbekannte Einladungsrichtung.")
        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_id is not None:
            cursor = db.execute(
                cursor_select + "WHERE " + scope + " AND i.id=?",
                (*scope_params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Einladung nicht gefunden.")
            if direction == "incoming":
                cursor_clause = (
                    "AND (lower(a.tag)>? OR (lower(a.tag)=? AND "
                    "(a.id>? OR (a.id=? AND i.id>?)))) "
                )
                params = (
                    *scope_params,
                    str(cursor["tag_key"]),
                    str(cursor["tag_key"]),
                    str(cursor["alliance_key"]),
                    str(cursor["alliance_key"]),
                    str(cursor["id"]),
                )
            else:
                cursor_clause = "AND (lower(u.name)>? OR (lower(u.name)=? AND i.id>?)) "
                params = (
                    *scope_params,
                    str(cursor["name_key"]),
                    str(cursor["name_key"]),
                    str(cursor["id"]),
                )
        rows = [
            dict(row)
            for row in db.execute(
                select + "WHERE " + scope + " " + cursor_clause + "ORDER BY " + order + " LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def alliance_member_page(
        self, db: Connection, alliance_id: str, before_user_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (alliance_id,)
        if before_user_id is not None:
            cursor = db.execute(
                "SELECT m.role,lower(u.name) AS name_key,m.user_id "
                "FROM members m JOIN users u ON u.id=m.user_id "
                "WHERE m.alliance_id=? AND m.user_id=?",
                (alliance_id, before_user_id),
            ).fetchone()
            if not cursor:
                self.error("Allianzmitglied nicht gefunden.")
            cursor_clause = (
                "AND (m.role>? OR (m.role=? AND (lower(u.name)>? "
                "OR (lower(u.name)=? AND m.user_id>?)))) "
            )
            params = (
                alliance_id,
                str(cursor["role"]),
                str(cursor["role"]),
                str(cursor["name_key"]),
                str(cursor["name_key"]),
                str(cursor["user_id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT m.user_id,m.alliance_id,m.role,u.name "
                "FROM members m JOIN users u ON u.id=m.user_id "
                "WHERE m.alliance_id=? "
                + cursor_clause
                + "ORDER BY m.role,lower(u.name),m.user_id LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def alliance_candidate_page(
        self,
        db: Connection,
        user_id: str,
        alliance_id: str,
        world_id: int,
        before_user_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        visible = sorted(visible_sectors(db, user_id, world_id))
        if not visible:
            return [], False
        visible_clause = "AND (c.x,c.y) IN (" + ",".join("(?,?)" for _ in visible) + ") "
        visibility_params: tuple[Any, ...] = tuple(
            value for coordinates in visible for value in coordinates
        )
        base = (
            "FROM colonies c JOIN users u ON u.id=c.user_id "
            "LEFT JOIN members m ON m.user_id=u.id "
            "WHERE c.world_id=? AND c.is_home=TRUE AND u.id<>? AND m.user_id IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM invites i WHERE i.alliance_id=? AND i.user_id=u.id) "
            + visible_clause
        )
        scope_params: tuple[Any, ...] = (world_id, user_id, alliance_id, *visibility_params)
        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_user_id is not None:
            cursor = db.execute(
                "SELECT lower(u.name) AS name_key,u.id " + base + "AND u.id=?",
                (*scope_params, before_user_id),
            ).fetchone()
            if not cursor:
                self.error("Kandidat nicht mehr verfügbar.")
            cursor_clause = "AND (lower(u.name)>? OR (lower(u.name)=? AND u.id>?)) "
            params = (
                *scope_params,
                str(cursor["name_key"]),
                str(cursor["name_key"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT u.id,u.name,c.x,c.y "
                + base
                + cursor_clause
                + "ORDER BY lower(u.name),u.id LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def player_directory_page(
        self,
        db: Connection,
        observer_id: str,
        world_id: int,
        now: int,
        travel: dict[tuple[int, int], int],
        before_user_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 400:
            self.error("Ungültige Größe für die Spielerliste.")
        cursor_clause = ""
        params: tuple[Any, ...] = (world_id,)
        if before_user_id is not None:
            cursor = db.execute(
                "SELECT p.joined,u.name,u.id FROM colonies c "
                "JOIN profiles p ON p.user_id=c.user_id JOIN users u ON u.id=c.user_id "
                "WHERE c.is_home=TRUE AND c.world_id=? AND c.user_id=?",
                (world_id, before_user_id),
            ).fetchone()
            if not cursor:
                self.error("Spieler-Cursor gehört nicht zu dieser Welt.")
            cursor_clause = (
                "AND (p.joined>? OR (p.joined=? AND (u.name>? " "OR (u.name=? AND u.id>?)))) "
            )
            params = (
                world_id,
                int(cursor["joined"]),
                int(cursor["joined"]),
                str(cursor["name"]),
                str(cursor["name"]),
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "SELECT c.user_id AS id,u.name,c.state,p.joined,wp.faction FROM colonies c "
                "JOIN profiles p ON p.user_id=c.user_id JOIN users u ON u.id=c.user_id "
                "LEFT JOIN world_players wp ON wp.user_id=c.user_id AND wp.world_id=c.world_id "
                "WHERE c.is_home=TRUE AND c.world_id=? "
                + cursor_clause
                + "ORDER BY p.joined,u.name,u.id LIMIT ?",
                (*params, page_size + 1),
            )
        )
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        target_ids = tuple(str(row["id"]) for row in rows)
        intel_by_target: dict[str, Any] = {}
        if target_ids:
            placeholders = ",".join("?" for _ in target_ids)
            intel_by_target = {
                str(row["target_id"]): row
                for row in db.execute(
                    "SELECT target_id,level,observed_at,expires_at,data FROM player_intel "
                    f"WHERE observer_id=? AND world_id=? AND target_id IN ({placeholders})",
                    (observer_id, world_id, *target_ids),
                )
            }
        players: list[dict[str, Any]] = []
        for row in rows:
            other = json.loads(row["state"])
            player = {key: other[key] for key in ("id", "name", "x", "y")} | {
                "protected_until": int(row["joined"]) + 3600,
                "vacation_until": other.get("vacation_until", 0),
                "faction": row["faction"],
                "intel_level": "unknown",
            }
            intel = intel_by_target.get(str(player["id"]))
            if intel:
                player["intel_report"] = {
                    "level": int(intel["level"]),
                    "observed_at": int(intel["observed_at"]),
                    "expires_at": int(intel["expires_at"]),
                    "status": "fresh" if int(intel["expires_at"]) > now else "stale",
                    "data": json.loads(intel["data"]),
                }
                if int(intel["expires_at"]) > now:
                    player["intel_level"] = int(intel["level"])
            player["travel_seconds"] = travel.get((int(player["x"]), int(player["y"])))
            players.append(player)
        return players, has_more

    def alliance_supply_target_page(
        self,
        db: Connection,
        user_id: str,
        alliance_id: str,
        world_id: int,
        before_colony_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für Allianzversorgungsziele.")
        member = self.member(db, user_id)
        if not member or str(member["alliance_id"]) != alliance_id:
            self.error("Du gehörst nicht mehr zu dieser Allianz.")
        cursor_clause = ""
        params: tuple[Any, ...] = (alliance_id, user_id, world_id)
        if before_colony_id is not None:
            cursor = db.execute(
                "SELECT lower(u.name) AS name_key,c.colony_id "
                "FROM members m JOIN colonies c ON c.user_id=m.user_id "
                "JOIN users u ON u.id=m.user_id "
                "WHERE m.alliance_id=? AND m.user_id<>? AND c.world_id=? "
                "AND c.is_home=TRUE AND c.colony_id=?",
                (*params, before_colony_id),
            ).fetchone()
            if not cursor:
                self.error("Allianzversorgungsziel nicht gefunden.")
            cursor_clause = "AND (lower(u.name)>? OR (lower(u.name)=? AND c.colony_id>?)) "
            params = (
                *params,
                str(cursor["name_key"]),
                str(cursor["name_key"]),
                str(cursor["colony_id"]),
            )
        rows = list(
            db.execute(
                "SELECT c.colony_id,c.world_id,c.x,c.y,c.state,u.name AS player_name "
                "FROM members m JOIN colonies c ON c.user_id=m.user_id AND c.is_home=TRUE "
                "JOIN users u ON u.id=m.user_id "
                "WHERE m.alliance_id=? AND m.user_id<>? AND c.world_id=? "
                + cursor_clause
                + "ORDER BY lower(u.name),c.colony_id LIMIT ?",
                (*params, page_size + 1),
            )
        )
        has_more = len(rows) > page_size
        entries = [
            {
                "colony_id": row["colony_id"],
                "world_id": int(row["world_id"]),
                "x": int(row["x"]),
                "y": int(row["y"]),
                "name": json.loads(row["state"]).get("colony_name", row["player_name"]),
            }
            for row in rows[:page_size]
        ]
        return entries, has_more

    def admin_user_page(
        self,
        db: Connection,
        before_user_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für die Moderationsliste.")
        cursor_clause = ""
        params: tuple[Any, ...] = ()
        if before_user_id is not None:
            cursor = db.execute(
                "SELECT u.name,u.id FROM users u JOIN profiles p ON p.user_id=u.id " "WHERE u.id=?",
                (before_user_id,),
            ).fetchone()
            if not cursor:
                self.error("Spieler-Cursor nicht gefunden.")
            cursor_clause = "WHERE (u.name>? OR (u.name=? AND u.id>?)) "
            params = (str(cursor["name"]), str(cursor["name"]), str(cursor["id"]))
        rows = list(
            db.execute(
                "SELECT u.id,u.name,p.role,p.banned,p.muted_until "
                "FROM users u JOIN profiles p ON p.user_id=u.id "
                + cursor_clause
                + "ORDER BY u.name,u.id LIMIT ?",
                (*params, page_size + 1),
            )
        )
        return [dict(row) for row in rows[:page_size]], len(rows) > page_size

    def moderation_case_page(
        self,
        db: Connection,
        before_case_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für die Moderationsfälle.")
        cursor_clause = ""
        params: tuple[Any, ...] = ()
        if before_case_id is not None:
            cursor = db.execute(
                "WITH moderation_queue AS ("
                "SELECT id,created FROM moderation_cases WHERE status='open' UNION ALL "
                "SELECT id,created FROM account_ban_appeals WHERE status='open') "
                "SELECT created,id FROM moderation_queue WHERE id=?",
                (before_case_id,),
            ).fetchone()
            if not cursor:
                self.error("Fall-Cursor nicht gefunden.")
            cursor_clause = "AND (c.created<? OR (c.created=? AND c.id<?)) "
            params = (
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "WITH moderation_queue AS ("
                "SELECT c.id,c.case_type,c.reporter_id,c.target_user_id,c.message_id,"
                "c.world_id,c.reason,c.created FROM moderation_cases c WHERE c.status='open' "
                "UNION ALL SELECT b.id,'account_ban_appeal',b.user_id,b.user_id,NULL,NULL,"
                "b.reason,b.created FROM account_ban_appeals b WHERE b.status='open') "
                "SELECT c.id,c.case_type,c.reporter_id,reporter.name AS reporter_name,"
                "c.target_user_id,target.name AS target_name,c.message_id,m.channel,m.body,"
                "c.world_id,c.reason,c.created FROM moderation_queue c "
                "JOIN users reporter ON reporter.id=c.reporter_id "
                "JOIN users target ON target.id=c.target_user_id "
                "LEFT JOIN messages m ON m.id=c.message_id "
                + ("WHERE " + cursor_clause[4:] if cursor_clause else "")
                + "ORDER BY c.created DESC,c.id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        return [dict(row) for row in rows[:page_size]], len(rows) > page_size

    def admin_failure_page(
        self,
        db: Connection,
        before_failure_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für die Fehlerliste.")
        cursor_clause = ""
        params: tuple[Any, ...] = ()
        if before_failure_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM job_failures WHERE id=?", (before_failure_id,)
            ).fetchone()
            if not cursor:
                self.error("Auftragsfehler-Cursor nicht gefunden.")
            cursor_clause = "WHERE (created<? OR (created=? AND id<?)) "
            params = (
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "SELECT id,user_id,job_id,attempts,error,created FROM job_failures "
                + cursor_clause
                + "ORDER BY created DESC,id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        return [dict(row) for row in rows[:page_size]], len(rows) > page_size

    def admin_audit_page(
        self,
        db: Connection,
        before_audit_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für das Auditprotokoll.")
        cursor_clause = ""
        params: tuple[Any, ...] = ()
        if before_audit_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM audit WHERE id=?", (before_audit_id,)
            ).fetchone()
            if not cursor:
                self.error("Audit-Cursor nicht gefunden.")
            cursor_clause = "WHERE (created<? OR (created=? AND id<?)) "
            params = (int(cursor["created"]), int(cursor["created"]), str(cursor["id"]))
        rows = list(
            db.execute(
                "SELECT id,action,target,created FROM audit "
                + cursor_clause
                + "ORDER BY created DESC,id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        return [dict(row) for row in rows[:page_size]], len(rows) > page_size

    def live_event_page(
        self,
        db: Connection,
        now: int,
        before_event_id: str | None = None,
        page_size: int = 50,
        *,
        world_id: int = 1,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für die Ereignisliste.")
        cursor_clause = ""
        params: tuple[Any, ...] = (world_id, now)
        if before_event_id is not None:
            cursor = db.execute(
                "SELECT starts,id FROM events WHERE id=? AND world_id=?",
                (before_event_id, world_id),
            ).fetchone()
            if not cursor:
                self.error("Ereignis-Cursor nicht gefunden.")
            cursor_clause = "AND (starts<? OR (starts=? AND id<?)) "
            params = (
                world_id,
                now,
                int(cursor["starts"]),
                int(cursor["starts"]),
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "SELECT e.id,e.name,e.starts,e.ends,e.bonus,e.warning_hours,e.end_starts,"
                "e.end_bonus,e.goal_score,r.version AS rules_version,r.digest AS rules_digest "
                "FROM events e LEFT JOIN live_event_rules r ON r.event_id=e.id "
                "WHERE e.world_id=? AND e.ends>? "
                + cursor_clause.replace("starts", "e.starts")
                + "ORDER BY e.starts DESC,e.id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        best = db.execute(
            "SELECT COALESCE(MAX(score),0) AS score FROM ("
            "SELECT SUM(ranking_score) AS score FROM colonies WHERE world_id=? GROUP BY user_id)",
            (world_id,),
        ).fetchone()
        best_score = int(best["score"] or 0)
        active_events = [
            dict(row)
            for row in db.execute(
                "SELECT starts,ends,bonus,end_starts,end_bonus FROM events "
                "WHERE world_id=? AND starts<=? AND ends>?",
                (world_id, now, now),
            )
        ]
        world_active_bonus = live_events.active_bonus_total(active_events, now)
        events = []
        for row in rows[:page_size]:
            event = dict(row)
            event["phase"] = live_events.phase(event, now)
            event["active_bonus"] = live_events.active_bonus(event, now)
            event["world_active_bonus"] = world_active_bonus
            event["goal_progress"] = best_score
            event["goal_reached"] = bool(
                event["goal_score"] and best_score >= int(event["goal_score"])
            )
            events.append(event)
        return events, len(rows) > page_size

    def message_page(
        self,
        db: Connection,
        user: str,
        world_id: int,
        alliance_id: str,
        channel: str,
        before_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        if channel == "world":
            scope = "m.channel='world' AND m.world_id=?"
            scope_params: tuple[Any, ...] = (world_id,)
        elif channel == "alliance":
            if not alliance_id:
                return [], False
            scope = "m.channel='alliance' AND m.recipient=?"
            scope_params = (alliance_id,)
        elif channel == "private":
            scope = "m.channel='private' AND (m.recipient=? OR m.sender=?)"
            scope_params = (user, user)
        else:
            self.error("Unbekannter Nachrichtenkanal.")

        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_id is not None:
            cursor = db.execute(
                "SELECT m.created,m.id FROM messages m WHERE m.hidden=0 AND "
                + scope
                + " AND m.id=?",
                (*scope_params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Ältere Nachricht nicht gefunden.")
            cursor_clause = "AND (m.created<? OR (m.created=? AND m.id<?)) "
            params = (
                *scope_params,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT m.id,m.sender,u.name,m.channel,m.recipient,m.body,m.created "
                "FROM messages m JOIN users u ON u.id=m.sender "
                "WHERE m.hidden=0 AND "
                + scope
                + " "
                + cursor_clause
                + "ORDER BY m.created DESC,m.id DESC LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def system_announcement_page(
        self,
        db: Connection,
        world_id: int,
        before_id: str | None = None,
        now: int | None = None,
        include_scheduled: bool = False,
    ) -> tuple[list[dict[str, Any]], bool]:
        publishable = "1=1" if include_scheduled else "(a.publish_at=0 OR a.publish_at<=?)"
        scope = "(a.world_id IS NULL OR a.world_id=?) AND a.archived=0 AND " + publishable
        params: tuple[Any, ...] = (world_id,)
        if not include_scheduled:
            params = (*params, int(now or time.time()))
        cursor_clause = ""
        if before_id is not None:
            cursor = db.execute(
                "SELECT CASE WHEN a.publish_at=0 THEN a.created ELSE a.publish_at END AS "
                "effective_at,a.id FROM system_announcements a WHERE " + scope + " AND a.id=?",
                (*params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Ankündigungs-Cursor ist nicht sichtbar.")
            effective_at = int(cursor["effective_at"])
            cursor_clause = (
                "AND (CASE WHEN a.publish_at=0 THEN a.created ELSE a.publish_at END<? "
                "OR (CASE WHEN a.publish_at=0 THEN a.created ELSE a.publish_at END=? "
                "AND a.id<?)) "
            )
            params = (
                *params,
                effective_at,
                effective_at,
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "SELECT a.id,a.world_id,a.author_id,u.name AS author_name,a.title,a.body,a.created,"
                "CASE WHEN a.publish_at=0 THEN a.created ELSE a.publish_at END AS publish_at,"
                "a.emergency "
                "FROM system_announcements a JOIN users u ON u.id=a.author_id WHERE "
                + scope
                + " "
                + cursor_clause
                + "ORDER BY CASE WHEN a.publish_at=0 THEN a.created ELSE a.publish_at END DESC,"
                "a.id DESC LIMIT 51",
                params,
            )
        )
        entries = [dict(row) for row in rows[:50]]
        for entry in entries:
            entry["emergency"] = bool(entry["emergency"])
        return entries, len(rows) > 50

    def system_mail_page(
        self, db: Connection, user_id: str, before_id: str | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        params: tuple[Any, ...] = (user_id,)
        cursor_clause = ""
        if before_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM system_mail WHERE recipient_id=? AND id=?",
                (*params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Postfach-Cursor ist nicht verfügbar.")
            cursor_clause = "AND (m.created<? OR (m.created=? AND m.id<?)) "
            params = (
                *params,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = list(
            db.execute(
                "SELECT m.id,m.title,m.body,m.created,m.read_at,u.name AS author_name "
                "FROM system_mail m JOIN users u ON u.id=m.author_id "
                "WHERE m.recipient_id=? "
                + cursor_clause
                + "ORDER BY m.created DESC,m.id DESC LIMIT 51",
                params,
            )
        )
        return [dict(row) for row in rows[:50]], len(rows) > 50

    def market_offer_page(
        self,
        db: Connection,
        world_id: int,
        now: int,
        before_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (world_id, now)
        if before_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM offers WHERE world_id=? AND id=?",
                (world_id, before_id),
            ).fetchone()
            if not cursor:
                self.error("Marktangebot nicht gefunden.")
            cursor_clause = "AND (o.created<? OR (o.created=? AND o.id<?)) "
            params = (
                world_id,
                now,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT o.*,u.name FROM offers o JOIN users u ON u.id=o.owner "
                "WHERE o.world_id=? AND o.status='open' AND o.expires>? "
                + cursor_clause
                + "ORDER BY o.created DESC,o.id DESC LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def ledger(self, db: Connection, state: dict[str, Any], action: str, before: list[int]) -> None:
        from .game import identity

        self.game.save(db, state)
        db.execute(
            "INSERT INTO ledger VALUES (?,?,?,?,?,?)",
            (
                identity(),
                state["id"],
                int(time.time()),
                action,
                json.dumps(before),
                json.dumps(state["resources"]),
            ),
        )

    def credit(
        self, db: Connection, user: str, resources: list[int], label: str, at: int | None = None
    ) -> None:
        state = self.game.read(db, user)
        self.credit_state(db, state, resources, label, at)

    def credit_colony(
        self, db: Connection, colony_id: str, resources: list[int], label: str, at: int
    ) -> None:
        state = self.game.read_colony(db, colony_id)
        self.credit_state(db, state, resources, label, at)

    def credit_state(
        self,
        db: Connection,
        state: dict[str, Any],
        resources: list[int],
        label: str,
        at: int | None,
    ) -> None:
        before = list(state["resources"])
        self.game.produce(state, int(time.time()) if at is None else at)
        # Deliveries go to a claimable overflow warehouse, never silently disappear.
        cap = 2000 + state["buildings"]["storage"] * 2000
        reserve = state.setdefault("reserve", [0, 0, 0])
        for i, value in enumerate(resources):
            room = max(0, cap - state["resources"][i])
            state["resources"][i] += min(room, value)
            reserve[i] += max(0, value - room)
        self.game.report(
            state,
            label,
            f"{resources[0]} Holz · {resources[1]} Stein · {resources[2]} Erz. Übermengen liegen im Reserve-Lager.",
        )
        self.ledger(db, state, label, before)

    def dispatch_colony_supply(
        self,
        db: Connection,
        state: dict[str, Any],
        payload: dict[str, Any],
        *,
        at: int | None = None,
        route_id: str | None = None,
    ) -> None:
        from .game import identity

        destination = self.text(payload, "key")
        target_row = db.execute(
            "SELECT colony_id,user_id,world_id,x,y,state FROM colonies WHERE colony_id=?",
            (destination,),
        ).fetchone()
        source_row = db.execute(
            "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
            (state["colony_id"], state["id"]),
        ).fetchone()
        if (
            not target_row
            or not source_row
            or target_row["user_id"] != state["id"]
            or target_row["world_id"] != source_row["world_id"]
        ):
            self.error("Versorgung ist nur zwischen eigenen Kolonien derselben Welt möglich.")
        if destination == state["colony_id"]:
            self.error("Wähle eine andere eigene Kolonie als Ziel.")
        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")

        unit_catalog = self.game.unit_catalog_for_world(db, int(source_row["world_id"]))

        army = payload.get("army")
        if (
            not isinstance(army, dict)
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Wähle mindestens einen verfügbaren Träger.")

        cargo = payload.get("resources")
        if (
            not isinstance(cargo, list)
            or len(cargo) != 3
            or any(
                type(amount) is not int or amount < 0 or amount > state["resources"][index]
                for index, amount in enumerate(cargo)
            )
        ):
            self.error("Die Rohstofffracht ist ungültig oder nicht verfügbar.")
        from . import items as generic_items
        from .neutral_market import GOODS, RESOURCE_IDS, _goods_inventory, depot_capacity

        source_goods = _goods_inventory(state)

        goods = payload.get("goods", {})
        if not isinstance(goods, dict) or any(
            not isinstance(good_id, str)
            or good_id not in GOODS
            or good_id in RESOURCE_IDS
            or type(amount) is not int
            or amount < 0
            or amount > int(source_goods.get(good_id, 0))
            for good_id, amount in goods.items()
        ):
            self.error("Die Warenfracht ist ungültig oder nicht verfügbar.")
        goods = {good_id: amount for good_id, amount in goods.items() if amount > 0}
        source_items = generic_items.inventory(state)
        items = payload.get("items", {})
        if not isinstance(items, dict) or any(
            not isinstance(item_id, str)
            or item_id not in generic_items.ITEMS
            or type(amount) is not int
            or amount < 0
            or amount > int(source_items.get(item_id, 0))
            for item_id, amount in items.items()
        ):
            self.error("Die Gegenstandsfracht ist ungültig oder nicht verfügbar.")
        items = {item_id: amount for item_id, amount in items.items() if amount > 0}
        if sum(cargo) + sum(goods.values()) + sum(items.values()) < 1:
            self.error("Wähle mindestens einen Rohstoff oder eine Ware für die Versorgung.")
        target = json.loads(target_row["state"])
        target_goods = _goods_inventory(target)
        inbound = target.setdefault("goods_inbound", {})
        inventory = target_goods
        capacity_per_kind = depot_capacity(target)
        for good_id, amount in goods.items():
            if type(inbound.get(good_id, 0)) is not int or inbound.get(good_id, 0) < 0:
                self.error("Die reservierte Warenfracht der Zielkolonie ist ungültig.")
            if (
                int(inventory.get(good_id, 0)) + int(inbound.get(good_id, 0)) + amount
                > capacity_per_kind
            ):
                self.error("Im Zieldepot ist nicht genug Platz für diese Warenfracht.")
        generic_items.reserve_incoming(target, items)
        capacity = self.game.army_transport_capacity(
            db, int(source_row["world_id"]), army, int(state["tech"]["logistics"])
        )
        cargo_weight = (
            sum(cargo)
            + sum(goods.values())
            + sum(items.values()) * generic_items.RULES.transport_weight
        )
        if cargo_weight > capacity:
            self.error(f"Transportkapazität reicht nicht aus (maximal {capacity}).")

        movement = self.reserve_movement_fuel(
            db,
            state,
            (state["x"], state["y"]),
            (target["x"], target["y"]),
            army,
            additional_ore_cost=cargo[2],
        )
        travel = int(movement["travel_seconds"])
        if "smuggler_navigation" in state.get("faction_research", []):
            travel = max(5, (travel * 90 + 99) // 100)
        state["resources"] = [current - sent for current, sent in zip(state["resources"], cargo)]
        source_inventory = dict(state.get("goods_inventory", {}))
        for good_id, amount in goods.items():
            source_inventory[good_id] = int(source_inventory.get(good_id, 0)) - amount
            inbound[good_id] = int(inbound.get(good_id, 0)) + amount
        state["goods_inventory"] = source_inventory
        target["goods_inbound"] = inbound
        source_items_inventory = dict(source_items)
        for item_id, amount in items.items():
            source_items_inventory[item_id] -= amount
        state["item_inventory"] = source_items_inventory
        self.game.save(db, target)
        for unit, count in army.items():
            state["units"][unit] = state["units"].get(unit, 0) - count
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "colony_supply",
                "key": destination,
                "due": (int(time.time()) if at is None else at) + travel,
                "travel": travel,
                "movement": movement,
                "army": army,
                "loot": cargo,
                "goods_cargo": goods,
                "item_cargo": items,
                "label": "Versorgung zu " + target.get("colony_name", target["name"]),
                "route_id": route_id,
            }
        )
        self.audit(
            db,
            state["id"],
            "colony_supply_dispatch",
            destination,
            source=state["colony_id"],
            cargo=cargo,
            goods=goods,
            items=items,
            cargo_weight=cargo_weight,
            carriers=army,
            travel=travel,
        )

    def dispatch_alliance_supply(
        self, db: Connection, state: dict[str, Any], payload: dict[str, Any]
    ) -> None:
        from .game import identity

        target_id = self.text(payload, "key")
        target_row = db.execute(
            "SELECT colony_id,user_id,world_id,x,y,state FROM colonies "
            "WHERE colony_id=? AND is_home=TRUE",
            (target_id,),
        ).fetchone()
        source_row = db.execute(
            "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
            (state["colony_id"], state["id"]),
        ).fetchone()
        source_member = self.member(db, state["id"])
        target_member = self.member(db, target_row["user_id"]) if target_row else None
        if (
            not target_row
            or target_row["user_id"] == state["id"]
            or not source_row
            or target_row["world_id"] != source_row["world_id"]
            or not source_member
            or not target_member
            or source_member["alliance_id"] != target_member["alliance_id"]
        ):
            self.error("Allianzversorgung erfordert ein verbündetes Mitglied derselben Welt.")
        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")

        unit_catalog = self.game.unit_catalog_for_world(db, int(source_row["world_id"]))

        army = payload.get("army")
        if (
            not isinstance(army, dict)
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Wähle mindestens einen verfügbaren Träger.")
        cargo = payload.get("resources")
        if (
            not isinstance(cargo, list)
            or len(cargo) != 3
            or any(
                type(amount) is not int or amount < 0 or amount > state["resources"][index]
                for index, amount in enumerate(cargo)
            )
            or sum(cargo) < 1
        ):
            self.error("Wähle mindestens einen verfügbaren Rohstoff für die Versorgung.")
        capacity = self.game.army_transport_capacity(
            db, int(source_row["world_id"]), army, int(state["tech"]["logistics"])
        )
        if sum(cargo) > capacity:
            self.error(f"Transportkapazität reicht nicht aus (maximal {capacity}).")

        target_state = json.loads(target_row["state"])
        movement = self.reserve_movement_fuel(
            db,
            state,
            (state["x"], state["y"]),
            (target_row["x"], target_row["y"]),
            army,
            additional_ore_cost=cargo[2],
        )
        travel = int(movement["travel_seconds"])
        state["resources"] = [current - sent for current, sent in zip(state["resources"], cargo)]
        for unit, count in army.items():
            state["units"][unit] = state["units"].get(unit, 0) - count
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "alliance_supply",
                "key": target_id,
                "target_user": target_row["user_id"],
                "alliance_id": source_member["alliance_id"],
                "due": int(time.time()) + travel,
                "travel": travel,
                "movement": movement,
                "army": army,
                "loot": cargo,
                "label": "Allianzversorgung zu "
                + target_state.get("colony_name", target_state["name"]),
            }
        )
        self.audit(
            db,
            state["id"],
            "alliance_supply_dispatch",
            target_id,
            recipient=target_row["user_id"],
            cargo=cargo,
            carriers=army,
            travel=travel,
        )

    def cancel_alliance_supply(
        self, db: Connection, state: dict[str, Any], payload: dict[str, Any]
    ) -> None:
        job_id = self.text(payload, "key")
        shipment = next(
            (
                job
                for job in state["jobs"]
                if job["id"] == job_id and job["kind"] == "alliance_supply"
            ),
            None,
        )
        if not shipment or int(shipment["due"]) <= int(time.time()):
            self.error("Diese Allianzversorgung ist nicht mehr abbrechbar.")
        before = list(state["resources"])
        cap = 2000 + state["buildings"]["storage"] * 2000
        reserve = state.setdefault("reserve", [0, 0, 0])
        for index, amount in enumerate(shipment["loot"]):
            room = max(0, cap - state["resources"][index])
            state["resources"][index] += min(room, amount)
            reserve[index] += max(0, amount - room)
        for unit, count in shipment["army"].items():
            state["units"][unit] = state["units"].get(unit, 0) + count
        state["jobs"] = [job for job in state["jobs"] if job["id"] != job_id]
        self.game.report(
            state,
            "Allianzversorgung abgebrochen",
            "Fracht und Träger wurden zurückgegeben. Übermengen liegen im Reserve-Lager.",
        )
        self.audit(
            db,
            state["id"],
            "alliance_supply_cancelled",
            job_id,
            recipient=shipment["target_user"],
            cargo=shipment["loot"],
            carriers=shipment["army"],
        )
        self.ledger(db, state, "alliance_supply_cancelled", before)

    def _return_allied_garrison(
        self,
        db: Connection,
        row: Any,
        now: int,
        *,
        reason: str,
        source_state: dict[str, Any] | None = None,
    ) -> bool:
        """Remove one stationed army and schedule its intact return at its source."""
        from .game import identity

        claimed = db.execute(
            "DELETE FROM terra_allied_garrisons WHERE id=? AND status='active' RETURNING id",
            (row["id"],),
        ).fetchone()
        if not claimed:
            return False
        source = db.execute(
            "SELECT colony_id,x,y,world_id FROM colonies WHERE colony_id=? AND user_id=?",
            (row["source_colony_id"], row["contributor_id"]),
        ).fetchone()
        host = db.execute(
            "SELECT x,y,world_id FROM colonies WHERE colony_id=? AND user_id=?",
            (row["host_colony_id"], row["host_user_id"]),
        ).fetchone()
        army = json.loads(row["army"])
        if source and host and source["world_id"] == host["world_id"]:
            if source_state is None:
                source_state = self.game.read_colony(db, str(source["colony_id"]))
            travel = int(row["travel_seconds"] or 0) or self.game.travel_time(
                db,
                (int(host["x"]), int(host["y"])),
                (int(source["x"]), int(source["y"])),
                int(source["world_id"]),
                army,
            )
            source_state.setdefault("jobs", []).append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": str(source["colony_id"]),
                    "label": "Alliierte Garnison kehrt zurück",
                    "due": now + travel,
                    "army": army,
                    "loot": [0, 0, 0],
                }
            )
            self.game.report(source_state, "Garnison kehrt zurück", reason)
            self.game.save(db, source_state)
            self.audit(
                db,
                str(row["contributor_id"]),
                "alliance_garrison_return",
                str(row["id"]),
                host=str(row["host_colony_id"]),
                army=army,
                reason=reason,
            )
        else:
            raise RuntimeError("Allied garrison source or host colony is missing")
        return True

    def _recall_alliance_garrisons_for_member(
        self, db: Connection, user_id: str, alliance_id: str, now: int
    ) -> None:
        rows = db.execute(
            "SELECT * FROM terra_allied_garrisons WHERE alliance_id=? AND status='active' "
            "AND (host_user_id=? OR contributor_id=?) ORDER BY id",
            (alliance_id, user_id, user_id),
        ).fetchall()
        for row in rows:
            self._return_allied_garrison(
                db, row, now, reason="Eine beteiligte Person hat die Allianz verlassen."
            )

    def alliance_garrison_command(
        self, db: Connection, state: dict[str, Any], action: str, payload: dict[str, Any]
    ) -> None:
        from . import terra_garrison
        from .game import identity

        user = str(state["id"])
        now = int(time.time())
        member = self.member(db, user)
        if not member:
            self.error("Alliierte Garnisonen erfordern eine Allianzmitgliedschaft.")
        alliance_id = str(member["alliance_id"])
        if action == "alliance_garrison_policy":
            home = db.execute(
                "SELECT colony_id,world_id FROM colonies "
                "WHERE user_id=? AND colony_id=? AND is_home=TRUE",
                (user, state["colony_id"]),
            ).fetchone()
            if not home:
                self.error("Die Freigabe kann nur an deiner Heimatkolonie geändert werden.")
            enabled = payload.get("enabled")
            capacity = payload.get("capacity", terra_garrison.MAX_CAPACITY)
            if type(enabled) is not bool or type(capacity) is not int or not 1 <= capacity <= 300:
                self.error("Ungültige Garnisonsfreigabe oder Kapazität.")
            occupied_rows = db.execute(
                "SELECT army FROM terra_allied_garrisons WHERE host_colony_id=? "
                "AND status IN ('travelling','active')",
                (home["colony_id"],),
            ).fetchall()
            occupied = sum(sum(json.loads(row["army"]).values()) for row in occupied_rows)
            if occupied > capacity:
                self.error("Die neue Kapazität unterschreitet bereits gebundene Garnisonen.")
            if not enabled:
                for row in db.execute(
                    "SELECT * FROM terra_allied_garrisons WHERE host_colony_id=? "
                    "AND alliance_id=? AND status='active' ORDER BY id",
                    (home["colony_id"], alliance_id),
                ).fetchall():
                    self._return_allied_garrison(
                        db, row, now, reason="Der Gastgeber hat die Freigabe beendet."
                    )
            db.execute(
                "INSERT INTO terra_allied_garrison_policies "
                "(home_colony_id,host_user_id,alliance_id,enabled,capacity,rule_version,updated) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(home_colony_id) DO UPDATE SET "
                "host_user_id=excluded.host_user_id,alliance_id=excluded.alliance_id,"
                "enabled=excluded.enabled,capacity=excluded.capacity,"
                "rule_version=excluded.rule_version,updated=excluded.updated",
                (
                    home["colony_id"],
                    user,
                    alliance_id,
                    enabled,
                    capacity,
                    terra_garrison.VERSION,
                    now,
                ),
            )
            self.audit(db, user, action, str(home["colony_id"]), enabled=enabled, capacity=capacity)
            return

        if action == "alliance_garrison_station":
            target_id = self.text(payload, "key")
            target = db.execute(
                "SELECT colony_id,user_id,world_id,x,y FROM colonies "
                "WHERE colony_id=? AND is_home=TRUE",
                (target_id,),
            ).fetchone()
            source = db.execute(
                "SELECT colony_id,world_id,x,y FROM colonies WHERE colony_id=? AND user_id=?",
                (state["colony_id"], user),
            ).fetchone()
            target_member = self.member(db, str(target["user_id"])) if target else None
            policy_lock = " FOR UPDATE" if db.postgres else ""
            policy = db.execute(
                "SELECT * FROM terra_allied_garrison_policies "
                "WHERE home_colony_id=? AND enabled=TRUE" + policy_lock,
                (target_id,),
            ).fetchone()
            if (
                not target
                or not source
                or target["user_id"] == user
                or int(target["world_id"]) != int(source["world_id"])
                or not target_member
                or target_member["alliance_id"] != alliance_id
                or not policy
                or policy["host_user_id"] != target["user_id"]
                or policy["alliance_id"] != alliance_id
            ):
                self.error(
                    "Das Ziel muss eine freigegebene Heimatkolonie eines Allianzmitglieds derselben Welt sein."
                )
            if len(state["jobs"]) >= self.game.terra_mission_limit(state):
                self.error(
                    f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen."
                )
            unit_catalog = self.game.unit_catalog_for_world(db, int(source["world_id"]))
            army = payload.get("army")
            if (
                not isinstance(army, dict)
                or any(
                    unit not in unit_catalog
                    or type(count) is not int
                    or count < 0
                    or count > state["units"].get(unit, 0)
                    for unit, count in army.items()
                )
                or sum(army.values()) < 1
            ):
                self.error("Wähle mindestens eine verfügbare Einheit für die Garnison.")
            army = {unit: count for unit, count in army.items() if count > 0}
            stationed = db.execute(
                "SELECT army FROM terra_allied_garrisons "
                "WHERE host_colony_id=? AND status IN ('travelling','active')",
                (target_id,),
            ).fetchall()
            committed = sum(sum(json.loads(row["army"]).values()) for row in stationed)
            if committed + sum(army.values()) > int(policy["capacity"]):
                self.error("Die freigegebene Garnisonskapazität ist ausgeschöpft.")
            movement = self.reserve_movement_fuel(
                db,
                state,
                (int(source["x"]), int(source["y"])),
                (int(target["x"]), int(target["y"])),
                army,
            )
            travel = int(movement["travel_seconds"])
            for unit, count in army.items():
                state["units"][unit] -= count
            job_id = identity()
            db.execute(
                "INSERT INTO terra_allied_garrisons "
                "(id,world_id,alliance_id,host_user_id,host_colony_id,contributor_id,"
                "source_colony_id,army,tactics,rule_version,status,created,travel_seconds) "
                "VALUES (?,?,?,?,?,?,?,?,?,?, 'travelling',?,?)",
                (
                    job_id,
                    int(target["world_id"]),
                    alliance_id,
                    str(target["user_id"]),
                    target_id,
                    user,
                    str(source["colony_id"]),
                    json.dumps(army, sort_keys=True),
                    int(state["tech"]["tactics"]),
                    terra_garrison.VERSION,
                    now,
                    travel,
                ),
            )
            state["jobs"].append(
                {
                    "id": job_id,
                    "kind": "alliance_garrison",
                    "key": target_id,
                    "host_user": str(target["user_id"]),
                    "alliance_id": alliance_id,
                    "due": now + travel,
                    "travel": travel,
                    "movement": movement,
                    "army": army,
                    "tactics": int(state["tech"]["tactics"]),
                    "rule_version": terra_garrison.VERSION,
                    "label": "Garnison zu " + target_id,
                }
            )
            self.audit(db, user, action, target_id, army=army, travel=travel)
            return

        garrison_id = self.text(payload, "key")
        row = db.execute(
            "SELECT * FROM terra_allied_garrisons WHERE id=? AND status='active' "
            "AND (host_user_id=? OR contributor_id=?)",
            (garrison_id, user, user),
        ).fetchone()
        if not row:
            self.error("Aktive alliierte Garnison nicht gefunden.")
        if self._return_allied_garrison(
            db,
            row,
            now,
            reason="Der Gastgeber oder Entsender hat den Rückruf ausgelöst.",
            source_state=(state if str(row["contributor_id"]) == user else None),
        ):
            self.audit(db, user, action, garrison_id)

    def _terra_attack_refund(
        self,
        db: Connection,
        attack_id: str,
        user_id: str,
        now: int,
        current_state: dict[str, Any] | None = None,
    ) -> None:
        """Return a withdrawn/cancelled wing and remove its scheduled trigger atomically."""
        wing = db.execute(
            "SELECT w.*,c.state FROM terra_alliance_attack_wings w "
            "JOIN colonies c ON c.colony_id=w.colony_id WHERE w.attack_id=? AND w.user_id=?",
            (attack_id, user_id),
        ).fetchone()
        if not wing or wing["status"] != "active":
            return
        colony = (
            current_state
            if current_state is not None and current_state["id"] == user_id
            else json.loads(wing["state"])
        )
        colony["jobs"] = [
            job for job in colony.get("jobs", []) if job.get("alliance_attack_id") != attack_id
        ]
        army = json.loads(wing["army"])
        for unit, count in army.items():
            colony["units"][unit] = colony["units"].get(unit, 0) + count
        self.game.report(
            colony,
            "Allianzangriff zurückgezogen",
            "Deine bereitgestellten Truppen wurden vollständig zurückgegeben.",
        )
        self.game.save(db, colony)
        db.execute(
            "UPDATE terra_alliance_attack_wings SET status='withdrawn' "
            "WHERE attack_id=? AND user_id=? AND status='active'",
            (attack_id, user_id),
        )
        self.audit(db, user_id, "alliance_attack_withdrawn", attack_id, army=army)

    def terra_alliance_attack_command(
        self, db: Connection, state: dict[str, Any], action: str, payload: dict[str, Any]
    ) -> None:
        """Create, join, withdraw from, or cancel a Terra alliance attack."""
        from . import terra_alliance, terra_combat
        from .game import identity

        user, now = str(state["id"]), int(time.time())
        world_id = int(state["world_id"])
        member = self.member(db, user)
        if not member:
            self.error("Ein Allianzangriff erfordert eine aktive Allianzmitgliedschaft.")
        alliance_id = str(member["alliance_id"])

        if action == "alliance_attack_withdraw":
            attack_id = self.text(payload, "key", 1, 100)
            attack = db.execute(
                "SELECT * FROM terra_alliance_attacks WHERE id=? AND alliance_id=? "
                "AND world_id=? AND status='assembling' AND join_until>?",
                (attack_id, alliance_id, world_id, now),
            ).fetchone()
            if not attack:
                self.error("Dieser Allianzangriff ist nicht mehr offen.")
            if str(attack["leader_id"]) == user:
                self.error("Die Einsatzleitung muss den gesamten Allianzangriff zurückziehen.")
            self._terra_attack_refund(db, attack_id, user, now, state)
            remaining = db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings "
                "WHERE attack_id=? AND status='active'",
                (attack_id,),
            ).fetchone()[0]
            if remaining == 0:
                db.execute(
                    "UPDATE terra_alliance_attacks SET status='cancelled',resolved_at=? WHERE id=?",
                    (now, attack_id),
                )
                terra_combat.discard_mission(db, attack_id)
            return

        if action == "alliance_attack_cancel":
            attack_id = self.text(payload, "key", 1, 100)
            attack = db.execute(
                "SELECT * FROM terra_alliance_attacks WHERE id=? AND alliance_id=? "
                "AND world_id=? AND leader_id=? AND status='assembling' AND join_until>?",
                (attack_id, alliance_id, world_id, user, now),
            ).fetchone()
            if not attack:
                self.error("Nur die Einsatzleitung kann einen offenen Angriff zurückziehen.")
            wings = db.execute(
                "SELECT user_id FROM terra_alliance_attack_wings "
                "WHERE attack_id=? AND status='active' ORDER BY user_id",
                (attack_id,),
            ).fetchall()
            for wing in wings:
                self._terra_attack_refund(
                    db,
                    attack_id,
                    str(wing["user_id"]),
                    now,
                    state if str(wing["user_id"]) == user else None,
                )
            db.execute(
                "UPDATE terra_alliance_attacks SET status='cancelled',resolved_at=? "
                "WHERE id=? AND status='assembling'",
                (now, attack_id),
            )
            terra_combat.discard_mission(db, attack_id)
            self.audit(db, user, action, attack_id)
            return

        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")
        unit_catalog = self.game.unit_catalog_for_world(db, world_id)
        army = payload.get("army", {})
        if (
            not isinstance(army, dict)
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Ungültige Truppenauswahl für den Allianzangriff.")

        # The mission form includes every catalogued unit, including faction units
        # that are unavailable to this colony. Ignore their zero-count fields.
        if any(count > 0 and unit not in state["units"] for unit, count in army.items()):
            self.error("Unbekannter Truppentyp.")
        army = {unit: count for unit, count in army.items() if count > 0}

        if action == "alliance_attack_create":
            combat_world = db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()
            combat_version = str(combat_world["terra_combat_ruleset"]) if combat_world else "FUR-2"
            acs_version = (
                "FUR-3-TERRA-ACS-3"
                if terra_combat.is_supported_version(combat_version)
                else terra_alliance.VERSION
            )
            target_id = self.text(payload, "key", 1, 100)
            target_kind = self.text(payload, "target_kind", 1, 16)
            if target_kind not in ("outpost", "player"):
                self.error("Ungültige Zielart.")
            capture = payload.get("capture", False)
            if type(capture) is not bool:
                self.error("Ungültige Eroberungseinstellung.")
            if target_kind == "outpost":
                target = next(
                    (
                        item
                        for item in self.game.world_outposts(db, world_id)
                        if item["id"] == target_id
                    ),
                    None,
                )
                if not target or target.get("owner") is not None:
                    self.error("Terra-Allianzangriffe können nur neutrale Außenposten anvisieren.")
            else:
                target_row = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (target_id, world_id),
                ).fetchone()
                if not target_row:
                    self.error("Der Zielspieler besitzt keine Heimatkolonie in dieser Welt.")
                self.can_attack(db, user, target_id, now, world_id)
                target = self.game.read_colony(db, str(target_row["colony_id"]))
                target["id"] = target_id
                target["kind"] = "player"
            if capture and target_kind == "player":
                self.error("Spielerkolonien können nicht erobert werden.")
            if capture and int(state["buildings"]["hq"]) < 3:
                self.error("Eroberungen benötigen Kommandozentrale Stufe 3.")
            target_id = str(target["id"] if target_kind == "outpost" else target_id)
            target_x, target_y = int(target["x"]), int(target["y"])
            if not sector_is_known(db, user, world_id, target_x, target_y):
                self.error("Das Ziel ist noch nicht aufgeklärt.")
            attack_id = identity()
            join_until = now + terra_alliance.ASSEMBLY_SECONDS
            leader_id = user
            attack = None
        else:
            attack_id = self.text(payload, "key", 1, 100)
            attack = db.execute(
                "SELECT * FROM terra_alliance_attacks WHERE id=? AND alliance_id=? "
                "AND world_id=? AND status='assembling' AND join_until>?",
                (attack_id, alliance_id, world_id, now),
            ).fetchone()
            if not attack:
                self.error("Dieser Allianzangriff ist nicht mehr offen.")
            if db.execute(
                "SELECT 1 FROM terra_alliance_attack_wings WHERE attack_id=? AND user_id=?",
                (attack_id, user),
            ).fetchone():
                self.error("Du bist diesem Allianzangriff bereits beigetreten.")
            count = db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='active'",
                (attack_id,),
            ).fetchone()[0]
            if count >= terra_alliance.MAXIMUM_MEMBERS:
                self.error("Dieser Allianzangriff hat bereits die maximale Teilnehmerzahl.")
            if attack["target_kind"] == "outpost":
                target = next(
                    (
                        item
                        for item in self.game.world_outposts(db, world_id)
                        if item["id"] == attack["target_id"]
                    ),
                    None,
                )
                if not target or target.get("owner") is not None:
                    self.error("Das festgelegte Außenpostenziel ist nicht mehr neutral.")
            else:
                target_row = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (attack["target_id"], world_id),
                ).fetchone()
                if not target_row:
                    self.error("Das festgelegte Spielerziel ist nicht mehr verfügbar.")
                self.can_attack(db, user, str(attack["target_id"]), now, world_id)
                target = self.game.read_colony(db, str(target_row["colony_id"]))
                target["id"] = attack["target_id"]
                target["kind"] = "player"
            leader_id = str(attack["leader_id"])
            leader_row = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND colony_id=("
                "SELECT colony_id FROM terra_alliance_attack_wings WHERE attack_id=? AND user_id=?)",
                (leader_id, world_id, attack_id, leader_id),
            ).fetchone()
            if not leader_row:
                self.error("Die Einsatzleitung ist nicht mehr verfügbar.")
            join_until = int(attack["join_until"])
            target_x, target_y = int(target["x"]), int(target["y"])

        movement = self.reserve_movement_fuel(
            db, state, (int(state["x"]), int(state["y"])), (target_x, target_y), army
        )
        travel = int(movement["travel_seconds"])
        due = (
            join_until + max(int(attack["max_travel"]), travel)
            if attack is not None
            else join_until + travel
        )
        for unit, count in army.items():
            state["units"][unit] = state["units"].get(unit, 0) - count
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "alliance_attack" if user == leader_id else "alliance_attack_wing",
                "key": attack_id,
                "label": "Allianzangriff",
                "due": due,
                "travel": travel,
                "movement": movement,
                "army": dict(army),
                "loot": [0, 0, 0],
                "alliance_attack_id": attack_id,
            }
        )
        if attack is None:
            db.execute(
                "INSERT INTO terra_alliance_attacks"
                "(id,world_id,alliance_id,leader_id,target_kind,target_id,capture,status,created,join_until,due,max_travel,rule_version) "
                "VALUES (?,?,?,?,?,?,?,'assembling',?,?,?,?,?)",
                (
                    attack_id,
                    world_id,
                    alliance_id,
                    leader_id,
                    target_kind,
                    target_id,
                    capture,
                    now,
                    join_until,
                    due,
                    travel,
                    acs_version,
                ),
            )
            if acs_version == "FUR-3-TERRA-ACS-3":
                pinned = terra_combat.pin_mission(db, attack_id, world_id, now)
                if pinned is None:
                    raise RuntimeError("FUR-3 ACS combat rules could not be pinned")
        db.execute(
            "INSERT INTO terra_alliance_attack_wings"
            "(attack_id,user_id,colony_id,army,tactics,logistics,travel_seconds,status,joined_at) "
            "VALUES (?,?,?,?,?,?,?,'active',?)",
            (
                attack_id,
                user,
                state["colony_id"],
                json.dumps(army),
                int(state["tech"]["tactics"]),
                int(state["tech"]["logistics"]),
                travel,
                now,
            ),
        )
        if attack is not None:
            max_travel = max(int(attack["max_travel"]), travel)
            due = join_until + max_travel
            db.execute(
                "UPDATE terra_alliance_attacks SET due=?,max_travel=? WHERE id=? AND status='assembling'",
                (due, max_travel, attack_id),
            )
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE colony_id IN "
                "(SELECT colony_id FROM terra_alliance_attack_wings WHERE attack_id=? AND status='active')",
                (attack_id,),
            ).fetchall():
                colony = json.loads(row["state"])
                for job in colony.get("jobs", []):
                    if job.get("alliance_attack_id") == attack_id:
                        job["due"] = due
                if row["colony_id"] == state["colony_id"]:
                    for current_job in state.get("jobs", []):
                        if current_job.get("alliance_attack_id") == attack_id:
                            current_job["due"] = due
                else:
                    self.game.save(db, colony)
        self.audit(
            db,
            user,
            action,
            attack_id,
            target_kind=target_kind if attack is None else attack["target_kind"],
            travel=travel,
            army=army,
        )

    def recall_mission(
        self, db: Connection, state: dict[str, Any], payload: dict[str, Any]
    ) -> None:
        """Recall an outbound mission and schedule its force to return from its current position."""
        from .game import identity
        from .neutral_market import GOODS, RESOURCE_IDS

        job_id = self.text(payload, "key")
        recallable = {
            "raid",
            "attack",
            "scout",
            "transport",
            "colony_supply",
            "station",
            "expedition",
            "ruin_exploration",
        }
        mission = next(
            (
                job
                for job in state["jobs"]
                if job.get("id") == job_id and job.get("kind") in recallable
            ),
            None,
        )
        now = int(time.time())
        if not mission or type(mission.get("due")) is not int or mission["due"] <= now:
            self.error("Dieser ausgehende Auftrag ist nicht mehr zurückrufbar.")
        from . import terra_combat

        if terra_combat.is_supported_version(str(mission.get("rules_version", ""))):
            terra_combat.discard_mission(db, job_id)
        if mission.get("kind") == "ruin_exploration":
            ruin_exploration.discard_mission(db, job_id)
        travel = mission.get("travel")
        if type(travel) is not int or travel < 1:
            self.error("Für diesen Auftrag ist keine gültige Rückreise berechenbar.")
        army = mission.get("army")
        if (
            not isinstance(army, dict)
            or not army
            or any(
                unit not in state["units"] or type(count) is not int or count < 0
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Die Truppen dieses Auftrags können nicht sicher zurückgerufen werden.")
        cargo = mission.get("loot", [0, 0, 0])
        if (
            not isinstance(cargo, list)
            or len(cargo) != 3
            or any(type(amount) is not int or amount < 0 for amount in cargo)
        ):
            self.error("Die Fracht dieses Auftrags kann nicht sicher zurückgerufen werden.")
        goods_cargo = mission.get("goods_cargo", {})
        if not isinstance(goods_cargo, dict) or any(
            not isinstance(good_id, str)
            or good_id not in GOODS
            or good_id in RESOURCE_IDS
            or type(amount) is not int
            or amount < 0
            for good_id, amount in goods_cargo.items()
        ):
            self.error("Die Warenfracht dieses Auftrags kann nicht sicher zurückgerufen werden.")
        from . import items as generic_items

        item_cargo = mission.get("item_cargo", {})
        if not isinstance(item_cargo, dict) or any(
            not isinstance(item_id, str)
            or item_id not in generic_items.ITEMS
            or type(amount) is not int
            or amount < 0
            for item_id, amount in item_cargo.items()
        ):
            self.error(
                "Die Gegenstandsfracht dieses Auftrags kann nicht sicher zurückgerufen werden."
            )
        if mission["kind"] == "colony_supply" and goods_cargo:
            destination = self.game.read_colony(db, str(mission.get("key", "")))
            inbound = dict(destination.get("goods_inbound", {}))
            for good_id, amount in goods_cargo.items():
                reserved = int(inbound.get(good_id, 0))
                if reserved < amount:
                    self.error("Die Warenfrachtreservierung der Zielkolonie fehlt.")
                inbound[good_id] = reserved - amount
                if inbound[good_id] == 0:
                    inbound.pop(good_id)
            destination["goods_inbound"] = inbound
            self.game.save(db, destination)
        if mission["kind"] == "colony_supply" and item_cargo:
            destination = self.game.read_colony(db, str(mission.get("key", "")))
            generic_items.release_incoming(destination, item_cargo)
            self.game.save(db, destination)
        departed = mission["due"] - travel
        elapsed = max(0, min(travel, now - departed))
        return_travel = max(5, elapsed)
        label = str(mission.get("label", "Mission"))
        state["jobs"] = [job for job in state["jobs"] if job.get("id") != job_id]
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "return",
                "key": str(mission.get("key", "")),
                "label": "Rückmarsch: " + label,
                "due": now + return_travel,
                "travel": return_travel,
                "army": dict(army),
                "loot": list(cargo),
                "goods_cargo": dict(goods_cargo),
                "item_cargo": dict(item_cargo),
                "return_reason": "recalled",
            }
        )
        self.game.report(
            state,
            "Mission zurückgerufen",
            f"{label} wurde auf dem Hinweg umgekehrt. Truppen und Fracht kehren in "
            f"{return_travel} Sekunden zurück.",
        )
        self.audit(
            db,
            state["id"],
            "mission_recalled",
            job_id,
            mission_kind=mission["kind"],
            target_id=mission.get("key", ""),
            elapsed=elapsed,
            return_travel=return_travel,
            army=army,
            cargo=cargo,
        )

    def alliance_forum_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        user, now = str(state["id"]), int(time.time())
        member = self.member(db, user)
        if not member:
            self.error("Das Allianzforum erfordert eine aktuelle Mitgliedschaft.")
        alliance_id = str(member["alliance_id"])
        moderator = member["role"] == "leader" or "forum_moderation" in self.alliance_permissions(
            db, member
        )
        if (
            action in ("alliance_forum_thread_create", "alliance_forum_reply")
            and int(self.profile(db, user)["muted_until"]) > now
        ):
            self.error("Dein Schreibrecht ist vorübergehend eingeschränkt.")

        if action == "alliance_forum_thread_create":
            thread_id, post_id = identity(), identity()
            title, body = self.text(p, "name", 1, 100), self.text(p, "body", 1, 4000)
            db.execute(
                "INSERT INTO alliance_forum_threads "
                "(id,alliance_id,author_id,title,created,updated,archived) VALUES (?,?,?,?,?,?,0)",
                (thread_id, alliance_id, user, title, now, now),
            )
            db.execute(
                "INSERT INTO alliance_forum_posts "
                "(id,thread_id,author_id,body,created,updated) VALUES (?,?,?,?,?,?)",
                (post_id, thread_id, user, body, now, now),
            )
            self.audit(db, user, action, thread_id, post_id=post_id, title=title)
        elif action == "alliance_forum_reply":
            thread_id = self.text(p, "key", 1, 100)
            thread = db.execute(
                "SELECT id FROM alliance_forum_threads "
                "WHERE id=? AND alliance_id=? AND archived=0",
                (thread_id, alliance_id),
            ).fetchone()
            if not thread:
                self.error("Offenes Forumthema nicht gefunden.")
            post_id = identity()
            db.execute(
                "INSERT INTO alliance_forum_posts "
                "(id,thread_id,author_id,body,created,updated) VALUES (?,?,?,?,?,?)",
                (post_id, thread_id, user, self.text(p, "body", 1, 4000), now, now),
            )
            db.execute(
                "UPDATE alliance_forum_threads SET updated=? WHERE id=? AND alliance_id=?",
                (now, thread_id, alliance_id),
            )
            self.audit(db, user, action, thread_id, post_id=post_id)
        elif action == "alliance_forum_thread_edit":
            thread_id, title = self.text(p, "key", 1, 100), self.text(p, "name", 1, 100)
            thread = db.execute(
                "SELECT author_id FROM alliance_forum_threads "
                "WHERE id=? AND alliance_id=? AND archived=0",
                (thread_id, alliance_id),
            ).fetchone()
            if not thread or (thread["author_id"] != user and not moderator):
                self.error("Dieses offene Forumthema darf nicht bearbeitet werden.")
            db.execute(
                "UPDATE alliance_forum_threads SET title=?,updated=? "
                "WHERE id=? AND alliance_id=? AND archived=0",
                (title, now, thread_id, alliance_id),
            )
            self.audit(db, user, action, thread_id, title=title)
        elif action == "alliance_forum_post_edit":
            post_id, body = self.text(p, "key", 1, 100), self.text(p, "body", 1, 4000)
            post = db.execute(
                "SELECT p.author_id,p.thread_id,t.archived FROM alliance_forum_posts p "
                "JOIN alliance_forum_threads t ON t.id=p.thread_id "
                "WHERE p.id=? AND t.alliance_id=?",
                (post_id, alliance_id),
            ).fetchone()
            if not post or post["archived"] or (post["author_id"] != user and not moderator):
                self.error("Dieser Beitrag darf nicht bearbeitet werden.")
            db.execute(
                "UPDATE alliance_forum_posts SET body=?,updated=? WHERE id=?",
                (body, now, post_id),
            )
            db.execute(
                "UPDATE alliance_forum_threads SET updated=? WHERE id=?",
                (now, post["thread_id"]),
            )
            self.audit(db, user, action, post_id)
        elif action == "alliance_forum_archive":
            if not moderator:
                self.error(
                    "Nur Leitung und Offiziere mit Forumrecht oder ausdrücklich berechtigte "
                    "Mitglieder dürfen Forumthemen archivieren."
                )
            thread_id = self.text(p, "key", 1, 100)
            archived = db.execute(
                "UPDATE alliance_forum_threads SET archived=1,updated=? "
                "WHERE id=? AND alliance_id=? AND archived=0 RETURNING id",
                (now, thread_id, alliance_id),
            ).fetchone()
            if not archived:
                self.error("Offenes Forumthema nicht gefunden.")
            self.audit(db, user, action, thread_id)
        elif action == "alliance_forum_report":
            post_id, reason = self.text(p, "key", 1, 100), self.text(p, "body", 1, 500)
            post = db.execute(
                "SELECT p.author_id FROM alliance_forum_posts p "
                "JOIN alliance_forum_threads t ON t.id=p.thread_id "
                "WHERE p.id=? AND t.alliance_id=?",
                (post_id, alliance_id),
            ).fetchone()
            if not post or post["author_id"] == user:
                self.error("Der fremde Forumsbeitrag wurde nicht gefunden.")
            if db.execute(
                "SELECT 1 FROM alliance_forum_reports WHERE post_id=? AND reporter_id=? "
                "AND status='pending'",
                (post_id, user),
            ).fetchone():
                self.error("Du hast diesen Beitrag bereits gemeldet.")
            report_id = identity()
            db.execute(
                "INSERT INTO alliance_forum_reports "
                "(id,post_id,reporter_id,reason,status,created,updated,resolved_by) "
                "VALUES (?,?,?,?,'pending',?,?,NULL)",
                (report_id, post_id, user, reason, now, now),
            )
            self.audit(db, user, action, report_id, post_id=post_id)
        elif action == "alliance_forum_report_resolve":
            if not moderator:
                self.error(
                    "Nur Leitung und Offiziere mit Forumrecht oder ausdrücklich berechtigte "
                    "Mitglieder dürfen Forumsmeldungen prüfen."
                )
            report_id = self.text(p, "key", 1, 100)
            resolved = db.execute(
                "UPDATE alliance_forum_reports SET status='resolved',updated=?,resolved_by=? "
                "WHERE id=? AND status='pending' AND post_id IN ("
                "SELECT p.id FROM alliance_forum_posts p "
                "JOIN alliance_forum_threads t ON t.id=p.thread_id WHERE t.alliance_id=?) "
                "RETURNING id",
                (now, user, report_id, alliance_id),
            ).fetchone()
            if not resolved:
                self.error("Offene Forums-Meldung nicht gefunden.")
            self.audit(db, user, action, report_id)

    def alliance_forum_reports_page(
        self,
        db: Connection,
        user: str,
        alliance_id: str,
        moderator: bool,
        before_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        visibility = "t.alliance_id=? AND (r.reporter_id=? OR ?=TRUE)"
        scope_params: tuple[Any, ...] = (alliance_id, user, moderator)
        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_id is not None:
            cursor = db.execute(
                "SELECT r.created,r.id FROM alliance_forum_reports r "
                "JOIN alliance_forum_posts p ON p.id=r.post_id "
                "JOIN alliance_forum_threads t ON t.id=p.thread_id "
                "WHERE " + visibility + " AND r.id=?",
                (*scope_params, before_id),
            ).fetchone()
            if not cursor:
                self.error("Forum-Meldung nicht gefunden.")
            cursor_clause = "AND (r.created<? OR (r.created=? AND r.id<?)) "
            created = int(cursor["created"])
            params = (
                *scope_params,
                created,
                created,
                str(cursor["id"]),
            )
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT r.id,r.post_id,r.reporter_id,reporter.name AS reporter_name,r.reason,r.status,"
                "r.created,r.updated,r.resolved_by,resolver.name AS resolver_name,t.id AS thread_id,"
                "t.title AS thread_title,p.body AS post_body,author.name AS post_author_name "
                "FROM alliance_forum_reports r JOIN alliance_forum_posts p ON p.id=r.post_id "
                "JOIN alliance_forum_threads t ON t.id=p.thread_id "
                "JOIN users reporter ON reporter.id=r.reporter_id "
                "JOIN users author ON author.id=p.author_id "
                "LEFT JOIN users resolver ON resolver.id=r.resolved_by "
                "WHERE "
                + visibility
                + " "
                + cursor_clause
                + "ORDER BY r.created DESC,r.id DESC LIMIT 51",
                params,
            )
        ]
        return rows[:50], len(rows) > 50

    def alliance_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        user, now = state["id"], int(time.time())
        member = self.member(db, user)
        if action.startswith("alliance_treasury_"):
            self.alliance_treasury_command(db, state, action, p)
            return
        if action.startswith("alliance_project_"):
            self.alliance_projects_command(db, state, action, p)
            return
        if action == "alliance_create":
            if member:
                self.error("Du gehörst bereits einer Allianz an.")
            tag, name = self.text(p, "tag", 3, 8).upper(), self.text(p, "name", 3, 30)
            if not re.fullmatch(r"[A-Z0-9]{3,8}", tag):
                self.error("Allianztag: 3–8 Buchstaben oder Zahlen.")
            if db.execute("SELECT 1 FROM alliances WHERE lower(tag)=lower(?)", (tag,)).fetchone():
                self.error("Dieser Allianztag ist bereits vergeben.")
            alliance = identity()
            db.execute(
                "INSERT INTO alliances VALUES (?,?,?,?,?,?)", (alliance, tag, name, "", user, now)
            )
            db.execute("INSERT INTO members VALUES (?,?,?)", (user, alliance, "leader"))
            for permission in ALLIANCE_PERMISSIONS:
                db.execute(
                    "INSERT INTO alliance_role_permissions(alliance_id,role,permission) "
                    "VALUES (?,'officer',?)",
                    (alliance, permission),
                )
        elif action == "alliance_accept":
            if member:
                self.error("Verlasse zuerst deine bisherige Allianz.")
            invite = db.execute(
                "SELECT * FROM invites WHERE id=? AND user_id=?", (self.text(p, "key"), user)
            ).fetchone()
            if not invite:
                self.error("Einladung nicht gefunden.")
            db.execute(
                "INSERT INTO members VALUES (?,?,?)", (user, invite["alliance_id"], "member")
            )
            db.execute("DELETE FROM invites WHERE user_id=?", (user,))
            db.execute("DELETE FROM alliance_applications WHERE user_id=?", (user,))
        elif action == "alliance_apply":
            if member:
                self.error("Verlasse zuerst deine bisherige Allianz.")
            alliance = self.text(p, "key", 1, 100)
            if not db.execute("SELECT 1 FROM alliances WHERE id=?", (alliance,)).fetchone():
                self.error("Allianz nicht gefunden.")
            if db.execute(
                "SELECT 1 FROM invites WHERE alliance_id=? AND user_id=?", (alliance, user)
            ).fetchone():
                self.error("Für diese Allianz liegt bereits eine Einladung vor.")
            db.execute(
                "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?) "
                "ON CONFLICT(alliance_id,user_id) DO NOTHING",
                (identity(), alliance, user, now),
            )
        elif action == "alliance_application_withdraw":
            application_id = self.text(p, "key", 1, 100)
            application = db.execute(
                "SELECT alliance_id FROM alliance_applications WHERE id=? AND user_id=?",
                (application_id, user),
            ).fetchone()
            if not application:
                self.error("Bewerbung nicht gefunden.")
            db.execute(
                "DELETE FROM alliance_applications WHERE id=? AND user_id=?",
                (application_id, user),
            )
            self.audit(
                db, user, action, str(application["alliance_id"]), application_id=application_id
            )
            return
        elif action in ("alliance_application_accept", "alliance_application_reject"):
            manager = self.require_alliance_permission(db, user, "applications")
            application_id = self.text(p, "key", 1, 100)
            application = db.execute(
                "SELECT user_id FROM alliance_applications WHERE id=? AND alliance_id=?",
                (application_id, manager["alliance_id"]),
            ).fetchone()
            if not application:
                self.error("Bewerbung nicht gefunden.")
            applicant = str(application["user_id"])
            if action == "alliance_application_accept":
                if self.member(db, applicant):
                    self.error("Dieser Spieler gehört bereits einer Allianz an.")
                db.execute(
                    "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
                    (applicant, manager["alliance_id"], "member"),
                )
                db.execute("DELETE FROM invites WHERE user_id=?", (applicant,))
                db.execute("DELETE FROM alliance_applications WHERE user_id=?", (applicant,))
            else:
                db.execute("DELETE FROM alliance_applications WHERE id=?", (application_id,))
            self.audit(db, user, action, application_id, applicant=applicant)
            return
        elif action == "alliance_invite_decline":
            invite_id = self.text(p, "key")
            invite = db.execute(
                "SELECT alliance_id FROM invites WHERE id=? AND user_id=?", (invite_id, user)
            ).fetchone()
            if not invite:
                self.error("Einladung nicht gefunden.")
            db.execute("DELETE FROM invites WHERE id=? AND user_id=?", (invite_id, user))
            self.audit(db, user, action, str(invite["alliance_id"]), invite_id=invite_id)
            return
        elif action == "alliance_leave":
            if not member:
                self.error("Du bist in keiner Allianz.")
            if member["role"] == "leader":
                self.error(
                    "Übertrage zuerst die Führung. Eine letzte Allianzleitung bleibt erhalten."
                )
            self._recall_alliance_garrisons_for_member(db, user, str(member["alliance_id"]), now)
            self.void_alliance_treasury_requests(
                db, user, str(member["alliance_id"]), actor_id=user, at=now
            )
            self.revoke_owner_report_shares(db, user, str(member["alliance_id"]))
            db.execute(
                "DELETE FROM alliance_transfer_requests WHERE successor_id=? AND alliance_id=?",
                (user, member["alliance_id"]),
            )
            db.execute("DELETE FROM members WHERE user_id=?", (user,))
        elif action == "alliance_transfer_accept":
            if not member:
                self.error("Du bist nicht Mitglied der vorgeschlagenen Allianz.")
            transfer = db.execute(
                "SELECT r.*,a.leader AS current_leader FROM alliance_transfer_requests r "
                "JOIN alliances a ON a.id=r.alliance_id "
                "WHERE r.id=? AND r.successor_id=? AND r.alliance_id=?",
                (self.text(p, "key", 1, 100), user, member["alliance_id"]),
            ).fetchone()
            if (
                not transfer
                or transfer["current_leader"] != transfer["leader_id"]
                or member["role"] == "leader"
                or not self.member(db, str(transfer["leader_id"]))
                or self.member(db, str(transfer["leader_id"]))["role"] != "leader"
            ):
                self.error("Diese Führungsübergabe ist nicht mehr gültig.")
            db.execute(
                "UPDATE members SET role='officer' WHERE user_id=? AND alliance_id=?",
                (transfer["leader_id"], member["alliance_id"]),
            )
            db.execute(
                "UPDATE members SET role='leader' WHERE user_id=? AND alliance_id=?",
                (user, member["alliance_id"]),
            )
            db.execute(
                "UPDATE alliances SET leader=? WHERE id=?",
                (user, member["alliance_id"]),
            )
            db.execute("DELETE FROM alliance_transfer_requests WHERE id=?", (transfer["id"],))
            self.audit(
                db,
                user,
                action,
                str(transfer["id"]),
                former_leader=str(transfer["leader_id"]),
            )
            return
        elif action == "alliance_transfer_decline":
            if not member:
                self.error("Du bist nicht Mitglied der vorgeschlagenen Allianz.")
            transfer_id = self.text(p, "key", 1, 100)
            declined = db.execute(
                "DELETE FROM alliance_transfer_requests WHERE id=? AND successor_id=? "
                "AND alliance_id=? RETURNING id,leader_id",
                (transfer_id, user, member["alliance_id"]),
            ).fetchone()
            if not declined:
                self.error("Führungsübergabe nicht gefunden.")
            self.audit(
                db,
                user,
                action,
                transfer_id,
                former_leader=str(declined["leader_id"]),
            )
            return
        elif action == "alliance_transfer_cancel":
            if not member or member["role"] != "leader":
                self.error("Nur die aktuelle Allianzleitung kann die Übergabe zurücknehmen.")
            transfer_id = self.text(p, "key", 1, 100)
            cancelled = db.execute(
                "DELETE FROM alliance_transfer_requests WHERE id=? AND alliance_id=? "
                "AND leader_id=? RETURNING id",
                (transfer_id, member["alliance_id"], user),
            ).fetchone()
            if not cancelled:
                self.error("Führungsübergabe nicht gefunden.")
            self.audit(db, user, action, transfer_id)
            return
        elif action.startswith("alliance_forum_"):
            self.alliance_forum_command(db, state, action, p)
            return
        else:
            leader = self.member(db, user)
            if not leader:
                self.error("Nur die Allianzleitung kann diese Aktion ausführen.")
            alliance = leader["alliance_id"]
            if action == "alliance_permissions_update":
                if leader["role"] != "leader":
                    self.error("Nur die Allianzleitung darf Rollenberechtigungen ändern.")
                role = p.get("role")
                permissions = p.get("permissions")
                if role not in ("officer", "member"):
                    self.error(
                        "Berechtigungen können nur für Offiziere oder Mitglieder gesetzt werden."
                    )
                if (
                    not isinstance(permissions, list)
                    or any(
                        not isinstance(permission, str) or permission not in ALLIANCE_PERMISSIONS
                        for permission in permissions
                    )
                    or len(set(permissions)) != len(permissions)
                ):
                    self.error("Die Berechtigungsauswahl ist ungültig.")
                db.execute(
                    "DELETE FROM alliance_role_permissions WHERE alliance_id=? AND role=?",
                    (alliance, role),
                )
                for permission in permissions:
                    db.execute(
                        "INSERT INTO alliance_role_permissions(alliance_id,role,permission) "
                        "VALUES (?,?,?)",
                        (alliance, role, permission),
                    )
                self.audit(db, user, action, str(alliance), role=role, permissions=permissions)
                return
            if action in ("alliance_role", "alliance_transfer") and leader["role"] != "leader":
                self.error("Nur die Allianzleitung darf Rollen oder Führung vergeben.")
            if action == "alliance_edit":
                self.require_alliance_permission(db, user, "description")
                db.execute(
                    "UPDATE alliances SET description=? WHERE id=?",
                    (self.text(p, "description", 1, 1000), alliance),
                )
            elif action == "alliance_invite":
                self.require_alliance_permission(db, user, "invitations")
                target = db.execute(
                    "SELECT id FROM users WHERE lower(name)=lower(?)", (self.text(p, "name"),)
                ).fetchone()
                if not target or self.member(db, target[0]):
                    self.error("Spieler unbekannt oder bereits in einer Allianz.")
                if db.execute(
                    "SELECT 1 FROM alliance_applications WHERE alliance_id=? AND user_id=?",
                    (alliance, target[0]),
                ).fetchone():
                    self.error("Dieser Spieler hat sich bereits bei der Allianz beworben.")
                db.execute(
                    "INSERT INTO invites VALUES (?,?,?) ON CONFLICT(alliance_id,user_id) DO NOTHING",
                    (identity(), alliance, target[0]),
                )
            elif action == "alliance_invite_cancel":
                self.require_alliance_permission(db, user, "invitations")
                invite_id = self.text(p, "key")
                invite = db.execute(
                    "SELECT user_id FROM invites WHERE id=? AND alliance_id=?",
                    (invite_id, alliance),
                ).fetchone()
                if not invite:
                    self.error("Einladung nicht gefunden.")
                db.execute(
                    "DELETE FROM invites WHERE id=? AND alliance_id=?", (invite_id, alliance)
                )
                self.audit(db, user, action, invite_id, invited_user=str(invite["user_id"]))
                return
            elif action == "alliance_bulletin_create":
                self.require_alliance_permission(db, user, "bulletin")
                bulletin_id = identity()
                title = self.text(p, "name", 1, 80)
                body = self.text(p, "body", 1, 2000)
                db.execute(
                    "INSERT INTO alliance_bulletins "
                    "(id,alliance_id,author_id,title,body,created,updated,archived) "
                    "VALUES (?,?,?,?,?,?,?,0)",
                    (bulletin_id, alliance, user, title, body, now, now),
                )
                self.audit(db, user, action, bulletin_id, title=title)
                return
            elif action == "alliance_bulletin_update":
                self.require_alliance_permission(db, user, "bulletin")
                bulletin_id = self.text(p, "key", 1, 100)
                title = self.text(p, "name", 1, 80)
                body = self.text(p, "body", 1, 2000)
                updated = db.execute(
                    "UPDATE alliance_bulletins SET title=?,body=?,updated=? "
                    "WHERE id=? AND alliance_id=? AND archived=0 RETURNING id",
                    (title, body, now, bulletin_id, alliance),
                ).fetchone()
                if not updated:
                    self.error("Aktive Allianzankündigung nicht gefunden.")
                self.audit(db, user, action, bulletin_id, title=title)
                return
            elif action == "alliance_bulletin_archive":
                self.require_alliance_permission(db, user, "bulletin")
                bulletin_id = self.text(p, "key", 1, 100)
                archived = db.execute(
                    "UPDATE alliance_bulletins SET archived=1,updated=? "
                    "WHERE id=? AND alliance_id=? AND archived=0 RETURNING id",
                    (now, bulletin_id, alliance),
                ).fetchone()
                if not archived:
                    self.error("Aktive Allianzankündigung nicht gefunden.")
                self.audit(db, user, action, bulletin_id)
                return
            elif action in ("alliance_kick", "alliance_role", "alliance_transfer"):
                if action == "alliance_kick":
                    self.require_alliance_permission(db, user, "member_removal")
                target_id = self.text(p, "key")
                target_member = self.member(db, target_id)
                if (
                    not target_member
                    or target_member["alliance_id"] != alliance
                    or target_id == user
                    or target_member["role"] == "leader"
                ):
                    self.error("Ungültiges Allianzmitglied.")
                if leader["role"] != "leader" and target_member["role"] != "member":
                    self.error("Offiziere können nur einfache Mitglieder entfernen.")
                if action == "alliance_kick":
                    db.execute(
                        "DELETE FROM alliance_transfer_requests WHERE successor_id=? "
                        "AND alliance_id=?",
                        (target_id, alliance),
                    )
                    self._recall_alliance_garrisons_for_member(db, target_id, alliance, now)
                    self.void_alliance_treasury_requests(
                        db, target_id, str(alliance), actor_id=user, at=now
                    )
                    self.revoke_owner_report_shares(db, target_id, str(alliance))
                    db.execute("DELETE FROM members WHERE user_id=?", (target_id,))
                else:
                    if leader["role"] != "leader":
                        self.error("Nur die Allianzleitung darf Rollen vergeben.")
                    if action == "alliance_transfer":
                        if db.execute(
                            "SELECT 1 FROM alliance_transfer_requests WHERE alliance_id=?",
                            (alliance,),
                        ).fetchone():
                            self.error("Für diese Allianz liegt bereits eine Führungsübergabe vor.")
                        db.execute(
                            "INSERT INTO alliance_transfer_requests "
                            "(id,alliance_id,leader_id,successor_id,created) VALUES (?,?,?,?,?)",
                            (identity(), alliance, user, target_id, now),
                        )
                    else:
                        role = self.text(p, "role")
                        if role not in ("officer", "member"):
                            self.error("Ungültige Rolle.")
                        db.execute("UPDATE members SET role=? WHERE user_id=?", (role, target_id))
            else:
                self.error("Unbekannter Allianzbefehl.")
        self.audit(db, user, action)

    def alliance_war_event(
        self,
        db: Connection,
        war_id: str,
        event_type: str,
        actor: str | None,
        details: dict[str, Any],
        created: int,
    ) -> None:
        from .game import identity

        created = alliance_war.next_event_time(db, war_id, created)
        db.execute(
            "INSERT INTO alliance_war_events(id,war_id,event_type,actor_alliance,details,created) "
            "VALUES (?,?,?,?,?,?)",
            (
                identity(),
                war_id,
                event_type,
                actor,
                json.dumps(details, separators=(",", ":")),
                created,
            ),
        )

    def alliance_war_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        member = self.require_alliance_permission(db, str(state["id"]), "diplomacy")
        own = str(member["alliance_id"])
        war_id = self.text(p, "key", 1, 100)
        war = db.execute(
            "SELECT * FROM alliance_wars WHERE id=? AND (alliance_a=? OR alliance_b=?)",
            (war_id, own, own),
        ).fetchone()
        if not war:
            self.error("Allianzkrieg nicht gefunden.")
        opponent = str(war["alliance_b"] if war["alliance_a"] == own else war["alliance_a"])
        now = int(time.time())
        if action == "alliance_peace_offer":
            if war["status"] != "active":
                self.error(
                    "Für diesen Krieg ist bereits ein Friedensvorschlag offen oder er ist beendet."
                )
            db.execute(
                "UPDATE alliance_wars SET status='peace_offered',peace_offered_by=? WHERE id=?",
                (own, war_id),
            )
            self.alliance_war_event(db, war_id, "peace_offered", own, {}, now)
        elif action == "alliance_peace_accept":
            if war["status"] != "peace_offered" or war["peace_offered_by"] == own:
                self.error("Es liegt kein gegnerischer Friedensvorschlag vor.")
            db.execute(
                "UPDATE alliance_wars SET status='ended',end_reason='peace',ended=? WHERE id=?",
                (now, war_id),
            )
            db.execute(
                "DELETE FROM diplomacy WHERE a=? AND b=?",
                (war["alliance_a"], war["alliance_b"]),
            )
            self.alliance_war_event(db, war_id, "ended_peace", own, {}, now)
            from .game import identity

            db.execute(
                "INSERT INTO alliance_diplomacy_events "
                "(id,alliance_a,alliance_b,actor_alliance,event_type,created) "
                "VALUES (?,?,?,?, 'neutralized',?)",
                (
                    identity(),
                    war["alliance_a"],
                    war["alliance_b"],
                    own,
                    alliance_war.next_diplomacy_event_time(
                        db, str(war["alliance_a"]), str(war["alliance_b"]), now
                    ),
                ),
            )
        elif action == "alliance_peace_decline":
            if war["status"] != "peace_offered" or war["peace_offered_by"] == own:
                self.error("Es liegt kein gegnerischer Friedensvorschlag vor.")
            db.execute(
                "UPDATE alliance_wars SET status='active',peace_offered_by=NULL WHERE id=?",
                (war_id,),
            )
            self.alliance_war_event(db, war_id, "peace_declined", own, {}, now)
        elif action == "alliance_peace_cancel":
            if war["status"] != "peace_offered" or war["peace_offered_by"] != own:
                self.error("Du kannst nur deinen eigenen Friedensvorschlag zurücknehmen.")
            db.execute(
                "UPDATE alliance_wars SET status='active',peace_offered_by=NULL WHERE id=?",
                (war_id,),
            )
            self.alliance_war_event(db, war_id, "peace_cancelled", own, {}, now)
        else:
            self.error("Unbekannte Friedensaktion.")
        self.audit(db, str(state["id"]), action, war_id, opponent=opponent)

    def alliance_wars_public_state(
        self, db: Connection
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        wars = [
            dict(row)
            for row in db.execute(
                "SELECT w.id,w.rules_version,w.rules_digest,w.target_points,w.score_a,w.score_b,"
                "w.status,w.peace_offered_by,w.winner,w.end_reason,w.started,w.ended,"
                "a.id AS alliance_a,a.name AS alliance_a_name,a.tag AS alliance_a_tag,"
                "b.id AS alliance_b,b.name AS alliance_b_name,b.tag AS alliance_b_tag,"
                "winner.name AS winner_name FROM alliance_wars w "
                "JOIN alliances a ON a.id=w.alliance_a JOIN alliances b ON b.id=w.alliance_b "
                "LEFT JOIN alliances winner ON winner.id=w.winner "
                "ORDER BY w.started DESC,w.id DESC LIMIT 50"
            )
        ]
        events = [
            dict(row)
            for row in db.execute(
                "SELECT e.id,e.war_id,e.event_type,e.actor_alliance,e.details,e.created,"
                "a.tag AS alliance_a_tag,b.tag AS alliance_b_tag,actor.tag AS actor_tag "
                "FROM alliance_war_events e JOIN alliance_wars w ON w.id=e.war_id "
                "JOIN alliances a ON a.id=w.alliance_a JOIN alliances b ON b.id=w.alliance_b "
                "LEFT JOIN alliances actor ON actor.id=e.actor_alliance "
                "ORDER BY e.created DESC,e.id DESC LIMIT 50"
            )
        ]
        for event in events:
            event["details"] = json.loads(str(event["details"]))
        return wars, events

    def diplomacy_command(self, db: Connection, state: dict[str, Any], p: dict[str, Any]) -> None:
        from .game import identity

        own = self.require_alliance_permission(db, state["id"], "diplomacy")["alliance_id"]
        other = self.text(p, "key")
        if (
            own == other
            or not db.execute("SELECT 1 FROM alliances WHERE id=?", (other,)).fetchone()
        ):
            self.error("Ungültige Gegenallianz.")
        a, b = sorted([own, other])
        status = self.text(p, "status")
        previous = db.execute("SELECT * FROM diplomacy WHERE a=? AND b=?", (a, b)).fetchone()
        formal_war = db.execute(
            "SELECT id FROM alliance_wars WHERE alliance_a=? AND alliance_b=? "
            "AND status IN ('active','peace_offered') ORDER BY started DESC,id LIMIT 1",
            (a, b),
        ).fetchone()
        event_type: str | None = None
        if status == "accept":
            if not previous or previous["proposed_by"] == own or previous["status"] != "nap":
                self.error("Kein fremdes Bündnisangebot vorhanden.")
            db.execute("UPDATE diplomacy SET accepted=1 WHERE a=? AND b=?", (a, b))
            event_type = "nap_accepted"
        elif status == "neutral":
            if formal_war:
                self.error(
                    "Ein aktiver Allianzkrieg endet erst nach angenommener Friedensverhandlung."
                )
            db.execute("DELETE FROM diplomacy WHERE a=? AND b=?", (a, b))
            if previous:
                event_type = "neutralized"
        elif status in ("nap", "war"):
            if status == "nap" and formal_war:
                self.error(
                    "Schließe zuerst den aktiven Allianzkrieg über einen Friedensvorschlag ab."
                )
            db.execute(
                "INSERT INTO diplomacy VALUES (?,?,?,?,?) ON CONFLICT(a,b) DO UPDATE SET status=excluded.status, proposed_by=excluded.proposed_by, accepted=excluded.accepted",
                (a, b, status, own, int(status == "war")),
            )
            event_type = "nap_proposed" if status == "nap" else "war_declared"
            if status == "war":
                from . import terra_combat

                world_id = int(state.get("world_id", 1))
                world_rules = db.execute(
                    "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                    (world_id,),
                ).fetchone()
                combat_rules = str(world_rules["terra_combat_ruleset"]) if world_rules else "FUR-2"
                if terra_combat.is_supported_version(combat_rules) and not formal_war:
                    war_id = identity()
                    now = int(time.time())
                    db.execute(
                        "INSERT INTO alliance_wars "
                        "(id,alliance_a,alliance_b,rules_version,rules_digest,target_points,"
                        "status,started) VALUES (?,?,?,?,?,?,'active',?)",
                        (
                            war_id,
                            a,
                            b,
                            alliance_war.VERSION,
                            alliance_war.RULES_DIGEST,
                            alliance_war.TARGET_POINTS,
                            now,
                        ),
                    )
                    self.alliance_war_event(
                        db,
                        war_id,
                        "declared",
                        str(own),
                        {
                            "objective": "enemy_unit_casualties",
                            "target_points": alliance_war.TARGET_POINTS,
                        },
                        now,
                    )
        else:
            self.error("Unbekannter diplomatischer Status.")
        if event_type:
            event_at = alliance_war.next_diplomacy_event_time(db, a, b, int(time.time()))
            db.execute(
                "INSERT INTO alliance_diplomacy_events "
                "(id,alliance_a,alliance_b,actor_alliance,event_type,created) "
                "VALUES (?,?,?,?,?,?)",
                (identity(), a, b, own, event_type, event_at),
            )
        self.audit(db, state["id"], "diplomacy", other, status=status)

    def diplomacy_events_page(
        self,
        db: Connection,
        before_event_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für das Diplomatieprotokoll.")
        cursor_clause = ""
        params: tuple[Any, ...] = ()
        if before_event_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM alliance_diplomacy_events WHERE id=?",
                (before_event_id,),
            ).fetchone()
            if not cursor:
                self.error("Diplomatie-Cursor nicht gefunden.")
            cursor_clause = "WHERE (e.created<? OR (e.created=? AND e.id<?)) "
            params = (int(cursor["created"]), int(cursor["created"]), str(cursor["id"]))
        rows = list(
            db.execute(
                "SELECT e.id,e.event_type,e.created,e.actor_alliance,"
                "a.tag AS alliance_a_tag,b.tag AS alliance_b_tag,"
                "actor.tag AS actor_alliance_tag "
                "FROM alliance_diplomacy_events e "
                "JOIN alliances a ON a.id=e.alliance_a "
                "JOIN alliances b ON b.id=e.alliance_b "
                "JOIN alliances actor ON actor.id=e.actor_alliance "
                + cursor_clause
                + "ORDER BY e.created DESC,e.id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        return [dict(row) for row in rows[:page_size]], len(rows) > page_size

    def communication(self, db: Connection, state: dict[str, Any], p: dict[str, Any]) -> None:
        from .game import identity

        user, now = state["id"], int(time.time())
        if self.profile(db, user)["muted_until"] > now:
            self.error("Dein Nachrichtenrecht ist vorübergehend eingeschränkt.")
        channel, body = self.text(p, "channel"), self.text(p, "body", 1, 2000)
        recipient = None
        if channel == "alliance":
            member = self.member(db, user)
            if not member:
                self.error("Allianzchat erfordert eine Mitgliedschaft.")
            recipient = member["alliance_id"]
        elif channel == "private":
            target = db.execute(
                "SELECT id FROM users WHERE lower(name)=lower(?)", (self.text(p, "name"),)
            ).fetchone()
            if not target or target[0] == user:
                self.error("Empfänger unbekannt oder identisch mit Absender.")
            recipient = target[0]
            if db.execute(
                "SELECT 1 FROM player_blocks WHERE (blocker=? AND blocked=?) "
                "OR (blocker=? AND blocked=?) LIMIT 1",
                (recipient, user, user, recipient),
            ).fetchone():
                self.error("Diese Person nimmt keine privaten Nachrichten von dir an.")
        elif channel != "world":
            self.error("Unbekannter Nachrichtenkanal.")
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES (?,?,?,?,?,?,0,?)",
            (identity(), user, channel, recipient, body, now, int(state.get("world_id", 1))),
        )

    def moderation_case_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        user, now = str(state["id"]), int(time.time())
        reason = self.text(p, "body", 3, 500)
        world_id = int(state.get("world_id", 1))
        if action == "message_report":
            message_id = self.text(p, "key", 1, 100)
            message = db.execute(
                "SELECT sender,channel,recipient,world_id FROM messages " "WHERE id=? AND hidden=0",
                (message_id,),
            ).fetchone()
            if not message or str(message["sender"]) == user:
                self.error("Diese Nachricht kann nicht gemeldet werden.")
            channel = str(message["channel"])
            visible = False
            if channel == "world":
                visible = int(message["world_id"]) == world_id
            elif channel == "private":
                visible = user in (str(message["sender"]), str(message["recipient"]))
            elif channel == "alliance":
                member = self.member(db, user)
                visible = bool(member and str(member["alliance_id"]) == str(message["recipient"]))
            if not visible:
                self.error("Diese Nachricht kannst du nicht melden.")
            if db.execute(
                "SELECT 1 FROM moderation_cases WHERE case_type='message_report' "
                "AND reporter_id=? AND message_id=?",
                (user, message_id),
            ).fetchone():
                self.error("Du hast diese Nachricht bereits gemeldet.")
            case_id = identity()
            db.execute(
                "INSERT INTO moderation_cases"
                "(id,case_type,reporter_id,target_user_id,message_id,world_id,reason,created) "
                "VALUES (?,'message_report',?,?,?,?,?,?)",
                (
                    case_id,
                    user,
                    str(message["sender"]),
                    message_id,
                    world_id,
                    reason,
                    now,
                ),
            )
        else:
            if int(self.profile(db, user)["muted_until"]) <= now:
                self.error("Ein Einspruch ist nur während einer aktiven Stummschaltung möglich.")
            if db.execute(
                "SELECT 1 FROM moderation_cases WHERE case_type='mute_appeal' "
                "AND reporter_id=? AND status='open'",
                (user,),
            ).fetchone():
                self.error("Für diese Stummschaltung ist bereits ein Einspruch offen.")
            case_id = identity()
            db.execute(
                "INSERT INTO moderation_cases"
                "(id,case_type,reporter_id,target_user_id,world_id,reason,created) "
                "VALUES (?,'mute_appeal',?,?,?,?,?)",
                (case_id, user, user, world_id, reason, now),
            )
        self.audit(db, user, action, case_id)

    def social_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        user, target_id, now = state["id"], self.text(p, "key", 1, 100), int(time.time())
        target = db.execute("SELECT id FROM users WHERE id=?", (target_id,)).fetchone()
        if not target or target_id == user:
            self.error("Spieler nicht gefunden.")
        a, b = sorted((user, target_id))
        relationship = db.execute(
            "SELECT requested_by,status FROM friendships WHERE a=? AND b=?", (a, b)
        ).fetchone()
        if action == "friend_request":
            if db.execute(
                "SELECT 1 FROM player_blocks WHERE (blocker=? AND blocked=?) "
                "OR (blocker=? AND blocked=?) LIMIT 1",
                (user, target_id, target_id, user),
            ).fetchone():
                self.error("Diese Kontaktanfrage kann nicht gesendet werden.")
            if relationship:
                self.error("Für diese Spieler besteht bereits ein Kontakt oder eine Anfrage.")
            db.execute(
                "INSERT INTO friendships(a,b,requested_by,status,created,updated) "
                "VALUES (?,?,?,'pending',?,?)",
                (a, b, user, now, now),
            )
            self.audit(db, user, action, target_id)
        elif action == "friend_accept":
            if (
                not relationship
                or relationship["status"] != "pending"
                or relationship["requested_by"] == user
            ):
                self.error("Eingehende Kontaktanfrage nicht gefunden.")
            db.execute(
                "UPDATE friendships SET status='accepted',updated=? WHERE a=? AND b=? "
                "AND status='pending'",
                (now, a, b),
            )
            self.audit(db, user, action, target_id)
        elif action in ("friend_decline", "friend_cancel"):
            if not relationship or relationship["status"] != "pending":
                self.error("Offene Kontaktanfrage nicht gefunden.")
            if (action == "friend_decline" and relationship["requested_by"] == user) or (
                action == "friend_cancel" and relationship["requested_by"] != user
            ):
                self.error("Diese Kontaktanfrage kann von deinem Konto nicht geändert werden.")
            db.execute("DELETE FROM friendships WHERE a=? AND b=?", (a, b))
            self.audit(db, user, action, target_id)
        elif action == "friend_remove":
            if not relationship or relationship["status"] != "accepted":
                self.error("Kontakt nicht gefunden.")
            db.execute("DELETE FROM friendships WHERE a=? AND b=?", (a, b))
            self.audit(db, user, action, target_id)
        elif action == "player_block":
            exists = db.execute(
                "SELECT 1 FROM player_blocks WHERE blocker=? AND blocked=?", (user, target_id)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO player_blocks(blocker,blocked,created) VALUES (?,?,?) "
                    "ON CONFLICT(blocker,blocked) DO NOTHING",
                    (user, target_id, now),
                )
                # Blocking ends an existing friendship so it cannot silently resume after unblock.
                db.execute("DELETE FROM friendships WHERE a=? AND b=?", (a, b))
                self.audit(db, user, action, target_id)
        elif action == "player_unblock":
            if not db.execute(
                "SELECT 1 FROM player_blocks WHERE blocker=? AND blocked=?", (user, target_id)
            ).fetchone():
                self.error("Dieser Spieler steht nicht auf deiner Blockliste.")
            db.execute("DELETE FROM player_blocks WHERE blocker=? AND blocked=?", (user, target_id))
            self.audit(db, user, action, target_id)
        else:
            self.error("Unbekannte Kontaktaktion.")

    def social_page(
        self,
        db: Connection,
        user: str,
        list_name: str,
        before_user_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        if not 1 <= page_size <= 50:
            self.error("Ungültige Größe für die Kontaktliste.")
        scope_params: tuple[Any, ...]
        if list_name == "friends":
            select = (
                "SELECT u.id,u.name,f.created FROM friendships f "
                "JOIN users u ON u.id=CASE WHEN f.a=? THEN f.b ELSE f.a END "
            )
            scope, scope_params, order = (
                "(f.a=? OR f.b=?) AND f.status='accepted'",
                (user, user, user),
                "lower(u.name),u.id",
            )
            name_order = True
        elif list_name == "incoming_requests":
            select = "SELECT u.id,u.name,f.created FROM friendships f JOIN users u ON u.id=f.requested_by "
            scope = "(f.a=? OR f.b=?) AND f.status='pending' AND f.requested_by<>?"
            scope_params = (user, user, user)
            order = "f.created,u.id"
            name_order = False
        elif list_name == "outgoing_requests":
            select = (
                "SELECT u.id,u.name,f.created FROM friendships f "
                "JOIN users u ON u.id=CASE WHEN f.a=? THEN f.b ELSE f.a END "
            )
            scope, scope_params, order = (
                "f.requested_by=? AND f.status='pending'",
                (user, user),
                "f.created,u.id",
            )
            name_order = False
        elif list_name == "blocked":
            select = (
                "SELECT u.id,u.name,b.created FROM player_blocks b JOIN users u ON u.id=b.blocked "
            )
            scope, scope_params, order = (
                "b.blocker=?",
                (user,),
                "lower(u.name),u.id",
            )
            name_order = True
        else:
            self.error("Unbekannte Kontaktliste.")
        cursor_clause = ""
        params: tuple[Any, ...] = scope_params
        if before_user_id is not None:
            cursor = db.execute(
                select + "WHERE " + scope + " AND u.id=?",
                (*scope_params, before_user_id),
            ).fetchone()
            if not cursor:
                self.error("Kontaktlisten-Cursor nicht gefunden.")
            if name_order:
                cursor_clause = "AND (lower(u.name)>? OR (lower(u.name)=? AND u.id>?)) "
                params = (
                    *scope_params,
                    str(cursor["name"]).lower(),
                    str(cursor["name"]).lower(),
                    str(cursor["id"]),
                )
            else:
                cursor_clause = "AND (f.created>? OR (f.created=? AND u.id>?)) "
                params = (
                    *scope_params,
                    int(cursor["created"]),
                    int(cursor["created"]),
                    str(cursor["id"]),
                )
        rows = list(
            db.execute(
                select + "WHERE " + scope + " " + cursor_clause + "ORDER BY " + order + " LIMIT ?",
                (*params, page_size + 1),
            )
        )
        entries = [
            {"id": str(row["id"]), "name": str(row["name"]), "created": int(row["created"])}
            for row in rows[:page_size]
        ]
        return entries, len(rows) > page_size

    def social_state(self, db: Connection, user: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for list_name in ("friends", "incoming_requests", "outgoing_requests", "blocked"):
            result[list_name], result[f"{list_name}_has_more"] = self.social_page(
                db, user, list_name
            )
        return result

    def owned_report_titles(self, db: Connection, user: str, world_id: int) -> dict[str, str]:
        reports: dict[str, str] = {}
        for row in db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=?",
            (user, world_id),
        ):
            colony = json.loads(row["state"])
            for report in colony.get("reports", []):
                report_id, title = report.get("id"), report.get("title")
                if isinstance(report_id, str) and isinstance(title, str):
                    reports[report_id] = title
        return reports

    def notes_command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        user, world_id = str(state["id"]), int(state.get("world_id", 1))
        now = int(time.time())
        if action == "note_delete":
            note_id = self.text(p, "key", 1, 100)
            if not db.execute(
                "DELETE FROM player_notes WHERE id=? AND owner=? AND world_id=? RETURNING id",
                (note_id, user, world_id),
            ).fetchone():
                self.error("Notiz nicht gefunden.")
            self.audit(db, user, action, note_id)
            return

        body = self.text(p, "body", 1, 500)
        target_kind = p.get("target_kind")
        note_id = identity()
        if target_kind == "sector":
            x, y = p.get("x"), p.get("y")
            if type(x) is not int or type(y) is not int or not 0 <= x <= 63 or not 0 <= y <= 63:
                self.error("Koordinaten müssen innerhalb der Weltkarte liegen.")
            db.execute(
                "INSERT INTO player_notes"
                "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
                "VALUES (?,?,?,'sector',?,?,NULL,?,?,?) "
                "ON CONFLICT(owner,world_id,sector_x,sector_y) WHERE target_kind='sector' "
                "DO UPDATE SET body=excluded.body,updated=excluded.updated",
                (note_id, user, world_id, x, y, body, now, now),
            )
            target = f"sector:{x}:{y}"
        elif target_kind == "report":
            report_id = self.text(p, "key", 1, 100)
            existing = db.execute(
                "SELECT 1 FROM player_notes WHERE owner=? AND world_id=? AND report_id=?",
                (user, world_id, report_id),
            ).fetchone()
            if report_id not in self.owned_report_titles(db, user, world_id) and not existing:
                self.error("Bericht in dieser Welt nicht gefunden.")
            db.execute(
                "INSERT INTO player_notes"
                "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
                "VALUES (?,?,?,'report',NULL,NULL,?,?,?,?) "
                "ON CONFLICT(owner,world_id,report_id) WHERE target_kind='report' "
                "DO UPDATE SET body=excluded.body,updated=excluded.updated",
                (note_id, user, world_id, report_id, body, now, now),
            )
            target = f"report:{report_id}"
        else:
            self.error("Notiztyp muss Koordinate oder Bericht sein.")
        self.audit(db, user, action, target)

    def notes_page(
        self,
        db: Connection,
        user: str,
        world_id: int,
        before_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        cursor_clause = ""
        params: tuple[Any, ...] = (user, world_id)
        if before_id is not None:
            cursor = db.execute(
                "SELECT updated,id FROM player_notes WHERE id=? AND owner=? AND world_id=?",
                (before_id, user, world_id),
            ).fetchone()
            if not cursor:
                self.error("Notiz-Cursor ungültig.")
            cursor_clause = "AND (updated<? OR (updated=? AND id>?)) "
            params = (*params, int(cursor["updated"]), int(cursor["updated"]), before_id)
        rows = list(
            db.execute(
                "SELECT id,target_kind,sector_x,sector_y,report_id,body,created,updated "
                "FROM player_notes WHERE owner=? AND world_id=? "
                + cursor_clause
                + "ORDER BY updated DESC,id LIMIT ?",
                (*params, page_size + 1),
            )
        )
        reports = {str(row["report_id"]) for row in rows if row["report_id"] is not None}
        report_titles = self.owned_report_titles(db, user, world_id) if reports else {}
        return [
            {
                "id": str(row["id"]),
                "target_kind": str(row["target_kind"]),
                "x": int(row["sector_x"]) if row["sector_x"] is not None else None,
                "y": int(row["sector_y"]) if row["sector_y"] is not None else None,
                "report_id": str(row["report_id"]) if row["report_id"] is not None else None,
                "report_title": report_titles.get(str(row["report_id"])),
                "body": str(row["body"]),
                "created": int(row["created"]),
                "updated": int(row["updated"]),
            }
            for row in rows[:page_size]
        ], len(rows) > page_size

    def notes_state(
        self, db: Connection, user: str, world_id: int
    ) -> tuple[list[dict[str, Any]], bool]:
        return self.notes_page(db, user, world_id)

    def report_sharing_command(
        self, db: Connection, state: dict[str, Any], action: str, payload: dict[str, Any]
    ) -> None:
        user = str(state["id"])
        world_id = int(state.get("world_id", 1))
        member = self.member(db, user)
        if not member:
            self.error("Berichtsfreigaben erfordern eine aktuelle Allianzmitgliedschaft.")
        if action == "report_share":
            report_id = self.text(payload, "key", 1, 100)
            report = next(
                (
                    item
                    for item in state.get("reports", [])
                    if isinstance(item, dict) and item.get("id") == report_id
                ),
                None,
            )
            if not report:
                self.error("Der Kampfbericht ist nicht in deiner aktuellen Kolonie verfügbar.")
            try:
                summary = report_sharing.project_report(report)
            except (TypeError, ValueError):
                self.error("Nur gültige Kampfberichte können geteilt werden.")
            from .game import identity

            db.execute(
                "INSERT INTO alliance_shared_reports"
                "(id,owner_id,alliance_id,world_id,report_id,summary,created) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(owner_id,world_id,report_id) "
                "DO UPDATE SET alliance_id=excluded.alliance_id,summary=excluded.summary,"
                "created=excluded.created",
                (
                    identity(),
                    user,
                    str(member["alliance_id"]),
                    world_id,
                    report_id,
                    json.dumps(summary, sort_keys=True, separators=(",", ":")),
                    int(time.time()),
                ),
            )
            self.audit(
                db,
                user,
                action,
                report_id,
                world_id=world_id,
                rules_version=report_sharing.VERSION,
                rules_digest=report_sharing.RULES_DIGEST,
            )
            return

        share_id = self.text(payload, "key", 1, 100)
        removed = db.execute(
            "DELETE FROM alliance_shared_reports WHERE id=? AND owner_id=? AND world_id=? "
            "RETURNING id",
            (share_id, user, world_id),
        ).fetchone()
        if not removed:
            self.error("Geteilten Kampfbericht nicht gefunden.")
        self.audit(db, user, action, share_id, world_id=world_id)

    def alliance_shared_report_page(
        self,
        db: Connection,
        user: str,
        alliance_id: str,
        world_id: int,
        before_id: str | None = None,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], bool]:
        member = self.member(db, user)
        if not member or str(member["alliance_id"]) != alliance_id:
            self.error("Aktuelle Allianzmitgliedschaft erforderlich.")
        cursor_clause = ""
        params: tuple[Any, ...] = (user, alliance_id, world_id, user)
        if before_id is not None:
            cursor = db.execute(
                "SELECT created,id FROM alliance_shared_reports WHERE id=? AND alliance_id=? "
                "AND world_id=?",
                (before_id, alliance_id, world_id),
            ).fetchone()
            if not cursor:
                self.error("Cursor für geteilte Berichte ungültig.")
            cursor_clause = "AND (s.created<? OR (s.created=? AND s.id<?)) "
            params = (
                *params[:4],
                int(cursor["created"]),
                int(cursor["created"]),
                before_id,
                *params[4:],
            )
        rows = list(
            db.execute(
                "SELECT s.id,s.owner_id,s.report_id,s.summary,s.created,u.name AS owner_name "
                "FROM alliance_shared_reports s JOIN users u ON u.id=s.owner_id "
                "JOIN members owner_member ON owner_member.user_id=s.owner_id "
                "AND owner_member.alliance_id=s.alliance_id "
                "JOIN members viewer_member ON viewer_member.user_id=? "
                "AND viewer_member.alliance_id=s.alliance_id "
                "WHERE s.alliance_id=? AND s.world_id=? "
                "AND EXISTS (SELECT 1 FROM colonies c WHERE c.user_id=s.owner_id "
                "AND c.world_id=s.world_id) "
                "AND EXISTS (SELECT 1 FROM colonies c WHERE c.user_id=? "
                "AND c.world_id=s.world_id) "
                + cursor_clause
                + "ORDER BY s.created DESC,s.id DESC LIMIT ?",
                (*params, page_size + 1),
            )
        )
        entries: list[dict[str, Any]] = []
        for row in rows[:page_size]:
            entry: dict[str, Any] = {
                "id": str(row["id"]),
                "owner_name": str(row["owner_name"]),
                "summary": json.loads(row["summary"]),
                "can_revoke": str(row["owner_id"]) == user,
            }
            if entry["can_revoke"]:
                entry["report_id"] = str(row["report_id"])
            entries.append(entry)
        return entries, len(rows) > page_size

    def revoke_owner_report_shares(self, db: Connection, owner: str, alliance_id: str) -> None:
        db.execute(
            "DELETE FROM alliance_shared_reports WHERE owner_id=? AND alliance_id=?",
            (owner, alliance_id),
        )

    def market(self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]) -> None:
        from .game import identity

        now, user = int(time.time()), state["id"]
        world_id = int(state.get("world_id", 1))
        if action == "market_create":
            give, want = self.integer(p, "give", 0, 2), self.integer(p, "want", 0, 2)
            amount, price = self.integer(p, "amount", 10, 100000), self.integer(
                p, "price", 10, 100000
            )
            if give == want or state["resources"][give] < amount:
                self.error("Ungültiger Tausch oder nicht genügend Rohstoffe.")
            if (
                db.execute(
                    "SELECT count(*) FROM offers WHERE owner=? AND world_id=? AND status='open'",
                    (user, world_id),
                ).fetchone()[0]
                >= 10
            ):
                self.error("Maximal zehn offene Angebote.")
            state["resources"][give] -= amount
            db.execute(
                "INSERT INTO offers(id,owner,give_resource,give_amount,want_resource,want_amount,"
                "created,expires,status,buyer,world_id,colony_id) "
                "VALUES (?,?,?,?,?,?,?,?,'open',NULL,?,?)",
                (
                    identity(),
                    user,
                    give,
                    amount,
                    want,
                    price,
                    now,
                    now + 86400,
                    world_id,
                    state["colony_id"],
                ),
            )
            return
        offer = db.execute(
            "SELECT * FROM offers WHERE id=? AND world_id=? AND status='open'",
            (self.text(p, "key"), world_id),
        ).fetchone()
        if not offer or offer["expires"] <= now:
            self.error("Angebot nicht mehr verfügbar.")
        if action == "market_cancel":
            if offer["owner"] != user:
                self.error("Du kannst nur eigene Angebote zurücknehmen.")
            origin = self.game.read_colony(db, offer["colony_id"] or state["colony_id"])
            before = list(origin["resources"])
            origin.setdefault("reserve", [0, 0, 0])[offer["give_resource"]] += offer["give_amount"]
            self.game.report(
                origin, "Marktangebot zurückgenommen", "Die hinterlegte Ware liegt im Reservelager."
            )
            self.ledger(db, origin, "Marktangebot zurückgenommen", before)
            db.execute("UPDATE offers SET status='cancelled' WHERE id=?", (offer["id"],))
        elif action in ("market_accept", "market_protected_convoy"):
            if (
                offer["owner"] == user
                or state["resources"][offer["want_resource"]] < offer["want_amount"]
            ):
                self.error("Eigenes Angebot oder zu wenige Rohstoffe.")
            if action == "market_protected_convoy":
                if (
                    self.world_faction(db, user, world_id) != "syndicate"
                    or "smuggler_navigation" not in state.get("faction_research", [])
                    or state.get("syndicate_convoy_ready_at", 0) > now
                ):
                    self.error(
                        "Der geschützte Konvoi benötigt Syndikatforschung und eine freie Abklingzeit."
                    )
                destination = self.text(p, "colony_id")
                target = db.execute(
                    "SELECT x,y FROM colonies WHERE colony_id=? AND user_id=? AND world_id=?",
                    (destination, user, world_id),
                ).fetchone()
                if not target or destination == state["colony_id"]:
                    self.error("Wähle eine andere eigene Kolonie derselben Welt.")
                travel = self.game.travel_time(
                    db, (state["x"], state["y"]), (target["x"], target["y"]), world_id
                )
                handling = 240 if "market_cipher" in state.get("faction_research", []) else 300
                db.execute(
                    "INSERT INTO terra_market_convoys(offer_id,target,resource,amount,due) VALUES (?,?,?,?,?)",
                    (
                        offer["id"],
                        destination,
                        offer["give_resource"],
                        offer["give_amount"],
                        now + handling + travel,
                    ),
                )
                state["syndicate_convoy_ready_at"] = now + 86400
            else:
                state.setdefault("reserve", [0, 0, 0])[offer["give_resource"]] += offer[
                    "give_amount"
                ]
            state["resources"][offer["want_resource"]] -= offer["want_amount"]
            payment = [0, 0, 0]
            payment[offer["want_resource"]] = offer["want_amount"]
            seller_colony = offer["colony_id"]
            if not seller_colony:
                home = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (offer["owner"], offer["world_id"]),
                ).fetchone()
                if not home:
                    self.error("Das Ursprungskonto besitzt keine Kolonie in dieser Welt.")
                seller_colony = home["colony_id"]
            self.credit_colony(db, seller_colony, payment, "Handelsabschluss", now)
            db.execute("UPDATE offers SET status='filled',buyer=? WHERE id=?", (user, offer["id"]))
            db.execute(
                "INSERT INTO market_trades VALUES (?,?,?,?,?,?,?,?)",
                (
                    identity(),
                    offer["world_id"],
                    now,
                    offer["want_resource"],
                    offer["give_resource"],
                    offer["want_amount"],
                    offer["give_amount"],
                    "player",
                ),
            )
        else:
            self.error("Unbekannter Marktbefehl.")
        self.audit(db, user, action, offer["id"])

    def can_attack(
        self,
        db: Connection,
        attacker: str,
        defender: str,
        now: int,
        world_id: int = 1,
        *,
        read_only: bool = False,
    ) -> None:
        if attacker == defender or not self.pvp_enabled(db, world_id):
            self.error("Spielerangriffe sind derzeit nicht möglich.")
        if db.execute(
            "SELECT 1 FROM terra_inactivity WHERE user_id IN (?,?) AND dormant_at IS NOT NULL",
            (attacker, defender),
        ).fetchone():
            self.error("Spielerangriffe sind derzeit nicht möglich.")
        if read_only:
            defense_row = db.execute(
                "SELECT * FROM profiles WHERE user_id=?", (defender,)
            ).fetchone()
            offense_row = db.execute(
                "SELECT * FROM profiles WHERE user_id=?", (attacker,)
            ).fetchone()
            if not defense_row or not offense_row:
                self.error("Der Zielspieler besitzt kein aufklärbares Profil.")
            defense = dict(defense_row)
            offense = dict(offense_row)
        else:
            defense = self.profile(db, defender)
            offense = self.profile(db, attacker)
        if defense["banned"] or now < defense["joined"] + 3600 or now < offense["joined"] + 3600:
            self.error("Neulingsschutz: beide Konten müssen mindestens eine Stunde bestehen.")
        home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (defender, world_id),
        ).fetchone()
        if not home:
            self.error("Der Zielspieler besitzt keine Heimatkolonie in dieser Welt.")
        if self.game.read_colony(db, home["colony_id"]).get("vacation_until", 0) > now:
            self.error("Der Zielspieler ist im Urlaubsmodus.")
        am, dm = self.member(db, attacker), self.member(db, defender)
        if am and dm:
            if am["alliance_id"] == dm["alliance_id"]:
                self.error("Angriffe auf Allianzmitglieder sind ausgeschlossen.")
            a, b = sorted([am["alliance_id"], dm["alliance_id"]])
            pact = db.execute(
                "SELECT 1 FROM diplomacy WHERE a=? AND b=? AND status='nap' AND accepted=1", (a, b)
            ).fetchone()
            if pact:
                self.error("Ein Nichtangriffspakt schützt diese Allianz.")

    def simulate_player_battle(
        self, db: Connection, state: dict[str, Any], target_user: str, army: dict[str, int]
    ) -> dict[str, Any]:
        """Project a PvP fight using only the attacker's current level-2 intel snapshot."""
        from .game import resolve_player_battle

        world_id = int(state.get("world_id", 1))
        now = int(time.time())
        self.can_attack(db, str(state["id"]), target_user, now, world_id, read_only=True)
        unit_catalog = self.game.unit_catalog_for_world(db, world_id)
        if (
            not isinstance(army, dict)
            or not army
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Wähle mindestens eine verfügbare Einheit für die Gefechtsprobe.")

        intel = db.execute(
            "SELECT level,observed_at,expires_at,data FROM player_intel "
            "WHERE observer_id=? AND target_id=? AND world_id=?",
            (state["id"], target_user, world_id),
        ).fetchone()
        if not intel or int(intel["level"]) < 2 or int(intel["expires_at"]) <= now:
            self.error(
                "Für eine PvP-Gefechtsprobe ist ein aktueller Aufklärungsbericht Stufe 2 nötig."
            )
        try:
            report = json.loads(intel["data"])
            defenders = report["units"]
            defense = report["defense"]
            if (
                not isinstance(defenders, dict)
                or any(
                    unit not in unit_catalog or type(count) is not int or count < 0
                    for unit, count in defenders.items()
                )
                or type(defense) is not int
                or defense < 1
            ):
                raise ValueError("invalid intel snapshot")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.error("Der Aufklärungsbericht enthält keine verwendbare Militärstärke.")
        combat_world = db.execute(
            "SELECT terra_combat_ruleset,terra_retreat_threshold_percent "
            "FROM world_settings WHERE world_id=?",
            (world_id,),
        ).fetchone()
        combat_version = str(combat_world["terra_combat_ruleset"]) if combat_world else "FUR-2"
        from . import terra_combat, terra_defense

        if terra_combat.is_supported_version(combat_version):
            combat = report.get("terra_combat")
            if (
                not isinstance(combat, dict)
                or combat.get("rules_version") != combat_version
                or combat.get("rules_digest") != terra_combat.RULESET_DIGESTS[combat_version]
            ):
                self.error("Für die FUR-3-Gefechtsprobe ist ein neuer Aufklärungsbericht nötig.")
            combat_units = combat.get("units")
            tactics = combat.get("tactics")
            armor_bonus = combat.get("armor_bonus")
            modifiers = combat.get("modifiers")
            if (
                not isinstance(combat_units, dict)
                or any(
                    unit not in terra_combat.rules_for(combat_version)["units"]
                    or type(count) is not int
                    or count < 0
                    for unit, count in combat_units.items()
                )
                or type(tactics) is not int
                or not 0 <= tactics <= 10
                or type(armor_bonus) is not int
                or not 0 <= armor_bonus <= 100
                or not isinstance(modifiers, dict)
            ):
                self.error("Der FUR-3-Aufklärungsbericht enthält ungültige Kampfdaten.")
            defender_structures: dict[str, list[int]] | None = None
            defense_digest: str | None = None
            if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
                defender_structures = combat.get("defender_structures")
                defense_digest = combat.get("defense_rules_digest")
                if not isinstance(defender_structures, dict):
                    self.error(
                        "Für die FUR-3-Gefechtsprobe ist ein neuer Aufklärungsbericht nötig."
                    )
                try:
                    terra_defense.validate_stacks(defender_structures)
                    if defense_digest != terra_defense.DIGEST:
                        raise ValueError("unsupported defense snapshot digest")
                except ValueError:
                    self.error(
                        "Für die FUR-3-Gefechtsprobe ist ein neuer Aufklärungsbericht nötig."
                    )
            try:
                result = terra_combat.simulate(
                    dict(army),
                    combat_units,
                    simulation_key=(
                        f"player:{state['id']}:{target_user}:{world_id}:{int(intel['observed_at'])}"
                    ),
                    attacker_tactics=int(state["tech"]["tactics"]),
                    defender_tactics=tactics,
                    defender_armor_bonus=armor_bonus,
                    defender_modifiers=modifiers,
                    retreat_threshold_percent=int(combat_world["terra_retreat_threshold_percent"]),
                    rules_version=combat_version,
                    defender_structures=defender_structures,
                    defense_rules_digest=defense_digest,
                )
            except (TypeError, ValueError) as exc:
                self.error(f"Der FUR-3-Aufklärungsbericht kann nicht simuliert werden: {exc}")
            result["loot"] = None
            return result
        return resolve_player_battle(
            army,
            defenders,
            defense,
            int(state["tech"]["tactics"]),
            int(state["tech"]["logistics"]),
        )

    def dispatch(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")
        now, key = int(time.time()), self.text(p, "key")
        if key == state["id"]:
            self.error("Wähle einen anderen Zielspieler.")
        world_id = int(state.get("world_id", 1))
        unit_catalog = self.game.unit_catalog_for_world(db, world_id)
        home = db.execute(
            "SELECT colony_id,world_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (key, world_id),
        ).fetchone()
        if not home:
            self.error("Der Zielspieler besitzt keine Heimatkolonie in dieser Welt.")
        target = self.game.read_colony(db, home["colony_id"])
        if not sector_is_known(db, state["id"], world_id, target["x"], target["y"]):
            self.error("Dieser Spielersektor ist noch nicht aufgeklärt.")
        intel_level = 0
        if action in ("attack", "scout"):
            self.can_attack(db, state["id"], key, now, world_id)
        if action == "scout":
            source = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (state["colony_id"], state["id"]),
            ).fetchone()
            if not home or not source or home["world_id"] != source["world_id"]:
                self.error("Aufklärung ist nur auf Spielerziele derselben Welt möglich.")
            target = self.game.read_colony(db, home["colony_id"])
        army = p.get("army", {})
        if (
            not isinstance(army, dict)
            or any(
                k not in unit_catalog or type(n) is not int or n < 0 or n > state["units"].get(k, 0)
                for k, n in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Ungültige Truppenauswahl.")
        if action == "scout":
            if any(unit != "ranger" and count for unit, count in army.items()):
                self.error("Aufklärungsmissionen können nur Ranger entsenden.")
            intel_level = 2 if army.get("ranger", 0) >= 3 else 1
        if int(target.get("world_id", world_id)) != world_id:
            self.error("Missionen sind nur innerhalb derselben Welt möglich.")
        cargo = [0, 0, 0]
        if action == "transport":
            cargo = p.get("resources", [])
            if (
                not isinstance(cargo, list)
                or len(cargo) != 3
                or any(
                    type(n) is not int or n < 0 or n > state["resources"][i]
                    for i, n in enumerate(cargo)
                )
                or sum(cargo) < 1
            ):
                self.error("Ungültige Fracht.")
            capacity = self.game.army_transport_capacity(
                db, world_id, army, int(state["tech"]["logistics"])
            )
            if sum(cargo) > capacity:
                self.error("Transportkapazität reicht nicht aus.")
            state["resources"] = [a - b for a, b in zip(state["resources"], cargo)]
        movement = self.reserve_movement_fuel(
            db,
            state,
            (state["x"], state["y"]),
            (target["x"], target["y"]),
            army,
        )
        travel = int(movement["travel_seconds"])
        for unit, count in army.items():
            state["units"][unit] = state["units"].get(unit, 0) - count
        mission = {
            "id": identity(),
            "kind": action,
            "key": target["colony_id"] if action == "scout" else key,
            "due": now + travel,
            "travel": travel,
            "movement": movement,
            "army": army,
            "loot": cargo,
            "tactics": state["tech"]["tactics"],
            "target_user": key if action == "scout" else None,
            "target_colony_id": target["colony_id"],
            "intel_level": intel_level,
            "label": (
                "Aufklärung bei "
                if action == "scout"
                else "Angriff auf " if action == "attack" else "Transport zu "
            )
            + target["name"],
        }
        if action == "attack":
            from . import terra_combat

            combat_mission = terra_combat.pin_mission(db, mission["id"], world_id, now)
            if combat_mission is not None:
                mission.update(combat_mission)
        if action == "scout":
            from . import terra_combat, terra_intelligence

            combat_world = db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()
            if combat_world and terra_combat.is_supported_version(
                str(combat_world["terra_combat_ruleset"])
            ):
                mission.update(
                    terra_intelligence.pin_mission(
                        db,
                        str(mission["id"]),
                        world_id,
                        str(state["id"]),
                        str(key),
                        int(target["tech"]["tactics"]),
                        int(target["buildings"]["wall"]),
                        now,
                    )
                )
        state["jobs"].append(mission)
        if action == "attack":
            self.game.report(
                target,
                "Feindlicher Anmarsch",
                f"{state['name']} greift an. Ankunft in {travel} Sekunden.",
            )
            self.game.save(db, target)

    def dispatch_expedition(self, db: Connection, state: dict[str, Any], p: dict[str, Any]) -> None:
        """Reserve troops for a frontier expedition to a known neutral outpost sector."""
        from .expeditions import RULES, RULES_DIGEST
        from .game import identity
        from .item_drops import RULE_HASH as ITEM_DROP_HASH
        from .item_drops import RULES as ITEM_DROP_RULES

        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")
        world_id = int(state.get("world_id", 1))
        unit_catalog = self.game.unit_catalog_for_world(db, world_id)
        target_id = self.text(p, "key", 1, 100)
        target = next(
            (post for post in self.game.world_outposts(db, world_id) if post["id"] == target_id),
            None,
        )
        if not target or target["owner"] is not None:
            self.error("Expeditionen können nur zu freien Außenposten-Sektoren starten.")
        if not sector_is_known(db, state["id"], world_id, target["x"], target["y"]):
            self.error("Der Expeditionssektor ist noch nicht aufgeklärt.")
        army = p.get("army", {})
        if (
            not isinstance(army, dict)
            or not army
            or any(
                unit not in unit_catalog
                or type(count) is not int
                or count < 0
                or count > state["units"].get(unit, 0)
                for unit, count in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Wähle mindestens eine verfügbare Einheit für die Expedition.")
        movement = self.reserve_movement_fuel(
            db, state, (state["x"], state["y"]), (target["x"], target["y"]), army
        )
        travel = int(movement["travel_seconds"])
        for unit, count in army.items():
            state["units"][unit] = state["units"].get(unit, 0) - count
        mission_id = identity()
        mission = {
            "id": mission_id,
            "kind": "expedition",
            "key": target_id,
            "world_id": world_id,
            "due": int(time.time()) + travel,
            "travel": travel,
            "movement": movement,
            "army": army,
            "loot": [0, 0, 0],
            "rules_version": RULES["version"],
            "rules_digest": RULES_DIGEST,
            "salvage_bonus_percent": (
                10 if "efficient_salvage" in state.get("faction_research", []) else 0
            ),
            "label": "Expedition nach " + target["name"],
        }
        if crafting.enabled_in_world(db, world_id):
            mission["item_drop_rules_version"] = ITEM_DROP_RULES.version
            mission["item_drop_rules_hash"] = ITEM_DROP_HASH
        state["jobs"].append(mission)
        self.audit(
            db,
            state["id"],
            "expedition_dispatched",
            mission_id,
            target_id=target_id,
            army=army,
            travel=travel,
            rules_version=RULES["version"],
            rules_digest=RULES_DIGEST,
            item_drop_rules_version=mission.get("item_drop_rules_version"),
            item_drop_rules_hash=mission.get("item_drop_rules_hash"),
        )

    def ruin_exploration_target(
        self, db: Connection, state: dict[str, Any], target_id: str
    ) -> dict[str, Any]:
        """Resolve a world-scoped, known ruin for both dispatch and movement quotes."""
        world_id = int(state.get("world_id", 1))
        world = db.execute(
            "SELECT settings FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()
        settings = json.loads(world["settings"] or "{}") if world else {}
        if (
            not isinstance(settings, dict)
            or settings.get("terra_ruin_exploration_ruleset", "FUR-2") != ruin_exploration.VERSION
        ):
            self.error("Ruinenerkundung ist in dieser Welt nicht aktiviert.")
        now = int(time.time())
        ruin = db.execute(
            "SELECT id,x,y,expires FROM terra_ruins WHERE id=? AND world_id=? AND expires>?",
            (target_id, world_id, now),
        ).fetchone()
        if ruin is None:
            self.error("Diese Kolonieruine ist nicht mehr aktiv.")
        if not sector_is_known(db, str(state["id"]), world_id, int(ruin["x"]), int(ruin["y"])):
            self.error("Der Ruinensektor ist noch nicht aufgeklärt.")
        return dict(ruin)

    def dispatch_ruin_exploration(
        self, db: Connection, state: dict[str, Any], p: dict[str, Any]
    ) -> None:
        """Reserve Rangers for an opted-in survey of one currently active ruin."""
        from .game import identity

        world_id = int(state["world_id"])
        target_id = self.text(p, "key", 1, 100)
        ruin = self.ruin_exploration_target(db, state, target_id)
        x, y = int(ruin["x"]), int(ruin["y"])
        now = int(time.time())
        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} gleichzeitige Operationen.")
        army = p.get("army")
        if (
            not isinstance(army, dict)
            or set(army) != {"ranger"}
            or type(army.get("ranger")) is not int
            or not 1 <= army["ranger"] <= int(state["units"].get("ranger", 0))
        ):
            self.error("Für die Ruinenerkundung sind verfügbare Ranger erforderlich.")
        movement = self.reserve_movement_fuel(
            db, state, (int(state["x"]), int(state["y"])), (x, y), army
        )
        travel = int(movement["travel_seconds"])
        mission_id = identity()
        try:
            pinned = ruin_exploration.pin_mission(
                db,
                mission_id,
                world_id,
                str(state["id"]),
                target_id,
                x,
                y,
                now,
                int(ruin["expires"]),
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Could not pin Terra ruin exploration rules") from exc
        state["units"]["ranger"] -= army["ranger"]
        mission = {
            "id": mission_id,
            "kind": "ruin_exploration",
            "key": target_id,
            "world_id": world_id,
            "x": x,
            "y": y,
            "due": now + travel,
            "travel": travel,
            "movement": movement,
            "army": dict(army),
            "loot": [0, 0, 0],
            "label": "Ruinenerkundung",
            **pinned,
        }
        state["jobs"].append(mission)
        self.audit(
            db,
            str(state["id"]),
            "ruin_exploration_dispatched",
            mission_id,
            world_id=world_id,
            ruin_id=target_id,
            coordinates=[x, y],
            rangers=army["ranger"],
            rules_version=ruin_exploration.VERSION,
            rules_digest=ruin_exploration.DIGEST,
            seed_commitment=pinned["seed_commitment"],
        )

    def process_job(self, db: Connection, state: dict[str, Any], job: dict[str, Any]) -> bool:
        from . import terra_combat, terra_defense, terra_intelligence
        from .game import identity

        if job["kind"] == "npc_convoy":
            result = npc_convoys.resolve(
                db,
                int(state["world_id"]),
                str(job["key"]),
                str(state["id"]),
                str(job["id"]),
                int(job["due"]),
            )
            self.audit(db, str(state["id"]), "npc_convoy_resolved", str(job["id"]), **result)
            opponent = "NPC-Plünderer" if result["role"] == "escort" else "NPC-Konvoiwache"
            convoy_outcome = "Sieg" if result["victory"] else "Niederlage"
            self.game.report(
                state,
                "Konvoigefecht abgeschlossen",
                f"{convoy_outcome} gegen {opponent}. {result['survivors']} Ranger kehren zurück. "
                f"Abholbare Belohnung: {result['reward_ore']} Erz.",
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": str(state["colony_id"]),
                    "label": "Rückmarsch vom Konvoi",
                    "due": result["return_due"],
                    "army": {"ranger": result["survivors"]},
                    "loot": [0, 0, 0],
                }
            )
            return True
        if job["kind"] == "terra_boss_attack":
            raid_id = str(job["key"])
            damage, returning_rangers = boss_raids.resolve(
                db,
                int(state["world_id"]),
                raid_id,
                str(state["id"]),
                str(job["id"]),
                int(job["due"]),
            )
            self.audit(
                db,
                str(state["id"]),
                "terra_boss_attack_resolved",
                raid_id,
                world_id=int(state["world_id"]),
                mission_id=str(job["id"]),
                damage=damage,
                survivors=returning_rangers,
            )
            self.game.report(
                state,
                "Weltboss-Angriff abgeschlossen",
                f"{damage} Schaden verbucht. {returning_rangers} Ranger kehren zur Kolonie zurück.",
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": str(state["colony_id"]),
                    "label": "Rückmarsch vom Weltboss",
                    "due": int(job["due"]) + int(boss_raids.RULES["attack_seconds"]),
                    "army": {"ranger": returning_rangers},
                    "loot": [0, 0, 0],
                }
            )
            return True
        if job["kind"] == "craft":
            from . import crafting

            output = crafting.complete(state, job, int(job["due"]))
            self.game.report(
                state,
                "Fertigung abgeschlossen",
                f"{job['label']}: "
                + ", ".join(f"{amount} {item_id}" for item_id, amount in output.items()),
            )
            self.audit(
                db,
                state["id"],
                "craft_completed",
                str(job["id"]),
                recipe_id=job["recipe_id"],
                batches=job["batches"],
                output=output,
                rules_version=crafting.RULES.version,
                rules_hash=crafting.RULE_HASH,
            )
            return True
        if job["kind"] == "alliance_attack_wing":
            return True
        if job["kind"] == "alliance_attack":
            self.resolve_terra_alliance_attack(db, state, job)
            return True
        if job["kind"] == "expedition":
            from . import item_drops
            from .expeditions import RULES_DIGEST, resolve_expedition, validate_ruleset
            from .items import ITEMS as ITEM_CATALOG
            from .items import RULES as ITEM_CATALOG_RULES

            try:
                validate_ruleset(
                    str(job.get("rules_version", "")), str(job.get("rules_digest", ""))
                )
            except ValueError:
                raise RuntimeError("Unsupported expedition rule version")
            result = resolve_expedition(str(job["id"]), dict(job["army"]))
            survivors = result["survivors"]
            lost = sum(job["army"].values()) - sum(survivors.values())
            labels = {
                "discovery": "Kartendaten gesichert",
                "cache": "Vorräte gefunden",
                "skirmish": "Grenzpatrouille abgewehrt",
                "hazard": "Geländeschaden erlitten",
                "quiet": "Keine besonderen Vorkommnisse",
            }
            capacity = sum(survivors.values()) * (40 + 10 * int(state["tech"]["logistics"]))
            bonus = job.get("salvage_bonus_percent", 0)
            loot = [amount * (100 + bonus) // 100 for amount in result["loot"]]
            remaining_capacity = capacity
            for resource in range(len(loot)):
                loot[resource] = min(loot[resource], remaining_capacity)
                remaining_capacity -= loot[resource]
            item_cargo: dict[str, int] = {}
            item_drop_result: dict[str, Any] = {
                "rules_version": None,
                "rules_hash": None,
                "outcome": result["outcome"],
                "rolls": [],
            }
            drop_version = job.get("item_drop_rules_version")
            drop_hash = job.get("item_drop_rules_hash")
            if drop_version is not None or drop_hash is not None:
                if not isinstance(drop_version, str) or not isinstance(drop_hash, str):
                    raise RuntimeError("Invalid expedition item-drop rule reference")
                try:
                    item_drop_result = item_drops.resolve(
                        str(job["id"]), str(result["outcome"]), drop_version, drop_hash
                    )
                except ValueError as exc:
                    raise RuntimeError("Unsupported expedition item-drop rules") from exc
                for drop in item_drop_result["rolls"]:
                    requested = int(drop["amount"])
                    weight = ITEM_CATALOG_RULES.transport_weight
                    carried = min(requested, remaining_capacity // weight)
                    if carried:
                        item_cargo[str(drop["item_id"])] = carried
                    remaining_capacity -= carried * weight
                    drop["carried"] = carried
                    drop["unrecovered"] = requested - carried
            item_summary = ""
            if item_cargo:
                item_summary = (
                    " Bergung: "
                    + ", ".join(
                        f"{amount} {ITEM_CATALOG[item_id].name}"
                        for item_id, amount in item_cargo.items()
                    )
                    + "."
                )
            elif any(int(drop.get("amount", 0)) > 0 for drop in item_drop_result["rolls"]):
                item_summary = " Bergungsmaterial gefunden, aber die Trägerkapazität war belegt."
            self.game.report(
                state,
                "Expedition: " + labels[result["outcome"]],
                f"Regel {result['rules_version']} · SHA-256 {result['rules_digest'][:12]} · "
                f"Truppenverluste {lost} "
                f"({result['loss_percent']} %) · Rückfracht: "
                f"{loot[0]} Holz, {loot[1]} Stein, {loot[2]} Erz.{item_summary}",
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": job["key"],
                    "label": "Rückkehr von " + str(job["label"]),
                    "due": int(job["due"]) + int(job["travel"]),
                    "army": survivors,
                    "loot": loot,
                    "item_cargo": item_cargo,
                }
            )
            self.audit(
                db,
                state["id"],
                "expedition_resolved",
                str(job["id"]),
                outcome=result["outcome"],
                loss_percent=result["loss_percent"],
                survivors=survivors,
                loot=loot,
                item_drops=item_drop_result["rolls"],
                rules_version=result["rules_version"],
                rules_digest=RULES_DIGEST,
                item_drop_rules_version=item_drop_result["rules_version"],
                item_drop_rules_hash=item_drop_result["rules_hash"],
            )
            return True
        if job["kind"] == "ruin_exploration":
            try:
                seed, pin, resolved = ruin_exploration.mission_seed(
                    db, str(job["id"]), int(job["world_id"]), str(state["id"])
                )
                if (
                    str(job.get("rules_version")) != ruin_exploration.VERSION
                    or str(job.get("rules_digest")) != ruin_exploration.DIGEST
                    or str(pin["ruin_id"]) != str(job["key"])
                    or int(pin["x"]) != int(job["x"])
                    or int(pin["y"]) != int(job["y"])
                    or str(pin["seed_commitment"]) != str(job.get("seed_commitment"))
                    or int(pin["expires"]) <= int(pin["created"])
                    or resolved
                ):
                    raise ValueError("invalid pinned ruin mission")
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError("Invalid Terra ruin exploration mission") from exc
            result = ruin_exploration.resolve(seed, dict(job["army"]))
            survivors = dict(result["survivors"])
            loot = result["loot"]
            observed = int(job["due"])
            expires = observed + int(
                ruin_exploration.RULES["ruin_survey"]["intel_retention_seconds"]
            )
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET "
                "observed_at=excluded.observed_at "
                "WHERE excluded.observed_at>map_sector_intel.observed_at",
                (state["id"], int(job["world_id"]), int(job["x"]), int(job["y"]), observed),
            )
            db.execute(
                "INSERT INTO terra_ruin_intel"
                "(observer_id,world_id,ruin_id,x,y,observed_at,expires_at,outcome) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(observer_id,world_id,ruin_id) DO UPDATE SET "
                "x=excluded.x,y=excluded.y,observed_at=excluded.observed_at,"
                "expires_at=excluded.expires_at,outcome=excluded.outcome "
                "WHERE excluded.observed_at>=terra_ruin_intel.observed_at",
                (
                    state["id"],
                    int(job["world_id"]),
                    str(job["key"]),
                    int(job["x"]),
                    int(job["y"]),
                    observed,
                    expires,
                    str(result["outcome"]),
                ),
            )
            outcome_labels = {
                "relic_cache": "Versiegeltes Reliktlager geborgen",
                "salvage": "Brauchbare Ruinenfracht geborgen",
                "unstable_ruin": "Instabile Kammern entdeckt",
                "hazard": "Gefährliche Trümmer ausgelöst",
                "quiet": "Keine besonderen Vorkommnisse",
            }
            lost = int(job["army"]["ranger"]) - survivors["ranger"]
            self.game.report(
                state,
                "Ruinenerkundung abgeschlossen",
                f"{outcome_labels[result['outcome']]} · {lost} Ranger verloren · "
                f"{loot[0]} Holz, {loot[1]} Stein, {loot[2]} Erz geborgen. "
                "Sektordaten und private Ruinenbeobachtung wurden aktualisiert.",
            )
            ruin_exploration.store_outcome(db, str(job["id"]), result, observed)
            self.audit(
                db,
                str(state["id"]),
                "ruin_exploration_resolved",
                str(job["id"]),
                world_id=int(job["world_id"]),
                ruin_id=str(job["key"]),
                coordinates=[int(job["x"]), int(job["y"])],
                outcome=str(result["outcome"]),
                loss_percent=int(result["loss_percent"]),
                survivors=survivors,
                loot=loot,
                rules_version=ruin_exploration.VERSION,
                rules_digest=ruin_exploration.DIGEST,
                seed_commitment=result["seed_commitment"],
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": str(state["colony_id"]),
                    "label": "Erkundungstrupp kehrt aus der Ruine zurück",
                    "due": observed + int(job["travel"]),
                    "army": survivors,
                    "loot": loot,
                }
            )
            return True

        if job["kind"] == "alliance_garrison":
            from . import terra_garrison

            host = db.execute(
                "SELECT colony_id,user_id,world_id FROM colonies "
                "WHERE colony_id=? AND user_id=? AND is_home=TRUE",
                (job["key"], job["host_user"]),
            ).fetchone()
            source = db.execute(
                "SELECT colony_id,world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (state["colony_id"], state["id"]),
            ).fetchone()
            contributor_member = self.member(db, str(state["id"]))
            host_member = self.member(db, str(job["host_user"])) if host else None
            policy = db.execute(
                "SELECT * FROM terra_allied_garrison_policies "
                "WHERE home_colony_id=? AND host_user_id=? AND alliance_id=? AND enabled=TRUE",
                (job["key"], job["host_user"], job["alliance_id"]),
            ).fetchone()
            reservation = db.execute(
                "SELECT id FROM terra_allied_garrisons WHERE id=? AND contributor_id=? "
                "AND host_colony_id=? AND status='travelling'",
                (job["id"], state["id"], job["key"]),
            ).fetchone()
            valid = bool(
                host
                and source
                and int(host["world_id"]) == int(source["world_id"]) == int(state["world_id"])
                and contributor_member
                and host_member
                and contributor_member["alliance_id"] == job["alliance_id"]
                and host_member["alliance_id"] == job["alliance_id"]
                and policy
                and reservation
                and job.get("rule_version") == terra_garrison.VERSION
            )
            if valid:
                db.execute(
                    "UPDATE terra_allied_garrisons SET status='active' "
                    "WHERE id=? AND status='travelling'",
                    (str(job["id"]),),
                )
                self.game.report(
                    state,
                    "Alliierte Garnison eingetroffen",
                    "Deine Einheiten sichern die verbündete Heimatkolonie.",
                )
                host_state = self.game.read_colony(db, str(host["colony_id"]))
                self.game.report(
                    host_state,
                    "Alliierte Garnison eingetroffen",
                    f"Ein Allianzmitglied hat {sum(job['army'].values())} Einheiten stationiert.",
                )
                self.game.save(db, host_state)
                self.audit(
                    db,
                    str(state["id"]),
                    "alliance_garrison_arrival",
                    str(job["id"]),
                    host=str(host["colony_id"]),
                    army=job["army"],
                )
                self.game.record_war_score(
                    db,
                    mission_id=str(job["id"]),
                    world_id=int(state["world_id"]),
                    user_id=str(state["id"]),
                    category="support",
                    points=sum(int(count) for count in job["army"].values()),
                    rules_version=str(
                        db.execute(
                            "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                            (int(state["world_id"]),),
                        ).fetchone()[0]
                    ),
                    at=int(job["due"]),
                )
            else:
                db.execute(
                    "DELETE FROM terra_allied_garrisons WHERE id=? AND status='travelling'",
                    (str(job["id"]),),
                )
                state["jobs"].append(
                    {
                        "id": identity(),
                        "kind": "return",
                        "key": str(state["colony_id"]),
                        "label": "Nicht angenommene Garnison kehrt zurück",
                        "due": int(job["due"]) + int(job["travel"]),
                        "army": dict(job["army"]),
                        "loot": [0, 0, 0],
                    }
                )
                self.game.report(
                    state,
                    "Alliierte Garnison abgelehnt",
                    "Freigabe, Allianz, Ziel oder Kapazität haben sich geändert. Deine Einheiten kehren zurück.",
                )
                self.audit(
                    db,
                    str(state["id"]),
                    "alliance_garrison_rejected",
                    str(job["id"]),
                    target_colony=str(job["key"]),
                )
            return True
        if job["kind"] == "station":
            world_id = int(state.get("world_id", 1))
            towns = self.game.world_outposts(db, world_id)
            target = next(t for t in towns if t["id"] == job["key"])
            if target["owner"] == state["id"]:
                for unit, count in job["army"].items():
                    target.setdefault("units", {}).setdefault(unit, 0)
                    target["units"][unit] += count
                self.game.save_world_outposts(db, world_id, towns)
                self.game.report(state, "Garnison verstärkt", target["name"])
            else:
                state["jobs"].append(
                    {
                        "id": identity(),
                        "kind": "return",
                        "key": job["key"],
                        "label": "Garnison kehrt zurück",
                        "due": job["due"] + job["travel"],
                        "army": job["army"],
                        "loot": [0, 0, 0],
                    }
                )
            return True
        if job["kind"] == "colony_supply":
            target_owner = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (job["key"], state["id"]),
            ).fetchone()
            source_world = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (state["colony_id"], state["id"]),
            ).fetchone()
            if (
                not target_owner
                or not source_world
                or target_owner["world_id"] != source_world["world_id"]
            ):
                raise RuntimeError("Eigentum oder Welt der Zielkolonie hat sich geändert.")
            target = self.game.read_colony(db, job["key"])
            army = dict(job["army"])
            cargo = list(job.get("loot", [0, 0, 0]))
            goods_cargo = job.get("goods_cargo", {})
            item_cargo = job.get("item_cargo", {})
            if not isinstance(goods_cargo, dict):
                raise RuntimeError("Gespeicherte Warenfracht ist ungültig.")
            if not isinstance(item_cargo, dict):
                raise RuntimeError("Gespeicherte Gegenstandsfracht ist ungültig.")
            from . import items as generic_items

            generic_items.receive_reserved(target, item_cargo)
            item_inventory = dict(target.get("item_inventory", {}))
            item_inbound = dict(target.get("item_inbound", {}))
            from .neutral_market import depot_capacity

            goods_inventory = dict(target.get("goods_inventory", {}))
            goods_inbound = dict(target.get("goods_inbound", {}))
            for good_id, amount in goods_cargo.items():
                if type(amount) is not int or amount < 0:
                    raise RuntimeError("Gespeicherte Warenfracht ist ungültig.")
                reserved = int(goods_inbound.get(good_id, 0))
                if reserved < amount:
                    raise RuntimeError("Warenfrachtreservierung fehlt.")
                goods_inbound[good_id] = reserved - amount
                if goods_inbound[good_id] == 0:
                    goods_inbound.pop(good_id)
                goods_inventory[good_id] = int(goods_inventory.get(good_id, 0)) + amount
            target["goods_inventory"] = goods_inventory
            target["goods_inbound"] = goods_inbound
            if any(amount > depot_capacity(target) for amount in goods_inventory.values()):
                raise RuntimeError("Warenfracht überschreitet das reservierte Depotlimit.")
            self.credit_colony(
                db,
                job["key"],
                cargo,
                "Kolonieversorgung eingetroffen",
                int(job["due"]),
            )
            target = self.game.read_colony(db, job["key"])
            target["goods_inventory"] = goods_inventory
            target["goods_inbound"] = goods_inbound
            target["item_inventory"] = item_inventory
            target["item_inbound"] = item_inbound
            self.game.save(db, target)
            self.game.report(
                state,
                "Kolonieversorgung zugestellt",
                f"{target.get('colony_name', target['name'])} erhielt "
                f"{cargo[0]} Holz, {cargo[1]} Stein und {cargo[2]} Erz. "
                f"Materialwaren: {sum(goods_cargo.values())}; "
                f"Gegenstände: {sum(item_cargo.values())}. Die Träger kehren zurück.",
            )
            self.audit(
                db,
                state["id"],
                "colony_supply_arrival",
                job["key"],
                source=state["colony_id"],
                cargo=cargo,
                goods=goods_cargo,
                items=item_cargo,
                carriers=army,
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": state["colony_id"],
                    "label": "Träger kehren zur Ausgangskolonie zurück",
                    "due": job["due"] + job["travel"],
                    "army": army,
                    "loot": [0, 0, 0],
                    "goods_cargo": {},
                    "item_cargo": {},
                    "route_id": job.get("route_id"),
                }
            )
            return True
        if job["kind"] == "alliance_supply":
            target_row = db.execute(
                "SELECT user_id,world_id FROM colonies WHERE colony_id=?",
                (job["key"],),
            ).fetchone()
            source_row = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (state["colony_id"], state["id"]),
            ).fetchone()
            source_member = self.member(db, state["id"])
            target_member = self.member(db, target_row["user_id"]) if target_row else None
            valid_receipt = bool(
                target_row
                and target_row["user_id"] == job.get("target_user")
                and source_row
                and target_row["world_id"] == source_row["world_id"]
                and source_member
                and target_member
                and source_member["alliance_id"] == job.get("alliance_id")
                and target_member["alliance_id"] == job.get("alliance_id")
            )
            army = dict(job["army"])
            cargo = list(job.get("loot", [0, 0, 0]))
            if valid_receipt:
                self.credit_colony(
                    db, job["key"], cargo, "Allianzversorgung eingetroffen", int(job["due"])
                )
                self.game.report(
                    state,
                    "Allianzversorgung zugestellt",
                    f"Dein Bündnispartner erhielt {cargo[0]} Holz, {cargo[1]} Stein und "
                    f"{cargo[2]} Erz. Die Träger kehren zurück.",
                )
                self.audit(
                    db,
                    state["id"],
                    "alliance_supply_arrival",
                    job["key"],
                    recipient=job["target_user"],
                    cargo=cargo,
                    carriers=army,
                )
            else:
                self.credit_state(
                    db, state, cargo, "Abgebrochene Allianzversorgung erstattet", int(job["due"])
                )
                self.game.report(
                    state,
                    "Allianzversorgung abgebrochen",
                    "Der Empfänger gehört bei Ankunft nicht mehr deiner Allianz oder Welt. "
                    "Die Fracht wurde erstattet; die Träger kehren zurück.",
                )
                self.audit(
                    db,
                    state["id"],
                    "alliance_supply_receipt_rejected",
                    job["key"],
                    recipient=job.get("target_user", ""),
                    cargo=cargo,
                    carriers=army,
                )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": state["colony_id"],
                    "label": "Allianzträger kehren zurück",
                    "due": job["due"] + job["travel"],
                    "army": army,
                    "loot": [0, 0, 0],
                }
            )
            return True
        if job["kind"] == "scout":
            from .game import RuleError

            army = dict(job["army"])
            return_army = army
            try:
                target = self.game.read_colony(db, job["key"])
                self.can_attack(
                    db,
                    state["id"],
                    job["target_user"],
                    int(job["due"]),
                    int(state.get("world_id", 1)),
                )
                target_owner = db.execute(
                    "SELECT user_id,world_id FROM colonies WHERE colony_id=?",
                    (job["key"],),
                ).fetchone()
                source_world = db.execute(
                    "SELECT world_id FROM colonies WHERE colony_id=?",
                    (state["colony_id"],),
                ).fetchone()
                if (
                    not target_owner
                    or target_owner["user_id"] != job["target_user"]
                    or not source_world
                    or source_world["world_id"] != target_owner["world_id"]
                ):
                    raise RuleError("Zielkolonie oder Welt hat sich geändert.")
            except RuleError as exc:
                if job.get("intel_rules_version") == terra_intelligence.VERSION:
                    terra_intelligence.discard_mission(db, str(job["id"]))
                self.game.report(
                    state, "Aufklärung abgebrochen", f"{exc} Alle Ranger kehren zurück."
                )
            else:
                level = int(job["intel_level"])
                counterintel: dict[str, Any] | None = None
                if job.get("intel_rules_version") == terra_intelligence.VERSION:
                    try:
                        seed, interception, detection, resolved = terra_intelligence.mission_seed(
                            db,
                            str(job["id"]),
                            int(state.get("world_id", 1)),
                            str(state["id"]),
                            str(job["target_user"]),
                            str(job["intel_seed_commitment"]),
                        )
                    except (KeyError, TypeError, ValueError) as exc:
                        raise RuntimeError("Invalid pinned counterintelligence record") from exc
                    if resolved:
                        return True
                    counterintel = terra_intelligence.resolve(
                        seed,
                        sum(army.values()),
                        interception_percent=interception,
                        detection_percent=detection,
                    )
                    if counterintel["intercepted"]:
                        returned = int(counterintel["rangers_returned"])
                        return_army = {"ranger": returned} if returned else {}
                    terra_intelligence.store_outcome(
                        db, str(job["id"]), counterintel, int(job["due"])
                    )
                    if counterintel["detected"]:
                        self.game.report(
                            target,
                            "Aufklärungsversuch entdeckt",
                            "Eine feindliche Spähmission wurde erkannt. Angreifer und Truppenstärke "
                            "werden nicht offengelegt.",
                        )
                        self.game.save(db, target)
                    if counterintel["intercepted"]:
                        self.game.report(
                            state,
                            "Aufklärung abgefangen",
                            "Die Gegenaufklärung hat einen Ranger abgefangen. Es wurden keine "
                            "Zieldaten gewonnen; überlebende Ranger kehren zurück.",
                        )
                        self.audit(
                            db,
                            state["id"],
                            "scout_intercepted",
                            str(job["target_user"]),
                            lost=int(counterintel["rangers_lost"]),
                            returned=int(counterintel["rangers_returned"]),
                            rules_version=counterintel["rules_version"],
                            rules_digest=counterintel["rules_digest"],
                        )
                    elif counterintel["detected"]:
                        self.audit(
                            db,
                            state["id"],
                            "scout_detected",
                            str(job["target_user"]),
                            rules_version=counterintel["rules_version"],
                            rules_digest=counterintel["rules_digest"],
                        )
                    self.audit(
                        db,
                        str(job["target_user"]),
                        "counterintel_alert",
                        str(job["id"]),
                        detected=bool(counterintel["detected"]),
                        intercepted=bool(counterintel["intercepted"]),
                        rules_version=counterintel["rules_version"],
                        rules_digest=counterintel["rules_digest"],
                    )
                if counterintel is None or not counterintel["intercepted"]:
                    data: dict[str, Any] = {
                        "hq": int(target["buildings"]["hq"]),
                        "buildings": dict(target["buildings"]),
                    }
                    if level >= 2:
                        data.update(
                            defense=self.fortified_player_defense(
                                db,
                                target,
                                self.world_faction(db, job["target_user"], int(target["world_id"]))
                                or "pioneers",
                                int(job["due"]),
                            ),
                            garrison=sum(target["units"].values()),
                            units=dict(target["units"]),
                        )
                        combat_world = db.execute(
                            "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=?",
                            (int(target["world_id"]),),
                        ).fetchone()
                        if combat_world and terra_combat.is_supported_version(
                            str(combat_world["terra_combat_ruleset"])
                        ):
                            combat_rules = terra_combat.rules_for(
                                str(combat_world["terra_combat_ruleset"])
                            )
                            combat_units = dict(target["units"])
                            for garrison in self.active_allied_garrisons(db, target):
                                for unit, count in json.loads(garrison["army"]).items():
                                    combat_units[unit] = combat_units.get(unit, 0) + int(count)
                            defender_faction = (
                                self.world_faction(
                                    db, str(job["target_user"]), int(target["world_id"])
                                )
                                or "pioneers"
                            )
                            data["terra_combat"] = {
                                "rules_version": str(combat_world["terra_combat_ruleset"]),
                                "rules_digest": terra_combat.RULESET_DIGESTS[
                                    str(combat_world["terra_combat_ruleset"])
                                ],
                                "units": combat_units,
                                "tactics": int(target["tech"]["tactics"]),
                                "armor_bonus": min(
                                    100,
                                    int(target["buildings"]["wall"])
                                    * int(combat_rules["formula"]["wall_armor_bonus_per_level"]),
                                ),
                                "modifiers": {
                                    "terrain": int(
                                        DEFENSE_PERCENT[str(target.get("terrain", "plain"))]
                                    ),
                                    "faction": (
                                        110
                                        if defender_faction == "wardens"
                                        and "kinetic_shield" in target.get("faction_research", [])
                                        else 100
                                    ),
                                },
                            }
                            if str(combat_world["terra_combat_ruleset"]) in (
                                "FUR-3-TERRA-COMBAT-4",
                                "FUR-3-TERRA-COMBAT-5",
                            ):
                                scout_defense_stacks = target.get("terra_defense_stacks", {})
                                terra_defense.validate_stacks(scout_defense_stacks)
                                scout_defense_digest = (
                                    str(target.get("terra_defense_rules_digest"))
                                    if any(scout_defense_stacks.values())
                                    else terra_defense.DIGEST
                                )
                                if scout_defense_digest != terra_defense.DIGEST:
                                    raise RuntimeError("Unsupported Terra defense intel digest")
                                data["terra_combat"]["defender_structures"] = scout_defense_stacks
                                data["terra_combat"]["defense_rules_digest"] = scout_defense_digest
                    try:
                        lifetime = hero_doctrines.intel_lifetime_seconds(job)
                    except ValueError as exc:
                        raise RuntimeError("Unsupported pinned hero doctrine rules") from exc
                    observed, expires = int(job["due"]), int(job["due"]) + lifetime
                    db.execute(
                        "INSERT INTO player_intel(observer_id,target_id,level,observed_at,expires_at,data,world_id) "
                        "VALUES (?,?,?,?,?,?,?) ON CONFLICT(observer_id,target_id) DO UPDATE SET "
                        "level=excluded.level,observed_at=excluded.observed_at,"
                        "expires_at=excluded.expires_at,data=excluded.data,world_id=excluded.world_id",
                        (
                            state["id"],
                            job["target_user"],
                            level,
                            observed,
                            expires,
                            json.dumps(data),
                            int(state.get("world_id", 1)),
                        ),
                    )
                    self.audit(db, state["id"], "scout_arrival", job["target_user"], level=level)
                    self.game.report(
                        state,
                        "Aufklärung abgeschlossen",
                        f"{target['name']}: Informationsstufe {level}; Bericht gültig bis "
                        f"{time.strftime('%H:%M:%S', time.localtime(expires))}.",
                    )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": state["colony_id"],
                    "label": "Aufklärer kehren zur Ausgangskolonie zurück",
                    "due": int(job["due"]) + int(job["travel"]),
                    "army": return_army,
                    "loot": [0, 0, 0],
                }
            )
            return True
        if job["kind"] not in ("attack", "transport"):
            return False

        army, loot = dict(job["army"]), list(job.get("loot", [0, 0, 0]))
        world_id = int(state["world_id"])
        target_colony_id = job.get("target_colony_id")
        if target_colony_id:
            target_row = db.execute(
                "SELECT colony_id FROM colonies WHERE colony_id=? AND user_id=? AND world_id=?",
                (target_colony_id, job["key"], world_id),
            ).fetchone()
        else:
            # Older jobs did not pin a colony. Their fallback is the home in the
            # source world, never the target account's currently selected world.
            target_row = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                (job["key"], world_id),
            ).fetchone()
        if not target_row:
            if terra_combat.is_supported_version(str(job.get("rules_version", ""))):
                terra_combat.discard_mission(db, str(job["id"]))
            self.game.report(
                state,
                "Mission abgebrochen",
                "Die ursprüngliche Zielkolonie ist nicht mehr verfügbar.",
            )
            state["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": state["colony_id"],
                    "label": "Rückkehr vom nicht verfügbaren Ziel",
                    "due": job["due"] + job["travel"],
                    "army": army,
                    "loot": loot,
                }
            )
            return True
        target = self.game.read_colony(db, target_row["colony_id"])
        if job["kind"] == "transport":
            self.credit_colony(db, target["colony_id"], loot, "Transport angekommen", at=job["due"])
            loot = [0, 0, 0]
            self.game.report(state, "Transport zugestellt", "Deine Transporttruppen kehren zurück.")
        else:
            from .game import RuleError

            try:
                self.can_attack(
                    db,
                    state["id"],
                    target["id"],
                    job["due"],
                    int(state.get("world_id", 1)),
                )
            except RuleError as exc:
                if terra_combat.is_supported_version(str(job.get("rules_version", ""))):
                    terra_combat.discard_mission(db, str(job["id"]))
                self.game.report(state, "Angriff abgebrochen", str(exc))
            else:
                self.game.produce(target, job["due"])
                before = list(target["resources"])
                army_in = dict(army)
                defenders_in = dict(target["units"])
                defender_host_before = dict(target["units"])
                combat_garrisons: list[Any] = []
                combat_version = str(job.get("rules_version", "FUR-2"))
                from .game import REGISTRY, RULES_DIGEST, resolve_player_battle

                if terra_combat.is_supported_version(combat_version):
                    combat_rules = terra_combat.rules_for(combat_version)
                    if job.get("rules_digest") != terra_combat.RULESET_DIGESTS[combat_version]:
                        raise RuntimeError("Unsupported FUR-3 combat rules digest")
                    try:
                        seed, retreat_threshold = terra_combat.mission_seed(
                            db,
                            str(job["id"]),
                            world_id,
                            str(job.get("seed_commitment", "")),
                        )
                    except ValueError as exc:
                        raise RuntimeError("Invalid FUR-3 combat replay record") from exc
                    combat_garrisons = self.active_allied_garrisons(db, target)
                    for garrison in combat_garrisons:
                        for unit, count in json.loads(garrison["army"]).items():
                            defenders_in[unit] = defenders_in.get(unit, 0) + int(count)
                    defender_faction = (
                        self.world_faction(db, target["id"], int(target["world_id"])) or "pioneers"
                    )
                    combat_modifiers = {
                        "terrain": int(DEFENSE_PERCENT[str(target.get("terrain", "plain"))]),
                        "faction": (
                            110
                            if defender_faction == "wardens"
                            and "kinetic_shield" in target.get("faction_research", [])
                            else 100
                        ),
                    }
                    defender_structures: dict[str, list[int]] | None = None
                    defense_digest: str | None = None
                    if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
                        defender_structures = target.get("terra_defense_stacks", {})
                        defense_digest = (
                            str(target.get("terra_defense_rules_digest"))
                            if any(defender_structures.values())
                            else terra_defense.DIGEST
                        )
                    outcome = terra_combat.resolve(
                        seed,
                        army,
                        defenders_in,
                        attacker_tactics=int(job["tactics"]),
                        defender_tactics=int(target["tech"]["tactics"]),
                        defender_armor_bonus=min(
                            100,
                            int(target["buildings"]["wall"])
                            * int(combat_rules["formula"]["wall_armor_bonus_per_level"]),
                        ),
                        defender_modifiers=combat_modifiers,
                        retreat_threshold_percent=retreat_threshold,
                        rules_version=combat_version,
                        defender_structures=defender_structures,
                        defense_rules_digest=defense_digest,
                    )
                    if outcome.get("terra_defense"):
                        target["terra_defense_stacks"] = outcome["terra_defense"][
                            "remaining_stacks"
                        ]
                    outcome["victory"] = outcome["outcome"] == "attacker_win"
                    outcome["power"] = sum(
                        int(combat_rules["units"][unit]["attack"]) * count
                        for unit, count in army.items()
                    )
                    outcome["defense"] = sum(
                        (
                            int(combat_rules["units"][unit]["armor"])
                            + int(combat_rules["units"][unit]["shield"])
                            + int(combat_rules["units"][unit]["hull"])
                        )
                        * count
                        for unit, count in defenders_in.items()
                    )
                    outcome["defense"] += int(target["buildings"]["wall"]) * 100
                    if outcome.get("terra_defense"):
                        outcome["defense"] += terra_defense.defense_power(
                            outcome["terra_defense"]["initial_stacks"]
                        )
                    capacity = self.game.army_transport_capacity(
                        db,
                        world_id,
                        dict(outcome["attacker_survivors"]),
                        int(state["tech"]["logistics"]),
                    )
                    outcome["loot"] = [
                        (
                            min(
                                int(amount) // 3,
                                capacity // 3,
                            )
                            if outcome["victory"]
                            else 0
                        )
                        for amount in target["resources"]
                    ]
                    terra_combat.store_replay(db, str(job["id"]), outcome, int(job["due"]))
                    defense = int(outcome["defense"])
                elif combat_version == "FUR-2":
                    defense = self.fortified_player_defense(
                        db,
                        target,
                        self.world_faction(db, target["id"], int(target["world_id"])) or "pioneers",
                        int(job["due"]),
                    )
                    outcome = resolve_player_battle(
                        army,
                        defenders_in,
                        defense,
                        int(job["tactics"]),
                        int(state["tech"]["logistics"]),
                        list(target["resources"]),
                    )
                else:
                    raise RuntimeError("Unsupported pinned combat ruleset")
                attack, win = int(outcome["power"]), bool(outcome["victory"])
                army = dict(outcome["attacker_survivors"])
                if terra_combat.is_supported_version(combat_version):
                    target["units"], allied_garrison_losses = self.apply_allied_garrison_casualties(
                        db,
                        target,
                        combat_garrisons,
                        dict(outcome["defender_losses"]),
                        at=int(job["due"]),
                        rule_version=combat_version,
                    )
                else:
                    target["units"] = dict(outcome["defender_survivors"])
                    allied_garrison_losses = self.apply_allied_garrison_losses(
                        db,
                        target,
                        attack_power=int(outcome["power"]),
                        defense_power=int(outcome["defense"]),
                        victory=bool(outcome["victory"]),
                        at=int(job["due"]),
                    )
                if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
                    self.game.record_terra_unit_wrecks(
                        db,
                        mission_id=str(job["id"]),
                        owner_id=str(state["id"]),
                        colony_id=str(state["colony_id"]),
                        world_id=world_id,
                        losses=dict(outcome["attacker_losses"]),
                        combat_version=combat_version,
                        at=int(job["due"]),
                    )
                    host_losses = {
                        unit: max(
                            0,
                            int(defender_host_before.get(unit, 0))
                            - int(target["units"].get(unit, 0)),
                        )
                        for unit in defender_host_before
                    }
                    self.game.record_terra_unit_wrecks(
                        db,
                        mission_id=str(job["id"]),
                        owner_id=str(target["id"]),
                        colony_id=str(target["colony_id"]),
                        world_id=world_id,
                        losses=host_losses,
                        combat_version=combat_version,
                        at=int(job["due"]),
                    )
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        self.game.record_terra_unit_wrecks(
                            db,
                            mission_id=str(job["id"]),
                            owner_id=str(garrison["contributor_id"]),
                            colony_id=str(garrison["source_colony_id"]),
                            world_id=world_id,
                            losses=dict(garrison_loss["losses"]),
                            combat_version=combat_version,
                            at=int(job["due"]),
                        )
                if terra_combat.is_supported_version(combat_version):
                    self.game.record_war_score(
                        db,
                        mission_id=str(job["id"]),
                        world_id=world_id,
                        user_id=str(state["id"]),
                        category="attack",
                        points=sum(int(value) for value in outcome["attacker_losses"].values()),
                        rules_version=combat_version,
                        at=int(job["due"]),
                    )
                    host_losses = {
                        unit: max(
                            0,
                            int(defender_host_before.get(unit, 0))
                            - int(target["units"].get(unit, 0)),
                        )
                        for unit in defender_host_before
                    }
                    self.game.record_war_score(
                        db,
                        mission_id=str(job["id"]),
                        world_id=world_id,
                        user_id=str(target["id"]),
                        category="defense",
                        points=sum(host_losses.values()),
                        rules_version=combat_version,
                        at=int(job["due"]),
                    )
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        self.game.record_war_score(
                            db,
                            mission_id=str(job["id"]),
                            world_id=world_id,
                            user_id=str(garrison["contributor_id"]),
                            category="defense",
                            points=sum(int(value) for value in garrison_loss["losses"].values()),
                            rules_version=combat_version,
                            at=int(job["due"]),
                        )
                if terra_combat.is_supported_version(combat_version) and host_losses:
                    defender_losses_by_user = {str(target["id"]): host_losses}
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        defender_losses_by_user[str(garrison["contributor_id"])] = dict(
                            garrison_loss["losses"]
                        )
                    alliance_war.record_battle(
                        db,
                        mission_id=str(job["id"]),
                        world_id=world_id,
                        attacker_losses={str(state["id"]): dict(outcome["attacker_losses"])},
                        defender_losses=defender_losses_by_user,
                        rules_version=combat_version,
                        at=int(job["due"]),
                    )
                loot = list(outcome["loot"] or [0, 0, 0])
                target["resources"] = [n - l for n, l in zip(target["resources"], loot)]
                text = (
                    f"{state['name']} gegen {target['name']}: Angriff {attack}, "
                    f"Verteidigung {defense}. Beute {sum(loot)}. Kampfregel {combat_version}."
                )
                if terra_combat.is_supported_version(combat_version):
                    report_rounds = []
                    for battle_round in outcome["rounds"]:
                        attack_action = next(
                            (a for a in battle_round["actions"] if a["side"] == "attacker"),
                            {"damage": 0},
                        )
                        defense_action = next(
                            (a for a in battle_round["actions"] if a["side"] == "defender"),
                            {"damage": 0},
                        )
                        attacker_before = battle_round["attacker_before"]
                        defender_before = battle_round["defender_before"]
                        attacker_after = battle_round["attacker_after"]
                        defender_after = battle_round["defender_after"]
                        report_rounds.append(
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
                    combat = {
                        **outcome,
                        "participants": {
                            "attacker": state["name"],
                            "defender": target["name"],
                        },
                        "allied_garrison_losses": allied_garrison_losses,
                        "rounds": report_rounds,
                    }
                else:
                    combat = {
                        "rules_version": REGISTRY["version"],
                        "rules_digest": RULES_DIGEST,
                        "participants": {"attacker": state["name"], "defender": target["name"]},
                        "allied_garrison_losses": allied_garrison_losses,
                        "rounds": [
                            {
                                "round": 1,
                                "attack_power": attack,
                                "defense_power": defense,
                                "victory": win,
                                "attacker": {
                                    "sent": army_in,
                                    "losses": {
                                        k: army_in.get(k, 0) - army.get(k, 0) for k in army_in
                                    },
                                    "survivors": dict(army),
                                },
                                "defender": {
                                    "sent": defenders_in,
                                    "losses": {
                                        k: defenders_in.get(k, 0) - target["units"].get(k, 0)
                                        for k in defenders_in
                                    },
                                    "survivors": dict(target["units"]),
                                },
                                "loot": list(loot),
                            }
                        ],
                    }
                self.game.report(
                    state,
                    "Angriff gewonnen" if win else "Angriff verloren",
                    text,
                    combat,
                    report_side="attacker",
                    share_allowed=True,
                )
                self.game.report(
                    target,
                    "Verteidigung durchbrochen" if win else "Angriff abgewehrt",
                    text,
                    combat,
                    report_side="defender",
                    share_allowed=not combat_garrisons,
                )
                self.ledger(db, target, "pvp_defense", before)
                self.audit(
                    db,
                    state["id"],
                    "battle",
                    target["id"],
                    attack=attack,
                    defense=defense,
                    army_in=job["army"],
                    survivors=army,
                    loot=loot,
                    rule="FUR-2",
                )
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "return",
                "key": job["key"],
                "label": "Rückkehr von " + target["name"],
                "due": job["due"] + job["travel"],
                "army": army,
                "loot": loot,
            }
        )
        return True

    def resolve_terra_alliance_attack(
        self, db: Connection, leader_state: dict[str, Any], job: dict[str, Any]
    ) -> None:
        """Resolve all valid wings once and schedule their individual return journeys."""
        from . import terra_alliance, terra_combat, terra_defense
        from .game import REGISTRY, RULES_DIGEST, UNITS, RuleError, identity

        attack_id = str(job["alliance_attack_id"])
        attack = db.execute(
            "SELECT * FROM terra_alliance_attacks WHERE id=? AND status='assembling'",
            (attack_id,),
        ).fetchone()
        if not attack:
            return
        if str(attack["rule_version"]) not in terra_alliance.RULESETS:
            raise RuntimeError("Unsupported Terra alliance attack rule version")
        world_id, now = int(attack["world_id"]), int(job["due"])
        wings = db.execute(
            "SELECT * FROM terra_alliance_attack_wings WHERE attack_id=? AND status='active' "
            "ORDER BY user_id",
            (attack_id,),
        ).fetchall()
        valid: list[dict[str, Any]] = []
        leader_invalid = False
        for row in wings:
            wing_user = str(row["user_id"])
            colony_row = db.execute(
                "SELECT user_id,world_id,state FROM colonies WHERE colony_id=?",
                (row["colony_id"],),
            ).fetchone()
            member = self.member(db, wing_user)
            is_valid = bool(
                colony_row
                and colony_row["user_id"] == wing_user
                and int(colony_row["world_id"]) == world_id
                and member
                and str(member["alliance_id"]) == str(attack["alliance_id"])
            )
            if is_valid:
                colony = (
                    leader_state
                    if wing_user == attack["leader_id"]
                    else json.loads(colony_row["state"])
                )
                try:
                    if attack["target_kind"] == "player":
                        self.can_attack(db, wing_user, str(attack["target_id"]), now, world_id)
                except RuleError:
                    is_valid = False
                if colony.get("terra_dormant") or int(colony.get("vacation_until", 0)) > now:
                    is_valid = False
            if not is_valid and wing_user == attack["leader_id"]:
                leader_invalid = True
            if is_valid:
                valid.append({**dict(row), "state": colony})
            else:
                self.game.report(
                    (
                        leader_state
                        if wing_user == attack["leader_id"]
                        else json.loads(colony_row["state"])
                    ),
                    "Allianzangriff abgebrochen",
                    "Deine Allianz- oder Schutzbedingungen änderten sich. Deine Truppen kehren unversehrt zurück.",
                )
                colony = (
                    leader_state
                    if wing_user == attack["leader_id"]
                    else json.loads(colony_row["state"])
                )
                colony["jobs"].append(
                    {
                        "id": identity(),
                        "kind": "return",
                        "key": colony["colony_id"],
                        "label": "Rückkehr vom Allianzangriff",
                        "due": now + int(row["travel_seconds"]),
                        "army": json.loads(row["army"]),
                        "loot": [0, 0, 0],
                        "alliance_attack_id": attack_id,
                    }
                )
                self.game.save(db, colony)
                db.execute(
                    "UPDATE terra_alliance_attack_wings SET status='returning' "
                    "WHERE attack_id=? AND user_id=?",
                    (attack_id, wing_user),
                )

        if leader_invalid:
            valid = []
            remaining_wings = db.execute(
                "SELECT * FROM terra_alliance_attack_wings WHERE attack_id=? AND status='active'",
                (attack_id,),
            ).fetchall()
            for row in remaining_wings:
                wing_user = str(row["user_id"])
                colony = (
                    leader_state
                    if wing_user == str(attack["leader_id"])
                    else self.game.read_colony(db, str(row["colony_id"]))
                )
                colony["jobs"].append(
                    {
                        "id": identity(),
                        "kind": "return",
                        "key": colony["colony_id"],
                        "label": "Rückkehr vom abgebrochenen Allianzangriff",
                        "due": now + int(row["travel_seconds"]),
                        "army": json.loads(row["army"]),
                        "loot": [0, 0, 0],
                        "alliance_attack_id": attack_id,
                    }
                )
                self.game.save(db, colony)
                db.execute(
                    "UPDATE terra_alliance_attack_wings SET status='returning' "
                    "WHERE attack_id=? AND user_id=?",
                    (attack_id, wing_user),
                )

        outposts = self.game.world_outposts(db, world_id)
        target: dict[str, Any] | None = None
        defender_state: dict[str, Any] | None = None
        if len(valid) >= terra_alliance.MINIMUM_MEMBERS:
            if attack["target_kind"] == "outpost":
                target = next(
                    (item for item in outposts if item["id"] == attack["target_id"]),
                    None,
                )
                if target and target.get("owner") is not None:
                    target = None
            else:
                target_row = db.execute(
                    "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                    (attack["target_id"], world_id),
                ).fetchone()
                if target_row:
                    defender_state = self.game.read_colony(db, str(target_row["colony_id"]))
                    try:
                        for wing in valid:
                            self.can_attack(
                                db, str(wing["user_id"]), str(attack["target_id"]), now, world_id
                            )
                    except RuleError:
                        defender_state = None
                    if defender_state:
                        target = defender_state
        result: dict[str, Any] | None = None
        loot = [0, 0, 0]
        defenders: dict[str, int] = {}
        defender_host_before: dict[str, int] = {}
        allied_garrison_losses: list[dict[str, Any]] = []
        combat_version: str | None = None
        combat_garrisons: list[Any] = []
        if target and len(valid) >= terra_alliance.MINIMUM_MEMBERS:
            armies = [json.loads(wing["army"]) for wing in valid]
            if str(attack["rule_version"]) == "FUR-3-TERRA-ACS-3":
                replay_row = db.execute(
                    "SELECT rules_version,rules_digest,seed_commitment FROM terra_combat_missions "
                    "WHERE mission_id=? AND world_id=?",
                    (attack_id, world_id),
                ).fetchone()
                if not replay_row:
                    raise RuntimeError("Missing pinned FUR-3 ACS combat replay record")
                combat_version = str(replay_row["rules_version"])
                combat_rules = terra_combat.rules_for(combat_version)
                combat_roster = combat_rules["units"]
                seed, retreat_threshold = terra_combat.mission_seed(
                    db, attack_id, world_id, str(replay_row["seed_commitment"])
                )
                defenders = {
                    unit: int(target.get("units", {}).get(unit, 0)) for unit in combat_roster
                }
                defender_modifiers: dict[str, int] = {}
                defender_tactics = 0
                defender_armor_bonus = 0
                defender_structures: dict[str, list[int]] | None = None
                defense_digest: str | None = None
                if attack["target_kind"] == "outpost":
                    terrain = terrain_at(db, int(target["x"]), int(target["y"]), world_id)
                    defender_modifiers["terrain"] = int(DEFENSE_PERCENT[terrain])
                    if combat_rules.get("neutral_outpost_fortification"):
                        defenders["outpost_fortification"] = int(target["tier"]) ** 2
                else:
                    defender_state = target
                    self.game.produce(defender_state, now)
                    combat_garrisons = self.active_allied_garrisons(db, defender_state)
                    for garrison in combat_garrisons:
                        for unit, amount in json.loads(garrison["army"]).items():
                            defenders[unit] = defenders.get(unit, 0) + int(amount)
                    defender_tactics = int(defender_state["tech"]["tactics"])
                    defender_armor_bonus = min(
                        100,
                        int(defender_state["buildings"]["wall"])
                        * int(combat_rules["formula"]["wall_armor_bonus_per_level"]),
                    )
                    defender_faction = (
                        self.world_faction(db, str(attack["target_id"]), world_id) or "pioneers"
                    )
                    defender_modifiers = {
                        "terrain": int(DEFENSE_PERCENT[str(target.get("terrain", "plain"))]),
                        "faction": (
                            110
                            if defender_faction == "wardens"
                            and "kinetic_shield" in target.get("faction_research", [])
                            else 100
                        ),
                    }
                    if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
                        defender_structures = defender_state.get("terra_defense_stacks", {})
                        defense_digest = (
                            str(defender_state.get("terra_defense_rules_digest"))
                            if any(defender_structures.values())
                            else terra_defense.DIGEST
                        )
                result = terra_combat.resolve_wings(
                    seed,
                    [
                        {"army": army, "tactics": int(wing["tactics"])}
                        for wing, army in zip(valid, armies)
                    ],
                    defenders,
                    rules_version=combat_version,
                    defender_tactics=defender_tactics,
                    defender_armor_bonus=defender_armor_bonus,
                    defender_modifiers=defender_modifiers,
                    retreat_threshold_percent=retreat_threshold,
                    defender_structures=defender_structures,
                    defense_rules_digest=defense_digest,
                )
                if result.get("terra_defense") and attack["target_kind"] == "player":
                    target["terra_defense_stacks"] = result["terra_defense"]["remaining_stacks"]
                result["victory"] = result["outcome"] == "attacker_win"
                result["power"] = sum(
                    int(combat_rules["units"][unit]["attack"]) * amount
                    for army in armies
                    for unit, amount in army.items()
                )
                result["defense"] = (
                    sum(
                        (
                            int(combat_rules["units"][unit]["armor"])
                            + int(combat_rules["units"][unit]["shield"])
                            + int(combat_rules["units"][unit]["hull"])
                        )
                        * amount
                        for unit, amount in defenders.items()
                        if unit in combat_roster
                    )
                    + defender_armor_bonus
                )
                if result.get("terra_defense"):
                    result["defense"] += terra_defense.defense_power(
                        result["terra_defense"]["initial_stacks"]
                    )
                if (
                    "outpost_fortification" in defenders
                    and "outpost_fortification" not in combat_roster
                ):
                    result["defense"] += int(
                        combat_rules["neutral_outpost_fortification"]["structure_per_tier_squared"]
                    ) * int(defenders["outpost_fortification"])
                survivors = result["wing_survivors"]
                if attack["target_kind"] == "player":
                    defender_before = list(target["resources"])
                    defender_host_before = dict(target["units"])
                    capacity = sum(
                        self.game.army_transport_capacity(
                            db,
                            world_id,
                            survivors[index],
                            int(valid[index]["logistics"]),
                        )
                        for index in range(len(valid))
                    )
                    if result["victory"]:
                        loot = [
                            min(int(amount) // 3, capacity // 3) for amount in target["resources"]
                        ]
                        target["resources"] = [
                            amount - stolen for amount, stolen in zip(target["resources"], loot)
                        ]
                if attack["target_kind"] == "player":
                    target["units"], allied_garrison_losses = self.apply_allied_garrison_casualties(
                        db,
                        target,
                        combat_garrisons,
                        dict(result["defender_losses"]),
                        at=now,
                        rule_version=combat_version,
                    )
                    self.ledger(db, target, "alliance_attack_defense", defender_before)
                    self.game.save(db, target)
                else:
                    target["units"] = dict(result["defender_survivors"])
                    target["units"].pop("outpost_fortification", None)
            elif attack["target_kind"] == "outpost":
                defenders = {unit: int(target.get("units", {}).get(unit, 0)) for unit in UNITS}
                result = terra_alliance.resolve(
                    [
                        {"army": army, "tactics": int(wing["tactics"])}
                        for wing, army in zip(valid, armies)
                    ],
                    defenders,
                    neutral_tier=int(target["tier"]),
                    terrain=terrain_at(db, int(target["x"]), int(target["y"]), world_id),
                )
            else:
                defender_state = target
                self.game.produce(defender_state, now)
                defense = self.fortified_player_defense(
                    db,
                    defender_state,
                    self.world_faction(db, str(attack["target_id"]), world_id) or "pioneers",
                    now,
                )
                defenders = {unit: int(defender_state["units"].get(unit, 0)) for unit in UNITS}
                result = terra_alliance.resolve(
                    [
                        {"army": army, "tactics": int(wing["tactics"])}
                        for wing, army in zip(valid, armies)
                    ],
                    defenders,
                    player_defense=defense,
                )
                capacity = sum(
                    sum(army.values()) * (40 + 10 * int(wing["logistics"]))
                    for wing, army in zip(valid, result["wing_survivors"])
                )
            if combat_version is None:
                survivors = result["wing_survivors"]
                target["units"] = result["defender_survivors"]
            if attack["target_kind"] == "player" and combat_version is None:
                assert defender_state is not None
                defender_before = list(defender_state["resources"])
                if result["victory"]:
                    loot = [
                        min(int(amount) // 3, capacity // 3)
                        for amount in defender_state["resources"]
                    ]
                    defender_state["resources"] = [
                        amount - stolen for amount, stolen in zip(defender_state["resources"], loot)
                    ]
                allied_garrison_losses = self.apply_allied_garrison_losses(
                    db,
                    defender_state,
                    attack_power=int(result["power"]),
                    defense_power=int(result["defense"]),
                    victory=bool(result["victory"]),
                    at=now,
                )
                self.ledger(db, defender_state, "alliance_attack_defense", defender_before)
                self.game.save(db, defender_state)
            if attack["target_kind"] == "outpost":
                if result["victory"]:
                    capacity = sum(
                        self.game.army_transport_capacity(
                            db,
                            world_id,
                            survivors[index],
                            int(valid[index]["logistics"]),
                        )
                        for index in range(len(valid))
                    )
                    loot = [min(int(stock), capacity // 3) for stock in target["stock"]]
                    target["stock"] = [
                        amount - stolen for amount, stolen in zip(target["stock"], loot)
                    ]
                    if attack["capture"]:
                        leader_owner = str(attack["leader_id"])
                        if target.get("owner") and target["owner"] != leader_owner:
                            previous = self.game.read_colony(db, str(target["owner"]))
                            previous["captures"] = max(0, int(previous.get("captures", 0)) - 1)
                            if int(target["tier"]) == 8:
                                previous["citadel"] = False
                            self.game.save(db, previous)
                        target.update(owner=leader_owner, cleared=True)
                        leader_state["captures"] = int(leader_state.get("captures", 0)) + 1
                        if int(target["tier"]) == 8:
                            leader_state["citadel"] = True
                self.game.save_world_outposts(db, world_id, outposts)
            if combat_version in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5"):
                for index, wing in enumerate(valid):
                    wing_losses = {
                        unit: max(
                            0,
                            int(armies[index].get(unit, 0)) - int(survivors[index].get(unit, 0)),
                        )
                        for unit in armies[index]
                    }
                    self.game.record_terra_unit_wrecks(
                        db,
                        mission_id=attack_id,
                        owner_id=str(wing["user_id"]),
                        colony_id=str(wing["colony_id"]),
                        world_id=world_id,
                        losses=wing_losses,
                        combat_version=combat_version,
                        at=now,
                    )
                if attack["target_kind"] == "player":
                    host_losses = {
                        unit: max(
                            0,
                            int(defender_host_before.get(unit, 0))
                            - int(target["units"].get(unit, 0)),
                        )
                        for unit in defender_host_before
                    }
                    self.game.record_terra_unit_wrecks(
                        db,
                        mission_id=attack_id,
                        owner_id=str(attack["target_id"]),
                        colony_id=str(target["colony_id"]),
                        world_id=world_id,
                        losses=host_losses,
                        combat_version=combat_version,
                        at=now,
                    )
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        self.game.record_terra_unit_wrecks(
                            db,
                            mission_id=attack_id,
                            owner_id=str(garrison["contributor_id"]),
                            colony_id=str(garrison["source_colony_id"]),
                            world_id=world_id,
                            losses=dict(garrison_loss["losses"]),
                            combat_version=combat_version,
                            at=now,
                        )
            if combat_version is not None:
                for index, wing in enumerate(valid):
                    wing_losses = {
                        unit: max(
                            0,
                            int(armies[index].get(unit, 0)) - int(survivors[index].get(unit, 0)),
                        )
                        for unit in armies[index]
                    }
                    self.game.record_war_score(
                        db,
                        mission_id=attack_id,
                        world_id=world_id,
                        user_id=str(wing["user_id"]),
                        category="attack",
                        points=sum(wing_losses.values()),
                        rules_version=combat_version,
                        at=now,
                    )
                if attack["target_kind"] == "player":
                    host_losses = {
                        unit: max(
                            0,
                            int(defender_host_before.get(unit, 0))
                            - int(target["units"].get(unit, 0)),
                        )
                        for unit in defender_host_before
                    }
                    self.game.record_war_score(
                        db,
                        mission_id=attack_id,
                        world_id=world_id,
                        user_id=str(attack["target_id"]),
                        category="defense",
                        points=sum(host_losses.values()),
                        rules_version=combat_version,
                        at=now,
                    )
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        self.game.record_war_score(
                            db,
                            mission_id=attack_id,
                            world_id=world_id,
                            user_id=str(garrison["contributor_id"]),
                            category="defense",
                            points=sum(int(value) for value in garrison_loss["losses"].values()),
                            rules_version=combat_version,
                            at=now,
                        )
                    attacker_loss_map = {
                        str(wing["user_id"]): {
                            unit: max(
                                0,
                                int(armies[index].get(unit, 0))
                                - int(survivors[index].get(unit, 0)),
                            )
                            for unit in armies[index]
                        }
                        for index, wing in enumerate(valid)
                    }
                    defender_loss_map = {str(attack["target_id"]): host_losses}
                    for garrison_loss in allied_garrison_losses:
                        garrison = next(
                            row
                            for row in combat_garrisons
                            if str(row["id"]) == str(garrison_loss["garrison_id"])
                        )
                        defender_loss_map[str(garrison["contributor_id"])] = dict(
                            garrison_loss["losses"]
                        )
                    alliance_war.record_battle(
                        db,
                        mission_id=attack_id,
                        world_id=world_id,
                        attacker_losses=attacker_loss_map,
                        defender_losses=defender_loss_map,
                        rules_version=combat_version,
                        at=now,
                    )
            tie_breakers = [str(wing["user_id"]) for wing in valid]
            capacities = [
                self.game.army_transport_capacity(
                    db, world_id, survivors[index], int(wing["logistics"])
                )
                for index, wing in enumerate(valid)
            ]
            shares = [
                terra_alliance.allocate_amount(amount, capacities, tie_breakers) for amount in loot
            ]
        else:
            survivors = [json.loads(wing["army"]) for wing in valid]
            shares = [[0] * len(valid) for _ in range(3)]

        if result is not None and combat_version is not None:
            result["loot"] = list(loot)
            terra_combat.store_replay(db, attack_id, result, now)
        elif str(attack["rule_version"]) == "FUR-3-TERRA-ACS-3":
            terra_combat.discard_mission(db, attack_id)

        combat_report: dict[str, Any] | None = None
        if result is not None:
            assert target is not None
            attacker_names = ", ".join(str(wing["state"]["name"]) for wing in valid)
            alliance_version = str(attack["rule_version"])
            combat_report = {
                "rules_version": combat_version or REGISTRY["version"],
                "rules_digest": (result["rules_digest"] if combat_version else RULES_DIGEST),
                "seed_commitment": result.get("seed_commitment"),
                "seed": result.get("seed"),
                "victory": result["victory"],
                "outcome": result.get("outcome"),
                "alliance_rules_version": alliance_version,
                "alliance_rules_digest": terra_alliance.DIGESTS[alliance_version],
                "participants": {
                    "attacker": attacker_names,
                    "defender": str(target.get("name", attack["target_id"])),
                },
                "allied_garrison_losses": allied_garrison_losses,
                "rounds": (
                    [
                        {
                            "round": battle_round["round"],
                            "attack_power": next(
                                (
                                    action["damage"]
                                    for action in battle_round["actions"]
                                    if action["side"] == "attacker"
                                ),
                                0,
                            ),
                            "defense_power": next(
                                (
                                    action["damage"]
                                    for action in battle_round["actions"]
                                    if action["side"] == "defender"
                                ),
                                0,
                            ),
                            "attacker_wings": [
                                {
                                    "commander": str(wing["state"]["name"]),
                                    "sent": json.loads(wing["army"]),
                                    "losses": {
                                        unit: max(
                                            0,
                                            int(json.loads(wing["army"]).get(unit, 0))
                                            - int(
                                                battle_round["attacker_wings_after"][index].get(
                                                    unit, 0
                                                )
                                            ),
                                        )
                                        for unit in combat_roster
                                    },
                                    "survivors": dict(battle_round["attacker_wings_after"][index]),
                                }
                                for index, wing in enumerate(valid)
                            ],
                            "defender": {
                                "sent": dict(result["defender_initial"]),
                                "losses": {
                                    unit: int(
                                        result["defender_initial"].get(unit, 0)
                                        - battle_round["defender_after"].get(unit, 0)
                                    )
                                    for unit in result["defender_initial"]
                                },
                                "survivors": dict(battle_round["defender_after"]),
                            },
                            "loot": list(loot),
                        }
                        for battle_round in result["rounds"]
                    ]
                    if combat_version
                    else [
                        {
                            "round": 1,
                            "attack_power": result["power"],
                            "defense_power": result["defense"],
                            "victory": result["victory"],
                            "attacker_wings": [
                                {
                                    "commander": str(wing["state"]["name"]),
                                    "sent": json.loads(wing["army"]),
                                    "losses": {
                                        unit: int(
                                            json.loads(wing["army"]).get(unit, 0)
                                            - survivors[index].get(unit, 0)
                                        )
                                        for unit in UNITS
                                    },
                                    "survivors": dict(survivors[index]),
                                }
                                for index, wing in enumerate(valid)
                            ],
                            "defender": {
                                "sent": defenders,
                                "losses": {
                                    unit: int(
                                        defenders.get(unit, 0)
                                        - result["defender_survivors"].get(unit, 0)
                                    )
                                    for unit in UNITS
                                },
                                "survivors": dict(result["defender_survivors"]),
                            },
                            "loot": list(loot),
                        }
                    ]
                ),
            }
            if result.get("terra_defense") is not None:
                combat_report["terra_defense"] = result["terra_defense"]
            if defender_state:
                self.game.report(
                    defender_state,
                    "Verteidigung durchbrochen" if result["victory"] else "Angriff abgewehrt",
                    f"Allianzverband {attacker_names}: Kampfkraft {result['power']} gegen "
                    f"{result['defense']}. Verluste: "
                    f"{sum(defenders.values()) - sum(result['defender_survivors'].values())}. "
                    f"Beute der Angreifer: {sum(loot)}.",
                    combat_report,
                    report_side="defender",
                    share_allowed=not combat_garrisons,
                )
                self.game.save(db, defender_state)

        valid_ids = {str(wing["user_id"]) for wing in valid}
        for row in wings:
            wing_user = str(row["user_id"])
            if wing_user not in valid_ids:
                continue
            index = next(i for i, wing in enumerate(valid) if str(wing["user_id"]) == wing_user)
            colony = (
                leader_state
                if wing_user == attack["leader_id"]
                else self.game.read_colony(db, str(row["colony_id"]))
            )
            colony["jobs"].append(
                {
                    "id": identity(),
                    "kind": "return",
                    "key": colony["colony_id"],
                    "label": "Rückkehr vom Allianzangriff",
                    "due": now + int(row["travel_seconds"]),
                    "army": survivors[index],
                    "loot": [shares[resource][index] for resource in range(3)],
                    "alliance_attack_id": attack_id,
                }
            )
            title = (
                "Allianzangriff gewonnen"
                if result and result["victory"]
                else "Allianzangriff verloren oder abgebrochen"
            )
            self.game.report(
                colony,
                title,
                "Gemeinsame Kampfkraft "
                + (
                    f"{result['power']} gegen {result['defense']}. "
                    if result
                    else "Die Ziel- oder Schutzbedingungen ließen keinen Kampf zu. "
                )
                + f"Deine Beute: {shares[0][index]} Holz, {shares[1][index]} Stein, {shares[2][index]} Erz. Überlebende kehren zu ihrer Ausgangskolonie zurück.",
                combat_report,
                report_side="attacker_wing",
                report_wing=index,
                share_allowed=True,
            )
            self.game.save(db, colony)
            self.audit(
                db,
                wing_user,
                "alliance_attack_resolved",
                attack_id,
                survivors=survivors[index],
                loot=[shares[r][index] for r in range(3)],
            )
            db.execute(
                "UPDATE terra_alliance_attack_wings SET status='returning' WHERE attack_id=? AND user_id=?",
                (attack_id, wing_user),
            )
        db.execute(
            "UPDATE terra_alliance_attacks SET status='resolved',resolved_at=? WHERE id=? AND status='assembling'",
            (now, attack_id),
        )

    def garrison(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        world_id = int(state.get("world_id", 1))
        unit_catalog = self.game.unit_catalog_for_world(db, world_id)
        towns = self.game.world_outposts(db, world_id)
        target = next((t for t in towns if t["id"] == self.text(p, "key")), None)
        if not target or target["owner"] != state["id"]:
            self.error("Garnisonsbefehle erfordern einen eigenen Außenposten.")
        if len(state["jobs"]) >= self.game.terra_mission_limit(state):
            self.error(f"Maximal {self.game.terra_mission_limit(state)} Operationen.")
        available = (
            state["units"]
            if action == "station"
            else target.setdefault("units", {k: 0 for k in unit_catalog})
        )
        limits = available
        if action == "recall":
            en_route = {
                unit: sum(
                    job["army"].get(unit, 0)
                    for job in state["jobs"]
                    if job["kind"] == "return" and job["key"] == target["id"]
                )
                for unit in unit_catalog
            }
            limits = {unit: max(0, count - en_route[unit]) for unit, count in available.items()}
        army = p.get("army", {})
        if (
            not isinstance(army, dict)
            or any(
                k not in unit_catalog or type(n) is not int or n < 0 or n > limits.get(k, 0)
                for k, n in army.items()
            )
            or sum(army.values()) < 1
        ):
            self.error("Ungültige Garnisonsauswahl.")
        for unit, count in army.items():
            available[unit] = available.get(unit, 0) - count
        if action == "station":
            movement = self.reserve_movement_fuel(
                db, state, (state["x"], state["y"]), (target["x"], target["y"]), army
            )
        else:
            movement = self.game.movement_quote(
                db,
                (state["x"], state["y"]),
                (target["x"], target["y"]),
                world_id,
                army,
            )
        travel = int(movement["travel_seconds"])
        state["jobs"].append(
            {
                "id": identity(),
                "kind": "station" if action == "station" else "return",
                "key": target["id"],
                "label": ("Garnison zu " if action == "station" else "Rückruf von ")
                + target["name"],
                "due": int(time.time()) + travel,
                "travel": travel,
                "movement": movement,
                "army": army,
                "loot": [0, 0, 0],
                "goods_cargo": {},
            }
        )
        self.game.save_world_outposts(db, world_id, towns)
        self.audit(db, state["id"], action, target["id"], army=army)

    def command(
        self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]
    ) -> None:
        from .game import identity

        user, now = state["id"], int(time.time())
        role = str(self.profile(db, str(user))["role"])
        if action == "hero_allocate":
            heroes.allocate(db, str(state["id"]), int(state["world_id"]), p.get("hero_stat"), now)
            self.audit(
                db,
                str(state["id"]),
                action,
                str(p.get("hero_stat", "")),
                world_id=int(state["world_id"]),
            )
        elif action == "hero_respec":
            hero_respec.reset(db, state, now)
            self.audit(
                db,
                str(state["id"]),
                action,
                str(state["world_id"]),
                world_id=int(state["world_id"]),
                rules_version=hero_respec.RULES.version,
                cost=hero_respec.RULES.cost,
            )
        elif action == "world_create":
            from . import terra_combat

            profile = self.profile(db, user)
            if profile["role"] != "admin":
                self.error("Nur die Spielleitung kann eine Welt anlegen.")
            name = self.text(p, "name", 3, 48)
            seed = self.integer(p, "seed", 0, 2**63 - 1)
            outposts = self.integer(p, "outposts", 8, 300)
            joinable = p.get("joinable", True)
            if type(joinable) is not bool:
                self.error("Ungültige Beitrittseinstellung.")
            combat_ruleset = p.get("terra_combat_ruleset", "FUR-2")
            if not isinstance(combat_ruleset, str) or combat_ruleset not in (
                "FUR-2",
                *terra_combat.RULESETS,
            ):
                self.error("Ungültiger Kampfregelstand.")
            retreat_threshold = (
                self.integer(p, "terra_retreat_threshold_percent", 1, 100)
                if "terra_retreat_threshold_percent" in p
                else 60
            )
            crafting_ruleset = p.get("crafting_ruleset", "FUR-2")
            if crafting_ruleset not in ("FUR-2", crafting.RULES.version):
                self.error("Ungültiger Fertigungsregelstand.")
            hero_ruleset = p.get("hero_ruleset", "FUR-2")
            if hero_ruleset not in ("FUR-2", heroes.RULES.version):
                self.error("Ungültiger Commander-Regelstand.")
            doctrine_ruleset = p.get("hero_doctrine_ruleset", "FUR-2")
            if doctrine_ruleset not in ("FUR-2", hero_doctrines.RULES.version):
                self.error("Ungültiger Commander-Doktrinstand.")
            if (
                doctrine_ruleset == hero_doctrines.RULES.version
                and hero_ruleset != heroes.RULES.version
            ):
                self.error("Commander-Doktrinen benötigen die aktivierte Heldenverwaltung.")
            respec_ruleset = p.get("hero_respec_ruleset", "FUR-2")
            if respec_ruleset not in ("FUR-2", hero_respec.RULES.version):
                self.error("Ungültiger Commander-Resetstand.")
            if respec_ruleset == hero_respec.RULES.version and hero_ruleset != heroes.RULES.version:
                self.error("Commander-Resets benötigen die aktivierte Heldenverwaltung.")
            camp_ruleset = p.get(npc_camps.RULESET_KEY, "FUR-2")
            if camp_ruleset not in ("FUR-2", *npc_camps.RULESET_VERSIONS):
                self.error("Ungültiger NPC-Lager-Regelstand.")
            ruin_ruleset = p.get("terra_ruin_exploration_ruleset", "FUR-2")
            if ruin_ruleset not in ("FUR-2", ruin_exploration.VERSION):
                self.error("Ungültiger Ruinenerkundungs-Regelstand.")
            mode = p.get("mode", "permanent")
            if mode not in ("permanent", "season", "sandbox"):
                self.error("Ungültiger Weltmodus.")
            world_id = self.game.create_world(db, name, seed, outposts, joinable, str(mode))
            db.execute(
                "UPDATE world_settings SET terra_combat_ruleset=?,"
                "terra_retreat_threshold_percent=?,settings=? WHERE world_id=?",
                (
                    combat_ruleset,
                    retreat_threshold,
                    json.dumps(
                        {
                            "crafting_ruleset": crafting_ruleset,
                            heroes.RULES.enabled_key: hero_ruleset,
                            hero_doctrines.RULES.enabled_key: doctrine_ruleset,
                            hero_respec.RULES.enabled_key: respec_ruleset,
                            npc_camps.RULESET_KEY: camp_ruleset,
                            "terra_ruin_exploration_ruleset": ruin_ruleset,
                        },
                        separators=(",", ":"),
                    ),
                    world_id,
                ),
            )
            if camp_ruleset in npc_camps.RULESET_VERSIONS:
                npc_camps.initialize_world(db, world_id, seed, now, str(camp_ruleset))
            self.audit(
                db,
                user,
                action,
                str(world_id),
                name=name,
                seed=seed,
                outposts=outposts,
                mode=mode,
                terra_combat_ruleset=combat_ruleset,
                crafting_ruleset=crafting_ruleset,
                hero_ruleset=hero_ruleset,
                hero_doctrine_ruleset=doctrine_ruleset,
                hero_respec_ruleset=respec_ruleset,
                npc_camps_ruleset=camp_ruleset,
                terra_ruin_exploration_ruleset=ruin_ruleset,
            )
        elif action == "world_update":
            from . import terra_combat

            profile = self.profile(db, user)
            if profile["role"] != "admin":
                self.error("Nur die Spielleitung kann Welteinstellungen ändern.")
            world_id = self.integer(p, "world_id", 1, 2**31 - 1)
            current = db.execute(
                "SELECT name,joinable,mode,settings,terra_combat_ruleset,"
                "terra_retreat_threshold_percent "
                "FROM world_settings WHERE world_id=?",
                (world_id,),
            ).fetchone()
            if not current:
                self.error("Diese Spielwelt existiert nicht.")
            try:
                world_config = json.loads(current["settings"] or "{}")
            except (TypeError, ValueError):
                self.error("Die gespeicherten Welteinstellungen sind ungültig.")
            if not isinstance(world_config, dict):
                self.error("Die gespeicherten Welteinstellungen sind ungültig.")
            name = self.text(p, "name", 3, 48) if "name" in p else str(current["name"])
            joinable = p.get("joinable", bool(current["joinable"]))
            if type(joinable) is not bool:
                self.error("Ungültige Beitrittseinstellung.")
            combat_ruleset = p.get("terra_combat_ruleset", str(current["terra_combat_ruleset"]))
            if combat_ruleset not in ("FUR-2", *terra_combat.RULESETS):
                self.error("Ungültiger Kampfregelstand.")
            current_ruleset = str(current["terra_combat_ruleset"])
            if combat_ruleset != current_ruleset:
                has_colonies = db.execute(
                    "SELECT 1 FROM colonies WHERE world_id=? LIMIT 1", (world_id,)
                ).fetchone()
                if has_colonies and (
                    current_ruleset in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
                    or combat_ruleset in ("FUR-3-TERRA-COMBAT-4", "FUR-3-TERRA-COMBAT-5")
                ):
                    self.error(
                        "COMBAT-4 kann nur vor dem ersten Weltbeitritt aktiviert oder gewechselt werden."
                    )
            retreat_threshold = (
                self.integer(p, "terra_retreat_threshold_percent", 1, 100)
                if "terra_retreat_threshold_percent" in p
                else int(current["terra_retreat_threshold_percent"])
            )
            crafting_ruleset = p.get(
                "crafting_ruleset", world_config.get("crafting_ruleset", "FUR-2")
            )
            if not isinstance(crafting_ruleset, str) or crafting_ruleset not in (
                "FUR-2",
                crafting.RULES.version,
            ):
                self.error("Ungültiger Fertigungsregelstand.")
            previous_crafting = world_config.get("crafting_ruleset", "FUR-2")
            if not isinstance(previous_crafting, str) or previous_crafting not in (
                "FUR-2",
                crafting.RULES.version,
            ):
                self.error("Der gespeicherte Fertigungsregelstand ist ungültig.")
            if previous_crafting == crafting.RULES.version and crafting_ruleset == "FUR-2":
                for colony_row in db.execute(
                    "SELECT state FROM colonies WHERE world_id=?", (world_id,)
                ):
                    colony_state = json.loads(colony_row["state"])
                    if any(job.get("kind") == "craft" for job in colony_state.get("jobs", [])):
                        self.error(
                            "Schließe alle laufenden Fertigungsaufträge vor dem Deaktivieren ab."
                        )
            hero_ruleset = p.get(
                "hero_ruleset", world_config.get(heroes.RULES.enabled_key, "FUR-2")
            )
            if hero_ruleset not in ("FUR-2", heroes.RULES.version):
                self.error("Ungültiger Commander-Regelstand.")
            doctrine_ruleset = p.get(
                "hero_doctrine_ruleset",
                world_config.get(hero_doctrines.RULES.enabled_key, "FUR-2"),
            )
            if doctrine_ruleset not in ("FUR-2", hero_doctrines.RULES.version):
                self.error("Ungültiger Commander-Doktrinstand.")
            if (
                doctrine_ruleset == hero_doctrines.RULES.version
                and hero_ruleset != heroes.RULES.version
            ):
                self.error("Commander-Doktrinen benötigen die aktivierte Heldenverwaltung.")
            respec_ruleset = p.get(
                "hero_respec_ruleset",
                world_config.get(hero_respec.RULES.enabled_key, "FUR-2"),
            )
            if respec_ruleset not in ("FUR-2", hero_respec.RULES.version):
                self.error("Ungültiger Commander-Resetstand.")
            if respec_ruleset == hero_respec.RULES.version and hero_ruleset != heroes.RULES.version:
                self.error("Commander-Resets benötigen die aktivierte Heldenverwaltung.")
            if (
                crafting_ruleset == crafting.RULES.version
                and previous_crafting != crafting.RULES.version
            ):
                for colony_row in db.execute(
                    "SELECT state FROM colonies WHERE world_id=?", (world_id,)
                ):
                    colony_state = json.loads(colony_row["state"])
                    if any(job.get("kind") == "craft" for job in colony_state.get("jobs", [])):
                        self.error(
                            "Vor der Aktivierung müssen alle alten Fertigungsaufträge abgeschlossen sein."
                        )
            if (
                joinable
                and current["mode"] == "season"
                and db.execute(
                    "SELECT 1 FROM seasons WHERE world_id=? AND ends<=?",
                    (world_id, int(time.time())),
                ).fetchone()
            ):
                self.error("Eine beendete Saisonwelt bleibt für neue Spieler geschlossen.")
            if (
                "name" in p
                and db.execute(
                    "SELECT 1 FROM world_settings WHERE lower(name)=lower(?) AND world_id<>?",
                    (name, world_id),
                ).fetchone()
            ):
                self.error("Dieser Weltname ist bereits vergeben.")
            requested_rules = {
                "terra_combat_ruleset": combat_ruleset,
                "crafting_ruleset": crafting_ruleset,
                "hero_ruleset": hero_ruleset,
                "hero_doctrine_ruleset": doctrine_ruleset,
                "hero_respec_ruleset": respec_ruleset,
            }
            active_rules = {
                "terra_combat_ruleset": current_ruleset,
                "crafting_ruleset": str(previous_crafting),
                "hero_ruleset": str(world_config.get(heroes.RULES.enabled_key, "FUR-2")),
                "hero_doctrine_ruleset": str(
                    world_config.get(hero_doctrines.RULES.enabled_key, "FUR-2")
                ),
                "hero_respec_ruleset": str(
                    world_config.get(hero_respec.RULES.enabled_key, "FUR-2")
                ),
                "npc_camps_ruleset": str(world_config.get(npc_camps.RULESET_KEY, "FUR-2")),
            }
            requested_rules["npc_camps_ruleset"] = active_rules["npc_camps_ruleset"]
            pending_rules = {
                str(row["rule_key"])
                for row in db.execute(
                    "SELECT rule_key FROM world_rule_rollouts "
                    "WHERE world_id=? AND status='pending'",
                    (world_id,),
                )
            }
            if any(
                key in pending_rules and requested_rules[key] != active_rules[key]
                for key in requested_rules
            ):
                self.error("Für diese Regelart ist bereits eine Aktivierung geplant.")
            if not {
                "name",
                "joinable",
                "terra_combat_ruleset",
                "terra_retreat_threshold_percent",
                "crafting_ruleset",
                "hero_ruleset",
                "hero_doctrine_ruleset",
                "hero_respec_ruleset",
                "npc_camps_ruleset",
            }.intersection(p):
                self.error("Keine Welteinstellung wurde geändert.")
            world_config["crafting_ruleset"] = crafting_ruleset
            world_config[heroes.RULES.enabled_key] = hero_ruleset
            world_config[hero_doctrines.RULES.enabled_key] = doctrine_ruleset
            world_config[hero_respec.RULES.enabled_key] = respec_ruleset
            world_config[npc_camps.RULESET_KEY] = active_rules["npc_camps_ruleset"]
            db.execute(
                "UPDATE world_settings SET name=?,joinable=?,settings=?,terra_combat_ruleset=?,"
                "terra_retreat_threshold_percent=? "
                "WHERE world_id=?",
                (
                    name,
                    joinable,
                    json.dumps(world_config, separators=(",", ":")),
                    combat_ruleset,
                    retreat_threshold,
                    world_id,
                ),
            )
            self.audit(
                db,
                user,
                action,
                str(world_id),
                name=name,
                joinable=joinable,
                terra_combat_ruleset=combat_ruleset,
                terra_retreat_threshold_percent=retreat_threshold,
                crafting_ruleset=crafting_ruleset,
                hero_ruleset=hero_ruleset,
                hero_doctrine_ruleset=doctrine_ruleset,
                hero_respec_ruleset=respec_ruleset,
                npc_camps_ruleset=active_rules["npc_camps_ruleset"],
            )
        elif action == "world_join":
            world_id = self.integer(p, "world_id", 1, 2**31 - 1)
            player_name = db.execute("SELECT name FROM users WHERE id=?", (user,)).fetchone()[0]
            self.game.join_world(db, user, player_name, world_id)
            self.audit(db, user, action, str(world_id))
        elif action == "admin_rule_rollout_schedule":
            from .game import identity

            if role != "admin":
                self.error("Regelupdates kann nur die Spielleitung planen.")
            world_id = self.integer(p, "world_id", 1, 2**31 - 1)
            rule_key = self.text(p, "rule_key", 1, 40)
            target_version = self.text(p, "target_version", 1, 80)
            if rule_key not in rule_rollouts.RULES:
                self.error("Unbekannte Regelart.")
            if target_version not in rule_rollouts.RULES[rule_key]:
                self.error("Dieser Regelstand ist für die ausgewählte Regelart ungültig.")
            active_at = self.integer(p, "active_at", now + 60, now + 90 * 86400)
            if not db.execute(
                "SELECT 1 FROM world_settings WHERE world_id=?", (world_id,)
            ).fetchone():
                self.error("Diese Spielwelt existiert nicht.")
            validation = rule_rollouts.validate_target(db, world_id, rule_key, target_version)
            if validation:
                self.error("Dieser Regelstand kann für die Welt nicht geplant werden.")
            if db.execute(
                "SELECT 1 FROM world_rule_rollouts WHERE world_id=? AND rule_key=? "
                "AND status='pending'",
                (world_id, rule_key),
            ).fetchone():
                self.error("Für diese Regelart ist bereits eine Aktivierung geplant.")
            rollout_id = identity()
            db.execute(
                "INSERT INTO world_rule_rollouts(id,world_id,rule_key,target_version,active_at,"
                "created_by,created) VALUES (?,?,?,?,?,?,?)",
                (rollout_id, world_id, rule_key, target_version, active_at, user, now),
            )
            self.audit(
                db,
                user,
                action,
                rollout_id,
                world_id=world_id,
                rule_key=rule_key,
                target_version=target_version,
                active_at=active_at,
            )
        elif action == "admin_rule_rollout_cancel":
            if role != "admin":
                self.error("Regelupdates kann nur die Spielleitung abbrechen.")
            rollout_id = self.text(p, "key", 1, 100)
            rollout = db.execute(
                "SELECT world_id,rule_key,target_version FROM world_rule_rollouts "
                "WHERE id=? AND status='pending'",
                (rollout_id,),
            ).fetchone()
            if rollout is None:
                self.error("Ausstehendes Regelupdate nicht gefunden.")
            rule_rollouts.cancel(db, rollout_id, now)
            self.audit(
                db,
                user,
                action,
                rollout_id,
                world_id=int(rollout["world_id"]),
                rule_key=str(rollout["rule_key"]),
                target_version=str(rollout["target_version"]),
            )
        elif action == "world_select":
            world_id = self.integer(p, "world_id", 1, 2**31 - 1)
            home = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                (user, world_id),
            ).fetchone()
            if not home:
                self.error("Du besitzt keine Heimatkolonie in dieser Welt.")
            db.execute(
                "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
                (home["colony_id"], world_id, user),
            )
            self.audit(db, user, action, str(world_id))
        elif action == "colony_select":
            colony_id = self.text(p, "key", 1, 100)
            colony = db.execute(
                "SELECT world_id FROM colonies WHERE colony_id=? AND user_id=?",
                (colony_id, user),
            ).fetchone()
            if not colony:
                self.error("Diese Kolonie gehört nicht zu deinem Imperium.")
            db.execute(
                "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
                (colony_id, colony["world_id"], user),
            )
            self.audit(db, user, action, colony_id)
        elif action == "colony_rename":
            colony_id = self.text(p, "colony_id", 1, 100)
            name = self.text(p, "name", 3, 32)
            if not all(character.isalnum() or character in " -" for character in name):
                self.error(
                    "Der Koloniename darf nur Buchstaben, Zahlen, Leerzeichen und Bindestriche enthalten."
                )
            colony = db.execute(
                "SELECT state,world_id,name_key FROM colonies WHERE colony_id=? AND user_id=?",
                (colony_id, user),
            ).fetchone()
            if not colony:
                self.error("Diese Kolonie gehört nicht zu deinem Imperium.")
            requested_name = name.casefold()
            conflict = db.execute(
                "SELECT 1 FROM colonies WHERE name_key=? AND colony_id<>? LIMIT 1",
                (requested_name, colony_id),
            ).fetchone()
            if conflict:
                self.error("Dieser Koloniename ist weltweit bereits vergeben.")
            colony_state = json.loads(colony["state"])
            if colony_state.get("colony_name", colony_state["name"]) == name:
                self.error("Dieser Name ist bereits für die Kolonie festgelegt.")
            colony_state["colony_name"] = name
            if colony_id == state["colony_id"]:
                state["colony_name"] = name
            else:
                db.execute(
                    "UPDATE colonies SET state=?,name_key=? WHERE colony_id=? AND user_id=?",
                    (json.dumps(colony_state), requested_name, colony_id, user),
                )
            self.audit(db, user, action, colony_id, name=name)
        elif action == "outpost_colonize":
            from .game import BUILDINGS, COLONY_CONVERSION_RULES, TECH, identity

            target_id = self.text(p, "key", 1, 100)
            confirmation = self.text(p, "confirmation", 3, 100)
            world_id = int(state.get("world_id", 1))
            unit_catalog = self.game.unit_catalog_for_world(db, world_id)
            towns = self.game.world_outposts(db, world_id)
            target = next((town for town in towns if town.get("id") == target_id), None)
            if not target or target.get("owner") != user or not target.get("cleared"):
                self.error(
                    "Nur ein vollständig eroberter eigener Außenposten kann umgewandelt werden."
                )
            if confirmation != target.get("name"):
                self.error("Bestätige die Umwandlung mit dem exakten Außenpostennamen.")
            if target.get("tier", 0) >= COLONY_CONVERSION_RULES["excluded_outpost_tier"]:
                self.error("Die Zitadelle des Kerns kann nicht in eine Kolonie umgewandelt werden.")
            if not sector_is_known(db, user, world_id, target["x"], target["y"]):
                self.error("Dieser Außenposten ist noch nicht aufgeklärt.")
            self.game.require_terra_settlement(db, world_id, target["x"], target["y"])
            if state["buildings"]["hq"] < COLONY_CONVERSION_RULES["headquarters_level"]:
                self.error("Die Umwandlung benötigt Kommandozentrale Stufe 3.")
            if any(
                math.hypot(target["x"] - camp_x, target["y"] - camp_y) < 6
                for camp_x, camp_y in self.game.npc_camp_points(db, world_id)
            ):
                self.error("Kolonien benötigen sechs Sektoren Abstand zu NPC-Lagern.")
            owned = db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? AND world_id=?",
                (user, world_id),
            ).fetchall()
            slot_limit = min(4, 1 + state["buildings"]["hq"] // 3)
            if len(owned) >= slot_limit:
                self.error("Für eine weitere Kolonie ist noch kein Kolonieslot frei.")
            colony_states = [json.loads(row["state"]) for row in owned]
            if any(
                math.hypot(colony["x"] - target["x"], colony["y"] - target["y"])
                < COLONY_CONVERSION_RULES["minimum_colony_distance"]
                for colony in colony_states
            ):
                self.error("Kolonien benötigen mindestens sechs Sektoren Abstand.")
            if not any(
                (target["x"], target["y"]) in travel_times(db, (colony["x"], colony["y"]), world_id)
                for colony in colony_states
            ):
                self.error("Der Außenposten ist über begehbares Gelände nicht erreichbar.")
            costs = COLONY_CONVERSION_RULES["cost"]
            if any(have < cost for have, cost in zip(state["resources"], costs)):
                self.error("Die Umwandlung kostet 6.000 Holz, 4.500 Stein und 3.000 Erz.")
            stock = target.get("stock")
            garrison = target.get("units")
            if (
                not isinstance(stock, list)
                or len(stock) != 3
                or any(type(value) is not int or value < 0 for value in stock)
                or not isinstance(garrison, dict)
                or any(
                    unit not in unit_catalog or type(count) is not int or count < 0
                    for unit, count in garrison.items()
                )
            ):
                self.error(
                    "Der gespeicherte Außenpostenstatus ist ungültig; wende dich an die Spielleitung."
                )
            if not any(
                type(colony.get("captures")) is int and colony["captures"] > 0
                for colony in colony_states
            ):
                self.error(
                    "Der Eroberungsstand passt nicht zum Außenposten; wende dich an die Spielleitung."
                )

            state["resources"] = [have - cost for have, cost in zip(state["resources"], costs)]
            capture_owner = next(
                colony
                for colony in colony_states
                if type(colony.get("captures")) is int and colony["captures"] > 0
            )
            if capture_owner["colony_id"] == state["colony_id"]:
                state["captures"] -= 1
            else:
                capture_owner["captures"] -= 1
                db.execute(
                    "UPDATE colonies SET state=?,ranking_score=? WHERE colony_id=? AND user_id=?",
                    (
                        json.dumps(capture_owner),
                        self.game.colony_score(capture_owner),
                        capture_owner["colony_id"],
                        user,
                    ),
                )

            name_index = len(owned) + 1
            colony_name = f"{state['name']} · Basis {name_index}"
            while db.execute(
                "SELECT 1 FROM colonies WHERE name_key=? LIMIT 1", (colony_name.casefold(),)
            ).fetchone():
                name_index += 1
                colony_name = f"{state['name']} · Basis {name_index}"
            new_id = identity()
            new_state = {
                "id": user,
                "colony_id": new_id,
                "colony_name": colony_name,
                "name": state["name"],
                "x": target["x"],
                "y": target["y"],
                "terrain": terrain_at(db, target["x"], target["y"], world_id),
                "resources": list(stock),
                "buildings": {
                    key: (1 if key in ("hq", "wood", "stone", "ore", "storage") else 0)
                    for key in BUILDINGS
                },
                "tech": {key: 0 for key in TECH},
                "units": {key: int(garrison.get(key, 0)) for key in unit_catalog},
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
                    target["x"],
                    target["y"],
                    json.dumps(new_state),
                    colony_name.casefold(),
                    self.game.colony_score(new_state),
                ),
            )
            towns.remove(target)
            self.game.save_world_outposts(db, world_id, towns)
            db.execute(
                "DELETE FROM map_bookmarks WHERE target_id=? AND world_id=?",
                (target_id, world_id),
            )
            self.audit(
                db,
                user,
                action,
                target_id,
                rule=COLONY_CONVERSION_RULES["version"],
                colony_id=new_id,
                colony_name=colony_name,
                coordinates=[target["x"], target["y"]],
                stock=stock,
                garrison=garrison,
                costs=costs,
            )
        elif action == "colony_home":
            colony_id = self.text(p, "key", 1, 100)
            receipt = designate_home(db, user, int(state["world_id"]), colony_id, now)
            self.audit(db, user, action, colony_id, **receipt)
            self.game.report(
                state,
                "Heimatkolonie gewechselt",
                "Die neue Heimat ist für Weltwahl und künftige Allianzversorgung vorgemerkt. "
                "Vorräte, Truppen und laufende Reisen bleiben an ihren bisherigen Kolonien.",
            )
        elif action == "colony_abandon":
            from .game import TERRA_RUIN_SECONDS

            colony_id = self.text(p, "colony_id", 1, 100)
            confirmation = self.text(p, "confirmation", 3, 32)
            colony = db.execute(
                "SELECT world_id,is_home,x,y,state FROM colonies WHERE colony_id=? AND user_id=?",
                (colony_id, user),
            ).fetchone()
            if not colony:
                self.error("Diese Kolonie gehört nicht zu deinem Imperium.")
            colony_state = json.loads(colony["state"])
            colony_name = colony_state.get("colony_name", colony_state["name"])
            if confirmation != colony_name:
                self.error("Bestätige die Aufgabe mit dem exakten Kolonienamen.")
            if colony["is_home"]:
                self.error(
                    "Die Heimatkolonie kann erst nach einem Heimatwechsel aufgegeben werden."
                )
            home = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                (user, colony["world_id"]),
            ).fetchone()
            if not home or home["colony_id"] == colony_id:
                self.error("Die letzte Heimatkolonie einer Welt kann nicht aufgegeben werden.")
            if colony_state.get("jobs"):
                self.error(
                    "Schließe zuerst alle Bau-, Forschungs-, Trainings- und Missionsaufträge ab."
                )
            if (
                db.execute(
                    "SELECT 1 FROM terra_orbit_cargo WHERE terra_colony=?", (colony_id,)
                ).fetchone()
                or db.execute(
                    "SELECT 1 FROM terra_market_convoys WHERE target=?", (colony_id,)
                ).fetchone()
            ):
                self.error("Warte zuerst auf die Ankunft der geschützten Fracht.")
            if any(colony_state.get("goods_inventory", {}).values()) or any(
                colony_state.get("goods_reserve", {}).values()
            ):
                self.error("Leere zuerst das Warenlager und Warenreservelager dieser Kolonie.")
            if any(colony_state.get("item_inventory", {}).values()) or any(
                colony_state.get("item_reserve", {}).values()
            ):
                self.error("Übertrage zuerst alle Gegenstände und das Gegenstandsreservelager.")
            if any(colony_state.get("goods_inbound", {}).values()) or any(
                colony_state.get("item_inbound", {}).values()
            ):
                self.error(
                    "Warte zuerst, bis alle reservierten Waren und Gegenstände angekommen sind."
                )
            incoming = False
            for source in db.execute(
                "SELECT state FROM colonies WHERE world_id=? AND colony_id<>?",
                (colony["world_id"], colony_id),
            ):
                source_state = json.loads(source["state"])
                if any(
                    job.get("kind") in ("colony_supply", "alliance_supply")
                    and job.get("key") == colony_id
                    or job.get("target_colony_id") == colony_id
                    or job.get("kind") == "scout"
                    and job.get("key") == colony_id
                    or job.get("kind") in ("attack", "transport")
                    and not job.get("target_colony_id")
                    and job.get("key") == user
                    for job in source_state.get("jobs", [])
                ):
                    incoming = True
                    break
            if incoming:
                self.error(
                    "Warte zuerst, bis alle eingehenden Versorgungen und Missionen abgeschlossen sind."
                )
            open_offers = db.execute(
                "SELECT count(*) FROM offers WHERE owner=? AND world_id=? AND colony_id=? AND status='open'",
                (user, colony["world_id"], colony_id),
            ).fetchone()[0]
            if open_offers:
                self.error("Nimm zuerst alle offenen Handelsangebote dieser Kolonie zurück.")
            db.execute(
                "UPDATE offers SET colony_id=NULL WHERE colony_id=? AND status<>'open'",
                (colony_id,),
            )
            profile = self.profile(db, user)
            if profile.get("active_colony_id") == colony_id:
                db.execute(
                    "UPDATE profiles SET active_colony_id=?,active_world_id=? WHERE user_id=?",
                    (home["colony_id"], colony["world_id"], user),
                )
            db.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?)",
                (
                    identity(),
                    user,
                    now,
                    "colony_abandon",
                    json.dumps(colony_state),
                    json.dumps({"removed": True, "colony_id": colony_id}),
                ),
            )
            db.execute(
                "INSERT INTO terra_ruins(id,world_id,x,y,created,expires) VALUES (?,?,?,?,?,?)",
                (
                    identity(),
                    colony["world_id"],
                    colony["x"],
                    colony["y"],
                    now,
                    now + TERRA_RUIN_SECONDS,
                ),
            )
            db.execute("DELETE FROM colonies WHERE colony_id=? AND user_id=?", (colony_id, user))
            self.audit(
                db,
                user,
                action,
                colony_id,
                name=colony_name,
                coordinates=[colony["x"], colony["y"]],
                resources=colony_state.get("resources", []),
                reserve=colony_state.get("reserve", []),
                units=colony_state.get("units", {}),
                buildings=colony_state.get("buildings", {}),
                tech=colony_state.get("tech", {}),
            )
        elif action == "alliance_send_supply":
            self.dispatch_alliance_supply(db, state, p)
        elif action == "alliance_supply_cancel":
            self.cancel_alliance_supply(db, state, p)
        elif action in (
            "alliance_garrison_policy",
            "alliance_garrison_station",
            "alliance_garrison_recall",
        ):
            self.alliance_garrison_command(db, state, action, p)
        elif action in (
            "alliance_attack_create",
            "alliance_attack_join",
            "alliance_attack_withdraw",
            "alliance_attack_cancel",
        ):
            self.terra_alliance_attack_command(db, state, action, p)
        elif action in (
            "alliance_peace_offer",
            "alliance_peace_accept",
            "alliance_peace_decline",
            "alliance_peace_cancel",
        ):
            self.alliance_war_command(db, state, action, p)
        elif action == "mission_recall":
            self.recall_mission(db, state, p)
        elif action == "expedition":
            self.dispatch_expedition(db, state, p)
        elif action in (
            "admin_npc_convoy_schedule",
            "npc_convoy_escort",
            "npc_convoy_raid",
            "npc_convoy_recall",
            "npc_convoy_claim",
        ):
            world = int(state["world_id"])
            try:
                if action == "admin_npc_convoy_schedule":
                    if role != "admin":
                        self.error("Nur die Spielleitung kann einen NPC-Konvoi ansetzen.")
                    convoy_id = identity()
                    npc_convoys.schedule(db, world, convoy_id, self.text(p, "name", 3, 48), now)
                    self.audit(
                        db, user, action, convoy_id, world_id=world, rules_digest=npc_convoys.DIGEST
                    )
                elif action in ("npc_convoy_escort", "npc_convoy_raid"):
                    convoy_id = self.text(p, "key", 1, 100)
                    count = self.integer(
                        p,
                        "count",
                        1,
                        min(
                            int(state["units"].get("ranger", 0)),
                            int(npc_convoys.RULES["maximum_rangers"]),
                        ),
                    )
                    if len(state["jobs"]) >= self.game.terra_mission_limit(state):
                        self.error("Deine Auftragsplätze sind belegt.")
                    mission = npc_convoys.join(
                        db,
                        world,
                        convoy_id,
                        user,
                        identity(),
                        (int(state["x"]), int(state["y"])),
                        "escort" if action == "npc_convoy_escort" else "raid",
                        count,
                        now,
                    )
                    state["units"]["ranger"] -= count
                    state["jobs"].append(mission)
                    self.audit(db, user, action, convoy_id, mission_id=mission["id"], rangers=count)
                elif action == "npc_convoy_recall":
                    mission_id = self.text(p, "key", 1, 100)
                    convoy_mission = next(
                        (
                            job
                            for job in state["jobs"]
                            if job["id"] == mission_id and job["kind"] == "npc_convoy"
                        ),
                        None,
                    )
                    if convoy_mission is None:
                        self.error("Dieser Konvoiauftrag gehört nicht zur aktiven Kolonie.")
                    recalled = npc_convoys.recall(
                        db, world, str(convoy_mission["key"]), user, mission_id, now
                    )
                    state["jobs"].remove(convoy_mission)
                    state["jobs"].append(
                        {
                            "id": identity(),
                            "kind": "return",
                            "key": str(state["colony_id"]),
                            "label": "Konvoi-Rückruf",
                            "due": recalled["return_due"],
                            "army": {"ranger": recalled["survivors"]},
                            "loot": [0, 0, 0],
                        }
                    )
                    self.audit(db, user, action, mission_id, world_id=world)
                else:
                    convoy_id = self.text(p, "key", 1, 100)
                    ore = npc_convoys.claim(db, world, convoy_id, user, now)
                    self.credit_state(db, state, [0, 0, ore], "Konvoi-Belohnung", now)
                    self.audit(db, user, action, convoy_id, world_id=world, ore=ore)
            except npc_convoys.ConvoyError as exc:
                self.error(str(exc))
        elif action == "admin_recurring_quests":
            if role != "admin":
                self.error("Nur die Spielleitung kann wiederkehrende Aufgaben umstellen.")
            enabled = p.get("enabled")
            if type(enabled) is not bool:
                self.error("Aktivierung der wiederkehrenden Aufgaben ist ungültig.")
            world_id = int(state["world_id"])
            if recurring_quests.set_enabled(db, world_id, identity(), now, enabled):
                self.audit(
                    db, user, action, str(world_id), enabled=enabled, rules=recurring_quests.VERSION
                )
        elif action == "admin_npc_invasion_schedule":
            if role != "admin":
                self.error("Nur die Spielleitung kann eine Invasion ansetzen.")
            world_id = int(state["world_id"])
            world = db.execute(
                "SELECT settings FROM world_settings WHERE world_id=?", (world_id,)
            ).fetchone()
            settings = json.loads(world["settings"] or "{}") if world else {}
            if (
                not isinstance(settings, dict)
                or settings.get(npc_camps.RULESET_KEY) != npc_camps.ATTACK_RULES_VERSION
            ):
                self.error("Eine Invasion benötigt die aktivierten CAMPS-3-Regeln.")
            name = self.text(p, "name", 3, 48)
            invasion_id = identity()
            if not npc_invasions.schedule(db, world_id, invasion_id, name, now):
                self.error("In dieser Welt läuft bereits ein Invasions-Zeitfenster.")
            self.audit(
                db, user, action, invasion_id, world_id=world_id, rules_digest=npc_invasions.DIGEST
            )
        elif action in ("admin_terra_boss_schedule", "terra_boss_attack", "terra_boss_claim"):
            world = int(state["world_id"])
            try:
                if action == "admin_terra_boss_schedule":
                    if role != "admin":
                        self.error("Nur die Spielleitung kann einen Weltboss ansetzen.")
                    raid_id = identity()
                    name = self.text(p, "name", 3, 48)
                    boss_raids.schedule(db, world, raid_id, name, now)
                    self.audit(
                        db, user, action, raid_id, world_id=world, rules_digest=boss_raids.DIGEST
                    )
                elif action == "terra_boss_attack":
                    raid_id = self.text(p, "key", 1, 100)
                    maximum = min(
                        int(state["units"].get("ranger", 0)),
                        int(boss_raids.RULES["max_rangers_per_attack"]),
                    )
                    count = self.integer(p, "count", 1, maximum)
                    if len(state["jobs"]) >= self.game.terra_mission_limit(state):
                        self.error("Deine Auftragsplätze sind belegt.")
                    mission = boss_raids.join(db, world, raid_id, user, identity(), count, now)
                    state["units"]["ranger"] -= count
                    state["jobs"].append(mission)
                    self.audit(db, user, action, raid_id, world_id=world, rangers=count)
                else:
                    raid_id = self.text(p, "key", 1, 100)
                    ore = boss_raids.claim(db, world, raid_id, user, now)
                    self.credit_state(db, state, [0, 0, ore], "Weltboss-Belohnung", now)
                    self.audit(db, user, action, raid_id, world_id=world, ore=ore)
            except boss_raids.BossRaidError as exc:
                self.error(str(exc))
        elif action == "ruin_exploration":
            self.dispatch_ruin_exploration(db, state, p)
        elif action.startswith("alliance_"):
            self.alliance_command(db, state, action, p)
        elif action == "diplomacy":
            self.diplomacy_command(db, state, p)
        elif action in ("message_report", "mute_appeal"):
            self.moderation_case_command(db, state, action, p)
        elif action == "mail_read":
            mail_id = self.text(p, "key", 1, 100)
            updated = db.execute(
                "UPDATE system_mail SET read_at=COALESCE(read_at,?) "
                "WHERE id=? AND recipient_id=? RETURNING id",
                (now, mail_id, user),
            ).fetchone()
            if not updated:
                self.error("Diese Nachricht ist in deinem Postfach nicht vorhanden.")
        elif action == "notification_preference":
            from .game_events import CATEGORIES

            category = p.get("category")
            muted = p.get("muted")
            if category not in CATEGORIES or type(muted) is not bool:
                self.error("Ungültige Benachrichtigungseinstellung.")
            db.execute(
                "INSERT INTO game_event_preferences(user_id,category,muted,updated) "
                "VALUES (?,?,?,?) ON CONFLICT(user_id,category) DO UPDATE SET "
                "muted=excluded.muted,updated=excluded.updated",
                (user, category, int(muted), now),
            )
            self.audit(db, user, action, str(category), muted=muted)
        elif action == "message":
            self.communication(db, state, p)
        elif action == "profile_settings_update":
            self.update_player_profile(db, state, p)
        elif action.startswith(("friend_", "player_block", "player_unblock")):
            self.social_command(db, state, action, p)
        elif action.startswith("note_"):
            self.notes_command(db, state, action, p)
        elif action in ("report_share", "report_unshare"):
            self.report_sharing_command(db, state, action, p)
        elif action.startswith("market_"):
            self.market(db, state, action, p)
        elif action == "colony_supply":
            self.dispatch_colony_supply(db, state, p)
        elif action in ("attack", "transport", "scout"):
            self.dispatch(db, state, action, p)
        elif action in ("station", "recall"):
            self.garrison(db, state, action, p)
        elif action == "reserve_claim":
            cap = 2000 + 2000 * state["buildings"]["storage"]
            reserve = state.setdefault("reserve", [0, 0, 0])
            for i in range(3):
                moved = min(reserve[i], max(0, cap - state["resources"][i]))
                reserve[i] -= moved
                state["resources"][i] += moved
        elif action in ("map_bookmark_add", "map_bookmark_remove"):
            target_id = self.text(p, "key", 1, 100)
            # World state is JSON in both adapters; validate against the current shared map.
            world_id = int(state.get("world_id", 1))
            towns = self.game.world_outposts(db, world_id)
            if not any(town.get("id") == target_id for town in towns):
                self.error("Dieser Außenposten existiert nicht in dieser Welt.")
            target = next(town for town in towns if town.get("id") == target_id)
            if not sector_is_known(db, user, world_id, target["x"], target["y"]):
                self.error("Dieser Sektor ist noch nicht aufgeklärt.")
            if action == "map_bookmark_add":
                exists = db.execute(
                    "SELECT 1 FROM map_bookmarks WHERE user_id=? AND target_id=? AND world_id=?",
                    (user, target_id, world_id),
                ).fetchone()
                count = db.execute(
                    "SELECT count(*) FROM map_bookmarks WHERE user_id=? AND world_id=?",
                    (user, world_id),
                ).fetchone()[0]
                if not exists and count >= 20:
                    self.error("Du kannst höchstens 20 Außenposten je Welt merken.")
                db.execute(
                    "INSERT INTO map_bookmarks(user_id,target_id,created,world_id) VALUES (?,?,?,?) "
                    "ON CONFLICT(user_id,target_id) DO NOTHING",
                    (user, target_id, now, world_id),
                )
            else:
                db.execute(
                    "DELETE FROM map_bookmarks WHERE user_id=? AND target_id=? AND world_id=?",
                    (user, target_id, world_id),
                )
            self.audit(db, user, action, target_id)
        elif action == "terra_warden_fortify":
            world_id = state["world_id"]
            if (
                p.get("world_id") != world_id
                or self.world_faction(db, user, world_id) != "wardens"
                or "kinetic_shield" not in state.get("faction_research", [])
            ):
                self.error("Die Befestigung benötigt Wächterforschung in der aktiven Welt.")
            if state.get("warden_fortify_ready_at", 0) > now:
                self.error("Die Wächterbefestigung ist noch in der Abklingzeit.")
            target_id = self.text(p, "key")
            member = self.member(db, user)
            row = db.execute(
                "SELECT c.user_id FROM colonies c JOIN members m ON m.user_id=c.user_id "
                "WHERE c.colony_id=? AND c.world_id=? AND c.user_id<>? AND m.alliance_id=?",
                (target_id, world_id, user, member["alliance_id"] if member else ""),
            ).fetchone()
            if not row or not member:
                self.error("Wähle eine verbündete Kolonie derselben Welt.")
            target = self.game.read_colony(db, target_id)
            if self.active_warden_fortification(db, target, now):
                self.error("Diese Kolonie ist bereits durch Wächter befestigt.")
            if state["resources"][2] < 200:
                self.error("Für die Wächterbefestigung fehlen 200 Erz.")
            state["resources"][2] -= 200
            state["warden_fortify_ready_at"] = now + 86400
            hours = 2 if "mobile_fortress" in state.get("faction_research", []) else 1
            ends = now + hours * 3600
            target["warden_fortification"] = {
                "owner": user,
                "alliance_id": member["alliance_id"],
                "starts": now,
                "ends": ends,
            }
            self.game.report(
                target,
                "Wächterbefestigung",
                f"Deine Kolonie erhält für {hours} h zehn Prozent Verteidigung.",
            )
            self.game.save(db, target)
            self.audit(db, user, action, target_id, world_id=world_id, ends=ends)
        elif action == "faction":
            faction = self.text(p, "key")
            world_id = int(state["world_id"])
            if faction not in ("pioneers", "wardens", "syndicate"):
                self.error("Fraktion ungültig.")
            updated = db.execute(
                "UPDATE world_players SET faction=? WHERE user_id=? AND world_id=? "
                "AND faction IS NULL RETURNING faction",
                (faction, user, world_id),
            ).fetchone()
            if not updated:
                self.error("Fraktion bereits festgelegt.")
            state["faction_chosen"] = True
            self.audit(db, user, "faction", faction, world_id=world_id)
        elif action == "vacation":
            if state.get("vacation_until", 0) > now:
                self.error("Urlaubsmodus läuft mindestens 24 Stunden.")
            for row in db.execute("SELECT state FROM colonies WHERE user_id=?", (user,)):
                other = json.loads(row[0])
                if other["jobs"]:
                    self.error("Urlaubsmodus erst ohne eigene Aufträge und feindliche Anmärsche.")
            if db.execute(
                "SELECT 1 FROM incoming_attack_index WHERE target_user=? LIMIT 1", (user,)
            ).fetchone():
                self.error("Urlaubsmodus erst ohne eigene Aufträge und feindliche Anmärsche.")
            state["vacation_until"] = now + 86400
        elif action.startswith("admin_"):
            self.admin(db, state, action, p)
        else:
            self.error("Unbekannte Aktion.")

    def admin(self, db: Connection, state: dict[str, Any], action: str, p: dict[str, Any]) -> None:
        from .game import identity

        user, now = state["id"], int(time.time())
        role = self.profile(db, user)["role"]
        if role not in ("admin", "moderator"):
            self.error("Keine Moderationsberechtigung.")
        if action in ("admin_ban", "admin_mute"):
            target = self.text(p, "key")
            profile = self.profile(db, target)
            if profile["role"] != "player":
                self.error("Administrationskonten können hier nicht gesperrt werden.")
            if action == "admin_ban":
                banned = self.integer(p, "value", 0, 1)
                db.execute("UPDATE profiles SET banned=? WHERE user_id=?", (banned, target))
                if banned:
                    db.execute("DELETE FROM sessions WHERE user_id=?", (target,))
            else:
                db.execute(
                    "UPDATE profiles SET muted_until=? WHERE user_id=?",
                    (now + self.integer(p, "minutes", 0, 10080) * 60, target),
                )
        elif action == "admin_case_resolve":
            case_id = self.text(p, "key", 1, 100)
            case = db.execute(
                "SELECT case_type,target_user_id,message_id FROM moderation_cases "
                "WHERE id=? AND status='open'",
                (case_id,),
            ).fetchone()
            ban_appeal = None
            if case is None:
                ban_appeal = db.execute(
                    "SELECT user_id FROM account_ban_appeals WHERE id=? AND status='open'",
                    (case_id,),
                ).fetchone()
                if ban_appeal:
                    case = {
                        "case_type": "account_ban_appeal",
                        "target_user_id": ban_appeal["user_id"],
                        "message_id": None,
                    }
            if not case:
                self.error("Offener Moderationsfall nicht gefunden.")
            outcome = self.text(p, "value", 1, 30)
            case_type = str(case["case_type"])
            if case_type == "account_ban_appeal":
                if outcome not in ("deny_ban_appeal", "grant_ban_appeal"):
                    self.error("Ungültige Entscheidung für einen Kontosperrungs-Einspruch.")
                if outcome == "grant_ban_appeal":
                    db.execute(
                        "UPDATE profiles SET banned=0 WHERE user_id=? AND role='player'",
                        (case["target_user_id"],),
                    )
                db.execute(
                    "UPDATE account_ban_appeals SET status='resolved',resolution=?,resolved=?,"
                    "resolver_id=? WHERE id=? AND status='open'",
                    (outcome, now, user, case_id),
                )
                self.audit(db, user, action, case_id, outcome=outcome)
                return
            elif case_type == "message_report":
                if outcome not in ("dismiss", "hide_message"):
                    self.error("Ungültige Entscheidung für eine Nachrichtenmeldung.")
                if outcome == "hide_message":
                    db.execute("UPDATE messages SET hidden=1 WHERE id=?", (case["message_id"],))
            else:
                if outcome not in ("deny_appeal", "lift_mute"):
                    self.error("Ungültige Entscheidung für einen Stummschaltungs-Einspruch.")
                if outcome == "lift_mute":
                    db.execute(
                        "UPDATE profiles SET muted_until=? WHERE user_id=?",
                        (now, case["target_user_id"]),
                    )
            db.execute(
                "UPDATE moderation_cases SET status='resolved',resolution=?,resolved=?,"
                "resolver_id=? WHERE id=? AND status='open'",
                (outcome, now, user, case_id),
            )
            self.audit(db, user, action, case_id, outcome=outcome)
        elif action == "admin_announcement_create":
            scope = p.get("target_kind")
            if scope == "global":
                if role != "admin":
                    self.error("Globale Ankündigungen kann nur die Spielleitung veröffentlichen.")
                world_id = None
            elif scope == "world":
                world_id = self.integer(p, "world_id", 1, 2**31 - 1)
                if role == "moderator" and world_id != int(state["world_id"]):
                    self.error("Moderatoren können nur ihre aktive Welt ankündigen.")
                if not db.execute(
                    "SELECT 1 FROM world_settings WHERE world_id=?", (world_id,)
                ).fetchone():
                    self.error("Diese Ankündigungswelt existiert nicht.")
            else:
                self.error("Ankündigungsreichweite ist ungültig.")
            announcement_id = identity()
            title = self.text(p, "name", 1, 80)
            body = self.text(p, "body", 1, 2000)
            publish_at = p.get("publish_at", now)
            if type(publish_at) is not int or not now <= publish_at <= now + 90 * 86400:
                self.error(
                    "Veröffentlichung muss jetzt oder innerhalb der nächsten 90 Tage erfolgen."
                )
            emergency = p.get("emergency", False)
            if not isinstance(emergency, bool):
                self.error("Notfallkennzeichnung ist ungültig.")
            db.execute(
                "INSERT INTO system_announcements(id,world_id,author_id,title,body,created,"
                "publish_at,emergency) VALUES (?,?,?,?,?,?,?,?)",
                (announcement_id, world_id, user, title, body, now, publish_at, int(emergency)),
            )
            self.audit(
                db,
                user,
                action,
                announcement_id,
                scope="global" if world_id is None else "world",
                world_id=world_id,
                title=title,
                publish_at=publish_at,
                emergency=emergency,
            )
        elif action == "admin_announcement_archive":
            announcement_id = self.text(p, "key", 1, 100)
            announcement = db.execute(
                "SELECT world_id FROM system_announcements WHERE id=? AND archived=0",
                (announcement_id,),
            ).fetchone()
            if not announcement:
                self.error("Aktive Ankündigung nicht gefunden.")
            if role == "moderator" and (
                announcement["world_id"] is None
                or int(announcement["world_id"]) != int(state["world_id"])
            ):
                self.error("Moderatoren können nur Ankündigungen ihrer aktiven Welt archivieren.")
            db.execute(
                "UPDATE system_announcements SET archived=1 WHERE id=? AND archived=0",
                (announcement_id,),
            )
            self.audit(db, user, action, announcement_id)
        elif action == "admin_mail_send":
            if role != "admin":
                self.error("Private Systemnachrichten kann nur die Spielleitung senden.")
            recipient_id = self.text(p, "key", 1, 100)
            if not db.execute("SELECT 1 FROM users WHERE id=?", (recipient_id,)).fetchone():
                self.error("Empfänger nicht gefunden.")
            mail_id = identity()
            title = self.text(p, "name", 1, 80)
            body = self.text(p, "body", 1, 2000)
            db.execute(
                "INSERT INTO system_mail(id,recipient_id,author_id,title,body,created) "
                "VALUES (?,?,?,?,?,?)",
                (mail_id, recipient_id, user, title, body, now),
            )
            self.audit(db, user, action, mail_id, recipient=recipient_id, title=title)
        elif action == "admin_hide":
            db.execute("UPDATE messages SET hidden=1 WHERE id=?", (self.text(p, "key"),))
        elif role != "admin":
            self.error("Diese Funktion erfordert Administratorrechte.")
        elif action == "admin_flag":
            key, value = self.text(p, "key"), self.text(p, "value")
            if key not in ("pvp", "registration", "maintenance") or value not in ("true", "false"):
                self.error("Ungültiger Schalter.")
            db.execute("UPDATE flags SET value=? WHERE name=?", (value, key))
        elif action == "admin_event":
            duration_hours = self.integer(p, "hours", 1, 168)
            warning_hours = self.integer(p, "warning_hours", 0, 168)
            end_hours = self.integer(p, "end_hours", 0, 168)
            if end_hours > duration_hours:
                self.error("Die Endphase darf nicht länger als das Ereignis sein.")
            event_id = identity()
            starts = now + warning_hours * 3600
            ends = starts + duration_hours * 3600
            event = {
                "id": event_id,
                "name": self.text(p, "name", 3, 60),
                "starts": starts,
                "ends": ends,
                "bonus": self.integer(p, "bonus", 0, 100),
                "world_id": int(state["world_id"]),
                "warning_hours": warning_hours,
                "end_starts": ends - end_hours * 3600 if end_hours else ends,
                "end_bonus": self.integer(p, "end_bonus", 0, 100),
                "goal_score": self.integer(p, "goal_score", 1, 1_000_000_000),
            }
            db.execute(
                "INSERT INTO events(id,name,starts,ends,bonus,world_id,warning_hours,"
                "end_starts,end_bonus,goal_score) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    event["id"],
                    event["name"],
                    event["starts"],
                    event["ends"],
                    event["bonus"],
                    event["world_id"],
                    event["warning_hours"],
                    event["end_starts"],
                    event["end_bonus"],
                    event["goal_score"],
                ),
            )
            version, frozen, digest = live_events.snapshot(event)
            db.execute(
                "INSERT INTO live_event_rules(event_id,version,snapshot,digest,source) "
                "VALUES (?,?,?,?,?)",
                (event_id, version, frozen, digest, "admin_create"),
            )
            self.audit(
                db,
                user,
                action,
                event_id,
                world_id=event["world_id"],
                rules_version=version,
                rules_digest=digest,
                goal_score=event["goal_score"],
            )
        elif action == "admin_season":
            world = db.execute(
                "SELECT mode FROM world_settings WHERE world_id=?", (state["world_id"],)
            ).fetchone()
            if not world or world["mode"] != "season":
                self.error(
                    "Saisonwettbewerbe sind nur in Saisonwelten erlaubt; "
                    "Sandboxwelten bleiben ohne Saisonwettbewerb."
                )
            if db.execute(
                "SELECT 1 FROM seasons s JOIN world_settings w ON w.world_id=s.world_id "
                "WHERE s.world_id=? AND w.mode='season'",
                (state["world_id"],),
            ).fetchone():
                self.error("Für einen neuen Wettbewerb lege eine neue Saisonwelt an.")
            if db.execute(
                "SELECT 1 FROM seasons WHERE world_id=? AND ends>? AND archived=0",
                (state["world_id"], now),
            ).fetchone():
                self.error("Es läuft bereits eine Saison.")
            from .game import REGISTRY, RULES_DIGEST, RULES_SNAPSHOT, identity

            season_id = identity()
            season_name = self.text(p, "name", 3, 60)
            goal_score = self.integer(p, "goal_score", 1, 1_000_000_000)
            db.execute(
                "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id,goal_score) "
                "VALUES (?,?,?,?,0,?,?,?)",
                (
                    season_id,
                    season_name,
                    now,
                    now + self.integer(p, "days", 1, 365) * 86400,
                    "[]",
                    state["world_id"],
                    goal_score,
                ),
            )
            db.execute(
                "INSERT INTO season_rules(season_id,version,snapshot,digest,source) "
                "VALUES (?,?,?,?,'season_start')",
                (season_id, REGISTRY["version"], RULES_SNAPSHOT, RULES_DIGEST),
            )
        elif action == "admin_retry":
            db.execute("DELETE FROM job_failures WHERE id=?", (self.text(p, "key"),))
        else:
            self.error("Unbekannter Administrationsbefehl.")
        self.audit(db, user, action, str(p.get("key", "")), parameters=p)

    def alliance_treasury_command(
        self, db: Connection, state: dict[str, Any], action: str, payload: dict[str, Any]
    ) -> None:
        user = str(state["id"])
        now = int(time.time())
        world_id = int(state["world_id"])
        member = self.member(db, user)
        if not member:
            self.error("Nur Allianzmitglieder können die Allianzkasse verwenden.")
        alliance_id = str(member["alliance_id"])
        try:
            if action == "alliance_treasury_donate":
                amounts = alliance_treasury.resource_vector(payload.get("resources"))
                colony = db.execute(
                    "SELECT user_id,world_id FROM colonies WHERE colony_id=?",
                    (state["colony_id"],),
                ).fetchone()
                if not colony or colony["user_id"] != user or int(colony["world_id"]) != world_id:
                    self.error("Die aktive Spenderkolonie gehört nicht zu dieser Welt.")
                if any(have < amount for have, amount in zip(state["resources"], amounts)):
                    self.error("Für diese Spende fehlen Rohstoffe in deiner aktiven Kolonie.")
                state["resources"] = [
                    int(have) - amount for have, amount in zip(state["resources"], amounts)
                ]
                alliance_treasury.change_balance(db, alliance_id, world_id, amounts, [0, 0, 0])
                alliance_treasury.append_ledger(
                    db,
                    entry_key=alliance_treasury.identity(),
                    alliance_id=alliance_id,
                    world_id=world_id,
                    actor_id=user,
                    request_id=None,
                    event_type="donation",
                    available=amounts,
                    reserved=[0, 0, 0],
                    details={"resources": amounts},
                    created=now,
                )
                self.audit(db, user, action, alliance_id, world_id=world_id, resources=amounts)
                return

            if action == "alliance_treasury_request":
                net = alliance_treasury.resource_vector(payload.get("resources"))
                colony = db.execute(
                    "SELECT user_id,world_id FROM colonies WHERE colony_id=?",
                    (state["colony_id"],),
                ).fetchone()
                if not colony or colony["user_id"] != user or int(colony["world_id"]) != world_id:
                    self.error("Auszahlungen gehen nur an deine aktive Kolonie dieser Welt.")
                gross, fee = alliance_treasury.gross_vector(net)
                if any(amount > 100_000 for amount in gross):
                    self.error(
                        "Der beantragte Betrag einschließlich Gebühr darf je Ressource 100.000 nicht überschreiten."
                    )
                required = (
                    int(alliance_treasury.RULES["withdrawals"]["approvals_at_or_above_threshold"])
                    if sum(gross) >= alliance_treasury.APPROVAL_THRESHOLD
                    else int(alliance_treasury.RULES["withdrawals"]["approvals_below_threshold"])
                )
                request_id = alliance_treasury.identity()
                expires = now + alliance_treasury.EXPIRY_SECONDS
                db.execute(
                    "INSERT INTO alliance_treasury_requests"
                    "(id,alliance_id,world_id,requester_id,destination_colony_id,gross_json,"
                    "fee_json,net_json,required_approvals,rules_version,rules_digest,status,created,expires) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)",
                    (
                        request_id,
                        alliance_id,
                        world_id,
                        user,
                        str(state["colony_id"]),
                        json.dumps(gross),
                        json.dumps(fee),
                        json.dumps(net),
                        required,
                        alliance_treasury.RULES_VERSION,
                        alliance_treasury.RULES_DIGEST,
                        now,
                        expires,
                    ),
                )
                alliance_treasury.change_balance(
                    db,
                    alliance_id,
                    world_id,
                    [-amount for amount in gross],
                    gross,
                )
                alliance_treasury.append_ledger(
                    db,
                    entry_key=request_id + ":reserve",
                    alliance_id=alliance_id,
                    world_id=world_id,
                    actor_id=user,
                    request_id=request_id,
                    event_type="withdrawal_reserved",
                    available=[-amount for amount in gross],
                    reserved=gross,
                    details={"gross": gross, "fee": fee, "net": net},
                    created=now,
                )
                self.audit(
                    db,
                    user,
                    action,
                    request_id,
                    world_id=world_id,
                    gross=gross,
                    fee=fee,
                    approvals_required=required,
                )
                return

            manager = member["role"] == "leader" or "treasury" in self.alliance_permissions(
                db, member
            )
            request_id = self.text(payload, "key", 1, 100)
            request_row = db.execute(
                "SELECT * FROM alliance_treasury_requests WHERE id=? AND alliance_id=? "
                "AND world_id=? AND status='pending'",
                (request_id, alliance_id, world_id),
            ).fetchone()
            if not request_row:
                self.error("Offener Kassenantrag in dieser Welt nicht gefunden.")
            request = dict(request_row)
            if action == "alliance_treasury_cancel":
                if request["requester_id"] != user:
                    self.error("Nur der Antragsteller kann den eigenen offenen Antrag stornieren.")
                alliance_treasury.release_request(
                    db, request, actor_id=user, status="cancelled", at=now
                )
                self.audit(db, user, action, request_id, world_id=world_id)
                return
            if not manager:
                self.error("Für diese Kassenaktion benötigst du das Allianzrecht Allianzkasse.")
            if request["requester_id"] == user:
                self.error("Antragsteller dürfen ihren eigenen Kassenantrag nicht freigeben.")
            if int(request["expires"]) <= now:
                alliance_treasury.release_request(
                    db, request, actor_id="worker", status="expired", at=now
                )
                self.audit(db, user, "alliance_treasury_expired", request_id, world_id=world_id)
                return
            if action == "alliance_treasury_decline":
                alliance_treasury.release_request(
                    db, request, actor_id=user, status="declined", at=now
                )
                self.audit(db, user, action, request_id, world_id=world_id)
                return
            if action != "alliance_treasury_approve":
                self.error("Unbekannte Kassenaktion.")
            valid_recipient = db.execute(
                "SELECT 1 FROM members m JOIN colonies c ON c.user_id=m.user_id "
                "WHERE m.user_id=? AND m.alliance_id=? AND c.colony_id=? AND c.world_id=?",
                (
                    request["requester_id"],
                    alliance_id,
                    request["destination_colony_id"],
                    world_id,
                ),
            ).fetchone()
            if not valid_recipient:
                alliance_treasury.release_request(
                    db, request, actor_id=user, status="void_membership", at=now
                )
                self.audit(db, user, "alliance_treasury_void", request_id, world_id=world_id)
                return
            added = db.execute(
                "INSERT INTO alliance_treasury_approvals(request_id,approver_id,approved_at) "
                "VALUES (?,?,?) ON CONFLICT(request_id,approver_id) DO NOTHING RETURNING request_id",
                (request_id, user, now),
            ).fetchone()
            if not added:
                self.error("Du hast diesen Kassenantrag bereits freigegeben.")
            approvals = int(
                db.execute(
                    "SELECT count(DISTINCT a.approver_id) FROM alliance_treasury_approvals a "
                    "JOIN members m ON m.user_id=a.approver_id AND m.alliance_id=? "
                    "WHERE a.request_id=? AND a.approver_id<>? AND "
                    "(m.role='leader' OR EXISTS (SELECT 1 FROM alliance_role_permissions p "
                    "WHERE p.alliance_id=m.alliance_id AND p.role=m.role AND p.permission='treasury'))",
                    (alliance_id, request_id, request["requester_id"]),
                ).fetchone()[0]
            )
            needed = int(request["required_approvals"])
            if approvals < needed:
                self.audit(
                    db,
                    user,
                    action,
                    request_id,
                    world_id=world_id,
                    approvals=approvals,
                    required=needed,
                )
                return
            gross = [int(value) for value in json.loads(str(request["gross_json"]))]
            fee = [int(value) for value in json.loads(str(request["fee_json"]))]
            net = [int(value) for value in json.loads(str(request["net_json"]))]
            alliance_treasury.change_balance(
                db, alliance_id, world_id, [0, 0, 0], [-amount for amount in gross]
            )
            self.credit_colony(
                db,
                str(request["destination_colony_id"]),
                net,
                "Auszahlung aus der Allianzkasse",
                now,
            )
            alliance_treasury.append_ledger(
                db,
                entry_key=request_id + ":paid",
                alliance_id=alliance_id,
                world_id=world_id,
                actor_id=user,
                request_id=request_id,
                event_type="withdrawal_paid",
                available=[0, 0, 0],
                reserved=[-amount for amount in gross],
                details={"gross": gross, "fee": fee, "net": net},
                created=now,
            )
            db.execute(
                "UPDATE alliance_treasury_requests SET status='paid',completed=? "
                "WHERE id=? AND status='pending'",
                (now, request_id),
            )
            self.audit(
                db,
                user,
                action,
                request_id,
                world_id=world_id,
                gross=gross,
                fee=fee,
                net=net,
                approvals=approvals,
            )
        except ValueError as exc:
            self.error(str(exc))

    def alliance_projects_command(
        self, db: Connection, state: dict[str, Any], action: str, payload: dict[str, Any]
    ) -> None:
        user = str(state["id"])
        world_id = int(state["world_id"])
        now = int(time.time())
        member = self.member(db, user)
        if not member:
            self.error("Allianzprojekte stehen nur aktuellen Mitgliedern offen.")
        alliance_id = str(member["alliance_id"])
        alliance_projects.expire(self, db, now, state)

        if action == "alliance_project_create":
            self.require_alliance_permission(db, user, "projects")
            key = self.text(payload, "key", 1, 40)
            template = alliance_projects.PROJECTS.get(key)
            if not template:
                self.error("Dieses Allianzprojekt gibt es nicht.")
            if db.execute(
                "SELECT 1 FROM alliance_projects WHERE alliance_id=? AND world_id=? "
                "AND status='active'",
                (alliance_id, world_id),
            ).fetchone():
                self.error("In dieser Welt läuft bereits ein Allianzprojekt.")
            project_id = alliance_projects.identity()
            target = [int(amount) for amount in template["target"]]
            db.execute(
                "INSERT INTO alliance_projects"
                "(id,alliance_id,world_id,project_key,title,record_reward,target_json,"
                "contributed_json,initiator_id,rules_version,rules_digest,status,created,deadline) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,'active',?,?)",
                (
                    project_id,
                    alliance_id,
                    world_id,
                    key,
                    str(template["name"]),
                    str(template["record"]),
                    json.dumps(target),
                    json.dumps([0, 0, 0]),
                    user,
                    alliance_projects.RULES_VERSION,
                    alliance_projects.RULES_DIGEST,
                    now,
                    now + int(template["duration_seconds"]),
                ),
            )
            self.audit(
                db,
                user,
                action,
                project_id,
                alliance=alliance_id,
                world_id=world_id,
                project_key=key,
                rules_version=alliance_projects.RULES_VERSION,
            )
            return

        project_id = self.text(payload, "key", 1, 100)
        row = db.execute(
            "SELECT * FROM alliance_projects WHERE id=? AND alliance_id=? AND world_id=? "
            "AND status='active'",
            (project_id, alliance_id, world_id),
        ).fetchone()
        if not row:
            self.error("Aktives Allianzprojekt in dieser Welt nicht gefunden.")
        project = dict(row)
        if action == "alliance_project_cancel":
            self.require_alliance_permission(db, user, "projects")
            alliance_projects.refund(
                self,
                db,
                project,
                actor_id=user,
                status="cancelled",
                at=now,
                active_state=state,
            )
            self.audit(db, user, action, project_id, world_id=world_id)
            return
        if action != "alliance_project_contribute":
            self.error("Unbekannte Allianzprojektaktion.")

        try:
            amounts = alliance_projects.resource_vector(payload.get("resources"))
        except ValueError as exc:
            self.error(str(exc))
        colony = db.execute(
            "SELECT user_id,world_id FROM colonies WHERE colony_id=?",
            (state["colony_id"],),
        ).fetchone()
        if not colony or colony["user_id"] != user or int(colony["world_id"]) != world_id:
            self.error("Beiträge kommen nur aus deiner aktiven Kolonie dieser Welt.")
        target = [int(amount) for amount in json.loads(str(project["target_json"]))]
        contributed = [int(amount) for amount in json.loads(str(project["contributed_json"]))]
        if any(
            amount > target_value - current
            for amount, target_value, current in zip(amounts, target, contributed)
        ):
            self.error("Ein Beitrag darf das jeweilige Projektziel nicht überschreiten.")
        if any(have < amount for have, amount in zip(state["resources"], amounts)):
            self.error("Für diesen Projektbeitrag fehlen Rohstoffe in deiner Kolonie.")
        state["resources"] = [
            int(have) - amount for have, amount in zip(state["resources"], amounts)
        ]
        contribution_id = alliance_projects.identity()
        db.execute(
            "INSERT INTO alliance_project_contributions"
            "(id,project_id,user_id,world_id,source_colony_id,resources_json,refunded,created) "
            "VALUES (?,?,?,?,?,?,FALSE,?)",
            (
                contribution_id,
                project_id,
                user,
                world_id,
                str(state["colony_id"]),
                json.dumps(amounts),
                now,
            ),
        )
        updated = [current + amount for current, amount in zip(contributed, amounts)]
        complete = all(current >= goal for current, goal in zip(updated, target))
        db.execute(
            "UPDATE alliance_projects SET contributed_json=?,status=?,completed=? "
            "WHERE id=? AND status='active'",
            (
                json.dumps(updated),
                "completed" if complete else "active",
                now if complete else None,
                project_id,
            ),
        )
        alliance_projects.append_ledger(
            db,
            entry_key=contribution_id,
            project=project,
            actor_id=user,
            source_colony_id=str(state["colony_id"]),
            event_type="contribution",
            resources=amounts,
            created=now,
        )
        self.audit(
            db,
            user,
            action,
            project_id,
            world_id=world_id,
            contribution_id=contribution_id,
            resources=amounts,
            completed=complete,
        )

    def void_alliance_treasury_requests(
        self, db: Connection, requester_id: str, alliance_id: str, *, actor_id: str, at: int
    ) -> None:
        for row in db.execute(
            "SELECT * FROM alliance_treasury_requests WHERE requester_id=? AND alliance_id=? "
            "AND status='pending' ORDER BY created,id",
            (requester_id, alliance_id),
        ).fetchall():
            alliance_treasury.release_request(
                db,
                dict(row),
                actor_id=actor_id,
                status="void_membership",
                at=at,
            )

    def decorate(self, db: Connection, state: dict[str, Any]) -> None:
        user, now = state["id"], int(time.time())
        state["server_time"] = now
        profile = self.profile(db, user)
        state["profile"] = {
            k: profile[k] for k in ("role", "joined", "faction", "muted_until", "verified")
        }
        state["profile"]["faction"] = (
            self.world_faction(db, user, int(state["world_id"])) or "pioneers"
        )
        state["profile"]["email"] = profile["email"]
        state["profile"]["mfa_enabled"] = bool(profile["totp"])
        state["profile"]["name_changed_at"] = int(profile.get("name_changed", 0))
        profile_settings = self.player_profile_settings(db, str(user))
        state["profile"]["public_profile_visibility"] = profile_settings["visibility"]
        state["profile"]["public_profile_title"] = profile_settings["title_id"]
        state["profile"]["public_profile_reward_title"] = profile_settings["reward_title_id"]
        state["profile"]["public_profile_skin"] = profile_settings["skin_id"]
        state["profile"]["public_profile_banner"] = profile_settings["banner_id"]
        state["profile"]["public_profile_badges"] = profile_settings["badge_ids"]
        from . import prestige

        state["prestige"] = prestige.view(db, str(user))
        state["profile_rules"] = {
            "version": player_profile.RULES["version"],
            "titles": player_profile.TITLES,
            "badges": player_profile.BADGES,
            "max_badges": player_profile.MAX_BADGES,
            "reward_titles": cosmetic_rewards.available_title_labels(db, str(user)),
            "skins": cosmetic_rewards.available_skin_labels(db, str(user)),
            "banners": cosmetic_rewards.available_banner_labels(db, str(user)),
        }
        state["map_bookmarks"] = [
            row[0]
            for row in db.execute(
                "SELECT target_id FROM map_bookmarks WHERE user_id=? AND world_id=? "
                "ORDER BY created,target_id",
                (user, int(state.get("world_id", 1))),
            )
        ]
        member = self.member(db, user)
        alliance = member["alliance_id"] if member else ""
        if member:
            world_id = int(state["world_id"])
            permissions = self.alliance_permissions(db, member)
            state["alliance_treasury_rules"] = alliance_treasury.RULES
            state["alliance_treasury_can_manage"] = (
                member["role"] == "leader" or "treasury" in permissions
            )
            balance_rows = {
                int(row["resource_index"]): row
                for row in db.execute(
                    "SELECT resource_index,available,reserved FROM alliance_treasury_balances "
                    "WHERE alliance_id=? AND world_id=?",
                    (alliance, world_id),
                )
            }
            state["alliance_treasury_balances"] = [
                {
                    "resource_index": index,
                    "available": (
                        int(balance_rows[index]["available"]) if index in balance_rows else 0
                    ),
                    "reserved": (
                        int(balance_rows[index]["reserved"]) if index in balance_rows else 0
                    ),
                }
                for index in range(3)
            ]
            state["alliance_treasury_requests"] = [
                dict(row)
                for row in db.execute(
                    "SELECT r.*,u.name AS requester_name,(SELECT count(DISTINCT ap.approver_id) "
                    "FROM alliance_treasury_approvals ap JOIN members m "
                    "ON m.user_id=ap.approver_id AND m.alliance_id=r.alliance_id "
                    "WHERE ap.request_id=r.id AND ap.approver_id<>r.requester_id AND "
                    "(m.role='leader' OR EXISTS (SELECT 1 FROM alliance_role_permissions p "
                    "WHERE p.alliance_id=m.alliance_id AND p.role=m.role AND p.permission='treasury'))) "
                    "AS approval_count FROM alliance_treasury_requests r "
                    "JOIN users u ON u.id=r.requester_id WHERE r.alliance_id=? AND r.world_id=? "
                    "ORDER BY r.created DESC,r.id DESC LIMIT 20",
                    (alliance, world_id),
                )
            ]
            state["alliance_treasury_ledger"] = [
                dict(row)
                for row in db.execute(
                    "SELECT l.*,u.name AS actor_name FROM alliance_treasury_ledger l "
                    "LEFT JOIN users u ON u.id=l.actor_id WHERE l.alliance_id=? AND l.world_id=? "
                    "ORDER BY l.created DESC,l.id DESC LIMIT 30",
                    (alliance, world_id),
                )
            ]
        else:
            state["alliance_treasury_rules"] = alliance_treasury.RULES
            state["alliance_treasury_can_manage"] = False
            state["alliance_treasury_balances"] = []
            state["alliance_treasury_requests"] = []
            state["alliance_treasury_ledger"] = []
        state["alliance_project_rules"] = alliance_projects.RULES
        state["alliance_project_can_manage"] = bool(
            member
            and (member["role"] == "leader" or "projects" in self.alliance_permissions(db, member))
        )
        state["alliance_projects"] = (
            [
                dict(row)
                for row in db.execute(
                    "SELECT p.*,u.name AS initiator_name FROM alliance_projects p "
                    "JOIN users u ON u.id=p.initiator_id WHERE p.alliance_id=? AND p.world_id=? "
                    "ORDER BY CASE WHEN p.status='active' THEN 0 ELSE 1 END,"
                    "p.created DESC,p.id DESC LIMIT 20",
                    (alliance, int(state["world_id"])),
                )
            ]
            if member
            else []
        )
        state["alliance_project_ledger"] = (
            [
                dict(row)
                for row in db.execute(
                    "SELECT l.*,u.name AS actor_name FROM alliance_project_ledger l "
                    "LEFT JOIN users u ON u.id=l.actor_id WHERE l.alliance_id=? AND l.world_id=? "
                    "ORDER BY l.created DESC,l.id DESC LIMIT 30",
                    (alliance, int(state["world_id"])),
                )
            ]
            if member
            else []
        )
        state["alliances"], state["alliances_has_more"] = self.alliance_directory_page(
            db, user_id=user
        )
        state["diplomacy_events"], state["diplomacy_events_has_more"] = self.diplomacy_events_page(
            db
        )
        state["alliance_wars"], state["alliance_war_events"] = self.alliance_wars_public_state(db)
        state["alliance_war_rules"] = {
            "version": alliance_war.VERSION,
            "target_points": alliance_war.TARGET_POINTS,
            "status": str(alliance_war.RULES["status"]),
        }
        state["membership"] = dict(member) if member else None
        state["shared_combat_report_keys"] = (
            {
                str(row["report_id"]): str(row["id"])
                for row in db.execute(
                    "SELECT report_id,id FROM alliance_shared_reports "
                    "WHERE owner_id=? AND alliance_id=? AND world_id=?",
                    (user, member["alliance_id"], int(state["world_id"])),
                )
            }
            if member
            else {}
        )
        if member:
            (
                state["alliance_shared_reports"],
                state["alliance_shared_reports_has_more"],
            ) = self.alliance_shared_report_page(
                db, user, str(member["alliance_id"]), int(state["world_id"])
            )
        else:
            state["alliance_shared_reports"] = []
            state["alliance_shared_reports_has_more"] = False
        home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (user, int(state["world_id"])),
        ).fetchone()
        state["alliance_garrison_home_colony_id"] = str(home["colony_id"]) if home else ""
        home_policy = (
            db.execute(
                "SELECT enabled,capacity,alliance_id FROM terra_allied_garrison_policies "
                "WHERE home_colony_id=? AND host_user_id=?",
                (home["colony_id"], user),
            ).fetchone()
            if home
            else None
        )
        state["alliance_garrison_policy"] = (
            dict(home_policy) if home_policy else {"enabled": False, "capacity": 300}
        )
        state["alliance_garrison_targets"] = []
        if member:
            for target_row in db.execute(
                "SELECT c.colony_id,c.user_id,c.state,p.capacity,u.name "
                "FROM terra_allied_garrison_policies p "
                "JOIN colonies c ON c.colony_id=p.home_colony_id "
                "JOIN users u ON u.id=c.user_id "
                "JOIN members m ON m.user_id=c.user_id "
                "WHERE p.enabled=TRUE AND p.alliance_id=? AND m.alliance_id=? "
                "AND c.world_id=? AND c.user_id<>? ORDER BY u.name,c.colony_id LIMIT 100",
                (
                    member["alliance_id"],
                    member["alliance_id"],
                    int(state["world_id"]),
                    user,
                ),
            ):
                target_state = json.loads(target_row["state"])
                state["alliance_garrison_targets"].append(
                    {
                        "colony_id": str(target_row["colony_id"]),
                        "name": str(target_state.get("colony_name", target_state["name"])),
                        "host_name": str(target_row["name"]),
                        "capacity": int(target_row["capacity"]),
                    }
                )
        state["alliance_garrisons"] = []
        for garrison in db.execute(
            "SELECT g.*,host.name AS host_name,contributor.name AS contributor_name "
            "FROM terra_allied_garrisons g "
            "JOIN users host ON host.id=g.host_user_id "
            "JOIN users contributor ON contributor.id=g.contributor_id "
            "WHERE g.host_user_id=? OR g.contributor_id=? ORDER BY g.created,g.id LIMIT 100",
            (user, user),
        ):
            state["alliance_garrisons"].append(
                {
                    "id": str(garrison["id"]),
                    "host_user": str(garrison["host_user_id"]),
                    "contributor": str(garrison["contributor_id"]),
                    "host_name": str(garrison["host_name"]),
                    "contributor_name": str(garrison["contributor_name"]),
                    "army": json.loads(garrison["army"]),
                    "status": str(garrison["status"]),
                    "can_recall": str(garrison["status"]) == "active",
                }
            )
        state["terra_alliance_attacks"] = []
        if member:
            for row in db.execute(
                "SELECT a.*,u.name AS leader_name, "
                "(SELECT count(*) FROM terra_alliance_attack_wings w "
                "WHERE w.attack_id=a.id AND w.status='active') AS participant_count, "
                "EXISTS(SELECT 1 FROM terra_alliance_attack_wings mine "
                "WHERE mine.attack_id=a.id AND mine.user_id=? AND mine.status='active') AS joined "
                "FROM terra_alliance_attacks a JOIN users u ON u.id=a.leader_id "
                "WHERE a.alliance_id=? AND a.world_id=? AND a.status='assembling' "
                "AND a.join_until>? ORDER BY a.join_until,a.id LIMIT 20",
                (user, alliance, int(state["world_id"]), now),
            ):
                attack = dict(row)
                if attack["target_kind"] == "outpost":
                    target = next(
                        (
                            post
                            for post in self.game.world_outposts(db, int(state["world_id"]))
                            if post["id"] == attack["target_id"]
                        ),
                        None,
                    )
                    attack["target_name"] = target["name"] if target else "Ziel nicht verfügbar"
                    attack["x"] = int(target["x"]) if target else None
                    attack["y"] = int(target["y"]) if target else None
                else:
                    target_row = db.execute(
                        "SELECT c.x,c.y,u.name FROM colonies c JOIN users u ON u.id=c.user_id "
                        "WHERE c.user_id=? AND c.world_id=? AND c.is_home=TRUE",
                        (attack["target_id"], int(state["world_id"])),
                    ).fetchone()
                    attack["target_name"] = (
                        target_row["name"] if target_row else "Ziel nicht verfügbar"
                    )
                    attack["x"] = int(target_row["x"]) if target_row else None
                    attack["y"] = int(target_row["y"]) if target_row else None
                attack["joined"] = bool(attack["joined"])
                state["terra_alliance_attacks"].append(attack)
            state["alliance_bulletins"], state["alliance_bulletins_has_more"] = (
                self.alliance_bulletin_page(db, str(alliance))
            )
            state["alliance_forum"], state["alliance_forum_has_more"] = self.alliance_forum_page(
                db, str(alliance)
            )
            (
                state["alliance_forum_reports"],
                state["alliance_forum_reports_has_more"],
            ) = self.alliance_forum_reports_page(
                db,
                user,
                str(alliance),
                member["role"] == "leader"
                or "forum_moderation" in self.alliance_permissions(db, member),
            )
            state["alliance_permissions"] = self.alliance_permissions(db, member)
            state["alliance_permission_catalog"] = [
                {"id": permission, "label": ALLIANCE_PERMISSION_LABELS[permission]}
                for permission in ALLIANCE_PERMISSIONS
            ]
            state["alliance_role_permissions"] = (
                {
                    role: [
                        str(row["permission"])
                        for row in db.execute(
                            "SELECT permission FROM alliance_role_permissions "
                            "WHERE alliance_id=? AND role=? ORDER BY permission",
                            (alliance, role),
                        )
                    ]
                    for role in ("officer", "member")
                }
                if member["role"] == "leader"
                else {}
            )
            transfer = db.execute(
                "SELECT r.id,r.alliance_id,r.leader_id,r.successor_id,r.created,"
                "leader.name AS leader_name,successor.name AS successor_name "
                "FROM alliance_transfer_requests r "
                "JOIN users leader ON leader.id=r.leader_id "
                "JOIN users successor ON successor.id=r.successor_id "
                "WHERE r.alliance_id=? AND (r.leader_id=? OR r.successor_id=?)",
                (alliance, user, user),
            ).fetchone()
            state["alliance_transfer_request"] = dict(transfer) if transfer else None
        else:
            state["alliance_bulletins"], state["alliance_bulletins_has_more"] = [], False
            state["alliance_forum"], state["alliance_forum_has_more"] = [], False
            state["alliance_forum_reports"] = []
            state["alliance_forum_reports_has_more"] = False
            state["alliance_permissions"] = []
            state["alliance_permission_catalog"] = []
            state["alliance_role_permissions"] = {}
            state["alliance_transfer_request"] = None
        (
            state["alliance_supply_targets"],
            state["alliance_supply_targets_has_more"],
        ) = (
            self.alliance_supply_target_page(db, user, str(alliance), int(state.get("world_id", 1)))
            if member
            else ([], False)
        )
        state["members"], state["members_has_more"] = (
            self.alliance_member_page(db, str(alliance)) if alliance else ([], False)
        )
        state["invites"], state["invites_has_more"] = self.alliance_invitation_page(
            db, user, "incoming"
        )
        state["alliance_applications"], state["alliance_applications_has_more"] = (
            self.alliance_application_page(db, user, "outgoing")
        )
        (
            state["alliance_incoming_applications"],
            state["alliance_incoming_applications_has_more"],
        ) = (
            self.alliance_application_page(db, user, "incoming", str(alliance))
            if member
            and (
                member["role"] == "leader"
                or "applications" in self.alliance_permissions(db, member)
            )
            else ([], False)
        )
        state["alliance_outgoing_invites"], state["alliance_outgoing_invites_has_more"] = (
            self.alliance_invitation_page(db, user, "outgoing", str(alliance))
            if member
            and (
                member["role"] == "leader" or "invitations" in self.alliance_permissions(db, member)
            )
            else ([], False)
        )
        state["messages"] = [
            dict(r)
            for r in db.execute(
                "SELECT m.id,m.sender,u.name,m.channel,m.recipient,m.body,m.created FROM messages m "
                "JOIN users u ON u.id=m.sender WHERE m.hidden=0 AND "
                "((m.channel='world' AND m.world_id=?) OR "
                "(m.channel='alliance' AND m.recipient=?) OR "
                "(m.channel='private' AND (m.recipient=? OR m.sender=?))) "
                "ORDER BY m.created DESC,m.id DESC LIMIT 100",
                (int(state.get("world_id", 1)), alliance, user, user),
            )
        ]
        from . import game_events

        state["notification_preferences"] = {
            category: muted
            for category, muted in game_events.page(db, user, int(state.get("world_id", 1)), None)[
                "preferences"
            ].items()
        }
        state["announcements"], state["announcements_has_more"] = self.system_announcement_page(
            db,
            int(state.get("world_id", 1)),
            now=int(state.get("server_time", 0) or time.time()),
            include_scheduled=state.get("profile", {}).get("role") in ("admin", "moderator"),
        )
        state["system_mail"], state["system_mail_has_more"] = self.system_mail_page(db, user)
        state["moderation_cases"] = [
            dict(row)
            for row in db.execute(
                "SELECT id,case_type,message_id,status,resolution,created FROM moderation_cases "
                "WHERE reporter_id=? ORDER BY created DESC,id DESC LIMIT 50",
                (user,),
            )
        ]
        state["moderation_cases"].extend(
            {
                "id": str(row["id"]),
                "case_type": "account_ban_appeal",
                "message_id": None,
                "status": str(row["status"]),
                "resolution": row["resolution"],
                "created": int(row["created"]),
            }
            for row in db.execute(
                "SELECT id,status,resolution,created FROM account_ban_appeals "
                "WHERE user_id=? ORDER BY created DESC,id DESC LIMIT 50",
                (user,),
            )
        )
        state["moderation_cases"].sort(
            key=lambda item: (int(item["created"]), str(item["id"])), reverse=True
        )
        state["moderation_cases"] = state["moderation_cases"][:50]
        state["message_has_more"] = {
            channel: self.message_page(
                db,
                user,
                int(state.get("world_id", 1)),
                str(alliance),
                channel,
            )[1]
            for channel in ("world", "alliance", "private")
        }
        state["social"] = self.social_state(db, user)
        state["notes"], state["notes_has_more"] = self.notes_state(
            db, user, int(state.get("world_id", 1))
        )
        state["offers"], state["offers_has_more"] = self.market_offer_page(
            db, int(state.get("world_id", 1)), now
        )
        state["market_history"] = self.market_history(db, now, int(state.get("world_id", 1)))
        state["players"], state["players_has_more"] = self.player_directory_page(
            db,
            user,
            int(state.get("world_id", 1)),
            now,
            state.get("_travel_times", {}),
            page_size=400,
        )
        (
            state["alliance_candidates"],
            state["alliance_candidates_has_more"],
        ) = self.alliance_candidate_page(db, user, str(alliance), int(state.get("world_id", 1)))
        state["events"], state["events_has_more"] = self.live_event_page(
            db, now, world_id=int(state["world_id"])
        )
        state["seasons"] = [
            dict(r)
            for r in db.execute(
                "SELECT s.*,r.version AS rules_version,r.digest AS rules_digest,r.source AS rules_source "
                "FROM seasons s LEFT JOIN season_rules r ON r.season_id=s.id "
                "WHERE s.world_id=? ORDER BY s.starts DESC,s.id DESC LIMIT 10",
                (state["world_id"],),
            )
        ]
        for season in state["seasons"]:
            season["awards"] = [
                dict(row)
                for row in db.execute(
                    "SELECT a.user_id AS id,u.name,a.award,a.score,a.created "
                    "FROM season_awards a JOIN users u ON u.id=a.user_id "
                    "WHERE a.season_id=? ORDER BY a.award,a.score DESC,a.user_id",
                    (season["id"],),
                )
            ]
            snapshot = db.execute(
                "SELECT rules_version,rules_digest,eligibility_policy FROM "
                "season_alliance_snapshots WHERE season_id=?",
                (season["id"],),
            ).fetchone()
            season["alliance_rules_version"] = str(snapshot["rules_version"]) if snapshot else None
            season["alliance_rules_digest"] = str(snapshot["rules_digest"]) if snapshot else None
            season["alliance_eligibility_policy"] = (
                str(snapshot["eligibility_policy"]) if snapshot else None
            )
            season["alliance_standings"] = [
                dict(row)
                for row in db.execute(
                    "SELECT alliance_id,alliance_name,alliance_tag,score,rank,eligible_accounts "
                    "FROM season_alliance_standings WHERE season_id=? ORDER BY rank",
                    (season["id"],),
                )
            ]
            season["ranking_rules_version"] = None
            season["ranking_rules_digest"] = None
            ranking_snapshot = db.execute(
                "SELECT rules_version,rules_digest FROM season_ranking_snapshots "
                "WHERE season_id=?",
                (season["id"],),
            ).fetchone()
            if ranking_snapshot:
                season["ranking_rules_version"] = str(ranking_snapshot["rules_version"])
                season["ranking_rules_digest"] = str(ranking_snapshot["rules_digest"])
            season["category_standings"] = [
                dict(row)
                for row in db.execute(
                    "SELECT category,user_id,display_name,score,rank "
                    "FROM season_ranking_standings WHERE season_id=? "
                    "ORDER BY category,rank LIMIT 500",
                    (season["id"],),
                )
            ]
        state["hall_of_fame"] = self.hall_of_fame(db, state)
        state["flags"] = {
            r["name"]: r["value"] == "true"
            for r in db.execute(
                "SELECT * FROM flags WHERE name IN ('pvp','registration','maintenance')"
            )
        }
        state["reserve"] = state.get("reserve", [0, 0, 0])
        state["world_pvp_enabled"] = self.pvp_enabled(db, state["world_id"])
        state["rules_version"] = "FUR-2"
        active_events = [
            dict(row)
            for row in db.execute(
                "SELECT starts,ends,bonus,end_starts,end_bonus FROM events "
                "WHERE world_id=? AND starts<=? AND ends>?",
                (state["world_id"], now, now),
            )
        ]
        event_bonus = live_events.active_bonus_total(active_events, now)
        commander_bonus = (
            2 * int(state.get("commander", {}).get("stats", {}).get("economy", 0))
            if state.get("commander", {}).get("enabled")
            else 0
        )
        state["production"] = [
            (
                (2 + state["buildings"][k] * 2)
                * (
                    100
                    + 15 * state["tech"]["engineering"]
                    + event_bonus
                    + state["captures"] * 5
                    + state.get("_region_bonus", 0)
                    + state.get("_faction_bonus", 0)
                    + commander_bonus
                    + (state.get("terra_energy", {}).get("ore_bonus", 0) if k == "ore" else 0)
                    + (
                        5
                        if k == "wood" and "adaptive_forestry" in state.get("faction_research", [])
                        else 0
                    )
                )
                if state.get("vacation_until", 0) <= now and not state.get("terra_dormant")
                else 0
            )
            for k in ("wood", "stone", "ore")
        ]
        state["regional_production_bonus"] = state.get("_region_bonus", 0)
        terrain_rates = PRODUCTION_PERCENT[state["terrain"]]
        state["production_details"] = []
        storage_cap = 2000 + state["buildings"]["storage"] * 2000
        paused = state.get("vacation_until", 0) > now or bool(state.get("terra_dormant"))
        for index, key in enumerate(("wood", "stone", "ore")):
            base_rate = 2 + state["buildings"][key] * 2
            bonus_percent = (
                15 * state["tech"]["engineering"]
                + event_bonus
                + state["captures"] * 5
                + state.get("_region_bonus", 0)
                + state.get("_faction_bonus", 0)
                + commander_bonus
                + (state.get("terra_energy", {}).get("ore_bonus", 0) if key == "ore" else 0)
                + (
                    5
                    if key == "wood" and "adaptive_forestry" in state.get("faction_research", [])
                    else 0
                )
            )
            effective_rate = base_rate * (100 + bonus_percent) * terrain_rates[index]
            if paused:
                effective_rate = 0
            deficit = max(0, storage_cap - state["resources"][index])
            carry = (
                state.get("carry", [0, 0, 0])[index] * 100
                + state.get("carry_sub", [0, 0, 0])[index]
            )
            seconds_to_cap = (
                (max(0, deficit * 10_000 - carry) + effective_rate - 1) // effective_rate
                if effective_rate > 0
                else None
            )
            state["production_details"].append(
                {
                    "resource": key,
                    "base_per_second": base_rate,
                    "bonus_percent": bonus_percent,
                    "terrain_percent": terrain_rates[index],
                    "terrain": TERRAIN_LABELS[state["terrain"]],
                    "per_second_hundredths": effective_rate // 100,
                    "per_second_ten_thousandths": effective_rate,
                    "storage": state["resources"][index],
                    "storage_cap": storage_cap,
                    "seconds_to_cap": seconds_to_cap,
                    "paused": paused,
                }
            )
        incoming = db.execute(
            "SELECT COUNT(*) FROM incoming_attack_index WHERE target_user=?", (user,)
        ).fetchone()
        state["incoming_count"] = int(incoming[0]) if incoming else 0
        if profile["role"] in ("admin", "moderator"):
            admin_users, admin_users_has_more = self.admin_user_page(db)
            admin_failures, admin_failures_has_more = self.admin_failure_page(db)
            admin_audit, admin_audit_has_more = self.admin_audit_page(db)
            admin_cases, admin_cases_has_more = self.moderation_case_page(db)
            state["administration"] = {
                "audit": admin_audit,
                "audit_has_more": admin_audit_has_more,
                "cases": admin_cases,
                "cases_has_more": admin_cases_has_more,
                "failures": admin_failures,
                "failures_has_more": admin_failures_has_more,
                "failure_total": int(db.execute("SELECT count(*) FROM job_failures").fetchone()[0]),
                "users": admin_users,
                "users_has_more": admin_users_has_more,
                "worker": (
                    dict(r)
                    if (r := db.execute("SELECT * FROM worker_status WHERE id=1").fetchone())
                    else None
                ),
            }

    def active_warden_fortification(self, db: Connection, state: dict[str, Any], at: int) -> bool:
        effect = state.get("warden_fortification", {})
        if not effect.get("starts", 0) <= at < effect.get("ends", 0):
            return False
        return bool(
            db.execute(
                "SELECT COUNT(*) FROM members WHERE user_id IN (?,?) AND alliance_id=?",
                (state["id"], effect["owner"], effect["alliance_id"]),
            ).fetchone()[0]
            == 2
        )

    def fortified_player_defense(
        self, db: Connection, state: dict[str, Any], faction: str, at: int
    ) -> int:
        from .game import UNITS

        defense = self.player_defense(state, faction)
        for garrison in self.active_allied_garrisons(db, state):
            army = json.loads(garrison["army"])
            power = sum(UNITS[unit]["power"] * count for unit, count in army.items())
            power = power * (100 + 15 * int(garrison["tactics"])) // 100
            defense += defense_with_terrain(power, str(state.get("terrain", "plain")))
        return defense * 110 // 100 if self.active_warden_fortification(db, state, at) else defense

    def active_allied_garrisons(self, db: Connection, state: dict[str, Any]) -> list[Any]:
        """Return only live, same-world garrisons still covered by explicit consent."""
        host_id = str(state.get("id", ""))
        colony_id = str(state.get("colony_id", ""))
        world_id = int(state.get("world_id", 1))
        host_member = self.member(db, host_id)
        if not host_member:
            return []
        rows = db.execute(
            "SELECT g.* FROM terra_allied_garrisons g "
            "JOIN terra_allied_garrison_policies p ON p.home_colony_id=g.host_colony_id "
            "JOIN members contributor ON contributor.user_id=g.contributor_id "
            "JOIN members host ON host.user_id=g.host_user_id "
            "WHERE g.host_colony_id=? AND g.world_id=? AND g.alliance_id=? "
            "AND g.status='active' AND p.enabled=TRUE AND p.alliance_id=g.alliance_id "
            "AND contributor.alliance_id=g.alliance_id AND host.alliance_id=g.alliance_id "
            "ORDER BY g.id",
            (colony_id, world_id, host_member["alliance_id"]),
        ).fetchall()
        return list(rows)

    def apply_allied_garrison_losses(
        self,
        db: Connection,
        state: dict[str, Any],
        *,
        attack_power: int,
        defense_power: int,
        victory: bool,
        at: int,
    ) -> list[dict[str, Any]]:
        """Apply the same deterministic defender casualty fraction per owned army."""
        rows = self.active_allied_garrisons(db, state)
        loss_percent = 100 if victory else min(100, attack_power * 70 // max(1, defense_power))
        results: list[dict[str, Any]] = []
        for row in rows:
            army = json.loads(row["army"])
            survivors = {
                unit: max(0, count - (count * loss_percent + 99) // 100)
                for unit, count in army.items()
            }
            losses = {
                unit: army.get(unit, 0) - survivors.get(unit, 0)
                for unit in army
                if army.get(unit, 0) != survivors.get(unit, 0)
            }
            if not losses:
                continue
            if sum(survivors.values()):
                db.execute(
                    "UPDATE terra_allied_garrisons SET army=? WHERE id=? AND status='active'",
                    (json.dumps(survivors, sort_keys=True), row["id"]),
                )
            else:
                db.execute(
                    "DELETE FROM terra_allied_garrisons WHERE id=? AND status='active'",
                    (row["id"],),
                )
            contributor_state = self.game.read_colony(db, str(row["source_colony_id"]))
            self.game.report(
                contributor_state,
                "Alliierte Garnison im Kampf",
                f"Bei der Verteidigung von {state['name']} gingen "
                f"{sum(losses.values())} deiner Einheiten verloren.",
            )
            self.game.save(db, contributor_state)
            results.append(
                {
                    "garrison_id": str(row["id"]),
                    "contributor": str(row["contributor_id"]),
                    "losses": losses,
                }
            )
            self.audit(
                db,
                str(row["contributor_id"]),
                "alliance_garrison_combat_losses",
                str(row["id"]),
                host=str(state["colony_id"]),
                losses=losses,
                loss_percent=loss_percent,
                at=at,
            )
        return results

    def apply_allied_garrison_casualties(
        self,
        db: Connection,
        state: dict[str, Any],
        garrisons: list[Any],
        losses: dict[str, int],
        *,
        at: int,
        rule_version: str = "FUR-3-TERRA-COMBAT-1",
    ) -> tuple[dict[str, int], list[dict[str, Any]]]:
        """Split actual FUR-3 per-unit casualties proportionally between troop owners."""
        owners: dict[str, dict[str, int]] = {"!host": dict(state["units"])}
        for row in garrisons:
            owners[str(row["id"])] = json.loads(row["army"])
        allocated: dict[str, dict[str, int]] = {owner: {} for owner in owners}
        for unit, loss in losses.items():
            total = sum(army.get(unit, 0) for army in owners.values())
            if type(loss) is not int or loss < 0 or loss > total:
                self.error("FUR-3 casualty count does not match the defender roster.")
            if not total:
                continue
            quotas = {owner: (army.get(unit, 0) * loss) // total for owner, army in owners.items()}
            remainders = {
                owner: (army.get(unit, 0) * loss) % total for owner, army in owners.items()
            }
            remaining = loss - sum(quotas.values())
            for owner in sorted(owners, key=lambda key: (-remainders[key], key))[:remaining]:
                quotas[owner] += 1
            for owner, amount in quotas.items():
                if amount:
                    allocated[owner][unit] = amount

        host_survivors = dict(state["units"])
        results: list[dict[str, Any]] = []
        for row in garrisons:
            owner = str(row["id"])
            army = owners[owner]
            casualties = allocated[owner]
            survivors = {
                unit: amount - casualties.get(unit, 0)
                for unit, amount in army.items()
                if amount - casualties.get(unit, 0) > 0
            }
            if casualties:
                if survivors:
                    db.execute(
                        "UPDATE terra_allied_garrisons SET army=? WHERE id=? AND status='active'",
                        (json.dumps(survivors, sort_keys=True), owner),
                    )
                else:
                    db.execute(
                        "DELETE FROM terra_allied_garrisons WHERE id=? AND status='active'",
                        (owner,),
                    )
                contributor = str(row["contributor_id"])
                contributor_state = self.game.read_colony(db, str(row["source_colony_id"]))
                self.game.report(
                    contributor_state,
                    "Alliierte Garnison im Kampf",
                    f"Bei der Verteidigung von {state['name']} gingen "
                    f"{sum(casualties.values())} deiner Einheiten verloren.",
                )
                self.game.save(db, contributor_state)
                results.append(
                    {"garrison_id": owner, "contributor": contributor, "losses": casualties}
                )
                self.audit(
                    db,
                    contributor,
                    "alliance_garrison_combat_losses",
                    owner,
                    host=str(state["colony_id"]),
                    losses=casualties,
                    rule=rule_version,
                    at=at,
                )
        for unit, host_loss in allocated["!host"].items():
            host_survivors[unit] = max(0, host_survivors.get(unit, 0) - host_loss)
        return host_survivors, results

    def player_defense(self, state: dict[str, Any], faction: str) -> int:
        from .game import UNITS

        army = sum(UNITS[key]["power"] * count for key, count in state["units"].items())
        army = army * (100 + 15 * state["tech"]["tactics"]) // 100
        wall = state["buildings"]["wall"] * 120
        if state.get("faction_chosen") and faction == "wardens":
            research = state.get("faction_research", [])
            wall = wall * (150 if "bastion_protocol" in research else 140) // 100
            if wall and "kinetic_shield" in research:
                army = army * 105 // 100
        defense = int(army + wall + 50)
        return defense_with_terrain(defense, str(state.get("terrain", "plain")))
