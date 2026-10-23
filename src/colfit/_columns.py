"""Arrange strings into evenly sized columns that fit a total width."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from itertools import accumulate
from typing import Literal

from ._check import cell_arg, choice_arg, int_arg, shown
from ._width import width_of

Order = Literal["rows", "columns"]

_ORDERS = ("rows", "columns")
_TOP = 16  # the widest items whose columns bound a layout before it is built
_PASSES = 32  # passes over the items a search may make, on top of the allowance
_ALLOWANCE = 1 << 22  # item visits any search may make, so small inputs are searched fully


def _column_widths(widths: list[int], ncols: int, order: str) -> list[int]:
    """Width of each non-empty column when the items are laid out in ``ncols`` columns."""
    if order == "rows":
        return [max(widths[col::ncols]) for col in range(ncols)]
    nrows = -(-len(widths) // ncols)
    return [max(widths[top : top + nrows]) for top in range(0, len(widths), nrows)]


def _most_columns(widths: list[int], width: int, gap: int) -> int:
    """No layout has more columns: each column is at least as wide as a different item."""
    total, count = -gap, 0
    for size in sorted(widths):
        total += size + gap
        if total > width:
            break
        count += 1
    return max(1, count)


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


def _search(widths: list[int], width: int, gap: int, order: str) -> int:
    """The number of columns to lay the items out in."""
    count, widest = len(widths), max(widths)
    bounds = _Bounds(widths, gap)
    budget = _PASSES * count + _ALLOWANCE
    tried_rows = 0
    for ncols in range(_most_columns(widths, width, gap), 1, -1):
        nrows = -(-count // ncols)
        if order == "columns":
            if nrows == tried_rows:
                continue  # the same layout as one more column, already too wide
            tried_rows = nrows
        if ncols * widest + gap * (ncols - 1) <= width:
            return ncols  # fits however the items fall
        budget -= _TOP + (nrows if order == "rows" else 0)
        if budget >= 0 and bounds.too_wide(ncols, order, width):
            continue
        budget -= count
        if budget < 0:
            # Out of budget: the most columns that fit, each as wide as the widest item.
            return max(1, (width + gap) // (widest + gap))
        col_widths = _column_widths(widths, ncols, order)
        if sum(col_widths) + gap * (len(col_widths) - 1) <= width:
            return ncols
    return 1


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
    items or a row already make too wide are skipped without building the layout. The
    time is linear in the number of items: the search makes at most 32 passes over them
    beyond a fixed allowance of about four million item visits, and a search that needs
    more (thousands of items across thousands of columns) stops there and takes the most
    columns that fit when each is as wide as the widest item. With ``gap=0`` cells touch,
    so two cells that Unicode joins into one cluster (a lone regional indicator before
    another) are drawn as one.

    Raises ``TypeError`` when ``items`` is a single ``str`` or holds a non-``str`` item, or
    an argument has the wrong type, and ``ValueError`` for a ``width`` below 1, a ``gap``
    below 0 or above ``sys.maxsize``, an unknown ``order``, or an item holding a control
    character outside an escape sequence, ending inside an unfinished one, or starting with
    a mark that joins the text before it (such as a combining accent). A gap too large for
    memory raises ``MemoryError``, as any string that large does.
    """
    int_arg("width", width, 1)
    int_arg("gap", gap, 0)
    if gap > sys.maxsize:
        raise ValueError(f"gap must be at most sys.maxsize, got {shown(gap)}")
    choice_arg("order", order, _ORDERS)
    if isinstance(items, str):
        raise TypeError("items must be an iterable of str, not a single str")
    materialized = [cell_arg("item", item) for item in items]
    if not materialized:
        return ""
    widths = [width_of(item) for item in materialized]
    ncols = _search(widths, width, gap, order)
    return _render(materialized, widths, _column_widths(widths, ncols, order), order, gap)
