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


# Spacing marks (Mc) that UAX #29 leaves out of SpacingMark, so each starts a cluster.
STANDALONE_SPACING_MARKS = [
    *(0x102B, 0x102C, 0x1038, 0x1062, 0x1063, 0x1064, *range(0x1067, 0x106E), 0x1083),
    *(*range(0x1087, 0x108D), 0x108F, 0x109A, 0x109B, 0x109C),
    *(0x1A61, 0x1A63, 0x1A64, 0xAA7B, 0xAA7D, 0x11720, 0x11721),
]
# A letter of the script of each, by block (code >> 8): Myanmar KA, Tai Tham HIGH KA, Ahom KA.
LETTERS = {0x10: "\u1000", 0x1A: "\u1a20", 0xAA: "\u1000", 0x117: "\U00011700"}
