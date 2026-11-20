from pathlib import Path

from development_runner.database import RunnerDatabase


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
