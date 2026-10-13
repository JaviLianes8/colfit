"""Argument checks shared by the public functions, with the errors they promise."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ._escapes import pieces

# C0 and C1 controls, and the Unicode line and paragraph separators.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")


def text_arg(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, not {type(value).__name__}")
    return value


def int_arg(name: str, value: object, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, not {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    return value


def choice_arg(name: str, value: object, options: Sequence[str]) -> str:
    if value not in options:
        raise ValueError(f"{name} must be one of {', '.join(map(repr, options))}, got {value!r}")
    return str(value)


def line_arg(name: str, value: object) -> str:
    """A string that is one line, with no control characters outside escape sequences."""
    text = text_arg(name, value)
    for piece, escape in pieces(text):
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
