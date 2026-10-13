"""pad and fit: alignment, fill, the centring tie rule, and exact widths."""

from __future__ import annotations

from colfit import display_width, fit, pad


def test_pad_aligns_left_by_default() -> None:
    assert pad("ab", 5) == "ab   "


def test_pad_aligns_right() -> None:
    assert pad("ab", 5, align="right") == "   ab"


def test_pad_centre_puts_the_odd_column_on_the_right() -> None:
    assert pad("ab", 5, align="center") == " ab  "
    assert pad("ab", 6, align="center") == "  ab  "


def test_pad_uses_the_fill_character() -> None:
    assert pad("ab", 5, align="center", fill=".") == ".ab.."


def test_pad_counts_display_columns() -> None:
    assert pad("\u65e5", 4) == "\u65e5  "
    assert pad("\x1b[1mx\x1b[0m", 3) == "\x1b[1mx\x1b[0m  "


def test_pad_leaves_text_that_is_already_wide_enough() -> None:
    assert pad("abcdef", 3) == "abcdef"
    assert pad("abc", 3) == "abc"


def test_fit_cuts_long_text_and_pads_short_text() -> None:
    assert fit("hello world", 8) == "hello w\u2026"
    assert fit("hi", 5, align="right") == "   hi"


def test_fit_fills_the_column_a_wide_character_could_not_use() -> None:
    assert fit("\u65e5\u672c\u8a9e", 4) == "\u65e5\u2026 "
    assert fit("\u65e5\u672c\u8a9e", 4, align="right", fill="_") == "_\u65e5\u2026"


def test_fit_passes_ellipsis_and_side_through() -> None:
    assert fit("abcdefghij", 7, side="middle", ellipsis="~") == "abc~hij"


def test_fit_is_always_exactly_the_width() -> None:
    for text in ("", "a", "\u65e5\u672c\u8a9e", "\U0001f1ea\U0001f1f8x", "e\u0301" * 9):
        for width in range(0, 8):
            assert display_width(fit(text, width)) == width, (text, width)
