import json
import sqlite3
from contextlib import closing

import pytest

from fur_empire.game import Game, identity
from fur_empire.world_snapshot import (
    export_world,
    rehearse_sqlite_migration,
    restore_sqlite_world_backup,
    restore_world,
)


def test_blueprint_restore_requires_new_database_and_preserves_topology(tmp_path):
    source = tmp_path / "source.sqlite3"
    target = tmp_path / "target.sqlite3"
    snapshot = tmp_path / "snapshot.json"
    game = Game(source)
    with game.transaction() as db:
        world = game.create_world(db, "Snapshot frontier", 48192, 8)
        tile = db.execute(
            "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain='plain' ORDER BY x,y LIMIT 1",
            (world,),
        ).fetchone()
        db.execute(
            "INSERT INTO terra_sector_rules VALUES (?,?,?,'protected')",
            (world, tile["x"], tile["y"]),
        )
    export_world(str(source), world, snapshot)
    with pytest.raises(FileExistsError):
        restore_world(snapshot, source, "Restore test")
    imported = restore_world(snapshot, target, "Restore test")
    with Game(target).transaction() as db:
        settings = db.execute(
            "SELECT name,mode,joinable FROM world_settings WHERE world_id=?", (imported,)
        ).fetchone()
        assert dict(settings) == {"name": "Restore test", "mode": "sandbox", "joinable": 0}
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT COUNT(*) FROM world_outposts WHERE world_id=?", (imported,)
            ).fetchone()[0]
            == 8
        )
        assert (
            db.execute(
                "SELECT kind FROM terra_sector_rules WHERE world_id=? AND x=? AND y=?",
                (imported, tile["x"], tile["y"]),
            ).fetchone()[0]
            == "protected"
        )
    broken = tmp_path / "broken.json"
    envelope = json.loads(snapshot.read_bytes())
    envelope["blueprint"]["seed"] += 1
    broken.write_text(json.dumps(envelope), encoding="utf-8")
    untouched = tmp_path / "unused.sqlite3"
    with pytest.raises(ValueError, match="Prüfsumme"):
        restore_world(broken, untouched, "Restore test")
    assert not untouched.exists()


def test_full_restore_preserves_pending_jobs_and_rejects_existing_target(tmp_path):
    source = tmp_path / "full.sqlite3"
    target = tmp_path / "restored.sqlite3"
    game = Game(source)
    owner = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Restorable', 'unused')", (owner,))
        game.create(db, owner, "Restorable")
        colony = game.read(db, owner)
        colony["jobs"].append({"id": identity(), "kind": "build", "due": colony["last"] + 600})
        game.save(db, colony)
    with pytest.raises(ValueError, match="Welt oder ihr Regelstand"):
        restore_sqlite_world_backup(source, target, 99)
    assert not target.exists()
    restore_sqlite_world_backup(source, target, 1)
    with closing(sqlite3.connect(target)) as restored:
        row = restored.execute("SELECT state FROM colonies WHERE user_id=?", (owner,)).fetchone()
        assert json.loads(row[0])["jobs"] == colony["jobs"]
    with pytest.raises(FileExistsError):
        restore_sqlite_world_backup(source, target, 1)


