import hashlib
import importlib
import json
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from fur_empire.contracts import Command

_PUSH_P256DH = (
    "BGsX0fLhLEJH-Lzm5WOkQPJ3A32BLeszoPShOUXYmMKWT-NC4v4af5uO5-tKfA-eFivOM1drMV7Oy7ZAaDe_UfU"
)
_PUSH_AUTH = "AAAAAAAAAAAAAAAAAAAAAA"


@pytest.mark.parametrize(
    "action,payload",
    [
        ("cancel_job", {"key": "queued-job"}),
        ("queue_move", {"key": "queued-job", "direction": "up"}),
        ("expedition", {"key": "visible-post", "army": {"ranger": 2}}),
        ("ruin_exploration", {"key": "visible-ruin", "army": {"ranger": 2}}),
        ("admin_terra_boss_schedule", {"name": "Kernwächter"}),
        ("admin_npc_invasion_schedule", {"name": "Grenzwelle"}),
        ("admin_recurring_quests", {"enabled": True}),
        ("admin_npc_convoy_schedule", {"name": "Grenzhandel"}),
        ("npc_convoy_escort", {"key": "public-convoy", "count": 10}),
        ("npc_convoy_raid", {"key": "public-convoy", "count": 15}),
        ("npc_convoy_recall", {"key": "own-mission"}),
        ("npc_convoy_claim", {"key": "completed-convoy"}),
        ("recurring_quest_claim", {"key": "1:recurring-version:1794950400:daily-build"}),
        ("terra_boss_attack", {"key": "active-boss", "count": 10}),
        ("terra_boss_claim", {"key": "defeated-boss"}),
        (
            "alliance_send_supply",
            {"key": "allied-base", "army": {"ranger": 2}, "resources": [10, 0, 0]},
        ),
        ("alliance_supply_cancel", {"key": "outbound-supply"}),
        ("colony_home", {"key": "owned-base"}),
        ("report_share", {"key": "combat-report"}),
        ("report_unshare", {"key": "opaque-share"}),
        (
            "admin_announcement_create",
            {"target_kind": "world", "world_id": 1, "name": "Test", "body": "Text"},
        ),
        ("admin_mail_send", {"key": "recipient-id", "name": "Test", "body": "Private"}),
        ("mail_read", {"key": "mail-id"}),
        ("notification_preference", {"category": "military", "muted": True}),
        ("craft_start", {"recipe_id": "component_press", "batches": 1}),
        ("item_recycle", {"item_id": "repair_kit", "item_amount": 1}),
    ],
)
def test_existing_domain_controls_are_reachable_through_the_api_contract(action, payload):
    parsed = Command.model_validate(
        {"action": action, "payload": payload, "token": "contract-reachability"}
    )
    assert parsed.action == action
    assert parsed.payload.model_dump(exclude_unset=True) == payload


def test_queue_direction_remains_strictly_validated():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Command.model_validate(
            {
                "action": "queue_move",
                "payload": {"key": "job", "direction": "sideways"},
                "token": "queue-direction-test",
            }
        )


def test_outpost_conversion_is_accepted_by_the_strict_command_contract():
    command = Command.model_validate(
        {
            "action": "outpost_colonize",
            "payload": {"key": "target-1", "confirmation": "Foundry Gate"},
            "token": "conversion-token-1",
        }
    )
    assert command.action == "outpost_colonize"
    assert command.payload.key == "target-1"
    assert command.payload.confirmation == "Foundry Gate"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_EMBEDDED_WORKER", "false")
    monkeypatch.setenv("FUR_DB", str(tmp_path / "api.sqlite3"))
    import fur_empire.api as module

    importlib.reload(module)
    with TestClient(module.app) as client:
        yield client


