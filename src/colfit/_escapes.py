"""Escape sequences (ECMA-48): terminals act on them but never draw them."""

from __future__ import annotations

import re

# ECMA-48 5.4: CSI, parameter bytes, intermediate bytes, final byte. A sequence cut short
# (end of text, or a character outside these ranges) ends where it stops matching.
_CSI = r"(?:\x1b\[|\x9b)[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]?"
# ECMA-48 5.6: control strings end with ST. BEL also ends an OSC, as in xterm. As in the
# DEC terminal parser, an ESC that does not start ST, CAN or SUB cuts a string short there.
_OSC = r"(?:\x1b\]|\x9d)[^\x07\x18\x1a\x1b\x9c]*(?:\x1b\\|\x9c|\x07)?"
_STRING = r"(?:\x1b[PX^_]|[\x90\x98\x9e\x9f])[^\x18\x1a\x1b\x9c]*(?:\x1b\\|\x9c)?"
# ECMA-48 5.3 and 5.5 (and ECMA-35 for intermediates): ESC, intermediates, one final byte.
_OTHER = r"\x1b[\x20-\x2f]*[\x30-\x7e]?"

SEQUENCE = re.compile("|".join((_CSI, _OSC, _STRING, _OTHER)))


def pieces(text: str) -> list[tuple[str, bool]]:
    """Split ``text`` into runs of plain text and single escape sequences, in order.

    Each piece is ``(text, is_escape)``. Plain runs are never empty.
    """
    if "\x1b" not in text and not any("\x90" <= char <= "\x9f" for char in text):
        return [(text, False)] if text else []
    out: list[tuple[str, bool]] = []
    start = 0
    for match in SEQUENCE.finditer(text):
        if match.start() > start:
            out.append((text[start : match.start()], False))
        out.append((match.group(), True))
        start = match.end()
    if start < len(text):
        out.append((text[start:], False))
    return out


def strip(text: str) -> str:
    """``text`` without its escape sequences."""
    return "".join(piece for piece, escape in pieces(text) if not escape)


def is_open(sequence: str) -> bool:
    """Whether an escape sequence at the end of a text would take in what follows it.

    A CSI without its final byte, a control string without its terminator or a lone ESC:
    anything written after it (padding, the next cell) would become part of it.
    """
    found = SEQUENCE.match(sequence + "a")
    return found is not None and found.end() > len(sequence)
