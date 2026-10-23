"""Replace part of a line of units with a mark so the result fits a width."""

from __future__ import annotations

from ._width import Unit, escapes_of, units, width_of


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
    return "".join(escapes_of(line))


def _spans(line: list[Unit], budget: int, side: str) -> tuple[int, int]:
    """Units ``line[:head]`` and ``line[tail:]`` kept around the mark."""
    if side == "end":
        return take(line, budget), len(line)
    if side == "start":
        return 0, len(line) - take(line[::-1], budget)
    head = take(line, (budget + 1) // 2)
    used = sum(unit[1] for unit in line[:head])
    return head, len(line) - take(line[head:][::-1], budget - used)


def cut(line: list[Unit], width: int, mark: str, side: str) -> str:
    """Replace part of ``line`` with ``mark`` so the result fits ``width`` columns.

    The removed part becomes ``mark`` followed by the escape sequences it held. The result
    is measured as a whole: a mark that joins the cluster next to it (one that starts
    with a combining mark) makes the kept text shorter until it fits.
    """
    marks = units(mark)
    budget = width - sum(unit[1] for unit in marks)
    if budget < 0:
        kept = take(marks, width)
        mark, budget = _joined(marks[:kept]) + _escapes(marks[kept:]), 0
    while True:
        head, tail = _spans(line, budget, side)
        result = _joined(line[:head]) + mark + _escapes(line[head:tail]) + _joined(line[tail:])
        over = width_of(result) - width
        used = sum(unit[1] for unit in line[:head]) + sum(unit[1] for unit in line[tail:])
        if over <= 0:
            return result
        if not used:
            # Only zero-width clusters are left, and the mark joined them: drop them too.
            return mark + _escapes(line)
        budget = max(0, used - over)