def test_full_auth_and_command(client):
    page = client.get("/")
    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-cache, must-revalidate"
    for path in ("app.js", "style.css", "favicon.svg"):
        assert client.get("/static/" + path).status_code == 200
    assert client.get("/static/app.js").headers["cache-control"] == "no-cache, must-revalidate"
    assert client.get("/api/v1/state").status_code == 401
    response = client.post(
        "/api/v1/auth/register", json={"name": "Commander", "password": "test-pass-123"}
    )
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Max-Age=604800" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    csrf = response.json()["csrf"]
    assert client.get("/api/v1/state").json()["name"] == "Commander"
    body = {"action": "build", "payload": {"key": "barracks"}, "token": "unique-token"}
    rejected = client.post("/api/v1/command", json=body)
    assert rejected.status_code == 400
    assert rejected.headers.get("X-Request-ID")
    assert set(rejected.json()) == {"error", "code", "request_id"}
    assert rejected.json()["code"] == "invalid_csrf"
    assert rejected.json()["request_id"] == rejected.headers["X-Request-ID"]
    assert (
        client.post("/api/v1/command", json=body, headers={"X-CSRF-Token": csrf}).status_code == 200
    )

    import fur_empire.api as module

    owner = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (owner,))
        db.execute(
            "UPDATE world_settings SET settings=? WHERE world_id=1",
            (json.dumps({"crafting_ruleset": "FUR-CRAFTING-1"}),),
        )
        state = module.game.read(db, owner)
        state["resources"][2] = 1000
        state["goods_inventory"] = {"alloy": 20, "circuits": 8}
        state["item_inventory"] = {"repair_kit": 1}
        module.game.save(db, state)
    recycle = client.post(
        "/api/v1/command",
        json={
            "action": "item_recycle",
            "payload": {"item_id": "repair_kit", "item_amount": 1},
            "token": "recycle-api-0001",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert recycle.status_code == 200
    assert recycle.json()["item_inventory"]["crafting_component"] == 2
    assert recycle.json()["goods_inventory"]["textiles"] == 3
    craft = client.post(
        "/api/v1/command",
        json={
            "action": "craft_start",
            "payload": {"recipe_id": "component_press", "batches": 1},
            "token": "craft-api-000001",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert craft.status_code == 200
    assert any(job["kind"] == "craft" for job in craft.json()["jobs"])
    assert client.post("/api/v1/logout", json={}, headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/v1/state").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"name": "Commander", "password": "test-pass-123"}
        ).status_code
        == 200
    )


def test_banned_player_can_appeal_without_session_and_moderator_can_review(client):
    import fur_empire.api as module

    admin_registration = client.post(
        "/api/v1/auth/register",
        json={"name": "AppealModerator", "password": "moderator-pass-123"},
    )
    assert admin_registration.status_code == 200
    admin_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (admin_id,))

    with TestClient(module.app) as banned_player:
        registration = banned_player.post(
            "/api/v1/auth/register",
            json={"name": "BanAppealPilot", "password": "appeal-pass-123"},
        )
        assert registration.status_code == 200
        player_id = banned_player.get("/api/v1/state").json()["id"]
        with module.game.transaction() as db:
            db.execute("UPDATE profiles SET banned=1 WHERE user_id=?", (player_id,))
        # A ban hides, but does not destroy, existing sessions. Each open appeal
        # must atomically revoke every active session for the applicant.
        banned_player.cookies.clear()

        appeal_data = {
            "name": "BanAppealPilot",
            "password": "appeal-pass-123",
            "reason": "The account suspension appears to be mistaken.",
        }
        wrong_password = banned_player.post(
            "/api/v1/auth/ban-appeal", json={**appeal_data, "password": "wrong-password-123"}
        )
        assert wrong_password.status_code == 400
        assert banned_player.cookies.get("fur_session") is None
        with module.game.transaction() as db:
            assert db.execute("SELECT count(*) FROM account_ban_appeals").fetchone()[0] == 0

        submitted = banned_player.post("/api/v1/auth/ban-appeal", json=appeal_data)
        repeated = banned_player.post("/api/v1/auth/ban-appeal", json=appeal_data)
        assert submitted.status_code == repeated.status_code == 202
        assert "Sperre bleibt" in submitted.json()["message"]
        assert banned_player.cookies.get("fur_session") is None
        with module.game.transaction() as db:
            assert (
                db.execute(
                    "SELECT count(*) FROM sessions WHERE user_id=? AND expires>?",
                    (player_id, int(module.time.time())),
                ).fetchone()[0]
                == 0
            )
            appeal = db.execute(
                "SELECT id,reason FROM account_ban_appeals WHERE user_id=? AND status='open'",
                (player_id,),
            ).fetchone()
            assert appeal is not None
            assert appeal["reason"] == appeal_data["reason"]
            assert db.execute("SELECT count(*) FROM account_ban_appeals").fetchone()[0] == 1
        case_id = str(appeal["id"])

        moderator_state = client.get("/api/v1/state").json()
        visible_case = next(
            item for item in moderator_state["administration"]["cases"] if item["id"] == case_id
        )
        assert visible_case["case_type"] == "account_ban_appeal"
        assert visible_case["reporter_name"] == "BanAppealPilot"
        assert visible_case["reason"] == appeal_data["reason"]
        with module.game.transaction() as db:
            later_cases, has_more = module.game.systems.moderation_case_page(
                db, before_case_id=case_id
            )
        assert later_cases == []
        assert has_more is False
        invalid_outcome = client.post(
            "/api/v1/command",
            json={
                "action": "admin_case_resolve",
                "payload": {"key": case_id, "value": "lift_mute"},
                "token": "invalid-ban-appeal-outcome",
            },
            headers={"X-CSRF-Token": admin_registration.json()["csrf"]},
        )
        assert invalid_outcome.status_code == 400
        resolved = client.post(
            "/api/v1/command",
            json={
                "action": "admin_case_resolve",
                "payload": {"key": case_id, "value": "grant_ban_appeal"},
                "token": "grant-ban-appeal-once",
            },
            headers={"X-CSRF-Token": admin_registration.json()["csrf"]},
        )
        assert resolved.status_code == 200
        with module.game.transaction() as db:
            assert (
                db.execute("SELECT banned FROM profiles WHERE user_id=?", (player_id,)).fetchone()[
                    0
                ]
                == 0
            )
            result = db.execute(
                "SELECT status,resolution,resolver_id FROM account_ban_appeals WHERE id=?",
                (case_id,),
            ).fetchone()
            assert tuple(result) == ("resolved", "grant_ban_appeal", admin_id)
            assert (
                db.execute(
                    "SELECT count(*) FROM audit WHERE actor=? AND action='admin_case_resolve'",
                    (admin_id,),
                ).fetchone()[0]
                == 1
            )

        relogin = banned_player.post(
            "/api/v1/auth/login",
            json={"name": appeal_data["name"], "password": appeal_data["password"]},
        )
        assert relogin.status_code == 200
        player_cases = banned_player.get("/api/v1/state").json()["moderation_cases"]
        assert any(
            item["id"] == case_id
            and item["case_type"] == "account_ban_appeal"
            and item["resolution"] == "grant_ban_appeal"
            for item in player_cases
        )


def test_ban_appeal_requires_existing_account_multifactor_when_enabled(client):
    import fur_empire.api as module
    from fur_empire.identity import totp

    with TestClient(module.app) as player:
        registration = player.post(
            "/api/v1/auth/register",
            json={"name": "MfaAppealPilot", "password": "appeal-pass-123"},
        )
        assert registration.status_code == 200
        player_id = player.get("/api/v1/state").json()["id"]
        secret = "JBSWY3DPEHPK3PXP"
        with module.game.transaction() as db:
            db.execute(
                "UPDATE profiles SET banned=1,totp=?,totp_last=-1 WHERE user_id=?",
                (secret, player_id),
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (player_id,))
        player.cookies.clear()

        body = {
            "name": "MfaAppealPilot",
            "password": "appeal-pass-123",
            "reason": "Please review this account suspension.",
        }
        missing_factor = player.post("/api/v1/auth/ban-appeal", json=body)
        assert missing_factor.status_code == 400
        with module.game.transaction() as db:
            assert db.execute("SELECT count(*) FROM account_ban_appeals").fetchone()[0] == 0

        current_step = int(time.time()) // 30
        submitted = player.post(
            "/api/v1/auth/ban-appeal",
            json={**body, "code": totp(secret, current_step)},
        )
        assert submitted.status_code == 202
        assert player.cookies.get("fur_session") is None
        with module.game.transaction() as db:
            assert (
                db.execute(
                    "SELECT count(*) FROM account_ban_appeals WHERE user_id=?", (player_id,)
                ).fetchone()[0]
                == 1
            )


def test_push_routes_are_opt_in_csrf_protected_owner_bound_and_configurable(client, monkeypatch):
    import fur_empire.api as module

    assert client.get("/service-worker.js").headers["service-worker-allowed"] == "/"
    assert "showNotification" in client.get("/service-worker.js").text
    assert client.get("/api/v1/push/config").json() == {"enabled": False, "public_key": ""}
    assert client.get("/api/v1/push/subscriptions").status_code == 401
    auth = client.post(
        "/api/v1/auth/register", json={"name": "PushPilot", "password": "test-pass-123"}
    )
    csrf = auth.json()["csrf"]
    assert client.get("/api/v1/push/subscriptions").status_code == 200
    denied = client.post(
        "/api/v1/push/subscriptions",
        json={
            "endpoint": "https://push.example.test/subscription",
            "keys": {"p256dh": _PUSH_P256DH, "auth": _PUSH_AUTH},
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert denied.status_code == 400
    assert "nicht aktiviert" in denied.json()["error"]
    from dataclasses import replace

    monkeypatch.setattr(
        module,
        "settings",
        replace(
            module.settings,
            webpush_public_key="public",
            webpush_private_key_file="private.pem",
            webpush_subject="mailto:ops@example.test",
        ),
    )
    monkeypatch.setattr(module.web_push, "validate_endpoint", lambda endpoint: None)
    body = {
        "endpoint": "https://push.example.test/subscription",
        "keys": {"p256dh": _PUSH_P256DH, "auth": _PUSH_AUTH},
    }
    saved = client.post("/api/v1/push/subscriptions", json=body, headers={"X-CSRF-Token": csrf})
    assert saved.status_code == 200
    assert saved.json()["created"] is True
    assert (
        client.get("/api/v1/push/subscriptions").json()["subscriptions"][0]["id"]
        == saved.json()["id"]
    )
    missing_csrf = client.delete(
        "/api/v1/push/subscriptions", params={"endpoint": body["endpoint"]}
    )
    assert missing_csrf.status_code == 400
    removed = client.delete(
        "/api/v1/push/subscriptions",
        params={"endpoint": body["endpoint"]},
        headers={"X-CSRF-Token": csrf},
    )
    assert removed.json() == {"ok": True, "removed": True}


def test_push_settings_must_be_provisioned_as_a_complete_set(monkeypatch):
    from fur_empire.config import Settings

    monkeypatch.setenv("FUR_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://fur:pass@db/fur")
    for name, value in {
        "PUBLIC_ORIGIN": "https://game.example.test",
        "SMTP_HOST": "smtp.example.test",
        "SMTP_FROM": "FUR <game@example.test>",
        "OPERATOR_NAME": "Ops",
        "OPERATOR_CONTACT": "ops@example.test",
        "WEBPUSH_PUBLIC_KEY": "public",
        "WEBPUSH_SUBJECT": "mailto:ops@example.test",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("WEBPUSH_PRIVATE_KEY_FILE", raising=False)
    with pytest.raises(RuntimeError, match="WEBPUSH_PUBLIC_KEY"):
        Settings.load("unused.sqlite3")


def test_push_route_contracts_validate_shape_and_subscription_owner_without_database(monkeypatch):
    from types import SimpleNamespace

    import fur_empire.api as module

    class FakeDatabase:
        def __init__(self):
            self.statements = []

        def execute(self, sql, params=()):
            self.statements.append((sql, params))
            if "SELECT id,user_id FROM web_push_subscriptions" in sql:
                return SimpleNamespace(fetchone=lambda: None)
            if "SELECT count(*) FROM web_push_subscriptions" in sql:
                return SimpleNamespace(fetchone=lambda: [0])
            if "SELECT COALESCE(MAX(sequence),0) FROM game_events" in sql:
                return SimpleNamespace(fetchone=lambda: [0])
            if "SELECT id,created,updated,failures" in sql:
                return SimpleNamespace(
                    fetchall=lambda: [{"id": "mine", "created": 1, "updated": 2, "failures": 0}]
                )
            return SimpleNamespace(fetchone=lambda: {"id": "mine"})

    class Transaction:
        def __init__(self, db):
            self.db = db

        def __enter__(self):
            return self.db

        def __exit__(self, *args):
            return None

    db = FakeDatabase()
    monkeypatch.setattr(module.game, "transaction", lambda: Transaction(db))
    monkeypatch.setattr(module, "session", lambda request, connection, mutate=False: "owner")
    monkeypatch.setattr(module, "limit", lambda request, bucket, maximum: None)
    from dataclasses import replace

    monkeypatch.setattr(
        module,
        "settings",
        replace(
            module.settings,
            webpush_public_key="public",
            webpush_private_key_file="private.pem",
            webpush_subject="mailto:ops@example.test",
        ),
    )
    monkeypatch.setattr(module.web_push, "validate_endpoint", lambda endpoint: None)
    request = SimpleNamespace()
    listing = module.web_push_subscriptions(request)
    assert listing["subscriptions"][0]["id"] == "mine"
    body = module.WebPushSubscription.model_validate(
        {
            "endpoint": "https://push.example.test/endpoint",
            "keys": {"p256dh": _PUSH_P256DH, "auth": _PUSH_AUTH},
        }
    )
    assert module.web_push_subscribe(body, request)["ok"] is True
    assert db.statements[-1][1][1] == "owner"
    assert (
        module.web_push_unsubscribe(request, "https://push.example.test/endpoint")["removed"]
        is True
    )


def test_system_announcement_and_mailbox_pages_enforce_session_and_recipient_scope(client):
    assert client.get("/api/v1/announcements", params={"before": "opaque"}).status_code == 401
    assert client.get("/api/v1/system-mail", params={"before": "opaque"}).status_code == 401
    registered = client.post(
        "/api/v1/auth/register", json={"name": "SystemMailReader", "password": "mail-reader-123"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    other = str(uuid4())
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (other, "Other Reader", "unused"))
        db.execute(
            "INSERT INTO system_announcements(id,world_id,author_id,title,body,created) "
            "VALUES ('global-news',NULL,?,'Global title','All worlds',100)",
            (owner,),
        )
        db.execute(
            "INSERT INTO system_announcements(id,world_id,author_id,title,body,created) "
            "VALUES ('world-news',1,?,'World title','World one',101)",
            (owner,),
        )
        db.execute(
            "INSERT INTO system_mail(id,recipient_id,author_id,title,body,created) "
            "VALUES ('own-system-mail',?,?, 'Your mail','Private content',102)",
            (owner, owner),
        )
        db.execute(
            "INSERT INTO system_mail(id,recipient_id,author_id,title,body,created) "
            "VALUES ('other-system-mail',?,?, 'Other mail','Not yours',103)",
            (other, owner),
        )
    result = client.get("/api/v1/state").json()
    assert {item["id"] for item in result["announcements"]} == {"global-news", "world-news"}
    assert [item["id"] for item in result["system_mail"]] == ["own-system-mail"]
    assert (
        client.get("/api/v1/system-mail", params={"before": "other-system-mail"}).status_code == 400
    )
    older = client.get("/api/v1/announcements", params={"before": "world-news"})
    assert older.status_code == 200
    assert [item["id"] for item in older.json()["entries"]] == ["global-news"]


def test_game_event_feed_filter_and_cursor_are_private_and_world_bound(client):
    import fur_empire.api as module
    from fur_empire.game import identity

    assert client.get("/api/v1/game-events", params={"world_id": 1}).status_code == 401
    registered = client.post(
        "/api/v1/auth/register", json={"name": "EventReader", "password": "event-reader-123"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()
    user_id = owner["id"]
    world_id = owner["active_world"]["id"]
    with module.game.transaction() as db:
        for index in range(60):
            db.execute(
                "INSERT INTO game_events(id,recipient,world_id,kind,created) VALUES (?,?,?,?,?)",
                (identity(), user_id, world_id, "attack" if index % 2 else "build", 1000 + index),
            )
    first = client.get("/api/v1/game-events", params={"world_id": world_id})
    assert first.status_code == 200
    assert len(first.json()["events"]) == 50
    assert first.json()["has_more"] is True
    filtered = client.get(
        "/api/v1/game-events", params={"world_id": world_id, "category": "military"}
    )
    assert filtered.status_code == 200
    assert filtered.json()["events"]
    assert all(event["category"] == "military" for event in filtered.json()["events"])
    older = client.get(
        "/api/v1/game-events",
        params={"world_id": world_id, "before": first.json()["cursor"]},
    )
    assert older.status_code == 200
    assert len(older.json()["events"]) == 10
    assert older.json()["has_more"] is False
    assert max(event["sequence"] for event in older.json()["events"]) < first.json()["cursor"]
    wrong_world = client.get("/api/v1/game-events", params={"world_id": world_id + 1})
    assert wrong_world.status_code == 400
    invalid_category = client.get(
        "/api/v1/game-events", params={"world_id": world_id, "category": "secrets"}
    )
    assert invalid_category.status_code == 422


def test_ruin_exploration_through_authenticated_http_commands(client):
    import fur_empire.api as module
    from fur_empire import ruin_exploration
    from fur_empire.terrain import travel_times

    login = client.post(
        "/api/v1/auth/register", json={"name": "RuinSurvey", "password": "ruin-survey-pass"}
    )
    assert login.status_code == 200
    headers = {"X-CSRF-Token": login.json()["csrf"]}
    initial = client.get("/api/v1/state").json()
    user = initial["id"]
    world = initial["world_id"]
    assert initial["expedition_rules"]["version"] == "FUR-3-EXPEDITIONS-1"
    assert sum(item["weight"] for item in initial["expedition_rules"]["outcomes"]) == 10000
    ruin_id = str(uuid4())
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin' WHERE user_id=?", (user,))
        origin = (initial["x"], initial["y"])
        x, y = next(
            point
            for point in travel_times(db, origin, world)
            if point != origin and sum((a - b) ** 2 for a, b in zip(point, origin)) <= 64
        )
        now = int(time.time())
        db.execute(
            "INSERT INTO terra_ruins(id,world_id,x,y,created,expires) VALUES (?,?,?,?,?,?)",
            (ruin_id, world, x, y, now, now + 86400),
        )

    request = {
        "action": "ruin_exploration",
        "payload": {"key": ruin_id, "army": {"ranger": 1}},
        "token": "start-ruin-http",
    }
    assert client.post("/api/v1/command", json=request, headers=headers).status_code == 400
    active_at = int(time.time()) + 120
    rollout = client.post(
        "/api/v1/command",
        headers=headers,
        json={
            "action": "admin_rule_rollout_schedule",
            "payload": {
                "world_id": world,
                "rule_key": "terra_ruin_exploration_ruleset",
                "target_version": ruin_exploration.VERSION,
                "active_at": active_at,
            },
            "token": "schedule-ruin-http",
        },
    )
    assert rollout.status_code == 200, rollout.json()
    with module.game.transaction() as db:
        module.game.advance(db, active_at)
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-3' WHERE world_id=?",
            (world,),
        )
    ready = client.get("/api/v1/state").json()
    assert ready["active_world"]["terra_ruin_exploration_ruleset"] == ruin_exploration.VERSION
    assert ruin_id in {target["id"] for target in ready["terra_ruin_targets"]}
    created = client.post(
        "/api/v1/command",
        headers=headers,
        json={
            "action": "world_create",
            "payload": {
                "name": "Ruin Survey Sandbox",
                "seed": 7024,
                "outposts": 8,
                "mode": "sandbox",
                "npc_camps_ruleset": "FUR-2",
                "terra_ruin_exploration_ruleset": ruin_exploration.VERSION,
                "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-5",
            },
            "token": "create-ruin-sandbox",
        },
    )
    assert created.status_code == 200, created.json()
    with module.game.transaction() as db:
        other_world = db.execute(
            "SELECT world_id FROM world_settings WHERE name='Ruin Survey Sandbox'"
        ).fetchone()["world_id"]
    joined = client.post(
        "/api/v1/command",
        headers=headers,
        json={
            "action": "world_join",
            "payload": {"world_id": other_world},
            "token": "join-ruin-sandbox",
        },
    )
    assert joined.status_code == 200, joined.json()
    assert joined.json()["active_world"]["id"] == other_world
    assert (
        joined.json()["active_world"]["terra_ruin_exploration_ruleset"] == ruin_exploration.VERSION
    )
    other_target = client.post("/api/v1/command", json=request, headers=headers)
    assert other_target.status_code == 400
    assert "nicht mehr aktiv" in other_target.json()["error"]
    selected = client.post(
        "/api/v1/command",
        headers=headers,
        json={
            "action": "world_select",
            "payload": {"world_id": world},
            "token": "select-original-ruin-world",
        },
    )
    assert selected.status_code == 200, selected.json()

    quote = client.post(
        "/api/v1/simulate-movement",
        json={"target_kind": "ruin", "target_id": ruin_id, "army": {"ranger": 1}},
        headers=headers,
    )
    assert quote.status_code == 200, quote.json()
    assert quote.json()["movement"]["fuel_ore"] > 0
    rejected = client.post("/api/v1/command", json=request)
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "invalid_csrf"
    sent = client.post("/api/v1/command", json=request, headers=headers)
    assert sent.status_code == 200, sent.json()
    mission = next(job for job in sent.json()["jobs"] if job["kind"] == "ruin_exploration")
    assert "seed" not in mission
    assert mission["travel"] == quote.json()["movement"]["travel_seconds"]
    retried = client.post("/api/v1/command", json=request, headers=headers)
    assert mission["id"] in {job["id"] for job in retried.json()["jobs"]}
    recalled = client.post(
        "/api/v1/command",
        headers=headers,
        json={
            "action": "mission_recall",
            "payload": {"key": mission["id"]},
            "token": "recall-ruin-http",
        },
    )
    assert recalled.status_code == 200, recalled.json()
    assert any(job["kind"] == "return" for job in recalled.json()["jobs"])
    with module.game.transaction() as db:
        module.game.advance(db, mission["due"] + mission["travel"])
        assert not db.execute(
            "SELECT 1 FROM terra_ruin_explorations WHERE mission_id=?", (mission["id"],)
        ).fetchone()
        assert not db.execute(
            "SELECT 1 FROM terra_ruin_intel WHERE observer_id=? AND ruin_id=?", (user, ruin_id)
        ).fetchone()
        assert module.game.read(db, user)["units"]["ranger"] == ready["units"]["ranger"]


def test_movement_simulation_is_read_only_and_scoped_to_known_targets(client):
    import fur_empire.api as module

    login = client.post(
        "/api/v1/auth/register", json={"name": "MovementPilot", "password": "movement-pass-123"}
    )
    assert login.status_code == 200
    csrf = login.json()["csrf"]
    initial_state = client.get("/api/v1/state").json()
    user_id = initial_state["id"]
    target = next(
        item
        for item in initial_state["world"]
        if (item["x"], item["y"]) != (initial_state["x"], initial_state["y"])
    )
    with module.game.transaction() as db:
        state = module.game.read(db, user_id)
        state["units"]["ranger"] = 1
        state["resources"][2] = 100
        module.game.save(db, state)
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset='FUR-3-TERRA-COMBAT-3' WHERE world_id=?",
            (state["world_id"],),
        )
        intel_before = int(
            db.execute(
                "SELECT count(*) FROM map_sector_intel WHERE observer_id=? AND world_id=?",
                (user_id, state["world_id"]),
            ).fetchone()[0]
        )
        ore_before = int(module.game.read(db, user_id)["resources"][2])

    response = client.post(
        "/api/v1/simulate-movement",
        json={"target_id": target["id"], "army": {"ranger": 1}},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert response.json()["read_only"] is True
    assert response.json()["movement"]["fuel_ore"] > 0
    assert response.json()["movement"]["affordable"] is True
    with module.game.transaction() as db:
        state = module.game.read(db, user_id)
        assert int(state["resources"][2]) == ore_before
        intel_after = int(
            db.execute(
                "SELECT count(*) FROM map_sector_intel WHERE observer_id=? AND world_id=?",
                (user_id, state["world_id"]),
            ).fetchone()[0]
        )
        assert intel_after == intel_before


def test_api_errors_redact_validation_and_unexpected_exception_details(client, monkeypatch):
    import fur_empire.api as module

    invalid = client.post("/api/v1/auth/register", json={"password": {"secret": "never-echo"}})
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_request"
    assert "never-echo" not in invalid.text
    assert invalid.json()["request_id"] == invalid.headers["X-Request-ID"]
    missing = client.get("/api/v1/unknown-route")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "Error Pilot", "password": "error-1234"}
        ).status_code
        == 200
    )

    def fail(*args):
        raise RuntimeError("private database details")

    monkeypatch.setattr(module.game, "view", fail)
    unexpected = client.get("/api/v1/state")
    assert unexpected.status_code == 500
    assert unexpected.json()["code"] == "internal_error"
    assert "private database details" not in unexpected.text
    assert unexpected.json()["request_id"] == unexpected.headers["X-Request-ID"]


def test_neutral_goods_command_requires_csrf_and_records_only_one_exchange(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "GoodsPilot", "password": "market-pass-123"}
    )
    csrf = registered.json()["csrf"]
    body = {
        "action": "goods_trade",
        "payload": {"goods_source": "wood", "goods_destination": "alloy", "amount": 100},
        "token": "neutral-goods-retry-1",
    }
    assert client.post("/api/v1/command", json=body).status_code == 400
    headers = {"X-CSRF-Token": csrf}
    first = client.post("/api/v1/command", json=body, headers=headers)
    assert first.status_code == 200
    assert first.json()["goods_inventory"]["alloy"] == 4
    assert first.json()["neutral_market"]["material_stacks"] == {
        "used": 1,
        "available_types": 7,
    }
    second = client.post("/api/v1/command", json=body, headers=headers)
    assert second.status_code == 200
    assert second.json()["goods_inventory"]["alloy"] == 4
    assert second.json()["neutral_market"]["material_stacks"] == {
        "used": 1,
        "available_types": 7,
    }
    body["payload"]["amount"] = True
    assert client.post("/api/v1/command", json=body, headers=headers).status_code == 422


def test_economy_simulation_uses_live_rules_and_rolls_back_every_domain_write(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "EconomyPilot", "password": "economy-pass-123"}
    )
    csrf = registered.json()["csrf"]
    import fur_empire.api as module

    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name=?", ("EconomyPilot",)).fetchone()[0]
        colony_state_before = db.execute(
            "SELECT state FROM colonies WHERE user_id=?", (user,)
        ).fetchone()[0]
        counts_before = {
            "commands": db.execute(
                "SELECT count(*) FROM commands WHERE user_id=?", (user,)
            ).fetchone()[0],
            "ledger": db.execute("SELECT count(*) FROM ledger WHERE user_id=?", (user,)).fetchone()[
                0
            ],
            "messages": db.execute(
                "SELECT count(*) FROM messages WHERE sender=?", (user,)
            ).fetchone()[0],
            "trades": db.execute(
                "SELECT count(*) FROM neutral_goods_trades WHERE owner=?", (user,)
            ).fetchone()[0],
        }

    payload = {
        "commands": [
            {
                "action": "goods_trade",
                "payload": {
                    "goods_source": "wood",
                    "goods_destination": "alloy",
                    "amount": 100,
                },
            }
        ]
    }
    assert client.post("/api/v1/economy/simulate", json=payload).json()["code"] == "invalid_csrf"
    response = client.post("/api/v1/economy/simulate", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    result = response.json()
    assert result["committed"] is False
    assert result["neutral_market_version"]
    assert len(result["neutral_market_digest"]) == 64
    assert result["rules_version"]
    assert len(result["rules_digest"]) == 64
    assert result["initial"] != result["steps"][0]["balance"]
    assert result["final"] == result["steps"][0]["balance"]

    with module.game.transaction() as db:
        assert (
            db.execute("SELECT state FROM colonies WHERE user_id=?", (user,)).fetchone()[0]
            == colony_state_before
        )
        counts_after = {
            "commands": db.execute(
                "SELECT count(*) FROM commands WHERE user_id=?", (user,)
            ).fetchone()[0],
            "ledger": db.execute("SELECT count(*) FROM ledger WHERE user_id=?", (user,)).fetchone()[
                0
            ],
            "messages": db.execute(
                "SELECT count(*) FROM messages WHERE sender=?", (user,)
            ).fetchone()[0],
            "trades": db.execute(
                "SELECT count(*) FROM neutral_goods_trades WHERE owner=?", (user,)
            ).fetchone()[0],
        }
        assert counts_after == counts_before


def test_economy_simulation_rolls_back_prior_steps_when_a_later_step_fails(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "RollbackPilot", "password": "rollback-pass-123"}
    )
    csrf = registered.json()["csrf"]
    payload = {
        "commands": [
            {
                "action": "goods_trade",
                "payload": {"goods_source": "wood", "goods_destination": "alloy", "amount": 100},
            },
            {"action": "build", "payload": {"key": "unknown_building"}},
        ]
    }
    response = client.post("/api/v1/economy/simulate", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 400
    assert response.json()["code"] == "rule_rejected"
    assert client.get("/api/v1/state").json().get("goods_inventory", {}).get("alloy", 0) == 0


def test_economy_simulation_rejects_oversized_or_non_economic_scenarios(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "BoundedPilot", "password": "bounded-pass-123"}
    )
    csrf = registered.json()["csrf"]
    headers = {"X-CSRF-Token": csrf}
    too_many = {"commands": [{"action": "quest"} for _ in range(21)]}
    assert (
        client.post("/api/v1/economy/simulate", json=too_many, headers=headers).status_code == 422
    )
    unsupported = {"commands": [{"action": "attack"}]}
    assert (
        client.post("/api/v1/economy/simulate", json=unsupported, headers=headers).status_code
        == 422
    )


def test_battle_simulator_requires_csrf_and_does_not_change_game_state(client):
    created = client.post(
        "/api/v1/auth/register", json={"name": "BattlePilot", "password": "battle-pass-123"}
    )
    csrf = created.json()["csrf"]
    state = client.get("/api/v1/state").json()
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        target = module.game.world_outposts(db, 1)[0]
        target.update(x=min(63, state["x"] + 1), y=state["y"], tier=1, stock=[120, 80, 40])
        module.game.save_world_outposts(db, 1, module.game.world_outposts(db, 1))
        before = db.execute(
            "SELECT state FROM world_outposts WHERE target_id=? AND world_id=1", (target["id"],)
        ).fetchone()[0]
    payload = {"target_id": target["id"], "army": {"ranger": 2}}
    assert client.post("/api/v1/simulate-battle", json=payload).status_code == 400
    response = client.post("/api/v1/simulate-battle", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert response.json()["deterministic"] is True
    assert set(response.json()["simulation"]) == {
        "power",
        "defense",
        "victory",
        "attacker_survivors",
        "attacker_losses",
        "defender_survivors",
        "loot",
    }
    with module.game.transaction() as db:
        after = db.execute(
            "SELECT state FROM world_outposts WHERE target_id=? AND world_id=1", (target["id"],)
        ).fetchone()[0]
        assert after == before


def test_fur3_battle_simulator_api_returns_ranges_without_persisting_combat(client):
    created = client.post(
        "/api/v1/auth/register", json={"name": "Fur3ProbePilot", "password": "probe-pass-123"}
    )
    assert created.status_code == 200
    csrf = created.json()["csrf"]
    state = client.get("/api/v1/state").json()
    module = importlib.import_module("fur_empire.api")
    from fur_empire import terra_combat

    with module.game.transaction() as db:
        target = module.game.world_outposts(db, 1)[0]
        target.update(
            x=min(63, state["x"] + 1),
            y=state["y"],
            tier=2,
            stock=[120, 80, 40],
            units={"ranger": 3, "sentinel": 1},
        )
        module.game.save_world_outposts(db, 1, module.game.world_outposts(db, 1))
        db.execute(
            "UPDATE world_settings SET terra_combat_ruleset=? WHERE world_id=1",
            (terra_combat.VERSION,),
        )
        db.execute(
            "INSERT INTO map_sector_intel(observer_id,world_id,x,y,observed_at) "
            "VALUES (?,?,?,?,?) ON CONFLICT(observer_id,world_id,x,y) DO UPDATE "
            "SET observed_at=excluded.observed_at",
            (state["id"], 1, target["x"], target["y"], int(time.time())),
        )
        before_post = db.execute(
            "SELECT state FROM world_outposts WHERE target_id=? AND world_id=1",
            (target["id"],),
        ).fetchone()[0]
        before_colony = db.execute(
            "SELECT state FROM colonies WHERE colony_id=?", (state["colony_id"],)
        ).fetchone()[0]

    response = client.post(
        "/api/v1/simulate-battle",
        json={"target_id": target["id"], "army": {"ranger": 2}},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200, response.text
    assert response.json()["deterministic"] is False
    simulation = response.json()["simulation"]
    assert simulation["simulation"]["samples"] == terra_combat.SIMULATION_SAMPLES
    assert len(simulation["simulation"]["attacker_losses_total"]) == 2
    assert len(simulation["simulation"]["loot"]) == 3
    assert "seed" not in simulation and "seed_commitment" not in simulation
    with module.game.transaction() as db:
        assert (
            db.execute(
                "SELECT state FROM world_outposts WHERE target_id=? AND world_id=1",
                (target["id"],),
            ).fetchone()[0]
            == before_post
        )
        assert (
            db.execute(
                "SELECT state FROM colonies WHERE colony_id=?", (state["colony_id"],)
            ).fetchone()[0]
            == before_colony
        )


def test_battle_simulator_accepts_player_target_only_with_fresh_level_two_intel(client):
    created = client.post(
        "/api/v1/auth/register", json={"name": "PvPPreviewPilot", "password": "preview-pass-123"}
    )
    assert created.status_code == 200
    csrf = created.json()["csrf"]
    module = importlib.import_module("fur_empire.api")
    target_user = "preview-target-" + str(uuid4())
    observer = client.get("/api/v1/state").json()["id"]
    now = int(time.time())
    with module.game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (target_user, "PreviewTarget", "unused"))
        module.game.create(db, target_user, "PreviewTarget")
        db.execute(
            "UPDATE profiles SET joined=? WHERE user_id IN (?,?)",
            (now - 7200, target_user, observer),
        )
        db.execute("UPDATE flags SET value='true' WHERE name='pvp'")
        db.execute(
            "INSERT INTO player_intel(observer_id,target_id,level,observed_at,expires_at,data,world_id) "
            "VALUES (?,?,2,?,?,?,1)",
            (
                observer,
                target_user,
                now - 60,
                now + 3600,
                json.dumps(
                    {
                        "hq": 3,
                        "buildings": {"hq": 3},
                        "defense": 300,
                        "garrison": 2,
                        "units": {"ranger": 2, "sentinel": 0, "mech": 0},
                    }
                ),
            ),
        )
    payload = {"target_id": target_user, "army": {"ranger": 2}}
    response = client.post("/api/v1/simulate-battle", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200, response.text
    simulation = response.json()["simulation"]
    assert simulation["defense"] == 300
    assert simulation["loot"] is None
    denied = client.post(
        "/api/v1/simulate-battle",
        json={"target_id": target_user, "army": {"ranger": 999}},
        headers={"X-CSRF-Token": csrf},
    )
    assert denied.status_code == 400


def test_mission_templates_are_validated_limited_and_owner_scoped(client):
    first = client.post(
        "/api/v1/auth/register", json={"name": "TemplatePilot", "password": "template-pass-123"}
    )
    assert first.status_code == 200
    csrf = first.json()["csrf"]
    assert client.get("/api/v1/mission-templates").json() == {"templates": []}
    payload = {
        "name": "Kernstoß",
        "mode": "attack",
        "army": {"ranger": 3, "mech": 1},
        "capture": True,
    }
    assert client.post("/api/v1/mission-templates", json=payload).status_code == 400
    created = client.post("/api/v1/mission-templates", json=payload, headers={"X-CSRF-Token": csrf})
    assert created.status_code == 200
    template = created.json()["template"]
    assert template["name"] == "Kernstoß"
    assert template["army"] == payload["army"]
    assert template["capture"] is True
    assert template["mode"] == "attack"
    assert (
        client.post(
            "/api/v1/mission-templates",
            json={**payload, "name": "kernstoß"},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/mission-templates",
            json={**payload, "name": "Unknown", "army": {"airship": 1}},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/mission-templates",
            json={**payload, "name": "Empty", "army": {"ranger": 0}},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 400
    )
    for number in range(2, 11):
        formation = {**payload, "mode": "expedition", "capture": False} if number == 10 else payload
        response = client.post(
            "/api/v1/mission-templates",
            json={**formation, "name": f"Formation {number}"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200
        if number == 10:
            assert response.json()["template"]["mode"] == "expedition"
    assert (
        client.post(
            "/api/v1/mission-templates",
            json={**payload, "name": "Too many"},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 400
    )

    second = client.post(
        "/api/v1/auth/register", json={"name": "OtherPilot", "password": "other-pass-123"}
    )
    assert second.status_code == 200
    other_csrf = second.json()["csrf"]
    assert client.get("/api/v1/mission-templates").json() == {"templates": []}
    assert (
        client.delete(
            f"/api/v1/mission-templates/{template['id']}", headers={"X-CSRF-Token": other_csrf}
        ).status_code
        == 400
    )

    login = client.post(
        "/api/v1/auth/login", json={"name": "TemplatePilot", "password": "template-pass-123"}
    )
    assert login.status_code == 200
    own_csrf = login.json()["csrf"]
    assert client.delete(
        f"/api/v1/mission-templates/{template['id']}", headers={"X-CSRF-Token": own_csrf}
    ).json() == {"ok": True}
    assert len(client.get("/api/v1/mission-templates").json()["templates"]) == 9


def test_production_templates_validate_scope_limit_and_queue_idempotently(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "ProductionPilot", "password": "production-pass-123"},
    )
    assert registered.status_code == 200
    csrf = registered.json()["csrf"]
    user_id = client.get("/api/v1/state").json()["id"]
    endpoint = "/api/v1/production-templates"
    payload = {"name": "Holz Ausbau", "kind": "build", "key": "wood", "count": 1}
    assert client.post(endpoint, json=payload).status_code == 400
    assert client.get(endpoint).json() == {"templates": []}

    created = client.post(endpoint, json=payload, headers={"X-CSRF-Token": csrf})
    assert created.status_code == 200
    template = created.json()["template"]
    assert {key: template[key] for key in ("name", "kind", "key", "count")} == payload
    for bad_payload, expected in (
        ({**payload, "name": "holz ausbau"}, 400),
        ({**payload, "name": "Unknown", "key": "orbital_foundry"}, 400),
        ({**payload, "name": "Count mismatch", "count": 2}, 400),
        ({"name": "Too many units", "kind": "train", "key": "ranger", "count": 101}, 422),
    ):
        assert (
            client.post(endpoint, json=bad_payload, headers={"X-CSRF-Token": csrf}).status_code
            == expected
        )

    before = client.get("/api/v1/state").json()["resources"]
    queue_url = f"{endpoint}/{template['id']}/queue"
    first = client.post(
        queue_url, json={"token": "production-queue-token-1"}, headers={"X-CSRF-Token": csrf}
    )
    replay = client.post(
        queue_url, json={"token": "production-queue-token-1"}, headers={"X-CSRF-Token": csrf}
    )
    assert first.status_code == replay.status_code == 200
    assert len(first.json()["jobs"]) == len(replay.json()["jobs"]) == 1
    assert first.json()["jobs"][0]["id"] == replay.json()["jobs"][0]["id"]
    second = client.post(
        queue_url, json={"token": "production-queue-token-2"}, headers={"X-CSRF-Token": csrf}
    )
    assert second.status_code == 200
    assert len(second.json()["jobs"]) == 2
    assert second.json()["resources"] != before

    trained = client.post(
        endpoint,
        json={"name": "Kleine Rangergruppe", "kind": "train", "key": "ranger", "count": 4},
        headers={"X-CSRF-Token": csrf},
    )
    assert trained.status_code == 200
    assert trained.json()["template"]["count"] == 4
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        state = module.game.read(db, user_id)
        state["buildings"]["barracks"] = 1
        module.game.save(db, state)
    training_template = trained.json()["template"]
    training_queue_url = f"{endpoint}/{training_template['id']}/queue"
    training_first = client.post(
        training_queue_url,
        json={"token": "production-train-template-1"},
        headers={"X-CSRF-Token": csrf},
    )
    training_replay = client.post(
        training_queue_url,
        json={"token": "production-train-template-1"},
        headers={"X-CSRF-Token": csrf},
    )
    assert training_first.status_code == training_replay.status_code == 200
    training_jobs = [job for job in training_first.json()["jobs"] if job["kind"] == "train"]
    assert len(training_jobs) == 1
    assert training_jobs[0]["count"] == 4
    assert [job["id"] for job in training_jobs] == [
        job["id"] for job in training_replay.json()["jobs"] if job["kind"] == "train"
    ]

    with module.game.transaction() as db:
        state = module.game.read(db, user_id)
        state["buildings"]["lab"] = 1
        module.game.save(db, state)
    research = client.post(
        endpoint,
        json={"name": "Taktik erforschen", "kind": "research", "key": "tactics"},
        headers={"X-CSRF-Token": csrf},
    )
    assert research.status_code == 200
    research_template = research.json()["template"]
    research_queued = client.post(
        f"{endpoint}/{research_template['id']}/queue",
        json={"token": "production-research-template-1"},
        headers={"X-CSRF-Token": csrf},
    )
    assert research_queued.status_code == 200
    assert any(
        job["kind"] == "research" and job["key"] == "tactics"
        for job in research_queued.json()["jobs"]
    )
    for number in range(3, 10):
        response = client.post(
            endpoint,
            json={**payload, "name": f"Build {number}"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200
    assert (
        client.post(
            endpoint,
            json={**payload, "name": "Eleventh"},
            headers={"X-CSRF-Token": csrf},
        ).status_code
        == 400
    )

    second_account = client.post(
        "/api/v1/auth/register", json={"name": "OtherProductionPilot", "password": "other-pass-123"}
    )
    assert second_account.status_code == 200
    other_csrf = second_account.json()["csrf"]
    assert client.get(endpoint).json() == {"templates": []}
    assert (
        client.delete(
            f"{endpoint}/{template['id']}", headers={"X-CSRF-Token": other_csrf}
        ).status_code
        == 400
    )
    other_state_before = client.get("/api/v1/state").json()
    with module.game.transaction() as db:
        commands_before = db.execute(
            "SELECT count(*) FROM commands WHERE user_id=?", (other_state_before["id"],)
        ).fetchone()[0]
    foreign_queue = client.post(
        queue_url,
        json={"token": "foreign-queue-token-1"},
        headers={"X-CSRF-Token": other_csrf},
    )
    assert foreign_queue.status_code == 400
    assert foreign_queue.json()["code"] == "rule_rejected"
    other_state = client.get("/api/v1/state").json()
    assert other_state["jobs"] == other_state_before["jobs"]
    with module.game.transaction() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM commands WHERE user_id=?", (other_state_before["id"],)
            ).fetchone()[0]
            == commands_before
        )

    login = client.post(
        "/api/v1/auth/login", json={"name": "ProductionPilot", "password": "production-pass-123"}
    )
    assert login.status_code == 200
    own_csrf = login.json()["csrf"]
    assert client.delete(
        f"{endpoint}/{template['id']}", headers={"X-CSRF-Token": own_csrf}
    ).json() == {"ok": True}


def test_production_template_requires_current_session_csrf(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "TemplateCsrfPilot", "password": "csrf-pass-123"}
    )
    assert registered.status_code == 200
    response = client.post(
        "/api/v1/production-templates",
        json={"name": "Wood", "kind": "build", "key": "wood"},
        headers={"X-CSRF-Token": "stale-session-token"},
    )
    assert response.status_code == 400
    assert "Sitzungsschutz" in response.json()["error"]


def test_friend_requests_use_the_authenticated_command_and_blocks_stop_private_messages(client):
    alpha = client.post(
        "/api/v1/auth/register", json={"name": "SocialAlpha", "password": "social-alpha-123"}
    )
    assert alpha.status_code == 200
    alpha_id = client.get("/api/v1/state").json()["id"]
    bravo = client.post(
        "/api/v1/auth/register", json={"name": "SocialBravo", "password": "social-bravo-123"}
    )
    assert bravo.status_code == 200
    bravo_id = client.get("/api/v1/state").json()["id"]

    alpha_login = client.post(
        "/api/v1/auth/login", json={"name": "SocialAlpha", "password": "social-alpha-123"}
    )
    alpha_csrf = alpha_login.json()["csrf"]
    request_body = {
        "action": "friend_request",
        "payload": {"key": bravo_id},
        "token": "social-request-token-1",
    }
    assert client.post("/api/v1/command", json=request_body).status_code == 400
    assert (
        client.post(
            "/api/v1/command", json=request_body, headers={"X-CSRF-Token": alpha_csrf}
        ).status_code
        == 200
    )
    assert [
        item["name"] for item in client.get("/api/v1/state").json()["social"]["outgoing_requests"]
    ] == ["SocialBravo"]

    bravo_login = client.post(
        "/api/v1/auth/login", json={"name": "SocialBravo", "password": "social-bravo-123"}
    )
    bravo_csrf = bravo_login.json()["csrf"]
    accept_body = {
        "action": "friend_accept",
        "payload": {"key": alpha_id},
        "token": "social-accept-token-1",
    }
    assert (
        client.post(
            "/api/v1/command", json=accept_body, headers={"X-CSRF-Token": bravo_csrf}
        ).status_code
        == 200
    )

    alpha_login = client.post(
        "/api/v1/auth/login", json={"name": "SocialAlpha", "password": "social-alpha-123"}
    )
    alpha_csrf = alpha_login.json()["csrf"]
    block_body = {
        "action": "player_block",
        "payload": {"key": bravo_id},
        "token": "social-block-token-1",
    }
    assert (
        client.post(
            "/api/v1/command", json=block_body, headers={"X-CSRF-Token": alpha_csrf}
        ).status_code
        == 200
    )

    bravo_login = client.post(
        "/api/v1/auth/login", json={"name": "SocialBravo", "password": "social-bravo-123"}
    )
    message = {
        "action": "message",
        "payload": {"channel": "private", "name": "SocialAlpha", "body": "Blocked message"},
        "token": "social-message-token-1",
    }
    response = client.post(
        "/api/v1/command", json=message, headers={"X-CSRF-Token": bravo_login.json()["csrf"]}
    )
    assert response.status_code == 400
    assert "privaten Nachrichten" in response.json()["error"]


def test_public_player_profile_is_opt_in_world_scoped_and_excludes_account_secrets(client):
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "ProfileOwner", "password": "profile-owner-123"}
        ).status_code
        == 200
    )
    owner_id = client.get("/api/v1/state").json()["id"]
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"name": "ProfileTarget", "password": "profile-target-123"},
        ).status_code
        == 200
    )
    target_state = client.get("/api/v1/state").json()
    target_id = target_state["id"]
    assert target_state["profile"]["public_profile_visibility"] == "private"

    owner_login = client.post(
        "/api/v1/auth/login", json={"name": "ProfileOwner", "password": "profile-owner-123"}
    )
    assert owner_login.status_code == 200
    assert client.get(f"/api/v1/profiles/{target_id}").status_code == 404

    target_login = client.post(
        "/api/v1/auth/login", json={"name": "ProfileTarget", "password": "profile-target-123"}
    )
    assert target_login.status_code == 200
    csrf = target_login.json()["csrf"]
    saved = client.post(
        "/api/v1/command",
        json={
            "action": "profile_settings_update",
            "payload": {
                "profile_visibility": "public",
                "profile_title": "architect",
                "profile_badges": "builder,scholar",
            },
            "token": "profile-settings-public-1",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert saved.status_code == 200
    target_state = client.get("/api/v1/state").json()
    assert target_state["profile"]["public_profile_badges"] == ["builder", "scholar"]

    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        db.execute(
            "UPDATE profiles SET email='private@example.invalid',verified=1 " "WHERE user_id=?",
            (target_id,),
        )

    owner_login = client.post(
        "/api/v1/auth/login", json={"name": "ProfileOwner", "password": "profile-owner-123"}
    )
    assert owner_login.status_code == 200
    response = client.get(f"/api/v1/profiles/{target_id}")
    assert response.status_code == 200
    public = response.json()["profile"]
    assert public["name"] == "ProfileTarget"
    assert public["title"] == "Architekt"
    assert public["badges"] == ["Baumeister", "Forscher"]
    assert public["world"] == "Genesis"
    assert 1 <= public["rank"] <= 2
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
    assert "email" not in public and "verified" not in public and "totp" not in public
    assert owner_id != target_id

    target_login = client.post(
        "/api/v1/auth/login", json={"name": "ProfileTarget", "password": "profile-target-123"}
    )
    private_again = client.post(
        "/api/v1/command",
        json={
            "action": "profile_settings_update",
            "payload": {
                "profile_visibility": "private",
                "profile_title": "architect",
                "profile_badges": "builder,scholar",
            },
            "token": "profile-settings-private-1",
        },
        headers={"X-CSRF-Token": target_login.json()["csrf"]},
    )
    assert private_again.status_code == 200
    client.post(
        "/api/v1/auth/login", json={"name": "ProfileOwner", "password": "profile-owner-123"}
    )
    assert client.get(f"/api/v1/profiles/{target_id}").status_code == 404


def test_shared_combat_report_api_requires_authentication_and_returns_redacted_summary(client):
    import fur_empire.api as module

    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "ReportOwner", "password": "report-owner-pass-123"},
    )
    assert registered.status_code == 200
    csrf = registered.json()["csrf"]
    with TestClient(module.app) as visitor:
        assert visitor.get("/api/v1/alliance/shared-reports").status_code == 401

    def command(action, payload):
        return client.post(
            "/api/v1/command",
            json={"action": action, "payload": payload, "token": uuid4().hex},
            headers={"X-CSRF-Token": csrf},
        )

    created = command("alliance_create", {"tag": "API", "name": "API Reports"})
    assert created.status_code == 200
    owner_id = created.json()["id"]
    report_id = str(uuid4())
    with module.game.transaction() as db:
        owner_state = module.game.read(db, owner_id)
        owner_state["reports"] = [
            {
                "id": report_id,
                "title": "Hidden Target Name at 50:50",
                "body": "Private loot 12345",
                "time": 1770000000,
                "share_owner": {"side": "attacker", "wing_index": None, "allowed": True},
                "combat": {
                    "rules_version": "hidden-rules",
                    "rules_digest": "hidden-digest",
                    "seed": "hidden-seed",
                    "participants": {"attacker": "ReportOwner", "defender": "Hidden Target"},
                    "rounds": [
                        {
                            "round": 1,
                            "victory": True,
                            "attacker": {"losses": {"ranger": 1}, "survivors": {"ranger": 2}},
                            "defender": {"losses": {"mech": 9}, "survivors": {"secret_unit": 4}},
                            "loot": [12345, 0, 0],
                        }
                    ],
                },
            }
        ]
        module.game.save(db, owner_state)

    shared = command("report_share", {"key": report_id})
    assert shared.status_code == 200
    response = client.get("/api/v1/alliance/shared-reports")
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["can_revoke"] is True
    assert entry["report_id"] == report_id
    assert entry["summary"] == {
        "outcome": "victory",
        "rounds": [{"number": 1, "outcome": "victory", "own_losses": 1, "own_survivors": 2}],
    }
    payload = json.dumps(response.json())
    for secret in (
        "Hidden Target",
        "50:50",
        "12345",
        "hidden-rules",
        "hidden-digest",
        "hidden-seed",
        "secret_unit",
    ):
        assert secret not in payload


