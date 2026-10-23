"""Cut, pad and fit one line of text to a number of terminal columns."""

from __future__ import annotations

from typing import Literal

from ._check import choice_arg, int_arg, line_arg, shown
from ._width import Unit, units, width_of

Align = Literal["left", "center", "right"]
Side = Literal["end", "start", "middle"]

_ALIGNS = ("left", "center", "right")
_SIDES = ("end", "start", "middle")
ELLIPSIS = "\u2026"


def take(line: list[Unit], budget: int) -> int:
    """How many leading units fit ``budget`` columns; escape sequences ride along free."""
    used = 0
    for index, (_, width, _) in enumerate(line):
        if used + width > budget:
            return index
        used += width
    return len(line)


def _joined(line: list[Unit]) -> str:
    return "".join(unit[0] for unit in line)


def _escapes(line: list[Unit]) -> str:
    return "".join(unit[0] for unit in line if unit[2])


def cut(line: list[Unit], width: int, mark: str, side: str) -> str:
    """Replace part of ``line`` with ``mark`` so the result fits ``width`` columns.

    The removed part becomes ``mark`` followed by the escape sequences it held.
    """
    marks = units(mark)
    budget = width - width_of(mark)
    if budget < 0:
        kept = take(marks, width)
        mark, budget = _joined(marks[:kept]) + _escapes(marks[kept:]), 0
    if side == "end":
        head, tail = take(line, budget), len(line)
    elif side == "start":
        head, tail = 0, len(line) - take(line[::-1], budget)
    else:
        head = take(line, (budget + 1) // 2)
        used = sum(unit[1] for unit in line[:head])
        tail = len(line) - take(line[head:][::-1], budget - used)
    return _joined(line[:head]) + mark + _escapes(line[head:tail]) + _joined(line[tail:])


def truncate(text: str, width: int, *, ellipsis: str = ELLIPSIS, side: Side = "end") -> str:
    r"""Cut ``text`` to at most ``width`` columns, marking the cut with ``ellipsis``.

    Text that fits is returned unchanged. ``side`` is where the cut goes: ``"end"``,
    ``"start"`` or ``"middle"`` (the start keeps the larger half). Grapheme clusters are
    never split, so the result can be one column short of ``width`` next to a wide
    character. Escape sequences of the removed text are kept right after the ellipsis.
    An ellipsis wider than ``width`` is itself cut.

    >>> truncate("The quick brown fox", 12, ellipsis="...")
    'The quick...'
    >>> truncate("The quick brown fox", 12, ellipsis="...", side="middle")
    'The q... fox'
    >>> truncate("The quick brown fox", 12) == "The quick b\u2026"
    True
    >>> truncate("short", 12)
    'short'

    Raises ``TypeError`` for arguments of the wrong type and ``ValueError`` for a
    negative ``width``, an unknown ``side``, or ``text`` or ``ellipsis`` holding a line
    break or another control character outside an escape sequence.
    """
    line_arg("text", text)
    int_arg("width", width, 0)
    line_arg("ellipsis", ellipsis)
    choice_arg("side", side, _SIDES)
    line = units(text)
    if sum(unit[1] for unit in line) <= width:
        return text
    return cut(line, width, ellipsis, side)


def _fill_arg(fill: object) -> str:
    text = line_arg("fill", fill)
    found = units(text)
    if len(found) != 1 or found[0][1] != 1:
        raise ValueError(f"fill must be one character one column wide, got {shown(fill)}")
    return text


def pad(text: str, width: int, *, align: Align = "left", fill: str = " ") -> str:
    r"""Pad ``text`` with ``fill`` to ``width`` columns; wider text is returned unchanged.

    ``align`` places the text ``"left"``, ``"right"`` or ``"center"``; when centring
    leaves an odd column over, it goes on the right.

    >>> pad("ok", 6, align="center")
    '  ok  '
    >>> pad("ok", 5, align="center", fill=".")
    '.ok..'
    >>> pad("\u65e5", 4, fill=".") == "\u65e5.."
    True

    Raises ``TypeError`` for arguments of the wrong type and ``ValueError`` for a
    negative ``width``, an unknown ``align``, a ``fill`` that is not one character one
    column wide, or ``text`` holding a control character outside an escape sequence.
    """
    line_arg("text", text)
    int_arg("width", width, 0)
    choice_arg("align", align, _ALIGNS)
    fill = _fill_arg(fill)
    spare = width - width_of(text)
    if spare <= 0:
        return text
    left = 0 if align == "left" else spare if align == "right" else spare // 2
    return fill * left + text + fill * (spare - left)


def fit(
    text: str,
    width: int,
    *,
    align: Align = "left",
    ellipsis: str = ELLIPSIS,
    side: Side = "end",
    fill: str = " ",
) -> str:
    """Return ``text`` in exactly ``width`` columns: cut as `truncate`, then padded as `pad`.

    >>> fit("The quick brown fox", 8, ellipsis="...")
    'The q...'
    >>> fit("ok", 5, align="right")
    '   ok'

    Raises what `truncate` and `pad` raise.
    """
    return pad(truncate(text, width, ellipsis=ellipsis, side=side), width, align=align, fill=fill)
