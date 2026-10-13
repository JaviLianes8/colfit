"""truncate: where the cut goes, what it keeps, and the tie rules."""

from __future__ import annotations

from colfit import display_width, truncate

E = "\u2026"


def test_text_that_fits_is_returned_unchanged() -> None:
    assert truncate("hello", 5) == "hello"
    assert truncate("", 0) == ""


def test_end_cut_keeps_the_start() -> None:
    assert truncate("hello world", 8) == "hello w" + E


def test_start_cut_keeps_the_end() -> None:
    assert truncate("hello world", 8, side="start") == E + "o world"


def test_middle_cut_keeps_both_ends() -> None:
    assert truncate("abcdefghij", 7, side="middle") == "abc" + E + "hij"


def test_middle_cut_gives_the_odd_column_to_the_start() -> None:
    assert truncate("abcdefghij", 6, side="middle") == "abc" + E + "ij"


def test_middle_cut_lets_the_end_use_a_column_the_start_could_not() -> None:
    # The start half is 2 columns but a wide character does not fit in it.
    assert truncate("\u65e5\u672cabcdef", 5, side="middle") == "\u65e5" + E + "ef"
    assert truncate("a\u65e5bcdefgh", 5, side="middle") == "a" + E + "fgh"


def test_custom_ellipsis_and_empty_ellipsis() -> None:
    assert truncate("hello world", 8, ellipsis="...") == "hello..."
    assert truncate("hello world", 5, ellipsis="") == "hello"


def test_wide_characters_are_never_split() -> None:
    assert truncate("\u65e5\u672c\u8a9e", 4) == "\u65e5" + E
    assert display_width(truncate("\u65e5\u672c\u8a9e", 4)) == 3


def test_clusters_are_never_split() -> None:
    family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
    assert truncate(family * 3, 5) == family * 2 + E
    assert truncate("e\u0301e\u0301e\u0301", 2) == "e\u0301" + E
    assert truncate("\U0001f1ea\U0001f1f8\U0001f1eb\U0001f1f7", 3) == "\U0001f1ea\U0001f1f8" + E


def test_zero_width_clusters_before_the_cut_are_kept() -> None:
    assert truncate("ab\u200bcdef", 3) == "ab\u200b" + E


def test_width_zero_keeps_only_escape_sequences() -> None:
    assert truncate("abc", 0) == ""
    assert truncate("\x1b[1mabc\x1b[0m", 0) == "\x1b[1m\x1b[0m"


def test_ellipsis_wider_than_the_width_is_cut_itself() -> None:
    assert truncate("abcdef", 2, ellipsis="...") == ".."
    assert truncate("abcdef", 1, ellipsis="\u65e5") == ""


def test_cut_ellipsis_keeps_its_escape_sequences() -> None:
    assert truncate("abcdef", 1, ellipsis="\x1b[2m..\x1b[0m") == "\x1b[2m.\x1b[0m"


def test_escape_sequences_before_the_cut_stay_and_removed_ones_follow_the_ellipsis() -> None:
    text = "\x1b[31mred\x1b[0m and \x1b[32mgreen\x1b[0m"
    assert truncate(text, 5) == "\x1b[31mred\x1b[0m " + E + "\x1b[32m\x1b[0m"


def test_start_cut_puts_removed_escape_sequences_after_the_ellipsis() -> None:
    assert truncate("\x1b[31mred\x1b[0m", 2, side="start") == E + "\x1b[31md\x1b[0m"


def test_middle_cut_puts_removed_escape_sequences_after_the_ellipsis() -> None:
    text = "ab\x1b[1mcdef\x1b[0mgh"
    assert truncate(text, 5, side="middle") == "ab\x1b[1m" + E + "\x1b[0mgh"


def test_text_wider_than_the_width_only_by_escapes_is_unchanged() -> None:
    assert truncate("\x1b[31mabc\x1b[0m", 3) == "\x1b[31mabc\x1b[0m"