def test_notes_require_csrf_are_private_and_enforce_world_coordinate_limits(client):
    owner = client.post(
        "/api/v1/auth/register", json={"name": "NoteOwner", "password": "notes-owner-123"}
    )
    assert owner.status_code == 200
    owner_id = client.get("/api/v1/state").json()["id"]
    visitor = client.post(
        "/api/v1/auth/register", json={"name": "NoteVisitor", "password": "notes-visitor-123"}
    )
    assert visitor.status_code == 200
    visitor_id = client.get("/api/v1/state").json()["id"]
    import fur_empire.api as module

    with module.game.transaction() as db:
        owner_state = module.game.read(db, owner_id)
        owner_state["reports"].append(
            {"id": "private-report-api", "title": "Private report", "body": "secret"}
        )
        module.game.save(db, owner_state)

    owner_login = client.post(
        "/api/v1/auth/login", json={"name": "NoteOwner", "password": "notes-owner-123"}
    )
    csrf = owner_login.json()["csrf"]
    payload = {
        "action": "note_save",
        "payload": {"target_kind": "sector", "x": 3, "y": 4, "body": "private map note"},
        "token": "notes-api-token-1",
    }
    assert client.post("/api/v1/command", json=payload).status_code == 400
    assert (
        client.post("/api/v1/command", json=payload, headers={"X-CSRF-Token": csrf}).status_code
        == 200
    )
    own_state = client.get("/api/v1/state").json()
    assert len(own_state["notes"]) == 1
    assert own_state["notes"][0]["body"] == "private map note"
    assert own_state["notes_has_more"] is False
    assert client.get("/api/v1/notes", params={"before": own_state["notes"][0]["id"]}).json() == {
        "notes": [],
        "has_more": False,
    }
    assert client.get("/api/v1/notes", params={"before": "unknown-note"}).status_code == 400

    visitor_login = client.post(
        "/api/v1/auth/login", json={"name": "NoteVisitor", "password": "notes-visitor-123"}
    )
    foreign_state = client.get("/api/v1/state").json()
    assert foreign_state["id"] == visitor_id
    assert foreign_state["notes"] == []
    assert foreign_state["notes_has_more"] is False
    too_long = {
        **payload,
        "payload": {"target_kind": "sector", "x": 3, "y": 4, "body": "x" * 501},
        "token": "notes-api-token-2",
    }
    rejected = client.post(
        "/api/v1/command",
        json=too_long,
        headers={"X-CSRF-Token": visitor_login.json()["csrf"]},
    )
    assert rejected.status_code == 400
    assert "500" in rejected.json()["error"]
    bad_coordinates = {
        **payload,
        "payload": {"target_kind": "sector", "x": 64, "y": 4, "body": "out of range"},
        "token": "notes-api-token-3",
    }
    out_of_range = client.post(
        "/api/v1/command",
        json=bad_coordinates,
        headers={"X-CSRF-Token": visitor_login.json()["csrf"]},
    )
    assert out_of_range.status_code == 422


