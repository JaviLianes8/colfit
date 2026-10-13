"""display_width: one rule per test, with the reason in the name."""

from __future__ import annotations

import pytest

from colfit import display_width


def test_ascii_counts_one_column_per_character() -> None:
    assert display_width("hello") == 5


def test_empty_string_is_zero() -> None:
    assert display_width("") == 0


def test_wide_east_asian_counts_two_columns() -> None:
    assert display_width("日本") == 4


def test_fullwidth_forms_count_two_columns() -> None:
    assert display_width("ＡＢ") == 4


def test_halfwidth_katakana_counts_one_column() -> None:
    assert display_width("ｶ") == 1


def test_ambiguous_characters_count_one_column() -> None:
    assert display_width("…±") == 2


def test_combining_marks_count_as_zero() -> None:
    assert display_width("é") == 1
    assert display_width("́") == 0


def test_zero_width_and_format_characters_count_as_zero() -> None:
    assert display_width("a​b⁠c﻿") == 3


def test_default_ignorable_unassigned_code_points_count_as_zero() -> None:
    assert display_width("a\U000e0fffb") == 2


def test_soft_hyphen_is_drawn_as_a_hyphen() -> None:
    assert display_width("­") == 1


def test_control_characters_take_no_columns() -> None:
    assert display_width("a\tb\r\n\x07") == 2


def test_hangul_syllable_with_trailing_jamo_is_one_wide_cell() -> None:
    assert display_width("한ᆫ") == 2
    assert display_width("한") == 2


def test_hangul_leading_filler_starts_a_wide_block() -> None:
    assert display_width("ᅟᅡ") == 2


def test_emoji_presentation_counts_two_columns() -> None:
    assert display_width("\U0001f600") == 2


def test_emoji_presentation_selector_widens_a_text_default_base() -> None:
    assert display_width("❤") == 1
    assert display_width("❤️") == 2


def test_text_presentation_selector_narrows_an_emoji_default_base() -> None:
    assert display_width("⌚") == 2
    assert display_width("⌚︎") == 1


def test_selectors_change_only_characters_with_variation_sequences() -> None:
    assert display_width("a️") == 1
    assert display_width("日︎") == 2


def test_keycap_sequence_is_one_emoji() -> None:
    assert display_width("#️⃣") == 2


def test_flag_is_one_wide_emoji_and_a_lone_indicator_is_wide() -> None:
    assert display_width("\U0001f1ea\U0001f1f8") == 2
    assert display_width("\U0001f1ea") == 2
    assert display_width("\U0001f1ea\U0001f1f8\U0001f1eb") == 4


def test_zwj_family_is_one_emoji() -> None:
    family = "\U0001f468‍\U0001f469‍\U0001f467‍\U0001f466"
    assert display_width(family) == 2


def test_modifier_sequence_is_one_emoji_even_on_a_text_default_base() -> None:
    assert display_width("\U0001f44d\U0001f3fd") == 2
    assert display_width("\U0001f590\U0001f3fb") == 2


def test_zwj_sequence_on_a_text_default_base_is_one_emoji() -> None:
    assert display_width("\U0001f3f3‍\U0001f308") == 2


def test_lone_skin_tone_modifier_is_wide() -> None:
    assert display_width("\U0001f3fb") == 2


def test_modifier_after_a_letter_is_drawn_on_its_own() -> None:
    assert display_width("a\U0001f3fb") == 3


def test_devanagari_conjunct_is_two_columns() -> None:
    assert display_width("क्ष") == 2


def test_spacing_vowel_sign_makes_its_syllable_two_columns() -> None:
    assert display_width("कि") == 2
    assert display_width("กำ") == 2


def test_lone_spacing_mark_takes_no_columns() -> None:
    assert display_width("ि") == 0


def test_prepended_concatenation_mark_is_drawn() -> None:
    assert display_width("؀1") == 2


def test_escape_sequences_take_no_columns() -> None:
    assert display_width("\x1b[31mred\x1b[0m") == 3


@pytest.mark.parametrize("bad", [b"abc", 3, None, ["a"]])
def test_non_strings_are_rejected(bad: object) -> None:
    with pytest.raises(TypeError, match="text must be str"):
        display_width(bad)  # type: ignore[arg-type]
