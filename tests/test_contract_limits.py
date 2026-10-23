"""Hostile sizes: no quadratic time, no huge allocation, only the promised errors."""

from __future__ import annotations

import sys
import time
import tracemalloc
from collections.abc import Callable

import pytest

from colfit import Order, columnize, display_width, fit, pad, truncate, wrap


def _seconds(call: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        call()
        best = min(best, time.perf_counter() - start)
    return best


def _linear(make: Callable[[int], Callable[[], object]], small: int) -> None:
    # Eight times the input: linear work takes about eight times longer, quadratic 64.
    fast, slow = _seconds(make(small)), _seconds(make(8 * small))
    assert slow < 24 * fast + 0.05, (fast, slow)


def test_wrap_is_linear_in_a_paragraph_made_of_escape_sequences() -> None:
    _linear(lambda n: lambda: wrap("\x1b[m" * n, 80), 50_000)


def test_wrap_is_linear_in_escape_sequences_between_spaces() -> None:
    _linear(lambda n: lambda: wrap("a" + " \x1b[m" * n, 80), 5_000)
    _linear(lambda n: lambda: wrap(" \x1b[m" * n, 80), 5_000)


@pytest.mark.parametrize("order", ["rows", "columns"])
def test_columnize_is_not_quadratic_when_one_item_is_as_wide_as_the_line(order: Order) -> None:
    def make(n: int) -> Callable[[], object]:
        return lambda: columnize(["a"] * n + ["b" * n], n, gap=0, order=order)

    _linear(make, 1_000)


@pytest.mark.parametrize("order", ["rows", "columns"])
def test_columnize_is_not_quadratic_when_two_wide_items_never_share_a_row(order: Order) -> None:
    def make(n: int) -> Callable[[], object]:
        items = ["a"] * n
        items[0] = items[n - 7] = "b" * (n // 2 + 1)
        return lambda: columnize(items, n, gap=0, order=order)

    _linear(make, 1_000)


def test_a_gap_wider_than_the_line_gives_one_column_without_building_it() -> None:
    assert columnize(["a"], 80, gap=sys.maxsize) == "a"
    assert columnize(["a", "b"], 5, gap=sys.maxsize) == "a\nb"
    tracemalloc.start()
    try:
        assert columnize(["a", "b"], 5, gap=10**8) == "a\nb"
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000


@pytest.mark.parametrize(
    "call",
    [lambda: pad("a", 10**20), lambda: fit("a", 2**63), lambda: pad("a", 2**63, align="right")],
)
def test_a_width_past_sys_maxsize_is_a_value_error(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=r"width must be at most sys.maxsize"):
        call()


def test_truncate_and_wrap_take_any_width() -> None:
    assert truncate("abc", 10**30) == "abc"
    assert wrap("abc", 10**30) == ["abc"]
    assert columnize(["a", "b"], 10**30) == "a  b"


def _bytes_per_character(call: Callable[[str], object], text: str) -> float:
    tracemalloc.start()
    try:
        call(text)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return peak / len(text)


def test_long_lines_are_cut_and_measured_without_a_unit_per_character() -> None:
    plain, accented = "a" * 1_000_000, "\u00e9" * 1_000_000
    assert _bytes_per_character(lambda t: truncate(t, 10), plain) < 2
    assert _bytes_per_character(lambda t: truncate(t, 10, side="middle"), plain) < 2
    assert _bytes_per_character(display_width, accented) < 4
    assert _bytes_per_character(display_width, "\x1b[1m" + accented) < 4