def test_relogin_rotates_csrf_and_state_returns_the_current_session_token(client):
    created = client.post(
        "/api/v1/auth/register", json={"name": "SessionPilot", "password": "session-pass-123"}
    )
    assert created.status_code == 200
    stale_csrf = created.json()["csrf"]

    relogin = client.post(
        "/api/v1/auth/login", json={"name": "SessionPilot", "password": "session-pass-123"}
    )
    assert relogin.status_code == 200
    current = client.get("/api/v1/state").json()["csrf"]
    assert current == relogin.json()["csrf"]
    assert current != stale_csrf

    body = {"action": "build", "payload": {"key": "barracks"}, "token": "session-retry"}
    stale = client.post("/api/v1/command", json=body, headers={"X-CSRF-Token": stale_csrf})
    assert stale.status_code == 400
    assert "Sitzungsschutz" in stale.json()["error"]
    accepted = client.post("/api/v1/command", json=body, headers={"X-CSRF-Token": current})
    assert accepted.status_code == 200


def test_account_session_inventory_is_private_safe_and_supports_single_revocation(client):
    import fur_empire.api as module

    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "SessionOwner", "password": "session-owner-pass"},
        headers={"user-agent": "FUR Desktop Alpha"},
    )
    first_cookie = client.cookies.get("fur_session")
    second_login = client.post(
        "/api/v1/auth/login",
        json={"name": "SessionOwner", "password": "session-owner-pass"},
        headers={"user-agent": "FUR Browser Beta"},
    )
    assert registration.status_code == second_login.status_code == 200
    csrf = second_login.json()["csrf"]
    inventory = client.get("/api/v1/account/sessions")
    assert inventory.status_code == 200
    sessions = inventory.json()["sessions"]
    assert len(sessions) == 2
    assert sum(item["current"] for item in sessions) == 1
    assert {item["user_agent"] for item in sessions} == {"FUR Desktop Alpha", "FUR Browser Beta"}
    assert all(
        set(item) == {"id", "created", "expires", "user_agent", "current"} for item in sessions
    )
    assert all("token" not in item and "csrf" not in item for item in sessions)
    old_session = next(item for item in sessions if not item["current"])
    csrf_denied = client.post(f"/api/v1/account/sessions/revoke/{old_session['id']}", json={})
    assert csrf_denied.status_code == 400
    assert "Sitzungsschutz" in csrf_denied.json()["error"]

    with TestClient(module.app) as other:
        other.post(
            "/api/v1/auth/register",
            json={"name": "OtherSessionUser", "password": "other-session-pass"},
        )
        other_csrf = other.get("/api/v1/state").json()["csrf"]
        denied = other.post(
            f"/api/v1/account/sessions/revoke/{old_session['id']}",
            json={},
            headers={"X-CSRF-Token": other_csrf},
        )
        assert denied.status_code == 400
        assert denied.json()["error"] == "Sitzung nicht gefunden."

    revoked = client.post(
        f"/api/v1/account/sessions/revoke/{old_session['id']}",
        json={},
        headers={"X-CSRF-Token": csrf},
    )
    assert revoked.status_code == 200
    assert revoked.json() == {"ok": True, "current": False}
    assert len(client.get("/api/v1/account/sessions").json()["sessions"]) == 1
    with TestClient(module.app) as old_device:
        old_device.cookies.set("fur_session", first_cookie)
        assert old_device.get("/api/v1/state").status_code == 401
    with module.game.transaction() as db:
        assert (
            db.execute("SELECT count(*) FROM audit WHERE action='session_revoke'").fetchone()[0]
            == 1
        )


def test_account_session_inventory_is_bounded_owner_scoped_and_keyset_paginated(client):
    import fur_empire.api as module

    registered = client.post(
        "/api/v1/auth/register", json={"name": "SessionPager", "password": "session-pager-pass"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    now = int(time.time())
    with module.game.transaction() as db:
        for index in range(51):
            db.execute(
                "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    f"session-page-token-{index:03}",
                    owner,
                    "csrf-unused",
                    now + 3600,
                    f"session-page-id-{index:03}",
                    now + 1000 + index,
                    "Test browser",
                ),
            )
    first = client.get("/api/v1/account/sessions")
    assert first.status_code == 200
    assert len(first.json()["sessions"]) == 50
    assert first.json()["has_more"] is True
    assert all(
        set(item) == {"id", "created", "expires", "user_agent", "current"}
        for item in first.json()["sessions"]
    )
    cursor = first.json()["sessions"][-1]["id"]
    older = client.get("/api/v1/account/sessions", params={"before": cursor})
    assert older.status_code == 200
    assert older.json()["sessions"][0]["id"] == "session-page-id-000"
    assert older.json()["has_more"] is False
    assert (
        client.get("/api/v1/account/sessions", params={"before": "unknown-session"}).status_code
        == 400
    )

    with TestClient(module.app) as other:
        other_registered = other.post(
            "/api/v1/auth/register",
            json={"name": "ForeignSessions", "password": "foreign-session-pass"},
        )
        assert other_registered.status_code == 200
        foreign_owner = other.get("/api/v1/state").json()["id"]
        with module.game.transaction() as db:
            db.execute(
                "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
                "VALUES ('foreign-session-token',?,'csrf',?, 'foreign-session-id',?, 'Foreign')",
                (foreign_owner, now + 3600, now + 2000),
            )
    assert (
        client.get("/api/v1/account/sessions", params={"before": "foreign-session-id"}).status_code
        == 400
    )


def test_account_session_bulk_revocation_preserves_current_or_logs_out_everywhere(client):
    import fur_empire.api as module

    client.post(
        "/api/v1/auth/register",
        json={"name": "BulkSessions", "password": "bulk-session-pass"},
    )
    first_cookie = client.cookies.get("fur_session")
    second = client.post(
        "/api/v1/auth/login",
        json={"name": "BulkSessions", "password": "bulk-session-pass"},
    )
    current_csrf = second.json()["csrf"]
    revoked_others = client.post(
        "/api/v1/account/sessions/revoke-others",
        json={},
        headers={"X-CSRF-Token": current_csrf},
    )
    assert revoked_others.status_code == 200
    assert revoked_others.json() == {"ok": True, "revoked": 1}
    assert len(client.get("/api/v1/account/sessions").json()["sessions"]) == 1
    with TestClient(module.app) as old_device:
        old_device.cookies.set("fur_session", first_cookie)
        assert old_device.get("/api/v1/state").status_code == 401

    third = client.post(
        "/api/v1/auth/login",
        json={"name": "BulkSessions", "password": "bulk-session-pass"},
    )
    logout_everywhere = client.post(
        "/api/v1/account/sessions/revoke-all",
        json={},
        headers={"X-CSRF-Token": third.json()["csrf"]},
    )
    assert logout_everywhere.status_code == 200
    assert logout_everywhere.json() == {"ok": True, "revoked": 2}
    assert client.get("/api/v1/state").status_code == 401
    with module.game.transaction() as db:
        assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='sessions_revoke_others'"
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT count(*) FROM audit WHERE action='sessions_revoke_all'").fetchone()[
                0
            ]
            == 1
        )


