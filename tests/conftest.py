"""Keep implicit application imports away from persistent databases during pytest."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def pytest_configure(config: pytest.Config) -> None:
    directory = TemporaryDirectory(prefix="fur-pytest-default-")
    config.add_cleanup(directory.cleanup)
    environment = pytest.MonkeyPatch()
    config.add_cleanup(environment.undo)
    environment.delenv("DATABASE_URL", raising=False)
    environment.delenv("DB_HOST", raising=False)
    environment.setenv("FUR_DB", str(Path(directory.name) / "implicit-api.sqlite3"))
    environment.setenv("FUR_ENV", "test")
    environment.setenv("FUR_EMBEDDED_WORKER", "false")
