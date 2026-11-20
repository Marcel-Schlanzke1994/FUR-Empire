"""Shared message catalogs for explicitly localized API clients."""

import json
from functools import lru_cache
from pathlib import Path

LANGUAGES = frozenset({"de", "en", "es", "fr"})


@lru_cache(maxsize=4)
def catalog(language: str) -> dict[str, str]:
    code = language if language in LANGUAGES else "de"
    path = Path(__file__).parent.parent / "static" / "locales" / f"{code}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.items()}


def localized_error(message: str, language_header: str) -> tuple[str | None, str]:
    language = language_header.split(",", 1)[0].split(";", 1)[0].split("-", 1)[0].lower()
    language = language if language in LANGUAGES else "de"
    key = next(
        (
            key
            for key, value in catalog("de").items()
            if key.startswith("error.") and value == message
        ),
        None,
    )
    return key, catalog(language).get(key, message) if key else message