def test_password_change_reauthenticates_and_revokes_every_session(client):
    import fur_empire.api as module

    client.post(
        "/api/v1/auth/register",
        json={"name": "PasswordChange", "password": "initial-password"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"name": "PasswordChange", "password": "initial-password"},
    )
    csrf = client.get("/api/v1/state").json()["csrf"]
    invalid = client.post(
        "/api/v1/account/private",
        json={
            "action": "password",
            "password": "wrong-password",
            "new_password": "replacement-pass",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert invalid.status_code == 400
    assert "Passwort stimmt nicht" in invalid.json()["error"]
    assert len(client.get("/api/v1/account/sessions").json()["sessions"]) == 2

    changed = client.post(
        "/api/v1/account/private",
        json={
            "action": "password",
            "password": "initial-password",
            "new_password": "replacement-pass",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 200
    assert "Max-Age=0" in changed.headers["set-cookie"]
    assert client.get("/api/v1/state").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"name": "PasswordChange", "password": "initial-password"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"name": "PasswordChange", "password": "replacement-pass"},
        ).status_code
        == 200
    )
    with module.game.transaction() as db:
        assert (
            db.execute("SELECT count(*) FROM audit WHERE action='account_password'").fetchone()[0]
            == 1
        )


def test_password_change_requires_current_totp_when_enabled(client):
    import fur_empire.api as module
    from fur_empire.identity import totp

    client.post(
        "/api/v1/auth/register",
        json={"name": "PasswordMfa", "password": "initial-password"},
    )
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name=?", ("PasswordMfa",)).fetchone()[0]
        secret = "JBSWY3DPEHPK3PXP"
        db.execute("UPDATE profiles SET totp=?,totp_last=-1 WHERE user_id=?", (secret, user))
    csrf = client.get("/api/v1/state").json()["csrf"]
    code = totp(secret, int(time.time()) // 30)
    invalid_code = str((int(code) + 1) % 1_000_000).zfill(6)
    bad_code = client.post(
        "/api/v1/account/private",
        json={
            "action": "password",
            "password": "initial-password",
            "new_password": "replacement-pass",
            "code": invalid_code,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert bad_code.status_code == 400
    assert "Authenticator-Code" in bad_code.json()["error"]
    changed = client.post(
        "/api/v1/account/private",
        json={
            "action": "password",
            "password": "initial-password",
            "new_password": "replacement-pass",
            "code": code,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 200
    assert client.get("/api/v1/state").status_code == 401


def test_command_rate_limit_rejects_requests_after_the_configured_threshold(client):
    body = {"action": "build", "payload": {"key": "barracks"}, "token": "rate-limit-test"}
    responses = [client.post("/api/v1/command", json=body) for _ in range(90)]
    assert all(response.status_code == 401 for response in responses)

    limited = client.post("/api/v1/command", json=body)
    assert limited.status_code == 400
    assert limited.json()["error"] == "Zu viele Anfragen. Bitte eine Minute warten."


def test_health_and_readiness_separate_database_and_worker_status(client):
    import fur_empire.api as module

    with module.game.transaction() as db:
        db.execute(
            "INSERT INTO worker_status(id,heartbeat,error) VALUES (1,?,'') "
            "ON CONFLICT(id) DO UPDATE SET heartbeat=excluded.heartbeat,error=''",
            (int(time.time()) - 31,),
        )

    health = client.get("/api/v1/health")
    not_ready = client.get("/api/v1/ready")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert not_ready.status_code == 503
    assert not_ready.json()["ready"] is False

    with module.game.transaction() as db:
        db.execute("UPDATE worker_status SET heartbeat=? WHERE id=1", (int(time.time()),))
    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["ready"] is True


def test_world_create_join_and_switch_api_contract(client):
    import fur_empire.api as module

    admin_login = client.post(
        "/api/v1/auth/register", json={"name": "WorldAdmin", "password": "world-admin-123"}
    )
    admin_csrf = admin_login.json()["csrf"]
    with module.game.transaction() as db:
        db.execute(
            "UPDATE profiles SET role='admin' WHERE user_id=(SELECT id FROM users WHERE name=?)",
            ("WorldAdmin",),
        )

    created = client.post(
        "/api/v1/command",
        json={
            "action": "world_create",
            "payload": {
                "name": "API Acceptance World",
                "seed": 701106,
                "outposts": 8,
                "joinable": True,
                "mode": "permanent",
                "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-1",
                "terra_retreat_threshold_percent": 37,
                "crafting_ruleset": "FUR-CRAFTING-1",
                "hero_ruleset": "FUR-3-HERO-1",
                "hero_doctrine_ruleset": "FUR-3-HERO-2",
                "hero_respec_ruleset": "FUR-3-HERO-3",
            },
            "token": "create-world-acceptance",
        },
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert created.status_code == 200
    assert {world["name"] for world in created.json()["worlds"]} == {
        "Genesis",
        "API Acceptance World",
    }
    created_world = next(world for world in created.json()["worlds"] if world["id"] == 2)
    assert created_world["player_count"] == 0
    assert created_world["terra_combat_ruleset"] == "FUR-3-TERRA-COMBAT-1"
    assert created_world["terra_retreat_threshold_percent"] == 37
    assert created_world["crafting_ruleset"] == "FUR-CRAFTING-1"
    assert created_world["hero_ruleset"] == "FUR-3-HERO-1"
    assert created_world["hero_doctrine_ruleset"] == "FUR-3-HERO-2"
    assert created_world["hero_respec_ruleset"] == "FUR-3-HERO-3"
    with module.game.transaction() as db:
        assert db.execute("SELECT count(*) FROM world_outposts WHERE world_id=2").fetchone()[0] == 8
        assert db.execute("SELECT count(*) FROM colonies WHERE world_id=2").fetchone()[0] == 0
    replayed = client.post(
        "/api/v1/command",
        json={
            "action": "world_create",
            "payload": {
                "name": "API Acceptance World",
                "seed": 701106,
                "outposts": 8,
                "joinable": True,
                "mode": "permanent",
                "terra_combat_ruleset": "FUR-3-TERRA-COMBAT-1",
                "terra_retreat_threshold_percent": 37,
                "crafting_ruleset": "FUR-CRAFTING-1",
                "hero_ruleset": "FUR-3-HERO-1",
                "hero_doctrine_ruleset": "FUR-3-HERO-2",
                "hero_respec_ruleset": "FUR-3-HERO-3",
            },
            "token": "create-world-acceptance",
        },
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert replayed.status_code == 200
    assert [world["id"] for world in replayed.json()["worlds"]] == [1, 2]
    invalid_profile = client.post(
        "/api/v1/command",
        json={
            "action": "world_create",
            "payload": {
                "name": "Invalid Rule World",
                "seed": 701107,
                "outposts": 8,
                "hero_ruleset": "FUR-2",
                "hero_doctrine_ruleset": "FUR-3-HERO-2",
            },
            "token": "create-world-invalid-profile",
        },
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert invalid_profile.status_code == 400
    assert all(world["id"] != 3 for world in client.get("/api/v1/state").json()["worlds"])
    updated = client.post(
        "/api/v1/command",
        json={
            "action": "world_update",
            "payload": {"world_id": 2, "name": "Renamed Acceptance World", "joinable": True},
            "token": "update-world-acceptance",
        },
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert updated.status_code == 200
    renamed = next(world for world in updated.json()["worlds"] if world["id"] == 2)
    assert renamed["name"] == "Renamed Acceptance World"
    assert renamed["joinable"] is True

    assert (
        client.post("/api/v1/logout", json={}, headers={"X-CSRF-Token": admin_csrf}).status_code
        == 200
    )
    player_login = client.post(
        "/api/v1/auth/register", json={"name": "WorldPilot", "password": "world-pilot-123"}
    )
    player_csrf = player_login.json()["csrf"]
    joined = client.post(
        "/api/v1/command",
        json={
            "action": "world_join",
            "payload": {"world_id": 2},
            "token": "join-world-acceptance",
        },
        headers={"X-CSRF-Token": player_csrf},
    )
    assert joined.status_code == 200
    assert joined.json()["active_world"]["id"] == 2
    assert joined.json()["colony_count"] == 1
    assert len(joined.json()["colonies"]) == 1
    assert len(joined.json()["empire_colonies"]) == 2
    denied_update = client.post(
        "/api/v1/command",
        json={
            "action": "world_update",
            "payload": {"world_id": 2, "name": "Unauthorized Name"},
            "token": "unauthorized-world-update",
        },
        headers={"X-CSRF-Token": player_csrf},
    )
    assert denied_update.status_code == 400

    switched = client.post(
        "/api/v1/command",
        json={
            "action": "world_select",
            "payload": {"world_id": 1},
            "token": "switch-world-acceptance",
        },
        headers={"X-CSRF-Token": player_csrf},
    )
    assert switched.status_code == 200
    assert switched.json()["active_world"]["id"] == 1
    assert switched.json()["colony_count"] == 1
    assert len(switched.json()["colonies"]) == 1
    assert len(switched.json()["empire_colonies"]) == 2


def test_operations_metrics_are_admin_only_and_flag_stale_backup(client):
    import fur_empire.api as module

    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "Ops Pilot", "password": "operations-123"}
        ).status_code
        == 200
    )
    path = "/api/v1/admin/operations"
    assert client.get(path).status_code == 400
    now = int(module.time.time())
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin'")
        db.execute("INSERT INTO backup_status VALUES (1,?)", (now - 90000,))
        db.execute("INSERT INTO scheduler_status VALUES (1,?,45)", (now,))
    result = client.get(path)
    assert result.status_code == 200
    assert result.json()["scheduler_lag_seconds"] == 45
    assert "scheduler_lag" in result.json()["alerts"]
    assert "backup_age" in result.json()["alerts"]
    assert result.json()["orbit_ledger_mismatches"] == 0


def test_ranking_endpoint_exposes_only_the_active_world_category_scores(client):
    login = client.post(
        "/api/v1/auth/register", json={"name": "Category Pilot", "password": "ranking-123"}
    )
    assert login.status_code == 200
    result = client.get("/api/v1/ranking")
    assert result.status_code == 200
    categories = result.json()["categories"]
    assert set(categories) == {
        "overall",
        "economy",
        "research",
        "pve",
        "war",
        "regions",
        "alliance",
    }
    assert all(len(rows) <= 50 for rows in categories.values())
    for category in ("overall", "economy", "research", "pve", "war", "regions"):
        assert categories[category][0]["name"] == "Category Pilot"
    assert categories["overall"][0]["score"] == (
        categories["economy"][0]["score"]
        + categories["research"][0]["score"]
        + categories["pve"][0]["score"]
    )


def test_rule_preview_requires_admin_and_keeps_catalog_unchanged(client):
    import fur_empire.api as module

    login = client.post(
        "/api/v1/auth/register", json={"name": "Rule Operator", "password": "preview-123"}
    )
    assert login.status_code == 200
    headers = {"X-CSRF-Token": login.json()["csrf"]}
    payload = {
        "world_id": 1,
        "terrain": "plain",
        "resource": "wood",
        "production_percent": 50,
        "unit": "ranger",
        "unit_power": 42,
    }
    path = "/api/v1/admin/rule-preview"
    assert client.post(path, json=payload, headers=headers).status_code == 400
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='admin'")
    result = client.post(path, json=payload, headers=headers)
    assert result.status_code == 200
    preview = result.json()
    assert preview["production_before"] == 2 * preview["production_after"]
    assert preview["unit_power_after"] == 42
    assert module.REGISTRY["units"]["ranger"]["power"] == preview["unit_power_before"]


def test_orbit_chart_requires_access_in_active_world(client):
    import fur_empire.api as module

    path = "/api/v1/orbit/system?world_id=1&galaxy=1&system=100"
    assert client.get(path).status_code == 401
    login = client.post(
        "/api/v1/auth/register", json={"name": "Orbit Cartographer", "password": "chart-12345"}
    )
    assert login.status_code == 200
    assert client.get(path).status_code == 400
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name='Orbit Cartographer'").fetchone()[0]
        db.execute(
            "INSERT INTO orbit_access(user_id,world_id,rule_version,unlocked_at) VALUES (?,?,?,?)",
            (user, 1, module.orbit_rules.VERSION, 1),
        )
    chart = client.get(path)
    assert chart.status_code == 200
    assert len(chart.json()["slots"]) == 16
    assert set(chart.json()["slots"][0]) == {"slot", "terrain"}
    now = int(module.time.time())
    with module.game.transaction() as db:
        db.execute(
            "INSERT INTO orbit_intel(observer,world_id,galaxy,system_no,slot,occupied,observed_at) "
            "VALUES (?,1,1,100,1,TRUE,?)",
            (user, now),
        )
        db.execute(
            "INSERT INTO orbit_intel(observer,world_id,galaxy,system_no,slot,occupied,observed_at) "
            "VALUES (?,1,1,100,2,TRUE,?)",
            (user, now - 86401),
        )
    observed = client.get(path).json()["slots"]
    assert observed[0]["occupied"] is True
    assert "occupied" not in observed[1]
    assert client.get(path.replace("world_id=1", "world_id=2")).status_code == 400
    assert client.get(path.replace("system=100", "system=101")).status_code == 422


def test_world_directory_is_bounded_and_cursor_paginated(client):
    import fur_empire.api as module

    login = client.post(
        "/api/v1/auth/register", json={"name": "WorldPagePilot", "password": "world-page-123"}
    )
    assert login.status_code == 200
    with module.game.transaction() as db:
        for world_id in range(2, 54):
            db.execute("INSERT INTO world(id,state) VALUES (?,?)", (world_id, "{}"))
            db.execute(
                "INSERT INTO world_settings(world_id,name,seed,outpost_count,joinable,created,settings) "
                "VALUES (?,?,?,8,1,0,'{}')",
                (world_id, f"Page World {world_id}", world_id),
            )
    state = client.get("/api/v1/state").json()
    assert len(state["worlds"]) == 50
    assert state["worlds"][0]["id"] == 1
    assert state["worlds"][0]["player_count"] == 1
    assert state["worlds"][-1]["id"] == 50
    assert state["worlds"][-1]["player_count"] == 0
    assert state["worlds_has_more"] is True
    page = client.get("/api/v1/worlds", params={"before": 50})
    assert page.status_code == 200
    assert [world["id"] for world in page.json()["worlds"]] == [51, 52, 53]
    assert all(world["player_count"] == 0 for world in page.json()["worlds"])
    assert page.json()["has_more"] is False
    assert client.get("/api/v1/worlds", params={"before": 999}).status_code == 400


def test_colony_rename_api_requires_csrf_and_returns_the_new_display_name(client):
    login = client.post(
        "/api/v1/auth/register", json={"name": "RenamePilot", "password": "rename-pilot-123"}
    )
    assert login.status_code == 200
    colony_id = client.get("/api/v1/state").json()["colony_id"]
    body = {
        "action": "colony_rename",
        "payload": {"colony_id": colony_id, "name": "Waldposten"},
        "token": "rename-home-colony",
    }
    assert client.post("/api/v1/command", json=body).status_code == 400
    renamed = client.post(
        "/api/v1/command", json=body, headers={"X-CSRF-Token": login.json()["csrf"]}
    )
    assert renamed.status_code == 200
    assert renamed.json()["colony_name"] == "Waldposten"
    assert renamed.json()["name"] == "RenamePilot"


def test_alliance_bulletin_api_requires_csrf_and_limits_visibility_to_members(client):
    owner = client.post(
        "/api/v1/auth/register", json={"name": "BulletinOwner", "password": "bulletin-owner-123"}
    )
    assert owner.status_code == 200
    csrf = owner.json()["csrf"]
    create_alliance = {
        "action": "alliance_create",
        "payload": {"tag": "BOARD", "name": "Board Keepers"},
        "token": "create-bulletin-alliance",
    }
    assert client.post("/api/v1/command", json=create_alliance).status_code == 400
    assert (
        client.post(
            "/api/v1/command", json=create_alliance, headers={"X-CSRF-Token": csrf}
        ).status_code
        == 200
    )

    post = {
        "action": "alliance_bulletin_create",
        "payload": {"name": "Opening", "body": "Welcome to the alliance."},
        "token": "create-first-bulletin",
    }
    assert client.post("/api/v1/command", json=post).status_code == 400
    published = client.post("/api/v1/command", json=post, headers={"X-CSRF-Token": csrf})
    assert published.status_code == 200
    assert published.json()["alliance_bulletins"][0]["title"] == "Opening"
    assert published.json()["alliance_bulletins"][0]["body"] == "Welcome to the alliance."

    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (owner_id,)
        ).fetchone()[0]
        created = int(time.time()) - 101
        for index in range(101):
            db.execute(
                "INSERT INTO alliance_bulletins "
                "(id,alliance_id,author_id,title,body,created,updated,archived) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    f"api-bulletin-{index:03}",
                    alliance_id,
                    owner_id,
                    f"Old {index}",
                    "Earlier board entry.",
                    created + index,
                    created + index,
                    index % 2,
                ),
            )
    first_page = client.get("/api/v1/state").json()
    assert len(first_page["alliance_bulletins"]) == 100
    assert first_page["alliance_bulletins_has_more"] is True
    first_ids = {entry["id"] for entry in first_page["alliance_bulletins"]}
    cursor = first_page["alliance_bulletins"][-1]["id"]
    second_page = client.get("/api/v1/alliance/bulletins", params={"before": cursor})
    assert second_page.status_code == 200
    assert second_page.json()["has_more"] is False
    assert len(second_page.json()["entries"]) == 2
    assert first_ids.isdisjoint(entry["id"] for entry in second_page.json()["entries"])

    outsider = client.post(
        "/api/v1/auth/register", json={"name": "BulletinGuest", "password": "bulletin-guest-123"}
    )
    assert outsider.status_code == 200
    assert client.get("/api/v1/state").json()["alliance_bulletins"] == []
    assert client.get("/api/v1/alliance/bulletins", params={"before": cursor}).status_code == 400


def test_alliance_forum_api_requires_csrf_and_pages_only_for_current_members(client):
    owner = client.post(
        "/api/v1/auth/register", json={"name": "ForumOwner", "password": "forum-owner-123"}
    )
    assert owner.status_code == 200
    csrf = owner.json()["csrf"]
    create_alliance = {
        "action": "alliance_create",
        "payload": {"tag": "FORUM", "name": "Forum Keepers"},
        "token": "create-forum-alliance",
    }
    assert client.post("/api/v1/command", json=create_alliance).status_code == 400
    assert (
        client.post(
            "/api/v1/command", json=create_alliance, headers={"X-CSRF-Token": csrf}
        ).status_code
        == 200
    )
    thread_command = {
        "action": "alliance_forum_thread_create",
        "payload": {"name": "Opening", "body": "First discussion."},
        "token": "create-forum-thread",
    }
    assert client.post("/api/v1/command", json=thread_command).status_code == 400
    created_thread = client.post(
        "/api/v1/command", json=thread_command, headers={"X-CSRF-Token": csrf}
    )
    assert created_thread.status_code == 200
    assert created_thread.json()["alliance_forum"][0]["posts"][0]["body"] == "First discussion."

    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (owner_id,)
        ).fetchone()[0]
        for index in range(51):
            thread_id = f"api-forum-{index:03}"
            post_id = f"api-forum-post-{index:03}"
            created_at = 100000 + index
            db.execute(
                "INSERT INTO alliance_forum_threads "
                "(id,alliance_id,author_id,title,created,updated,archived) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    thread_id,
                    alliance_id,
                    owner_id,
                    f"Old {index}",
                    created_at,
                    created_at,
                    index % 2,
                ),
            )
            db.execute(
                "INSERT INTO alliance_forum_posts "
                "(id,thread_id,author_id,body,created,updated) VALUES (?,?,?,?,?,?)",
                (post_id, thread_id, owner_id, "Forum pagination post.", created_at, created_at),
            )
            db.execute(
                "INSERT INTO alliance_forum_reports "
                "(id,post_id,reporter_id,reason,status,created,updated,resolved_by) "
                "VALUES (?,?,?,'Pagination test','pending',?,?,NULL)",
                (f"api-forum-report-{index:03}", post_id, owner_id, created_at, created_at),
            )
    first_page = client.get("/api/v1/state").json()
    assert len(first_page["alliance_forum"]) == 50
    assert first_page["alliance_forum_has_more"] is True
    cursor = first_page["alliance_forum"][-1]["id"]
    older_page = client.get("/api/v1/alliance/forum", params={"before": cursor})
    assert older_page.status_code == 200
    assert older_page.json()["has_more"] is False
    assert len(older_page.json()["threads"]) == 2
    assert len(first_page["alliance_forum_reports"]) == 50
    assert first_page["alliance_forum_reports_has_more"] is True
    report_cursor = first_page["alliance_forum_reports"][-1]["id"]
    older_reports = client.get("/api/v1/alliance/forum-reports", params={"before": report_cursor})
    assert older_reports.status_code == 200
    assert len(older_reports.json()["reports"]) == 1
    assert older_reports.json()["has_more"] is False
    assert (
        client.get(
            "/api/v1/alliance/forum-reports", params={"before": "unknown-report"}
        ).status_code
        == 400
    )

    outsider = client.post(
        "/api/v1/auth/register", json={"name": "ForumGuest", "password": "forum-guest-123"}
    )
    assert outsider.status_code == 200
    assert client.get("/api/v1/state").json()["alliance_forum"] == []
    assert client.get("/api/v1/alliance/forum", params={"before": cursor}).status_code == 400
    assert (
        client.get("/api/v1/alliance/forum-reports", params={"before": report_cursor}).status_code
        == 400
    )


def test_message_history_is_keyset_paginated_and_keeps_channel_visibility(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "HistoryOwner", "password": "history-pass-123"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    module = importlib.import_module("fur_empire.api")
    sender, stranger = f"sender-{uuid4()}", f"stranger-{uuid4()}"
    with module.game.transaction() as db:
        for user_id, name in ((sender, "HistorySender"), (stranger, "HistoryStranger")):
            db.execute("INSERT INTO users VALUES (?,?,?)", (user_id, name, "unused"))
            module.game.create(db, user_id, name)
        for index in range(60):
            db.execute(
                "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
                "VALUES (?,?, 'world',NULL,?,?,0,1)",
                (f"world-history-{index:03}", sender, f"World {index}", 1000 + index),
            )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('world-history-hidden',?,'world',NULL,'hidden',2000,1,1)",
            (sender,),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('private-to-owner',?,'private',?,'private incoming',2001,0,1)",
            (sender, owner),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('private-from-owner',?,'private',?,'private outgoing',2002,0,1)",
            (owner, sender),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES ('private-for-stranger',?,'private',?,'not for owner',2003,0,1)",
            (sender, stranger),
        )

    state = client.get("/api/v1/state").json()
    assert state["message_has_more"]["world"] is True
    first = client.get("/api/v1/messages", params={"channel": "world"})
    assert first.status_code == 200
    page = first.json()
    assert len(page["messages"]) == 50
    assert page["has_more"] is True
    assert "world-history-hidden" not in {message["id"] for message in page["messages"]}
    cursor = page["messages"][-1]["id"]
    older = client.get("/api/v1/messages", params={"channel": "world", "before": cursor})
    assert older.status_code == 200
    assert len(older.json()["messages"]) == 10
    assert older.json()["has_more"] is False
    assert {message["id"] for message in page["messages"]}.isdisjoint(
        message["id"] for message in older.json()["messages"]
    )

    private = client.get("/api/v1/messages", params={"channel": "private"}).json()
    assert {message["id"] for message in private["messages"]} == {
        "private-to-owner",
        "private-from-owner",
    }
    assert (
        client.get("/api/v1/messages", params={"channel": "private", "before": cursor}).status_code
        == 400
    )
    assert client.get("/api/v1/messages", params={"channel": "invalid"}).status_code == 422


def test_market_offer_api_is_bounded_and_uses_the_current_world(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "MarketPageOwner", "password": "market-pass-123"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        colony = db.execute(
            "SELECT colony_id,world_id FROM colonies WHERE user_id=? AND is_home=TRUE",
            (owner,),
        ).fetchone()
        for index in range(51):
            db.execute(
                "INSERT INTO offers "
                "(id,owner,give_resource,give_amount,want_resource,want_amount,created,expires,"
                "status,buyer,world_id,colony_id) VALUES (?,?,?,?,?,?,?,?, 'open',NULL,?,?)",
                (
                    f"api-market-page-{index:03}",
                    owner,
                    0,
                    10,
                    1,
                    20,
                    1_700_000_000 + index,
                    int(time.time()) + 3600,
                    int(colony["world_id"]),
                    colony["colony_id"],
                ),
            )
    state = client.get("/api/v1/state").json()
    assert len(state["offers"]) == 50
    assert state["offers_has_more"] is True
    cursor = state["offers"][-1]["id"]
    page = client.get("/api/v1/market/offers", params={"before": cursor})
    assert page.status_code == 200
    assert len(page.json()["offers"]) == 1
    assert page.json()["has_more"] is False
    assert (
        client.get("/api/v1/market/offers", params={"before": "unknown-market-offer"}).status_code
        == 400
    )


def test_alliance_candidate_api_paginates_only_for_current_alliance_managers(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "InvitePageLeader", "password": "invite-pass-123"}
    )
    assert registered.status_code == 200
    owner_state = client.get("/api/v1/state").json()
    created = client.post(
        "/api/v1/command",
        json={
            "action": "alliance_create",
            "payload": {"tag": "IPG", "name": "Invite Page Guild"},
            "token": str(uuid4()),
        },
        headers={"X-CSRF-Token": owner_state["csrf"]},
    )
    assert created.status_code == 200
    owner_state = client.get("/api/v1/state").json()
    world_id = int(owner_state["active_world"]["id"])
    visible = {
        tuple(map(int, key.split(":")))
        for key, sector in owner_state["sector_intel"].items()
        if sector["status"] == "current"
    }
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        supply_target_id = str(uuid4())
        db.execute(
            "INSERT INTO users VALUES (?,?,?)",
            (supply_target_id, "InvitePageSupplyTarget", "unused"),
        )
        module.game.create(db, supply_target_id, "InvitePageSupplyTarget")
        supply_target = db.execute(
            "SELECT colony_id FROM colonies WHERE user_id=? AND world_id=? AND is_home=TRUE",
            (supply_target_id, world_id),
        ).fetchone()
        db.execute(
            "INSERT INTO members(user_id,alliance_id,role) VALUES (?,?,?)",
            (supply_target_id, owner_state["membership"]["alliance_id"], "member"),
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
        candidates = sorted((visible & land) - occupied)
        assert len(candidates) >= 51
        for index, (x, y) in enumerate(candidates[:51]):
            candidate_id = str(uuid4())
            candidate_name = f"InviteCandidate{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (candidate_id, candidate_name, "unused"),
            )
            module.game.create(db, candidate_id, candidate_name)
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
    updated = client.get("/api/v1/state").json()
    assert len(updated["alliance_candidates"]) == 50
    assert updated["alliance_candidates_has_more"] is True
    assert len(updated["alliance_supply_targets"]) == 1
    supply_page = client.get(
        "/api/v1/alliance/supply-targets", params={"before": supply_target["colony_id"]}
    )
    assert supply_page.status_code == 200
    assert supply_page.json() == {"targets": [], "has_more": False}
    assert (
        client.get(
            "/api/v1/alliance/supply-targets", params={"before": "unknown-supply-target"}
        ).status_code
        == 400
    )
    player_page = client.get("/api/v1/players", params={"before": updated["players"][0]["id"]})
    assert player_page.status_code == 200
    assert len(player_page.json()["players"]) == 50
    assert player_page.json()["has_more"] is True
    with module.game.transaction() as db:
        a, b = sorted((str(updated["id"]), supply_target_id))
        db.execute(
            "INSERT INTO friendships(a,b,requested_by,status,created,updated) VALUES (?,?,?,'pending',10,10)",
            (a, b, str(updated["id"])),
        )
    updated = client.get("/api/v1/state").json()
    assert updated["social"]["outgoing_requests"][0]["id"] == supply_target_id
    social_page = client.get(
        "/api/v1/social",
        params={
            "list": "outgoing_requests",
            "before": updated["social"]["outgoing_requests"][0]["id"],
        },
    )
    assert social_page.status_code == 200
    assert social_page.json() == {"entries": [], "has_more": False}
    assert (
        client.get(
            "/api/v1/social",
            params={"list": "friends", "before": updated["social"]["outgoing_requests"][0]["id"]},
        ).status_code
        == 400
    )
    cursor = updated["alliance_candidates"][-1]["id"]
    page = client.get("/api/v1/alliance/candidates", params={"before": cursor})
    assert page.status_code == 200
    assert len(page.json()["candidates"]) == 1
    assert page.json()["has_more"] is False

    guest = client.post(
        "/api/v1/auth/register", json={"name": "InvitePageGuest", "password": "guest-pass-123"}
    )
    assert guest.status_code == 200
    denied = client.get("/api/v1/alliance/candidates", params={"before": cursor})
    assert denied.status_code == 400
    assert (
        client.get(
            "/api/v1/alliance/supply-targets", params={"before": supply_target["colony_id"]}
        ).status_code
        == 400
    )


def test_admin_user_failure_and_audit_pages_require_current_moderation_role(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "AdminPageModerator", "password": "admin-page-123"}
    )
    assert registered.status_code == 200
    user_state = client.get("/api/v1/state").json()
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        db.execute("UPDATE profiles SET role='moderator' WHERE user_id=?", (user_state["id"],))
        failure_id = str(uuid4())
        db.execute(
            "INSERT INTO job_failures(id,user_id,job_id,attempts,error,created) "
            "VALUES (?,?,?,?,?,?)",
            (failure_id, user_state["id"], "admin-page-job", 2, "temporary failure", 100),
        )
        moderation_case_id = "admin-page-moderation-case"
        db.execute(
            "INSERT INTO moderation_cases"
            "(id,case_type,reporter_id,target_user_id,world_id,reason,created) "
            "VALUES (?,'mute_appeal',?,?,1,'review requested',100)",
            (moderation_case_id, user_state["id"], user_state["id"]),
        )
        for index in range(51):
            db.execute(
                "INSERT INTO audit(id,actor,action,target,details,created) VALUES (?,?,?,?,?,?)",
                (
                    f"admin-audit-page-{index:03}",
                    user_state["id"],
                    "moderation_test",
                    f"target-{index}",
                    "{}",
                    int(time.time()) + 1000 + index,
                ),
            )
    admin_state = client.get("/api/v1/state").json()
    assert len(admin_state["administration"]["users"]) == 1
    assert admin_state["administration"]["users_has_more"] is False
    assert admin_state["administration"]["failure_total"] == 1
    assert admin_state["administration"]["failures"][0]["id"] == failure_id
    assert admin_state["administration"]["failures_has_more"] is False
    assert len(admin_state["administration"]["audit"]) == 50
    assert admin_state["administration"]["audit_has_more"] is True
    assert admin_state["administration"]["cases"][0]["id"] == moderation_case_id
    assert admin_state["administration"]["cases_has_more"] is False

    users_page = client.get("/api/v1/admin/users", params={"before": user_state["id"]})
    assert users_page.status_code == 200
    assert users_page.json() == {"users": [], "has_more": False}
    failures_page = client.get("/api/v1/admin/job-failures", params={"before": failure_id})
    assert failures_page.status_code == 200
    assert failures_page.json() == {"failures": [], "has_more": False}
    cases_page = client.get("/api/v1/admin/moderation-cases", params={"before": moderation_case_id})
    assert cases_page.status_code == 200
    assert cases_page.json() == {"cases": [], "has_more": False}
    audit_cursor = admin_state["administration"]["audit"][-1]["id"]
    audit_page = client.get("/api/v1/admin/audit", params={"before": audit_cursor})
    assert audit_page.status_code == 200
    assert audit_page.json()["entries"][0]["id"] == "admin-audit-page-000"
    assert set(audit_page.json()["entries"][0]) == {"id", "action", "target", "created"}
    assert audit_page.json()["has_more"] is False
    assert client.get("/api/v1/admin/audit", params={"before": "unknown-audit"}).status_code == 400
    assert (
        client.get("/api/v1/admin/moderation-cases", params={"before": "unknown-case"}).status_code
        == 400
    )
    assert client.get("/api/v1/admin/users", params={"before": "unknown-user"}).status_code == 400
    assert (
        client.get("/api/v1/admin/job-failures", params={"before": "unknown-failure"}).status_code
        == 400
    )

    guest = client.post(
        "/api/v1/auth/register", json={"name": "AdminPageGuest", "password": "guest-page-123"}
    )
    assert guest.status_code == 200
    assert client.get("/api/v1/admin/users", params={"before": user_state["id"]}).status_code == 400
    assert (
        client.get("/api/v1/admin/job-failures", params={"before": failure_id}).status_code == 400
    )
    assert client.get("/api/v1/admin/audit", params={"before": audit_cursor}).status_code == 400
    assert (
        client.get(
            "/api/v1/admin/moderation-cases", params={"before": moderation_case_id}
        ).status_code
        == 400
    )


def test_public_diplomacy_event_pages_are_authenticated_and_cursor_checked(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "DiplomacyPager", "password": "diplomacy-pager-123"}
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        for index, (alliance_id, tag) in enumerate(
            (("chronicle-a", "CRA"), ("chronicle-b", "CRB"))
        ):
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) "
                "VALUES (?,?,?,'',?,?)",
                (alliance_id, tag, f"Chronicle {index}", owner, index),
            )
        for index in range(51):
            db.execute(
                "INSERT INTO alliance_diplomacy_events "
                "(id,alliance_a,alliance_b,actor_alliance,event_type,created) "
                "VALUES (?,?,?,?,?,?)",
                (
                    f"api-diplomacy-{index:03}",
                    "chronicle-a",
                    "chronicle-b",
                    "chronicle-a",
                    "nap_proposed",
                    int(time.time()) + 1000 + index,
                ),
            )
    current = client.get("/api/v1/state").json()
    assert len(current["diplomacy_events"]) == 50
    assert current["diplomacy_events_has_more"] is True
    cursor = current["diplomacy_events"][-1]["id"]
    older = client.get("/api/v1/diplomacy/events", params={"before": cursor})
    assert older.status_code == 200
    assert [event["id"] for event in older.json()["events"]] == ["api-diplomacy-000"]
    assert older.json()["has_more"] is False
    assert (
        client.get("/api/v1/diplomacy/events", params={"before": "unknown-event"}).status_code
        == 400
    )

    client.cookies.clear()
    assert client.get("/api/v1/diplomacy/events", params={"before": cursor}).status_code == 401


