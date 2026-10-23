"""Contracts from the eighth QA round: each one fails on a mutant of the code."""

from __future__ import annotations

import pytest

from colfit import display_width, graphemes


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("\u0d4e\uff9e", 2),
        ("\u0d4e\U0001f3fb", 3),
        ("\u0600\u0e33", 2),
    ],
    ids=["voiced-mark", "modifier", "thai-am"],
)
def test_a_character_after_a_visible_prepended_base_adds_its_own_width(
    text: str, width: int
) -> None:
    # The prepended character is the base here, and an Extend or SpacingMark letter after
    # it adds its width as it does after any other base.
    assert graphemes(text) == [text]
    assert display_width(text) == width


@pytest.mark.parametrize(
    "text",
    [
        "\u0915\u094d\u0937\u094d\u200d\u0937",
        "\u0915\u094d\u200d\u0937\u094d\u200d\u0937",
        "\u0995\u09cd\u0995\u09cd\u0995",
        "\u0995\u09cd\u200d\u0995\u09cd\u0995",
    ],
    ids=["zwj-before-third", "zwj-before-each", "bengali", "bengali-zwj"],
)
def test_a_conjunct_of_three_consonants_takes_two_columns(text: str) -> None:
    # Every later consonant joins the conjunct, after any linker and after a ZWJ: the ZWJ
    # changes no width.
    assert graphemes(text) == [text]
    assert display_width(text) == 2


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("\u00a9\u0301\ufe0f", 2),
        ("\u2764\u0301\ufe0f", 2),
        ("\u00a9\u200d\ufe0f", 2),
        ("\u231a\u0301\ufe0e", 1),
        ("\u231a\u200d\ufe0e", 1),
        ("\U0001f468\u200d\u2764\ufe0e", 2),
        ("\U0001f468\u200d\u2764\ufe0f", 2),
    ],
    ids=[
        "emoji-after-mark",
        "heart-emoji-after-mark",
        "emoji-after-zwj",
        "text-after-mark",
        "text-after-zwj",
        "text-on-a-later-pictograph",
        "emoji-on-a-later-pictograph",
    ],
)
def test_a_presentation_selector_applies_only_to_the_cluster_base(text: str, width: int) -> None:
    # Anywhere in the cluster, a selector picks the presentation of the base when the base
    # has both; it never acts on another character of the cluster.
    assert graphemes(text) == [text]
    assert display_width(text) == width


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("\u00ad\u0301", 1),
        ("\u00ad\u200d", 1),
        ("\u00ad\uff9e", 2),
        ("\u00ad\u0301\u0301", 1),
    ],
    ids=["acute", "zwj", "voiced-mark", "two-acutes"],
)
def test_marks_after_a_soft_hyphen_do_not_widen_it(text: str, width: int) -> None:
    # A soft hyphen is a control in UAX #29, so the marks after it are a cluster of their
    # own; only a spacing mark there widens the cluster before it.
    assert len(graphemes(text)) == 2
    assert display_width(text) == width


def test_a_spacing_mark_after_a_soft_hyphen_widens_it() -> None:
    assert graphemes("\u00ad\u093e") == ["\u00ad", "\u093e"]
    assert display_width("\u00ad\u093e") == 2
