"""Shared access to the fetched third-party sources (see sources/MANIFEST.txt)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

SOURCES = Path(__file__).resolve().parent / "sources"


@pytest.fixture
def source() -> Callable[[str], str]:
    """Read a fetched source by name, skipping the test when it has not been fetched."""

    def read(name: str) -> str:
        path = SOURCES / name
        if not path.is_file():
            pytest.skip(f"{name} not fetched; run python scripts/fetch_sources.py")
        return path.read_text(encoding="utf-8")

    return read


def code_points(field: str) -> str:
    """``"0041 0301"`` as the string it names."""
    return "".join(chr(int(code, 16)) for code in field.split())
