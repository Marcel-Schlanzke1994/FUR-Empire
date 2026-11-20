"""Versioned provisional FUR-3 alliance-war scoring and append-only battle results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "rules" / "fur-3-alliance-war-1.json").read_text(encoding="utf-8")
)
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = "sha256:" + hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
VERSION = str(RULES["version"])
TARGET_POINTS = int(RULES["objective"]["target_points"])


def next_event_time(db: Connection, war_id: str, requested: int) -> int:
    latest = db.execute(
        "SELECT max(created) AS latest FROM alliance_war_events WHERE war_id=?", (war_id,)
    ).fetchone()
    previous = int(latest["latest"]) if latest and latest["latest"] is not None else requested - 1
    return max(requested, previous + 1)


def next_diplomacy_event_time(
    db: Connection, alliance_a: str, alliance_b: str, requested: int
) -> int:
    a, b = sorted((alliance_a, alliance_b))
    latest = db.execute(
        "SELECT max(created) AS latest FROM alliance_diplomacy_events "
        "WHERE alliance_a=? AND alliance_b=?",
        (a, b),
    ).fetchone()
    previous = int(latest["latest"]) if latest and latest["latest"] is not None else requested - 1
    return max(requested, previous + 1)


def record_battle(
    db: Connection,
    *,
    mission_id: str,
    world_id: int,
    attacker_losses: dict[str, dict[str, int]],
    defender_losses: dict[str, dict[str, int]],
    rules_version: str,
    at: int,
) -> None:
    """Credit enemy casualties to the two warring alliances exactly once per battle."""
    if rules_version == "FUR-2" or VERSION != str(RULES["version"]):
        return
    from .game import identity

    def memberships(users: list[str]) -> dict[str, str]:
        if not users:
            return {}
        placeholders = ",".join("?" for _ in users)
        return {
            str(row["user_id"]): str(row["alliance_id"])
            for row in db.execute(
                "SELECT user_id,alliance_id FROM members WHERE user_id IN (" + placeholders + ")",
                tuple(users),
            )
        }

    attacker_memberships = memberships(list(attacker_losses))
    defender_memberships = memberships(list(defender_losses))
    attacker_alliances = set(attacker_memberships.values())
    defender_alliances = set(defender_memberships.values())
    pairs = [
        (attack_alliance, defense_alliance)
        for attack_alliance in attacker_alliances
        for defense_alliance in defender_alliances
        if attack_alliance != defense_alliance
    ]
    war = None
    attack_alliance = defense_alliance = ""
    for attack_candidate, defense_candidate in sorted(pairs):
        a, b = sorted((attack_candidate, defense_candidate))
        war = db.execute(
            "SELECT * FROM alliance_wars WHERE alliance_a=? AND alliance_b=? "
            "AND status IN ('active','peace_offered') ORDER BY started DESC,id LIMIT 1",
            (a, b),
        ).fetchone()
        if war:
            attack_alliance, defense_alliance = attack_candidate, defense_candidate
            break
    if not war:
        return
    if str(war["rules_version"]) != VERSION or str(war["rules_digest"]) != RULES_DIGEST:
        raise ValueError("the active alliance-war ruleset is unavailable")
    # A coalition can bring members of several alliances. Only casualties on
    # the two recorded sides of this war may affect its score.
    scoring_attackers = {
        user: losses
        for user, losses in attacker_losses.items()
        if attacker_memberships.get(user) == attack_alliance
    }
    scoring_defenders = {
        user: losses
        for user, losses in defender_losses.items()
        if defender_memberships.get(user) == defense_alliance
    }
    attacker_total = sum(
        max(0, int(points)) for losses in scoring_attackers.values() for points in losses.values()
    )
    defender_total = sum(
        max(0, int(points)) for losses in scoring_defenders.values() for points in losses.values()
    )
    if attacker_total + defender_total == 0:
        return
    battle_id = identity()
    inserted = db.execute(
        "INSERT INTO alliance_war_battles "
        "(id,war_id,mission_id,world_id,attacker_alliance,defender_alliance,"
        "attacker_losses,defender_losses,rules_version,created) "
        "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(war_id,mission_id) DO NOTHING RETURNING id",
        (
            battle_id,
            war["id"],
            mission_id,
            world_id,
            attack_alliance,
            defense_alliance,
            attacker_total,
            defender_total,
            rules_version,
            at,
        ),
    ).fetchone()
    if not inserted:
        return

    def allocate(total: int, users: list[str], scoring_alliance: str, category: str) -> None:
        eligible = []
        for user in sorted(set(users)):
            member = db.execute(
                "SELECT alliance_id FROM members WHERE user_id=?", (user,)
            ).fetchone()
            if member and str(member["alliance_id"]) == scoring_alliance:
                eligible.append(user)
        if not total or not eligible:
            return
        share, remainder = divmod(total, len(eligible))
        for index, user in enumerate(eligible):
            points = share + int(index < remainder)
            if points:
                db.execute(
                    "INSERT INTO alliance_war_score_ledger "
                    "(war_id,mission_id,alliance_id,user_id,category,points,created) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (war["id"], mission_id, scoring_alliance, user, category, points, at),
                )

    allocate(defender_total, list(scoring_attackers), attack_alliance, "attack")
    allocate(attacker_total, list(scoring_defenders), defense_alliance, "defense")
    a, b = str(war["alliance_a"]), str(war["alliance_b"])
    score_a = defender_total if attack_alliance == a else attacker_total
    score_b = defender_total if attack_alliance == b else attacker_total
    event_at = next_event_time(db, str(war["id"]), at)
    db.execute(
        "UPDATE alliance_wars SET score_a=score_a+?,score_b=score_b+? WHERE id=?",
        (score_a, score_b, war["id"]),
    )
    refreshed = db.execute("SELECT * FROM alliance_wars WHERE id=?", (war["id"],)).fetchone()
    db.execute(
        "INSERT INTO alliance_war_events "
        "(id,war_id,event_type,actor_alliance,details,created) VALUES (?,?, 'battle_score',?,?,?)",
        (
            identity(),
            war["id"],
            attack_alliance,
            json.dumps(
                {
                    "world_id": world_id,
                    "attacker_alliance": attack_alliance,
                    "defender_alliance": defense_alliance,
                    "attacker_losses": attacker_total,
                    "defender_losses": defender_total,
                    "score_a": int(refreshed["score_a"]),
                    "score_b": int(refreshed["score_b"]),
                    "rules_version": str(war["rules_version"]),
                },
                separators=(",", ":"),
            ),
            event_at,
        ),
    )
    winner = None
    if int(refreshed["score_a"]) >= int(war["target_points"]):
        winner = a
    if int(refreshed["score_b"]) >= int(war["target_points"]):
        winner = b if winner is None else ""
    if winner is not None:
        reason = "objective" if winner else "objective_draw"
        ended_event_at = next_event_time(db, str(war["id"]), at)
        db.execute(
            "UPDATE alliance_wars SET status='ended',winner=?,end_reason=?,ended=? " "WHERE id=?",
            (winner or None, reason, ended_event_at, war["id"]),
        )
        db.execute("DELETE FROM diplomacy WHERE a=? AND b=?", (a, b))
        db.execute(
            "INSERT INTO alliance_war_events "
            "(id,war_id,event_type,actor_alliance,details,created) VALUES (?,?, 'ended_objective',?,?,?)",
            (
                identity(),
                war["id"],
                winner or None,
                json.dumps(
                    {
                        "winner": winner or None,
                        "reason": reason,
                        "score_a": int(refreshed["score_a"]),
                        "score_b": int(refreshed["score_b"]),
                    },
                    separators=(",", ":"),
                ),
                ended_event_at,
            ),
        )
        db.execute(
            "INSERT INTO alliance_diplomacy_events "
            "(id,alliance_a,alliance_b,actor_alliance,event_type,created) "
            "VALUES (?,?,?,?, 'neutralized',?)",
            (
                identity(),
                a,
                b,
                winner or attack_alliance,
                next_diplomacy_event_time(db, a, b, at),
            ),
        )
