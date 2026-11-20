"""HTTP interface. Local binding only; game rules live in Game."""

import hashlib
import json
import logging
import os
import re
import secrets
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import (
    game_events,
    live_events,
    orbit_attack,
    orbit_intel,
    orbit_rules,
    orbit_transport,
    ranking_categories,
    web_push,
)
from .config import Settings
from .contracts import Command, CommandOrigin, Payload
from .database import Connection
from .fog import sector_is_known
from .game import REGISTRY, RULES_DIGEST, UNITS, Game, RuleError, identity
from .identity import AccountAction, Accounts, valid_email, verify_totp
from .neutral_market import RULE_HASH as NEUTRAL_MARKET_RULE_HASH
from .neutral_market import RULES as NEUTRAL_MARKET_RULES
from .observability import configure, latency_p95, record_latency
from .terrain import PRODUCTION_PERCENT, travel_times
from .worker import run

ROOT = Path(__file__).resolve().parent.parent
(ROOT / "data").mkdir(exist_ok=True)
settings = Settings.load(str(ROOT / "data" / "empire.sqlite3"))
game = Game(settings.database)
accounts = Accounts(game)
logger = logging.getLogger("fur.api")
configure()
LOGIN_ACCOUNT_NETWORK_LIMIT = 5


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    stop = threading.Event()
    worker = None
    if os.getenv("FUR_EMBEDDED_WORKER", "false" if settings.production else "true") == "true":
        worker = threading.Thread(target=run, args=(game, settings, stop), daemon=True)
        worker.start()
    yield
    stop.set()
    if worker:
        worker.join(timeout=12)


app = FastAPI(title="FUR Empire", version="0.2.0", docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
hasher = PasswordHasher()
dummy_hash = hasher.hash("invalid-user-timing-padding")


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=8, max_length=128)
    email: str = Field(default="", max_length=254)
    code: str = Field(default="", max_length=10)
    recovery_code: str = Field(default="", max_length=32)
    password_confirmation: str | None = Field(default=None, max_length=128)
    terms_accepted: bool = False
    privacy_acknowledged: bool = False
    registration_version: str | None = Field(default=None, max_length=32)
    language: Literal["de", "en", "es", "fr"] = "de"


class BanAppealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=8, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    code: str = Field(default="", max_length=10)
    recovery_code: str = Field(default="", max_length=32)


class PrivateAccountCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: str = Field(min_length=1, max_length=32)
    email: str = Field(default="", max_length=254)
    password: str = Field(default="", max_length=128)
    new_password: str = Field(default="", max_length=128)
    new_name: str = Field(default="", max_length=24)
    code: str = Field(default="", max_length=10)


class BattleSimulation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    target_id: str = Field(min_length=1, max_length=100)
    army: dict[str, int] = Field(min_length=1, max_length=8)


class MovementSimulation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    target_id: str = Field(min_length=1, max_length=100)
    army: dict[str, int] = Field(min_length=1, max_length=21)
    target_kind: Literal["ruin"] | None = None


class EconomySimulationStep(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["build", "research", "train", "trade", "goods_trade", "quest"]
    payload: Payload = Field(default_factory=Payload)


class EconomySimulation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    commands: list[EconomySimulationStep] = Field(min_length=1, max_length=20)


class MissionTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=2, max_length=32)
    mode: Literal["attack", "scout", "transport", "station", "expedition"]
    army: dict[str, int] = Field(min_length=1, max_length=8)
    capture: bool = False


class ProductionTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=2, max_length=32)
    kind: Literal["build", "research", "train"]
    key: str = Field(min_length=1, max_length=100)
    count: int = Field(default=1, ge=1, le=100)


class ProductionTemplateQueue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    token: str = Field(min_length=8, max_length=100)
    origin: CommandOrigin | None = None


