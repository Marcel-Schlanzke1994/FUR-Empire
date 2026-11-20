"""Immutable FUR-3 alliance season scoring and archived standings."""

import hashlib
import json
from pathlib import Path
from typing import Any

from .database import Connection

RULES_PATH = Path(__file__).parent / "rules" / "fur-3-alliance-ranking-1.json"
RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))
RULES_VERSION = str(RULES["version"])
RULES_SNAPSHOT = json.dumps(RULES, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
RULES_DIGEST = "sha256:" + hashlib.sha256(RULES_SNAPSHOT.encode("utf-8")).hexdigest()
ELIGIBILITY_POLICY = "verified=1; non-empty email; identical addresses globally unique; separate addresses not deduplicated"


def archive_season_alliances(
    db: Connection,
    *,
    season_id: str,
    world_id: int,
    starts: int,
    ends: int,
    closed_at: int,
) -> list[dict[str, Any]]:
    """Freeze eligible alliance scores, attributed when each FUR-3 score was earned."""
    existing = db.execute(
        "SELECT 1 FROM season_alliance_snapshots WHERE season_id=?", (season_id,)
    ).fetchone()
    if existing:
        return [
            dict(row)
            for row in db.execute(
                "SELECT alliance_id AS id,alliance_name AS name,alliance_tag AS tag,score,rank,"
                "eligible_accounts FROM season_alliance_standings WHERE season_id=? "
                "ORDER BY rank",
                (season_id,),
            )
        ]

    rows = [
        dict(row)
        for row in db.execute(
            "SELECT a.id,a.name,a.tag,SUM(l.points) AS score,"
            "COUNT(DISTINCT l.user_id) AS eligible_accounts "
            "FROM alliance_military_score_ledger l "
            "JOIN alliances a ON a.id=l.alliance_id "
            "JOIN profiles p ON p.user_id=l.user_id "
            "WHERE l.world_id=? AND l.created>=? AND l.created<=? "
            "AND substr(l.rules_version,1,6)='FUR-3-' AND p.verified=1 "
            "AND p.email IS NOT NULL AND trim(p.email)<>'' "
            "GROUP BY a.id,a.name,a.tag ORDER BY score DESC,a.id ASC",
            (world_id, starts, ends),
        )
    ]
    db.execute(
        "INSERT INTO season_alliance_snapshots"
        "(season_id,rules_version,rules_digest,closed_at,eligibility_policy) "
        "VALUES (?,?,?,?,?)",
        (season_id, RULES_VERSION, RULES_DIGEST, closed_at, ELIGIBILITY_POLICY),
    )
    for place, row in enumerate(rows, start=1):
        db.execute(
            "INSERT INTO season_alliance_standings"
            "(season_id,alliance_id,alliance_name,alliance_tag,score,rank,eligible_accounts) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                season_id,
                row["id"],
                row["name"],
                row["tag"],
                int(row["score"]),
                place,
                int(row["eligible_accounts"]),
            ),
        )
        row["score"] = int(row["score"])
        row["eligible_accounts"] = int(row["eligible_accounts"])
        row["rank"] = place
    return rows
