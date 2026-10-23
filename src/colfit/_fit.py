"""Cut, pad and fit one line of text to a number of terminal columns."""

from __future__ import annotations

import sys
from typing import Literal

from ._check import choice_arg, int_arg, line_arg, shown
from ._cut import cut
from ._unicode import grapheme_class
from ._width import units, width_of

Align = Literal["left", "center", "right"]
Side = Literal["end", "start", "middle"]

_ALIGNS = ("left", "center", "right")
_SIDES = ("end", "start", "middle")
ELLIPSIS = "\u2026"


def _plain(text: str) -> bool:
    return text.isascii() and text.isprintable()


def _sliced(text: str, width: int, mark: str, side: str) -> str:
    """`truncate` for printable ASCII, where every character is one column."""
    mark = mark[:width]
    budget = width - len(mark)
    if side == "end":
        return text[:budget] + mark
    if side == "start":
        return mark + text[len(text) - budget :]
    head = (budget + 1) // 2
    return text[:head] + mark + text[len(text) - (budget - head) :]


def truncate(text: str, width: int, *, ellipsis: str = ELLIPSIS, side: Side = "end") -> str:
    r"""Cut ``text`` to at most ``width`` columns, marking the cut with ``ellipsis``.

    Text that fits is returned unchanged. ``side`` is where the cut goes: ``"end"``,
    ``"start"`` or ``"middle"`` (the start keeps the larger half). Grapheme clusters are
    never split, so the result can be short of ``width`` by less than the width of the
    cluster that did not fit. Escape sequences of the removed text are kept right after
    the ellipsis. An ellipsis wider than ``width`` is itself cut. The result is measured
    as a whole, so an ellipsis that joins the text next to it (one that starts with a
    combining mark) still fits.

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
    break or another control character outside an escape sequence, or ending inside an
    unfinished one.
    """
    line_arg("text", text)
    int_arg("width", width, 0)
    line_arg("ellipsis", ellipsis)
    choice_arg("side", side, _SIDES)
    if _plain(text):
        if len(text) <= width or _plain(ellipsis):
            return text if len(text) <= width else _sliced(text, width, ellipsis, side)
        if len(text) > 2 * width + 1:
            # At most ``width`` characters are kept from each end; an empty unit too wide
            # for any budget stands for the rest, so a long line costs only what is kept.
            gap = ("", width + 1, False)
            return cut(
                [*units(text[:width]), gap, *units(text[len(text) - width :])],
                width,
                ellipsis,
                side,
            )
    line = units(text)
    if sum(unit[1] for unit in line) <= width:
        return text
    return cut(line, width, ellipsis, side)


def _fill_arg(fill: object) -> str:
    text = line_arg("fill", fill)
    found = units(text)
    if len(found) != 1 or found[0][1] != 1 or grapheme_class(text[0]) in "EJS":
        raise ValueError(
            "fill must be one character one column wide that does not join the text before"
            f" it, got {shown(fill)}"
        )
    return text


def _spread(text: str, width: int, align: str, fill: str) -> str:
    """``fill`` on the sides of ``text`` so the whole takes exactly ``width`` columns.

    A fill next to the text can join one of its clusters (a text that starts with a
    combining mark): the fill on that side is then measured joined, and the padding goes
    where it reaches the width, on the side ``align`` asks for when it can.
    """
    size = width_of(text)
    spare = width - size
    left = 0 if align == "left" else spare if align == "right" else spare // 2
    plain = fill * left + text + fill * (spare - left)
    if (text.isascii() and fill.isascii()) or width_of(plain) == width:
        return plain
    on_left = width_of(fill + text) - 1 - size
    on_right = width_of(text + fill) - 1 - size
    both = spare - on_left - on_right
    sides = [(both // 2, both - both // 2), (0, spare - on_right), (spare - on_left, 0)]
    if align != "center":
        sides = sides[1:] if align == "left" else [sides[2], sides[1]]
        sides.append((both // 2, both - both // 2))
    for before, after in sides:
        result = fill * before + text + fill * after
        if min(before, after) >= 0 and width_of(result) == width:
            return result
    return plain


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
    ``width`` below 0 or above ``sys.maxsize``, an unknown ``align``, a ``fill`` that is not
    one character one column wide or that joins the text before it (a combining mark),
    or ``text`` holding a control character outside an escape sequence or ending inside an
    unfinished one. Padding too large for memory raises ``MemoryError``, as any string
    that large does.
    """
    line_arg("text", text)
    int_arg("width", width, 0)
    if width > sys.maxsize:
        raise ValueError(f"width must be at most sys.maxsize, got {shown(width)}")
    choice_arg("align", align, _ALIGNS)
    fill = _fill_arg(fill)
    if width_of(text) >= width:
        return text
    return _spread(text, width, align, fill)


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
