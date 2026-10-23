"""Edges of the 1.0 promise: error types and sizes, the indent rule, the column search."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest

from colfit import Order, columnize, display_width, fit, pad, truncate, wrap


@pytest.mark.parametrize(
    "call",
    [
        lambda v: truncate("abc", 2, side=v),
        lambda v: fit("abc", 2, side=v),
        lambda v: pad("abc", 5, align=v),
        lambda v: fit("abc", 5, align=v),
        lambda v: columnize(["a"], order=v),
    ],
)
@pytest.mark.parametrize("value", [1, None, b"end", ["rows"]])
def test_a_choice_of_the_wrong_type_is_a_type_error(
    call: Callable[[Any], object], value: object
) -> None:
    with pytest.raises(TypeError, match=r"must be str, not "):
        call(value)


HUGE = "x" * 1_000_000


@pytest.mark.parametrize(
    "call",
    [
        lambda: truncate("abc", 2, side=HUGE),  # type: ignore[arg-type]
        lambda: pad("abc", 5, align=HUGE),  # type: ignore[arg-type]
        lambda: columnize(["a"], order=HUGE),  # type: ignore[arg-type]
        lambda: pad("abc", 5, fill=HUGE),
        lambda: truncate("abc", -(10**5000)),
        lambda: wrap("abc", 1, max_lines=-(10**100)),
        lambda: columnize(["a"], gap=-(10**5000)),
    ],
)
def test_error_messages_stay_short_for_huge_arguments(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError) as error:
        call()
    assert len(str(error.value)) < 160


def test_a_message_quotes_at_most_forty_characters() -> None:
    with pytest.raises(ValueError) as error:
        truncate("abc", 2, side="y" * 50)  # type: ignore[arg-type]
    assert str(error.value).endswith("got 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy...")
    with pytest.raises(ValueError) as error:
        truncate("abc", 2, side="y" * 37)  # type: ignore[arg-type]
    assert str(error.value).endswith("got '" + "y" * 37 + "'")


class _Unprintable(int):
    def __repr__(self) -> str:
        raise RuntimeError("no repr")


def test_an_argument_that_cannot_be_shown_still_gives_the_promised_error() -> None:
    with pytest.raises(ValueError, match="got <_Unprintable that cannot be shown>"):
        pad("abc", _Unprintable(-3))


def test_a_huge_type_name_is_cut_in_type_errors() -> None:
    kind = type("K" * 10_000, (), {})
    with pytest.raises(TypeError) as error:
        display_width(kind())
    assert len(str(error.value)) < 100


def test_the_indent_stays_when_the_first_word_fits_after_it() -> None:
    assert wrap("   ab cd", 5) == ["   ab", "cd"]


def test_the_indent_goes_when_the_first_word_fits_a_line_but_not_after_it() -> None:
    assert wrap("   abcd ef", 5) == ["abcd", "ef"]
    assert wrap("         ab", 4) == ["ab"]


def test_the_indent_stays_before_a_word_that_must_break_anyway() -> None:
    assert wrap("   abcdefgh", 5) == ["   ab", "cdefg", "h"]


def test_spaces_alone_are_one_empty_line_and_no_text_no_line() -> None:
    assert wrap("   ", 5) == [""]
    assert wrap("", 5) == []


def _reference(items: list[str], width: int, gap: int, order: str) -> str:
    """The plain search: every column count from the most down, every layout built."""
    count = len(items)
    for ncols in range(min(count, max(1, (width + gap) // (1 + gap))), 0, -1):
        nrows = -(-count // ncols)
        if order == "rows":
            grid = [list(range(c, count, ncols)) for c in range(ncols)]
        else:
            grid = [list(range(c * nrows, min(c * nrows + nrows, count))) for c in range(ncols)]
        grid = [column for column in grid if column]
        sizes = [max(display_width(items[i]) for i in column) for column in grid]
        if ncols == 1 or sum(sizes) + gap * (len(sizes) - 1) <= width:
            lines = []
            for row in range(nrows):
                cells = [
                    items[col[row]] + " " * (sizes[k] - display_width(items[col[row]]))
                    for k, col in enumerate(grid)
                    if row < len(col)
                ]
                lines.append((" " * gap).join(cells).rstrip(" "))
            return "\n".join(lines)
    return ""


@pytest.mark.parametrize("order", ["rows", "columns"])
def test_the_column_search_finds_what_the_plain_search_finds(order: Order) -> None:
    rng = random.Random(2026)
    pieces = ["a", "bb", "ccc", "dddddd", "\u65e5", "e\u0301", "\x1b[1mx\x1b[0m"]
    for _ in range(1500):
        items = [
            "".join(rng.choices(pieces, k=rng.randint(1, 4))) for _ in range(rng.randint(1, 30))
        ]
        width, gap = rng.randint(1, 60), rng.randint(0, 3)
        assert columnize(items, width, gap=gap, order=order) == _reference(items, width, gap, order)
