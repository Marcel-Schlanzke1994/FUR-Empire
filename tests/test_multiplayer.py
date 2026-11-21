"""The same domain scenarios run against SQLite and real PostgreSQL."""

import json
import math
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
from threading import Barrier
from urllib.parse import quote

import pytest
from argon2 import PasswordHasher

from fur_empire import (
    alliance_war,
    hero_doctrines,
    heroes,
    npc_convoys,
    recurring_quests,
    ruin_exploration,
    terra_alliance,
    terra_combat,
    terra_defense,
    terra_garrison,
    terra_intelligence,
    web_push,
)
from fur_empire.expeditions import RULES as EXPEDITION_RULES
from fur_empire.expeditions import RULES_DIGEST as EXPEDITION_RULES_DIGEST
from fur_empire.expeditions import resolve_expedition, validate_ruleset
from fur_empire.game import (
    FACTION_RESEARCH,
    REGISTRY,
    RULES_DIGEST,
    RULES_SNAPSHOT,
    UNITS,
    Game,
    JobProcessingError,
    RuleError,
    identity,
)
from fur_empire.identity import AccountAction, Accounts, digest, totp
from fur_empire.item_drops import RULE_HASH as ITEM_DROP_HASH
from fur_empire.item_drops import RULES as ITEM_DROP_RULES
from fur_empire.item_drops import resolve as resolve_item_drops
from fur_empire.item_drops import view as item_drop_view
from fur_empire.manage import backup
from fur_empire.terrain import PRODUCTION_PERCENT, defense_with_terrain, travel_costs, travel_times
from fur_empire.worker import cycle

_PUSH_P256DH = (
    "BGsX0fLhLEJH-Lzm5WOkQPJ3A32BLeszoPShOUXYmMKWT-NC4v4af5uO5-tKfA-eFivOM1drMV7Oy7ZAaDe_UfU"
)
_PUSH_AUTH = "AAAAAAAAAAAAAAAAAAAAAA"


@pytest.fixture(params=["sqlite", "postgres"])
def universe(request, tmp_path, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    pg = None
    schema = "fur_test_" + identity().replace("-", "")
    if request.param == "postgres":
        base = os.getenv("FUR_TEST_POSTGRES")
        if not base:
            pytest.skip("FUR_TEST_POSTGRES not configured")
        import psycopg
        from psycopg import sql

        pg = psycopg.connect(base, autocommit=True)
        pg.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        target = (
            base + ("?" if "?" not in base else "&") + "options=" + quote("-csearch_path=" + schema)
        )
    else:
        target = str(tmp_path / "world.sqlite3")
    game = Game(target)
    users = []
    with game.transaction() as db:
        for name in ("Alpha", "Bravo", "Charlie"):
            user = identity()
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, name, "unused"))
            game.create(db, user, name)
            db.execute("UPDATE profiles SET joined=? WHERE user_id=?", (clock[0] - 7200, user))
            users.append(user)
    yield game, users, clock
    if pg:
        from psycopg import sql

        pg.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        pg.close()


def command(universe, index, action, payload=None, token=None):
    game, users, _ = universe
    with game.transaction() as db:
        return game.command(db, users[index], action, payload or {}, token or identity())


def test_npc_convoy_pve_roles_late_worker_and_once_only_rewards(universe):
    game, users, clock = universe
    request = {"name": "Grenzhandel"}
    assert state(universe, 0)["npc_convoy"]["convoy"] is None
    with pytest.raises(RuleError, match="Spielleitung"):
        command(universe, 0, "admin_npc_convoy_schedule", request)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        for user in users:
            colony = game.read(db, user)
            colony["units"]["ranger"] = 40
            colony["resources"] = [4000, 4000, 4000]
            game.save(db, colony)
    scheduled = command(universe, 0, "admin_npc_convoy_schedule", request)
    convoy = scheduled["npc_convoy"]["convoy"]
    target = {"key": convoy["id"]}
    with pytest.raises(RuleError, match="bereits"):
        command(universe, 0, "admin_npc_convoy_schedule", request)
    with pytest.raises(RuleError, match="Zeitfenster"):
        command(universe, 0, "npc_convoy_escort", {**target, "count": 10})
    with pytest.raises(RuleError, match="keine Belohnung"):
        command(universe, 0, "npc_convoy_claim", target)
    with game.transaction() as db:
        raw = db.execute("SELECT route FROM npc_convoys WHERE id=?", (convoy["id"],)).fetchone()
        route = json.loads(raw["route"])
        for (x, y), (nx, ny) in pairwise(route):
            assert abs(x - nx) + abs(y - ny) == 1
        kinds = {
            (row["x"], row["y"]): row["terrain"]
            for row in db.execute("SELECT x,y,terrain FROM world_terrain WHERE world_id=1")
        }
        assert all(kinds[tuple(point)] != "water" for point in route)
    clock[0] = convoy["starts"]
    for index, (action, count) in enumerate(
        (("npc_convoy_escort", 10), ("npc_convoy_raid", 15), ("npc_convoy_raid", 1))
    ):
        token = identity()
        first = command(universe, index, action, {**target, "count": count}, token)
        repeated = command(universe, index, action, {**target, "count": count}, token)
        assert first["units"] == repeated["units"]
        assert repeated["units"]["ranger"] == 40 - count
        assert repeated["npc_convoy"]["convoy"]["own"]["rangers"] == count
        with pytest.raises(RuleError, match="bereits genutzt"):
            command(universe, index, action, {**target, "count": count})
    # The worker is offline for the whole event. Due times still determine the result.
    clock[0] = convoy["ends"] + 600
    with game.transaction() as db:
        game.advance(db, clock[0])
        game.advance(db, clock[0])
        assert [game.read(db, user)["units"]["ranger"] for user in users] == [39, 38, 39]
        for index, user in enumerate(users):
            row = db.execute(
                "SELECT victory,survivors,reward_ore,status FROM npc_convoy_participants "
                "WHERE convoy_id=? AND user_id=?",
                (convoy["id"], user),
            ).fetchone()
            assert row["victory"] == int(index != 2)
            assert row["survivors"] == [9, 13, 0][index]
            assert row["reward_ore"] == (300 if index != 2 else 0)
            assert row["status"] == "completed"
    assert state(universe, 2)["npc_convoy"]["rewards"] == []
    with pytest.raises(RuleError, match="keine Belohnung"):
        command(universe, 2, "npc_convoy_claim", target)
    barrier = Barrier(2)

    def compete(token):
        barrier.wait(timeout=10)
        try:
            return command(universe, 0, "npc_convoy_claim", target, token)
        except RuleError as exc:
            assert "keine Belohnung" in str(exc)
            return None

    tokens = [identity(), identity()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, tokens))
    assert sum(result is not None for result in results) == 1
    winner = tokens[0] if results[0] is not None else tokens[1]
    repeated = command(universe, 0, "npc_convoy_claim", target, winner)
    assert repeated["reserve"][2] == 300
    assert not repeated["npc_convoy"]["rewards"]
    assert command(universe, 1, "npc_convoy_claim", target)["reserve"][2] == 300


def test_npc_convoy_next_checkpoint_recall_and_world_isolation(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        colony = game.read(db, users[0])
        colony["units"]["ranger"] = 20
        game.save(db, colony)
    convoy = command(universe, 0, "admin_npc_convoy_schedule", {"name": "Abendroute"})[
        "npc_convoy"
    ]["convoy"]
    target = {"key": convoy["id"]}
    clock[0] = convoy["checkpoints"][0]["ends"] - 1
    dispatched = command(universe, 0, "npc_convoy_escort", {**target, "count": 10})
    own = dispatched["npc_convoy"]["convoy"]["own"]
    assert own["due"] >= convoy["checkpoints"][1]["starts"]
    assert own["due"] < convoy["checkpoints"][1]["ends"]
    recall = {"key": own["mission_id"]}
    with pytest.raises(RuleError, match="aktiven Kolonie"):
        command(universe, 1, "npc_convoy_recall", recall)
    token = identity()
    recalled = command(universe, 0, "npc_convoy_recall", recall, token)
    assert recalled["npc_convoy"]["convoy"]["own"]["status"] == "cancelled"
    assert command(universe, 0, "npc_convoy_recall", recall, token)["units"]["ranger"] == 10
    with pytest.raises(RuleError, match="bereits genutzt"):
        command(universe, 0, "npc_convoy_raid", {**target, "count": 5})
    clock[0] = max(job["due"] for job in recalled["jobs"])
    with game.transaction() as db:
        game.advance(db, clock[0])
        game.advance(db, clock[0])
        assert game.read(db, users[0])["units"]["ranger"] == 20
        second = game.create_world(db, "Convoy isolation", 123456, 8)
    other = command(universe, 0, "world_join", {"world_id": second})
    assert other["npc_convoy"]["convoy"] is None
    assert other["npc_convoy"]["rewards"] == []
    with pytest.raises(RuleError, match="aktiven Welt"):
        command(universe, 0, "npc_convoy_claim", target)
    clock[0] = convoy["ends"]
    with pytest.raises(RuleError, match="Zeitfenster"):
        command(universe, 1, "npc_convoy_escort", {**target, "count": 1})


def test_npc_convoy_finite_slots_and_disconnected_route(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        colony = game.read(db, users[0])
        colony["units"]["ranger"] = 20
        game.save(db, colony)
    convoy = command(universe, 0, "admin_npc_convoy_schedule", {"name": "Endlicher Handel"})[
        "npc_convoy"
    ]["convoy"]
    clock[0] = convoy["starts"]
    with game.transaction() as db:
        origin = (colony["x"], colony["y"])
        for index in range(int(npc_convoys.RULES["slots"])):
            user = identity()
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, f"Slot {index}", "unused"))
            npc_convoys.join(db, 1, convoy["id"], user, identity(), origin, "escort", 10, clock[0])
    with pytest.raises(RuleError, match="Teilnahmeplätze"):
        command(universe, 0, "npc_convoy_escort", {"key": convoy["id"], "count": 10})
    assert state(universe, 0)["units"]["ranger"] == 20
    # Scheduling never invents a route through blocked terrain.
    clock[0] = convoy["ends"]
    with game.transaction() as db:
        db.execute("UPDATE world_terrain SET terrain='water' WHERE world_id=1")
        with pytest.raises(npc_convoys.ConvoyError, match="begehbare Handelsroute"):
            npc_convoys.schedule(db, 1, identity(), "Gesperrt", clock[0])
        assert db.execute("SELECT COUNT(*) FROM npc_convoys").fetchone()[0] == 1


def test_recurring_quest_completion_and_once_only_reward_through_normal_commands(universe):
    game, users, clock = universe
    setup = {"enabled": True}
    assert state(universe, 0)["recurring_quests"]["quests"] == []
    with pytest.raises(RuleError, match="Spielleitung"):
        command(universe, 1, "admin_recurring_quests", setup)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        colony = game.read(db, users[0])
        colony["buildings"].update(barracks=1, lab=1, storage=3)
        colony["resources"] = [8000, 8000, 8000]
        game.save(db, colony)
    # Keep the entire scenario inside a single UTC day and week.
    clock[0] = recurring_quests.periods(clock[0])["daily"][1] + 3600
    command(universe, 0, "admin_recurring_quests", setup)
    queued = command(universe, 0, "build", {"key": "wood"})
    assert all(row["progress"] == 0 for row in queued["recurring_quests"]["quests"])
    command(universe, 0, "research", {"key": "engineering"})
    queued = command(universe, 0, "train", {"key": "ranger", "count": 20})
    clock[0] = max(job["due"] for job in queued["jobs"])
    with game.transaction() as db:
        game.advance(db, clock[0])
        game.advance(db, clock[0])
        colony = game.read(db, users[0])
        cap = 2000 + colony["buildings"]["storage"] * 2000
        colony["resources"] = [cap, cap, cap]
        game.save(db, colony)

    current = command(universe, 0, "admin_recurring_quests", {"enabled": False})
    assert not current["recurring_quests"]["enabled"]
    progress = {row["id"]: row for row in current["recurring_quests"]["quests"]}
    assert {key: row["progress"] for key, row in progress.items()} == {
        "daily-build": 1,
        "daily-research": 1,
        "daily-train": 4,
        "weekly-build": 1,
        "weekly-research": 1,
        "weekly-train": 20,
    }
    weekly = progress["weekly-train"]
    payload = {"key": weekly["key"]}
    assert not state(universe, 1)["recurring_quests"]["quests"]
    with pytest.raises(RuleError, match="Aufgabenbelohnung"):
        command(universe, 1, "recurring_quest_claim", payload)

    barrier = Barrier(2)

    def compete(token):
        barrier.wait(timeout=10)
        try:
            return command(universe, 0, "recurring_quest_claim", payload, token)
        except RuleError as error:
            assert "Aufgabenbelohnung" in str(error)
            return None

    tokens = (identity(), identity())
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(compete, tokens))
    assert sum(value is not None for value in outcomes) == 1
    winner = tokens[0] if outcomes[0] is not None else tokens[1]
    repeated = command(universe, 0, "recurring_quest_claim", payload, winner)
    assert repeated["reserve"] == list(weekly["reward"])
    assert next(row for row in repeated["recurring_quests"]["quests"] if row["id"] == weekly["id"])[
        "claimed"
    ]
    assert repeated["claimed"] == current["claimed"]

    with game.transaction() as db:
        second = game.create_world(db, "Quest isolation", 112358, 8)
    selected = command(universe, 0, "world_join", {"world_id": second})
    assert selected["recurring_quests"]["quests"] == []
    with pytest.raises(RuleError, match="Aufgabenbelohnung"):
        command(universe, 0, "recurring_quest_claim", payload)


def test_recurring_quest_utc_rollover_uses_order_due_time(universe):
    game, users, clock = universe
    monday = recurring_quests.periods(clock[0])["weekly"][1]
    clock[0] = monday - 600
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    enabled = command(universe, 0, "admin_recurring_quests", {"enabled": True})
    build = next(row for row in enabled["recurring_quests"]["quests"] if row["id"] == "daily-build")
    week = next(row for row in enabled["recurring_quests"]["quests"] if row["id"] == "weekly-build")
    assert build["ends"] == week["ends"] == monday
    queued = command(universe, 0, "build", {"key": "wood"})
    assert queued["jobs"][0]["due"] < monday
    clock[0] = monday
    with game.transaction() as db:
        game.advance(db, clock[0])
        progress = {
            row["quest_id"]: (row["period_start"], row["progress"])
            for row in db.execute(
                "SELECT quest_id,period_start,progress FROM recurring_quest_progress"
            )
        }
    assert progress == {
        "daily-build": (monday - recurring_quests.DAY, 1),
        "weekly-build": (monday - recurring_quests.WEEK, 1),
    }
    next_quests = state(universe, 0)["recurring_quests"]["quests"]
    assert {row["ends"] for row in next_quests} == {
        monday + recurring_quests.DAY,
        monday + recurring_quests.WEEK,
    }
    assert all(row["progress"] == 0 for row in next_quests)
    with pytest.raises(RuleError, match="abgelaufen"):
        command(universe, 0, "recurring_quest_claim", {"key": build["key"]})
    with pytest.raises(RuleError, match="abgelaufen"):
        command(universe, 0, "recurring_quest_claim", {"key": week["key"]})


def test_web_push_subscription_owner_limit_endpoint_ssrf_and_unsubscribe(tmp_path, monkeypatch):
    game = Game(tmp_path / "push.sqlite3")
    users = [identity(), identity()]
    with game.transaction() as db:
        for index, user in enumerate(users):
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, f"Push{index}", "unused"))
            game.create(db, user, f"Push{index}")
        with pytest.raises(ValueError):
            web_push.validate_endpoint("http://127.0.0.1/private")
        with pytest.raises(ValueError):
            web_push.validate_endpoint("https://localhost/private")
        with pytest.raises(ValueError, match="Anbieter"):
            web_push.validate_endpoint("https://push.example.test/subscription")
        monkeypatch.setattr(
            web_push.socket,
            "getaddrinfo",
            lambda *_args, **_kwargs: [(None, None, None, None, ("8.8.8.8", 443))],
        )
        web_push.validate_endpoint("https://fcm.googleapis.com/fcm/send/endpoint")
        monkeypatch.setattr(web_push, "validate_endpoint", lambda endpoint: None)
        result = web_push.subscribe(
            db, users[0], "https://push.example.test/subscription", _PUSH_P256DH, _PUSH_AUTH, 100
        )
        assert result["created"] is True
        with pytest.raises(ValueError, match="anderen Konto"):
            web_push.subscribe(
                db,
                users[1],
                "https://push.example.test/subscription",
                _PUSH_P256DH,
                _PUSH_AUTH,
                101,
            )
        for index in range(web_push.MAX_SUBSCRIPTIONS - 1):
            web_push.subscribe(
                db, users[0], f"https://push.example.test/{index}", _PUSH_P256DH, _PUSH_AUTH, 102
            )
        with pytest.raises(ValueError, match="höchstens fünf"):
            web_push.subscribe(
                db, users[0], "https://push.example.test/sixth", _PUSH_P256DH, _PUSH_AUTH, 103
            )
        assert web_push.unsubscribe(db, users[1], "https://push.example.test/subscription") is False
        assert web_push.unsubscribe(db, users[0], "https://push.example.test/subscription") is True


def test_web_push_event_queue_is_generic_deduplicated_muted_and_expires(tmp_path, monkeypatch):
    game = Game(tmp_path / "push-queue.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "PushQueue", "unused"))
        game.create(db, user, "PushQueue")
        monkeypatch.setattr(web_push, "validate_endpoint", lambda endpoint: None)
        subscription = web_push.subscribe(
            db, user, "https://push.example.test/one", _PUSH_P256DH, _PUSH_AUTH, 100
        )
        from fur_empire import game_events

        game_events.stage(db, "event-1", user, 1, "attack", 110)
        game_events.publish(db)
        game_events.stage(db, "event-1", user, 1, "attack", 110)
        game_events.publish(db)
        queued = db.execute("SELECT * FROM web_push_outbox").fetchall()
        assert len(queued) == 1
        assert set(json.loads(web_push.GENERIC_PAYLOAD)) == {"title", "body", "url", "tag"}
        assert "attack" not in web_push.GENERIC_PAYLOAD
        db.execute(
            "INSERT INTO game_event_preferences(user_id,category,muted,updated) VALUES (?,?,1,?)",
            (user, "military", 120),
        )
        game_events.stage(db, "event-muted", user, 1, "attack", 121)
        game_events.publish(db)
        assert db.execute("SELECT count(*) FROM web_push_outbox").fetchone()[0] == 1
        web_push.cleanup(db, 110 + web_push.MAX_AGE_SECONDS)
        assert db.execute("SELECT count(*) FROM web_push_outbox").fetchone()[0] == 0
        assert db.execute(
            "SELECT 1 FROM web_push_subscriptions WHERE id=?", (subscription["id"],)
        ).fetchone()


def test_web_push_sender_retries_and_removes_expired_provider_subscriptions(tmp_path, monkeypatch):
    import sys
    import types
    from types import SimpleNamespace

    game = Game(tmp_path / "push-delivery.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "PushDelivery", "unused"))
        game.create(db, user, "PushDelivery")
        monkeypatch.setattr(web_push, "validate_endpoint", lambda endpoint: None)
        subscription = web_push.subscribe(
            db,
            user,
            "https://push.example.test/one",
            _PUSH_P256DH,
            _PUSH_AUTH,
            100,
        )
        db.execute(
            "INSERT INTO web_push_outbox(id,subscription_id,event_id,available_at,created) VALUES (?,?,?,?,?)",
            (identity(), subscription["id"], "event-delivery", 100, 100),
        )

    class PushFailure(Exception):
        response = SimpleNamespace(status_code=503)

    settings = SimpleNamespace(
        webpush_public_key="public",
        webpush_private_key_file="private.pem",
        webpush_subject="mailto:ops@example.test",
    )
    monkeypatch.setattr(web_push, "validate_endpoint", lambda endpoint: None)
    monkeypatch.setitem(
        sys.modules,
        "requests",
        SimpleNamespace(Session=lambda: SimpleNamespace(trust_env=True)),
    )
    request_errors = types.ModuleType("requests.exceptions")
    request_errors.RequestException = OSError
    monkeypatch.setitem(sys.modules, "requests.exceptions", request_errors)
    monkeypatch.setitem(
        sys.modules,
        "pywebpush",
        SimpleNamespace(
            WebPushException=PushFailure,
            webpush=lambda *args, **kwargs: (_ for _ in ()).throw(PushFailure()),
        ),
    )
    web_push.deliver_batch(game, 100, settings)
    with game.transaction() as db:
        queued = db.execute("SELECT attempts,available_at FROM web_push_outbox").fetchone()
        assert queued["attempts"] == 1 and queued["available_at"] == 130
        row = db.execute("SELECT id FROM web_push_outbox").fetchone()
        db.execute(
            "UPDATE web_push_outbox SET available_at=100,lease_until=0 WHERE id=?", (row["id"],)
        )

    class GoneFailure(PushFailure):
        response = SimpleNamespace(status_code=410)

    monkeypatch.setitem(
        sys.modules,
        "pywebpush",
        SimpleNamespace(
            WebPushException=GoneFailure,
            webpush=lambda *args, **kwargs: (_ for _ in ()).throw(GoneFailure()),
        ),
    )
    web_push.deliver_batch(game, 200, settings)
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM web_push_subscriptions").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM web_push_outbox").fetchone()[0] == 0


def prepare_terra_alliance_target(universe):
    game, users, clock = universe
    alliance_id = identity()
    with game.transaction() as db:
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (alliance_id, "ACS", "ACS test", "", users[0], clock[0]),
        )
        for index in (0, 1):
            db.execute(
                "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
                (users[index], alliance_id, "leader" if index == 0 else "member"),
            )
            colony = game.read(db, users[index])
            colony["units"]["ranger"] = 100
            game.save(db, colony)
        posts = game.world_outposts(db, 1)
        target = next(
            post
            for post in posts
            if post["owner"] is None
            and post["tier"] == 1
            and all(
                (post["x"], post["y"])
                in travel_times(
                    db, (game.read(db, users[index])["x"], game.read(db, users[index])["y"]), 1
                )
                for index in (0, 1)
            )
        )
        for index in (0, 1):
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
                (users[index], 1, target["x"], target["y"], clock[0]),
            )
    return target


def state(universe, index):
    game, users, _ = universe
    with game.transaction() as db:
        return game.view(db, users[index])


def test_new_player_starting_resources_and_production_are_adapter_independent(universe):
    game, _, clock = universe
    fresh_user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?, 'Fresh Pilot', 'unused')", (fresh_user,))
        game.create(db, fresh_user, "Fresh Pilot")
        colony = game.read(db, fresh_user)
        joined = int(
            db.execute("SELECT joined FROM profiles WHERE user_id=?", (fresh_user,)).fetchone()[0]
        )

        assert colony["terrain"] != "water"
        assert colony["resources"] == [1200, 1000, 800]
        assert [colony["buildings"][key] for key in ("wood", "stone", "ore")] == [1, 1, 1]
        assert joined + 3600 >= clock[0]


def test_expedition_template_schema_14_migrates_without_changing_player_world(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colonies_before = [
            (row["user_id"], row["colony_id"], row["world_id"], row["state"])
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        world_before = [
            (row["world_id"], row["target_id"], row["state"])
            for row in db.execute(
                "SELECT world_id,target_id,state FROM world_outposts ORDER BY world_id,target_id"
            )
        ]
        db.execute("DROP TABLE mission_templates")
        db.execute("DROP TABLE alliance_applications")
        db.execute("DELETE FROM schema_versions WHERE version=13")
        db.execute("DELETE FROM schema_versions WHERE version=14")
        db.execute("DELETE FROM schema_versions WHERE version=15")
        migration = (
            Path(__file__).parent.parent
            / "fur_empire"
            / "migrations"
            / (
                "013_mission_templates_postgres.sql"
                if db.postgres
                else "013_mission_templates_sqlite.sql"
            )
        )
        db.executescript(migration.read_text(encoding="utf-8"))
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("existing-template", users[0], "Existing profile", "attack", '{"ranger":2}', False, 1),
        )

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=90").fetchone()
        assert db.execute("SELECT count(*) FROM alliance_applications").fetchone()[0] == 0
        assert [
            (row["user_id"], row["colony_id"], row["world_id"], row["state"])
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before
        assert [
            (row["world_id"], row["target_id"], row["state"])
            for row in db.execute(
                "SELECT world_id,target_id,state FROM world_outposts ORDER BY world_id,target_id"
            )
        ] == world_before
        saved_template = db.execute(
            "SELECT id,owner,name,mode,army,capture,created FROM mission_templates"
        ).fetchone()
        assert tuple(
            saved_template[key]
            for key in ("id", "owner", "name", "mode", "army", "capture", "created")
        ) == (
            "existing-template",
            users[0],
            "Existing profile",
            "attack",
            '{"ranger":2}',
            False if db.postgres else 0,
            1,
        )
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("expedition-template", users[0], "Frontier", "expedition", '{"ranger":1}', False, 2),
        )
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == len(users)


def test_production_template_schema_19_migrates_without_changing_player_data(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        outpost_count = db.execute("SELECT count(*) FROM world_outposts").fetchone()[0]
        db.execute("DROP TABLE production_templates")
        db.execute("DELETE FROM schema_versions WHERE version=19")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM production_templates").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == len(users)
        assert db.execute("SELECT count(*) FROM world_outposts").fetchone()[0] == outpost_count
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_social_schema_20_migrates_without_changing_existing_accounts_or_colonies(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE friendships")
        db.execute("DROP TABLE player_blocks")
        db.execute("DELETE FROM schema_versions WHERE version=20")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM friendships").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM player_blocks").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_player_notes_schema_21_migrates_without_changing_player_data(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE player_notes")
        db.execute("DELETE FROM schema_versions WHERE version=21")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM player_notes").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_player_profile_schema_89_defaults_existing_accounts_to_private(universe):
    game, users, _ = universe
    with game.transaction() as db:
        accounts_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        db.execute("DROP TABLE moderation_cases")
        db.execute("DROP TABLE system_mail")
        db.execute("DROP TABLE system_announcements")
        db.execute("DROP TABLE alliance_shared_reports")
        db.execute("DELETE FROM schema_versions WHERE version IN (90,91,92)")
        db.execute("DROP TABLE player_profile_badges")
        db.execute("DROP TABLE player_cosmetic_unlocks")
        db.execute("DROP TABLE player_profile_settings")
        db.execute("DELETE FROM schema_versions WHERE version=96")
        db.execute("DELETE FROM schema_versions WHERE version=89")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM player_profile_settings").fetchone()[0] == len(
            users
        )
        assert (
            db.execute(
                "SELECT count(*) FROM player_profile_settings WHERE visibility<>'private' "
                "OR title_id<>'none'"
            ).fetchone()[0]
            == 0
        )
        assert db.execute("SELECT count(*) FROM player_profile_badges").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM player_cosmetic_unlocks").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT count(*) FROM player_profile_settings WHERE reward_title_id<>'none' "
                "OR skin_id<>'none' OR banner_id<>'none'"
            ).fetchone()[0]
            == 0
        )
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == accounts_before


def test_alliance_shared_reports_schema_90_migrates_without_changing_player_data(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        accounts_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE alliance_shared_reports")
        db.execute("DROP TABLE moderation_cases")
        db.execute("DROP TABLE system_mail")
        db.execute("DROP TABLE system_announcements")
        db.execute("DELETE FROM schema_versions WHERE version IN (90,91,92)")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM alliance_shared_reports").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM moderation_cases").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == accounts_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_schema_105_revokes_legacy_attacker_perspective_report_shares(universe):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "SAFE", "name": "Safe Sharing"})
    with game.transaction() as db:
        alliance_id = str(game.systems.member(db, users[0])["alliance_id"])
        db.execute(
            "INSERT INTO alliance_shared_reports"
            "(id,owner_id,alliance_id,world_id,report_id,summary,created) VALUES (?,?,?,?,?,?,?)",
            (
                identity(),
                users[0],
                alliance_id,
                1,
                identity(),
                json.dumps({"outcome": "victory", "rounds": []}),
                clock[0],
            ),
        )
        db.execute("DELETE FROM schema_versions WHERE version=105")
        account_count = int(db.execute("SELECT count(*) FROM users").fetchone()[0])
    Game(game.path)
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_shared_reports").fetchone()[0] == 0
        assert int(db.execute("SELECT count(*) FROM users").fetchone()[0]) == account_count
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=105").fetchone()


def test_schema_106_adds_ban_appeals_without_changing_existing_accounts(universe):
    game, users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        db.execute("DROP TABLE account_ban_appeals")
        db.execute("DELETE FROM schema_versions WHERE version=106")

    from fur_empire.game import Game

    migrated = Game(game.path)
    with migrated.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert (
            db.execute("SELECT count(*) FROM account_ban_appeals WHERE status='open'").fetchone()[0]
            == 0
        )
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before

        banned = db.execute("SELECT banned FROM profiles WHERE user_id=?", (users[0],)).fetchone()
        assert banned is not None


def test_announcements_and_system_mail_schema_92_migrate_additively(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        accounts_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE system_mail")
        db.execute("DROP TABLE system_announcements")
        db.execute("DELETE FROM schema_versions WHERE version=92")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM system_mail").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM system_announcements").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == accounts_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_public_announcements_and_private_system_mail_enforce_scope_and_roles(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='moderator' WHERE user_id=?", (users[0],))
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[2],))

    command(
        universe,
        0,
        "admin_announcement_create",
        {"target_kind": "world", "world_id": 1, "name": "Weltpflege", "body": "Heute 20 Uhr."},
    )
    with game.transaction() as db:
        world_entries, _ = game.systems.system_announcement_page(db, 1)
        other_world_entries, _ = game.systems.system_announcement_page(db, 999)
        assert len(world_entries) == 1
        assert world_entries[0]["title"] == "Weltpflege"
        assert other_world_entries == []
    with pytest.raises(RuleError, match="Globale Ankündigungen"):
        command(
            universe,
            0,
            "admin_announcement_create",
            {"target_kind": "global", "name": "Global", "body": "Nicht erlaubt."},
        )
    with pytest.raises(RuleError, match="aktive Welt"):
        command(
            universe,
            0,
            "admin_announcement_create",
            {"target_kind": "world", "world_id": 999, "name": "Fremde Welt", "body": "Nein."},
        )

    command(
        universe,
        2,
        "admin_announcement_create",
        {"target_kind": "global", "name": "Betriebshinweis", "body": "Willkommen."},
    )
    command(
        universe,
        2,
        "admin_mail_send",
        {"key": users[1], "name": "Kontohinweis", "body": "Nur an Bravo."},
    )
    assert len(state(universe, 0)["announcements"]) == 2
    scheduled_at = clock[0] + 600
    command(
        universe,
        0,
        "admin_announcement_create",
        {
            "target_kind": "world",
            "world_id": 1,
            "name": "Notfallfenster",
            "body": "Geplante Notfallinformation.",
            "publish_at": scheduled_at,
            "emergency": True,
        },
    )
    moderator_view = state(universe, 0)["announcements"]
    assert len(moderator_view) == 3
    scheduled_item = next(item for item in moderator_view if item["title"] == "Notfallfenster")
    assert scheduled_item["publish_at"] == scheduled_at
    assert scheduled_item["emergency"] is True
    assert len(state(universe, 1)["announcements"]) == 2
    with pytest.raises(RuleError, match="nächsten 90 Tage"):
        command(
            universe,
            0,
            "admin_announcement_create",
            {
                "target_kind": "world",
                "world_id": 1,
                "name": "Zu weit voraus",
                "body": "Wird abgewiesen.",
                "publish_at": clock[0] + 91 * 86400,
            },
        )
    with pytest.raises(RuleError, match="Notfallkennzeichnung"):
        command(
            universe,
            0,
            "admin_announcement_create",
            {
                "target_kind": "world",
                "world_id": 1,
                "name": "Ungültig",
                "body": "Wird abgewiesen.",
                "emergency": "yes",
            },
        )
    clock[0] = scheduled_at + 1
    published_items = state(universe, 1)["announcements"]
    assert published_items[0]["title"] == "Notfallfenster"
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE action='admin_announcement_create' AND details LIKE ?",
            ("%Notfallfenster%",),
        ).fetchone()[0]
        audit_details = json.loads(audit)
        assert audit_details["emergency"] is True
        assert audit_details["publish_at"] == scheduled_at
    inbox = state(universe, 1)["system_mail"]
    assert len(inbox) == 1
    assert inbox[0]["title"] == "Kontohinweis"
    assert state(universe, 0)["system_mail"] == []
    assert state(universe, 2)["system_mail"] == []
    with pytest.raises(RuleError, match="nur die Spielleitung"):
        command(
            universe,
            0,
            "admin_mail_send",
            {"key": users[1], "name": "Nein", "body": "Moderator darf keine Privatpost senden."},
        )
    with pytest.raises(RuleError, match="nicht vorhanden"):
        command(universe, 0, "mail_read", {"key": inbox[0]["id"]})
    command(universe, 1, "mail_read", {"key": inbox[0]["id"]})
    command(universe, 1, "mail_read", {"key": inbox[0]["id"]})
    assert state(universe, 1)["system_mail"][0]["read_at"] is not None
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE action='admin_mail_send' ORDER BY created DESC LIMIT 1"
        ).fetchone()
        assert "Nur an Bravo" not in audit["details"]


def test_scheduled_announcement_migration_preserves_legacy_publication_time(universe):
    game, users, clock = universe
    announcement_id = identity()
    created = clock[0] - 1200
    with game.transaction() as db:
        db.execute(
            "INSERT INTO system_announcements(id,world_id,author_id,title,body,created) "
            "VALUES (?,?,?,?,?,?)",
            (announcement_id, 1, users[0], "Bestandshinweis", "Unverändert sichtbar", created),
        )
        users_before = db.execute("SELECT count(*) FROM users").fetchone()[0]
        colonies_before = db.execute("SELECT count(*) FROM colonies").fetchone()[0]
        db.execute("DROP INDEX system_announcements_publish_idx")
        db.execute("ALTER TABLE system_announcements DROP COLUMN emergency")
        db.execute("ALTER TABLE system_announcements DROP COLUMN publish_at")
        db.execute("DELETE FROM schema_versions WHERE version=103")

    Game(game.path)
    with game.transaction() as db:
        migrated = db.execute(
            "SELECT publish_at,emergency FROM system_announcements WHERE id=?",
            (announcement_id,),
        ).fetchone()
        assert int(migrated["publish_at"]) == created
        assert bool(migrated["emergency"]) is False
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == users_before
        assert db.execute("SELECT count(*) FROM colonies").fetchone()[0] == colonies_before
        visible, _ = game.systems.system_announcement_page(db, 1, now=clock[0])
        assert any(item["id"] == announcement_id for item in visible)


def test_world_rule_rollout_is_scoped_scheduled_audited_and_keeps_pinned_missions(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(
        universe,
        0,
        "world_create",
        {"name": "Rollout World", "seed": 71104, "outposts": 12, "joinable": True},
    )
    command(
        universe,
        0,
        "world_update",
        {"world_id": 2, "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-1"},
    )
    mission_id = identity()
    with game.transaction() as db:
        pinned = terra_combat.pin_mission(db, mission_id, 2, clock[0])
        assert pinned and pinned["rules_version"] == "FUR-3-TERRA-COMBAT-1"
    active_at = clock[0] + 600
    command(
        universe,
        0,
        "admin_rule_rollout_schedule",
        {
            "world_id": 2,
            "rule_key": "terra_combat_ruleset",
            "target_version": "FUR-3-TERRA-COMBAT-2",
            "active_at": active_at,
        },
    )
    with pytest.raises(RuleError, match="Regelupdates kann nur die Spielleitung planen"):
        command(
            universe,
            1,
            "admin_rule_rollout_schedule",
            {
                "world_id": 2,
                "rule_key": "terra_combat_ruleset",
                "target_version": "FUR-3-TERRA-COMBAT-2",
                "active_at": active_at,
            },
        )
    with pytest.raises(RuleError, match="bereits eine Aktivierung geplant"):
        command(
            universe,
            0,
            "admin_rule_rollout_schedule",
            {
                "world_id": 2,
                "rule_key": "terra_combat_ruleset",
                "target_version": "FUR-3-TERRA-COMBAT-3",
                "active_at": active_at,
            },
        )
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=2"
            ).fetchone()[0]
            == "FUR-3-TERRA-COMBAT-1"
        )
        rollout = db.execute(
            "SELECT id FROM world_rule_rollouts WHERE world_id=2 AND status='pending'"
        ).fetchone()
        rollout_id = str(rollout["id"])
    command(universe, 0, "admin_rule_rollout_cancel", {"key": rollout_id})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT status FROM world_rule_rollouts WHERE id=?", (rollout_id,)
            ).fetchone()[0]
            == "cancelled"
        )
    next_at = clock[0] + 1200
    command(
        universe,
        0,
        "admin_rule_rollout_schedule",
        {
            "world_id": 2,
            "rule_key": "terra_combat_ruleset",
            "target_version": "FUR-3-TERRA-COMBAT-2",
            "active_at": next_at,
        },
    )
    clock[0] = next_at
    with game.transaction() as db:
        game.advance(db, next_at)
        assert (
            db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=2"
            ).fetchone()[0]
            == "FUR-3-TERRA-COMBAT-2"
        )
        assert (
            db.execute(
                "SELECT rules_version FROM terra_combat_missions WHERE mission_id=?", (mission_id,)
            ).fetchone()[0]
            == "FUR-3-TERRA-COMBAT-1"
        )
        assert (
            db.execute(
                "SELECT status FROM world_rule_rollouts WHERE world_id=2 AND target_version=? "
                "AND active_at=?",
                ("FUR-3-TERRA-COMBAT-2", next_at),
            ).fetchone()[0]
            == "applied"
        )
        game.advance(db, next_at)
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='world_rule_rollout_applied'"
            ).fetchone()[0]
            == 1
        )


def test_world_rule_rollout_rechecks_dependent_state_at_activation(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(
        universe,
        0,
        "world_create",
        {"name": "Delayed Dependency World", "seed": 71105, "outposts": 12, "joinable": True},
    )
    command(
        universe,
        0,
        "world_update",
        {
            "world_id": 2,
            "hero_ruleset": heroes.RULES.version,
            "crafting_ruleset": "FUR-2",
            "terra_combat_ruleset": "FUR-2",
            "hero_doctrine_ruleset": "FUR-2",
            "hero_respec_ruleset": "FUR-2",
        },
    )
    active_at = clock[0] + 600
    command(
        universe,
        0,
        "admin_rule_rollout_schedule",
        {
            "world_id": 2,
            "rule_key": "hero_doctrine_ruleset",
            "target_version": hero_doctrines.RULES.version,
            "active_at": active_at,
        },
    )
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=2",
            (json.dumps({heroes.RULES.enabled_key: "FUR-2"}),),
        )
    clock[0] = active_at
    with game.transaction() as db:
        game.advance(db, active_at)
        row = db.execute(
            "SELECT status,failure_code FROM world_rule_rollouts WHERE world_id=2"
        ).fetchone()
        assert row["status"] == "failed"
        assert row["failure_code"] == "commander_ruleset_required"
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=2").fetchone()[0]
        )
        assert settings.get(heroes.RULES.enabled_key, "FUR-2") == "FUR-2"
        assert settings.get(hero_doctrines.RULES.enabled_key, "FUR-2") == "FUR-2"
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='world_rule_rollout_failed'"
            ).fetchone()[0]
            == 1
        )


def test_npc_attack_planner_is_bounded_fair_private_and_idempotent(universe, monkeypatch):
    from fur_empire import npc_camps

    game, users, clock = universe
    now = clock[0]
    with game.transaction() as db:
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        settings[npc_camps.RULESET_KEY] = npc_camps.MOVEMENT_RULES_VERSION
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps(settings),))
        npc_camps.initialize_world(db, 1, 504921, now, npc_camps.MOVEMENT_RULES_VERSION)
        posts = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY sort_order LIMIT 2"
        ).fetchall()
        for row, owner, name in zip(posts, users[:2], ("Target <Alpha>", "Target Bravo")):
            post = json.loads(row["state"])
            post["owner"] = owner
            post["name"] = name
            db.execute(
                "UPDATE world_outposts SET state=? WHERE world_id=1 AND target_id=?",
                (json.dumps(post), row["target_id"]),
            )
        assert npc_camps.run_attack_planner(db, now) == 0
        camp_id = str(
            db.execute(
                "SELECT camp_id FROM npc_camps WHERE world_id=1 ORDER BY camp_id LIMIT 1"
            ).fetchone()["camp_id"]
        )
        for row, owner in zip(posts, users[:2]):
            post = json.loads(
                db.execute(
                    "SELECT state FROM world_outposts WHERE world_id=1 AND target_id=?",
                    (row["target_id"],),
                ).fetchone()["state"]
            )
            db.execute(
                "INSERT INTO npc_camp_intel"
                "(world_id,camp_id,target_id,x,y,observed_owner,tier,defense,observed_at,observed_owner_id) "
                "VALUES (1,?,?,?,?,TRUE,?,?,?,?)",
                (
                    camp_id,
                    str(row["target_id"]),
                    int(post["x"]),
                    int(post["y"]),
                    int(post["tier"]),
                    100,
                    now,
                    owner,
                ),
            )
        with monkeypatch.context() as legacy:
            legacy.setattr(
                npc_camps, "stored_rules_digest", lambda *_: npc_camps.LEGACY_MOVEMENT_DIGEST
            )
            assert npc_camps.run_attack_planner(db, now) == 0
        assert npc_camps.run_attack_planner(db, now) == 1
        assert npc_camps.run_attack_planner(db, now + 1) == 0
        first = db.execute(
            "SELECT * FROM npc_attack_plans WHERE world_id=1 ORDER BY cycle"
        ).fetchone()
        assert first is not None
        assert first["rules_version"] == npc_camps.MOVEMENT_RULES_VERSION
        assert len(first["rules_digest"]) == 64
        first_owner = str(first["target_owner"])
        assert len(npc_camps.attack_plan_page(db, 1, first_owner)) == 1
        other_owner = users[1] if first_owner == users[0] else users[0]
        assert npc_camps.attack_plan_page(db, 1, other_owner) == []
        assert npc_camps.run_attack_planner(db, now + 300) == 1
        plans = db.execute(
            "SELECT target_owner FROM npc_attack_plans WHERE world_id=1 ORDER BY cycle"
        ).fetchall()
        assert str(plans[1]["target_owner"]) != first_owner
        assert (
            db.execute("SELECT count(*) FROM npc_attack_plans WHERE world_id=1").fetchone()[0] == 2
        )
        with pytest.raises(Exception, match="immutable"):
            db.execute(
                "UPDATE npc_attack_plans SET target_name='changed' WHERE id=?", (first["id"],)
            )


@pytest.mark.parametrize("invasion", [False, True], ids=["regular", "invasion"])
def test_npc_attack_v3_warns_resolves_once_and_keeps_report_private(universe, invasion):
    from fur_empire import npc_camps, npc_invasions

    game, users, clock = universe
    now = clock[0] = clock[0] // 300 * 300 + 10
    owner = users[0]
    with game.transaction() as db:
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        settings[npc_camps.RULESET_KEY] = npc_camps.ATTACK_RULES_VERSION
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps(settings),))
        npc_camps.initialize_world(db, 1, 504921, now, npc_camps.ATTACK_RULES_VERSION)
        invasion_id = None
        if invasion:
            with pytest.raises(RuleError, match="Spielleitung"):
                game.command(
                    db, owner, "admin_npc_invasion_schedule", {"name": "Sektorwelle"}, identity()
                )
            db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (owner,))
            scheduled = game.command(
                db, owner, "admin_npc_invasion_schedule", {"name": "Sektorwelle"}, identity()
            )["npc_invasions"]["items"][0]
            assert scheduled["status"] == "warning"
            assert scheduled["budget"] == 6
            with pytest.raises(RuleError, match="bereits ein Invasions-Zeitfenster"):
                game.command(
                    db, owner, "admin_npc_invasion_schedule", {"name": "Zweite Welle"}, identity()
                )
        post_row = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY sort_order LIMIT 1"
        ).fetchone()
        post = json.loads(post_row["state"])
        post.update(owner=owner, name="NPC-Angriffsziel", units={}, stock=[1000, 500, 300])
        db.execute(
            "UPDATE world_outposts SET state=? WHERE world_id=1 AND target_id=?",
            (json.dumps(post), post_row["target_id"]),
        )
        camp = db.execute(
            "SELECT camp_id,units FROM npc_camps WHERE world_id=1 ORDER BY camp_id LIMIT 1"
        ).fetchone()
        camp_id = str(camp["camp_id"])
        db.execute(
            "INSERT INTO npc_camp_intel"
            "(world_id,camp_id,target_id,x,y,observed_owner,tier,defense,observed_at,observed_owner_id) "
            "VALUES (1,?,?,?,?,TRUE,?,?,?,?)",
            (
                camp_id,
                str(post_row["target_id"]),
                int(post["x"]),
                int(post["y"]),
                int(post["tier"]),
                100,
                now,
                owner,
            ),
        )
        if invasion:
            assert npc_camps.run_attack_planner(db, scheduled["starts"] - 1) == 0
            invasion_id = db.execute("SELECT id FROM npc_invasions").fetchone()[0]
            db.execute("UPDATE npc_invasions SET budget=1 WHERE id=?", (invasion_id,))
            now = clock[0] = scheduled["starts"]
            assert npc_invasions.planning_window(
                db, 1, scheduled["ends"] - 300, scheduled["ends"]
            ) == (invasion_id, False)
        assert npc_camps.run_attack_planner(db, now) == 1
        assert npc_camps.run_attack_planner(db, now + 1) == 0
        mission = db.execute("SELECT * FROM npc_attack_missions WHERE world_id=1").fetchone()
        assert mission is not None
        assert mission["status"] == "warning"
        assert mission["arrival"] == now + 300
        assert npc_camps.attack_plan_page(db, 1, owner)[0]["attack_status"] == "warning"
        assert npc_camps.attack_plan_page(db, 1, users[1]) == []
        camp_before = json.loads(camp["units"])
        assert npc_camps.resolve_due_attacks(db, game, now + 299) == 0
        assert npc_camps.resolve_due_attacks(db, game, now + 300) == 1
        assert npc_camps.resolve_due_attacks(db, game, now + 301) == 0
        resolved = db.execute(
            "SELECT status,outcome,replay,loot FROM npc_attack_missions WHERE id=?",
            (mission["id"],),
        ).fetchone()
        assert resolved["status"] == "resolved"
        replay = json.loads(resolved["replay"])
        loot = json.loads(resolved["loot"])
        assert replay["seed_commitment"] == mission["seed_commitment"]
        assert replay["attack_rules_version"] == npc_camps.ATTACK_RULES_VERSION
        assert all(0 <= amount <= 200 for amount in loot)
        updated = json.loads(
            db.execute(
                "SELECT state FROM world_outposts WHERE world_id=1 AND target_id=?",
                (post_row["target_id"],),
            ).fetchone()["state"]
        )
        assert updated["owner"] == owner
        assert updated["stock"] == [1000 - loot[0], 500 - loot[1], 300 - loot[2]]
        camp_after = json.loads(
            db.execute(
                "SELECT units FROM npc_camps WHERE world_id=1 AND camp_id=?", (camp_id,)
            ).fetchone()["units"]
        )
        assert sum(camp_after.values()) <= sum(camp_before.values())
        defender_row = db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=1 "
            "ORDER BY is_home DESC LIMIT 1",
            (owner,),
        ).fetchone()
        defender_state = json.loads(defender_row["state"])
        assert defender_state["reports"][0]["title"].startswith("NPC-")
        if invasion:
            assert npc_invasions.planning_window(db, 1, now + 600, now + 900) == (
                invasion_id,
                False,
            )
            assert npc_invasions.view(db, 2, now, False)["items"] == []
            history = npc_invasions.view(db, 1, scheduled["ends"], True)["items"][0]
            assert history == {
                "name": "Sektorwelle",
                "status": "ended",
                "starts": scheduled["starts"],
                "ends": scheduled["ends"],
                "budget": 1,
                "planned": 1,
                "resolved": 1,
                "cancelled": 0,
            }
        assert defender_state["reports"][0]["combat"]["mission_id"] == mission["id"]


def test_npc_attack_v3_cancels_when_target_owner_changes(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    now = clock[0]
    with game.transaction() as db:
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        settings[npc_camps.RULESET_KEY] = npc_camps.ATTACK_RULES_VERSION
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps(settings),))
        npc_camps.initialize_world(db, 1, 504921, now, npc_camps.ATTACK_RULES_VERSION)
        post_row = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY sort_order LIMIT 1"
        ).fetchone()
        post = json.loads(post_row["state"])
        post["owner"] = users[0]
        db.execute(
            "UPDATE world_outposts SET state=? WHERE world_id=1 AND target_id=?",
            (json.dumps(post), post_row["target_id"]),
        )
        camp_id = str(
            db.execute(
                "SELECT camp_id FROM npc_camps WHERE world_id=1 ORDER BY camp_id LIMIT 1"
            ).fetchone()["camp_id"]
        )
        db.execute(
            "INSERT INTO npc_camp_intel"
            "(world_id,camp_id,target_id,x,y,observed_owner,tier,defense,observed_at,observed_owner_id) "
            "VALUES (1,?,?,?,?,TRUE,?,?,?,?)",
            (
                camp_id,
                str(post_row["target_id"]),
                int(post["x"]),
                int(post["y"]),
                int(post["tier"]),
                100,
                now,
                users[0],
            ),
        )
        assert npc_camps.run_attack_planner(db, now) == 1
        mission_id = str(
            db.execute("SELECT id FROM npc_attack_missions WHERE world_id=1").fetchone()["id"]
        )
        post["owner"] = users[1]
        db.execute(
            "UPDATE world_outposts SET state=? WHERE world_id=1 AND target_id=?",
            (json.dumps(post), post_row["target_id"]),
        )
        assert npc_camps.resolve_due_attacks(db, game, now + 300) == 1
        mission = db.execute(
            "SELECT status,cancel_reason FROM npc_attack_missions WHERE id=?", (mission_id,)
        ).fetchone()
        assert mission["status"] == "cancelled"
        assert mission["cancel_reason"] == "target_changed"


def test_npc_attack_v3_does_not_warn_players_in_vacation_mode(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    now = clock[0]
    with game.transaction() as db:
        settings = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=1").fetchone()[0]
        )
        settings[npc_camps.RULESET_KEY] = npc_camps.ATTACK_RULES_VERSION
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps(settings),))
        npc_camps.initialize_world(db, 1, 504921, now, npc_camps.ATTACK_RULES_VERSION)
        home = db.execute(
            "SELECT colony_id,state FROM colonies WHERE world_id=1 AND user_id=? "
            "ORDER BY is_home DESC LIMIT 1",
            (users[0],),
        ).fetchone()
        home_state = json.loads(home["state"])
        home_state["vacation_until"] = now + 3600
        db.execute(
            "UPDATE colonies SET state=? WHERE colony_id=?",
            (json.dumps(home_state), home["colony_id"]),
        )
        post_row = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY sort_order LIMIT 1"
        ).fetchone()
        post = json.loads(post_row["state"])
        post["owner"] = users[0]
        db.execute(
            "UPDATE world_outposts SET state=? WHERE world_id=1 AND target_id=?",
            (json.dumps(post), post_row["target_id"]),
        )
        camp_id = str(
            db.execute(
                "SELECT camp_id FROM npc_camps WHERE world_id=1 ORDER BY camp_id LIMIT 1"
            ).fetchone()["camp_id"]
        )
        db.execute(
            "INSERT INTO npc_camp_intel"
            "(world_id,camp_id,target_id,x,y,observed_owner,tier,defense,observed_at,observed_owner_id) "
            "VALUES (1,?,?,?,?,TRUE,?,?,?,?)",
            (
                camp_id,
                str(post_row["target_id"]),
                int(post["x"]),
                int(post["y"]),
                int(post["tier"]),
                100,
                now,
                users[0],
            ),
        )
        assert npc_camps.run_attack_planner(db, now) == 0
        assert db.execute("SELECT count(*) FROM npc_attack_missions").fetchone()[0] == 0


def test_schema_107_adds_npc_camps_without_changing_player_world_state(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        users_before = db.execute("SELECT id,name,password FROM users ORDER BY id").fetchall()
        colonies_before = db.execute(
            "SELECT colony_id,user_id,world_id,state FROM colonies ORDER BY colony_id"
        ).fetchall()
        posts_before = db.execute(
            "SELECT world_id,target_id,state FROM world_outposts ORDER BY world_id,target_id"
        ).fetchall()
        assert db.execute("SELECT count(*) FROM npc_camps").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM npc_camp_events").fetchone()[0] == 0
        assert len(users_before) == len(users)
        assert len(colonies_before) == len(users)
        assert len(posts_before) > 0


def test_npc_camp_actions_are_allowlisted_bounded_and_idempotent(universe):
    from fur_empire import npc_camps

    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        npc_camps.initialize_world(db, 1, 504921, 1000)
        settings = {npc_camps.RULESET_KEY: npc_camps.RULES_VERSION}
        camps = npc_camps.page(db, 1, settings)
        by_profile = {camp["profile_id"]: camp for camp in camps}

        resupply = npc_camps.perform_action(
            db, 1, by_profile["ash_covenant"]["id"], "resupply", "event-resupply", 1000, settings
        )
        assert resupply["resources"] == [1340, 1130, 910]
        replay = npc_camps.perform_action(
            db, 1, by_profile["ash_covenant"]["id"], "resupply", "event-resupply", 1001, settings
        )
        assert replay["replayed"] is True
        assert replay["resources"] == resupply["resources"]
        with pytest.raises(RuleError, match="anders verwendet"):
            npc_camps.perform_action(
                db, 1, by_profile["ash_covenant"]["id"], "scout", "event-resupply", 1001, settings
            )

        scout = npc_camps.perform_action(
            db, 1, by_profile["ash_covenant"]["id"], "scout", "event-scout", 1002, settings
        )
        assert scout["movement_quota"] == 3 and scout["scout_actions"] == 1
        reinforce = npc_camps.perform_action(
            db, 1, by_profile["iron_compact"]["id"], "reinforce", "event-reinforce", 1003, settings
        )
        assert reinforce["units"]["ranger"] == 12
        assert reinforce["units"]["guardian"] == 17
        assert reinforce["deployment_quota"] == 7
        fortify = npc_camps.perform_action(
            db, 1, by_profile["iron_compact"]["id"], "fortify", "event-fortify", 1004, settings
        )
        assert fortify["fortification_level"] == 1
        maneuver = npc_camps.perform_action(
            db, 1, by_profile["thorn_conclave"]["id"], "maneuver", "event-maneuver", 1005, settings
        )
        assert maneuver["movement_quota"] == 3 and maneuver["maneuver_actions"] == 1

        with pytest.raises(RuleError, match="darf die angeforderte Aktion nicht ausführen"):
            npc_camps.perform_action(
                db, 1, by_profile["thorn_conclave"]["id"], "fortify", "event-denied", 1006, settings
            )
        db.execute(
            "UPDATE npc_camps SET resources='[0,0,0]',fortification_level=10 "
            "WHERE world_id=1 AND camp_id=?",
            (by_profile["iron_compact"]["id"],),
        )
        with pytest.raises(RuleError, match="nicht genügend Vorräte"):
            npc_camps.perform_action(
                db, 1, by_profile["iron_compact"]["id"], "reinforce", "event-poor", 1007, settings
            )
        db.execute(
            "UPDATE npc_camps SET resources='[1200,1000,800]' WHERE world_id=1 AND camp_id=?",
            (by_profile["iron_compact"]["id"],),
        )
        with pytest.raises(RuleError, match="maximale Befestigungsstufe"):
            npc_camps.perform_action(
                db,
                1,
                by_profile["iron_compact"]["id"],
                "fortify",
                "event-max-fortify",
                1008,
                settings,
            )
        assert npc_camps.reset_daily_quotas(db, 1009) == 0
        db.execute(
            "UPDATE npc_camps SET movement_quota=0,deployment_quota=0,quota_checked_at=86400 "
            "WHERE world_id=1 AND camp_id=?",
            (by_profile["ash_covenant"]["id"],),
        )
        assert npc_camps.reset_daily_quotas(db, 3 * 86400 + 1) == 5
        restored = npc_camps.page(db, 1, settings)
        ash = next(camp for camp in restored if camp["profile_id"] == "ash_covenant")
        assert ash["movement_quota"] == 4 and ash["deployment_quota"] == 8


def test_npc_camp_movement_scouts_private_intel_and_moves_one_safe_step(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(
        universe,
        0,
        "world_create",
        {
            "name": "NPC Movement Trial",
            "seed": 812_406,
            "outposts": 24,
            "joinable": True,
            "npc_camps_ruleset": npc_camps.MOVEMENT_RULES_VERSION,
        },
    )
    world_id = 2
    settings = {npc_camps.RULESET_KEY: npc_camps.MOVEMENT_RULES_VERSION}
    now = clock[0]
    with game.transaction() as db:
        camp = db.execute(
            "SELECT camp_id,x,y FROM npc_camps WHERE world_id=? AND profile_id='thorn_conclave'",
            (world_id,),
        ).fetchone()
        assert camp is not None and camp["x"] is not None and camp["y"] is not None
        posts = {
            str(post["id"]): post
            for post in game.world_outposts(db, world_id)
            if post["owner"] is None
        }
        camp_points = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM npc_camps WHERE world_id=? AND x IS NOT NULL", (world_id,)
            )
        }
        land = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'",
                (world_id,),
            )
        }
        protected = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM terra_sector_rules WHERE world_id=? "
                "AND kind IN ('protected','spawn_reserved')",
                (world_id,),
            )
        }
        occupied = {(int(post["x"]), int(post["y"])) for post in game.world_outposts(db, world_id)}
        occupied.update(camp_points)
        found: tuple[str, tuple[int, int], tuple[int, int]] | None = None
        for target_id, post in sorted(posts.items()):
            tx, ty = int(post["x"]), int(post["y"])
            for dx, dy in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                goal = tx + dx, ty + dy
                start = tx + 2 * dx, ty + 2 * dy
                if (
                    goal in land
                    and start in land
                    and goal not in occupied | protected
                    and start not in occupied | protected
                ):
                    found = target_id, start, goal
                    break
            if found:
                break
        assert (
            found is not None
        ), "test world must contain a safe land route beside a neutral outpost"
        target_id, start, goal = found
        camp_id = str(camp["camp_id"])
        db.execute(
            "UPDATE npc_camps SET x=?,y=? WHERE world_id=? AND camp_id=?",
            (start[0], start[1], world_id, camp_id),
        )
        posts_before = {
            str(row["target_id"]): str(row["state"])
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts WHERE world_id=? ORDER BY target_id",
                (world_id,),
            )
        }
        scanned = npc_camps.perform_action(
            db, world_id, camp_id, "scout", "movement-scout", now, settings
        )
        assert scanned["x"] == start[0] and scanned["y"] == start[1]
        assert scanned["scouted_outposts"] >= 1
        assert db.execute(
            "SELECT observed_owner FROM npc_camp_intel WHERE world_id=? AND camp_id=? AND target_id=?",
            (world_id, camp_id, target_id),
        ).fetchone()["observed_owner"] in (False, 0)
        db.execute(
            "DELETE FROM npc_camp_intel WHERE world_id=? AND camp_id=? AND target_id<>?",
            (world_id, camp_id, target_id),
        )
        moved = npc_camps.perform_action(
            db, world_id, camp_id, "maneuver", "movement-step", now + 1, settings
        )
        assert moved["x"] == goal[0] and moved["y"] == goal[1]
        assert moved["target_outpost_id"] == target_id
        assert moved["arrived"] is True and moved["remaining_steps"] == 0
        resources_before_no_target = moved["resources"]
        quota_before_no_target = moved["movement_quota"]
        with pytest.raises(RuleError, match="kein sicheres, erreichbares neutrales Ziel"):
            npc_camps.perform_action(
                db, world_id, camp_id, "maneuver", "movement-no-target", now + 2, settings
            )
        unchanged = npc_camps.page(db, world_id, settings, now + 2)
        unchanged_camp = next(item for item in unchanged if item["id"] == camp_id)
        assert unchanged_camp["resources"] == resources_before_no_target
        assert unchanged_camp["movement_quota"] == quota_before_no_target
        replay = npc_camps.perform_action(
            db, world_id, camp_id, "maneuver", "movement-step", now + 2, settings
        )
        assert replay["replayed"] is True
        final_position = db.execute(
            "SELECT x,y FROM npc_camps WHERE world_id=? AND camp_id=?", (world_id, camp_id)
        ).fetchone()
        assert (int(final_position["x"]), int(final_position["y"])) == goal
        assert {
            str(row["target_id"]): str(row["state"])
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts WHERE world_id=? ORDER BY target_id",
                (world_id,),
            )
        } == posts_before
        page = npc_camps.page(db, world_id, settings, now + 2)
        result = next(item for item in page if item["id"] == camp_id)
        assert (result["x"], result["y"]) == goal
        assert result["scouted_outposts"] >= 1


def test_npc_camp_positions_keep_standoff_from_joining_colonies(universe):
    from fur_empire import npc_camps

    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(
        universe,
        0,
        "world_create",
        {
            "name": "NPC Camp Standoff",
            "seed": 91_084,
            "outposts": 12,
            "joinable": True,
            "npc_camps_ruleset": npc_camps.MOVEMENT_RULES_VERSION,
        },
    )
    with game.transaction() as db:
        camps = db.execute("SELECT x,y FROM npc_camps WHERE world_id=2").fetchall()
        assert len(camps) == 5
        assert all(row["x"] is not None and row["y"] is not None for row in camps)
        for row in camps:
            assert all(
                math.hypot(int(row["x"]) - int(camp["x"]), int(row["y"]) - int(camp["y"])) >= 4
                for camp in camps
                if camp is not row
            )
        camp_points = {(int(row["x"]), int(row["y"])) for row in camps}
    command(universe, 1, "world_join", {"world_id": 2})
    with game.transaction() as db:
        colony = db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=2", (users[1],)
        ).fetchone()
        assert colony is not None
        home = json.loads(colony["state"])
        assert all(math.hypot(home["x"] - x, home["y"] - y) >= 6 for x, y in camp_points)


def test_npc_movement_rollout_adds_locations_without_resetting_camp_state(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(
        universe,
        0,
        "world_create",
        {
            "name": "NPC Movement Rollout",
            "seed": 812_407,
            "outposts": 16,
            "joinable": True,
            "npc_camps_ruleset": npc_camps.RULES_VERSION,
        },
    )
    with game.transaction() as db:
        before = {
            str(row["camp_id"]): (str(row["resources"]), str(row["units"]))
            for row in db.execute(
                "SELECT camp_id,resources,units FROM npc_camps WHERE world_id=2 ORDER BY camp_id"
            )
        }
    active_at = clock[0] + 120
    command(
        universe,
        0,
        "admin_rule_rollout_schedule",
        {
            "world_id": 2,
            "rule_key": npc_camps.RULESET_KEY,
            "target_version": npc_camps.MOVEMENT_RULES_VERSION,
            "active_at": active_at,
        },
    )
    clock[0] = active_at
    with game.transaction() as db:
        game.advance(db, active_at)
        config = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=2").fetchone()[0]
        )
        assert config[npc_camps.RULESET_KEY] == npc_camps.MOVEMENT_RULES_VERSION
        rows = db.execute(
            "SELECT camp_id,resources,units,x,y FROM npc_camps WHERE world_id=2 ORDER BY camp_id"
        ).fetchall()
        assert len(rows) == 5
        assert all(0 <= int(row["x"]) < 64 and 0 <= int(row["y"]) < 64 for row in rows)
        after_policy = {
            str(row["camp_id"]): (str(row["resources"]), str(row["units"])) for row in rows
        }
        assert set(after_policy) == set(before)
        assert (
            npc_camps.initialize_world(db, 2, 812_407, active_at, npc_camps.MOVEMENT_RULES_VERSION)
            == 0
        )
        after_retry = {
            str(row["camp_id"]): (str(row["resources"]), str(row["units"]))
            for row in db.execute(
                "SELECT camp_id,resources,units FROM npc_camps WHERE world_id=2 ORDER BY camp_id"
            )
        }
        assert after_retry == after_policy


def test_npc_camp_daily_quota_reset_runs_in_world_advance(universe):
    from fur_empire import npc_camps

    game, _users, clock = universe
    with game.transaction() as db:
        npc_camps.initialize_world(db, 1, 504921, clock[0])
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({npc_camps.RULESET_KEY: npc_camps.RULES_VERSION}),),
        )
        camp_id = str(
            db.execute(
                "SELECT camp_id FROM npc_camps WHERE world_id=1 AND profile_id='ash_covenant'"
            ).fetchone()[0]
        )
        db.execute(
            "UPDATE npc_camps SET movement_quota=0,deployment_quota=0,quota_checked_at=? "
            "WHERE world_id=1 AND camp_id=?",
            (clock[0] // 86400 * 86400, camp_id),
        )
        next_day = (clock[0] // 86400 + 1) * 86400 + 5
        game.advance(db, next_day)
        first = db.execute(
            "SELECT movement_quota,deployment_quota,quota_checked_at FROM npc_camps "
            "WHERE world_id=1 AND camp_id=?",
            (camp_id,),
        ).fetchone()
        assert first["movement_quota"] == 4
        assert first["deployment_quota"] == 8
        assert first["quota_checked_at"] == next_day // 86400 * 86400
        game.advance(db, next_day + 1)
        assert db.execute("SELECT count(*) FROM npc_camp_events").fetchone()[0] == 5


def test_npc_camp_daily_policy_is_world_scoped_and_retry_safe(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    now = clock[0]
    with game.transaction() as db:
        world_id = game.create_world(db, "NPC policy", 813_771, 8, True)
        game.join_world(db, users[0], "Alpha", world_id)
        npc_camps.initialize_world(db, world_id, 813_771, now)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=?",
            (json.dumps({npc_camps.RULESET_KEY: npc_camps.RULES_VERSION}), world_id),
        )

        assert npc_camps.run_daily_policy(db, now) == 5
        after_first_run = db.execute(
            "SELECT camp_id,resources,units FROM npc_camps WHERE world_id=? ORDER BY position",
            (world_id,),
        ).fetchall()
        assert npc_camps.run_daily_policy(db, now + 30) == 0
        after_retry = db.execute(
            "SELECT camp_id,resources,units FROM npc_camps WHERE world_id=? ORDER BY position",
            (world_id,),
        ).fetchall()
        assert [tuple(row) for row in after_retry] == [tuple(row) for row in after_first_run]
        assert (
            db.execute(
                "SELECT count(*) FROM npc_camp_events WHERE world_id=?", (world_id,)
            ).fetchone()[0]
            == 5
        )
        assert (
            db.execute("SELECT count(*) FROM npc_camp_events WHERE world_id=1").fetchone()[0] == 0
        )

        assert npc_camps.run_daily_policy(db, now + 86400) == 5
        assert (
            db.execute(
                "SELECT count(*) FROM npc_camp_events WHERE world_id=?", (world_id,)
            ).fetchone()[0]
            == 10
        )


def test_npc_camp_ruleset_is_opt_in_world_scoped_and_rollout_retry_safe(universe):
    from fur_empire import npc_camps

    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        assert db.execute("SELECT count(*) FROM npc_camps").fetchone()[0] == 0
        assert npc_camps.page(db, 1, {}) == []
        assert len(npc_camps.PROFILES) == 5
        assert len({tuple(profile["actions"]) for profile in npc_camps.RULES["profiles"]}) == 5
    command(
        universe,
        0,
        "world_create",
        {
            "name": "NPC Camp Direct Opt In",
            "seed": 71306,
            "outposts": 12,
            "joinable": True,
            "npc_camps_ruleset": npc_camps.RULES_VERSION,
        },
    )
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=2").fetchone()[0] == 5
        assert (
            json.loads(
                db.execute("SELECT settings FROM world_settings WHERE world_id=2").fetchone()[0]
            )[npc_camps.RULESET_KEY]
            == npc_camps.RULES_VERSION
        )
    command(
        universe,
        0,
        "world_create",
        {"name": "NPC Camp Rollout", "seed": 71307, "outposts": 12, "joinable": True},
    )
    active_at = clock[0] + 120
    rollout = {
        "world_id": 3,
        "rule_key": "npc_camps_ruleset",
        "target_version": npc_camps.RULES_VERSION,
        "active_at": active_at,
    }
    command(universe, 0, "admin_rule_rollout_schedule", rollout)
    with pytest.raises(RuleError, match="Regelupdates kann nur die Spielleitung planen"):
        command(universe, 1, "admin_rule_rollout_schedule", rollout)
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=3").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=1").fetchone()[0] == 0
    clock[0] = active_at
    with game.transaction() as db:
        assert game.advance(db, active_at) == 0
        world_config = json.loads(
            db.execute("SELECT settings FROM world_settings WHERE world_id=3").fetchone()[0]
        )
        assert world_config[npc_camps.RULESET_KEY] == npc_camps.RULES_VERSION
        first_page = npc_camps.page(db, 3, world_config)
        assert len(first_page) == 5
        assert {camp["profile_id"] for camp in first_page} == set(npc_camps.PROFILES)
        assert all(
            0 <= camp["movement_quota"] <= 4 and 0 <= camp["deployment_quota"] <= 8
            for camp in first_page
        )
        assert (
            db.execute("SELECT count(*) FROM npc_camp_events WHERE world_id=3").fetchone()[0] == 5
        )
        assert all(
            npc_camps.validate_action(camp["profile_id"], action)
            for camp in first_page
            for action in camp["actions"]
        )
        assert not npc_camps.validate_action("ash_covenant", "autonomous_attack")
        assert game.view(db, users[0])["npc_camps"] == []  # player remains in FUR-2 world 1
        directory = game.view(db, users[0])["worlds"]
        assert (
            next(world for world in directory if world["id"] == 3)["npc_camps_ruleset"]
            == npc_camps.RULES_VERSION
        )
        npc_camps.initialize_world(db, 3, 71307, active_at)
        game.advance(db, active_at)
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=3").fetchone()[0] == 5
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=1").fetchone()[0] == 0
    command(universe, 0, "world_join", {"world_id": 3})
    command(universe, 0, "world_select", {"world_id": 3})
    with game.transaction() as db:
        state = game.view(db, users[0])
        assert len(state["npc_camps"]) == 5
        assert state["active_world"]["npc_camps_ruleset"] == npc_camps.RULES_VERSION
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=3").fetchone()[0] == 5
        assert db.execute("SELECT count(*) FROM npc_camps WHERE world_id=1").fetchone()[0] == 0


def test_alliance_bulletin_schema_22_migrates_without_changing_player_data(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE alliance_bulletins")
        db.execute("DELETE FROM schema_versions WHERE version=22")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM alliance_bulletins").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_alliance_forum_schema_23_migrates_without_changing_player_data(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE alliance_forum_reports")
        db.execute("DROP TABLE alliance_forum_posts")
        db.execute("DROP TABLE alliance_forum_threads")
        db.execute("DELETE FROM schema_versions WHERE version=23")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM alliance_forum_threads").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM alliance_forum_posts").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM alliance_forum_reports").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_diplomacy_chronicle_schema_24_migrates_without_changing_player_data(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        users_before = [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ]
        colonies_before = [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ]
        db.execute("DROP TABLE alliance_diplomacy_events")
        db.execute("DELETE FROM schema_versions WHERE version=24")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM alliance_diplomacy_events").fetchone()[0] == 0
        assert [
            tuple(row[key] for key in ("id", "name", "password"))
            for row in db.execute("SELECT id,name,password FROM users ORDER BY id")
        ] == users_before
        assert [
            tuple(row[key] for key in ("user_id", "colony_id", "world_id", "state"))
            for row in db.execute(
                "SELECT user_id,colony_id,world_id,state FROM colonies ORDER BY user_id"
            )
        ] == colonies_before


def test_alliance_bulletin_is_moderated_member_scoped_and_idempotent(universe):
    game, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "BOARD", "name": "Bulletin Board"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    with game.transaction() as db:
        invite_id = db.execute("SELECT id FROM invites WHERE user_id=?", (users[1],)).fetchone()[0]
    command(universe, 1, "alliance_accept", {"key": invite_id})

    create_barrier = Barrier(2)

    def create_bulletin():
        create_barrier.wait(timeout=10)
        return command(
            universe,
            0,
            "alliance_bulletin_create",
            {"name": "Supply plan", "body": "Prepare the northern route."},
            "bulletin-create-once",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        created, duplicate = [
            future.result()
            for future in (pool.submit(create_bulletin), pool.submit(create_bulletin))
        ]
    board = state(universe, 1)["alliance_bulletins"]
    assert len(board) == 1
    bulletin = board[0]
    assert bulletin["title"] == "Supply plan"
    assert bulletin["body"] == "Prepare the northern route."
    assert bulletin["author_name"] == "Alpha"
    assert bulletin["archived"] == 0
    assert duplicate["alliance_bulletins"] == created["alliance_bulletins"]
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_bulletins").fetchone()[0] == 1
    with pytest.raises(RuleError, match="Allianzleitung"):
        command(
            universe,
            1,
            "alliance_bulletin_create",
            {"name": "Unauthorized", "body": "Member cannot publish."},
        )
    with pytest.raises(RuleError, match="Allianzleitung"):
        command(
            universe,
            1,
            "alliance_bulletin_update",
            {"key": bulletin["id"], "name": "Changed", "body": "Unauthorized edit."},
        )

    command(
        universe,
        0,
        "alliance_bulletin_update",
        {"key": bulletin["id"], "name": "Updated plan", "body": "Use the east route."},
    )
    command(universe, 0, "alliance_bulletin_archive", {"key": bulletin["id"]})
    assert state(universe, 1)["alliance_bulletins"][0]["archived"] == 1
    with pytest.raises(RuleError, match="Aktive"):
        command(
            universe,
            0,
            "alliance_bulletin_update",
            {"key": bulletin["id"], "name": "Changed after archive", "body": "No."},
        )

    # Current membership grants board visibility; leaving immediately revokes it.
    command(universe, 0, "alliance_kick", {"key": users[1]})
    assert state(universe, 1)["alliance_bulletins"] == []
    command(universe, 2, "alliance_create", {"tag": "OTHER", "name": "Other"})
    with pytest.raises(RuleError, match="nicht gefunden"):
        command(
            universe,
            2,
            "alliance_bulletin_archive",
            {"key": bulletin["id"]},
        )
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='alliance_bulletin_create' "
            "AND target=?",
            (users[0], bulletin["id"]),
        ).fetchone()
        assert audit is not None
        assert "Prepare the northern route." not in audit["details"]


def test_alliance_bulletin_keyset_pages_are_stable_and_include_archived_posts(universe):
    game, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "PAGES", "name": "Page Keepers"})
    with game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (users[0],)
        ).fetchone()[0]
        for index in range(205):
            db.execute(
                "INSERT INTO alliance_bulletins "
                "(id,alliance_id,author_id,title,body,created,updated,archived) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    f"bulletin-{index:03}",
                    alliance_id,
                    users[0],
                    f"Entry {index}",
                    "Archived and active entries share one ordered history.",
                    10000 + index,
                    10000 + index,
                    index % 2,
                ),
            )

    collected = []
    cursor = None
    while True:
        with game.transaction() as db:
            page, has_more = game.systems.alliance_bulletin_page(db, alliance_id, cursor)
        collected.extend(page)
        if not has_more:
            break
        cursor = page[-1]["id"]
    assert len(collected) == 205
    assert len({entry["id"] for entry in collected}) == 205
    assert [entry["created"] for entry in collected] == sorted(
        (entry["created"] for entry in collected), reverse=True
    )
    assert {entry["archived"] for entry in collected} == {0, 1}


def test_alliance_forum_rights_archive_reports_and_member_visibility(universe):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "FORUM", "name": "Forum Keepers"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    with game.transaction() as db:
        invite_id = db.execute("SELECT id FROM invites WHERE user_id=?", (users[1],)).fetchone()[0]
    command(universe, 1, "alliance_accept", {"key": invite_id})

    command(
        universe,
        0,
        "alliance_forum_thread_create",
        {"name": "Northern route", "body": "First plan."},
        "forum-thread-once",
    )
    thread = state(universe, 1)["alliance_forum"][0]
    assert thread["title"] == "Northern route"
    assert thread["posts"][0]["body"] == "First plan."
    assert state(universe, 2)["alliance_forum"] == []
    with pytest.raises(RuleError, match="darf nicht bearbeitet werden"):
        command(
            universe,
            1,
            "alliance_forum_thread_edit",
            {"key": thread["id"], "name": "Changed by member"},
        )
    with pytest.raises(RuleError, match="Leitung und Offiziere"):
        command(universe, 1, "alliance_forum_archive", {"key": thread["id"]})

    command(
        universe,
        1,
        "alliance_forum_reply",
        {"key": thread["id"], "body": "A reply with useful details."},
    )
    posts = state(universe, 0)["alliance_forum"][0]["posts"]
    reply = next(post for post in posts if post["author_id"] == users[1])
    command(
        universe,
        1,
        "alliance_forum_post_edit",
        {"key": reply["id"], "body": "Updated reply."},
    )
    assert any(
        post["body"] == "Updated reply."
        for post in state(universe, 0)["alliance_forum"][0]["posts"]
    )

    with game.transaction() as db:
        db.execute("UPDATE profiles SET muted_until=? WHERE user_id=?", (clock[0] + 3600, users[1]))
    with pytest.raises(RuleError, match="Schreibrecht"):
        command(universe, 1, "alliance_forum_reply", {"key": thread["id"], "body": "Muted."})
    with game.transaction() as db:
        db.execute("UPDATE profiles SET muted_until=0 WHERE user_id=?", (users[1],))

    command(
        universe,
        0,
        "alliance_forum_report",
        {"key": reply["id"], "body": "Please review this reply."},
    )
    report = state(universe, 0)["alliance_forum_reports"][0]
    assert report["status"] == "pending"
    assert report["post_id"] == reply["id"]
    assert report["reason"] == "Please review this reply."
    with pytest.raises(RuleError, match="bereits gemeldet"):
        command(
            universe,
            0,
            "alliance_forum_report",
            {"key": reply["id"], "body": "Duplicate report."},
        )
    with pytest.raises(RuleError, match="Leitung und Offiziere"):
        command(universe, 1, "alliance_forum_report_resolve", {"key": report["id"]})
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='alliance_forum_report' AND target=?",
            (users[0], report["id"]),
        ).fetchone()
        assert audit is not None
        assert "Please review this reply." not in audit["details"]

    command(universe, 0, "alliance_forum_report_resolve", {"key": report["id"]})
    assert state(universe, 0)["alliance_forum_reports"][0]["status"] == "resolved"
    command(
        universe,
        0,
        "alliance_forum_thread_edit",
        {"key": thread["id"], "name": "North route plan"},
    )
    command(universe, 0, "alliance_forum_archive", {"key": thread["id"]})
    archived = state(universe, 0)["alliance_forum"][0]
    assert archived["archived"] == 1
    assert archived["title"] == "North route plan"
    with pytest.raises(RuleError, match="Offenes Forumthema"):
        command(universe, 1, "alliance_forum_reply", {"key": thread["id"], "body": "Too late."})
    with pytest.raises(RuleError, match="darf nicht bearbeitet werden"):
        command(
            universe,
            1,
            "alliance_forum_post_edit",
            {"key": reply["id"], "body": "Edit after archive."},
        )

    command(universe, 0, "alliance_kick", {"key": users[1]})
    assert state(universe, 1)["alliance_forum"] == []
    assert state(universe, 1)["alliance_forum_reports"] == []


def test_alliance_forum_reports_are_private_and_keyset_paginated(universe):
    game, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "RPT", "name": "Report pagination"})
    with game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (users[0],)
        ).fetchone()[0]
        for user_id in users[1:]:
            db.execute(
                "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
                (user_id, alliance_id, "member"),
            )
        for index in range(52):
            thread_id = f"report-page-thread-{index:03}"
            post_id = f"report-page-post-{index:03}"
            report_id = f"report-page-report-{index:03}"
            reporter_id = users[1] if index < 51 else users[2]
            created = 2_000_000_000 + index
            db.execute(
                "INSERT INTO alliance_forum_threads "
                "(id,alliance_id,author_id,title,created,updated,archived) "
                "VALUES (?,?,?,?,?,?,0)",
                (thread_id, alliance_id, users[0], f"Thread {index}", created, created),
            )
            db.execute(
                "INSERT INTO alliance_forum_posts "
                "(id,thread_id,author_id,body,created,updated) VALUES (?,?,?,?,?,?)",
                (post_id, thread_id, users[0], f"Post {index}", created, created),
            )
            db.execute(
                "INSERT INTO alliance_forum_reports "
                "(id,post_id,reporter_id,reason,status,created,updated,resolved_by) "
                "VALUES (?,?,?,?,'pending',?,?,NULL)",
                (report_id, post_id, reporter_id, f"Reason {index}", created, created),
            )

    with game.transaction() as db:
        first, has_more = game.systems.alliance_forum_reports_page(db, users[1], alliance_id, False)
        assert len(first) == 50
        assert has_more is True
        assert all(report["reporter_id"] == users[1] for report in first)
        second, has_more = game.systems.alliance_forum_reports_page(
            db, users[1], alliance_id, False, first[-1]["id"]
        )
        assert len(second) == 1
        assert has_more is False
        assert second[0]["reporter_id"] == users[1]
        all_reports, has_more = game.systems.alliance_forum_reports_page(
            db, users[0], alliance_id, True
        )
        assert len(all_reports) == 50
        assert has_more is True
        with pytest.raises(RuleError, match="Forum-Meldung nicht gefunden"):
            game.systems.alliance_forum_reports_page(
                db, users[2], alliance_id, False, first[-1]["id"]
            )

    leader_state = state(universe, 0)
    assert len(leader_state["alliance_forum_reports"]) == 50
    assert leader_state["alliance_forum_reports_has_more"] is True


def test_friend_requests_are_private_approved_and_block_private_messages(universe):
    game, users, _ = universe
    command(universe, 0, "friend_request", {"key": users[1]})
    assert [item["name"] for item in state(universe, 0)["social"]["outgoing_requests"]] == ["Bravo"]
    assert [item["name"] for item in state(universe, 1)["social"]["incoming_requests"]] == ["Alpha"]
    charlie_social = state(universe, 2)["social"]
    assert all(
        not charlie_social[name]
        for name in ("friends", "incoming_requests", "outgoing_requests", "blocked")
    )
    with pytest.raises(RuleError, match="nicht gefunden"):
        command(universe, 0, "friend_accept", {"key": users[1]})

    command(universe, 1, "friend_accept", {"key": users[0]})
    assert [item["name"] for item in state(universe, 0)["social"]["friends"]] == ["Bravo"]
    assert [item["name"] for item in state(universe, 1)["social"]["friends"]] == ["Alpha"]

    command(
        universe,
        1,
        "message",
        {"channel": "private", "name": "Alpha", "body": "Vor der Sperre"},
    )
    with game.transaction() as db:
        private_message_id = db.execute(
            "SELECT id FROM messages WHERE channel='private' AND sender=? AND recipient=?",
            (users[1], users[0]),
        ).fetchone()[0]
    command(universe, 0, "player_block", {"key": users[1]})
    assert [item["name"] for item in state(universe, 0)["social"]["blocked"]] == ["Bravo"]
    assert state(universe, 0)["social"]["friends"] == []
    assert "blocked_by" not in state(universe, 1)["social"]
    assert state(universe, 1)["social"]["friends"] == []
    with pytest.raises(RuleError, match="privaten Nachrichten"):
        command(universe, 1, "message", {"channel": "private", "name": "Alpha", "body": "Nope"})
    with pytest.raises(RuleError, match="Kontaktanfrage"):
        command(universe, 1, "friend_request", {"key": users[0]})

    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[2],))
    command(universe, 2, "admin_hide", {"key": private_message_id})
    with game.transaction() as db:
        assert (
            db.execute("SELECT hidden FROM messages WHERE id=?", (private_message_id,)).fetchone()[
                0
            ]
            == 1
        )
    command(universe, 0, "player_unblock", {"key": users[1]})
    assert state(universe, 0)["social"]["blocked"] == []
    assert state(universe, 0)["social"]["friends"] == []


def test_friend_request_decline_cancel_and_remove_require_the_correct_actor(universe):
    game, users, _ = universe

    command(universe, 0, "friend_request", {"key": users[1]})
    with pytest.raises(RuleError, match="nicht geändert"):
        command(universe, 0, "friend_decline", {"key": users[1]})
    with pytest.raises(RuleError, match="Kontaktanfrage nicht gefunden"):
        command(universe, 2, "friend_cancel", {"key": users[0]})
    command(universe, 1, "friend_decline", {"key": users[0]})
    assert state(universe, 0)["social"]["outgoing_requests"] == []
    assert state(universe, 1)["social"]["incoming_requests"] == []

    command(universe, 0, "friend_request", {"key": users[1]})
    with pytest.raises(RuleError, match="nicht geändert"):
        command(universe, 1, "friend_cancel", {"key": users[0]})
    command(universe, 0, "friend_cancel", {"key": users[1]})
    assert state(universe, 0)["social"]["outgoing_requests"] == []
    assert state(universe, 1)["social"]["incoming_requests"] == []

    command(universe, 0, "friend_request", {"key": users[1]})
    command(universe, 1, "friend_accept", {"key": users[0]})
    with pytest.raises(RuleError, match="Kontakt nicht gefunden"):
        command(universe, 2, "friend_remove", {"key": users[0]})
    command(universe, 0, "friend_remove", {"key": users[1]})
    assert state(universe, 0)["social"]["friends"] == []
    assert state(universe, 1)["social"]["friends"] == []
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM friendships").fetchone()[0] == 0


def test_player_profile_is_private_by_default_and_only_returns_allowlisted_world_stats(universe):
    game, users, _ = universe
    with game.transaction() as db:
        game.systems.profile(db, users[0])
        game.systems.player_profile_settings(db, users[0])
        game.systems.profile(db, users[1])
        game.systems.player_profile_settings(db, users[1])
        assert game.systems.public_player_profile(db, users[0], users[1], 1) is None
        own_private_profile = game.systems.public_player_profile(db, users[1], users[1], 1)
        assert own_private_profile is not None
        assert game.systems.public_player_profile(db, users[1], users[1], 2) is None
        db.execute(
            "UPDATE profiles SET email='private@example.invalid',verified=1,totp='secret' "
            "WHERE user_id=?",
            (users[1],),
        )

    command(
        universe,
        1,
        "profile_settings_update",
        {
            "profile_visibility": "public",
            "profile_title": "pathfinder",
            "profile_badges": "frontier,builder,scholar",
        },
    )
    with game.transaction() as db:
        public = game.systems.public_player_profile(db, users[0], users[1], 1)
        assert public is not None
        assert public["name"] == "Bravo"
        assert public["title"] == "Wegfinder"
        assert public["badges"] == ["Grenzgänger", "Baumeister", "Forscher"]
        assert public["world"] == "Genesis"
        assert 1 <= public["rank"] <= len(users)
        assert public["score"] >= 0
        assert public["rules_version"] == "FUR-3-PLAYER-PROFILE-1"
        assert "email" not in public
        assert "totp" not in public
        assert "id" not in public
        assert set(public) == {
            "name",
            "title",
            "skin",
            "skin_id",
            "banner",
            "banner_id",
            "badges",
            "world",
            "rank",
            "score",
            "rules_version",
        }
        own_state = game.view(db, users[1])
        assert own_state["profile"]["public_profile_visibility"] == "public"
        assert own_state["profile"]["public_profile_title"] == "pathfinder"
        with pytest.raises(RuleError, match="drei"):
            game.systems.update_player_profile(
                db,
                game.read(db, users[1]),
                {
                    "profile_visibility": "public",
                    "profile_title": "pathfinder",
                    "profile_badges": "frontier,builder,scholar,envoy",
                },
            )


def test_campaign_directive_unlocks_account_cosmetics_once_and_requires_ownership(universe):
    from fur_empire import cosmetic_rewards

    game, users, _ = universe
    with game.transaction() as db:
        state = game.read(db, users[0])
        state["buildings"]["barracks"] = 1
        state["claimed"].append("economy")
        game.save(db, state)
        state = game.read(db, users[0])
        quest = next(item for item in game.quests(state) if item["id"] == "army")
        assert quest["done"]
        game.command(db, users[0], "quest", {"key": "army"}, "cosmetic-army-claim")
        owned = cosmetic_rewards.unlocked(db, users[0])
        assert owned == {"skin:ash_guard"}
        row = db.execute(
            "SELECT source_directive,rules_version FROM player_cosmetic_unlocks "
            "WHERE user_id=? AND cosmetic_id='skin:ash_guard'",
            (users[0],),
        ).fetchone()
        assert row["source_directive"] == "army"
        assert row["rules_version"] == cosmetic_rewards.RULES.version
        game.command(db, users[0], "quest", {"key": "army"}, "cosmetic-army-claim")
        assert cosmetic_rewards.unlocked(db, users[0]) == owned
        assert cosmetic_rewards.unlocked(db, users[0]) == owned
        state = game.read(db, users[0])
        with pytest.raises(RuleError, match="noch nicht freigeschaltet"):
            game.systems.update_player_profile(
                db,
                state,
                {
                    "profile_visibility": "public",
                    "profile_title": "none",
                    "profile_reward_title": "frontier_founder",
                    "profile_skin": "citadel_guard",
                    "profile_banner": "none",
                    "profile_badges": "",
                },
            )
        game.systems.update_player_profile(
            db,
            state,
            {
                "profile_visibility": "public",
                "profile_title": "none",
                "profile_reward_title": "none",
                "profile_skin": "ash_guard",
                "profile_banner": "none",
                "profile_badges": "",
            },
        )
        public = game.systems.public_player_profile(db, users[1], users[0], 1)
        assert public is not None
        assert public["skin"] == "Aschenwacht"
        assert public["skin_id"] == "ash_guard"
        assert public["banner"] == ""
        assert public["banner_id"] == "none"


def test_simultaneous_friend_requests_create_one_pending_relationship(universe):
    _, users, _ = universe
    barrier = Barrier(2)

    def send_request(index: int) -> bool:
        barrier.wait(timeout=10)
        try:
            command(universe, index, "friend_request", {"key": users[1 - index]})
        except RuleError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(send_request, (0, 1)))
    assert sorted(outcomes) == [False, True]
    first, second = state(universe, 0)["social"], state(universe, 1)["social"]
    assert len(first["outgoing_requests"]) + len(second["outgoing_requests"]) == 1
    assert len(first["incoming_requests"]) + len(second["incoming_requests"]) == 1


def test_personal_notes_are_private_world_bound_and_limited(universe):
    game, users, _ = universe
    with game.transaction() as db:
        owner_state = game.read(db, users[0])
        owner_state["reports"].append(
            {"id": "owner-report-1", "title": "Eigener Bericht", "body": "Privater Inhalt"}
        )
        game.save(db, owner_state)

    command(
        universe,
        0,
        "note_save",
        {"target_kind": "sector", "x": 7, "y": 9, "body": "<Angriffsroute>"},
    )
    owner_notes = state(universe, 0)["notes"]
    assert len(owner_notes) == 1
    sector_note_id = owner_notes[0]["id"]
    assert owner_notes[0]["body"] == "<Angriffsroute>"
    assert state(universe, 1)["notes"] == []
    with game.transaction() as db:
        assert game.systems.notes_state(db, users[0], 2) == ([], False)

    command(
        universe,
        0,
        "note_save",
        {"target_kind": "sector", "x": 7, "y": 9, "body": "Aktualisierte Route"},
    )
    owner_notes = state(universe, 0)["notes"]
    assert len(owner_notes) == 1
    assert owner_notes[0]["id"] == sector_note_id
    assert owner_notes[0]["body"] == "Aktualisierte Route"

    command(
        universe,
        0,
        "note_save",
        {"target_kind": "report", "key": "owner-report-1", "body": "Auswertung"},
    )
    owner_notes = state(universe, 0)["notes"]
    report_note = next(note for note in owner_notes if note["target_kind"] == "report")
    assert report_note["report_title"] == "Eigener Bericht"
    with pytest.raises(RuleError, match="Bericht in dieser Welt"):
        command(
            universe,
            1,
            "note_save",
            {"target_kind": "report", "key": "owner-report-1", "body": "Fremder Bericht"},
        )
    with pytest.raises(RuleError, match="500"):
        command(
            universe,
            0,
            "note_save",
            {"target_kind": "sector", "x": 8, "y": 9, "body": "n" * 501},
        )
    with pytest.raises(RuleError, match="Koordinaten"):
        command(
            universe,
            0,
            "note_save",
            {"target_kind": "sector", "x": 64, "y": 9, "body": "Außerhalb"},
        )
    with pytest.raises(RuleError, match="Notiz nicht gefunden"):
        command(universe, 1, "note_delete", {"key": sector_note_id})
    command(universe, 0, "note_delete", {"key": sector_note_id})
    assert all(note["id"] != sector_note_id for note in state(universe, 0)["notes"])


def test_alliance_combat_report_shares_are_redacted_scoped_and_revoked_on_membership_change(
    universe,
):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "SHARE", "name": "Report Keepers"})
    for index, name in ((1, "Bravo"), (2, "Charlie")):
        command(universe, 0, "alliance_invite", {"name": name})
        with game.transaction() as db:
            invite_id = db.execute(
                "SELECT id FROM invites WHERE user_id=?", (users[index],)
            ).fetchone()[0]
        command(universe, index, "alliance_accept", {"key": invite_id})

    report_ids = {}
    for index in (1, 2):
        report_id = identity()
        report_ids[index] = report_id
        with game.transaction() as db:
            colony = game.read(db, users[index])
            colony["reports"].insert(
                0,
                {
                    "id": report_id,
                    "title": "Victory at SECRET-TARGET-COORDINATES",
                    "body": "Private loot 7000; hidden opponent ACCOUNT-ID",
                    "time": clock[0],
                    "share_owner": {"side": "attacker", "wing_index": None, "allowed": True},
                    "combat": {
                        "rules_version": "SECRET-RULES",
                        "rules_digest": "SECRET-DIGEST",
                        "seed": "SECRET-SEED",
                        "participants": {"attacker": "Bravo", "defender": "Hidden Target"},
                        "rounds": [
                            {
                                "round": 1,
                                "victory": True,
                                "attacker": {
                                    "losses": {"ranger": 2},
                                    "survivors": {"ranger": 3, "sentinel": 1},
                                },
                                "defender": {
                                    "losses": {"mech": 99},
                                    "survivors": {"secret_defense": 8},
                                },
                                "loot": [7000, 6000, 5000],
                            }
                        ],
                    },
                },
            )
            game.save(db, colony)

    command(universe, 1, "report_share", {"key": report_ids[1]})
    command(universe, 2, "report_share", {"key": report_ids[2]})
    shared = state(universe, 0)["alliance_shared_reports"]
    assert {entry["owner_name"] for entry in shared} == {"Bravo", "Charlie"}
    bravo = next(entry for entry in shared if entry["owner_name"] == "Bravo")
    assert bravo["summary"] == {
        "outcome": "victory",
        "rounds": [{"number": 1, "outcome": "victory", "own_losses": 2, "own_survivors": 4}],
    }
    assert "report_id" not in bravo and not bravo["can_revoke"]
    assert "SECRET" not in json.dumps(shared)
    assert "Hidden Target" not in json.dumps(shared)
    assert "7000" not in json.dumps(shared)
    assert len(state(universe, 1)["shared_combat_report_keys"]) == 1
    assert state(universe, 2)["alliance_shared_reports"]
    with game.transaction() as db:
        alliance_id = str(game.systems.member(db, users[0])["alliance_id"])
        first_page, has_more = game.systems.alliance_shared_report_page(
            db, users[0], alliance_id, 1, page_size=1
        )
        second_page, has_more_after = game.systems.alliance_shared_report_page(
            db, users[0], alliance_id, 1, before_id=first_page[0]["id"], page_size=1
        )
    assert has_more and not has_more_after
    assert first_page[0]["id"] != second_page[0]["id"]

    with pytest.raises(RuleError, match="Geteilten Kampfbericht nicht gefunden"):
        command(universe, 2, "report_unshare", {"key": bravo["id"]})
    command(universe, 1, "report_unshare", {"key": bravo["id"]})
    assert not any(
        entry["owner_name"] == "Bravo" for entry in state(universe, 0)["alliance_shared_reports"]
    )

    command(universe, 1, "report_share", {"key": report_ids[1]})
    command(universe, 1, "alliance_leave")
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM alliance_shared_reports WHERE owner_id=?", (users[1],)
            ).fetchone()[0]
            == 0
        )

    command(universe, 0, "alliance_kick", {"key": users[2]})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM alliance_shared_reports WHERE owner_id=?", (users[2],)
            ).fetchone()[0]
            == 0
        )
    assert state(universe, 0)["alliance_shared_reports"] == []


def test_alliance_report_sharing_rejects_noncombat_and_malformed_reports(universe):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "SAFE", "name": "Safe Reports"})
    noncombat_id, malformed_id = identity(), identity()
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["reports"] = [
            {
                "id": noncombat_id,
                "title": "Private event",
                "body": "Do not share",
                "time": clock[0],
            },
            {
                "id": malformed_id,
                "title": "Malformed battle",
                "body": "Do not share",
                "time": clock[0],
                "share_owner": {"side": "attacker", "wing_index": None, "allowed": True},
                "combat": {
                    "rounds": [
                        {
                            "round": 1,
                            "victory": True,
                            "attacker": {"losses": {"ranger": True}, "survivors": {}},
                        }
                    ]
                },
            },
        ]
        game.save(db, colony)
    with pytest.raises(RuleError, match="Nur gültige Kampfberichte"):
        command(universe, 0, "report_share", {"key": noncombat_id})
    with pytest.raises(RuleError, match="Nur gültige Kampfberichte"):
        command(universe, 0, "report_share", {"key": malformed_id})
    assert not state(universe, 0)["alliance_shared_reports"]


def test_report_share_projection_uses_the_report_owners_side_and_wing():
    from fur_empire.report_sharing import project_report

    defender = project_report(
        {
            "share_owner": {"side": "defender", "wing_index": None, "allowed": True},
            "combat": {
                "rounds": [
                    {
                        "round": 1,
                        "victory": True,
                        "attacker": {"losses": {"enemy": 99}, "survivors": {"enemy": 88}},
                        "defender": {"losses": {"ranger": 2}, "survivors": {"ranger": 3}},
                    }
                ],
            },
        }
    )
    assert defender == {
        "outcome": "defeat",
        "rounds": [{"number": 1, "outcome": "defeat", "own_losses": 2, "own_survivors": 3}],
    }

    wing = project_report(
        {
            "share_owner": {"side": "attacker_wing", "wing_index": 1, "allowed": True},
            "combat": {
                "rounds": [
                    {
                        "round": 1,
                        "victory": True,
                        "attacker_wings": [
                            {"losses": {"ally": 50}, "survivors": {"ally": 40}},
                            {"losses": {"ranger": 1}, "survivors": {"ranger": 4}},
                        ],
                    }
                ],
            },
        }
    )
    assert wing["rounds"][0]["own_losses"] == 1
    assert wing["rounds"][0]["own_survivors"] == 4
    with pytest.raises(ValueError, match="safe owner-specific"):
        project_report({"combat": {"rounds": [{"victory": True}]}})


def test_player_notes_are_bounded_keyset_pages_scoped_to_owner_and_world(universe):
    game, users, _ = universe
    with game.transaction() as db:
        world_id = int(game.read(db, users[0])["world_id"])
        for index in range(53):
            db.execute(
                "INSERT INTO player_notes"
                "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
                "VALUES (?,? ,?,'sector',?,?,NULL,?, ?,?)",
                (
                    f"note-page-{index:03}",
                    users[0],
                    world_id,
                    index % 64,
                    index // 64,
                    str(index),
                    index,
                    index,
                ),
            )
        db.execute(
            "INSERT INTO player_notes"
            "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
            "VALUES ('foreign-note',? ,?,'sector',0,0,NULL,'private',1,1)",
            (users[1], world_id),
        )
        first, has_more = game.systems.notes_page(db, users[0], world_id)
        assert len(first) == 50 and has_more
        second, has_more = game.systems.notes_page(db, users[0], world_id, first[-1]["id"])
        assert len(second) == 3 and not has_more
        assert {note["id"] for note in first}.isdisjoint(note["id"] for note in second)
        assert first[0]["id"] == "note-page-052"
        assert second[-1]["id"] == "note-page-000"
        with pytest.raises(RuleError, match="Notiz-Cursor"):
            game.systems.notes_page(db, users[0], world_id, "foreign-note")
        with pytest.raises(RuleError, match="Notiz-Cursor"):
            game.systems.notes_page(db, users[0], world_id + 100, first[-1]["id"])


def test_player_colonies_are_bounded_keyset_pages_scoped_to_owner(universe):
    game, users, _ = universe
    with game.transaction() as db:
        world_id = int(game.read(db, users[0])["world_id"])
        occupied = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=?", (world_id,))
        }
        free = [(x, y) for y in range(64) for x in range(64) if (x, y) not in occupied][:52]
        assert len(free) == 52
        for index, (x, y) in enumerate(free):
            colony_id = f"colony-page-{index:03}"
            colony_state = {
                "name": "Alpha",
                "colony_name": f"Colony {index}",
                "x": x,
                "y": y,
                "buildings": {"hq": 1},
            }
            db.execute(
                "INSERT INTO colonies(colony_id,user_id,world_id,is_home,x,y,state) "
                "VALUES (?,?,?,FALSE,?,?,?)",
                (colony_id, users[0], world_id, x, y, json.dumps(colony_state)),
            )
        first, has_more = game.systems.player_colonies_page(db, users[0])
        assert len(first) == 50 and has_more
        assert first[0]["is_home"] is True
        second, has_more = game.systems.player_colonies_page(db, users[0], first[-1]["colony_id"])
        assert len(second) == 3 and not has_more
        assert {colony["colony_id"] for colony in first}.isdisjoint(
            colony["colony_id"] for colony in second
        )
        with pytest.raises(RuleError, match="Kolonie-Cursor"):
            game.systems.player_colonies_page(db, users[0], users[1])


def test_expedition_outcome_is_deterministic_and_bounded():
    army = {"ranger": 17, "sentinel": 9, "mech": 3}
    first = resolve_expedition("mission-seed", army)
    assert resolve_expedition("mission-seed", army) == first
    assert first["rules_version"] == EXPEDITION_RULES["version"]
    assert first["rules_digest"] == EXPEDITION_RULES_DIGEST
    validate_ruleset(first["rules_version"], first["rules_digest"])
    assert first["outcome"] in {item["id"] for item in EXPEDITION_RULES["outcomes"]}
    assert all(0 <= first["survivors"][unit] <= count for unit, count in army.items())
    assert sum(first["loot"]) <= max(item["resource_max"] for item in EXPEDITION_RULES["outcomes"])
    observed = {resolve_expedition(f"coverage-{index}", army)["outcome"] for index in range(500)}
    assert observed == {item["id"] for item in EXPEDITION_RULES["outcomes"]}
    drop_view = item_drop_view()
    assert drop_view["version"] == ITEM_DROP_RULES.version
    assert drop_view["transport_weight"] == 1
    assert drop_view["drops"][0]["chance_basis_points"] == 1000
    assert drop_view["drops"][0]["overall_chance_basis_points"] == 800
    assert drop_view["drops"][0]["max_per_mission"] == 1
    assert item_drop_view(False)["enabled"] is False
    assert item_drop_view(True)["enabled"] is True
    drop_seed = next(
        f"item-seed-{index}"
        for index in range(1000)
        if resolve_item_drops(
            f"item-seed-{index}", "discovery", ITEM_DROP_RULES.version, ITEM_DROP_HASH
        )["rolls"][0]["amount"]
    )
    seeded_drop = resolve_item_drops(
        drop_seed,
        "discovery",
        ITEM_DROP_RULES.version,
        ITEM_DROP_HASH,
    )
    assert seeded_drop == resolve_item_drops(
        drop_seed, "discovery", ITEM_DROP_RULES.version, ITEM_DROP_HASH
    )
    assert seeded_drop["rolls"][0]["amount"] == 1
    assert (
        resolve_item_drops(
            "guaranteed-hazard-test", "hazard", ITEM_DROP_RULES.version, ITEM_DROP_HASH
        )["rolls"][0]["amount"]
        == 0
    )
    with pytest.raises(ValueError, match="Unsupported expedition item-drop rules"):
        resolve_item_drops("mission", "discovery", ITEM_DROP_RULES.version, "0" * 64)


def test_expedition_requires_the_exact_immutable_rule_snapshot():
    with pytest.raises(ValueError, match="Unsupported expedition rule snapshot"):
        validate_ruleset(EXPEDITION_RULES["version"], "0" * 64)
    with pytest.raises(ValueError, match="Unsupported expedition rule snapshot"):
        validate_ruleset("FUR-3-EXPEDITIONS-2", EXPEDITION_RULES_DIGEST)


def test_expedition_dispatch_resolves_and_returns_once(universe):
    game, users, clock = universe
    initial = state(universe, 0)
    target = next(post for post in initial["world"] if post["owner"] is None)
    token = identity()
    sent = command(universe, 0, "expedition", {"key": target["id"], "army": {"ranger": 5}}, token)
    mission = next(job for job in sent["jobs"] if job["kind"] == "expedition")
    assert sent["units"]["ranger"] == initial["units"]["ranger"] - 5
    assert mission["rules_version"] == EXPEDITION_RULES["version"]
    assert mission["rules_digest"] == EXPEDITION_RULES_DIGEST
    assert "item_drop_rules_version" not in mission
    assert "item_drop_rules_hash" not in mission
    assert (
        command(universe, 0, "expedition", {"key": target["id"], "army": {"ranger": 5}}, token)[
            "units"
        ]["ranger"]
        == initial["units"]["ranger"] - 5
    )

    expected = resolve_expedition(mission["id"], mission["army"])
    clock[0] = mission["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        arrived = game.read(db, users[0])
        assert not any(job["kind"] == "expedition" for job in arrived["jobs"])
        return_job = next(job for job in arrived["jobs"] if job["kind"] == "return")
        assert return_job["army"] == expected["survivors"]
        capacity = sum(expected["survivors"].values()) * (40 + 10 * arrived["tech"]["logistics"])
        assert sum(return_job["loot"]) <= capacity
        requested_items = 0
        carried_items = min(requested_items, capacity - sum(return_job["loot"]))
        expected_item_cargo = {"loot_material": carried_items} if carried_items else {}
        assert return_job["item_cargo"] == expected_item_cargo
        assert sum(return_job["loot"]) + sum(expected_item_cargo.values()) <= capacity
        assert sum(expected_item_cargo.values()) <= 1
        assert all(
            actual <= proposed for actual, proposed in zip(return_job["loot"], expected["loot"])
        )
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='expedition_resolved'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )
    clock[0] = return_job["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        returned = game.read(db, users[0])
        assert (
            returned["units"]["ranger"]
            == initial["units"]["ranger"] - 5 + expected["survivors"]["ranger"]
        )
        assert not any(job["kind"] == "return" for job in returned["jobs"])
        assert returned.get("item_inventory", {}).get("loot_material", 0) == carried_items
        snapshot = json.dumps(
            [returned["units"], returned["resources"], returned.get("item_inventory", {})],
            sort_keys=True,
        )
        game.advance(db, clock[0])
        repeated = game.read(db, users[0])
        assert (
            json.dumps(
                [repeated["units"], repeated["resources"], repeated.get("item_inventory", {})],
                sort_keys=True,
            )
            == snapshot
        )


def test_expedition_carries_and_returns_a_seeded_item_drop_once(universe, monkeypatch):
    from fur_empire import expeditions, item_drops

    monkeypatch.setattr(item_drops, "_roll", lambda seed, item_id: 0)
    original_resolver = expeditions.resolve_expedition

    def discovery(seed, army):
        result = original_resolver(seed, army)
        result["outcome"] = "discovery"
        result["loot"] = [0, 0, 0]
        result["survivors"] = dict(army)
        return result

    monkeypatch.setattr(expeditions, "resolve_expedition", discovery)
    game, users, clock = universe
    initial = state(universe, 0)
    target = next(post for post in initial["world"] if post["owner"] is None)
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["units"]["ranger"] = 1
        game.save(db, colony)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"crafting_ruleset": "FUR-CRAFTING-1"}),),
        )
    sent = command(universe, 0, "expedition", {"key": target["id"], "army": {"ranger": 1}})
    mission = next(job for job in sent["jobs"] if job["kind"] == "expedition")
    clock[0] = mission["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        arrived = game.read(db, users[0])
        return_job = next(job for job in arrived["jobs"] if job["kind"] == "return")
        assert return_job["item_cargo"] == {"loot_material": 1}
        assert return_job["loot"] == [0, 0, 0]
        assert sum(return_job["item_cargo"].values()) <= 1
    clock[0] = return_job["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        returned = game.read(db, users[0])
        assert returned["item_inventory"]["loot_material"] == 1
        assert returned["jobs"] == []
        game.advance(db, clock[0])
        repeated = game.read(db, users[0])
        assert repeated["item_inventory"]["loot_material"] == 1


def test_expedition_rejects_owned_target_and_unavailable_army(universe):
    game, users, _ = universe
    with game.transaction() as db:
        towns = game.world_outposts(db, 1)
        own_post = towns[0]
        own_post["owner"] = users[0]
        game.save_world_outposts(db, 1, towns)
    with pytest.raises(RuleError, match="freien Außenposten"):
        command(universe, 0, "expedition", {"key": own_post["id"], "army": {"ranger": 1}})
    neutral = next(post for post in state(universe, 0)["world"] if post["owner"] is None)
    with pytest.raises(RuleError, match="verfügbare Einheit"):
        command(universe, 0, "expedition", {"key": neutral["id"], "army": {"ranger": 999}})


def test_ruin_exploration_resolution_is_repeatable_bounded_and_versioned():
    army = {"ranger": 12}
    result = ruin_exploration.resolve("0123456789abcdef" * 4, army)
    assert result == ruin_exploration.resolve("0123456789abcdef" * 4, army)
    assert result["rules_version"] == ruin_exploration.VERSION
    assert result["rules_digest"] == ruin_exploration.DIGEST
    ruin_exploration.validate_ruleset(result["rules_version"], result["rules_digest"])
    assert result["outcome"] in {outcome["id"] for outcome in ruin_exploration.RULES["outcomes"]}
    assert 0 <= sum(result["loot"]) <= 160
    assert all(0 <= result["survivors"][unit] <= count for unit, count in army.items())
    small_surveys = [
        ruin_exploration.resolve(f"{index:064x}", {"ranger": 1}) for index in range(50)
    ]
    assert any(sum(survey["loot"]) == 100 for survey in small_surveys)
    assert all(
        sum(survey["loot"]) <= 100 * survey["survivors"]["ranger"] for survey in small_surveys
    )
    assert {ruin_exploration.resolve(f"{index:064x}", army)["outcome"] for index in range(500)} == {
        outcome["id"] for outcome in ruin_exploration.RULES["outcomes"]
    }
    with pytest.raises(ValueError, match="snapshot"):
        ruin_exploration.validate_ruleset(ruin_exploration.VERSION, "sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="army"):
        ruin_exploration.resolve("bad-seed", {"ranger": -1})


def test_ruin_exploration_dispatch_resolves_once_updates_private_fog_and_returns(universe):
    game, users, clock = universe
    initial = state(universe, 0)
    ruin_id = identity()
    with game.transaction() as db:
        home = game.read(db, users[0])
        reachable = travel_times(db, (home["x"], home["y"]), int(home["world_id"]))
        occupied = {(post["x"], post["y"]) for post in game.world_outposts(db, 1)}
        occupied.update(
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=1")
        )
        x, y = next(
            coordinate
            for coordinate in reachable
            if coordinate not in occupied and coordinate != (home["x"], home["y"])
        )
        settings = {"terra_ruin_exploration_ruleset": ruin_exploration.VERSION}
        db.execute("UPDATE world_settings SET settings=? WHERE world_id=1", (json.dumps(settings),))
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET observed_at=excluded.observed_at",
            (users[0], 1, x, y, clock[0] - 3600),
        )
        db.execute(
            "INSERT INTO terra_ruins(id,world_id,x,y,created,expires) VALUES (?,?,?,?,?,?)",
            (ruin_id, 1, x, y, clock[0] - 60, clock[0] + 86400),
        )
    sent = command(universe, 0, "ruin_exploration", {"key": ruin_id, "army": {"ranger": 6}})
    mission = next(job for job in sent["jobs"] if job["kind"] == "ruin_exploration")
    assert sent["units"]["ranger"] == initial["units"]["ranger"] - 6
    assert mission["rules_version"] == ruin_exploration.VERSION
    assert mission["rules_digest"] == ruin_exploration.DIGEST
    assert "seed" not in mission
    with game.transaction() as db:
        private_seed, _, already_resolved = ruin_exploration.mission_seed(
            db, mission["id"], 1, users[0]
        )
        assert not already_resolved
    expected = ruin_exploration.resolve(private_seed, mission["army"])
    clock[0] = mission["due"]
    barrier = Barrier(2)

    def resolve_due_missions():
        barrier.wait(timeout=10)
        with game.transaction() as db:
            game.advance(db, clock[0])

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = [executor.submit(resolve_due_missions) for _ in range(2)]
        for attempt in attempts:
            attempt.result(timeout=120)

    with game.transaction() as db:
        result = db.execute(
            "SELECT outcome,resolved,seed_commitment FROM terra_ruin_explorations WHERE mission_id=?",
            (mission["id"],),
        ).fetchone()
        assert result["outcome"] == json.dumps(expected, sort_keys=True, separators=(",", ":"))
        assert result["resolved"] == mission["due"]
        assert result["seed_commitment"] == expected["seed_commitment"]
        intel = db.execute(
            "SELECT observed_at,expires_at FROM terra_ruin_intel "
            "WHERE observer_id=? AND world_id=1 AND ruin_id=?",
            (users[0], ruin_id),
        ).fetchone()
        assert intel["observed_at"] == mission["due"]
        assert intel["expires_at"] == mission["due"] + 86400
        sector = db.execute(
            "SELECT observed_at FROM map_sector_intel WHERE observer_id=? AND world_id=1 AND x=? AND y=?",
            (users[0], x, y),
        ).fetchone()
        assert sector["observed_at"] == mission["due"]
        owner_state = game.read(db, users[0])
        returning = next(job for job in owner_state["jobs"] if job["kind"] == "return")
        assert returning["loot"] == expected["loot"]
        assert returning["army"] == expected["survivors"]
        assert ruin_id in game.view(db, users[0])["terra_ruin_intel"]
        other_state = game.view(db, users[2])
        assert ruin_id not in other_state.get("terra_ruin_intel", {})
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='ruin_exploration_resolved' AND target=?",
                (users[0], mission["id"]),
            ).fetchone()[0]
            == 1
        )
        result_snapshot = (dict(result), dict(intel), dict(sector))
        game.advance(db, clock[0])
        assert (
            dict(
                db.execute(
                    "SELECT outcome,resolved,seed_commitment FROM terra_ruin_explorations WHERE mission_id=?",
                    (mission["id"],),
                ).fetchone()
            )
            == result_snapshot[0]
        )
    clock[0] = returning["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        game.advance(db, clock[0])
        arrived = game.read(db, users[0])
        assert (
            arrived["units"]["ranger"] == sent["units"]["ranger"] + expected["survivors"]["ranger"]
        )
        assert not any(job["id"] == returning["id"] for job in arrived["jobs"])


def test_ruin_exploration_rejects_disabled_unknown_or_invalid_targets(universe):
    _, _, _ = universe
    with pytest.raises(RuleError, match="nicht aktiviert"):
        command(universe, 0, "ruin_exploration", {"key": identity(), "army": {"ranger": 1}})
    game, users, clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"terra_ruin_exploration_ruleset": ruin_exploration.VERSION}),),
        )
        db.execute(
            "INSERT INTO terra_ruins(id,world_id,x,y,created,expires) VALUES (?,?,?,?,?,?)",
            ("unknown-sector-ruin", 1, 60, 60, clock[0] - 60, clock[0] + 86400),
        )
    with pytest.raises(RuleError, match="noch nicht aufgeklärt"):
        command(
            universe, 0, "ruin_exploration", {"key": "unknown-sector-ruin", "army": {"ranger": 1}}
        )
    with game.transaction() as db:
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, 60, 60, clock[0]),
        )
    with pytest.raises(RuleError, match="Ranger erforderlich"):
        command(
            universe, 0, "ruin_exploration", {"key": "unknown-sector-ruin", "army": {"sentinel": 1}}
        )
    with pytest.raises(RuleError, match="nicht mehr aktiv"):
        command(universe, 0, "ruin_exploration", {"key": "missing-ruin", "army": {"ranger": 1}})


def test_terra_boss_raid_credits_capped_damage_and_pays_once_on_both_adapters(universe):
    game, users, clock = universe
    request = {"name": "Kernwächter"}
    assert state(universe, 0)["terra_boss"]["raid"] is None
    with pytest.raises(RuleError, match="Spielleitung"):
        command(universe, 0, "admin_terra_boss_schedule", request)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        fourth = identity()
        users.append(fourth)
        db.execute("INSERT INTO users VALUES (?,?,?)", (fourth, "Delta", "unused"))
        game.create(db, fourth, "Delta")
        for user in users:
            colony = game.read(db, user)
            colony["units"]["ranger"] = 40
            colony["resources"][2] = 4000
            game.save(db, colony)
    raid = command(universe, 0, "admin_terra_boss_schedule", request)["terra_boss"]["raid"]
    target = {"key": raid["id"]}
    with pytest.raises(RuleError, match="Boss-Zeitfenster"):
        command(universe, 0, "admin_terra_boss_schedule", request)
    with pytest.raises(RuleError, match="aktiven Boss-Zeitfenster"):
        command(universe, 0, "terra_boss_attack", {**target, "count": 16})
    with pytest.raises(RuleError, match="gemeinsamen Sieg"):
        command(universe, 0, "terra_boss_claim", target)

    clock[0] = raid["starts"]
    for index, count in enumerate((16, 40, 20, 1)):
        attack = command(universe, index, "terra_boss_attack", {**target, "count": count})
        assert attack["units"]["ranger"] == 40 - count
        assert attack["terra_boss"]["raid"]["joined"]
        clock[0] += 1
    with pytest.raises(RuleError, match="bereits gebucht"):
        command(universe, 0, "terra_boss_attack", {**target, "count": 1})

    clock[0] += 300
    with game.transaction() as db:
        game.advance(db, clock[0])
        game.advance(db, clock[0])
        contributions = [
            tuple(row.values()) if isinstance(row, dict) else tuple(row)
            for row in db.execute(
                "SELECT damage,survivors FROM terra_boss_contributions WHERE raid_id=? ORDER BY due",
                (raid["id"],),
            )
        ]
        assert contributions == [(400, 14), (500, 36), (100, 16), (0, 1)]
        assert game.view(db, users[0])["terra_boss"]["raid"]["remaining_health"] == 0
        assert game.view(db, users[3])["terra_boss"]["rewards"] == []
    with pytest.raises(RuleError, match="keine Belohnung"):
        command(universe, 3, "terra_boss_claim", target)

    clock[0] += 301
    with game.transaction() as db:
        game.advance(db, clock[0])
        assert [game.read(db, user)["units"]["ranger"] for user in users] == [38, 36, 36, 40]
        assert [game.view(db, user)["terra_boss"]["rewards"][0]["ore"] for user in users[:3]] == [
            2400,
            3000,
            600,
        ]

    barrier = Barrier(2)

    def try_claim():
        barrier.wait(timeout=10)
        try:
            return command(universe, 0, "terra_boss_claim", target)["reserve"][2]
        except RuleError as exc:
            assert "keine Belohnung" in str(exc)
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        claims = [executor.submit(try_claim) for _ in range(2)]
        assert [amount for attempt in claims if (amount := attempt.result(timeout=120))] == [2400]
    for index, ore in ((1, 3000), (2, 600)):
        assert command(universe, index, "terra_boss_claim", target)["reserve"][2] == ore
    assert sum(state(universe, index)["reserve"][2] for index in range(4)) == 6000


def secondary_colony(universe, index):
    game, users, _ = universe
    with game.transaction() as db:
        home = game.read(db, users[index])
        home["buildings"]["hq"] = 3
        home["resources"] = [10000, 10000, 10000]
        game.save(db, home)
        occupied = {
            (town["x"], town["y"])
            for town in json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        }
        colony_rows = db.execute("SELECT state FROM colonies WHERE world_id=1").fetchall()
        colonies = [json.loads(row[0]) for row in colony_rows]
        occupied.update((colony["x"], colony["y"]) for colony in colonies)
        x, y = next(
            (x, y)
            for y in range(64)
            for x in range(64)
            if (x, y) not in occupied
            and all(math.hypot(x - colony["x"], y - colony["y"]) >= 6 for colony in colonies)
        )
    command(universe, index, "colonize", {"x": x, "y": y})
    with game.transaction() as db:
        return db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND is_home=FALSE",
            (users[index],),
        ).fetchone()[0]


def test_home_designation_preserves_colonies_and_enforces_world_cooldown(universe):
    game, users, clock = universe
    colony_id = secondary_colony(universe, 0)
    with game.transaction() as db:
        before = {
            row["colony_id"]: json.loads(row["state"])
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=?", (users[0],)
            )
        }
        old_home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=1 AND is_home=TRUE",
            (users[0],),
        ).fetchone()[0]
    token = identity()
    changed = command(universe, 0, "colony_home", {"key": colony_id}, token)
    command(universe, 0, "colony_home", {"key": colony_id}, token)
    assert changed["home_designation"]["available"] is False
    with game.transaction() as db:
        homes = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=1 AND is_home=TRUE",
            (users[0],),
        ).fetchall()
        assert [row[0] for row in homes] == [colony_id]
        for key, original in before.items():
            current = game.read_colony(db, key)
            for field in ("resources", "units", "jobs", "x", "y", "buildings", "tech"):
                assert current[field] == original[field]
    with pytest.raises(RuleError, match="24 Stunden"):
        command(universe, 0, "colony_home", {"key": old_home})
    with pytest.raises(RuleError, match="eigene Kolonie"):
        command(universe, 1, "colony_home", {"key": colony_id})
    clock[0] += 86400
    command(universe, 0, "colony_home", {"key": old_home})


def test_neutral_goods_retry_and_account_isolation_on_each_adapter(universe):
    game, users, _ = universe
    token = identity()
    payload = {"goods_source": "wood", "goods_destination": "alloy", "amount": 100}
    command(universe, 0, "goods_trade", payload, token)
    command(universe, 0, "goods_trade", payload, token)
    with game.transaction() as db:
        assert game.read(db, users[0])["goods_inventory"]["alloy"] == 4
        assert not game.read(db, users[1]).get("goods_inventory")
        assert (
            db.execute(
                "SELECT count(*) FROM neutral_goods_trades WHERE owner=?", (users[0],)
            ).fetchone()[0]
            == 1
        )


def test_schema_29_to_31_is_additive_and_preserves_colony_json(universe):
    game, users, _ = universe
    with game.transaction() as db:
        before = [
            (row["colony_id"], row["state"])
            for row in db.execute("SELECT colony_id,state FROM colonies ORDER BY colony_id")
        ]
        # The fixture is always a temporary SQLite DB or disposable PG schema.
        db.execute("DROP TABLE neutral_goods_trades")
        db.execute("DROP TABLE colony_home_changes")
        if db.postgres:
            db.execute("DROP FUNCTION reject_neutral_goods_change()")
        db.execute("DELETE FROM schema_versions WHERE version IN (30,31)")
    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        after = [
            (row["colony_id"], row["state"])
            for row in db.execute("SELECT colony_id,state FROM colonies ORDER BY colony_id")
        ]
        assert before == after
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM colony_home_changes").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == len(users)


def test_player_transport_stays_in_source_world_after_recipient_switches(universe):
    game, users, clock = universe
    with game.transaction() as db:
        source = game.read(db, users[0])
        target = game.read(db, users[1])
        # Only resource stocks are frozen; mission resolution still uses the worker.
        target["resources"] = [4000, 4000, 4000]
        game.save(db, target)
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET observed_at=excluded.observed_at",
            (users[0], 1, target["x"], target["y"], clock[0]),
        )
    dispatched = command(
        universe,
        0,
        "transport",
        {
            "key": users[1],
            "army": {"ranger": 1},
            "resources": [10, 0, 0],
        },
    )
    mission = next(job for job in dispatched["jobs"] if job["kind"] == "transport")
    assert mission["target_colony_id"] == target["colony_id"]
    with game.transaction() as db:
        world_id = game.create_world(db, "Recipient Orbit Boundary", 71991, 8, True)
        game.join_world(db, users[1], "Bravo", world_id)
        other_colony = game.read(db, users[1])
    clock[0] = mission["due"]
    cycle(game)
    with game.transaction() as db:
        original = game.read_colony(db, target["colony_id"])
        other = game.read_colony(db, other_colony["colony_id"])
        assert original["reserve"][0] == 10
        assert not other.get("reserve", [0, 0, 0])[0]
        assert original["world_id"] == source["world_id"] != other["world_id"]


def test_colony_supply_delivers_to_selected_base_overflow_and_returns_carriers(universe):
    game, users, clock = universe
    destination = secondary_colony(universe, 0)
    with game.transaction() as db:
        source = game.read(db, users[0])
        source["resources"] = [2000, 2000, 2000]
        source["goods_inventory"] = {"alloy": 50}
        source["item_inventory"] = {"repair_kit": 10}
        source["units"]["ranger"] = 10
        source["last"] = clock[0]
        game.save(db, source)
        target = game.read_colony(db, destination)
        target["resources"] = [3990, 3990, 3990]
        target["reserve"] = [0, 0, 0]
        target["last"] = clock[0]
        game.save(db, target)

    token = identity()
    payload = {
        "key": destination,
        "army": {"ranger": 2},
        "resources": [24, 24, 23],
        "goods": {"alloy": 5},
        "items": {"repair_kit": 4},
    }
    dispatched = command(universe, 0, "colony_supply", payload, token)
    source_id = dispatched["colony_id"]
    supply_jobs = [job for job in dispatched["jobs"] if job["kind"] == "colony_supply"]
    assert len(supply_jobs) == 1
    arrival = supply_jobs[0]["due"]
    travel = supply_jobs[0]["travel"]
    assert dispatched["units"]["ranger"] == 8
    assert dispatched["resources"] == [1976, 1976, 1977]
    assert dispatched["neutral_market"]["goods"][3]["amount"] == 45
    assert (
        next(item for item in dispatched["generic_items"]["items"] if item["id"] == "repair_kit")[
            "amount"
        ]
        == 6
    )

    # Replaying the identical client token must not create another shipment.
    replayed = command(universe, 0, "colony_supply", payload, token)
    assert sum(job["kind"] == "colony_supply" for job in replayed["jobs"]) == 1
    assert replayed["resources"] == dispatched["resources"]

    clock[0] = arrival
    game = Game(game.path)
    with game.transaction() as db:
        game.advance(db, clock[0])
        target = game.read_colony(db, destination)
        assert target["resources"] == [4000, 4000, 4000]
        assert target["reserve"] == [24, 24, 23]
        assert target["goods_inventory"]["alloy"] == 5
        assert target.get("goods_inbound", {}) == {}
        assert target["item_inventory"]["repair_kit"] == 4
        assert target.get("item_inbound", {}) == {}
        source = game.read_colony(db, source_id)
        assert source["units"]["ranger"] == 8
        assert any(
            report["title"] == "Kolonieversorgung zugestellt" for report in source["reports"]
        )
        assert any(
            report["title"] == "Kolonieversorgung eingetroffen" for report in target["reports"]
        )
        assert len([job for job in source["jobs"] if job["kind"] == "return"]) == 1

    clock[0] = arrival + travel
    with game.transaction() as db:
        game.advance(db, clock[0])
        source = game.read_colony(db, source_id)
        assert source["units"]["ranger"] == 10
        assert source["jobs"] == []
        game.advance(db, clock[0])
        assert game.read_colony(db, source_id)["units"]["ranger"] == 10
        assert game.read_colony(db, destination)["reserve"] == [24, 24, 23]


def test_colony_supply_rejects_foreign_or_same_colony_target(universe):
    _, users, _ = universe
    own_destination = secondary_colony(universe, 0)
    with pytest.raises(RuleError, match="eigenen Kolonien"):
        command(
            universe,
            0,
            "colony_supply",
            {"key": users[1], "army": {"ranger": 1}, "resources": [1, 0, 0]},
        )
    with pytest.raises(RuleError, match="andere eigene Kolonie"):
        command(
            universe,
            0,
            "colony_supply",
            {"key": users[0], "army": {"ranger": 1}, "resources": [1, 0, 0]},
        )
    assert own_destination != users[0]


def test_colony_rename_is_owner_scoped_globally_unique_and_idempotent(universe):
    game, users, _ = universe
    secondary = secondary_colony(universe, 0)
    token = identity()
    payload = {"colony_id": secondary, "name": "Nordhafen 7"}
    renamed = command(universe, 0, "colony_rename", payload, token)
    assert (
        next(c["name"] for c in renamed["colonies"] if c["colony_id"] == secondary) == "Nordhafen 7"
    )
    replay = command(universe, 0, "colony_rename", payload, token)
    assert (
        next(c["name"] for c in replay["colonies"] if c["colony_id"] == secondary) == "Nordhafen 7"
    )
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='colony_rename' AND target=?",
            (users[0], secondary),
        ).fetchone()
        assert json.loads(audit["details"])["name"] == "Nordhafen 7"

    with pytest.raises(RuleError, match="gehört nicht"):
        command(universe, 1, "colony_rename", {"colony_id": secondary, "name": "Fremde Basis"})
    with pytest.raises(RuleError, match="weltweit bereits vergeben"):
        command(universe, 0, "colony_rename", {"colony_id": secondary, "name": "Alpha"})
    with pytest.raises(RuleError, match="weltweit bereits vergeben"):
        command(universe, 0, "colony_rename", {"colony_id": secondary, "name": "aLpHa"})
    with game.transaction() as db:
        world_id = game.create_world(db, "Zweite Welt", 90210, 8, True)
        game.join_world(db, users[1], "Bravo", world_id)
    with pytest.raises(RuleError, match="weltweit bereits vergeben"):
        command(universe, 0, "colony_rename", {"colony_id": secondary, "name": "Bravo"})
    for invalid in ("ab", "Name!", "Name_test", "   ", "x" * 33):
        with pytest.raises(RuleError):
            command(universe, 0, "colony_rename", {"colony_id": secondary, "name": invalid})
    assert (
        next(c["name"] for c in state(universe, 0)["colonies"] if c["colony_id"] == secondary)
        == "Nordhafen 7"
    )


def test_orbit_failure_quarantines_only_its_job_and_admin_can_retry(universe, monkeypatch):
    from fur_empire.orbit_rules import VERSION

    game, users, clock = universe
    with game.transaction() as db:
        for user in users[:2]:
            db.execute(
                "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) VALUES (?,1,?,?)",
                (user, VERSION, clock[0]),
            )
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    first = command(
        universe, 0, "orbit_colonize", {"world_id": 1, "galaxy": 1, "system": 1, "slot": 1}
    )
    clock[0] += 1
    second = command(
        universe, 1, "orbit_colonize", {"world_id": 1, "galaxy": 1, "system": 1, "slot": 2}
    )
    with game.transaction() as db:
        failed = db.execute(
            "SELECT mission_id FROM orbit_planet_claims WHERE owner=?", (users[0],)
        ).fetchone()[0]
    resolve = game.process_orbit_event

    def fail_one(db, kind, event_id, due):
        if event_id == failed:
            raise ValueError("test failure")
        resolve(db, kind, event_id, due)

    monkeypatch.setattr(game, "process_orbit_event", fail_one)
    clock[0] = second["orbit_access"]["claims"][0]["arrival"] + 10
    for _ in range(4):
        cycle(game)
    with game.transaction() as db:
        failure = db.execute(
            "SELECT id,attempts,error FROM job_failures WHERE user_id=? AND job_id=?",
            (users[0], "orbit:claim:" + failed),
        ).fetchone()
        assert failure["attempts"] == 3
        assert failure["error"] == "ValueError"
        assert db.execute("SELECT lag_seconds FROM scheduler_status WHERE id=1").fetchone()[0] == 10
    assert state(universe, 0)["orbit_access"]["claims"][0]["founded_at"] is None
    assert state(universe, 1)["orbit_access"]["claims"][0]["founded_at"] is not None
    monkeypatch.setattr(game, "process_orbit_event", resolve)
    retried = command(universe, 0, "admin_retry", {"key": failure["id"]})
    assert (
        retried["orbit_access"]["claims"][0]["founded_at"]
        == first["orbit_access"]["claims"][0]["arrival"]
    )


def test_syndicate_convoy_delivers_purchased_escrow_once_to_selected_colony(universe):
    game, users, clock = universe
    target = secondary_colony(universe, 0)
    command(universe, 0, "faction", {"key": "syndicate"})
    with game.transaction() as db:
        buyer = game.read(db, users[0])
        buyer["faction_research"] = ["smuggler_navigation"]
        game.save(db, buyer)
    listed = command(
        universe, 1, "market_create", {"give": 0, "amount": 50, "want": 1, "price": 20}
    )
    offer = next(item for item in listed["offers"] if item["owner"] == users[1])
    token = identity()
    payload = {"key": offer["id"], "colony_id": target}
    ordered = command(universe, 0, "market_protected_convoy", payload, token)
    assert ordered["syndicate_convoys"][0]["amount"] == 50
    assert ordered["syndicate_convoys"][0]["target"] == target
    assert (
        command(universe, 0, "market_protected_convoy", payload, token)["syndicate_convoys"]
        == ordered["syndicate_convoys"]
    )
    clock[0] = ordered["syndicate_convoys"][0]["due"]
    cycle(game)
    cycle(game)
    with game.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM terra_market_convoys").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT COUNT(*) FROM ledger WHERE user_id=? AND action='Syndikatkonvoi eingetroffen'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT status FROM offers WHERE id=?", (offer["id"],)).fetchone()[0]
            == "filled"
        )


def test_warden_fortification_requires_current_alliance_and_expires(universe):
    game, users, clock = universe
    command(universe, 0, "faction", {"key": "wardens"})
    with game.transaction() as db:
        source = game.read(db, users[0])
        source["faction_research"] = ["kinetic_shield"]
        game.save(db, source)
        target = game.read(db, users[1])
        alliance = identity()
        db.execute(
            "INSERT INTO alliances(id,tag,name,description,leader,created) VALUES (?,?,?,?,?,?)",
            (alliance, "FORT", "Fortification", "", users[0], clock[0]),
        )
        db.execute("INSERT INTO members VALUES (?,?,'leader')", (users[0], alliance))
        db.execute("INSERT INTO members VALUES (?,?,'member')", (users[1], alliance))
        base = game.systems.player_defense(target, "pioneers")
    payload = {"world_id": 1, "key": target["colony_id"]}
    before = state(universe, 0)["resources"][2]
    fortified = command(universe, 0, "terra_warden_fortify", payload)
    assert fortified["resources"][2] == before - 200
    with game.transaction() as db:
        target = game.read(db, users[1])
        assert (
            game.systems.fortified_player_defense(db, target, "pioneers", clock[0])
            == base * 110 // 100
        )
        assert (
            game.systems.fortified_player_defense(db, target, "pioneers", clock[0] + 3600) == base
        )
        db.execute("DELETE FROM members WHERE user_id=?", (users[1],))
        assert game.systems.fortified_player_defense(db, target, "pioneers", clock[0]) == base


def test_faction_research_requires_world_faction_and_changes_wood_rate(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=4, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)
    initial = command(universe, 0, "faction", {"key": "pioneers"})
    with pytest.raises(RuleError, match="freigeschalteten Fraktion"):
        command(universe, 0, "terra_faction_research", {"key": "kinetic_shield"})
    queued = command(universe, 0, "terra_faction_research", {"key": "adaptive_forestry"})
    clock[0] = next(job["due"] for job in queued["jobs"] if job["kind"] == "terra_faction_research")
    cycle(game)
    done = state(universe, 0)
    assert done["faction_research"] == ["adaptive_forestry"]
    assert (
        done["production_details"][0]["bonus_percent"]
        == initial["production_details"][0]["bonus_percent"] + 5
    )
    with pytest.raises(RuleError, match="bereits abgeschlossen"):
        command(universe, 0, "terra_faction_research", {"key": "adaptive_forestry"})
    with game.transaction() as db:
        start = (done["x"], done["y"])
        occupied = {(town["x"], town["y"]) for town in game.world_outposts(db, 1)}
        neighbors = db.execute("SELECT x,y FROM colonies WHERE world_id=1").fetchall()
        x, y = next(
            point
            for point in sorted(travel_times(db, start, 1))
            if math.hypot(point[0] - start[0], point[1] - start[1]) <= 12
            and point not in occupied
            and all(math.hypot(point[0] - row["x"], point[1] - row["y"]) >= 6 for row in neighbors)
        )
    surveyed = command(universe, 0, "terra_pioneer_survey", {"world_id": 1, "x": x, "y": y})
    assert surveyed["pioneer_survey"]["expires"] == clock[0] + 3600
    with pytest.raises(RuleError, match="Abklingzeit"):
        command(universe, 0, "terra_pioneer_survey", {"world_id": 1, "x": x, "y": y})
    founded = command(universe, 0, "colonize", {"x": x, "y": y})
    assert founded["resources"] == [
        stock - cost for stock, cost in zip(surveyed["resources"], (1840, 1380, 920))
    ]
    assert "pioneer_survey" not in founded


@pytest.mark.parametrize(
    ("research_key", "owner_faction"),
    [(key, definition[0]) for key, definition in FACTION_RESEARCH.items()],
)
def test_every_faction_research_is_owner_scoped_idempotent_and_completes(
    universe, research_key, owner_faction
):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=4, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)

    before = state(universe, 0)["resources"]
    command(universe, 0, "faction", {"key": owner_faction})
    foreign_key = next(key for key, rule in FACTION_RESEARCH.items() if rule[0] != owner_faction)
    with pytest.raises(RuleError, match="freigeschalteten Fraktion"):
        command(universe, 0, "terra_faction_research", {"key": foreign_key})

    token = identity()
    payload = {"key": research_key}
    queued = command(universe, 0, "terra_faction_research", payload, token)
    replay = command(universe, 0, "terra_faction_research", payload, token)
    costs = FACTION_RESEARCH[research_key][1]
    assert queued["resources"] == [stock - cost for stock, cost in zip(before, costs)]
    assert replay["resources"] == queued["resources"]
    assert [job["key"] for job in replay["jobs"] if job["kind"] == "terra_faction_research"] == [
        research_key
    ]

    clock[0] = next(job["due"] for job in queued["jobs"] if job["kind"] == "terra_faction_research")
    cycle(game)
    completed = state(universe, 0)
    assert completed["faction_research"] == [research_key]


def test_terra_trade_route_reserves_carriers_returns_and_pauses_on_shortage(universe):
    game, users, clock = universe
    destination = secondary_colony(universe, 0)
    with game.transaction() as db:
        source = game.read(db, users[0])
        source["units"]["ranger"] = 1
        game.save(db, source)
    scope = {"world_id": 1, "colony_id": source["colony_id"]}
    route_payload = {
        **scope,
        "key": destination,
        "army": {"ranger": 1},
        "resources": [25, 0, 0],
    }
    for invalid_hours in (0, 169):
        with pytest.raises(RuleError, match="Ungültige Träger"):
            command(
                universe,
                0,
                "terra_route_create",
                {**route_payload, "hours": invalid_hours},
            )
    created = command(
        universe,
        0,
        "terra_route_create",
        {**route_payload, "hours": 1},
    )
    route = created["terra_trade_routes"][0]
    with pytest.raises(RuleError, match="besteht bereits"):
        command(universe, 0, "terra_route_create", {**route_payload, "hours": 1})
    clock[0] = route["due"]
    cycle(game)
    launched = state(universe, 0)
    flight = next(job for job in launched["jobs"] if job.get("route_id") == route["id"])
    assert launched["units"]["ranger"] == 0
    assert flight["loot"] == [25, 0, 0]
    clock[0] = flight["due"] + flight["travel"]
    cycle(game)
    cycle(game)
    returned = state(universe, 0)
    assert returned["units"]["ranger"] == 1
    assert not any(job.get("route_id") == route["id"] for job in returned["jobs"])
    with game.transaction() as db:
        source = game.read(db, users[0])
        source["units"]["ranger"] = 0
        game.save(db, source)
    clock[0] = returned["terra_trade_routes"][0]["due"]
    cycle(game)
    assert state(universe, 0)["terra_trade_routes"][0]["paused"]
    resumed = command(universe, 0, "terra_route_resume", {**scope, "key": route["id"]})
    assert not resumed["terra_trade_routes"][0]["paused"]
    stopped = command(universe, 0, "terra_route_stop", {**scope, "key": route["id"]})
    assert not stopped["terra_trade_routes"]
    maximum = command(universe, 0, "terra_route_create", {**route_payload, "hours": 168})
    assert maximum["terra_trade_routes"][0]["interval_seconds"] == 168 * 3600
    command(
        universe,
        0,
        "terra_route_stop",
        {**scope, "key": maximum["terra_trade_routes"][0]["id"]},
    )


def test_terra_prestige_requires_world_opt_in_and_preserves_hq_level(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=10, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        colony["terra_prestige_level"] = 4
        colony["terra_energy_levels"] = {"command_uplink": 6}
        game.save(db, colony)
    with pytest.raises(RuleError, match="nicht freigegeben"):
        command(universe, 0, "terra_prestige")
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(universe, 0, "admin_enable_terra_prestige", {"world_id": 1})
    queued = command(universe, 0, "terra_prestige")
    assert queued["resources"] == [2500, 2500, 2000]
    assert queued["terra_mission_limit"] == 40
    clock[0] = next(job["due"] for job in queued["jobs"] if job["kind"] == "terra_prestige")
    cycle(game)
    finished = state(universe, 0)
    assert finished["buildings"]["hq"] == 10
    assert finished["terra_prestige"]["level"] == 5
    assert finished["terra_mission_limit"] == 42


def test_terra_special_buildings_extend_sight_and_mission_limit_on_completion(universe):
    from fur_empire.fog import visible_sectors

    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=3, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)
        before = visible_sectors(db, users[0], 1)
    scanner = command(universe, 0, "terra_energy_build", {"key": "scanner_tower"})
    clock[0] = next(job["due"] for job in scanner["jobs"] if job["kind"] == "terra_energy_build")
    cycle(game)
    with game.transaction() as db:
        assert visible_sectors(db, users[0], 1) > before
    uplink = command(universe, 0, "terra_energy_build", {"key": "command_uplink"})
    assert uplink["terra_mission_limit"] == 30
    clock[0] = next(job["due"] for job in uplink["jobs"] if job["kind"] == "terra_energy_build")
    cycle(game)
    assert state(universe, 0)["terra_mission_limit"] == 32


def test_terra_energy_modules_complete_and_throttle_bonus_under_shortage(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=7, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)
    fusion = command(universe, 0, "terra_energy_build", {"key": "fusion_plant"})
    assert fusion["resources"] == [4300, 4200, 3600]
    assert fusion["terra_energy"]["demand"] == 0
    clock[0] = next(job["due"] for job in fusion["jobs"] if job["kind"] == "terra_energy_build")
    cycle(game)
    assert state(universe, 0)["terra_energy"] == {
        "supply": 0,
        "demand": 6,
        "served": 0,
        "ore_bonus": 0,
    }
    core = command(universe, 0, "terra_energy_build", {"key": "energy_core"})
    clock[0] = next(job["due"] for job in core["jobs"] if job["kind"] == "terra_energy_build")
    cycle(game)
    assert state(universe, 0)["terra_energy"] == {
        "supply": 4,
        "demand": 6,
        "served": 4,
        "ore_bonus": 8,
    }
    clock[0] = state(universe, 0)["fusion_supplied_until"]
    cycle(game)
    expired = state(universe, 0)
    assert expired["terra_energy"]["ore_bonus"] == 0
    token = identity()
    fueled = command(universe, 0, "terra_fusion_supply", token=token)
    assert fueled["resources"][2] == expired["resources"][2] - 120
    assert fueled["terra_energy"]["ore_bonus"] == 8
    assert (
        command(universe, 0, "terra_fusion_supply", token=token)["resources"] == fueled["resources"]
    )


def test_overdue_orbit_scout_observes_before_later_shipyard_completion(universe):
    from fur_empire.orbit_rules import VERSION

    game, users, clock = universe
    origin, destination = identity(), identity()
    with game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) VALUES (?,1,?,?)",
            (users[0], VERSION, clock[0]),
        )
        for slot, colony in ((1, origin), (2, destination)):
            db.execute(
                "INSERT INTO orbit_planet_claims "
                "(world_id,galaxy,system_no,slot,owner,mission_id,rule_version,arrival,founded_at) "
                "VALUES (1,1,1,?,?,?,?,?,?)",
                (slot, users[0], colony, VERSION, clock[0], clock[0]),
            )
    cycle(game)
    with game.transaction() as db:
        db.execute("INSERT INTO orbit_ships VALUES (?,'probe',0)", (origin,))
        db.execute(
            "INSERT INTO orbit_scouts(id,origin,galaxy,system_no,slot,due,duration,rule_version,intel_level) "
            "VALUES (?,?,1,1,2,?,60,?,2)",
            (identity(), origin, clock[0] + 60, VERSION),
        )
        db.execute(
            "INSERT INTO orbit_ship_orders VALUES (?,'probe',3,?)", (destination, clock[0] + 90)
        )
    clock[0] += 200
    cycle(game)
    cycle(game)
    with game.transaction() as db:
        assert db.execute("SELECT ships FROM orbit_intel").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT amount FROM orbit_ships WHERE mission_id=?", (destination,)
            ).fetchone()[0]
            == 3
        )
        assert (
            db.execute("SELECT amount FROM orbit_ships WHERE mission_id=?", (origin,)).fetchone()[0]
            == 1
        )
        other_world = game.create_world(db, "Reference boundary", 48192, 8)
        terra_id = game.read(db, users[0])["colony_id"]
        foreign_orbit = identity()
        db.execute(
            "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) VALUES (?,?,?,?)",
            (users[0], other_world, VERSION, clock[0]),
        )
        db.execute(
            "INSERT INTO orbit_planet_claims "
            "(world_id,galaxy,system_no,slot,owner,mission_id,rule_version,arrival,founded_at) "
            "VALUES (?,1,1,1,?,?,?,?,?)",
            (other_world, users[0], foreign_orbit, VERSION, clock[0], clock[0]),
        )
    cycle(game)
    with pytest.raises(Exception, match="invalid mission world"), game.transaction() as db:
        db.execute(
            "INSERT INTO terra_orbit_cargo(id,terra_colony,orbit_colony,to_orbit,ore,due,rule_version) "
            "VALUES (?,?,?,TRUE,10,?,?)",
            (identity(), terra_id, foreign_orbit, clock[0] + 60, VERSION),
        )
    with pytest.raises(Exception, match="invalid mission world"), game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_transports(id,origin,target,ore,ether,ships,due,duration,rule_version) "
            "VALUES (?,?,?,10,0,1,?,60,?)",
            (identity(), origin, foreign_orbit, clock[0] + 60, VERSION),
        )
    with game.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM terra_orbit_cargo").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM orbit_transports").fetchone()[0] == 0


def test_bound_command_replay_cannot_apply_after_world_switch(universe):
    from fur_empire.contracts import CommandOrigin

    game, users, _ = universe
    current = state(universe, 0)
    origin = CommandOrigin(
        world_id=1, colony_id=current["colony_id"], rule_version=REGISTRY["version"]
    )
    payload = {"colony_id": current["colony_id"], "name": "Alpha Gebunden"}
    token = identity()
    with game.transaction() as db:
        game.command(db, users[0], "colony_rename", payload, token, origin)
        receipt = db.execute(
            "SELECT signature,origin_world_id,origin_colony_id,rule_version "
            "FROM commands WHERE user_id=? AND token=?",
            (users[0], token),
        ).fetchone()
        assert receipt["signature"].startswith("sha256:")
        assert payload["name"] not in receipt["signature"]
        assert receipt["origin_world_id"] == 1
        assert receipt["origin_colony_id"] == current["colony_id"]
        assert receipt["rule_version"] == REGISTRY["version"]
        second = game.create_world(db, "Idempotency frontier", 48192, 8)
    command(universe, 0, "world_join", {"world_id": second})
    with pytest.raises(RuleError, match="nicht mehr aktiv"), game.transaction() as db:
        game.command(db, users[0], "colony_rename", payload, identity(), origin)
    with game.transaction() as db:
        replay = game.command(db, users[0], "colony_rename", payload, token, origin)
        assert replay["world_id"] == second
        assert (
            db.execute(
                "SELECT COUNT(*) FROM game_event_outbox WHERE recipient=? AND kind='colony_rename'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )
    with pytest.raises(RuleError, match="anders verwendet"), game.transaction() as db:
        game.command(
            db, users[0], "colony_rename", {**payload, "name": "Andere Basis"}, token, origin
        )


def test_game_event_outbox_retries_publication_and_isolates_recipient_and_world(universe):
    from fur_empire import game_events

    game, users, _ = universe
    terra = state(universe, 0)
    payload = {"colony_id": terra["colony_id"], "name": "Alpha Protokoll"}
    token = identity()
    command(universe, 0, "colony_rename", payload, token)
    command(universe, 0, "colony_rename", payload, token)
    with pytest.raises(RuntimeError, match="simulated crash"), game.transaction() as db:
        assert not game_events.page(db, users[0], 1, None)["events"]
        assert db.execute("SELECT COUNT(*) FROM game_event_outbox").fetchone()[0] == 1
        game_events.publish(db)
        raise RuntimeError("simulated crash")
    with game.transaction() as db:
        assert not game_events.page(db, users[0], 1, None)["events"]
        assert db.execute("SELECT COUNT(*) FROM game_event_outbox").fetchone()[0] == 1
    cycle(game)
    cycle(game)
    with game.transaction() as db:
        page = game_events.page(db, users[0], 1, None)
        assert [entry["kind"] for entry in page["events"]] == ["colony_rename"]
        assert not game_events.page(db, users[0], 1, page["cursor"])["events"]
        assert not game_events.page(db, users[1], 1, None)["events"]
        assert not game_events.page(db, users[0], 2, None)["events"]
        assert db.execute("SELECT COUNT(*) FROM game_event_outbox").fetchone()[0] == 0


def test_game_event_preferences_mute_categories_and_keep_delivery_failures_private(
    universe, monkeypatch
):
    from fur_empire import game_events

    game, users, clock = universe
    with game.transaction() as db:
        db.execute(
            "INSERT INTO game_event_preferences(user_id,category,muted,updated) VALUES (?,?,1,?)",
            (users[0], "economy", clock[0]),
        )
        game_events.stage(db, identity(), users[0], 1, "build", clock[0])
        game_events.stage(db, identity(), users[0], 1, "attack", clock[0] + 1)
        game_events.publish(db)
        page = game_events.page(db, users[0], 1, None)
        assert [event["category"] for event in page["events"]] == ["military"]
        assert page["preferences"]["economy"] is True
        assert not game_events.page(db, users[1], 1, None)["delivery_failures"]

    failing_event = identity()
    with game.transaction() as db:
        game_events.stage(db, failing_event, users[0], 1, "research", clock[0] + 2)

    original_execute = game.execute if hasattr(game, "execute") else None
    del original_execute
    original = game_events.muted

    def fail_one(db, user, kind):
        if kind == "research":
            raise RuntimeError("simulated delivery store failure")
        return original(db, user, kind)

    monkeypatch.setattr(game_events, "muted", fail_one)
    for _ in range(5):
        with game.transaction() as db:
            game_events.publish(db)
    with game.transaction() as db:
        failures = game_events.page(db, users[0], 1, None)["delivery_failures"]
        assert failures == [
            {
                "id": failing_event,
                "kind": "research",
                "attempts": 5,
                "failed_at": clock[0] + 2,
                "category": "research",
            }
        ]
        assert not game_events.page(db, users[1], 1, None)["delivery_failures"]
        assert (
            db.execute(
                "SELECT count(*) FROM game_event_outbox WHERE id=?", (failing_event,)
            ).fetchone()[0]
            == 0
        )


def test_game_event_category_filter_and_cursor_page_older_history(universe):
    from fur_empire import game_events

    game, users, clock = universe
    with game.transaction() as db:
        for index in range(60):
            kind = "attack" if index % 2 else "build"
            game_events.stage(db, identity(), users[0], 1, kind, clock[0] + index)
        game_events.publish(db)
        newest = game_events.page(db, users[0], 1, None)
        assert len(newest["events"]) == game_events.PAGE_SIZE
        assert newest["has_more"] is True
        assert newest["events"][0]["sequence"] < newest["events"][-1]["sequence"]
        filtered = game_events.page(db, users[0], 1, None, "military")
        assert filtered["events"]
        assert all(event["category"] == "military" for event in filtered["events"])
        older = game_events.page(db, users[0], 1, newest["cursor"])
        assert len(older["events"]) == 10
        assert older["has_more"] is False
        assert max(event["sequence"] for event in older["events"]) < newest["cursor"]


def test_game_event_category_mapping_covers_major_domain_action_families():
    from fur_empire.game_events import category_for

    expected = {
        "build": "economy",
        "market_create": "economy",
        "alliance_project_create": "economy",
        "alliance_project_cancel": "economy",
        "research": "research",
        "terra_faction_research": "research",
        "attack": "military",
        "outpost_colonize": "military",
        "colonize": "economy",
        "terra_defense_build": "military",
        "terra_defense_repair": "military",
        "alliance_attack_create": "military",
        "alliance_create": "social",
        "friend_request": "social",
        "message_report": "social",
        "profile_settings_update": "system",
        "admin_ban": "system",
        "unknown_future_event": "system",
    }
    assert {kind: category_for(kind) for kind in expected} == expected


def test_terra_inactivity_warns_then_pauses_and_restores_without_deleting(universe):
    game, users, clock = universe
    secondary = secondary_colony(universe, 0)
    with game.transaction() as db:
        db.execute(
            "INSERT INTO terra_inactivity(user_id,last_seen) VALUES (?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET last_seen=excluded.last_seen",
            (users[0], clock[0] - 30 * 86400),
        )
    cycle(game)
    with game.transaction() as db:
        lifecycle = db.execute(
            "SELECT warned_at,dormant_at FROM terra_inactivity WHERE user_id=?", (users[0],)
        ).fetchone()
        assert lifecycle["warned_at"] == clock[0]
        assert lifecycle["dormant_at"] is None
    clock[0] += 7 * 86400
    cycle(game)
    dormant = state(universe, 0)
    assert dormant["terra_dormant"]
    assert any(row["colony_id"] == secondary for row in dormant["colonies"])
    with pytest.raises(RuleError, match="Reaktiviere"):
        command(universe, 0, "build", {"key": "wood"})
    clock[0] += 86400
    cycle(game)
    assert state(universe, 0)["resources"] == dormant["resources"]
    restored = command(universe, 0, "terra_reactivate")
    assert not restored.get("terra_dormant")
    assert restored["resources"] == dormant["resources"]
    with game.transaction() as db:
        assert not game.read_colony(db, secondary).get("terra_dormant")


def test_colony_abandon_resolves_jobs_supplies_offers_and_preserves_home(universe):
    game, users, clock = universe
    secondary = secondary_colony(universe, 0)
    with game.transaction() as db:
        target = game.read_colony(db, secondary)
        target_name = target["colony_name"]
        target["jobs"].append(
            {"id": identity(), "kind": "build", "key": "wood", "due": clock[0] + 60}
        )
        game.save(db, target)
        home = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=1 AND is_home=TRUE",
            (users[0],),
        ).fetchone()["colony_id"]
        sender = game.read(db, users[1])
        sender["jobs"].append(
            {
                "id": identity(),
                "kind": "colony_supply",
                "key": secondary,
                "due": clock[0] + 60,
                "army": {"ranger": 1},
                "loot": [10, 0, 0],
            }
        )
        game.save(db, sender)

    payload = {"colony_id": secondary, "confirmation": target_name}
    with pytest.raises(RuleError, match="exakten Kolonienamen"):
        command(universe, 0, "colony_abandon", {**payload, "confirmation": "wrong"})
    with pytest.raises(RuleError, match="Heimatkolonie"):
        command(universe, 0, "colony_abandon", {"colony_id": home, "confirmation": "Alpha"})
    with pytest.raises(RuleError, match="gehört nicht"):
        command(universe, 1, "colony_abandon", payload)
    with pytest.raises(RuleError, match="Schließe zuerst alle"):
        command(universe, 0, "colony_abandon", payload)

    with game.transaction() as db:
        target = game.read_colony(db, secondary)
        target["jobs"] = []
        game.save(db, target)
        sender = game.read_colony(db, users[1])
        sender["jobs"] = []
        game.save(db, sender)
        sender_row = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=1 AND is_home=TRUE",
            (users[1],),
        ).fetchone()
        sender = game.read_colony(db, sender_row["colony_id"])
        sender["jobs"].append(
            {
                "id": identity(),
                "kind": "colony_supply",
                "key": secondary,
                "due": clock[0] + 60,
                "army": {"ranger": 1},
                "loot": [10, 0, 0],
            }
        )
        game.save(db, sender)
    with pytest.raises(RuleError, match="eingehenden Versorgungen"):
        command(universe, 0, "colony_abandon", payload)

    with game.transaction() as db:
        sender = game.read_colony(db, sender_row["colony_id"])
        sender["jobs"] = []
        game.save(db, sender)
    command(universe, 0, "colony_select", {"key": secondary})
    listed = command(
        universe, 0, "market_create", {"give": 0, "amount": 10, "want": 1, "price": 10}
    )
    offer_id = next(offer["id"] for offer in listed["offers"] if offer["owner"] == users[0])
    command(universe, 0, "colony_select", {"key": home})
    with pytest.raises(RuleError, match="offenen Handelsangebote"):
        command(universe, 0, "colony_abandon", payload)
    command(universe, 0, "market_cancel", {"key": offer_id})
    with game.transaction() as db:
        target = game.read_colony(db, secondary)
        target["item_inventory"] = {"repair_kit": 1}
        game.save(db, target)
    with pytest.raises(RuleError, match="Gegenstände"):
        command(universe, 0, "colony_abandon", payload)
    with game.transaction() as db:
        target = game.read_colony(db, secondary)
        target["item_inventory"] = {}
        target["item_reserve"] = {"repair_kit": 1}
        game.save(db, target)
    with pytest.raises(RuleError, match="Gegenstände"):
        command(universe, 0, "colony_abandon", payload)
    with game.transaction() as db:
        target = game.read_colony(db, secondary)
        target["item_reserve"] = {}
        game.save(db, target)
    command(universe, 0, "colony_select", {"key": secondary})

    token = identity()
    abandoned = command(universe, 0, "colony_abandon", payload, token)
    assert all(colony["colony_id"] != secondary for colony in abandoned["colonies"])
    assert (
        next(colony for colony in abandoned["colonies"] if colony["is_home"])["colony_id"] == home
    )
    replay = command(universe, 0, "colony_abandon", payload, token)
    assert next(colony for colony in replay["colonies"] if colony["is_home"])["colony_id"] == home
    with game.transaction() as db:
        assert (
            db.execute("SELECT 1 FROM colonies WHERE colony_id=?", (secondary,)).fetchone() is None
        )
        profile = db.execute(
            "SELECT active_colony_id FROM profiles WHERE user_id=?", (users[0],)
        ).fetchone()
        assert profile["active_colony_id"] == home
        offer = db.execute("SELECT status,colony_id FROM offers WHERE id=?", (offer_id,)).fetchone()
        assert offer["status"] == "cancelled" and offer["colony_id"] is None
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='colony_abandon' AND target=?",
            (users[0], secondary),
        ).fetchone()
        assert json.loads(audit["details"])["name"] == target_name
        ledger = db.execute(
            "SELECT before_state,after_state FROM ledger WHERE user_id=? AND action='colony_abandon'",
            (users[0],),
        ).fetchone()
        assert json.loads(ledger["before_state"])["colony_id"] == secondary
        assert json.loads(ledger["after_state"]) == {"removed": True, "colony_id": secondary}
        ruins = db.execute("SELECT x,y,expires FROM terra_ruins WHERE world_id=1").fetchall()
        assert len(ruins) == 1
        assert (ruins[0]["x"], ruins[0]["y"]) == (target["x"], target["y"])
        assert ruins[0]["expires"] == clock[0] + 86400
        with pytest.raises(RuleError, match="Ruine"):
            game.require_terra_settlement(db, 1, target["x"], target["y"])
        game.require_terra_settlement(db, 2, target["x"], target["y"])
    clock[0] += 86400
    with game.transaction() as db:
        game.require_terra_settlement(db, 1, target["x"], target["y"])
        assert not game.active_terra_ruins(db, 1)


def test_concurrent_prerequisite_build_does_not_unlock_research(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [20000, 20000, 20000]
        game.save(db, colony)

    start_together = Barrier(2)

    def issue(action):
        start_together.wait(timeout=10)
        try:
            return command(universe, 0, action, {"key": "lab" if action == "build" else "tactics"})
        except RuleError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        build, research = list(pool.map(issue, ("build", "research")))

    assert build is not None
    assert research is None
    current = state(universe, 0)
    assert current["buildings"]["lab"] == 0
    assert [job["kind"] for job in current["jobs"]] == ["build"]
    assert current["jobs"][0]["key"] == "lab"


def test_research_levels_and_bonuses_are_scoped_to_each_colony(universe):
    game, users, _clock = universe
    destination = secondary_colony(universe, 0)
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["lab"] = 1
        home["buildings"]["storage"] = 10
        home["buildings"]["wood"] = 1
        home["tech"]["engineering"] = 2
        home["tech"]["logistics"] = 1
        home["tech"]["tactics"] = 3
        home["resources"] = [20000, 20000, 20000]
        home["units"]["ranger"] = 20
        game.save(db, home)
        outpost = game.read_colony(db, destination)
        outpost["buildings"]["lab"] = 1
        outpost["buildings"]["storage"] = 10
        outpost["buildings"]["wood"] = 1
        outpost["resources"] = [20000, 20000, 20000]
        outpost["units"]["ranger"] = 20
        game.save(db, outpost)

    home_view = state(universe, 0)
    assert home_view["tech"] == {"tactics": 3, "logistics": 1, "engineering": 2}
    assert home_view["production_details"][0]["bonus_percent"] == 30
    assert home_view["production_details"][0]["base_per_second"] == 4
    home_rate = (
        home_view["production_details"][0]["base_per_second"]
        * (100 + home_view["production_details"][0]["bonus_percent"])
        * home_view["production_details"][0]["terrain_percent"]
        // 100
    )
    assert home_view["production_details"][0]["per_second_hundredths"] == home_rate

    command(universe, 0, "colony_select", {"key": destination})
    outpost_view = state(universe, 0)
    assert outpost_view["tech"] == {"tactics": 0, "logistics": 0, "engineering": 0}
    assert outpost_view["production_details"][0]["bonus_percent"] == 0
    assert outpost_view["production_details"][0]["base_per_second"] == 4
    outpost_rate = (
        outpost_view["production_details"][0]["base_per_second"]
        * (100 + outpost_view["production_details"][0]["bonus_percent"])
        * outpost_view["production_details"][0]["terrain_percent"]
        // 100
    )
    assert outpost_view["production_details"][0]["per_second_hundredths"] == outpost_rate

    # The 50-unit crossing verifies that the selected colony's local research
    # controls its dispatch capacity.
    with pytest.raises(RuleError, match="Transportkapazität"):
        command(
            universe,
            0,
            "transport",
            {"key": users[1], "army": {"ranger": 2}, "resources": [81, 0, 0]},
        )
    command(universe, 0, "colony_select", {"key": users[0]})
    home_view = state(universe, 0)
    assert home_view["tech"]["logistics"] == 1
    with pytest.raises(RuleError, match="Transportkapazität"):
        command(
            universe,
            0,
            "transport",
            {"key": users[1], "army": {"ranger": 2}, "resources": [101, 0, 0]},
        )
    accepted = command(
        universe,
        0,
        "transport",
        {"key": users[1], "army": {"ranger": 2}, "resources": [100, 0, 0]},
    )
    assert next(job for job in accepted["jobs"] if job["kind"] == "transport")["loot"] == [
        100,
        0,
        0,
    ]


def test_colony_supply_rejects_other_world_and_insufficient_capacity(universe):
    game, users, _ = universe
    same_world_destination = secondary_colony(universe, 0)
    with game.transaction() as db:
        other_world = game.create_world(db, "Second World", 72026, 8)
        game.join_world(db, users[0], "Alpha", other_world)
        other_world_destination = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (users[0], other_world),
        ).fetchone()["colony_id"]
        db.execute(
            "UPDATE profiles SET active_colony_id=?,active_world_id=1 WHERE user_id=?",
            (users[0], users[0]),
        )
        source = game.read(db, users[0])
        source["resources"] = [100, 100, 100]
        source["units"]["ranger"] = 3
        game.save(db, source)
    with pytest.raises(RuleError, match="derselben Welt"):
        command(
            universe,
            0,
            "colony_supply",
            {
                "key": other_world_destination,
                "army": {"ranger": 1},
                "resources": [1, 0, 0],
            },
        )
    with pytest.raises(RuleError, match="Transportkapazität"):
        command(
            universe,
            0,
            "colony_supply",
            {
                "key": same_world_destination,
                "army": {"ranger": 1},
                "resources": [41, 0, 0],
            },
        )
    assert state(universe, 0)["resources"] == [100, 100, 100]


def test_colony_supply_concurrent_idempotent_retry_sends_only_once(universe):
    game, users, _ = universe
    destination = secondary_colony(universe, 0)
    with game.transaction() as db:
        source = game.read(db, users[0])
        source["resources"] = [1000, 1000, 1000]
        source["units"]["ranger"] = 10
        game.save(db, source)
    token = identity()
    payload = {"key": destination, "army": {"ranger": 2}, "resources": [30, 25, 25]}

    def dispatch(_attempt):
        return command(universe, 0, "colony_supply", payload, token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(dispatch, (0, 1)))
    assert all(
        sum(job["kind"] == "colony_supply" for job in result["jobs"]) == 1 for result in results
    )
    assert all(result["resources"] == [970, 975, 975] for result in results)
    with game.transaction() as db:
        jobs = [
            job
            for row in db.execute("SELECT state FROM colonies WHERE colony_id=?", (users[0],))
            for job in json.loads(row[0])["jobs"]
            if job["kind"] == "colony_supply"
        ]
        assert len(jobs) == 1


def test_world_outpost_normalization_backfills_existing_world_without_data_loss(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        before_users = db.execute("SELECT count(*) FROM users").fetchone()[0]
        before_colonies = db.execute("SELECT count(*) FROM colonies").fetchone()[0]
        legacy_outposts = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        legacy_outposts[0]["owner"] = users[0]
        legacy_outposts[0]["stock"] = [101, 202, 303]
        legacy_state = json.dumps(legacy_outposts)
        db.execute("UPDATE world SET state=? WHERE id=1", (legacy_state,))
        db.execute("DELETE FROM schema_versions WHERE version=9")
        db.execute("DROP TABLE world_outposts")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT state FROM world WHERE id=1").fetchone()[0] == legacy_state
        assert upgraded.world_outposts(db, 1) == legacy_outposts
        assert (
            db.execute("SELECT count(*) FROM world_outposts WHERE world_id=1").fetchone()[0] == 104
        )
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == before_users
        assert db.execute("SELECT count(*) FROM colonies").fetchone()[0] == before_colonies


def test_neutral_outpost_stock_replenishment_is_world_scoped_and_bounded(universe):
    game, users, clock = universe
    with game.transaction() as db:
        game.create_world(db, "Resupply Cross Adapter", 910071, 8, True)
        genesis = game.world_outposts(db, 1)
        genesis[0]["owner"] = users[0]
        genesis[0]["stock"] = [0, 0, 0]
        game.save_world_outposts(db, 1, genesis)
        second = game.world_outposts(db, 2)
        tier_one = second[1]
        tier_one["stock"] = [0, 399, 400]
        citadel = second[0]
        citadel["stock"] = [3199, 3200, 4000]
        game.save_world_outposts(db, 2, second)
        for world_id in (1, 2):
            db.execute(
                "UPDATE world_settings SET settings=? WHERE world_id=?",
                (json.dumps({"outpost_stock_checked_at": clock[0] - 60}), world_id),
            )

    cycle(game)
    with game.transaction() as db:
        owned = next(t for t in game.world_outposts(db, 1) if t["id"] == genesis[0]["id"])
        neutral = next(t for t in game.world_outposts(db, 2) if t["id"] == tier_one["id"])
        updated_citadel = next(t for t in game.world_outposts(db, 2) if t["id"] == citadel["id"])
        assert owned["stock"] == [0, 0, 0]
        assert neutral["stock"] == [1, 400, 400]
        assert updated_citadel["stock"] == [3200, 3200, 4000]
    cycle(game)
    with game.transaction() as db:
        unchanged = next(t for t in game.world_outposts(db, 2) if t["id"] == tier_one["id"])
        assert unchanged["stock"] == [1, 400, 400]


def test_combat5_fortification_worker_regeneration_is_adapter_independent(universe):
    game, _, clock = universe
    now = clock[0]
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=?,settings=? WHERE world_id=1",
            (
                "FUR-3-TERRA-COMBAT-5",
                json.dumps({"outpost_stock_checked_at": now}),
            ),
        )
        posts = game.world_outposts(db, 1)
        target = posts[1]
        target["tier"] = 1
        target["fortification_integrity"] = 3
        target["fortification_checked_at"] = now - 60
        game.save_world_outposts(db, 1, posts)

        game.advance(db, now)

        healed = next(post for post in game.world_outposts(db, 1) if post["id"] == target["id"])
        assert healed["fortification_integrity"] == 5
        assert healed["fortification_checked_at"] == now


def test_region_control_bonus_is_scoped_to_the_active_world(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        world_id = game.create_world(db, "Territory Adapter", 337711, 24, True)
        outposts = game.world_outposts(db, world_id)
        groups = {}
        for post in outposts:
            groups.setdefault((post["x"] // 16, post["y"] // 16), []).append(post)
        region_posts = max(groups.values(), key=len)
        threshold = max(2, len(region_posts) // 2 + 1)
        for post in region_posts[:threshold]:
            post["owner"] = users[0]
        game.save_world_outposts(db, world_id, outposts)

        assert game.regional_production_bonus(db, users[0], 1) == 0
        assert game.regional_production_bonus(db, users[0], world_id) == 2
        game.join_world(db, users[0], "Alpha", world_id)
        region_x, region_y = region_posts[0]["x"] // 16, region_posts[0]["y"] // 16
        for y in range(region_y * 16, region_y * 16 + 16):
            for x in range(region_x * 16, region_x * 16 + 16):
                db.execute(
                    "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO NOTHING",
                    (users[0], world_id, x, y, 1),
                )

        state = game.view(db, users[0])

        assert state["active_world"]["id"] == world_id
        assert state["regional_production_bonus"] == 2
        assert len(state["regions"]) == 16
        assert sum(region["owner_id"] == users[0] for region in state["regions"]) == 1


def test_all_region_bonus_is_capped_and_separate_from_personal_ranking(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        ranking_before = game.ranking(db)
        posts = game.world_outposts(db, 1)
        groups = {}
        for post in posts:
            groups.setdefault((post["x"] // 16, post["y"] // 16), []).append(post)
        sparse_region = min(groups, key=lambda region: len(groups[region]))
        donor_region = max(groups, key=lambda region: len(groups[region]))
        assert len(groups[sparse_region]) == 1
        assert len(groups[donor_region]) >= 3

        occupied = {(post["x"], post["y"]) for post in posts}
        occupied.update(
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=1")
        )
        target = next(
            (x, y)
            for y in range(sparse_region[1] * 16, (sparse_region[1] + 1) * 16)
            for x in range(sparse_region[0] * 16, (sparse_region[0] + 1) * 16)
            if (x, y) not in occupied
            and db.execute(
                "SELECT 1 FROM world_terrain WHERE world_id=1 AND x=? AND y=? AND terrain<>'water'",
                (x, y),
            ).fetchone()
        )
        posts.remove(groups[donor_region][0])
        moved_post = groups[donor_region][0]
        moved_post.update(x=target[0], y=target[1])
        posts.append(moved_post)
        for post in posts:
            post["owner"] = users[0]
        game.save_world_outposts(db, 1, posts)

        assert game.regional_production_bonus(db, users[0], 1) == 32
        regions = game.world_regions(db, 1)
        assert len([region for region in regions if region["owner_id"] == users[0]]) == 16
        assert game.ranking(db) == ranking_before


def test_alliance_region_boundaries_follow_member_owned_outposts(universe):
    game, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "BOUND", "name": "Boundary Test"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    with game.transaction() as db:
        invite = db.execute("SELECT id FROM invites WHERE user_id=?", (users[1],)).fetchone()[0]
    command(universe, 1, "alliance_accept", {"key": invite})
    with game.transaction() as db:
        posts = [
            post
            for post in game.world_outposts(db, 1)
            if not (int(post["x"]) < 16 and int(post["y"]) < 16)
        ]
        posts = posts[:3]
        for index, owner in enumerate(users):
            posts[index].update(x=index, y=0, owner=owner)
        game.save_world_outposts(db, 1, posts)
        region = next(item for item in game.world_regions(db, 1) if item["id"] == "A1")
        assert region["owner_id"] is None
        assert region["alliance_owner_id"] is not None
        assert region["alliance_leader_tied"] is False


def test_world_context_migration_allows_a_second_world_without_data_loss(universe):
    game, users, _clock = universe
    with game.connect() as db:
        if not db.postgres:
            db.execute("PRAGMA foreign_keys=OFF")
        db.execute("BEGIN IMMEDIATE")
        before_world = db.execute("SELECT state FROM world WHERE id=1").fetchone()[0]
        before_colonies = db.execute("SELECT count(*) FROM colonies").fetchone()[0]
        if db.postgres:
            db.execute("ALTER TABLE world DROP CONSTRAINT world_id_positive")
            db.execute("ALTER TABLE world ADD CONSTRAINT world_id_check CHECK(id=1)")
            # Later gameplay tables reference world_settings. Remove only that
            # dependency while replaying migration 10; restore it afterward.
            db.execute(
                "ALTER TABLE commander_heroes DROP CONSTRAINT commander_heroes_world_id_fkey"
            )
        else:
            db.execute(
                "CREATE TABLE world_new(id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL)"
            )
            db.execute("INSERT INTO world_new SELECT * FROM world")
            db.execute("DROP TABLE world")
            db.execute("ALTER TABLE world_new RENAME TO world")
        db.execute("ALTER TABLE profiles DROP COLUMN active_world_id")
        db.execute("DROP TABLE world_settings")
        db.execute("DELETE FROM schema_versions WHERE version=10")
        db.execute("COMMIT")
        if not db.postgres:
            db.execute("PRAGMA foreign_keys=ON")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        if db.postgres:
            db.execute(
                "ALTER TABLE commander_heroes ADD CONSTRAINT commander_heroes_world_id_fkey "
                "FOREIGN KEY(world_id) REFERENCES world_settings(world_id) ON DELETE CASCADE"
            )
        assert db.execute("SELECT state FROM world WHERE id=1").fetchone()[0] == before_world
        assert db.execute("SELECT count(*) FROM colonies").fetchone()[0] == before_colonies
        assert (
            db.execute(
                "SELECT active_world_id FROM profiles WHERE user_id=?", (users[0],)
            ).fetchone()[0]
            == 1
        )
        db.execute("INSERT INTO world(id,state) VALUES (2,'[]')")
        db.execute(
            "INSERT INTO world_settings(world_id,name,seed,outpost_count,created,settings) "
            "VALUES (2,'Second Dawn',7001,0,1,'{}')"
        )
        if not db.postgres:
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_seeded_economic_sequences_keep_resources_and_units_valid(universe):
    game, users, clock = universe
    players = users[:2]
    with game.transaction() as db:
        for user in players:
            colony = game.read(db, user)
            colony["resources"] = [500_000, 500_000, 500_000]
            colony["buildings"]["lab"] = 1
            colony["buildings"]["barracks"] = 3
            colony["buildings"]["storage"] = 10
            game.save(db, colony)

    rng = random.Random(0xF0E)
    operations = []
    for _index in range(80):
        action = rng.choice(("build", "research", "train", "trade", "cancel_job"))
        if action == "build":
            payload = {
                "key": rng.choice(
                    ("hq", "wood", "stone", "ore", "storage", "barracks", "lab", "wall")
                )
            }
        elif action == "research":
            payload = {"key": rng.choice(("tactics", "logistics", "engineering"))}
        elif action == "train":
            payload = {
                "key": rng.choice(("ranger", "sentinel", "mech")),
                "count": rng.randint(1, 100),
            }
        elif action == "trade":
            source, destination = rng.sample(range(3), 2)
            payload = {"source": source, "dest": destination, "amount": rng.randint(1, 50_000)}
        else:
            payload = {}
        operations.append((action, payload))

    for player_index, user in enumerate(players):
        for index, (action, payload) in enumerate(operations):
            token = f"property-{player_index}-{index}"
            request = {"action": action, "payload": payload}
            with game.transaction() as db:
                colony = game.read(db, user)
            if action == "cancel_job" and colony["jobs"]:
                request["payload"] = {"key": rng.choice(colony["jobs"])["id"]}
            try:
                with game.transaction() as db:
                    game.command(db, user, request["action"], request["payload"], token)
                with game.transaction() as db:
                    game.command(db, user, request["action"], request["payload"], token)
            except RuleError:
                pass
            with game.transaction() as db:
                current = game.read(db, user)
            assert all(type(value) is int and value >= 0 for value in current["resources"])
            assert all(type(value) is int and value >= 0 for value in current["reserve"])
            assert all(type(value) is int and value >= 0 for value in current["units"].values())
            assert len(current["jobs"]) <= 30

    clock[0] += 1_000_000
    with game.transaction() as db:
        game.advance(db, clock[0])
        for user in players:
            final = game.read(db, user)
            assert all(type(value) is int and value >= 0 for value in final["resources"])
            assert all(type(value) is int and value >= 0 for value in final["units"].values())


def test_npc_frontier_catchup_is_world_scoped_and_adapter_independent(universe):
    game, _users, clock = universe
    with game.transaction() as db:
        world_id = game.create_world(db, "NPC Adapter", 991_723, 24, True)
        genesis_before = game.world_outposts(db, 1)
        for post in genesis_before:
            post["owner"] = "npc-test-isolation-marker"
        game.save_world_outposts(db, 1, genesis_before)
        genesis_before = game.world_outposts(db, 1)
        outposts = game.world_outposts(db, world_id)
        target = outposts[1]
        target["tier"] = 2
        target["stock"] = [0, 0, 0]
        owned = outposts[2]
        owned["owner"] = "npc-test-owned-marker"
        owned["stock"] = [0, 0, 0]
        game.save_world_outposts(db, world_id, outposts)
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=?",
            (json.dumps({"npc_frontier_checked_at": clock[0] - 300}), world_id),
        )
        game.update_npc_frontiers(db, clock[0])
        refreshed = {post["id"]: post for post in game.world_outposts(db, world_id)}
        assert refreshed[target["id"]]["npc_pressure"] == 2
        assert refreshed[target["id"]]["stock"] == [0, 0, 0]
        assert "npc_pressure" not in refreshed[owned["id"]]
        game.update_npc_frontiers(db, clock[0] + 148 * 300)
        caught_up = {post["id"]: post for post in game.world_outposts(db, world_id)}
        assert caught_up[target["id"]]["npc_pressure"] == 98
        assert caught_up[target["id"]]["stock"] == [4, 4, 4]
        assert game.world_outposts(db, 1) == genesis_before


def test_seeded_world_generation_is_repeatable_with_reachable_start_targets(universe):
    game, users, _clock = universe
    seed = 863_119
    with game.transaction() as db:
        first_world = game.create_world(db, "Seed Reference", seed, 24, True)
        second_world = game.create_world(db, "Seed Repeat", seed, 24, True)
        first_terrain = [
            (int(row["x"]), int(row["y"]), str(row["terrain"]))
            for row in db.execute(
                "SELECT x,y,terrain FROM world_terrain WHERE world_id=? ORDER BY y,x",
                (first_world,),
            )
        ]
        second_terrain = [
            (int(row["x"]), int(row["y"]), str(row["terrain"]))
            for row in db.execute(
                "SELECT x,y,terrain FROM world_terrain WHERE world_id=? ORDER BY y,x",
                (second_world,),
            )
        ]
        first_posts = [
            (post["x"], post["y"], post["tier"], tuple(post["stock"]))
            for post in game.world_outposts(db, first_world)
        ]
        second_posts = [
            (post["x"], post["y"], post["tier"], tuple(post["stock"]))
            for post in game.world_outposts(db, second_world)
        ]
        assert len(first_terrain) == 4096
        assert first_terrain == second_terrain
        assert first_posts == second_posts
        assert all(
            terrain != "water"
            for x, y, _, _ in first_posts
            for terrain in [
                db.execute(
                    "SELECT terrain FROM world_terrain WHERE world_id=? AND x=? AND y=?",
                    (first_world, x, y),
                ).fetchone()["terrain"]
            ]
        )
        game.join_world(db, users[0], "Alpha", first_world)
        home = game.read(db, users[0])
        travel = travel_times(db, (home["x"], home["y"]), first_world)
        reachable_posts = [
            post
            for post in game.world_outposts(db, first_world)
            if post["owner"] is None and travel.get((post["x"], post["y"]), 10**9) <= 3600
        ]
        assert home["terrain"] != "water"
        assert reachable_posts


def test_admin_world_creation_and_player_join_keep_world_state_isolated(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        genesis_outposts = game.world_outposts(db, 1)
        genesis_terrain = db.execute(
            "SELECT x,y,terrain FROM world_terrain WHERE world_id=1 ORDER BY y,x"
        ).fetchall()
    command(universe, 0, "message", {"channel": "world", "body": "Nur Genesis"})
    genesis_offer = command(
        universe,
        0,
        "market_create",
        {"give": 0, "amount": 10, "want": 1, "price": 10},
    )["offers"][0]["id"]

    created = command(
        universe,
        0,
        "world_create",
        {
            "name": "Second Dawn",
            "seed": 72026,
            "outposts": 24,
            "joinable": True,
            "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-5",
        },
    )
    assert [(world["id"], world["has_colony"]) for world in created["worlds"]] == [
        (1, True),
        (2, False),
    ]
    assert (
        next(world for world in created["worlds"] if world["id"] == 2)["terra_combat_ruleset"]
        == "FUR-3-TERRA-COMBAT-5"
    )
    closed = command(universe, 0, "world_update", {"world_id": 2, "joinable": False})
    assert next(world for world in closed["worlds"] if world["id"] == 2)["joinable"] is False
    with pytest.raises(RuleError, match="nimmt derzeit keine neuen Spieler auf"):
        command(universe, 1, "world_join", {"world_id": 2})
    renamed = command(
        universe,
        0,
        "world_update",
        {"world_id": 2, "name": "Second Dawn II", "joinable": True},
    )
    assert (
        next(world for world in renamed["worlds"] if world["id"] == 2)["name"] == "Second Dawn II"
    )
    combat_enabled = command(
        universe,
        0,
        "world_update",
        {
            "world_id": 2,
            "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-1",
            "terra_retreat_threshold_percent": 37,
        },
    )
    assert (
        next(world for world in combat_enabled["worlds"] if world["id"] == 2)[
            "terra_combat_ruleset"
        ]
        == "FUR-3-TERRA-COMBAT-1"
    )
    assert (
        next(world for world in combat_enabled["worlds"] if world["id"] == 2)[
            "terra_retreat_threshold_percent"
        ]
        == 37
    )
    with pytest.raises(RuleError, match="zwischen 1 und 100"):
        command(
            universe,
            0,
            "world_update",
            {"world_id": 2, "terra_retreat_threshold_percent": 101},
        )
    second_world = command(universe, 1, "world_join", {"world_id": 2})
    assert {
        key: second_world["active_world"][key] for key in ("id", "name", "seed", "outpost_count")
    } == {"id": 2, "name": "Second Dawn II", "seed": 72026, "outpost_count": 24}
    assert second_world["active_world"]["mode"] == "permanent"
    assert second_world["active_world"]["terra_combat_ruleset"] == "FUR-3-TERRA-COMBAT-1"
    assert second_world["active_world"]["terra_retreat_threshold_percent"] == 37
    assert second_world["active_world"]["rules_version"] == "FUR-2"
    assert second_world["active_world"]["rules_digest"]
    assert second_world["world_id"] == 2
    assert len(second_world["colonies"]) == 1
    assert {colony["world_id"] for colony in second_world["colonies"]} == {2}
    assert len(second_world["empire_colonies"]) == 2
    assert len(second_world["world"]) <= 24
    assert len(second_world["terrain_map"]) < 4096
    assert second_world["resources"] == [1200, 1000, 800]
    assert all(
        second_world["terrain_map"][f"{post['x']}:{post['y']}"] != "water"
        for post in second_world["world"]
    )
    assert not any(message["body"] == "Nur Genesis" for message in second_world["messages"])
    assert all(offer["id"] != genesis_offer for offer in second_world["offers"])
    with game.transaction() as db:
        assert game.world_outposts(db, 1) == genesis_outposts
        assert (
            db.execute(
                "SELECT x,y,terrain FROM world_terrain WHERE world_id=1 ORDER BY y,x"
            ).fetchall()
            == genesis_terrain
        )
        colony = db.execute(
            "SELECT colony_id,world_id,is_home FROM colonies WHERE user_id=? AND world_id=2",
            (users[1],),
        ).fetchone()
        assert colony["world_id"] == 2 and bool(colony["is_home"])
        assert colony["colony_id"] != users[1]

    owner_second_world = command(universe, 0, "world_join", {"world_id": 2})
    assert owner_second_world["world_id"] == 2
    assert owner_second_world["colony_count"] == 1
    assert len(owner_second_world["colonies"]) == 1
    assert len(owner_second_world["empire_colonies"]) == 2
    command(universe, 0, "message", {"channel": "world", "body": "Nur Second Dawn"})
    assert any(message["body"] == "Nur Second Dawn" for message in state(universe, 1)["messages"])
    second_offer = command(
        universe,
        0,
        "market_create",
        {"give": 0, "amount": 10, "want": 1, "price": 10},
    )["offers"][0]["id"]
    assert any(offer["id"] == second_offer for offer in state(universe, 1)["offers"])
    with pytest.raises(RuleError, match="Angebot nicht mehr verfügbar"):
        command(universe, 1, "market_accept", {"key": genesis_offer})
    command(universe, 1, "market_accept", {"key": second_offer})
    assert state(universe, 0)["resources"] == [1190, 1010, 800]
    with game.transaction() as db:
        assert game.read_colony(db, users[0])["resources"] == [1190, 1000, 800]

    command(universe, 0, "world_select", {"world_id": 1})
    with game.transaction() as db:
        target_home_row = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=2 AND is_home=TRUE",
            (users[0],),
        ).fetchone()
        target_home = game.read_colony(db, target_home_row["colony_id"])
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(observer_id,world_id,x,y) DO UPDATE SET observed_at=excluded.observed_at",
            (users[1], 2, target_home["x"], target_home["y"], clock[0]),
        )
    attacking = command(
        universe,
        1,
        "attack",
        {"key": users[0], "army": {"ranger": 1}},
    )
    assert any(job["kind"] == "attack" for job in attacking["jobs"])

    switched = command(universe, 1, "world_select", {"world_id": 1})
    assert switched["world_id"] == 1
    with pytest.raises(RuleError, match="keine Heimatkolonie"):
        command(universe, 2, "world_select", {"world_id": 2})


def test_world_scoped_data_migration_backfills_legacy_trade_holding(universe):
    game, users, clock = universe
    with game.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        for index in range(1, 5):
            names = (
                "messages_world_feed",
                "offers_world_open",
                "player_intel_world",
                "map_bookmarks_world_order",
            )
            db.execute(f"DROP INDEX {names[index - 1]}")
        for table in ("messages", "offers", "player_intel", "map_bookmarks"):
            db.execute(f"ALTER TABLE {table} DROP COLUMN world_id")
        db.execute("ALTER TABLE offers DROP COLUMN colony_id")
        db.execute("DELETE FROM schema_versions WHERE version=11")
        offer_id = identity()
        db.execute(
            "INSERT INTO offers(id,owner,give_resource,give_amount,want_resource,want_amount,"
            "created,expires,status,buyer) VALUES (?,?,0,100,1,50,?,?,'open',NULL)",
            (offer_id, users[0], clock[0], clock[0] + 86400),
        )
        db.execute("COMMIT")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        offer = db.execute("SELECT * FROM offers WHERE id=?", (offer_id,)).fetchone()
        assert offer["world_id"] == 1
        assert offer["colony_id"] == users[0]
        assert offer["status"] == "open"
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 3


def alliance_with_two_members(universe):
    _, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "SUPPLY", "name": "Supply Circle"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})
    return users


def test_alliance_supply_validates_membership_capacity_and_delivers_to_home(universe):
    game, users, clock = universe
    alliance_with_two_members(universe)
    with game.transaction() as db:
        target_state = game.read(db, users[1])
        target_state["buildings"]["storage"] = 0
        target_state["resources"] = [1990, 1980, 1970]
        game.save(db, target_state)
    source = state(universe, 0)
    assert state(universe, 0)["alliance_supply_targets"][0]["colony_id"] == users[1]
    with pytest.raises(RuleError, match="Transportkapazität"):
        command(
            universe,
            0,
            "alliance_send_supply",
            {"key": users[1], "army": {"ranger": 1}, "resources": [60, 0, 0]},
        )
    with pytest.raises(RuleError, match="verbündetes Mitglied"):
        command(
            universe,
            0,
            "alliance_send_supply",
            {"key": users[2], "army": {"ranger": 2}, "resources": [70, 50, 30]},
        )

    sent = command(
        universe,
        0,
        "alliance_send_supply",
        {"key": users[1], "army": {"ranger": 4}, "resources": [70, 50, 30]},
    )
    shipment = next(job for job in sent["jobs"] if job["kind"] == "alliance_supply")
    assert shipment["due"] > clock[0]
    assert sent["resources"] == [1130, 950, 770]
    assert sent["units"]["ranger"] == source["units"]["ranger"] - 4

    clock[0] = shipment["due"] + 1
    recipient = state(universe, 1)
    assert recipient["resources"] == [2000, 2000, 2000]
    assert all(amount > 0 for amount in recipient["reserve"])
    receipt = next(
        report
        for report in recipient["reports"]
        if report["title"] == "Allianzversorgung eingetroffen"
    )
    assert all(amount in receipt["body"] for amount in ("70 Holz", "50 Stein", "30 Erz"))
    arrived = state(universe, 0)
    assert any(report["title"] == "Allianzversorgung zugestellt" for report in arrived["reports"])
    assert not any(job["kind"] == "alliance_supply" for job in arrived["jobs"])
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='alliance_supply_arrival'"
            ).fetchone()[0]
            == 1
        )


def test_concurrent_alliance_supply_retry_escrows_once(universe):
    game, users, _ = universe
    alliance_with_two_members(universe)
    token = identity()
    payload = {"key": users[1], "army": {"ranger": 2}, "resources": [25, 20, 15]}
    before = state(universe, 0)

    def dispatch(_attempt):
        return command(universe, 0, "alliance_send_supply", payload, token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(dispatch, (0, 1)))
    expected_resources = [
        old - sent for old, sent in zip(before["resources"], payload["resources"])
    ]
    assert all(result["resources"] == expected_resources for result in results)
    assert all(
        sum(job["kind"] == "alliance_supply" for job in result["jobs"]) == 1 for result in results
    )
    with game.transaction() as db:
        source = json.loads(
            db.execute("SELECT state FROM colonies WHERE colony_id=?", (users[0],)).fetchone()[0]
        )
        assert sum(job["kind"] == "alliance_supply" for job in source["jobs"]) == 1
        assert source["resources"] == expected_resources


def test_alliance_supply_targets_are_world_scoped_and_keyset_paginated(universe):
    game, users, _ = universe
    alliance_with_two_members(universe)
    command(universe, 0, "alliance_invite", {"name": "Charlie"})
    invitation = state(universe, 2)["invites"][0]["id"]
    command(universe, 2, "alliance_accept", {"key": invitation})
    source = state(universe, 0)
    world_id = int(source["active_world"]["id"])
    alliance_id = str(source["membership"]["alliance_id"])
    with game.transaction() as db:
        first, has_more = game.systems.alliance_supply_target_page(
            db, users[0], alliance_id, world_id, page_size=1
        )
        assert len(first) == 1
        assert has_more is True
        assert first[0]["world_id"] == world_id
        second, has_more = game.systems.alliance_supply_target_page(
            db,
            users[0],
            alliance_id,
            world_id,
            str(first[0]["colony_id"]),
            page_size=1,
        )
        assert len(second) == 1
        assert has_more is False
        assert first[0]["colony_id"] != second[0]["colony_id"]
        with pytest.raises(RuleError, match="nicht gefunden"):
            game.systems.alliance_supply_target_page(
                db,
                users[0],
                alliance_id,
                world_id + 1,
                str(first[0]["colony_id"]),
                page_size=1,
            )
        with pytest.raises(RuleError, match="gehörst nicht mehr"):
            game.systems.alliance_supply_target_page(
                db, users[0], alliance_id + "-other", world_id, page_size=1
            )


def test_alliance_supply_cancellation_refunds_once_and_membership_change_refunds_at_arrival(
    universe,
):
    game, users, clock = universe
    alliance_with_two_members(universe)
    source_before = state(universe, 0)
    token = identity()
    payload = {"key": users[1], "army": {"ranger": 4}, "resources": [70, 50, 30]}
    sent = command(universe, 0, "alliance_send_supply", payload, token)
    shipment = next(job for job in sent["jobs"] if job["kind"] == "alliance_supply")
    cancel_token = identity()
    cancel = command(universe, 0, "alliance_supply_cancel", {"key": shipment["id"]}, cancel_token)
    replay = command(universe, 0, "alliance_supply_cancel", {"key": shipment["id"]}, cancel_token)
    assert cancel["resources"] == [1200, 1000, 800]
    assert cancel["units"] == source_before["units"]
    assert replay["resources"] == cancel["resources"]
    with pytest.raises(RuleError, match="nicht mehr abbrechbar"):
        command(universe, 0, "alliance_supply_cancel", {"key": shipment["id"]})

    sent_again = command(universe, 0, "alliance_send_supply", payload, token=identity())
    shipment_again = next(job for job in sent_again["jobs"] if job["kind"] == "alliance_supply")
    command(universe, 1, "alliance_leave")
    clock[0] = shipment_again["due"] + 1
    source = state(universe, 0)
    assert all(
        actual >= expected for actual, expected in zip(source["resources"], [1200, 1000, 800])
    )
    assert any(report["title"] == "Allianzversorgung abgebrochen" for report in source["reports"])
    assert not any(job["kind"] == "alliance_supply" for job in source["jobs"])
    assert all(
        actual >= expected
        for actual, expected in zip(state(universe, 1)["resources"], [1200, 1000, 800])
    )
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='alliance_supply_receipt_rejected'"
            ).fetchone()[0]
            == 1
        )


def test_alliance_roles_invites_and_private_chat(universe):
    game, users, _ = universe
    own = command(universe, 0, "alliance_create", {"tag": "FUR", "name": "FUR Empire"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})
    with pytest.raises(RuleError):
        command(universe, 1, "alliance_invite", {"name": "Charlie"})
    command(universe, 0, "alliance_role", {"key": users[1], "role": "officer"})
    command(universe, 1, "alliance_invite", {"name": "Charlie"})
    command(
        universe, 0, "message", {"channel": "alliance", "body": "Nur Verbündete dürfen das lesen."}
    )
    assert any(m["channel"] == "alliance" for m in state(universe, 1)["messages"])
    assert not any(m["channel"] == "alliance" for m in state(universe, 2)["messages"])
    command(universe, 0, "alliance_transfer", {"key": users[1]})
    transfer = state(universe, 1)["alliance_transfer_request"]
    assert transfer["successor_id"] == users[1]
    assert state(universe, 1)["membership"]["role"] == "officer"
    with pytest.raises(RuleError, match="Übertrage zuerst"):
        command(universe, 0, "alliance_leave")
    command(universe, 1, "alliance_transfer_accept", {"key": transfer["id"]})
    assert state(universe, 1)["membership"]["role"] == "leader"
    command(universe, 0, "alliance_leave")
    assert state(universe, 0)["membership"] is None
    assert len(own["alliances"]) == 1
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM audit").fetchone()[0] >= 6


def test_alliance_leadership_transfer_requires_successor_consent(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "CONSENT", "name": "Consent Circle"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})

    command(universe, 0, "alliance_transfer", {"key": users[1]})
    transfer = state(universe, 0)["alliance_transfer_request"]
    assert transfer["successor_name"] == "Bravo"
    assert state(universe, 1)["alliance_transfer_request"]["id"] == transfer["id"]
    assert state(universe, 2)["alliance_transfer_request"] is None
    with game.transaction() as db:
        assert db.execute("SELECT leader FROM alliances").fetchone()[0] == users[0]
        assert (
            db.execute("SELECT role FROM members WHERE user_id=?", (users[1],)).fetchone()[0]
            == "member"
        )

    with pytest.raises(RuleError, match="nicht Mitglied"):
        command(universe, 2, "alliance_transfer_accept", {"key": transfer["id"]})
    with pytest.raises(RuleError, match="nicht Mitglied"):
        command(universe, 2, "alliance_transfer_decline", {"key": transfer["id"]})
    command(universe, 1, "alliance_transfer_decline", {"key": transfer["id"]})
    assert state(universe, 0)["alliance_transfer_request"] is None

    command(universe, 0, "alliance_transfer", {"key": users[1]})
    transfer = state(universe, 1)["alliance_transfer_request"]
    command(universe, 0, "alliance_transfer_cancel", {"key": transfer["id"]})
    with pytest.raises(RuleError, match="nicht mehr gültig"):
        command(universe, 1, "alliance_transfer_accept", {"key": transfer["id"]})

    command(universe, 0, "alliance_transfer", {"key": users[1]})
    transfer = state(universe, 1)["alliance_transfer_request"]
    accept_token = identity()
    accepted = command(
        universe,
        1,
        "alliance_transfer_accept",
        {"key": transfer["id"]},
        accept_token,
    )
    replay = command(
        universe,
        1,
        "alliance_transfer_accept",
        {"key": transfer["id"]},
        accept_token,
    )
    assert replay["membership"] == accepted["membership"]
    assert replay["membership"]["role"] == "leader"
    assert state(universe, 0)["membership"]["role"] == "officer"
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_transfer_requests").fetchone()[0] == 0


def test_alliance_permissions_are_configurable_and_leader_only(universe):
    game, _users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "PERM", "name": "Permission Circle"})
    assert set(state(universe, 0)["alliance_permissions"]) == {
        "applications",
        "invitations",
        "description",
        "member_removal",
        "diplomacy",
        "bulletin",
        "forum_moderation",
        "treasury",
        "projects",
    }
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})
    command(universe, 0, "alliance_permissions_update", {"role": "member", "permissions": []})
    with pytest.raises(RuleError, match="Berechtigung"):
        command(universe, 1, "alliance_invite", {"name": "Charlie"})
    with pytest.raises(RuleError, match="Rollenberechtigungen"):
        command(
            universe,
            1,
            "alliance_permissions_update",
            {"role": "member", "permissions": ["invitations"]},
        )

    command(
        universe,
        0,
        "alliance_permissions_update",
        {"role": "member", "permissions": ["invitations"]},
    )
    assert state(universe, 1)["alliance_permissions"] == ["invitations"]
    command(universe, 1, "alliance_invite", {"name": "Charlie"})
    with pytest.raises(RuleError, match="Offiziere oder Mitglieder"):
        command(
            universe,
            0,
            "alliance_permissions_update",
            {"role": "leader", "permissions": []},
        )
    with pytest.raises(RuleError, match="Berechtigungsauswahl"):
        command(
            universe,
            0,
            "alliance_permissions_update",
            {"role": "member", "permissions": ["server_admin"]},
        )
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM alliance_role_permissions WHERE role='member'"
            ).fetchone()[0]
            == 1
        )


def test_alliance_invitation_recipient_can_decline_only_their_invite(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "DECL", "name": "Decline Circle"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    command(universe, 0, "alliance_invite", {"name": "Charlie"})
    bravo_invite = state(universe, 1)["invites"][0]["id"]
    token = identity()
    command(universe, 1, "alliance_invite_decline", {"key": bravo_invite}, token)
    replay = command(universe, 1, "alliance_invite_decline", {"key": bravo_invite}, token)
    assert replay["invites"] == []
    assert state(universe, 1)["invites"] == []
    assert len(state(universe, 2)["invites"]) == 1
    assert len(state(universe, 0)["alliance_outgoing_invites"]) == 1
    assert state(universe, 2)["alliance_outgoing_invites"] == []
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM invites").fetchone()[0] == 1
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_invite_decline'",
                (users[1],),
            ).fetchone()[0]
            == 1
        )
        with pytest.raises(RuleError, match="Einladung nicht gefunden"):
            game.command(db, users[2], "alliance_invite_decline", {"key": bravo_invite}, identity())


def test_alliance_leader_or_officer_can_cancel_only_their_alliance_invites(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "CANC", "name": "Cancel Circle"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    assert state(universe, 0)["alliance_outgoing_invites"][0]["id"] == invite
    leader_state = state(universe, 0)
    assert "alliance_invite_candidates" not in leader_state
    assert "alliance_invite_candidates" not in state(universe, 2)
    assert all(
        candidate["id"] not in {users[0], users[1]}
        for candidate in leader_state["alliance_candidates"]
    )
    with game.transaction() as db, pytest.raises(RuleError, match="Nur die Allianzleitung"):
        game.command(db, users[2], "alliance_invite_cancel", {"key": invite}, identity())
    command(universe, 0, "alliance_invite_cancel", {"key": invite})
    assert state(universe, 1)["invites"] == []
    with pytest.raises(RuleError, match="Einladung nicht gefunden"):
        command(universe, 0, "alliance_invite_cancel", {"key": invite})

    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    second_invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": second_invite})
    command(universe, 0, "alliance_role", {"key": users[1], "role": "officer"})
    command(universe, 1, "alliance_invite", {"name": "Charlie"})
    officer_invite = state(universe, 2)["invites"][0]["id"]
    command(universe, 1, "alliance_invite_cancel", {"key": officer_invite})
    assert state(universe, 2)["invites"] == []


def test_alliance_applications_can_be_withdrawn_decided_and_do_not_leak(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "APLY", "name": "Application Circle"})
    alliance_id = state(universe, 0)["membership"]["alliance_id"]
    command(universe, 1, "alliance_apply", {"key": alliance_id})
    application = state(universe, 1)["alliance_applications"][0]
    assert application["alliance_id"] == alliance_id
    assert len(state(universe, 0)["alliance_incoming_applications"]) == 1
    assert state(universe, 2)["alliance_incoming_applications"] == []
    with game.transaction() as db, pytest.raises(RuleError, match="Nur die Allianzleitung"):
        game.command(
            db, users[2], "alliance_application_accept", {"key": application["id"]}, identity()
        )
    with (
        game.transaction() as db,
        pytest.raises(RuleError, match="bereits bei der Allianz beworben"),
    ):
        game.command(db, users[0], "alliance_invite", {"name": "Bravo"}, identity())

    token = identity()
    command(universe, 1, "alliance_application_withdraw", {"key": application["id"]}, token)
    replay = command(
        universe, 1, "alliance_application_withdraw", {"key": application["id"]}, token
    )
    assert replay["alliance_applications"] == []
    assert state(universe, 0)["alliance_incoming_applications"] == []

    command(universe, 1, "alliance_apply", {"key": alliance_id})
    accepted_id = state(universe, 1)["alliance_applications"][0]["id"]
    command(universe, 0, "alliance_application_accept", {"key": accepted_id})
    assert state(universe, 1)["membership"]["alliance_id"] == alliance_id
    assert state(universe, 0)["alliance_incoming_applications"] == []
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_applications").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_application_accept'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )


def test_alliance_application_can_be_rejected_and_applicant_can_reapply(universe):
    game, _users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "REJT", "name": "Review Circle"})
    alliance_id = state(universe, 0)["membership"]["alliance_id"]
    command(universe, 1, "alliance_apply", {"key": alliance_id})
    first_id = state(universe, 0)["alliance_incoming_applications"][0]["id"]
    command(universe, 0, "alliance_application_reject", {"key": first_id})
    assert state(universe, 1)["alliance_applications"] == []
    command(universe, 1, "alliance_apply", {"key": alliance_id})
    assert len(state(universe, 0)["alliance_incoming_applications"]) == 1
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_applications").fetchone()[0] == 1


def test_session_management_schema16_backfills_existing_sessions_on_each_adapter(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute(
            "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                "hashed-session-token",
                users[0],
                "csrf-secret",
                2_000_000_000,
                "temporary-id",
                1_900_000_000,
                "Legacy browser",
            ),
        )
        db.execute("DROP INDEX sessions_owner_feed")
        db.execute("DROP INDEX sessions_session_id_unique")
        db.execute("ALTER TABLE sessions DROP COLUMN user_agent")
        db.execute("ALTER TABLE sessions DROP COLUMN created")
        db.execute("ALTER TABLE sessions DROP COLUMN session_id")
        db.execute("DELETE FROM schema_versions WHERE version=16")
        db.execute("DELETE FROM schema_versions WHERE version=27")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        session = db.execute(
            "SELECT token,user_id,csrf,expires,session_id,created,user_agent FROM sessions "
            "WHERE token=?",
            ("hashed-session-token",),
        ).fetchone()
        assert tuple(session[key] for key in ("token", "user_id", "csrf", "expires")) == (
            "hashed-session-token",
            users[0],
            "csrf-secret",
            2_000_000_000,
        )
        assert session["session_id"]
        assert session["session_id"] != "hashed-session-token"
        assert session["created"] == 0
        assert session["user_agent"] == ""


def test_password_change_reauthenticates_and_revokes_sessions_on_each_adapter(universe):
    game, users, _clock = universe
    user = users[0]
    old_password = "Current-password-123"
    new_password = "Replacement-password-456"
    with game.transaction() as db:
        db.execute(
            "UPDATE users SET password=? WHERE id=?", (PasswordHasher().hash(old_password), user)
        )
        db.execute(
            "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                "hash-before-password-change",
                user,
                "csrf-value",
                2_000_000_000,
                "session-before-change",
                1_900_000_000,
                "Test client",
            ),
        )
        with pytest.raises(RuleError, match="Passwort stimmt nicht"):
            Accounts(game).private(
                db,
                user,
                AccountAction(
                    action="password", password="incorrect-password", new_password=new_password
                ),
            )
    with game.transaction() as db:
        Accounts(game).private(
            db,
            user,
            AccountAction(action="password", password=old_password, new_password=new_password),
        )
        saved_hash = db.execute("SELECT password FROM users WHERE id=?", (user,)).fetchone()[0]
        assert PasswordHasher().verify(saved_hash, new_password)
        assert (
            db.execute("SELECT count(*) FROM sessions WHERE user_id=?", (user,)).fetchone()[0] == 0
        )
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='account_password'", (user,)
            ).fetchone()[0]
            == 1
        )


def test_map_bookmarks_are_private_idempotent_and_limited(universe):
    game, users, _ = universe
    with game.transaction() as db:
        all_targets = game.world_outposts(db, 1)
        for target in all_targets[:21]:
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(observer_id,world_id,x,y) DO NOTHING",
                (users[0], 1, target["x"], target["y"], 1),
            )
    targets = all_targets
    selected = [target["id"] for target in targets[:21]]

    command(universe, 0, "map_bookmark_add", {"key": selected[0]})
    command(universe, 0, "map_bookmark_add", {"key": selected[0]})
    assert state(universe, 0)["map_bookmarks"] == [selected[0]]
    assert state(universe, 1)["map_bookmarks"] == []

    with pytest.raises(RuleError, match="existiert nicht"):
        command(universe, 0, "map_bookmark_add", {"key": "not-a-world-target"})
    with pytest.raises(RuleError, match="höchstens 20"):
        for target_id in selected[1:]:
            command(universe, 0, "map_bookmark_add", {"key": target_id})

    command(universe, 0, "map_bookmark_remove", {"key": selected[0]})
    assert selected[0] not in state(universe, 0)["map_bookmarks"]
    command(universe, 0, "map_bookmark_add", {"key": selected[-1]})
    assert len(state(universe, 0)["map_bookmarks"]) == 20
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM map_bookmarks WHERE user_id=? AND world_id=1",
                (users[0],),
            ).fetchone()[0]
            == 20
        )


def test_map_bookmark_limit_is_independent_for_each_world(universe):
    game, users, clock = universe
    with game.transaction() as db:
        world_id = game.create_world(db, "Bookmark Limit World", 771_203, 24, True)
        game.join_world(db, users[0], "Alpha", world_id)
        targets_by_world = {
            1: game.world_outposts(db, 1)[:21],
            world_id: game.world_outposts(db, world_id)[:21],
        }
        for target_world, targets in targets_by_world.items():
            for target in targets:
                db.execute(
                    "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO NOTHING",
                    (users[0], target_world, target["x"], target["y"], clock[0]),
                )

    command(universe, 0, "world_select", {"world_id": 1})
    for target in targets_by_world[1][:20]:
        command(universe, 0, "map_bookmark_add", {"key": target["id"]})
    assert len(state(universe, 0)["map_bookmarks"]) == 20

    command(universe, 0, "world_select", {"world_id": world_id})
    assert state(universe, 0)["world_id"] == world_id
    for target in targets_by_world[world_id][:20]:
        command(universe, 0, "map_bookmark_add", {"key": target["id"]})
    assert len(state(universe, 0)["map_bookmarks"]) == 20
    with pytest.raises(RuleError, match="20 Außenposten je Welt"):
        command(universe, 0, "map_bookmark_add", {"key": targets_by_world[world_id][20]["id"]})

    command(universe, 0, "world_select", {"world_id": 1})
    assert set(state(universe, 0)["map_bookmarks"]) == {
        target["id"] for target in targets_by_world[1][:20]
    }
    with game.transaction() as db:
        counts = db.execute(
            "SELECT world_id,count(*) AS total FROM map_bookmarks "
            "WHERE user_id=? GROUP BY world_id ORDER BY world_id",
            (users[0],),
        ).fetchall()
        assert {int(row["world_id"]): int(row["total"]) for row in counts} == {
            1: 20,
            world_id: 20,
        }


def test_colonization_creates_independent_owned_colony_and_switch_is_authorized(universe):
    game, users, _ = universe
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["hq"] = 3
        home["resources"] = [5000, 5000, 5000]
        game.save(db, home)
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        existing = [
            json.loads(row[0]) for row in db.execute("SELECT state FROM colonies WHERE world_id=1")
        ]
    blocked = {(town["x"], town["y"]) for town in towns}
    blocked.update((colony["x"], colony["y"]) for colony in existing)
    target = next(
        (x, y)
        for y in range(64)
        for x in range(64)
        if (x, y) not in blocked
        and all(math.hypot(x - colony["x"], y - colony["y"]) >= 6 for colony in existing)
    )

    created = command(universe, 0, "colonize", {"x": target[0], "y": target[1]})
    assert created["colony_count"] == 2
    assert created["colony_slot_limit"] == 2
    assert created["x"] != target[0] or created["y"] != target[1]
    new_colony = next(c for c in created["colonies"] if not c["is_home"])
    assert (new_colony["x"], new_colony["y"]) == target
    assert created["resources"] == [3000, 3500, 4000]
    assert len(created["ranking"]) == 3

    switched = command(universe, 0, "colony_select", {"key": new_colony["colony_id"]})
    assert switched["colony_id"] == new_colony["colony_id"]
    assert (switched["x"], switched["y"]) == target
    assert switched["resources"] == [500, 500, 500]
    assert switched["units"]["ranger"] == 5

    command(universe, 0, "build", {"key": "wood"})
    home_colony = next(c for c in switched["colonies"] if c["is_home"])
    home_state = command(universe, 0, "colony_select", {"key": home_colony["colony_id"]})
    assert home_state["jobs"] == []
    assert (
        next(c for c in home_state["colonies"] if c["selected"])["colony_id"]
        == home_colony["colony_id"]
    )

    with pytest.raises(RuleError, match="gehört nicht zu deinem Imperium"):
        command(universe, 1, "colony_select", {"key": new_colony["colony_id"]})
    with game.transaction() as db:
        saved = db.execute(
            "SELECT state FROM colonies WHERE colony_id=? AND user_id=?",
            (new_colony["colony_id"], users[0]),
        ).fetchone()
        assert saved is not None and json.loads(saved[0])["jobs"][0]["kind"] == "build"

    restarted = Game(game.path)
    with restarted.transaction() as db:
        resumed = restarted.view(db, users[0])
        assert resumed["colony_id"] == home_colony["colony_id"]
        assert resumed["colony_count"] == 2


def test_owned_outpost_conversion_transfers_stock_garrison_and_removes_territory(universe):
    game, users, clock = universe
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["hq"] = 3
        home["buildings"]["storage"] = 10
        home["resources"] = [9000, 7000, 5000]
        home["captures"] = 1
        game.save(db, home)
        travel = travel_times(db, (home["x"], home["y"]), 1)
        towns = game.world_outposts(db, 1)
        target = next(
            town
            for town in towns
            if town["tier"] < 8
            and math.hypot(town["x"] - home["x"], town["y"] - home["y"]) >= 6
            and (town["x"], town["y"]) in travel
        )
        target.update(
            owner=users[0],
            cleared=True,
            stock=[125, 250, 375],
            units={"ranger": 3, "sentinel": 2, "mech": 1},
        )
        game.save_world_outposts(db, 1, towns)
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, target["x"], target["y"], clock[0]),
        )
        db.execute(
            "INSERT INTO map_bookmarks(user_id,target_id,created,world_id) VALUES (?,?,?,?)",
            (users[0], target["id"], clock[0], 1),
        )
        target_id, target_name = target["id"], target["name"]

    token = identity()
    converted = command(
        universe, 0, "outpost_colonize", {"key": target_id, "confirmation": target_name}, token
    )
    assert converted["colony_count"] == 2
    assert converted["resources"] == [3000, 2500, 2000]
    new_colony = next(c for c in converted["colonies"] if not c["is_home"])
    assert (new_colony["x"], new_colony["y"]) == (target["x"], target["y"])
    with game.transaction() as db:
        new_state = json.loads(
            db.execute(
                "SELECT state FROM colonies WHERE colony_id=?", (new_colony["colony_id"],)
            ).fetchone()[0]
        )
        home_state = game.read(db, users[0])
    assert new_state["resources"] == [125, 250, 375]
    expected_garrison = {"ranger": 3, "sentinel": 2, "mech": 1}
    assert {
        unit: new_state["units"].get(unit, 0) for unit in expected_garrison
    } == expected_garrison
    assert all(
        new_state["units"].get(unit, 0) == 0
        for unit in new_state["units"].keys() - expected_garrison.keys()
    )
    assert home_state["captures"] == 0
    replay = command(
        universe, 0, "outpost_colonize", {"key": target_id, "confirmation": target_name}, token
    )
    assert replay["colony_count"] == 2
    assert replay["resources"] == converted["resources"]
    with game.transaction() as db:
        assert all(post["id"] != target_id for post in game.world_outposts(db, 1))
        assert (
            db.execute(
                "SELECT 1 FROM map_bookmarks WHERE target_id=? AND world_id=1", (target_id,)
            ).fetchone()
            is None
        )
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='outpost_colonize' AND target=?",
            (users[0], target_id),
        ).fetchone()
        assert json.loads(audit["details"])["costs"] == [6000, 4500, 3000]


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("confirmation", "exakten Außenpostennamen"),
        ("citadel", "Zitadelle des Kerns"),
        ("foreign", "vollständig eroberter eigener Außenposten"),
        ("cost", "Umwandlung kostet"),
    ],
)
def test_outpost_conversion_rejects_unconfirmed_or_ineligible_target(universe, failure, message):
    game, users, clock = universe
    with game.transaction() as db:
        home = game.read(db, users[0])
        home["buildings"]["hq"] = 3
        home["buildings"]["storage"] = 10
        home["resources"] = [9000, 7000, 5000]
        home["captures"] = 1
        game.save(db, home)
        travel = travel_times(db, (home["x"], home["y"]), 1)
        towns = game.world_outposts(db, 1)
        target = next(
            town
            for town in towns
            if town["tier"] < 8
            and math.hypot(town["x"] - home["x"], town["y"] - home["y"]) >= 6
            and (town["x"], town["y"]) in travel
        )
        target.update(owner=users[0], cleared=True)
        if failure == "citadel":
            target["tier"] = 8
        if failure == "foreign":
            target["owner"] = users[1]
        if failure == "cost":
            home["resources"] = [5999, 7000, 5000]
            game.save(db, home)
        game.save_world_outposts(db, 1, towns)
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, target["x"], target["y"], clock[0]),
        )
        target_id, target_name = target["id"], target["name"]

    confirmation = "wrong name" if failure == "confirmation" else target_name
    with pytest.raises(RuleError, match=message):
        command(universe, 0, "outpost_colonize", {"key": target_id, "confirmation": confirmation})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM colonies WHERE user_id=? AND world_id=1", (users[0],)
            ).fetchone()[0]
            == 1
        )
        assert any(post["id"] == target_id for post in game.world_outposts(db, 1))


def test_relocation_keeps_colony_identity_and_blocks_incoming_missions(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=3, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)
        viewed = game.view(db, users[0])
        other = game.read(db, users[1])
        occupied = {(town["x"], town["y"]) for town in game.world_outposts(db, 1)}
        neighbors = db.execute(
            "SELECT x,y FROM colonies WHERE world_id=1 AND colony_id<>?",
            (colony["colony_id"],),
        ).fetchall()
        start = (colony["x"], colony["y"])
        x, y = next(
            point
            for point in sorted(travel_times(db, start, 1))
            if point != start
            and point not in occupied
            and f"{point[0]}:{point[1]}" in viewed["terrain_map"]
            and all(math.hypot(row["x"] - point[0], row["y"] - point[1]) >= 6 for row in neighbors)
        )
        other["jobs"].append(
            {
                "id": identity(),
                "kind": "colony_supply",
                "key": colony["colony_id"],
                "due": clock[0] + 600,
            }
        )
        game.save(db, other)
    payload = {"world_id": 1, "colony_id": colony["colony_id"], "x": x, "y": y}
    with pytest.raises(RuleError, match="laufender Aufträge"):
        command(universe, 0, "colony_relocate", payload)
    with game.transaction() as db:
        other = game.read(db, users[1])
        other["jobs"] = []
        game.save(db, other)
    sector = {"world_id": 1, "x": x, "y": y, "key": "protected"}
    with pytest.raises(RuleError, match="Nur die Spielleitung"):
        command(universe, 0, "admin_terra_sector", sector)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    marked = command(universe, 0, "admin_terra_sector", sector)
    assert marked["terra_sector_rules"][f"{x}:{y}"] == "protected"
    with pytest.raises(RuleError, match="geschützt"):
        command(universe, 0, "colony_relocate", payload)
    with pytest.raises(RuleError, match="geschützt"):
        command(universe, 0, "colonize", {"x": x, "y": y})
    command(universe, 0, "admin_terra_sector", {**sector, "key": "clear"})
    token = identity()
    moved = command(universe, 0, "colony_relocate", payload, token)
    assert moved["colony_id"] == colony["colony_id"]
    assert (moved["x"], moved["y"]) == (x, y)
    assert moved["resources"] == [3000, 3500, 4000]
    assert moved["relocation_ready_at"] == clock[0] + 7 * 86400
    assert (
        command(universe, 0, "colony_relocate", payload, token)["resources"] == moved["resources"]
    )
    with pytest.raises(RuleError, match="versetzbar"):
        command(universe, 0, "colony_relocate", payload)
    with game.transaction() as db:
        row = db.execute(
            "SELECT x,y FROM colonies WHERE colony_id=?", (colony["colony_id"],)
        ).fetchone()
        assert (row["x"], row["y"]) == (x, y)


def test_spawn_reservation_is_prioritized_only_in_its_world(universe):
    game, _users, _ = universe
    with game.transaction() as db:
        world = game.create_world(db, "Reserved start", 48192, 8)
        reserved = db.execute(
            "SELECT t.x,t.y FROM world_terrain t WHERE t.world_id=? AND t.terrain<>'water' "
            "AND NOT EXISTS(SELECT 1 FROM world_outposts p WHERE p.world_id=t.world_id "
            "AND p.x=t.x AND p.y=t.y) ORDER BY t.x,t.y LIMIT 1",
            (world,),
        ).fetchone()
        db.execute(
            "INSERT INTO terra_sector_rules(world_id,x,y,kind) VALUES (?,?,?,'spawn_reserved')",
            (world, reserved["x"], reserved["y"]),
        )
    genesis = state(universe, 0)
    assert f"{reserved['x']}:{reserved['y']}" not in genesis["terra_sector_rules"]
    joined = command(universe, 0, "world_join", {"world_id": world})
    assert (joined["x"], joined["y"]) == (reserved["x"], reserved["y"])


def test_colonization_requires_headquarters_slot_and_costs(universe):
    game, users, _ = universe
    initial = state(universe, 0)
    occupied = {(town["x"], town["y"]) for town in initial["world"]}
    occupied.update((colony["x"], colony["y"]) for colony in initial["colonies"])
    players = initial["players"]
    free = next(
        (x, y)
        for y in range(64)
        for x in range(64)
        if (x, y) not in occupied
        and all(math.hypot(x - other["x"], y - other["y"]) >= 6 for other in players)
    )
    with pytest.raises(RuleError, match="Stufe 3"):
        command(universe, 0, "colonize", {"x": free[0], "y": free[1]})

    with game.transaction() as db:
        base = game.read(db, users[0])
        base["buildings"]["hq"] = 3
        base["resources"] = [2000, 1500, 999]
        game.save(db, base)
    with pytest.raises(RuleError, match="Kolonisationskosten"):
        command(universe, 0, "colonize", {"x": free[0], "y": free[1]})


def test_two_players_racing_for_one_sector_create_only_one_colony(universe):
    game, users, _ = universe
    with game.transaction() as db:
        for user in users[:2]:
            home = game.read(db, user)
            home["buildings"]["hq"] = 3
            home["resources"] = [4000, 4000, 4000]
            game.save(db, home)
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        colonies = [
            json.loads(row[0]) for row in db.execute("SELECT state FROM colonies WHERE world_id=1")
        ]
    occupied = {(town["x"], town["y"]) for town in towns}
    occupied.update((colony["x"], colony["y"]) for colony in colonies)
    target = next(
        (x, y)
        for y in range(64)
        for x in range(64)
        if (x, y) not in occupied
        and all(math.hypot(x - colony["x"], y - colony["y"]) >= 6 for colony in colonies)
    )

    start_together = Barrier(2)

    def colonize(index):
        start_together.wait(timeout=10)
        try:
            command(universe, index, "colonize", {"x": target[0], "y": target[1]})
            return index
        except RuleError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(colonize, (0, 1)))
    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    winner = winners[0]
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM colonies WHERE world_id=1 AND x=? AND y=?", target
            ).fetchone()[0]
            == 1
        )
        for index, user in enumerate(users[:2]):
            home_row = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=1 AND is_home=TRUE",
                (user,),
            ).fetchone()
            home = game.read_colony(db, home_row["colony_id"])
            assert home["resources"] == (
                [2000, 2500, 3000] if index == winner else [4000, 4000, 4000]
            )


def test_diplomacy_and_own_alliance_block_attacks(universe):
    _, users, _ = universe
    a = command(universe, 0, "alliance_create", {"tag": "AAA", "name": "Alpha Allianz"})[
        "membership"
    ]["alliance_id"]
    b = command(universe, 1, "alliance_create", {"tag": "BBB", "name": "Bravo Allianz"})[
        "membership"
    ]["alliance_id"]
    command(universe, 0, "diplomacy", {"key": b, "status": "nap"})
    command(universe, 1, "diplomacy", {"key": a, "status": "accept"})
    with pytest.raises(RuleError, match="Nichtangriffspakt"):
        command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 5}})
    command(universe, 0, "diplomacy", {"key": b, "status": "war"})
    attack = command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 5}})
    assert attack["jobs"][0]["kind"] == "attack"


def test_alliance_diplomacy_chronicle_is_public_ordered_and_immutable(universe):
    game, users, clock = universe
    first = command(universe, 0, "alliance_create", {"tag": "CHRON", "name": "Chronicle One"})[
        "membership"
    ]["alliance_id"]
    second = command(universe, 1, "alliance_create", {"tag": "LOGS", "name": "Chronicle Two"})[
        "membership"
    ]["alliance_id"]

    command(universe, 0, "diplomacy", {"key": second, "status": "nap"})
    with game.transaction() as db:
        directory, _has_more = game.systems.alliance_directory_page(db, user_id=users[0])
        target = next(alliance for alliance in directory if alliance["id"] == second)
        assert target["diplomacy_status"] == "nap"
        assert target["diplomacy_accepted"] == 0
        assert target["diplomacy_proposed_by"] == first
    assert "diplomacy" not in state(universe, 0)
    clock[0] += 1
    command(universe, 1, "diplomacy", {"key": first, "status": "accept"})
    clock[0] += 1
    command(universe, 0, "diplomacy", {"key": second, "status": "war"})
    clock[0] += 1
    command(universe, 1, "diplomacy", {"key": first, "status": "neutral"})

    events = state(universe, 2)["diplomacy_events"]
    assert [event["event_type"] for event in events] == [
        "neutralized",
        "war_declared",
        "nap_accepted",
        "nap_proposed",
    ]
    assert all(
        {event["alliance_a_tag"], event["alliance_b_tag"]} == {"CHRON", "LOGS"} for event in events
    )
    assert {event["actor_alliance_tag"] for event in events} == {"CHRON", "LOGS"}
    with game.transaction() as db:
        first_page, has_more = game.systems.diplomacy_events_page(db, page_size=2)
        assert [event["id"] for event in first_page] == [events[0]["id"], events[1]["id"]]
        assert has_more is True
        second_page, has_more = game.systems.diplomacy_events_page(
            db, first_page[-1]["id"], page_size=2
        )
        assert [event["id"] for event in second_page] == [events[2]["id"], events[3]["id"]]
        assert has_more is False
        with pytest.raises(RuleError, match="Diplomatie-Cursor"):
            game.systems.diplomacy_events_page(db, "unknown-event")

    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute(
            "UPDATE alliance_diplomacy_events SET event_type='neutralized' WHERE id=?",
            (events[0]["id"],),
        )
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM alliance_diplomacy_events WHERE id=?", (events[0]["id"],))


def test_alliance_treasury_fees_four_eyes_refunds_and_membership_scope(universe):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "BANK", "name": "Bank Circle"})
    for index in (1, 2):
        command(universe, 0, "alliance_invite", {"name": ("Bravo", "Charlie")[index - 1]})
        invite = state(universe, index)["invites"][0]["id"]
        command(universe, index, "alliance_accept", {"key": invite})
        command(universe, 0, "alliance_role", {"key": users[index], "role": "officer"})

    for index in (0, 1, 2):
        command(
            universe,
            index,
            "alliance_treasury_donate",
            {"resources": [1200, 1000, 800]},
        )

    command(universe, 1, "alliance_treasury_request", {"resources": [100, 200, 0]})
    small = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [100, 200, 0]
    )
    assert json.loads(small["gross_json"]) == [102, 203, 0]
    assert json.loads(small["fee_json"]) == [2, 3, 0]
    assert small["required_approvals"] == 1
    command(universe, 1, "alliance_treasury_request", {"resources": [1, 0, 0]})
    tiny = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [1, 0, 0]
    )
    assert json.loads(tiny["gross_json"]) == [2, 0, 0]
    assert json.loads(tiny["fee_json"]) == [1, 0, 0]
    assert tiny["required_approvals"] == 1
    with pytest.raises(RuleError, match="Kassenbestand"):
        command(universe, 1, "alliance_treasury_request", {"resources": [99_000, 0, 0]})
    before = state(universe, 1)["resources"]
    command(universe, 0, "alliance_treasury_approve", {"key": small["id"]})
    assert state(universe, 1)["resources"] == [before[0] + 100, before[1] + 200, before[2]]

    command(universe, 1, "alliance_treasury_request", {"resources": [2000, 1800, 1200]})
    large = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [2000, 1800, 1200]
    )
    assert json.loads(large["gross_json"]) == [2021, 1819, 1213]
    assert json.loads(large["fee_json"]) == [21, 19, 13]
    assert large["required_approvals"] == 2
    with pytest.raises(RuleError, match="eigenen Kassenantrag"):
        command(universe, 1, "alliance_treasury_approve", {"key": large["id"]})
    before_large = state(universe, 1)["resources"]
    command(universe, 0, "alliance_treasury_approve", {"key": large["id"]})
    pending = next(
        row for row in state(universe, 1)["alliance_treasury_requests"] if row["id"] == large["id"]
    )
    assert pending["status"] == "pending"
    assert pending["approval_count"] == 1
    assert state(universe, 1)["resources"] == before_large
    command(
        universe,
        0,
        "alliance_permissions_update",
        {
            "role": "officer",
            "permissions": [
                "applications",
                "invitations",
                "description",
                "member_removal",
                "diplomacy",
                "bulletin",
                "forum_moderation",
            ],
        },
    )
    with pytest.raises(RuleError, match="Allianzkasse"):
        command(universe, 2, "alliance_treasury_approve", {"key": large["id"]})
    command(
        universe,
        0,
        "alliance_permissions_update",
        {
            "role": "officer",
            "permissions": [
                "applications",
                "invitations",
                "description",
                "member_removal",
                "diplomacy",
                "bulletin",
                "forum_moderation",
                "treasury",
            ],
        },
    )
    command(universe, 2, "alliance_treasury_approve", {"key": large["id"]})
    paid = next(
        row for row in state(universe, 1)["alliance_treasury_requests"] if row["id"] == large["id"]
    )
    assert paid["status"] == "paid"
    assert state(universe, 1)["resources"] == [
        before_large[0] + 2000,
        before_large[1] + 1800,
        before_large[2] + 1200,
    ]

    command(universe, 1, "alliance_treasury_request", {"resources": [50, 0, 0]})
    cancelled = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [50, 0, 0]
    )
    command(universe, 1, "alliance_treasury_cancel", {"key": cancelled["id"]})
    assert (
        next(
            row
            for row in state(universe, 1)["alliance_treasury_requests"]
            if row["id"] == cancelled["id"]
        )["status"]
        == "cancelled"
    )

    command(universe, 1, "alliance_treasury_request", {"resources": [60, 0, 0]})
    leaving = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [60, 0, 0]
    )
    command(universe, 1, "alliance_leave")
    assert (
        next(
            row
            for row in state(universe, 0)["alliance_treasury_requests"]
            if row["id"] == leaving["id"]
        )["status"]
        == "void_membership"
    )
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})
    command(universe, 0, "alliance_role", {"key": users[1], "role": "officer"})

    command(universe, 1, "alliance_treasury_request", {"resources": [0, 75, 0]})
    expires = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [0, 75, 0]
    )
    clock[0] += 7 * 86400 + 1
    with game.transaction() as db:
        game.expire(db, clock[0])
        assert (
            db.execute(
                "SELECT status FROM alliance_treasury_requests WHERE id=?", (expires["id"],)
            ).fetchone()[0]
            == "expired"
        )
        with pytest.raises(Exception, match="immutable"):
            db.execute("DELETE FROM alliance_treasury_ledger")

    current_world_balance = state(universe, 1)["alliance_treasury_balances"]
    assert [row["available"] for row in current_world_balance] == [1477, 978, 1187]
    treasury_rules = state(universe, 1)["alliance_treasury_rules"]
    assert treasury_rules["version"] == "FUR-3-ALLIANCE-TREASURY-3"
    assert treasury_rules["status"] == "owner_approved"
    with game.transaction() as db:
        world_two = game.create_world(db, "Treasury isolation", 872_019, 8, True)
        game.join_world(db, users[1], "Bravo", world_two)
    command(universe, 1, "alliance_treasury_donate", {"resources": [50, 0, 0]})
    assert [row["available"] for row in state(universe, 1)["alliance_treasury_balances"]] == [
        50,
        0,
        0,
    ]
    with game.transaction() as db:
        alliance = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (users[1],)
        ).fetchone()[0]
        original_world_balance = db.execute(
            "SELECT available FROM alliance_treasury_balances "
            "WHERE alliance_id=? AND world_id=1 ORDER BY resource_index",
            (alliance,),
        ).fetchall()
        assert [row[0] for row in original_world_balance] == [1477, 978, 1187]
    with pytest.raises(RuleError, match="Kassenbestand"):
        command(universe, 1, "alliance_treasury_request", {"resources": [51, 0, 0]})

    command(universe, 1, "alliance_treasury_request", {"resources": [40, 0, 0]})
    kicked = next(
        row
        for row in state(universe, 1)["alliance_treasury_requests"]
        if json.loads(row["net_json"]) == [40, 0, 0]
    )
    command(universe, 0, "alliance_kick", {"key": users[1]})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT status FROM alliance_treasury_requests WHERE id=?", (kicked["id"],)
            ).fetchone()[0]
            == "void_membership"
        )
        world_two_balance = db.execute(
            "SELECT available,reserved FROM alliance_treasury_balances "
            "WHERE alliance_id=? AND world_id=? AND resource_index=0",
            (alliance, world_two),
        ).fetchone()
        assert (world_two_balance[0], world_two_balance[1]) == (50, 0)


def test_alliance_projects_complete_cancel_expire_and_refund_contributions(universe):
    game, users, clock = universe
    command(universe, 0, "alliance_create", {"tag": "BUILD", "name": "Builders"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    invite = state(universe, 1)["invites"][0]["id"]
    command(universe, 1, "alliance_accept", {"key": invite})
    command(universe, 0, "alliance_role", {"key": users[1], "role": "officer"})
    assert "projects" in state(universe, 1)["alliance_permissions"]
    command(
        universe,
        0,
        "alliance_permissions_update",
        {"role": "officer", "permissions": []},
    )
    with pytest.raises(RuleError, match="Berechtigung"):
        command(universe, 1, "alliance_project_create", {"key": "frontier_beacon"})
    assert state(universe, 1)["alliance_projects"] == []
    command(
        universe,
        0,
        "alliance_permissions_update",
        {"role": "officer", "permissions": ["projects"]},
    )
    command(universe, 0, "alliance_project_create", {"key": "frontier_beacon"})
    active = next(
        project
        for project in state(universe, 0)["alliance_projects"]
        if project["status"] == "active"
    )
    with pytest.raises(RuleError, match="bereits ein Allianzprojekt"):
        command(universe, 0, "alliance_project_create", {"key": "alliance_hall"})
    before_member = state(universe, 1)["resources"]
    command(
        universe, 1, "alliance_project_contribute", {"key": active["id"], "resources": [1000, 0, 0]}
    )
    assert state(universe, 1)["resources"] == [before_member[0] - 1000, *before_member[1:]]
    with pytest.raises(RuleError, match="Projektziel"):
        command(
            universe,
            0,
            "alliance_project_contribute",
            {"key": active["id"], "resources": [1001, 0, 0]},
        )
    command(
        universe,
        1,
        "alliance_project_contribute",
        {"key": active["id"], "resources": [200, 1000, 800]},
    )
    command(
        universe,
        0,
        "alliance_project_contribute",
        {"key": active["id"], "resources": [800, 500, 200]},
    )
    completed = next(
        project
        for project in state(universe, 0)["alliance_projects"]
        if project["id"] == active["id"]
    )
    assert completed["status"] == "completed"
    assert completed["rules_version"] == "FUR-3-ALLIANCE-PROJECTS-1"
    assert completed["record_reward"] == "Grenzfeuer errichtet"

    command(universe, 0, "alliance_project_create", {"key": "alliance_hall"})
    cancelled = next(
        project
        for project in state(universe, 0)["alliance_projects"]
        if project["status"] == "active"
    )
    before_member = state(universe, 0)["resources"]
    command(
        universe,
        0,
        "alliance_project_contribute",
        {"key": cancelled["id"], "resources": [20, 30, 40]},
    )
    command(universe, 0, "alliance_project_cancel", {"key": cancelled["id"]})
    assert state(universe, 0)["resources"] == before_member
    assert (
        next(
            project
            for project in state(universe, 0)["alliance_projects"]
            if project["id"] == cancelled["id"]
        )["status"]
        == "cancelled"
    )

    command(universe, 0, "alliance_project_create", {"key": "supply_festival"})
    expiring = next(
        project
        for project in state(universe, 0)["alliance_projects"]
        if project["status"] == "active"
    )
    command(
        universe,
        0,
        "alliance_project_contribute",
        {"key": expiring["id"], "resources": [20, 30, 40]},
    )
    clock[0] = int(expiring["deadline"]) + 1
    with game.transaction() as db:
        game.expire(db, clock[0])
        assert (
            db.execute(
                "SELECT status FROM alliance_projects WHERE id=?", (expiring["id"],)
            ).fetchone()[0]
            == "expired"
        )
        refunded = db.execute(
            "SELECT resource_index,SUM(amount) FROM alliance_project_ledger "
            "WHERE project_id=? AND event_type='refund' GROUP BY resource_index ORDER BY resource_index",
            (expiring["id"],),
        ).fetchall()
        assert [(row[0], row[1]) for row in refunded] == [(0, 20), (1, 30), (2, 40)]
        assert (
            db.execute(
                "SELECT COUNT(*) FROM alliance_project_contributions WHERE project_id=? AND refunded=TRUE",
                (expiring["id"],),
            ).fetchone()[0]
            == 1
        )
        game.expire(db, clock[0])
        assert (
            db.execute(
                "SELECT COUNT(*) FROM alliance_project_ledger "
                "WHERE project_id=? AND event_type='refund'",
                (expiring["id"],),
            ).fetchone()[0]
            == 3
        )
        with pytest.raises(Exception, match="immutable"):
            db.execute("DELETE FROM alliance_project_ledger")


def test_alliance_season_archive_schema_and_transactional_close(universe):
    game, users, clock = universe
    first, second = identity(), identity()
    with game.transaction() as db:
        db.execute(
            "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
            ("first@example.test", users[0]),
        )
        db.execute(
            "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
            ("second@example.test", users[1]),
        )
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (first, "FIRST", "First Alliance", "", users[0], clock[0]),
        )
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (second, "SECOND", "Second Alliance", "", users[1], clock[0]),
        )
        db.execute("INSERT INTO members VALUES (?,?,?)", (users[0], first, "leader"))
        db.execute("INSERT INTO members VALUES (?,?,?)", (users[1], second, "leader"))
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings,world_id) "
            "VALUES (?,?,?, ?,0,'[]',1)",
            ("soc005-adapter-season", "SOC-005 adapter", clock[0] - 10, clock[0]),
        )
        game.record_war_score(
            db,
            mission_id="soc005-adapter-mission",
            world_id=1,
            user_id=users[0],
            category="attack",
            points=17,
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0],
        )
        game.expire(db, clock[0])
        snapshot = db.execute(
            "SELECT rules_version FROM season_alliance_snapshots WHERE season_id=?",
            ("soc005-adapter-season",),
        ).fetchone()
        rows = db.execute(
            "SELECT alliance_id,score,rank,eligible_accounts FROM season_alliance_standings "
            "WHERE season_id=?",
            ("soc005-adapter-season",),
        ).fetchall()
        assert snapshot["rules_version"] == "FUR-3-ALLIANCE-RANKING-1"
        assert [
            tuple(row[key] for key in ("alliance_id", "score", "rank", "eligible_accounts"))
            for row in rows
        ] == [(first, 17, 1, 1)]


def test_formal_fur3_alliance_war_requires_diplomatic_acceptance_and_is_public(universe):
    game, _users, _clock = universe
    first = command(universe, 0, "alliance_create", {"tag": "WAR1", "name": "War One"})[
        "membership"
    ]["alliance_id"]
    second = command(universe, 1, "alliance_create", {"tag": "WAR2", "name": "War Two"})[
        "membership"
    ]["alliance_id"]

    # Legacy worlds preserve their existing diplomacy behavior and create no formal record.
    command(universe, 0, "diplomacy", {"key": second, "status": "war"})
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM alliance_wars").fetchone()[0] == 0
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-4' WHERE world_id=1"
        )
    command(universe, 1, "diplomacy", {"key": first, "status": "war"})
    public = state(universe, 2)
    assert len(public["alliance_wars"]) == 1
    war = public["alliance_wars"][0]
    assert war["rules_version"] == alliance_war.VERSION
    assert war["rules_digest"] == alliance_war.RULES_DIGEST
    assert war["status"] == "active"
    assert {war["alliance_a"], war["alliance_b"]} == {first, second}

    command(universe, 0, "alliance_peace_offer", {"key": war["id"]})
    with pytest.raises(RuleError, match="Friedensvorschlag"):
        command(universe, 0, "alliance_peace_accept", {"key": war["id"]})
    with pytest.raises(RuleError, match="Allianzleitung"):
        command(universe, 2, "alliance_peace_decline", {"key": war["id"]})
    command(universe, 1, "alliance_peace_decline", {"key": war["id"]})
    assert state(universe, 0)["alliance_wars"][0]["status"] == "active"

    command(universe, 1, "alliance_peace_offer", {"key": war["id"]})
    command(universe, 0, "alliance_peace_accept", {"key": war["id"]})
    final = state(universe, 2)["alliance_wars"][0]
    assert (final["status"], final["end_reason"], final["ended"]) == (
        "ended",
        "peace",
        final["ended"],
    )
    assert final["ended"] is not None
    with game.transaction() as db:
        a, b = sorted((first, second))
        assert db.execute("SELECT 1 FROM diplomacy WHERE a=? AND b=?", (a, b)).fetchone() is None
        assert (
            db.execute(
                "SELECT event_type FROM alliance_diplomacy_events ORDER BY created DESC,id DESC LIMIT 1"
            ).fetchone()[0]
            == "neutralized"
        )
        assert (
            db.execute(
                "SELECT count(*) FROM alliance_war_events WHERE war_id=?", (war["id"],)
            ).fetchone()[0]
            == 5
        )


def test_formal_war_battle_scoring_is_idempotent_filters_coalitions_and_ends_at_objective(universe):
    game, users, clock = universe
    first = command(universe, 0, "alliance_create", {"tag": "SCOR", "name": "Scoring One"})[
        "membership"
    ]["alliance_id"]
    second = command(universe, 1, "alliance_create", {"tag": "CASU", "name": "Scoring Two"})[
        "membership"
    ]["alliance_id"]
    outsider = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (outsider, "Coalition", "unused"))
        game.create(db, outsider, "Coalition")
        outsider_alliance = identity()
        db.execute(
            "INSERT INTO alliances VALUES (?,?,?,?,?,?)",
            (outsider_alliance, "COAL", "Coalition", "", outsider, 1),
        )
        db.execute("INSERT INTO members VALUES (?,?,?)", (outsider, outsider_alliance, "leader"))
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-4' WHERE world_id=1"
        )
    command(universe, 0, "diplomacy", {"key": second, "status": "war"})
    with game.transaction() as db:
        war = db.execute("SELECT * FROM alliance_wars").fetchone()
        db.execute("UPDATE alliance_wars SET target_points=4 WHERE id=?", (war["id"],))
        war_id = str(war["id"])
        alliance_war.record_battle(
            db,
            mission_id="battle-one",
            world_id=1,
            attacker_losses={users[0]: {"ranger": 0}, outsider: {"ranger": 40}},
            defender_losses={users[1]: {"ranger": 3}},
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0] + 1,
        )
        # A retry for the same mission cannot re-credit the battle.
        alliance_war.record_battle(
            db,
            mission_id="battle-one",
            world_id=1,
            attacker_losses={users[0]: {"ranger": 99}},
            defender_losses={users[1]: {"ranger": 99}},
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0] + 1,
        )
        totals = db.execute(
            "SELECT score_a,score_b,status FROM alliance_wars WHERE id=?", (war_id,)
        ).fetchone()
        assert sorted((int(totals["score_a"]), int(totals["score_b"]))) == [0, 3]
        assert totals["status"] == "active"
        alliance_war.record_battle(
            db,
            mission_id="battle-two",
            world_id=1,
            attacker_losses={users[0]: {"ranger": 0}, outsider: {"ranger": 500}},
            defender_losses={users[1]: {"ranger": 1}},
            rules_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0] + 2,
        )
        final = db.execute(
            "SELECT alliance_a,score_a,score_b,status,winner,end_reason FROM alliance_wars WHERE id=?",
            (war_id,),
        ).fetchone()
        winner_score = int(final["score_a"] if final["alliance_a"] == first else final["score_b"])
        assert winner_score == 4
        assert final["status"] == "ended"
        assert final["winner"] == first
        assert final["end_reason"] == "objective"
        assert (
            db.execute(
                "SELECT count(*) FROM alliance_war_battles WHERE war_id=?", (war_id,)
            ).fetchone()[0]
            == 2
        )
        ledger = db.execute(
            "SELECT alliance_id,user_id,points FROM alliance_war_score_ledger WHERE war_id=?",
            (war_id,),
        ).fetchall()
        assert len(ledger) == 2
        assert all(str(row["user_id"]) != outsider for row in ledger)
        assert (
            db.execute(
                "SELECT event_type FROM alliance_war_events WHERE war_id=? ORDER BY created DESC,id DESC LIMIT 1",
                (war_id,),
            ).fetchone()[0]
            == "ended_objective"
        )
        assert (
            db.execute(
                "SELECT event_type FROM alliance_diplomacy_events ORDER BY created DESC,id DESC LIMIT 1"
            ).fetchone()[0]
            == "neutralized"
        )
        hall = game.systems.hall_of_fame(db, {"id": users[0], "world_id": 1})
        assert len(hall["wars"]) == 1
        assert hall["wars"][0]["winner"] == first
        assert hall["wars"][0]["end_reason"] == "objective"
        db.execute("SAVEPOINT immutable_event_update")
        with pytest.raises(Exception, match="immutable"):
            db.execute("UPDATE alliance_war_events SET details='{}' WHERE war_id=?", (war_id,))
        db.execute("ROLLBACK TO SAVEPOINT immutable_event_update")
        db.execute("RELEASE SAVEPOINT immutable_event_update")
        battle_id = db.execute(
            "SELECT id FROM alliance_war_battles WHERE war_id=? LIMIT 1", (war_id,)
        ).fetchone()[0]
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("UPDATE alliance_war_battles SET attacker_losses=999 WHERE id=?", (battle_id,))
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM alliance_war_battles WHERE id=?", (battle_id,))


def test_live_event_feed_is_bounded_and_aggregate_bonus_is_capped(universe):
    game, _users, _clock = universe
    now = int(time.time())
    with game.transaction() as db:
        for index in range(51):
            db.execute(
                "INSERT INTO events(id,name,starts,ends,bonus) VALUES (?,?,?,?,?)",
                (f"live-event-{index:03}", f"Event {index}", now - 100 + index, now + 86400, 3),
            )
        db.execute(
            "INSERT INTO events(id,name,starts,ends,bonus) VALUES (?,?,?,?,?)",
            ("expired-event", "Expired", now - 500, now - 1, 100),
        )
        first_page, has_more = game.systems.live_event_page(db, now)
        assert len(first_page) == 50
        assert has_more is True
        assert first_page[0]["id"] == "live-event-050"
        older, has_more = game.systems.live_event_page(db, now, first_page[-1]["id"])
        assert [event["id"] for event in older] == ["live-event-000"]
        assert has_more is False
        with pytest.raises(RuleError, match="Ereignis-Cursor"):
            game.systems.live_event_page(db, now, "unknown-event")

    current = state(universe, 0)
    assert len(current["events"]) == 50
    assert current["events_has_more"] is True
    assert current["events"][0]["world_active_bonus"] == 100
    assert current["production_details"][0]["bonus_percent"] == 100


@pytest.mark.parametrize(
    "arrival_change", ("pvp_disabled", "vacation_started", "protection_started", "nap_accepted")
)
def test_pvp_attack_rechecks_protection_and_diplomacy_at_arrival(universe, arrival_change):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        attacker = game.read(db, users[0])
        attacker["units"]["mech"] = 20
        game.save(db, attacker)

    alliances = None
    if arrival_change == "nap_accepted":
        first = command(universe, 0, "alliance_create", {"tag": "PVA", "name": "Aegis"})[
            "membership"
        ]["alliance_id"]
        second = command(universe, 1, "alliance_create", {"tag": "PVB", "name": "Bastion"})[
            "membership"
        ]["alliance_id"]
        alliances = (first, second)

    sent = command(universe, 0, "attack", {"key": users[1], "army": {"mech": 20}})
    attack = next(job for job in sent["jobs"] if job["kind"] == "attack")
    arrival = int(attack["due"])
    with game.transaction() as db:
        if arrival_change == "pvp_disabled":
            db.execute("UPDATE flags SET value='false' WHERE name='pvp'")
        elif arrival_change == "vacation_started":
            target = game.read(db, users[1])
            target["vacation_until"] = arrival + 60
            game.save(db, target)
        elif arrival_change == "protection_started":
            db.execute("UPDATE profiles SET joined=? WHERE user_id=?", (arrival - 1800, users[1]))
    if alliances:
        command(universe, 0, "diplomacy", {"key": alliances[1], "status": "nap"})
        command(universe, 1, "diplomacy", {"key": alliances[0], "status": "accept"})

    clock[0] = arrival
    aborted = state(universe, 0)
    assert sum(report["title"] == "Angriff abgebrochen" for report in aborted["reports"]) == 1
    assert not any(report.get("combat") for report in aborted["reports"])
    return_job = next(job for job in aborted["jobs"] if job["kind"] == "return")
    assert return_job["army"] == {"mech": 20}
    clock[0] = int(return_job["due"])
    returned = state(universe, 0)
    assert returned["units"]["mech"] == 20
    assert sum(report["title"] == "Angriff abgebrochen" for report in returned["reports"]) == 1


def test_market_escrow_concurrent_acceptance_and_reserve(universe):
    game, users, clock = universe
    opened = command(
        universe, 0, "market_create", {"give": 0, "amount": 200, "want": 2, "price": 100}
    )
    offer = opened["offers"][0]["id"]
    assert opened["resources"][0] == 1000

    def accept(index):
        try:
            command(universe, index, "market_accept", {"key": offer})
            return True
        except RuleError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(accept, [1, 2])) == 1
    seller = state(universe, 0)
    assert seller["resources"][2] == 900
    assert sum(state(universe, i)["reserve"][0] for i in (1, 2)) == 200
    with game.transaction() as db:
        row = db.execute("SELECT * FROM offers WHERE id=?", (offer,)).fetchone()
        assert row["buyer"] in users[1:]
        assert row["status"] == "filled"
    created = command(
        universe, 0, "market_create", {"give": 0, "amount": 100, "want": 1, "price": 100}
    )
    assert len(created["offers"]) == 1
    clock[0] += 86401
    assert not state(universe, 0)["offers"]
    assert state(universe, 0)["reserve"][0] == 100


def test_market_history_is_anonymous_aggregated_and_records_completed_trades_only(universe):
    game, users, clock = universe
    token = identity()
    first = command(universe, 0, "trade", {"source": 0, "dest": 1, "amount": 100}, token)
    replay = command(universe, 0, "trade", {"source": 0, "dest": 1, "amount": 100}, token)
    assert replay["resources"] == first["resources"]
    with game.transaction() as db:
        other_world = game.create_world(db, "Market Isolation", 72027, 8)
        db.execute(
            "INSERT INTO market_trades "
            "(id,world_id,timestamp,source_resource,target_resource,source_amount,target_amount,trade_kind) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (identity(), 1, clock[0], 0, 1, 300, 300, "neutral"),
        )
        db.execute(
            "INSERT INTO market_trades "
            "(id,world_id,timestamp,source_resource,target_resource,source_amount,target_amount,trade_kind) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (identity(), other_world, clock[0], 1, 2, 999999, 999999, "neutral"),
        )
        db.execute(
            "INSERT INTO market_trades "
            "(id,world_id,timestamp,source_resource,target_resource,source_amount,target_amount,trade_kind) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (identity(), 1, clock[0] - 30 * 86400 - 1, 0, 1, 10000, 10000, "neutral"),
        )
    replay = state(universe, 0)
    assert not any(
        item["source_resource"] == 1 and item["target_resource"] == 2
        for item in replay["market_history"]
    )
    neutral = next(
        item
        for item in replay["market_history"]
        if item["source_resource"] == 0 and item["target_resource"] == 1
    )
    assert neutral["source_amount"] == 400
    assert neutral["target_amount"] == 350
    assert neutral["trade_count"] == 2
    assert neutral["weighted_price_milli"] == 875
    assert neutral["timestamp"] == (clock[0] // 3600) * 3600
    assert "user_id" not in neutral and "owner" not in neutral and "buyer" not in neutral

    command(universe, 0, "market_create", {"give": 0, "amount": 200, "want": 2, "price": 100})
    before_accept = state(universe, 0)["market_history"]
    assert not any(row["trade_kind"] == "player" for row in before_accept)
    offer = next(row for row in state(universe, 0)["offers"] if row["owner"] == users[0])
    clock[0] += 5
    filled = command(universe, 1, "market_accept", {"key": offer["id"]})
    player_trade = next(row for row in filled["market_history"] if row["trade_kind"] == "player")
    assert player_trade["source_resource"] == 2
    assert player_trade["target_resource"] == 0
    assert player_trade["source_amount"] == 100
    assert player_trade["target_amount"] == 200
    assert player_trade["trade_count"] == 1

    assert (
        "user_id" not in player_trade
        and "owner" not in player_trade
        and "buyer" not in player_trade
    )

    with game.transaction() as db:
        columns = (
            {row["name"] for row in db.execute("PRAGMA table_info(market_trades)")}
            if not db.postgres
            else {
                row["column_name"]
                for row in db.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='market_trades'"
                )
            }
        )
        assert not {"user_id", "buyer", "seller", "account_id"} & columns
        event_count = db.execute("SELECT count(*) FROM market_trades").fetchone()[0]
        assert event_count == 5


def test_market_offer_pages_are_bounded_world_scoped_and_keyset_stable(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = db.execute(
            "SELECT colony_id,world_id FROM colonies WHERE user_id=? AND is_home=TRUE",
            (users[0],),
        ).fetchone()
        world_id = int(colony["world_id"])
        for index in range(52):
            db.execute(
                "INSERT INTO offers "
                "(id,owner,give_resource,give_amount,want_resource,want_amount,created,expires,"
                "status,buyer,world_id,colony_id) VALUES (?,?,?,?,?,?,?,?, 'open',NULL,?,?)",
                (
                    f"market-page-{index:03}",
                    users[0],
                    0,
                    10,
                    1,
                    20,
                    1_700_000_000 + index,
                    clock[0] + 3600,
                    world_id,
                    colony["colony_id"],
                ),
            )
        db.execute(
            "INSERT INTO offers "
            "(id,owner,give_resource,give_amount,want_resource,want_amount,created,expires,"
            "status,buyer,world_id,colony_id) VALUES (?,?,?,?,?,?,?,?, 'open',NULL,?,?)",
            (
                "market-page-expired",
                users[0],
                0,
                10,
                1,
                20,
                1_800_000_000,
                clock[0] - 1,
                world_id,
                colony["colony_id"],
            ),
        )
        first, has_more = game.systems.market_offer_page(db, world_id, clock[0])
        assert len(first) == 50
        assert has_more is True
        assert "market-page-expired" not in {offer["id"] for offer in first}
        second, has_more = game.systems.market_offer_page(db, world_id, clock[0], first[-1]["id"])
        assert len(second) == 2
        assert has_more is False
        assert {offer["id"] for offer in first}.isdisjoint(offer["id"] for offer in second)
        with pytest.raises(RuleError, match="nicht gefunden"):
            game.systems.market_offer_page(db, world_id + 1, clock[0], first[-1]["id"])


def test_market_history_is_limited_to_60_past_hour_buckets(universe):
    game, _, clock = universe
    current_bucket = (clock[0] // 3600) * 3600
    with game.transaction() as db:
        rows = [
            (
                identity(),
                1,
                current_bucket - hour * 3600,
                2,
                0,
                100 + hour,
                200 + hour,
                "neutral",
            )
            for hour in range(61)
        ]
        rows.append((identity(), 1, current_bucket + 3600, 2, 0, 999, 999, "neutral"))
        for row in rows:
            db.execute(
                "INSERT INTO market_trades "
                "(id,world_id,timestamp,source_resource,target_resource,source_amount,target_amount,trade_kind) "
                "VALUES (?,?,?,?,?,?,?,?)",
                row,
            )

    history = state(universe, 0)["market_history"]
    assert len(history) == 60
    assert history[0]["timestamp"] == current_bucket
    assert history[-1]["timestamp"] == current_bucket - 59 * 3600
    assert all(row["source_amount"] != 999 for row in history)


def test_pvp_battle_wall_loot_and_return(universe):
    game, users, clock = universe
    with game.transaction() as db:
        s = game.read(db, users[0])
        s["units"]["mech"] = 100
        game.save(db, s)
        s = game.read(db, users[1])
        s["buildings"]["wall"] = 2
        game.save(db, s)
    command(universe, 0, "attack", {"key": users[1], "army": {"mech": 100}})
    defender_state = state(universe, 1)
    assert defender_state["incoming_count"] == 1
    assert "incoming" not in defender_state
    with game.transaction() as db:
        indexed = db.execute(
            "SELECT target_user,source_colony_id FROM incoming_attack_index"
        ).fetchone()
        assert indexed["target_user"] == users[1]
        assert indexed["source_colony_id"] == users[0]
    clock[0] += 100
    attacker = state(universe, 0)
    defender = state(universe, 1)
    assert 0 < attacker["units"]["mech"] < 100
    assert not attacker["jobs"]
    assert defender["units"]["ranger"] == 0
    attack_report = next(r for r in attacker["reports"] if r["title"] == "Angriff gewonnen")
    defense_report = next(
        r for r in defender["reports"] if r["title"] == "Verteidigung durchbrochen"
    )
    assert attack_report["combat"] == defense_report["combat"]
    assert attack_report["time"] == defense_report["time"] == clock[0]
    assert attack_report["combat"]["participants"] == {
        "attacker": attacker["name"],
        "defender": defender["name"],
    }
    round_report = attack_report["combat"]["rounds"][0]
    assert round_report["round"] == 1
    assert round_report["attacker"]["sent"] == {"mech": 100}
    assert round_report["attacker"]["survivors"]["mech"] == attacker["units"]["mech"]
    assert round_report["attacker"]["losses"]["mech"] == 100 - attacker["units"]["mech"]
    assert round_report["defender"]["sent"]["ranger"] > 0
    assert round_report["defender"]["losses"]["ranger"] == (
        round_report["defender"]["sent"]["ranger"] - round_report["defender"]["survivors"]["ranger"]
    )
    assert len(round_report["loot"]) == 3
    assert not any(report.get("combat") for report in state(universe, 2)["reports"])
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM incoming_attack_index WHERE target_user=?", (users[1],)
            ).fetchone()[0]
            == 0
        )
        audit = db.execute("SELECT details FROM audit WHERE action='battle'").fetchone()
        target_terrain = game.read(db, users[1])["terrain"]
        assert json.loads(audit[0])["defense"] == defense_with_terrain(470, target_terrain)
        assert (
            db.execute("SELECT count(*) FROM ledger WHERE action='pvp_defense'").fetchone()[0] == 1
        )


def test_fur3_pvp_attack_uses_pinned_seed_and_publishes_replay_to_both_players(universe):
    from fur_empire import terra_combat

    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        attacker = game.read(db, users[0])
        attacker["units"]["mech"] = 80
        game.save(db, attacker)
        defender = game.read(db, users[1])
        defender["units"]["ranger"] = 18
        defender["buildings"]["wall"] = 2
        game.save(db, defender)

    sent = command(universe, 0, "attack", {"key": users[1], "army": {"mech": 80}})
    mission = next(job for job in sent["jobs"] if job["kind"] == "attack")
    assert mission["rules_version"] == terra_combat.VERSION
    assert "seed" not in mission
    with game.transaction() as db:
        pinned = db.execute(
            "SELECT seed,seed_commitment,resolved FROM terra_combat_missions WHERE mission_id=?",
            (mission["id"],),
        ).fetchone()
        assert pinned["seed_commitment"] == mission["seed_commitment"]
        assert pinned["resolved"] is None
        db.execute("UPDATE world_settings SET terra_combat_ruleset='FUR-2' WHERE world_id=1")

    clock[0] = mission["due"]
    attacker_after = state(universe, 0)
    defender_after = state(universe, 1)
    attack_report = next(r for r in attacker_after["reports"] if r.get("combat"))
    defense_report = next(r for r in defender_after["reports"] if r.get("combat"))
    assert attack_report["combat"] == defense_report["combat"]
    assert attack_report["combat"]["rules_version"] == terra_combat.VERSION
    assert attack_report["combat"]["seed"] == pinned["seed"]
    assert 1 <= len(attack_report["combat"]["rounds"]) <= 6
    with game.transaction() as db:
        replay = db.execute(
            "SELECT resolved,replay FROM terra_combat_missions WHERE mission_id=?",
            (mission["id"],),
        ).fetchone()
        assert replay["resolved"] == mission["due"]
        assert json.loads(replay["replay"])["seed"] == pinned["seed"]


def test_incoming_attack_index_schema_25_backfills_existing_player_attacks(universe):
    game, users, _clock = universe
    command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 5}})
    with game.transaction() as db:
        expected = db.execute(
            "SELECT job_id,target_user,source_colony_id,due FROM incoming_attack_index"
        ).fetchone()
        assert expected is not None
        db.execute("DROP TABLE incoming_attack_index")
        db.execute("DELETE FROM schema_versions WHERE version=25")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        restored = db.execute(
            "SELECT job_id,target_user,source_colony_id,due FROM incoming_attack_index"
        ).fetchone()
        assert dict(restored) == dict(expected)
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124


def test_colony_name_index_schema_28_backfills_names_without_rewriting_player_state(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        home_before = game.read(db, users[0])
        world_id = game.create_world(db, "Namensindex-Welt", 712907, 8, True)
        game.join_world(db, users[0], home_before["name"], world_id)
        rows_before = [
            (str(row["colony_id"]), str(row["state"]))
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY world_id",
                (users[0],),
            )
        ]
        db.execute("DROP INDEX colonies_name_key")
        db.execute("ALTER TABLE colonies DROP COLUMN name_key")
        db.execute("DELETE FROM schema_versions WHERE version=28")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        rows_after = [
            (str(row["colony_id"]), str(row["state"]))
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY world_id",
                (users[0],),
            )
        ]
        assert rows_after == rows_before
        keys = [
            str(row["name_key"])
            for row in db.execute(
                "SELECT name_key FROM colonies WHERE user_id=? ORDER BY world_id", (users[0],)
            )
        ]
        assert keys == [home_before["name"].casefold(), home_before["name"].casefold()]
        if db.postgres:
            index = db.execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname=current_schema() "
                "AND indexname='colonies_name_key'"
            ).fetchone()
        else:
            index = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' AND name='colonies_name_key'"
            ).fetchone()
        assert index is not None


def test_ranking_score_schema_29_backfills_and_tracks_colony_changes(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        state = game.read(db, users[0])
        state["buildings"]["hq"] = 3
        state["tech"]["tactics"] = 2
        state["captures"] = 1
        serialized = json.dumps(state)
        db.execute(
            "UPDATE colonies SET state=? WHERE colony_id=?",
            (serialized, state["colony_id"]),
        )
        db.execute("DROP INDEX colonies_world_ranking")
        db.execute("ALTER TABLE colonies DROP COLUMN ranking_score")
        db.execute("DELETE FROM schema_versions WHERE version=29")

    upgraded = Game(game.path)
    with upgraded.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        row = db.execute(
            "SELECT state,ranking_score FROM colonies WHERE colony_id=?", (state["colony_id"],)
        ).fetchone()
        assert row["state"] == serialized
        expected = (
            10 * sum(state["buildings"].values())
            + 20 * sum(state["tech"].values())
            + 100 * state["captures"]
        )
        assert row["ranking_score"] == expected
        if db.postgres:
            index = db.execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname=current_schema() "
                "AND indexname='colonies_world_ranking'"
            ).fetchone()
        else:
            index = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' "
                "AND name='colonies_world_ranking'"
            ).fetchone()
        assert index is not None
        state["buildings"]["hq"] = 4
        upgraded.save(db, state)
        expected = (
            10 * sum(state["buildings"].values())
            + 20 * sum(state["tech"].values())
            + 100 * state["captures"]
        )
        assert upgraded.player_ranking_score(db, users[0], 1) == expected


def test_session_inventory_feed_index_is_created_on_each_database_adapter(universe):
    game, _users, _clock = universe
    with game.transaction() as db:
        if db.postgres:
            index = db.execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname=current_schema() "
                "AND indexname='sessions_owner_feed'"
            ).fetchone()
        else:
            index = next(
                (
                    row
                    for row in db.execute("PRAGMA index_list('sessions')")
                    if row["name"] == "sessions_owner_feed"
                ),
                None,
            )
        assert index is not None


def test_tactics_snapshot_logistics_capacity_and_wardens_wall_bonus(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        attacker = game.read(db, users[0])
        attacker["tech"]["tactics"] = 2
        attacker["units"]["mech"] = 10
        game.save(db, attacker)
        defender = game.read(db, users[1])
        defender["buildings"]["wall"] = 2
        defender["tech"]["tactics"] = 1
        defender["faction_chosen"] = True
        pioneers = game.systems.player_defense(defender, "pioneers")
        wardens = game.systems.player_defense(defender, "wardens")
        assert pioneers == defense_with_terrain(497, defender["terrain"])
        assert wardens == defense_with_terrain(593, defender["terrain"])

    dispatched = command(universe, 0, "attack", {"key": users[1], "army": {"mech": 10}})
    assert dispatched["jobs"][0]["tactics"] == 2

    with game.transaction() as db:
        state = game.read(db, users[0])
        state["jobs"] = []
        state["units"]["mech"] = 0
        state["units"]["ranger"] = 15
        state["tech"]["logistics"] = 1
        state["resources"] = [1200, 1000, 800]
        game.save(db, state)
    transported = command(
        universe,
        0,
        "transport",
        {"key": users[1], "army": {"ranger": 2}, "resources": [0, 0, 100]},
    )
    assert transported["resources"][2] == 700
    assert transported["jobs"][0]["kind"] == "transport"
    with game.transaction() as db:
        state = game.read(db, users[0])
        state["tech"]["logistics"] = 0
        game.save(db, state)
    with pytest.raises(RuleError, match="Transportkapazität"):
        command(
            universe,
            0,
            "transport",
            {"key": users[1], "army": {"ranger": 2}, "resources": [0, 0, 101]},
        )


def test_transport_delivers_once_after_restart(universe):
    game, users, clock = universe
    command(
        universe,
        0,
        "transport",
        {"key": users[1], "army": {"ranger": 10}, "resources": [200, 100, 0]},
    )
    assert state(universe, 0)["units"]["ranger"] == 5
    clock[0] += 100
    game = Game(game.path)
    with game.transaction() as db:
        target = game.view(db, users[1])
        sender = game.view(db, users[0])
        before = list(target["resources"])
        assert sender["units"]["ranger"] == 15
        assert not sender["jobs"]
        assert any(r["title"] == "Transport angekommen" for r in target["reports"])
        assert game.view(db, users[1])["resources"] == before


def test_transport_preserves_depot_overflow_and_returns_units_once(universe):
    game, users, clock = universe
    with game.transaction() as db:
        receiver = game.read(db, users[1])
        receiver["buildings"]["storage"] = 1
        receiver["resources"] = [3900, 4000, 3900]
        receiver["reserve"] = [0, 0, 0]
        game.save(db, receiver)
    command(
        universe,
        0,
        "transport",
        {"key": users[1], "army": {"ranger": 10}, "resources": [200, 100, 0]},
    )
    clock[0] += 100
    game = Game(game.path)
    with game.transaction() as db:
        receiver_state = game.read(db, users[1])
        # Freeze offline production at the transport arrival instant so this
        # assertion isolates the cargo credit from elapsed-time income.
        receiver_state["last"] = clock[0]
        game.save(db, receiver_state)
        sender = game.view(db, users[0])
        receiver = game.view(db, users[1])
        assert sender["units"]["ranger"] == 15
        assert sender["jobs"] == []
        assert receiver["resources"] == [4000, 4000, 3900]
        assert receiver["reserve"] == [100, 100, 0]
        # Reprocessing after restart must not deliver cargo or return carriers twice.
        game.advance(db, clock[0])
        assert game.view(db, users[0])["units"]["ranger"] == 15
        assert game.view(db, users[1])["reserve"] == [100, 100, 0]


def test_newbie_and_vacation_protection(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET joined=? WHERE user_id=?", (clock[0], users[1]))
    with pytest.raises(RuleError, match="Neulingsschutz"):
        command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 1}})
    command(universe, 1, "vacation")
    before = state(universe, 1)["resources"]
    clock[0] += 7200
    assert state(universe, 1)["resources"] == before
    with pytest.raises(RuleError, match="Urlaubsmodus"):
        command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 1}})
    with pytest.raises(RuleError, match="Urlaubsmodus"):
        command(universe, 1, "build", {"key": "wood"})


def test_vacation_requires_no_own_or_incoming_attack_and_lasts_at_least_one_day(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    command(universe, 0, "admin_flag", {"key": "pvp", "value": "true"})
    command(universe, 0, "attack", {"key": users[1], "army": {"ranger": 1}})
    with pytest.raises(RuleError, match="ohne eigene Aufträge"):
        command(universe, 0, "vacation")
    with pytest.raises(RuleError, match="feindliche Anmärsche"):
        command(universe, 1, "vacation")
    # Advance the inbound operation to its battle resolution before entering
    # vacation, then assert the exact minimum protection window.
    clock[0] += 100
    result = command(universe, 1, "vacation")
    assert result["vacation_until"] == clock[0] + 86400


def test_events_integrate_actual_interval_and_season_archives(universe):
    game, users, clock = universe
    now = clock[0]
    with game.transaction() as db:
        defender = game.read(db, users[1])
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        db.execute("UPDATE world_settings SET mode='season' WHERE world_id=1")
        db.execute(
            "INSERT INTO events(id,name,starts,ends,bonus) VALUES (?,?,?,?,?)",
            (identity(), "Kurzereignis", now + 10, now + 20, 50),
        )
    command(universe, 0, "admin_season", {"name": "Saison Eins", "days": 1, "goal_score": 50})
    clock[0] += 30
    terrain_rates = PRODUCTION_PERCENT[defender["terrain"]]
    expected = [
        [1200, 1000, 800][index]
        + (30 * 4 * 100 * terrain_rates[index] // 100 + 10 * 4 * 50 * terrain_rates[index] // 100)
        // 100
        for index in range(3)
    ]
    assert state(universe, 1)["resources"] == expected
    clock[0] += 86400
    archived = state(universe, 1)["seasons"][0]
    assert archived["archived"] == 1
    assert len(json.loads(archived["standings"])) == 3
    assert json.loads(archived["standings"])[0]["score"] == 50
    assert archived["rules_version"] == REGISTRY["version"]
    assert archived["rules_digest"] == RULES_DIGEST
    assert archived["rules_source"] == "season_start"
    assert archived["goal_score"] == 50
    assert json.loads(archived["standings"])[0]["goal_reached"] is True
    assert "season_champion" in json.loads(archived["standings"])[0]["awards"]
    assert len(archived["awards"]) == sum(
        len(standing["awards"]) for standing in json.loads(archived["standings"])
    )
    assert {award["award"] for award in archived["awards"]} == {
        "season_champion",
        "goal_achieved",
    }
    assert sum(award["award"] == "season_champion" for award in archived["awards"]) == 1
    with game.transaction() as db:
        award_count = db.execute(
            "SELECT count(*) FROM season_awards WHERE season_id=?", (archived["id"],)
        ).fetchone()[0]
        assert award_count == len(archived["awards"])
        game.advance(db, clock[0])
        assert (
            db.execute(
                "SELECT count(*) FROM season_awards WHERE season_id=?", (archived["id"],)
            ).fetchone()[0]
            == award_count
        )
        prestige_count = {
            str(row["user_id"]): int(row["count"])
            for row in db.execute(
                "SELECT user_id, count(*) AS count FROM prestige_records GROUP BY user_id"
            )
        }
        expected_prestige_count = {}
        for standing in json.loads(archived["standings"]):
            earned = int("season_champion" in standing["awards"])
            earned += int("goal_achieved" in standing["awards"])
            if earned:
                expected_prestige_count[standing["id"]] = earned
        assert prestige_count == expected_prestige_count
        game.advance(db, clock[0])
        assert {
            str(row["user_id"]): int(row["count"])
            for row in db.execute(
                "SELECT user_id, count(*) AS count FROM prestige_records GROUP BY user_id"
            )
        } == prestige_count
        with pytest.raises(Exception, match="season awards are immutable"):
            db.execute("UPDATE season_awards SET score=0 WHERE season_id=?", (archived["id"],))
    with game.transaction() as db:
        snapshot = db.execute(
            "SELECT snapshot FROM season_rules WHERE season_id=?", (archived["id"],)
        ).fetchone()[0]
        with pytest.raises(Exception, match="season rules are immutable"):
            db.execute("UPDATE season_rules SET snapshot='{}' WHERE season_id=?", (archived["id"],))
    assert snapshot == RULES_SNAPSHOT


def test_existing_season_gets_explicitly_labeled_rules_baseline(universe):
    game, _, clock = universe
    season_id = identity()
    with game.transaction() as db:
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings) VALUES (?,?,?,?,1,?)",
            (season_id, "Altbestand", clock[0] - 200, clock[0] - 100, "[]"),
        )
    Game(game.path)
    with game.transaction() as db:
        rules = db.execute("SELECT * FROM season_rules WHERE season_id=?", (season_id,)).fetchone()
    assert rules["version"] == REGISTRY["version"]
    assert rules["digest"] == RULES_DIGEST
    assert rules["source"] == "legacy_backfill"


def test_moderation_ownership_and_immutable_audit(universe):
    game, users, _ = universe
    with pytest.raises(RuleError):
        command(universe, 0, "admin_ban", {"key": users[1], "value": 1})
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='moderator' WHERE user_id=?", (users[0],))
    command(universe, 0, "admin_mute", {"key": users[1], "minutes": 60})
    with pytest.raises(RuleError):
        command(universe, 1, "message", {"channel": "world", "body": "Spamming"})
    with pytest.raises(RuleError):
        command(universe, 0, "admin_flag", {"key": "pvp", "value": "false"})
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM audit")


def test_chat_message_reports_and_mute_appeals_are_private_and_audited(universe):
    game, users, clock = universe
    command(universe, 1, "message", {"channel": "world", "body": "Bitte bleib sachlich."})
    world_message = next(
        message for message in state(universe, 0)["messages"] if message["sender"] == users[1]
    )
    command(
        universe,
        1,
        "message",
        {"channel": "private", "name": "Charlie", "body": "Private Nachricht."},
    )
    private_message = next(
        message
        for message in state(universe, 1)["messages"]
        if message["channel"] == "private" and message["sender"] == users[1]
    )
    with pytest.raises(RuleError, match="nicht melden"):
        command(
            universe,
            0,
            "message_report",
            {"key": private_message["id"], "body": "Nicht mein Postfach."},
        )

    command(
        universe,
        0,
        "message_report",
        {"key": world_message["id"], "body": "Bitte durch die Moderation prüfen."},
    )
    with pytest.raises(RuleError, match="bereits gemeldet"):
        command(
            universe,
            0,
            "message_report",
            {"key": world_message["id"], "body": "Doppelte Meldung."},
        )
    assert state(universe, 0)["moderation_cases"][0]["case_type"] == "message_report"
    assert state(universe, 1)["moderation_cases"] == []

    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='moderator' WHERE user_id=?", (users[2],))
    admin = state(universe, 2)["administration"]
    report = next(item for item in admin["cases"] if item["case_type"] == "message_report")
    command(
        universe,
        2,
        "admin_case_resolve",
        {"key": report["id"], "value": "hide_message"},
    )
    with game.transaction() as db:
        assert (
            db.execute("SELECT hidden FROM messages WHERE id=?", (world_message["id"],)).fetchone()[
                0
            ]
            == 1
        )
        row = db.execute(
            "SELECT status,resolution,resolver_id FROM moderation_cases WHERE id=?",
            (report["id"],),
        ).fetchone()
        assert (row["status"], row["resolution"], row["resolver_id"]) == (
            "resolved",
            "hide_message",
            users[2],
        )

    command(universe, 2, "admin_mute", {"key": users[1], "minutes": 60})
    command(
        universe,
        1,
        "mute_appeal",
        {"body": "Die Stummschaltung wurde irrtümlich verhängt."},
    )
    with pytest.raises(RuleError, match="bereits ein Einspruch"):
        command(universe, 1, "mute_appeal", {"body": "Noch ein Einspruch."})
    appeal = next(
        item
        for item in state(universe, 2)["administration"]["cases"]
        if item["case_type"] == "mute_appeal"
    )
    command(
        universe,
        2,
        "admin_case_resolve",
        {"key": appeal["id"], "value": "lift_mute"},
    )
    assert int(state(universe, 1)["profile"]["muted_until"]) <= clock[0]
    assert any(item["resolution"] == "lift_mute" for item in state(universe, 1)["moderation_cases"])
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='admin_case_resolve' "
                "AND target=?",
                (users[2], appeal["id"]),
            ).fetchone()[0]
            == 2
        )


def test_admin_user_and_failure_pages_are_bounded_stable_and_cursor_checked(universe):
    game, users, _ = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        for index, created in enumerate((10, 20, 30)):
            db.execute(
                "INSERT INTO audit(id,actor,action,target,details,created) VALUES (?,?,?,?,?,?)",
                (f"admin-audit-{index}", users[0], "test", f"target-{index}", "{}", created),
            )
        for index, created in enumerate((10, 20, 30)):
            db.execute(
                "INSERT INTO job_failures(id,user_id,job_id,attempts,error,created) "
                "VALUES (?,?,?,?,?,?)",
                (f"admin-page-{index}", users[0], f"job-{index}", index + 1, "failed", created),
            )
        first_users, users_have_more = game.systems.admin_user_page(db, page_size=1)
        second_users, users_have_more = game.systems.admin_user_page(
            db, str(first_users[-1]["id"]), page_size=1
        )
        assert len(first_users) == len(second_users) == 1
        assert users_have_more is True
        assert first_users[0]["id"] != second_users[0]["id"]
        third_users, users_have_more = game.systems.admin_user_page(
            db, str(second_users[-1]["id"]), page_size=1
        )
        assert third_users[0]["id"] not in {first_users[0]["id"], second_users[0]["id"]}
        assert users_have_more is False
        first_failures, failures_have_more = game.systems.admin_failure_page(db, page_size=1)
        second_failures, failures_have_more = game.systems.admin_failure_page(
            db, str(first_failures[-1]["id"]), page_size=1
        )
        assert first_failures[0]["created"] == 30
        assert second_failures[0]["created"] == 20
        assert failures_have_more is True
        third_failures, failures_have_more = game.systems.admin_failure_page(
            db, str(second_failures[-1]["id"]), page_size=1
        )
        assert third_failures[0]["created"] == 10
        assert failures_have_more is False
        first_audit, audit_has_more = game.systems.admin_audit_page(db, page_size=1)
        second_audit, audit_has_more = game.systems.admin_audit_page(
            db, str(first_audit[-1]["id"]), page_size=1
        )
        third_audit, audit_has_more = game.systems.admin_audit_page(
            db, str(second_audit[-1]["id"]), page_size=1
        )
        assert [entry["id"] for entry in first_audit + second_audit + third_audit] == [
            "admin-audit-2",
            "admin-audit-1",
            "admin-audit-0",
        ]
        assert audit_has_more is False
        with pytest.raises(RuleError, match="Spieler-Cursor"):
            game.systems.admin_user_page(db, "unknown-user")
        with pytest.raises(RuleError, match="Auftragsfehler-Cursor"):
            game.systems.admin_failure_page(db, "unknown-failure")
        with pytest.raises(RuleError, match="Audit-Cursor"):
            game.systems.admin_audit_page(db, "unknown-audit")


def test_social_pages_are_bounded_stable_and_owner_scoped_on_each_database(universe):
    game, users, _ = universe
    with game.transaction() as db:
        a, b = sorted((users[0], users[1]))
        db.execute(
            "INSERT INTO friendships(a,b,requested_by,status,created,updated) VALUES (?,?,?,'accepted',10,10)",
            (a, b, users[0]),
        )
        a, b = sorted((users[0], users[2]))
        db.execute(
            "INSERT INTO friendships(a,b,requested_by,status,created,updated) VALUES (?,?,?,'accepted',20,20)",
            (a, b, users[0]),
        )
        db.execute(
            "INSERT INTO player_blocks(blocker,blocked,created) VALUES (?,?,?)",
            (users[0], users[1], 10),
        )
        db.execute(
            "INSERT INTO player_blocks(blocker,blocked,created) VALUES (?,?,?)",
            (users[0], users[2], 20),
        )
        first, has_more = game.systems.social_page(db, users[0], "friends", page_size=1)
        second, has_more = game.systems.social_page(
            db, users[0], "friends", str(first[-1]["id"]), page_size=1
        )
        assert len(first) == len(second) == 1
        assert first[0]["name"] == "Bravo"
        assert second[0]["name"] == "Charlie"
        assert has_more is False
        blocked, has_more = game.systems.social_page(db, users[0], "blocked", page_size=1)
        assert blocked[0]["name"] == "Bravo"
        assert has_more is True
        with pytest.raises(RuleError, match="Kontaktlisten-Cursor"):
            game.systems.social_page(db, users[1], "friends", str(first[0]["id"]))
        with pytest.raises(RuleError, match="Unbekannte Kontaktliste"):
            game.systems.social_page(db, users[0], "unknown")


def test_private_message_visibility(universe):
    command(
        universe,
        0,
        "message",
        {"channel": "private", "name": "Bravo", "body": "Persönliche Nachricht"},
    )
    assert len(state(universe, 0)["messages"]) == 1
    assert len(state(universe, 1)["messages"]) == 1
    assert not state(universe, 2)["messages"]


def test_message_history_pages_are_channel_scoped_on_each_database(universe):
    game, users, clock = universe
    with game.transaction() as db:
        world_id = int(game.read(db, users[0])["world_id"])
        for index in range(55):
            db.execute(
                "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
                "VALUES (?,?, 'world',NULL,?,?,0,?)",
                (
                    f"page-world-{index:03}",
                    users[1],
                    f"world {index}",
                    clock[0] + index,
                    world_id,
                ),
            )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('page-private-in',?,'private',?,'incoming',?,0,?)",
            (users[1], users[0], clock[0] + 60, world_id),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('page-private-out',?,'private',?,'outgoing',?,0,?)",
            (users[0], users[1], clock[0] + 61, world_id),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('page-private-other',?,'private',?,'foreign',?,0,?)",
            (users[1], users[2], clock[0] + 62, world_id),
        )
        first, has_more = game.systems.message_page(db, users[0], world_id, "", "world")
        assert len(first) == 50 and has_more
        older, has_more = game.systems.message_page(
            db, users[0], world_id, "", "world", str(first[-1]["id"])
        )
        assert len(older) == 5 and not has_more
        assert {row["id"] for row in first}.isdisjoint(row["id"] for row in older)
        private, has_more = game.systems.message_page(db, users[0], world_id, "", "private")
        assert {row["id"] for row in private} == {"page-private-in", "page-private-out"}
        assert not has_more


def test_ranking_pages_keep_score_order_and_reject_unknown_cursors(universe):
    game, _users, _clock = universe
    with game.transaction() as db:
        for index in range(48):
            user_id = identity()
            name = f"RankPilot{index:02}"
            db.execute("INSERT INTO users VALUES (?,?,?)", (user_id, name, "unused"))
            game.create(db, user_id, name)
        expected = game.ranking_for_world(db, 1)
        first, offset, has_more = game.ranking_page(db, 1)
        assert offset == 0 and has_more
        assert [entry["id"] for entry in first] == [entry["id"] for entry in expected[:50]]
        second, offset, has_more = game.ranking_page(db, 1, first[-1]["id"])
        assert offset == 50 and not has_more
        assert [entry["id"] for entry in second] == [entry["id"] for entry in expected[50:]]
        with pytest.raises(RuleError, match="Ranglisteneintrag nicht gefunden"):
            game.ranking_page(db, 1, "unknown-ranking-cursor")


def test_alliance_directory_pages_are_stable_and_bounded_on_each_database(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        for index in range(51):
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) "
                "VALUES (?,?,?,?,?,?)",
                (
                    f"directory-{index:03}",
                    f"D{index:03}",
                    f"Directory alliance {index}",
                    "",
                    users[0],
                    index,
                ),
            )
        first, has_more = game.systems.alliance_directory_page(db)
        assert len(first) == 50 and has_more
        assert [row["id"] for row in first] == [f"directory-{i:03}" for i in range(50)]
        second, has_more = game.systems.alliance_directory_page(db, str(first[-1]["id"]))
        assert [row["id"] for row in second] == ["directory-050"]
        assert not has_more
        with pytest.raises(RuleError, match="Ältere Allianz nicht gefunden"):
            game.systems.alliance_directory_page(db, "unknown-alliance-cursor")


def test_alliance_member_pages_are_stable_bounded_and_current_alliance_scoped(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "ROSTER", "name": "Roster Keepers"})
    with game.transaction() as db:
        alliance_id = str(
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (users[0],)).fetchone()[0]
        )
        for index in range(50):
            user_id = f"roster-member-{index:03}"
            name = f"Member {index:03}"
            db.execute("INSERT INTO users VALUES (?,?,?)", (user_id, name, "unused"))
            db.execute("INSERT INTO members VALUES (?,?,?)", (user_id, alliance_id, "member"))
        first, has_more = game.systems.alliance_member_page(db, alliance_id)
        assert len(first) == 50 and has_more
        assert first[0]["user_id"] == users[0]
        assert [entry["name"] for entry in first[1:]] == [f"Member {i:03}" for i in range(49)]
        second, has_more = game.systems.alliance_member_page(
            db, alliance_id, str(first[-1]["user_id"])
        )
        assert [entry["name"] for entry in second] == ["Member 049"]
        assert not has_more
        with pytest.raises(RuleError, match="Allianzmitglied nicht gefunden"):
            game.systems.alliance_member_page(db, alliance_id, "unknown-member")
        with pytest.raises(RuleError, match="Allianzmitglied nicht gefunden"):
            game.systems.alliance_member_page(db, "another-alliance", str(first[0]["user_id"]))
    current = state(universe, 0)
    assert len(current["members"]) == 50
    assert current["members_has_more"] is True


def test_alliance_application_pages_are_bounded_and_scope_cursors_to_the_owner(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "APPLY", "name": "Application Keepers"})
    with game.transaction() as db:
        alliance_id = str(
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (users[0],)).fetchone()[0]
        )
        for index in range(51):
            applicant_id = f"application-user-{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (applicant_id, f"Applicant {index:03}", "unused"),
            )
            db.execute(
                "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?)",
                (f"application-{index:03}", alliance_id, applicant_id, index),
            )
        incoming, has_more = game.systems.alliance_application_page(
            db, users[0], "incoming", alliance_id
        )
        assert len(incoming) == 50 and has_more
        assert incoming[0]["id"] == "application-050"
        second, has_more = game.systems.alliance_application_page(
            db, users[0], "incoming", alliance_id, str(incoming[-1]["id"])
        )
        assert [entry["id"] for entry in second] == ["application-000"]
        assert not has_more
        with pytest.raises(RuleError, match="Bewerbung nicht gefunden"):
            game.systems.alliance_application_page(db, users[0], "incoming", alliance_id, "foreign")
        for index in range(51):
            target_alliance = f"outgoing-alliance-{index:03}"
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) "
                "VALUES (?,?,?,?,?,?)",
                (target_alliance, f"O{index:03}", f"Outgoing {index:03}", "", users[2], index),
            )
            db.execute(
                "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?)",
                (f"outgoing-application-{index:03}", target_alliance, users[1], index),
            )
        outgoing, has_more = game.systems.alliance_application_page(db, users[1], "outgoing")
        assert len(outgoing) == 50 and has_more
        assert outgoing[0]["id"] == "outgoing-application-050"
        older, has_more = game.systems.alliance_application_page(
            db, users[1], "outgoing", before_id=str(outgoing[-1]["id"])
        )
        assert [entry["id"] for entry in older] == ["outgoing-application-000"]
        assert not has_more
    current = state(universe, 0)
    assert len(current["alliance_incoming_applications"]) == 50
    assert current["alliance_incoming_applications_has_more"] is True
    applicant_state = state(universe, 1)
    assert len(applicant_state["alliance_applications"]) == 50
    assert applicant_state["alliance_applications_has_more"] is True


def test_alliance_invitation_pages_are_bounded_and_scope_cursors_to_each_direction(universe):
    game, users, _clock = universe
    command(universe, 0, "alliance_create", {"tag": "INVITE", "name": "Invite Keepers"})
    with game.transaction() as db:
        alliance_id = str(
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (users[0],)).fetchone()[0]
        )
        for index in range(51):
            target_alliance = f"incoming-alliance-{index:03}"
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) VALUES (?,?,?,?,?,?)",
                (target_alliance, f"I{index:03}", f"Incoming {index:03}", "", users[2], index),
            )
            db.execute(
                "INSERT INTO invites VALUES (?,?,?)",
                (f"incoming-invite-{index:03}", target_alliance, users[1]),
            )
            target_user = f"invitee-{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)", (target_user, f"Invitee {index:03}", "unused")
            )
            db.execute(
                "INSERT INTO invites VALUES (?,?,?)",
                (f"outgoing-invite-{index:03}", alliance_id, target_user),
            )
        incoming, has_more = game.systems.alliance_invitation_page(db, users[1], "incoming")
        assert len(incoming) == 50 and has_more
        older, has_more = game.systems.alliance_invitation_page(
            db, users[1], "incoming", before_id=str(incoming[-1]["id"])
        )
        assert [entry["id"] for entry in older] == ["incoming-invite-050"]
        assert not has_more
        outgoing, has_more = game.systems.alliance_invitation_page(
            db, users[0], "outgoing", alliance_id
        )
        assert len(outgoing) == 50 and has_more
        assert [entry["name"] for entry in outgoing[:2]] == ["Invitee 000", "Invitee 001"]
        final, has_more = game.systems.alliance_invitation_page(
            db, users[0], "outgoing", alliance_id, str(outgoing[-1]["id"])
        )
        assert [entry["name"] for entry in final] == ["Invitee 050"]
        assert not has_more
        with pytest.raises(RuleError, match="Einladung nicht gefunden"):
            game.systems.alliance_invitation_page(
                db, users[1], "incoming", before_id="outgoing-invite-050"
            )
    invited_state = state(universe, 1)
    assert len(invited_state["invites"]) == 50
    assert invited_state["invites_has_more"] is True
    manager_state = state(universe, 0)
    assert len(manager_state["alliance_outgoing_invites"]) == 50
    assert manager_state["alliance_outgoing_invites_has_more"] is True


def test_message_body_accepts_2000_characters_and_rejects_2001(universe):
    accepted = "x" * 2000
    command(universe, 0, "message", {"channel": "private", "name": "Bravo", "body": accepted})
    assert state(universe, 1)["messages"][0]["body"] == accepted
    with pytest.raises(RuleError, match="2000"):
        command(universe, 0, "message", {"channel": "world", "body": "x" * 2001})


def test_faction_and_production_bonus(universe):
    game, users, clock = universe
    with game.transaction() as db:
        defender = game.read(db, users[1])
    command(universe, 0, "faction", {"key": "pioneers"})
    clock[0] += 10
    assert state(universe, 0)["resources"][0] == 1244
    assert (
        state(universe, 1)["resources"][0]
        == 1200 + 40 * PRODUCTION_PERCENT[defender["terrain"]][0] // 100
    )
    with pytest.raises(RuleError):
        command(universe, 0, "faction", {"key": "wardens"})


def test_neutral_trade_pays_fifty_or_sixty_percent_after_syndicate_choice(universe):
    game, users, _clock = universe
    ordinary = command(universe, 0, "trade", {"source": 0, "dest": 1, "amount": 100})
    assert ordinary["resources"][:2] == [1100, 1050]
    command(universe, 1, "faction", {"key": "syndicate"})
    syndicate = command(universe, 1, "trade", {"source": 0, "dest": 1, "amount": 100})
    assert syndicate["resources"][:2] == [1100, 1060]
    with pytest.raises(RuleError):
        command(universe, 1, "faction", {"key": "pioneers"})
    with game.transaction() as db:
        profile = db.execute(
            "SELECT faction FROM world_players WHERE user_id=? AND world_id=1", (users[1],)
        ).fetchone()
        assert profile["faction"] == "syndicate"


def test_build_cancellation_refunds_only_unspent_time_and_is_idempotent(universe):
    game, users, clock = universe
    with game.transaction() as db:
        state_before = game.read(db, users[0])
        state_before["resources"] = [20000, 20000, 20000]
        state_before["buildings"]["storage"] = 10
        game.save(db, state_before)

    started = command(universe, 0, "build", {"key": "wall"})
    queued = started["jobs"][0]
    assert queued["duration"] == 7
    assert queued["costs"] == [80, 160, 70]
    clock[0] += 3
    with game.transaction() as db:
        game.advance(db, clock[0])
        before_cancel = game.read(db, users[0])
        before = list(before_cancel["resources"])
    token = identity()
    cancelled = command(universe, 0, "cancel_job", {"key": queued["id"]}, token)
    refund = [45, 91, 40]  # floor(cost × 4 seconds remaining / 7 total)
    cap = 22000
    expected_resources = [min(cap, amount + refund[i]) for i, amount in enumerate(before)]
    expected_reserve = [max(0, amount + refund[i] - cap) for i, amount in enumerate(before)]
    assert cancelled["resources"] == expected_resources
    assert cancelled["reserve"] == expected_reserve
    assert all(job["id"] != queued["id"] for job in cancelled["jobs"])
    assert cancelled["reports"][0]["title"] == "Auftrag abgebrochen"
    assert "Erstattung Holz 45, Stein 91, Erz 40" in cancelled["reports"][0]["body"]
    assert (
        command(universe, 0, "cancel_job", {"key": queued["id"]}, token)["resources"]
        == expected_resources
    )
    with game.transaction() as db:
        assert (
            db.execute("SELECT count(*) FROM ledger WHERE action='cancel_job'").fetchone()[0] == 1
        )
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='job_cancelled'",
            (users[0],),
        ).fetchone()
        assert json.loads(audit["details"]) == {
            "job_kind": "build",
            "job_key": "wall",
            "refund": refund,
            "duration": 7,
            "remaining": 4,
            "was_queued": False,
        }


def test_legacy_build_jobs_can_be_cancelled_and_missions_cannot(universe):
    game, users, clock = universe
    started = command(universe, 0, "build", {"key": "wall"})
    queued = started["jobs"][0]
    with game.transaction() as db:
        state_before = game.read(db, users[0])
        state_before["jobs"][0].pop("duration")
        state_before["jobs"][0].pop("costs")
        state_before["jobs"][0].pop("started_at")
        game.save(db, state_before)
    clock[0] += 2
    assert command(universe, 0, "cancel_job", {"key": queued["id"]})["jobs"] == []

    raid = command(
        universe,
        0,
        "raid",
        {"key": state(universe, 0)["world"][0]["id"], "army": {"ranger": 1}},
    )
    with pytest.raises(RuleError, match="kann nicht abgebrochen"):
        command(universe, 0, "cancel_job", {"key": raid["jobs"][0]["id"]})


def test_neutral_battle_simulation_is_exact_fog_scoped_and_read_only(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        posts = game.world_outposts(db, 1)
        target = posts[0]
        target.update(x=min(63, colony["x"] + 1), y=colony["y"], tier=1, stock=[120, 80, 40])
        target["owner"] = None
        target["units"] = {"ranger": 2}
        game.save_world_outposts(db, 1, posts)
        before_colony = db.execute(
            "SELECT state FROM colonies WHERE colony_id=?", (colony["colony_id"],)
        ).fetchone()[0]
        before_posts = [
            row[0]
            for row in db.execute(
                "SELECT state FROM world_outposts WHERE world_id=1 ORDER BY sort_order,target_id"
            )
        ]
        before_audit = db.execute("SELECT count(*) FROM audit").fetchone()[0]
        before_ledger = db.execute("SELECT count(*) FROM ledger").fetchone()[0]
        result = game.simulate_outpost_battle(db, colony, target["id"], {"ranger": 4})
        assert result["power"] == 4 * 12 * (100 + 15 * colony["tech"]["tactics"]) // 100
        assert result["defense"] > 0
        assert result["attacker_losses"] == 4 - sum(result["attacker_survivors"].values())
        assert len(result["loot"]) == 3
        assert (
            db.execute(
                "SELECT state FROM colonies WHERE colony_id=?", (colony["colony_id"],)
            ).fetchone()[0]
            == before_colony
        )
        assert [
            row[0]
            for row in db.execute(
                "SELECT state FROM world_outposts WHERE world_id=1 ORDER BY sort_order,target_id"
            )
        ] == before_posts
        assert db.execute("SELECT count(*) FROM audit").fetchone()[0] == before_audit
        assert db.execute("SELECT count(*) FROM ledger").fetchone()[0] == before_ledger

        hidden = posts[1]
        corners = [(0, 0), (0, 63), (63, 0), (63, 63)]
        hidden_x, hidden_y = max(
            corners, key=lambda point: math.hypot(point[0] - colony["x"], point[1] - colony["y"])
        )
        hidden.update(x=hidden_x, y=hidden_y, owner=None)
        game.save_world_outposts(db, 1, posts)
        with pytest.raises(RuleError, match="nicht bekannt"):
            game.simulate_outpost_battle(db, colony, hidden["id"], {"ranger": 1})
        with pytest.raises(RuleError, match="Gefechtsprobe"):
            game.simulate_outpost_battle(db, colony, target["id"], {"ranger": 999})


def test_combat4_catalog_and_logistics_convoy_work_in_neutral_battle_projection(universe):
    game, users, _ = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        colony = game.read(db, users[0])
        colony["units"].update(scout=2, logistics_convoy=1)
        posts = game.world_outposts(db, 1)
        target = posts[0]
        target.update(
            x=min(63, colony["x"] + 1),
            y=colony["y"],
            tier=1,
            owner=None,
            stock=[120, 80, 40],
            units={"ranger": 2},
        )
        game.save_world_outposts(db, 1, posts)

        projection = game.simulate_outpost_battle(
            db, colony, target["id"], {"scout": 2, "logistics_convoy": 1}
        )
        assert set(projection["attacker_survivors"]) <= {"scout", "logistics_convoy"}
        assert game.army_transport_capacity(db, 1, {"scout": 2, "logistics_convoy": 1}, 0) == int(
            game.unit_catalog_for_world(db, 1)["logistics_convoy"]["cargo"]
        )


def test_combat4_repair_wreck_ledger_and_refund_work_in_both_databases(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        state = game.read(db, users[0])
        state["buildings"]["barracks"] = 1
        game.save(db, state)
        wreck = game.record_terra_unit_wrecks(
            db,
            mission_id="postgres-sqlite-recovery-contract",
            owner_id=users[0],
            colony_id=state["colony_id"],
            world_id=1,
            losses={"ranger": 4},
            combat_version="FUR-3-TERRA-COMBAT-4",
            at=clock[0],
        )[0]
    before = list(state["resources"])
    payload = {
        "wreck_id": wreck["id"],
        "count": 1,
        "world_id": 1,
        "colony_id": state["colony_id"],
    }
    queued = command(universe, 0, "terra_repair_units", payload)
    repair = next(job for job in queued["jobs"] if job["kind"] == "terra_repair")
    cancelled = command(universe, 0, "cancel_job", {"key": repair["id"]})
    assert not any(job["kind"] == "terra_repair" for job in cancelled["jobs"])
    with game.transaction() as db:
        restored = db.execute(
            "SELECT amount FROM terra_unit_wrecks WHERE id=?", (wreck["id"],)
        ).fetchone()
        current = game.read(db, users[0])
        assert restored[0] == 1
        assert current["resources"] == before


def test_combat4_defense_build_repair_and_idempotency_are_colony_scoped(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        state = game.read(db, users[0])
        state["buildings"].update(hq=6, barracks=2)
        state["tech"].update(weapons=1, shields=1)
        state["resources"] = [10000, 10000, 10000]
        game.save(db, state)
        other = game.read(db, users[1])
        other["buildings"].update(hq=6, barracks=2)
        other["tech"].update(weapons=1, shields=1)
        other["resources"] = [10000, 10000, 10000]
        game.save(db, other)

    payload = {
        "key": "kinetic_turret",
        "world_id": 1,
        "colony_id": state["colony_id"],
    }
    build_token = identity()
    built = command(universe, 0, "terra_defense_build", payload, token=build_token)
    repeated = command(universe, 0, "terra_defense_build", payload, token=build_token)
    assert built["terra_defense"]["stacks"]["kinetic_turret"] == [100]
    assert repeated["terra_defense"]["stacks"]["kinetic_turret"] == [100]
    assert built["terra_defense"]["slot_usage"] == 1
    assert built["terra_defense"]["stack_rules_version"] == terra_defense.VERSION
    assert built["terra_defense"]["stack_rules_digest"] == terra_defense.DIGEST

    with game.transaction() as db:
        damaged = game.read(db, users[0])
        damaged["terra_defense_stacks"]["kinetic_turret"][0] = 50
        game.save(db, damaged)
    repaired = command(universe, 0, "terra_defense_repair", payload)
    assert repaired["terra_defense"]["stacks"]["kinetic_turret"] == [100]

    with pytest.raises(RuleError, match="aktiven COMBAT-4"):
        command(universe, 0, "terra_defense_build", {**payload, "colony_id": other["colony_id"]})


@pytest.mark.parametrize(
    "unit",
    sorted(
        set(terra_combat.rules_for("FUR-3-TERRA-COMBAT-4")["units"])
        - set(UNITS)
        - {"outpost_fortification"}
    ),
)
def test_combat4_unapproved_roster_training_stays_locked_without_side_effects(universe, unit):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        state = game.read(db, users[0])
        state["resources"] = [100_000, 100_000, 100_000]
        game.save(db, state)
        before = game.read(db, users[0])

    with pytest.raises(RuleError, match="nicht zur Ausbildung freigegeben"):
        command(universe, 0, "train", {"key": unit, "count": 1})

    with game.transaction() as db:
        after = game.read(db, users[0])
    assert after["resources"] == before["resources"]
    assert after["units"] == before["units"]
    assert after["jobs"] == before["jobs"]


def test_combat4_defense_repair_is_blocked_by_incoming_enemy_attack(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        state = game.read(db, users[0])
        state["buildings"].update(hq=3, barracks=2)
        state["tech"]["weapons"] = 1
        state["resources"] = [10000, 10000, 10000]
        state["terra_defense_stacks"] = {"kinetic_turret": [50]}
        state["terra_defense_rules_version"] = terra_defense.VERSION
        state["terra_defense_rules_digest"] = terra_defense.DIGEST
        game.save(db, state)
        attacker = game.read(db, users[1])
        attacker["jobs"].append(
            {"id": identity(), "kind": "attack", "key": users[0], "due": clock[0] + 60}
        )
        game.save(db, attacker)
    with pytest.raises(RuleError, match="feindlicher Anmärsche"):
        command(
            universe,
            0,
            "terra_defense_repair",
            {"key": "kinetic_turret", "world_id": 1, "colony_id": state["colony_id"]},
        )


def test_combat4_defense_stacks_reject_unknown_pinned_rules(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        state = game.read(db, users[0])
        state["buildings"].update(hq=3, barracks=2)
        state["tech"]["weapons"] = 1
        state["resources"] = [10000, 10000, 10000]
        state["terra_defense_stacks"] = {"kinetic_turret": [50]}
        state["terra_defense_rules_version"] = "FUR-3-TERRA-DEFENSE-0"
        state["terra_defense_rules_digest"] = "sha256:unknown"
        game.save(db, state)
    with pytest.raises(RuleError, match="unbekannte Regeln"):
        command(
            universe,
            0,
            "terra_defense_repair",
            {"key": "kinetic_turret", "world_id": 1, "colony_id": state["colony_id"]},
        )


def test_fur3_player_battle_damages_and_persists_defense_stacks_in_replay(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        attacker = game.read(db, users[0])
        attacker["units"]["artillery_platform"] = 40
        attacker["resources"][2] = 10000
        game.save(db, attacker)
        defender = game.read(db, users[1])
        defender["units"]["ranger"] = 4
        defender["buildings"]["wall"] = 0
        defender["terra_defense_stacks"] = {
            "kinetic_turret": [100],
            "aegis_emitter": [],
            "proximity_mines": [],
            "command_bunker": [],
        }
        defender["terra_defense_rules_version"] = terra_defense.VERSION
        defender["terra_defense_rules_digest"] = terra_defense.DIGEST
        game.save(db, defender)

    sent = command(universe, 0, "attack", {"key": users[1], "army": {"artillery_platform": 40}})
    mission = next(job for job in sent["jobs"] if job["kind"] == "attack")
    clock[0] = int(mission["due"])
    attacker_after = state(universe, 0)
    defender_after = state(universe, 1)
    stored = defender_after["terra_defense_stacks"]["kinetic_turret"][0]
    assert 0 <= stored < 100
    defender_report = next(report for report in defender_after["reports"] if report.get("combat"))
    defense_result = defender_report["combat"]["terra_defense"]
    assert defense_result["digest"] == terra_defense.DIGEST
    assert defense_result["remaining_stacks"]["kinetic_turret"][0] == stored
    with game.transaction() as db:
        replay_row = db.execute(
            "SELECT replay FROM terra_combat_missions WHERE mission_id=?", (mission["id"],)
        ).fetchone()
        replay = json.loads(replay_row["replay"])
        colony_state = json.loads(
            db.execute(
                "SELECT state FROM colonies WHERE colony_id=?", (defender["colony_id"],)
            ).fetchone()[0]
        )
        assert replay["terra_defense"] == defense_result
        assert colony_state["terra_defense_stacks"]["kinetic_turret"][0] == stored
    assert not any(job["kind"] == "attack" for job in attacker_after["jobs"])


def test_player_battle_simulation_requires_fresh_level_two_intel_and_is_read_only(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        attacker = game.read(db, users[0])
        intel_data = {
            "hq": 3,
            "buildings": {"hq": 3},
            "defense": 275,
            "garrison": 5,
            "units": {"ranger": 2, "sentinel": 3, "mech": 0},
        }
        db.execute(
            "INSERT INTO player_intel(observer_id,target_id,level,observed_at,expires_at,data,world_id) "
            "VALUES (?,?,2,?,?,?,1)",
            (users[0], users[1], clock[0] - 120, clock[0] + 3600, json.dumps(intel_data)),
        )
        before_states = db.execute(
            "SELECT user_id,state FROM colonies WHERE user_id IN (?,?) ORDER BY user_id",
            (users[0], users[1]),
        ).fetchall()
        before_audit = db.execute("SELECT count(*) FROM audit").fetchone()[0]
        before_ledger = db.execute("SELECT count(*) FROM ledger").fetchone()[0]

        result = game.simulate_outpost_battle(db, attacker, users[1], {"ranger": 4})

        assert result["defense"] == intel_data["defense"]
        assert set(result["defender_survivors"]) == set(intel_data["units"])
        assert result["loot"] is None
        assert "resources" not in result
        assert (
            db.execute(
                "SELECT user_id,state FROM colonies WHERE user_id IN (?,?) ORDER BY user_id",
                (users[0], users[1]),
            ).fetchall()
            == before_states
        )
        assert db.execute("SELECT count(*) FROM audit").fetchone()[0] == before_audit
        assert db.execute("SELECT count(*) FROM ledger").fetchone()[0] == before_ledger


@pytest.mark.parametrize("level,expiry_offset", [(1, 3600), (2, -1)])
def test_player_battle_simulation_rejects_insufficient_or_expired_intel(
    universe, level, expiry_offset
):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        attacker = game.read(db, users[0])
        db.execute(
            "INSERT INTO player_intel(observer_id,target_id,level,observed_at,expires_at,data,world_id) "
            "VALUES (?,?,?,?,?,?,1)",
            (
                users[0],
                users[1],
                level,
                clock[0] - 3600,
                clock[0] + expiry_offset,
                json.dumps({"defense": 100, "units": {"ranger": 1}}),
            ),
        )
        with pytest.raises(RuleError, match="aktueller Aufklärungsbericht Stufe 2"):
            game.simulate_outpost_battle(db, attacker, users[1], {"ranger": 1})


def test_player_battle_simulation_unknown_target_does_not_create_profile(universe):
    game, users, _clock = universe
    unknown = "unknown-preview-target"
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        attacker = game.read(db, users[0])
        before = db.execute("SELECT count(*) FROM profiles").fetchone()[0]
        with pytest.raises(RuleError, match="kein aufklärbares Profil"):
            game.simulate_outpost_battle(db, attacker, unknown, {"ranger": 1})
        assert db.execute("SELECT count(*) FROM profiles").fetchone()[0] == before


def test_fur3_neutral_battle_simulation_is_reproducible_and_read_only(universe):
    game, users, _clock = universe
    from fur_empire import terra_combat

    with game.transaction() as db:
        colony = game.read(db, users[0])
        posts = game.world_outposts(db, 1)
        target = posts[0]
        target.update(
            x=min(63, colony["x"] + 1),
            y=colony["y"],
            tier=2,
            owner=None,
            stock=[600, 400, 200],
            units={"ranger": 4, "sentinel": 1},
        )
        game.save_world_outposts(db, 1, posts)
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=?,"
            "terra_retreat_threshold_percent=42 WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
            "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO UPDATE "
            "SET observed_at=excluded.observed_at",
            (users[0], 1, target["x"], target["y"], int(time.time())),
        )
        before_colony = db.execute(
            "SELECT state FROM colonies WHERE colony_id=?", (colony["colony_id"],)
        ).fetchone()[0]
        before_posts = db.execute(
            "SELECT target_id,state FROM world_outposts ORDER BY target_id"
        ).fetchall()
        before_counts = {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("audit", "ledger")
        }

        first = game.simulate_outpost_battle(db, colony, target["id"], {"ranger": 4})
        second = game.simulate_outpost_battle(db, colony, target["id"], {"ranger": 4})

        assert first == second
        assert first["deterministic"] is False
        assert first["rules_version"] == terra_combat.VERSION
        assert first["simulation"]["samples"] == terra_combat.SIMULATION_SAMPLES
        assert first["simulation"]["attacker_victory_percent"] >= 0
        assert len(first["simulation"]["loot"]) == 3
        assert "seed" not in first and "seed_commitment" not in first
        assert (
            db.execute(
                "SELECT state FROM colonies WHERE colony_id=?", (colony["colony_id"],)
            ).fetchone()[0]
            == before_colony
        )
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts ORDER BY target_id"
            ).fetchall()
        ] == [tuple(row) for row in before_posts]
        assert {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("audit", "ledger")
        } == before_counts


def test_fur3_scout_snapshot_drives_read_only_player_battle_simulation(universe):
    game, users, clock = universe
    from fur_empire import terra_combat

    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        defender = game.read(db, users[1])
        defender["units"].update(ranger=7, sentinel=2)
        defender["buildings"]["wall"] = 0
        defender["terra_defense_stacks"] = {
            "kinetic_turret": [100],
            "proximity_mines": [100],
        }
        defender["terra_defense_rules_version"] = terra_defense.VERSION
        defender["terra_defense_rules_digest"] = terra_defense.DIGEST
        game.save(db, defender)

    dispatched = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 3}})
    scout = next(job for job in dispatched["jobs"] if job["kind"] == "scout")
    clock[0] = int(scout["due"])
    arrived = state(universe, 0)
    intel = next(
        player["intel_report"] for player in arrived["players"] if player["id"] == users[1]
    )
    combat_snapshot = intel["data"]["terra_combat"]
    assert intel["level"] == 2
    assert combat_snapshot["rules_version"] == "FUR-3-TERRA-COMBAT-4"
    assert combat_snapshot["rules_digest"] == terra_combat.RULESET_DIGESTS["FUR-3-TERRA-COMBAT-4"]
    assert combat_snapshot["units"]["ranger"] == 7
    assert combat_snapshot["units"]["sentinel"] == 2
    assert combat_snapshot["armor_bonus"] == 0
    assert combat_snapshot["defender_structures"] == defender["terra_defense_stacks"]
    assert combat_snapshot["defense_rules_digest"] == terra_defense.DIGEST
    assert "resources" not in intel["data"]

    with game.transaction() as db:
        attacker = game.read(db, users[0])
        defender = game.read(db, users[1])
        defender["units"].update(mech=100, ranger=0, sentinel=0)
        defender["terra_defense_stacks"]["kinetic_turret"][0] = 0
        defender["terra_defense_stacks"]["proximity_mines"][0] = 0
        game.save(db, defender)
        before_states = db.execute(
            "SELECT user_id,state FROM colonies WHERE user_id IN (?,?) ORDER BY user_id",
            (users[0], users[1]),
        ).fetchall()
        before_counts = {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("audit", "ledger")
        }
        first = game.simulate_outpost_battle(db, attacker, users[1], {"ranger": 1})
        second = game.simulate_outpost_battle(db, attacker, users[1], {"ranger": 1})
        assert first == second
        assert first["deterministic"] is False
        assert first["simulation"]["samples"] == terra_combat.SIMULATION_SAMPLES
        assert first["terra_defense"]["initial_stacks"] == combat_snapshot["defender_structures"]
        assert first["simulation"]["terra_defense"]["digest"] == terra_defense.DIGEST
        assert 0 <= first["simulation"]["terra_defense"]["minefield_trigger_percent"] <= 100
        assert first["loot"] is None
        assert "resources" not in first
        assert (
            db.execute(
                "SELECT user_id,state FROM colonies WHERE user_id IN (?,?) ORDER BY user_id",
                (users[0], users[1]),
            ).fetchall()
            == before_states
        )
        assert {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("audit", "ledger")
        } == before_counts


def test_neutral_battle_report_records_unit_level_round_results(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["units"]["ranger"] = 5
        game.save(db, colony)
        posts = game.world_outposts(db, 1)
        target = posts[0]
        target.update(x=colony["x"] + 1, y=colony["y"], tier=1, owner=None)
        target["units"] = {"ranger": 2, "sentinel": 1, "mech": 0}
        game.save_world_outposts(db, 1, posts)
    command(universe, 0, "raid", {"key": target["id"], "army": {"ranger": 5}})
    clock[0] += 100
    result = state(universe, 0)
    report = next(item for item in result["reports"] if item.get("combat"))
    round_report = report["combat"]["rounds"][0]
    assert report["combat"]["rules_version"] == "FUR-2"
    assert round_report["attacker"]["sent"] == {"ranger": 5}
    assert round_report["attacker"]["losses"]["ranger"] == (
        round_report["attacker"]["sent"]["ranger"] - round_report["attacker"]["survivors"]["ranger"]
    )
    assert round_report["defender"]["sent"] == {"ranger": 2, "sentinel": 1, "mech": 0}
    assert round_report["defender"]["losses"]["sentinel"] == (
        round_report["defender"]["sent"]["sentinel"]
        - round_report["defender"]["survivors"]["sentinel"]
    )
    assert round_report["defender"]["losses"]["ranger"] == (
        round_report["defender"]["sent"]["ranger"] - round_report["defender"]["survivors"]["ranger"]
    )
    assert len(round_report["loot"]) == 3


def test_fur2_battle_resolver_composition_grid_is_deterministic_and_bounded():
    from fur_empire.game import UNITS, resolve_outpost_battle

    unit_types = tuple(UNITS)
    terrain_types = ("plain", "forest", "mountain", "pass")
    armies = [{unit: count} for unit in unit_types for count in (1, 2)]
    armies.extend(
        (
            {unit: 1 for unit in unit_types},
            {unit: 2 for unit in unit_types},
        )
    )
    scenarios = 0
    for army in armies:
        for defenders in armies:
            for tier in (1, 3, 8):
                for tactics in (0, 2, 4):
                    for terrain in terrain_types:
                        outcome = resolve_outpost_battle(army, defenders, tier, tactics, terrain)
                        assert outcome == resolve_outpost_battle(
                            army, defenders, tier, tactics, terrain
                        )
                        assert outcome["power"] >= 0
                        assert outcome["defense"] > 0
                        assert outcome["attacker_losses"] >= 0
                        assert all(
                            0 <= count <= army.get(unit, 0)
                            for unit, count in outcome["attacker_survivors"].items()
                        )
                        assert all(
                            0 <= count <= defenders.get(unit, 0)
                            for unit, count in outcome["defender_survivors"].items()
                        )
                        assert outcome["victory"] is (outcome["power"] > outcome["defense"])
                        if outcome["victory"]:
                            assert not any(outcome["defender_survivors"].values())
                        else:
                            assert not any(outcome["attacker_survivors"].values())
                        scenarios += 1
    assert scenarios == 14400


def test_each_fur2_unit_has_a_bounded_win_and_loss_counterexample():
    from fur_empire.game import UNITS, resolve_outpost_battle

    for unit in UNITS:
        favorable = resolve_outpost_battle({unit: 10}, {}, 1, 0, "plain")
        unfavorable = resolve_outpost_battle({unit: 1}, {}, 8, 0, "plain")
        assert favorable["victory"] is True, unit
        assert unfavorable["victory"] is False, unit
        assert favorable["power"] > favorable["defense"]
        assert unfavorable["power"] <= unfavorable["defense"]


@pytest.mark.parametrize(
    "mission_kind",
    ("raid", "attack", "scout", "transport", "colony_supply", "station", "expedition"),
)
def test_outbound_mission_recall_returns_force_and_reserved_cargo_once(universe, mission_kind):
    game, users, clock = universe
    fur3_recall = mission_kind == "raid"
    with game.transaction() as db:
        if fur3_recall:
            from fur_empire import terra_combat

            db.execute(
                "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
                (terra_combat.VERSION,),
            )
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        source = game.read(db, users[0])
        source["resources"] = [10000, 10000, 10000]
        if mission_kind == "colony_supply":
            source["goods_inventory"] = {"alloy": 50}
            source["item_inventory"] = {"repair_kit": 20}
        source["buildings"]["wood"] = 0
        source["buildings"]["stone"] = 0
        source["buildings"]["ore"] = 0
        if mission_kind == "colony_supply":
            source["buildings"]["hq"] = 3
        game.save(db, source)
        target = game.read(db, users[1])
        if mission_kind in ("attack", "scout", "transport"):
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO UPDATE "
                "SET observed_at=excluded.observed_at",
                (users[0], 1, target["x"], target["y"], clock[0]),
            )
        elif mission_kind == "station":
            posts = game.world_outposts(db, 1)
            posts[0]["owner"] = users[0]
            game.save_world_outposts(db, 1, posts)
        original_units = dict(source["units"])

    if mission_kind == "colony_supply":
        with game.transaction() as db:
            source = game.read(db, users[0])
            reachable = travel_times(db, (source["x"], source["y"]), 1)
            occupied = {(post["x"], post["y"]) for post in game.world_outposts(db, 1)} | {
                (int(row["x"]), int(row["y"]))
                for row in db.execute("SELECT x,y FROM colonies WHERE world_id=1")
            }
            sector = next(
                (x, y)
                for x, y in reachable
                if math.hypot(x - source["x"], y - source["y"]) >= 6 and (x, y) not in occupied
            )
            db.execute(
                "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
                "VALUES (?,?,?,?,?)",
                (users[0], 1, sector[0], sector[1], clock[0]),
            )
        command(universe, 0, "colonize", {"x": sector[0], "y": sector[1]})

    army = {"ranger": 2}
    if mission_kind == "raid":
        target_post = state(universe, 0)["world"][0]
        sent = command(universe, 0, "raid", {"key": target_post["id"], "army": army})
    elif mission_kind == "station":
        with game.transaction() as db:
            target_post = game.world_outposts(db, 1)[0]
        sent = command(universe, 0, "station", {"key": target_post["id"], "army": army})
    elif mission_kind == "expedition":
        target_post = next(post for post in state(universe, 0)["world"] if post["owner"] is None)
        sent = command(universe, 0, "expedition", {"key": target_post["id"], "army": army})
    elif mission_kind == "colony_supply":
        with game.transaction() as db:
            destination = db.execute(
                "SELECT colony_id FROM colonies WHERE user_id=? AND is_home=FALSE",
                (users[0],),
            ).fetchone()["colony_id"]
        sent = command(
            universe,
            0,
            "colony_supply",
            {
                "key": destination,
                "army": army,
                "resources": [60, 0, 0],
                "goods": {"alloy": 5},
                "items": {"repair_kit": 4},
            },
        )
    else:
        payload = {"key": users[1], "army": army}
        if mission_kind == "transport":
            payload["resources"] = [60, 0, 0]
        sent = command(universe, 0, mission_kind, payload)
    mission = next(job for job in sent["jobs"] if job["kind"] == mission_kind)
    if fur3_recall:
        assert mission["rules_version"] == terra_combat.VERSION
    elapsed = max(1, int(mission["travel"]) // 2)
    clock[0] = min(int(mission["due"]) - 1, clock[0] + elapsed)
    before_recall = state(universe, 0)
    reserved_resources = list(before_recall["resources"])

    token = identity()
    recall_barrier = Barrier(2)

    def recall(_attempt):
        recall_barrier.wait()
        return command(universe, 0, "mission_recall", {"key": mission["id"]}, token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        recall_results = list(pool.map(recall, (0, 1)))
    recalled = recall_results[0]
    assert all(result["jobs"] == recalled["jobs"] for result in recall_results)
    returning = [job for job in recalled["jobs"] if job.get("return_reason") == "recalled"]
    assert len(returning) == 1
    assert recalled["units"] == sent["units"]
    assert recalled["resources"] == reserved_resources
    if mission_kind == "colony_supply":
        assert recalled["neutral_market"]["goods"][3]["amount"] == 45
        assert (
            next(item for item in recalled["generic_items"]["items"] if item["id"] == "repair_kit")[
                "amount"
            ]
            == 16
        )
        with game.transaction() as db:
            target = game.read_colony(db, destination)
            assert target.get("goods_inbound", {}) == {}
            assert target.get("item_inbound", {}) == {}
    assert recalled["reports"][0]["title"] == "Mission zurückgerufen"
    if fur3_recall:
        with game.transaction() as db:
            assert (
                db.execute(
                    "SELECT count(*) FROM terra_combat_missions WHERE mission_id=?",
                    (mission["id"],),
                ).fetchone()[0]
                == 0
            )
    with game.transaction() as db:
        projected = game.read(db, users[0])
        game.produce(projected, int(returning[0]["due"]))
        cap = 2000 + projected["buildings"]["storage"] * 2000
        expected_resources = [
            min(cap, amount + cargo)
            for amount, cargo in zip(projected["resources"], returning[0]["loot"])
        ]
        expected_reserve = [
            projected.setdefault("reserve", [0, 0, 0])[index]
            + max(0, amount + returning[0]["loot"][index] - cap)
            for index, amount in enumerate(projected["resources"])
        ]
    clock[0] = returning[0]["due"]
    completed = state(universe, 0)
    assert {unit: completed["units"].get(unit, 0) for unit in original_units} == original_units
    assert all(
        completed["units"].get(unit, 0) == 0
        for unit in completed["units"].keys() - original_units.keys()
    )
    assert completed["resources"] == expected_resources
    assert completed["reserve"] == expected_reserve
    if mission_kind == "colony_supply":
        assert completed["goods_inventory"]["alloy"] == 50
        assert completed["item_inventory"]["repair_kit"] == 20
    assert not any(
        job["id"] == mission["id"] or job["kind"] == "return" for job in completed["jobs"]
    )
    assert completed["reports"][0]["title"] == "Mission zurückgekehrt"
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='mission_recalled'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )


def test_cancelling_completed_build_is_rejected(universe):
    game, users, clock = universe
    started = command(universe, 0, "build", {"key": "wall"})
    job = started["jobs"][0]
    clock[0] = job["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
    with pytest.raises(RuleError, match="kann nicht abgebrochen"):
        command(universe, 0, "cancel_job", {"key": job["id"]})
    with game.transaction() as db:
        colony = game.read(db, users[0])
        assert colony["buildings"]["wall"] == 1
        assert colony["jobs"] == []


def test_build_queue_reserves_projected_levels_and_starts_each_job_once(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [20000, 20000, 20000]
        colony["buildings"]["hq"] = 2
        colony["buildings"]["storage"] = 10
        game.save(db, colony)

    first = command(universe, 0, "build", {"key": "wall"})["jobs"]
    second = command(universe, 0, "build", {"key": "wall"})["jobs"]
    third = command(universe, 0, "build", {"key": "lab"})["jobs"]
    jobs = sorted(
        (job for job in third if job["kind"] == "build"), key=lambda job: job["queue_order"]
    )
    assert [job["target_level"] for job in jobs] == [1, 2, 1]
    assert jobs[0]["due"] == clock[0] + 6
    assert jobs[1]["started_at"] == jobs[0]["due"]
    assert jobs[1]["due"] == jobs[0]["due"] + 14
    assert jobs[2]["started_at"] == jobs[1]["due"]
    assert jobs[2]["due"] == jobs[1]["due"] + 6
    assert first[0]["id"] == jobs[0]["id"]
    assert second[-1]["target_level"] == 2

    clock[0] = jobs[0]["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        colony = game.read(db, users[0])
    active = next(job for job in colony["jobs"] if job["id"] == jobs[1]["id"])
    assert colony["buildings"]["wall"] == 1
    assert active["queued"] is False
    assert active["started_at"] == jobs[0]["due"]
    assert active["due"] == jobs[1]["due"]

    clock[0] = jobs[1]["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        colony = game.read(db, users[0])
    assert colony["buildings"]["wall"] == 2


def test_queued_build_duration_uses_headquarters_level_when_it_starts(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [20000, 20000, 20000]
        colony["buildings"]["storage"] = 10
        game.save(db, colony)
    first = command(universe, 0, "build", {"key": "hq"})["jobs"]
    second = command(universe, 0, "build", {"key": "wall"})["jobs"][-1]
    assert second["duration"] == 7
    clock[0] = first[0]["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        colony = game.read(db, users[0])
    active_wall = next(job for job in colony["jobs"] if job["id"] == second["id"])
    assert colony["buildings"]["hq"] == 2
    assert active_wall["queued"] is False
    assert active_wall["duration"] == 6
    assert active_wall["due"] == first[0]["due"] + 6


def test_legacy_running_upgrade_accepts_a_new_planned_followup(universe):
    game, users, _clock = universe
    started = command(universe, 0, "build", {"key": "wall"})
    legacy = started["jobs"][0]
    with game.transaction() as db:
        colony = game.read(db, users[0])
        for field in ("queue_order", "target_level", "queued", "started_at", "duration", "costs"):
            colony["jobs"][0].pop(field, None)
        game.save(db, colony)
    result = command(universe, 0, "build", {"key": "wall"})
    queue = sorted(
        (job for job in result["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    assert [job["id"] for job in queue] == [legacy["id"], result["jobs"][-1]["id"]]
    assert queue[0].get("queued", False) is False
    assert queue[1]["queued"] is True
    assert queue[1]["target_level"] == 2
    assert queue[1]["costs"] == [160, 320, 140]


def test_cancelling_queued_upgrade_reprices_later_levels_and_refunds_difference(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [20000, 20000, 20000]
        colony["buildings"]["storage"] = 10
        game.save(db, colony)
    first = command(universe, 0, "build", {"key": "wall"})["jobs"]
    second = command(universe, 0, "build", {"key": "wall"})["jobs"]
    third = command(universe, 0, "build", {"key": "wall"})["jobs"][-1]
    with game.transaction() as db:
        game.advance(db, clock[0])
        before = list(game.read(db, users[0])["resources"])
    result = command(universe, 0, "cancel_job", {"key": second[-1]["id"]})
    assert result["resources"] == [before[0] + 240, before[1] + 480, before[2] + 210]
    remaining = sorted(
        (job for job in result["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    assert [job["target_level"] for job in remaining] == [1, 2]
    assert remaining[1]["costs"] == [160, 320, 140]
    assert remaining[1]["started_at"] == first[0]["due"]
    assert remaining[1]["due"] == first[0]["due"] + 15
    assert third["target_level"] == 3


def test_cancelling_queued_research_reprices_same_technology_levels(universe):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"]["lab"] = 1
        colony["buildings"]["storage"] = 10
        colony["buildings"]["wood"] = 0
        colony["buildings"]["stone"] = 0
        colony["buildings"]["ore"] = 0
        colony["resources"] = [20000, 20000, 20000]
        game.save(db, colony)
    first = command(universe, 0, "research", {"key": "tactics"})["jobs"]
    second = command(universe, 0, "research", {"key": "tactics"})["jobs"]
    third = command(universe, 0, "research", {"key": "tactics"})["jobs"][-1]
    clock[0] += 1
    with game.transaction() as db:
        colony = game.read(db, users[0])
        game.produce(colony, clock[0])
        before = list(colony["resources"])
        game.save(db, colony)
    result = command(universe, 0, "cancel_job", {"key": second[-1]["id"]})
    remaining = sorted(
        (job for job in result["jobs"] if job["kind"] == "research"),
        key=lambda job: job["queue_order"],
    )
    assert [job["target_level"] for job in remaining] == [1, 2]
    assert remaining[1]["costs"] == [140, 180, 300]
    assert remaining[1]["started_at"] == first[0]["due"]
    assert remaining[1]["due"] == first[0]["due"] + 24
    assert result["resources"] == [before[0] + 210, before[1] + 270, before[2] + 450]
    assert third["target_level"] == 3


def test_queue_reorder_with_insufficient_repricing_resources_is_atomic(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"]["storage"] = 10
        colony["resources"] = [20000, 20000, 20000]
        game.save(db, colony)
    command(universe, 0, "build", {"key": "wall"})
    command(universe, 0, "build", {"key": "wall"})
    command(universe, 0, "build", {"key": "barracks"})
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [0, 0, 0]
        game.save(db, colony)
    before = state(universe, 0)
    queued_jobs = sorted(
        (job for job in before["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    waiting_wall = queued_jobs[1]
    with game.transaction() as db:
        colony = game.read(db, users[0])
        next(job for job in colony["jobs"] if job["id"] == waiting_wall["id"])["costs"] = [
            0,
            0,
            0,
        ]
        game.save(db, colony)
    before = state(universe, 0)
    queued_jobs = sorted(
        (job for job in before["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    waiting_wall = queued_jobs[1]
    before_jobs = sorted(
        (dict(job) for job in before["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    before_resources = before["resources"]
    with pytest.raises(RuleError, match="Nicht genügend Rohstoffe"):
        command(universe, 0, "queue_move", {"key": waiting_wall["id"], "direction": "down"})
    after = state(universe, 0)
    after_jobs = sorted(
        (job for job in after["jobs"] if job["kind"] == "build"),
        key=lambda job: job["queue_order"],
    )
    assert after["resources"] == before_resources
    assert after_jobs == before_jobs


def test_queued_jobs_can_be_reordered_and_capacity_is_enforced(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["resources"] = [20000, 20000, 20000]
        colony["buildings"]["storage"] = 10
        game.save(db, colony)
    command(universe, 0, "build", {"key": "wall"})
    command(universe, 0, "build", {"key": "barracks"})
    command(universe, 0, "build", {"key": "lab"})
    jobs = state(universe, 0)["jobs"]
    running = next(job for job in jobs if job["kind"] == "build" and not job.get("queued"))
    lab = next(job for job in jobs if job["key"] == "lab")
    moved = command(universe, 0, "queue_move", {"key": lab["id"], "direction": "up"})
    queue = sorted(
        (job for job in moved["jobs"] if job["kind"] == "build"), key=lambda job: job["queue_order"]
    )
    assert [job["key"] for job in queue] == ["wall", "lab", "barracks"]
    assert queue[0]["id"] == running["id"]
    assert queue[1]["due"] < jobs[-1]["due"]
    with game.transaction() as db:
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='job_queue_moved'",
            (users[0],),
        ).fetchone()
        assert json.loads(audit["details"]) == {
            "job_kind": "build",
            "direction": "up",
            "queue_order": 1,
        }
    with pytest.raises(RuleError, match="verschieben"):
        command(universe, 0, "queue_move", {"key": running["id"], "direction": "up"})

    for key in ("ore", "stone"):
        command(universe, 0, "build", {"key": key})
    with pytest.raises(RuleError, match="fünf Aufträge"):
        command(universe, 0, "build", {"key": "wood"})


def test_player_lists_exclude_current_player_from_direct_messages_and_invites(universe):
    game, users, _ = universe
    first = state(universe, 0)
    colony_points = {}
    with game.transaction() as db:
        colony_points = {
            user: json.loads(row["state"])
            for user in users
            for row in db.execute(
                "SELECT state FROM colonies WHERE user_id=? AND world_id=1", (user,)
            )
        }
    expected_visible_players = [
        user
        for user in users
        if math.hypot(first["x"] - colony_points[user]["x"], first["y"] - colony_points[user]["y"])
        <= 8
    ]
    assert [player["id"] for player in first["players"]] == expected_visible_players
    assert [player["id"] for player in first["alliance_candidates"]] == [
        user for user in expected_visible_players if user != users[0]
    ]
    assert first["players"][1]["intel_level"] == "unknown"
    assert "defense" not in first["players"][1]
    assert "garrison" not in first["players"][1]
    assert "units" not in first["players"][1]


def test_alliance_invite_candidates_are_active_world_visible_and_keyset_paginated(universe):
    game, users, _ = universe
    owner_state = state(universe, 0)
    world_id = int(owner_state["active_world"]["id"])
    baseline_candidate_count = len(owner_state["alliance_candidates"])
    visible = {
        tuple(map(int, key.split(":")))
        for key, sector in owner_state["sector_intel"].items()
        if sector["status"] == "current"
    }
    with game.transaction() as db:
        baseline_player_count = int(
            db.execute(
                "SELECT count(*) FROM colonies WHERE world_id=? AND is_home=TRUE", (world_id,)
            ).fetchone()[0]
        )
        occupied = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute("SELECT x,y FROM colonies WHERE world_id=?", (world_id,))
        }
        land = {
            (int(row["x"]), int(row["y"]))
            for row in db.execute(
                "SELECT x,y FROM world_terrain WHERE world_id=? AND terrain<>'water'", (world_id,)
            )
        }
        candidate_sectors = sorted((visible & land) - occupied)
        assert len(candidate_sectors) >= 51
        for index, (x, y) in enumerate(candidate_sectors[:51]):
            candidate_id = identity()
            candidate_name = f"ZCandidate{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (candidate_id, candidate_name, "unused"),
            )
            game.create(db, candidate_id, candidate_name)
            colony = db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
                (candidate_id, world_id),
            ).fetchone()
            candidate_state = json.loads(colony["state"])
            candidate_state["x"], candidate_state["y"] = x, y
            db.execute(
                "UPDATE colonies SET x=?,y=?,state=? WHERE colony_id=?",
                (x, y, json.dumps(candidate_state), colony["colony_id"]),
            )
        first, has_more = game.systems.alliance_candidate_page(db, users[0], "", world_id)
        assert len(first) == 50
        assert has_more is True
        assert all((candidate["x"], candidate["y"]) in visible for candidate in first)
        second, has_more = game.systems.alliance_candidate_page(
            db, users[0], "", world_id, str(first[-1]["id"])
        )
        assert len(first) + len(second) == 51 + baseline_candidate_count
        assert has_more is False
        assert {candidate["id"] for candidate in first}.isdisjoint(
            candidate["id"] for candidate in second
        )
        player_first, players_have_more = game.systems.player_directory_page(
            db, users[0], world_id, 1_700_000_000, {}, page_size=50
        )
        assert len(player_first) == 50
        assert players_have_more is True
        player_second, players_have_more = game.systems.player_directory_page(
            db,
            users[0],
            world_id,
            1_700_000_000,
            {},
            str(player_first[-1]["id"]),
            page_size=50,
        )
        assert len(player_first) + len(player_second) == baseline_player_count + 51
        assert players_have_more is False
        assert {player["id"] for player in player_first}.isdisjoint(
            player["id"] for player in player_second
        )
        assert all(player["intel_level"] == "unknown" for player in player_first)
        with pytest.raises(RuleError, match="nicht mehr verfügbar"):
            game.systems.alliance_candidate_page(db, users[0], "", world_id, "unknown-candidate")

    with game.transaction() as db:
        defender = game.read(db, users[1])
        defender["buildings"]["wall"] = 2
        defender["units"]["ranger"] = 10
        game.save(db, defender)
    updated = state(universe, 0)
    assert updated["players"][1]["intel_level"] == "unknown"
    assert "defense" not in updated["players"][1]
    assert "garrison" not in updated["players"][1]
    with game.transaction() as db:
        towns = json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])
        town = towns[0]
        town["owner"] = users[1]
        town["units"] = {"mech": 2}
        game.save_world_outposts(db, 1, towns)
    captured = next(post for post in state(universe, 0)["world"] if post["id"] == town["id"])
    assert captured["intel_level"] == "unknown"
    assert "garrison" not in captured
    assert "defense" not in captured
    assert "units" not in captured
    own_post = next(post for post in state(universe, 1)["world"] if post["id"] == town["id"])
    assert own_post["units"] == {"mech": 2}

    command(universe, 0, "message", {"channel": "private", "name": "Bravo", "body": "Treffpunkt?"})
    own_inbox = [
        message for message in state(universe, 0)["messages"] if message["channel"] == "private"
    ]
    bravo_inbox = [
        message for message in state(universe, 1)["messages"] if message["channel"] == "private"
    ]
    charlie_inbox = [
        message for message in state(universe, 2)["messages"] if message["channel"] == "private"
    ]
    assert len(own_inbox) == len(bravo_inbox) == 1
    assert not charlie_inbox


def test_scouting_reports_are_private_tiered_expire_and_return_rangers(universe):
    game, users, clock = universe
    with game.transaction() as db:
        target = game.read(db, users[1])
        target["buildings"]["hq"] = 4
        target["units"]["ranger"] = 7
        target["units"]["sentinel"] = 2
        game.save(db, target)
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")

    scout_token = identity()
    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 3}}, scout_token)
    job = next(item for item in sent["jobs"] if item["kind"] == "scout")
    assert job["intel_level"] == 2
    assert sent["units"]["ranger"] == 12
    assert (
        command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 3}}, scout_token)[
            "units"
        ]["ranger"]
        == 12
    )
    clock[0] = job["due"]
    arrived = state(universe, 0)
    report = next(
        player["intel_report"] for player in arrived["players"] if player["id"] == users[1]
    )
    assert report["level"] == 2
    assert report["status"] == "fresh"
    assert report["data"]["hq"] == 4
    assert report["data"]["units"] == {"ranger": 7, "sentinel": 2, "mech": 0}
    assert report["data"]["defense"] > 0
    assert "resources" not in report["data"]
    assert all(
        "intel_report" not in player
        for player in state(universe, 1)["players"]
        if player["id"] == users[0]
    )
    assert all(
        "intel_report" not in player
        for player in state(universe, 2)["players"]
        if player["id"] == users[1]
    )

    clock[0] = job["due"] + 3601
    stale = next(
        player["intel_report"]
        for player in state(universe, 0)["players"]
        if player["id"] == users[1]
    )
    assert stale["status"] == "stale"
    assert stale["data"]["defense"] == report["data"]["defense"]
    returned = state(universe, 0)
    assert returned["units"]["ranger"] == 15


def test_fur3_counterintelligence_detects_scout_without_exposing_attacker(universe, monkeypatch):
    game, users, clock = universe
    outcome_seed = f"{3:064x}"
    monkeypatch.setattr(terra_intelligence.secrets, "token_hex", lambda _size: outcome_seed)
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-1",),
        )
        target = game.read(db, users[1])
        target["buildings"]["wall"] = 0
        target["tech"]["tactics"] = 0
        target["buildings"]["hq"] = 4
        game.save(db, target)
    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 3}})
    scout = next(job for job in sent["jobs"] if job["kind"] == "scout")
    assert scout["intel_rules_version"] == terra_intelligence.VERSION
    assert "seed" not in scout
    assert "detection_percent" not in json.dumps(scout)
    assert len(scout["intel_seed_commitment"]) == 64
    clock[0] = int(scout["due"])
    attacker = state(universe, 0)
    defender = state(universe, 1)
    report = next(
        player["intel_report"] for player in attacker["players"] if player["id"] == users[1]
    )
    assert report["data"]["hq"] == 4
    assert any(item["title"] == "Aufklärungsversuch entdeckt" for item in defender["reports"])
    alert = next(
        item for item in defender["reports"] if item["title"] == "Aufklärungsversuch entdeckt"
    )
    assert users[0] not in alert["body"]
    clock[0] = int(scout["due"]) + int(scout["travel"])
    assert state(universe, 0)["units"]["ranger"] == 15


def test_fur3_counterintelligence_interception_returns_survivors_without_intel(
    universe, monkeypatch
):
    game, users, clock = universe
    outcome_seed = next(
        f"{value:064x}"
        for value in range(1000)
        if terra_intelligence.resolve(
            f"{value:064x}", 3, interception_percent=50, detection_percent=60
        )["intercepted"]
    )
    monkeypatch.setattr(terra_intelligence.secrets, "token_hex", lambda _size: outcome_seed)
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-1",),
        )
        target = game.read(db, users[1])
        target["buildings"]["wall"] = 10
        target["tech"]["tactics"] = 10
        game.save(db, target)
    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 3}})
    scout = next(job for job in sent["jobs"] if job["kind"] == "scout")
    clock[0] = int(scout["due"])
    attacker = state(universe, 0)
    defender = state(universe, 1)
    assert not any(
        player.get("intel_report") for player in attacker["players"] if player["id"] == users[1]
    )
    assert any(item["title"] == "Aufklärung abgefangen" for item in attacker["reports"])
    assert any(item["title"] == "Aufklärungsversuch entdeckt" for item in defender["reports"])
    clock[0] = int(scout["due"]) + int(scout["travel"])
    assert state(universe, 0)["units"]["ranger"] == 14


def test_fur2_scouting_does_not_pin_counterintelligence(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 1}})
    scout = next(job for job in sent["jobs"] if job["kind"] == "scout")
    assert "intel_rules_version" not in scout
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM terra_intel_missions").fetchone()[0] == 0


def test_scouting_rejects_non_rangers_and_pvp_protections(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        defender = game.read(db, users[0])
        defender["units"]["sentinel"] = 1
        game.save(db, defender)
    with pytest.raises(RuleError, match="nur Ranger"):
        command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 1, "sentinel": 1}})
    with game.transaction() as db:
        db.execute("UPDATE profiles SET joined=? WHERE user_id=?", (int(time.time()), users[1]))
    with pytest.raises(RuleError, match="Neulingsschutz"):
        command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 1}})


@pytest.mark.parametrize("arrival_change", ("pvp_disabled", "vacation_started"))
def test_scouting_rechecks_protection_at_arrival_and_returns_rangers_once(universe, arrival_change):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")

    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 2}})
    scout = next(job for job in sent["jobs"] if job["kind"] == "scout")
    assert sent["units"]["ranger"] == 13
    with game.transaction() as db:
        if arrival_change == "pvp_disabled":
            db.execute("UPDATE flags SET value='false' WHERE name='pvp'")
        else:
            target = game.read(db, users[1])
            target["vacation_until"] = int(scout["due"]) + 3600
            game.save(db, target)

    clock[0] = int(scout["due"])
    aborted = state(universe, 0)
    assert aborted["units"]["ranger"] == 13
    assert any(report["title"] == "Aufklärung abgebrochen" for report in aborted["reports"])
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM player_intel WHERE observer_id=? AND target_id=?",
                (users[0], users[1]),
            ).fetchone()[0]
            == 0
        )

    retried = state(universe, 0)
    assert sum(report["title"] == "Aufklärung abgebrochen" for report in retried["reports"]) == 1
    clock[0] = int(scout["due"]) + int(scout["travel"])
    returned = state(universe, 0)
    assert returned["units"]["ranger"] == 15
    assert not any(job["kind"] in ("scout", "return") for job in returned["jobs"])


def test_single_ranger_reveals_buildings_but_not_military_strength(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        target = game.read(db, users[1])
        target["buildings"]["hq"] = 3
        target["units"]["ranger"] = 9
        game.save(db, target)
    sent = command(universe, 0, "scout", {"key": users[1], "army": {"ranger": 1}})
    job = next(item for item in sent["jobs"] if item["kind"] == "scout")
    assert job["intel_level"] == 1
    clock[0] = job["due"]
    report = next(
        player["intel_report"]
        for player in state(universe, 0)["players"]
        if player["id"] == users[1]
    )
    assert report["level"] == 1
    assert report["data"]["hq"] == 3
    assert report["data"]["buildings"]["hq"] == 3
    assert "defense" not in report["data"]
    assert "garrison" not in report["data"]
    assert "units" not in report["data"]


def test_alliance_invitation_uses_player_name_from_select(universe):
    game, users, _ = universe
    command(universe, 0, "alliance_create", {"tag": "FUR", "name": "FUR Pioniere"})
    command(universe, 0, "alliance_invite", {"name": "Bravo"})
    assert (
        state(universe, 1)["invites"][0]["alliance_id"]
        == state(universe, 0)["membership"]["alliance_id"]
    )
    with game.transaction() as db:
        assert (
            db.execute("SELECT count(*) FROM invites WHERE user_id=?", (users[1],)).fetchone()[0]
            == 1
        )


def test_worker_finishes_without_page_requests(universe):
    game, users, clock = universe
    command(universe, 0, "build", {"key": "wood"})
    clock[0] += 20
    cycle(game)
    with game.transaction() as db:
        assert game.read(db, users[0])["buildings"]["wood"] == 2
        assert db.execute("SELECT heartbeat FROM worker_status").fetchone()[0] == clock[0]


def test_worker_retries_transaction_after_mid_tick_failure_exactly_once(universe, monkeypatch):
    game, users, clock = universe
    command(universe, 0, "build", {"key": "wood"})
    with game.transaction() as db:
        pending = game.read(db, users[0])["jobs"][0]
    clock[0] = int(pending["due"]) + 1
    original_tick = game.tick

    def fail_after_transactional_mutation(db, state, now):
        original_tick(db, state, now)
        raise RuntimeError("simulated worker crash before transaction commit")

    monkeypatch.setattr(game, "tick", fail_after_transactional_mutation)
    cycle(game)
    with game.transaction() as db:
        rolled_back = game.read(db, users[0])
        assert rolled_back["buildings"]["wood"] == 1
        assert len(rolled_back["jobs"]) == 1
        assert (
            db.execute(
                "SELECT attempts FROM job_failures WHERE job_id=?", (pending["id"],)
            ).fetchone()[0]
            == 1
        )

    monkeypatch.setattr(game, "tick", original_tick)
    cycle(game)
    cycle(game)
    with game.transaction() as db:
        completed = game.read(db, users[0])
        assert completed["buildings"]["wood"] == 2
        assert not completed["jobs"]
        assert (
            sum(report["title"] == "Auftrag abgeschlossen" for report in completed["reports"]) == 1
        )


def test_concurrent_worker_cycles_complete_due_job_once(universe):
    game, users, clock = universe
    command(universe, 0, "build", {"key": "wood"})
    with game.transaction() as db:
        pending = game.read(db, users[0])["jobs"][0]
    clock[0] = int(pending["due"]) + 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _index: cycle(game), range(8)))

    with game.transaction() as db:
        completed = game.read(db, users[0])
        assert completed["buildings"]["wood"] == 2
        assert not completed["jobs"]
        assert (
            sum(report["title"] == "Auftrag abgeschlossen" for report in completed["reports"]) == 1
        )
        assert (
            db.execute(
                "SELECT count(*) FROM job_failures WHERE user_id=? AND job_id=?",
                (users[0], pending["id"]),
            ).fetchone()[0]
            == 0
        )


def test_account_verification_single_use_and_mfa(universe):
    game, users, clock = universe
    accounts = Accounts(game)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET email=? WHERE user_id=?", ("alpha@example.test", users[0]))
        accounts.send_token(db, users[0], "verify", "alpha@example.test")
        body = db.execute("SELECT body FROM outbox WHERE user_id=?", (users[0],)).fetchone()[0]
        token = body.split("\n\n")[1]
        accounts.public(db, AccountAction(action="verify", token=token))
        assert (
            db.execute("SELECT verified FROM profiles WHERE user_id=?", (users[0],)).fetchone()[0]
            == 1
        )
    with pytest.raises(RuleError), game.transaction() as db:
        accounts.public(db, AccountAction(action="verify", token=token))
    secret = "JBSWY3DPEHPK3PXP"
    with game.transaction() as db:
        db.execute(
            "INSERT INTO flags VALUES (?,?)",
            ("mfa_pending_" + users[0], json.dumps({"secret": secret, "expires": clock[0] + 600})),
        )
        accounts.private(
            db, users[0], AccountAction(action="mfa_confirm", code=totp(secret, clock[0] // 30))
        )
        assert (
            db.execute("SELECT totp FROM profiles WHERE user_id=?", (users[0],)).fetchone()[0]
            == secret
        )
    from fur_empire.identity import verify_totp

    with pytest.raises(RuleError):
        verify_totp(secret, totp(secret, clock[0] // 30), clock[0] // 30)
    assert digest(token) != token


def test_totp_recovery_codes_are_hashed_single_use_and_regenerated_after_reauth(universe):
    game, users, clock = universe
    accounts = Accounts(game)
    secret = "JBSWY3DPEHPK3PXP"
    with game.transaction() as db:
        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (PasswordHasher().hash("recovery-test-password"), users[0]),
        )
        db.execute("UPDATE profiles SET totp=? WHERE user_id=?", (secret, users[0]))
        first = accounts.private(
            db,
            users[0],
            AccountAction(
                action="recovery_codes_regenerate",
                password="recovery-test-password",
                code=totp(secret, clock[0] // 30),
            ),
        )
        codes = first["recovery_codes"]
        assert len(codes) == 10
        assert all(len(code) == 20 for code in codes)
        saved = db.execute(
            "SELECT code_hash FROM mfa_recovery_codes WHERE user_id=?", (users[0],)
        ).fetchall()
        assert len(saved) == 10
        assert all(row[0] not in codes for row in saved)
        assert {row[0] for row in saved} == {digest(code) for code in codes}
        from fur_empire.identity import consume_recovery_code

        assert consume_recovery_code(db, users[0], codes[0])
        assert not consume_recovery_code(db, users[0], codes[0])
        # Advance the deterministic authenticator step before proving regeneration
        # invalidates all codes issued by the prior operation.
        clock[0] += 30
        second = accounts.private(
            db,
            users[0],
            AccountAction(
                action="recovery_codes_regenerate",
                password="recovery-test-password",
                code=totp(secret, clock[0] // 30),
            ),
        )
        assert len(second["recovery_codes"]) == 10
        assert not consume_recovery_code(db, users[0], codes[1])
        assert (
            db.execute(
                "SELECT count(*) FROM mfa_recovery_codes WHERE user_id=?", (users[0],)
            ).fetchone()[0]
            == 10
        )


def test_mfa_confirmation_issues_recovery_codes_once(universe):
    game, users, clock = universe
    accounts = Accounts(game)
    secret = "JBSWY3DPEHPK3PXP"
    with game.transaction() as db:
        db.execute(
            "INSERT INTO flags VALUES (?,?)",
            ("mfa_pending_" + users[0], json.dumps({"secret": secret, "expires": clock[0] + 600})),
        )
        result = accounts.private(
            db, users[0], AccountAction(action="mfa_confirm", code=totp(secret, clock[0] // 30))
        )
        assert len(result["recovery_codes"]) == 10
        assert (
            db.execute(
                "SELECT count(*) FROM mfa_recovery_codes WHERE user_id=?", (users[0],)
            ).fetchone()[0]
            == 10
        )


def test_recovery_code_schema_17_migrates_on_each_adapter(universe):
    game, users, _ = universe
    before = state(universe, 0)
    with game.transaction() as db:
        db.execute("DROP TABLE mfa_recovery_codes")
        db.execute("DELETE FROM schema_versions WHERE version=17")
    migrated = Game(game.path)
    with migrated.transaction() as db:
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM mfa_recovery_codes").fetchone()[0] == 0
        assert db.execute("SELECT 1 FROM users WHERE id=?", (users[0],)).fetchone()
    assert state((migrated, users, [int(time.time())]), 0)["id"] == before["id"]


def test_login_account_network_limit_runs_on_each_database_adapter(universe, monkeypatch):
    game, users, _clock = universe
    from fastapi.testclient import TestClient

    monkeypatch.setenv("FUR_DB", game.path)
    import fur_empire.api as api_module

    monkeypatch.setattr(api_module, "game", game)
    monkeypatch.setattr(api_module, "accounts", Accounts(game))
    monkeypatch.setenv("FUR_EMBEDDED_WORKER", "false")
    with game.transaction() as db:
        for user in users[:2]:
            db.execute(
                "UPDATE users SET password=? WHERE id=?",
                (PasswordHasher().hash("adapter-login-password"), user),
            )

    with TestClient(api_module.app) as client:
        for _attempt in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"name": "Alpha", "password": "wrong-adapter-password"},
            )
            assert response.status_code == 400
            assert response.json()["error"] == "Name oder Passwort stimmt nicht."
        throttled = client.post(
            "/api/v1/auth/login",
            json={"name": "Alpha", "password": "wrong-adapter-password"},
        )
        assert throttled.status_code == 400
        assert throttled.json()["error"] == "Zu viele Anfragen. Bitte eine Minute warten."
        other_account = client.post(
            "/api/v1/auth/login",
            json={"name": "Bravo", "password": "adapter-login-password"},
        )
        assert other_account.status_code == 200


def test_commander_name_change_enforces_24_hour_cooldown_and_keeps_colony_names(universe):
    game, users, clock = universe
    owner, other = users[:2]
    accounts = Accounts(game)
    secondary = secondary_colony(universe, 0)
    with game.transaction() as db:
        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (PasswordHasher().hash("rename-account-password"), owner),
        )
        db.execute(
            "UPDATE profiles SET totp=? WHERE user_id=?",
            ("JBSWY3DPEHPK3PXP", owner),
        )
        before = {
            row["colony_id"]: json.loads(row["state"])
            for row in db.execute("SELECT colony_id,state FROM colonies WHERE user_id=?", (owner,))
        }
        action = AccountAction(
            action="rename",
            new_name="New Commander",
            password="rename-account-password",
            code=totp("JBSWY3DPEHPK3PXP", clock[0] // 30),
        )
        with pytest.raises(RuleError, match="bereits vergeben"):
            accounts.private(db, owner, action.model_copy(update={"new_name": "Bravo"}))
        assert accounts.private(db, owner, action) == {"ok": True}
        assert (
            db.execute("SELECT name FROM users WHERE id=?", (owner,)).fetchone()[0]
            == "New Commander"
        )
        for row in db.execute("SELECT colony_id,state FROM colonies WHERE user_id=?", (owner,)):
            updated = json.loads(row["state"])
            assert updated["name"] == "New Commander"
            assert updated["colony_name"] == before[row["colony_id"]]["colony_name"]
        audit = db.execute(
            "SELECT details FROM audit WHERE actor=? AND action='account_rename' ORDER BY created DESC LIMIT 1",
            (owner,),
        ).fetchone()
        assert json.loads(audit["details"])["old_name"] == "Alpha"
        changed_at = int(
            db.execute("SELECT name_changed FROM profiles WHERE user_id=?", (owner,)).fetchone()[0]
        )
        with pytest.raises(RuleError, match="alle 24 Stunden"):
            accounts.private(db, owner, action.model_copy(update={"new_name": "Too Soon"}))
        assert db.execute("SELECT name FROM users WHERE id=?", (other,)).fetchone()[0] == "Bravo"
        assert secondary != owner
    clock[0] = changed_at + 86400
    with game.transaction() as db:
        assert accounts.private(
            db,
            owner,
            AccountAction(
                action="rename",
                new_name="Commander Two",
                password="rename-account-password",
                code=totp("JBSWY3DPEHPK3PXP", clock[0] // 30),
            ),
        ) == {"ok": True}


def test_personal_data_export_stays_account_scoped_on_each_database_adapter(universe):
    game, users, clock = universe
    owner, foreign = users[:2]
    accounts = Accounts(game)
    with game.transaction() as db:
        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (PasswordHasher().hash("adapter-export-password"), owner),
        )
        db.execute(
            "UPDATE profiles SET email=?,verified=1,totp=? WHERE user_id=?",
            ("owner-export@example.test", "JBSWY3DPEHPK3PXP", owner),
        )
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("owner-template", owner, "Own mission", "attack", '{"ranger":2}', False, clock[0]),
        )
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("foreign-template", foreign, "Other mission", "attack", '{"mech":2}', False, clock[0]),
        )
        db.execute(
            "INSERT INTO map_bookmarks(user_id,target_id,created) VALUES (?,?,?)",
            (owner, "own-target", clock[0]),
        )
        db.execute(
            "INSERT INTO map_bookmarks(user_id,target_id,created) VALUES (?,?,?)",
            (foreign, "other-target", clock[0]),
        )
        result = accounts.private(
            db,
            owner,
            AccountAction(
                action="export",
                password="adapter-export-password",
                code=totp("JBSWY3DPEHPK3PXP", clock[0] // 30),
            ),
        )
        assert len(result["colonies"]) == 1
        assert result["colonies"][0]["colony_id"] == owner
        assert [item["name"] for item in result["mission_templates"]] == ["Own mission"]
        assert result["map_bookmarks"] == [{"target_id": "own-target", "created": clock[0]}]
        assert result["account"]["email"] == "owner-export@example.test"
        assert result["account"]["mfa_enabled"] is True
        encoded = json.dumps(result)
        assert "JBSWY3DPEHPK3PXP" not in encoded
        assert "Other mission" not in encoded
        assert "other-target" not in encoded
        assert foreign not in encoded


def test_backup_restore_sqlite_integrity(universe, tmp_path):
    game, users, _ = universe
    if game.path.startswith("postgres"):
        pytest.skip("PostgreSQL backup/restore verified separately with pg_dump/pg_restore")
    command(universe, 0, "alliance_create", {"tag": "FUR", "name": "Backup Allianz"})
    destination = backup(game, tmp_path / "snapshots")
    restored = Game(destination)
    with restored.transaction() as db:
        assert restored.view(db, users[0])["membership"]


def test_one_hundred_concurrent_transfers_no_double_spend(universe):
    game, users, _ = universe

    def trade(_):
        try:
            command(universe, 0, "trade", {"source": 0, "dest": 1, "amount": 10})
            return True
        except RuleError:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        successes = sum(pool.map(trade, range(100)))
    assert successes == 100
    current = state(universe, 0)
    assert current["resources"] == [200, 1500, 800]
    with game.transaction() as db:
        assert (
            db.execute("SELECT count(*) FROM commands WHERE user_id=?", (users[0],)).fetchone()[0]
            == 100
        )


def test_world_expansion_and_spawn_uniqueness(universe):
    game, users, clock = universe
    with game.transaction() as db:
        citadel = next(
            post for post in game.world_outposts(db, 1) if post["name"] == "Zitadelle des Kerns"
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, citadel["x"], citadel["y"], clock[0]),
        )
    current = state(universe, 0)
    assert len(current["world"]) <= 104
    with game.transaction() as db:
        citadel = next(
            post for post in game.world_outposts(db, 1) if post["name"] == "Zitadelle des Kerns"
        )
    assert citadel["tier"] == 8
    positions = [(t["x"], t["y"]) for t in current["world"]] + [
        (p["x"], p["y"]) for p in current["players"]
    ]
    player_positions = [(player["x"], player["y"]) for player in current["players"]]
    assert len(positions) == len(set(positions))
    assert all(
        math.hypot(x - other_x, y - other_y) >= 6
        for index, (x, y) in enumerate(player_positions)
        for other_x, other_y in player_positions[index + 1 :]
    ), player_positions
    assert all(0 <= x < 64 and 0 <= y < 64 for x, y in positions)
    assert len(Game(game.path).path) > 0


def test_outpost_garrison_recall_and_enemy_recapture(universe):
    game, users, clock = universe
    with game.transaction() as db:
        for user in users[:2]:
            s = game.read(db, user)
            s["buildings"]["hq"] = 3
            s["units"]["mech"] = 100
            game.save(db, s)
    post = state(universe, 0)["world"][0]["id"]
    command(universe, 0, "raid", {"key": post, "army": {"mech": 50}, "capture": True})
    clock[0] += 100
    assert state(universe, 0)["captures"] == 1
    command(universe, 0, "station", {"key": post, "army": {"ranger": 5}})
    clock[0] += 100
    assert next(t for t in state(universe, 0)["world"] if t["id"] == post)["units"]["ranger"] == 5
    command(universe, 0, "recall", {"key": post, "army": {"ranger": 2}})
    clock[0] += 100
    assert next(t for t in state(universe, 0)["world"] if t["id"] == post)["units"]["ranger"] == 3
    command(universe, 1, "raid", {"key": post, "army": {"mech": 50}, "capture": True})
    clock[0] += 100
    assert state(universe, 1)["captures"] == 1
    assert state(universe, 0)["captures"] == 0
    assert any(r["title"] == "Außenposten verloren" for r in state(universe, 0)["reports"])


def test_garrison_recall_is_unavailable_during_travel_and_returns_once(universe):
    game, users, clock = universe
    with game.transaction() as db:
        state0 = game.read(db, users[0])
        state0["buildings"]["hq"] = 3
        state0["units"]["mech"] = 100
        game.save(db, state0)
    post = state(universe, 0)["world"][0]["id"]
    command(universe, 0, "raid", {"key": post, "army": {"mech": 50}, "capture": True})
    clock[0] += 100
    assert state(universe, 0)["captures"] == 1
    command(universe, 0, "station", {"key": post, "army": {"ranger": 5}})
    clock[0] += 100
    assert state(universe, 0)["world"][0]["units"]["ranger"] == 5
    command(universe, 0, "recall", {"key": post, "army": {"ranger": 3}})
    transit = state(universe, 0)
    assert transit["jobs"][-1]["kind"] == "return"
    assert transit["jobs"][-1]["army"] == {"ranger": 3}
    with pytest.raises(RuleError, match="Ungültige Garnisonsauswahl"):
        command(universe, 0, "recall", {"key": post, "army": {"ranger": 3}})
    in_transit = state(universe, 0)
    assert in_transit["units"]["ranger"] == 10
    assert in_transit["jobs"][-1]["kind"] == "return"
    clock[0] += 100
    game = Game(game.path)
    arrived = state(universe, 0)
    assert arrived["units"]["ranger"] == 13
    assert not arrived["jobs"]
    assert next(t for t in arrived["world"] if t["id"] == post)["units"]["ranger"] == 2
    with game.transaction() as db:
        game.advance(db, clock[0])
    assert state(universe, 0)["units"]["ranger"] == 13


def test_faction_choice_and_trade_are_independent_across_worlds(universe):
    game, users, _ = universe
    first = command(universe, 0, "faction", {"key": "syndicate"})
    assert first["neutral_market"]["payout_percent"] == 60
    with game.transaction() as db:
        world_id = game.create_world(db, "Faction frontier", 19812, 8, True)
        game.join_world(db, users[0], "Alpha", world_id)
    second = command(universe, 0, "faction", {"key": "wardens"})
    assert second["profile"]["faction"] == "wardens"
    assert second["neutral_market"]["payout_percent"] == 50
    back = command(universe, 0, "world_select", {"world_id": 1})
    assert back["profile"]["faction"] == "syndicate"
    assert back["neutral_market"]["payout_percent"] == 60


def test_pioneer_reserves_exclusive_planet_and_founds_once(universe):
    from fur_empire.orbit_rules import VERSION

    game, users, clock = universe

    from fur_empire.orbit_attack import report_page

    def reports(colony_id):
        with game.transaction() as db:
            return report_page(db, colony_id)["reports"]

    with game.transaction() as db:
        for user in users[:2]:
            db.execute(
                "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) "
                "VALUES (?,1,?,?)",
                (user, VERSION, clock[0]),
            )
    target = {"world_id": 1, "galaxy": 1, "system": 1, "slot": 1}
    token = identity()
    launched = command(universe, 0, "orbit_colonize", target, token)["orbit_access"]
    assert not launched["pioneer_available"]
    assert launched["claims"][0]["founded_at"] is None
    assert command(universe, 0, "orbit_colonize", target, token)["orbit_access"] == launched
    with pytest.raises(RuleError, match="nicht verfügbar"):
        command(universe, 1, "orbit_colonize", target)
    assert state(universe, 1)["orbit_access"]["pioneer_available"]
    assert not state(universe, 1)["orbit_access"]["claims"]
    clock[0] = launched["claims"][0]["arrival"]
    cycle(game)
    cycle(game)
    assert state(universe, 0)["orbit_access"]["claims"][0]["founded_at"] == clock[0]
    with game.transaction() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM audit WHERE action='orbit_colony_founded'").fetchone()[
                0
            ]
            == 1
        )
    colony = state(universe, 0)["orbit_access"]["colonies"][0]
    build = {"world_id": 1, "colony_id": colony["mission_id"], "key": "refinery"}
    with pytest.raises(RuleError, match="nicht verfügbar"):
        command(universe, 1, "orbit_build", build)
    queued = command(universe, 0, "orbit_build", build)["orbit_access"]["colonies"][0]
    assert queued["ore"] == 380
    assert queued["refinery"] == 0
    clock[0] = queued["due"] + 301
    cycle(game)
    economy = state(universe, 0)["orbit_access"]["colonies"][0]
    assert economy["refinery"] == 1
    assert economy["ether"] == 1
    assert economy["remainder"] == 12
    assert economy["ore"] == 386
    assert economy["ore_remainder"] == 1860
    clock[0] += 40 * 3600
    target = {"world_id": 1, "colony_id": colony["mission_id"]}
    researched = command(universe, 0, "orbit_research_shipbuilding", target)["orbit_access"][
        "colonies"
    ][0]
    ships = {**target, "key": "probe", "count": 2}
    with pytest.raises(RuleError, match="Schiffbauforschung"):
        command(universe, 0, "orbit_build_ships", ships)
    clock[0] = researched["shipbuilding_ready_at"]
    token = identity()
    ordered = command(universe, 0, "orbit_build_ships", ships, token)["orbit_access"]["colonies"][0]
    assert ordered["ship_order"]["amount"] == 2
    assert (
        command(universe, 0, "orbit_build_ships", ships, token)["orbit_access"]["colonies"][0]
        == ordered
    )
    clock[0] = ordered["ship_order"]["due"]
    cycle(game)
    cycle(game)
    assert state(universe, 0)["orbit_access"]["colonies"][0]["ships"] == {"probe": 2}
    with game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'colony_ship',1)",
            (colony["mission_id"],),
        )
    second_target = {
        "world_id": 1,
        "galaxy": 1,
        "system": 1,
        "slot": 2,
        "colony_id": colony["mission_id"],
    }
    before = state(universe, 0)["orbit_access"]["colonies"][0]["ether"]
    with pytest.raises(RuleError, match="nicht verfügbar"):
        command(universe, 1, "orbit_colonize", second_target)
    second = command(universe, 0, "orbit_colonize", second_target)["orbit_access"]
    assert second["colonies"][0]["ether"] == before - 4
    assert second["colonies"][0]["ships"]["colony_ship"] == 0
    assert second["claims"][1]["founded_at"] is None
    clock[0] = second["claims"][1]["arrival"]
    cycle(game)
    colonies = state(universe, 0)["orbit_access"]["colonies"]
    assert len(colonies) == 2
    with game.transaction() as db:
        db.execute(
            "UPDATE orbit_economy SET ore=500,ether=500 WHERE mission_id=?",
            (colony["mission_id"],),
        )
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'freighter',1)",
            (colony["mission_id"],),
        )
    funded_origin = state(universe, 0)["orbit_access"]["colonies"][0]
    freight = {
        **target,
        "key": colonies[1]["mission_id"],
        "count": 1,
        "orbit_ore": 100,
        "orbit_ether": 20,
    }
    with pytest.raises(RuleError, match="Ladekapazität"):
        command(universe, 0, "orbit_transport", {**freight, "orbit_ore": 160})
    token = identity()
    shipped = command(universe, 0, "orbit_transport", freight, token)["orbit_access"]["colonies"]
    assert shipped[0]["ships"]["freighter"] == 0
    assert shipped[0]["ore"] == funded_origin["ore"] - 100
    assert shipped[0]["ether"] == funded_origin["ether"] - 26
    assert (
        command(universe, 0, "orbit_transport", freight, token)["orbit_access"]["colonies"]
        == shipped
    )
    clock[0] = shipped[0]["transports"][0]["due"] + 60
    cycle(game)
    cycle(game)
    arrived = state(universe, 0)["orbit_access"]["colonies"]
    assert arrived[0]["ships"]["freighter"] == 1
    assert not arrived[0]["transports"]
    assert arrived[1]["ore_reserve"] == 100
    assert arrived[1]["ether_reserve"] == 20
    collected = command(
        universe, 0, "orbit_collect_reserve", {"world_id": 1, "colony_id": arrived[1]["mission_id"]}
    )["orbit_access"]["colonies"][1]
    assert collected["ore_reserve"] == 0
    assert collected["ether"] == 20
    outbound = command(universe, 0, "orbit_transport", freight)["orbit_access"]["colonies"][0][
        "transports"
    ][0]
    clock[0] += 10
    recall = {**target, "key": outbound["id"]}
    token = identity()
    recalled = command(universe, 0, "orbit_recall_transport", recall, token)["orbit_access"][
        "colonies"
    ][0]["transports"][0]
    assert recalled["recalled"]
    assert recalled["due"] == clock[0] + 10
    assert (
        command(universe, 0, "orbit_recall_transport", recall, token)["orbit_access"]["colonies"][
            0
        ]["transports"][0]
        == recalled
    )
    clock[0] = recalled["due"]
    cycle(game)
    cycle(game)
    returned = state(universe, 0)["orbit_access"]["colonies"]
    assert returned[0]["ore_reserve"] == 100
    assert returned[0]["ether_reserve"] == 20
    assert returned[0]["ships"]["freighter"] == 1
    assert returned[1]["ore_reserve"] == 0
    assert returned[1]["ether_reserve"] == 0
    scout = {**target, "galaxy": 1, "system": 1, "slot": 2}
    sent = command(universe, 0, "orbit_scout", scout)["orbit_access"]["colonies"][0]
    assert sent["ships"]["probe"] == 1
    clock[0] = sent["scouts"][0]["due"] + 60
    cycle(game)
    cycle(game)
    assert state(universe, 0)["orbit_access"]["colonies"][0]["ships"]["probe"] == 2
    with game.transaction() as db:
        intel = db.execute("SELECT observer,world_id,slot,occupied FROM orbit_intel").fetchall()
        assert len(intel) == 1
        assert tuple(intel[0][key] for key in ("observer", "world_id", "slot", "occupied")) == (
            users[0],
            1,
            2,
            True,
        )
        battle_id = identity()
        db.execute(
            "INSERT INTO orbit_battle_reports VALUES (?,?,?,?,?)",
            (battle_id, returned[0]["mission_id"], returned[1]["mission_id"], clock[0], "{}"),
        )
        db.execute(
            "INSERT INTO orbit_debris VALUES (?,?,?,?)",
            (battle_id, 80, 40, clock[0] + 3600),
        )
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'salvager',1)",
            (returned[0]["mission_id"],),
        )
    salvage = {**target, "key": battle_id, "count": 1}
    launched = command(universe, 0, "orbit_salvage", salvage)["orbit_access"]["colonies"][0]
    assert launched["ships"]["salvager"] == 0
    clock[0] = launched["transports"][0]["due"] + 60
    cycle(game)
    cycle(game)
    salvaged = state(universe, 0)["orbit_access"]["colonies"][0]
    assert salvaged["ships"]["salvager"] == 1
    assert salvaged["ore_reserve"] == 180
    assert salvaged["ether_reserve"] == 30
    assert reports(salvaged["mission_id"])[0]["debris_ether"] == 30
    from fur_empire.orbit_attack import record_debris

    with game.transaction() as db:
        origin_id, target_id = (item["mission_id"] for item in returned)
        first, second_battle = identity(), identity()
        for report_id in (first, second_battle):
            db.execute(
                "INSERT INTO orbit_battle_reports VALUES (?,?,?,?,?)",
                (report_id, origin_id, target_id, clock[0], "{}"),
            )
            record_debris(db, report_id, target_id, clock[0], 1100, 300)
        moon = db.execute("SELECT battle_id FROM orbit_moons WHERE colony_id=?", (target_id,))
        assert moon.fetchone()[0] == first
        first_debris = db.execute(
            "SELECT ore,ether FROM orbit_debris WHERE battle_id=?", (first,)
        ).fetchone()
        second_debris = db.execute(
            "SELECT ore,ether FROM orbit_debris WHERE battle_id=?", (second_battle,)
        ).fetchone()
        assert (first_debris["ore"], first_debris["ether"]) == (100, 50)
        assert (second_debris["ore"], second_debris["ether"]) == (1100, 300)
    assert state(universe, 0)["orbit_access"]["colonies"][1]["moon_formed_at"] == clock[0]
    with game.transaction() as db:
        db.execute(
            "UPDATE orbit_economy SET ore=2000,ether=1000 WHERE mission_id=?",
            (origin_id,),
        )
    building = command(universe, 0, "orbit_station_build", target)["orbit_access"]["colonies"][0][
        "station"
    ]
    assert building["level"] == 0
    clock[0] = building["ready_at"]
    cycle(game)
    garrison = {**target, "key": "probe", "count": 1}
    stationed = command(universe, 0, "orbit_station_deploy", garrison)["orbit_access"]["colonies"][
        0
    ]
    assert stationed["station"]["ships"] == {"probe": 1}
    assert stationed["ships"]["probe"] == 1
    with game.transaction() as db:
        db.execute(
            "UPDATE orbit_station_ships SET amount=100 WHERE colony_id=? AND ship='probe'",
            (origin_id,),
        )
    with pytest.raises(RuleError, match="voll"):
        command(universe, 0, "orbit_station_deploy", garrison)
    full_station = state(universe, 0)["orbit_access"]["colonies"][0]
    assert full_station["station"]["ships"] == {"probe": 100}
    assert full_station["ships"]["probe"] == 1
    with game.transaction() as db:
        db.execute(
            "UPDATE orbit_station_ships SET amount=1 WHERE colony_id=? AND ship='probe'",
            (origin_id,),
        )
    clock[0] = stationed["station"]["maintained_until"]
    assert not state(universe, 0)["orbit_access"]["colonies"][0]["station"]["active"]
    maintained = command(universe, 0, "orbit_station_upkeep", target)["orbit_access"]["colonies"][0]
    assert maintained["station"]["active"]
    withdrawn = command(universe, 0, "orbit_station_withdraw", garrison)["orbit_access"][
        "colonies"
    ][0]
    assert not withdrawn["station"]["ships"]
    assert withdrawn["ships"]["probe"] == 2
    with game.transaction() as db:
        db.execute("UPDATE orbit_economy SET ore=1000,ether=200 WHERE mission_id=?", (target_id,))
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'probe',1)", (target_id,)
        )
    scanner = command(universe, 0, "orbit_build_scanner", {"world_id": 1, "colony_id": target_id})[
        "orbit_access"
    ]["colonies"][1]
    clock[0] = scanner["scanner_ready_at"]
    advanced = command(
        universe,
        0,
        "orbit_scout",
        {"world_id": 1, "colony_id": target_id, "galaxy": 1, "system": 1, "slot": 1},
    )["orbit_access"]["colonies"][1]["scouts"][0]
    clock[0] = advanced["due"]
    cycle(game)
    command(universe, 0, "orbit_transport", freight)
    scan = {"world_id": 1, "colony_id": target_id, "galaxy": 1, "system": 1, "slot": 2}
    with pytest.raises(RuleError, match="Sensorreichweite"):
        command(universe, 0, "orbit_phalanx_scan", {**scan, "system": 7})
    scanned = command(universe, 0, "orbit_phalanx_scan", scan)["orbit_access"]["colonies"][1]
    assert scanned["phalanx"]["missions"] == [{"kind": "freight", "due": clock[0] + 60}]
    assert scanned["ether"] == 6
    with pytest.raises(RuleError, match="Abklingzeit"):
        command(universe, 0, "orbit_phalanx_scan", scan)
    with game.transaction() as db:
        result = db.execute(
            "SELECT intel_level,ships FROM orbit_intel WHERE observer=? AND slot=1", (users[0],)
        ).fetchone()
        assert result["intel_level"] == 2
        assert result["ships"] > 0
        terra = game.read(db, users[0])
        terra["buildings"]["hq"] = 10
        game.save(db, terra)
        for orbit_id in (origin_id, target_id):
            db.execute("UPDATE orbit_economy SET ore=5000 WHERE mission_id=?", (orbit_id,))
            db.execute(
                "INSERT INTO orbit_stations(colony_id,level,maintained_until) VALUES (?,2,?) "
                "ON CONFLICT(colony_id) DO UPDATE SET level=2,maintained_until=excluded.maintained_until",
                (orbit_id, clock[0] + 86400),
            )
    for orbit_id in (origin_id, target_id):
        built = command(
            universe, 0, "orbit_build_jumpgate", {"world_id": 1, "colony_id": orbit_id}
        )["orbit_access"]["colonies"]
    jump = {**target, "orbit_target": target_id, "key": "probe", "count": 1}
    with pytest.raises(RuleError, match="einsatzbereit"):
        command(universe, 0, "orbit_jump", jump)
    from fur_empire.orbit_expedition import resolve

    with game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'courier',4)", (origin_id,)
        )
    mission = {**target, "galaxy": 1, "system": 1, "slot": 2, "count": 4}
    token = identity()
    launched = command(universe, 0, "orbit_expedition", mission, token)["orbit_access"]["colonies"][
        0
    ]
    assert launched["ships"]["courier"] == 0
    assert launched["expeditions"][0]["result"] is None
    assert (
        command(universe, 0, "orbit_expedition", mission, token)["orbit_access"]["colonies"][0]
        == launched
    )
    with game.transaction() as db:
        seed = db.execute("SELECT seed FROM orbit_expeditions").fetchone()[0]
    expected = resolve(seed, 4)
    clock[0] = launched["expeditions"][0]["due"] + 60
    cycle(game)
    cycle(game)
    expedition = state(universe, 0)["orbit_access"]["colonies"][0]
    assert expedition["ships"]["courier"] == 4 - expected["lost"]
    assert expedition["expeditions"][0]["result"] == expected
    assert expedition["ore_reserve"] == launched["ore_reserve"] + expected["ore"]
    assert expedition["ether_reserve"] == launched["ether_reserve"] + expected["ether"]
    clock[0] = built[0]["jumpgate"]["ready_at"]
    with pytest.raises(RuleError, match="nicht genügend"):
        command(universe, 0, "orbit_jump", {**jump, "count": 100})
    token = identity()
    jumped = command(universe, 0, "orbit_jump", jump, token)["orbit_access"]["colonies"]
    assert jumped[0]["ships"]["probe"] == 1
    assert jumped[1]["ships"]["probe"] == 2
    assert jumped[0]["jumpgate"]["cooldown_until"] == clock[0] + 21600
    assert jumped[1]["jumpgate"]["cooldown_until"] == clock[0] + 21600
    assert command(universe, 0, "orbit_jump", jump, token)["orbit_access"]["colonies"] == jumped
    with pytest.raises(RuleError, match="einsatzbereit"):
        command(universe, 0, "orbit_jump", jump)
    enemy = command(
        universe, 1, "orbit_colonize", {"world_id": 1, "galaxy": 1, "system": 1, "slot": 3}
    )
    clock[0] = enemy["orbit_access"]["claims"][0]["arrival"]
    cycle(game)
    enemy_id = state(universe, 1)["orbit_access"]["colonies"][0]["mission_id"]
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute("UPDATE orbit_economy SET ether=1000 WHERE mission_id=?", (origin_id,))
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'siege_ship',3)",
            (origin_id,),
        )
        report_id = identity()
        db.execute(
            "INSERT INTO orbit_battle_reports VALUES (?,?,?,?,?)",
            (report_id, origin_id, enemy_id, clock[0] - 86400, "{}"),
        )
        record_debris(db, report_id, enemy_id, clock[0] - 86400, 1000, 250)
        db.execute(
            "INSERT INTO orbit_intel(observer,world_id,galaxy,system_no,slot,occupied,observed_at,intel_level,moon) "
            "VALUES (?,1,1,1,3,TRUE,?,2,TRUE)",
            (users[0], clock[0]),
        )
    siege = {**target, "galaxy": 1, "system": 1, "slot": 3, "key": "siege_ship", "count": 3}
    sent = command(universe, 0, "orbit_destroy_moon", siege)["orbit_access"]["colonies"][0]
    clock[0] = sent["attacks"][0]["due"] + 60
    cycle(game)
    cycle(game)
    assert state(universe, 1)["orbit_access"]["colonies"][0]["moon_formed_at"] is None
    attackers = state(universe, 0)["orbit_access"]["colonies"][0]
    assert attackers["ships"]["siege_ship"] == 2
    assert reports(origin_id)[0]["moon_siege"] == {"destroyed": True, "demolition_ships": 1}
    outbound = command(universe, 0, "orbit_attack", {**siege, "count": 1, "retreat_pct": 20})[
        "orbit_access"
    ]["colonies"][0]["attacks"][0]
    recall = {**target, "key": outbound["id"]}
    recalled = command(universe, 0, "orbit_recall_attack", recall)["orbit_access"]["colonies"][0][
        "attacks"
    ][0]
    assert recalled["recalled"]
    assert recalled["fuel_spent"] == 44
    clock[0] = recalled["due"]
    cycle(game)
    cycle(game)
    returned_attack = state(universe, 0)["orbit_access"]["colonies"][0]
    assert returned_attack["ships"]["siege_ship"] == 2
    assert not returned_attack["attacks"]
    assert all(report["id"] != outbound["id"] for report in reports(origin_id))
    active = command(universe, 0, "orbit_attack", {**siege, "count": 1})["orbit_access"][
        "colonies"
    ][0]
    with game.transaction() as db:
        db.execute(
            "UPDATE orbit_economy SET supplied_until=? WHERE mission_id=?",
            (clock[0], origin_id),
        )
    with pytest.raises(RuleError, match="Flottenversorgung"):
        command(universe, 0, "orbit_attack", {**siege, "count": 1})
    clock[0] = active["attacks"][0]["due"] + 60
    cycle(game)
    expired = state(universe, 0)["orbit_access"]["colonies"][0]
    assert expired["ships"]["siege_ship"] == 2
    assert expired["supplied_until"] < clock[0]
    supplied = command(universe, 0, "orbit_fleet_supply", target)["orbit_access"]["colonies"][0]
    assert supplied["ether"] == expired["ether"] - 12
    assert supplied["supplied_until"] == clock[0] + 86400
    wreck_report = reports(origin_id)[0]["id"]
    with game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_wrecks(battle_id,colony_id,ship,amount,expires) VALUES (?,?,?,1,?)",
            (wreck_report, origin_id, "probe", clock[0] + 600),
        )
    repair = {**target, "key": "probe", "count": 1}
    with pytest.raises(RuleError, match="reparierbare Wracks"):
        command(universe, 0, "orbit_repair_wrecks", {**repair, "count": 2})
    token = identity()
    queued = command(universe, 0, "orbit_repair_wrecks", repair, token)["orbit_access"]["colonies"][
        0
    ]
    assert not queued["wrecks"]
    assert queued["ore"] == supplied["ore"] - 10
    assert queued["ether"] == supplied["ether"] - 6
    assert (
        command(universe, 0, "orbit_repair_wrecks", repair, token)["orbit_access"]["colonies"][0]
        == queued
    )
    clock[0] = queued["ship_order"]["due"]
    cycle(game)
    cycle(game)
    repaired = state(universe, 0)["orbit_access"]["colonies"][0]
    assert repaired["ships"]["probe"] == supplied["ships"]["probe"] + 1
    with pytest.raises(RuleError, match="reparierbare Wracks"):
        command(universe, 0, "orbit_repair_wrecks", repair)
    before_cargo = state(universe, 0)
    cargo = {**target, "orbit_ore": 100}
    token = identity()
    imported = command(universe, 0, "orbit_import_ore", cargo, token)
    origin = imported["orbit_access"]["colonies"][0]
    assert imported["resources"][2] == before_cargo["resources"][2] - 120
    assert origin["ore_reserve"] == repaired["ore_reserve"]
    assert (
        command(universe, 0, "orbit_import_ore", cargo, token)["resources"] == imported["resources"]
    )
    with pytest.raises(RuleError, match="bereits Fracht"):
        command(universe, 0, "orbit_export_ore", cargo)
    clock[0] = origin["gateway_cargo"][0]["due"]
    cycle(game)
    cycle(game)
    arrived = state(universe, 0)["orbit_access"]["colonies"][0]
    assert arrived["ore_reserve"] == origin["ore_reserve"] + 100
    assert not arrived["gateway_cargo"]
    exported = command(universe, 0, "orbit_export_ore", cargo)["orbit_access"]["colonies"][0]
    assert exported["ore"] == arrived["ore"] - 120
    clock[0] = exported["gateway_cargo"][0]["due"]
    cycle(game)
    with game.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM terra_orbit_cargo").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT COUNT(*) FROM ledger WHERE action='Orbit-Fracht eingetroffen'"
            ).fetchone()[0]
            == 1
        )
        db.execute("UPDATE orbit_economy SET screens=1 WHERE mission_id=?", (enemy_id,))
        db.execute(
            "INSERT INTO orbit_ships(mission_id,ship,amount) VALUES (?,'probe',1)", (enemy_id,)
        )
    armed = command(universe, 0, "orbit_build_ammunition", {**target, "key": "lances", "count": 2})[
        "orbit_access"
    ]["colonies"][0]
    assert armed["lances"] == 2
    dispatched = command(universe, 0, "orbit_attack", {**siege, "count": 1, "lances": 2})[
        "orbit_access"
    ]["colonies"][0]
    assert dispatched["lances"] == 0
    clock[0] = dispatched["attacks"][0]["due"]
    cycle(game)
    cycle(game)
    report = reports(origin_id)[0]
    assert report["ammunition"] == {"lances": 2, "intercepted": 1}
    assert report["opening_lances"] == 1
    assert state(universe, 1)["orbit_access"]["colonies"][0]["screens"] == 0
    from fur_empire.orbit_expedition import resolve_special

    event_payload = {"world_id": 1, "key": "anomaly"}
    with pytest.raises(RuleError, match="Nur die Spielleitung"):
        command(universe, 0, "admin_orbit_event", event_payload)
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    event = command(universe, 0, "admin_orbit_event", event_payload)["orbit_access"][
        "special_events"
    ][0]
    assert event["ends"] == clock[0] + 36 * 3600
    mission = {
        **target,
        "galaxy": 1,
        "system": 1,
        "slot": 2,
        "count": 1,
        "orbit_target": event["id"],
    }
    seed = next(
        f"{value:064x}"
        for value in range(100)
        if resolve_special(f"{value:064x}", 1, "anomaly")["ether"]
    )
    for expected in (160, 0):
        outbound = command(universe, 0, "orbit_expedition", mission)["orbit_access"]["colonies"][0][
            "expeditions"
        ][0]
        with game.transaction() as db:
            db.execute("UPDATE orbit_expeditions SET seed=? WHERE finished_at IS NULL", (seed,))
        clock[0] = outbound["due"] + 60
        cycle(game)
        cycle(game)
        result = state(universe, 0)["orbit_access"]["colonies"][0]["expeditions"][0]["result"]
        assert result["ether"] == expected
    with game.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM orbit_event_rewards").fetchone()[0] == 1
        ledger_count = db.execute(
            "SELECT COUNT(*) FROM orbit_resource_ledger WHERE colony_id=?", (origin_id,)
        ).fetchone()[0]
        current = db.execute(
            "SELECT ore,ether,ore_reserve,ether_reserve FROM orbit_economy WHERE mission_id=?",
            (origin_id,),
        ).fetchone()
        snapshot = db.execute(
            "SELECT ore,ether,ore_reserve,ether_reserve FROM orbit_resource_ledger "
            "WHERE colony_id=? ORDER BY sequence DESC LIMIT 1",
            (origin_id,),
        ).fetchone()
        assert dict(snapshot) == dict(current)
    with pytest.raises(RuntimeError, match="rollback ledger"), game.transaction() as db:
        db.execute(
            "UPDATE orbit_economy SET ore_reserve=ore_reserve+1 WHERE mission_id=?", (origin_id,)
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM orbit_resource_ledger WHERE colony_id=?", (origin_id,)
            ).fetchone()[0]
            == ledger_count + 1
        )
        raise RuntimeError("rollback ledger")
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM orbit_resource_ledger WHERE colony_id=?", (origin_id,)
            ).fetchone()[0]
            == ledger_count
        )
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM orbit_resource_ledger WHERE colony_id=?", (origin_id,))
    with game.transaction() as db:
        for _ in range(11):
            db.execute(
                "INSERT INTO orbit_battle_reports VALUES (?,?,?,?,?)",
                (identity(), origin_id, enemy_id, clock[0], "{}"),
            )
        first_page = report_page(db, origin_id)
        second_page = report_page(db, origin_id, first_page["before"])
        assert len(first_page["reports"]) == 10
        assert {row["id"] for row in first_page["reports"]}.isdisjoint(
            row["id"] for row in second_page["reports"]
        )
        with pytest.raises(ValueError, match="Berichtscursor"):
            report_page(db, target_id, first_page["before"])


def test_orbit_unlock_debits_once_and_stays_in_its_world(universe):
    game, users, _ = universe
    with pytest.raises(RuleError, match="Kommandozentrale"):
        command(universe, 0, "orbit_unlock")
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=8, depot=4)
        colony["tech"].update(engineering=8, logistics=8)
        colony["resources"] = [8000, 8000, 8000]
        game.save(db, colony)
        other = game.create_world(db, "Orbit isolation", 48192, 8)
    token = identity()
    unlocked = command(universe, 0, "orbit_unlock", token=token)
    assert unlocked["orbit_access"]["unlocked"]
    assert unlocked["resources"] == [4700, 5200, 2700]
    assert command(universe, 0, "orbit_unlock", token=token)["resources"] == unlocked["resources"]
    with pytest.raises(RuleError, match="bereits freigeschaltet"):
        command(universe, 0, "orbit_unlock")
    assert not state(universe, 1)["orbit_access"]["unlocked"]
    preset = {"world_id": 1, "name": "Vorhut", "key": "probe", "count": 4, "retreat_pct": 25}
    token = identity()
    saved = command(universe, 0, "orbit_save_fleet_template", preset, token)
    template = saved["orbit_access"]["templates"][0]
    assert (template["ship"], template["amount"], template["retreat_pct"]) == ("probe", 4, 25)
    assert saved["resources"] == unlocked["resources"]
    assert command(universe, 0, "orbit_save_fleet_template", preset, token)["orbit_access"][
        "templates"
    ] == [template]
    with pytest.raises(RuleError, match="bereits vergeben"):
        command(universe, 0, "orbit_save_fleet_template", {**preset, "name": "VORHUT"})
    joined = command(universe, 0, "world_join", {"world_id": other})
    assert not joined["orbit_access"]["unlocked"]
    assert not joined["orbit_access"]["templates"]
    with pytest.raises(RuleError, match="nicht verfügbar"):
        command(universe, 0, "orbit_delete_template", {"world_id": other, "key": template["id"]})
    command(universe, 0, "world_select", {"world_id": 1})
    deleted = command(universe, 0, "orbit_delete_template", {"world_id": 1, "key": template["id"]})
    assert not deleted["orbit_access"]["templates"]


def test_world_catalog_pins_snapshot_and_rejects_in_place_changes(universe, monkeypatch):
    game, _, _ = universe
    with game.transaction() as db:
        world_id = game.create_world(db, "Catalog frontier", 48192, 8)
        rows = db.execute(
            "SELECT w.world_id,c.version,c.snapshot,c.digest FROM world_rulesets w "
            "JOIN rule_catalogs c ON c.version=w.version ORDER BY w.world_id"
        ).fetchall()
        assert [row["world_id"] for row in rows] == [1, world_id]
        for row in rows:
            assert row["version"] == REGISTRY["version"]
            assert row["snapshot"] == RULES_SNAPSHOT
            assert row["digest"] == RULES_DIGEST
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("UPDATE rule_catalogs SET digest='changed'")
    with pytest.raises(Exception, match="immutable"), game.transaction() as db:
        db.execute("DELETE FROM world_rulesets WHERE world_id=?", (world_id,))
    monkeypatch.setattr("fur_empire.game.RULES_DIGEST", "changed")
    with pytest.raises(RuleError, match="Regelkatalog weicht"):
        Game(game.path)


def test_sandbox_blocks_pvp_and_seasons_without_changing_genesis(universe):
    game, users, clock = universe
    with game.transaction() as db:
        sandbox = game.create_world(db, "Training frontier", 48192, 8, True, "sandbox")
        game.join_world(db, users[0], "Alpha", sandbox)
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        assert game.systems.pvp_enabled(db, 1)
        assert not game.systems.pvp_enabled(db, sandbox)
        with pytest.raises(RuleError, match="Spielerangriffe"):
            game.systems.can_attack(db, users[0], users[1], clock[0], sandbox)
    with pytest.raises(RuleError, match="ohne Saisonwettbewerb"):
        command(
            universe,
            0,
            "admin_season",
            {"name": "Training season", "days": 1, "goal_score": 10000},
        )


def test_world_events_and_season_archive_are_isolated(universe):
    game, users, clock = universe
    with game.transaction() as db:
        genesis_before = game.read(db, users[0])
        genesis_colony_id = str(genesis_before["colony_id"])
        world_id = game.create_world(db, "Season frontier", 48192, 8, True, "season")
        game.join_world(db, users[0], "Alpha", world_id)
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    state = command(
        universe,
        0,
        "admin_event",
        {
            "name": "Frontier boost",
            "hours": 1,
            "bonus": 20,
            "warning_hours": 1,
            "end_hours": 1,
            "end_bonus": 40,
            "goal_score": 10000,
        },
    )
    assert state["active_world"]["mode"] == "season"
    assert any(event["name"] == "Frontier boost" for event in state["events"])
    with game.transaction() as db:
        events, _ = game.systems.live_event_page(db, clock[0], world_id=1)
        assert all(event["name"] != "Frontier boost" for event in events)
    command(
        universe,
        0,
        "admin_season",
        {"name": "Frontier season", "days": 1, "goal_score": 10000},
    )
    clock[0] += 86400
    with pytest.raises(RuleError, match="beendete Saisonwelt"), game.transaction() as db:
        game.join_world(db, users[1], "Beta", world_id)
    cycle(game)
    with pytest.raises(RuleError, match="beendete Saisonwelt"):
        command(universe, 0, "world_update", {"world_id": world_id, "joinable": True})
    with pytest.raises(RuleError, match="neue Saisonwelt"):
        command(
            universe,
            0,
            "admin_season",
            {"name": "Second season", "days": 1, "goal_score": 10000},
        )
    with game.transaction() as db:
        season = db.execute(
            "SELECT archived,standings FROM seasons WHERE world_id=?", (world_id,)
        ).fetchone()
        assert season["archived"]
        assert [entry["id"] for entry in json.loads(season["standings"])] == [users[0]]
        assert not db.execute(
            "SELECT joinable FROM world_settings WHERE world_id=?", (world_id,)
        ).fetchone()[0]
        genesis_after_row = db.execute(
            "SELECT colony_id,state FROM colonies WHERE user_id=? AND world_id=1",
            (users[0],),
        ).fetchone()
        genesis_after = json.loads(genesis_after_row["state"])
        assert genesis_after_row["colony_id"] == genesis_colony_id
        assert genesis_after["buildings"] == genesis_before["buildings"]
        assert genesis_after["units"] == genesis_before["units"]
        assert all(
            after >= before
            for after, before in zip(genesis_after["resources"], genesis_before["resources"])
        )
        assert not db.execute("SELECT 1 FROM seasons WHERE world_id=1").fetchone()


def test_admin_can_start_seasons_only_in_season_worlds(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    with pytest.raises(RuleError, match="nur in Saisonwelten"):
        command(
            universe,
            0,
            "admin_season",
            {"name": "Permanent season", "days": 30, "goal_score": 10000},
        )
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM seasons").fetchone()[0] == 0


def test_directive_claims_are_scoped_to_the_active_world(universe):
    game, users, _clock = universe
    user = users[0]
    with game.transaction() as db:
        genesis = game.read(db, user)
        for key in ("wood", "stone", "ore"):
            genesis["buildings"][key] = 2
        game.save(db, genesis)

        season_world = game.create_world(db, "Directive Season", 518_210, 8, True, "season")
        game.join_world(db, user, "Alpha in Season", season_world)
        seasonal = game.read(db, user)
        assert seasonal["world_id"] == season_world
        assert seasonal["claimed"] == []
        for key in ("wood", "stone", "ore"):
            seasonal["buildings"][key] = 2
        game.save(db, seasonal)

        claimed_season = game.command(db, user, "quest", {"key": "economy"}, identity())
        assert claimed_season["world_id"] == season_world
        assert "economy" in claimed_season["claimed"]

        db.execute(
            "UPDATE profiles SET active_colony_id=?,active_world_id=1 WHERE user_id=?",
            (genesis["colony_id"], user),
        )
        permanent = game.read(db, user)
        assert permanent["world_id"] == 1
        assert "economy" not in permanent["claimed"]


@pytest.mark.parametrize(
    ("faction", "research", "unit", "foreign_unit"),
    [
        ("pioneers", "adaptive_forestry", "terraformer_drone", "shield_sentinel"),
        ("pioneers", "adaptive_forestry", "frontier_vanguard", "covert_courier"),
        ("wardens", "kinetic_shield", "shield_sentinel", "covert_courier"),
        ("wardens", "kinetic_shield", "bastion_walker", "salvage_engineer"),
        ("syndicate", "smuggler_navigation", "covert_courier", "terraformer_drone"),
        ("syndicate", "smuggler_navigation", "salvage_engineer", "frontier_vanguard"),
    ],
)
def test_faction_unit_training_is_world_and_research_scoped(
    universe, faction, research, unit, foreign_unit
):
    game, users, clock = universe
    with game.transaction() as db:
        colony = game.read(db, users[0])
        colony["buildings"].update(hq=4, barracks=4, storage=4)
        colony["resources"] = [5000, 5000, 5000]
        game.save(db, colony)

    command(universe, 0, "faction", {"key": faction})
    with pytest.raises(RuleError, match="Spezialforschung"):
        command(universe, 0, "train", {"key": unit, "count": 2})

    queued = command(universe, 0, "terra_faction_research", {"key": research})
    clock[0] = next(job["due"] for job in queued["jobs"] if job["kind"] == "terra_faction_research")
    cycle(game)

    with pytest.raises(RuleError, match="Spezialforschung"):
        command(universe, 0, "train", {"key": foreign_unit, "count": 2})

    token = identity()
    payload = {"key": unit, "count": 2}
    queued = command(universe, 0, "train", payload, token)
    replay = command(universe, 0, "train", payload, token)
    assert replay["resources"] == queued["resources"]
    assert replay["units"][unit] == 0
    clock[0] = next(job["due"] for job in queued["jobs"] if job["kind"] == "train")
    cycle(game)
    cycle(game)
    assert state(universe, 0)["units"][unit] == 2


@pytest.mark.parametrize(
    ("research", "expected"),
    [([], 28), (["rapid_construction"], 25)],
)
def test_rapid_construction_duration(research, expected):
    colony = {"buildings": {"hq": 4}, "faction_research": research}
    assert Game.construction_duration(colony, 4) == expected
    assert Game.construction_duration(colony, 1) >= 3


def test_bastion_protocol_strengthens_only_warden_wall(universe):
    game, _, _ = universe
    colony = {
        "buildings": {"wall": 2},
        "units": {},
        "tech": {"tactics": 0},
        "terrain": "plain",
        "faction_chosen": True,
        "faction_research": [],
    }
    baseline = game.systems.player_defense(colony, "wardens")
    colony["faction_research"] = ["bastion_protocol"]
    assert game.systems.player_defense(colony, "wardens") == baseline + 24
    assert game.systems.player_defense(colony, "pioneers") == 290
    colony["buildings"]["wall"] = 0
    assert game.systems.player_defense(colony, "wardens") == 50


def test_allied_garrison_rules_are_versioned_and_bound_capacity():
    import copy

    terra_garrison.validate_rules(terra_garrison.RULES)
    assert terra_garrison.VERSION == "FUR-3-TERRA-ALLIED-GARRISON-1"
    assert terra_garrison.DIGEST.startswith("sha256:")
    invalid = copy.deepcopy(terra_garrison.RULES)
    invalid["capacity_units_per_home_colony"] = 301
    with pytest.raises(ValueError, match="capacity"):
        terra_garrison.validate_rules(invalid)


def test_terra_alliance_rules_keep_fur2_rounding_and_conserve_integer_loot():
    wings = [
        {"army": {"ranger": 1}, "tactics": 0},
        {"army": {"ranger": 1}, "tactics": 1},
    ]
    result = terra_alliance.resolve(wings, {}, neutral_tier=1)
    assert result["power"] == 25  # 12 + floor(12 * 1.15), rounded per commander as FUR-2.
    assert terra_alliance.allocate_amount(11, [1, 2, 3], ["b", "c", "a"]) == [2, 4, 5]
    assert sum(terra_alliance.allocate_amount(100, [1, 2, 3], ["a", "b", "c"])) == 100


def test_terra_alliance_attack_escrows_resolves_and_returns_every_wing(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 20}},
    )
    with game.transaction() as db:
        operation = db.execute("SELECT * FROM terra_alliance_attacks").fetchone()
        assert operation["status"] == "assembling"
        attack_id = str(operation["id"])
        assert game.read(db, users[0])["units"]["ranger"] == 80
        assert game.view(db, users[2])["terra_alliance_attacks"] == []
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 20}},
    )
    with game.transaction() as db:
        operation = db.execute(
            "SELECT due,max_travel FROM terra_alliance_attacks WHERE id=?", (attack_id,)
        ).fetchone()
        wings = db.execute(
            "SELECT user_id,colony_id,travel_seconds FROM terra_alliance_attack_wings "
            "WHERE attack_id=? ORDER BY user_id",
            (attack_id,),
        ).fetchall()
        assert len(wings) == 2
        assert operation["due"] == clock[0] + 300 + operation["max_travel"]
        due = int(operation["due"])
    clock[0] = due
    with game.transaction() as db:
        game.advance(db, due)
        result = db.execute(
            "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
        ).fetchone()
        assert result["status"] == "resolved"
        returning = db.execute(
            "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='returning'",
            (attack_id,),
        ).fetchone()[0]
        assert returning == 2
        return_due = max(
            int(job["due"])
            for row in db.execute("SELECT state FROM colonies WHERE user_id IN (?,?)", users[:2])
            for job in json.loads(row["state"])["jobs"]
            if job.get("alliance_attack_id") == attack_id
        )
    clock[0] = return_due
    with game.transaction() as db:
        game.advance(db, return_due)
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='returned'",
                (attack_id,),
            ).fetchone()[0]
            == 2
        )
        for user in users[:2]:
            colony = game.read(db, user)
            assert colony["units"]["ranger"] > 80
            assert not any(job.get("alliance_attack_id") == attack_id for job in colony["jobs"])


def test_fur3_acs_pins_combat_and_returns_participant_attributed_wings(universe):
    from fur_empire import terra_combat

    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        target_state = next(
            post for post in game.world_outposts(db, 1) if post["id"] == target["id"]
        )
        target_state["tier"] = 2
        target_state["units"] = {"sentinel": 8}
        posts = game.world_outposts(db, 1)
        next(post for post in posts if post["id"] == target["id"]).update(target_state)
        game.save_world_outposts(db, 1, posts)
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-2",),
        )

    created = command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 30}},
    )
    attack_id = next(
        mission["alliance_attack_id"]
        for mission in created["jobs"]
        if mission["kind"] == "alliance_attack"
    )
    leader_mission = next(
        mission for mission in created["jobs"] if mission["kind"] == "alliance_attack"
    )
    assert "seed_commitment" not in leader_mission
    assert "seed" not in leader_mission
    with game.transaction() as db:
        attack = db.execute(
            "SELECT rule_version,due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
        ).fetchone()
        assert attack["rule_version"] == "FUR-3-TERRA-ACS-3"
        replay = db.execute(
            "SELECT rules_version,rules_digest,resolved FROM terra_combat_missions "
            "WHERE mission_id=?",
            (attack_id,),
        ).fetchone()
        assert replay["rules_version"] == "FUR-3-TERRA-COMBAT-2"
        assert replay["rules_digest"] == terra_combat.RULESET_DIGESTS[replay["rules_version"]]
        assert replay["resolved"] is None

    command(universe, 1, "alliance_attack_join", {"key": attack_id, "army": {"ranger": 30}})
    with game.transaction() as db:
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()["due"]
        )
    clock[0] = due
    with game.transaction() as db:
        game.advance(db, due)
        replay_text = db.execute(
            "SELECT replay FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
        ).fetchone()["replay"]
        report_count = len(
            [
                report
                for report in game.read(db, users[0])["reports"]
                if report.get("combat", {}).get("alliance_rules_version") == "FUR-3-TERRA-ACS-3"
            ]
        )
        game.advance(db, due)
        assert (
            db.execute(
                "SELECT replay FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
            ).fetchone()["replay"]
            == replay_text
        )
        assert (
            len(
                [
                    report
                    for report in game.read(db, users[0])["reports"]
                    if report.get("combat", {}).get("alliance_rules_version") == "FUR-3-TERRA-ACS-3"
                ]
            )
            == report_count
        )
        replay = db.execute(
            "SELECT resolved,replay FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
        ).fetchone()
        assert replay["resolved"] == due
        result = json.loads(replay["replay"])
        assert result["rules_version"] == "FUR-3-TERRA-COMBAT-2"
        assert len(result["wing_survivors"]) == 2
        for user in users[:2]:
            colony = game.read(db, user)
            report = next(
                item
                for item in colony["reports"]
                if item.get("combat", {}).get("alliance_rules_version") == "FUR-3-TERRA-ACS-3"
            )
            assert report["combat"]["seed"] == result["seed"]
            assert report["combat"]["seed_commitment"] == result["seed_commitment"]
            rounds = report["combat"]["rounds"]
            assert len(rounds) == len(result["rounds"])
            assert all(len(round["attacker_wings"]) == 2 for round in rounds)
            assert all(
                "outpost_fortification" not in round["attacker_wings"][index]["sent"]
                for round in rounds
                for index in (0, 1)
            )
        return_due = max(
            int(job["due"])
            for row in db.execute("SELECT state FROM colonies WHERE user_id IN (?,?)", users[:2])
            for job in json.loads(row["state"])["jobs"]
            if job.get("alliance_attack_id") == attack_id
        )
    clock[0] = return_due
    with game.transaction() as db:
        game.advance(db, return_due)
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='returned'",
                (attack_id,),
            ).fetchone()[0]
            == 2
        )


def test_terra_alliance_attack_ignores_zero_count_locked_catalog_units(universe):
    game, users, _ = universe
    target = prepare_terra_alliance_target(universe)
    army = {unit: 0 for unit in UNITS}
    army["ranger"] = 10

    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": army},
    )

    with game.transaction() as db:
        wing = db.execute(
            "SELECT army FROM terra_alliance_attack_wings WHERE user_id=?", (users[0],)
        ).fetchone()
        assert json.loads(wing["army"]) == {"ranger": 10}
        assert game.read(db, users[0])["units"]["ranger"] == 90


def test_terra_alliance_attack_cancellation_refunds_every_escrowed_unit(universe):
    game, users, _ = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 10}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 15}},
    )
    command(universe, 1, "alliance_attack_withdraw", {"key": attack_id})
    with game.transaction() as db:
        assert game.read(db, users[1])["units"]["ranger"] == 100
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attack_wings WHERE attack_id=? AND user_id=?",
                (attack_id, users[1]),
            ).fetchone()[0]
            == "withdrawn"
        )
    command(universe, 0, "alliance_attack_cancel", {"key": attack_id})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()["status"]
            == "cancelled"
        )
        for user, initial in ((users[0], 100), (users[1], 100)):
            assert game.read(db, user)["units"]["ranger"] == initial
            assert not any(
                job.get("alliance_attack_id") == attack_id for job in game.read(db, user)["jobs"]
            )
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='withdrawn'",
                (attack_id,),
            ).fetchone()[0]
            == 2
        )


def test_fur3_acs_cancellation_discards_unresolved_combat_seed(universe):
    game, users, _clock = universe
    target = prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-1",),
        )
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 20}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
        assert db.execute(
            "SELECT 1 FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
        ).fetchone()
    command(universe, 0, "alliance_attack_cancel", {"key": attack_id})
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT 1 FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
            ).fetchone()
            is None
        )
        assert game.read(db, users[0])["units"]["ranger"] == 100


def test_terra_alliance_attack_rechecks_leader_protection_and_returns_intact(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 11}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 13}},
    )
    with game.transaction() as db:
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
        )
        leader = game.read(db, users[0])
        leader["vacation_until"] = due + 3600
        game.save(db, leader)
    clock[0] = due
    with game.transaction() as db:
        game.advance(db, due)
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
            == "resolved"
        )
        return_due = due
        for user, expected, expected_army in (
            (users[0], 89, 11),
            (users[1], 87, 13),
        ):
            colony = game.read(db, user)
            assert colony["units"]["ranger"] == expected
            return_job = next(
                job
                for job in colony["jobs"]
                if job.get("alliance_attack_id") == attack_id and job["kind"] == "return"
            )
            assert return_job["army"] == {"ranger": expected_army}
            return_due = max(return_due, int(return_job["due"]))

    clock[0] = return_due
    with game.transaction() as db:
        game.advance(db, return_due)
        for user in users[:2]:
            colony = game.read(db, user)
            assert colony["units"]["ranger"] == 100
            assert not any(
                job.get("alliance_attack_id") == attack_id and job["kind"] == "return"
                for job in colony["jobs"]
            )


def test_terra_alliance_attack_returns_intact_when_member_leaves_before_arrival(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 10}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 12}},
    )
    with game.transaction() as db:
        db.execute("DELETE FROM members WHERE user_id=?", (users[1],))
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
        )
    clock[0] = due
    with game.transaction() as db:
        game.advance(db, due)
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
            == "resolved"
        )
        statuses = {
            str(row["user_id"]): str(row["status"])
            for row in db.execute(
                "SELECT user_id,status FROM terra_alliance_attack_wings WHERE attack_id=?",
                (attack_id,),
            ).fetchall()
        }
        assert set(statuses.values()) == {"returning"}
        for index, user in enumerate(users[:2]):
            colony = game.read(db, user)
            return_job = next(
                job for job in colony["jobs"] if job.get("alliance_attack_id") == attack_id
            )
            assert return_job["kind"] == "return"
            assert return_job["army"] == {"ranger": (10, 12)[index]}
            assert colony["units"]["ranger"] == 90 if index == 0 else 88
            assert not any(
                report["title"] == "Allianzangriff gewonnen" for report in colony["reports"]
            )


def test_terra_alliance_attack_returns_intact_if_locked_outpost_changes_owner(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 10}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 12}},
    )
    with game.transaction() as db:
        posts = game.world_outposts(db, 1)
        changed = next(post for post in posts if post["id"] == target["id"])
        changed["owner"] = users[2]
        changed["cleared"] = True
        game.save_world_outposts(db, 1, posts)
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
        )
    clock[0] = due
    with game.transaction() as db:
        game.advance(db, due)
        post_after = next(post for post in game.world_outposts(db, 1) if post["id"] == target["id"])
        assert post_after["owner"] == users[2]
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
            == "resolved"
        )
        for user, expected in ((users[0], 10), (users[1], 12)):
            colony = game.read(db, user)
            return_job = next(
                job for job in colony["jobs"] if job.get("alliance_attack_id") == attack_id
            )
            assert return_job["kind"] == "return"
            assert return_job["army"] == {"ranger": expected}


def test_terra_alliance_attack_rejects_join_after_assembly_lock(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 10}},
    )
    with game.transaction() as db:
        operation = db.execute("SELECT * FROM terra_alliance_attacks").fetchone()
        attack_id = str(operation["id"])
        join_until = int(operation["join_until"])
    clock[0] = join_until
    with pytest.raises(RuleError, match="nicht mehr offen"):
        command(
            universe,
            1,
            "alliance_attack_join",
            {"key": attack_id, "army": {"ranger": 12}},
        )
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=?", (attack_id,)
            ).fetchone()[0]
            == 1
        )
        assert game.read(db, users[1])["units"]["ranger"] == 100
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
            == "assembling"
        )


def test_terra_alliance_attack_enforces_twelve_member_limit(universe):
    game, users, _ = universe
    target = prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        alliance_id = str(
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (users[0],)).fetchone()[0]
        )
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 1}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])

    extra_users = []
    with game.transaction() as db:
        for index in range(10):
            user_id = identity()
            name = f"ACSMember{index:02d}"
            extra_users.append(user_id)
            db.execute("INSERT INTO users VALUES (?,?,?)", (user_id, name, "unused"))
            game.create(db, user_id, name)
            db.execute(
                "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
                (user_id, alliance_id, "member"),
            )

    # One existing member plus ten new accounts reaches twelve total wings.
    for user_id in (users[1], *extra_users):
        with game.transaction() as db:
            game.command(
                db,
                user_id,
                "alliance_attack_join",
                {"key": attack_id, "army": {"ranger": 1}},
                identity(),
            )

    overflow_user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (overflow_user, "ACSOverflow", "unused"))
        game.create(db, overflow_user, "ACSOverflow")
        db.execute(
            "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
            (overflow_user, alliance_id, "member"),
        )
    with pytest.raises(RuleError, match="maximale Teilnehmerzahl"), game.transaction() as db:
        game.command(
            db,
            overflow_user,
            "alliance_attack_join",
            {"key": attack_id, "army": {"ranger": 1}},
            identity(),
        )
    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='active'",
                (attack_id,),
            ).fetchone()[0]
            == 12
        )
        assert game.read(db, overflow_user)["units"]["ranger"] == 15


def test_terra_alliance_player_attack_uses_current_server_defense_and_updates_defender(universe):
    game, users, clock = universe
    prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
        db.execute(
            "UPDATE profiles SET joined=? WHERE user_id IN (?,?)",
            (clock[0] - 7200, users[0], users[2]),
        )
        leader, wing = game.read(db, users[0]), game.read(db, users[1])
        defender = game.read(db, users[2])
        defender["units"]["ranger"] = 3
        defender["terra_defense_stacks"] = {
            "kinetic_turret": [100],
            "proximity_mines": [100],
        }
        defender["terra_defense_rules_version"] = terra_defense.VERSION
        defender["terra_defense_rules_digest"] = terra_defense.DIGEST
        game.save(db, defender)
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[0], 1, defender["x"], defender["y"], clock[0]),
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
            (users[1], 1, defender["x"], defender["y"], clock[0]),
        )
        attack_target = {"id": users[2], "x": defender["x"], "y": defender["y"]}
        leader_reachable = travel_times(db, (leader["x"], leader["y"]), 1)
        wing_reachable = travel_times(db, (wing["x"], wing["y"]), 1)
        leader_costs = travel_costs(db, (leader["x"], leader["y"]), 1)
        wing_costs = travel_costs(db, (wing["x"], wing["y"]), 1)
        posts = {(post["x"], post["y"]) for post in game.world_outposts(db, 1)}
        occupied = {(leader["x"], leader["y"]), (wing["x"], wing["y"])} | posts
        candidates = sorted(
            point
            for point in leader_reachable
            if point in wing_reachable
            and point not in occupied
            and leader_costs[point] <= 120
            and wing_costs[point] <= 120
        )
        if (attack_target["x"], attack_target["y"]) not in candidates:
            point = candidates[0]
            defender["x"], defender["y"] = point
            db.execute(
                "UPDATE colonies SET x=?,y=? WHERE colony_id=?", (*point, defender["colony_id"])
            )
            game.save(db, defender)
            attack_target["x"], attack_target["y"] = point
            for attacker in (users[0], users[1]):
                db.execute(
                    "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) VALUES (?,?,?,?,?)",
                    (attacker, 1, point[0], point[1], clock[0]),
                )
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": users[2], "target_kind": "player", "army": {"ranger": 100}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 100}},
    )
    with game.transaction() as db:
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
        )
    clock[0] = due
    with game.transaction() as db:
        before = game.read(db, users[2])["units"]["ranger"]
        game.advance(db, due)
        defender_after = game.read(db, users[2])
        assert defender_after["units"]["ranger"] < before
        assert any(
            report["title"] == "Verteidigung durchbrochen" for report in defender_after["reports"]
        )
        report = next(
            report
            for report in defender_after["reports"]
            if report.get("combat", {}).get("alliance_rules_version") == "FUR-3-TERRA-ACS-3"
        )
        assert report["combat"]["terra_defense"]["digest"] == terra_defense.DIGEST
        replay_row = db.execute(
            "SELECT replay FROM terra_combat_missions WHERE mission_id=?", (attack_id,)
        ).fetchone()
        replay = json.loads(replay_row["replay"])
        assert replay["terra_defense"] == report["combat"]["terra_defense"]
        assert defender_after["terra_defense_stacks"] == replay["terra_defense"]["remaining_stacks"]


def test_terra_alliance_attack_creation_is_idempotent_under_parallel_retry(universe):
    game, users, _ = universe
    target = prepare_terra_alliance_target(universe)
    token = identity()
    payload = {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 21}}
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(
                lambda _: command(universe, 0, "alliance_attack_create", payload, token),
                range(6),
            )
        )
    with game.transaction() as db:
        assert len(results) == 6
        assert db.execute("SELECT count(*) FROM terra_alliance_attacks").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM terra_alliance_attack_wings").fetchone()[0] == 1
        assert game.read(db, users[0])["units"]["ranger"] == 79
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_attack_create'",
                (users[0],),
            ).fetchone()[0]
            == 1
        )


def test_terra_alliance_attack_resolution_retry_does_not_duplicate_returns_or_reports(universe):
    game, users, clock = universe
    target = prepare_terra_alliance_target(universe)
    command(
        universe,
        0,
        "alliance_attack_create",
        {"key": target["id"], "target_kind": "outpost", "army": {"ranger": 30}},
    )
    with game.transaction() as db:
        attack_id = str(db.execute("SELECT id FROM terra_alliance_attacks").fetchone()["id"])
    command(
        universe,
        1,
        "alliance_attack_join",
        {"key": attack_id, "army": {"ranger": 30}},
    )
    with game.transaction() as db:
        due = int(
            db.execute(
                "SELECT due FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
        )
    clock[0] = due
    for _ in range(2):
        with game.transaction() as db:
            game.advance(db, due)

    with game.transaction() as db:
        assert (
            db.execute(
                "SELECT status FROM terra_alliance_attacks WHERE id=?", (attack_id,)
            ).fetchone()[0]
            == "resolved"
        )
        for user in users[:2]:
            colony = game.read(db, user)
            returns = [job for job in colony["jobs"] if job.get("alliance_attack_id") == attack_id]
            assert len(returns) == 1
            assert returns[0]["kind"] == "return"
            assert (
                sum(
                    report.get("combat", {}).get("alliance_rules_version") == terra_alliance.VERSION
                    for report in colony["reports"]
                )
                == 1
            )
            assert (
                db.execute(
                    "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_attack_resolved' "
                    "AND target=?",
                    (user, attack_id),
                ).fetchone()[0]
                == 1
            )
        assert (
            db.execute(
                "SELECT count(*) FROM terra_alliance_attack_wings WHERE attack_id=? AND status='returning'",
                (attack_id,),
            ).fetchone()[0]
            == 2
        )


def test_terra_alliance_attack_schema_73_migration_preserves_existing_game_state(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colony_before = db.execute(
            "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id", (users[0],)
        ).fetchall()
        outpost_before = db.execute(
            "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY target_id"
        ).fetchall()
        db.execute("DROP TABLE terra_alliance_attack_wings")
        db.execute("DROP TABLE terra_alliance_attacks")
        db.execute("DELETE FROM schema_versions WHERE version=73")
        from fur_empire.database import migrate

        migrate(db)
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=73").fetchone()
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id",
                (users[0],),
            )
        ] == [tuple(row) for row in colony_before]
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts WHERE world_id=1 ORDER BY target_id"
            )
        ] == [tuple(row) for row in outpost_before]


def test_terra_allied_garrison_schema_74_migration_preserves_player_state(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colony_before = db.execute(
            "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id", (users[0],)
        ).fetchall()
        db.execute("DROP TABLE terra_allied_garrisons")
        db.execute("DROP TABLE terra_allied_garrison_policies")
        db.execute("DELETE FROM schema_versions WHERE version=74")

        from fur_empire.database import migrate

        migrate(db)
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=74").fetchone()
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert db.execute("SELECT count(*) FROM terra_allied_garrisons").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM terra_allied_garrison_policies").fetchone()[0] == 0
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id",
                (users[0],),
            )
        ] == [tuple(row) for row in colony_before]


def test_terra_combat_schema_75_migration_preserves_world_and_player_state(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colony_before = db.execute(
            "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id", (users[0],)
        ).fetchall()
        outposts_before = db.execute(
            "SELECT target_id,state FROM world_outposts ORDER BY world_id,target_id"
        ).fetchall()
        db.execute("DROP TABLE terra_combat_missions")
        db.execute("ALTER TABLE world_settings DROP COLUMN terra_combat_ruleset")
        db.execute("DELETE FROM schema_versions WHERE version=75")

        from fur_empire.database import migrate

        migrate(db)
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=75").fetchone()
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert (
            db.execute(
                "SELECT terra_combat_ruleset FROM world_settings WHERE world_id=1"
            ).fetchone()[0]
            == "FUR-2"
        )
        assert db.execute("SELECT count(*) FROM terra_combat_missions").fetchone()[0] == 0
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id",
                (users[0],),
            )
        ] == [tuple(row) for row in colony_before]
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts ORDER BY world_id,target_id"
            )
        ] == [tuple(row) for row in outposts_before]


def test_terra_retreat_threshold_schema_76_migration_preserves_world_and_player_state(universe):
    game, users, _ = universe
    with game.transaction() as db:
        colony_before = db.execute(
            "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id", (users[0],)
        ).fetchall()
        outposts_before = db.execute(
            "SELECT target_id,state FROM world_outposts ORDER BY world_id,target_id"
        ).fetchall()
        db.execute("ALTER TABLE world_settings DROP COLUMN terra_retreat_threshold_percent")
        db.execute("DELETE FROM schema_versions WHERE version=76")

        from fur_empire.database import migrate

        migrate(db)
        assert db.execute("SELECT 1 FROM schema_versions WHERE version=76").fetchone()
        assert db.execute("SELECT max(version) FROM schema_versions").fetchone()[0] == 124
        assert (
            db.execute(
                "SELECT DISTINCT terra_retreat_threshold_percent FROM world_settings"
            ).fetchall()[0][0]
            == 60
        )
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=? ORDER BY colony_id",
                (users[0],),
            )
        ] == [tuple(row) for row in colony_before]
        assert [
            tuple(row)
            for row in db.execute(
                "SELECT target_id,state FROM world_outposts ORDER BY world_id,target_id"
            )
        ] == [tuple(row) for row in outposts_before]


def test_fur3_mission_pins_the_world_retreat_threshold(universe):
    game, _, clock = universe
    from fur_empire import terra_combat

    mission_id = identity()
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=?,"
            "terra_retreat_threshold_percent=37 WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        pinned = terra_combat.pin_mission(db, mission_id, 1, clock[0])
        row = db.execute(
            "SELECT retreat_threshold_percent FROM terra_combat_missions WHERE mission_id=?",
            (mission_id,),
        ).fetchone()
        assert pinned["rules_version"] == terra_combat.VERSION
        assert row["retreat_threshold_percent"] == 37


def test_terra_combat_mission_seed_stays_private_until_atomic_replay(universe):
    from fur_empire import terra_combat

    game, users, clock = universe
    mission_id = "combat-replay-test"
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        pinned = terra_combat.pin_mission(db, mission_id, 1, clock[0])
        assert pinned is not None
        assert pinned["rules_version"] == terra_combat.VERSION
        assert len(pinned["seed_commitment"]) == 64
        public_colony = db.execute(
            "SELECT state FROM colonies WHERE user_id=? AND world_id=1", (users[0],)
        ).fetchone()[0]
        assert "combat-replay-test" not in public_colony
        assert pinned["seed_commitment"] not in public_colony
        seed, threshold = terra_combat.mission_seed(db, mission_id, 1)
        replay = terra_combat.resolve(
            seed, {"ranger": 12}, {"sentinel": 2}, retreat_threshold_percent=threshold
        )
        terra_combat.store_replay(db, mission_id, replay, clock[0])
        stored = db.execute(
            "SELECT resolved,replay,seed FROM terra_combat_missions WHERE mission_id=?",
            (mission_id,),
        ).fetchone()
        assert stored["resolved"] == clock[0]
        assert json.loads(stored["replay"]) == replay
        assert json.loads(stored["replay"])["seed"] == stored["seed"]
        with pytest.raises(ValueError, match="already resolved"):
            terra_combat.mission_seed(db, mission_id, 1)
        with pytest.raises(ValueError, match="already resolved"):
            terra_combat.store_replay(db, mission_id, replay, clock[0])


def test_allied_garrison_requires_host_consent_and_stations_member_force(universe):
    game, users, clock = universe
    prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        host = game.read(db, users[0])
        host_colony_id = host["colony_id"]
    with pytest.raises(RuleError, match="freigegebene Heimatkolonie"):
        command(
            universe,
            1,
            "alliance_garrison_station",
            {"key": host_colony_id, "army": {"ranger": 5}},
        )
    command(
        universe,
        0,
        "alliance_garrison_policy",
        {"enabled": True, "capacity": 10},
    )
    command(
        universe,
        1,
        "alliance_garrison_station",
        {"key": host_colony_id, "army": {"ranger": 5}},
    )
    with game.transaction() as db:
        alliance_id = game.systems.member(db, users[0])["alliance_id"]
        db.execute(
            "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
            (users[2], alliance_id, "member"),
        )
        third = game.read(db, users[2])
        third["units"]["ranger"] = 20
        game.save(db, third)
    with pytest.raises(RuleError, match="ausgeschöpft"):
        command(
            universe,
            2,
            "alliance_garrison_station",
            {"key": host_colony_id, "army": {"ranger": 6}},
        )
    assert state(universe, 2)["units"]["ranger"] == 20
    contributor = state(universe, 1)
    arrival = next(job for job in contributor["jobs"] if job["kind"] == "alliance_garrison")
    assert contributor["units"]["ranger"] == 95
    with game.transaction() as db:
        clock[0] = int(arrival["due"])
        game.advance(db, clock[0])
        row = db.execute(
            "SELECT * FROM terra_allied_garrisons WHERE id=?", (arrival["id"],)
        ).fetchone()
        assert row
        assert json.loads(row["army"]) == {"ranger": 5}
        host_state = game.read_colony(db, host_colony_id)
        assert game.systems.active_allied_garrisons(db, host_state)
        base_defense = game.systems.player_defense(host_state, "pioneers")
        allied_defense = game.systems.fortified_player_defense(db, host_state, "pioneers", clock[0])
        assert allied_defense > base_defense
        losses = game.systems.apply_allied_garrison_losses(
            db,
            host_state,
            attack_power=500,
            defense_power=700,
            victory=False,
            at=clock[0],
        )
        assert losses[0]["losses"] == {"ranger": 3}
        assert json.loads(
            db.execute(
                "SELECT army FROM terra_allied_garrisons WHERE id=?", (arrival["id"],)
            ).fetchone()[0]
        ) == {"ranger": 2}
    command(universe, 0, "alliance_garrison_policy", {"enabled": False, "capacity": 10})
    with game.transaction() as db:
        assert not db.execute(
            "SELECT 1 FROM terra_allied_garrisons WHERE id=?", (arrival["id"],)
        ).fetchone()
        contributor = game.read(db, users[1])
        returning = next(job for job in contributor["jobs"] if job["kind"] == "return")
        assert returning["army"] == {"ranger": 2}
        clock[0] = int(returning["due"])
        game.advance(db, clock[0])
        assert game.read(db, users[1])["units"]["ranger"] == 97


def test_fur3_garrison_casualties_are_allocated_to_each_owner_exactly(universe):
    game, users, clock = universe
    host_colony_id = prepare_allied_garrison_capacity(universe, capacity=10)
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
    sent = command(
        universe,
        1,
        "alliance_garrison_station",
        {"key": host_colony_id, "army": {"ranger": 4}},
    )
    arrival = next(job for job in sent["jobs"] if job["kind"] == "alliance_garrison")
    clock[0] = int(arrival["due"])
    with game.transaction() as db:
        game.advance(db, clock[0])
        host = game.read_colony(db, host_colony_id)
        host["units"]["ranger"] = 4
        garrison = db.execute(
            "SELECT * FROM terra_allied_garrisons WHERE id=? AND status='active'",
            (arrival["id"],),
        ).fetchone()
        assert garrison is not None
        host_survivors, garrison_losses = game.systems.apply_allied_garrison_casualties(
            db,
            host,
            [garrison],
            {"ranger": 4},
            at=clock[0],
            rule_version="FUR-3-TERRA-COMBAT-4",
        )
        assert host_survivors["ranger"] == 2
        assert garrison_losses == [
            {"garrison_id": arrival["id"], "contributor": users[1], "losses": {"ranger": 2}}
        ]
        stored = db.execute(
            "SELECT army FROM terra_allied_garrisons WHERE id=?", (arrival["id"],)
        ).fetchone()
        assert json.loads(stored["army"]) == {"ranger": 2}
        contributor = game.read_colony(db, users[1])
        assert contributor["units"]["ranger"] == 96
        assert any(
            report["title"] == "Alliierte Garnison im Kampf" for report in contributor["reports"]
        )


def test_allied_garrison_recall_survives_contributor_command_save(universe):
    game, users, clock = universe
    prepare_terra_alliance_target(universe)
    command(universe, 0, "alliance_garrison_policy", {"enabled": True, "capacity": 10})
    with game.transaction() as db:
        host = game.read(db, users[0])
        host_colony_id = host["colony_id"]
    command(
        universe,
        1,
        "alliance_garrison_station",
        {"key": host_colony_id, "army": {"ranger": 5}},
    )
    with game.transaction() as db:
        contributor = game.read(db, users[1])
        arrival = next(job for job in contributor["jobs"] if job["kind"] == "alliance_garrison")
        clock[0] = int(arrival["due"])
        game.advance(db, clock[0])
        active = db.execute(
            "SELECT id FROM terra_allied_garrisons WHERE contributor_id=? AND status='active'",
            (users[1],),
        ).fetchone()
        assert active

        garrison_id = str(active["id"])
    command(universe, 1, "alliance_garrison_recall", {"key": garrison_id})
    with game.transaction() as db:
        persisted = game.read(db, users[1])
        returning = next(job for job in persisted["jobs"] if job["kind"] == "return")
        assert returning["army"] == {"ranger": 5}

        clock[0] = int(returning["due"])
        game.advance(db, clock[0])
        assert game.read(db, users[1])["units"]["ranger"] == 100


def prepare_allied_garrison_capacity(universe, capacity=5):
    game, users, _ = universe
    prepare_terra_alliance_target(universe)
    with game.transaction() as db:
        alliance_id = str(
            db.execute("SELECT alliance_id FROM members WHERE user_id=?", (users[0],)).fetchone()[0]
        )
        db.execute(
            "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
            (users[2], alliance_id, "member"),
        )
        host = game.read(db, users[0])
        host_id = str(host["colony_id"])
        other = game.read(db, users[2])
        other["units"]["ranger"] = 10
        game.save(db, other)
    command(universe, 0, "alliance_garrison_policy", {"enabled": True, "capacity": capacity})
    return host_id


def test_allied_garrison_parallel_capacity_reservation_never_overbooks(universe):
    game, users, _ = universe
    host_id = prepare_allied_garrison_capacity(universe, capacity=5)

    def deploy(index):
        try:
            command(
                universe,
                index,
                "alliance_garrison_station",
                {"key": host_id, "army": {"ranger": 4}},
                identity(),
            )
            return True
        except RuleError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted = list(pool.map(deploy, (1, 2)))
    assert sum(accepted) == 1
    with game.transaction() as db:
        rows = db.execute(
            "SELECT army,status FROM terra_allied_garrisons WHERE host_colony_id=?",
            (host_id,),
        ).fetchall()
        assert len(rows) == 1
        assert sum(json.loads(rows[0]["army"]).values()) == 4
        assert rows[0]["status"] == "travelling"
        for index, was_accepted in ((1, accepted[0]), (2, accepted[1])):
            initial = 100 if index == 1 else 10
            expected = initial - 4 if was_accepted else initial
            assert game.read(db, users[index])["units"]["ranger"] == expected


def test_allied_garrison_parallel_command_replay_escrows_once(universe):
    game, users, _ = universe
    host_id = prepare_allied_garrison_capacity(universe, capacity=10)
    token = identity()
    payload = {"key": host_id, "army": {"ranger": 4}}
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(
                lambda _: command(universe, 1, "alliance_garrison_station", payload, token),
                range(6),
            )
        )
    assert len(results) == 6
    with game.transaction() as db:
        rows = db.execute(
            "SELECT id,army FROM terra_allied_garrisons WHERE contributor_id=? AND host_colony_id=?",
            (users[1], host_id),
        ).fetchall()
        assert len(rows) == 1
        assert json.loads(rows[0]["army"]) == {"ranger": 4}
        assert game.read(db, users[1])["units"]["ranger"] == 96
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_garrison_station'",
                (users[1],),
            ).fetchone()[0]
            == 1
        )


def test_allied_garrison_arrival_retry_creates_one_active_garrison(universe):
    game, users, clock = universe
    host_id = prepare_allied_garrison_capacity(universe, capacity=10)
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
    command(
        universe,
        1,
        "alliance_garrison_station",
        {"key": host_id, "army": {"ranger": 4}},
    )
    with game.transaction() as db:
        source = game.read(db, users[1])
        mission = next(job for job in source["jobs"] if job["kind"] == "alliance_garrison")
        due = int(mission["due"])
    clock[0] = due
    for _ in range(2):
        with game.transaction() as db:
            game.advance(db, due)
    with game.transaction() as db:
        rows = db.execute(
            "SELECT id,army,status FROM terra_allied_garrisons "
            "WHERE contributor_id=? AND host_colony_id=?",
            (users[1], host_id),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["status"] == "active"
        assert json.loads(rows[0]["army"]) == {"ranger": 4}
        source = game.read(db, users[1])
        assert not any(job["kind"] == "alliance_garrison" for job in source["jobs"])


def test_allied_garrison_arrival_rolls_back_atomically_after_host_save_failure(
    universe, monkeypatch
):
    game, users, clock = universe
    host_id = prepare_allied_garrison_capacity(universe, capacity=10)
    with game.transaction() as db:
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            ("FUR-3-TERRA-COMBAT-4",),
        )
    command(
        universe,
        1,
        "alliance_garrison_station",
        {"key": host_id, "army": {"ranger": 4}},
    )
    with game.transaction() as db:
        source = game.read(db, users[1])
        mission = next(job for job in source["jobs"] if job["kind"] == "alliance_garrison")
        due = int(mission["due"])
    clock[0] = due
    save = game.save

    def fail_host_save(db, state):
        if state["colony_id"] == host_id and any(
            report["title"] == "Alliierte Garnison eingetroffen" for report in state["reports"]
        ):
            raise RuntimeError("injected host persistence failure")
        save(db, state)

    monkeypatch.setattr(game, "save", fail_host_save)
    with pytest.raises(JobProcessingError), game.transaction() as db:
        game.advance(db, due)

    with game.transaction() as db:
        row = db.execute(
            "SELECT status,army FROM terra_allied_garrisons WHERE id=?", (mission["id"],)
        ).fetchone()
        assert row["status"] == "travelling"
        assert json.loads(row["army"]) == {"ranger": 4}
        source = game.read(db, users[1])
        assert source["units"]["ranger"] == 96
        assert any(job["id"] == mission["id"] for job in source["jobs"])
        host = game.read_colony(db, host_id)
        assert not any(
            report["title"] == "Alliierte Garnison eingetroffen" for report in host["reports"]
        )
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_garrison_arrival'",
                (users[1],),
            ).fetchone()[0]
            == 0
        )

    monkeypatch.setattr(game, "save", save)
    with game.transaction() as db:
        game.advance(db, due)
    with game.transaction() as db:
        row = db.execute(
            "SELECT status FROM terra_allied_garrisons WHERE id=?", (mission["id"],)
        ).fetchone()
        assert row["status"] == "active"
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE actor=? AND action='alliance_garrison_arrival'",
                (users[1],),
            ).fetchone()[0]
            == 1
        )
        host = game.read_colony(db, host_id)
        assert (
            sum(report["title"] == "Alliierte Garnison eingetroffen" for report in host["reports"])
            == 1
        )
        assert (
            db.execute(
                "SELECT points FROM war_score_ledger WHERE mission_id=? AND user_id=? "
                "AND category='support'",
                (mission["id"], users[1]),
            ).fetchone()[0]
            == 4
        )
        assert (
            db.execute(
                "SELECT count(*) FROM war_score_ledger WHERE mission_id=?",
                (mission["id"],),
            ).fetchone()[0]
            == 1
        )


def test_admin_live_event_schedule_end_phase_goal_and_snapshot(universe):
    game, users, clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    payload = {
        "name": "Zielprobe",
        "hours": 2,
        "bonus": 20,
        "warning_hours": 1,
        "end_hours": 1,
        "end_bonus": 40,
        "goal_score": 100000,
    }
    token = identity()
    before = state(universe, 0)["events"]
    result = command(universe, 0, "admin_event", payload, token=token)
    event = next(item for item in result["events"] if item["name"] == "Zielprobe")
    assert event["phase"] == "warning"
    assert event["active_bonus"] == 0
    assert event["goal_progress"] < event["goal_score"]
    assert event["goal_reached"] is False
    assert event["starts"] == clock[0] + 3600
    assert event["ends"] == clock[0] + 3 * 3600
    assert event["end_starts"] == clock[0] + 2 * 3600
    with game.transaction() as db:
        rules = db.execute(
            "SELECT version,digest,snapshot,source FROM live_event_rules WHERE event_id=?",
            (event["id"],),
        ).fetchone()
        assert rules["version"] == "FUR-2-LIVE-2"
        assert len(rules["digest"]) == 64
        assert rules["source"] == "admin_create"
        assert json.loads(rules["snapshot"])["goal_score"] == 100000
        assert json.loads(rules["snapshot"])["overlap_bonus_cap"] == 100
        with pytest.raises(Exception, match="live event rules are immutable"):
            db.execute(
                "UPDATE live_event_rules SET version='mutated' WHERE event_id=?", (event["id"],)
            )
    replay = command(universe, 0, "admin_event", payload, token=token)
    assert sum(item["name"] == "Zielprobe" for item in replay["events"]) == 1
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM live_event_rules").fetchone()[0] == 1
    clock[0] += 3600
    active = next(item for item in state(universe, 0)["events"] if item["id"] == event["id"])
    assert active["phase"] == "active"
    assert active["active_bonus"] == 20
    with game.transaction() as db:
        leader = game.read(db, users[1])
        leader["buildings"]["wood"] = 10000
        game.save(db, leader)
    achieved = next(item for item in state(universe, 0)["events"] if item["id"] == event["id"])
    assert achieved["goal_reached"] is True
    clock[0] += 3600
    end_phase = next(item for item in state(universe, 0)["events"] if item["id"] == event["id"])
    assert end_phase["phase"] == "end"
    assert end_phase["active_bonus"] == 40
    clock[0] += 3600
    assert all(item["id"] != event["id"] for item in state(universe, 0)["events"])
    assert before == []


def test_admin_live_event_rejects_invalid_end_phase_atomically(universe):
    game, users, _clock = universe
    with game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (users[0],))
    with pytest.raises(RuleError, match="Endphase"):
        command(
            universe,
            0,
            "admin_event",
            {
                "name": "Ungültig",
                "hours": 2,
                "bonus": 20,
                "warning_hours": 0,
                "end_hours": 3,
                "end_bonus": 40,
                "goal_score": 100,
            },
        )
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM live_event_rules").fetchone()[0] == 0


def test_player_cannot_create_live_event_and_foreign_world_is_not_selectable(universe):
    game, _users, _clock = universe
    with pytest.raises(RuleError, match="Keine Moderationsberechtigung"):
        command(
            universe,
            1,
            "admin_event",
            {
                "name": "Nicht erlaubt",
                "hours": 2,
                "bonus": 20,
                "warning_hours": 1,
                "end_hours": 1,
                "end_bonus": 40,
                "goal_score": 10000,
            },
        )
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM live_event_rules").fetchone()[0] == 0


def test_live_event_end_phase_production_integrates_piecewise(universe):
    import copy

    game, users, _clock = universe
    with game.transaction() as db:
        base = game.read(db, users[0])
    base["buildings"]["storage"] = 10000
    starts = int(base["last"])
    event = {
        "starts": starts,
        "ends": starts + 7200,
        "bonus": 20,
        "end_starts": starts + 3600,
        "end_bonus": 40,
    }
    normal = copy.deepcopy(base)
    normal["_events"] = [{**event, "end_bonus": 20}]
    boosted = copy.deepcopy(base)
    boosted["_events"] = [event]
    game.produce(normal, starts + 7200)
    game.produce(boosted, starts + 7200)
    assert all(after >= before for after, before in zip(boosted["resources"], normal["resources"]))
    assert any(after > before for after, before in zip(boosted["resources"], normal["resources"]))
