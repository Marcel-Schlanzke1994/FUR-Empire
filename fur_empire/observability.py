"""JSON logs with UTC timestamps; request bodies and secrets are never recorded."""

import json
import logging
import time
from collections import deque
from datetime import UTC, datetime
from threading import Lock

LATENCY_WINDOW_SECONDS = 300
_latencies: deque[tuple[float, int]] = deque(maxlen=2048)
_latency_lock = Lock()


def record_latency(milliseconds: int) -> None:
    with _latency_lock:
        _latencies.append((time.monotonic(), milliseconds))


def latency_p95() -> tuple[int | None, int]:
    cutoff = time.monotonic() - LATENCY_WINDOW_SECONDS
    with _latency_lock:
        values = sorted(value for at, value in _latencies if at >= cutoff)
    count = len(values)
    return (values[(95 * count + 99) // 100 - 1] if count else None, count)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=False,
        )


def configure() -> None:
    logger = logging.getLogger("fur")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
