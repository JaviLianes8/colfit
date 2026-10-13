"""graphemes: examples of each rule family of UAX #29 (hand written, see test_sources)."""

from __future__ import annotations

import pytest

from colfit import graphemes


def test_empty_text_has_no_clusters() -> None:
    assert graphemes("") == []


def test_ascii_letters_are_one_cluster_each() -> None:
    assert graphemes("abc") == ["a", "b", "c"]


def test_crlf_is_one_cluster_and_other_controls_stand_alone() -> None:
    assert graphemes("a\r\nb\n\x07") == ["a", "\r\n", "b", "\n", "\x07"]


def test_marks_stay_with_their_base() -> None:
    assert graphemes("ẹ́x") == ["ẹ́", "x"]


def test_a_mark_after_a_control_starts_its_own_cluster() -> None:
    assert graphemes("\ń") == ["\n", "́"]


def test_hangul_jamo_join_into_syllables() -> None:
    assert graphemes("한한ᆫ") == ["한", "한ᆫ"]


def test_spacing_marks_and_prepend_join() -> None:
    assert graphemes("कि") == ["कि"]
    assert graphemes("؀١") == ["؀١"]


def test_conjunct_joins_across_the_linker() -> None:
    assert graphemes("क्षि") == ["क्षि"]
    assert graphemes("क्‍ष") == ["क्‍ष"]


def test_linker_before_a_non_consonant_breaks() -> None:
    assert graphemes("क्अ") == ["क्", "अ"]


def test_emoji_zwj_sequence_is_one_cluster() -> None:
    family = "\U0001f468‍\U0001f469‍\U0001f467"
    assert graphemes(family + "!") == [family, "!"]


def test_zwj_after_a_letter_does_not_join_an_emoji() -> None:
    assert graphemes("a‍\U0001f600") == ["a‍", "\U0001f600"]


def test_regional_indicators_pair_up_from_the_start() -> None:
    a, b, c = "\U0001f1e6", "\U0001f1e7", "\U0001f1e8"
    assert graphemes(a + b + c) == [a + b, c]
    assert graphemes("x" + a + b + c + a) == ["x", a + b, c + a]


def test_modifier_sequence_is_one_cluster() -> None:
    assert graphemes("\U0001f44d\U0001f3fd") == ["\U0001f44d\U0001f3fd"]


def test_non_strings_are_rejected() -> None:
    with pytest.raises(TypeError, match="text must be str"):
        graphemes(b"ab")  # type: ignore[arg-type]
