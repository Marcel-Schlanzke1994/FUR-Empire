"""Versioned settings for world-scoped production events."""

import hashlib
import json
from typing import Any

RULES_VERSION = "FUR-2-LIVE-2"
MAX_COMBINED_PRODUCTION_BONUS = 100


def snapshot(event: dict[str, Any]) -> tuple[str, str, str]:
    payload = {
        "version": RULES_VERSION,
        "world_id": int(event["world_id"]),
        "name": str(event["name"]),
        "starts": int(event["starts"]),
        "ends": int(event["ends"]),
        "bonus": int(event["bonus"]),
        "warning_hours": int(event["warning_hours"]),
        "end_starts": int(event["end_starts"]),
        "end_bonus": int(event["end_bonus"]),
        "goal_score": int(event["goal_score"]),
        "overlap_bonus_cap": MAX_COMBINED_PRODUCTION_BONUS,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return RULES_VERSION, canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def phase(event: dict[str, Any], now: int) -> str:
    if now < int(event["starts"]):
        return "warning"
    end_starts = int(event.get("end_starts") or event["ends"])
    if end_starts < int(event["ends"]) and now >= end_starts:
        return "end"
    return "active"


def active_bonus(event: dict[str, Any], now: int) -> int:
    if not int(event["starts"]) <= now < int(event["ends"]):
        return 0
    return int(event["end_bonus"] if phase(event, now) == "end" else event["bonus"])


def active_bonus_total(events: list[dict[str, Any]], now: int) -> int:
    return min(
        MAX_COMBINED_PRODUCTION_BONUS,
        sum(active_bonus(event, now) for event in events),
    )


def integrated_bonus_seconds(events: list[dict[str, Any]], start: int, end: int) -> int:
    """Integrate overlapping event bonuses, capped at each phase boundary."""
    if end <= start:
        return 0
    deltas: dict[int, int] = {}

    def add_interval(interval_start: int, interval_end: int, bonus: int) -> None:
        clipped_start = max(start, interval_start)
        clipped_end = min(end, interval_end)
        if clipped_start >= clipped_end:
            return
        deltas[clipped_start] = deltas.get(clipped_start, 0) + bonus
        deltas[clipped_end] = deltas.get(clipped_end, 0) - bonus

    for event in events:
        event_start = int(event["starts"])
        event_end = int(event["ends"])
        end_start = int(event.get("end_starts") or event_end)
        base_end = min(event_end, end_start)
        add_interval(event_start, base_end, int(event["bonus"]))
        if end_start < event_end:
            add_interval(
                max(event_start, end_start),
                event_end,
                int(event.get("end_bonus", event["bonus"])),
            )

    total = 0
    current_bonus = 0
    previous = start
    for boundary in sorted({start, end, *deltas}):
        if boundary > previous:
            total += (boundary - previous) * min(MAX_COMBINED_PRODUCTION_BONUS, current_bonus)
        current_bonus += deltas.get(boundary, 0)
        previous = boundary
    return total
