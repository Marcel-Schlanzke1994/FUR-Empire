"""Exercise a disposable private staging player lifecycle over HTTPS."""

from __future__ import annotations

import http.cookiejar
import ipaddress
import json
import os
import ssl
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPCookieProcessor,
    HTTPSHandler,
    Request,
    build_opener,
)


def main() -> int:
    base_url = os.environ.get("FUR_STAGING_URL", "https://localhost:8443").rstrip("/")
    name = os.environ.get("FUR_STAGING_DEMO_NAME", "").strip()
    password = os.environ.get("FUR_STAGING_DEMO_PASSWORD", "")
    if not name or not password:
        print("Set FUR_STAGING_DEMO_NAME and FUR_STAGING_DEMO_PASSWORD.", file=sys.stderr)
        return 2
    parsed_url = urlsplit(base_url)
    try:
        loopback = (
            parsed_url.hostname == "localhost"
            or ipaddress.ip_address(parsed_url.hostname or "").is_loopback
        )
    except ValueError:
        loopback = False
    if parsed_url.scheme != "https" or not loopback or parsed_url.username or parsed_url.password:
        print("The staging smoke only permits HTTPS on a loopback host.", file=sys.stderr)
        return 2

    cookies = http.cookiejar.CookieJar()
    tls = ssl._create_unverified_context()
    opener = build_opener(HTTPCookieProcessor(cookies), HTTPSHandler(context=tls))

    def request(
        path: str, method: str = "GET", body: object = None, csrf: str = ""
    ) -> dict[str, object]:
        headers = {"Accept": "application/json", "Origin": base_url, "Referer": f"{base_url}/"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if csrf:
            headers["X-CSRF-Token"] = csrf
        response = opener.open(
            Request(f"{base_url}{path}", data=data, headers=headers, method=method), timeout=15
        )
        if response.status != 200:
            raise RuntimeError(f"{path} returned HTTP {response.status}")
        result = json.loads(response.read())
        if not isinstance(result, dict):
            raise TypeError(f"{path} returned a non-object response")
        return result

    try:
        health = request("/api/v1/health")
        ready = request("/api/v1/ready")
        assert health.get("status") == "ok", "health check failed"
        assert ready.get("ready") is True, "worker readiness check failed"

        login = request("/api/v1/auth/login", "POST", {"name": name, "password": password})
        csrf = login.get("csrf")
        assert login.get("ok") is True and isinstance(csrf, str) and csrf, "login/CSRF setup failed"
        assert any(
            cookie.name == "fur_session" and cookie.secure for cookie in cookies
        ), "secure session cookie was not set"

        state = request("/api/v1/state")
        assert (
            state.get("csrf") == csrf and state.get("name") == name
        ), "authenticated player state did not match the login"
        updated = request(
            "/api/v1/command",
            "POST",
            {"action": "build", "payload": {"key": "wood"}, "token": str(uuid.uuid4())},
            csrf,
        )
        assert updated.get("name") == name, "authenticated game command returned unexpected state"
    except (AssertionError, HTTPError, URLError, TypeError, ValueError) as exc:
        print(f"Staging smoke failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Staging API smoke passed: health, readiness, secure login, session/CSRF, state, build command."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