def test_active_event_page_endpoint_paginates_without_changing_event_bonus(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "EventPager", "password": "event-pager-123"}
    )
    assert registered.status_code == 200
    now = int(time.time())
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        for index in range(51):
            db.execute(
                "INSERT INTO events(id,name,starts,ends,bonus) VALUES (?,?,?,?,?)",
                (f"api-live-event-{index:03}", f"Event {index}", now - 100 + index, now + 86400, 1),
            )
    current = client.get("/api/v1/state").json()
    assert len(current["events"]) == 50
    assert current["events_has_more"] is True
    assert current["production_details"][0]["bonus_percent"] == 51
    older = client.get("/api/v1/events", params={"before": current["events"][-1]["id"]})
    assert older.status_code == 200
    assert [event["id"] for event in older.json()["events"]] == ["api-live-event-000"]
    assert older.json()["has_more"] is False
    assert client.get("/api/v1/events", params={"before": "unknown-event"}).status_code == 400


def test_ranking_page_is_scoped_to_authenticated_active_world(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "RankingOwner", "password": "ranking-pass-123"}
    )
    assert registered.status_code == 200
    state = client.get("/api/v1/state").json()
    assert state["ranking_score"] >= 0
    cursor = state["ranking"][0]["id"]
    page = client.get("/api/v1/ranking", params={"before": cursor})
    assert page.status_code == 200
    assert page.json()["entries"] == []
    assert page.json()["offset"] == 1
    assert page.json()["has_more"] is False
    assert [row["id"] for row in page.json()["military_entries"]] == [state["id"]]
    assert page.json()["military_entries"][0]["score"] == 0
    assert page.json()["alliance_military_entries"] == []
    assert client.get("/api/v1/ranking", params={"before": "unknown"}).status_code == 400


