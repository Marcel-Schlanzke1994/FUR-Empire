"""Check that the canonical feature inventory agrees with both evidence records."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = ROOT / "spec" / "FEATURES.json"
TRACEABILITY_PATH = ROOT / "TRACEABILITY.md"
MATRIX_PATH = ROOT / "docs" / "implementation" / "IMPLEMENTATION_MATRIX.json"
STATUSES = {"verified", "partial", "unverified", "not_audited"}


def load_features(path: Path = FEATURES_PATH) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data["features"]
    if not isinstance(features, list):
        raise TypeError(f"{path.name} must contain a feature list")
    result: dict[str, dict[str, Any]] = {}
    for feature in features:
        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not feature_id:
            raise ValueError("Each feature must have a non-empty id")
        if feature_id in result:
            raise ValueError(f"Duplicate feature id in {path.name}: {feature_id}")
        if feature.get("status") not in STATUSES:
            raise ValueError(f"Invalid status for {feature_id}: {feature.get('status')!r}")
        result[feature_id] = feature
    return result


def trace_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line_number, line in enumerate(
        TRACEABILITY_PATH.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.startswith("|"):
            continue
        cells = re.split(r"(?<!\\)\|", line[1:-1])
        if len(cells) < 4:
            continue
        feature_id, _, status = (cell.strip() for cell in cells[:3])
        if feature_id in ("ID", "---") or set(feature_id) == {"-"}:
            continue
        if not feature_id or not status:
            raise ValueError(f"Traceability row {line_number} has an empty ID or status")
        rows.append((feature_id, status))
    return rows


def main() -> int:
    try:
        features = load_features()
        matrix = load_features(MATRIX_PATH)
        rows = trace_rows()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Traceability check could not read valid inputs: {exc}", file=sys.stderr)
        return 2

    counts = Counter(feature_id for feature_id, _ in rows)
    duplicate_ids = sorted(feature_id for feature_id, count in counts.items() if count > 1)
    trace_ids = set(counts)
    missing_ids = sorted(set(features) - trace_ids)
    extra_ids = sorted(trace_ids - set(features))
    drift = sorted(
        (feature_id, features[feature_id]["status"], status)
        for feature_id, status in rows
        if feature_id in features and features[feature_id]["status"] != status
    )

    matrix_drift = sorted(
        (
            feature_id,
            features.get(feature_id, {}).get("status"),
            matrix.get(feature_id, {}).get("status"),
        )
        for feature_id in features.keys() | matrix.keys()
        if features.get(feature_id, {}).get("status") != matrix.get(feature_id, {}).get("status")
    )

    if duplicate_ids or missing_ids or extra_ids or drift or matrix_drift:
        if duplicate_ids:
            print(f"Duplicate traceability IDs: {', '.join(duplicate_ids)}", file=sys.stderr)
        if missing_ids:
            print(f"Missing traceability IDs: {', '.join(missing_ids)}", file=sys.stderr)
        if extra_ids:
            print(f"Unknown traceability IDs: {', '.join(extra_ids)}", file=sys.stderr)
        if drift:
            print(f"Feature status drift: {drift}", file=sys.stderr)
        if matrix_drift:
            print(f"Implementation matrix status drift: {matrix_drift}", file=sys.stderr)
        return 1

    print(f"Traceability OK: {len(features)} unique feature IDs, trace and matrix match inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
