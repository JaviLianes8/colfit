"""wrap: break at spaces, then between clusters, keep paragraphs, cap the lines."""

from __future__ import annotations

from colfit import wrap

E = "…"
TEXT = "The quick brown fox jumps over the lazy dog"


def test_lines_break_at_spaces_and_fill_greedily() -> None:
    assert wrap(TEXT, 12) == ["The quick", "brown fox", "jumps over", "the lazy dog"]


def test_text_that_fits_is_one_line() -> None:
    assert wrap("short", 10) == ["short"]


def test_empty_text_has_no_lines() -> None:
    assert wrap("", 10) == []


def test_spaces_at_a_break_are_dropped_and_inner_runs_kept() -> None:
    assert wrap("a  b   c", 4) == ["a  b", "c"]
    assert wrap("word   ", 4) == ["word"]


def test_leading_spaces_are_the_indent() -> None:
    assert wrap("  ab cd ef", 6) == ["  ab", "cd ef"]


def test_line_breaks_start_paragraphs_and_blank_lines_stay() -> None:
    assert wrap("ab cd\n\nef\r\ngh", 10) == ["ab cd", "", "ef", "gh"]
    assert wrap("   \nx", 3) == ["", "x"]


def test_long_words_break_between_clusters() -> None:
    assert wrap("abcdefgh", 3) == ["abc", "def", "gh"]
    assert wrap("ééé", 2) == ["éé", "é"]


def test_a_broken_word_shares_its_last_line() -> None:
    assert wrap("abcdefgh ij", 3) == ["abc", "def", "gh", "ij"]
    assert wrap("abcdefg h", 3) == ["abc", "def", "g h"]


def test_wide_characters_break_without_splitting() -> None:
    assert wrap("日本語です", 5) == ["日本", "語で", "す"]


def test_a_cluster_wider_than_the_line_gets_a_line_of_its_own() -> None:
    assert wrap("a日b", 1) == ["a", "日", "b"]


def test_escape_sequences_stay_with_the_text_before_them() -> None:
    lines = wrap("\x1b[1mbold text\x1b[0m here", 8)
    assert lines == ["\x1b[1mbold", "text\x1b[0m", "here"]


def test_max_lines_ends_the_last_kept_line_with_the_ellipsis() -> None:
    assert wrap(TEXT, 12, max_lines=2) == ["The quick", "brown fox" + E]


def test_max_lines_cuts_a_full_last_line_to_make_room() -> None:
    assert wrap(TEXT, 10, max_lines=3) == ["The quick", "brown fox", "jumps ove" + E]


def test_max_lines_keeps_the_escape_sequences_of_dropped_lines() -> None:
    lines = wrap("\x1b[1mone two\x1b[0m three", 3, max_lines=1)
    assert lines == ["\x1b[1mon" + E + "\x1b[0m"]


def test_max_lines_that_are_enough_change_nothing() -> None:
    assert wrap(TEXT, 12, max_lines=4) == wrap(TEXT, 12)


def test_custom_ellipsis_on_the_last_line() -> None:
    assert wrap(TEXT, 12, max_lines=1, ellipsis=" [...]") == ["The qu [...]"]
