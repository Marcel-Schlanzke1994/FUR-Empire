"""Fail closed in production; no implicit public demo configuration."""

import base64
import hmac
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse


def secret(name: str) -> str:
    path = os.getenv(name + "_FILE")
    return Path(path).read_text().rstrip("\r\n") if path else os.getenv(name, "")


def boolean_setting(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value not in ("true", "false"):
        raise RuntimeError(f"{name} muss true oder false sein.")
    return value == "true"


@dataclass(frozen=True)
class Settings:
    production: bool
    database: str
    origin: str
    allowed_hosts: list[str]
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_tls: bool
    operator_name: str
    operator_contact: str
    admin_mfa: bool
    beta_mode: bool
    email_verification_required: bool
    webpush_public_key: str
    webpush_private_key_file: str
    webpush_subject: str

    @classmethod
    def load(cls, default_database: str) -> "Settings":
        mode = os.getenv("FUR_ENV", "local")
        if mode not in ("local", "test", "staging", "production"):
            raise RuntimeError("FUR_ENV muss local, test, staging oder production sein.")
        staging = mode == "staging"
        production = mode in ("staging", "production")
        beta_mode = boolean_setting("BETA_MODE", True)
        email_verification_required = boolean_setting(
            "ACCOUNT_EMAIL_VERIFICATION_REQUIRED", not beta_mode
        )
        if beta_mode and email_verification_required:
            raise RuntimeError(
                "BETA_MODE=true kann nicht mit ACCOUNT_EMAIL_VERIFICATION_REQUIRED=true "
                "kombiniert werden."
            )
        database = os.getenv("DATABASE_URL", os.getenv("FUR_DB", default_database))
        if os.getenv("DB_HOST") and not os.getenv("DATABASE_URL"):
            password = secret("DB_PASSWORD")
            if not password:
                raise RuntimeError("DB_PASSWORD muss über einen Secret bereitgestellt werden.")
            database = f"postgresql://{quote(os.getenv('DB_USER','fur'),safe='')}:{quote(password,safe='')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','5432')}/{quote(os.getenv('DB_NAME','fur'),safe='')}"
        origin = os.getenv("PUBLIC_ORIGIN", "http://127.0.0.1:8080").rstrip("/")
        parsed = urlparse(origin)
        smtp_host = os.getenv("SMTP_HOST", "")
        webpush_private_key_file = os.getenv("WEBPUSH_PRIVATE_KEY_FILE", "")
        webpush_private_key_available = bool(
            webpush_private_key_file
            and Path(webpush_private_key_file).is_file()
            and Path(webpush_private_key_file).stat().st_size > 0
        )
        push_fields = (
            os.getenv("WEBPUSH_PUBLIC_KEY", ""),
            webpush_private_key_available,
            os.getenv("WEBPUSH_SUBJECT", ""),
        )
        if any(push_fields) and not all(push_fields):
            raise RuntimeError(
                "WEBPUSH_PUBLIC_KEY, WEBPUSH_PRIVATE_KEY_FILE und WEBPUSH_SUBJECT müssen gemeinsam gesetzt sein."
            )
        if all(push_fields):
            _validate_webpush_key_pair(
                os.getenv("WEBPUSH_PUBLIC_KEY", ""),
                webpush_private_key_file,
                os.getenv("WEBPUSH_SUBJECT", ""),
            )
        operator_name = os.getenv("OPERATOR_NAME", "")
        operator_contact = os.getenv("OPERATOR_CONTACT", "")
        if production:
            missing = []
            if not database.startswith(("postgresql://", "postgres://")):
                missing.append("DATABASE_URL (PostgreSQL)")
            local_stage_origin = staging and parsed.hostname in ("localhost", "127.0.0.1")
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or (parsed.hostname in ("localhost", "127.0.0.1") and not local_stage_origin)
                or parsed.path not in ("", "/")
                or parsed.query
                or parsed.fragment
            ):
                missing.append("PUBLIC_ORIGIN (öffentliche HTTPS-Adresse)")
            for key, value in [
                ("SMTP_HOST", smtp_host),
                ("SMTP_FROM", os.getenv("SMTP_FROM", "")),
                ("OPERATOR_NAME", operator_name),
                ("OPERATOR_CONTACT", operator_contact),
            ]:
                if not value:
                    missing.append(key)
            if missing:
                raise RuntimeError("Produktionskonfiguration unvollständig: " + ", ".join(missing))
            if staging and (
                smtp_host != "mailpit"
                or int(os.getenv("SMTP_PORT", "587")) != 1025
                or os.getenv("SMTP_TLS", "true") != "false"
            ):
                raise RuntimeError(
                    "Staging-E-Mail muss ausschließlich den lokalen Mailpit verwenden."
                )
            if not staging and os.getenv("SMTP_TLS", "true") != "true":
                raise RuntimeError("SMTP_TLS muss im Produktivbetrieb aktiviert bleiben.")
        return cls(
            production,
            database,
            origin,
            (
                [parsed.hostname or "127.0.0.1", "127.0.0.1", "localhost", "testserver"]
                if not production
                else [str(parsed.hostname), "127.0.0.1"]
            ),
            smtp_host,
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER", ""),
            secret("SMTP_PASSWORD"),
            os.getenv("SMTP_FROM", ""),
            os.getenv("SMTP_TLS", "true") == "true",
            operator_name,
            operator_contact,
            production,
            beta_mode,
            email_verification_required,
            os.getenv("WEBPUSH_PUBLIC_KEY", ""),
            webpush_private_key_file,
            os.getenv("WEBPUSH_SUBJECT", ""),
        )


def _validate_webpush_key_pair(public_value: str, private_key_file: str, subject: str) -> None:
    parsed_subject = urlparse(subject)
    if not (
        subject.startswith("mailto:")
        or (
            parsed_subject.scheme == "https"
            and parsed_subject.hostname
            and not parsed_subject.username
        )
    ):
        raise RuntimeError("WEBPUSH_SUBJECT muss mailto: oder eine HTTPS-Adresse sein.")
    try:
        public_bytes = base64.b64decode(
            public_value + "=" * (-len(public_value) % 4), altchars=b"-_", validate=True
        )
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            PublicFormat,
        )
        from py_vapid import Vapid  # type: ignore[import-untyped]

        private = Vapid.from_file(private_key_file)
        private_public_bytes = private.public_key.public_bytes(
            Encoding.X962, PublicFormat.UncompressedPoint
        )
    except Exception as exc:
        raise RuntimeError(
            "VAPID-Schlüsseldatei oder öffentlicher Schlüssel ist ungültig."
        ) from exc
    if (
        len(public_bytes) != 65
        or public_bytes[0] != 4
        or not hmac.compare_digest(public_bytes, private_public_bytes)
    ):
        raise RuntimeError("WEBPUSH_PUBLIC_KEY passt nicht zum privaten VAPID-Schlüssel.")
