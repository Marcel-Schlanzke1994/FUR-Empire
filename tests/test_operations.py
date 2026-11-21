import importlib
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fur_empire.config import Settings
from fur_empire.game import Game, RuleError, identity
from fur_empire.identity import Accounts
from fur_empire.manage import (
    _insert_demo_accounts,
    generate_webpush_key_pair,
    seed_demo_database,
    worker_recent,
)
from fur_empire.worker import cycle, deliver


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_DB", str(tmp_path / "api.sqlite3"))
    monkeypatch.setenv("FUR_EMBEDDED_WORKER", "false")
    import fur_empire.api as module

    importlib.reload(module)
    with TestClient(module.app) as client:
        response = client.post(
            "/api/v1/auth/register", json={"name": "Operator", "password": "test-password-123"}
        )
        csrf = response.json()["csrf"]
        yield module, client, {"X-CSRF-Token": csrf}


def test_production_config_fails_closed(monkeypatch):
    monkeypatch.setenv("FUR_ENV", "production")
    for key in (
        "DATABASE_URL",
        "DB_HOST",
        "PUBLIC_ORIGIN",
        "SMTP_HOST",
        "SMTP_FROM",
        "OPERATOR_NAME",
        "OPERATOR_CONTACT",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="Produktionskonfiguration unvollständig"):
        Settings.load("local.sqlite3")


