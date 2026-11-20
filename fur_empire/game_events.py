"""Transactional game-event outbox and private, replayable event feed."""

import sqlite3
from typing import Any

import psycopg

from .database import Connection

BATCH_SIZE = 200
PAGE_SIZE = 50
CATEGORIES = ("economy", "research", "military", "social", "system")


def category_for(kind: str) -> str:
    if kind in {
        "build",
        "trade",
        "goods_trade",
        "craft_start",
        "craft_completed",
        "craft_cancelled",
        "item_recycle",
        "market_create",
        "market_accept",
        "market_cancel",
        "alliance_treasury_donate",
        "alliance_treasury_request",
        "alliance_treasury_approve",
        "alliance_treasury_decline",
        "alliance_treasury_cancel",
        "alliance_project_contribute",
        "alliance_project_create",
        "alliance_project_cancel",
        "colonize",
        "reserve_claim",
        "terra_energy_build",
        "terra_fusion_supply",
        "terra_route_create",
        "terra_route_resume",
        "terra_route_stop",
        "orbit_build",
        "orbit_import_ore",
        "orbit_export_ore",
        "orbit_collect_reserve",
        "orbit_salvage",
    }:
        return "economy"
    if kind in {
        "research",
        "orbit_research_shipbuilding",
        "terra_faction_research",
        "terra_pioneer_survey",
    }:
        return "research"
    if kind in {
        "train",
        "terra_repair_units",
        "terra_defense_build",
        "terra_defense_repair",
        "raid",
        "orbit_colonize",
        "outpost_colonize",
        "orbit_build_ships",
        "orbit_repair_wrecks",
        "orbit_build_defense",
        "orbit_build_ammunition",
        "orbit_station_build",
        "orbit_station_upkeep",
        "orbit_station_deploy",
        "orbit_station_withdraw",
        "orbit_build_jumpgate",
        "orbit_jump",
        "orbit_transport",
        "orbit_recall_transport",
        "orbit_scout",
        "orbit_expedition",
        "orbit_build_scanner",
        "orbit_phalanx_scan",
        "orbit_attack",
        "orbit_destroy_moon",
        "orbit_alliance_attack",
        "orbit_join_attack",
        "orbit_recall_attack",
        "orbit_fleet_supply",
        "expedition",
        "ruin_exploration",
        "terra_boss_attack",
        "terra_boss_claim",
        "attack",
        "transport",
        "scout",
        "mission_recall",
        "colony_supply",
        "station",
        "recall",
        "alliance_send_supply",
        "alliance_supply_cancel",
        "alliance_garrison_station",
        "alliance_garrison_recall",
        "alliance_attack_create",
        "alliance_attack_join",
        "alliance_attack_withdraw",
        "alliance_attack_cancel",
        "terra_warden_fortify",
        "market_protected_convoy",
        "gateway_cargo_arrived",
    }:
        return "military"
    if kind.startswith(
        ("alliance_", "friend_", "player_block", "player_unblock", "message")
    ) or kind in {
        "diplomacy",
        "report_share",
        "report_unshare",
        "note_save",
        "note_delete",
        "alliance_garrison_policy",
    }:
        return "social"
    if kind.startswith("admin_") or kind in {
        "vacation",
        "mail_read",
        "profile_settings_update",
        "notification_preference",
        "world_create",
        "world_update",
        "world_join",
        "world_select",
        "colony_select",
        "colony_home",
        "colony_rename",
        "colony_abandon",
        "map_bookmark_add",
        "map_bookmark_remove",
        "faction",
        "quest",
        "cancel_job",
        "queue_move",
        "colony_relocate",
        "terra_reactivate",
        "terra_prestige",
        "admin_case_resolve",
        "player_block",
        "player_unblock",
        "orbit_unlock",
        "orbit_save_fleet_template",
        "orbit_save_shipyard_template",
        "orbit_delete_template",
        "admin_enable_terra_prestige",
        "admin_terra_sector",
        "admin_orbit_event",
        "admin_hide",
        "admin_flag",
        "admin_event",
        "admin_season",
        "admin_retry",
    }:
        return "system"
    return "system"


def muted(db: Connection, user: str, kind: str) -> bool:
    row = db.execute(
        "SELECT muted FROM game_event_preferences WHERE user_id=? AND category=?",
        (user, category_for(kind)),
    ).fetchone()
    return bool(row["muted"]) if row else False


