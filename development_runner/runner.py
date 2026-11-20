from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from development_runner.database import RunnerDatabase


class Worker:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.state_dir = Path(config["state_dir"])
        self.repo = Path(config["repository"])
        self.db = RunnerDatabase(self.state_dir / "runner.sqlite3")
        self.worker_id = str(config.get("worker_id", socket.gethostname()))
        self.stop_file = self.state_dir / "STOP"
        self._stop = False

    def request_stop(self, *_args: object) -> None:
        self._stop = True

    def run(self, once: bool = False) -> int:
        self.db.initialize()
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        idle_seconds = int(self.config.get("idle_seconds", 60))
        while not self._stop and not self.stop_file.exists():
            midnight = int(
                datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            )
            usage = self.db.usage_since(midnight)
            if (
                usage["calls"] >= float(self.config.get("max_calls_per_day", 8))
                or usage["duration"] >= float(self.config.get("max_runtime_seconds_per_day", 21600))
                or usage["cost"] >= float(self.config.get("max_estimated_cost_usd_per_day", 20))
            ):
                if once:
                    return 2
                time.sleep(idle_seconds)
                continue
            task = self.db.claim(self.worker_id, int(self.config.get("lease_seconds", 15000)))
            if task is None:
                if once:
                    return 0
                time.sleep(idle_seconds)
                continue
            self.execute(task)
            if once:
                return 0
        return 0

    def execute(self, task: Any) -> None:
        task_id = int(task["id"])
        attempt = int(task["attempts"])
        log_dir = self.state_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"task-{task_id}-attempt-{attempt}.log"
        prompt_path = self.state_dir / f"task-{task_id}.md"
        prompt_path.write_text(str(task["prompt"]), encoding="utf-8")
        command = [str(part).format(prompt_file=prompt_path) for part in self.config["command"]]
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
        env.update({str(k): str(v) for k, v in self.config.get("environment", {}).items()})
        started = time.monotonic()
        error = ""
        exit_code = -1
        with log_path.open("wb") as log:
            try:
                result = subprocess.run(
                    command,
                    cwd=self.repo,
                    env=env,
                    input=str(task["prompt"]).encode("utf-8"),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=int(task["timeout_seconds"]),
                    check=False,
                )
                exit_code = result.returncode
                if exit_code:
                    error = f"agent exited with {exit_code}"
            except subprocess.TimeoutExpired:
                error = f"agent exceeded {task['timeout_seconds']} seconds"
            except OSError as exc:
                error = f"agent could not start: {exc}"
        duration = time.monotonic() - started
        with self.db.connect() as connection:
            now = int(time.time())
            session = connection.execute(
                """INSERT INTO agent_sessions
                (task_id,worker_id,started_at,finished_at,outcome,exit_code,duration_seconds,log_path)
                VALUES (?,?,?,?,?,?,?,?)""",
                (
                    task_id,
                    self.worker_id,
                    now - int(duration),
                    now,
                    "succeeded" if exit_code == 0 else "failed",
                    exit_code,
                    duration,
                    str(log_path),
                ),
            )
            connection.execute(
                """INSERT INTO execution_attempts
                (task_id,session_id,attempt_number,started_at,finished_at,exit_code,error)
                VALUES (?,?,?,?,?,?,?)""",
                (task_id, session.lastrowid, attempt, now - int(duration), now, exit_code, error),
            )
        self.db.finish(task_id, exit_code == 0, error)


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("runner configuration must be a JSON object")
    return cast(dict[str, Any], value)
