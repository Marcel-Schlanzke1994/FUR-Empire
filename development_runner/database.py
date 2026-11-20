from __future__ import annotations

import contextlib
import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued','running','succeeded','failed','blocked','cancelled')),
    risk TEXT NOT NULL DEFAULT 'normal'
        CHECK (risk IN ('normal','approval_required')),
    max_attempts INTEGER NOT NULL DEFAULT 2 CHECK (max_attempts BETWEEN 1 AND 5),
    timeout_seconds INTEGER NOT NULL DEFAULT 3600 CHECK (timeout_seconds BETWEEN 60 AND 14400),
    attempts INTEGER NOT NULL DEFAULT 0,
    not_before INTEGER NOT NULL DEFAULT 0,
    lease_owner TEXT,
    lease_until INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    last_error TEXT
);
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE RESTRICT,
    PRIMARY KEY (task_id, depends_on_id),
    CHECK (task_id <> depends_on_id)
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    decision TEXT NOT NULL CHECK (decision IN ('approved','rejected')),
    actor TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS agent_sessions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    worker_id TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    finished_at INTEGER,
    outcome TEXT,
    exit_code INTEGER,
    duration_seconds REAL,
    token_count INTEGER,
    estimated_cost_usd REAL,
    log_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS execution_attempts (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    started_at INTEGER NOT NULL,
    finished_at INTEGER,
    exit_code INTEGER,
    error TEXT,
    UNIQUE(task_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    passed INTEGER NOT NULL CHECK (passed IN (0,1)),
    summary TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    branch TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(task_id, commit_sha)
);
CREATE TABLE IF NOT EXISTS runner_events (
    id INTEGER PRIMARY KEY,
    level TEXT NOT NULL,
    event TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_runnable
    ON tasks(status, not_before, priority, created_at);
"""


class RunnerDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextlib.contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def add_task(
        self,
        title: str,
        prompt: str,
        priority: int = 100,
        max_attempts: int = 2,
        timeout_seconds: int = 3600,
        risk: str = "normal",
    ) -> int:
        now = int(time.time())
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO tasks
                (title,prompt,priority,max_attempts,timeout_seconds,risk,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (title, prompt, priority, max_attempts, timeout_seconds, risk, now, now),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("task insert did not return an id")
            return int(cursor.lastrowid)

    def claim(self, worker_id: str, lease_seconds: int) -> sqlite3.Row | None:
        now = int(time.time())
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """UPDATE tasks SET status='queued', lease_owner=NULL, lease_until=NULL,
                updated_at=? WHERE status='running' AND lease_until < ?""",
                (now, now),
            )
            row = connection.execute(
                """SELECT t.* FROM tasks t
                WHERE t.status='queued' AND t.not_before <= ? AND t.attempts < t.max_attempts
                AND NOT EXISTS (
                    SELECT 1 FROM task_dependencies d JOIN tasks p ON p.id=d.depends_on_id
                    WHERE d.task_id=t.id AND p.status <> 'succeeded'
                )
                AND (t.risk='normal' OR EXISTS (
                    SELECT 1 FROM approvals a WHERE a.task_id=t.id AND a.decision='approved'
                ))
                ORDER BY t.priority ASC, t.created_at ASC, t.id ASC LIMIT 1""",
                (now,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            connection.execute(
                """UPDATE tasks SET status='running', attempts=attempts+1, lease_owner=?,
                lease_until=?, updated_at=? WHERE id=?""",
                (worker_id, now + lease_seconds, now, row["id"]),
            )
            claimed = connection.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone()
            connection.commit()
            if claimed is None:
                raise RuntimeError("claimed task disappeared")
            return cast(sqlite3.Row, claimed)

    def finish(self, task_id: int, succeeded: bool, error: str = "") -> None:
        now = int(time.time())
        with self.connect() as connection:
            row = connection.execute(
                "SELECT attempts,max_attempts FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"unknown task {task_id}")
            status = (
                "succeeded"
                if succeeded
                else ("queued" if row["attempts"] < row["max_attempts"] else "failed")
            )
            delay = 0 if succeeded else min(3600, 60 * (2 ** max(0, row["attempts"] - 1)))
            connection.execute(
                """UPDATE tasks SET status=?, not_before=?, lease_owner=NULL, lease_until=NULL,
                updated_at=?, last_error=? WHERE id=?""",
                (status, now + delay, now, error[:4000] or None, task_id),
            )

    def list_tasks(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM tasks ORDER BY id")]

    def usage_since(self, timestamp: int) -> dict[str, float]:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS calls, COALESCE(SUM(duration_seconds),0) AS duration,
                COALESCE(SUM(estimated_cost_usd),0) AS cost
                FROM agent_sessions WHERE started_at >= ?""",
                (timestamp,),
            ).fetchone()
            if row is None:
                return {"calls": 0.0, "duration": 0.0, "cost": 0.0}
            return {
                "calls": float(row["calls"]),
                "duration": float(row["duration"]),
                "cost": float(row["cost"]),
            }
