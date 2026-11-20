"""Persist an honest Phase-A checkpoint. Does not import or run the application."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = "2026-11-08T23:17:06Z"
LOCAL_DATE = "2026-11-09"
MARKER = "## 2026-11-09 — Phase A: integrierte Implementierung, keine Testläufe"


def append_once(path: Path, marker: str, text: str) -> None:
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in previous:
        path.write_text(previous + "\n\n" + text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    state_path = ROOT / "RESUME_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    baseline = ROOT / "backups/implementation-20261109"
    candidates = []
    for folder in ("fur_empire", "static", "tests", "scripts", "docs/implementation", "assets"):
        candidates.extend(
            path
            for path in (ROOT / folder).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    changed = []
    for path in candidates:
        relative = path.relative_to(ROOT)
        original = baseline / relative
        if (
            not original.exists()
            or hashlib.sha256(path.read_bytes()).digest()
            != hashlib.sha256(original.read_bytes()).digest()
        ):
            changed.append(relative.as_posix())
    matrix = json.loads(
        (ROOT / "docs/implementation/IMPLEMENTATION_MATRIX.json").read_text(encoding="utf-8")
    )
    state.update(
        date=LOCAL_DATE,
        updated_at_utc=STAMP,
        objective="Vollständiger CODEX_MASTERPROMPT: 344 Original-IDs implementieren, dann Gesamtabnahme.",
        phase="A_IMPLEMENTATION_ONLY",
        current_epic="E04",
        current_state="in_progress",
        implementation_complete=False,
        current_matrix="docs/implementation/IMPLEMENTATION_MATRIX.json",
        next_feature_id="ENG-001",
        next_steps=[
            "Read the current checkpoint and DECISIONS; do not run tests, linters, app or worker against persistent data.",
            "Finish source layer audit for the original 344 contracts; unreviewed rows are not implementation evidence.",
            "Resolve global account vs per-world faction/progression, event and season policies through additive world-player state.",
            "Finish shared intelligence/target-colony handling across home changes, including fresh reports from old-home scouting.",
            "Continue versioned FUR-3 rules, missing engine functions, Terra, military and all subsequent epics.",
            "Only after full connected implementation enter Phase B and execute every required quality/DB/browser/security check.",
        ],
        database_protection={
            "persistent_databases_opened_or_modified_this_turn": False,
            "migrations_applied_this_turn": [],
            "prepared_schema_versions": [30, 31],
            "source_schema_found_before_changes": 29,
            "live_schema": "not_inspected_this_turn",
            "data_directory_changed_by_agent": False,
            "runtime_restarted_or_deployed": False,
            "source_backup": "backups/implementation-20261109",
            "source_backup_checksums": "backups/implementation-20261109/SOURCE_SHA256.txt",
            "warning": "Game initialization migrates automatically. Do not start current source with persistent Main/Staging/SQLite until Phase-B disposable migration/restore acceptance.",
        },
        latest_package={
            "status": "implemented_components_unverified_product_incomplete",
            "feature_ids": [
                "F2-048",
                "TERRA-008",
                "ENG-004",
                "E04",
                "ECO-003",
                "ECO-004",
                "K08",
                "ECO-011",
                "ENG-001",
                "W06",
                "W03",
                "WAR-006",
            ],
            "implementation": "Ten-good exchange and immutable receipts, original SVG icons, per-world home designation; strict API reachability repaired; fixed colony/world mission targets.",
            "verification": "No test, lint, syntax, type, browser, CI, migration, runtime or Docker checks executed. Only source reads, source backup and standard-library documentation generation.",
            "prepared_tests": [
                "tests/test_neutral_market.py",
                "tests/test_api.py",
                "tests/test_multiplayer.py",
                "tests/frontend.test.cjs",
            ],
            "remaining": "All global acceptance, full 344-layer review and many gameplay systems remain; see matrix and DELTA.",
        },
        remaining_ids=[row["id"] for row in matrix["features"]],
        remaining_ids_note="All 344 remain within the overall Phase-A/Phase-B contract; component implementations are not full feature acceptance.",
        changed_paths=sorted(
            set(
                changed
                + [
                    "GRAFIK.md",
                    "LICENSE_PROVENANCE.md",
                    "RESUME_STATE.json",
                    "TRACEABILITY.md",
                    "PROGRESS_LOG.md",
                    "RELEASE_CANDIDATE_REPORT.md",
                    "THIRD_PARTY_NOTICES.md",
                ]
            )
        ),
        asset_backlog="Ten neutral-market SVGs integrated_unverified; inventory of all remaining required asset families pending in GRAFIK.md.",
        blockers=[
            "No Git history in this workspace",
            "External production services/owner launch approval remain future work; no cost or publication authorized",
        ],
        last_checkpoint="2026-11-09 Phase A: actual source extended through prepared schema31; no execution of application/checks; exact source links in docs/implementation. Resume ENG-001 and complete source audit, preserving existing source schema29 work.",
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    progress = (
        MARKER
        + "\n\n"
        + (
            f"Checkpoint UTC: {STAMP}. Originaler Übergabekatalog mit 344 IDs zusätzlich zu historischen Trackern übernommen. "
            "Aktuelle Source-Baseline hatte bereits Schema29; Ausgangskopie mit SHA-256-Dateiinventar in `backups/implementation-20261109/`.\n\n"
            "Implementiert: F2-048 zehn Neutralmarktgüter, serverseitiger Werttausch/Bestände/Cap, additive Inventarfelder, "
            "unveränderliche welt-/koloniegebundene Belege (Migration030), Export/Abandon-Schutz, echte Handels-UI und zehn Original-SVGs. "
            "TERRA-008 Heimatwechsel mit weltbezogener 24h-Frist, Regelhash und Audit (Migration031). "
            "Vorhandene Queue-/Expeditions-/Allianzversorgungsaktionen im API-Vertrag erreichbar gemacht. "
            "Spielerangriffe/Transporte pinnen neue Zielkolonien; Altjobs bleiben bei Ankunft in der Ursprungswelt. "
            "Allianzversorgung behält nach Heimatwechsel das ursprüngliche berechtigte Ziel.\n\n"
            "Regressionen für Domain/API/SQLite/PostgreSQL/UI vorbereitet, **keine Tests oder sonstigen Prüfläufe ausgeführt**. "
            "Keine DB geöffnet/migriert, keine Prozesse gestartet/neu gestartet, kein Docker/Deployment, keine Abhängigkeiten geändert. "
            "Nur Source-Inspektion, Dateisicherung, Patches sowie die beiden Dokumentationsgeneratoren ausgeführt. "
            "Kein neues verified, kein Release Candidate. Nächster Punkt: ENG-001 / WorldPlayer- und Fortschrittsgrenzen sowie weiteres 344-ID-Layer-Audit."
        )
    )
    append_once(ROOT / "PROGRESS_LOG.md", MARKER, progress)
    trace_header = "## Aktueller Phase-A-Status 2026-11-09"
    append_once(
        ROOT / "TRACEABILITY.md",
        trace_header,
        trace_header + "\n\nOriginale 344-ID-Verträge und aktuelle Layer-/Komponentenstände: "
        "`docs/implementation/IMPLEMENTATION_MATRIX.json` und `.md`. "
        "Die bisherigen Tabellen und verified-Einträge sind historische Nachweise. "
        "Für diese Änderungen wurden keine Tests ausgeführt; keine aktuelle Verifikation. "
        "F2-048/TERRA-008 und die API-/Missionsverknüpfungen sind dort mit Source-, API-, DB-, UI-, "
        "Worker-, Berechtigungs-, Asset- und vorbereiteten Testpfaden dokumentiert.",
    )
    report = ROOT / "RELEASE_CANDIDATE_REPORT.md"
    current_header = "# Aktueller Stand 2026-11-09 — NICHT GETESTET / KEIN RELEASE CANDIDATE"
    historical = report.read_text(encoding="utf-8")
    if not historical.startswith(current_header):
        report.write_text(
            current_header
            + "\n\nPhase A aktiv. Neue Markt-, Heimat-, API- und Missionsänderungen sind ungetestet. "
            "344/344 Vollimplementierung ist nicht erreicht. Migrationen030/031 nur vorbereitet; "
            "keine Anwendung, DB oder Deploymentumgebung gestartet/geändert. "
            "Aktuelle Details: `docs/implementation/DELTA.md`, Matrix und `RESUME_STATE.json`. "
            "Alle nachfolgenden Prüfergebnisse stammen aus früheren Ständen und sind keine Abnahme dieser Änderungen.\n\n---\n\n"
            + historical,
            encoding="utf-8",
        )
    append_once(
        ROOT / "THIRD_PARTY_NOTICES.md",
        "## Originale Warenicons 2026-11-09",
        "## Originale Warenicons 2026-11-09\n\nZehn eigenständig gezeichnete SVGs in `static/assets/goods/`; "
        "keine Drittanbieterquelle, keine neuen Lizenz- oder Paketimporte. "
        "Metadaten/Produktionsprompts: `assets/ASSET_MANIFEST.json`; Herkunft: `LICENSE_PROVENANCE.md`.",
    )


if __name__ == "__main__":
    main()
