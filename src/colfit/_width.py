"""Terminal display width of text, aware of wide and zero-width characters."""

from __future__ import annotations

import unicodedata

# Characters that occupy no cells even though they are not combining marks.
_ZERO_WIDTH = frozenset(
    {
        0x200B,  # zero width space
        0x200C,  # zero width non-joiner
        0x200D,  # zero width joiner
        0x2060,  # word joiner
        0xFEFF,  # zero width no-break space
    }
)


def _char_width(char: str) -> int:
    code = ord(char)
    if code == 0 or unicodedata.combining(char):
        return 0
    if code < 0x20 or 0x7F <= code < 0xA0:
        return 0
    if code in _ZERO_WIDTH:
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def display_width(text: str) -> int:
    """Number of terminal cells ``text`` occupies.

    Wide East Asian characters count as two cells, combining and zero-width
    characters as zero, so alignment holds for scripts beyond ASCII.
    """
    return sum(_char_width(char) for char in text)
