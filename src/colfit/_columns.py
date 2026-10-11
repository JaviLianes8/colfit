"""Arrange strings into evenly sized columns that fit a total width."""

from __future__ import annotations

from collections.abc import Iterable

from ._width import display_width

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
    rows = []
    for row in range(nrows):
        rows.append([column[row] for column in columns if row < len(column)])
    return rows, col_widths


def _fits(col_widths: list[int], gap: int, width: int) -> bool:
    if not col_widths:
        return True
    return sum(col_widths) + gap * (len(col_widths) - 1) <= width


def _render(
    items: list[str], widths: list[int], rows: list[list[int]], col_widths: list[int], gap: int
) -> str:
    separator = " " * gap
    lines = []
    for row in rows:
        cells = [items[idx] + " " * (col_widths[col] - widths[idx]) for col, idx in enumerate(row)]
        lines.append(separator.join(cells).rstrip())
    return "\n".join(lines)


def columnize(items: Iterable[str], width: int = 80, *, gap: int = 2, order: str = "rows") -> str:
    """Lay ``items`` out in the most columns that fit ``width``.

    ``gap`` spaces separate columns. ``order`` fills row by row (``"rows"``) or
    column by column (``"columns"``, like ``ls``). Column widths follow the
    display width of their contents, so wide and zero-width characters align.
    Items wider than ``width`` fall back to a single column.
    """
    if order not in _ORDERS:
        raise ValueError(f"order must be one of {_ORDERS}, got {order!r}")
    if gap < 0:
        raise ValueError(f"gap must not be negative, got {gap}")
    materialized = list(items)
    if not materialized:
        return ""
    widths = [display_width(item) for item in materialized]
    usable = width if width >= 1 else 1
    upper = min(len(materialized), max(1, (usable + gap) // (1 + gap)))
    for ncols in range(upper, 0, -1):
        rows, col_widths = _layout(widths, ncols, order)
        if ncols == 1 or _fits(col_widths, gap, usable):
            return _render(materialized, widths, rows, col_widths, gap)
    return _render(materialized, widths, *_layout(widths, 1, order), gap)
