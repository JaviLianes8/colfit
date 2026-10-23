"""Character property lookups over the generated Unicode tables."""

from __future__ import annotations

import re
from bisect import bisect_right
from functools import lru_cache

from . import _tables

_RUN = re.compile(r"([0-9a-z]+)([A-Z])([0-9a-z]+) ")
_HANGUL_FIRST = 0xAC00
_HANGUL_LAST = 0xD7A3


class _Runs:
    """Sorted, disjoint code point runs, each with a one letter value."""

    def __init__(self, packed: str) -> None:
        self.starts: list[int] = []
        self.ends: list[int] = []
        self.values: list[str] = []
        after = 0
        for gap, value, span in _RUN.findall(packed):
            first = after + int(gap, 36)
            after = first + int(span, 36) + 1
            self.starts.append(first)
            self.ends.append(after - 1)
            self.values.append(value)

    def get(self, code: int, default: str) -> str:
        index = bisect_right(self.starts, code) - 1
        if index >= 0 and code <= self.ends[index]:
            return self.values[index]
        return default


_GRAPHEME = _Runs(_tables.GRAPHEME)
_CONJUNCT = _Runs(_tables.CONJUNCT)
_WIDTH = _Runs(_tables.WIDTH)
_VARIATION = _Runs(_tables.VARIATION)


@lru_cache(maxsize=4096)
def grapheme_class(char: str) -> str:
    """Grapheme_Cluster_Break letter of ``char``; ``Q`` is Extended_Pictographic, ``.`` Other.

    Hangul syllables are ``H`` (LV) or ``Y`` (LVT), computed from the code point.
    """
    code = ord(char)
    if _HANGUL_FIRST <= code <= _HANGUL_LAST:
        return "H" if (code - _HANGUL_FIRST) % 28 == 0 else "Y"
    return _GRAPHEME.get(code, ".")


def conjunct_class(char: str) -> str:
    """Indic_Conjunct_Break letter: ``K`` Linker, ``O`` Consonant, ``X`` Extend, ``.`` None."""
    return _CONJUNCT.get(ord(char), ".")


@lru_cache(maxsize=4096)
def char_width(char: str) -> int:
    """Columns of one code point on its own: 0, 1 or 2."""
    value = _WIDTH.get(ord(char), ".")
    return 2 if value == "W" else 1 if value == "." else 0


@lru_cache(maxsize=4096)
def is_spacing_mark(char: str) -> bool:
    """Whether ``char`` is a spacing combining mark (General_Category Mc)."""
    return _WIDTH.get(ord(char), ".") == "M"


def has_variations(char: str) -> bool:
    """Whether ``char`` has a text and an emoji presentation sequence."""
    return _VARIATION.get(ord(char), ".") == "B"
