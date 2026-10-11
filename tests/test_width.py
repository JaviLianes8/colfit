from colfit import display_width


def test_ascii_counts_one_cell_per_character() -> None:
    assert display_width("hello") == 5


def test_empty_string_is_zero() -> None:
    assert display_width("") == 0


def test_wide_east_asian_counts_two_cells() -> None:
    assert display_width("日本") == 4


def test_combining_marks_count_as_zero() -> None:
    assert display_width("é") == 1


def test_zero_width_characters_count_as_zero() -> None:
    assert display_width("a​b") == 2
