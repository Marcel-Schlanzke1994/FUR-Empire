"""One-time, non-gameplay cosmetic rewards from existing campaign directives."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .database import Connection


class CosmeticRules(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str
    scope: str
    gameplay_effects: bool
    titles: dict[str, str] = Field(min_length=1, max_length=100)
    skins: dict[str, str] = Field(min_length=1, max_length=100)
    banners: dict[str, str] = Field(min_length=1, max_length=100)
    directive_rewards: dict[str, list[str]] = Field(min_length=1, max_length=20)
    prestige: dict[str, object]


RULES = CosmeticRules.model_validate(
    json.loads(
        (Path(__file__).parent / "rules" / "fur-3-cosmetic-rewards-1.json").read_text(
            encoding="utf-8"
        )
    )
)
if RULES.scope != "account" or RULES.gameplay_effects:
    raise ValueError("Cosmetic rewards must remain account-scoped and non-gameplay")
COSMETICS = {
    **{f"title:{key}": ("title", label) for key, label in RULES.titles.items()},
    **{f"skin:{key}": ("skin", label) for key, label in RULES.skins.items()},
    **{f"banner:{key}": ("banner", label) for key, label in RULES.banners.items()},
}
if any(
    not isinstance(items, list)
    or any(item not in COSMETICS for item in items)
    or len(items) != len(set(items))
    for items in RULES.directive_rewards.values()
):
    raise ValueError("Invalid cosmetic directive reward catalog")


def award_for_directive(db: Connection, user_id: str, directive_id: str, now: int) -> list[str]:
    """Insert each unlock once; the caller shares the directive claim transaction."""
    awarded: list[str] = []
    for cosmetic_id in RULES.directive_rewards.get(directive_id, []):
        inserted = db.execute(
            "INSERT INTO player_cosmetic_unlocks(user_id,cosmetic_id,source_directive,"
            "rules_version,created) VALUES (?,?,?,?,?) ON CONFLICT(user_id,cosmetic_id) DO NOTHING",
            (user_id, cosmetic_id, directive_id, RULES.version, now),
        ).cursor.rowcount
        if inserted == 1:
            awarded.append(cosmetic_id)
    return awarded


def unlocked(db: Connection, user_id: str) -> set[str]:
    return {
        str(row["cosmetic_id"])
        for row in db.execute(
            "SELECT cosmetic_id FROM player_cosmetic_unlocks WHERE user_id=?", (user_id,)
        )
    }


def available_title_labels(db: Connection, user_id: str) -> dict[str, str]:
    owned = unlocked(db, user_id)
    return {key: label for key, label in RULES.titles.items() if f"title:{key}" in owned}


def available_skin_labels(db: Connection, user_id: str) -> dict[str, str]:
    owned = unlocked(db, user_id)
    return {key: label for key, label in RULES.skins.items() if f"skin:{key}" in owned}


def available_banner_labels(db: Connection, user_id: str) -> dict[str, str]:
    owned = unlocked(db, user_id)
    return {key: label for key, label in RULES.banners.items() if f"banner:{key}" in owned}