def test_alliance_directory_is_bounded_and_uses_a_validated_keyset_cursor(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "AllianceDirectory", "password": "directory-pass-123"},
    )
    assert registered.status_code == 200
    owner = client.get("/api/v1/state").json()["id"]
    module = importlib.import_module("fur_empire.api")
    with module.game.transaction() as db:
        for index in range(51):
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) "
                "VALUES (?,?,?,?,?,?)",
                (
                    f"directory-{index:03}",
                    f"D{index:03}",
                    f"Directory alliance {index}",
                    "",
                    owner,
                    index,
                ),
            )
    state = client.get("/api/v1/state").json()
    assert len(state["alliances"]) == 50
    assert state["alliances_has_more"] is True
    first_ids = [alliance["id"] for alliance in state["alliances"]]
    page = client.get("/api/v1/alliances", params={"before": first_ids[-1]})
    assert page.status_code == 200
    assert len(page.json()["alliances"]) == 1
    assert page.json()["has_more"] is False
    assert page.json()["alliances"][0]["id"] == "directory-050"
    assert client.get("/api/v1/alliances", params={"before": "unknown"}).status_code == 400


def test_alliance_member_api_pages_current_roster_and_requires_membership(client):
    owner = client.post(
        "/api/v1/auth/register", json={"name": "RosterOwner", "password": "roster-owner-123"}
    )
    assert owner.status_code == 200
    csrf = owner.json()["csrf"]
    created = client.post(
        "/api/v1/command",
        json={
            "action": "alliance_create",
            "payload": {"tag": "ROSTER", "name": "Roster Keepers"},
            "token": "create-roster-alliance",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 200
    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (owner_id,)
        ).fetchone()[0]
        for index in range(50):
            user_id = f"api-roster-{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)", (user_id, f"Roster {index:03}", "unused")
            )
            db.execute("INSERT INTO members VALUES (?,?,?)", (user_id, alliance_id, "member"))
    first_page = client.get("/api/v1/state").json()
    assert len(first_page["members"]) == 50
    assert first_page["members_has_more"] is True
    page = client.get(
        "/api/v1/alliance/members", params={"before": first_page["members"][-1]["user_id"]}
    )
    assert page.status_code == 200
    assert [entry["name"] for entry in page.json()["members"]] == ["Roster 049"]
    assert page.json()["has_more"] is False
    assert client.get("/api/v1/alliance/members", params={"before": "unknown"}).status_code == 400
    with module.game.transaction() as db:
        db.execute("DELETE FROM members WHERE user_id=?", (owner_id,))
    assert client.get("/api/v1/alliance/members").status_code == 400


def test_alliance_application_api_bounds_incoming_and_checks_manager_role(client):
    owner = client.post(
        "/api/v1/auth/register",
        json={"name": "ApplicationOwner", "password": "application-owner-123"},
    )
    assert owner.status_code == 200
    created = client.post(
        "/api/v1/command",
        json={
            "action": "alliance_create",
            "payload": {"tag": "APPLY", "name": "Application Keepers"},
            "token": "create-application-alliance",
        },
        headers={"X-CSRF-Token": owner.json()["csrf"]},
    )
    assert created.status_code == 200
    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (owner_id,)
        ).fetchone()[0]
        for index in range(51):
            applicant_id = f"api-applicant-{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (applicant_id, f"Applicant {index:03}", "unused"),
            )
            db.execute(
                "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?)",
                (f"api-application-{index:03}", alliance_id, applicant_id, index),
            )
    first = client.get("/api/v1/state").json()
    assert len(first["alliance_incoming_applications"]) == 50
    assert first["alliance_incoming_applications_has_more"] is True
    page = client.get(
        "/api/v1/alliance/applications",
        params={
            "direction": "incoming",
            "before": first["alliance_incoming_applications"][-1]["id"],
        },
    )
    assert page.status_code == 200
    assert [entry["id"] for entry in page.json()["applications"]] == ["api-application-000"]
    assert page.json()["has_more"] is False
    assert (
        client.get("/api/v1/alliance/applications", params={"direction": "invalid"}).status_code
        == 422
    )
    with module.game.transaction() as db:
        db.execute("UPDATE members SET role='member' WHERE user_id=?", (owner_id,))
    assert (
        client.get("/api/v1/alliance/applications", params={"direction": "incoming"}).status_code
        == 400
    )


def test_alliance_application_api_returns_only_the_current_players_outgoing_requests(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "ApplicationApplicant", "password": "application-applicant-123"},
    )
    assert registered.status_code == 200
    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    other_id = "foreign-application-owner"
    with module.game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (other_id, "Other Applicant", "unused"))
        for index, alliance_id in enumerate(("applicant-alliance", "other-alliance")):
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) VALUES (?,?,?,?,?,?)",
                (alliance_id, f"A{index}PP", f"Applicant Alliance {index}", "", owner_id, index),
            )
        db.execute(
            "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?)",
            ("own-application", "applicant-alliance", owner_id, 10),
        )
        db.execute(
            "INSERT INTO alliance_applications(id,alliance_id,user_id,created) VALUES (?,?,?,?)",
            ("foreign-application", "other-alliance", other_id, 11),
        )
    current = client.get("/api/v1/state").json()
    assert [entry["id"] for entry in current["alliance_applications"]] == ["own-application"]
    assert (
        next(
            alliance for alliance in current["alliances"] if alliance["id"] == "applicant-alliance"
        )["application_id"]
        == "own-application"
    )
    response = client.get("/api/v1/alliance/applications", params={"direction": "outgoing"})
    assert response.status_code == 200
    assert [entry["id"] for entry in response.json()["applications"]] == ["own-application"]
    assert response.json()["has_more"] is False
    assert (
        client.get("/api/v1/alliance/applications", params={"direction": "incoming"}).status_code
        == 400
    )


def test_alliance_invitation_api_pages_both_directions_and_rechecks_manager_role(client):
    owner = client.post(
        "/api/v1/auth/register",
        json={"name": "InvitationOwner", "password": "invitation-owner-123"},
    )
    assert owner.status_code == 200
    created = client.post(
        "/api/v1/command",
        json={
            "action": "alliance_create",
            "payload": {"tag": "INVITE", "name": "Invite Keepers"},
            "token": "create-invitation-alliance",
        },
        headers={"X-CSRF-Token": owner.json()["csrf"]},
    )
    assert created.status_code == 200
    module = importlib.import_module("fur_empire.api")
    owner_id = client.get("/api/v1/state").json()["id"]
    with module.game.transaction() as db:
        alliance_id = db.execute(
            "SELECT alliance_id FROM members WHERE user_id=?", (owner_id,)
        ).fetchone()[0]
        for index in range(51):
            invitee = f"api-invitee-{index:03}"
            db.execute(
                "INSERT INTO users VALUES (?,?,?)", (invitee, f"Invitee {index:03}", "unused")
            )
            db.execute(
                "INSERT INTO invites VALUES (?,?,?)",
                (f"outgoing-invite-{index:03}", alliance_id, invitee),
            )
            target_alliance = f"api-incoming-alliance-{index:03}"
            db.execute(
                "INSERT INTO alliances(id,tag,name,description,leader,created) VALUES (?,?,?,?,?,?)",
                (target_alliance, f"I{index:03}", f"Incoming {index:03}", "", owner_id, index),
            )
            db.execute(
                "INSERT INTO invites VALUES (?,?,?)",
                (f"incoming-invite-{index:03}", target_alliance, owner_id),
            )
    first = client.get("/api/v1/state").json()
    assert len(first["invites"]) == 50 and first["invites_has_more"] is True
    assert len(first["alliance_outgoing_invites"]) == 50
    assert first["alliance_outgoing_invites_has_more"] is True
    incoming = client.get(
        "/api/v1/alliance/invitations",
        params={"direction": "incoming", "before": first["invites"][-1]["id"]},
    )
    assert incoming.status_code == 200
    assert [entry["id"] for entry in incoming.json()["invitations"]] == ["incoming-invite-050"]
    outgoing = client.get(
        "/api/v1/alliance/invitations",
        params={"direction": "outgoing", "before": first["alliance_outgoing_invites"][-1]["id"]},
    )
    assert outgoing.status_code == 200
    assert [entry["name"] for entry in outgoing.json()["invitations"]] == ["Invitee 050"]
    assert (
        client.get("/api/v1/alliance/invitations", params={"direction": "invalid"}).status_code
        == 422
    )
    with module.game.transaction() as db:
        db.execute("UPDATE members SET role='member' WHERE user_id=?", (owner_id,))
    assert (
        client.get("/api/v1/alliance/invitations", params={"direction": "outgoing"}).status_code
        == 400
    )


def test_colony_abandon_api_accepts_the_command_but_protects_the_world_home(client):
    login = client.post(
        "/api/v1/auth/register", json={"name": "AbandonPilot", "password": "abandon-pilot-123"}
    )
    assert login.status_code == 200
    state = client.get("/api/v1/state").json()
    body = {
        "action": "colony_abandon",
        "payload": {"colony_id": state["colony_id"], "confirmation": state["colony_name"]},
        "token": "confirm-home-abandon",
    }
    assert client.post("/api/v1/command", json=body).status_code == 400
    rejected = client.post(
        "/api/v1/command", json=body, headers={"X-CSRF-Token": login.json()["csrf"]}
    )
    assert rejected.status_code == 400
    assert "Heimatkolonie" in rejected.json()["error"]
    assert client.get("/api/v1/state").json()["colony_id"] == state["colony_id"]


def test_registration_switch_blocks_new_accounts_but_existing_login_remains(client):
    registered = client.post(
        "/api/v1/auth/register", json={"name": "Founder", "password": "founder-pass-123"}
    )
    csrf = registered.json()["csrf"]
    import fur_empire.api as module

    with module.game.transaction() as db:
        db.execute(
            "UPDATE profiles SET role='admin' WHERE user_id=(SELECT id FROM users WHERE name=?)",
            ("Founder",),
        )
    changed = client.post(
        "/api/v1/command",
        json={
            "action": "admin_flag",
            "payload": {"key": "registration", "value": "false"},
            "token": "disable-registration",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 200
    denied = client.post(
        "/api/v1/auth/register", json={"name": "Latecomer", "password": "late-pass-123"}
    )
    assert denied.status_code == 400
    client.post("/api/v1/logout", json={}, headers={"X-CSRF-Token": csrf})
    login = client.post(
        "/api/v1/auth/login", json={"name": "Founder", "password": "founder-pass-123"}
    )
    assert login.status_code == 200
    assert client.get("/api/v1/state").json()["name"] == "Founder"


def test_expired_session_is_rejected_and_totp_code_cannot_be_replayed(client):
    import fur_empire.api as module
    from fur_empire.identity import totp

    name, password = "Secure", "secure-pass-123"
    assert (
        client.post("/api/v1/auth/register", json={"name": name, "password": password}).status_code
        == 200
    )
    session_hash = hashlib.sha256(client.cookies.get("fur_session").encode()).hexdigest()
    with module.game.transaction() as db:
        db.execute(
            "UPDATE sessions SET expires=? WHERE token=?", (int(time.time()) - 1, session_hash)
        )
    assert client.get("/api/v1/state").status_code == 401

    secret = "JBSWY3DPEHPK3PXP"
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone()[0]
        db.execute("UPDATE profiles SET totp=? WHERE user_id=?", (secret, user))
    code = totp(secret, int(time.time()) // 30)
    assert (
        client.post(
            "/api/v1/auth/login", json={"name": name, "password": password, "code": code}
        ).status_code
        == 200
    )
    replay = client.post(
        "/api/v1/auth/login", json={"name": name, "password": password, "code": code}
    )
    assert replay.status_code == 400
    assert "bereits verwendeter" in replay.json()["error"]


def test_login_accepts_and_consumes_one_recovery_code(client):
    import fur_empire.api as module
    from fur_empire.identity import digest, replace_recovery_codes

    name, password = "RecoveryPilot", "recovery-pilot-123"
    assert (
        client.post("/api/v1/auth/register", json={"name": name, "password": password}).status_code
        == 200
    )
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone()[0]
        db.execute("UPDATE profiles SET totp=? WHERE user_id=?", ("JBSWY3DPEHPK3PXP", user))
        codes = replace_recovery_codes(db, user)
    client.post(
        "/api/v1/logout",
        json={},
        headers={"X-CSRF-Token": client.get("/api/v1/state").json()["csrf"]},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"name": name, "password": password, "recovery_code": codes[0]},
    )
    assert login.status_code == 200
    assert client.get("/api/v1/state").status_code == 200
    client.post("/api/v1/logout", json={}, headers={"X-CSRF-Token": login.json()["csrf"]})
    replay = client.post(
        "/api/v1/auth/login",
        json={"name": name, "password": password, "recovery_code": codes[0]},
    )
    assert replay.status_code == 400
    assert "Recovery-Code" in replay.json()["error"]
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone()[0]
        assert (
            db.execute(
                "SELECT 1 FROM mfa_recovery_codes WHERE user_id=? AND code_hash=?",
                (user, digest(codes[0])),
            ).fetchone()
            is None
        )


def test_email_change_requires_correct_password_and_recovery_token_expiry(client):
    import fur_empire.api as module
    from fur_empire.identity import digest

    login = client.post(
        "/api/v1/auth/register", json={"name": "Account", "password": "account-pass-123"}
    )
    csrf = login.json()["csrf"]
    invalid = client.post(
        "/api/v1/account/private",
        json={"action": "email", "email": "changed@example.test", "password": "wrong-pass"},
        headers={"X-CSRF-Token": csrf},
    )
    assert invalid.status_code == 400
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name='Account'").fetchone()[0]
        assert (
            db.execute("SELECT email FROM profiles WHERE user_id=?", (user,)).fetchone()[0] is None
        )
        db.execute(
            "UPDATE profiles SET email=?,verified=1 WHERE user_id=?", ("account@example.test", user)
        )
    client.post(
        "/api/v1/account/public",
        json={"action": "request_reset", "email": "account@example.test"},
    )
    with module.game.transaction() as db:
        body = db.execute("SELECT body FROM outbox WHERE subject LIKE '%zurücksetzen%'").fetchone()[
            0
        ]
        token = body.split("\n\n")[1]
        db.execute(
            "UPDATE auth_tokens SET expires=? WHERE token=?", (int(time.time()) - 1, digest(token))
        )
    expired = client.post(
        "/api/v1/account/public",
        json={"action": "reset", "token": token, "password": "account-new-pass-123"},
    )
    assert expired.status_code == 400
    assert "abgelaufen" in expired.json()["error"]


def test_public_account_action_prunes_expired_auth_token_hashes(client):
    import fur_empire.api as module
    from fur_empire.identity import digest

    registered = client.post(
        "/api/v1/auth/register", json={"name": "TokenCleanup", "password": "cleanup-pass-123"}
    )
    assert registered.status_code == 200
    user = client.get("/api/v1/state").json()["id"]
    expired_hash = digest("expired-recovery-secret")
    live_hash = digest("live-recovery-secret")
    with module.game.transaction() as db:
        db.execute(
            "INSERT INTO auth_tokens(token,user_id,purpose,expires) VALUES (?,?,?,?)",
            (expired_hash, user, "reset", int(time.time()) - 1),
        )
        db.execute(
            "INSERT INTO auth_tokens(token,user_id,purpose,expires) VALUES (?,?,?,?)",
            (live_hash, user, "verify", int(time.time()) + 600),
        )
    response = client.post(
        "/api/v1/account/public", json={"action": "request_reset", "email": "unknown@example.test"}
    )
    assert response.status_code == 200
    with module.game.transaction() as db:
        assert not db.execute("SELECT 1 FROM auth_tokens WHERE token=?", (expired_hash,)).fetchone()
        assert db.execute("SELECT 1 FROM auth_tokens WHERE token=?", (live_hash,)).fetchone()


def test_origin_password_and_uniqueness(client):
    body = {"name": "Commander", "password": "test-pass-123"}
    assert (
        client.post(
            "/api/v1/auth/register", json=body, headers={"Origin": "https://attacker.test"}
        ).status_code
        == 403
    )
    assert client.post("/api/v1/auth/register", json=body).status_code == 200
    assert client.post("/api/v1/auth/register", json=body).status_code == 400
    assert (
        client.post("/api/v1/auth/login", json={**body, "password": "wrong-pass"}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "Other", "password": "short"}
        ).status_code
        == 422
    )


def test_login_has_account_and_network_rate_limit_without_cross_account_lockout(client):
    for name in ("PilotAlpha", "PilotBravo"):
        assert (
            client.post(
                "/api/v1/auth/register", json={"name": name, "password": "pilot-pass-123"}
            ).status_code
            == 200
        )

    for _attempt in range(5):
        denied = client.post(
            "/api/v1/auth/login", json={"name": "PilotAlpha", "password": "wrong-pass-123"}
        )
        assert denied.status_code == 400
        assert denied.json()["error"] == "Name oder Passwort stimmt nicht."

    throttled = client.post(
        "/api/v1/auth/login", json={"name": "PilotAlpha", "password": "wrong-pass-123"}
    )
    assert throttled.status_code == 400
    assert throttled.json()["error"] == "Zu viele Anfragen. Bitte eine Minute warten."

    other_account = client.post(
        "/api/v1/auth/login", json={"name": "PilotBravo", "password": "pilot-pass-123"}
    )
    assert other_account.status_code == 200


def test_login_and_password_recovery_errors_do_not_enumerate_accounts(client):
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "KnownPilot", "password": "known-pass-123"}
        ).status_code
        == 200
    )
    known_login = client.post(
        "/api/v1/auth/login", json={"name": "KnownPilot", "password": "wrong-pass-123"}
    )
    unknown_login = client.post(
        "/api/v1/auth/login", json={"name": "UnknownPilot", "password": "wrong-pass-123"}
    )
    assert known_login.status_code == unknown_login.status_code == 400
    known_error = known_login.json()
    unknown_error = unknown_login.json()
    assert known_error["error"] == unknown_error["error"] == "Name oder Passwort stimmt nicht."
    assert known_error["code"] == unknown_error["code"]
    assert known_error["request_id"] and unknown_error["request_id"]
    assert known_error["request_id"] != unknown_error["request_id"]

    import fur_empire.api as module

    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users WHERE name='KnownPilot'").fetchone()[0]
        db.execute(
            "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
            ("known@example.test", user),
        )
    known_recovery = client.post(
        "/api/v1/account/public",
        json={"action": "request_reset", "email": "known@example.test"},
    )
    unknown_recovery = client.post(
        "/api/v1/account/public",
        json={"action": "request_reset", "email": "unknown@example.test"},
    )
    assert known_recovery.status_code == unknown_recovery.status_code == 200
    assert known_recovery.json() == unknown_recovery.json()


