"""Contracts from the fourth QA round: each one failed on the code or a mutant of it."""

from __future__ import annotations

import pytest

from colfit import display_width

_ZWJ = "\u200d"


@pytest.mark.parametrize(
    "prepended",
    ["\u0600", "\u0d4e", "\U00011f02"],
    ids=["arabic-number-sign", "malayalam-dot-reph", "kawi"],
)
def test_a_zwj_after_a_prepended_character_sits_on_it_like_any_other_mark(
    prepended: str,
) -> None:
    # The ZWJ has no base of its own either, so the spacing mark after it widens the
    # prepended character, as it widens "a" in "a\u200d\u093e".
    assert display_width("a" + _ZWJ + "\u093e") == 2
    assert display_width(prepended + _ZWJ + "\u093e") == 2
    assert display_width(prepended + prepended + _ZWJ + "\u093e") == 3


def test_the_order_of_the_marks_after_a_prepended_character_does_not_matter() -> None:
    marks = ["\u0301" + _ZWJ, _ZWJ + "\u0301", "\u200c", _ZWJ]
    assert [display_width("\u0600" + mark + "\u093e") for mark in marks] == [2, 2, 2, 2]
    assert display_width("\u0d4e" + _ZWJ + "\u0d3e") == display_width("\u0d15\u200d\u0d3e")


@pytest.mark.parametrize("mark", ["\u102b", "\u102c"])
def test_a_spacing_mark_of_no_grapheme_class_widens_the_prepended_character(mark: str) -> None:
    # U+102B and U+102C are spacing marks (Mc) that UAX #29 does not class as SpacingMark.
    assert display_width("a" + mark) == 2
    assert display_width("\u0600" + mark) == 2


@pytest.mark.parametrize("am", ["\u0e33", "\u0eb3"], ids=["thai", "lao"])
@pytest.mark.parametrize("tail", ["\u093e", "\u094d\u0915"], ids=["vowel", "conjunct"])
def test_the_am_letter_after_a_prepended_character_takes_the_place_of_a_mark(
    am: str, tail: str
) -> None:
    # Thai and Lao AM are SpacingMark in UAX #29 though not Mc: on a prepended character
    # they count as a mark, as they do on "a".
    assert display_width("a" + am + tail) == 2
    assert display_width("\u0600" + am + tail) == 2


@pytest.mark.parametrize("count", [2, 3, 4])
def test_each_prepended_character_before_nonspacing_marks_counts_once(count: int) -> None:
    assert display_width("\u0600" * count + "\u0301") == count
    assert display_width("\u0600" * count + "\u0301\u0301") == count
    assert display_width("\u0600" * count + _ZWJ) == count
