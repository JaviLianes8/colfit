"""Shared access to the fetched third-party sources (see sources/MANIFEST.txt)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest

SOURCES = Path(__file__).resolve().parent / "sources"


def _manifest() -> dict[str, str]:
    """sha256 of each fetched source, by name, as the tracked manifest records it."""
    lines = (SOURCES / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    return {line.split()[2]: line.split()[0] for line in lines if line and line[0] != "#"}


@pytest.fixture
def source() -> Callable[[str], str]:
    """Read a fetched source by name, skipping the test when it has not been fetched."""

    def read(name: str) -> str:
        path = SOURCES / name
        if not path.is_file():
            pytest.skip(f"{name} not fetched; run python scripts/fetch_sources.py")
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == _manifest()[name], f"{name} was changed"
        return data.decode("utf-8")

    return read


def code_points(field: str) -> str:
    """``"0041 0301"`` as the string it names."""
    return "".join(chr(int(code, 16)) for code in field.split())
