from __future__ import annotations

import argparse
import json
from pathlib import Path

from development_runner.database import RunnerDatabase
from development_runner.runner import Worker, load_config


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="fur-development-runner")
    result.add_argument("--config", type=Path, required=True)
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("init")
    add = sub.add_parser("add-task")
    add.add_argument("--title", required=True)
    add.add_argument("--prompt-file", type=Path, required=True)
    add.add_argument("--priority", type=int, default=100)
    add.add_argument("--max-attempts", type=int, default=2)
    add.add_argument("--timeout", type=int, default=3600)
    add.add_argument("--approval-required", action="store_true")
    dependency = sub.add_parser("add-dependency")
    dependency.add_argument("--task-id", type=int, required=True)
    dependency.add_argument("--depends-on", type=int, required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--task-id", type=int, required=True)
    approve.add_argument("--actor", required=True)
    approve.add_argument("--note", default="")
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("--once", action="store_true")
    sub.add_parser("stop")
    sub.add_parser("resume")
    return result


def main() -> int:
    args = parser().parse_args()
    config = load_config(args.config)
    state = Path(config["state_dir"])
    db = RunnerDatabase(state / "runner.sqlite3")
    if args.action == "init":
        db.initialize()
    elif args.action == "add-task":
        db.initialize()
        task_id = db.add_task(
            args.title,
            args.prompt_file.read_text(encoding="utf-8"),
            args.priority,
            args.max_attempts,
            args.timeout,
            "approval_required" if args.approval_required else "normal",
        )
        print(task_id)
    elif args.action == "list":
        db.initialize()
        print(json.dumps(db.list_tasks(), indent=2, ensure_ascii=False))
    elif args.action == "add-dependency":
        db.initialize()
        db.add_dependency(args.task_id, args.depends_on)
    elif args.action == "approve":
        db.initialize()
        db.approve(args.task_id, args.actor, args.note)
    elif args.action == "run":
        return Worker(config).run(args.once)
    elif args.action == "stop":
        state.mkdir(parents=True, exist_ok=True)
        (state / "STOP").touch(exist_ok=True)
    elif args.action == "resume":
        (state / "STOP").unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
