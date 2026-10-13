"""Properties over seeded random strings mixing every kind of cluster and escape sequence."""

from __future__ import annotations

import itertools
import random

import pytest

from colfit import columnize, display_width, fit, graphemes, truncate, wrap
from colfit._width import units

PIECES = [
    *"abcxyz",
    " ",
    "  ",
    "\u65e5",
    "\uff21",
    "e\u0301",
    "\u0301",
    "\u200b",
    "\U0001f468\u200d\U0001f469\u200d\U0001f467",
    "\U0001f44d\U0001f3fd",
    "\U0001f1ea",
    "\u2764\ufe0f",
    "\u0915\u094d\u0937\u093f",
    "\u1112\u1161\u11ab",
    "\ud55c",
    "\x1b[31m",
    "\x1b[0m",
    "\x1b]8;;https://x.y\x1b\\",
    "\x1b]8;;\x07",
]


def _samples(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    return ["".join(rng.choices(PIECES, k=rng.randint(0, 12))) for _ in range(count)]


def _join(found: list[tuple[str, int, bool]]) -> str:
    return "".join(unit[0] for unit in found)


def _escapes(found: list[tuple[str, int, bool]]) -> str:
    return "".join(unit[0] for unit in found if unit[2])


def _shapes(text: str, side: str, mark: str) -> set[str]:
    """Every result the cut rule allows: whole units kept, the rest replaced by the mark."""
    found = units(text)
    n = len(found)
    if side == "end":
        return {_join(found[:k]) + mark + _escapes(found[k:]) for k in range(n + 1)}
    if side == "start":
        return {mark + _escapes(found[:k]) + _join(found[k:]) for k in range(n + 1)}
    return {
        _join(found[:i]) + mark + _escapes(found[i:j]) + _join(found[j:])
        for i in range(n + 1)
        for j in range(i, n + 1)
    }


@pytest.mark.parametrize("side", ["end", "start", "middle"])
@pytest.mark.parametrize("mark", ["\u2026", "...", ""])
def test_truncate_fits_keeps_whole_units_and_every_escape(side: str, mark: str) -> None:
    for text in _samples(len(side) * 7 + len(mark), 300):
        for width in range(0, 10):
            result = truncate(text, width, ellipsis=mark, side=side)  # type: ignore[arg-type]
            assert display_width(result) <= width
            if display_width(text) <= width:
                assert result == text
            else:
                cut_mark = truncate(mark, width, ellipsis="")
                assert result in _shapes(text, side, cut_mark), (text, width)
                assert _escapes(units(result)) == _escapes(units(text))


def test_truncate_at_the_end_keeps_as_much_as_fits() -> None:
    for text in _samples(3, 400):
        for width in range(1, 10):
            result = truncate(text, width)
            if result == text:
                continue
            kept = units(result[: result.index("\u2026")])
            rest = [unit for unit in units(text)[len(kept) :] if not unit[2]]
            assert display_width(_join(kept)) + 1 + rest[0][1] > width


def test_fit_is_exactly_the_width() -> None:
    for text in _samples(4, 400):
        for width in range(0, 10):
            for side in ("end", "start", "middle"):
                assert display_width(fit(text, width, side=side, align="center")) == width


def test_wrap_keeps_every_unit_in_order_and_fits() -> None:
    for text in _samples(5, 400):
        for width in range(1, 9):
            lines = wrap(text, width)
            for line in lines:
                wide_cluster = len([u for u in units(line) if u[1]]) == 1
                assert display_width(line) <= width or wide_cluster, (text, width, line)
                assert line == line.rstrip(" ") or not line.strip(" ")
                if not display_width(line):
                    assert not display_width(text.strip(" ")), (text, width, line)
            got = [u for line in lines for u in units(line) if u[0] != " "]
            assert got == [u for u in units(text) if u[0] != " "]


def test_wrap_with_max_lines_keeps_every_escape() -> None:
    for text in _samples(6, 300):
        for width in range(1, 7):
            lines = wrap(text, width, max_lines=2)
            assert len(lines) <= 2
            assert _escapes(units("".join(lines))) == _escapes(units(text))
            assert all(display_width(line) <= max(width, 2) for line in lines)


def test_columnize_fits_without_trailing_spaces() -> None:
    rng = random.Random(7)
    for _ in range(300):
        items = [text for text in _samples(rng.randrange(10**6), rng.randint(1, 9)) if text]
        width = rng.randint(1, 30)
        for order in ("rows", "columns"):
            out = columnize(items, width, gap=rng.randint(0, 3), order=order)
            if items and max(map(display_width, items)) <= width:
                assert all(display_width(line) <= width for line in out.splitlines())
            assert all(line == line.rstrip(" ") for line in out.splitlines())


def test_width_adds_up_across_cluster_boundaries() -> None:
    texts = _samples(8, 200)
    for left, right in itertools.pairwise(texts):
        if graphemes(left + right) == graphemes(left) + graphemes(right):
            assert display_width(left + right) == display_width(left) + display_width(right)
