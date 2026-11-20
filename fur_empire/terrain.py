"""Authoritative terrain generation and shortest-path travel rules."""

import heapq
import math
import random

from .database import Connection
from .registry import load_rule_model

TERRAIN_RULES = load_rule_model().terrain
TERRAIN_KINDS: tuple[str, ...] = tuple(TERRAIN_RULES)
TERRAIN_LABELS: dict[str, str] = {kind: rule.name for kind, rule in TERRAIN_RULES.items()}
MOVEMENT_COST: dict[str, float] = {
    kind: math.inf if rule.movement_cost is None else float(rule.movement_cost)
    for kind, rule in TERRAIN_RULES.items()
}
GENERATION_WEIGHT: dict[str, int] = {
    kind: rule.generation_weight for kind, rule in TERRAIN_RULES.items()
}
PRODUCTION_PERCENT: dict[str, tuple[int, int, int]] = {
    kind: (
        rule.production_percent[0],
        rule.production_percent[1],
        rule.production_percent[2],
    )
    for kind, rule in TERRAIN_RULES.items()
}
DEFENSE_PERCENT: dict[str, int] = {
    kind: rule.defense_percent for kind, rule in TERRAIN_RULES.items()
}


def seed_world(db: Connection, world_id: int = 1, seed: int = 504_921) -> None:
    """Fill missing tiles from a fixed seed without moving existing map objects."""
    occupied = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute("SELECT x,y FROM colonies WHERE world_id=?", (world_id,))
    }
    if (
        db.execute("SELECT count(*) FROM world_terrain WHERE world_id=?", (world_id,)).fetchone()[0]
        == 4096
    ):
        return
    occupied.update(
        (int(row["x"]), int(row["y"]))
        for row in db.execute("SELECT x,y FROM world_outposts WHERE world_id=?", (world_id,))
    )
    existing = {
        (int(row["x"]), int(row["y"]))
        for row in db.execute("SELECT x,y FROM world_terrain WHERE world_id=?", (world_id,))
    }
    rng = random.Random(seed)
    weights = tuple(GENERATION_WEIGHT[kind] for kind in TERRAIN_KINDS)
    rows: list[tuple[int, int, str]] = []
    for y in range(64):
        for x in range(64):
            kind = rng.choices(TERRAIN_KINDS, weights=weights, k=1)[0]
            if kind == "water" and (x, y) in occupied:
                kind = "plain"
            if (x, y) not in existing:
                rows.append((x, y, kind))
    batch_size = 4000 if db.postgres else 300
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        values = ",".join("(?,?,?,?)" for _ in batch)
        params = tuple(value for x, y, kind in batch for value in (world_id, x, y, kind))
        db.execute(
            f"INSERT INTO world_terrain(world_id,x,y,terrain) VALUES {values} "
            "ON CONFLICT(world_id,x,y) DO NOTHING",
            params,
        )


def terrain_at(db: Connection, x: int, y: int, world_id: int = 1) -> str:
    row = db.execute(
        "SELECT terrain FROM world_terrain WHERE world_id=? AND x=? AND y=?",
        (world_id, x, y),
    ).fetchone()
    if not row:
        raise ValueError("Geländedaten fehlen für diesen Weltsektor.")
    return str(row[0])


def travel_seconds(
    db: Connection,
    start: tuple[int, int],
    finish: tuple[int, int],
    world_id: int = 1,
) -> int:
    times = travel_times(db, start, world_id)
    if finish not in times:
        raise ValueError("Zwischen Ausgangs- und Zielsektor gibt es keinen begehbaren Weg.")
    return times[finish]


def travel_times(
    db: Connection, start: tuple[int, int], world_id: int = 1
) -> dict[tuple[int, int], int]:
    return {
        point: max(5, (distance + 4) // 5)
        for point, distance in travel_costs(db, start, world_id).items()
    }


def travel_costs(
    db: Connection, start: tuple[int, int], world_id: int = 1
) -> dict[tuple[int, int], int]:
    """Return terrain-weighted path costs without converting them to legacy seconds."""
    kinds = {
        (int(row["x"]), int(row["y"])): str(row["terrain"])
        for row in db.execute("SELECT x,y,terrain FROM world_terrain WHERE world_id=?", (world_id,))
    }
    costs = {point: MOVEMENT_COST[kind] for point, kind in kinds.items()}
    if start not in costs or math.isinf(costs[start]):
        raise ValueError("Einheiten können nicht in oder aus Wasserfeldern reisen.")
    distances: dict[tuple[int, int], int] = {start: 0}
    queue: list[tuple[int, tuple[int, int]]] = [(0, start)]
    while queue:
        current_cost, point = heapq.heappop(queue)
        if current_cost != distances[point]:
            continue
        x, y = point
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            step = costs.get(neighbor, math.inf)
            if math.isinf(step):
                continue
            edge_cost = (int(costs[point]) + int(step)) // 2
            candidate = current_cost + edge_cost
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    return distances


def travel_cost(
    db: Connection,
    start: tuple[int, int],
    finish: tuple[int, int],
    world_id: int = 1,
) -> int:
    costs = travel_costs(db, start, world_id)
    if finish not in costs:
        raise ValueError("Zwischen Ausgangs- und Zielsektor gibt es keinen begehbaren Weg.")
    return costs[finish]


def defense_with_terrain(defense: int, kind: str) -> int:
    return defense * DEFENSE_PERCENT[kind] // 100
