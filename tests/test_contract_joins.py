"""Text written next to other text is measured as it joins there.

Unicode joins some characters to the cluster before them: combining marks, spacing vowel
signs, a ZWJ, variation selectors, skin tone modifiers. An ellipsis, a fill or a cell put
next to text, or an escape sequence inside it, must not break a width promise.
"""

from __future__ import annotations

import random

import pytest
from conftest import LETTERS, STANDALONE_SPACING_MARKS

from colfit import Align, Side, columnize, display_width, fit, graphemes, pad, truncate, wrap
from colfit._width import units


def test_truncate_measures_an_ellipsis_that_joins_the_kept_text() -> None:
    assert truncate("abcdef", 4, ellipsis="\u093f") == "abc\u093f"
    assert display_width(truncate("a\u2764bcdef", 4, ellipsis="\ufe0f..")) <= 4
    assert display_width(truncate("\u0915bcdef", 3, ellipsis="\u093e.")) <= 3
    assert display_width(wrap("abc def", 3, max_lines=1, ellipsis="\u093f")[0]) <= 3


def test_fit_and_pad_reach_the_width_when_the_fill_joins_the_text() -> None:
    assert pad("\u093fab", 6, align="right") == "   \u093fab"
    assert display_width(fit("\u093f", 3, align="right")) == 3
    assert display_width(fit("a\u2764bcdef", 4, ellipsis="\ufe0f..")) == 4
    assert display_width(pad("\u093f", 3, align="center")) == 3


def test_a_fill_that_joins_the_text_before_it_is_refused() -> None:
    for fill in ("\u0e33", "\uff9e", "\u0301", "\u200d"):
        with pytest.raises(ValueError, match="fill must be one character one column wide"):
            pad("a", 3, fill=fill)


@pytest.mark.parametrize("item", ["\u093fx", "\u0301", "\u200dx", "\u102cx", "\x1b[1m\u0301x"])
def test_columnize_refuses_an_item_that_starts_with_a_joining_mark(item: str) -> None:
    with pytest.raises(ValueError, match="item must not start with a mark that joins"):
        columnize(["ab", item], 5)


def test_columnize_takes_marks_after_the_first_character() -> None:
    assert columnize(["ab", "x\u093f"], 6) == "ab  x\u093f"


def test_an_escape_sequence_inside_a_cluster_changes_no_width() -> None:
    assert display_width("\U0001f1ea\x1b[0m\U0001f1f8") == 2
    assert display_width("\U0001f468\u200d\x1b[1m\U0001f469") == 2
    assert display_width("\u0915\x1b[1m\u093f") == 2
    assert display_width("e\x1b[1m\u0301") == 1


def test_a_cluster_with_an_escape_inside_is_never_split_and_keeps_it() -> None:
    assert truncate("\u0915\x1b[1m\u093fabc", 2) == "\u2026\x1b[1m"
    assert wrap("e\x1b[1m\u0301 ab", 1) == ["e\x1b[1m\u0301", "a", "b"]


@pytest.mark.parametrize("code", STANDALONE_SPACING_MARKS)
def test_a_spacing_mark_in_a_cluster_of_its_own_still_widens_its_syllable(code: int) -> None:
    assert len(STANDALONE_SPACING_MARKS) == 31
    mark = chr(code)
    letter = LETTERS[code >> 8]
    assert len(graphemes(letter + mark)) == 2
    assert display_width(letter + mark) == 2
    assert display_width(letter + mark + mark) == 2  # one syllable widens once
    assert display_width("\u65e5" + mark) == 2  # already two columns
    assert display_width(mark) == 0  # nothing before it to widen


def test_a_zwj_makes_one_emoji_only_before_another_pictograph() -> None:
    assert display_width("\u00a9\u200d\u0301") == 1
    assert display_width("\u00a9\u200d\u00a9") == 2
    assert display_width("\U0001f469\u200d\u0301") == 2


def test_prepended_characters_are_drawn_before_the_cluster_they_join() -> None:
    assert display_width("\u0d4e\U0001f44d\U0001f3fd") == 3
    assert display_width("\u0d4e\u0915\u093f") == 3
    assert display_width("\u06001") == 2


PIECES = [
    *"ab ",
    "\u65e5",
    "\u093f",
    "\u093e",
    "\u102c",
    "\u0915",
    "\u094d",
    "\ufe0f",
    "\ufe0e",
    "\u200d",
    "\u0301",
    "\u2764",
    "\u00a9",
    "\U0001f3fd",
    "\U0001f469",
    "\U0001f1ea",
    "\u0d4e",
    "\u0600",
    "\u0e33",
    "\x1b[1m",
]


@pytest.mark.parametrize("seed", [1, 2])
def test_every_width_promise_holds_for_text_that_joins_its_neighbours(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        text = "".join(rng.choices(PIECES, k=rng.randint(0, 8)))
        mark = "".join(rng.choices(PIECES, k=rng.randint(0, 3)))
        width = rng.randint(0, 9)
        side: Side = rng.choice(["end", "start", "middle"])
        align: Align = rng.choice(["left", "center", "right"])
        case = (text, mark, width, side, align)
        assert display_width(truncate(text, width, ellipsis=mark, side=side)) <= width, case
        assert display_width(fit(text, width, ellipsis=mark, side=side, align=align)) == width
        assert display_width(pad(text, width, align=align)) == max(width, display_width(text))
        for line in wrap(text, width + 1, max_lines=2, ellipsis=mark):
            wide = [unit for unit in units(line) if unit[1]]
            assert display_width(line) <= width + 1 or len(wide) == 1, case


def test_columns_fit_when_cells_touch_or_are_padded() -> None:
    rng = random.Random(3)
    for _ in range(1500):
        items = ["x" + "".join(rng.choices(PIECES, k=rng.randint(0, 5))) for _ in range(6)]
        width, gap = rng.randint(1, 30), rng.randint(0, 2)
        for order in ("rows", "columns"):
            out = columnize(items, width, gap=gap, order=order)
            if max(map(display_width, items)) <= width:
                assert all(display_width(line) <= width for line in out.split("\n")), items
