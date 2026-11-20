from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from development_runner.database import RunnerDatabase


def parse_usage(log_path: Path) -> tuple[int | None, int, int]:
    latest: tuple[int, int] | None = None
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        pending = [event]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                if isinstance(value.get("input_tokens"), int) and isinstance(
                    value.get("output_tokens"), int
                ):
                    latest = (value["input_tokens"], value["output_tokens"])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
    if latest is None:
        return None, 0, 0
    input_tokens, output_tokens = latest
    return input_tokens + output_tokens, input_tokens, output_tokens


class Worker:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.state_dir = Path(config["state_dir"])
        self.repo = Path(config["repository"])
        self.db = RunnerDatabase(self.state_dir / "runner.sqlite3")
        self.worker_id = str(config.get("worker_id", socket.gethostname()))
        self.stop_file = self.state_dir / "STOP"
        self._stop = False
        self._stop_event = threading.Event()

    def request_stop(self, *_args: object) -> None:
        self._stop = True
        self._stop_event.set()

    def run(self, once: bool = False) -> int:
        self.db.initialize()
        self.db.recover_worker_tasks(self.worker_id)
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
                self._stop_event.wait(idle_seconds)
                continue
            task = self.db.claim(self.worker_id, int(self.config.get("lease_seconds", 15000)))
            if task is None:
                if once:
                    return 0
                self._stop_event.wait(idle_seconds)
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
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
        env.update({str(k): str(v) for k, v in self.config.get("environment", {}).items()})
        try:
            worktree, branch = self.prepare_worktree(task_id, env)
        except (OSError, subprocess.CalledProcessError) as exc:
            self.db.finish(task_id, False, f"worktree preparation failed: {exc}")
            return
        command = [str(part).format(prompt_file=prompt_path) for part in self.config["command"]]
        started = time.monotonic()
        error = ""
        exit_code = -1
        with log_path.open("wb") as log:
            try:
                result = subprocess.run(
                    command,
                    cwd=worktree,
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
        if exit_code == 0:
            try:
                exit_code, error = self.validate_and_publish(task_id, worktree, branch, env)
            except (OSError, subprocess.SubprocessError) as exc:
                exit_code, error = -1, f"validation or publication failed: {exc}"
        token_count, input_tokens, output_tokens = parse_usage(log_path)
        estimated_cost = None
        if token_count is not None and "input_cost_per_million" in self.config:
            estimated_cost = (
                input_tokens * float(self.config["input_cost_per_million"])
                + output_tokens * float(self.config["output_cost_per_million"])
            ) / 1_000_000
        with self.db.connect() as connection:
            now = int(time.time())
            session = connection.execute(
                """INSERT INTO agent_sessions
                (task_id,worker_id,started_at,finished_at,outcome,exit_code,duration_seconds,
                 token_count,estimated_cost_usd,log_path)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    task_id,
                    self.worker_id,
                    now - int(duration),
                    now,
                    "succeeded" if exit_code == 0 else "failed",
                    exit_code,
                    duration,
                    token_count,
                    estimated_cost,
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

    def prepare_worktree(self, task_id: int, env: dict[str, str]) -> tuple[Path, str]:
        branch = f"agent/task-{task_id}"
        worktree = self.state_dir / "worktrees" / f"task-{task_id}"
        if (worktree / ".git").exists():
            return worktree, branch
        worktree.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=self.repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(worktree), "origin/main"],
            cwd=self.repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
        )
        return worktree, branch

    def validate_and_publish(
        self, task_id: int, worktree: Path, branch: str, env: dict[str, str]
    ) -> tuple[int, str]:
        for raw_command in self.config.get("validation_commands", []):
            command = [str(part) for part in raw_command]
            result = subprocess.run(
                command,
                cwd=worktree,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=int(self.config.get("validation_timeout_seconds", 3600)),
                check=False,
            )
            summary = (result.stdout + result.stderr)[-4000:]
            with self.db.connect() as connection:
                connection.execute(
                    """INSERT INTO test_results(task_id,command,passed,summary,created_at)
                    VALUES (?,?,?,?,?)""",
                    (
                        task_id,
                        json.dumps(command),
                        int(result.returncode == 0),
                        summary,
                        int(time.time()),
                    ),
                )
            if result.returncode != 0:
                return result.returncode, f"validation failed: {' '.join(command)}"
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if status:
            subprocess.run(["git", "add", "-A"], cwd=worktree, env=env, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Complete agent task {task_id}"],
                cwd=worktree,
                env=env,
                check=True,
            )
        commit_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=worktree,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=worktree,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
        )
        with self.db.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO commits(task_id,commit_sha,branch,created_at) VALUES (?,?,?,?)",
                (task_id, commit_sha, branch, int(time.time())),
            )
        return 0, ""


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("runner configuration must be a JSON object")
    return cast(dict[str, Any], value)
