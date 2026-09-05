"""Point every test at a throwaway VIDFORGE_HOME before the app imports."""

import os
import tempfile
from pathlib import Path

_TMP_HOME = Path(tempfile.mkdtemp(prefix="vidforge-tests-"))
os.environ["VIDFORGE_HOME"] = str(_TMP_HOME)
os.environ.setdefault("VIDFORGE_DEVICE", "cpu")

import pytest  # noqa: E402

from vidforge.config import get_settings  # noqa: E402
from vidforge.service import AppContext  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    """A fresh context (own database and output dir) per test."""
    from vidforge.config import build_settings

    monkeypatch.setenv("VIDFORGE_HOME", str(tmp_path))
    context = AppContext(settings=build_settings())
    yield context
    context.shutdown()
