"""Contracts from the seventh QA round: each one fails on a mutant of the code."""

from __future__ import annotations

import pytest

from colfit import display_width, graphemes

_ZWJ = "\u200d"
_LEADS = ["a", "\u0e01", "\u0915\u094d", "\u4e2d", "\uff76"]
_LEAD_IDS = ["latin", "thai", "devanagari-virama", "cjk", "halfwidth-katakana"]
# Visible characters that join the cluster before them even after a ZWJ: Thai and Lao AM
# (SpacingMark, gc Lo), the halfwidth voiced marks (Extend, one column) and a skin tone
# modifier (Extend, two columns).
_TAILS = ["\u0e33", "\u0eb3", "\uff9e", "\uff9f", "\U0001f3fb", "\U0001f3ff"]
_TAIL_IDS = ["thai-am", "lao-am", "voiced", "semi-voiced", "light", "dark"]


@pytest.mark.parametrize("lead", _LEADS, ids=_LEAD_IDS)
@pytest.mark.parametrize("tail", _TAILS, ids=_TAIL_IDS)
def test_a_zwj_takes_no_columns_and_the_character_after_it_keeps_its_own(
    lead: str, tail: str
) -> None:
    # The ZWJ joins no pictographs here, so it is only a format character: it takes no
    # columns and hides nothing, and the cluster measures as without it.
    assert graphemes(lead + _ZWJ + tail) == [lead + _ZWJ + tail]
    assert display_width(lead + _ZWJ + tail) == display_width(lead + tail)


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("a\u200d\u0e33", 2),
        ("\uff76\u200d\uff9e", 2),
        ("a\u200d\U0001f3fb", 3),
        ("\u4e2d\u200d\U0001f3fb", 4),
        ("\u0915\u094d\u200d\u0937", 2),
    ],
    ids=["thai-am", "voiced-mark", "modifier", "wide-modifier", "half-form-conjunct"],
)
def test_the_width_after_a_zwj_outside_an_emoji_sequence(text: str, width: int) -> None:
    assert display_width(text) == width
