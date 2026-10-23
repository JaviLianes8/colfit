"""Contracts from the sixth QA round: each one fails on a mutant of the code."""

from __future__ import annotations

import pytest

from colfit import display_width

_PREPENDED = ["\u0600", "\u0d4e"]
_IDS = ["arabic-number-sign", "malayalam-dot-reph"]
# Kirat Rai vowel signs: letters (gc Lo) with Grapheme_Cluster_Break=V that take one column.
_VOWELS = ["\U00016d63", "\U00016d67", "\U00016d68", "\U00016d69", "\U00016d6a"]
_TAILS = ["\u093e", "\u094d\u0915", "\u0903"]


@pytest.mark.parametrize("prepended", _PREPENDED, ids=_IDS)
@pytest.mark.parametrize("vowel", _VOWELS, ids=[f"{ord(v):X}" for v in _VOWELS])
@pytest.mark.parametrize("tail", _TAILS, ids=["vowel", "conjunct", "visarga"])
def test_a_one_column_vowel_letter_after_a_prepended_character_is_its_own_base(
    prepended: str, vowel: str, tail: str
) -> None:
    # Like any jamo, the vowel letter is the base, not a mark on the prepended character:
    # the spacing mark widens the letter to two and the prepended character adds its one.
    assert display_width(vowel) == 1
    assert display_width(vowel + tail) == 2
    assert display_width(prepended + vowel + tail) == 3
