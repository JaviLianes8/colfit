"""display_width: one rule per test, with the reason in the name."""

from __future__ import annotations

import pytest

from colfit import display_width


def test_ascii_counts_one_column_per_character() -> None:
    assert display_width("hello") == 5


def test_empty_string_is_zero() -> None:
    assert display_width("") == 0


def test_wide_east_asian_counts_two_columns() -> None:
    assert display_width("\u65e5\u672c") == 4


def test_fullwidth_forms_count_two_columns() -> None:
    assert display_width("\uff21\uff22") == 4


def test_halfwidth_katakana_counts_one_column() -> None:
    assert display_width("\uff76") == 1


def test_ambiguous_characters_count_one_column() -> None:
    assert display_width("\u2026\u00b1") == 2


def test_combining_marks_count_as_zero() -> None:
    assert display_width("e\u0301") == 1
    assert display_width("\u0301") == 0


def test_zero_width_and_format_characters_count_as_zero() -> None:
    assert display_width("a\u200bb\u2060c\ufeff") == 3


def test_default_ignorable_unassigned_code_points_count_as_zero() -> None:
    assert display_width("a\U000e0fffb") == 2


def test_soft_hyphen_is_drawn_as_a_hyphen() -> None:
    assert display_width("\u00ad") == 1


def test_control_characters_take_no_columns() -> None:
    assert display_width("a\tb\r\n\x07") == 2


def test_hangul_syllable_with_trailing_jamo_is_one_wide_cell() -> None:
    assert display_width("\ud55c\u11ab") == 2
    assert display_width("\u1112\u1161\u11ab") == 2


def test_hangul_leading_filler_starts_a_wide_block() -> None:
    assert display_width("\u115f\u1161") == 2


def test_emoji_presentation_counts_two_columns() -> None:
    assert display_width("\U0001f600") == 2


def test_emoji_presentation_selector_widens_a_text_default_base() -> None:
    assert display_width("\u2764") == 1
    assert display_width("\u2764\ufe0f") == 2


def test_text_presentation_selector_narrows_an_emoji_default_base() -> None:
    assert display_width("\u231a") == 2
    assert display_width("\u231a\ufe0e") == 1


def test_selectors_change_only_characters_with_variation_sequences() -> None:
    assert display_width("a\ufe0f") == 1
    assert display_width("\u65e5\ufe0e") == 2


def test_keycap_sequence_is_one_emoji() -> None:
    assert display_width("#\ufe0f\u20e3") == 2


def test_flag_is_one_wide_emoji_and_a_lone_indicator_is_wide() -> None:
    assert display_width("\U0001f1ea\U0001f1f8") == 2
    assert display_width("\U0001f1ea") == 2
    assert display_width("\U0001f1ea\U0001f1f8\U0001f1eb") == 4


def test_zwj_family_is_one_emoji() -> None:
    family = "\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466"
    assert display_width(family) == 2


def test_modifier_sequence_is_one_emoji_even_on_a_text_default_base() -> None:
    assert display_width("\U0001f44d\U0001f3fd") == 2
    assert display_width("\U0001f590\U0001f3fb") == 2


def test_zwj_sequence_on_a_text_default_base_is_one_emoji() -> None:
    assert display_width("\U0001f3f3\u200d\U0001f308") == 2


def test_lone_skin_tone_modifier_is_wide() -> None:
    assert display_width("\U0001f3fb") == 2


def test_modifier_after_a_letter_is_drawn_on_its_own() -> None:
    assert display_width("a\U0001f3fb") == 3


def test_devanagari_conjunct_is_two_columns() -> None:
    assert display_width("\u0915\u094d\u0937") == 2


def test_spacing_vowel_sign_makes_its_syllable_two_columns() -> None:
    assert display_width("\u0915\u093f") == 2
    assert display_width("\u0e01\u0e33") == 2


def test_lone_spacing_mark_takes_no_columns() -> None:
    assert display_width("\u093f") == 0
    assert display_width("\u0301\u093f") == 0


def test_spacing_letters_add_their_own_width() -> None:
    # Thai SARA AM is a letter that joins the cluster, drawn in its own cell.
    assert display_width("\u0e01\u0e33\u0e33") == 3
    assert display_width("\u65e5\u0e33") == 3


def test_a_chain_of_conjuncts_stays_two_columns() -> None:
    assert display_width("\u0915\u094d\u0937\u094d\u092e") == 2


def test_an_emoji_joined_after_a_prepend_base_is_not_counted_twice() -> None:
    assert display_width("\u0600\U0001f600\u200d\U0001f600") == 3


def test_prepended_concatenation_mark_is_drawn() -> None:
    assert display_width("\u06001") == 2


def test_escape_sequences_take_no_columns() -> None:
    assert display_width("\x1b[31mred\x1b[0m") == 3


@pytest.mark.parametrize("bad", [b"abc", 3, None, ["a"]])
def test_non_strings_are_rejected(bad: object) -> None:
    with pytest.raises(TypeError, match="text must be str"):
        display_width(bad)  # type: ignore[arg-type]
