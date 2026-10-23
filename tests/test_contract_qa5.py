"""Contracts from the fifth QA round: each one fails on a mutant of the code."""

from __future__ import annotations

import pytest

from colfit import display_width

_PREPENDED = ["\u0600", "\u0d4e"]
_IDS = ["arabic-number-sign", "malayalam-dot-reph"]
_A = "\U0001f1e6"  # regional indicator A


@pytest.mark.parametrize("prepended", _PREPENDED, ids=_IDS)
def test_a_flag_after_a_prepended_character_keeps_its_two_columns(prepended: str) -> None:
    assert display_width(prepended + _A) == 1 + display_width(_A) == 3
    assert display_width(prepended + _A + _A) == 1 + display_width(_A + _A) == 3
    assert display_width(prepended + prepended + _A) == 4


@pytest.mark.parametrize("prepended", _PREPENDED, ids=_IDS)
@pytest.mark.parametrize(
    "syllable", ["\uac00", "\uac01", "\u1100"], ids=["lv", "lvt", "leading-jamo"]
)
@pytest.mark.parametrize("tail", ["\u093e", "\u094d\u0915"], ids=["vowel", "conjunct"])
def test_a_hangul_syllable_after_a_prepended_character_keeps_its_two_columns(
    prepended: str, syllable: str, tail: str
) -> None:
    # The syllable is the base: the prepended character only adds its column before it.
    assert display_width(syllable + "\u093e") == 2
    assert display_width(prepended + syllable + tail) == 3


@pytest.mark.parametrize("prepended", _PREPENDED, ids=_IDS)
@pytest.mark.parametrize("jamo", ["\u1160", "\u1161", "\u11a8"], ids=["filler", "a", "kiyeok"])
def test_a_medial_or_final_jamo_after_a_prepended_character_is_its_own_base(
    prepended: str, jamo: str
) -> None:
    # A medial or final jamo is a letter, not a mark: with no leading jamo it is a base of
    # zero columns, so the spacing mark after it widens nothing, alone or after U+0600.
    assert display_width(jamo + "\u093e") == 0
    assert display_width(prepended + jamo + "\u093e") == 1
    assert display_width(prepended + "\u200d" + "\u093e") == 2
