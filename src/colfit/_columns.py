"""Arrange strings into evenly sized columns that fit a total width."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import accumulate
from typing import Literal

from ._check import cell_arg, choice_arg, int_arg
from ._width import width_of

Order = Literal["rows", "columns"]

_ORDERS = ("rows", "columns")
_TOP = 16  # the widest items whose columns bound a layout before it is built


def _column_widths(widths: list[int], ncols: int, order: str) -> list[int]:
    """Width of each non-empty column when the items are laid out in ``ncols`` columns."""
    if order == "rows":
        return [max(widths[col::ncols]) for col in range(ncols)]
    nrows = -(-len(widths) // ncols)
    return [max(widths[top : top + nrows]) for top in range(0, len(widths), nrows)]


class _Bounds:
    """Cheap lower bounds on a layout's total width, to skip most layouts too wide."""

    def __init__(self, widths: list[int], gap: int) -> None:
        self.widths, self.gap = widths, gap
        self.narrowest = min(widths)
        self.top = sorted(range(len(widths)), key=widths.__getitem__)[-_TOP:]
        self.sums = list(accumulate(widths, initial=0))

    def too_wide(self, ncols: int, order: str, width: int) -> bool:
        count, gap, narrowest = len(self.widths), self.gap, self.narrowest
        nrows = -(-count // ncols)
        if order == "columns":
            ncols = -(-count // nrows)
        floor: dict[int, int] = {}
        for i in self.top:  # the widest items, each in its own column
            col = i % ncols if order == "rows" else i // nrows
            floor[col] = max(floor.get(col, 0), self.widths[i])
        least = sum(floor.values()) + (ncols - len(floor)) * narrowest + gap * (ncols - 1)
        if least > width:
            return True
        if order == "columns":
            return False
        sums = self.sums
        for top in range(0, count, ncols):  # every row, each cell in its own column
            end = min(top + ncols, count)
            row = sums[end] - sums[top] + (ncols - (end - top)) * narrowest
            if row + gap * (ncols - 1) > width:
                return True
        return False


def _render(
    items: list[str], widths: list[int], col_widths: list[int], order: str, gap: int
) -> str:
    count, ncols = len(items), len(col_widths)
    nrows = -(-count // ncols)
    separator = " " * gap if ncols > 1 else ""
    lines = []
    for row in range(nrows):
        if order == "rows":
            line = range(row * ncols, min(row * ncols + ncols, count))
        else:
            line = range(row, count, nrows)
        cells = [items[i] + " " * (col_widths[col] - widths[i]) for col, i in enumerate(line[:-1])]
        # The last cell needs no padding: it would be stripped with the line's end.
        cells.append(items[line[-1]])
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

    Each column count is tried from the most that could fit down. Counts that the widest
    items or a row already make too wide are skipped without building the layout, and
    each other count takes time in proportion to the number of items. The time is at most
    the number of items times ``width // (gap + 1)``, linear for any fixed width, and only
    items laid out to pass those checks get near it. With ``gap=0`` cells touch,
    so two cells that Unicode joins into one cluster (a lone regional indicator before
    another) are drawn as one.

    Raises ``TypeError`` when ``items`` is a single ``str`` or holds a non-``str`` item, or
    an argument has the wrong type, and ``ValueError`` for a ``width`` below 1, a negative
    ``gap``, an unknown ``order``, or an item holding a control character outside an
    escape sequence, ending inside an unfinished one, or starting with a mark that joins
    the text before it (such as a combining accent).
    """
    int_arg("width", width, 1)
    int_arg("gap", gap, 0)
    choice_arg("order", order, _ORDERS)
    if isinstance(items, str):
        raise TypeError("items must be an iterable of str, not a single str")
    materialized = [cell_arg("item", item) for item in items]
    if not materialized:
        return ""
    widths = [width_of(item) for item in materialized]
    # Two columns never fit when the gap alone is wider than the line.
    upper = min(len(widths), max(1, (width + gap) // (1 + gap))) if gap < width else 1
    bounds = _Bounds(widths, gap)
    tried_rows = 0
    for ncols in range(upper, 1, -1):
        if order == "columns":
            nrows = -(-len(widths) // ncols)
            if nrows == tried_rows:
                continue  # the same layout as one more column, already too wide
            tried_rows = nrows
        if bounds.too_wide(ncols, order, width):
            continue
        col_widths = _column_widths(widths, ncols, order)
        if sum(col_widths) + gap * (len(col_widths) - 1) <= width:
            return _render(materialized, widths, col_widths, order, gap)
    return _render(materialized, widths, [max(widths)], order, gap)
