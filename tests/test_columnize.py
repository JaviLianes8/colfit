"""columnize: the most columns that fit, row or column order, display-width padding."""

from __future__ import annotations

from colfit import columnize

FRUITS = ["apple", "fig", "cherry", "date", "elderberry", "kiwi", "lime"]


def test_empty_list_returns_empty_string() -> None:
    assert columnize([]) == ""


def test_single_item_returns_that_item() -> None:
    assert columnize(["only"]) == "only"


def test_short_items_pack_into_one_line() -> None:
    assert columnize(["a", "b", "c", "d"], width=80) == "a  b  c  d"


def test_wide_items_fall_back_to_a_single_column() -> None:
    assert columnize(["abcdefghij", "klmnopqrst"], width=5) == "abcdefghij\nklmnopqrst"


def test_item_longer_than_width_still_renders() -> None:
    assert columnize(["abcdefghij"], width=5) == "abcdefghij"


def test_row_order_fills_left_to_right() -> None:
    assert columnize(["1", "2", "3", "4", "5"], width=4, order="rows") == "1  2\n3  4\n5"


def test_column_order_fills_top_to_bottom() -> None:
    assert columnize(["1", "2", "3", "4", "5"], width=4, order="columns") == "1  4\n2  5\n3"


def test_exact_fit_is_accepted_and_one_more_column_is_not() -> None:
    assert columnize(["ab", "cd", "ef"], width=10) == "ab  cd  ef"
    assert columnize(["ab", "cd", "ef"], width=9) == "ab  cd\nef"


def test_each_column_takes_the_width_of_its_widest_cell() -> None:
    expected = "apple       fig   cherry  date\nelderberry  kiwi  lime"
    assert columnize(FRUITS, width=30) == expected


def test_column_order_with_uneven_columns() -> None:
    expected = "apple   date        lime\nfig     elderberry\ncherry  kiwi"
    assert columnize(FRUITS, width=30, order="columns") == expected


def test_gap_sets_the_space_between_columns() -> None:
    assert columnize(["aa", "bb"], width=80, gap=5) == "aa     bb"
    assert columnize(["aa", "bb"], width=80, gap=0) == "aabb"


def test_wide_characters_count_as_two_columns() -> None:
    assert columnize(["\u65e5", "x", "y", "z"], width=6, gap=2) == "\u65e5  x\ny   z"


def test_emoji_and_accents_line_up() -> None:
    items = ["\U0001f1ea\U0001f1f8", "e\u0301", "ab", "c"]
    assert columnize(items, width=6) == "\U0001f1ea\U0001f1f8  e\u0301\nab  c"


def test_coloured_items_are_padded_by_their_visible_width() -> None:
    items = ["\x1b[31mred\x1b[0m", "b", "cc", "d"]
    assert columnize(items, width=7) == "\x1b[31mred\x1b[0m  b\ncc   d"


def test_lines_carry_no_trailing_spaces() -> None:
    for line in columnize(FRUITS, width=30, order="columns").splitlines():
        assert line == line.rstrip(" ")


def test_any_iterable_of_strings_is_accepted() -> None:
    assert columnize(iter(("a", "b")), width=10) == "a  b"
    assert columnize((s for s in "xyz"), width=10) == "x  y  z"