def test_account_export_is_owner_scoped_and_excludes_security_or_foreign_content(client):
    owner = client.post(
        "/api/v1/auth/register", json={"name": "ExportOwner", "password": "export-owner-123"}
    )
    assert owner.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/register", json={"name": "OtherPilot", "password": "other-pilot-123"}
        ).status_code
        == 200
    )
    owner_login = client.post(
        "/api/v1/auth/login", json={"name": "ExportOwner", "password": "export-owner-123"}
    )
    assert owner_login.status_code == 200

    import fur_empire.api as module
    from fur_empire.identity import digest, totp

    with module.game.transaction() as db:
        owner_id = db.execute("SELECT id FROM users WHERE name='ExportOwner'").fetchone()[0]
        other_id = db.execute("SELECT id FROM users WHERE name='OtherPilot'").fetchone()[0]
        owner_state = module.game.read(db, owner_id)
        owner_state["item_inventory"] = {"repair_kit": 7}
        owner_state["item_reserve"] = {"loot_material": 3}
        module.game.save(db, owner_state)
        db.execute(
            "UPDATE profiles SET email=?,verified=1,totp=? WHERE user_id=?",
            ("owner@example.test", "JBSWY3DPEHPK3PXP", owner_id),
        )
        db.execute(
            "INSERT INTO mfa_recovery_codes(user_id,code_hash,created) VALUES (?,?,?)",
            (owner_id, digest("one-time-recovery-material"), int(time.time())),
        )
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("owner-template", owner_id, "My formation", "attack", '{"ranger":3}', 0, 1),
        )
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("other-template", other_id, "Foreign formation", "attack", '{"mech":4}', 0, 2),
        )
        db.execute(
            "INSERT INTO production_templates(id,owner,name,kind,item_key,count,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("owner-production", owner_id, "Woodline", "build", "wood", 1, 3),
        )
        db.execute(
            "INSERT INTO production_templates(id,owner,name,kind,item_key,count,created) "
            "VALUES (?,?,?,?,?,?,?)",
            ("other-production", other_id, "Foreign queue", "train", "ranger", 10, 4),
        )
        friend_a, friend_b = sorted((owner_id, other_id))
        db.execute(
            "INSERT INTO friendships(a,b,requested_by,status,created,updated) "
            "VALUES (?,?,?,'accepted',?,?)",
            (friend_a, friend_b, owner_id, 5, 5),
        )
        db.execute(
            "INSERT INTO map_bookmarks(user_id,target_id,created) VALUES (?,?,?)",
            (owner_id, "owner-target", 1),
        )
        db.execute(
            "INSERT INTO map_bookmarks(user_id,target_id,created) VALUES (?,?,?)",
            (other_id, "foreign-target", 2),
        )
        db.execute(
            "INSERT INTO player_notes"
            "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
            "VALUES (?,?,1,'sector',?,?,NULL,?,?,?)",
            ("owner-note", owner_id, 5, 7, "My private note", 1, 2),
        )
        db.execute(
            "INSERT INTO player_notes"
            "(id,owner,world_id,target_kind,sector_x,sector_y,report_id,body,created,updated) "
            "VALUES (?,?,1,'sector',?,?,NULL,?,?,?)",
            ("other-note", other_id, 9, 11, "Foreign note", 1, 2),
        )
        db.execute(
            "INSERT INTO messages(id,sender,channel,recipient,body,created,hidden,world_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ("foreign-message", other_id, "private", owner_id, "FOREIGN MESSAGE BODY", 1, 0, 1),
        )
        owner_password_hash = db.execute(
            "SELECT password FROM users WHERE id=?", (owner_id,)
        ).fetchone()[0]

    export_body = {
        "action": "export",
        "password": "export-owner-123",
        "code": totp("JBSWY3DPEHPK3PXP", int(time.time()) // 30),
    }
    bad_csrf = client.post("/api/v1/account/private", json=export_body)
    assert bad_csrf.status_code == 400
    wrong_password = client.post(
        "/api/v1/account/private",
        json={**export_body, "password": "wrong-export-password"},
        headers={"X-CSRF-Token": owner_login.json()["csrf"]},
    )
    assert wrong_password.status_code == 400
    assert "Passwort" in wrong_password.json()["error"]
    response = client.post(
        "/api/v1/account/private",
        json=export_body,
        headers={"X-CSRF-Token": owner_login.json()["csrf"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert (
        'attachment; filename="fur-empire-account-export.json"'
        == response.headers["content-disposition"]
    )
    assert response.headers["cache-control"] == "no-store"
    export = response.json()
    assert export["format"] == "fur-empire-account-export"
    assert export["account"]["name"] == "ExportOwner"
    assert export["account"]["email"] == "owner@example.test"
    assert export["account"]["mfa_enabled"] is True
    assert len(export["colonies"]) == 1
    assert export["colonies"][0]["colony_id"] == owner_id
    assert export["colonies"][0]["item_inventory"] == {"repair_kit": 7}
    assert export["colonies"][0]["item_reserve"] == {"loot_material": 3}
    assert [item["name"] for item in export["mission_templates"]] == ["My formation"]
    assert export["production_templates"] == [
        {"name": "Woodline", "kind": "build", "key": "wood", "count": 1, "created": 3}
    ]
    assert export["social"]["friends"] == [{"name": "OtherPilot", "created": 5}]
    assert export["social"]["blocked"] == []
    assert export["notes"] == [
        {
            "world_id": 1,
            "target_kind": "sector",
            "x": 5,
            "y": 7,
            "report_id": None,
            "body": "My private note",
            "created": 1,
            "updated": 2,
        }
    ]
    assert export["map_bookmarks"] == [{"target_id": "owner-target", "created": 1}]
    assert all(
        set(item) == {"created", "expires", "user_agent"} for item in export["active_sessions"]
    )
    encoded = response.text
    for forbidden in (
        owner_password_hash,
        "JBSWY3DPEHPK3PXP",
        digest("one-time-recovery-material"),
        "FOREIGN MESSAGE BODY",
        "Foreign formation",
        "foreign-target",
        "Foreign note",
        str(other_id),
    ):
        assert forbidden not in encoded
    assert "csrf" not in encoded.lower()
    assert '"token"' not in encoded.lower()


def test_accounts_have_separate_resources(client):
    first = client.post(
        "/api/v1/auth/register", json={"name": "First", "password": "password-one"}
    ).json()
    client.post(
        "/api/v1/command",
        json={
            "action": "trade",
            "payload": {"source": 0, "dest": 1, "amount": 100},
            "token": "unique-token",
        },
        headers={"X-CSRF-Token": first["csrf"]},
    )
    client.post("/api/v1/auth/register", json={"name": "Second", "password": "password-two"})
    state = client.get("/api/v1/state").json()
    assert state["resources"][0] >= 1200
    assert len(state["ranking"]) == 2


def test_language_preference_persists_and_is_account_scoped(client):
    endpoint = "/api/v1/account/language"
    assert client.post(endpoint, json={"language": "fr"}).status_code == 401
    first = client.post(
        "/api/v1/auth/register", json={"name": "LanguageOne", "password": "language-pass-one"}
    ).json()
    assert client.get("/api/v1/state").json()["language"] == "de"
    assert client.post(endpoint, json={"language": "fr"}).status_code == 400
    headers = {"X-CSRF-Token": first["csrf"]}
    for language in ("de", "en", "es", "fr"):
        response = client.post(endpoint, json={"language": language}, headers=headers)
        assert response.status_code == 200
        assert client.get("/api/v1/state").json()["language"] == language
    assert client.post(endpoint, json={"language": "invalid"}, headers=headers).status_code == 422
    client.post(
        "/api/v1/auth/register", json={"name": "LanguageTwo", "password": "language-pass-two"}
    )
    assert client.get("/api/v1/state").json()["language"] == "de"
    client.post("/api/v1/auth/login", json={"name": "LanguageOne", "password": "language-pass-one"})
    assert client.get("/api/v1/state").json()["language"] == "fr"


def test_authenticated_live_chat_streams_persistent_messages(client):
    auth = client.post(
        "/api/v1/auth/register",
        json={"name": "LiveChatOne", "password": "live-chat-password"},
    ).json()
    with client.websocket_connect("/api/v1/chat/live") as socket:
        initial = socket.receive_json()
        assert initial["type"] == "snapshot"
        assert initial["messages"]["world"] == []
        response = client.post(
            "/api/v1/command",
            headers={"X-CSRF-Token": auth["csrf"]},
            json={
                "action": "message",
                "payload": {"channel": "world", "body": "Realtime hello"},
                "token": str(uuid4()),
            },
        )
        assert response.status_code == 200
        update = socket.receive_json()
        assert update["messages"]["world"][0]["body"] == "Realtime hello"


def test_live_chat_delivers_between_two_real_accounts_without_reload(client):
    first = client.post(
        "/api/v1/auth/register",
        json={"name": "RealtimeAlpha", "password": "realtime-alpha-pass"},
    ).json()
    import fur_empire.api as module

    with TestClient(module.app) as second:
        second.post(
            "/api/v1/auth/register",
            json={"name": "RealtimeBravo", "password": "realtime-bravo-pass"},
        )
        with second.websocket_connect("/api/v1/chat/live") as socket:
            assert socket.receive_json()["messages"]["world"] == []
            sent = client.post(
                "/api/v1/command",
                headers={"X-CSRF-Token": first["csrf"]},
                json={
                    "action": "message",
                    "payload": {"channel": "world", "body": "Visible to Bravo"},
                    "token": str(uuid4()),
                },
            )
            assert sent.status_code == 200
            delivered = socket.receive_json()["messages"]["world"][0]
            assert delivered["name"] == "RealtimeAlpha"
            assert delivered["body"] == "Visible to Bravo"


def test_live_chat_rejects_anonymous_connections(client):
    client.cookies.clear()
    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect("/api/v1/chat/live"),
    ):
        pass
    assert closed.value.code == 4401


def test_beta_registration_records_version_and_rejects_missing_acceptance(client):
    body = {
        "name": "BetaCommander",
        "password": "beta-password-123",
        "password_confirmation": "different-password",
        "email": "beta@example.test",
        "registration_version": "2026-11-20",
        "language": "es",
    }
    assert client.post("/api/v1/auth/register", json=body).status_code == 400
    body["password_confirmation"] = body["password"]
    assert client.post("/api/v1/auth/register", json=body).status_code == 400
    body.update(terms_accepted=True, privacy_acknowledged=True)
    assert client.post("/api/v1/auth/register", json=body).status_code == 200
    beta_state = client.get("/api/v1/state").json()
    assert beta_state["language"] == "es"
    command_response = client.post(
        "/api/v1/command",
        headers={"X-CSRF-Token": beta_state["csrf"]},
        json={
            "action": "message",
            "payload": {"channel": "world", "body": "Beta access works"},
            "token": str(uuid4()),
        },
    )
    assert command_response.status_code == 200
    import fur_empire.api as module

    with module.game.transaction() as db:
        row = db.execute(
            "SELECT terms_version,privacy_version,language FROM registration_acceptance"
        ).fetchone()
        assert tuple(row) == ("2026-11-20", "2026-11-20", "es")
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM auth_tokens").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM email_verification_pending").fetchone()[0] == 0


def test_post_beta_registration_requires_only_new_accounts_to_verify(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_DB", str(tmp_path / "regular-registration.sqlite3"))
    monkeypatch.setenv("FUR_ENV", "test")
    monkeypatch.setenv("FUR_EMBEDDED_WORKER", "false")
    monkeypatch.setenv("BETA_MODE", "false")
    monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION_REQUIRED", "true")
    import fur_empire.api as module

    importlib.reload(module)
    with TestClient(module.app) as regular:
        payload = {
            "name": "RegularCommander",
            "password": "regular-password-123",
            "password_confirmation": "regular-password-123",
            "email": "regular@example.test",
            "registration_version": "2026-11-20",
            "language": "fr",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        }
        created = regular.post("/api/v1/auth/register", json=payload)
        assert created.status_code == 202
        assert created.json()["requires_email_verification"] is True
        denied = regular.post(
            "/api/v1/auth/login",
            json={"name": payload["name"], "password": payload["password"]},
        )
        assert denied.status_code == 400
        with module.game.transaction() as db:
            mail = db.execute(
                "SELECT body FROM outbox WHERE recipient=? ORDER BY created DESC LIMIT 1",
                (payload["email"],),
            ).fetchone()
        token = str(mail["body"]).split("\n\n")[1]
        confirmed = regular.post(
            "/api/v1/account/public", json={"action": "verify", "token": token}
        )
        assert confirmed.status_code == 200
        logged_in = regular.post(
            "/api/v1/auth/login",
            json={"name": payload["name"], "password": payload["password"]},
        )
        assert logged_in.status_code == 200
    # This test reloads the process-global API module; restore the normal beta policy for
    # subsequent tests that intentionally import the same module without their own fixture.
    monkeypatch.setenv("BETA_MODE", "true")
    monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION_REQUIRED", "false")
    importlib.reload(module)
