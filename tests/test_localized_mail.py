import time

from fur_empire.game import Game, identity
from fur_empire.identity import Accounts, digest


def test_security_email_uses_account_language_and_single_use_token(tmp_path):
    game = Game(tmp_path / "localized-mail.sqlite3")
    user = identity()
    with game.transaction() as db:
        db.execute("INSERT INTO users VALUES (?,?,?)", (user, "MailTester", "unused-test-hash"))
        game.create(db, user, "MailTester")
        for language, expected in (
            ("de", "E-Mail bestätigen"),
            ("en", "Verify your email"),
            ("es", "Verifica tu correo"),
            ("fr", "Vérifiez votre e-mail"),
        ):
            db.execute(
                "INSERT INTO account_preferences VALUES (?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET language=excluded.language",
                (user, language),
            )
            Accounts(game).send_token(db, user, "verify", "mail@example.test")
            mail = db.execute("SELECT subject,body FROM outbox ORDER BY created,id").fetchall()
            selected = next(row for row in reversed(mail) if expected in row["subject"])
            token = selected["body"].split("\n\n")[1]
            assert "{token}" not in selected["body"]
            stored = db.execute(
                "SELECT expires FROM auth_tokens WHERE user_id=? AND token=?",
                (user, digest(token)),
            ).fetchone()
            assert stored and int(time.time()) < stored[0] <= int(time.time()) + 1800
            assert (
                db.execute(
                    "SELECT count(*) FROM auth_tokens WHERE user_id=? AND purpose='verify'", (user,)
                ).fetchone()[0]
                == 1
            )
