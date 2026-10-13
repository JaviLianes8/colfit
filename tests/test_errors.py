"""What each public function rejects, and with which error."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from colfit import columnize, fit, pad, truncate, wrap

LINE_FUNCTIONS: list[Callable[..., Any]] = [truncate, pad, fit]


@pytest.mark.parametrize("function", LINE_FUNCTIONS)
@pytest.mark.parametrize("bad", [b"abc", 5, None])
def test_text_must_be_a_string(function: Callable[..., Any], bad: object) -> None:
    with pytest.raises(TypeError, match="text must be str"):
        function(bad, 5)


@pytest.mark.parametrize("function", [*LINE_FUNCTIONS, wrap])
@pytest.mark.parametrize("bad", [2.0, "3", True, None])
def test_width_must_be_an_int(function: Callable[..., Any], bad: object) -> None:
    with pytest.raises(TypeError, match="width must be int"):
        function("abc", bad)


@pytest.mark.parametrize("function", LINE_FUNCTIONS)
def test_width_must_not_be_negative(function: Callable[..., Any]) -> None:
    with pytest.raises(ValueError, match="width must be at least 0, got -1"):
        function("abc", -1)


def test_wrap_and_columnize_need_at_least_one_column() -> None:
    with pytest.raises(ValueError, match="width must be at least 1, got 0"):
        wrap("abc", 0)
    with pytest.raises(ValueError, match="width must be at least 1, got 0"):
        columnize(["abc"], 0)


@pytest.mark.parametrize("function", LINE_FUNCTIONS)
@pytest.mark.parametrize("control", ["\n", "\r", "\x00", "\x7f", "\x85", "\u2028", "\x1b[1m\x07"])
def test_single_line_text_rejects_control_characters(
    function: Callable[..., Any], control: str
) -> None:
    with pytest.raises(ValueError, match="text must be one line without control characters"):
        function("a" + control + "b", 5)


def test_a_tab_points_to_expandtabs() -> None:
    with pytest.raises(ValueError, match=r"str\.expandtabs"):
        truncate("a\tb", 5)
    with pytest.raises(ValueError, match=r"str\.expandtabs"):
        wrap("a\tb", 5)


def test_control_characters_inside_escape_sequences_are_fine() -> None:
    assert truncate("\x1b]0;title\x07ab", 5) == "\x1b]0;title\x07ab"


def test_ellipsis_must_be_one_line_text() -> None:
    with pytest.raises(TypeError, match="ellipsis must be str"):
        truncate("abc", 2, ellipsis=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ellipsis must be one line"):
        truncate("abc", 2, ellipsis="\n")
    with pytest.raises(ValueError, match="ellipsis must be one line"):
        wrap("abc", 2, ellipsis="\t")


def test_side_align_and_order_must_be_known_values() -> None:
    with pytest.raises(ValueError, match="side must be one of 'end', 'start', 'middle'"):
        truncate("abc", 2, side="left")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="align must be one of 'left', 'center', 'right'"):
        pad("abc", 5, align="middle")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="order must be one of 'rows', 'columns'"):
        columnize(["a"], order="diagonal")  # type: ignore[arg-type]


@pytest.mark.parametrize("fill", ["", "ab", "\u65e5", "\u0301", "\x1b[1m", "e\u0301\u0301x"])
def test_fill_must_be_one_character_one_column_wide(fill: str) -> None:
    with pytest.raises(ValueError, match="fill must be one character one column wide"):
        pad("abc", 5, fill=fill)
    with pytest.raises(ValueError, match="fill must be one character one column wide"):
        fit("abcdefgh", 5, fill=fill)


def test_fill_may_carry_marks_if_it_stays_one_column() -> None:
    assert pad("a", 3, fill="e\u0301") == "ae\u0301e\u0301"


def test_max_lines_must_be_a_positive_int() -> None:
    with pytest.raises(ValueError, match="max_lines must be at least 1, got 0"):
        wrap("abc", 2, max_lines=0)
    with pytest.raises(TypeError, match="max_lines must be int"):
        wrap("abc", 2, max_lines=1.0)  # type: ignore[arg-type]


def test_wrap_text_must_be_a_string() -> None:
    with pytest.raises(TypeError, match="text must be str"):
        wrap(b"abc", 5)  # type: ignore[arg-type]


def test_columnize_rejects_bad_items_and_arguments() -> None:
    with pytest.raises(TypeError, match="not a single str"):
        columnize("abc")
    with pytest.raises(TypeError, match="item must be str"):
        columnize(["a", 1])  # type: ignore[list-item]
    with pytest.raises(ValueError, match="item must be one line"):
        columnize(["a", "b\nc"])
    with pytest.raises(ValueError, match="gap must be at least 0, got -1"):
        columnize(["a"], gap=-1)
    with pytest.raises(TypeError, match="width must be int"):
        columnize(["a"], width=True)
