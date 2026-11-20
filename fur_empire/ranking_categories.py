"""World-scoped ranking categories and immutable seasonal snapshots."""

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES = json.loads(
    (Path(__file__).parent / "rules" / "fur-2-ranking-categories-1.json").read_text(
        encoding="utf-8"
    )
)
RULES_VERSION = str(RULES["version"])
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = "sha256:" + hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
CATEGORY_KEYS = ("overall", "economy", "research", "pve", "war", "regions")


def _rank(scores: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {"id": user_id, "name": str(value["name"]), "score": int(value["score"])}
        for user_id, value in scores.items()
    ]
    return sorted(rows, key=lambda row: (-row["score"], row["id"]))


def account_scores(
    db: Connection, world_id: int, regions: list[dict[str, Any]]
) -> dict[str, dict[str, dict[str, Any]]]:
    scores: dict[str, dict[str, dict[str, Any]]] = {key: {} for key in CATEGORY_KEYS}
    for row in db.execute(
        "SELECT c.user_id,u.name,c.state,c.ranking_score FROM colonies c "
        "JOIN users u ON u.id=c.user_id WHERE c.world_id=? ORDER BY c.user_id,c.colony_id",
        (world_id,),
    ):
        user_id = str(row["user_id"])
        name = str(row["name"])
        colony = json.loads(row["state"])
        values = {
            "overall": int(row["ranking_score"]),
            "economy": sum(int(value) for value in colony["buildings"].values()) * 10,
            "research": sum(int(value) for value in colony["tech"].values()) * 20,
            "pve": int(colony["captures"]) * 100,
            "war": 0,
            "regions": 0,
        }
        for category, score in values.items():
            target = scores[category].setdefault(user_id, {"name": name, "score": 0})
            target["score"] = int(target["score"]) + score
    for row in db.execute(
        "SELECT user_id,SUM(points) AS score FROM war_score_ledger "
        "WHERE world_id=? AND substr(rules_version,1,6)='FUR-3-' GROUP BY user_id",
        (world_id,),
    ):
        user_id = str(row["user_id"])
        if user_id in scores["war"]:
            scores["war"][user_id]["score"] = int(row["score"] or 0)
    for region in regions:
        owner_id = region.get("owner_id")
        if not isinstance(owner_id, str) or owner_id not in scores["regions"]:
            continue
        scores["regions"][owner_id]["score"] = int(scores["regions"][owner_id]["score"]) + 2
    return scores


def live_rankings(
    db: Connection,
    world_id: int,
    regions: list[dict[str, Any]],
    alliance_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    scores = account_scores(db, world_id, regions)
    rankings = {category: _rank(rows)[:50] for category, rows in scores.items()}
    rankings["alliance"] = [
        {
            "id": str(row["id"]),
            "name": str(row["name"]),
            "tag": str(row["tag"]),
            "score": int(row["score"]),
        }
        for row in alliance_rows[:50]
    ]
    return rankings


def archive_season_rankings(
    db: Connection,
    *,
    season_id: str,
    world_id: int,
    starts: int,
    ends: int,
    closed_at: int,
    regions: list[dict[str, Any]],
) -> None:
    existing = db.execute(
        "SELECT 1 FROM season_ranking_snapshots WHERE season_id=?", (season_id,)
    ).fetchone()
    if existing:
        return
    scores = account_scores(db, world_id, regions)
    legacy_standings = db.execute(
        "SELECT standings FROM seasons WHERE id=?", (season_id,)
    ).fetchone()
    overall = {
        str(row["id"]): {"name": str(row["name"]), "score": int(row["score"])}
        for row in json.loads(legacy_standings["standings"])
    }
    scores["overall"] = overall
    scores["war"] = {
        str(row["user_id"]): {"name": str(row["name"]), "score": int(row["score"])}
        for row in db.execute(
            "SELECT l.user_id,u.name,SUM(l.points) AS score FROM war_score_ledger l "
            "JOIN users u ON u.id=l.user_id WHERE l.world_id=? AND l.created>=? AND l.created<=? "
            "AND substr(l.rules_version,1,6)='FUR-3-' GROUP BY l.user_id,u.name",
            (world_id, starts, ends),
        )
        if str(row["user_id"]) in overall
    }
    db.execute(
        "INSERT INTO season_ranking_snapshots(season_id,rules_version,rules_digest,closed_at) "
        "VALUES (?,?,?,?)",
        (season_id, RULES_VERSION, RULES_DIGEST, closed_at),
    )
    for category in CATEGORY_KEYS:
        for rank, entry in enumerate(_rank(scores[category]), start=1):
            db.execute(
                "INSERT INTO season_ranking_standings"
                "(season_id,category,user_id,display_name,score,rank) VALUES (?,?,?,?,?,?)",
                (season_id, category, entry["id"], entry["name"], entry["score"], rank),
            )
