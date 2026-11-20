"""Versioned command contract. Pydantic validation rejects coercion and extra fields."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Action = Literal[
    "build",
    "research",
    "train",
    "terra_repair_units",
    "raid",
    "quest",
    "trade",
    "goods_trade",
    "craft_start",
    "item_recycle",
    "hero_allocate",
    "hero_respec",
    "orbit_unlock",
    "orbit_colonize",
    "orbit_build",
    "orbit_research_shipbuilding",
    "orbit_build_ships",
    "orbit_repair_wrecks",
    "orbit_import_ore",
    "orbit_export_ore",
    "colony_relocate",
    "terra_reactivate",
    "terra_energy_build",
    "terra_fusion_supply",
    "terra_prestige",
    "terra_route_create",
    "terra_route_resume",
    "terra_route_stop",
    "terra_faction_research",
    "terra_pioneer_survey",
    "terra_warden_fortify",
    "market_protected_convoy",
    "admin_enable_terra_prestige",
    "admin_terra_sector",
    "orbit_build_defense",
    "orbit_build_ammunition",
    "orbit_station_build",
    "orbit_station_upkeep",
    "orbit_station_deploy",
    "orbit_station_withdraw",
    "orbit_build_jumpgate",
    "orbit_jump",
    "orbit_transport",
    "orbit_collect_reserve",
    "orbit_recall_transport",
    "orbit_salvage",
    "orbit_scout",
    "orbit_expedition",
    "admin_orbit_event",
    "orbit_build_scanner",
    "orbit_phalanx_scan",
    "orbit_attack",
    "orbit_destroy_moon",
    "orbit_alliance_attack",
    "orbit_join_attack",
    "orbit_recall_attack",
    "orbit_save_fleet_template",
    "orbit_save_shipyard_template",
    "orbit_delete_template",
    "orbit_fleet_supply",
    "cancel_job",
    "queue_move",
    "expedition",
    "ruin_exploration",
    "admin_terra_boss_schedule",
    "admin_npc_invasion_schedule",
    "admin_recurring_quests",
    "admin_npc_convoy_schedule",
    "npc_convoy_escort",
    "npc_convoy_raid",
    "npc_convoy_recall",
    "npc_convoy_claim",
    "recurring_quest_claim",
    "terra_boss_attack",
    "terra_boss_claim",
    "alliance_send_supply",
    "alliance_supply_cancel",
    "alliance_garrison_policy",
    "alliance_garrison_station",
    "alliance_garrison_recall",
    "alliance_attack_create",
    "alliance_attack_join",
    "alliance_attack_withdraw",
    "alliance_attack_cancel",
    "alliance_create",
    "alliance_accept",
    "alliance_apply",
    "alliance_application_withdraw",
    "alliance_application_accept",
    "alliance_application_reject",
    "alliance_invite_decline",
    "alliance_invite_cancel",
    "alliance_leave",
    "alliance_edit",
    "alliance_invite",
    "alliance_kick",
    "alliance_role",
    "alliance_permissions_update",
    "alliance_transfer",
    "alliance_transfer_accept",
    "alliance_transfer_decline",
    "alliance_transfer_cancel",
    "alliance_peace_offer",
    "alliance_peace_accept",
    "alliance_peace_decline",
    "alliance_peace_cancel",
    "alliance_treasury_donate",
    "alliance_treasury_request",
    "alliance_treasury_approve",
    "alliance_treasury_decline",
    "alliance_treasury_cancel",
    "alliance_project_create",
    "alliance_project_contribute",
    "alliance_project_cancel",
    "alliance_bulletin_create",
    "alliance_bulletin_update",
    "alliance_bulletin_archive",
    "alliance_forum_thread_create",
    "alliance_forum_reply",
    "alliance_forum_thread_edit",
    "alliance_forum_post_edit",
    "alliance_forum_archive",
    "alliance_forum_report",
    "alliance_forum_report_resolve",
    "diplomacy",
    "message",
    "message_report",
    "mute_appeal",
    "mail_read",
    "notification_preference",
    "admin_case_resolve",
    "admin_announcement_create",
    "admin_announcement_archive",
    "admin_rule_rollout_schedule",
    "admin_rule_rollout_cancel",
    "admin_mail_send",
    "friend_request",
    "friend_accept",
    "friend_decline",
    "friend_cancel",
    "friend_remove",
    "player_block",
    "player_unblock",
    "profile_settings_update",
    "note_save",
    "note_delete",
    "report_share",
    "report_unshare",
    "market_create",
    "market_accept",
    "market_cancel",
    "attack",
    "transport",
    "scout",
    "mission_recall",
    "colony_supply",
    "station",
    "recall",
    "reserve_claim",
    "world_create",
    "world_update",
    "world_join",
    "world_select",
    "colony_select",
    "colony_home",
    "colony_rename",
    "colony_abandon",
    "outpost_colonize",
    "colonize",
    "map_bookmark_add",
    "map_bookmark_remove",
    "faction",
    "vacation",
    "admin_ban",
    "admin_mute",
    "admin_hide",
    "admin_flag",
    "admin_event",
    "admin_season",
    "admin_retry",
]


class Payload(BaseModel):
    mode: Literal["permanent", "season", "sandbox"] = "permanent"
    terra_combat_ruleset: (
        Literal[
            "FUR-2",
            "FUR-3-TERRA-COMBAT-1",
            "FUR-3-TERRA-COMBAT-2",
            "FUR-3-TERRA-COMBAT-3",
            "FUR-3-TERRA-COMBAT-4",
            "FUR-3-TERRA-COMBAT-5",
        ]
        | None
    ) = None
    terra_retreat_threshold_percent: int | None = Field(default=None, ge=1, le=100)
    crafting_ruleset: Literal["FUR-2", "FUR-CRAFTING-1"] | None = None
    npc_camps_ruleset: (
        Literal["FUR-2", "FUR-3-NPC-CAMPS-1", "FUR-3-NPC-CAMPS-2", "FUR-3-NPC-CAMPS-3"] | None
    ) = None
    terra_ruin_exploration_ruleset: Literal["FUR-2", "FUR-3-TERRA-RUIN-EXPLORATION-1"] | None = None
    rule_key: str | None = Field(default=None, min_length=1, max_length=40)
    target_version: str | None = Field(default=None, min_length=1, max_length=80)
    active_at: int | None = Field(default=None, ge=0, le=2**63 - 1)
    model_config = ConfigDict(extra="forbid", strict=True)
    key: str = Field(default="", max_length=100)
    direction: Literal["up", "down"] | None = None
    colony_id: str | None = Field(default=None, min_length=1, max_length=100)
    confirmation: str | None = Field(default=None, min_length=3, max_length=100)
    army: dict[str, int] | None = None
    count: int | None = Field(default=None, ge=1, le=100)
    capture: bool = False
    enabled: bool | None = None
    capacity: int | None = Field(default=None, ge=1, le=300)
    resources: list[int] | None = Field(default=None, min_length=3, max_length=3)
    source: int | None = Field(default=None, ge=0, le=2)
    dest: int | None = Field(default=None, ge=0, le=2)
    goods_source: str | None = Field(default=None, min_length=1, max_length=40)
    goods_destination: str | None = Field(default=None, min_length=1, max_length=40)
    amount: int | None = Field(default=None, ge=10, le=100000)
    item_amount: int | None = Field(default=None, ge=1, le=100)
    item_id: str | None = Field(default=None, min_length=1, max_length=80)
    recipe_id: str | None = Field(default=None, min_length=1, max_length=80)
    batches: int | None = Field(default=None, ge=1, le=10)
    give: int | None = Field(default=None, ge=0, le=2)
    want: int | None = Field(default=None, ge=0, le=2)
    price: int | None = Field(default=None, ge=10, le=100000)
    tag: str | None = Field(default=None, max_length=8)
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    profile_visibility: Literal["private", "public"] | None = None
    profile_title: str | None = Field(default=None, max_length=40)
    profile_badges: str | None = Field(default=None, max_length=120)
    profile_reward_title: str | None = Field(default=None, max_length=40)
    profile_skin: str | None = Field(default=None, max_length=40)
    profile_banner: str | None = Field(default=None, max_length=40)
    hero_stat: Literal["military", "economy", "recon", "command"] | None = None
    hero_ruleset: Literal["FUR-2", "FUR-3-HERO-1"] | None = None
    hero_doctrine_ruleset: Literal["FUR-2", "FUR-3-HERO-2"] | None = None
    hero_respec_ruleset: Literal["FUR-2", "FUR-3-HERO-3"] | None = None
    role: str | None = Field(default=None, max_length=20)
    channel: str | None = Field(default=None, max_length=20)
    body: str | None = Field(default=None, max_length=4000)
    target_kind: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=20)
    value: int | str | None = None
    hours: int | None = Field(default=None, ge=1, le=168)
    bonus: int | None = Field(default=None, ge=0, le=100)
    warning_hours: int | None = Field(default=None, ge=0, le=168)
    end_hours: int | None = Field(default=None, ge=0, le=168)
    end_bonus: int | None = Field(default=None, ge=0, le=100)
    days: int | None = Field(default=None, ge=1, le=365)
    goal_score: int | None = Field(default=None, ge=1, le=1_000_000_000)
    minutes: int | None = Field(default=None, ge=0, le=10080)
    x: int | None = Field(default=None, ge=0, le=63)
    y: int | None = Field(default=None, ge=0, le=63)
    world_id: int | None = Field(default=None, ge=1, le=2**31 - 1)
    galaxy: int | None = Field(default=None, ge=1)
    system: int | None = Field(default=None, ge=1)
    slot: int | None = Field(default=None, ge=1)
    orbit_ore: int | None = Field(default=None, ge=0, le=10000)
    orbit_ether: int | None = Field(default=None, ge=0, le=10000)
    orbit_target: str | None = Field(default=None, min_length=1, max_length=100)
    wreck_id: str | None = Field(default=None, min_length=1, max_length=100)
    retreat_pct: int | None = Field(default=None, ge=10, le=100)
    lances: int | None = Field(default=None, ge=0, le=20)
    seed: int | None = Field(default=None, ge=0, le=2**63 - 1)
    outposts: int | None = Field(default=None, ge=8, le=300)
    joinable: bool | None = None
    permissions: list[str] | None = Field(default=None, max_length=9)
    category: Literal["economy", "research", "military", "social", "system"] | None = None
    muted: bool | None = None


class CommandOrigin(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    world_id: int = Field(ge=1, le=2**31 - 1)
    colony_id: str = Field(min_length=1, max_length=100)
    rule_version: str = Field(min_length=1, max_length=100)


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Action
    payload: Payload = Field(default_factory=Payload)
    token: str = Field(min_length=8, max_length=100)
    origin: CommandOrigin | None = None
