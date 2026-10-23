"""Contracts from the third QA round: each one failed on the code or a mutant of it."""

from __future__ import annotations

import random

import pytest
from test_contract_edges import _reference

from colfit import Order, _columns, columnize, display_width


@pytest.mark.parametrize(
    "text",
    [
        "\u0600\u0301\u093e",
        "\u0d4e\u0d41\u0d3e",
        "\U00011f02\U00011f00\U00011f03",
        "\u0600\u0301\u0301\u093e",
    ],
    ids=["arabic-number-sign", "malayalam-dot-reph", "kawi", "two-marks"],
)
def test_a_spacing_mark_after_nonspacing_marks_still_widens_the_prepended_character(
    text: str,
) -> None:
    # The marks have no base of their own, so they sit on the prepended character, and
    # the spacing mark widens it as it widens "a" in "a\u0301\u093e".
    assert display_width("a" + text[1:]) == 2
    assert display_width(text) == 2
    assert display_width(text[0] + text) == 3


def test_a_cluster_of_spacing_marks_with_no_base_measures_its_visible_letter() -> None:
    # U+0E33 is a letter that UAX #29 treats as a spacing mark; nothing before it to widen.
    assert (display_width("\u102c\u0e33"), display_width("a\u102c\u0e33")) == (1, 3)
    assert display_width("\u093e\u0e33") == 1


@pytest.mark.parametrize("order", ["rows", "columns"])
def test_a_few_hundred_items_are_searched_in_full(order: Order) -> None:
    rng = random.Random(1)
    items = [rng.choice(["a", "bb"]) for _ in range(500)]
    expected = _reference(items, 500, 0, order)
    assert columnize(items, 500, gap=0, order=order) == expected
    if order == "rows":
        assert len(expected.split("\n")) == 2  # 303 columns, not the 250 of the widest item


def test_a_search_cut_short_counts_no_gap_after_the_last_column() -> None:
    rng = random.Random(1)
    items = [rng.choice(["a", "bb"]) for _ in range(64_000)]
    lines = columnize(items, 91_994, gap=1).split("\n")
    # 30,665 columns two wide with 30,664 gaps between them take exactly 91,994.
    assert [len(line.split()) for line in lines] == [30_665, 30_665, 2_670]
    assert max(display_width(line) for line in lines) <= 91_994


def test_column_order_skips_counts_that_give_a_row_count_already_tried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Skewed widths: rebuilding layouts already too wide would spend the allowance on
    # them and fall back to the widest item, well inside the documented allowance.
    rng = random.Random(8000)
    items = ["x" * (40 if rng.random() < 0.01 else rng.randint(1, 3)) for _ in range(8000)]
    found = columnize(items, 5000, gap=0, order="columns")
    assert len(found.split("\n")) == 11
    monkeypatch.setattr(_columns, "_ALLOWANCE", 1 << 40)
    assert columnize(items, 5000, gap=0, order="columns") == found


@pytest.mark.parametrize("digits", [4000, 5000])
def test_a_gap_of_thousands_of_digits_is_quoted_short(digits: int) -> None:
    with pytest.raises(ValueError, match=r"gap must be at most sys.maxsize") as raised:
        columnize(["a"], 80, gap=10**digits)
    assert len(str(raised.value)) <= 100
