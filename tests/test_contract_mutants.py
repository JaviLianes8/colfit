"""Contracts added after the author mutation round: each pins a rule a mutant got past."""

from __future__ import annotations

import pytest

from colfit import columnize, display_width, pad, wrap


@pytest.mark.parametrize("introducer", ["\x90", "\x98", "\x9e", "\x9f"])
def test_an_8_bit_control_string_runs_to_its_terminator_or_the_end(introducer: str) -> None:
    # DCS, SOS, PM and APC as single 8-bit characters, with no ESC anywhere in the text.
    assert display_width("ab" + introducer + "junk") == 2
    assert display_width("ab" + introducer + "junk\x9cxy") == 4


def test_a_linker_with_no_consonant_before_it_makes_no_conjunct() -> None:
    # Marks take no columns, so a cluster that starts with a virama is just its consonant.
    assert display_width("\u094d\u0915") == 1
    assert display_width("\u0301\u094d\u0915") == 1
    assert display_width("\u0915\u094d\u0915") == 2


def test_columnize_strips_only_ascii_spaces_at_line_ends() -> None:
    items = ["a\u3000", "b\u00a0"]
    assert columnize(items, 3) == "a\u3000\nb\u00a0"
    assert pad("a\u3000", 4) == "a\u3000 "


def test_wrap_breaks_only_at_the_ascii_space() -> None:
    # No-break, em and ideographic spaces are word characters; U+3000 takes two columns.
    assert wrap("ab\u3000cd", 5) == ["ab\u3000c", "d"]
    assert wrap("a\u00a0b c", 3) == ["a\u00a0b", "c"]
    assert wrap("a\u2003b", 2) == ["a\u2003", "b"]
    assert wrap("a b", 2) == ["a", "b"]


def test_the_ellipsis_comes_before_the_dropped_escapes_even_on_an_empty_line() -> None:
    assert wrap("\n\x1b[31mred", 5, max_lines=1, ellipsis="\x1b[0m") == ["\x1b[0m\x1b[31m"]
    assert wrap("ab\ncd\x1b[1m", 5, max_lines=1, ellipsis="") == ["ab\x1b[1m"]


def test_a_quoted_argument_of_forty_characters_is_whole_and_of_41_is_cut() -> None:
    with pytest.raises(ValueError) as error:
        pad("a", 3, fill="x" * 38)  # its repr is exactly 40 characters
    assert str(error.value).endswith("got '" + "x" * 38 + "'")
    with pytest.raises(ValueError) as error:
        pad("a", 3, fill="x" * 39)
    assert str(error.value).endswith("got '" + "x" * 36 + "...")
