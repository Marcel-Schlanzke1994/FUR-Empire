from pathlib import Path

from development_runner.database import RunnerDatabase
from development_runner.runner import parse_usage


def test_claim_respects_dependencies_and_retries(tmp_path: Path) -> None:
    db = RunnerDatabase(tmp_path / "runner.sqlite3")
    db.initialize()
    first = db.add_task("first", "do first", max_attempts=1)
    second = db.add_task("second", "do second")
    with db.connect() as connection:
        connection.execute(
            "INSERT INTO task_dependencies(task_id,depends_on_id) VALUES (?,?)", (second, first)
        )
    claimed = db.claim("worker", 120)
    assert claimed is not None and claimed["id"] == first
    db.finish(first, True)
    claimed = db.claim("worker", 120)
    assert claimed is not None and claimed["id"] == second
    db.finish(second, False, "boom")
    tasks = {task["id"]: task for task in db.list_tasks()}
    assert tasks[second]["status"] == "queued"
    assert tasks[second]["last_error"] == "boom"


def test_approval_required_task_is_not_claimed_without_approval(tmp_path: Path) -> None:
    db = RunnerDatabase(tmp_path / "runner.sqlite3")
    db.initialize()
    task_id = db.add_task("danger", "careful", risk="approval_required")
    assert db.claim("worker", 120) is None
    with db.connect() as connection:
        connection.execute(
            "INSERT INTO approvals(task_id,decision,actor,created_at) VALUES (?, 'approved', ?, 1)",
            (task_id, "owner"),
        )
    claimed = db.claim("worker", 120)
    assert claimed is not None and claimed["id"] == task_id


def test_usage_is_persisted_for_budget_checks(tmp_path: Path) -> None:
    db = RunnerDatabase(tmp_path / "runner.sqlite3")
    db.initialize()
    task_id = db.add_task("budget", "measure")
    with db.connect() as connection:
        connection.execute(
            """INSERT INTO agent_sessions
            (task_id,worker_id,started_at,finished_at,outcome,exit_code,duration_seconds,
             estimated_cost_usd,log_path)
            VALUES (?,?,100,110,'succeeded',0,10,1.25,'run.log')""",
            (task_id, "worker"),
        )
    assert db.usage_since(99) == {"calls": 1.0, "duration": 10.0, "cost": 1.25}


def test_database_helpers_persist_dependencies_and_approvals(tmp_path: Path) -> None:
    db = RunnerDatabase(tmp_path / "runner.sqlite3")
    db.initialize()
    parent = db.add_task("parent", "first")
    child = db.add_task("child", "second", risk="approval_required")
    db.add_dependency(child, parent)
    db.approve(child, "owner", "reviewed")
    with db.connect() as connection:
        dependency = connection.execute(
            "SELECT depends_on_id FROM task_dependencies WHERE task_id=?", (child,)
        ).fetchone()
        approval = connection.execute(
            "SELECT actor,note FROM approvals WHERE task_id=?", (child,)
        ).fetchone()
    assert dependency is not None and dependency["depends_on_id"] == parent
    assert approval is not None and tuple(approval) == ("owner", "reviewed")


def test_parse_usage_reads_latest_codex_json_event(tmp_path: Path) -> None:
    log = tmp_path / "agent.jsonl"
    log.write_text(
        '{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":20}}\n'
        "not-json\n"
        '{"event":{"usage":{"input_tokens":125,"output_tokens":25}}}\n',
        encoding="utf-8",
    )
    assert parse_usage(log) == (150, 125, 25)
