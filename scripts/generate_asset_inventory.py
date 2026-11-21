"""Build the official Terra/Orbit asset inventory without optional dependencies."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "static" / "assets" / "game" / "asset-catalog.json"
OUTPUT_PATH = ROOT / "docs" / "asset-inventory.json"
IMAGE_EXTENSIONS = {".avif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
PACKAGES = {
    "terra": (ROOT / "FUR_EMPIRE_ASSETS" / "01_TERRA", ROOT / "static/assets/game/terra"),
    "orbit": (ROOT / "FUR_EMPIRE_ASSETS" / "02_ORBIT", ROOT / "static/assets/game/orbit"),
}
USAGE = {
    "alliance_emblems": "Allianzidentität",
    "backgrounds": "Orbit-Ansichten und responsive Hintergründe",
    "banners": "Saison- und Kampagnenbanner",
    "branding": "öffentliche Website und Anwendungsbranding",
    "buildings": "Gebäudekatalog und Kolonieausbau",
    "campaign": "Kampagnendirektiven",
    "commander": "Kommandantenprofil und Doktrinen",
    "damage_overlays": "Zustand von Terra-Festungen",
    "defenses": "Orbit-Verteidigungskatalog",
    "effects": "Orbit-Kampf- und Aktivitätseffekte",
    "factions": "Fraktionsidentität",
    "fog": "Sichtbarkeitszustände der Terra-Karte",
    "inventory": "Inventargegenstände und Belohnungen",
    "map_objects": "Terra-Kartenobjekte",
    "markers": "Terra-Karten- und Missionsmarker",
    "orbital_objects": "Objekte des Orbit-Systems",
    "outposts": "Terra-Außenposten",
    "planets": "Planeten des Orbit-Systems",
    "prestige": "Prestigebelohnungen",
    "research": "Forschungskatalog",
    "resources": "Ressourcenanzeigen",
    "ships": "Orbit-Flottenkatalog",
    "skins": "kosmetische Einheitenskins",
    "terrain": "Gelände der Terra-Karte",
    "title": "Terra-Landingpage und Titelgrafiken",
    "ui": "gemeinsame Oberflächensteuerung und Zustände",
    "units": "Einheitenkatalog und Kampfansichten",
}


@dataclass(frozen=True)
class AssetRecord:
    package: str
    source_path: str
    target_path: str
    extension: str
    width: int | None
    height: int | None
    bytes: int
    sha256: str
    catalog_key: str | None
    usage: str
    status: str
    reason: str | None


def dimensions(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    if suffix == ".webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8X":
            return (
                int.from_bytes(data[24:27], "little") + 1,
                int.from_bytes(data[27:30], "little") + 1,
            )
        if kind == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            width, height = struct.unpack("<HH", data[26:30])
            return width & 0x3FFF, height & 0x3FFF
        if kind == b"VP8L" and len(data) >= 25:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if suffix == ".svg":
        text = data[:4096].decode("utf-8", errors="replace")
        width = re.search(r'\bwidth=["\']([0-9.]+)', text)
        height = re.search(r'\bheight=["\']([0-9.]+)', text)
        if width and height:
            return round(float(width.group(1))), round(float(height.group(1)))
        viewbox = re.search(r'\bviewBox=["\'][^"\']*?([0-9.]+)\s+([0-9.]+)["\']', text)
        if viewbox:
            return round(float(viewbox.group(1))), round(float(viewbox.group(2)))
    return None, None


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_catalog() -> tuple[dict[str, Any], dict[str, str]]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    by_file: dict[str, str] = {}
    for key, entry in catalog["assets"].items():
        for file_path in entry["files"]:
            by_file[file_path.lstrip("/")] = key
    return catalog["assets"], by_file


def build() -> list[AssetRecord]:
    catalog, by_file = load_catalog()
    records: list[AssetRecord] = []
    for package, (source_root, target_root) in PACKAGES.items():
        for source in sorted(source_root.rglob("*")):
            if not source.is_file() or source.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            target = target_root / source.relative_to(source_root)
            target_name = relative(target)
            catalog_key = by_file.get(target_name)
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            target_exists = target.is_file()
            target_matches = (
                target_exists and hashlib.sha256(target.read_bytes()).hexdigest() == source_hash
            )
            entry = catalog.get(catalog_key) if catalog_key else None
            category = str(entry["category"]) if entry else source.relative_to(source_root).parts[0]
            usage = next(
                (
                    label
                    for prefix, label in USAGE.items()
                    if category == prefix or category.startswith(prefix + "/")
                ),
                "katalogisierte Spielgrafik",
            )
            width, height = dimensions(source)
            reason: str | None = None
            if not target_exists:
                status = "missing-runtime-copy"
                reason = "Keine Laufzeitkopie vorhanden."
            elif not target_matches:
                status = "runtime-copy-differs"
                reason = "Die Laufzeit-Prüfsumme weicht von der offiziellen Quelle ab."
            elif not catalog_key:
                status = "uncataloged"
                reason = "Die Laufzeitkopie fehlt im zentralen Assetkatalog."
            else:
                status = "integrated"
            records.append(
                AssetRecord(
                    package=package,
                    source_path=relative(source),
                    target_path=target_name,
                    extension=source.suffix.lower().lstrip("."),
                    width=width,
                    height=height,
                    bytes=source.stat().st_size,
                    sha256=source_hash,
                    catalog_key=catalog_key,
                    usage=usage,
                    status=status,
                    reason=reason,
                )
            )
    return records


def main() -> None:
    records = build()
    payload = {
        "schema_version": 1,
        "source_roots": {name: relative(paths[0]) for name, paths in PACKAGES.items()},
        "runtime_root": "static/assets/game",
        "totals": {
            "files": len(records),
            "bytes": sum(record.bytes for record in records),
            "integrated": sum(record.status == "integrated" for record in records),
            "unresolved": sum(record.status != "integrated" for record in records),
        },
        "assets": [asdict(record) for record in records],
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {OUTPUT_PATH.relative_to(ROOT)}: {payload['totals']['files']} files, "
        f"{payload['totals']['unresolved']} unresolved."
    )


if __name__ == "__main__":
    main()
