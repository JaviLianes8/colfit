"""Argument checks shared by the public functions, with the errors they promise."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ._escapes import is_open, pieces
from ._unicode import grapheme_class, is_spacing_mark

# C0 and C1 controls, and the Unicode line and paragraph separators.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")
# Error messages quote at most this many characters of an argument.
_SHOWN = 40


def shown(value: object) -> str:
    """``repr(value)``, cut short so a huge argument never fills an error message."""
    try:
        text = repr(value)
    except Exception:  # an int past the digit limit, or a repr that fails
        return f"<{type(value).__name__[:_SHOWN]} that cannot be shown>"
    return text if len(text) <= _SHOWN else text[: _SHOWN - 3] + "..."


def _wrong_type(name: str, expected: str, value: object) -> TypeError:
    return TypeError(f"{name} must be {expected}, not {type(value).__name__[:_SHOWN]}")


def text_arg(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise _wrong_type(name, "str", value)
    return value


def int_arg(name: str, value: object, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _wrong_type(name, "int", value)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {shown(value)}")
    return value


def choice_arg(name: str, value: object, options: Sequence[str]) -> str:
    text = text_arg(name, value)
    if text not in options:
        listed = ", ".join(map(repr, options))
        raise ValueError(f"{name} must be one of {listed}, got {shown(text)}")
    return text


def line_arg(name: str, value: object) -> str:
    """A string that is one line, with no control characters outside escape sequences."""
    text = text_arg(name, value)
    found_pieces = pieces(text)
    if found_pieces and found_pieces[-1][1] and is_open(found_pieces[-1][0]):
        raise ValueError(f"{name} ends inside an unfinished escape sequence")
    for piece, escape in found_pieces:
        found = None if escape else _CONTROL.search(piece)
        if found:
            hint = (
                "; expand tabs first (str.expandtabs, or expand in a shell)"
                if found.group() == "\t"
                else ""
            )
            raise ValueError(
                f"{name} must be one line without control characters, found {found.group()!r}{hint}"
            )
    return text


def cell_arg(name: str, value: object) -> str:
    """A `line_arg` whose first visible character does not join the text before it.

    Such a character (a combining accent, a spacing vowel sign, a ZWJ) would join the
    space or cell written before it and change that cluster's width.
    """
    text = line_arg(name, value)
    visible = next((piece for piece, escape in pieces(text) if not escape), "")
    if visible and (grapheme_class(visible[0]) in "EJS" or is_spacing_mark(visible[0])):
        raise ValueError(
            f"{name} must not start with a mark that joins the text before it, found {visible[0]!r}"
        )
    return text