class WebPushKey(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    p256dh: str = Field(min_length=1, max_length=128)
    auth: str = Field(min_length=1, max_length=128)


class WebPushSubscription(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    endpoint: str = Field(min_length=1, max_length=2048)
    keys: WebPushKey


def api_error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": message,
        "code": code,
        "request_id": request.state.request_id,
    }
    if request.headers.get("x-fur-i18n") == "1":
        from .i18n import localized_error

        key, translated = localized_error(message, request.headers.get("accept-language", "de"))
        payload["error"] = translated
        if key:
            payload["message_key"] = key
            payload["message_params"] = {}
    return JSONResponse(payload, status_code=status)


@app.middleware("http")
async def security(request: Request, call_next: Any) -> Any:
    started = time.monotonic()
    request_id = identity()
    request.state.request_id = request_id
    origin = request.headers.get("origin")
    expected = settings.origin if settings.production else str(request.base_url).rstrip("/")
    if (
        request.headers.get("content-length", "").isdigit()
        and int(request.headers["content-length"]) > 16384
    ):
        response = api_error(request, 413, "request_too_large", "Anfrage zu groß.")
    elif request.method == "POST" and (
        (origin and origin != expected) or (settings.production and not origin)
    ):
        response = api_error(request, 403, "origin_rejected", "Fremder Ursprung abgelehnt.")
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            if not request.url.path.startswith("/api/"):
                raise
            logger.error("request_failed id=%s type=%s", request_id, type(exc).__name__)
            response = api_error(
                request, 500, "internal_error", "Die Anfrage konnte nicht verarbeitet werden."
            )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Request-ID"] = request_id
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Frame-Options"] = "DENY"
    if settings.production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path in ("/", "/legal", "/static/app.js", "/static/community.js"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if request.url.path.startswith("/api/") and request.url.path not in (
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/admin/operations",
    ):
        record_latency(elapsed_ms)
    logger.info(
        "request id=%s method=%s path=%s status=%s ms=%d",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(RuleError)
async def rules(request: Request, exc: RuleError) -> JSONResponse:
    if isinstance(exc, AuthenticationError):
        return api_error(request, 401, "authentication_required", str(exc))
    if isinstance(exc, SessionProtectionError):
        return api_error(request, 400, "invalid_csrf", str(exc))
    if isinstance(exc, RateLimitError):
        return api_error(request, 400, "rate_limited", str(exc))
    return api_error(request, 400, "rule_rejected", str(exc))


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
    return api_error(request, 422, "invalid_request", "Bitte prüfe die Eingaben.")


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> Any:
    if not request.url.path.startswith("/api/"):
        return await http_exception_handler(request, exc)
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    response = api_error(request, exc.status_code, code, "Die API-Anfrage ist nicht verfügbar.")
    response.headers.update(exc.headers or {})
    return response


class AuthenticationError(RuleError):
    pass


class SessionProtectionError(RuleError):
    pass


class RateLimitError(RuleError):
    pass


def session(request: Request, db: Connection, mutate: bool = False) -> str:
    token = hashlib.sha256(request.cookies.get("fur_session", "").encode()).hexdigest()
    row = db.execute(
        "SELECT * FROM sessions WHERE token=? AND expires>?", (token, int(time.time()))
    ).fetchone()
    if row is None:
        raise AuthenticationError("Bitte melde dich an.")
    profile = game.systems.profile(db, row["user_id"])
    if profile["banned"]:
        raise RuleError("Dieses Konto ist gesperrt.")
    if mutate and not secrets.compare_digest(request.headers.get("x-csrf-token", ""), row["csrf"]):
        raise SessionProtectionError("Ungültiger Sitzungsschutz. Bitte Seite neu laden.")
    game.note_terra_activity(db, row["user_id"], int(time.time()))
    return str(row["user_id"])


def limit(request: Request, bucket: str, maximum: int) -> None:
    address = request.client.host if request.client else "local"
    # Proxy trust is configured at Uvicorn; never read arbitrary forwarded headers here.
    key = hashlib.sha256((address + ":" + bucket).encode()).hexdigest()
    now = int(time.time())
    exceeded = False
    with game.transaction() as db:
        db.execute("DELETE FROM rate_limits WHERE starts<?", (now - 120,))
        row = db.execute("SELECT * FROM rate_limits WHERE bucket=?", (key,)).fetchone()
        if not row or row["starts"] <= now - 60:
            db.execute(
                "INSERT INTO rate_limits VALUES (?,?,1) ON CONFLICT(bucket) DO UPDATE SET starts=excluded.starts,count=1",
                (key, now),
            )
        elif row["count"] >= maximum:
            exceeded = True
        else:
            db.execute("UPDATE rate_limits SET count=count+1 WHERE bucket=?", (key,))
    if exceeded:
        raise RateLimitError("Zu viele Anfragen. Bitte eine Minute warten.")


@app.post("/api/v1/auth/ban-appeal")
def submit_ban_appeal(payload: BanAppealRequest, request: Request) -> JSONResponse:
    """Allow a locked-out account owner to request review without restoring access."""
    limit(request, "ban_appeal", 5)
    name = payload.name.strip()
    if not re.fullmatch(r"[\w -]{3,24}", name):
        raise RuleError("Name oder Passwort stimmt nicht.")
    account_key = hashlib.sha256(name.casefold().encode()).hexdigest()
    limit(request, "ban_appeal_account_" + account_key, LOGIN_ACCOUNT_NETWORK_LIMIT)
    accepted = False
    with game.transaction() as db:
        row = db.execute(
            "SELECT u.id,u.password,p.banned,p.role,p.totp,p.totp_last "
            "FROM users u JOIN profiles p ON p.user_id=u.id "
            "WHERE lower(u.name)=lower(?)",
            (name,),
        ).fetchone()
        stored_hash = str(row["password"]) if row else dummy_hash
        valid: bool
        try:
            valid = hasher.verify(stored_hash, payload.password)
        except VerificationError:
            valid = False
        if row and valid and str(row["role"]) == "player" and bool(row["banned"]):
            user = str(row["id"])
            authenticated = not bool(row["totp"]) and not payload.code and not payload.recovery_code
            if row["totp"]:
                if payload.code and payload.recovery_code:
                    authenticated = False
                elif payload.recovery_code:
                    from .identity import consume_recovery_code

                    authenticated = consume_recovery_code(db, user, payload.recovery_code)
                    if authenticated:
                        game.systems.audit(db, user, "account_recovery_code_used")
                else:
                    try:
                        step = verify_totp(str(row["totp"]), payload.code, int(row["totp_last"]))
                    except RuleError:
                        authenticated = False
                    else:
                        db.execute("UPDATE profiles SET totp_last=? WHERE user_id=?", (step, user))
                        authenticated = True
            if authenticated:
                reason = payload.reason.strip()
                if len(reason) >= 3:
                    now = int(time.time())
                    inserted = db.execute(
                        "INSERT INTO account_ban_appeals(id,user_id,reason,created) "
                        "VALUES (?,?,?,?) ON CONFLICT DO NOTHING RETURNING id",
                        (identity(), user, reason, now),
                    )
                    if inserted.fetchone():
                        # Ban state blocks use, but intentionally does not erase sessions
                        # for an administrative review. Revoke them on appeal submission.
                        db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
                        game.systems.audit(db, user, "account_ban_appeal_submitted")
                    accepted = True
    # Keep account existence and ban state private; valid owners receive the same neutral receipt.
    message = (
        "Dein Einspruch wurde eingereicht oder ist bereits offen. Die Sperre bleibt bis zur Prüfung aktiv."
        if accepted
        else "Antrag nicht möglich. Bitte prüfe deine Zugangsdaten und Sicherheitscodes."
    )
    return JSONResponse({"ok": accepted, "message": message}, status_code=202 if accepted else 400)


@app.post("/api/v1/auth/{mode}")
def auth(mode: str, credentials: Credentials, request: Request) -> JSONResponse:
    if mode not in ("login", "register"):
        raise RuleError("Unbekannte Anmeldung.")
    limit(request, "auth", 20)
    now = time.time()
    name = credentials.name.strip()
    if not re.fullmatch(r"[\w -]{3,24}", name):
        raise RuleError("Name: 3–24 Buchstaben, Zahlen, Leerzeichen oder Bindestriche.")
    if mode == "login":
        account_key = hashlib.sha256(name.casefold().encode()).hexdigest()
        limit(request, "login_account_" + account_key, LOGIN_ACCOUNT_NETWORK_LIMIT)
    with game.transaction() as db:
        row = db.execute("SELECT * FROM users WHERE lower(name)=lower(?)", (name,)).fetchone()
        if mode == "register":
            if not game.systems.flag(db, "registration"):
                raise RuleError("Registrierung ist vorübergehend geschlossen.")
            if settings.production and (
                len(credentials.password) < 12 or not valid_email(credentials.email)
            ):
                raise RuleError(
                    "Für die Registrierung sind eine gültige E-Mail und mindestens 12 Passwortzeichen erforderlich."
                )
            if settings.production or credentials.registration_version is not None:
                from .i18n import catalog

                if credentials.password_confirmation != credentials.password:
                    raise RuleError(catalog("de")["error.password_confirmation"])
                if (
                    not credentials.terms_accepted
                    or not credentials.privacy_acknowledged
                    or credentials.registration_version != "2026-11-20"
                ):
                    raise RuleError(catalog("de")["error.registration_acceptance"])
            if row:
                raise RuleError("Dieser Kommandantenname ist bereits vergeben.")
            user = identity()
            db.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (user, name, hasher.hash(credentials.password)),
            )
            game.create(db, user, name)
            db.execute(
                "INSERT INTO account_preferences(user_id,language) VALUES (?,?)",
                (user, credentials.language),
            )
            if credentials.registration_version is not None:
                db.execute(
                    "INSERT INTO registration_acceptance VALUES (?,?,?,?,?)",
                    (
                        user,
                        credentials.registration_version,
                        credentials.registration_version,
                        int(now),
                        credentials.language,
                    ),
                )
            if credentials.email:
                email = credentials.email.strip().lower()
                if (
                    not valid_email(email)
                    or db.execute(
                        "SELECT 1 FROM profiles WHERE lower(email)=lower(?)", (email,)
                    ).fetchone()
                ):
                    raise RuleError("E-Mail ungültig oder bereits vergeben.")
                db.execute("UPDATE profiles SET email=? WHERE user_id=?", (email, user))
                accounts.send_token(db, user, "verify", email)
        else:
            valid: bool
            try:
                valid = hasher.verify(row["password"] if row else dummy_hash, credentials.password)
            except VerificationError:
                valid = False
            if not row or not valid:
                raise RuleError("Name oder Passwort stimmt nicht.")
            user = row["id"]
            profile = game.systems.profile(db, user)
            if profile["banned"]:
                raise RuleError("Dieses Konto ist gesperrt.")
            if profile["totp"]:
                if credentials.code and credentials.recovery_code:
                    raise RuleError("Verwende entweder Authenticator- oder Recovery-Code.")
                if credentials.recovery_code:
                    from .identity import consume_recovery_code

                    if not consume_recovery_code(db, user, credentials.recovery_code):
                        raise RuleError("Recovery-Code ungültig oder bereits verwendet.")
                    game.systems.audit(db, user, "account_recovery_code_used")
                else:
                    step = verify_totp(profile["totp"], credentials.code, profile["totp_last"])
                    db.execute("UPDATE profiles SET totp_last=? WHERE user_id=?", (step, user))
            elif credentials.recovery_code:
                raise RuleError("Für dieses Konto ist kein Recovery-Code verfügbar.")
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        session_id = secrets.token_urlsafe(18)
        user_agent = "".join(
            character
            for character in request.headers.get("user-agent", "")[:300]
            if character >= " " and character != "\x7f"
        )
        db.execute("DELETE FROM sessions WHERE expires<?", (int(now),))
        db.execute(
            "INSERT INTO sessions(token,user_id,csrf,expires,session_id,created,user_agent) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                hashlib.sha256(raw.encode()).hexdigest(),
                user,
                csrf,
                int(now) + 604800,
                session_id,
                int(now),
                user_agent,
            ),
        )
    response = JSONResponse({"ok": True, "csrf": csrf})
    response.set_cookie(
        "fur_session",
        raw,
        httponly=True,
        samesite="strict",
        secure=settings.production,
        max_age=604800,
    )
    return response


@app.get("/api/v1/state")
def state(request: Request) -> dict[str, Any]:
    with game.transaction() as db:
        user = session(request, db)
        result = game.view(db, user)
        result["quests"] = game.quests(result)
        preference = db.execute(
            "SELECT language FROM account_preferences WHERE user_id=?", (user,)
        ).fetchone()
        result["language"] = preference[0] if preference else None
        token = hashlib.sha256(request.cookies["fur_session"].encode()).hexdigest()
        result["csrf"] = db.execute("SELECT csrf FROM sessions WHERE token=?", (token,)).fetchone()[
            0
        ]
        return result


class LanguagePreference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    language: Literal["de", "en", "es", "fr"]


@app.post("/api/v1/account/language")
def set_account_language(body: LanguagePreference, request: Request) -> dict[str, str]:
    limit(request, "account_language", 30)
    with game.transaction() as db:
        user = session(request, db, True)
        db.execute(
            "INSERT INTO account_preferences(user_id,language) VALUES (?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET language=excluded.language",
            (user, body.language),
        )
    return {"language": body.language}


@app.get("/api/v1/alliance/bulletins")
def older_alliance_bulletins(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "alliance_bulletins", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Die Allianz-Pinnwand erfordert eine aktuelle Mitgliedschaft.")
        entries, has_more = game.systems.alliance_bulletin_page(
            db, str(member["alliance_id"]), before
        )
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/alliance/forum")
def older_alliance_forum(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "alliance_forum", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Das Allianzforum erfordert eine aktuelle Mitgliedschaft.")
        threads, has_more = game.systems.alliance_forum_page(db, str(member["alliance_id"]), before)
        return {"threads": threads, "has_more": has_more}


@app.get("/api/v1/alliance/shared-reports")
def older_alliance_shared_reports(
    request: Request,
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_shared_reports", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Geteilte Kampfberichte erfordern eine aktuelle Allianzmitgliedschaft.")
        entries, has_more = game.systems.alliance_shared_report_page(
            db,
            user,
            str(member["alliance_id"]),
            int(colony["world_id"]),
            before,
        )
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/alliance/forum-reports")
def older_alliance_forum_reports(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "alliance_forum_reports", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Forum-Meldungen erfordern eine aktuelle Allianzmitgliedschaft.")
        moderator = member["role"] in ("leader", "officer")
        entries, has_more = game.systems.alliance_forum_reports_page(
            db, user, str(member["alliance_id"]), moderator, before
        )
        return {"reports": entries, "has_more": has_more}


@app.get("/api/v1/alliances")
def older_alliances(
    request: Request,
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_directory", 60)
    with game.transaction() as db:
        user = session(request, db)
        alliances, has_more = game.systems.alliance_directory_page(db, before, user)
        return {"alliances": alliances, "has_more": has_more}


@app.get("/api/v1/alliance/members")
def older_alliance_members(
    request: Request,
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_members_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Die Mitgliederliste erfordert eine aktuelle Allianzmitgliedschaft.")
        entries, has_more = game.systems.alliance_member_page(
            db, str(member["alliance_id"]), before
        )
        return {"members": entries, "has_more": has_more}


@app.get("/api/v1/alliance/candidates")
def alliance_candidates_page(
    request: Request,
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_candidates_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if not member or member["role"] not in ("leader", "officer"):
            raise RuleError("Einladungskandidaten kann nur die Allianzleitung einsehen.")
        colony = game.read(db, user)
        entries, has_more = game.systems.alliance_candidate_page(
            db,
            user,
            str(member["alliance_id"]),
            int(colony["world_id"]),
            before,
        )
        return {"candidates": entries, "has_more": has_more}


@app.get("/api/v1/alliance/applications")
def alliance_applications_page(
    request: Request,
    direction: Literal["incoming", "outgoing"],
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_applications_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if direction == "incoming":
            if not member or member["role"] not in ("leader", "officer"):
                raise RuleError("Bewerbungen kann nur die Allianzleitung einsehen.")
            entries, has_more = game.systems.alliance_application_page(
                db, user, direction, str(member["alliance_id"]), before
            )
        else:
            entries, has_more = game.systems.alliance_application_page(
                db, user, direction, before_id=before
            )
        return {"applications": entries, "has_more": has_more}


@app.get("/api/v1/alliance/invitations")
def alliance_invitations_page(
    request: Request,
    direction: Literal["incoming", "outgoing"],
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "alliance_invitations_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        member = game.systems.member(db, user)
        if direction == "outgoing":
            if not member or member["role"] not in ("leader", "officer"):
                raise RuleError("Offene Einladungen kann nur die Allianzleitung einsehen.")
            entries, has_more = game.systems.alliance_invitation_page(
                db, user, direction, str(member["alliance_id"]), before
            )
        else:
            entries, has_more = game.systems.alliance_invitation_page(
                db, user, direction, before_id=before
            )
        return {"invitations": entries, "has_more": has_more}


@app.get("/api/v1/messages")
def older_messages(
    request: Request,
    channel: Literal["world", "alliance", "private"],
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "messages_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        member = game.systems.member(db, user)
        messages, has_more = game.systems.message_page(
            db,
            user,
            int(colony["world_id"]),
            str(member["alliance_id"]) if member else "",
            channel,
            before,
        )
        return {"messages": messages, "has_more": has_more}


@app.get("/api/v1/announcements")
def older_announcements(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "system_announcements", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        role_row = db.execute("SELECT role FROM profiles WHERE user_id=?", (user,)).fetchone()
        entries, has_more = game.systems.system_announcement_page(
            db,
            int(colony["world_id"]),
            before,
            include_scheduled=bool(role_row and role_row["role"] in ("admin", "moderator")),
        )
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/system-mail")
def older_system_mail(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "system_mail", 60)
    with game.transaction() as db:
        user = session(request, db)
        entries, has_more = game.systems.system_mail_page(db, user, before)
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/social")
def older_social_contacts(
    request: Request,
    list_name: Literal["friends", "incoming_requests", "outgoing_requests", "blocked"] = Query(
        alias="list"
    ),
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "social_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        entries, has_more = game.systems.social_page(db, user, list_name, before)
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/profiles/{profile_user_id}")
def public_player_profile(request: Request, profile_user_id: str) -> dict[str, Any]:
    limit(request, "public_player_profile", 60)
    with game.transaction() as db:
        viewer = session(request, db)
        current_state = game.read(db, viewer)
        public_profile = game.systems.public_player_profile(
            db, viewer, profile_user_id, int(current_state["world_id"])
        )
        if public_profile is None:
            raise HTTPException(status_code=404, detail="Profil ist privat oder nicht verfügbar.")
        return {"profile": public_profile}


@app.get("/api/v1/notes")
def older_player_notes(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "player_notes_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        entries, has_more = game.systems.notes_page(db, user, int(colony["world_id"]), before)
        return {"notes": entries, "has_more": has_more}


@app.get("/api/v1/ranking")
def older_ranking(
    request: Request,
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "ranking_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        entries, offset, has_more = game.ranking_page(db, int(colony["world_id"]), before)
        return {
            "entries": entries,
            "offset": offset,
            "has_more": has_more,
            "military_entries": game.military_ranking_for_world(db, int(colony["world_id"]))[:50],
            "alliance_military_entries": game.alliance_military_ranking_for_world(
                db, int(colony["world_id"])
            )[:50],
            "categories": ranking_categories.live_rankings(
                db,
                int(colony["world_id"]),
                game.world_regions(db, int(colony["world_id"])),
                game.alliance_military_ranking_for_world(db, int(colony["world_id"])),
            ),
            "my_military_score_audit": game.war_score_audit(db, user, int(colony["world_id"])),
        }


@app.get("/api/v1/market/offers")
def older_market_offers(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "market_offers", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        offers, has_more = game.systems.market_offer_page(
            db, int(colony["world_id"]), int(time.time()), before
        )
        return {"offers": offers, "has_more": has_more}


@app.get("/api/v1/players")
def older_players(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "player_directory_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        world_id = int(colony["world_id"])
        travel = travel_times(db, (int(colony["x"]), int(colony["y"])), world_id)
        entries, has_more = game.systems.player_directory_page(
            db, user, world_id, int(time.time()), travel, before
        )
        return {"players": entries, "has_more": has_more}


class RulePreview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    world_id: int = Field(ge=1)
    terrain: Literal["plain", "forest", "water", "mountain", "pass"]
    resource: Literal["wood", "stone", "ore"]
    production_percent: int = Field(ge=0, le=300)
    unit: Literal["ranger", "sentinel", "mech"]
    unit_power: int = Field(ge=1, le=100000)


@app.post("/api/v1/admin/rule-preview")
def preview_rules(body: RulePreview, request: Request) -> dict[str, Any]:
    limit(request, "rule_preview", 20)
    with game.transaction() as db:
        user = session(request, db, True)
        profile = game.systems.profile(db, user)
        if profile["role"] != "admin" or (settings.admin_mfa and not profile["totp"]):
            raise RuleError("Nur die berechtigte Spielleitung kann Regeln simulieren.")
        colony = game.read(db, user)
        if colony["world_id"] != body.world_id:
            raise RuleError("Diese Welt ist nicht aktiv.")
        index = ("wood", "stone", "ore").index(body.resource)
        base = 2 + 2 * colony["buildings"][body.resource]
        now = int(time.time())
        event_bonus = live_events.active_bonus_total(colony["_events"], now)
        multiplier = (
            100
            + 15 * colony["tech"]["engineering"]
            + 5 * colony["captures"]
            + colony["_region_bonus"]
            + colony["_faction_bonus"]
            + event_bonus
        )
        active_missions = sum(
            job["kind"] not in ("build", "research", "train", "return")
            for row in db.execute("SELECT state FROM colonies WHERE world_id=?", (body.world_id,))
            for job in json.loads(row["state"])["jobs"]
        )
        return {
            "world_id": body.world_id,
            "production_before": base * multiplier * PRODUCTION_PERCENT[body.terrain][index],
            "production_after": base * multiplier * body.production_percent,
            "unit_power_before": REGISTRY["units"][body.unit]["power"],
            "unit_power_after": body.unit_power,
            "pending_terra_missions": active_missions,
        }


@app.get("/api/v1/game-events")
def private_game_events(
    request: Request,
    world_id: int = Query(ge=1, le=2**31 - 1),
    before: int | None = Query(default=None, ge=1, le=2**63 - 1),
    category: Literal["economy", "research", "military", "social", "system"] | None = None,
) -> dict[str, Any]:
    limit(request, "game_event_feed", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        if colony["world_id"] != world_id:
            raise RuleError("Diese Welt ist nicht aktiv.")
        result = game_events.page(db, user, world_id, before, category)
        return {"world_id": world_id, **result}


@app.get("/api/v1/push/config")
def web_push_config() -> dict[str, Any]:
    enabled = bool(
        settings.webpush_public_key
        and settings.webpush_private_key_file
        and settings.webpush_subject
    )
    return {"enabled": enabled, "public_key": settings.webpush_public_key if enabled else ""}


@app.get("/api/v1/push/subscriptions")
def web_push_subscriptions(request: Request) -> dict[str, Any]:
    with game.transaction() as db:
        user = session(request, db)
        rows = db.execute(
            "SELECT id,created,updated,failures FROM web_push_subscriptions "
            "WHERE user_id=? ORDER BY updated DESC,id",
            (user,),
        ).fetchall()
        return {"subscriptions": [dict(row) for row in rows]}


@app.post("/api/v1/push/subscriptions")
def web_push_subscribe(body: WebPushSubscription, request: Request) -> dict[str, Any]:
    if (
        not settings.webpush_public_key
        or not settings.webpush_private_key_file
        or not settings.webpush_subject
    ):
        raise RuleError("Push-Benachrichtigungen sind auf diesem Server nicht aktiviert.")
    limit(request, "web_push_subscribe", 5)
    with game.transaction() as db:
        user = session(request, db, True)
        try:
            result = web_push.subscribe(
                db, user, body.endpoint, body.keys.p256dh, body.keys.auth, int(time.time())
            )
        except ValueError as exc:
            raise RuleError(str(exc)) from exc
        return {"ok": True, **result}


@app.delete("/api/v1/push/subscriptions")
def web_push_unsubscribe(
    request: Request, endpoint: str = Query(min_length=1, max_length=2048)
) -> dict[str, Any]:
    limit(request, "web_push_unsubscribe", 10)
    with game.transaction() as db:
        user = session(request, db, True)
        try:
            removed = web_push.unsubscribe(db, user, endpoint)
        except ValueError as exc:
            raise RuleError(str(exc)) from exc
        return {"ok": True, "removed": removed}


@app.get("/api/v1/orbit/battle-reports")
def orbit_battle_reports(
    request: Request,
    world_id: int = Query(ge=1, le=2**31 - 1),
    colony_id: str = Query(min_length=1, max_length=100),
    before: str | None = Query(default=None, min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "orbit_battle_reports", 60)
    with game.transaction() as db:
        user = session(request, db)
        if game.read(db, user)["world_id"] != world_id:
            raise RuleError("Diese Welt ist nicht aktiv.")
        try:
            orbit_transport.owned_colony(db, user, world_id, colony_id)
            return {
                "world_id": world_id,
                "colony_id": colony_id,
                **orbit_attack.report_page(db, colony_id, before),
            }
        except ValueError as exc:
            raise RuleError(str(exc)) from exc


@app.get("/api/v1/orbit/system")
def orbit_system(
    request: Request,
    world_id: int = Query(ge=1),
    galaxy: int = Query(ge=1, le=orbit_rules.GALAXY_COUNT),
    system: int = Query(ge=1, le=orbit_rules.SYSTEMS_PER_GALAXY),
) -> dict[str, Any]:
    limit(request, "orbit_system", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        if colony["world_id"] != world_id:
            raise RuleError("Diese Welt ist nicht aktiv.")
        world = db.execute(
            "SELECT w.seed FROM world_settings w JOIN orbit_access a ON a.world_id=w.world_id "
            "WHERE w.world_id=? AND a.user_id=? AND a.rule_version=?",
            (world_id, user, orbit_rules.VERSION),
        ).fetchone()
        if not world:
            raise RuleError("Der Orbit-Zugang ist in dieser Welt gesperrt.")
        observations = {}
        for row in db.execute(
            "SELECT slot,occupied,observed_at,intel_level,ships,moon FROM orbit_intel "
            "WHERE observer=? AND world_id=? AND galaxy=? AND system_no=? AND observed_at>?",
            (user, world_id, galaxy, system, int(time.time()) - orbit_intel.INTEL_SECONDS),
        ):
            observation = {
                "intel_level": row["intel_level"],
                "observed_at": row["observed_at"],
                "expires_at": row["observed_at"] + orbit_intel.INTEL_SECONDS,
            }
            if row["intel_level"] > 0:
                observation["occupied"] = bool(row["occupied"])
            if row["intel_level"] == 2 and row["ships"] is not None:
                observation["ships"] = row["ships"]
                observation["moon"] = bool(row["moon"])
            observations[row["slot"]] = observation
        return {
            "world_id": world_id,
            "galaxy": galaxy,
            "system": system,
            "slots": [
                {**slot, **observations.get(slot["slot"], {})}
                for slot in orbit_rules.system_chart(int(world["seed"]), world_id, galaxy, system)
            ],
        }


@app.get("/api/v1/worlds")
def older_worlds(
    request: Request,
    before: int = Query(ge=1),
) -> dict[str, Any]:
    limit(request, "world_directory_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        worlds, has_more = game.systems.world_directory_page(db, user, before)
        return {"worlds": worlds, "has_more": has_more}


@app.get("/api/v1/colonies")
def older_player_colonies(
    request: Request,
    before: str = Query(min_length=1, max_length=100),
) -> dict[str, Any]:
    limit(request, "player_colonies_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colonies, has_more = game.systems.player_colonies_page(db, user, before)
        return {"colonies": colonies, "has_more": has_more}


@app.get("/api/v1/alliance/supply-targets")
def older_alliance_supply_targets(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "alliance_supply_targets", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        member = game.systems.member(db, user)
        if not member:
            raise RuleError("Du gehörst keiner Allianz an.")
        targets, has_more = game.systems.alliance_supply_target_page(
            db,
            user,
            str(member["alliance_id"]),
            int(colony["world_id"]),
            before,
        )
        return {"targets": targets, "has_more": has_more}


@app.get("/api/v1/admin/users")
def older_admin_users(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "admin_users_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        profile = game.systems.profile(db, user)
        if profile["role"] not in ("admin", "moderator"):
            raise RuleError("Keine Berechtigung.")
        users, has_more = game.systems.admin_user_page(db, before)
        return {"users": users, "has_more": has_more}


@app.get("/api/v1/admin/job-failures")
def older_admin_job_failures(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "admin_failures_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        profile = game.systems.profile(db, user)
        if profile["role"] not in ("admin", "moderator"):
            raise RuleError("Keine Berechtigung.")
        failures, has_more = game.systems.admin_failure_page(db, before)
        return {"failures": failures, "has_more": has_more}


@app.get("/api/v1/admin/moderation-cases")
def older_admin_moderation_cases(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "admin_moderation_cases", 60)
    with game.transaction() as db:
        user = session(request, db)
        profile = game.systems.profile(db, user)
        if profile["role"] not in ("admin", "moderator"):
            raise RuleError("Keine Berechtigung.")
        cases, has_more = game.systems.moderation_case_page(db, before)
        return {"cases": cases, "has_more": has_more}


@app.get("/api/v1/admin/audit")
def older_admin_audit(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "admin_audit_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        profile = game.systems.profile(db, user)
        if profile["role"] not in ("admin", "moderator"):
            raise RuleError("Keine Berechtigung.")
        entries, has_more = game.systems.admin_audit_page(db, before)
        return {"entries": entries, "has_more": has_more}


@app.get("/api/v1/diplomacy/events")
def older_diplomacy_events(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "diplomacy_events_page", 60)
    with game.transaction() as db:
        session(request, db)
        events, has_more = game.systems.diplomacy_events_page(db, before)
        return {"events": events, "has_more": has_more}


@app.get("/api/v1/events")
def older_live_events(
    request: Request, before: str = Query(min_length=1, max_length=100)
) -> dict[str, Any]:
    limit(request, "live_events_page", 60)
    with game.transaction() as db:
        user = session(request, db)
        colony = game.read(db, user)
        events, has_more = game.systems.live_event_page(
            db, int(time.time()), before, world_id=int(colony["world_id"])
        )
        return {"events": events, "has_more": has_more, "world_id": colony["world_id"]}


@app.post("/api/v1/command")
def command(body: Command, request: Request) -> dict[str, Any]:
    limit(request, "command", 90)
    with game.transaction() as db:
        user = session(request, db, True)
        profile = game.systems.profile(db, user)
        if settings.production and not profile["verified"]:
            raise RuleError("Bestätige zuerst deine E-Mail-Adresse unter Kontosicherheit.")
        if settings.admin_mfa and body.action.startswith("admin_") and not profile["totp"]:
            raise RuleError("Vor Administrationsaktionen muss der Authenticator eingerichtet sein.")
        result = game.command(
            db,
            user,
            body.action,
            body.payload.model_dump(exclude_unset=True),
            body.token,
            body.origin,
        )
        result["quests"] = game.quests(result)
        return result


@app.post("/api/v1/simulate-battle")
def simulate_battle(body: BattleSimulation, request: Request) -> dict[str, Any]:
    limit(request, "battle_simulation", 60)
    with game.transaction() as db:
        user = session(request, db, True)
        profile = game.systems.profile(db, user)
        if settings.production and not profile["verified"]:
            raise RuleError("Bestätige zuerst deine E-Mail-Adresse unter Kontosicherheit.")
        colony = game.read(db, user)
        result = game.simulate_outpost_battle(db, colony, body.target_id, body.army)
        return {"simulation": result, "deterministic": bool(result.get("deterministic", True))}


@app.post("/api/v1/simulate-movement")
def simulate_movement(body: MovementSimulation, request: Request) -> dict[str, Any]:
    limit(request, "movement_simulation", 60)
    with game.transaction() as db:
        user = session(request, db, True)
        state = game.read(db, user)
        world_id = int(state["world_id"])
        target: dict[str, Any] | None
        if body.target_kind == "ruin":
            if set(body.army) != {"ranger"}:
                raise RuleError("Für die Ruinenerkundung sind verfügbare Ranger erforderlich.")
            target = game.systems.ruin_exploration_target(db, state, body.target_id)
        else:
            target = next(
                (
                    item
                    for item in game.world_outposts(db, world_id)
                    if str(item.get("id")) == body.target_id
                ),
                None,
            )
            if target is None:
                player_target = db.execute(
                    "SELECT x,y FROM colonies WHERE user_id=? AND world_id=? "
                    "ORDER BY is_home DESC LIMIT 1",
                    (body.target_id, world_id),
                ).fetchone()
                if player_target:
                    target = {"x": int(player_target["x"]), "y": int(player_target["y"])}
        if target is None or not sector_is_known(
            db, user, world_id, int(target["x"]), int(target["y"])
        ):
            raise RuleError("Dieses Ziel ist nicht sichtbar oder gehört nicht zu deiner Welt.")
        if (
            any(type(count) is not int or count < 0 for count in body.army.values())
            or not any(body.army.values())
            or any(count > int(state["units"].get(unit, 0)) for unit, count in body.army.items())
        ):
            raise RuleError("Ungültige Truppenauswahl für die Bewegungsprobe.")
        quote = game.movement_quote(
            db,
            (int(state["x"]), int(state["y"])),
            (int(target["x"]), int(target["y"])),
            world_id,
            body.army,
        )
        quote["affordable"] = int(state["resources"][2]) >= int(quote["fuel_ore"])
        return {"movement": quote, "read_only": True}


@app.post("/api/v1/economy/simulate")
def simulate_economy(body: EconomySimulation, request: Request) -> dict[str, Any]:
    """Run a bounded personal economy scenario through live rules, then roll it all back."""
    limit(request, "economy_simulation", 20)
    flow_types = {
        "build": "sink",
        "research": "sink",
        "train": "sink",
        "trade": "conversion",
        "goods_trade": "conversion",
        "quest": "faucet",
    }
    with game.transaction() as db:
        db.execute("SAVEPOINT economy_simulation")
        try:
            user = session(request, db, True)
            profile = game.systems.profile(db, user)
            if settings.production and not profile["verified"]:
                raise RuleError("Bestätige zuerst deine E-Mail-Adresse unter Kontosicherheit.")

            state = game.read(db, user)

            def balances(snapshot: dict[str, Any]) -> dict[str, Any]:
                return {
                    "resources": [int(amount) for amount in snapshot["resources"]],
                    "goods": {
                        str(key): int(amount)
                        for key, amount in sorted(snapshot.get("goods_inventory", {}).items())
                    },
                    "reserve": [int(amount) for amount in snapshot.get("reserve", [0, 0, 0])],
                }

            initial = balances(state)
            steps: list[dict[str, Any]] = []
            for step in body.commands:
                game.command(
                    db,
                    user,
                    step.action,
                    step.payload.model_dump(exclude_unset=True),
                    "eco-sim-" + secrets.token_urlsafe(24),
                )
                state = game.read(db, user)
                steps.append(
                    {
                        "action": step.action,
                        "flow": flow_types[step.action],
                        "balance": balances(state),
                    }
                )
            return {
                "deterministic": False,
                "committed": False,
                "rules_version": str(REGISTRY["version"]),
                "rules_digest": RULES_DIGEST,
                "neutral_market_version": NEUTRAL_MARKET_RULES.version,
                "neutral_market_digest": NEUTRAL_MARKET_RULE_HASH,
                "initial": initial,
                "steps": steps,
                "final": balances(state),
            }
        finally:
            db.execute("ROLLBACK TO SAVEPOINT economy_simulation")
            db.execute("RELEASE SAVEPOINT economy_simulation")


def mission_template_json(row: Any) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "mode": str(row["mode"]),
        "army": json.loads(row["army"]),
        "capture": bool(row["capture"]),
        "created": int(row["created"]),
    }


@app.get("/api/v1/mission-templates")
def mission_templates(request: Request) -> dict[str, Any]:
    limit(request, "mission_templates", 120)
    with game.transaction() as db:
        user = session(request, db)
        rows = db.execute(
            "SELECT id,name,mode,army,capture,created FROM mission_templates "
            "WHERE owner=? ORDER BY created,id",
            (user,),
        ).fetchall()
        return {"templates": [mission_template_json(row) for row in rows]}


@app.post("/api/v1/mission-templates")
def create_mission_template(body: MissionTemplateCreate, request: Request) -> dict[str, Any]:
    limit(request, "mission_templates", 120)
    with game.transaction() as db:
        user = session(request, db, True)
        name = body.name.strip()
        if len(name) < 2 or any(ord(char) < 32 for char in name):
            raise RuleError("Der Vorlagenname muss 2 bis 32 druckbare Zeichen haben.")
        if any(unit not in UNITS for unit in body.army):
            raise RuleError("Die Vorlage enthält einen unbekannten Einheitentyp.")
        if any(
            type(count) is not int or count < 0 or count > 1_000_000 for count in body.army.values()
        ):
            raise RuleError("Die Vorlage enthält eine ungültige Truppenzahl.")
        if sum(body.army.values()) < 1:
            raise RuleError("Eine Vorlage braucht mindestens eine Einheit.")
        if body.capture and body.mode != "attack":
            raise RuleError("Eroberung ist nur für Angriffsprofile verfügbar.")
        if db.execute(
            "SELECT 1 FROM mission_templates WHERE owner=? AND lower(name)=lower(?)",
            (user, name),
        ).fetchone():
            raise RuleError("Dieser Vorlagenname ist bereits vergeben.")
        if (
            db.execute("SELECT count(*) FROM mission_templates WHERE owner=?", (user,)).fetchone()[
                0
            ]
            >= 10
        ):
            raise RuleError("Du kannst höchstens 10 Missionsvorlagen speichern.")
        template_id, created = identity(), int(time.time())
        db.execute(
            "INSERT INTO mission_templates(id,owner,name,mode,army,capture,created) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                template_id,
                user,
                name,
                body.mode,
                json.dumps(body.army, ensure_ascii=False, sort_keys=True),
                body.capture,
                created,
            ),
        )
        row = db.execute(
            "SELECT id,name,mode,army,capture,created FROM mission_templates WHERE id=? AND owner=?",
            (template_id, user),
        ).fetchone()
        return {"template": mission_template_json(row)}


@app.delete("/api/v1/mission-templates/{template_id}")
def delete_mission_template(template_id: str, request: Request) -> dict[str, bool]:
    limit(request, "mission_templates", 120)
    with game.transaction() as db:
        user = session(request, db, True)
        if not db.execute(
            "SELECT 1 FROM mission_templates WHERE id=? AND owner=?", (template_id, user)
        ).fetchone():
            raise RuleError("Missionsvorlage nicht gefunden.")
        db.execute("DELETE FROM mission_templates WHERE id=? AND owner=?", (template_id, user))
        return {"ok": True}


def production_template_json(row: Any) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "kind": str(row["kind"]),
        "key": str(row["item_key"]),
        "count": int(row["count"]),
        "created": int(row["created"]),
    }


@app.get("/api/v1/production-templates")
def production_templates(request: Request) -> dict[str, Any]:
    limit(request, "production_templates", 120)
    with game.transaction() as db:
        user = session(request, db)
        rows = db.execute(
            "SELECT id,name,kind,item_key,count,created FROM production_templates "
            "WHERE owner=? ORDER BY created,id",
            (user,),
        ).fetchall()
        return {"templates": [production_template_json(row) for row in rows]}


@app.post("/api/v1/production-templates")
def create_production_template(body: ProductionTemplateCreate, request: Request) -> dict[str, Any]:
    limit(request, "production_templates", 120)
    with game.transaction() as db:
        user = session(request, db, True)
        name = body.name.strip()
        if len(name) < 2 or any(ord(char) < 32 for char in name):
            raise RuleError("Der Vorlagenname muss 2 bis 32 druckbare Zeichen haben.")
        catalog = {
            "build": REGISTRY["buildings"],
            "research": REGISTRY["tech"],
            "train": UNITS,
        }[body.kind]
        if body.key not in catalog:
            raise RuleError("Unbekannter Produktionsauftrag.")
        if body.kind != "train" and body.count != 1:
            raise RuleError("Bau- und Forschungsvorlagen verwenden immer genau einen Auftrag.")
        if db.execute(
            "SELECT 1 FROM production_templates WHERE owner=? AND lower(name)=lower(?)",
            (user, name),
        ).fetchone():
            raise RuleError("Dieser Vorlagenname ist bereits vergeben.")
        if (
            db.execute(
                "SELECT count(*) FROM production_templates WHERE owner=?", (user,)
            ).fetchone()[0]
            >= 10
        ):
            raise RuleError("Du kannst höchstens 10 Produktionsvorlagen speichern.")
        template_id, created = identity(), int(time.time())
        db.execute(
            "INSERT INTO production_templates(id,owner,name,kind,item_key,count,created) "
            "VALUES (?,?,?,?,?,?,?)",
            (template_id, user, name, body.kind, body.key, body.count, created),
        )
        row = db.execute(
            "SELECT id,name,kind,item_key,count,created FROM production_templates "
            "WHERE id=? AND owner=?",
            (template_id, user),
        ).fetchone()
        return {"template": production_template_json(row)}


@app.delete("/api/v1/production-templates/{template_id}")
def delete_production_template(template_id: str, request: Request) -> dict[str, bool]:
    limit(request, "production_templates", 120)
    with game.transaction() as db:
        user = session(request, db, True)
        if not db.execute(
            "SELECT 1 FROM production_templates WHERE id=? AND owner=?", (template_id, user)
        ).fetchone():
            raise RuleError("Produktionsvorlage nicht gefunden.")
        db.execute("DELETE FROM production_templates WHERE id=? AND owner=?", (template_id, user))
        return {"ok": True}


@app.post("/api/v1/production-templates/{template_id}/queue")
def queue_production_template(
    template_id: str, body: ProductionTemplateQueue, request: Request
) -> dict[str, Any]:
    limit(request, "command", 90)
    with game.transaction() as db:
        user = session(request, db, True)
        profile = game.systems.profile(db, user)
        if settings.production and not profile["verified"]:
            raise RuleError("Bestätige zuerst deine E-Mail-Adresse unter Kontosicherheit.")
        row = db.execute(
            "SELECT kind,item_key,count FROM production_templates WHERE id=? AND owner=?",
            (template_id, user),
        ).fetchone()
        if not row:
            raise RuleError("Produktionsvorlage nicht gefunden.")
        payload: dict[str, str | int] = {"key": str(row["item_key"])}
        if str(row["kind"]) == "train":
            payload["count"] = int(row["count"])
        result = game.command(db, user, str(row["kind"]), payload, body.token, body.origin)
        result["quests"] = game.quests(result)
        return result


@app.post("/api/v1/logout")
def logout(request: Request) -> JSONResponse:
    with game.transaction() as db:
        session(request, db, True)
        token = hashlib.sha256(request.cookies["fur_session"].encode()).hexdigest()
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
    response = JSONResponse({"ok": True})
    response.delete_cookie("fur_session")
    return response


@app.get("/api/v1/account/sessions")
def account_sessions(
    request: Request, before: str | None = Query(default=None, max_length=100)
) -> dict[str, Any]:
    limit(request, "account_sessions", 60)
    with game.transaction() as db:
        user = session(request, db)
        current_token = hashlib.sha256(request.cookies["fur_session"].encode()).hexdigest()
        now = int(time.time())
        cursor_clause = ""
        params: tuple[Any, ...] = (user, now)
        if before is not None:
            cursor = db.execute(
                "SELECT created,session_id FROM sessions WHERE session_id=? AND user_id=?",
                (before, user),
            ).fetchone()
            if not cursor:
                raise RuleError("Sitzungs-Cursor nicht gefunden.")
            cursor_clause = "AND (created<? OR (created=? AND session_id<?)) "
            params = (
                user,
                now,
                int(cursor["created"]),
                int(cursor["created"]),
                str(cursor["session_id"]),
            )
        rows = list(
            db.execute(
                "SELECT session_id,created,expires,user_agent,token FROM sessions "
                "WHERE user_id=? AND expires>? "
                + cursor_clause
                + "ORDER BY created DESC,session_id DESC LIMIT ?",
                (*params, 51),
            )
        )
        return {
            "sessions": [
                {
                    "id": str(row["session_id"]),
                    "created": int(row["created"]),
                    "expires": int(row["expires"]),
                    "user_agent": str(row["user_agent"]),
                    "current": secrets.compare_digest(str(row["token"]), current_token),
                }
                for row in rows[:50]
            ],
            "has_more": len(rows) > 50,
        }


@app.post("/api/v1/account/sessions/revoke-others")
def revoke_other_sessions(request: Request) -> dict[str, int | bool]:
    limit(request, "account_sessions_mutate", 20)
    with game.transaction() as db:
        user = session(request, db, True)
        current_token = hashlib.sha256(request.cookies["fur_session"].encode()).hexdigest()
        count = int(
            db.execute(
                "SELECT count(*) FROM sessions WHERE user_id=? AND token<>?",
                (user, current_token),
            ).fetchone()[0]
        )
        db.execute("DELETE FROM sessions WHERE user_id=? AND token<>?", (user, current_token))
        game.systems.audit(db, user, "sessions_revoke_others", user, count=count)
        return {"ok": True, "revoked": count}


@app.post("/api/v1/account/sessions/revoke-all")
def revoke_all_sessions(request: Request) -> JSONResponse:
    limit(request, "account_sessions_mutate", 20)
    with game.transaction() as db:
        user = session(request, db, True)
        count = int(
            db.execute("SELECT count(*) FROM sessions WHERE user_id=?", (user,)).fetchone()[0]
        )
        game.systems.audit(db, user, "sessions_revoke_all", user, count=count)
        db.execute("DELETE FROM sessions WHERE user_id=?", (user,))
    response = JSONResponse({"ok": True, "revoked": count})
    response.delete_cookie("fur_session")
    return response


@app.post("/api/v1/account/sessions/revoke/{session_id}")
def revoke_session(session_id: str, request: Request) -> JSONResponse:
    limit(request, "account_sessions_mutate", 20)
    with game.transaction() as db:
        user = session(request, db, True)
        row = db.execute(
            "SELECT token FROM sessions WHERE session_id=? AND user_id=?",
            (session_id, user),
        ).fetchone()
        if not row:
            raise RuleError("Sitzung nicht gefunden.")
        current_token = hashlib.sha256(request.cookies["fur_session"].encode()).hexdigest()
        is_current = secrets.compare_digest(str(row["token"]), current_token)
        db.execute("DELETE FROM sessions WHERE session_id=? AND user_id=?", (session_id, user))
        game.systems.audit(db, user, "session_revoke", user, current=is_current)
    response = JSONResponse({"ok": True, "current": is_current})
    if is_current:
        response.delete_cookie("fur_session")
    return response


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    with game.connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok", "service": "fur-empire", "version": "0.2.0"}


@app.get("/api/v1/ready")
def ready() -> JSONResponse:
    with game.connect() as db:
        worker = db.execute("SELECT heartbeat FROM worker_status WHERE id=1").fetchone()
        failures = db.execute("SELECT count(*) FROM job_failures WHERE attempts>=3").fetchone()[0]
        scheduler = db.execute(
            "SELECT sampled_at,lag_seconds FROM scheduler_status WHERE id=1"
        ).fetchone()
    ok = bool(worker and worker[0] > int(time.time()) - 30 and failures == 0)
    return JSONResponse(
        {"ready": ok, "quarantined": failures, "scheduler": dict(scheduler) if scheduler else None},
        status_code=200 if ok else 503,
    )


@app.get("/api/v1/admin/operations")
def operations_status(request: Request) -> dict[str, Any]:
    limit(request, "operations_status", 6)
    with game.transaction() as db:
        user = session(request, db)
        profile = game.systems.profile(db, user)
        if profile["role"] != "admin" or (settings.admin_mfa and not profile["totp"]):
            raise RuleError("Nur die berechtigte Spielleitung kann Betriebsdaten ansehen.")
        now = int(time.time())
        p95, count = latency_p95()
        scheduler = db.execute(
            "SELECT sampled_at,lag_seconds FROM scheduler_status WHERE id=1"
        ).fetchone()
        backup = db.execute("SELECT completed_at FROM backup_status WHERE id=1").fetchone()
        worker = db.execute("SELECT heartbeat FROM worker_status WHERE id=1").fetchone()
        backup_age = max(0, now - backup[0]) if backup else None
        worker_age = max(0, now - worker[0]) if worker else None
        scheduler_lag = scheduler["lag_seconds"] if scheduler else None
        mismatches = db.execute(
            "SELECT COUNT(*) FROM orbit_economy e LEFT JOIN orbit_resource_ledger l "
            "ON l.sequence=(SELECT MAX(r.sequence) FROM orbit_resource_ledger r "
            "WHERE r.colony_id=e.mission_id) WHERE l.sequence IS NULL OR l.ore<>e.ore "
            "OR l.ether<>e.ether OR l.ore_reserve<>e.ore_reserve OR l.ether_reserve<>e.ether_reserve"
        ).fetchone()[0]
        alerts = []
        if count >= 20 and p95 is not None and p95 > 500:
            alerts.append("api_latency")
        if worker_age is None or worker_age >= 30:
            alerts.append("worker_heartbeat")
        if scheduler_lag is not None and scheduler_lag > 30:
            alerts.append("scheduler_lag")
        if backup_age is None or backup_age > 86400:
            alerts.append("backup_age")
        if mismatches:
            alerts.append("orbit_ledger_integrity")
        return {
            "api_p95_ms": p95,
            "api_samples": count,
            "worker_age_seconds": worker_age,
            "scheduler_lag_seconds": scheduler_lag,
            "backup_age_seconds": backup_age,
            "orbit_ledger_mismatches": mismatches,
            "alerts": alerts,
        }


@app.post("/api/v1/account/public")
def public_account(body: AccountAction, request: Request) -> dict[str, Any]:
    limit(request, "recovery", 10)
    with game.transaction() as db:
        return accounts.public(db, body)


@app.post("/api/v1/account/private")
def private_account(body: PrivateAccountCommand, request: Request) -> JSONResponse:
    limit(request, "account", 15)
    with game.transaction() as db:
        result = accounts.private(
            db,
            session(request, db, True),
            AccountAction(**body.model_dump()),
        )
    response = JSONResponse(result)
    if body.action == "export":
        response.headers["Content-Disposition"] = (
            'attachment; filename="fur-empire-account-export.json"'
        )
    if body.action == "password":
        response.delete_cookie("fur_session")
    return response


@app.get("/api/v1/account/local-mail")
def local_mail(request: Request) -> list[dict[str, Any]]:
    if settings.production:
        raise RuleError("Lokale Mailvorschau ist im Produktivbetrieb deaktiviert.")
    with game.transaction() as db:
        user = session(request, db)
        return [
            dict(r)
            for r in db.execute(
                "SELECT subject,body,created FROM outbox WHERE user_id=? ORDER BY created DESC LIMIT 5",
                (user,),
            )
        ]


@app.get("/api/v1/public-config")
def public_config() -> dict[str, Any]:
    return {
        "production": settings.production,
        "operator_name": settings.operator_name,
        "operator_contact": settings.operator_contact,
        "version": "0.2.0",
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/service-worker.js")
def service_worker() -> FileResponse:
    response = FileResponse(
        ROOT / "static" / "service-worker.js", media_type="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get("/legal")
def legal() -> FileResponse:
    return FileResponse(ROOT / "static" / "legal.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