def test_sqlite_migration_rehearsal_upgrades_only_the_new_copy(tmp_path):
    source = tmp_path / "old.sqlite3"
    target = tmp_path / "rehearsal.sqlite3"
    game = Game(source)
    owner = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Legacy Operator', 'unused')", (owner,))
        game.create(db, owner, "Legacy Operator")
        colony = game.read(db, owner)
        colony["jobs"].append({"id": identity(), "kind": "build", "due": colony["last"] + 600})
        game.save(db, colony)
        db.execute("DROP TABLE terra_alliance_attack_wings")
        db.execute("DROP TABLE terra_alliance_attacks")
        db.execute("DELETE FROM schema_versions WHERE version=73")
        db.execute("DROP TABLE terra_allied_garrisons")
        db.execute("DROP TABLE terra_allied_garrison_policies")
        db.execute("DELETE FROM schema_versions WHERE version=74")
        db.execute("DROP TABLE terra_combat_missions")
        db.execute("ALTER TABLE world_settings DROP COLUMN terra_combat_ruleset")
        db.execute("DELETE FROM schema_versions WHERE version=75")
        db.execute("ALTER TABLE world_settings DROP COLUMN terra_retreat_threshold_percent")
        db.execute("DELETE FROM schema_versions WHERE version=76")
        db.execute("DROP TABLE terra_intel_missions")
        db.execute("DELETE FROM schema_versions WHERE version=77")
        db.execute("DELETE FROM schema_versions WHERE version=78")
        db.execute("DELETE FROM schema_versions WHERE version=79")
        db.execute("DELETE FROM schema_versions WHERE version=80")
        db.execute("DROP TABLE terra_unit_wrecks")
        db.execute("DELETE FROM schema_versions WHERE version=81")
        db.execute("DROP TABLE war_score_ledger")
        db.execute("DELETE FROM schema_versions WHERE version=82")
        db.execute("DROP TABLE alliance_war_events")
        db.execute("DROP TABLE alliance_war_score_ledger")
        db.execute("DROP TABLE alliance_war_battles")
        db.execute("DROP TABLE alliance_wars")
        db.execute("DELETE FROM schema_versions WHERE version=85")
        db.execute("DROP TABLE season_alliance_standings")
        db.execute("DROP TABLE season_alliance_snapshots")
        db.execute("DROP TABLE alliance_military_score_ledger")
        db.execute("DELETE FROM schema_versions WHERE version=86")
        db.execute("DROP TABLE alliance_shared_reports")
        db.execute("DELETE FROM schema_versions WHERE version=90")
        db.execute("DROP TABLE moderation_cases")
        db.execute("DROP TABLE system_mail")
        db.execute("DROP TABLE system_announcements")
        db.execute("DROP TABLE world_rule_rollouts")
        db.execute("DELETE FROM schema_versions WHERE version=104")
        db.execute("DELETE FROM schema_versions WHERE version=105")
        db.execute("DROP TABLE account_ban_appeals")
        db.execute("DELETE FROM schema_versions WHERE version=106")
        db.execute("DROP TABLE commander_hero_xp_events")
        db.execute("DROP TABLE commander_heroes")
        db.execute("DROP TABLE player_cosmetic_unlocks")
        db.execute("DELETE FROM schema_versions WHERE version IN (91,92,93,94,95,96,103)")
        db.execute("DROP TABLE game_event_delivery_failures")
        db.execute("DROP TABLE game_event_preferences")
        db.execute("DROP TABLE player_profile_badges")
        db.execute("DROP TABLE player_profile_settings")
        db.execute("DELETE FROM schema_versions WHERE version=89")
        db.execute("DROP TABLE alliance_project_ledger")
        db.execute("DROP TABLE alliance_project_contributions")
        db.execute("DROP TABLE alliance_projects")
        db.execute("DELETE FROM schema_versions WHERE version=88")
        db.execute("DROP TABLE alliance_treasury_ledger")
        db.execute("DROP TABLE alliance_treasury_approvals")
        db.execute("DROP TABLE alliance_treasury_requests")
        db.execute("DROP TABLE alliance_treasury_balances")
        db.execute("DELETE FROM schema_versions WHERE version=87")
        db.execute("DROP TABLE alliance_transfer_requests")
        db.execute("DELETE FROM schema_versions WHERE version=84")
        db.execute("DROP TABLE alliance_role_permissions")
        db.execute("DELETE FROM schema_versions WHERE version=83")
        db.execute("DROP TABLE terra_market_convoys")
        db.execute("DELETE FROM schema_versions WHERE version=72")
        db.execute("DROP TABLE web_push_outbox")
        db.execute("DROP TABLE web_push_subscriptions")
        db.execute("DELETE FROM schema_versions WHERE version=97")
        db.execute("ALTER TABLE seasons DROP COLUMN goal_score")
        db.execute("DELETE FROM schema_versions WHERE version=98")
        db.execute("DROP TABLE season_awards")
        db.execute("DELETE FROM schema_versions WHERE version=99")
        db.execute("DROP TABLE live_event_rules")
        db.execute("ALTER TABLE events DROP COLUMN goal_score")
        db.execute("ALTER TABLE events DROP COLUMN end_bonus")
        db.execute("ALTER TABLE events DROP COLUMN end_starts")
        db.execute("ALTER TABLE events DROP COLUMN warning_hours")
        db.execute("DELETE FROM schema_versions WHERE version=100")
        db.execute("DROP TABLE season_ranking_standings")
        db.execute("DROP TABLE season_ranking_snapshots")
        db.execute("DELETE FROM schema_versions WHERE version=101")
        db.execute("DROP TABLE prestige_records")
        db.execute("DELETE FROM schema_versions WHERE version=102")
        db.execute("DROP TABLE npc_camp_events")
        db.execute("DROP TABLE npc_camp_intel")
        db.execute("DROP TABLE npc_camps")
        db.execute("DROP TABLE npc_invasion_attacks")
        db.execute("DROP TABLE npc_invasions")
        db.execute("DROP TABLE npc_attack_missions")
        db.execute("DROP TABLE terra_ruin_intel")
        db.execute("DROP TABLE terra_ruin_explorations")
        db.execute("DROP TABLE terra_boss_contributions")
        db.execute("DROP TABLE terra_boss_raids")
        db.execute("DROP TABLE npc_convoy_participants")
        db.execute("DROP TABLE npc_convoys")
        db.execute("DROP TABLE registration_acceptance")
        db.execute("DROP TABLE account_preferences")
        db.execute("DROP TABLE recurring_quest_progress")
        db.execute("DROP TABLE recurring_quest_windows")
        db.execute(
            "DELETE FROM schema_versions WHERE version IN (114,115,116,117,118,119,120,121,122,123)"
        )
        db.execute("DROP TABLE npc_attack_plans")
        db.execute("DELETE FROM schema_versions WHERE version IN (107,108,109,110,111,112,113)")
    assert rehearse_sqlite_migration(source, target) == {"schema_before": 71, "schema_after": 123}
    with closing(sqlite3.connect(source)) as original:
        assert original.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 71
    with closing(sqlite3.connect(target)) as copy:
        copy.execute("PRAGMA foreign_keys=ON")
        assert (
            json.loads(copy.execute("SELECT state FROM colonies").fetchone()[0])["jobs"]
            == colony["jobs"]
        )
        assert copy.execute("PRAGMA foreign_key_check").fetchall() == []
        copy.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-5' WHERE world_id=1"
        )
