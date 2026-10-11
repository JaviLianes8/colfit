from colfit import columnize


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


def test_gap_sets_the_space_between_columns() -> None:
    assert columnize(["aa", "bb"], width=80, gap=5) == "aa     bb"


def test_wide_characters_count_as_two_cells() -> None:
    assert columnize(["日", "x", "y", "z"], width=6, gap=2) == "日  x\ny   z"


def test_unknown_order_is_rejected() -> None:
    try:
        columnize(["a"], order="diagonal")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_negative_gap_is_rejected() -> None:
    try:
        columnize(["a"], gap=-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