def test_staging_uses_secure_sessions_and_local_mailpit(monkeypatch):
    values = {
        "FUR_ENV": "staging",
        "DATABASE_URL": "postgresql://fur@db/fur_staging",
        "PUBLIC_ORIGIN": "https://localhost:8443",
        "SMTP_HOST": "mailpit",
        "SMTP_PORT": "1025",
        "SMTP_TLS": "false",
        "SMTP_FROM": "FUR Empire <noreply@localhost>",
        "OPERATOR_NAME": "Local Stage",
        "OPERATOR_CONTACT": "stage@localhost",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    settings = Settings.load("unused.sqlite3")
    assert settings.production
    assert settings.origin == "https://localhost:8443"
    assert settings.admin_mfa

    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    with pytest.raises(RuntimeError, match="ausschließlich den lokalen Mailpit"):
        Settings.load("unused.sqlite3")


def test_beta_account_policy_is_explicit_and_consistent(monkeypatch):
    monkeypatch.setenv("FUR_ENV", "test")
    monkeypatch.setenv("BETA_MODE", "true")
    monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION_REQUIRED", "false")
    settings = Settings.load("unused.sqlite3")
    assert settings.beta_mode is True
    assert settings.email_verification_required is False
    monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION_REQUIRED", "true")
    with pytest.raises(RuntimeError, match="kann nicht"):
        Settings.load("unused.sqlite3")
    monkeypatch.setenv("BETA_MODE", "invalid")
    with pytest.raises(RuntimeError, match="true oder false"):
        Settings.load("unused.sqlite3")


def test_webpush_key_generation_is_one_time_and_config_checks_public_private_match(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("FUR_ENV", "test")
    key_file = tmp_path / "webpush-private.pem"
    public_key = generate_webpush_key_pair(key_file)
    assert key_file.read_text(encoding="ascii").startswith("-----BEGIN PRIVATE KEY-----")
    with pytest.raises(FileExistsError, match="bleibt unverändert"):
        generate_webpush_key_pair(key_file)

    monkeypatch.setenv("WEBPUSH_PUBLIC_KEY", public_key)
    monkeypatch.setenv("WEBPUSH_PRIVATE_KEY_FILE", str(key_file))
    monkeypatch.setenv("WEBPUSH_SUBJECT", "mailto:ops@example.test")
    settings = Settings.load("unused.sqlite3")
    assert settings.webpush_public_key == public_key
    assert settings.webpush_private_key_file == str(key_file)

    monkeypatch.setenv(
        "WEBPUSH_PUBLIC_KEY", ("A" if public_key[0] != "A" else "B") + public_key[1:]
    )
    with pytest.raises(RuntimeError, match="passt nicht"):
        Settings.load("unused.sqlite3")


def test_demo_seed_creates_only_isolated_local_accounts(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_ENV", "local")
    target = tmp_path / "demo.sqlite3"

    credentials = seed_demo_database(target, account_count=3)

    assert [entry[0] for entry in credentials] == ["DemoAstra", "DemoBoreal", "DemoCinder"]
    assert all(len(password) >= 20 for _, password, _ in credentials)
    game = Game(target)
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 3
        assert db.execute("SELECT count(*) FROM colonies").fetchone()[0] == 3
        assert (
            len(json.loads(db.execute("SELECT state FROM world WHERE id=1").fetchone()[0])) == 104
        )


def test_demo_seed_refuses_existing_default_and_production_databases(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_ENV", "local")
    target = tmp_path / "existing.sqlite3"
    target.write_bytes(b"preserve this file")
    with pytest.raises(FileExistsError):
        seed_demo_database(target)
    assert target.read_bytes() == b"preserve this file"

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Standard-Spielstand"):
        seed_demo_database(Path("data/empire.sqlite3"))
    monkeypatch.setenv("FUR_ENV", "production")
    with pytest.raises(ValueError, match="nur in lokaler oder Testumgebung"):
        seed_demo_database(tmp_path / "production-demo.sqlite3")


def test_demo_seed_validates_account_count(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_ENV", "test")
    with pytest.raises(ValueError, match="zwischen 2 und 10"):
        seed_demo_database(tmp_path / "too-few.sqlite3", account_count=1)
    ten_accounts = seed_demo_database(tmp_path / "ten-accounts.sqlite3", account_count=10)
    assert len(ten_accounts) == len({name for name, _, _ in ten_accounts}) == 10

    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/production")
    with pytest.raises(ValueError, match="keine konfigurierte Serverdatenbank"):
        seed_demo_database(tmp_path / "server-env.sqlite3")


def test_worker_health_probe_reads_heartbeat_without_migrating(tmp_path):
    database = tmp_path / "worker.sqlite3"
    game = Game(database)
    with game.transaction() as db:
        db.execute("INSERT INTO worker_status(id,heartbeat) VALUES (1,?)", (1000,))
    assert worker_recent(str(database), now=1020)
    assert not worker_recent(str(database), now=1031)


def test_email_outbox_delivery_is_committed_and_retry_is_visible(tmp_path, monkeypatch):
    monkeypatch.setenv("FUR_ENV", "test")
    monkeypatch.setenv("FUR_DB", str(tmp_path / "outbox.sqlite3"))
    monkeypatch.setenv("SMTP_HOST", "mail.test")
    monkeypatch.setenv("SMTP_PORT", "25")
    monkeypatch.setenv("SMTP_TLS", "false")
    monkeypatch.setenv("SMTP_FROM", "FUR Empire <noreply@example.test>")
    settings = Settings.load("unused.sqlite3")
    game = Game(settings.database)
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "Outbox", "unused"))
        game.create(db, user, "Outbox")
        Accounts(game).send_token(db, user, "verify", "pilot@example.test")

    sent = []

    class SuccessSMTP:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("mail.test", 25, 10)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr("fur_empire.worker.smtplib.SMTP", SuccessSMTP)
    deliver(game, settings)
    with game.transaction() as db:
        row = db.execute("SELECT * FROM outbox").fetchone()
        assert row["status"] == "sent"
        assert row["attempts"] == 1
        assert row["body"] == ""
    assert len(sent) == 1
    assert sent[0]["To"] == "pilot@example.test"
    assert sent[0]["Message-ID"].startswith("<")

    class FailedSMTP(SuccessSMTP):
        def send_message(self, _message):
            raise OSError("test SMTP unavailable")

    with game.transaction() as db:
        Accounts(game).send_token(db, user, "verify", "pilot@example.test")
    monkeypatch.setattr("fur_empire.worker.smtplib.SMTP", FailedSMTP)
    deliver(game, settings)
    with game.transaction() as db:
        retry = db.execute("SELECT * FROM outbox WHERE status='pending'").fetchone()
        assert retry["attempts"] == 1
        assert retry["body"]


def test_staging_seed_marks_only_generated_test_profiles_verified(tmp_path):
    game = Game(tmp_path / "staging.sqlite3")
    accounts = _insert_demo_accounts(game, 3, marker="staging_demo_seeded")
    assert len(accounts) == 3
    with game.transaction() as db:
        profiles = db.execute("SELECT email,verified FROM profiles ORDER BY email").fetchall()
        assert all(row[1] == 1 and row[0].endswith("@staging.invalid") for row in profiles)
    assert _insert_demo_accounts(game, 3, marker="staging_demo_seeded") == []
    with game.transaction() as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 3


def test_production_disables_local_mail_and_requires_verification(api, monkeypatch):
    module, client, headers = api
    from dataclasses import replace

    monkeypatch.setattr(
        module,
        "settings",
        replace(
            module.settings,
            production=True,
            origin="https://fur.example.org",
            admin_mfa=True,
            beta_mode=False,
            email_verification_required=True,
        ),
    )
    assert client.get("/api/v1/account/local-mail").status_code == 400
    with module.game.transaction() as db:
        user_id = db.execute("SELECT id FROM users WHERE name='Operator'").fetchone()[0]
        db.execute(
            "INSERT INTO email_verification_pending(user_id,created) VALUES (?,?)",
            (user_id, 0),
        )
    body = {"action": "build", "payload": {"key": "wood"}, "token": identity()}
    assert client.post("/api/v1/command", json=body, headers=headers).status_code == 403
    h = {**headers, "Origin": "https://fur.example.org"}
    result = client.post("/api/v1/command", json=body, headers=h)
    assert result.status_code == 400
    assert "E-Mail" in result.json()["error"]
    with module.game.transaction() as db:
        user_id = db.execute("SELECT id FROM users WHERE name='Operator'").fetchone()[0]
        db.execute("UPDATE profiles SET role='admin',verified=1 WHERE user_id=?", (user_id,))
    admin_result = client.post(
        "/api/v1/command",
        json={
            "action": "admin_flag",
            "payload": {"key": "pvp", "value": "false"},
            "token": identity(),
        },
        headers=h,
    )
    assert admin_result.status_code == 400
    assert "Authenticator" in admin_result.json()["error"]


def test_csrf_host_strict_payloads_and_persistent_limit(api):
    _, client, headers = api
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400
    body = {"action": "train", "payload": {"key": "ranger", "count": True}, "token": identity()}
    assert client.post("/api/v1/command", json=body, headers=headers).status_code == 422
    assert (
        client.post(
            "/api/v1/command", json={**body, "action": "not-an-action"}, headers=headers
        ).status_code
        == 422
    )
    for _ in range(10):
        assert (
            client.post(
                "/api/v1/account/public",
                json={"action": "request_reset", "email": "missing@example.test"},
            ).status_code
            == 200
        )
    response = client.post(
        "/api/v1/account/public", json={"action": "request_reset", "email": "missing@example.test"}
    )
    assert response.status_code == 400
    assert "Zu viele" in response.json()["error"]


def test_private_account_actions_require_csrf_and_update_email(api):
    _, client, headers = api
    data = {
        "action": "email",
        "email": "new-address@example.test",
        "password": "test-password-123",
    }
    rejected = client.post("/api/v1/account/private", json=data)
    assert rejected.status_code == 400
    assert "Sitzungsschutz" in rejected.json()["error"]

    accepted = client.post("/api/v1/account/private", json=data, headers=headers)
    assert accepted.status_code == 200
    assert accepted.json() == {"ok": True}
    state = client.get("/api/v1/state").json()
    assert state["profile"]["email"] == "new-address@example.test"
    assert not state["profile"]["verified"]


def test_reset_revokes_sessions_and_token_is_single_use(api):
    module, client, _headers = api
    with module.game.transaction() as db:
        user = db.execute("SELECT id FROM users").fetchone()[0]
        db.execute(
            "UPDATE profiles SET email=?,verified=1 WHERE user_id=?",
            ("operator@example.test", user),
        )
    client.post(
        "/api/v1/account/public", json={"action": "request_reset", "email": "operator@example.test"}
    )
    with module.game.transaction() as db:
        body = db.execute("SELECT body FROM outbox WHERE subject LIKE '%zurücksetzen%'").fetchone()[
            0
        ]
        token = body.split("\n\n")[1]
    response = client.post(
        "/api/v1/account/public",
        json={"action": "reset", "token": token, "password": "new-test-pass-123"},
    )
    assert response.status_code == 200
    assert client.get("/api/v1/state").status_code == 401
    assert (
        client.post(
            "/api/v1/account/public",
            json={"action": "reset", "token": token, "password": "new-test-pass-123"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"name": "Operator", "password": "new-test-pass-123"}
        ).status_code
        == 200
    )


def test_failed_job_quarantine_does_not_block_other_players(tmp_path, monkeypatch):
    now = int(time.time())
    monkeypatch.setattr("fur_empire.game.time.time", lambda: now)
    game = Game(tmp_path / "world.sqlite3")
    users = [identity(), identity()]
    bad = identity()
    with game.transaction() as db:
        for index, user in enumerate(users):
            db.execute("INSERT INTO users VALUES (?,?,?)", (user, f"User{index}", "unused"))
            game.create(db, user, f"User{index}")
        state = game.read(db, users[0])
        state["jobs"] = [
            {
                "id": bad,
                "kind": "raid",
                "key": "broken-target",
                "due": now - 1,
                "army": {"ranger": 1},
                "travel": 5,
                "label": "Broken",
            }
        ]
        game.save(db, state)
    for _ in range(3):
        cycle(game)
    with game.transaction() as db:
        assert db.execute("SELECT attempts FROM job_failures").fetchone()[0] == 3
        game.command(db, users[1], "build", {"key": "wood"}, identity())
        assert game.view(db, users[0])["jobs"][0]["id"] == bad
    with pytest.raises(RuleError, match="Korrektur"), game.transaction() as db:
        game.command(db, users[0], "build", {"key": "wood"}, identity())


def test_quarantined_upgrade_freezes_followups_until_head_is_cancelled(tmp_path, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    game = Game(tmp_path / "world.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "Queued", "unused"))
        game.create(db, user, "Queued")
        colony = game.read(db, user)
        colony["resources"] = [20000, 20000, 20000]
        colony["buildings"]["storage"] = 10
        game.save(db, colony)
        first = game.command(db, user, "build", {"key": "wall"}, identity())["jobs"][0]
        second = game.command(db, user, "build", {"key": "lab"}, identity())["jobs"][-1]
        db.execute(
            "INSERT INTO job_failures VALUES (?,?,?,?,?,?)",
            (identity(), user, first["id"], 3, "forced quarantine", clock[0]),
        )

    clock[0] = second["due"] + 10
    with game.transaction() as db:
        game.advance(db, clock[0])
        colony = game.read(db, user)
        assert colony["buildings"]["wall"] == 0
        assert colony["buildings"]["lab"] == 0
        assert {job["id"] for job in colony["jobs"]} == {first["id"], second["id"]}
        result = game.command(db, user, "cancel_job", {"key": first["id"]}, identity())
        promoted = next(job for job in result["jobs"] if job["id"] == second["id"])
        assert promoted["queued"] is False
        assert promoted["started_at"] == clock[0]
        assert promoted["due"] == clock[0] + promoted["duration"]

    clock[0] = promoted["due"]
    with game.transaction() as db:
        game.advance(db, clock[0])
        assert game.read(db, user)["buildings"]["lab"] == 1


def test_season_closes_before_later_build(tmp_path, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("fur_empire.game.time.time", lambda: clock[0])
    game = Game(tmp_path / "world.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "Season", "unused"))
        game.create(db, user, "Season")
        db.execute(
            "INSERT INTO seasons(id,name,starts,ends,archived,standings) VALUES (?,?,?,?,0,?)",
            (identity(), "Short", clock[0] - 10, clock[0] + 2, "[]"),
        )
        game.command(db, user, "build", {"key": "wood"}, identity())
    clock[0] += 20
    with game.transaction() as db:
        result = game.view(db, user)
        assert result["buildings"]["wood"] == 2
        assert json.loads(result["seasons"][0]["standings"])[0]["score"] == 50