def stage(db: Connection, event: str, recipient: str, world: int, kind: str, now: int) -> None:
    db.execute(
        "INSERT INTO game_event_outbox(id,recipient,world_id,kind,created) VALUES (?,?,?,?,?)",
        (event, recipient, world, kind, now),
    )


def publish(db: Connection) -> None:
    events = db.execute(
        "SELECT id,recipient,world_id,kind,created FROM game_event_outbox ORDER BY created,id LIMIT ?",
        (BATCH_SIZE,),
    ).fetchall()
    for event in events:
        try:
            if not muted(db, event["recipient"], event["kind"]):
                db.execute(
                    "INSERT INTO game_events(id,recipient,world_id,kind,created) VALUES (?,?,?,?,?) "
                    "ON CONFLICT(id) DO NOTHING",
                    tuple(event[key] for key in ("id", "recipient", "world_id", "kind", "created")),
                )
            db.execute("DELETE FROM game_event_outbox WHERE id=?", (event["id"],))
            db.execute("DELETE FROM game_event_delivery_failures WHERE id=?", (event["id"],))
        except (sqlite3.Error, psycopg.Error, OSError, ValueError, RuntimeError):
            attempts = db.execute(
                "SELECT attempts FROM game_event_delivery_failures WHERE id=?", (event["id"],)
            ).fetchone()
            count = int(attempts["attempts"]) + 1 if attempts else 1
            db.execute(
                "INSERT INTO game_event_delivery_failures(id,recipient,world_id,kind,attempts,failed_at) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "attempts=excluded.attempts,failed_at=excluded.failed_at",
                (
                    event["id"],
                    event["recipient"],
                    event["world_id"],
                    event["kind"],
                    count,
                    event["created"],
                ),
            )
            if count >= 5:
                db.execute("DELETE FROM game_event_outbox WHERE id=?", (event["id"],))

    from . import web_push

    web_push.enqueue_pending_events(db, BATCH_SIZE)


def page(
    db: Connection,
    user: str,
    world: int,
    before: int | None,
    category: str | None = None,
) -> dict[str, Any]:
    if category is not None and category not in CATEGORIES:
        raise ValueError("Unknown game-event category")
    matches: list[dict[str, Any]] = []
    scan_before = before
    exhausted = False
    while len(matches) <= PAGE_SIZE and not exhausted:
        if scan_before is None:
            batch = db.execute(
                "SELECT sequence,id,kind,created FROM game_events WHERE recipient=? AND world_id=? "
                "ORDER BY sequence DESC LIMIT ?",
                (user, world, BATCH_SIZE),
            ).fetchall()
        else:
            batch = db.execute(
                "SELECT sequence,id,kind,created FROM game_events WHERE recipient=? AND world_id=? "
                "AND sequence<? ORDER BY sequence DESC LIMIT ?",
                (user, world, scan_before, BATCH_SIZE),
            ).fetchall()
        exhausted = len(batch) < BATCH_SIZE
        if batch:
            scan_before = int(batch[-1]["sequence"])
        matches.extend(
            dict(row) for row in batch if category is None or category_for(row["kind"]) == category
        )
    has_more = len(matches) > PAGE_SIZE
    selected = matches[:PAGE_SIZE]
    ordered = list(reversed(selected))
    entries = [{**event, "category": category_for(event["kind"])} for event in ordered]
    failures = db.execute(
        "SELECT id,kind,attempts,failed_at FROM game_event_delivery_failures "
        "WHERE recipient=? AND world_id=? ORDER BY failed_at DESC,id DESC LIMIT ?",
        (user, world, PAGE_SIZE),
    ).fetchall()
    failure_entries = [
        {**dict(row), "category": category_for(row["kind"])}
        for row in failures
        if category is None or category_for(row["kind"]) == category
    ]
    preferences = {category: False for category in CATEGORIES}
    for row in db.execute(
        "SELECT category,muted FROM game_event_preferences WHERE user_id=?", (user,)
    ):
        preferences[row["category"]] = bool(row["muted"])
    return {
        "events": entries,
        "cursor": int(selected[-1]["sequence"]) if selected else before,
        "has_more": has_more,
        "preferences": preferences,
        "delivery_failures": failure_entries,
    }
