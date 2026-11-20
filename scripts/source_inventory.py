"""Inventory the supplied references without executing or importing foreign code."""

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    source = root / "Neuer Ordner"
    result: list[dict[str, object]] = []
    for repository in sorted(p for p in source.iterdir() if p.is_dir()):
        files: list[dict[str, str | int]] = []
        for path in sorted(p for p in repository.rglob("*") if p.is_file()):
            files.append(
                {
                    "path": path.relative_to(repository).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest(),
                }
            )
        result.append(
            {
                "repository": repository.name,
                "files": files,
                "count": len(files),
                "bytes": sum(int(file_record["bytes"]) for file_record in files),
            }
        )
    (root / "docs" / "source-inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps([{"repository": r["repository"], "count": r["count"]} for r in result]))


if __name__ == "__main__":
    main()
