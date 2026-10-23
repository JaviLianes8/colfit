"""Arrange strings into evenly sized columns that fit a total width."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import accumulate
from typing import Literal

from ._check import choice_arg, int_arg, line_arg
from ._width import width_of

Order = Literal["rows", "columns"]

_ORDERS = ("rows", "columns")


def _column_widths(widths: list[int], ncols: int, order: str) -> list[int]:
    """Width of each non-empty column when the items are laid out in ``ncols`` columns."""
    if order == "rows":
        return [max(widths[col::ncols]) for col in range(ncols)]
    nrows = -(-len(widths) // ncols)
    return [max(widths[top : top + nrows]) for top in range(0, len(widths), nrows)]


def _render(
    items: list[str], widths: list[int], col_widths: list[int], order: str, gap: int
) -> str:
    count, ncols = len(items), len(col_widths)
    nrows = -(-count // ncols)
    separator = " " * gap
    lines = []
    for row in range(nrows):
        if order == "rows":
            line = range(row * ncols, min(row * ncols + ncols, count))
        else:
            line = range(row, count, nrows)
        cells = [items[i] + " " * (col_widths[col] - widths[i]) for col, i in enumerate(line)]
        lines.append(separator.join(cells).rstrip(" "))
    return "\n".join(lines)


def columnize(items: Iterable[str], width: int = 80, *, gap: int = 2, order: Order = "rows") -> str:
    """Lay ``items`` out in the most columns that fit ``width`` terminal columns.

    ``gap`` spaces separate columns. ``order`` fills row by row (``"rows"``) or column by
    column (``"columns"``, like ``ls``). Cells are padded to the display width of their
    column, so wide characters, emoji and coloured items line up. Items wider than
    ``width`` fall back to a single column. Lines carry no trailing spaces.

    >>> fruits = ["apple", "fig", "cherry", "date", "kiwi"]
    >>> print(columnize(fruits, width=20))
    apple  fig   cherry
    date   kiwi
    >>> print(columnize(fruits, width=20, order="columns"))
    apple  cherry  kiwi
    fig    date

    Each column count is tried from the most that could fit down, so the time grows with
    the number of items times ``width // (gap + 1)``: linear for terminal widths.

    Raises ``TypeError`` when ``items`` is a single ``str`` or holds a non-``str`` item, or
    an argument has the wrong type, and ``ValueError`` for a ``width`` below 1, a negative
    ``gap``, an unknown ``order``, or an item holding a control character outside an
    escape sequence.
    """
    int_arg("width", width, 1)
    int_arg("gap", gap, 0)
    choice_arg("order", order, _ORDERS)
    if isinstance(items, str):
        raise TypeError("items must be an iterable of str, not a single str")
    materialized = [line_arg("item", item) for item in items]
    if not materialized:
        return ""
    widths = [width_of(item) for item in materialized]
    upper = min(len(widths), max(1, (width + gap) // (1 + gap)))
    first_row = list(accumulate(widths[:upper], initial=0))
    tried_rows = 0
    for ncols in range(upper, 1, -1):
        if order == "columns":
            nrows = -(-len(widths) // ncols)
            if nrows == tried_rows:
                continue  # the same layout as one more column, already too wide
            tried_rows = nrows
        elif first_row[ncols] + gap * (ncols - 1) > width:
            continue  # the first row alone is too wide
        col_widths = _column_widths(widths, ncols, order)
        if sum(col_widths) + gap * (len(col_widths) - 1) <= width:
            return _render(materialized, widths, col_widths, order, gap)
    return _render(materialized, widths, [max(widths)], order, gap)
