"""Author initial Phase-A tracking and original SVG assets without running game code.

This is a documentation generator, not a validator or a test. Existing historical
evidence is retained as history and must not be interpreted as current acceptance.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "docs" / "implementation"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    original = json.loads(
        (ROOT / "FUR_CODEX_UEBERGABE/MASTER_SPEC/spec/FEATURES.json").read_text(encoding="utf-8")
    )
    previous = json.loads((ROOT / "spec/FEATURES.json").read_text(encoding="utf-8"))
    old_by_id = {row["id"]: row for row in previous["features"]}
    rows = []
    for feature in original["features"]:
        old = old_by_id.get(feature["id"], {})
        evidence = old.get("evidence", {})
        known = old.get("status") in ("partial", "verified")
        row = {
            "id": feature["id"],
            "title": feature["title"],
            "epic": feature["planned_epic"],
            "dependencies": feature["dependencies"],
            "behavior_contract": feature["behavior_contract"],
            "acceptance": feature["acceptance"],
            "status": "existing_partial" if known else "in_progress",
            "assessment": "historical_mapping_requires_current_review",
            "current_state": "Prior evidence retained below; complete layer audit remains open.",
            "implementation_steps": [
                "Inspect current source against every acceptance item.",
                "Complete domain, persistence, API, UI, workers and policies.",
                "Prepare regression cases; execute only in Phase B.",
            ],
            "layers": {key: [] for key in ("domain", "persistence", "api", "ui", "worker")},
            "authorization": [],
            "translations": [],
            "helptext": [],
            "asset_ids": [],
            "open_details": [
                "Current source audit",
                "Complete localization and help",
                "Phase-B acceptance",
            ],
            "historical_status": old.get("status", "not_audited"),
            "historical_evidence": evidence,
            "verification": "not_run_in_phase_A",
        }
        if feature["id"].startswith("ORB-"):
            row.update(
                status="missing",
                assessment="no_orbit_domain_api_or_ui_in_current_source",
                current_state="Proposed Orbit rules exist in handover; runtime integration is absent.",
            )
        if feature["id"] == "F2-048":
            row.update(
                status="existing_partial",
                assessment="source_inspected",
                current_state="Ten-good exchange implemented; global feature acceptance remains open.",
                layers={
                    "domain": ["fur_empire/neutral_market.py", "fur_empire/game.py:Game.command"],
                    "persistence": [
                        "colonies.state.goods_inventory",
                        "neutral_goods_trades",
                        "fur_empire/migrations/030_neutral_goods_sqlite.sql",
                        "fur_empire/migrations/030_neutral_goods_postgres.sql",
                    ],
                    "api": ["POST /api/v1/command goods_trade", "GET /api/v1/state neutral_market"],
                    "ui": ["static/app.js:neutralMarketMarkup", "static/app.js:bindNeutralMarket"],
                    "worker": [
                        "not_applicable: synchronous atomic exchange; Game worker preserves colony JSON"
                    ],
                },
                authorization=[
                    "session + CSRF + origin",
                    "active owned colony",
                    "maintenance/ban/vacation gates",
                    "server prices/caps/stock",
                    "command token + payload signature",
                ],
                translations=["German UI; other locales pending"],
                helptext=["docs/game-design/NEUTRAL_MARKET.md"],
                asset_ids=[
                    "RESOURCE-" + key.upper()
                    for key in (
                        "wood",
                        "stone",
                        "ore",
                        "alloy",
                        "circuits",
                        "textiles",
                        "rations",
                        "medicine",
                        "lubricant",
                        "ceramics",
                    )
                ],
                open_details=[
                    "SQLite/PostgreSQL migration acceptance in Phase B",
                    "Five-language UI",
                    "Keyboard/mobile/browser acceptance",
                    "Material price balance",
                ],
                subfunctions=[
                    {"name": "ten_goods_atomic_exchange", "status": "implemented_unverified"}
                ],
                prepared_tests=[
                    "tests/test_neutral_market.py",
                    "tests/test_api.py",
                    "tests/frontend.test.cjs",
                ],
            )
        if feature["id"] == "TERRA-008":
            row.update(
                status="existing_partial",
                assessment="source_inspected",
                current_state="Home designation implemented with per-world 24h cooldown; global acceptance open.",
                layers={
                    "domain": [
                        "fur_empire/colony_management.py",
                        "fur_empire/systems.py:Systems.command",
                    ],
                    "persistence": [
                        "colonies.is_home",
                        "colony_home_changes",
                        "fur_empire/migrations/031_colony_home_sqlite.sql",
                        "fur_empire/migrations/031_colony_home_postgres.sql",
                    ],
                    "api": [
                        "POST /api/v1/command colony_home",
                        "GET /api/v1/state home_designation",
                    ],
                    "ui": ["static/app.js:colonyHomeMarkup", "Imperium / Kolonien"],
                    "worker": ["fixed mission targets preserved; no new timed job required"],
                },
                authorization=[
                    "session/CSRF",
                    "owned colony in active world",
                    "cooldown stored per owner/world",
                    "existing unique home index",
                    "global game transaction",
                ],
                translations=["German UI; other locales pending"],
                helptext=[
                    "docs/implementation/DECISIONS.md D03",
                    "in-screen home designation help",
                ],
                open_details=["Phase-B DB/cooldown/mission/device acceptance", "Five-language UI"],
                subfunctions=[
                    {"name": "world_scoped_home_designation", "status": "implemented_unverified"}
                ],
                prepared_tests=[
                    "tests/test_multiplayer.py",
                    "tests/test_api.py",
                    "tests/frontend.test.cjs",
                ],
            )
        if feature["id"] in ("ENG-004", "E04", "ECO-003", "ECO-004", "K08", "ECO-011"):
            row["status"] = "existing_partial"
            row["assessment"] = "command_contract_gap_inspected_and_connected"
            row["layers"]["domain"] = [
                "fur_empire/game.py:Game.command",
                "fur_empire/systems.py:Systems.command",
            ]
            row["layers"]["api"] = [
                "fur_empire/contracts.py:Action/Payload",
                "POST /api/v1/command",
            ]
            row["layers"]["ui"] = ["static/app.js:existing queue/mission/supply controls"]
            row["current_state"] = (
                "Existing domain controls now admitted by strict API contract; broader scope still open."
            )
            row["prepared_tests"] = ["tests/test_api.py:contract reachability cases"]
        if feature["id"] in ("ENG-001", "W06", "W03", "WAR-006"):
            row["status"] = "existing_partial"
            row["assessment"] = "mission_arrival_target_gap_inspected_and_connected"
            row["layers"]["domain"] = ["fur_empire/systems.py:Systems.dispatch/Systems.process_job"]
            row["layers"]["persistence"] = ["colonies.state.jobs[].target_colony_id"]
            row["layers"]["worker"] = [
                "fur_empire/worker.py:cycle",
                "Game.advance",
                "Systems.process_job",
            ]
            row["current_state"] = (
                "New player missions pin target colony; legacy arrival is source-world scoped."
            )
            row["prepared_tests"] = ["tests/test_multiplayer.py:recipient world switch arrival"]
        if feature["id"] == "ITEM-001":
            row.update(
                status="existing_partial",
                assessment="material_inventory_subset_implemented",
                current_state="Seven material stacks are colony/world-bound, capped, exported and auditable; general item lifecycle remains open.",
                layers={
                    "domain": ["fur_empire/neutral_market.py:balances/exchange"],
                    "persistence": ["colonies.state.goods_inventory", "neutral_goods_trades"],
                    "api": ["POST /api/v1/command goods_trade", "GET /api/v1/state"],
                    "ui": ["static/app.js:neutralMarketMarkup"],
                    "worker": ["existing colony JSON persistence preserves material fields"],
                },
                authorization=[
                    "active owned colony",
                    "server stock/cap validation",
                    "atomic immutable receipt",
                ],
                open_details=[
                    "General item definitions/recipes/drops",
                    "Item transfers and reserve rules",
                    "Five-language UI",
                    "Phase-B acceptance",
                ],
            )
        rows.append(row)
    write(
        DEST / "IMPLEMENTATION_MATRIX.json",
        json.dumps(
            {
                "phase": "A_IMPLEMENTATION_ONLY",
                "date": "2026-11-09",
                "implementation_complete": False,
                "source_catalog": "FUR_CODEX_UEBERGABE/MASTER_SPEC/spec/FEATURES.json",
                "status_note": "in_progress without reviewed layer paths means inventory audit, not implemented gameplay.",
                "features": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write(
        DEST / "IMPLEMENTATION_MATRIX.md",
        "# Implementierungsmatrix — Phase A\n\n"
        "344 Original-IDs. Kein aktueller Verifikationsnachweis. Die JSON-Datei enthält Originalverträge, "
        "Abhängigkeiten, Layer, offene Punkte und unveränderte historische Nachweise. "
        "`in_progress` mit offenem Source-Audit ist keine Implementierungsbehauptung.\n\n"
        "| ID | Epic | Titel | Status | Prüfung |\n|---|---|---|---|---|\n"
        + "\n".join(
            f"| {r['id']} | {r['epic']} | {r['title']} | {r['status']} | {r['assessment']} |"
            for r in rows
        )
        + "\n",
    )

    catalog = json.loads(
        (ROOT / "fur_empire/rules/neutral-market-1.json").read_text(encoding="utf-8")
    )
    motifs = {
        "wood": '<path d="M30 92V44l20-16 18 16v48M42 50h14M42 64h14M42 78h14M76 34v58M88 44v48"/>',
        "stone": '<path d="m22 82 10-35 30-17 35 22 9 35-42 13Zm10-35 31 20 34-15M63 67l1 33"/>',
        "ore": '<path d="m28 78 13-39 39-13 22 44-33 35Zm13-39 28 66M41 39l61 31M69 105l7-52"/>',
        "alloy": '<path d="m22 62 42-24 42 24-42 25Zm0 0v22l42 24 42-24V62M64 87v21M39 52l42 24"/>',
        "circuits": '<rect x="39" y="39" width="50" height="50" rx="6"/><path d="M50 24v15m14-15v15m14-15v15M50 89v15m14-15v15m14-15v15M24 50h15m-15 14h15m-15 14h15M89 50h15M89 64h15M89 78h15"/><rect x="53" y="53" width="22" height="22"/>',
        "textiles": '<path d="M28 32h60l12 62H40Zm0 0-8 56 20 6M42 42l10 40m6-40 10 40m6-40 10 40M35 54h57M37 69h59"/>',
        "rations": '<rect x="30" y="27" width="68" height="78" rx="8"/><path d="M30 42h68M45 92h38M64 55v25m0-12-14-8m14 1 13-8"/>',
        "medicine": '<rect x="24" y="36" width="80" height="66" rx="8"/><path d="M48 36V24h32v12M57 50h14v14h14v14H71v14H57V78H43V64h14Z"/>',
        "lubricant": '<path d="M48 25h32v18l17 15v46H31V58l17-15Zm0 18h32M48 25v-9h32v9M64 58s-14 16-14 24a14 14 0 0 0 28 0c0-8-14-24-14-24Z"/>',
        "ceramics": '<path d="m28 40 36-19 36 19v48l-36 19-36-19Zm0 0 36 19 36-19M64 59v48M28 64l36 19 36-19"/>',
    }
    assets = []
    for good in catalog["goods"]:
        key = good["id"]
        relative = f"static/assets/goods/{key}.svg"
        write(
            ROOT / relative,
            '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
            f'<title>{good["name"]}</title><g fill="none" stroke="#D4AD66" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round">' + motifs[key] + "</g></svg>\n",
        )
        assets.append(
            {
                "asset_id": "RESOURCE-" + key.upper(),
                "feature_ids": ["F2-048"],
                "screen": "Handel / neutrale Warenbörse",
                "path": relative,
                "type": "icon",
                "exact_size_px": [128, 128],
                "aspect_ratio": "1:1",
                "format": "SVG",
                "transparent": True,
                "variants": ["default; SVG scales to DPR 1/2/3"],
                "description": good["name"] + ": eigenes geometrisches Gold-Liniensymbol.",
                "palette": ["#D4AD66"],
                "states": ["static"],
                "alt_de": good["name"],
                "source_creator": "FUR original SVG authored in workspace",
                "license": "owned-original",
                "status": "integrated_unverified",
                "priority": "P1",
                "generation_prompt": f"Create an original 128x128 transparent SVG icon of {good['name']}; "
                "gold #D4AD66 outline, tactical cyber geometry, no text, no logos, no third-party assets.",
                "ui_binding": "static/app.js:neutralMarketMarkup; allowlisted file path, adjacent visible label",
                "acceptance": "Visible and legible at 64px, correct good, keyboard/mobile checks in Phase B.",
                "fallback": "Adjacent text, stock and price remain available without image.",
            }
        )
    write(
        ROOT / "assets/ASSET_MANIFEST.json",
        json.dumps(
            {
                "phase": "A_IMPLEMENTATION_ONLY",
                "inventory_complete": False,
                "note": "Ten newly authored icons; existing assets and all remaining required families need inventory.",
                "assets": assets,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    template = (ROOT / "FUR_CODEX_UEBERGABE/GRAFIK.md").read_text(encoding="utf-8")
    write(
        ROOT / "GRAFIK.md",
        template + "\n\n## Konkrete Integration 2026-11-09 — ungetestet\n\n"
        "Alle zehn folgenden Original-SVGs sind in der Warenbörse gebunden. "
        "Exakte Metadaten und Produktionsprompts: `assets/ASSET_MANIFEST.json`. "
        "Die übrigen Familien oben bleiben `asset_pending`; das Gesamtinventar ist noch offen.\n\n"
        "| Asset | Datei | Maße | Format | Transparenz | Status |\n|---|---|---|---|---|---|\n"
        + "\n".join(
            f"| {a['asset_id']} | {a['path']} | 128 × 128 | SVG | ja | integrated_unverified |"
            for a in assets
        )
        + "\n",
    )


if __name__ == "__main__":
    main()
