"""Account recovery and TOTP. Secrets are never included in game state."""

import base64
import hashlib
import hmac
import json
import re
import secrets
import struct
import time
from typing import Any

from argon2 import PasswordHasher
from pydantic import BaseModel, ConfigDict, Field

from .database import Connection
from .game import Game, RuleError, identity


class AccountAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    email: str = Field(default="", max_length=254)
    token: str = Field(default="", max_length=200)
    password: str = Field(default="", max_length=128)
    new_password: str = Field(default="", max_length=128)
    new_name: str = Field(default="", max_length=24)
    code: str = Field(default="", max_length=10)


def valid_email(value: str) -> bool:
    import re

    return bool(re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def totp(secret: str, step: int) -> str:
    raw = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8))
    hashed = hmac.new(raw, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = hashed[-1] & 15
    return str((struct.unpack(">I", hashed[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000).zfill(
        6
    )


def verify_totp(secret: str, code: str, last: int = -1) -> int:
    current = int(time.time()) // 30
    for step in (current - 1, current, current + 1):
        if step > last and hmac.compare_digest(totp(secret, step), code):
            return step
    raise RuleError("Ungültiger oder bereits verwendeter Authenticator-Code.")


def replace_recovery_codes(db: Connection, user: str) -> list[str]:
    codes = [secrets.token_hex(10) for _ in range(10)]
    now = int(time.time())
    db.execute("DELETE FROM mfa_recovery_codes WHERE user_id=?", (user,))
    for code in codes:
        db.execute(
            "INSERT INTO mfa_recovery_codes(user_id,code_hash,created) VALUES (?,?,?)",
            (user, digest(code), now),
        )
    return codes


def consume_recovery_code(db: Connection, user: str, code: str) -> bool:
    if not code or len(code) != 20:
        return False
    row = db.execute(
        "SELECT 1 FROM mfa_recovery_codes WHERE user_id=? AND code_hash=?",
        (user, digest(code.lower())),
    ).fetchone()
    if not row:
        return False
    db.execute(
        "DELETE FROM mfa_recovery_codes WHERE user_id=? AND code_hash=?",
        (user, digest(code.lower())),
    )
    return True


class Accounts:
    def __init__(self, game: Game):
        self.game = game

    def export(self, db: Connection, user: str) -> dict[str, Any]:
        account = db.execute("SELECT id,name FROM users WHERE id=?", (user,)).fetchone()
        profile = db.execute(
            "SELECT email,verified,joined,faction,role,totp,active_world_id,active_colony_id "
            "FROM profiles WHERE user_id=?",
            (user,),
        ).fetchone()
        if account is None or profile is None:
            raise RuleError("Kontodaten nicht gefunden.")

        colonies = []
        for row in db.execute(
            "SELECT colony_id,world_id,is_home,x,y,state FROM colonies "
            "WHERE user_id=? ORDER BY world_id,is_home DESC,colony_id",
            (user,),
        ):
            state = json.loads(row["state"])
            colonies.append(
                {
                    "colony_id": row["colony_id"],
                    "world_id": int(row["world_id"]),
                    "home": bool(row["is_home"]),
                    "name": str(state.get("colony_name", state.get("name", ""))),
                    "coordinates": {"x": int(row["x"]), "y": int(row["y"])},
                    "resources": list(state.get("resources", [])),
                    "goods_inventory": dict(state.get("goods_inventory", {})),
                    "goods_reserve": dict(state.get("goods_reserve", {})),
                    "goods_inbound": dict(state.get("goods_inbound", {})),
                    "item_inventory": dict(state.get("item_inventory", {})),
                    "item_reserve": dict(state.get("item_reserve", {})),
                    "item_inbound": dict(state.get("item_inbound", {})),
                    "buildings": dict(state.get("buildings", {})),
                    "technologies": dict(state.get("tech", {})),
                    "units": dict(state.get("units", {})),
                    "captures": int(state.get("captures", 0)),
                }
            )

        sessions = [
            {
                "created": int(row["created"]),
                "expires": int(row["expires"]),
                "user_agent": str(row["user_agent"]),
            }
            for row in db.execute(
                "SELECT created,expires,user_agent FROM sessions "
                "WHERE user_id=? AND expires>? ORDER BY created",
                (user, int(time.time())),
            )
        ]
        templates = [
            {
                "name": str(row["name"]),
                "mode": str(row["mode"]),
                "army": json.loads(row["army"]),
                "capture": bool(row["capture"]),
                "created": int(row["created"]),
            }
            for row in db.execute(
                "SELECT name,mode,army,capture,created FROM mission_templates "
                "WHERE owner=? ORDER BY created,id",
                (user,),
            )
        ]
        production_templates = [
            {
                "name": str(row["name"]),
                "kind": str(row["kind"]),
                "key": str(row["item_key"]),
                "count": int(row["count"]),
                "created": int(row["created"]),
            }
            for row in db.execute(
                "SELECT name,kind,item_key,count,created FROM production_templates "
                "WHERE owner=? ORDER BY created,id",
                (user,),
            )
        ]
        social = {
            "friends": [
                {"name": str(row["name"]), "created": int(row["created"])}
                for row in db.execute(
                    "SELECT u.name,f.created FROM friendships f "
                    "JOIN users u ON u.id=CASE WHEN f.a=? THEN f.b ELSE f.a END "
                    "WHERE (f.a=? OR f.b=?) AND f.status='accepted' ORDER BY lower(u.name),u.id",
                    (user, user, user),
                )
            ],
            "incoming_requests": [
                {"name": str(row["name"]), "created": int(row["created"])}
                for row in db.execute(
                    "SELECT u.name,f.created FROM friendships f JOIN users u ON u.id=f.requested_by "
                    "WHERE (f.a=? OR f.b=?) AND f.status='pending' AND f.requested_by<>? "
                    "ORDER BY f.created,u.id",
                    (user, user, user),
                )
            ],
            "outgoing_requests": [
                {"name": str(row["name"]), "created": int(row["created"])}
                for row in db.execute(
                    "SELECT u.name,f.created FROM friendships f "
                    "JOIN users u ON u.id=CASE WHEN f.a=? THEN f.b ELSE f.a END "
                    "WHERE f.requested_by=? AND f.status='pending' ORDER BY f.created,u.id",
                    (user, user),
                )
            ],
            "blocked": [
                {"name": str(row["name"]), "created": int(row["created"])}
                for row in db.execute(
                    "SELECT u.name,b.created FROM player_blocks b JOIN users u ON u.id=b.blocked "
                    "WHERE b.blocker=? ORDER BY lower(u.name),u.id",
                    (user,),
                )
            ],
        }
        notes = [
            {
                "world_id": int(row["world_id"]),
                "target_kind": str(row["target_kind"]),
                "x": int(row["sector_x"]) if row["sector_x"] is not None else None,
                "y": int(row["sector_y"]) if row["sector_y"] is not None else None,
                "report_id": str(row["report_id"]) if row["report_id"] is not None else None,
                "body": str(row["body"]),
                "created": int(row["created"]),
                "updated": int(row["updated"]),
            }
            for row in db.execute(
                "SELECT world_id,target_kind,sector_x,sector_y,report_id,body,created,updated "
                "FROM player_notes WHERE owner=? ORDER BY world_id,updated,id",
                (user,),
            )
        ]
        bookmarks = [
            {"target_id": str(row["target_id"]), "created": int(row["created"])}
            for row in db.execute(
                "SELECT target_id,created FROM map_bookmarks WHERE user_id=? ORDER BY created,target_id",
                (user,),
            )
        ]
        return {
            "format": "fur-empire-account-export",
            "version": 1,
            "exported_at": int(time.time()),
            "account": {
                "id": str(account["id"]),
                "name": str(account["name"]),
                "email": profile["email"],
                "email_verified": bool(profile["verified"]),
                "joined": int(profile["joined"]),
                "faction": next(
                    (
                        row["faction"]
                        for row in db.execute(
                            "SELECT faction FROM world_players WHERE user_id=? AND world_id=?",
                            (user, profile["active_world_id"]),
                        )
                        if row["faction"]
                    ),
                    "pioneers",
                ),
                "role": str(profile["role"]),
                "mfa_enabled": profile["totp"] is not None,
                "active_world_id": profile["active_world_id"],
                "active_colony_id": profile["active_colony_id"],
            },
            "world_memberships": [
                {"world_id": int(row["world_id"]), "faction": row["faction"]}
                for row in db.execute(
                    "SELECT world_id,faction FROM world_players WHERE user_id=? ORDER BY world_id",
                    (user,),
                )
            ],
            "colonies": colonies,
            "active_sessions": sessions,
            "mission_templates": templates,
            "production_templates": production_templates,
            "social": social,
            "notes": notes,
            "map_bookmarks": bookmarks,
            "excluded": [
                "password and authenticator secrets, recovery codes, and session tokens",
                "messages and other communications containing third-party content",
                "other players' data, network identifiers, moderation and anti-abuse records",
            ],
        }

    def send_token(self, db: Connection, user: str, purpose: str, email: str) -> None:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        db.execute("DELETE FROM auth_tokens WHERE user_id=? AND purpose=?", (user, purpose))
        db.execute(
            "INSERT INTO auth_tokens VALUES (?,?,?,?)", (digest(token), user, purpose, now + 1800)
        )
        from .i18n import catalog

        preference = db.execute(
            "SELECT language FROM account_preferences WHERE user_id=?", (user,)
        ).fetchone()
        messages = catalog(str(preference[0]) if preference else "de")
        message_kind = "verify" if purpose == "verify" else "reset"
        subject = messages[f"mail.{message_kind}.subject"]
        body = messages[f"mail.{message_kind}.body"].format(token=token)
        db.execute(
            "INSERT INTO outbox VALUES (?,?,?,?,?,'pending',0,?)",
            (identity(), user, email, subject, body, now),
        )

    def public(self, db: Connection, p: AccountAction) -> dict[str, Any]:
        now = int(time.time())
        # Expired hashes are no longer usable and should not accumulate indefinitely.
        db.execute("DELETE FROM auth_tokens WHERE expires<=?", (now,))
        if p.action == "request_reset":
            row = db.execute(
                "SELECT user_id,email FROM profiles WHERE lower(email)=lower(?) AND verified=1",
                (p.email.strip(),),
            ).fetchone()
            if row:
                self.send_token(db, row[0], "reset", row[1])
            return {
                "ok": True,
                "message": "Falls ein bestätigtes Konto existiert, wird ein Wiederherstellungscode zugestellt.",
            }
        if p.action not in ("reset", "verify"):
            raise RuleError("Unbekannte Kontoaktion.")
        row = db.execute(
            "SELECT * FROM auth_tokens WHERE token=? AND purpose=? AND expires>?",
            (digest(p.token), p.action, now),
        ).fetchone()
        if not row:
            raise RuleError("Der Code ist ungültig, verbraucht oder abgelaufen.")
        user = row["user_id"]
        if p.action == "reset":
            if len(p.password) < 12:
                raise RuleError("Neues Passwort: mindestens 12 Zeichen.")
            profile = self.game.systems.profile(db, user)
            if profile["totp"]:
                step = verify_totp(profile["totp"], p.code, profile["totp_last"])
                db.execute("UPDATE profiles SET totp_last=? WHERE user_id=?", (step, user))
            db.execute(
                "UPDATE users SET password=? WHERE id=?", (PasswordHasher().hash(p.password), user)
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
        else:
            db.execute("UPDATE profiles SET verified=1 WHERE user_id=?", (user,))
        db.execute("DELETE FROM auth_tokens WHERE token=?", (digest(p.token),))
        self.game.systems.audit(db, user, "account_" + p.action)
        return {"ok": True}

    def private(self, db: Connection, user: str, p: AccountAction) -> dict[str, Any]:
        profile = self.game.systems.profile(db, user)
        if p.action == "export":
            self.reauthenticate(db, user, p, profile)
            result = self.export(db, user)
            self.game.systems.audit(db, user, "account_export")
            return result
        if p.action == "rename":
            new_name = p.new_name.strip()
            if not 3 <= len(new_name) <= 24 or not re.fullmatch(r"[\w -]{3,24}", new_name):
                raise RuleError("Name: 3–24 Buchstaben, Zahlen, Leerzeichen oder Bindestriche.")
            if new_name == self.game.read(db, user)["name"]:
                raise RuleError("Das ist bereits dein Kommandantenname.")
            now = int(time.time())
            last_change = int(profile.get("name_changed", 0))
            if last_change and now < last_change + 86400:
                raise RuleError("Der Kommandantenname kann nur alle 24 Stunden geändert werden.")
            collision = db.execute(
                "SELECT id FROM users WHERE lower(name)=lower(?) AND id<>?", (new_name, user)
            ).fetchone()
            if collision:
                raise RuleError("Dieser Kommandantenname ist bereits vergeben.")
            self.reauthenticate(db, user, p, profile)
            old_name = str(db.execute("SELECT name FROM users WHERE id=?", (user,)).fetchone()[0])
            db.execute("UPDATE users SET name=? WHERE id=?", (new_name, user))
            for row in db.execute(
                "SELECT colony_id,state FROM colonies WHERE user_id=?", (user,)
            ).fetchall():
                colony = json.loads(row["state"])
                colony["name"] = new_name
                db.execute(
                    "UPDATE colonies SET state=? WHERE user_id=? AND colony_id=?",
                    (json.dumps(colony), user, row["colony_id"]),
                )
            db.execute("UPDATE profiles SET name_changed=? WHERE user_id=?", (now, user))
            self.game.systems.audit(
                db, user, "account_rename", user, old_name=old_name, new_name=new_name
            )
            return {"ok": True}
        if p.action == "email":
            email = p.email.strip().lower()
            if not valid_email(email):
                raise RuleError("Bitte eine gültige E-Mail-Adresse eingeben.")
            other = db.execute(
                "SELECT user_id FROM profiles WHERE lower(email)=lower(?)", (email,)
            ).fetchone()
            if other and other[0] != user:
                raise RuleError("Diese E-Mail-Adresse ist nicht verfügbar.")
            # Require password and existing MFA to protect a recovery destination.
            self.reauthenticate(db, user, p, profile)
            db.execute("UPDATE profiles SET email=?,verified=0 WHERE user_id=?", (email, user))
            self.send_token(db, user, "verify", email)
        elif p.action == "verification_resend":
            if not profile["email"]:
                raise RuleError("Hinterlege zuerst eine E-Mail-Adresse.")
            self.send_token(db, user, "verify", profile["email"])
        elif p.action == "password":
            if not 8 <= len(p.new_password) <= 128:
                raise RuleError("Das neue Passwort muss 8 bis 128 Zeichen enthalten.")
            self.reauthenticate(db, user, p, profile)
            db.execute(
                "UPDATE users SET password=? WHERE id=?",
                (PasswordHasher().hash(p.new_password), user),
            )
            db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
        elif p.action == "mfa_begin":
            if profile["totp"]:
                raise RuleError("Authenticator ist bereits eingerichtet.")
            self.reauthenticate(db, user, p, profile)
            secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
            # A short-lived setup challenge never enables MFA until a correct code is supplied.
            db.execute("DELETE FROM flags WHERE name=?", ("mfa_pending_" + user,))
            db.execute(
                "INSERT INTO flags VALUES (?,?)",
                (
                    "mfa_pending_" + user,
                    json.dumps({"secret": secret, "expires": int(time.time()) + 600}),
                ),
            )
            return {"ok": True, "secret": secret}
        elif p.action == "mfa_confirm":
            row = db.execute(
                "SELECT value FROM flags WHERE name=?", ("mfa_pending_" + user,)
            ).fetchone()
            setup = json.loads(row[0]) if row else {}
            if setup.get("expires", 0) < int(time.time()) or profile["totp"]:
                raise RuleError("Einrichtung abgelaufen oder bereits abgeschlossen.")
            step = verify_totp(setup["secret"], p.code)
            db.execute(
                "UPDATE profiles SET totp=?,totp_last=? WHERE user_id=?",
                (setup["secret"], step, user),
            )
            db.execute("DELETE FROM flags WHERE name=?", ("mfa_pending_" + user,))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
            recovery_codes = replace_recovery_codes(db, user)
        elif p.action == "mfa_disable":
            if profile["role"] == "admin":
                raise RuleError("Administratorkonten benötigen einen Authenticator.")
            self.reauthenticate(db, user, p, profile)
            db.execute("UPDATE profiles SET totp=NULL,totp_last=-1 WHERE user_id=?", (user,))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
            db.execute("DELETE FROM mfa_recovery_codes WHERE user_id=?", (user,))
        elif p.action == "recovery_codes_regenerate":
            if not profile["totp"]:
                raise RuleError("Aktiviere zuerst den Authenticator.")
            self.reauthenticate(db, user, p, profile)
            recovery_codes = replace_recovery_codes(db, user)
        else:
            raise RuleError("Unbekannte Kontoaktion.")
        self.game.systems.audit(db, user, "account_" + p.action)
        return {
            "ok": True,
            **(
                {"recovery_codes": recovery_codes}
                if p.action in ("mfa_confirm", "recovery_codes_regenerate")
                else {}
            ),
        }

    def reauthenticate(
        self, db: Connection, user: str, p: AccountAction, profile: dict[str, Any]
    ) -> None:
        from argon2.exceptions import VerificationError

        row = db.execute("SELECT password FROM users WHERE id=?", (user,)).fetchone()
        try:
            PasswordHasher().verify(row[0], p.password)
        except VerificationError:
            raise RuleError("Passwort stimmt nicht.") from None
        if profile["totp"]:
            step = verify_totp(profile["totp"], p.code, profile["totp_last"])
            db.execute("UPDATE profiles SET totp_last=? WHERE user_id=?", (step, user))
