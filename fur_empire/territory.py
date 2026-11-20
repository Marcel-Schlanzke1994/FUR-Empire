"""Derived regional control for the 64-by-64 world map."""

from collections.abc import Mapping, Sequence
from typing import Any

REGION_SIDE = 4
REGION_SIZE = 16
REGION_PRODUCTION_BONUS = 2
MAX_REGION_PRODUCTION_BONUS = REGION_SIDE * REGION_SIDE * REGION_PRODUCTION_BONUS
MIN_OUTPOSTS_FOR_CONTROL = 2


def summarize_regions(
    outposts: Sequence[Mapping[str, Any]],
    alliance_by_owner: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Summarize player and alliance control from the actual owners of each post."""
    regions: list[dict[str, Any]] = []
    for row in range(REGION_SIDE):
        for column in range(REGION_SIDE):
            region_id = f"{chr(ord('A') + column)}{row + 1}"
            members = [
                post
                for post in outposts
                if int(post["x"]) // REGION_SIZE == column and int(post["y"]) // REGION_SIZE == row
            ]
            owners: dict[str, int] = {}
            alliances: dict[str, int] = {}
            for post in members:
                owner = post.get("owner")
                if isinstance(owner, str) and owner:
                    owners[owner] = owners.get(owner, 0) + 1
                    alliance = (alliance_by_owner or {}).get(owner)
                    if alliance:
                        alliances[alliance] = alliances.get(alliance, 0) + 1
            leader_posts = max(owners.values(), default=0)
            leaders = [owner for owner, count in owners.items() if count == leader_posts]
            leader_id = leaders[0] if len(leaders) == 1 else None
            required_posts = max(MIN_OUTPOSTS_FOR_CONTROL, len(members) // 2 + 1)
            controller = leader_id if len(members) > 0 and leader_posts >= required_posts else None
            alliance_leader_posts = max(alliances.values(), default=0)
            alliance_leaders = [
                alliance for alliance, count in alliances.items() if count == alliance_leader_posts
            ]
            alliance_controller = (
                alliance_leaders[0]
                if len(alliance_leaders) == 1
                and len(members) > 0
                and alliance_leader_posts >= required_posts
                else None
            )
            regions.append(
                {
                    "id": region_id,
                    "x_min": column * REGION_SIZE,
                    "x_max": (column + 1) * REGION_SIZE - 1,
                    "y_min": row * REGION_SIZE,
                    "y_max": (row + 1) * REGION_SIZE - 1,
                    "outpost_count": len(members),
                    "leader_id": leader_id,
                    "leader_outposts": leader_posts,
                    "leader_tied": len(leaders) > 1,
                    "required_posts": required_posts,
                    "owner_id": controller,
                    "alliance_owner_id": alliance_controller,
                    "alliance_leader_tied": len(alliance_leaders) > 1,
                    "production_bonus_percent": (REGION_PRODUCTION_BONUS if controller else 0),
                }
            )
    return regions
