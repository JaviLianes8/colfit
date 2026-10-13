"""Arrange strings into evenly sized columns that fit a total width."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from ._check import choice_arg, int_arg, line_arg
from ._width import width_of

Order = Literal["rows", "columns"]

_ORDERS = ("rows", "columns")


def _layout(widths: list[int], ncols: int, order: str) -> tuple[list[list[int]], list[int]]:
    """Index grid (rows of item indices) and the width of each kept column."""
    count = len(widths)
    nrows = -(-count // ncols)
    if order == "rows":
        columns = [list(range(start, count, ncols)) for start in range(ncols)]
    else:
        columns = [list(range(c * nrows, min(c * nrows + nrows, count))) for c in range(ncols)]
    columns = [column for column in columns if column]
    col_widths = [max(widths[i] for i in column) for column in columns]
    rows = [[column[row] for column in columns if row < len(column)] for row in range(nrows)]
    return rows, col_widths


def _render(
    items: list[str], widths: list[int], rows: list[list[int]], col_widths: list[int], gap: int
) -> str:
    separator = " " * gap
    lines = []
    for row in rows:
        cells = [items[idx] + " " * (col_widths[col] - widths[idx]) for col, idx in enumerate(row)]
        lines.append(separator.join(cells).rstrip(" "))
    return "\n".join(lines)


def columnize(items: Iterable[str], width: int = 80, *, gap: int = 2, order: Order = "rows") -> str:
    """Lay ``items`` out in the most columns that fit ``width`` terminal columns.

    ``gap`` spaces separate columns. ``order`` fills row by row (``"rows"``) or column by
    column (``"columns"``, like ``ls``). Cells are padded to the display width of their
    column, so wide characters, emoji and coloured items line up. Items wider than
    ``width`` fall back to a single column. Lines carry no trailing spaces.
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
    upper = min(len(materialized), max(1, (width + gap) // (1 + gap)))
    for ncols in range(upper, 1, -1):
        rows, col_widths = _layout(widths, ncols, order)
        if sum(col_widths) + gap * (len(col_widths) - 1) <= width:
            return _render(materialized, widths, rows, col_widths, gap)
    return _render(materialized, widths, *_layout(widths, 1, order), gap)
